from math import atan2, radians, sqrt, pi
from random import uniform, choice

import bpy
from mathutils import Matrix, Euler

from .utils import declination, angle_mean, convert_quat, zAxis, tau, xAxis, curve_up, round_bone
from .StemSpline import StemSpline


# This is the function which extends (or grows) a given stem.
def grow_spline(n, stem, numSplit, splitAng, splitAngV, splitStraight, splineList, hType, splineToBone, closeTip, splitRadiusRatio,
                minRadius, kp, splitHeight, outAtt, splitLength, lenVar, taperCrown, boneStep, rotate, rotateV, matIndex):

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
    tf = 1.0 #disabled

    #outward attraction
    if (n >= 0) and (kp > 0) and (outAtt > 0):
        p = stem.p.co.copy()
        d = atan2(p[0], -p[1])# + tau
        edir = dir.to_euler('XYZ', Euler((0, 0, d), 'XYZ'))
        d = angle_mean(edir[2], d, (kp * outAtt))
        dirv = Euler((edir[0], edir[1], d), 'XYZ')
        dir = dirv.to_quaternion()

    if n == 0:
        dir = convert_quat(dir)

    if n != 0:
        splitLength = 0

    # If the stem splits, we need to add new splines etc
    if numSplit > 0:
        # Get the curve data
        cuData = stem.spline.id_data.name
        cu = bpy.data.curves[cuData]

        #calc split angles
        splitAng = splitAng/2
        if n == 0:
            angle = splitAng + uniform(-splitAngV, splitAngV)
        else:
            #angle = stem.splitSigny * (splitAng + uniform(-splitAngV, splitAngV))
            #stem.splitSigny = -stem.splitSigny
            angle = choice([1, -1]) * (splitAng + uniform(-splitAngV, splitAngV))
        if n > 0:
            #make branches flatter
            angle *= max(1 - declination(dir) / 90, 0) * .67 + .33

        spreadangle = stem.splitSignx * (splitAng + uniform(-splitAngV, splitAngV))
        stem.splitSignx = -stem.splitSignx

        branchStraightness = splitStraight#0
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
            lenV = (1-splitLength) * uniform(1-lenVar, 1+(splitLength * lenVar))
            lenV = max(lenV, 0.01) * tf
            bScale = min(lenV, 1)

            #split radius factor
            splitR = splitRadiusRatio #0.707 #sqrt(1/(numSplit+1))

            if splitRadiusRatio == 0:
                splitR1 = sqrt(.5 * bScale)
                splitR2 = sqrt(1 - (.5 * bScale))
