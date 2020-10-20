from math import atan2, radians, sqrt, pi
from random import uniform, choice

import bpy
from mathutils import Matrix, Euler

from .utils import declination, angle_mean, convert_quat, z_axis, tau, x_axis, curve_up, round_bone
from .StemSpline import StemSpline
from .ui_settings.TreeSettings import TreeSettings


# This is the function which extends (or grows) a given stem.
def grow_spline(tree_settings: TreeSettings, lvl, stem, num_split, spline_list, spline_to_bone, close_tip, kp, bone_step):
    out_att = tree_settings.attractOut[lvl]
    handle_type = tree_settings.handles

    # Curv at base
    stem_curv = stem.curv
    if (lvl == 0) and (kp <= tree_settings.splitHeight):
        stem_curv = 0.0

    curve_angle = stem_curv + (uniform(0, stem.curvV) * kp * stem.curvSignx)
    curve_var = uniform(0, stem.curvV) * kp * stem.curvSigny
    stem.curvSignx *= -1
    stem.curvSigny *= -1

    curve_var_mat = Matrix.Rotation(curve_var, 3, 'Y')

    # First find the current direction of the stem
    current_direction = stem.quat()

    # Length taperCrown
    if lvl == 0:
        dec = declination(current_direction) / 180
        dec = dec ** 2
        tf = 1 - (dec * tree_settings.taperCrown * 30)
        tf = max(.1, tf)
    else:
        tf = 1.0
    tf = 1.0 # disabled

    # Outward attraction
    if (lvl >= 0) and (kp > 0) and (out_att > 0):
        p = stem.p.co.copy()
        d = atan2(p[0], -p[1])  # + tau
        e_dir = current_direction.to_euler('XYZ', Euler((0, 0, d), 'XYZ'))
        d = angle_mean(e_dir[2], d, (kp * out_att))
        dir_v = Euler((e_dir[0], e_dir[1], d), 'XYZ')
        current_direction = dir_v.to_quaternion()

    if lvl == 0:
        current_direction = convert_quat(current_direction)

    if lvl != 0:
        split_length = 0

    # If the stem splits, we need to add new splines etc
    if num_split > 0:
        dir_vec, split_r2 = add_splines_on_split(bone_step, close_tip, curve_angle, curve_var_mat, current_direction, lvl, num_split, spline_list, spline_to_bone, stem, tf, tree_settings)

    else:
        curve_var_mat = Matrix.Rotation(curve_var, 3, 'Y')
        # If there are no splits then generate the growth direction without accounting for spreading of stems
        dir_vec = z_axis.copy()
        div_rot_mat = Matrix.Rotation(-curve_angle, 3, 'X')
        dir_vec.rotate(div_rot_mat)

        # Horizontal curvature variation
        dir_vec.rotate(curve_var_mat)

        dir_vec.rotate(current_direction)

        stem.splitlast = 0  # numSplit #keep track of numSplit for next stem

    # Introduce upward curvature
    up_rot_axis = x_axis.copy()
    up_rot_axis.rotate(dir_vec.to_track_quat('Z', 'Y'))
    curve_up_ang = curve_up(stem.vertAtt, dir_vec.to_track_quat('Z', 'Y'), stem.segMax)
    up_rot_mat = Matrix.Rotation(-curve_up_ang, 3, up_rot_axis)
    dir_vec.rotate(up_rot_mat)

    dir_vec.normalize()
    dir_vec *= stem.segL * tf

    # Get the end point position
    end_co = stem.p.co.copy() + dir_vec

    stem.spline.bezier_points.add(1)
    new_point = stem.spline.bezier_points[-1]
    (new_point.co, new_point.handle_left_type, new_point.handle_right_type) = (end_co, handle_type, handle_type)

    new_radius = stem.radS*(1 - (stem.seg + 1)/stem.segMax) + stem.radE*((stem.seg + 1)/stem.segMax)
    if num_split > 0:
        new_radius = max(new_radius * split_r2, tree_settings.minRadius)
        stem.radS = max(stem.radS * split_r2, tree_settings.minRadius)
        stem.radE = max(stem.radE * split_r2, tree_settings.minRadius)
    new_radius = max(new_radius, stem.radE)
    if (stem.seg == stem.segMax-1) and close_tip:
        new_radius = 0.0
    new_point.radius = new_radius

    # Set bezier handles for first point.
    if len(stem.spline.bezier_points) == 2:
        temp_point = stem.spline.bezier_points[0]
        if handle_type is 'AUTO':
            dir_vec = z_axis.copy()
            dir_vec.rotate(current_direction)
            dir_vec = dir_vec * stem.segL * 0.33
            (temp_point.handle_left_type, temp_point.handle_right_type) = ('ALIGNED', 'ALIGNED')
            temp_point.handle_right = temp_point.co + dir_vec
            temp_point.handle_left = temp_point.co - dir_vec
        elif handle_type is 'VECTOR':
            (temp_point.handle_left_type, temp_point.handle_right_type) = ('VECTOR', 'VECTOR')

    # Update the last point in the spline to be the newly added one
    stem.updateEnd()


