from collections import deque

from .utils import eval_bez, eval_bez_tan
from .ChildPoint import ChildPoint


def interp_stem(stem, t_values, max_offset, base_size):
    points = stem.spline.bezier_points
    num_segments = len(points) - 1
    stem_len = stem.segL * num_segments

    check_bottom = stem.offsetLen / max_offset
    check_top = check_bottom + (stem_len / max_offset)

    # Loop through all the parametric values to be determined
    temp_list = deque()
    for t in t_values:
        if (t >= check_bottom) and (t <= check_top) and (t < 1.0):
            scaled_t = (t - check_bottom) / (check_top - check_bottom)
            offset = ((t - base_size) / (check_top - base_size)) * (1 - base_size) + base_size

            length = num_segments * scaled_t
            index = int(length)
            t_temp = length - index

            coord = eval_bez(points[index].co, points[index].handle_right, points[index + 1].handle_left, points[index + 1].co, t_temp)
            quat = (eval_bez_tan(points[index].co, points[index].handle_right, points[index + 1].handle_left, points[index + 1].co, t_temp)).to_track_quat('Z', 'Y')
            radius = (1-t_temp)*points[index].radius + t_temp*points[index+1].radius # radius at the child point

            temp_list.append(ChildPoint(coord, quat, (stem.radS, radius, stem.radE), t, offset, stem.segMax * stem.segL, 'bone' + (str(stem.splN).rjust(3, '0')) + '.' + (str(index).rjust(3, '0'))))
        elif t == 1:
            # Add stems at tip
            index = num_segments-1
            coord = points[-1].co
            quat = (points[-1].handle_right - points[-1].co).to_track_quat('Z', 'Y')
            radius = points[-1].radius
            temp_list.append(ChildPoint(coord, quat, (stem.radS, radius, stem.radE), 1, 1, stem.segMax * stem.segL, 'bone' + (str(stem.splN).rjust(3, '0')) + '.' + (str(index).rjust(3, '0'))))

    return temp_list
