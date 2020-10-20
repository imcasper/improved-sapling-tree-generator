import copy
from math import floor
from random import setstate, uniform, getstate

from .utils import splits2
from .shape_ratio import shape_ratio
from .find_child_points import find_child_points, find_child_points2, find_child_points3
from .grow_spline import grow_spline
from .interp_stem import interp_stem
from .TreeSettings import TreeSettings


def perform_pruning(tree_settings: TreeSettings, baseSize, childP, cu, n, scaleVal,
                    splineToBone, st, closeTip, boneStep, leaves, leafType):
    # When using pruning, we need to ensure that the random effects will be the same for each iteration to make sure the problem is linear.
    randState = getstate()
    startPrune = True
    lengthTest = 0.0
    # Store all the original values for the stem to make sure we have access after it has been modified by pruning
    originalLength = st.segL
    originalCurv = st.curv
    originalCurvV = st.curvV
    originalSeg = st.seg
    originalHandleR = st.p.handle_right.copy()
    originalHandleL = st.p.handle_left.copy()
    originalCo = st.p.co.copy()
    currentMax = 1.0
    currentMin = 0.0
    currentScale = 1.0
    oldMax = 1.0
    deleteSpline = False
    originalSplineToBone = copy.copy(splineToBone)
    forceSprout = False

    ratio = tree_settings.ratio
    while startPrune and ((currentMax - currentMin) > 0.005):
        setstate(randState)

        # If the search will halt after this iteration, then set the adjustment of stem length to take into account the pruning ratio
        if (currentMax - currentMin) < 0.01:
            currentScale = (currentScale - 1) * tree_settings.pruneRatio + 1
            startPrune = False
            forceSprout = True
        # Change the segment length of the stem by applying some scaling
        st.segL = originalLength * currentScale
        # To prevent millions of splines being created we delete any old ones and replace them with only their first points to begin the spline again
        if deleteSpline:
            for x in splineList:
                cu.splines.remove(x.spline)
            newSpline = cu.splines.new('BEZIER')
            newPoint = newSpline.bezier_points[-1]
            newPoint.co = originalCo
            newPoint.handle_right = originalHandleR
            newPoint.handle_left = originalHandleL
            (newPoint.handle_left_type, newPoint.handle_right_type) = ('VECTOR', 'VECTOR')
            st.spline = newSpline
            st.curv = originalCurv
            st.curvV = originalCurvV
            st.seg = originalSeg
            st.p = newPoint
            newPoint.radius = st.radS
            splineToBone = originalSplineToBone

        # Grow the tree branch

        #split length variation
        stemsegL = st.segL #initial segment length used for variation of each split stem
        #if (n != 0):
        #    st.segL = stemsegL * uniform(1 - lengthV[n], 1 + lengthV[n]) #variation for main stem

        # Initialise the spline list of split stems in the current branch
        splineList = [st]
        # For each of the segments of the stem which must be grown we have to add to each spline in splineList
        for k in range(tree_settings.curveRes[n]):
            # Make a copy of the current list to avoid continually adding to the list we're iterating over
            tempList = splineList[:]
            # print('Leng: ', len(tempList))

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

                #adjust numSplit
                lastsplit = getattr(spl, 'splitlast', 0)
                splitVal = splitValue
                if lastsplit == 0:
                    splitVal = splitValue ** 0.5# * 1.33
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

                grow_spline(tree_settings, n, spl, numSplit, splineList, splineToBone, closeTip, kp, stemsegL, boneStep)

        # If pruning is enabled then we must to the check to see if the end of the spline is within the evelope
        if tree_settings.prune:
            # Check each endpoint to see if it is inside
            for s in splineList:
                coordMag = (s.spline.bezier_points[-1].co.xy).length
                ratio = (scaleVal - s.spline.bezier_points[-1].co.z) / (scaleVal * max(1 - tree_settings.pruneBase, 1e-6))
                # Don't think this if part is needed
                if (n == 0) and (s.spline.bezier_points[-1].co.z < tree_settings.pruneBase * scaleVal):
                    insideBool = True  # Init to avoid UnboundLocalError later
                else:
                    insideBool = (
                            (coordMag / scaleVal) < tree_settings.pruneWidth * shape_ratio(9, ratio, tree_settings.pruneWidthPeak, tree_settings.prunePowerHigh,
                                                                             tree_settings.prunePowerLow))
                # If the point is not inside then we adjust the scale and current search bounds
                if not insideBool:
                    oldMax = currentMax
                    currentMax = currentScale
                    currentScale = 0.5 * (currentMax + currentMin)
                    break
            # If the scale is the original size and the point is inside then we need to make sure it won't be pruned or extended to the edge of the envelope
            if insideBool and (currentScale != 1):
                currentMin = currentScale
                currentMax = oldMax
                currentScale = 0.5 * (currentMax + currentMin)
            if insideBool and ((currentMax - currentMin) == 1):
                currentMin = 1

        # If the search will halt on the next iteration then we need to make sure we sprout child points to grow the next splines or leaves
        if (((currentMax - currentMin) < 0.005) or not tree_settings.prune) or forceSprout:
            if (n == 0) and (tree_settings.rMode in ['rotate', 'random']):
                tVals = find_child_points2(st.children)
            elif (n == 0) and (tree_settings.rMode == 'distance'):
                tVals = find_child_points3(splineList, st.children)
            elif (n == tree_settings.levels - 1) and (leafType in ['1', '3']):
                tVal = find_child_points(splineList, st.children // 2)
                tVals = []
                for t in tVal[:-1]:
                    tVals.extend([t, t])
                if (leaves / 2) == (leaves // 2):
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

            if (n < tree_settings.levels - 1) and tree_settings.noTip:
                tVals = tVals[:-1]

            # remove some of the points because of baseSize
            if (n == 0) and (tree_settings.rMode == 'distance'):
                tVals = [t for t in tVals if t > baseSize]
            else:
                trimNum = int(baseSize * (len(tVals) + 1))
                tVals = tVals[trimNum:]

            #grow branches in rings/whorls
            if (n == 0) and (tree_settings.nrings > 0):
                tVals = [(floor(t * tree_settings.nrings) / tree_settings.nrings) * uniform(.995, 1.005) for t in tVals[:-1]]
                if not tree_settings.noTip:
                    tVals.append(1)
                tVals = [t for t in tVals if t > baseSize]

            #branch distribution
            if n == 0:
                tVals = [((t - baseSize) / (1 - baseSize)) for t in tVals]
                if tree_settings.branchDist < 1.0:
                    tVals = [t ** (1 / tree_settings.branchDist) for t in tVals]
                else:
                    tVals = [1 - (1 - t) ** tree_settings.branchDist for t in tVals]
                tVals = [t * (1 - baseSize) + baseSize for t in tVals]

            # For all the splines, we interpolate them and add the new points to the list of child points
            maxOffset = max([s.offsetLen + (len(s.spline.bezier_points) - 1) * s.segL for s in splineList])
            for s in splineList:
                #print(str(n)+'level: ', s.segMax*s.segL)
                childP.extend(interp_stem(s, tVals, maxOffset, baseSize))

        # Force the splines to be deleted
        deleteSpline = True
        # If pruning isn't enabled then make sure it doesn't loop
        if not tree_settings.prune:
            startPrune = False
    return ratio, splineToBone