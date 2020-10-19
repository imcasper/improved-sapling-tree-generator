import os

import bpy


def get_preset_paths():
    """Return paths for both local and user preset folders"""
    userDir = os.path.join(bpy.utils.script_path_user(), 'presets', 'operator', 'add_curve_sapling_3')

    if os.path.isdir(userDir):
        pass
    else:
        os.makedirs(userDir)

    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)
    localDir = os.path.join(directory, "presets")

    return (localDir, userDir)