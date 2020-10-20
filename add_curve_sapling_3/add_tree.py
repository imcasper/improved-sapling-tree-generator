import time
from collections import deque, OrderedDict
from math import radians, copysign
from random import seed, uniform, getstate

import bpy
from mathutils import Vector

from .utils import toRad, evalBez, roundBone
from .preform_pruning import perform_pruning
from .shape_ratio import shape_ratio
from .kickstart_trunk import kickstart_trunk
from .fabricate_stems import fabricate_stems
from .gen_leaf_mesh import gen_leaf_mesh
from .create_armature import create_armature
from .find_taper import find_taper
from .TreeSettings import TreeSettings
from .LeafSettings import LeafSettings
from .ArmatureSettings import ArmatureSettings


def add_tree(props):
    global splitError
    #startTime = time.time()
    # Set the seed for repeatable results
    seed(props.seed)#

    # Set all other variables
    tree_settings = TreeSettings(props)
    leaf_settings = LeafSettings(props)
    armature_settings = ArmatureSettings(props)

    baseSize = props.baseSize
    baseSize_s = props.baseSize_s
    leafBaseSize = props.leafBaseSize

    pruneBase = props.pruneBase

    #taper
    if tree_settings.autoTaper:
        tree_settings.taper = find_taper(tree_settings)

    leafObj = None

    for ob in bpy.data.objects:
        ob.select = False

    # Initialise the tree object and curve and adjust the settings
    cu = bpy.data.curves.new('tree', 'CURVE')
    treeOb = bpy.data.objects.new('tree', cu)
    bpy.context.scene.objects.link(treeOb)
    if not armature_settings.useArm:
        treeOb.location=bpy.context.scene.cursor_location

    cu.dimensions = '3D'
    cu.fill_mode = 'FULL'
    cu.bevel_depth = tree_settings.bevelDepth
    cu.bevel_resolution = tree_settings.bevelRes
    cu.use_uv_as_generated = True

    #material slots
    for i in range(max(tree_settings.matIndex)+1):
        treeOb.data.materials.append(None)

    # Fix the scale of the tree now
    scaleVal = tree_settings.scale + uniform(-tree_settings.scaleV, tree_settings.scaleV)
    scaleVal += copysign(1e-6, scaleVal)  # Move away from zero to avoid div by zero

    pruneBase = min(pruneBase, baseSize)
    # If pruning is turned on we need to draw the pruning envelope
    if tree_settings.prune:
        create_pruning_envelope(pruneBase, scaleVal, treeOb, tree_settings)

    # Each of the levels needed by the user we grow all the splines
    childP, levelCount, splineToBone = grow_all_splines(baseSize, baseSize_s, armature_settings.boneStep, cu, leafBaseSize, leaf_settings, scaleVal, tree_settings)

    # If we need to add leaves, we do it here
    leafMesh, leafObj, leafP = add_leafs(childP, leafObj, leaf_settings, treeOb)

    armature_settings.armLevels = min(armature_settings.armLevels, tree_settings.levels)
    armature_settings.armLevels -= 1

    # unpack vars from splineToBone
    splineToBone1 = splineToBone
    splineToBone = [s[0] if len(s) > 1 else s for s in splineToBone1]
    isend = [s[1] if len(s) > 1 else False for s in splineToBone1]
    issplit = [s[2] if len(s) > 2 else False for s in splineToBone1]
    splitPidx = [s[3] if len(s) > 2 else 0 for s in splineToBone1]

    # add mesh object
    treeObj = None
    if armature_settings.makeMesh:
        treeMesh = bpy.data.meshes.new('treemesh')
        treeObj = bpy.data.objects.new('treemesh', treeMesh)
        bpy.context.scene.objects.link(treeObj)
        if not armature_settings.useArm:
            treeObj.location=bpy.context.scene.cursor_location

    # If we need an armature we add it
    if armature_settings.useArm:
        # Create the armature and objects
        armOb = create_armature(armature_settings, leafP, cu, leafMesh, leafObj, leaf_settings.leafVertSize, leaf_settings.leaves, levelCount, splineToBone, treeOb, treeObj)

    #print(time.time()-startTime)

    #mesh branches
    if armature_settings.makeMesh:
        t1 = time.time()

        treeVerts = []
        treeEdges = []
        root_vert = []
        vert_radius = []
        vertexGroups = OrderedDict()
        lastVerts = []

        #vertex group for each level
        levelGroups = []
        for n in range(tree_settings.levels):
            treeObj.vertex_groups.new("Branching Level " + str(n))
            levelGroups.append([])

        for i, curve in enumerate(cu.splines):
            points = curve.bezier_points

            #find branching level
            level = 0
            for l, c in enumerate(levelCount):
                if i < c:
                    level = l
                    break
            level = min(level, 3)

            step = armature_settings.boneStep[level]
            vindex = len(treeVerts)

            p1 = points[0]

            #add extra vertex for splits
            if issplit[i]:
                pb = int(splineToBone[i][4:-4])
                pn = splitPidx[i] #int(splineToBone[i][-3:])
                p_1 = cu.splines[pb].bezier_points[pn]
                p_2 = cu.splines[pb].bezier_points[pn+1]
                p = evalBez(p_1.co, p_1.handle_right, p_2.handle_left, p_2.co, 1 - 1/(tree_settings.resU + 1))
                treeVerts.append(p)

                root_vert.append(False)
                vert_radius.append((p1.radius * .75, p1.radius * .75))
                treeEdges.append([vindex,vindex+1])
                vindex += 1

            if isend[i]:
                parent = lastVerts[int(splineToBone[i][4:-4])]
                vindex -= 1
            else:
                #add first point
                treeVerts.append(p1.co)
                root_vert.append(True)
                vert_radius.append((p1.radius, p1.radius))

            #dont make vertex group if above armLevels
            if (i >= levelCount[armature_settings.armLevels]):
                idx = i
                groupName = splineToBone[idx]
                g = True
                while groupName not in vertexGroups:
                    #find parent bone of parent bone
                    b = splineToBone[idx]
                    idx = int(b[4:-4])
                    groupName = splineToBone[idx]
            else:
                g = False

            for n, p2 in enumerate(points[1:]):
                if not g:
                    groupName = 'bone' + (str(i)).rjust(3, '0') + '.' + (str(n)).rjust(3, '0')
                    groupName = roundBone(groupName, step)
                    if groupName not in vertexGroups:
                        vertexGroups[groupName] = []

                # parent first vert in split to parent branch bone
                if issplit[i] and n == 0:
                    if g:
                        vertexGroups[groupName].append(vindex - 1)
                    else:
                        vertexGroups[splineToBone[i]].append(vindex - 1)
                    levelGroups[level].append(vindex - 1)

                for f in range(1, tree_settings.resU+1):
                    pos = f / tree_settings.resU
                    p = evalBez(p1.co, p1.handle_right, p2.handle_left, p2.co, pos)
                    radius = p1.radius + (p2.radius - p1.radius) * pos

                    treeVerts.append(p)
                    root_vert.append(False)
                    vert_radius.append((radius, radius))

                    if (isend[i]) and (n == 0) and (f == 1):
                        edge = [parent, n * tree_settings.resU + f + vindex]
                    else:
                        edge = [n * tree_settings.resU + f + vindex - 1, n * tree_settings.resU + f + vindex]
                        #add vert to group
                        vertexGroups[groupName].append(n * tree_settings.resU + f + vindex - 1)
                        levelGroups[level].append(n * tree_settings.resU + f + vindex - 1)
                    treeEdges.append(edge)

                vertexGroups[groupName].append(n * tree_settings.resU + tree_settings.resU + vindex)
                levelGroups[level].append(n * tree_settings.resU + tree_settings.resU + vindex)

                p1 = p2

            lastVerts.append(len(treeVerts)-1)

        treeMesh.from_pydata(treeVerts, treeEdges, ())

        if armature_settings.useArm:
            for group in vertexGroups:
                treeObj.vertex_groups.new(group)
                treeObj.vertex_groups[group].add(vertexGroups[group], 1.0, 'ADD')

        for i, g in enumerate(levelGroups):
            treeObj.vertex_groups["Branching Level " + str(i)].add(g, 1.0, 'ADD')

        #add armature
        if armature_settings.useArm:
            armMod = treeObj.modifiers.new('windSway', 'ARMATURE')
            if armature_settings.previewArm:
                armOb.hide = True
                armOb.data.draw_type = 'STICK'
            armMod.object = armOb
            armMod.use_bone_envelopes = False
            armMod.use_vertex_groups = True

        #add skin modifier and set data
        skinMod = treeObj.modifiers.new('Skin', 'SKIN')
        skinMod.use_smooth_shade = True
        if armature_settings.previewArm:
            skinMod.show_viewport = False
        skindata = treeObj.data.skin_vertices[0].data
        for i, radius in enumerate(vert_radius):
            skindata[i].radius = radius
            skindata[i].use_root = root_vert[i]

        print("mesh time", time.time() - t1)


