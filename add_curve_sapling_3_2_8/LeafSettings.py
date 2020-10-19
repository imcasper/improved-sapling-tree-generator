from math import radians
from .leaf_rot import leaf_rot


class LeafSettings:
    def __init__(self, props):
        self.leafType = props.leafType
        self.leafDownAngle = radians(props.leafDownAngle)
        self.leafDownAngleV = radians(props.leafDownAngleV)
        self.leafRotate = radians(props.leafRotate)
        self.leafRotateV = radians(props.leafRotateV)
        self.leafScale = props.leafScale  #
        self.leafScaleX = props.leafScaleX  #
        self.leafScaleT = props.leafScaleT
        self.leafScaleV = props.leafScaleV
        self.leafShape = props.leafShape
        self.leafDupliObj = props.leafDupliObj
        self.leafangle = props.leafangle
        self.horzLeaves = props.horzLeaves
        self.leafDist = int(props.leafDist)  #

        self.leafObjY = props.leafObjY
        self.leafObjZ = props.leafObjZ
        self.leafObjRot = leaf_rot(self.leafObjY, self.leafObjZ)

