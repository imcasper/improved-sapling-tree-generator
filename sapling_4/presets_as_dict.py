import ast
import os

from .get_preset_paths import get_preset_paths


def preset_as_dict(filename):
    try:
        f = open(os.path.join(get_preset_paths()[0], filename), 'r')
    except (FileNotFoundError, IOError):
        f = open(os.path.join(get_preset_paths()[1], filename), 'r')
    settings = f.read()
    f.close()
    settings = ast.literal_eval(settings.replace('\n', ''))
    return settings