def grow_all_splines(baseSize, baseSize_s, boneStep, cu, leafBaseSize, leaf_settings, scaleVal, tree_settings):
    global splitError
    childP = []
    stemList = []
    levelCount = []
    splineToBone = deque([''])
    addsplinetobone = splineToBone.append
    # Each of the levels needed by the user we grow all the splines
    for n in range(tree_settings.levels):
        storeN = n
        stemList = deque()
        addstem = stemList.append
        # If n is used as an index to access parameters for the tree it must be at most 3 or it will reference outside the array index
        n = min(3, n)
        splitError = 0.0

        # closeTip only on last level
        closeTipp = all([(n == tree_settings.levels - 1), tree_settings.closeTip])

        # If this is the first level of growth (the trunk) then we need some special work to begin the tree
        if n == 0:
            kickstart_trunk(tree_settings, addstem, leaf_settings.leaves, cu, scaleVal)
        # If this isn't the trunk then we may have multiple stem to initialize
        else:
            # For each of the points defined in the list of stem starting points we need to grow a stem.
            fabricate_stems(tree_settings, addsplinetobone, addstem, baseSize, childP, cu, leaf_settings.leafDist, leaf_settings.leaves, leaf_settings.leafType, n, scaleVal, storeN, boneStep)

        # change base size for each level
        if n > 0:
            baseSize *= baseSize_s  # decrease at each level
        if (n == tree_settings.levels - 1):
            baseSize = leafBaseSize

        childP = []
        # Now grow each of the stems in the list of those to be extended
        for st in stemList:
            # Now do the iterative pruning, this uses a binary search and halts once the difference between upper and lower bounds of the search are less than 0.005
            tree_settings.ratio, splineToBone = perform_pruning(tree_settings, baseSize, childP, cu, n, scaleVal, splineToBone, st, closeTipp, boneStep, leaf_settings.leaves, leaf_settings.leafType)

        levelCount.append(len(cu.splines))
    return childP, levelCount, splineToBone


