from collections import deque

from .utils import evalBez, evalBezTan
from .ChildPoint import ChildPoint


def interp_stem(stem, tVals, maxOffset, baseSize):
    points = stem.spline.bezier_points
    numSegs = len(points) - 1
    stemLen = stem.segL * numSegs

    checkBottom = stem.offsetLen / maxOffset
    checkTop = checkBottom + (stemLen / maxOffset)

    # Loop through all the parametric values to be determined
    tempList = deque()
    for t in tVals:
        if (t >= checkBottom) and (t <= checkTop) and (t < 1.0):
            scaledT = (t - checkBottom) / (checkTop - checkBottom)
            ofst = ((t - baseSize) / (checkTop - baseSize)) * (1 - baseSize) + baseSize

            length = numSegs * scaledT
            index = int(length)
            tTemp = length - index

            coord = evalBez(points[index].co, points[index].handle_right, points[index+1].handle_left, points[index+1].co, tTemp)
            quat = (evalBezTan(points[index].co, points[index].handle_right, points[index+1].handle_left, points[index+1].co, tTemp)).to_track_quat('Z', 'Y')
            radius = (1-tTemp)*points[index].radius + tTemp*points[index+1].radius # radius at the child point

            tempList.append(ChildPoint(coord, quat, (stem.radS, radius, stem.radE), t, ofst, stem.segMax * stem.segL, 'bone' + (str(stem.splN).rjust(3, '0')) + '.' + (str(index).rjust(3, '0'))))
        elif t == 1:
            #add stems at tip
            index = numSegs-1
            coord = points[-1].co
            quat = (points[-1].handle_right - points[-1].co).to_track_quat('Z', 'Y')
            radius = points[-1].radius
            tempList.append(ChildPoint(coord, quat, (stem.radS, radius, stem.radE), 1, 1, stem.segMax * stem.segL, 'bone' + (str(stem.splN).rjust(3, '0')) + '.' + (str(index).rjust(3, '0'))))

    return tempList