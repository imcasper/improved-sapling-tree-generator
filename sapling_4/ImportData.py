import ast
import os

import bpy
from bpy.props import StringProperty

from .get_preset_paths import get_preset_paths
from .settings_lists import settings


class ImportData(bpy.types.Operator):
    """This operator handles importing existing presets"""
    bl_idname = 'sapling.importdata'
    bl_label = 'Import Preset'

    filename: StringProperty()

    def execute(self, context):
        # Make sure the operator knows about the global variables
        global settings, useSet, is_first
        # Read the preset data into the global settings
        try:
            f = open(os.path.join(get_preset_paths()[0], self.filename), 'r')
        except (FileNotFoundError, IOError):
            f = open(os.path.join(get_preset_paths()[1], self.filename), 'r')
        settings = f.readline()
        f.close()
        #print(settings)
        settings = ast.literal_eval(settings)

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

        # Set the flag to use the settings
        useSet = True
        is_first = True
        return {'FINISHED'}