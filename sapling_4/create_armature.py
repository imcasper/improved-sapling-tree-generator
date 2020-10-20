from collections import OrderedDict
from math import radians
from random import uniform

import bpy
from mathutils import Vector

from .utils import tau, round_bone
from .ArmatureSettings import ArmatureSettings


def create_armature(armature_settings: ArmatureSettings, leaf_points, tree_curve, leaf_mesh, leaf_mesh_object, leaf_vert_size, leaves, level_count, spline_to_bone, tree_curve_object, tree_mesh_object):
    armature = bpy.data.armatures.new('tree')
    armature_object = bpy.data.objects.new('treeArm', armature)
    armature_object.location = bpy.context.scene.cursor.location
    bpy.context.scene.collection.objects.link(armature_object)

    # Create a new action to store all animation
    new_action = bpy.data.actions.new(name='windAction')
    armature_object.animation_data_create()
    armature_object.animation_data.action = new_action
    armature.display_type = 'STICK'
    # armature.use_deform_delay = True

    # Add the armature modifier to the curve
    armature_modifier = tree_curve_object.modifiers.new('windSway', 'ARMATURE')
    if armature_settings.previewArm:
        armature_modifier.show_viewport = False
        armature.display_type = 'WIRE'
        tree_curve_object.hide_viewport = True

    armature_modifier.use_apply_on_spline = True
    armature_modifier.object = armature_object
    armature_modifier.use_bone_envelopes = True
    armature_modifier.use_vertex_groups = False

    # If there are leaves then they need a modifier
    if leaves:
        armature_modifier = leaf_mesh_object.modifiers.new('windSway', 'ARMATURE')
        armature_modifier.object = armature_object
        armature_modifier.use_bone_envelopes = False
        armature_modifier.use_vertex_groups = True

    # Make sure all objects are deselected (may not be required?)
    for ob in bpy.data.objects:
        ob.select_set(state=False)

    fps = bpy.context.scene.render.fps
    anim_speed = (24 / fps) * armature_settings.frameRate

    # Set the armature as active and go to edit mode to add bones
    bpy.context.view_layer.objects.active = armature_object
    bpy.ops.object.mode_set(mode='EDIT')

    # For all the splines in the curve we need to add bones at each bezier point
    for i, par_bone in enumerate(spline_to_bone):
        if (i < level_count[armature_settings.armLevels]) or (armature_settings.armLevels == -1) or (not armature_settings.makeMesh):
            add_bones_to_branches(anim_speed, armature, armature_object, armature_settings, tree_curve, fps, i, level_count, par_bone)

    if leaves:
        add_bones_for_leafs(anim_speed, armature, armature_object, armature_settings, leaf_mesh, leaf_mesh_object, leaf_points, leaf_vert_size, spline_to_bone)

    # Now we need the rotation mode to be 'XYZ' to ensure correct rotation
    bpy.ops.object.mode_set(mode='OBJECT')
    for pose_bone in armature_object.pose.bones:
        pose_bone.rotation_mode = 'XYZ'

    tree_curve_object.parent = armature_object
    if armature_settings.makeMesh:
        tree_mesh_object.parent = armature_object

    return armature_object


def add_bones_for_leafs(anim_speed, arm, arm_ob, armature_settings, leaf_mesh, leaf_mesh_object, leaf_points, leaf_vert_size, spline_to_bone):
    bone_list = [b.name for b in arm.edit_bones]
    vertex_groups = OrderedDict()
    for i, cp in enumerate(leaf_points):
        # Find leafs parent bone
        leaf_parent = round_bone(cp.parBone, armature_settings.boneStep[armature_settings.armLevels])
        idx = int(leaf_parent[4:-4])
        while leaf_parent not in bone_list:
            # Find parent bone of parent bone
            leaf_parent = spline_to_bone[idx]
            idx = int(leaf_parent[4:-4])

        if armature_settings.leafAnim:
            animate_leafs(anim_speed, arm, arm_ob, armature_settings, cp, i, leaf_mesh, leaf_parent, leaf_vert_size,
                          vertex_groups)

        else:
            if leaf_parent not in vertex_groups:
                vertex_groups[leaf_parent] = []
            vertex_groups[leaf_parent].extend(
                [v.index for v in leaf_mesh.vertices[leaf_vert_size * i:(leaf_vert_size * i + leaf_vert_size)]])

    for group in vertex_groups:
        leaf_mesh_object.vertex_groups.new(name=group)
        leaf_mesh_object.vertex_groups[group].add(vertex_groups[group], 1.0, 'ADD')


