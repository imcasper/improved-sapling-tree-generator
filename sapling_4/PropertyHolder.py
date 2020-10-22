# import bpy
# import bpy.types

from typing import Dict


class PropHolder:
    def __init__(self):
        self.props = {}

    def append_props(self, new_props: Dict):
        # print("woop")
        # self.props.append(props)
        new_prop_keys = new_props.keys()
        for key in new_prop_keys:
            self.props[key] = new_props.get(key)
        print(self.props)


TPH: PropHolder = PropHolder()


def app_prop(new_props: Dict):
    TPH.append_props(new_props)

