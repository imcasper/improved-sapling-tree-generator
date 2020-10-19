from .utils import to_rad


class TreeSettings:
    def __init__(self, props):
        self.levels = props.levels  #
        self.length = props.length  #
        self.lengthV = props.lengthV  #
        self.taperCrown = props.taperCrown
        self.branches = props.branches  #
        self.curveRes = props.curveRes  #
        self.curve = to_rad(props.curve)  #
        self.curveV = to_rad(props.curveV)  #
        self.curveBack = to_rad(props.curveBack)  #
        self.baseSplits = props.baseSplits  #
        self.segSplits = props.segSplits  #
        self.splitByLen = props.splitByLen
        self.rMode = props.rMode
        self.splitStraight = props.splitStraight
        self.splitLength = props.splitLength
        self.splitAngle = to_rad(props.splitAngle)  #
        self.splitAngleV = to_rad(props.splitAngleV)  #
        self.scale = props.scale  #
        self.scaleV = props.scaleV  #
        self.attractUp = props.attractUp  #
        self.attractOut = props.attractOut
        self.shape = int(props.shape)  #
        self.shapeS = int(props.shapeS)  #
        self.customShape = props.customShape
        self.branchDist = props.branchDist
        self.nrings = props.nrings
        self.baseSize = props.baseSize
        self.baseSize_s = props.baseSize_s
        self.leafBaseSize = props.leafBaseSize
        self.splitHeight = props.splitHeight
        self.splitBias = props.splitBias
        self.ratio = props.ratio
        self.minRadius = props.minRadius
        self.closeTip = props.closeTip
        self.rootFlare = props.rootFlare
        self.splitRadiusRatio = props.splitRadiusRatio
        self.autoTaper = props.autoTaper
        self.taper = props.taper  #
        self.noTip = props.noTip
        self.radiusTweak = props.radiusTweak
        self.ratioPower = props.ratioPower  #
        self.downAngle = to_rad(props.downAngle)  #
        self.downAngleV = to_rad(props.downAngleV)  #
        self.rotate = to_rad(props.rotate)  #
        self.rotateV = to_rad(props.rotateV)  #
        self.scale0 = props.scale0  #
        self.scaleV0 = props.scaleV0  #

        self.useOldDownAngle = props.useOldDownAngle
        self.useParentAngle = props.useParentAngle

        self.matIndex = props.matIndex

        self.bevelRes = props.bevelRes  #
        self.resU = props.resU  #

        # Some effects can be turned ON and OFF, the necessary variables are changed here
        self.bevelDepth = 0.0
        if props.bevel:
            self.bevelDepth = 1.0

        self.handles = 'VECTOR'
        if props.handleType == '0':
            self.handles = 'AUTO'
