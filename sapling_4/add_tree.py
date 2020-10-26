from math import copysign
from random import seed, uniform

import bpy

from .ui_settings.ArmatureSettings import ArmatureSettings
from .ui_settings.LeafSettings import LeafSettings
from .ui_settings.TreeSettings import TreeSettings
from .add_leafs import add_leafs
from .grow_all_splines import grow_all_splines
from .make_armature_mesh import make_armature_mesh
from .create_armature import create_armature
from .find_taper import find_taper


def add_tree(props):
    global splitError
    # startTime = time.time()
    # Set the seed for repeatable results
    print(props)
    random_seed = props.seed
    seed(random_seed)

    # Set all other variables
    tree_settings = TreeSettings(props)
    leaf_settings = LeafSettings(props)
    armature_settings = ArmatureSettings(props)
    scale_v = props.scaleV#
    base_size = props.baseSize

    attachment = props.attachment

    # taper
    if tree_settings.autoTaper:
        tree_settings.taper = find_taper(tree_settings)

    for ob in bpy.data.objects:
        ob.select_set(state=False)

    # Initialise the tree object and curve and adjust the settings
    tree_curve = bpy.data.curves.new('tree', 'CURVE')
    tree_curve_object = bpy.data.objects.new('tree', tree_curve)
    bpy.context.scene.collection.objects.link(tree_curve_object)
    if not armature_settings.useArm:
        tree_curve_object.location = bpy.context.scene.cursor.location

    tree_curve.dimensions = '3D'
    tree_curve.fill_mode = 'FULL'
    tree_curve.bevel_depth = tree_settings.bevelDepth
    tree_curve.bevel_resolution = tree_settings.bevelRes
    # tree_curve.use_uv_as_generated = True # removed 2.82

    # material slots
    for i in range(max(tree_settings.matIndex)+1):
        tree_curve_object.data.materials.append(None)

    # Fix the scale of the tree now
    if random_seed == 0:  # first tree is always average size
        scale_v = 0
    scale_val = tree_settings.scale + uniform(-scale_v, scale_v)
    scale_val += copysign(1e-6, scale_val)  # Move away from zero to avoid div by zero

    # Each of the levels needed by the user we grow all the splines
    child_points, level_count, spline_to_bone = grow_all_splines(tree_settings, armature_settings, leaf_settings, attachment, base_size, tree_curve, scale_val)

    # Set curve resolution
    tree_curve.resolution_u = tree_settings.resU

    # If we need to add leaves, we do it here
    leaf_mesh, leaf_mesh_object, leaf_points = add_leafs(child_points, leaf_settings, tree_curve_object)

    armature_settings.armLevels = min(armature_settings.armLevels, tree_settings.levels)
    armature_settings.armLevels -= 1

    # unpack vars from spline_to_bone
    spline_to_bone1 = spline_to_bone
    spline_to_bone = [s[0] if len(s) > 1 else s for s in spline_to_bone1]

    # add mesh object
    tree_mesh_object = None
    tree_mesh = None
    if armature_settings.makeMesh:
        tree_mesh = bpy.data.meshes.new('treemesh')
        tree_mesh_object = bpy.data.objects.new('treemesh', tree_mesh)
        bpy.context.scene.collection.objects.link(tree_mesh_object)
        if not armature_settings.useArm:
            tree_mesh_object.location = bpy.context.scene.cursor.location

    armature_object = None
    # If we need an armature we add it
    if armature_settings.useArm:
        # Create the armature and objects
        armature_object = create_armature(armature_settings, leaf_points, tree_curve, leaf_mesh, leaf_mesh_object, leaf_settings.leafVertSize, leaf_settings.leaves, level_count, spline_to_bone, tree_curve_object, tree_mesh_object)

    # print(time.time()-startTime)

    # Mesh branches
    if armature_settings.makeMesh:
        make_armature_mesh(armature_settings, tree_settings, armature_object, tree_curve, level_count, spline_to_bone, tree_mesh, tree_mesh_object)
