import os

import bpy
from bpy.props import StringProperty

from .get_preset_paths import get_preset_paths


class ExportData(bpy.types.Operator):
    """This operator handles writing presets to file"""
    bl_idname = 'sapling.exportdata'
    bl_label = 'Export Preset'

    data: StringProperty()

    def execute(self, context):
        print("ExportData: execute")
        # Unpack some data from the input
        data, filename, overwrite = eval(self.data)

        fpath1 = os.path.join(get_preset_paths()[0], filename + '.py')
        fpath2 = os.path.join(get_preset_paths()[1], filename + '.py')

        if os.path.exists(fpath1):
            # If it exists in built-in presets then report an error
            self.report({'ERROR_INVALID_INPUT'}, 'Can\'t have same name as built-in preset')
            return {'CANCELLED'}
        elif (not os.path.exists(fpath2)) or (os.path.exists(fpath2) and overwrite):
            #if (it does not exist) or (exists and overwrite) then write file
            if data:
                # If it doesn't exist, create the file with the required data
                f = open(os.path.join(get_preset_paths()[1], filename + '.py'), 'w')
                f.write(data)
                f.close()
                return {'FINISHED'}
            else:
                return {'CANCELLED'}
        else:
            # If it exists then report an error
            self.report({'ERROR_INVALID_INPUT'}, 'Preset Already Exists')
            return {'CANCELLED'}