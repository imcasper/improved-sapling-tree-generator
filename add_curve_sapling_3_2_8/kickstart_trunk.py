from math import pi
from random import uniform

from mathutils import Vector, Matrix

from .utils import zAxis
from .StemSpline import StemSpline
from .TreeSettings import TreeSettings


def kickstart_trunk(tree_settings: TreeSettings, addstem, leaves, cu, scaleVal):
    newSpline = cu.splines.new('BEZIER')
    newSpline.material_index = tree_settings.matIndex[0]
    #cu.resolution_u = resU
    newPoint = newSpline.bezier_points[-1]
    newPoint.co = Vector((0, 0, 0))

    #start trunk rotation with downAngle
    tempPos = zAxis.copy()
    downAng = tree_settings.downAngle[0] - .5 * pi
    downAng = downAng + uniform(-tree_settings.downAngleV[0], tree_settings.downAngleV[0])
    downRot = Matrix.Rotation(downAng, 3, 'X')
    tempPos.rotate(downRot)
    handle = tempPos
    newPoint.handle_right = handle
    newPoint.handle_left = -handle

    branchL = scaleVal * tree_settings.length[0]
    curveVal = tree_settings.curve[0] / tree_settings.curveRes[0]
    #curveVal = curveVal * (branchL / scaleVal)
    if tree_settings.levels == 1:
        childStems = leaves
    else:
        childStems = tree_settings.branches[1]
    startRad = scaleVal * tree_settings.ratio * tree_settings.scale0 * uniform(1-tree_settings.scaleV0, 1+tree_settings.scaleV0)
    endRad = (startRad * (1 - tree_settings.taper[0])) ** tree_settings.ratioPower
    startRad = max(startRad, tree_settings.minRadius)
    endRad = max(endRad, tree_settings.minRadius)
    newPoint.radius = startRad * tree_settings.rootFlare
    addstem(
        StemSpline(newSpline, curveVal, tree_settings.curveV[0] / tree_settings.curveRes[0], tree_settings.attractUp[0], 0, tree_settings.curveRes[0], branchL / tree_settings.curveRes[0],
                   childStems, startRad, endRad, 0, 0, None))
