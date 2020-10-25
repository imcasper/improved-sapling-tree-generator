import bpy
from bpy.props import IntVectorProperty, FloatProperty, BoolProperty, EnumProperty, IntProperty, FloatVectorProperty, \
    StringProperty
from .PropertyHolder import app_prop
from .default_extractor import default_extractor


class TestSettings(bpy.types.PropertyGroup):

    # def __init__(self):
    #     print("Test Init")
    #     self.uppdater
    #
    # def set_uppdater(self, uppdtr):
    #     self.uppdater = uppdtr

    def update_tree(self, context):
        print("Test Update")
        # default_extractor(self)
        # app_prop(self)
        # self.do_update = True
        # self.uppdater()

    # do_update: BoolProperty(name='Do Update',
    #                         default=True, options={'HIDDEN'})

    bevel: BoolProperty(name='Bevel',
                        description='Whether the curve is beveled',
                        default=False, update=update_tree)

    twilac_ugg: BoolProperty(name='TwUgg',
                        description='To See If PropHolder Gets This',
                        default=False, update=update_tree)

    bevelRes: IntProperty(name='Bevel Resolution',
                          description='The bevel resolution of the curves',
                          min=0,
                          max=32,
                          default=0, update=update_tree)
    resU: IntProperty(name='Curve Resolution',
                      description='The resolution along the curves',
                      min=1,
                      default=4, update=update_tree)

    levels: IntProperty(name='Levels',
                        description='Number of recursive branches',
                        min=1,
                        max=6,
                        soft_max=4,
                        default=3, update=update_tree)



