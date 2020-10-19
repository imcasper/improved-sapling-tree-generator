from math import radians, copysign
from random import uniform

from mathutils import Vector, Matrix, Euler

from .utils import zAxis


def gen_leaf_mesh(leafScale, leafScaleX, leafScaleT, leafScaleV, loc, quat, offset, index, downAngle, downAngleV, rotate, rotateV, oldRot,
                  leaves, leafShape, leafangle, horzLeaves, leafType, ln, leafObjRot):
    if leafShape == 'hex':
        verts = [Vector((0, 0, 0)), Vector((0.5, 0, 1/3)), Vector((0.5, 0, 2/3)), Vector((0, 0, 1)), Vector((-0.5, 0, 2/3)), Vector((-0.5, 0, 1/3))]
        edges = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [0, 3]]
        faces = [[0, 1, 2, 3], [0, 3, 4, 5]]
    elif leafShape == 'rect':
        #verts = [Vector((1, 0, 0)), Vector((1, 0, 1)), Vector((-1, 0, 1)), Vector((-1, 0, 0))]
        verts = [Vector((.5, 0, 0)), Vector((.5, 0, 1)), Vector((-.5, 0, 1)), Vector((-.5, 0, 0))]
        edges = [[0, 1], [1, 2], [2, 3], [3, 0]]
        faces = [[0, 1, 2, 3]]
    elif leafShape == 'dFace':
        verts = [Vector((.5, .5, 0)), Vector((.5, -.5, 0)), Vector((-.5, -.5, 0)), Vector((-.5, .5, 0))]
        edges = [[0, 1], [1, 2], [2, 3], [3, 0]]
        faces = [[0, 3, 2, 1]]
    elif leafShape == 'dVert':
        verts = [Vector((0, 0, 1))]
        edges = []
        faces = []

    vertsList = []
    facesList = []
    normal = Vector((0, 0, 1))

    if leafType in ['0', '5']:
        oldRot += radians(137.5)
    elif leafType == '1':
        if ln % 2:
            oldRot += radians(180)
        else:
            oldRot += radians(137.5)
    elif leafType in ['2', '3']:
        oldRot = -copysign(rotate, oldRot)
    elif leafType == '4':
        rotMat = Matrix.Rotation(oldRot + uniform(-rotateV, rotateV), 3, 'Y')
        if leaves == 1:
            rotMat = Matrix.Rotation(0, 3, 'Y')
        else:
            oldRot += rotate / (leaves - 1)

    if leafType != '4':
        rotMat = Matrix.Rotation(oldRot + uniform(-rotateV, rotateV), 3, 'Z')

    # reduce downAngle if leaf is at branch tip
    if (offset == 1):
        if leafType in ['0', '1', '2', '5']:
            downAngle = downAngle * .67
        elif leafType == '3':
            if (leaves / 2) == (leaves // 2):
                downAngle = downAngle * .67
            else:
                downAngle = 0
                downAngleV = 0

    if leafType != '4':
        downV = -downAngleV * offset ** 2
        downRotMat = Matrix.Rotation(downAngle + downV + uniform(-rotateV*0, rotateV*0), 3, 'X')

    zVar = Matrix.Rotation(uniform(-rotateV, rotateV), 3, 'Z')

    #leaf scale variation
    if (leafType == '4') and (rotate != 0) and (leaves > 1):
        f = 1 - abs((oldRot - (rotate / (leaves - 1))) / (rotate / 2))
    else:
        f = offset

    if leafScaleT < 0:
        leafScale = leafScale * (1 - (1 - f) * -leafScaleT)
    else:
        leafScale = leafScale * (1 - f * leafScaleT)

    leafScale = leafScale * uniform(1 - leafScaleV, 1 + leafScaleV)

    if leafShape == 'dFace':
        leafScale = leafScale * .1

    #Rotate leaf vector
    m = Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    if leafType in ['2', '3']:
        m.rotate(Euler((0, 0, radians(90))))
        if oldRot > 0:
            m.rotate(Euler((0, 0, radians(180))))

    if leafType != '4':
        m.rotate(downRotMat)

    m.rotate(rotMat)
    m.rotate(quat)

    # convert rotation for upward facing leaves
    if leafType in ['4', '5']:
        lRot = m
    else:
        v = zAxis.copy()
        v.rotate(m)
        lRot = v.to_track_quat('Z', 'Y')

    # For each of the verts we now rotate and scale them, then append them to the list to be added to the mesh
    for v in verts:
        v.z *= leafScale
        v.y *= leafScale
        v.x *= leafScaleX*leafScale

        if leafShape in ['dVert', 'dFace']:
            v.rotate(leafObjRot)

        v.rotate(Euler((0, 0, radians(180))))

        #rotate variation
        v.rotate(zVar)

        #leafangle
        v.rotate(Matrix.Rotation(radians(-leafangle), 3, 'X'))

        v.rotate(lRot)

    if leafShape == 'dVert':
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