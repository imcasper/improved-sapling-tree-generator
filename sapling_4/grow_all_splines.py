from collections import deque

from .fabricate_stems import fabricate_stems
from .grow_branch_level import grow_branch_level
from .kickstart_trunk import kickstart_trunk
from .ui_settings.ArmatureSettings import ArmatureSettings
from .ui_settings.LeafSettings import LeafSettings
from .ui_settings.TreeSettings import TreeSettings


def grow_all_splines(tree_settings: TreeSettings, armature_settings: ArmatureSettings, leaf_settings: LeafSettings, attachment, base_size, tree_curve, scale_val):
    global split_error
    child_points = []
    summary_leaf_child_points = []
    stem_list = []
    level_count = []
    spline_to_bone = deque([''])
    add_spline_to_bone = spline_to_bone.append
    # Each of the levels needed by the user we grow all the splines
    for lvl in range(tree_settings.levels):
        store_n = lvl
        stem_list = deque()
        add_stem = stem_list.append

        # If lvl is used as an index to access parameters for the tree it must be at most 3 or it will reference outside the array index
        lvl = min(3, lvl)
        split_error = 0.0

        # Close tip only on last level
        close_tip = all([(lvl == tree_settings.levels - 1), tree_settings.closeTip])

        # If this is the first level of growth (the trunk) then we need some special work to begin the tree
        if lvl == 0:
            kickstart_trunk(tree_settings, add_stem, leaf_settings.leaves, tree_curve, scale_val)
        # If this isn't the trunk then we may have multiple stem to initialize
        else:
            # For each of the points defined in the list of stem starting points we need to grow a stem.
            fabricate_stems(tree_settings, add_spline_to_bone, add_stem, base_size, child_points, tree_curve, leaf_settings.leafDist, leaf_settings.leaves, leaf_settings.leafType, lvl, scale_val, store_n, armature_settings.boneStep)

        # Change base size for each level
        if lvl > 0:
            base_size = tree_settings.baseSize_s
        if lvl == tree_settings.levels - 1:
            base_size = tree_settings.leafBaseSize

        child_points = []
        # Now grow each of the stems in the list of those to be extended
        for stem in stem_list:
            spline_to_bone = grow_branch_level(tree_settings, base_size, child_points, lvl, scale_val, spline_to_bone, stem, close_tip, armature_settings.boneStep, leaf_settings.leaves, leaf_settings.leafType, attachment)

        if leaf_settings.leafLevel <= lvl:
            summary_leaf_child_points.extend(child_points)

        level_count.append(len(tree_curve.splines))

    return summary_leaf_child_points, level_count, spline_to_bone
