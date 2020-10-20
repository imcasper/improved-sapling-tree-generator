import time
from collections import OrderedDict

from .utils import eval_bez, round_bone
from .TreeSettings import TreeSettings
from .ArmatureSettings import ArmatureSettings


def make_armature_mesh(armature_settings, tree_settings, armature_object, tree_curve, level_count, spline_to_bone, tree_mesh, tree_mesh_object):
    splineToBone1 = spline_to_bone
    spline_to_bone = [s[0] if len(s) > 1 else s for s in splineToBone1]
    isend = [s[1] if len(s) > 1 else False for s in splineToBone1]
    issplit = [s[2] if len(s) > 2 else False for s in splineToBone1]
    splitPidx = [s[3] if len(s) > 2 else 0 for s in splineToBone1]

    t1 = time.time()
    treeVerts = []
    treeEdges = []
    root_vert = []
    vert_radius = []
    vertexGroups = OrderedDict()
    lastVerts = []
    # vertex group for each level
    levelGroups = []
    for lvl in range(tree_settings.levels):
        tree_mesh_object.vertex_groups.new(name="Branching Level " + str(lvl))
        levelGroups.append([])
    for i, tree_settings.curve in enumerate(tree_curve.splines):
        points = tree_settings.curve.bezier_points

        # find branching level
        level = 0
        for l, c in enumerate(level_count):
            if i < c:
                level = l
                break
        level = min(level, 3)

        step = armature_settings.boneStep[level]
        vindex = len(treeVerts)

        p1 = points[0]

        # add extra vertex for splits
        if issplit[i]:
            pb = int(spline_to_bone[i][4:-4])
            pn = splitPidx[i]  # int(splineToBone[i][-3:])
            p_1 = tree_curve.splines[pb].bezier_points[pn]
            p_2 = tree_curve.splines[pb].bezier_points[pn + 1]
            p = eval_bez(p_1.co, p_1.handle_right, p_2.handle_left, p_2.co, 1 - 1 / (tree_settings.resU + 1))
            treeVerts.append(p)

            root_vert.append(False)
            vert_radius.append((p1.radius * .75, p1.radius * .75))
            treeEdges.append([vindex, vindex + 1])
            vindex += 1

        if isend[i]:
            parent = lastVerts[int(spline_to_bone[i][4:-4])]
            vindex -= 1
        else:
            # add first point
            treeVerts.append(p1.co)
            root_vert.append(True)
            vert_radius.append((p1.radius, p1.radius))

        # dont make vertex group if above armLevels
        if (i >= level_count[armature_settings.armLevels]):
            idx = i
            groupName = spline_to_bone[idx]
            g = True
            while groupName not in vertexGroups:
                # find parent bone of parent bone
                b = spline_to_bone[idx]
                idx = int(b[4:-4])
                groupName = spline_to_bone[idx]
        else:
            g = False

        for lvl, p2 in enumerate(points[1:]):
            if not g:
                groupName = 'bone' + (str(i)).rjust(3, '0') + '.' + (str(lvl)).rjust(3, '0')
                groupName = round_bone(groupName, step)
                if groupName not in vertexGroups:
                    vertexGroups[groupName] = []

            # parent first vert in split to parent branch bone
            if issplit[i] and lvl == 0:
                if g:
                    vertexGroups[groupName].append(vindex - 1)
                else:
                    vertexGroups[spline_to_bone[i]].append(vindex - 1)
                levelGroups[level].append(vindex - 1)

            for f in range(1, tree_settings.resU + 1):
                pos = f / tree_settings.resU
                p = eval_bez(p1.co, p1.handle_right, p2.handle_left, p2.co, pos)
                radius = p1.radius + (p2.radius - p1.radius) * pos

                treeVerts.append(p)
                root_vert.append(False)
                vert_radius.append((radius, radius))

                if (isend[i]) and (lvl == 0) and (f == 1):
                    edge = [parent, lvl * tree_settings.resU + f + vindex]
                else:
                    edge = [lvl * tree_settings.resU + f + vindex - 1, lvl * tree_settings.resU + f + vindex]
                    # add vert to group
                    vertexGroups[groupName].append(lvl * tree_settings.resU + f + vindex - 1)
                    levelGroups[level].append(lvl * tree_settings.resU + f + vindex - 1)
                treeEdges.append(edge)

            vertexGroups[groupName].append(lvl * tree_settings.resU + tree_settings.resU + vindex)
            levelGroups[level].append(lvl * tree_settings.resU + tree_settings.resU + vindex)

            p1 = p2

        lastVerts.append(len(treeVerts) - 1)
    tree_mesh.from_pydata(treeVerts, treeEdges, ())
    if armature_settings.useArm:
        for group in vertexGroups:
            tree_mesh_object.vertex_groups.new(name=group)
            tree_mesh_object.vertex_groups[group].add(vertexGroups[group], 1.0, 'ADD')
    for i, g in enumerate(levelGroups):
        tree_mesh_object.vertex_groups["Branching Level " + str(i)].add(g, 1.0, 'ADD')
    # add armature
    if armature_settings.useArm:
        armMod = tree_mesh_object.modifiers.new('windSway', 'ARMATURE')
        if armature_settings.previewArm:
            armature_object.hide_viewport = True
            armature_object.data.display_type = 'STICK'
        armMod.object = armature_object
        armMod.use_bone_envelopes = False
        armMod.use_vertex_groups = True
    # add skin modifier and set data
    skinMod = tree_mesh_object.modifiers.new('Skin', 'SKIN')
    skinMod.use_smooth_shade = True
    if armature_settings.previewArm:
        skinMod.show_viewport = False
    skindata = tree_mesh_object.data.skin_vertices[0].data
    for i, radius in enumerate(vert_radius):
        skindata[i].radius = radius
        skindata[i].use_root = root_vert[i]
    print("mesh time", time.time() - t1)