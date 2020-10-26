import bpy
import bpy.types
import time
from bpy.props import IntVectorProperty, FloatProperty, BoolProperty, EnumProperty, IntProperty, FloatVectorProperty, \
    StringProperty, PointerProperty
from math import ceil

import sapling_4
import sapling_4.settings_lists
from .default_extractor import default_extractor
from .settings_lists import settings, axes, handleList, branchmodes, shapeList3, shapeList4, attachmenttypes, leaftypes
from .TestSettings import TestSettings
from .ExportData import ExportData
from .ImportData import ImportData
from .PresetMenu import PresetMenu
from .add_tree import add_tree
from .get_preset_paths import get_preset_paths
from .utils import splits, splits2, splits3, declination, curve_up, curve_down, eval_bez, eval_bez_tan, round_bone, \
    to_rad, angle_mean, convert_quat

from .PropertyHolder import PropHolder, TPH


class AddTree(bpy.types.Operator):
    bl_idname = "curve.tree_add"
    bl_label = "Sapling: Add Tree"
    bl_options = {'REGISTER', 'UNDO'}


    def objectList(self, context):
        objects = []
        bObjects = bpy.data.objects
        for obj in bObjects:
            if (obj.type in ['MESH', 'CURVE', 'SURFACE']) and (obj.name not in ['tree', 'leaves']):
                objects.append((obj.name, obj.name, ""))

        return objects

    def update_tree(self, context):
        print("AddTree: uppd Tree")
        self.do_update = True

    def update_leaves(self, context):
        print("AddTree: uppd Tree")
        if self.showLeaves:
            self.do_update = True
        else:
            self.do_update = False

    def no_update_tree(self, context):
        print("AddTree: no uppd Tree")
        self.do_update = False

    test_property_group: PointerProperty(type=TestSettings, update=update_tree)

    do_update: BoolProperty(name='Do Update',
        default=True, options={'HIDDEN'})


    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw(self, context):

        layout = self.layout

        layout.prop(self.test_property_group, 'chooseSet')
        # self.geometry_options(layout)
        if self.test_property_group.chooseSet == '0':
            self.geometry_options(layout)

        elif self.test_property_group.chooseSet == '1':
            self.branch_radius_options(layout)

        elif self.test_property_group.chooseSet == '2':
            self.branch_splitting_options(layout)

        elif self.test_property_group.chooseSet == '3':
            self.branch_growth_options(layout)

        elif self.test_property_group.chooseSet == '5':
            self.leaves_options(layout)

        elif self.test_property_group.chooseSet == '6':
            self.armature_options(layout)

    def geometry_options(self, layout):
        box = layout.box()
        box.label(text="Geometry:")
        row = box.row()
        # row.prop(self, 'bevel')
        row.prop(self.test_property_group, 'bevel')
        # row.prop(self, 'makeMesh')
        row = box.row()
        row.prop(self.test_property_group, 'bevelRes')
        row.prop(self.test_property_group, 'resU')


        box.prop(self.test_property_group, 'handleType')
        row = box.row()
        row.prop(self.test_property_group, 'matIndex')
        # box.prop(self, 'shape')
        # row = box.row()
        # row.prop(self, 'customShape')
        # box.prop(self, 'shapeS')
        # box.label(text="")
        # box.prop(self, 'branchDist')
        # box.prop(self, 'nrings')
        box.label(text="")
        box.prop(self.test_property_group, 'seed')
        box.label(text="Tree Scale:")
        row = box.row()
        row.prop(self.test_property_group, 'scale')
        row.prop(self.test_property_group, 'scaleV')
        # Here we create a dict of all the properties.
        # Unfortunately as_keyword doesn't work with vector properties,
        # so we need something custom. This is it
        # data = self.create_property_dict()
        row = box.row()
        row.prop(self.test_property_group, 'presetName')
        # Send the data dict and the file name to the exporter
        row.operator('sapling.exportdata').data = repr([repr(TPH), self.test_property_group.presetName, self.test_property_group.overwrite])
        row = box.row()
        row.label(text=" ")
        row.prop(self.test_property_group, 'overwrite')
        row = box.row()
        row.menu('SAPLING_MT_preset', text='Load Preset')
        row.prop(self.test_property_group, 'limitImport')

    def branch_radius_options(self, layout):
        box = layout.box()
        box.label(text="Branch Radius:")
        row = box.row()
        row.prop(self.test_property_group, 'bevel')
        row.prop(self.test_property_group, 'bevelRes')
        box.prop(self.test_property_group, 'ratio')
        box.prop(self.test_property_group, 'minRadius')
        box.prop(self.test_property_group, 'closeTip')
        box.prop(self.test_property_group, 'rootFlare')
        box.prop(self.test_property_group, 'splitRadiusRatio')
        box.label(text="")
        box.label(text="Other:")
        row = box.row()
        row.prop(self.test_property_group, 'autoTaper')
        row.prop(self.test_property_group, 'noTip')
        row = box.row()
        row.prop(self.test_property_group, 'scale0')
        row.prop(self.test_property_group, 'scaleV0')
        box.prop(self.test_property_group, 'ratioPower')
        split = box.split()
        col = split.column()
        col.prop(self.test_property_group, 'taper')
        col = split.column()
        col.prop(self.test_property_group, 'radiusTweak')

    def branch_splitting_options(self, layout):
        box = layout.box()
        box.label(text="Branch Splitting:")
        box.prop(self.test_property_group, 'levels')
        box.prop(self.test_property_group, 'baseSplits')
        row = box.row()
        row.prop(self.test_property_group, 'splitHeight')
        row.prop(self.test_property_group, 'splitBias')
        row = box.row()
        split = row.split()
        col = split.column()
        col.label(text="Start Length:")
        col = split.column()
        col.prop(self.test_property_group, 'baseSize')
        col.prop(self.test_property_group, 'baseSize_s')
        # box.label(text="")
        box.prop(self.test_property_group, 'branchDist')
        box.prop(self.test_property_group, 'nrings')
        split = box.split()
        col = split.column()
        col.prop(self.test_property_group, 'branches')
        col.prop(self.test_property_group, 'splitAngle')
        col.prop(self.test_property_group, 'rotate')
        # col.prop(self.test_property_group, 'attractOut')
        col.label(text="Branch Attachment:")
        row = col.row()
        row.prop(self.test_property_group, 'attachment', expand=True)
        col.prop(self.test_property_group, 'splitByLen')
        # col.prop(self.test_property_group, 'taperCrown')
        col = split.column()
        col.prop(self.test_property_group, 'segSplits')
        col.prop(self.test_property_group, 'splitAngleV')
        col.prop(self.test_property_group, 'rotateV')
        col.label(text="Branching Mode:")
        col.prop(self.test_property_group, 'rMode')
        col.prop(self.test_property_group, 'splitStraight')
        col.prop(self.test_property_group, 'splitLength')
        box.column().prop(self.test_property_group, 'curveRes')

    def branch_growth_options(self, layout):
        box = layout.box()
        box.label(text="Branch Growth:")
        # box.prop(self, 'taperCrown')
        row = box.row()
        split = row.split()
        col = split.column()
        # col.prop(self, 'length')
        col.label(text="Shape:")
        col = split.column()
        col.prop(self.test_property_group, 'shape')
        col.prop(self.test_property_group, 'shapeS')
        box.label(text="Custom Shape:")
        row = box.row()
        row.prop(self.test_property_group, 'customShape')
        split = box.split()
        col = split.column()
        col.prop(self.test_property_group, 'length')
        col.prop(self.test_property_group, 'downAngle')
        col.prop(self.test_property_group, 'curve')
        # col.prop(self.test_property_group, 'curveBack')
        col.prop(self.test_property_group, 'attractOut')
        col = split.column()
        col.prop(self.test_property_group, 'lengthV')
        col.prop(self.test_property_group, 'downAngleV')
        col.prop(self.test_property_group, 'curveV')
        col.prop(self.test_property_group, 'attractUp')
        # box.prop(self.test_property_group, 'useOldDownAngle')
        box.prop(self.test_property_group, 'useParentAngle')

    def leaves_options(self, layout):
        box = layout.box()
        box.label(text="Leaves:")
        box.prop(self.test_property_group, 'showLeaves')
        box.prop(self.test_property_group, 'leafShape')
        box.prop(self.test_property_group, 'leafDupliObj')
        row = box.row()
        row.label(text="Leaf Object Axes:")
        row.prop(self.test_property_group, 'leafObjZ')
        row.prop(self.test_property_group, 'leafObjY')
        # row.prop(self.test_property_group, 'leafObjX')
        box.prop(self.test_property_group, 'leaves')
        box.prop(self.test_property_group, 'leafBaseSize')
        box.prop(self.test_property_group, 'leafDist')
        box.label(text="")
        box.prop(self.test_property_group, 'leafType')
        box.prop(self.test_property_group, 'leafangle')
        row = box.row()
        row.prop(self.test_property_group, 'leafDownAngle')
        row.prop(self.test_property_group, 'leafDownAngleV')
        row = box.row()
        row.prop(self.test_property_group, 'leafRotate')
        row.prop(self.test_property_group, 'leafRotateV')
        box.label(text="")
        row = box.row()
        row.prop(self.test_property_group, 'leafScale')
        row.prop(self.test_property_group, 'leafScaleX')
        row = box.row()
        row.prop(self.test_property_group, 'leafScaleT')
        row.prop(self.test_property_group, 'leafScaleV')

    def armature_options(self, layout):
        box = layout.box()
        box.label(text="Armature and Animation:")
        row = box.row()
        row.prop(self.test_property_group, 'useArm')
        row.prop(self.test_property_group, 'previewArm')
        row = box.row()
        row.prop(self.test_property_group, 'armAnim')
        row.prop(self.test_property_group, 'leafAnim')
        box.prop(self.test_property_group, 'frameRate')
        box.prop(self.test_property_group, 'loopFrames')
        # row = box.row()
        # row.prop(self.test_property_group, 'windSpeed')
        # row.prop(self.test_property_group, 'windGust')
        box.label(text='Wind Settings:')
        box.prop(self.test_property_group, 'wind')
        row = box.row()
        row.prop(self.test_property_group, 'gust')
        row.prop(self.test_property_group, 'gustF')
        box.label(text='Leaf Wind Settings:')
        box.prop(self.test_property_group, 'af1')
        box.prop(self.test_property_group, 'af2')
        box.prop(self.test_property_group, 'af3')
        box.label(text="")
        box.prop(self.test_property_group, 'makeMesh')
        box.label(text="Armature Simplification:")
        box.prop(self.test_property_group, 'armLevels')
        box.prop(self.test_property_group, 'boneStep')

    def create_property_dict(self):
        print("create prop dict")
        # Here we create a dict of all the properties.
        # Unfortunately as_keyword doesn't work with vector properties,
        # so we need something custom. This is it
        global TPH
        data = []

        prop = self.__getattribute__('test_property_group')
        # print("prop!!!\n", prop)
        default_extractor(prop)
        prop_items = self.__getattribute__('test_property_group').items()
        # dict_items = (self.as_keywords(ignore=("chooseSet", "presetName", "limitImport", "do_update", "overwrite", "leafDupliObj"))).items()

        for a, b in prop_items:
            # print(a,b)
            # If the property is a vector property then add the slice to the list
            try:
                len(b)
                data.append((a, b[:]))
            # Otherwise, it is fine so just add it
            except:
                data.append((a, b))
        # Create the dict from the list
        data = dict(data)
        TPH.set_attr(data)
        return data

    def execute(self, context):
        print("AddTree: execute")
        # Ensure the use of the global variables
        global TPH
        start_time = time.time()
        # If we need to set the properties from a preset then do it here
        if TPH.useSet:
            print("AddTree: use sett")
            thp_dict = TPH.__dict__
            keys_to_ignore = ["chooseSet", "presetName", "limitImport", "do_update", "overwrite", "leafDupliObj"]
            # print("thp_dict: ", thp_dict)
            for key in keys_to_ignore:
                if key in thp_dict:
                    del thp_dict[key]
            # print("thp_dict: ", thp_dict)
            for a, b in thp_dict.items():
                setattr(self.__getattribute__('test_property_group'), a, b)
            # if self.limitImport:
            #     setattr(self, 'levels', min(settings['levels'], 2))
            #     setattr(self, 'showLeaves', False)
            TPH.useSet = False
        if self.do_update:
            print("AddTree: do_uppdate")
            # Backup most recent settings in case of exit
            if not TPH.is_first:
                print("AddTree: not_first")
                # Here we create a dict of all the properties.
                data = self.create_property_dict()
                # print("_______DATA DICT_________\n", data)

                # Then save
                bpy.ops.sapling.exportdata("INVOKE_DEFAULT", data=repr([repr(data), "PreviousSettings", True]))

            # add_tree(self)
            self.create_property_dict()
            # print("THP.Items:", TPH.__dict__)
            # print(TPH.__getattribute__('leafObjZ'))
            add_tree(TPH)

            # print("__self:__\n", self)
            # print("__self.__dict__:__\n", self.__dict__)
            # print("__self.as_keywords():__\n", self.as_keywords())
            # print("__self.test_property_group:__\n", self.test_property_group)
            # print("__self.__getattribute__('test_property_group'):__\n", self.__getattribute__('test_property_group'))

            # print(self.test_property_group)

            # print("__TPH.props:__\n", TPH.props)
            # cProfile.runctx("addTree(self)", globals(), locals())

            print("Tree creation in %0.1fs" % (time.time() - start_time))

            TPH.is_first = False

            return {'FINISHED'}
        else:
            return {'PASS_THROUGH'}

    def invoke(self, context, event):
        print("AddTree: invoke")
        global THP
        TPH.is_first = True
        prop = self.__getattribute__('test_property_group')
        default_extractor(prop)
        bpy.ops.sapling.importdata(filename="Default Tree.py")

        return self.execute(context)
