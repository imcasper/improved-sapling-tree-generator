from math import copysign
from random import seed, uniform

import bpy

from .ArmatureSettings import ArmatureSettings
from .LeafSettings import LeafSettings
from .TreeSettings import TreeSettings
from .add_leafs import add_leafs
from .grow_all_splines import grow_all_splines
from .make_armature_mesh import make_armature_mesh
from .create_armature import create_armature
from .find_taper import find_taper


def add_tree(props):
    global splitError
    #startTime = time.time()
    # Set the seed for repeatable results
    rseed = props.seed
    seed(rseed)

    # Set all other variables
    tree_settings = TreeSettings(props)
    leaf_settings = LeafSettings(props)
    armature_settings = ArmatureSettings(props)
    scaleV = props.scaleV#
    baseSize = props.baseSize

    attachment = props.attachment

    # taper
    if tree_settings.autoTaper:
        tree_settings.taper = find_taper(tree_settings)

    for ob in bpy.data.objects:
        ob.select_set(state=False)

    # Initialise the tree object and curve and adjust the settings
    cu = bpy.data.curves.new('tree', 'CURVE')
    treeOb = bpy.data.objects.new('tree', cu)
    bpy.context.scene.collection.objects.link(treeOb)
    if not armature_settings.useArm:
        treeOb.location = bpy.context.scene.cursor.location

    cu.dimensions = '3D'
    cu.fill_mode = 'FULL'
    cu.bevel_depth = tree_settings.bevelDepth
    cu.bevel_resolution = tree_settings.bevelRes
    # cu.use_uv_as_generated = True # removed 2.82

    # material slots
    for i in range(max(tree_settings.matIndex)+1):
        treeOb.data.materials.append(None)

    # Fix the scale of the tree now
    if rseed == 0: #first tree is always average size
        scaleV = 0
    scaleVal = tree_settings.scale + uniform(-scaleV, scaleV)
    scaleVal += copysign(1e-6, scaleVal)  # Move away from zero to avoid div by zero

    # Each of the levels needed by the user we grow all the splines
    childP, levelCount, splineToBone = grow_all_splines(tree_settings, armature_settings, leaf_settings, attachment, baseSize, cu, scaleVal)

    # Set curve resolution
    cu.resolution_u = tree_settings.resU

    # If we need to add leaves, we do it here
    leafMesh, leafObj, leafP = add_leafs(childP, leaf_settings, treeOb)

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
        armOb = create_armature(armature_settings, leafP, cu, leafMesh, leafObj, leaf_settings.leafVertSize, leaf_settings.leaves, levelCount, splineToBone, treeOb, treeObj)

    #print(time.time()-startTime)

    #mesh branches
    if armature_settings.makeMesh:
        make_armature_mesh(armOb, armature_settings, cu, levelCount, splineToBone, treeMesh, treeObj, tree_settings)