def add_leafs(childP, leafObj, leaf_settings, treeOb):
    leafVerts = []
    leafFaces = []
    leafNormals = []
    leafMesh = None  # in case we aren't creating leaves, we'll still have the variable
    leafP = []
    if leaf_settings.leaves:
        oldRot = 0.0
        # n = min(3, n+1)
        # For each of the child points we add leaves
        for ln, cp in enumerate(childP):
            # If the special flag is set then we need to add several leaves at the same location
            if leaf_settings.leafType == '4':
                oldRot = -leaf_settings.leafRotate / 2
                for g in range(abs(leaf_settings.leaves)):
                    (vertTemp, faceTemp, normal, oldRot) = gen_leaf_mesh(leaf_settings, cp.co, cp.quat, cp.offset,
                                                                         len(leafVerts), oldRot, ln)
                    leafVerts.extend(vertTemp)
                    leafFaces.extend(faceTemp)
                    leafNormals.extend(normal)
                    leafP.append(cp)
            # Otherwise just add the leaves like splines.
            else:
                (vertTemp, faceTemp, normal, oldRot) = gen_leaf_mesh(leaf_settings, cp.co, cp.quat, cp.offset,
                                                                     len(leafVerts), oldRot, ln)
                leafVerts.extend(vertTemp)
                leafFaces.extend(faceTemp)
                leafNormals.extend(normal)
                leafP.append(cp)

        # Create the leaf mesh and object, add geometry using from_pydata, edges are currently added by validating the mesh which isn't great
        leafMesh = bpy.data.meshes.new('leaves')
        leafObj = bpy.data.objects.new('leaves', leafMesh)
        bpy.context.scene.objects.link(leafObj)
        leafObj.parent = treeOb
        leafMesh.from_pydata(leafVerts, (), leafFaces)

        # set vertex normals for dupliVerts
        if leaf_settings.leafShape == 'dVert':
            leafMesh.vertices.foreach_set('normal', leafNormals)

        # enable duplication
        if leaf_settings.leafShape == 'dFace':
            leafObj.dupli_type = "FACES"
            leafObj.use_dupli_faces_scale = True
            leafObj.dupli_faces_scale = 10.0
            try:
                bpy.data.objects[leaf_settings.leafDupliObj].parent = leafObj
            except KeyError:
                pass
        elif leaf_settings.leafShape == 'dVert':
            leafObj.dupli_type = "VERTS"
            leafObj.use_dupli_vertices_rotation = True
            try:
                bpy.data.objects[leaf_settings.leafDupliObj].parent = leafObj
            except KeyError:
                pass

        # add leaf UVs
        if leaf_settings.leafShape == 'rect':
            leafMesh.uv_textures.new("leafUV")
            uvlayer = leafMesh.uv_layers.active.data

            u1 = .5 * (1 - leaf_settings.leafScaleX)
            u2 = 1 - u1

            for i in range(0, len(leafFaces)):
                uvlayer[i * 4 + 0].uv = Vector((u2, 0))
                uvlayer[i * 4 + 1].uv = Vector((u2, 1))
                uvlayer[i * 4 + 2].uv = Vector((u1, 1))
                uvlayer[i * 4 + 3].uv = Vector((u1, 0))

        elif leaf_settings.leafShape == 'hex':
            leafMesh.uv_textures.new("leafUV")
            uvlayer = leafMesh.uv_layers.active.data

            u1 = .5 * (1 - leaf_settings.leafScaleX)
            u2 = 1 - u1

            for i in range(0, int(len(leafFaces) / 2)):
                uvlayer[i * 8 + 0].uv = Vector((.5, 0))
                uvlayer[i * 8 + 1].uv = Vector((u1, 1 / 3))
                uvlayer[i * 8 + 2].uv = Vector((u1, 2 / 3))
                uvlayer[i * 8 + 3].uv = Vector((.5, 1))

                uvlayer[i * 8 + 4].uv = Vector((.5, 0))
                uvlayer[i * 8 + 5].uv = Vector((.5, 1))
                uvlayer[i * 8 + 6].uv = Vector((u2, 2 / 3))
                uvlayer[i * 8 + 7].uv = Vector((u2, 1 / 3))

        leafMesh.validate()
    return leafMesh, leafObj, leafP

