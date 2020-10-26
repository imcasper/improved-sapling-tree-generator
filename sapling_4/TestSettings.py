import bpy
from bpy.props import IntVectorProperty, FloatProperty, BoolProperty, EnumProperty, IntProperty, FloatVectorProperty, \
    StringProperty
from .PropertyHolder import app_prop
from .default_extractor import default_extractor
from .settings_lists import settings, axes, handleList, branchmodes, shapeList3, shapeList4, attachmenttypes, leaftypes, leafShapes


class TestSettings(bpy.types.PropertyGroup):

    # def __init__(self):
    #     print("Test Init")
    #     self.uppdater
    #
    # def set_uppdater(self, uppdtr):
    #     self.uppdater = uppdtr

    def objectList(self, context):
        objects = []
        bObjects = bpy.data.objects
        for obj in bObjects:
            if (obj.type in ['MESH', 'CURVE', 'SURFACE']) and (obj.name not in ['tree', 'leaves']):
                objects.append((obj.name, obj.name, ""))

        return objects

    def update_tree(self, context):
        print("Test Update")
        # default_extractor(self)
        # app_prop(self)
        self.do_update = True
        # self.uppdater()

    def no_update_tree(self, context):
        print("Test No update")
        self.do_update = False

    def update_leaves(self, context):
        print("Test upd leafs")
        if self.showLeaves:
            self.do_update = True
        else:
            self.do_update = False

    do_update: BoolProperty(name='Do Update',
                            default=True, options={'HIDDEN'})

    # bevel: BoolProperty(name='Bevel',
    #                     description='Whether the curve is beveled',
    #                     default=False, update=update_tree)
    #
    # twilac_ugg: BoolProperty(name='TwUgg',
    #                     description='To See If PropHolder Gets This',
    #                     default=False, update=update_tree)
    #
    # bevelRes: IntProperty(name='Bevel Resolution',
    #                       description='The bevel resolution of the curves',
    #                       min=0,
    #                       max=32,
    #                       default=0, update=update_tree)
    # resU: IntProperty(name='Curve Resolution',
    #                   description='The resolution along the curves',
    #                   min=1,
    #                   default=4, update=update_tree)
    #
    # levels: IntProperty(name='Levels',
    #                     description='Number of recursive branches',
    #                     min=1,
    #                     max=6,
    #                     soft_max=4,
    #                     default=3, update=update_tree)

    chooseSet: EnumProperty(name='Settings',
        description='Choose the settings to modify',
        items=settings,
        default='0', update=no_update_tree)

    bevel: BoolProperty(name='Bevel',
        description='Whether the curve is beveled',
        default=False, update=update_tree)

    showLeaves: BoolProperty(name='Show Leaves',
        description='Whether the leaves are shown',
        default=False, update=update_tree)
    useArm: BoolProperty(name='Use Armature',
        description='Whether the armature is generated',
        default=False, update=update_tree)
    seed: IntProperty(name='Random Seed',
        description='The seed of the random number generator',
        default=0, update=update_tree)
    handleType: EnumProperty(name='Handle Type',
        description='The type of bezier curve handles',
        items=handleList,
        default='0', update=update_tree)

    bevelRes: IntProperty(name='Bevel Resolution',
        description='The bevel resolution of the curves',
        min=0,
        max=32,
        default=0, update=update_tree)
    resU: IntProperty(name='Curve Resolution',
        description='The resolution along the curves',
        min=1,
        default=4, update=update_tree)

    levels: IntProperty(name='Levels',
        description='Number of recursive branches',
        min=1,
        max=6,
        soft_max=4,
        default=3, update=update_tree)

    length: FloatVectorProperty(name='Length',
        description='The relative lengths of each branch level',
        min=0.000001,
        default=[1, 0.3, 0.6, 0.45],
        size=4, update=update_tree)
    lengthV: FloatVectorProperty(name='Length Variation',
        description='Branch and split length variations for each level',
        min=0.0,
        max=1.0,
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    taperCrown: FloatProperty(name='Taper Crown',
        description='Shorten trunk splits toward outside of tree',
        min=0.0,
        soft_max=1.0,
        default=0, update=update_tree)
    branches: IntVectorProperty(name='Branches',
        description='The number of branches grown at each level',
        min=0,
        default=[50, 30, 10, 10],
        size=4, update=update_tree)
    curveRes: IntVectorProperty(name='Curve Resolution',
        description='The number of segments on each branch',
        min=1,
        soft_max=16,
        default=[8, 5, 3, 1],
        size=4, update=update_tree)
    curve: FloatVectorProperty(name='Curvature',
        description='The angle of the end of the branch',
        default=[0, -40, -40, 0],
        size=4, update=update_tree)
    curveV: FloatVectorProperty(name='Curvature Variation',
        description='Variation of the curvature',
        default=[20, 50, 75, 0],
        size=4, update=update_tree)
    curveBack: FloatVectorProperty(name='Back Curvature',
        description='Curvature for the second half of a branch',
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    baseSplits: IntProperty(name='Base Splits',
        description='Number of trunk splits at its base',
        min=0,
        default=0, update=update_tree)
    segSplits: FloatVectorProperty(name='Segment Splits',
        description='Number of splits per segment',
        min=0,
        soft_max=1,
        max=3,
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    splitByLen: BoolProperty(name='Split relative to length',
        description='Split proportional to branch length',
        default=False, update=update_tree)
    rMode: EnumProperty(name="", #"Branching Mode"
        description='Branching and Rotation Mode',
        items=branchmodes,
        default="rotate", update=update_tree)
    splitStraight: FloatProperty(name="Split Straight",
        description="Straightness of trunk branch splits",
        min=0.0,
        max=1.0,
        default=0, update=update_tree)
    splitLength: FloatProperty(name="Split Length",
        description="Length of trunk branch splits, (similar to length variation but not random)",
        min=0.0,
        max=1.0,
        default=0, update=update_tree)
    splitAngle: FloatVectorProperty(name='Split Angle',
        description='Angle of branch splitting',
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    splitAngleV: FloatVectorProperty(name='Split Angle Variation',
        description='Variation in the split angle',
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    scale: FloatProperty(name='Scale',
        description='The tree scale',
        min=0.0,
        default=13.0, update=update_tree)
    scaleV: FloatProperty(name='Scale Variation',
        description='The variation in the tree scale',
        default=3.0, update=update_tree)
    attractUp: FloatVectorProperty(name='Vertical Attraction',
        description='Branch upward attraction',
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    attractOut: FloatVectorProperty(name='Outward Attraction',
        description='Branch outward attraction',
        default=[0, 0, 0, 0],
        min=0.0,
        max=1.0,
        size=4, update=update_tree)
    shape: EnumProperty(name='', #Shape
        description='The overall shape of the tree',
        items=shapeList3,
        default='7', update=update_tree)
    shapeS: EnumProperty(name='', #Secondary Branches Shape
        description='The shape of secondary splits',
        items=shapeList4,
        default='4', update=update_tree)
    customShape: FloatVectorProperty(name='',#Custom Shape
        description='Branch Length at \n(Base, Middle, Middle Position, Top)',
        size=4,
        min=.01,
        max=1,
        default=[.5, 1.0, .3, .5], update=update_tree)
    branchDist: FloatProperty(name='Branch Distribution',
        description='Adjust branch spacing to put more branches at the top or bottom of the tree',
        min=0.1,
        soft_max=10,
        default=1.0, update=update_tree)
    nrings: IntProperty(name='Whorls',
        description='number of whorls',
        min=0,
        default=0, update=update_tree)
    baseSize: FloatProperty(name='', # 'Trunk Height'
        description='Fraction of trunk with no branches (Base Size)',
        min=0.0,
        max=1.0,
        default=0.4, update=update_tree)
    baseSize_s: FloatProperty(name='', #Secondary Start Length
        description='Fraction of 2nd and higher levels with no branches',
        min=0.0,
        max=1.0,
        default=0.25, update=update_tree)
    leafBaseSize: FloatProperty(name='Leaf Start Length',
        description='Fraction of stem length with no leaves',
        min=0.0,
        max=1.0,
        default=0.20, update=update_tree)
    splitHeight: FloatProperty(name='Split Height',
        description='Fraction of tree height with no splits',
        min=0.0,
        max=1.0,
        default=0.2, update=update_tree)
    splitBias: FloatProperty(name='Split Bias',
        description='Put more splits at the top or bottom of the tree',
        soft_min=-2.0,
        soft_max=2.0,
        default=0.0, update=update_tree)
    ratio: FloatProperty(name='Ratio',
        description='Ratio of tree scale to base radius',
        min=0.0,
        default=0.015, update=update_tree)
    minRadius: FloatProperty(name='Minimum Radius',
        description='Minimum branch Radius',
        min=0.0,
        default=0.0, update=update_tree)
    closeTip: BoolProperty(name='Close Tip',
        description='Set radius at branch tips to zero',
        default=False, update=update_tree)
    rootFlare: FloatProperty(name='Root Flare',
        description='Root radius factor',
        min=1.0,
        default=1.0, update=update_tree)
    splitRadiusRatio: FloatProperty(name='Split Radius Ratio',
        description='Reduce radius after branch splits, (0 is auto)',
        min=0.0,
        max=1.0,
        default=0.75, update=update_tree)
    autoTaper: BoolProperty(name='Auto Taper',
        description='Calculate taper automaticly based on branch lengths',
        default=True, update=update_tree)
    taper: FloatVectorProperty(name='Taper',
        description='The fraction of tapering on each branch',
        min=0.0,
        max=1.0,
        default=[1, 1, 1, 1],
        size=4, update=update_tree)
    noTip: BoolProperty(name='No branch at stem tip',
        description='Useful for non-typical / abstract trees',
        default=False, update=update_tree)
    radiusTweak: FloatVectorProperty(name='Tweak Radius',
        description='multiply radius by this factor',
        min=0.0,
        max=1.0,
        default=[1, 1, 1, 1],
        size=4, update=update_tree)
    ratioPower: FloatProperty(name='Radius Ratio Power',
        description='Power which defines the radius of a branch compared to the radius of the branch it grew from',
        min=0.0,
        soft_min=1.0,
        default=1.2, update=update_tree)
    downAngle: FloatVectorProperty(name='Down Angle',
        description='The angle between a new branch and the one it grew from',
        default=[90, 60, 45, 45],
        size=4, update=update_tree)
    downAngleV: FloatVectorProperty(name='Down Angle Variation',
        description='Angle to decrease Down Angle by towards end of parent branch \n(negative values add random variation)',
        default=[0, -50, 10, 10],
        size=4, update=update_tree)
    useOldDownAngle: BoolProperty(name='Use old down angle variation',
        default=False, update=update_tree)
    useParentAngle: BoolProperty(name='Use parent angle',
        description='(first level) Rotate branch to match parent branch',
        default=True, update=update_tree)
    rotate: FloatVectorProperty(name='Rotate Angle',
        description='The angle of a new branch around the one it grew from \n(negative values make branches rotate opposite from the previous one)',
        default=[137.5, 137.5, 137.5, 137.5],
        size=4, update=update_tree)
    rotateV: FloatVectorProperty(name='Rotate Angle Variation',
        description='Variation in the rotate angle',
        default=[0, 0, 0, 0],
        size=4, update=update_tree)
    scale0: FloatProperty(name='Radius Scale',
        description='The scale of the trunk radius',
        min=0.0,
        default=1.0, update=update_tree)
    scaleV0: FloatProperty(name='Radius Scale Variation',
        description='Variation in the radius scale',
        min=0.0,
        max=1.0,
        default=0.2, update=update_tree)
    attachment: EnumProperty(name='Attachment',
        description='Type of branch arrangment',
        items=attachmenttypes,
        default='0', update=update_tree)
    leaves: IntProperty(name='Leaves',
        description='Maximum number of leaves per branch',
        min=0,
        default=25, update=update_tree)
    leafType: EnumProperty(name='Leaf Type',
        description='Type of leaf arrangment',
        items=leaftypes,
        default='0', update=update_leaves) #update_leaves update_tree

    leafDownAngle: FloatProperty(name='Leaf Down Angle',
        description='The angle between a new leaf and the branch it grew from',
        default=45, update=update_leaves)
    leafDownAngleV: FloatProperty(name='Leaf Down Angle Variation',
        description='Angle to decrease Down Angle by towards end of parent branch',
        min=0,
        default=10, update=update_tree)
    leafRotate: FloatProperty(name='Leaf Rotate Angle',
        description='The rotate angle for Alternate and Opposite leaves',
        default=90, update=update_tree)
    leafRotateV: FloatProperty(name='Rotation Variation',
        description='Add randomness to leaf orientation',
        default=0.0, update=update_leaves)

    leafObjZ: EnumProperty(name='',
        description='leaf tip axis',
        items=axes,
        default="+2", update=update_leaves)
    leafObjY: EnumProperty(name='',
        description='leaf top axis',
        items=axes,
        default="+1", update=update_leaves)
    #leafObjX: EnumProperty(name='',
    #    description='leaf side axis',
    #    items=axes,
    #    default="+0", update=update_leaves)

    leafScale: FloatProperty(name='Leaf Scale',
        description='The scaling applied to the whole leaf',
        min=0.0,
        default=0.17, update=update_leaves)
    leafScaleX: FloatProperty(name='Leaf Scale X',
        description='The scaling applied to the x direction of the leaf',
        min=0.0,
        default=1.0, update=update_leaves)
    leafScaleT: FloatProperty(name='Leaf Scale Taper',
        description='scale leaves toward the tip or base of the patent branch',
        min=-1.0,
        max=1.0,
        default=0.0, update=update_leaves)
    leafScaleV: FloatProperty(name='Leaf Scale Variation',
        description='randomize leaf scale',
        min=0.0,
        max=1.0,
        default=0.0, update=update_leaves)
    # leafShape: EnumProperty(name='Leaf Shape',
    #     description='The shape of the leaves',
    #     items=(('hex', 'Hexagonal', '0'), ('rect', 'Rectangular', '1'), ('dFace', 'DupliFaces', '2'), ('dVert', 'DupliVerts', '3')),
    #     default='hex', update=update_leaves)
    leafShape: EnumProperty(name='Leaf Shape',
        description='The shape of the leaves',
        items=leafShapes,
        default='hex', update=update_leaves)
    leafDupliObj: EnumProperty(name='Leaf Object',
        description='Object to use for leaf instancing if Leaf Shape is DupliFaces or DupliVerts',
        items=objectList,
        update=update_leaves)

    leafangle: FloatProperty(name='Leaf Angle',
        description='Leaf vertical attraction',
        default=0.0, update=update_leaves)
    leafDist: EnumProperty(name='Leaf Distribution',
        description='The way leaves are distributed on branches',
        items=shapeList4,
        default='6', update=update_tree)

    armAnim: BoolProperty(name='Armature Animation',
        description='Whether animation is added to the armature',
        default=False, update=update_tree)
    previewArm: BoolProperty(name='Fast Preview',
        description=('Disable armature modifier, hide tree, and set bone display to wire, for fast playback \n'
                     'If Make Mesh is enabled: \nDisable skin modifier, hide curve tree and armature'),
        default=False, update=update_tree)
    leafAnim: BoolProperty(name='Leaf Animation',
        description='Whether animation is added to the leaves',
        default=False, update=update_tree)
    frameRate: FloatProperty(name='Animation Speed',
        description='Adjust speed of animation, relative to scene frame rate',
        min=0.001,
        default=1, update=update_tree)
    loopFrames: IntProperty(name='Loop Frames',
        description='Number of frames to make the animation loop for, zero is disabled',
        min=0,
        default=0, update=update_tree)

    #    windSpeed: FloatProperty(name='Wind Speed',
    #        description='The wind speed to apply to the armature',
    #        default=2.0, update=update_tree)
    #    windGust: FloatProperty(name='Wind Gust',
    #        description='The greatest increase over Wind Speed',
    #        default=0.0, update=update_tree)

    wind: FloatProperty(name='Overall Wind Strength',
        description='The intensity of the wind to apply to the armature',
        default=1.0, update=update_tree)

    gust: FloatProperty(name='Wind Gust Strength',
        description='The amount of directional movement, (from the positive Y direction)',
        default=1.0, update=update_tree)

    gustF: FloatProperty(name='Wind Gust Fequency',
        description='The Fequency of directional movement',
        default=0.075, update=update_tree)

    af1: FloatProperty(name='Amplitude',
        description='Multiplier for noise amplitude',
        default=1.0, update=update_tree)
    af2: FloatProperty(name='Frequency',
        description='Multiplier for noise fequency',
        default=1.0, update=update_tree)
    af3: FloatProperty(name='Randomness',
        description='Random offset in noise',
        default=4.0, update=update_tree)

    makeMesh: BoolProperty(name='Make Mesh',
        description='Convert curves to mesh, uses skin modifier, enables armature simplification',
        default=False, update=update_tree)
    armLevels: IntProperty(name='Armature Levels',
        description='Number of branching levels to make bones for, 0 is all levels',
        min=0,
        default=2, update=update_tree)
    boneStep: IntVectorProperty(name='Bone Length',
        description='Number of stem segments per bone',
        min=1,
        default=[1, 1, 1, 1],
        size=4, update=update_tree)
    matIndex: IntVectorProperty(name='Material Index',
        description='Material index for each split level (curves only)',
        min=0,
        max=3,
        default=[0, 0, 0, 0],
        size=4, update=update_tree)

    presetName: StringProperty(name='Preset Name',
        description='The name of the preset to be saved',
        default='',
        subtype='FILE_NAME', update=no_update_tree)
    limitImport: BoolProperty(name='Limit Import',
        description='Limited imported tree to 2 levels & no leaves for speed',
        default=True, update=no_update_tree)
    overwrite: BoolProperty(name='Overwrite',
        description='When checked, overwrite existing preset files when saving',
        default=False, update=no_update_tree)