def add_splines_on_split(bone_step, close_tip, curve_angle, curve_var_mat, current_direction, lvl, num_split, spline_list, spline_to_bone, stem, tf, tree_settings):
    split_ang = tree_settings.splitAngle[lvl]
    split_ang_v = tree_settings.splitAngleV[lvl]

    # Get the curve data
    cu_data = stem.spline.id_data.name
    cu = bpy.data.curves[cu_data]
    # Calculate split angles
    split_ang = split_ang / 2
    if lvl == 0:
        angle = split_ang + uniform(-split_ang_v, split_ang_v)
    else:
        # angle = stem.splitSigny * (split_ang + uniform(-split_ang_v, split_ang_v))
        # stem.splitSigny = -stem.splitSigny
        angle = choice([1, -1]) * (split_ang + uniform(-split_ang_v, split_ang_v))
    if lvl > 0:
        # Make branches flatter
        angle *= max(1 - declination(current_direction) / 90, 0) * .67 + .33
    spread_angle = stem.splitSignx * (split_ang + uniform(-split_ang_v, split_ang_v))
    stem.splitSignx = -stem.splitSignx
    branch_straightness = tree_settings.splitStraight  # 0
    if lvl == 0:
        branch_straightness = tree_settings.splitStraight
    if not hasattr(stem, 'rLast'):
        stem.rLast = radians(uniform(0, 360))
    br = tree_settings.rotate[0] + uniform(-tree_settings.rotateV[0], tree_settings.rotateV[0])
    branch_rot = stem.rLast + br
    branch_rot_mat = Matrix.Rotation(branch_rot, 3, 'Z')
    stem.rLast = branch_rot

    # Now for each split add the new spline and adjust the growth direction
    for i in range(num_split):
        split_r2 = new_adjusted_spline(angle, bone_step, branch_rot, branch_rot_mat, branch_straightness, close_tip, cu, curve_angle, curve_var_mat, current_direction, i, lvl, num_split, spline_list, spline_to_bone, spread_angle, stem, tf, tree_settings)

    # The original spline also needs to keep growing so adjust its direction too
    div_rot_mat = Matrix.Rotation(-angle * (1 - branch_straightness) - curve_angle, 3, 'X')
    dir_vec = z_axis.copy()
    dir_vec.rotate(div_rot_mat)

    # Horizontal curvature variation
    dir_vec.rotate(curve_var_mat)
    if lvl == 0:  # Special case for trunk splits
        dir_vec.rotate(branch_rot_mat)

    # Spread
    if lvl != 0:  # Special case for trunk splits
        spread_mat = Matrix.Rotation(-spread_angle * (1 - branch_straightness), 3, 'Y')
        dir_vec.rotate(spread_mat)
    dir_vec.rotate(current_direction)
    stem.splitlast = 1  # numSplit #keep track of numSplit for next stem
    return dir_vec, split_r2