def animate_leafs(anim_speed, arm, arm_ob, armature_settings, cp, i, leaf_mesh, leaf_parent, leaf_vert_size,
                  vertex_groups):
    b_name = "leaf" + str(i)
    b = arm.edit_bones.new(b_name)
    b.head = cp.co
    b.tail = cp.co + Vector((0, 0, .02))
    b.envelope_distance = 0.0
    b.parent = arm.edit_bones[leaf_parent]
    vertex_groups[b_name] = [v.index for v in
                             leaf_mesh.vertices[leaf_vert_size * i:(leaf_vert_size * i + leaf_vert_size)]]
    if armature_settings.armAnim:
        # Define all the required parameters of the wind sway by the dimension of the spline
        a1 = armature_settings.wind * .25
        a1 *= armature_settings.af1

        b_mult = (1 / anim_speed) * 6
        b_mult *= 1 / max(armature_settings.af2, .001)

        offset_rand = armature_settings.af3
        bx_offset = uniform(-offset_rand, offset_rand)
        by_offset = uniform(-offset_rand, offset_rand)

        # Add new fcurves for each sway as well as the modifiers
        sway_x = arm_ob.animation_data.action.fcurves.new('pose.bones["' + b_name + '"].rotation_euler',
                                                          index=0)
        sway_y = arm_ob.animation_data.action.fcurves.new('pose.bones["' + b_name + '"].rotation_euler',
                                                          index=2)

        # Add keyframe so noise works
        sway_x.keyframe_points.add(1)
        sway_y.keyframe_points.add(1)
        sway_x.keyframe_points[0].co = (0, 0)
        sway_y.keyframe_points[0].co = (0, 0)

        # Add noise modifiers
        sway_x_mod = sway_x.modifiers.new(type='NOISE')
        sway_y_mod = sway_y.modifiers.new(type='NOISE')

        if armature_settings.loopFrames != 0:
            sway_x_mod.use_restricted_range = True
            sway_x_mod.frame_end = armature_settings.loopFrames
            sway_x_mod.blend_in = 4
            sway_x_mod.blend_out = 4
            sway_y_mod.use_restricted_range = True
            sway_y_mod.frame_end = armature_settings.loopFrames
            sway_y_mod.blend_in = 4
            sway_y_mod.blend_out = 4

        sway_x_mod.scale = b_mult
        sway_x_mod.strength = a1
        sway_x_mod.offset = bx_offset

        sway_y_mod.scale = b_mult
        sway_y_mod.strength = a1
        sway_y_mod.offset = by_offset


