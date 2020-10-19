from collections import OrderedDict
from math import copysign, atan2, sin, cos, pi
from random import uniform, randint

from mathutils import Vector, Matrix

from .utils import tau, zAxis, convertQuat, roundBone
from .shape_ratio import shape_ratio
from .StemSpline import StemSpline
from .TreeSettings import TreeSettings


def fabricate_stems(tree_settings: TreeSettings, addsplinetobone, addstem, baseSize, childP, cu, leafDist, leaves, leafType, n, scaleVal, storeN, boneStep):

    #prevent baseSize from going to 1.0
    baseSize = min(0.999, baseSize)

    # Store the old rotation to allow new stems to be rotated away from the previous one.
    oldRotate = 0

    #use fancy child point selection / rotation
    if (n == 1) and (tree_settings.rMode != "original"):
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
            if tree_settings.rMode == "rotate":
                if tree_settings.rotate[n] < 0.0:
                    oldRotate = -copysign(tree_settings.rotate[n], oldRotate)
                else:
                    oldRotate += tree_settings.rotate[n]
                bRotate = oldRotate + uniform(-tree_settings.rotateV[n], tree_settings.rotateV[n])

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
                bL = br.lengthPar * tree_settings.length[1] * shape_ratio(tree_settings.shape, (1 - br.offset) / (1 - baseSize), custom=tree_settings.customShape)

                #account for down angle
                if tree_settings.downAngleV[1] > 0:
                    downA = tree_settings.downAngle[n] + (-tree_settings.downAngleV[n] * (1 - (1 - br.offset) / (1 - baseSize)) ** 2)
                else:
                    downA = tree_settings.downAngle[n]
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

            elif tree_settings.rMode == 'distance':
                for i, br in enumerate(p):
                    rotV = tree_settings.rotateV[n] * .5
                    bRotate = tree_settings.rotate[n] * br.index
                    bL = br.lengthPar * tree_settings.length[1] * shape_ratio(tree_settings.shape, (1 - br.stemOffset) / (1 - baseSize), custom=tree_settings.customShape)
                    if tree_settings.downAngleV[1] > 0:
                        downA = tree_settings.downAngle[n] + (-tree_settings.downAngleV[n] * (1 - (1 - br.stemOffset) / (1 - baseSize)) ** 2)
                    else:
                        downA = tree_settings.downAngle[n]

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
                        bL = branch.lengthPar * tree_settings.length[1] * shape_ratio(tree_settings.shape, (1 - branch.stemOffset) / (1 - baseSize), custom=tree_settings.customShape)
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
        newSpline.material_index = tree_settings.matIndex[n]
        #cu.resolution_u = resU
        newPoint = newSpline.bezier_points[-1]
        newPoint.co = p.co
        tempPos = zAxis.copy()
        # If the -ve flag for downAngle is used we need a special formula to find it
        if tree_settings.useOldDownAngle:
            if tree_settings.downAngleV[n] < 0.0:
                downV = tree_settings.downAngleV[n] * (1 - 2 * (.2 + .8 * ((1 - p.offset) / (1 - baseSize))))
            # Otherwise just find a random value
            else:
                downV = uniform(-tree_settings.downAngleV[n], tree_settings.downAngleV[n])
        else:
            if tree_settings.downAngleV[n] < 0.0:
                downV = uniform(-tree_settings.downAngleV[n], tree_settings.downAngleV[n])
            else:
                downV = -tree_settings.downAngleV[n] * (1 - (1 - p.stemOffset) / (1 - baseSize)) ** 2 #(110, 80) = (60, -50)

        if p.offset == 1:
            downRotMat = Matrix.Rotation(0, 3, 'X')
        else:
            downRotMat = Matrix.Rotation(tree_settings.downAngle[n] + downV, 3, 'X')

        # If the -ve flag for rotate is used we need to find which side of the stem the last child point was and then grow in the opposite direction.
        if tree_settings.rotate[n] < 0.0:
            oldRotate = -copysign(tree_settings.rotate[n], oldRotate)
        # Otherwise just generate a random number in the specified range
        else:
            oldRotate += tree_settings.rotate[n]
        bRotate = oldRotate + uniform(-tree_settings.rotateV[n], tree_settings.rotateV[n])

        if (n == 1) and  (tree_settings.rMode in ["rotate", 'distance']):
            bRotate = rot_a[i]

        rotMat = Matrix.Rotation(bRotate, 3, 'Z')

        # Rotate the direction of growth and set the new point coordinates
        tempPos.rotate(downRotMat)
        tempPos.rotate(rotMat)

        #use quat angle
        if (n == 1) and (p.offset != 1):
            if tree_settings.useParentAngle:
                tempPos.rotate(convertQuat(p.quat))
        else:
            tempPos.rotate(p.quat)

        newPoint.handle_right = p.co + tempPos * 0.33

        # Find branch length and the number of child stems.
        maxbL = scaleVal
        for l in tree_settings.length[:n+1]:
            maxbL *= l
        lMax = tree_settings.length[n] # * uniform(1 - lenV, 1 + lenV)
        if n == 1:
            lShape = shape_ratio(tree_settings.shape, (1 - p.stemOffset) / (1 - baseSize), custom=tree_settings.customShape)
        else:
            lShape = shape_ratio(tree_settings.shapeS, (1 - p.stemOffset) / (1 - baseSize))
        branchL = p.lengthPar * lMax * lShape
        childStems = tree_settings.branches[min(3, n + 1)] * (0.1 + 0.9 * (branchL / maxbL))

        # If this is the last level before leaves then we need to generate the child points differently
        if (storeN == tree_settings.levels - 1):
            if leafType == '4':
                childStems = 0 #False
            else:
                childStems = leaves * (0.1 + 0.9 * (branchL / maxbL)) * shape_ratio(leafDist, (1 - p.offset))

        #print("n=%d, levels=%d, n'=%d, childStems=%s"%(n, levels, storeN, childStems))

        # Determine the starting and ending radii of the stem using the tapering of the stem
        #startRad = min((p.radiusPar[0] * ((branchL / p.lengthPar) ** ratioPower)) * radiusTweak[n], 10)
        ratio = (p.radiusPar[0] - p.radiusPar[2]) / p.lengthPar
        startRad = min(((ratio * branchL) ** tree_settings.ratioPower) * tree_settings.radiusTweak[n], p.radiusPar[1])#p.radiusPar[1] #10
        #startRad = min((ratio * p.lengthPar * ((branchL / p.lengthPar) ** ratioPower)) * radiusTweak[n], 10)#p.radiusPar[1]
        #p.radiusPar[2] is parent end radius
        if p.offset == 1:
            startRad = p.radiusPar[1]
        endRad = (startRad * (1 - tree_settings.taper[n])) ** tree_settings.ratioPower
        startRad = max(startRad, tree_settings.minRadius)
        endRad = max(endRad, tree_settings.minRadius)
        newPoint.radius = startRad

        # stem curvature
        curveVal = tree_settings.curve[n] / tree_settings.curveRes[n]
        curveVar = tree_settings.curveV[n] / tree_settings.curveRes[n]

        #curveVal = curveVal * (branchL / scaleVal)

        # Add the new stem to list of stems to grow and define which bone it will be parented to
        nstem = StemSpline(newSpline, curveVal, curveVar, tree_settings.attractUp[n], 0, tree_settings.curveRes[n], branchL / tree_settings.curveRes[n], childStems,
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