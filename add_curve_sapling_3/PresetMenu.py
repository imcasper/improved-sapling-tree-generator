import os

import bpy

from .get_preset_paths import get_preset_paths


class PresetMenu(bpy.types.Menu):
    """Create the preset menu by finding all preset files
    in the preset directory"""
    bl_idname = "sapling.presetmenu"
    bl_label = "Presets"

    def draw(self, context):
        # Get all the sapling presets
        presets = [a for a in os.listdir(get_preset_paths()[0]) if a[-3:] == '.py']
        presets.extend([a for a in os.listdir(get_preset_paths()[1]) if a[-3:] == '.py'])
        layout = self.layout
        # Append all to the menu
        for p in presets:
            layout.operator("sapling.importdata", text=p[:-3]).filename = p