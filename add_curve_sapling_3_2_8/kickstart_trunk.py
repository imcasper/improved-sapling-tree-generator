from math import pi
from random import uniform

from mathutils import Vector, Matrix

from .utils import zAxis
from .StemSpline import StemSpline


def kickstart_trunk(addstem, levels, leaves, branches, cu, downAngle, downAngleV, curve, curveRes, curveV, attractUp, length, lengthV,
                    ratio, ratioPower, resU, scale0, scaleV0, scaleVal, taper, minRadius, rootFlare, matIndex):
    newSpline = cu.splines.new('BEZIER')
    newSpline.material_index = matIndex[0]
    #cu.resolution_u = resU
    newPoint = newSpline.bezier_points[-1]
    newPoint.co = Vector((0, 0, 0))

    #start trunk rotation with downAngle
    tempPos = zAxis.copy()
    downAng = downAngle[0] - .5 * pi
    downAng = downAng + uniform(-downAngleV[0], downAngleV[0])
    downRot = Matrix.Rotation(downAng, 3, 'X')
    tempPos.rotate(downRot)
    handle = tempPos
    newPoint.handle_right = handle
    newPoint.handle_left = -handle

    branchL = scaleVal * length[0]
    curveVal = curve[0] / curveRes[0]
    #curveVal = curveVal * (branchL / scaleVal)
    if levels == 1:
        childStems = leaves
    else:
        childStems = branches[1]
    startRad = scaleVal * ratio * scale0 * uniform(1-scaleV0, 1+scaleV0)
    endRad = (startRad * (1 - taper[0])) ** ratioPower
    startRad = max(startRad, minRadius)
    endRad = max(endRad, minRadius)
    newPoint.radius = startRad * rootFlare
    addstem(
        StemSpline(newSpline, curveVal, curveV[0] / curveRes[0], attractUp[0], 0, curveRes[0], branchL / curveRes[0],
                   childStems, startRad, endRad, 0, 0, None))