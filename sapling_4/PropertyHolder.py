# import bpy
# import bpy.types

from typing import Dict


class PropHolder:
    def __init__(self):
        self.useSet: bool = False
        self.is_first: bool = False
        # self.props = {}

    def append_props(self, new_props: Dict):
        # print("woop")
        # self.props.append(props)
        new_prop_keys = new_props.keys()
        for key in new_prop_keys:
            self.props[key] = new_props.get(key)
        # print(self.props)

    def set_attr(self, new_props: Dict):
        # print(new_props)
        print("settAttr")
        new_prop_keys = new_props.keys()
        for key in new_prop_keys:
            setattr(self, key, new_props.get(key))
            # self.props[key] = new_props.get(key)
        # for prop_name, prop_value in new_props:
        #     setattr(self, prop_name, prop_value)


TPH: PropHolder = PropHolder()

# settings = ""


def app_prop(new_props: Dict):
    TPH.append_props(new_props)

