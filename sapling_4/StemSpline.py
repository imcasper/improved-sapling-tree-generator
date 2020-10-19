from random import choice


# This class will contain a part of the tree which needs to be extended and the required tree parameters
class StemSpline:
    def __init__(self, spline, curvature, curvatureV, attractUp, segments, maxSegs, segLength, childStems, stemRadStart, stemRadEnd, splineNum, ofst, pquat):
        self.spline = spline
        self.p = spline.bezier_points[-1]
        self.curv = curvature
        self.curvV = curvatureV
        self.vertAtt = attractUp
        self.seg = segments
        self.segMax = maxSegs
        self.segL = segLength
        self.children = childStems
        self.radS = stemRadStart
        self.radE = stemRadEnd
        self.splN = splineNum
        self.offsetLen = ofst
        self.patentQuat = pquat

        self.curvSignx = choice([1, -1])
        self.curvSigny = choice([1, -1])
        self.splitSignx = choice([1, -1])
        self.splitSigny = choice([1, -1])

    # This method determines the quaternion of the end of the spline
    def quat(self):
        if len(self.spline.bezier_points) == 1:
            return ((self.spline.bezier_points[-1].handle_right - self.spline.bezier_points[-1].co).normalized()).to_track_quat('Z', 'Y')
        else:
            return ((self.spline.bezier_points[-1].co - self.spline.bezier_points[-2].co).normalized()).to_track_quat('Z', 'Y')
    # Update the end of the spline and increment the segment count
    def updateEnd(self):
        self.p = self.spline.bezier_points[-1]
        self.seg += 1