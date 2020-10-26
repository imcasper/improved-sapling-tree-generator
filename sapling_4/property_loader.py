import bpy

from bpy.types import PointerProperty
from .AddTree import AddTree
from .TestSettings import TestSettings


classes = (
    TestSettings,
    AddTree,
    # TTPH
)


def myregister():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    print("registered TestProps")

    # bpy.types.Scene.test_sett = bpy.props.PointerProperty(type=TestSettings)
    # bpy.types.Scene.sapling_settings = bpy.props.PointerProperty(type=AddTree)



def myunregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


print("loaded properties?")