def add_bones_to_branches(anim_speed, armature, armature_object, armature_settings, tree_curve, fps, i, level_count, par_bone):
    s = tree_curve.splines[i]
    b = None
    # Get some data about the spline like length and number of points
    num_points = len(s.bezier_points) - 1
    # Find branching level
    level = 0
    for l, c in enumerate(level_count):
        if i < c:
            level = l
            break
    level = min(level, 3)
    step = armature_settings.boneStep[level]

    # Calculate things for animation
    spline_l = num_points * (s.bezier_points[0].co - s.bezier_points[1].co).length
    # Set the random phase difference of the animation
    bx_offset = uniform(0, tau)
    by_offset = uniform(0, tau)
    # Set the phase multiplier for the spline
    # bMult_r = (s.bezier_points[0].radius / max(spline_l, 1e-6)) * (1 / 15) * (1 / frameRate)
    # b_mult = degrees(bMult_r)  # This shouldn't have to be in degrees but it looks much better in animation
    b_mult = (1 / max(spline_l ** .5, 1e-6)) * (1 / 4)
    # print((1 / b_mult) * tau) # Print wavelength in frames

    wind_freq1 = b_mult * anim_speed
    wind_freq2 = 0.7 * b_mult * anim_speed
    if armature_settings.loopFrames != 0:
        b_mult_l = 1 / (armature_settings.loopFrames / tau)
        f_ratio = max(1, round(wind_freq1 / b_mult_l))
        fg_ratio = max(1, round(wind_freq2 / b_mult_l))
        wind_freq1 = f_ratio * b_mult_l
        wind_freq2 = fg_ratio * b_mult_l

    # For all the points in the curve (less the last) add a bone and name it by the spline it will affect
    nx = 0
    for n in range(0, num_points, step):
        old_bone = b
        bone_name = 'bone' + (str(i)).rjust(3, '0') + '.' + (str(n)).rjust(3, '0')
        b = armature.edit_bones.new(bone_name)
        b.head = s.bezier_points[n].co
        nx += step
        nx = min(nx, num_points)
        b.tail = s.bezier_points[nx].co

        b.head_radius = s.bezier_points[n].radius
        b.tail_radius = s.bezier_points[n + 1].radius
        b.envelope_distance = 0.001

        #                # If there are leaves then we need a new vertex group so they will attach to the bone
        #                if not leafAnim:
        #                    if (len(levelCount) > 1) and (i >= levelCount[-2]) and leafObj:
        #                        leafObj.vertex_groups.new(name=bone_name)
        #                    elif (len(levelCount) == 1) and leafObj:
        #                        leafObj.vertex_groups.new(name=bone_name)

        # If this is first point of the spline then it must be parented to the level above it
        if n == 0:
            if par_bone:
                b.parent = armature.edit_bones[par_bone]
        # Otherwise, we need to attach it to the previous bone in the spline
        else:
            b.parent = old_bone
            b.use_connect = True
        # If there isn't a previous bone then it shouldn't be attached
        if not old_bone:
            b.use_connect = False

        # Add the animation to the armature if required
        if armature_settings.armAnim:
            animate_branches(armature_object, armature_settings, bone_name, bx_offset, by_offset, fps, n, num_points,
                             nx, s, spline_l, step, wind_freq1, wind_freq2)


