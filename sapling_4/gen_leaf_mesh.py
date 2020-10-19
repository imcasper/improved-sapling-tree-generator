from math import radians, copysign
from random import uniform

from mathutils import Vector, Matrix, Euler

from .utils import zAxis
from .LeafSettings import LeafSettings


def gen_leaf_mesh(leaf_settings: LeafSettings, loc, quat, offset, index, oldRot, leaves, ln):
    leafScale = leaf_settings.leafScale
    downAngle = leaf_settings.leafDownAngle
    downAngleV = leaf_settings.leafDownAngleV
    if leaf_settings.leafShape == 'hex':
        verts = [Vector((0, 0, 0)), Vector((0.5, 0, 1/3)), Vector((0.5, 0, 2/3)), Vector((0, 0, 1)), Vector((-0.5, 0, 2/3)), Vector((-0.5, 0, 1/3))]
        edges = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [0, 3]]
        faces = [[0, 1, 2, 3], [0, 3, 4, 5]]
    elif leaf_settings.leafShape == 'rect':
        #verts = [Vector((1, 0, 0)), Vector((1, 0, 1)), Vector((-1, 0, 1)), Vector((-1, 0, 0))]
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

    vertsList = []
    facesList = []
    normal = Vector((0, 0, 1))

    if leaf_settings.leafType in ['0', '5']:
        oldRot += radians(137.5)
    elif leaf_settings.leafType == '1':
        if ln % 2:
            oldRot += radians(180)
        else:
            oldRot += radians(137.5)
    elif leaf_settings.leafType in ['2', '3']:
        oldRot = -copysign(leaf_settings.leafRotate, oldRot)
    elif leaf_settings.leafType == '4':
        rotMat = Matrix.Rotation(oldRot + uniform(-leaf_settings.leafRotateV, leaf_settings.leafRotateV), 3, 'Y')
        if leaves == 1:
            rotMat = Matrix.Rotation(0, 3, 'Y')
        else:
            oldRot += leaf_settings.leafRotate / (leaves - 1)

    if leaf_settings.leafType != '4':
        rotMat = Matrix.Rotation(oldRot + uniform(-leaf_settings.leafRotateV, leaf_settings.leafRotateV), 3, 'Z')

    # reduce downAngle if leaf is at branch tip
    if (offset == 1):
        if leaf_settings.leafType in ['0', '1', '2', '5']:
            downAngle = downAngle * .67
        elif leaf_settings.leafType == '3':
            if (leaves / 2) == (leaves // 2):
                downAngle = downAngle * .67
            else:
                downAngle = 0
                downAngleV = 0

    if leaf_settings.leafType != '4':
        downV = -downAngleV * offset ** 2
        downRotMat = Matrix.Rotation(downAngle + downV + uniform(-leaf_settings.leafRotateV*0, leaf_settings.leafRotateV*0), 3, 'X')

    zVar = Matrix.Rotation(uniform(-leaf_settings.leafRotateV, leaf_settings.leafRotateV), 3, 'Z')

    #leaf scale variation
    if (leaf_settings.leafType == '4') and (leaf_settings.leafRotate != 0) and (leaves > 1):
        f = 1 - abs((oldRot - (leaf_settings.leafRotate / (leaves - 1))) / (leaf_settings.leafRotate / 2))
    else:
        f = offset

    if leaf_settings.leafScaleT < 0:
        leafScale = leafScale * (1 - (1 - f) * -leaf_settings.leafScaleT)
    else:
        leafScale = leafScale * (1 - f * leaf_settings.leafScaleT)

    leafScale = leafScale * uniform(1 - leaf_settings.leafScaleV, 1 + leaf_settings.leafScaleV)

    if leaf_settings.leafShape == 'dFace':
        leafScale = leafScale * .1

    #Rotate leaf vector
    m = Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    if leaf_settings.leafType in ['2', '3']:
        m.rotate(Euler((0, 0, radians(90))))
        if oldRot > 0:
            m.rotate(Euler((0, 0, radians(180))))

    if leaf_settings.leafType != '4':
        m.rotate(downRotMat)

    m.rotate(rotMat)
    m.rotate(quat)

    # convert rotation for upward facing leaves
    if leaf_settings.leafType in ['4', '5']:
        lRot = m
    else:
        v = zAxis.copy()
        v.rotate(m)
        lRot = v.to_track_quat('Z', 'Y')

    # For each of the verts we now rotate and scale them, then append them to the list to be added to the mesh
    for v in verts:
        v.z *= leafScale
        v.y *= leafScale
        v.x *= leaf_settings.leafScaleX*leafScale

        if leaf_settings.leafShape in ['dVert', 'dFace']:
            v.rotate(leaf_settings.leafObjRot)

        v.rotate(Euler((0, 0, radians(180))))

        #rotate variation
        v.rotate(zVar)

        #leafangle
        v.rotate(Matrix.Rotation(radians(-leaf_settings.leafangle), 3, 'X'))

        v.rotate(lRot)

    if leaf_settings.leafShape == 'dVert':
        normal = verts[0]
        normal.normalize()
        v = loc
        vertsList.append([v.x, v.y, v.z])
    else:
        for v in verts:
            v += loc
            vertsList.append([v.x, v.y, v.z])
        for f in faces:
            facesList.append([f[0] + index, f[1] + index, f[2] + index, f[3] + index])

    return vertsList, facesList, normal, oldRot