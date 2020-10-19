import copy
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
from .leaf_rot import leaf_rot



def add_tree(props):
    global splitError
    #startTime = time.time()
    # Set the seed for repeatable results
    seed(props.seed)#

    # Set all other variables
    levels = props.levels#
    length = props.length#
    lengthV = props.lengthV#
    taperCrown = props.taperCrown
    branches = props.branches#
    curveRes = props.curveRes#
    curve = toRad(props.curve)#
    curveV = toRad(props.curveV)#
    curveBack = toRad(props.curveBack)#
    baseSplits = props.baseSplits#
    segSplits = props.segSplits#
    splitByLen = props.splitByLen
    rMode = props.rMode
    splitStraight = props.splitStraight
    splitLength = props.splitLength
    splitAngle = toRad(props.splitAngle)#
    splitAngleV = toRad(props.splitAngleV)#
    scale = props.scale#
    scaleV = props.scaleV#
    attractUp = props.attractUp#
    attractOut = props.attractOut
    shape = int(props.shape)#
    shapeS = int(props.shapeS)#
    customShape = props.customShape
    branchDist = props.branchDist
    nrings = props.nrings
    baseSize = props.baseSize
    baseSize_s = props.baseSize_s
    leafBaseSize = props.leafBaseSize
    splitHeight = props.splitHeight
    splitBias = props.splitBias
    ratio = props.ratio
    minRadius = props.minRadius
    closeTip = props.closeTip
    rootFlare = props.rootFlare
    splitRadiusRatio = props.splitRadiusRatio
    autoTaper = props.autoTaper
    taper = props.taper#
    noTip = props.noTip
    radiusTweak = props.radiusTweak
    ratioPower = props.ratioPower#
    downAngle = toRad(props.downAngle)#
    downAngleV = toRad(props.downAngleV)#
    rotate = toRad(props.rotate)#
    rotateV = toRad(props.rotateV)#
    scale0 = props.scale0#
    scaleV0 = props.scaleV0#
    prune = props.prune#
    pruneWidth = props.pruneWidth#
    pruneBase = props.pruneBase
    pruneWidthPeak = props.pruneWidthPeak#
    prunePowerLow = props.prunePowerLow#
    prunePowerHigh = props.prunePowerHigh#
    pruneRatio = props.pruneRatio#
    leafType = props.leafType
    leafDownAngle = radians(props.leafDownAngle)
    leafDownAngleV = radians(props.leafDownAngleV)
    leafRotate = radians(props.leafRotate)
    leafRotateV = radians(props.leafRotateV)
    leafScale = props.leafScale#
    leafScaleX = props.leafScaleX#
    leafScaleT = props.leafScaleT
    leafScaleV = props.leafScaleV
    leafShape = props.leafShape
    leafDupliObj = props.leafDupliObj
    leafangle = props.leafangle
    horzLeaves = props.horzLeaves
    leafDist = int(props.leafDist)#
    bevelRes = props.bevelRes#
    resU = props.resU#

    #leafObjX = props.leafObjX
    leafObjY = props.leafObjY
    leafObjZ = props.leafObjZ

    useArm = props.useArm
    previewArm = props.previewArm
    armAnim = props.armAnim
    leafAnim = props.leafAnim
    frameRate = props.frameRate
    loopFrames = props.loopFrames

    #windSpeed = props.windSpeed
    #windGust = props.windGust

    wind = props.wind
    gust = props.gust
    gustF = props.gustF

    af1 = props.af1
    af2 = props.af2
    af3 = props.af3

    makeMesh = props.makeMesh
    armLevels = props.armLevels
    boneStep = props.boneStep
    matIndex = props.matIndex

    useOldDownAngle = props.useOldDownAngle
    useParentAngle = props.useParentAngle

    if not makeMesh:
        boneStep = [1, 1, 1, 1]

    #taper
    if autoTaper:
        taper = find_taper(length, taper, shape, shapeS, levels, customShape)

    leafObj = None

    leafObjRot = leaf_rot(leafObjY, leafObjZ)

    # Some effects can be turned ON and OFF, the necessary variables are changed here
    if not props.bevel:
        bevelDepth = 0.0
    else:
        bevelDepth = 1.0

    if not props.showLeaves:
        leaves = 0
    else:
        leaves = props.leaves

    if props.handleType == '0':
        handles = 'AUTO'
    else:
        handles = 'VECTOR'

    for ob in bpy.data.objects:
        ob.select_set(state=False)

    # Initialise the tree object and curve and adjust the settings
    cu = bpy.data.curves.new('tree', 'CURVE')
    treeOb = bpy.data.objects.new('tree', cu)
    bpy.context.scene.collection.objects.link(treeOb)
    if not useArm:
        treeOb.location=bpy.context.scene.cursor.location

    cu.dimensions = '3D'
    cu.fill_mode = 'FULL'
    cu.bevel_depth = bevelDepth
    cu.bevel_resolution = bevelRes
    # cu.use_uv_as_generated = True # removed 2.82

    #material slots
    for i in range(max(matIndex)+1):
        treeOb.data.materials.append(None)

    # Fix the scale of the tree now
    scaleVal = scale + uniform(-scaleV, scaleV)
    scaleVal += copysign(1e-6, scaleVal)  # Move away from zero to avoid div by zero

    pruneBase = min(pruneBase, baseSize)
    # If pruning is turned on we need to draw the pruning envelope
    if prune:
        enHandle = 'VECTOR'
        enNum = 128
        enCu = bpy.data.curves.new('envelope', 'CURVE')
        enOb = bpy.data.objects.new('envelope', enCu)
        enOb.parent = treeOb
        bpy.context.scene.collection.objects.link(enOb)
        newSpline = enCu.splines.new('BEZIER')
        newPoint = newSpline.bezier_points[-1]
        newPoint.co = Vector((0, 0, scaleVal))
        (newPoint.handle_right_type, newPoint.handle_left_type) = (enHandle, enHandle)
        # Set the coordinates by varying the z value, envelope will be aligned to the x-axis
        for c in range(enNum):
            newSpline.bezier_points.add(1)
            newPoint = newSpline.bezier_points[-1]
            ratioVal = (c+1)/(enNum)
            zVal = scaleVal - scaleVal*(1-pruneBase)*ratioVal
            newPoint.co = Vector((scaleVal * pruneWidth * shape_ratio(9, ratioVal, pruneWidthPeak, prunePowerHigh, prunePowerLow), 0, zVal))
            (newPoint.handle_right_type, newPoint.handle_left_type) = (enHandle, enHandle)
        newSpline = enCu.splines.new('BEZIER')
        newPoint = newSpline.bezier_points[-1]
        newPoint.co = Vector((0, 0, scaleVal))
        (newPoint.handle_right_type, newPoint.handle_left_type) = (enHandle, enHandle)
        # Create a second envelope but this time on the y-axis
        for c in range(enNum):
            newSpline.bezier_points.add(1)
            newPoint = newSpline.bezier_points[-1]
            ratioVal = (c+1)/(enNum)
            zVal = scaleVal - scaleVal*(1-pruneBase)*ratioVal
            newPoint.co = Vector((0, scaleVal * pruneWidth * shape_ratio(9, ratioVal, pruneWidthPeak, prunePowerHigh, prunePowerLow), zVal))
            (newPoint.handle_right_type, newPoint.handle_left_type) = (enHandle, enHandle)


    childP = []
    stemList = []

    levelCount = []
    splineToBone = deque([''])
    addsplinetobone = splineToBone.append

    # Each of the levels needed by the user we grow all the splines
    for n in range(levels):
        storeN = n
        stemList = deque()
        addstem = stemList.append
        # If n is used as an index to access parameters for the tree it must be at most 3 or it will reference outside the array index
        n = min(3, n)
        splitError = 0.0

        #closeTip only on last level
        closeTipp = all([(n == levels-1), closeTip])

        # If this is the first level of growth (the trunk) then we need some special work to begin the tree
        if n == 0:
            kickstart_trunk(addstem, levels, leaves, branches, cu, downAngle, downAngleV, curve, curveRes, curveV, attractUp,
                            length, lengthV, ratio, ratioPower, resU, scale0, scaleV0, scaleVal, taper, minRadius, rootFlare, matIndex)
        # If this isn't the trunk then we may have multiple stem to initialize
        else:
            # For each of the points defined in the list of stem starting points we need to grow a stem.
            fabricate_stems(addsplinetobone, addstem, baseSize, branches, childP, cu, curve, curveBack,
                            curveRes, curveV, attractUp, downAngle, downAngleV, leafDist, leaves, leafType, length, lengthV,
                            levels, n, ratio, ratioPower, resU, rotate, rotateV, scaleVal, shape, storeN,
                            taper, shapeS, minRadius, radiusTweak, customShape, rMode, segSplits,
                            useOldDownAngle, useParentAngle, boneStep, matIndex)

        #change base size for each level
        if n > 0:
            baseSize *= baseSize_s #decrease at each level
        if (n == levels - 1):
            baseSize = leafBaseSize

        childP = []
        # Now grow each of the stems in the list of those to be extended
        for st in stemList:
            # When using pruning, we need to ensure that the random effects will be the same for each iteration to make sure the problem is linear.
            randState = getstate()
            startPrune = True
            lengthTest = 0.0
            # Store all the original values for the stem to make sure we have access after it has been modified by pruning
            originalLength = st.segL
            originalCurv = st.curv
            originalCurvV = st.curvV
            originalSeg = st.seg
            originalHandleR = st.p.handle_right.copy()
            originalHandleL = st.p.handle_left.copy()
            originalCo = st.p.co.copy()
            currentMax = 1.0
            currentMin = 0.0
            currentScale = 1.0
            oldMax = 1.0
            deleteSpline = False
            originalSplineToBone = copy.copy(splineToBone)
            forceSprout = False
            # Now do the iterative pruning, this uses a binary search and halts once the difference between upper and lower bounds of the search are less than 0.005
            ratio, splineToBone = perform_pruning(baseSize, baseSplits, childP, cu, currentMax, currentMin,
                                                  currentScale, curve, curveBack, curveRes, deleteSpline, forceSprout,
                                                  handles, n, levels, branches, oldMax, originalSplineToBone, originalCo, originalCurv,
                                                  originalCurvV, originalHandleL, originalHandleR, originalLength,
                                                  originalSeg, prune, prunePowerHigh, prunePowerLow, pruneRatio,
                                                  pruneWidth, pruneBase, pruneWidthPeak, randState, ratio, scaleVal, segSplits,
                                                  splineToBone, splitAngle, splitAngleV, st, startPrune,
                                                  branchDist, length, splitByLen, closeTipp, splitRadiusRatio, minRadius, nrings, splitBias, splitHeight,
                                                  attractOut, rMode, splitStraight, splitLength, lengthV, taperCrown, noTip, boneStep, rotate, rotateV, leaves, leafType, matIndex)

        levelCount.append(len(cu.splines))

    cu.resolution_u = resU

    # If we need to add leaves, we do it here
    leafVerts = []
    leafFaces = []
    leafNormals = []

    leafMesh = None # in case we aren't creating leaves, we'll still have the variable

    leafP = []
    if leaves:
        oldRot = 0.0
        n = min(3, n+1)
        # For each of the child points we add leaves
        for ln, cp in enumerate(childP):
            # If the special flag is set then we need to add several leaves at the same location
            if leafType == '4':
                oldRot = -leafRotate / 2
                for g in range(abs(leaves)):
                    (vertTemp, faceTemp, normal, oldRot) = gen_leaf_mesh(leafScale, leafScaleX, leafScaleT, leafScaleV, cp.co, cp.quat, cp.offset,
                                                                         len(leafVerts), leafDownAngle, leafDownAngleV, leafRotate, leafRotateV,
                                                                         oldRot, leaves, leafShape, leafangle, horzLeaves, leafType, ln, leafObjRot)
                    leafVerts.extend(vertTemp)
                    leafFaces.extend(faceTemp)
                    leafNormals.extend(normal)
                    leafP.append(cp)
            # Otherwise just add the leaves like splines.
            else:
                (vertTemp, faceTemp, normal, oldRot) = gen_leaf_mesh(leafScale, leafScaleX, leafScaleT, leafScaleV, cp.co, cp.quat, cp.offset,
                                                                     len(leafVerts), leafDownAngle, leafDownAngleV, leafRotate, leafRotateV,
                                                                     oldRot, leaves, leafShape, leafangle, horzLeaves, leafType, ln, leafObjRot)
                leafVerts.extend(vertTemp)
                leafFaces.extend(faceTemp)
                leafNormals.extend(normal)
                leafP.append(cp)

        # Create the leaf mesh and object, add geometry using from_pydata, edges are currently added by validating the mesh which isn't great
        leafMesh = bpy.data.meshes.new('leaves')
        leafObj = bpy.data.objects.new('leaves', leafMesh)
        bpy.context.scene.collection.objects.link(leafObj)
        leafObj.parent = treeOb
        leafMesh.from_pydata(leafVerts, (), leafFaces)

        #set vertex normals for dupliVerts
        if leafShape == 'dVert':
            leafMesh.vertices.foreach_set('normal', leafNormals)

        # enable duplication
        if leafShape == 'dFace':
            leafObj.instance_type = "FACES"
            leafObj.use_instance_faces_scale = True
            leafObj.instance_faces_scale = 10.0
            try:
                bpy.data.objects[leafDupliObj].parent = leafObj
            except KeyError:
                pass
        elif leafShape == 'dVert':
            leafObj.instance_type = "VERTS"
            leafObj.use_instance_vertices_rotation = True
            try:
                bpy.data.objects[leafDupliObj].parent = leafObj
            except KeyError:
                pass

        #add leaf UVs
        if leafShape == 'rect':
            leafMesh.uv_layers.new(name="leafUV")
            uvlayer = leafMesh.uv_layers.active.data

            u1 = .5 * (1 - leafScaleX)
            u2 = 1 - u1

            for i in range(0, len(leafFaces)):
                uvlayer[i*4 + 0].uv = Vector((u2, 0))
                uvlayer[i*4 + 1].uv = Vector((u2, 1))
                uvlayer[i*4 + 2].uv = Vector((u1, 1))
                uvlayer[i*4 + 3].uv = Vector((u1, 0))

        elif leafShape == 'hex':
            leafMesh.uv_layers.new(name="leafUV")
            uvlayer = leafMesh.uv_layers.active.data

            u1 = .5 * (1 - leafScaleX)
            u2 = 1 - u1

            for i in range(0, int(len(leafFaces) / 2)):
                uvlayer[i*8 + 0].uv = Vector((.5, 0))
                uvlayer[i*8 + 1].uv = Vector((u1, 1/3))
                uvlayer[i*8 + 2].uv = Vector((u1, 2/3))
                uvlayer[i*8 + 3].uv = Vector((.5, 1))

                uvlayer[i*8 + 4].uv = Vector((.5, 0))
                uvlayer[i*8 + 5].uv = Vector((.5, 1))
                uvlayer[i*8 + 6].uv = Vector((u2, 2/3))
                uvlayer[i*8 + 7].uv = Vector((u2, 1/3))

        leafMesh.validate()

    leafVertSize = {'hex': 6, 'rect': 4, 'dFace': 4, 'dVert': 1}[leafShape]

    armLevels = min(armLevels, levels)
    armLevels -= 1

    # unpack vars from splineToBone
    splineToBone1 = splineToBone
    splineToBone = [s[0] if len(s) > 1 else s for s in splineToBone1]
    isend = [s[1] if len(s) > 1 else False for s in splineToBone1]
    issplit = [s[2] if len(s) > 2 else False for s in splineToBone1]
    splitPidx = [s[3] if len(s) > 2 else 0 for s in splineToBone1]

    # add mesh object
    treeObj = None
    if makeMesh:
        treeMesh = bpy.data.meshes.new('treemesh')
        treeObj = bpy.data.objects.new('treemesh', treeMesh)
        bpy.context.scene.collection.objects.link(treeObj)
        if not useArm:
            treeObj.location=bpy.context.scene.cursor.location

    # If we need an armature we add it
    if useArm:
        # Create the armature and objects
        armOb = create_armature(armAnim, leafP, cu, frameRate, leafMesh, leafObj, leafVertSize, leaves, levelCount, splineToBone,
                                treeOb, treeObj, wind, gust, gustF, af1, af2, af3, leafAnim, loopFrames, previewArm, armLevels, makeMesh, boneStep)

    #print(time.time()-startTime)

    #mesh branches
    if makeMesh:
        t1 = time.time()

        treeVerts = []
        treeEdges = []
        root_vert = []
        vert_radius = []
        vertexGroups = OrderedDict()
        lastVerts = []

        #vertex group for each level
        levelGroups = []
        for n in range(levels):
            treeObj.vertex_groups.new(name="Branching Level " + str(n))
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

            step = boneStep[level]
            vindex = len(treeVerts)

            p1 = points[0]

            #add extra vertex for splits
            if issplit[i]:
                pb = int(splineToBone[i][4:-4])
                pn = splitPidx[i] #int(splineToBone[i][-3:])
                p_1 = cu.splines[pb].bezier_points[pn]
                p_2 = cu.splines[pb].bezier_points[pn+1]
                p = evalBez(p_1.co, p_1.handle_right, p_2.handle_left, p_2.co, 1 - 1/(resU + 1))
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
            if (i >= levelCount[armLevels]):
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

                for f in range(1, resU+1):
                    pos = f / resU
                    p = evalBez(p1.co, p1.handle_right, p2.handle_left, p2.co, pos)
                    radius = p1.radius + (p2.radius - p1.radius) * pos

                    treeVerts.append(p)
                    root_vert.append(False)
                    vert_radius.append((radius, radius))

                    if (isend[i]) and (n == 0) and (f == 1):
                        edge = [parent, n * resU + f + vindex]
                    else:
                        edge = [n * resU + f + vindex - 1, n * resU + f + vindex]
                        #add vert to group
                        vertexGroups[groupName].append(n * resU + f + vindex - 1)
                        levelGroups[level].append(n * resU + f + vindex - 1)
                    treeEdges.append(edge)

                vertexGroups[groupName].append(n * resU + resU + vindex)
                levelGroups[level].append(n * resU + resU + vindex)

                p1 = p2

            lastVerts.append(len(treeVerts)-1)

        treeMesh.from_pydata(treeVerts, treeEdges, ())

        if useArm:
            for group in vertexGroups:
                treeObj.vertex_groups.new(name=group)
                treeObj.vertex_groups[group].add(vertexGroups[group], 1.0, 'ADD')

        for i, g in enumerate(levelGroups):
            treeObj.vertex_groups["Branching Level " + str(i)].add(g, 1.0, 'ADD')

        #add armature
        if useArm:
            armMod = treeObj.modifiers.new('windSway', 'ARMATURE')
            if previewArm:
                armOb.hide_viewport = True
                armOb.data.display_type = 'STICK'
            armMod.object = armOb
            armMod.use_bone_envelopes = False
            armMod.use_vertex_groups = True

        #add skin modifier and set data
        skinMod = treeObj.modifiers.new('Skin', 'SKIN')
        skinMod.use_smooth_shade = True
        if previewArm:
            skinMod.show_viewport = False
        skindata = treeObj.data.skin_vertices[0].data
        for i, radius in enumerate(vert_radius):
            skindata[i].radius = radius
            skindata[i].use_root = root_vert[i]

        print("mesh time", time.time() - t1)