# -*- coding: utf-8 -*-

#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================
import time
from math import ceil

import add_curve_sapling_3_2_8
from .AddTree import AddTree
from .AddMultipleTrees import AddMultipleTrees
from .ExportData import ExportData
from .ImportData import ImportData
from .PresetMenu import PresetMenu
from .add_tree import add_tree
from .get_preset_paths import get_preset_paths

# from .get_preset_paths import get_preset_paths
# from .utils import toRad, evalBez, roundBone
# from .preform_pruning import perform_pruning
# from .shape_ratio import shape_ratio
# from .kickstart_trunk import kickstart_trunk
# from .fabricate_stems import fabricate_stems
# from .gen_leaf_mesh import gen_leaf_mesh
# from .create_armature import create_armature
# from .find_taper import find_taper
# from .leaf_rot import leaf_rot
import bpy
import bpy.types
from bpy.props import FloatVectorProperty, IntVectorProperty, FloatProperty, BoolProperty, EnumProperty, IntProperty, StringProperty

bl_info = {
    "name": "Sapling_3",
    "author": "Andrew Hale (TrumanBlending), modified by Aaron Buchler 2015-2018",
    "version": (0, 3, 4),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Curve",
    "description": ("Adds a parametric tree. The method is presented by "
    "Jason Weber & Joseph Penn in their paper 'Creation and Rendering of "
    "Realistic Trees'."),
    "category": "Add Curve"}

if "bpy" in locals():
    import importlib
    importlib.reload(add_curve_sapling_3_2_8)
else:
    from .utils import toRad, evalBez, roundBone
    from .get_preset_paths import get_preset_paths
    from .add_tree import add_tree


def menu_func(self, context):
    self.layout.operator(AddTree.bl_idname, text="Add Tree 3.4", icon='PLUGIN')
def menu_func2(self, context):
    self.layout.operator(AddMultipleTrees.bl_idname, text="Add Multiple Trees", icon='PLUGIN')

classes = (
    AddTree,
    AddMultipleTrees,
    PresetMenu,
    ImportData,
    ExportData,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.VIEW3D_MT_curve_add.append(menu_func)
    bpy.types.VIEW3D_MT_curve_add.append(menu_func2)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.VIEW3D_MT_curve_add.remove(menu_func2)
    bpy.types.VIEW3D_MT_curve_add.remove(menu_func)

if __name__ == "__main__":
    register()
