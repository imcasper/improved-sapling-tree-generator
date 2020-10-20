from collections import OrderedDict
from math import radians
from random import uniform

import bpy
from mathutils import Vector

from .utils import tau, roundBone
from .ArmatureSettings import ArmatureSettings


def create_armature(armature_settings: ArmatureSettings, leafP, cu, leafMesh, leafObj, leafVertSize, leaves, levelCount, splineToBone,
                    treeOb, treeObj):
    arm = bpy.data.armatures.new('tree')
    armOb = bpy.data.objects.new('treeArm', arm)
    armOb.location=bpy.context.scene.cursor.location
    bpy.context.scene.collection.objects.link(armOb)
    # Create a new action to store all animation
    newAction = bpy.data.actions.new(name='windAction')
    armOb.animation_data_create()
    armOb.animation_data.action = newAction
    arm.display_type = 'STICK'
    #arm.use_deform_delay = True
    # Add the armature modifier to the curve
    armMod = treeOb.modifiers.new('windSway', 'ARMATURE')
    if armature_settings.previewArm:
        armMod.show_viewport = False
        arm.display_type = 'WIRE'
        treeOb.hide_viewport = True
    armMod.use_apply_on_spline = True
    armMod.object = armOb
    armMod.use_bone_envelopes = True
    armMod.use_vertex_groups = False
    # If there are leaves then they need a modifier
    if leaves:
        armMod = leafObj.modifiers.new('windSway', 'ARMATURE')
        armMod.object = armOb
        armMod.use_bone_envelopes = False
        armMod.use_vertex_groups = True
    # Make sure all objects are deselected (may not be required?)
    for ob in bpy.data.objects:
        ob.select_set(state=False)

    fps = bpy.context.scene.render.fps
    animSpeed = (24 / fps) * armature_settings.frameRate

    # Set the armature as active and go to edit mode to add bones
    bpy.context.view_layer.objects.active = armOb
    bpy.ops.object.mode_set(mode='EDIT')
    # For all the splines in the curve we need to add bones at each bezier point
    for i, parBone in enumerate(splineToBone):
        if (i < levelCount[armature_settings.armLevels]) or (armature_settings.armLevels == -1) or (not armature_settings.makeMesh):
            s = cu.splines[i]
            b = None
            # Get some data about the spline like length and number of points
            numPoints = len(s.bezier_points) - 1

            #find branching level
            level = 0
            for l, c in enumerate(levelCount):
                if i < c:
                    level = l
                    break
            level = min(level, 3)

            step = armature_settings.boneStep[level]

            # Calculate things for animation
            if armature_settings.armAnim:
                splineL = numPoints * ((s.bezier_points[0].co - s.bezier_points[1].co).length)
                # Set the random phase difference of the animation
                bxOffset = uniform(0, tau)
                byOffset = uniform(0, tau)
                # Set the phase multiplier for the spline
                #bMult_r = (s.bezier_points[0].radius / max(splineL, 1e-6)) * (1 / 15) * (1 / frameRate)
                #bMult = degrees(bMult_r)  # This shouldn't have to be in degrees but it looks much better in animation
                bMult = (1 / max(splineL ** .5, 1e-6)) * (1 / 4)
                #print((1 / bMult) * tau) #print wavelength in frames

                windFreq1 = bMult * animSpeed
                windFreq2 = 0.7 * bMult * animSpeed
                if armature_settings.loopFrames != 0:
                    bMult_l = 1 / (armature_settings.loopFrames / tau)
                    fRatio = max(1, round(windFreq1 / bMult_l))
                    fgRatio = max(1, round(windFreq2 / bMult_l))
                    windFreq1 = fRatio * bMult_l
                    windFreq2 = fgRatio * bMult_l

            # For all the points in the curve (less the last) add a bone and name it by the spline it will affect
            nx = 0
            for n in range(0, numPoints, step):
                oldBone = b
                boneName = 'bone' + (str(i)).rjust(3, '0') + '.' + (str(n)).rjust(3, '0')
                b = arm.edit_bones.new(boneName)
                b.head = s.bezier_points[n].co
                nx += step
                nx = min(nx, numPoints)
                b.tail = s.bezier_points[nx].co

                b.head_radius = s.bezier_points[n].radius
                b.tail_radius = s.bezier_points[n + 1].radius
                b.envelope_distance = 0.001