def create_pruning_envelope(pruneBase, scaleVal, treeOb, tree_settings):
    enHandle = 'VECTOR'
    enNum = 128
    enCu = bpy.data.curves.new('envelope', 'CURVE')
    enOb = bpy.data.objects.new('envelope', enCu)
    enOb.parent = treeOb
    bpy.context.scene.objects.link(enOb)
    newSpline = enCu.splines.new('BEZIER')
    newPoint = newSpline.bezier_points[-1]
    newPoint.co = Vector((0, 0, scaleVal))
    (newPoint.handle_right_type, newPoint.handle_left_type) = (enHandle, enHandle)
    # Set the coordinates by varying the z value, envelope will be aligned to the x-axis
    for c in range(enNum):
        newSpline.bezier_points.add()
        newPoint = newSpline.bezier_points[-1]
        ratioVal = (c + 1) / (enNum)
        zVal = scaleVal - scaleVal * (1 - pruneBase) * ratioVal
        newPoint.co = Vector((scaleVal * tree_settings.pruneWidth * shape_ratio(9, ratioVal,
                                                                                tree_settings.pruneWidthPeak,
                                                                                tree_settings.prunePowerHigh,
                                                                                tree_settings.prunePowerLow), 0, zVal))
        (newPoint.handle_right_type, newPoint.handle_left_type) = (enHandle, enHandle)
    newSpline = enCu.splines.new('BEZIER')
    newPoint = newSpline.bezier_points[-1]
    newPoint.co = Vector((0, 0, scaleVal))
    (newPoint.handle_right_type, newPoint.handle_left_type) = (enHandle, enHandle)
    # Create a second envelope but this time on the y-axis
    for c in range(enNum):
        newSpline.bezier_points.add()
        newPoint = newSpline.bezier_points[-1]
        ratioVal = (c + 1) / (enNum)
        zVal = scaleVal - scaleVal * (1 - pruneBase) * ratioVal
        newPoint.co = Vector((0, scaleVal * tree_settings.pruneWidth * shape_ratio(9, ratioVal,
                                                                                   tree_settings.pruneWidthPeak,
                                                                                   tree_settings.prunePowerHigh,
                                                                                   tree_settings.prunePowerLow), zVal))
        (newPoint.handle_right_type, newPoint.handle_left_type) = (enHandle, enHandle)
