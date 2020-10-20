from math import pi
from random import uniform

from mathutils import Vector, Matrix

from .utils import z_axis
from .StemSpline import StemSpline
from .ui_settings.TreeSettings import TreeSettings


def kickstart_trunk(tree_settings: TreeSettings, add_stem, leaves, tree_curve, scale_val):
    new_spline = tree_curve.splines.new('BEZIER')
    new_spline.material_index = tree_settings.matIndex[0]
    new_point = new_spline.bezier_points[-1]
    new_point.co = Vector((0, 0, 0))

    # Start trunk rotation with down_angle
    temp_pos = z_axis.copy()
    down_ang = tree_settings.downAngle[0] - .5 * pi
    down_ang = down_ang  # + uniform(-downAngleV[0], downAngleV[0])
    down_rot = Matrix.Rotation(down_ang, 3, 'X')

    temp_pos.rotate(down_rot)
    down_rot = Matrix.Rotation(tree_settings.downAngleV[0], 3, 'Y')

    temp_pos.rotate(down_rot)
    handle = temp_pos
    new_point.handle_right = handle
    new_point.handle_left = -handle

    branch_l = scale_val * tree_settings.length[0]
    curve_val = tree_settings.curve[0] / tree_settings.curveRes[0]

    if tree_settings.levels == 1:
        child_stems = leaves
    else:
        child_stems = tree_settings.branches[1]

    start_rad = scale_val * tree_settings.ratio * tree_settings.scale0 * uniform(1 - tree_settings.scaleV0, 1 + tree_settings.scaleV0)
    end_rad = (start_rad * (1 - tree_settings.taper[0])) ** tree_settings.ratioPower
    start_rad = max(start_rad, tree_settings.minRadius)
    end_rad = max(end_rad, tree_settings.minRadius)
    new_point.radius = start_rad * tree_settings.rootFlare

    add_stem(StemSpline(new_spline, curve_val, tree_settings.curveV[0], tree_settings.attractUp[0], 0, tree_settings.curveRes[0], branch_l / tree_settings.curveRes[0], child_stems, start_rad, end_rad, 0, 0, None))
