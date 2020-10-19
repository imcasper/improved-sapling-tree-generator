from math import atan2, sqrt, radians, pi
from random import uniform, choice

import bpy
from mathutils import Matrix, Euler

from .utils import declination, anglemean, convertQuat, zAxis, tau, xAxis, curveUp, roundBone
from .StemSpline import StemSpline


# This is the function which extends (or grows) a given stem.
def grow_spline(n, stem, numSplit, splitAng, splitAngV, splitStraight, splineList, hType, splineToBone, closeTip, splitRadiusRatio, minRadius, kp, splitHeight, outAtt,
                stemsegL, splitLength, lenVar, taperCrown, boneStep, rotate, rotateV, matIndex):

    #curv at base
    sCurv = stem.curv
    if (n == 0) and (kp <= splitHeight):
        sCurv = 0.0

    curveangle = sCurv + (uniform(0, stem.curvV) * kp * stem.curvSignx)
    curveVar = uniform(0, stem.curvV) * kp * stem.curvSigny
    stem.curvSignx *= -1
    stem.curvSigny *= -1

    curveVarMat = Matrix.Rotation(curveVar, 3, 'Y')

    # First find the current direction of the stem
    dir = stem.quat()

    #length taperCrown
    if n == 0:
        dec = declination(dir) / 180
        dec = dec ** 2
        tf = 1 - (dec * taperCrown * 30)
        tf = max(.1, tf)
    else:
        tf = 1.0

    #outward attraction
    if (n >= 0) and (kp > 0) and (outAtt > 0):
        p = stem.p.co.copy()
        d = atan2(p[0], -p[1])# + tau
        edir = dir.to_euler('XYZ', Euler((0, 0, d), 'XYZ'))
        d = anglemean(edir[2], d, (kp * outAtt))
        dirv = Euler((edir[0], edir[1], d), 'XYZ')
        dir = dirv.to_quaternion()

    if n == 0:
        dir = convertQuat(dir)

    #split radius factor
    splitR = splitRadiusRatio #0.707 #sqrt(1/(numSplit+1))

    if splitRadiusRatio == -1:
        lenV = (1-splitLength)
        ra = lenV / (lenV + 1)
        splitR1 = sqrt(ra)
        splitR2 = sqrt(1-ra)
    elif splitRadiusRatio == 0:
        splitR1 = sqrt(0.5)
        splitR2 = sqrt(1 - (0.5 * (1-splitLength)))
    else:
        splitR1 = splitR
        splitR2 = splitR

    # If the stem splits, we need to add new splines etc
    if numSplit > 0:
        # Get the curve data
        cuData = stem.spline.id_data.name
        cu = bpy.data.curves[cuData]

        #calc split angles
        if n == 0:
            angle = (splitAng + uniform(-splitAngV, splitAngV))
        else:
            angle = choice([-1, 1]) * (splitAng + uniform(-splitAngV, splitAngV))
        if n > 0:
            #make branches flatter
            angle *= max(1 - declination(dir) / 90, 0) * .67 + .33
        spreadangle = choice([-1, 1]) * (splitAng + uniform(-splitAngV, splitAngV))

        splitLen = 0
        if n == 0:
            splitLen = splitLength
        branchStraightness = 0
        if n == 0:
            branchStraightness = splitStraight

        if not hasattr(stem, 'rLast'):
            stem.rLast = radians(uniform(0, 360))

        br = rotate[0] + uniform(-rotateV[0], rotateV[0])
        branchRot = stem.rLast + br
        branchRotMat = Matrix.Rotation(branchRot, 3, 'Z')
        stem.rLast = branchRot

        # Now for each split add the new spline and adjust the growth direction
        for i in range(numSplit):
            #find split scale and length variation for split branches
            lenV = (1-splitLen) * uniform(1-lenVar, 1+(splitLen * lenVar))
            lenV = max(lenV, 0.01)
            bScale = min(lenV * tf, 1)

            newSpline = cu.splines.new('BEZIER')
            newSpline.material_index = matIndex[n]
            newPoint = newSpline.bezier_points[-1]
            (newPoint.co, newPoint.handle_left_type, newPoint.handle_right_type) = (stem.p.co, 'VECTOR', 'VECTOR')
            newRadius = (stem.radS*(1 - stem.seg/stem.segMax) + stem.radE*(stem.seg/stem.segMax)) * bScale * splitR1
            #newRadius = max(newRadius, stem.radE * bScale)
            newPoint.radius = newRadius
            # Here we make the new "sprouting" stems diverge from the current direction
            divRotMat = Matrix.Rotation(angle * (1+branchStraightness) + curveangle, 3, 'X')
            dirVec = zAxis.copy()
            dirVec.rotate(divRotMat)

            #horizontal curvature variation
            dirVec.rotate(curveVarMat)

            if n == 0: #Special case for trunk splits
                dirVec.rotate(branchRotMat)

                ang = pi - ((tau) / (numSplit + 1)) * (i+1)
                dirVec.rotate(Matrix.Rotation(ang, 3, 'Z'))

            # Spread the stem out horizontally
            if n != 0: #Special case for trunk splits
                spreadMat = Matrix.Rotation(spreadangle, 3, 'Y')
                dirVec.rotate(spreadMat)

            dirVec.rotate(dir)

            # Introduce upward curvature
            upRotAxis = xAxis.copy()
            upRotAxis.rotate(dirVec.to_track_quat('Z', 'Y'))
            curveUpAng = curveUp(stem.vertAtt, dirVec.to_track_quat('Z', 'Y'), stem.segMax)
            upRotMat = Matrix.Rotation(-curveUpAng, 3, upRotAxis)
            dirVec.rotate(upRotMat)

            # Make the growth vec the length of a stem segment
            dirVec.normalize()

            #split length variation
            stemL = stem.segL * lenV # was stemsegL, now relative to direct parent branch
            dirVec *= stemL * tf
            ofst = stem.offsetLen + (stem.segL * (len(stem.spline.bezier_points) - 1))

            # Get the end point position
            end_co = stem.p.co.copy()

            # Add the new point and adjust its coords, handles and radius
            newSpline.bezier_points.add()
            newPoint = newSpline.bezier_points[-1]
            (newPoint.co, newPoint.handle_left_type, newPoint.handle_right_type) = (end_co + dirVec, hType, hType)

            newRadius = (stem.radS*(1 - (stem.seg + 1)/stem.segMax) + stem.radE*((stem.seg + 1)/stem.segMax)) * bScale * splitR1
            newRadius = max(newRadius, minRadius)
            #newRadius = max(newRadius, stem.radE * bScale)
            nRadS = max(stem.radS * bScale * splitR1, minRadius)
            nRadE = max(stem.radE * bScale * splitR1, minRadius) # * 1
            if (stem.seg == stem.segMax-1) and closeTip:
                newRadius = 0.0
            newPoint.radius = newRadius

            # If this isn't the last point on a stem, then we need to add it to the list of stems to continue growing
            #print(stem.seg != stem.segMax, stem.seg, stem.segMax)
            #if stem.seg != stem.segMax: # if probs not necessary
            nstem = StemSpline(newSpline, stem.curv, stem.curvV, stem.vertAtt, stem.seg + 1, stem.segMax, stemL, stem.children,
                               nRadS, nRadE, len(cu.splines) - 1, ofst, stem.quat())
            nstem.splitlast = 1#numSplit #keep track of numSplit for next stem
            nstem.rLast = branchRot + pi
            if hasattr(stem, 'isFirstTip'):
                nstem.isFirstTip = True
            splineList.append(nstem)
            bone = 'bone'+(str(stem.splN)).rjust(3, '0')+'.'+(str(len(stem.spline.bezier_points)-2)).rjust(3, '0')
            bone = roundBone(bone, boneStep[n])
            splineToBone.append((bone, False, True, len(stem.spline.bezier_points)-2))

        # The original spline also needs to keep growing so adjust its direction too
        divRotMat = Matrix.Rotation(-angle * (1-branchStraightness) + curveangle, 3, 'X')
        dirVec = zAxis.copy()
        dirVec.rotate(divRotMat)

        #horizontal curvature variation
        dirVec.rotate(curveVarMat)

        if n == 0: #Special case for trunk splits
            dirVec.rotate(branchRotMat)

        #spread
        if n != 0: #Special case for trunk splits
            spreadMat = Matrix.Rotation(-spreadangle, 3, 'Y')
            dirVec.rotate(spreadMat)

        dirVec.rotate(dir)

        stem.splitlast = 1#numSplit #keep track of numSplit for next stem

    else:
        # If there are no splits then generate the growth direction without accounting for spreading of stems
        dirVec = zAxis.copy()
        divRotMat = Matrix.Rotation(curveangle, 3, 'X')
        dirVec.rotate(divRotMat)

        #horizontal curvature variation
        dirVec.rotate(curveVarMat)

        dirVec.rotate(dir)

        stem.splitlast = 0#numSplit #keep track of numSplit for next stem

    # Introduce upward curvature
    upRotAxis = xAxis.copy()
    upRotAxis.rotate(dirVec.to_track_quat('Z', 'Y'))
    curveUpAng = curveUp(stem.vertAtt, dirVec.to_track_quat('Z', 'Y'), stem.segMax)
    upRotMat = Matrix.Rotation(-curveUpAng, 3, upRotAxis)
    dirVec.rotate(upRotMat)

    dirVec.normalize()
    dirVec *= stem.segL * tf

    # Get the end point position
    end_co = stem.p.co.copy() + dirVec

    stem.spline.bezier_points.add()
    newPoint = stem.spline.bezier_points[-1]
    (newPoint.co, newPoint.handle_left_type, newPoint.handle_right_type) = (end_co, hType, hType)

    newRadius = stem.radS*(1 - (stem.seg + 1)/stem.segMax) + stem.radE*((stem.seg + 1)/stem.segMax)
    if numSplit > 0:
        newRadius = max(newRadius * splitR2, minRadius)
        stem.radS = max(stem.radS * splitR2, minRadius)
        stem.radE = max(stem.radE * splitR2, minRadius) # * 1
    newRadius = max(newRadius, stem.radE)
    if (stem.seg == stem.segMax-1) and closeTip:
        newRadius = 0.0
    newPoint.radius = newRadius

    # Set bezier handles for first point.
    if len(stem.spline.bezier_points) == 2:
        tempPoint = stem.spline.bezier_points[0]
        if hType is 'AUTO':
            dirVec = zAxis.copy()
            dirVec.rotate(dir)
            dirVec = dirVec * stemsegL * 0.33
            (tempPoint.handle_left_type, tempPoint.handle_right_type) = ('ALIGNED', 'ALIGNED')
            tempPoint.handle_right = tempPoint.co + dirVec
            tempPoint.handle_left = tempPoint.co - dirVec
        elif hType is 'VECTOR':
            (tempPoint.handle_left_type, tempPoint.handle_right_type) = ('VECTOR', 'VECTOR')

    # Update the last point in the spline to be the newly added one
    stem.updateEnd()
    #return splineList