#            elif splitRadiusRatio == -1:
#                ra = lenV / (lenV + 1)
#                splitR1 = sqrt(ra)
#                splitR2 = sqrt(1-ra)
#            elif splitRadiusRatio == 0:
#                splitR1 = sqrt(0.5) * bScale
#                splitR2 = sqrt(1 - splitR1*splitR1)
#
#                #splitR2 = sqrt(1 - (0.5 * (1-splitLength)))
            else:
                splitR1 = splitR * bScale
                splitR2 = splitR

            newSpline = cu.splines.new('BEZIER')
            newSpline.material_index = matIndex[n]
            newPoint = newSpline.bezier_points[-1]
            (newPoint.co, newPoint.handle_left_type, newPoint.handle_right_type) = (stem.p.co, 'VECTOR', 'VECTOR')
            newRadius = (stem.radS*(1 - stem.seg/stem.segMax) + stem.radE*(stem.seg/stem.segMax)) * splitR1
            newRadius = max(newRadius, minRadius)
            newPoint.radius = newRadius

            # Here we make the new "sprouting" stems diverge from the current direction
            divRotMat = Matrix.Rotation(angle * (1+branchStraightness) - curveangle, 3, 'X')
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
                spreadMat = Matrix.Rotation(spreadangle * (1+branchStraightness), 3, 'Y')
                dirVec.rotate(spreadMat)

            dirVec.rotate(dir)

            # Introduce upward curvature
            upRotAxis = xAxis.copy()
            upRotAxis.rotate(dirVec.to_track_quat('Z', 'Y'))
            curveUpAng = curve_up(stem.vertAtt, dirVec.to_track_quat('Z', 'Y'), stem.segMax)
            upRotMat = Matrix.Rotation(-curveUpAng, 3, upRotAxis)
            dirVec.rotate(upRotMat)

            # Make the growth vec the length of a stem segment
            dirVec.normalize()

            #split length variation
            stemL = stem.segL * lenV
            dirVec *= stemL * tf
            ofst = stem.offsetLen + (stem.segL * (len(stem.spline.bezier_points) - 1))

            # Get the end point position
            end_co = stem.p.co.copy()

            # Add the new point and adjust its coords, handles and radius
            newSpline.bezier_points.add(1)
            newPoint = newSpline.bezier_points[-1]
            (newPoint.co, newPoint.handle_left_type, newPoint.handle_right_type) = (end_co + dirVec, hType, hType)

            newRadius = (stem.radS*(1 - (stem.seg + 1)/stem.segMax) + stem.radE*((stem.seg + 1)/stem.segMax)) * splitR1
            newRadius = max(newRadius, minRadius)
            nRadS = max(stem.radS * splitR1, minRadius)
            nRadE = max(stem.radE * splitR1, minRadius)
            if (stem.seg == stem.segMax-1) and closeTip:
                newRadius = 0.0
            newPoint.radius = newRadius

            # Add nstem to splineList
            nstem = StemSpline(newSpline, stem.curv, stem.curvV, stem.vertAtt, stem.seg + 1, stem.segMax, stemL, stem.children,
                               nRadS, nRadE, len(cu.splines) - 1, ofst, stem.quat())
            nstem.splitlast = 1 #numSplit #keep track of numSplit for next stem
            nstem.rLast = branchRot + pi
            nstem.splitSignx = stem.splitSignx
            if hasattr(stem, 'isFirstTip'):
                nstem.isFirstTip = True
            splineList.append(nstem)
            bone = 'bone'+(str(stem.splN)).rjust(3, '0')+'.'+(str(len(stem.spline.bezier_points)-2)).rjust(3, '0')
            bone = round_bone(bone, boneStep[n])
            splineToBone.append((bone, False, True, len(stem.spline.bezier_points)-2))

        # The original spline also needs to keep growing so adjust its direction too
        divRotMat = Matrix.Rotation(-angle * (1-branchStraightness) - curveangle, 3, 'X')
        dirVec = zAxis.copy()
        dirVec.rotate(divRotMat)

        #horizontal curvature variation
        dirVec.rotate(curveVarMat)

        if n == 0: #Special case for trunk splits
            dirVec.rotate(branchRotMat)

        #spread
        if n != 0: #Special case for trunk splits
            spreadMat = Matrix.Rotation(-spreadangle * (1-branchStraightness), 3, 'Y')
            dirVec.rotate(spreadMat)

        dirVec.rotate(dir)

        stem.splitlast = 1 #numSplit #keep track of numSplit for next stem

    else:
        # If there are no splits then generate the growth direction without accounting for spreading of stems
        dirVec = zAxis.copy()
        divRotMat = Matrix.Rotation(-curveangle, 3, 'X')
        dirVec.rotate(divRotMat)

        #horizontal curvature variation
        dirVec.rotate(curveVarMat)

        dirVec.rotate(dir)

        stem.splitlast = 0 #numSplit #keep track of numSplit for next stem

    # Introduce upward curvature
    upRotAxis = xAxis.copy()
    upRotAxis.rotate(dirVec.to_track_quat('Z', 'Y'))
    curveUpAng = curve_up(stem.vertAtt, dirVec.to_track_quat('Z', 'Y'), stem.segMax)
    upRotMat = Matrix.Rotation(-curveUpAng, 3, upRotAxis)
    dirVec.rotate(upRotMat)

    dirVec.normalize()
    dirVec *= stem.segL * tf

    # Get the end point position
    end_co = stem.p.co.copy() + dirVec

    stem.spline.bezier_points.add(1)
    newPoint = stem.spline.bezier_points[-1]
    (newPoint.co, newPoint.handle_left_type, newPoint.handle_right_type) = (end_co, hType, hType)

    newRadius = stem.radS*(1 - (stem.seg + 1)/stem.segMax) + stem.radE*((stem.seg + 1)/stem.segMax)
    if numSplit > 0:
        newRadius = max(newRadius * splitR2, minRadius)
        stem.radS = max(stem.radS * splitR2, minRadius)
        stem.radE = max(stem.radE * splitR2, minRadius)
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
            dirVec = dirVec * stem.segL * 0.33
            (tempPoint.handle_left_type, tempPoint.handle_right_type) = ('ALIGNED', 'ALIGNED')
            tempPoint.handle_right = tempPoint.co + dirVec
            tempPoint.handle_left = tempPoint.co - dirVec
        elif hType is 'VECTOR':
            (tempPoint.handle_left_type, tempPoint.handle_right_type) = ('VECTOR', 'VECTOR')

    # Update the last point in the spline to be the newly added one
    stem.updateEnd()