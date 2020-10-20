from math import ceil, floor
from random import uniform
from typing import List

from .utils import splits2
from .grow_spline import grow_spline
from .interp_stem import interp_stem
from .find_child_points import find_child_points, find_child_points2, find_child_points3
from .ChildPoint import ChildPoint
from .ui_settings.TreeSettings import TreeSettings


def grow_branch_level(tree_settings: TreeSettings, base_size, child_points: List[ChildPoint], lvl, scale_val, spline_to_bone, stem, close_tip, bone_step, leaves, leaf_type, attachment):
    # Initialise the spline list of split stems in the current branch
    spline_list = [stem]
    # For each of the segments of the stem which must be grown we have to add to each spline in spline_list
    for k in range(tree_settings.curveRes[lvl]):
        # Make a copy of the current list to avoid continually adding to the list we're iterating over
        temp_list = spline_list[:]

        # for curve variation
        if tree_settings.curveRes[lvl] > 1:
            kp = (k / (tree_settings.curveRes[lvl] - 1)) # * 2
        else:
            kp = 1.0

        # split bias
        split_value = tree_settings.segSplits[lvl]
        if lvl == 0:
            split_value = ((2 * tree_settings.splitBias) * (kp - .5) + 1) * split_value
            split_value = max(split_value, 0.0)

        # For each of the splines in this list set the number of splits and then grow it
        for spl in temp_list:
            split_and_grow_splines(bone_step, close_tip, k, kp, lvl, scale_val, spl, spline_list, spline_to_bone, split_value, tree_settings)

    # Sprout child points to grow the next splines or leaves
    if (lvl == 0) and (tree_settings.rMode == 'rotate'):
        t_values = find_child_points2(stem.children)
    elif (lvl == 0) and (tree_settings.rMode == 'distance'):
        t_values = find_child_points3(spline_list, stem.children, rp=.25) #degrees(rotateV[3])

    elif ((lvl > 0) and (lvl != tree_settings.levels - 1) and (attachment == "1")) or ((lvl == tree_settings.levels - 1) and (leaf_type in ['1', '3'])):  # oppositely attached leaves and branches
        t_val = find_child_points(spline_list, ceil(stem.children / 2))
        t_values = []
        for t in t_val[:-1]:
            t_values.extend([t, t])
        if (lvl == tree_settings.levels - 1) and ((leaves / 2) == (leaves // 2)):
            # Put two leaves at branch tip if leaves is even
            t_values.extend([1, 1])
        else:
            t_values.append(1)
    else:
        t_values = find_child_points(spline_list, stem.children)

    if 1 not in t_values:
        t_values.append(1.0)
    if (lvl != tree_settings.levels - 1) and (tree_settings.branches[min(3, lvl + 1)] == 0):
        t_values = []

    if (lvl < tree_settings.levels - 1) and tree_settings.noTip:
        t_values = t_values[:-1]

    # Remove some of the points because of baseSize
    t_values = [t for t in t_values if t > base_size]

    # Grow branches in rings/whorls
    if (lvl == 0) and (tree_settings.nrings > 0):
        t_values = [(floor(t * tree_settings.nrings) / tree_settings.nrings) * uniform(.999, 1.001) for t in t_values[:-1]]
        if not tree_settings.noTip:
            t_values.append(1)
        t_values = [t for t in t_values if t > base_size]

    # Branch distribution
    if lvl == 0:
        t_values = [((t - base_size) / (1 - base_size)) for t in t_values]
        if tree_settings.branchDist <= 1.0:
            t_values = [t ** (1 / tree_settings.branchDist) for t in t_values]
        else:
            # t_values = [1 - (1 - t) ** branchDist for t in t_values]
            t_values = [1 - t for t in t_values]
            p = ((1/.5 ** tree_settings.branchDist) - 1) ** 2
            t_values = [(p ** t - 1) / (p-1) for t in t_values]
            t_values = [1 - t for t in t_values]
        t_values = [t * (1 - base_size) + base_size for t in t_values]

    # For all the splines, we interpolate them and add the new points to the list of child points
    max_offset = max([s.offsetLen + (len(s.spline.bezier_points) - 1) * s.segL for s in spline_list])
    for s in spline_list:
        # print(str(n)+'level: ', s.segMax*s.segL)
        child_points.extend(interp_stem(s, t_values, max_offset, base_size))

    return spline_to_bone


def split_and_grow_splines(bone_step, close_tip, k, kp, lvl, scale_val, spl, spline_list, spline_to_bone, split_value,
                           tree_settings):
    # Adjust num_split #this is not perfect, but it's good enough and not worth improving
    last_split = getattr(spl, 'splitlast', 0)
    split_val = split_value
    if last_split == 0:
        split_val = split_value ** 0.5  # * 1.33
    elif last_split == 1:
        split_val = split_value * split_value
    if k == 0:
        num_split = 0
    elif (k == 1) and (lvl == 0):
        num_split = tree_settings.baseSplits
    elif (lvl == 0) and (k == int((tree_settings.curveRes[lvl]) * tree_settings.splitHeight)) and (
            split_val > 0):  # always split at splitHeight
        num_split = 1
    elif (lvl == 0) and (k < ((tree_settings.curveRes[lvl]) * tree_settings.splitHeight)) and (k != 1):  # splitHeight
        num_split = 0
    else:
        if (lvl >= 0) and tree_settings.splitByLen:
            L = ((spl.segL * tree_settings.curveRes[lvl]) / scale_val)
            lf = 1
            for l in tree_settings.length[:lvl + 1]:
                lf *= l
            L = L / lf
            num_split = splits2(split_val * L)
        else:
            num_split = splits2(split_val)
    if (k == int(tree_settings.curveRes[lvl] / 2 + 0.5)) and (tree_settings.curveBack[lvl] != 0):
        spl.curv += 2 * (tree_settings.curveBack[lvl] / tree_settings.curveRes[lvl])  # was -4 *
    grow_spline(tree_settings, lvl, spl, num_split, spline_list, spline_to_bone, close_tip, kp, bone_step)