from math import radians, copysign
from random import uniform
from typing import List

from mathutils import Vector, Matrix, Euler

from .utils import z_axis
from .ui_settings.LeafSettings import LeafSettings


def gen_leaf_mesh(leaf_settings: LeafSettings, loc, quat, offset, index, old_rot, leaf_number):
    leaf_scale = leaf_settings.leafScale
    down_angle = leaf_settings.leafDownAngle
    down_angle_v = leaf_settings.leafDownAngleV

    verts: List[Vector] = []
    faces = []
    if leaf_settings.leafShape == 'hex':
        verts = [Vector((0, 0, 0)), Vector((0.5, 0, 1/3)), Vector((0.5, 0, 2/3)), Vector((0, 0, 1)), Vector((-0.5, 0, 2/3)), Vector((-0.5, 0, 1/3))]
        edges = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [0, 3]]
        faces = [[0, 1, 2, 3], [0, 3, 4, 5]]
    elif leaf_settings.leafShape == 'rect':
        # verts = [Vector((1, 0, 0)), Vector((1, 0, 1)), Vector((-1, 0, 1)), Vector((-1, 0, 0))]
        verts = [Vector((.5, 0, 0)), Vector((.5, 0, 1)), Vector((-.5, 0, 1)), Vector((-.5, 0, 0))]
        edges = [[0, 1], [1, 2], [2, 3], [3, 0]]
        faces = [[0, 1, 2, 3]]
    elif leaf_settings.leafShape == 'dFace':
        verts = [Vector((.5, .5, 0)), Vector((.5, -.5, 0)), Vector((-.5, -.5, 0)), Vector((-.5, .5, 0))]
        edges = [[0, 1], [1, 2], [2, 3], [3, 0]]
        faces = [[0, 3, 2, 1]]
    elif leaf_settings.leafShape == 'dVert':
        verts = [Vector((0, 0, 1))]
        edges = []
        faces = []

    verts_list = []
    faces_list = []
    normal = Vector((0, 0, 1))

    if leaf_settings.leafType in ['0', '5']:
        old_rot += radians(137.5)

    elif leaf_settings.leafType == '1':
        if leaf_number % 2:
            old_rot += radians(180)
        else:
            old_rot += radians(137.5)

    elif leaf_settings.leafType in ['2', '3']:
        old_rot = -copysign(leaf_settings.leafRotate, old_rot)

    elif leaf_settings.leafType == '4':
        rot_mat = Matrix.Rotation(old_rot + uniform(-leaf_settings.leafRotateV, leaf_settings.leafRotateV), 3, 'Y')
        if leaf_settings.leaves == 1:
            rot_mat = Matrix.Rotation(0, 3, 'Y')
        else:
            old_rot += leaf_settings.leafRotate / (leaf_settings.leaves - 1)

    # Reduce down_angle if leaf is at branch tip
    if offset == 1:
        if leaf_settings.leafType in ['0', '1', '2', '5']:
            down_angle = down_angle * .67
        elif leaf_settings.leafType == '3':
            if (leaf_settings.leaves / 2) == (leaf_settings.leaves // 2):
                down_angle = down_angle * .67
            else:
                down_angle = 0
                down_angle_v = 0

    z_var = Matrix.Rotation(uniform(-leaf_settings.leafRotateV, leaf_settings.leafRotateV), 3, 'Z')

    # Leaf scale variation
    if (leaf_settings.leafType == '4') and (leaf_settings.leafRotate != 0) and (leaf_settings.leaves > 1):
        f = 1 - abs((old_rot - (leaf_settings.leafRotate / (leaf_settings.leaves - 1))) / (leaf_settings.leafRotate / 2))
    else:
        f = offset

    if leaf_settings.leafScaleT < 0:
        leaf_scale = leaf_scale * (1 - (1 - f) * -leaf_settings.leafScaleT)
    else:
        leaf_scale = leaf_scale * (1 - f * leaf_settings.leafScaleT)

    leaf_scale = leaf_scale * uniform(1 - leaf_settings.leafScaleV, 1 + leaf_settings.leafScaleV)

    if leaf_settings.leafShape == 'dFace':
        leaf_scale = leaf_scale * .1

    # Rotate leaf vector
    m = Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    if leaf_settings.leafType in ['2', '3']:
        m.rotate(Euler((0, 0, radians(90))))
        if old_rot > 0:
            m.rotate(Euler((0, 0, radians(180))))

    if leaf_settings.leafType != '4':
        rot_mat = Matrix.Rotation(old_rot + uniform(-leaf_settings.leafRotateV, leaf_settings.leafRotateV), 3, 'Z')
        down_v = -down_angle_v * offset ** 2
        down_rot_mat = Matrix.Rotation(down_angle + down_v + uniform(-leaf_settings.leafRotateV * 0, leaf_settings.leafRotateV * 0), 3, 'X')
        m.rotate(down_rot_mat)

    m.rotate(rot_mat)
    m.rotate(quat)

    # Convert rotation for upward facing leaves
    if leaf_settings.leafType in ['4', '5']:
        l_rot = m
    else:
        v = z_axis.copy()
        v.rotate(m)
        l_rot = v.to_track_quat('Z', 'Y')

    # For each of the verts we now rotate and scale them, then append them to the list to be added to the mesh
    for v in verts:
        v.z *= leaf_scale
        v.y *= leaf_scale
        v.x *= leaf_settings.leafScaleX*leaf_scale

        if leaf_settings.leafShape in ['dVert', 'dFace']:
            v.rotate(leaf_settings.leafObjRot)

        v.rotate(Euler((0, 0, radians(180))))

        #rotate variation
        v.rotate(z_var)

        #leafangle
        v.rotate(Matrix.Rotation(radians(-leaf_settings.leafangle), 3, 'X'))

        v.rotate(l_rot)

    if leaf_settings.leafShape == 'dVert':
        normal = verts[0]
        normal.normalize()
        v = loc
        verts_list.append([v.x, v.y, v.z])
    else:
        for v in verts:
            v += loc
            verts_list.append([v.x, v.y, v.z])
        for f in faces:
            faces_list.append([f[0] + index, f[1] + index, f[2] + index, f[3] + index])

    return verts_list, faces_list, normal, old_rot
