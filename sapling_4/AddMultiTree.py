import bpy
import bpy.types
from bpy.props import IntVectorProperty, FloatProperty, BoolProperty, EnumProperty, IntProperty
from math import ceil
import sapling_4
import sapling_4.settings_lists

from .settings_lists import axes
from .add_tree import add_tree

useSet = False
is_first = False


class AddMultipleTrees(bpy.types.Operator):
    bl_idname = "curve.trees_add"
    bl_label = "Sapling: Add Trees"
    bl_options = {'REGISTER', 'UNDO'}

    def objectList(self, context):
        objects = []
        bObjects = bpy.data.objects
#        try:
#            bObjects = bpy.data.objects
#        except AttributeError:
#            pass
#        else:
        for obj in bObjects:
            if (obj.type in ['MESH', 'CURVE', 'SURFACE']) and (obj.name not in ['tree', 'leaves']):
                objects.append((obj.name, obj.name, ""))
        return objects

    do_update: BoolProperty(name='Re-grow Trees',
        default=True)

    bevel: BoolProperty(name='Bevel',
        description='Whether the curve is beveled',
        default=False)
    showLeaves: BoolProperty(name='Show Leaves',
        description='Whether the leaves are shown',
        default=False)
    useArm: BoolProperty(name='Use Armature',
        description='Whether the armature is generated',
        default=False)
    seed: IntProperty(name='Random Seed',
        description='The seed of the random number generator',
        default=0)
    numTrees: IntProperty(name='Number of trees',
        description='Number of trees to generate while incrementing the seed',
        min=1,
        default=1)

    scale: FloatProperty(name='Scale',
        description='The tree scale (Scale)',
        min=0.0,
        default=13.0)
    scaleV: FloatProperty(name='Scale Variation',
        description='The variation in the tree scale',
        default=3.0)

    bevelRes: IntProperty(name='Bevel Resolution',
        description='The bevel resolution of the curves',
        min=0,
        max=32,
        default=0)
    resU: IntProperty(name='Curve Resolution',
        description='The resolution along the curves',
        min=1,
        default=4)

    leafShape: EnumProperty(name='Leaf Shape',
        description='The shape of the leaves',
        items=(('hex', 'Hexagonal', '0'), ('rect', 'Rectangular', '1'), ('dFace', 'DupliFaces', '2'), ('dVert', 'DupliVerts', '3')),
        default='hex')
    leafDupliObj: EnumProperty(name='Leaf Object',
        description='Object to use for leaf instancing if Leaf Shape is DupliFaces or DupliVerts',
        items=objectList)
    leafObjZ: EnumProperty(name='',
                           description='leaf tip axis',
                           items=axes,
                           default="+2")
    leafObjY: EnumProperty(name='',
                           description='leaf top axis',
                           items=axes,
                           default="+1")
    leafScale: FloatProperty(name='Leaf Scale',
        description='The scaling applied to the whole leaf (LeafScale)',
        min=0.0,
        default=0.17)

    armAnim: BoolProperty(name='Armature Animation',
        description='Whether animation is added to the armature',
        default=False)
    previewArm: BoolProperty(name='Fast Preview',
        description='Disable armature modifier, hide tree, and set bone display to wire, for fast playback',
        ##Disable skin modifier and hide tree and armature, for fast playback
        default=False)
    leafAnim: BoolProperty(name='Leaf Animation',
        description='Whether animation is added to the leaves',
        default=False)
    frameRate: FloatProperty(name='Animation Speed',
        description=('Adjust speed of animation, relative to scene frame rate'),
        min=0.001,
        default=1)
    loopFrames: IntProperty(name='Loop Frames',
        description='Number of frames to make the animation loop for, zero is disabled',
        min=0,
        default=0)

    makeMesh: BoolProperty(name='Make Mesh',
        description='Convert curves to mesh, uses skin modifier, enables armature simplification',
        default=False)
    armLevels: IntProperty(name='Armature Levels',
        description='Number of branching levels to make bones for, 0 is all levels',
        min=0,
        default=2)
    boneStep: IntVectorProperty(name='Bone Length',
        description='Number of stem segments per bone',
        min=1,
        default=[1, 1, 1, 1],
        size=4)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw(self, context):

        layout = self.layout

        layout.prop(self, 'do_update', icon='CURVE_DATA')

        box = layout.box()
        box.label(text="Geometry:")

        row = box.row()
        row.menu('SAPLING_MT_preset', text='Load Preset')

        box.prop(self, 'seed')
        box.prop(self, 'numTrees')

        box.prop(self, 'bevel')

        row = box.row()
        row.prop(self, 'bevelRes')
        row.prop(self, 'resU')

        box.label(text="Tree Scale:")
        row = box.row()
        row.prop(self, 'scale')
        row.prop(self, 'scaleV')

        box = layout.box()
        box.label(text="Leaves:")

        box.prop(self, 'showLeaves')
        box.prop(self, 'leafShape')
        box.prop(self, 'leafDupliObj')
        row = box.row()
        row.label(text="Leaf Object Axes:")
        row.prop(self, 'leafObjZ')
        row.prop(self, 'leafObjY')

        #box.prop(self, 'leaves')
        box.prop(self, 'leafScale')

        box = layout.box()
        box.label(text="Armature and Animation:")

        row = box.row()
        row.prop(self, 'useArm')
        row.prop(self, 'previewArm')

        row = box.row()
        row.prop(self, 'armAnim')
        row.prop(self, 'leafAnim')

        box.prop(self, 'frameRate')
        box.prop(self, 'loopFrames')

        box.label(text="")
        box.prop(self, 'makeMesh')
        box.label(text="Armature Simplification:")
        box.prop(self, 'armLevels')
        box.prop(self, 'boneStep')


    def execute(self, context):
        # Ensure the use of the global variables
        global useSet
        # If we need to set the properties from a preset then do it here
        #presetAsDict
        if useSet:
            for a, b in sapling_4.settings_lists.settings.items():
                setattr(self, a, b)
            useSet = False
        if self.do_update:
            #loop for multiple trees
            initSeed = self.seed
            for n in range(self.numTrees):
                setattr(self, 'seed', self.seed + n)
                space = 6
                grid = ceil(self.numTrees ** .5)
                x = (n // grid) * space
                y = (n % grid) * space
                bpy.context.scene.cursor.location = (x, y, 0)
                add_tree(self)
            setattr(self, 'seed', initSeed)
            self.do_update = False
            return {'FINISHED'}
        else:
            return {'PASS_THROUGH'}

    def invoke(self, context, event):
#        global settings, useSet
#        useSet = True
        bpy.ops.sapling.importdata(filename="Default Tree.py")
        return self.execute(context)