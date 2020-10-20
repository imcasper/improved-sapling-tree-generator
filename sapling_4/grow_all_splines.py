from collections import deque

from .fabricate_stems import fabricate_stems
from .grow_branch_level import grow_branch_level
from .kickstart_trunk import kickstart_trunk
from .ArmatureSettings import ArmatureSettings
from .LeafSettings import LeafSettings
from .TreeSettings import TreeSettings


def grow_all_splines(tree_settings: TreeSettings, armature_settings: ArmatureSettings, leaf_settings: LeafSettings, attachment, base_size, cu, scaleVal):
    global splitError
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
        splitError = 0.0

        # closeTip only on last level
        close_tipp = all([(lvl == tree_settings.levels - 1), tree_settings.closeTip])

        # If this is the first level of growth (the trunk) then we need some special work to begin the tree
        if lvl == 0:
            kickstart_trunk(tree_settings, add_stem, leaf_settings.leaves, cu, scaleVal)
        # If this isn't the trunk then we may have multiple stem to initialize
        else:
            # For each of the points defined in the list of stem starting points we need to grow a stem.
            fabricate_stems(tree_settings, add_spline_to_bone, add_stem, base_size, child_points, cu, leaf_settings.leafDist, leaf_settings.leaves, leaf_settings.leafType, lvl, scaleVal, store_n, armature_settings.boneStep)

        # change base size for each level
        if lvl > 0:
            base_size = tree_settings.baseSize_s
        if (lvl == tree_settings.levels - 1):
            base_size = tree_settings.leafBaseSize

        child_points = []
        # Now grow each of the stems in the list of those to be extended
        for st in stem_list:
            spline_to_bone = grow_branch_level(tree_settings, base_size, child_points, cu, lvl, scaleVal, spline_to_bone, st, close_tipp, tree_settings.noTip, armature_settings.boneStep, leaf_settings.leaves, leaf_settings.leafType, attachment)

        level_count.append(len(cu.splines))
    return child_points, level_count, spline_to_bone