from math import ceil, floor
from random import uniform

from .utils import splits, splits2, splits3
from .grow_spline import grow_spline
from .interp_stem import interp_stem
from .find_child_points import find_child_points, find_child_points2, find_child_points3


def grow_branch_level(baseSize, baseSplits, childP, cu, curve, curveBack, curveRes, handles, n, levels, branches, scaleVal,
                  segSplits, splineToBone, splitAngle, splitAngleV, st, branchDist, length, splitByLen, closeTip,
                  splitRadiusRatio, minRadius, nrings, splitBias, splitHeight, attractOut, rMode, splitStraight,
                  splitLength, lengthV, taperCrown, noTip, boneStep, rotate, rotateV, leaves, leafType, attachment, matIndex):
    # Initialise the spline list of split stems in the current branch
    splineList = [st]
    # For each of the segments of the stem which must be grown we have to add to each spline in splineList
    for k in range(curveRes[n]):
        # Make a copy of the current list to avoid continually adding to the list we're iterating over
        tempList = splineList[:]

        #for curve variation
        if curveRes[n] > 1:
            kp = (k / (curveRes[n] - 1)) # * 2
        else:
            kp = 1.0

        #split bias
        splitValue = segSplits[n]
        if n == 0:
            splitValue = ((2 * splitBias) * (kp - .5) + 1) * splitValue
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
                numSplit = baseSplits
            elif (n == 0) and (k == int((curveRes[n]) * splitHeight)) and (splitVal > 0): #always split at splitHeight
                numSplit = 1
            elif (n == 0) and (k < ((curveRes[n]) * splitHeight)) and (k != 1): #splitHeight
                numSplit = 0
            else:
                if (n >= 0) and splitByLen:
                    L = ((spl.segL * curveRes[n]) / scaleVal)
                    lf = 1
                    for l in length[:n+1]:
                        lf *= l
                    L = L / lf
                    numSplit = splits2(splitVal * L)
                else:
                    numSplit = splits2(splitVal)

            if (k == int(curveRes[n] / 2 + 0.5)) and (curveBack[n] != 0):
                spl.curv += 2 * (curveBack[n] / curveRes[n]) #was -4 *

            grow_spline(n, spl, numSplit, splitAngle[n], splitAngleV[n], splitStraight, splineList, handles, splineToBone,
                        closeTip, splitRadiusRatio, minRadius, kp, splitHeight, attractOut[n], splitLength, lengthV[n], taperCrown, boneStep, rotate, rotateV, matIndex)

    # Sprout child points to grow the next splines or leaves
    if (n == 0) and (rMode == 'rotate'):
        tVals = find_child_points2(st.children)
    elif (n == 0) and (rMode == 'distance'):
        tVals = find_child_points3(splineList, st.children, rp=.25) #degrees(rotateV[3])

    elif ((n > 0) and (n != levels - 1) and (attachment == "1")) or ((n == levels - 1) and (leafType in ['1', '3'])): # oppositely attached leaves and branches
        tVal = find_child_points(splineList, ceil(st.children / 2))
        tVals = []
        for t in tVal[:-1]:
            tVals.extend([t, t])
        if (n == levels - 1) and ((leaves / 2) == (leaves // 2)):
            # put two leaves at branch tip if leaves is even
            tVals.extend([1, 1])
        else:
            tVals.append(1)
    else:
        tVals = find_child_points(splineList, st.children)

    if 1 not in tVals:
        tVals.append(1.0)
    if (n != levels - 1) and (branches[min(3, n+1)] == 0):
        tVals = []

    if (n < levels - 1) and noTip:
        tVals = tVals[:-1]

    # remove some of the points because of baseSize
    tVals = [t for t in tVals if t > baseSize]

    #grow branches in rings/whorls
    if (n == 0) and (nrings > 0):
        tVals = [(floor(t * nrings) / nrings) * uniform(.999, 1.001) for t in tVals[:-1]]
        if not noTip:
            tVals.append(1)
        tVals = [t for t in tVals if t > baseSize]

    #branch distribution
    if n == 0:
        tVals = [((t - baseSize) / (1 - baseSize)) for t in tVals]
        if branchDist <= 1.0:
            tVals = [t ** (1 / branchDist) for t in tVals]
        else:
            #tVals = [1 - (1 - t) ** branchDist for t in tVals]
            tVals = [1 - t for t in tVals]
            p = ((1/.5 ** branchDist) - 1) ** 2
            tVals = [(p ** t - 1) / (p-1) for t in tVals]
            tVals = [1 - t for t in tVals]
        tVals = [t * (1 - baseSize) + baseSize for t in tVals]

    # For all the splines, we interpolate them and add the new points to the list of child points
    maxOffset = max([s.offsetLen + (len(s.spline.bezier_points) - 1) * s.segL for s in splineList])
    for s in splineList:
        #print(str(n)+'level: ', s.segMax*s.segL)
        childP.extend(interp_stem(s, tVals, maxOffset, baseSize))

    return splineToBone