def animate_branches(armature_object, armature_settings, bone_name, bx_offset, by_offset, fps, n, num_points, nx, s,
                     spline_l, step, wind_freq1, wind_freq2):
    # Define all the required parameters of the wind sway by the dimension of the spline
    # a0 = 4 * spline_l * (1 - n / (num_points + 1)) / max(s.bezier_points[n].radius, 1e-6)
    a0 = 2 * (spline_l / num_points) * (1 - n / (num_points + 1)) / max(s.bezier_points[n].radius, 1e-6)
    a0 = a0 * min(step, num_points)
    # a0 = (spline_l / num_points) / max(s.bezier_points[n].radius, 1e-6)
    a1 = (armature_settings.wind / 50) * a0
    a2 = a1 * .65  # (windGust / 50) * a0 + a1 / 2
    p = s.bezier_points[nx].co - s.bezier_points[n].co
    p.normalize()
    ag = (armature_settings.wind * armature_settings.gust / 50) * a0
    a3 = -p[0] * ag
    a4 = p[2] * ag
    a1 = radians(a1)
    a2 = radians(a2)
    a3 = radians(a3)
    a4 = radians(a4)
    # Wind bending
    if armature_settings.loopFrames == 0:
        sway_freq = armature_settings.gustF * (tau / fps) * armature_settings.frameRate  # anim_speed # .075 # 0.02
    else:
        sway_freq = 1 / (armature_settings.loopFrames / tau)
    # Prevent tree base from rotating
    if (bone_name == "bone000.000") or (bone_name == "bone000.001"):
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
    # Add new fcurves for each sway as well as the modifiers
    sway_x = armature_object.animation_data.action.fcurves.new('pose.bones["' + bone_name + '"].rotation_euler',
                                                               index=0)
    sway_y = armature_object.animation_data.action.fcurves.new('pose.bones["' + bone_name + '"].rotation_euler',
                                                               index=2)
    # Set the parameters for each modifier
    # sway_x_mod1
    # set_modifier_parameters(sway_x, a1, bx_offset, wind_freq1)
    # # sway_y_mod1
    # set_modifier_parameters(sway_y, a1, by_offset, wind_freq1)
    # # sway_x_mod2
    # set_modifier_parameters(sway_x, a2, 0.7 * bx_offset, wind_freq2, True)
    # # sway_y_mod2
    # set_modifier_parameters(sway_y, a2, 0.7 * by_offset, wind_freq2, True)
    # # sway_x_mod3
    # set_modifier_parameters(sway_x, a3, )
    # # sway_y_mod3
    # set_modifier_parameters(sway_y, )
    # # wind bending
    # sway_y_mod3 = sway_y.modifiers.new(type='FNGENERATOR')
    # sway_y_mod3.amplitude = a3
    # sway_y_mod3.phase_multiplier = sway_freq
    # sway_y_mod3.value_offset = .6 * a3
    # sway_y_mod3.use_additive = True
    # sway_x_mod3 = sway_x.modifiers.new(type='FNGENERATOR')
    # sway_x_mod3.amplitude = a4
    # sway_x_mod3.phase_multiplier = sway_freq
    # sway_x_mod3.value_offset = .6 * a4
    # sway_x_mod3.use_additive = True
    set_modifier_parameters(a1, a2, a3, a4, bx_offset, by_offset, sway_freq, sway_x, sway_y, wind_freq1,
                            wind_freq2)


# def set_modifier_parameters1(sway_mod, a, offset, wind_freq, use_add=False):
#     sway_mod = sway_mod.modifiers.new(type='FNGENERATOR')
#     sway_mod.amplitude = a
#     sway_mod.phase_offset = offset
#     sway_mod.phase_multiplier = wind_freq
#     sway_mod.use_additive = use_add


def set_modifier_parameters(a1, a2, a3, a4, bx_offset, by_offset, sway_freq, sway_x, sway_y, wind_freq1, wind_freq2):
    sway_x_mod1 = sway_x.modifiers.new(type='FNGENERATOR')
    sway_x_mod1.amplitude = a1
    sway_x_mod1.phase_offset = bx_offset
    sway_x_mod1.phase_multiplier = wind_freq1

    sway_y_mod1 = sway_y.modifiers.new(type='FNGENERATOR')
    sway_y_mod1.amplitude = a1
    sway_y_mod1.phase_offset = by_offset
    sway_y_mod1.phase_multiplier = wind_freq1

    sway_x_mod2 = sway_x.modifiers.new(type='FNGENERATOR')
    sway_x_mod2.amplitude = a2
    sway_x_mod2.phase_offset = 0.7 * bx_offset
    sway_x_mod2.phase_multiplier = wind_freq2
    sway_x_mod2.use_additive = True

    sway_y_mod2 = sway_y.modifiers.new(type='FNGENERATOR')
    sway_y_mod2.amplitude = a2
    sway_y_mod2.phase_offset = 0.7 * by_offset
    sway_y_mod2.phase_multiplier = wind_freq2
    sway_y_mod2.use_additive = True

    # Wind bending
    sway_y_mod3 = sway_y.modifiers.new(type='FNGENERATOR')
    sway_y_mod3.amplitude = a3
    sway_y_mod3.phase_multiplier = sway_freq
    sway_y_mod3.value_offset = .6 * a3
    sway_y_mod3.use_additive = True

    sway_x_mod3 = sway_x.modifiers.new(type='FNGENERATOR')
    sway_x_mod3.amplitude = a4
    sway_x_mod3.phase_multiplier = sway_freq
    sway_x_mod3.value_offset = .6 * a4
    sway_x_mod3.use_additive = True
