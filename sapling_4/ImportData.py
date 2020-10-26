import ast
import os

import bpy
from bpy.props import StringProperty

from .get_preset_paths import get_preset_paths
from .presets_as_dict import preset_as_dict
from .PropertyHolder import TPH


class ImportData(bpy.types.Operator):
    """This operator handles importing existing presets"""
    bl_idname = 'sapling.importdata'
    bl_label = 'Import Preset'

    filename: StringProperty()

    def execute(self, context):
        print("ImportData: execute")
        # Read the preset data
        settings = preset_as_dict(self.filename)

        #use old attractup
        if type(settings['attractUp']) == float:
            atr = settings['attractUp']
            settings['attractUp'] = [0, 0, atr, atr]

        #use old leaf rotations
        if 'leafDownAngle' not in settings:
            l = settings['levels']
            settings['leafDownAngle'] = settings['downAngle'][min(l, 3)]
            settings['leafDownAngleV'] = settings['downAngleV'][min(l, 3)]
            settings['leafRotate'] = settings['rotate'][min(l, 3)]
            settings['leafRotateV'] = settings['rotateV'][min(l, 3)]

        #use old leaf settings
        if 'leafType' not in settings:
            settings['leafType'] = '0'
        if settings['leaves'] < 0:
            settings['leaves'] = abs(settings['leaves'])
            settings['leafType'] = '4'
        if settings['leafRotate'] < 1:
            settings['leafType'] = '2'

        if 'noTip' not in settings:
            settings['noTip'] = False

        #zero curveback
        if 'curveBack' in settings:
            settings['curveBack'] = [0, 0, 0, 0]



        # print(settings)
        print("imported settings")
        global TPH
        # Set the flag to use the settings
        TPH.useSet = True
        TPH.is_first = True
        TPH.set_attr(settings)
        return {'FINISHED'}
