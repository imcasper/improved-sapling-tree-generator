class ArmatureSettings:
    def __init__(self, props):
        self.useArm = props.useArm
        self.previewArm = props.previewArm
        self.armAnim = props.armAnim
        self.leafAnim = props.leafAnim
        self.frameRate = props.frameRate
        self.loopFrames = props.loopFrames

        # self.windSpeed = props.windSpeed
        # self.windGust = props.windGust

        self.wind = props.wind
        self.gust = props.gust
        self.gustF = props.gustF

        self.af1 = props.af1
        self.af2 = props.af2
        self.af3 = props.af3

        self.makeMesh = props.makeMesh
        self.armLevels = props.armLevels

        self.boneStep = [1, 1, 1, 1]

        if self.makeMesh:
            self.boneStep = props.boneStep
