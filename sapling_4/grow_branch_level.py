from math import ceil, floor
from random import uniform

from .utils import splits, splits2, splits3
from .grow_spline import grow_spline
from .interp_stem import interp_stem
from .find_child_points import find_child_points, find_child_points2, find_child_points3
from .TreeSettings import TreeSettings


def grow_branch_level(tree_settings: TreeSettings, base_size, child_p, cu, n, scale_val, spline_to_bone, st, close_tip, noTip, bone_step, leaves, leaf_type, attachment):
    # Initialise the spline list of split stems in the current branch
    spline_list = [st]
    # For each of the segments of the stem which must be grown we have to add to each spline in spline_list
    for k in range(tree_settings.curveRes[n]):
        # Make a copy of the current list to avoid continually adding to the list we're iterating over
        temp_list = spline_list[:]

        #for curve variation
        if tree_settings.curveRes[n] > 1:
            kp = (k / (tree_settings.curveRes[n] - 1)) # * 2
        else:
            kp = 1.0

        #split bias
        split_value = tree_settings.segSplits[n]
        if n == 0:
            split_value = ((2 * tree_settings.splitBias) * (kp - .5) + 1) * split_value
            split_value = max(split_value, 0.0)

        # For each of the splines in this list set the number of splits and then grow it
        for spl in temp_list:

            #adjust num_split #this is not perfect, but it's good enough and not worth improving
            last_split = getattr(spl, 'splitlast', 0)
            split_val = split_value
            if last_split == 0:
                split_val = split_value ** 0.5 # * 1.33
            elif last_split == 1:
                split_val = split_value * split_value

            if k == 0:
                num_split = 0
            elif (k == 1) and (n == 0):
                num_split = tree_settings.baseSplits
            elif (n == 0) and (k == int((tree_settings.curveRes[n]) * tree_settings.splitHeight)) and (split_val > 0): #always split at splitHeight
                num_split = 1
            elif (n == 0) and (k < ((tree_settings.curveRes[n]) * tree_settings.splitHeight)) and (k != 1): #splitHeight
                num_split = 0
            else:
                if (n >= 0) and tree_settings.splitByLen:
                    L = ((spl.segL * tree_settings.curveRes[n]) / scale_val)
                    lf = 1
                    for l in tree_settings.length[:n+1]:
                        lf *= l
                    L = L / lf
                    num_split = splits2(split_val * L)
                else:
                    num_split = splits2(split_val)

            if (k == int(tree_settings.curveRes[n] / 2 + 0.5)) and (tree_settings.curveBack[n] != 0):
                spl.curv += 2 * (tree_settings.curveBack[n] / tree_settings.curveRes[n]) #was -4 *

            grow_spline(tree_settings, n, spl, num_split, spline_list, spline_to_bone, close_tip, kp, bone_step)

    # Sprout child points to grow the next splines or leaves
    if (n == 0) and (tree_settings.rMode == 'rotate'):
        t_vals = find_child_points2(st.children)
    elif (n == 0) and (tree_settings.rMode == 'distance'):
        t_vals = find_child_points3(spline_list, st.children, rp=.25) #degrees(rotateV[3])

    elif ((n > 0) and (n != tree_settings.levels - 1) and (attachment == "1")) or ((n == tree_settings.levels - 1) and (leaf_type in ['1', '3'])): # oppositely attached leaves and branches
        tVal = find_child_points(spline_list, ceil(st.children / 2))
        t_vals = []
        for t in tVal[:-1]:
            t_vals.extend([t, t])
        if (n == tree_settings.levels - 1) and ((leaves / 2) == (leaves // 2)):
            # put two leaves at branch tip if leaves is even
            t_vals.extend([1, 1])
        else:
            t_vals.append(1)
    else:
        t_vals = find_child_points(spline_list, st.children)

    if 1 not in t_vals:
        t_vals.append(1.0)
    if (n != tree_settings.levels - 1) and (tree_settings.branches[min(3, n+1)] == 0):
        t_vals = []

    if (n < tree_settings.levels - 1) and tree_settings.noTip:
        t_vals = t_vals[:-1]

    # remove some of the points because of baseSize
    t_vals = [t for t in t_vals if t > base_size]

    #grow branches in rings/whorls
    if (n == 0) and (tree_settings.nrings > 0):
        t_vals = [(floor(t * tree_settings.nrings) / tree_settings.nrings) * uniform(.999, 1.001) for t in t_vals[:-1]]
        if not tree_settings.noTip:
            t_vals.append(1)
        t_vals = [t for t in t_vals if t > base_size]

    #branch distribution
    if n == 0:
        t_vals = [((t - base_size) / (1 - base_size)) for t in t_vals]
        if tree_settings.branchDist <= 1.0:
            t_vals = [t ** (1 / tree_settings.branchDist) for t in t_vals]
        else:
            #t_vals = [1 - (1 - t) ** branchDist for t in t_vals]
            t_vals = [1 - t for t in t_vals]
            p = ((1/.5 ** tree_settings.branchDist) - 1) ** 2
            t_vals = [(p ** t - 1) / (p-1) for t in t_vals]
            t_vals = [1 - t for t in t_vals]
        t_vals = [t * (1 - base_size) + base_size for t in t_vals]

    # For all the splines, we interpolate them and add the new points to the list of child points
    maxOffset = max([s.offsetLen + (len(s.spline.bezier_points) - 1) * s.segL for s in spline_list])
    for s in spline_list:
        #print(str(n)+'level: ', s.segMax*s.segL)
        child_p.extend(interp_stem(s, t_vals, maxOffset, base_size))

    return spline_to_bone