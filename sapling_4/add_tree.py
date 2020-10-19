import time
from collections import deque, OrderedDict
from math import copysign
from random import seed, uniform

import bpy

from .ArmatureSettings import ArmatureSettings
from .LeafSettings import LeafSettings
from .TreeSettings import TreeSettings
from .add_leafs import add_leafs
from .utils import eval_bez, round_bone
from .kickstart_trunk import kickstart_trunk
from .fabricate_stems import fabricate_stems
from .grow_branch_level import grow_branch_level
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

    bevelRes = props.bevelRes#
    resU = props.resU#

    #leafObjX = props.leafObjX
    leafObjY = props.leafObjY
    leafObjZ = props.leafObjZ

    armature_settings = ArmatureSettings(props)

    matIndex = props.matIndex

    useOldDownAngle = props.useOldDownAngle
    useParentAngle = props.useParentAngle

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
    if not armature_settings.useArm:
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
            fabricate_stems(tree_settings, addsplinetobone, addstem, baseSize, childP, cu, leaf_settings.leafDist, leaves, leaf_settings.leafType, lvl, scaleVal, storeN, useOldDownAngle, useParentAngle, armature_settings.boneStep, matIndex)

        #change base size for each level
        if lvl > 0:
            baseSize = tree_settings.baseSize_s
        if (lvl == tree_settings.levels - 1):
            baseSize = tree_settings.leafBaseSize

        childP = []
        # Now grow each of the stems in the list of those to be extended
        for st in stemList:
            splineToBone = grow_branch_level(tree_settings, baseSize, childP, cu, handles, lvl, scaleVal, splineToBone, st, closeTipp, noTip, armature_settings.boneStep, leaves, leaf_settings.leafType, attachment, matIndex)

        levelCount.append(len(cu.splines))

    # Set curve resolution
    cu.resolution_u = resU

    # If we need to add leaves, we do it here
    leafMesh, leafObj, leafP, leafVertSize = add_leafs(childP, leafObj, leafObjRot, leaf_settings, leaves, lvl, treeOb)

    armature_settings.armLevels = min(armature_settings.armLevels, tree_settings.levels)
    armature_settings.armLevels -= 1

    # unpack vars from splineToBone
    splineToBone1 = splineToBone
    splineToBone = [s[0] if len(s) > 1 else s for s in splineToBone1]

    # add mesh object
    treeObj = None
    if armature_settings.makeMesh:
        treeMesh = bpy.data.meshes.new('treemesh')
        treeObj = bpy.data.objects.new('treemesh', treeMesh)
        bpy.context.scene.collection.objects.link(treeObj)
        if not armature_settings.useArm:
            treeObj.location=bpy.context.scene.cursor.location

    # If we need an armature we add it
    if armature_settings.useArm:
        # Create the armature and objects
        armOb = create_armature(armature_settings, leafP, cu, leafMesh, leafObj, leafVertSize, leaves, levelCount, splineToBone, treeOb, treeObj)

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

            step = armature_settings.boneStep[level]
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

        if armature_settings.useArm:
            for group in vertexGroups:
                treeObj.vertex_groups.new(name=group)
                treeObj.vertex_groups[group].add(vertexGroups[group], 1.0, 'ADD')

        for i, g in enumerate(levelGroups):
            treeObj.vertex_groups["Branching Level " + str(i)].add(g, 1.0, 'ADD')

        #add armature
        if armature_settings.useArm:
            armMod = treeObj.modifiers.new('windSway', 'ARMATURE')
            if armature_settings.previewArm:
                armOb.hide_viewport = True
                armOb.data.display_type = 'STICK'
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