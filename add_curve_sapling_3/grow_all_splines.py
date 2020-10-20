from collections import deque

from add_curve_sapling_3.fabricate_stems import fabricate_stems
from add_curve_sapling_3.kickstart_trunk import kickstart_trunk
from add_curve_sapling_3.preform_pruning import perform_pruning


def grow_all_splines(base_size, base_size_s, bone_step, cu, leaf_base_size, leaf_settings, scale_val, tree_settings):
    global split_error
    child_points = []
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

        # closeTip only on last level
        close_tipp = all([(lvl == tree_settings.levels - 1), tree_settings.closeTip])

        # If this is the first level of growth (the trunk) then we need some special work to begin the tree
        if lvl == 0:
            kickstart_trunk(tree_settings, add_stem, leaf_settings.leaves, cu, scale_val)
        # If this isn't the trunk then we may have multiple stem to initialize
        else:
            # For each of the points defined in the list of stem starting points we need to grow a stem.
            fabricate_stems(tree_settings, add_spline_to_bone, add_stem, base_size, child_points, cu, leaf_settings.leafDist, leaf_settings.leaves, leaf_settings.leafType, lvl, scale_val, store_n, bone_step)

        # change base size for each level
        if lvl > 0:
            base_size *= base_size_s  # decrease at each level
        if (lvl == tree_settings.levels - 1):
            base_size = leaf_base_size

        child_points = []
        # Now grow each of the stems in the list of those to be extended
        for st in stem_list:
            # Now do the iterative pruning, this uses a binary search and halts once the difference between upper and lower bounds of the search are less than 0.005
            tree_settings.ratio, spline_to_bone = perform_pruning(tree_settings, base_size, child_points, cu, lvl, scale_val, spline_to_bone, st, close_tipp, bone_step, leaf_settings.leaves, leaf_settings.leafType)

        level_count.append(len(cu.splines))
    return child_points, level_count, spline_to_bone