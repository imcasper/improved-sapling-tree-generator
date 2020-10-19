from collections import deque
from math import copysign
from random import seed, uniform

import bpy

from .ArmatureSettings import ArmatureSettings
from .LeafSettings import LeafSettings
from .TreeSettings import TreeSettings
from .add_leafs import add_leafs
from .make_armature_mesh import make_armature_mesh
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

    armature_settings = ArmatureSettings(props)

    #taper
    if tree_settings.autoTaper:
        tree_settings.taper = find_taper(tree_settings)

    leafObj = None

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
    cu.bevel_depth = tree_settings.bevelDepth
    cu.bevel_resolution = tree_settings.bevelRes
    #cu.use_uv_as_generated = True # removed 2.82

    #material slots
    for i in range(max(tree_settings.matIndex)+1):
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
            kickstart_trunk(tree_settings, addstem, leaf_settings.leaves, cu, scaleVal)
        # If this isn't the trunk then we may have multiple stem to initialize
        else:
            # For each of the points defined in the list of stem starting points we need to grow a stem.
            fabricate_stems(tree_settings, addsplinetobone, addstem, baseSize, childP, cu, leaf_settings.leafDist, leaf_settings.leaves, leaf_settings.leafType, lvl, scaleVal, storeN, armature_settings.boneStep)

        #change base size for each level
        if lvl > 0:
            baseSize = tree_settings.baseSize_s
        if (lvl == tree_settings.levels - 1):
            baseSize = tree_settings.leafBaseSize

        childP = []
        # Now grow each of the stems in the list of those to be extended
        for st in stemList:
            splineToBone = grow_branch_level(tree_settings, baseSize, childP, cu, lvl, scaleVal, splineToBone, st, closeTipp, noTip, armature_settings.boneStep, leaf_settings.leaves, leaf_settings.leafType, attachment)

        levelCount.append(len(cu.splines))

    # Set curve resolution
    cu.resolution_u = tree_settings.resU

    # If we need to add leaves, we do it here
    leafMesh, leafObj, leafP, leafVertSize = add_leafs(childP, leafObj, leaf_settings, lvl, treeOb)

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
        armOb = create_armature(armature_settings, leafP, cu, leafMesh, leafObj, leafVertSize, leaf_settings.leaves, levelCount, splineToBone, treeOb, treeObj)

    #print(time.time()-startTime)

    #mesh branches
    if armature_settings.makeMesh:
        make_armature_mesh(armOb, armature_settings, cu, levelCount, splineToBone,
                           treeMesh, treeObj, tree_settings)