def new_adjusted_spline(angle, bone_step, branch_rot, branch_rot_mat, branch_straightness, close_tip, cu, curve_angle,
                        curve_var_mat, current_direction, i, lvl, num_split, spline_list, spline_to_bone,
                        spread_angle, stem, tf, tree_settings):

    split_length = tree_settings.splitLength
    len_var = tree_settings.lengthV[lvl]
    handle_type = tree_settings.handles

    # Find split scale and length variation for split branches
    len_v = (1 - split_length) * uniform(1 - len_var, 1 + (split_length * len_var))
    len_v = max(len_v, 0.01) * tf
    b_scale = min(len_v, 1)

    # Split radius factor
    split_r = tree_settings.splitRadiusRatio  # 0.707 #sqrt(1/(numSplit+1))
    if tree_settings.splitRadiusRatio == 0:
        split_r1 = sqrt(.5 * b_scale)
        split_r2 = sqrt(1 - (.5 * b_scale))
    #            elif splitRadiusRatio == -1:
    #                ra = len_v / (len_v + 1)
    #                split_r1 = sqrt(ra)
    #                split_r2 = sqrt(1-ra)
    #            elif splitRadiusRatio == 0:
    #                split_r1 = sqrt(0.5) * b_scale
    #                split_r2 = sqrt(1 - split_r1*split_r1)
    #
    #                #split_r2 = sqrt(1 - (0.5 * (1-split_length)))
    else:
        split_r1 = split_r * b_scale
        split_r2 = split_r
    new_spline = cu.splines.new('BEZIER')
    new_spline.material_index = tree_settings.matIndex[lvl]
    # new_point = new_spline.bezier_points[-1]
    # (new_point.co, new_point.handle_left_type, new_point.handle_right_type) = (end_co + dir_vec, handle_type, handle_type)
    # new_radius = (stem.radS * (1 - (stem.seg + 1) / stem.segMax) + stem.radE * ((stem.seg + 1) / stem.segMax)) * split_r1
    # new_radius = (stem.radS * (1 -  stem.seg      / stem.segMax) + stem.radE * ( stem.seg      / stem.segMax)) * split_r1
    # new_radius = max(new_radius, tree_settings.minRadius)
    new_point, new_radius = add_new_point(stem.p.co, 'VECTOR', stem.seg, new_spline, split_r1, stem, tree_settings)
    # new_point = new_spline.bezier_points[-1]
    # (new_point.co, new_point.handle_left_type, new_point.handle_right_type) = (stem.p.co, 'VECTOR', 'VECTOR')
    # new_radius = (stem.radS * (1 - stem.seg/stem.segMax) + stem.radE*(stem.seg/stem.segMax)) * split_r1
    # new_radius = max(new_radius, tree_settings.minRadius)
    new_point.radius = new_radius

    # Here we make the new "sprouting" stems diverge from the current direction
    div_rot_mat = Matrix.Rotation(angle * (1 + branch_straightness) - curve_angle, 3, 'X')
    dir_vec = z_axis.copy()
    dir_vec.rotate(div_rot_mat)

    # Horizontal curvature variation
    dir_vec.rotate(curve_var_mat)
    if lvl == 0:  # Special case for trunk splits
        dir_vec.rotate(branch_rot_mat)

        ang = pi - (tau / (num_split + 1)) * (i + 1)
        dir_vec.rotate(Matrix.Rotation(ang, 3, 'Z'))

    # Spread the stem out horizontally
    if lvl != 0:  # Special case for trunk splits
        spread_mat = Matrix.Rotation(spread_angle * (1 + branch_straightness), 3, 'Y')
        dir_vec.rotate(spread_mat)
    dir_vec.rotate(current_direction)

    # Introduce upward curvature
    up_rot_axis = x_axis.copy()
    up_rot_axis.rotate(dir_vec.to_track_quat('Z', 'Y'))
    curve_up_ang = curve_up(stem.vertAtt, dir_vec.to_track_quat('Z', 'Y'), stem.segMax)
    up_rot_mat = Matrix.Rotation(-curve_up_ang, 3, up_rot_axis)
    dir_vec.rotate(up_rot_mat)

    # Make the growth vec the length of a stem segment
    dir_vec.normalize()

    # Split length variation
    stem_l = stem.segL * len_v
    dir_vec *= stem_l * tf
    offset = stem.offsetLen + (stem.segL * (len(stem.spline.bezier_points) - 1))

    # Get the end point position
    end_co = stem.p.co.copy()

    # Add the new point and adjust its coords, handles and radius
    new_spline.bezier_points.add(1)
    new_point, new_radius = add_new_point(dir_vec + end_co, stem.seg + 1, handle_type, new_spline, split_r1, stem, tree_settings)
    n_rad_s = max(stem.radS * split_r1, tree_settings.minRadius)
    n_rad_e = max(stem.radE * split_r1, tree_settings.minRadius)

    if (stem.seg == stem.segMax - 1) and close_tip:
        new_radius = 0.0
    new_point.radius = new_radius
    # Add n_stem to splineList
    n_stem = StemSpline(new_spline, stem.curv, stem.curvV, stem.vertAtt, stem.seg + 1, stem.segMax, stem_l, stem.children, n_rad_s, n_rad_e, len(cu.splines) - 1, offset, stem.quat())
    n_stem.splitlast = 1  # numSplit #keep track of numSplit for next stem
    n_stem.rLast = branch_rot + pi
    n_stem.splitSignx = stem.splitSignx

    if hasattr(stem, 'isFirstTip'):
        n_stem.isFirstTip = True
    spline_list.append(n_stem)
    bone = 'bone' + (str(stem.splN)).rjust(3, '0') + '.' + (str(len(stem.spline.bezier_points) - 2)).rjust(3, '0')
    bone = round_bone(bone, bone_step[lvl])
    spline_to_bone.append((bone, False, True, len(stem.spline.bezier_points) - 2))
    return split_r2


def add_new_point(ugg, handle_type, seg, new_spline, split_r1, stem, tree_settings):
    new_point = new_spline.bezier_points[-1]
    (new_point.co, new_point.handle_left_type, new_point.handle_right_type) = (ugg, handle_type, handle_type)
    new_radius = (stem.radS * (1 - seg / stem.segMax) + stem.radE * (seg / stem.segMax)) * split_r1
    new_radius = max(new_radius, tree_settings.minRadius)
    return new_point, new_radius
