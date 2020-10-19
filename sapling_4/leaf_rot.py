from mathutils import Vector, Matrix


def leaf_rot(leafObjY, leafObjZ):
    def tovector(ax):
        vec = [0, 0, 0]
        a = int(ax[1])
        s = ax[0]
        if s == '+':
            s = 1
        else:
            s = -1
        vec[a] = s
        return Vector(vec)

    yvec = tovector(leafObjY)
    zvec = tovector(leafObjZ)

    xvec = zvec.cross(yvec)

    if zvec[2] in [1, -1]:
        xvec *= -1
    elif xvec[2] in [1, -1]:
        zvec *= -1
        xvec *= -1
    else:
        zvec *= -1
        yvec *= -1
        xvec *= -1

    m = Matrix([xvec, yvec, zvec])
    m = m.to_euler()
    return m