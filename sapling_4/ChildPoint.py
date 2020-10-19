# This class contains the data for a point where a new branch will sprout
class ChildPoint:
    def __init__(self, coords, quat, radiusPar, offset, sOfst, lengthPar, parBone):
        self.co = coords
        self.quat = quat
        self.radiusPar = radiusPar
        self.offset = offset
        self.stemOffset = sOfst
        self.lengthPar = lengthPar
        self.parBone = parBone