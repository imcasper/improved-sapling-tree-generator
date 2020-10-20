import time
from collections import OrderedDict

from .utils import eval_bez, round_bone
from .TreeSettings import TreeSettings
from .ArmatureSettings import ArmatureSettings


def make_armature_mesh(armature_settings: ArmatureSettings, tree_settings: TreeSettings, armature_object, tree_curve, level_count, spline_to_bone, tree_mesh, tree_mesh_object):
    spline_to_bone1 = spline_to_bone
    spline_to_bone = [s[0] if len(s) > 1 else s for s in spline_to_bone1]
    is_end = [s[1] if len(s) > 1 else False for s in spline_to_bone1]
    is_split = [s[2] if len(s) > 2 else False for s in spline_to_bone1]
    split_pidx = [s[3] if len(s) > 2 else 0 for s in spline_to_bone1]

    t1 = time.time()
    tree_verts = []
    tree_edges = []
    root_vert = []
    vert_radius = []
    vertex_groups = OrderedDict()
    last_verts = []

    # Vertex group for each level
    level_groups = []
    for lvl in range(tree_settings.levels):
        tree_mesh_object.vertex_groups.new(name="Branching Level " + str(lvl))
        level_groups.append([])

    for i, tree_settings.curve in enumerate(tree_curve.splines):
        points = tree_settings.curve.bezier_points

        # Find branching level
        level = 0
        for lvl, c in enumerate(level_count):
            if i < c:
                level = lvl
                break
        level = min(level, 3)

        step = armature_settings.boneStep[level]
        v_index = len(tree_verts)

        p1 = points[0]

        # Add extra vertex for splits
        if is_split[i]:
            pb = int(spline_to_bone[i][4:-4])
            pn = split_pidx[i]  # int(splineToBone[i][-3:])
            p_1 = tree_curve.splines[pb].bezier_points[pn]
            p_2 = tree_curve.splines[pb].bezier_points[pn + 1]
            p = eval_bez(p_1.co, p_1.handle_right, p_2.handle_left, p_2.co, 1 - 1 / (tree_settings.resU + 1))
            tree_verts.append(p)

            root_vert.append(False)
            vert_radius.append((p1.radius * .75, p1.radius * .75))
            tree_edges.append([v_index, v_index + 1])
            v_index += 1

        if is_end[i]:
            parent = last_verts[int(spline_to_bone[i][4:-4])]
            v_index -= 1
        else:
            # Add first point
            tree_verts.append(p1.co)
            root_vert.append(True)
            vert_radius.append((p1.radius, p1.radius))

        # Dont make vertex group if above armLevels
        if (i >= level_count[armature_settings.armLevels]):
            idx = i
            group_name = spline_to_bone[idx]
            g = True
            while group_name not in vertex_groups:
                # find parent bone of parent bone
                b = spline_to_bone[idx]
                idx = int(b[4:-4])
                group_name = spline_to_bone[idx]
        else:
            g = False

        for lvl, p2 in enumerate(points[1:]):
            if not g:
                group_name = 'bone' + (str(i)).rjust(3, '0') + '.' + (str(lvl)).rjust(3, '0')
                group_name = round_bone(group_name, step)
                if group_name not in vertex_groups:
                    vertex_groups[group_name] = []

            # parent first vert in split to parent branch bone
            if is_split[i] and lvl == 0:
                if g:
                    vertex_groups[group_name].append(v_index - 1)
                else:
                    vertex_groups[spline_to_bone[i]].append(v_index - 1)
                level_groups[level].append(v_index - 1)

            for f in range(1, tree_settings.resU + 1):
                pos = f / tree_settings.resU
                p = eval_bez(p1.co, p1.handle_right, p2.handle_left, p2.co, pos)
                radius = p1.radius + (p2.radius - p1.radius) * pos

                tree_verts.append(p)
                root_vert.append(False)
                vert_radius.append((radius, radius))

                if (is_end[i]) and (lvl == 0) and (f == 1):
                    edge = [parent, lvl * tree_settings.resU + f + v_index]
                else:
                    edge = [lvl * tree_settings.resU + f + v_index - 1, lvl * tree_settings.resU + f + v_index]
                    # add vert to group
                    vertex_groups[group_name].append(lvl * tree_settings.resU + f + v_index - 1)
                    level_groups[level].append(lvl * tree_settings.resU + f + v_index - 1)
                tree_edges.append(edge)

            vertex_groups[group_name].append(lvl * tree_settings.resU + tree_settings.resU + v_index)
            level_groups[level].append(lvl * tree_settings.resU + tree_settings.resU + v_index)

            p1 = p2

        last_verts.append(len(tree_verts) - 1)
    tree_mesh.from_pydata(tree_verts, tree_edges, ())
    if armature_settings.useArm:
        for group in vertex_groups:
            tree_mesh_object.vertex_groups.new(name=group)
            tree_mesh_object.vertex_groups[group].add(vertex_groups[group], 1.0, 'ADD')

    for i, g in enumerate(level_groups):
        tree_mesh_object.vertex_groups["Branching Level " + str(i)].add(g, 1.0, 'ADD')

    # Add armature
    if armature_settings.useArm:
        armature_modifier = tree_mesh_object.modifiers.new('windSway', 'ARMATURE')
        if armature_settings.previewArm:
            armature_object.hide_viewport = True
            armature_object.data.display_type = 'STICK'
        armature_modifier.object = armature_object
        armature_modifier.use_bone_envelopes = False
        armature_modifier.use_vertex_groups = True
    # add skin modifier and set data
    skin_modifier = tree_mesh_object.modifiers.new('Skin', 'SKIN')
    skin_modifier.use_smooth_shade = True
    if armature_settings.previewArm:
        skin_modifier.show_viewport = False
    skin_data = tree_mesh_object.data.skin_vertices[0].data
    for i, radius in enumerate(vert_radius):
        skin_data[i].radius = radius
        skin_data[i].use_root = root_vert[i]
    print("mesh time", time.time() - t1)
