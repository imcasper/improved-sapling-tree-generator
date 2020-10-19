from math import floor
from random import setstate, uniform

from .utils import splits2
from .grow_spline import grow_spline
from .shape_ratio import shape_ratio
from .find_child_points import find_child_points, find_child_points2, find_child_points3
from .interp_stem import interp_stem


def perform_pruning(baseSize, baseSplits, childP, cu, currentMax, currentMin, currentScale, curve, curveBack, curveRes,
                    deleteSpline, forceSprout, handles, n, levels, branches, oldMax, originalSplineToBone, originalCo, originalCurv,
                    originalCurvV, originalHandleL, originalHandleR, originalLength, originalSeg, prune, prunePowerHigh,
                    prunePowerLow, pruneRatio, pruneWidth, pruneBase, pruneWidthPeak, randState, ratio, scaleVal, segSplits,
                    splineToBone, splitAngle, splitAngleV, st, startPrune, branchDist, length, splitByLen, closeTip, splitRadiusRatio, minRadius, nrings,
                    splitBias, splitHeight, attractOut, rMode, splitStraight, splitLength, lengthV, taperCrown, noTip, boneStep, rotate, rotateV, leaves, leafType, matIndex):
    while startPrune and ((currentMax - currentMin) > 0.005):
        setstate(randState)

        # If the search will halt after this iteration, then set the adjustment of stem length to take into account the pruning ratio
        if (currentMax - currentMin) < 0.01:
            currentScale = (currentScale - 1) * pruneRatio + 1
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
        for k in range(curveRes[n]):
            # Make a copy of the current list to avoid continually adding to the list we're iterating over
            tempList = splineList[:]
            # print('Leng: ', len(tempList))

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
                            closeTip, splitRadiusRatio, minRadius, kp, splitHeight, attractOut[n], stemsegL, splitLength, lengthV[n], taperCrown, boneStep, rotate, rotateV, matIndex)

        # If pruning is enabled then we must to the check to see if the end of the spline is within the evelope
        if prune:
            # Check each endpoint to see if it is inside
            for s in splineList:
                coordMag = (s.spline.bezier_points[-1].co.xy).length
                ratio = (scaleVal - s.spline.bezier_points[-1].co.z) / (scaleVal * max(1 - pruneBase, 1e-6))
                # Don't think this if part is needed
                if (n == 0) and (s.spline.bezier_points[-1].co.z < pruneBase * scaleVal):
                    insideBool = True  # Init to avoid UnboundLocalError later
                else:
                    insideBool = (
                            (coordMag / scaleVal) < pruneWidth * shape_ratio(9, ratio, pruneWidthPeak, prunePowerHigh,
                                                                             prunePowerLow))
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
        if (((currentMax - currentMin) < 0.005) or not prune) or forceSprout:
            if (n == 0) and (rMode in ['rotate', 'random']):
                tVals = find_child_points2(st.children)
            elif (n == 0) and (rMode == 'distance'):
                tVals = find_child_points3(splineList, st.children)
            elif (n == levels - 1) and (leafType in ['1', '3']):
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
            if (n != levels - 1) and (branches[min(3, n+1)] == 0):
                tVals = []

            if (n < levels - 1) and noTip:
                tVals = tVals[:-1]

            # remove some of the points because of baseSize
            if (n == 0) and (rMode == 'distance'):
                tVals = [t for t in tVals if t > baseSize]
            else:
                trimNum = int(baseSize * (len(tVals) + 1))
                tVals = tVals[trimNum:]

            #grow branches in rings/whorls
            if (n == 0) and (nrings > 0):
                tVals = [(floor(t * nrings) / nrings) * uniform(.995, 1.005) for t in tVals[:-1]]
                if not noTip:
                    tVals.append(1)
                tVals = [t for t in tVals if t > baseSize]

            #branch distribution
            if n == 0:
                tVals = [((t - baseSize) / (1 - baseSize)) for t in tVals]
                if branchDist < 1.0:
                    tVals = [t ** (1 / branchDist) for t in tVals]
                else:
                    tVals = [1 - (1 - t) ** branchDist for t in tVals]
                tVals = [t * (1 - baseSize) + baseSize for t in tVals]

            # For all the splines, we interpolate them and add the new points to the list of child points
            maxOffset = max([s.offsetLen + (len(s.spline.bezier_points) - 1) * s.segL for s in splineList])
            for s in splineList:
                #print(str(n)+'level: ', s.segMax*s.segL)
                childP.extend(interp_stem(s, tVals, maxOffset, baseSize))

        # Force the splines to be deleted
        deleteSpline = True
        # If pruning isn't enabled then make sure it doesn't loop
        if not prune:
            startPrune = False
    return ratio, splineToBone