# -*- coding: utf-8 -*-

# ====================== BEGIN GPL LICENSE BLOCK ======================
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
# ======================= END GPL LICENSE BLOCK ========================
import bpy

import sapling_4
from bpy.props import IntVectorProperty, FloatProperty, BoolProperty, EnumProperty, IntProperty, FloatVectorProperty, \
    StringProperty
import bpy.types

import sapling_4.settings_lists
from .settings_lists import settings, axes, handleList, branchmodes, shapeList3, shapeList4, attachmenttypes, leaftypes
from . import property_loader

from .ExportData import ExportData
from .ImportData import ImportData
from .PresetMenu import PresetMenu
from .AddTree import AddTree
from .AddMultipleTrees import AddMultipleTrees
# from .TestSettings import TestSettings

bl_info = {
    "name": "Sapling_4",
    "author": "Andrew Hale (TrumanBlending), modified by Aaron Buchler 2015-2020",
    "version": (0, 4, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Curve",
    "description": "Adds a parametric tree.",
    "category": "Add Curve"}
##"Originally based on the method presented by Jason Weber & Joseph Penn in their paper 'Creation and Rendering of Realistic Trees'."##

# if "bpy" in locals():
#     import importlib
#     importlib.reload(sapling_4)
# else:
#     import bpy
#     import bpy.types


def menu_func(self, context):
    self.layout.operator(AddTree.bl_idname, text="Add Tree 4.0", icon='PLUGIN')


def menu_func2(self, context):
    self.layout.operator(AddMultipleTrees.bl_idname, text="Add Multiple Trees", icon='PLUGIN')


classes = (
    # TestSettings,
    # AddTree,
    AddMultipleTrees,
    PresetMenu,
    ImportData,
    ExportData,
)


def register():
    from bpy.utils import register_class
    property_loader.myregister()
    for cls in classes:
        register_class(cls)
    # bpy.types.Scene.test_sett = bpy.props.PointerProperty(type=TestSettings)
    bpy.types.VIEW3D_MT_curve_add.append(menu_func)
    bpy.types.VIEW3D_MT_curve_add.append(menu_func2)
    # global settings


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.VIEW3D_MT_curve_add.remove(menu_func2)
    bpy.types.VIEW3D_MT_curve_add.remove(menu_func)
    property_loader.myunregister()

if __name__ == "__main__":
    register()
