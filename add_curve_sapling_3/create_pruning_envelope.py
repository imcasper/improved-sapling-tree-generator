import bpy
from mathutils import Vector

from add_curve_sapling_3.shape_ratio import shape_ratio


def create_pruning_envelope(prune_base, scale_val, tree_ob, tree_settings):
    en_handle = 'VECTOR'
    en_num = 128
    en_cu = bpy.data.curves.new('envelope', 'CURVE')
    en_ob = bpy.data.objects.new('envelope', en_cu)
    en_ob.parent = tree_ob
    bpy.context.scene.objects.link(en_ob)
    new_spline = en_cu.splines.new('BEZIER')
    new_point = new_spline.bezier_points[-1]
    new_point.co = Vector((0, 0, scale_val))
    (new_point.handle_right_type, new_point.handle_left_type) = (en_handle, en_handle)
    # Set the coordinates by varying the z value, envelope will be aligned to the x-axis
    for c in range(en_num):
        new_spline.bezier_points.add()
        new_point = new_spline.bezier_points[-1]
        ratio_val = (c + 1) / (en_num)
        z_val = scale_val - scale_val * (1 - prune_base) * ratio_val
        new_point.co = Vector((scale_val * tree_settings.pruneWidth * shape_ratio(9, ratio_val,
                                                                                 tree_settings.pruneWidthPeak,
                                                                                 tree_settings.prunePowerHigh,
                                                                                 tree_settings.prunePowerLow), 0, z_val))
        (new_point.handle_right_type, new_point.handle_left_type) = (en_handle, en_handle)
    new_spline = en_cu.splines.new('BEZIER')
    new_point = new_spline.bezier_points[-1]
    new_point.co = Vector((0, 0, scale_val))
    (new_point.handle_right_type, new_point.handle_left_type) = (en_handle, en_handle)
    # Create a second envelope but this time on the y-axis
    for c in range(en_num):
        new_spline.bezier_points.add()
        new_point = new_spline.bezier_points[-1]
        ratio_val = (c + 1) / (en_num)
        z_val = scale_val - scale_val * (1 - prune_base) * ratio_val
        new_point.co = Vector((0, scale_val * tree_settings.pruneWidth * shape_ratio(9, ratio_val,
                                                                                    tree_settings.pruneWidthPeak,
                                                                                    tree_settings.prunePowerHigh,
                                                                                    tree_settings.prunePowerLow), z_val))
        (new_point.handle_right_type, new_point.handle_left_type) = (en_handle, en_handle)