import time
from collections import deque, OrderedDict
from math import radians, copysign
from random import seed, uniform

import bpy
from mathutils import Vector

from .LeafSettings import LeafSettings
from .TreeSettings import TreeSettings
from .utils import to_rad, eval_bez, round_bone
from .kickstart_trunk import kickstart_trunk
from .fabricate_stems import fabricate_stems
from .grow_branch_level import grow_branch_level
from .gen_leaf_mesh import gen_leaf_mesh
from .create_armature import create_armature
from .leaf_rot import leaf_rot
from .find_taper import find_taper


def add_tree(props):
    global splitError
    #startTime = time.time()
    # Set the seed for repeatable results
    rseed = props.seed
    seed(rseed)

    # Set all other variables
    tree_settings = TreeSettings(props)
    scaleV = props.scaleV#
    baseSize = props.baseSize
    noTip = props.noTip
    attachment = props.attachment

    leaf_settings = LeafSettings(props)
    # leafType = props.leafType
    # leafDownAngle = radians(props.leafDownAngle)
    # leafDownAngleV = radians(props.leafDownAngleV)
    # leafRotate = radians(props.leafRotate)
    # leafRotateV = radians(props.leafRotateV)
    # leafScale = props.leafScale#
    # leafScaleX = props.leafScaleX#
    # leafScaleT = props.leafScaleT
    # leafScaleV = props.leafScaleV
    # leafShape = props.leafShape
    # leafDupliObj = props.leafDupliObj
    # leafangle = props.leafangle
    # leafDist = int(props.leafDist)#
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
    if tree_settings.autoTaper:
        tree_settings.taper = find_taper(tree_settings)

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
    #cu.use_uv_as_generated = True # removed 2.82

    #material slots
    for i in range(max(matIndex)+1):
        treeOb.data.materials.append(None)

    # Fix the scale of the tree now
    if rseed == 0: #first tree is always average size
        scaleV = 0
    scaleVal = tree_settings.scale + uniform(-scaleV, scaleV)
    scaleVal += copysign(1e-6, scaleVal)  # Move away from zero to avoid div by zero

    childP = []
    stemList = []

    levelCount = []
    splineToBone = deque([''])
    addsplinetobone = splineToBone.append

    # Each of the levels needed by the user we grow all the splines
    for lvl in range(tree_settings.levels):
        storeN = lvl
        stemList = deque()
        addstem = stemList.append
        # If lvl is used as an index to access parameters for the tree it must be at most 3 or it will reference outside the array index
        lvl = min(3, lvl)
        splitError = 0.0

        #closeTip only on last level
        closeTipp = all([(lvl == tree_settings.levels-1), tree_settings.closeTip])

        # If this is the first level of growth (the trunk) then we need some special work to begin the tree
        if lvl == 0:
            kickstart_trunk(tree_settings, addstem, leaves, cu, scaleVal, matIndex)
        # If this isn't the trunk then we may have multiple stem to initialize
        else:
            # For each of the points defined in the list of stem starting points we need to grow a stem.
            fabricate_stems(tree_settings, addsplinetobone, addstem, baseSize, childP, cu, leaf_settings.leafDist, leaves, leaf_settings.leafType, lvl, scaleVal, storeN, useOldDownAngle, useParentAngle, boneStep, matIndex)

        #change base size for each level
        if lvl > 0:
            baseSize = tree_settings.baseSize_s
        if (lvl == tree_settings.levels - 1):
            baseSize = tree_settings.leafBaseSize

        childP = []
        # Now grow each of the stems in the list of those to be extended
        for st in stemList:
            splineToBone = grow_branch_level(tree_settings, baseSize, childP, cu, handles, lvl, scaleVal, splineToBone, st, closeTipp, noTip, boneStep, leaves, leaf_settings.leafType, attachment, matIndex)

        levelCount.append(len(cu.splines))

    # Set curve resolution
    cu.resolution_u = resU

    # If we need to add leaves, we do it here
    leafVerts = []
    leafFaces = []
    leafNormals = []

    leafMesh = None # in case we aren't creating leaves, we'll still have the variable

    leafP = []
    if leaves:
        oldRot = 0.0
        lvl = min(3, lvl+1)
        # For each of the child points we add leaves
        for ln, cp in enumerate(childP):
            # If the special flag is set then we need to add several leaves at the same location
            if leaf_settings.leafType == '4':
                oldRot = -leaf_settings.leafRotate / 2
                for g in range(abs(leaves)):
                    (vertTemp, faceTemp, normal, oldRot) = gen_leaf_mesh(leaf_settings, cp.co, cp.quat, cp.offset, len(leafVerts), oldRot, leaves, ln, leafObjRot)
                    leafVerts.extend(vertTemp)
                    leafFaces.extend(faceTemp)
                    leafNormals.extend(normal)
                    leafP.append(cp)
            # Otherwise just add the leaves like splines.
            else:
                (vertTemp, faceTemp, normal, oldRot) = gen_leaf_mesh(leaf_settings, cp.co, cp.quat, cp.offset, len(leafVerts), oldRot, leaves, ln, leafObjRot)
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
        if leaf_settings.leafShape == 'dVert':
            leafMesh.vertices.foreach_set('normal', leafNormals)

        # enable duplication
        if leaf_settings.leafShape == 'dFace':
            leafObj.instance_type = "FACES"
            leafObj.use_instance_faces_scale = True
            leafObj.instance_faces_scale = 10.0
            try:
                bpy.data.objects[leaf_settings.leafDupliObj].parent = leafObj
            except KeyError:
                pass
        elif leaf_settings.leafShape == 'dVert':
            leafObj.instance_type = "VERTS"
            leafObj.use_instance_vertices_rotation = True
            try:
                bpy.data.objects[leaf_settings.leafDupliObj].parent = leafObj
            except KeyError:
                pass

        #add leaf UVs
        if leaf_settings.leafShape == 'rect':
            leafMesh.uv_layers.new(name="leafUV")
            uvlayer = leafMesh.uv_layers.active.data

            u1 = .5 * (1 - leaf_settings.leafScaleX)
            u2 = 1 - u1

            for i in range(0, len(leafFaces)):
                uvlayer[i*4 + 0].uv = Vector((u2, 0))
                uvlayer[i*4 + 1].uv = Vector((u2, 1))
                uvlayer[i*4 + 2].uv = Vector((u1, 1))
                uvlayer[i*4 + 3].uv = Vector((u1, 0))

        elif leaf_settings.leafShape == 'hex':
            leafMesh.uv_layers.new(name="leafUV")
            uvlayer = leafMesh.uv_layers.active.data

            u1 = .5 * (1 - leaf_settings.leafScaleX)
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

    leafVertSize = {'hex': 6, 'rect': 4, 'dFace': 4, 'dVert': 1}[leaf_settings.leafShape]

    armLevels = min(armLevels, tree_settings.levels)
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
        for lvl in range(tree_settings.levels):
            treeObj.vertex_groups.new(name="Branching Level " + str(lvl))
            levelGroups.append([])

        for i, tree_settings.curve in enumerate(cu.splines):
            points = tree_settings.curve.bezier_points

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
                p = eval_bez(p_1.co, p_1.handle_right, p_2.handle_left, p_2.co, 1 - 1 / (resU + 1))
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
                        vertexGroups[splineToBone[i]].append(vindex - 1)
                    levelGroups[level].append(vindex - 1)

                for f in range(1, resU+1):
                    pos = f / resU
                    p = eval_bez(p1.co, p1.handle_right, p2.handle_left, p2.co, pos)
                    radius = p1.radius + (p2.radius - p1.radius) * pos

                    treeVerts.append(p)
                    root_vert.append(False)
                    vert_radius.append((radius, radius))

                    if (isend[i]) and (lvl == 0) and (f == 1):
                        edge = [parent, lvl * resU + f + vindex]
                    else:
                        edge = [lvl * resU + f + vindex - 1, lvl * resU + f + vindex]
                        #add vert to group
                        vertexGroups[groupName].append(lvl * resU + f + vindex - 1)
                        levelGroups[level].append(lvl * resU + f + vindex - 1)
                    treeEdges.append(edge)

                vertexGroups[groupName].append(lvl * resU + resU + vindex)
                levelGroups[level].append(lvl * resU + resU + vindex)

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