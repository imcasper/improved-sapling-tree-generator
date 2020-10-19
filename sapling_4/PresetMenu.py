import os

import bpy

from .get_preset_paths import get_preset_paths


class PresetMenu(bpy.types.Menu):
    """Create the preset menu by finding all preset files
    in the preset directory"""
    bl_idname = "SAPLING_MT_preset" #was sapling.presetmenu
    bl_label = "Presets"

    def draw(self, context):
        # Get all the sapling presets
        presets = [a for a in os.listdir(get_preset_paths()[0]) if a[-3:] == '.py']
        presetsUser = [a for a in os.listdir(get_preset_paths()[1]) if a[-3:] == '.py']
        layout = self.layout
        # Append all to the menu
        if "PreviousSettings.py" in presetsUser:
            p = "PreviousSettings.py"
            layout.operator("sapling.importdata", text=p[:-3]).filename = p
            presetsUser.remove("PreviousSettings.py")
        layout.separator()
        for p in presets:
            layout.operator("sapling.importdata", text=p[:-3]).filename = p
        layout.separator()
        for p in presetsUser:
            layout.operator("sapling.importdata", text=p[:-3]).filename = p