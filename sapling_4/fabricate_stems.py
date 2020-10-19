from collections import OrderedDict
from math import copysign, atan2, sin, cos, pi
from random import uniform, choice, randint

from mathutils import Vector, Matrix

from .utils import tau, zAxis, convert_quat, round_bone
from .StemSpline import StemSpline
from .shape_ratio import shape_ratio
from .TreeSettings import TreeSettings


def fabricate_stems(tree_settings: TreeSettings, addsplinetobone, addstem, baseSize, childP, cu,
                    leafDist, leaves, leafType, n,
                    scaleVal, shape, storeN, taper, shapeS,
                    useOldDownAngle, useParentAngle, boneStep, matIndex):

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
                bL = br.lengthPar * tree_settings.length[1] * shape_ratio(shape, (1 - br.offset) / (1 - baseSize), custom=tree_settings.customShape)

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
                cv = (v - center2) - bv
                a = atan2(cv[0], cv[1])

                childP.append(p[idx])
                rot_a.append(a)

            elif tree_settings.rMode == 'distance1': #distance1
                for i, br in enumerate(p):
                    rotV = tree_settings.rotateV[n] * .5
                    bRotate = tree_settings.rotate[n] * br.index
                    bL = br.lengthPar * tree_settings.length[1] * shape_ratio(shape, (1 - br.stemOffset) / (1 - baseSize), custom=tree_settings.customShape)
                    if tree_settings.downAngleV[1] > 0:
                        downA = tree_settings.downAngle[n] + (-tree_settings.downAngleV[n] * (1 - (1 - br.stemOffset) / (1 - baseSize)) ** 2)
                    else:
                        downA = tree_settings.downAngle[n]

                    downRotMat = Matrix.Rotation(downA, 3, 'X')
                    rotMat = Matrix.Rotation(bRotate, 3, 'Z')

                    bVec = zAxis.copy()
                    bVec.rotate(downRotMat)
                    bVec.rotate(rotMat)
                    bVec.rotate(convert_quat(br.quat))
                    bVec *= bL
                    p1 = bVec + br.co

                    #distance to other branches
                    isIntersect = []
                    for branch in p:
                        p2 = branch.co
                        p3 = p2 - p1
                        l = p3.length * uniform(1.0, 1.1)
                        bL = branch.lengthPar * tree_settings.length[1] * shape_ratio(shape, (1 - branch.stemOffset) / (1 - baseSize), custom=tree_settings.customShape)
                        isIntersect.append(l < bL)

                    del isIntersect[i]

                    if not any(isIntersect):
                        childP.append(br)
                        rot_a.append(bRotate + uniform(-rotV, rotV))

            elif tree_settings.rMode == 'distance': #distance2
                bRotate = oldRotate + tree_settings.rotate[n]

                cP = []
                rA = []
                bN = []
                for i, br in enumerate(p):
                    rotV = uniform(-tree_settings.rotateV[n]*.5, tree_settings.rotateV[n]*.5)

                    bL = br.lengthPar * tree_settings.length[1] * shape_ratio(shape, (1 - br.stemOffset) / (1 - baseSize), custom=tree_settings.customShape)
                    if tree_settings.downAngleV[1] > 0:
                        downA = tree_settings.downAngle[n] + (-tree_settings.downAngleV[n] * (1 - (1 - br.stemOffset) / (1 - baseSize)) ** 2)
                    else:
                        downA = tree_settings.downAngle[n]

                    downRotMat = Matrix.Rotation(downA, 3, 'X')
                    bRotate = bRotate + rotV
                    rotMat = Matrix.Rotation(bRotate, 3, 'Z')

                    bVec = zAxis.copy()
                    bVec.rotate(downRotMat)
                    bVec.rotate(rotMat)
                    bVec.rotate(convert_quat(br.quat))
                    bVec *= bL
                    p1 = bVec + br.co

                    #distance to other branches
                    isIntersect = []
                    dists = []
                    lengths = []
                    for branch in p:
                        p2 = branch.co
                        p3 = p2 - p1
                        l = p3.length#*rotateV[n]# * uniform(.90, 1.00) # (1.0, 1.1)
                        bL = branch.lengthPar * tree_settings.length[1] * shape_ratio(shape, (1 - branch.stemOffset) / (1 - baseSize), custom=tree_settings.customShape)
                        isIntersect.append(l < bL)

                        d = br.co - branch.co
                        dists.append(d.length)
                        lengths.append(bL)

                    del isIntersect[i]
                    del dists[i]
                    del lengths[i]

                    if len(dists) > 0:
                        #nearest = min(dists)
                        farthest = max(dists)
                        bL = lengths[dists.index(farthest)]
                        near = farthest < bL
                    else:
                        near = False

                    if not any(isIntersect):
                        cP.append(br)
                        rA.append(bRotate + rotV)
                        bN.append(near)

                #print(bN)

                if len(cP) == 1:
                    for i, br in enumerate(cP):
                        childP.append(br)
                        rot_a.append(rA[i])
                else:
                    nearcP = []
                    nearrA = []
                    for i, near in enumerate(bN):
                        if near:
                            nearcP.append(cP[i])
                            nearrA.append(rA[i])
                            #childP.append(cP[i])
                            #rot_a.append(rA[i])
                        else:
                            childP.append(cP[i])
                            rot_a.append(rA[i])

                    if len(nearcP) > 0:
                        i = choice(list(range(len(nearcP))))
                        childP.append(nearcP[i])
                        rot_a.append(nearrA[i])

                oldRotate += tree_settings.rotate[n]

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
        newPoint = newSpline.bezier_points[-1]
        newPoint.co = p.co
        tempPos = zAxis.copy()
        # If the -ve flag for downAngle is used we need a special formula to find it
        if useOldDownAngle:
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
            if useParentAngle:
                tempPos.rotate(convert_quat(p.quat))
        else:
            tempPos.rotate(p.quat)

        newPoint.handle_right = p.co + tempPos * 0.33

        # Find branch length and the number of child stems.
        maxbL = scaleVal
        for l in tree_settings.length[:n+1]:
            maxbL *= l
        lMax = tree_settings.length[n] * uniform(1 - tree_settings.lengthV[n], 1 + tree_settings.lengthV[n])
        if n == 1:
            lShape = shape_ratio(shape, (1 - p.stemOffset) / (1 - baseSize), custom=tree_settings.customShape)
            tShape = shape_ratio(shape, 0, custom=tree_settings.customShape)
        else:
            lShape = shape_ratio(shapeS, (1 - p.stemOffset) / (1 - baseSize))
            tShape = shape_ratio(shapeS, 0)
        branchL = p.lengthPar * lMax * lShape
        childStems = tree_settings.branches[min(3, n + 1)] * (0.1 + 0.9 * (branchL / maxbL))

        # If this is the last level before leaves then we need to generate the child points differently
        if (storeN == tree_settings.levels - 1):
            if leafType == '4':
                childStems = 0 #False
            else:
                childStems = leaves * (0.1 + 0.9 * (branchL / maxbL)) * shape_ratio(leafDist, (1 - p.offset))

        # Determine the starting and ending radii of the stem using the tapering of the stem
        #startRad = min((p.radiusPar[0] * ((branchL / p.lengthPar) ** ratioPower)) * radiusTweak[n], 10)
        #startRad = min((ratio * p.lengthPar * ((branchL / p.lengthPar) ** ratioPower)) * radiusTweak[n], 10)#p.radiusPar[1]

        #ratio = (p.radiusPar[0] - p.radiusPar[2]) / p.lengthPar
        #startRad = min(((ratio * branchL) ** ratioPower) * radiusTweak[n], p.radiusPar[1])#p.radiusPar[1] #10

        startRad = min(((p.radiusPar[2] * (1/tShape) * lShape) ** tree_settings.ratioPower) * tree_settings.radiusTweak[n], p.radiusPar[1])

        #p.radiusPar[0] is parent start radius
        #p.radiusPar[1] is parent radius
        #p.radiusPar[2] is parent end radius

        if p.offset == 1:
            startRad = p.radiusPar[1]
        endRad = (startRad * (1 - taper[n])) ** tree_settings.ratioPower
        startRad = max(startRad, tree_settings.minRadius)
        endRad = max(endRad, tree_settings.minRadius)
        newPoint.radius = startRad

        # stem curvature
        curveVal = tree_settings.curve[n] / tree_settings.curveRes[n]

        # Add the new stem to list of stems to grow and define which bone it will be parented to
        nstem = StemSpline(newSpline, curveVal, tree_settings.curveV[n], tree_settings.attractUp[n], 0, tree_settings.curveRes[n], branchL / tree_settings.curveRes[n], childStems,
                           startRad, endRad, len(cu.splines) - 1, 0, p.quat)
        if (n == 1) and (p.offset == 1):
            nstem.isFirstTip = True
        addstem(nstem)

        bone = round_bone(p.parBone, boneStep[n - 1])
        if p.offset == 1:
            isend = True
        else:
            isend = False
        addsplinetobone((bone, isend))