#                # If there are leaves then we need a new vertex group so they will attach to the bone
#                if not leafAnim:
#                    if (len(levelCount) > 1) and (i >= levelCount[-2]) and leafObj:
#                        leafObj.vertex_groups.new(name=boneName)
#                    elif (len(levelCount) == 1) and leafObj:
#                        leafObj.vertex_groups.new(name=boneName)

                # If this is first point of the spline then it must be parented to the level above it
                if n == 0:
                    if parBone:
                        b.parent = arm.edit_bones[parBone]
                # Otherwise, we need to attach it to the previous bone in the spline
                else:
                    b.parent = oldBone
                    b.use_connect = True
                # If there isn't a previous bone then it shouldn't be attached
                if not oldBone:
                    b.use_connect = False

                # Add the animation to the armature if required
                if armature_settings.armAnim:
                    # Define all the required parameters of the wind sway by the dimension of the spline
                    #a0 = 4 * splineL * (1 - n / (numPoints + 1)) / max(s.bezier_points[n].radius, 1e-6)
                    a0 = 2 * (splineL / numPoints) * (1 - n / (numPoints + 1)) / max(s.bezier_points[n].radius, 1e-6)
                    a0 = a0 * min(step, numPoints)
                    #a0 = (splineL / numPoints) / max(s.bezier_points[n].radius, 1e-6)
                    a1 = (armature_settings.wind / 50) * a0
                    a2 = a1 * .65  #(windGust / 50) * a0 + a1 / 2

                    p = s.bezier_points[nx].co - s.bezier_points[n].co
                    p.normalize()
                    ag = (armature_settings.wind * armature_settings.gust / 50) * a0
                    a3 = -p[0] * ag
                    a4 = p[2] * ag

                    a1 = radians(a1)
                    a2 = radians(a2)
                    a3 = radians(a3)
                    a4 = radians(a4)

                    #wind bending
                    if armature_settings.loopFrames == 0:
                        swayFreq = armature_settings.gustF * (tau / fps) * armature_settings.frameRate  #animSpeed # .075 # 0.02
                    else:
                        swayFreq = 1 / (armature_settings.loopFrames / tau)

                    # Prevent tree base from rotating
                    if (boneName == "bone000.000") or (boneName == "bone000.001"):
                        a1 = 0
                        a2 = 0
                        a3 = 0
                        a4 = 0

                    # Add new fcurves for each sway as well as the modifiers
                    swayX = armOb.animation_data.action.fcurves.new('pose.bones["' + boneName + '"].rotation_euler', index=0)
                    swayY = armOb.animation_data.action.fcurves.new('pose.bones["' + boneName + '"].rotation_euler', index=2)

                    swayXMod1 = swayX.modifiers.new(type='FNGENERATOR')
                    swayXMod2 = swayX.modifiers.new(type='FNGENERATOR')

                    swayYMod1 = swayY.modifiers.new(type='FNGENERATOR')
                    swayYMod2 = swayY.modifiers.new(type='FNGENERATOR')

                    # Set the parameters for each modifier
                    swayXMod1.amplitude = a1
                    swayXMod1.phase_offset = bxOffset
                    swayXMod1.phase_multiplier = windFreq1

                    swayXMod2.amplitude = a2
                    swayXMod2.phase_offset = 0.7 * bxOffset
                    swayXMod2.phase_multiplier = windFreq2
                    swayXMod2.use_additive = True

                    swayYMod1.amplitude = a1
                    swayYMod1.phase_offset = byOffset
                    swayYMod1.phase_multiplier = windFreq1

                    swayYMod2.amplitude = a2
                    swayYMod2.phase_offset = 0.7 * byOffset
                    swayYMod2.phase_multiplier = windFreq2
                    swayYMod2.use_additive = True

                    #wind bending
                    swayYMod3 = swayY.modifiers.new(type='FNGENERATOR')
                    swayYMod3.amplitude = a3
                    swayYMod3.phase_multiplier = swayFreq
                    swayYMod3.value_offset = .6 * a3
                    swayYMod3.use_additive = True

                    swayXMod3 = swayX.modifiers.new(type='FNGENERATOR')
                    swayXMod3.amplitude = a4
                    swayXMod3.phase_multiplier = swayFreq
                    swayXMod3.value_offset = .6 * a4
                    swayXMod3.use_additive = True

    if leaves:
        bonelist = [b.name for b in arm.edit_bones]
        vertexGroups = OrderedDict()
        for i, cp in enumerate(leafP):
            # find leafs parent bone
            leafParent = roundBone(cp.parBone, armature_settings.boneStep[armature_settings.armLevels])
            idx = int(leafParent[4:-4])
            while leafParent not in bonelist:
                #find parent bone of parent bone
                leafParent = splineToBone[idx]
                idx = int(leafParent[4:-4])

            if armature_settings.leafAnim:
                bname = "leaf" + str(i)
                b = arm.edit_bones.new(bname)
                b.head = cp.co
                b.tail = cp.co + Vector((0, 0, .02))
                b.envelope_distance = 0.0
                b.parent = arm.edit_bones[leafParent]

                vertexGroups[bname] = [v.index for v in leafMesh.vertices[leafVertSize * i:(leafVertSize * i + leafVertSize)]]

                if armature_settings.armAnim:
                    # Define all the required parameters of the wind sway by the dimension of the spline
                    a1 = armature_settings.wind * .25
                    a1 *= armature_settings.af1

                    bMult = (1 / animSpeed) * 6
                    bMult *= 1 / max(armature_settings.af2, .001)

                    ofstRand = armature_settings.af3
                    bxOffset = uniform(-ofstRand, ofstRand)
                    byOffset = uniform(-ofstRand, ofstRand)

                    # Add new fcurves for each sway as well as the modifiers
                    swayX = armOb.animation_data.action.fcurves.new('pose.bones["' + bname + '"].rotation_euler', index=0)
                    swayY = armOb.animation_data.action.fcurves.new('pose.bones["' + bname + '"].rotation_euler', index=2)

                    # Add keyframe so noise works
                    swayX.keyframe_points.add(1)
                    swayY.keyframe_points.add(1)
                    swayX.keyframe_points[0].co = (0, 0)
                    swayY.keyframe_points[0].co = (0, 0)

                    # Add noise modifiers
                    swayXMod = swayX.modifiers.new(type='NOISE')
                    swayYMod = swayY.modifiers.new(type='NOISE')

                    if armature_settings.loopFrames != 0:
                        swayXMod.use_restricted_range = True
                        swayXMod.frame_end = armature_settings.loopFrames
                        swayXMod.blend_in = 4
                        swayXMod.blend_out = 4
                        swayYMod.use_restricted_range = True
                        swayYMod.frame_end = armature_settings.loopFrames
                        swayYMod.blend_in = 4
                        swayYMod.blend_out = 4

                    swayXMod.scale = bMult
                    swayXMod.strength = a1
                    swayXMod.offset = bxOffset

                    swayYMod.scale = bMult
                    swayYMod.strength = a1
                    swayYMod.offset = byOffset

            else:
                if leafParent not in vertexGroups:
                    vertexGroups[leafParent] = []
                vertexGroups[leafParent].extend([v.index for v in leafMesh.vertices[leafVertSize * i:(leafVertSize * i + leafVertSize)]])

        for group in vertexGroups:
            leafObj.vertex_groups.new(name=group)
            leafObj.vertex_groups[group].add(vertexGroups[group], 1.0, 'ADD')

    # Now we need the rotation mode to be 'XYZ' to ensure correct rotation
    bpy.ops.object.mode_set(mode='OBJECT')
    for p in armOb.pose.bones:
        p.rotation_mode = 'XYZ'

    treeOb.parent = armOb
    if armature_settings.makeMesh:
        treeObj.parent = armOb

    return armOb
