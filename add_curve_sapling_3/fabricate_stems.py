from collections import OrderedDict
from math import copysign, atan2, sin, cos, pi
from random import uniform, randint

from mathutils import Vector, Matrix

from .utils import tau, zAxis, convertQuat, roundBone
from .shape_ratio import shape_ratio
from .StemSpline import StemSpline


def fabricate_stems(addsplinetobone, addstem, baseSize, branches, childP, cu, curve, curveBack, curveRes, curveV, attractUp,
                    downAngle, downAngleV, leafDist, leaves, leafType, length, lengthV, levels, n, ratio, ratioPower, resU,
                    rotate, rotateV, scaleVal, shape, storeN, taper, shapeS, minRadius, radiusTweak, customShape, rMode, segSplits,
                    useOldDownAngle, useParentAngle, boneStep, matIndex):

    #prevent baseSize from going to 1.0
    baseSize = min(0.999, baseSize)

    # Store the old rotation to allow new stems to be rotated away from the previous one.
    oldRotate = 0

    #use fancy child point selection / rotation
    if (n == 1) and (rMode != "original"):
        childP_T = OrderedDict()
        childP_L = []
        for i, p in enumerate(childP):
            if p.offset == 1:
                childP_L.append(p)
            else:
                p.index = i
                if p.offset not in childP_T:
                    childP_T[p.offset] = [p]
                else:
                    childP_T[p.offset].append(p)

        childP_T = [childP_T[k] for k in sorted(childP_T.keys())]

        childP = []
        rot_a = []
        for p in childP_T:
            if rMode == "rotate":
                if rotate[n] < 0.0:
                    oldRotate = -copysign(rotate[n], oldRotate)
                else:
                    oldRotate += rotate[n]
                bRotate = oldRotate + uniform(-rotateV[n], rotateV[n])

                #find center of split branches
                #average
                cx = sum([a.co[0] for a in p]) / len(p)
                cy = sum([a.co[1] for a in p]) / len(p)
                #center of range
                #xc = [a.co[0] for a in p]
                #yc = [a.co[1] for a in p]
                #cx = (max(xc) + min(xc)) / 2
                #cy = (max(yc) + min(yc)) / 2

                center = Vector((cx, cy, 0))
                center2 = Vector((-cx, cy))

                #choose start point whose angle is closest to the rotate angle
                a1 = bRotate % tau
                a_diff = []
                for a in p:
                    a = a.co
                    a = a - center
                    a2 = atan2(a[0], -a[1])
                    d = min((a1-a2+tau)%tau, (a2-a1+tau)%tau)
                    a_diff.append(d)

                idx = a_diff.index(min(a_diff))

                #find branch end point

                br = p[idx]
                b = br.co
                vx = sin(bRotate)
                vy = cos(bRotate)
                v = Vector((vx, vy))

                bD = ((b[0] * b[0] + b[1] * b[1]) ** .5)

                #acount for length
                bL = br.lengthPar * length[1] * shape_ratio(shape, (1 - br.offset) / (1 - baseSize), custom=customShape)

                #account for down angle
                if downAngleV[1] > 0:
                    downA = downAngle[n] + (-downAngleV[n] * (1 - (1 - br.offset) / (1 - baseSize)) ** 2)
                else:
                    downA = downAngle[n]
                if downA < (.5 * pi):
                    downA = sin(downA) ** 2
                    bL *= downA

                bL *= 0.33 #adjustment constant value
                v *= (bD + bL) #branch end point

                #find actual rotate angle from branch location
                bv = Vector((b[0], -b[1]))
                cv = v - bv - center2
                a = atan2(cv[0], cv[1])

                childP.append(p[idx])
                rot_a.append(a)

            elif rMode == 'distance':
                for i, br in enumerate(p):
                    rotV = rotateV[n] * .5
                    bRotate = rotate[n] * br.index
                    bL = br.lengthPar * length[1] * shape_ratio(shape, (1 - br.stemOffset) / (1 - baseSize), custom=customShape)
                    if downAngleV[1] > 0:
                        downA = downAngle[n] + (-downAngleV[n] * (1 - (1 - br.stemOffset) / (1 - baseSize)) ** 2)
                    else:
                        downA = downAngle[n]

                    downRotMat = Matrix.Rotation(downA, 3, 'X')
                    rotMat = Matrix.Rotation(bRotate, 3, 'Z')

                    bVec = zAxis.copy()
                    bVec.rotate(downRotMat)
                    bVec.rotate(rotMat)
                    bVec.rotate(convertQuat(br.quat))
                    bVec *= bL
                    p1 = bVec + br.co

                    #distance to other branches
                    isIntersect = []
                    for branch in p:
                        p2 = branch.co
                        p3 = p2 - p1
                        l = p3.length * uniform(1.0, 1.1)
                        bL = branch.lengthPar * length[1] * shape_ratio(shape, (1 - branch.stemOffset) / (1 - baseSize), custom=customShape)
                        isIntersect.append(l < bL)

                    del isIntersect[i]

                    if not any(isIntersect):
                        childP.append(br)
                        rot_a.append(bRotate + uniform(-rotV, rotV))

            else:
                idx = randint(0, len(p)-1)
                childP.append(p[idx])

        childP.extend(childP_L)
        rot_a.extend([0] * len(childP_L))

        oldRotate = 0

    for i, p in enumerate(childP):
        # Add a spline and set the coordinate of the first point.
        newSpline = cu.splines.new('BEZIER')
        newSpline.material_index = matIndex[n]
        cu.resolution_u = resU
        newPoint = newSpline.bezier_points[-1]
        newPoint.co = p.co
        tempPos = zAxis.copy()
        # If the -ve flag for downAngle is used we need a special formula to find it
        if useOldDownAngle:
            if downAngleV[n] < 0.0:
                downV = downAngleV[n] * (1 - 2 * (.2 + .8 * ((1 - p.offset) / (1 - baseSize))))
            # Otherwise just find a random value
            else:
                downV = uniform(-downAngleV[n], downAngleV[n])
        else:
            if downAngleV[n] < 0.0:
                downV = uniform(-downAngleV[n], downAngleV[n])
            else:
                downV = -downAngleV[n] * (1 - (1 - p.stemOffset) / (1 - baseSize)) ** 2 #(110, 80) = (60, -50)

        if p.offset == 1:
            downRotMat = Matrix.Rotation(0, 3, 'X')
        else:
            downRotMat = Matrix.Rotation(downAngle[n] + downV, 3, 'X')

        # If the -ve flag for rotate is used we need to find which side of the stem the last child point was and then grow in the opposite direction.
        if rotate[n] < 0.0:
            oldRotate = -copysign(rotate[n], oldRotate)
        # Otherwise just generate a random number in the specified range
        else:
            oldRotate += rotate[n]
        bRotate = oldRotate + uniform(-rotateV[n], rotateV[n])

        if (n == 1) and  (rMode in ["rotate", 'distance']):
            bRotate = rot_a[i]

        rotMat = Matrix.Rotation(bRotate, 3, 'Z')

        # Rotate the direction of growth and set the new point coordinates
        tempPos.rotate(downRotMat)
        tempPos.rotate(rotMat)

        #use quat angle
        if (n == 1) and (p.offset != 1):
            if useParentAngle:
                tempPos.rotate(convertQuat(p.quat))
        else:
            tempPos.rotate(p.quat)

        newPoint.handle_right = p.co + tempPos * 0.33

        # Find branch length and the number of child stems.
        maxbL = scaleVal
        for l in length[:n+1]:
            maxbL *= l
        lMax = length[n] # * uniform(1 - lenV, 1 + lenV)
        if n == 1:
            lShape = shape_ratio(shape, (1 - p.stemOffset) / (1 - baseSize), custom=customShape)
        else:
            lShape = shape_ratio(shapeS, (1 - p.stemOffset) / (1 - baseSize))
        branchL = p.lengthPar * lMax * lShape
        childStems = branches[min(3, n + 1)] * (0.1 + 0.9 * (branchL / maxbL))

        # If this is the last level before leaves then we need to generate the child points differently
        if (storeN == levels - 1):
            if leafType == '4':
                childStems = 0 #False
            else:
                childStems = leaves * (0.1 + 0.9 * (branchL / maxbL)) * shape_ratio(leafDist, (1 - p.offset))

        #print("n=%d, levels=%d, n'=%d, childStems=%s"%(n, levels, storeN, childStems))

        # Determine the starting and ending radii of the stem using the tapering of the stem
        #startRad = min((p.radiusPar[0] * ((branchL / p.lengthPar) ** ratioPower)) * radiusTweak[n], 10)
        ratio = (p.radiusPar[0] - p.radiusPar[2]) / p.lengthPar
        startRad = min(((ratio * branchL) ** ratioPower) * radiusTweak[n], p.radiusPar[1])#p.radiusPar[1] #10
        #startRad = min((ratio * p.lengthPar * ((branchL / p.lengthPar) ** ratioPower)) * radiusTweak[n], 10)#p.radiusPar[1]
        #p.radiusPar[2] is parent end radius
        if p.offset == 1:
            startRad = p.radiusPar[1]
        endRad = (startRad * (1 - taper[n])) ** ratioPower
        startRad = max(startRad, minRadius)
        endRad = max(endRad, minRadius)
        newPoint.radius = startRad

        # stem curvature
        curveVal = curve[n] / curveRes[n]
        curveVar = curveV[n] / curveRes[n]

        #curveVal = curveVal * (branchL / scaleVal)

        # Add the new stem to list of stems to grow and define which bone it will be parented to
        nstem = StemSpline(newSpline, curveVal, curveVar, attractUp[n], 0, curveRes[n], branchL / curveRes[n], childStems,
                           startRad, endRad, len(cu.splines) - 1, 0, p.quat)
        if (n == 1) and (p.offset == 1):
            nstem.isFirstTip = True
        addstem(nstem)

        bone = roundBone(p.parBone, boneStep[n-1])
        if p.offset == 1:
            isend = True
        else:
            isend = False
        addsplinetobone((bone, isend))