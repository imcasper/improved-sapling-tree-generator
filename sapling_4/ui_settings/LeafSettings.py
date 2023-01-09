from math import radians
from ..leaf_rot import leaf_rot
from ..settings_lists import axes, leafShapes
from typing import List


class LeafSettings:
    def __init__(self, props):
        self.leafLevel = int(props.leafLevel)
        self.leafType = props.leafType
        self.leafDownAngle = radians(props.leafDownAngle)
        self.leafDownAngleV = radians(props.leafDownAngleV)
        self.leafRotate = radians(props.leafRotate)
        self.leafRotateV = radians(props.leafRotateV)
        self.leafScale = props.leafScale  #
        self.leafScaleX = props.leafScaleX  #
        self.leafScaleT = props.leafScaleT
        self.leafScaleV = props.leafScaleV
        self.leafShape = leafShapes[props.leafShape][0]
        self.leafDupliObj = props.leafDupliObj
        self.leafangle = props.leafangle
        self.leafDist = int(props.leafDist)  #

        # leafObjX = props.leafObjX
        # print("objY: ", props.leafObjY, "\nobjZ: ", props.leafObjZ)
        self.leafObjY = axes[props.leafObjY][0]
        self.leafObjZ = axes[props.leafObjZ][0]

        # print("self.objY: ", self.leafObjY, "\nself.objZ: ", self.leafObjZ)
        self.leafObjRot = leaf_rot(self.leafObjY, self.leafObjZ)

        self.leaves = 0
        if props.showLeaves:
            self.leaves = props.leaves

        # print("props.leafShape: ", props.leafShape, "self.leafShape: ", self.leafShape)
        self.leafVertSize = {'hex': 6, 'rect': 4, 'dFace': 4, 'dVert': 1}[self.leafShape]

        # self.leafVertSize = props.leafShape

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
