from math import ceil, floor
from random import uniform

from .utils import splits, splits2, splits3
from .grow_spline import grow_spline
from .interp_stem import interp_stem
from .find_child_points import find_child_points, find_child_points2, find_child_points3
from .TreeSettings import TreeSettings


def grow_branch_level(tree_settings: TreeSettings, baseSize, baseSplits, childP, cu, handles, n, branches, scaleVal, splineToBone, st, closeTip, noTip, boneStep, leaves, leafType, attachment, matIndex):
    # Initialise the spline list of split stems in the current branch
    splineList = [st]
    # For each of the segments of the stem which must be grown we have to add to each spline in splineList
    for k in range(tree_settings.curveRes[n]):
        # Make a copy of the current list to avoid continually adding to the list we're iterating over
        tempList = splineList[:]

        #for curve variation
        if tree_settings.curveRes[n] > 1:
            kp = (k / (tree_settings.curveRes[n] - 1)) # * 2
        else:
            kp = 1.0

        #split bias
        splitValue = tree_settings.segSplits[n]
        if n == 0:
            splitValue = ((2 * tree_settings.splitBias) * (kp - .5) + 1) * splitValue
            splitValue = max(splitValue, 0.0)

        # For each of the splines in this list set the number of splits and then grow it
        for spl in tempList:

            #adjust numSplit #this is not perfect, but it's good enough and not worth improving
            lastsplit = getattr(spl, 'splitlast', 0)
            splitVal = splitValue
            if lastsplit == 0:
                splitVal = splitValue ** 0.5 # * 1.33
            elif lastsplit == 1:
                splitVal = splitValue * splitValue

            if k == 0:
                numSplit = 0
            elif (k == 1) and (n == 0):
                numSplit = tree_settings.baseSplits
            elif (n == 0) and (k == int((tree_settings.curveRes[n]) * tree_settings.splitHeight)) and (splitVal > 0): #always split at splitHeight
                numSplit = 1
            elif (n == 0) and (k < ((tree_settings.curveRes[n]) * tree_settings.splitHeight)) and (k != 1): #splitHeight
                numSplit = 0
            else:
                if (n >= 0) and tree_settings.splitByLen:
                    L = ((spl.segL * tree_settings.curveRes[n]) / scaleVal)
                    lf = 1
                    for l in tree_settings.length[:n+1]:
                        lf *= l
                    L = L / lf
                    numSplit = splits2(splitVal * L)
                else:
                    numSplit = splits2(splitVal)

            if (k == int(tree_settings.curveRes[n] / 2 + 0.5)) and (tree_settings.curveBack[n] != 0):
                spl.curv += 2 * (tree_settings.curveBack[n] / tree_settings.curveRes[n]) #was -4 *

            grow_spline(n, spl, numSplit, tree_settings.splitAngle[n], tree_settings.splitAngleV[n], tree_settings.splitStraight, splineList, handles, splineToBone,
                        closeTip, tree_settings.splitRadiusRatio, tree_settings.minRadius, kp, tree_settings.splitHeight, tree_settings.attractOut[n], tree_settings.splitLength, tree_settings.lengthV[n], tree_settings.taperCrown, boneStep, tree_settings.rotate, tree_settings.rotateV, matIndex)

    # Sprout child points to grow the next splines or leaves
    if (n == 0) and (tree_settings.rMode == 'rotate'):
        tVals = find_child_points2(st.children)
    elif (n == 0) and (tree_settings.rMode == 'distance'):
        tVals = find_child_points3(splineList, st.children, rp=.25) #degrees(rotateV[3])

    elif ((n > 0) and (n != tree_settings.levels - 1) and (attachment == "1")) or ((n == tree_settings.levels - 1) and (leafType in ['1', '3'])): # oppositely attached leaves and branches
        tVal = find_child_points(splineList, ceil(st.children / 2))
        tVals = []
        for t in tVal[:-1]:
            tVals.extend([t, t])
        if (n == tree_settings.levels - 1) and ((leaves / 2) == (leaves // 2)):
            # put two leaves at branch tip if leaves is even
            tVals.extend([1, 1])
        else:
            tVals.append(1)
    else:
        tVals = find_child_points(splineList, st.children)

    if 1 not in tVals:
        tVals.append(1.0)
    if (n != tree_settings.levels - 1) and (tree_settings.branches[min(3, n+1)] == 0):
        tVals = []

    if (n < tree_settings.levels - 1) and noTip:
        tVals = tVals[:-1]

    # remove some of the points because of baseSize
    tVals = [t for t in tVals if t > baseSize]

    #grow branches in rings/whorls
    if (n == 0) and (tree_settings.nrings > 0):
        tVals = [(floor(t * tree_settings.nrings) / tree_settings.nrings) * uniform(.999, 1.001) for t in tVals[:-1]]
        if not noTip:
            tVals.append(1)
        tVals = [t for t in tVals if t > baseSize]

    #branch distribution
    if n == 0:
        tVals = [((t - baseSize) / (1 - baseSize)) for t in tVals]
        if tree_settings.branchDist <= 1.0:
            tVals = [t ** (1 / tree_settings.branchDist) for t in tVals]
        else:
            #tVals = [1 - (1 - t) ** branchDist for t in tVals]
            tVals = [1 - t for t in tVals]
            p = ((1/.5 ** tree_settings.branchDist) - 1) ** 2
            tVals = [(p ** t - 1) / (p-1) for t in tVals]
            tVals = [1 - t for t in tVals]
        tVals = [t * (1 - baseSize) + baseSize for t in tVals]

    # For all the splines, we interpolate them and add the new points to the list of child points
    maxOffset = max([s.offsetLen + (len(s.spline.bezier_points) - 1) * s.segL for s in splineList])
    for s in splineList:
        #print(str(n)+'level: ', s.segMax*s.segL)
        childP.extend(interp_stem(s, tVals, maxOffset, baseSize))

    return splineToBone