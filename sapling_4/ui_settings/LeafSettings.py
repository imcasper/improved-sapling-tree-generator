from math import radians
from ..leaf_rot import leaf_rot
from typing import List


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
        self.leafLevel = int(props.leafLevel)  #
        self.leafDist = int(props.leafDist)  #

        # leafObjX = props.leafObjX
        self.leafObjY = props.leafObjY
        self.leafObjZ = props.leafObjZ
        self.leafObjRot = leaf_rot(self.leafObjY, self.leafObjZ)

        self.leaves = 0
        if props.showLeaves:
            self.leaves = props.leaves

        self.leafVertSize = {'hex': 6, 'rect': 4, 'dFace': 4, 'dVert': 1}[self.leafShape]

    def get_uv_list(self):
        if self.leafShape == 'hex':
            hex_x_adj: List[float] = [0, 1, 1, 0, 0, 0, -1, -1]
            hex_base_x: List[float] = [.5, 0, 0, .5, .5, .5, 1, 1]
            hex_base_y: List[float] = [0, 1 / 3, 2 / 3, 1, 0, 1, 2 / 3, 1 / 3]
            return hex_x_adj, hex_base_x, hex_base_y
        if self.leafShape == 'rect':
            rect_x_adj: List[float] = [-1, -1, 1, 1]
            rect_base_x: List[float] = [1, 1, 0, 0]
            rect_base_y: List[float] = [0, 1, 1, 0]
            return rect_x_adj, rect_base_x, rect_base_y
