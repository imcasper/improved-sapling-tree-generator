from mathutils import Vector, Matrix


def leaf_rot(leaf_obj_y, leaf_obj_z):
    def to_vector(ax):
        vec = [0, 0, 0]
        a = int(ax[1])
        s = ax[0]
        if s == '+':
            s = 1
        else:
            s = -1
        vec[a] = s
        return Vector(vec)

    y_vec = to_vector(leaf_obj_y)
    z_vec = to_vector(leaf_obj_z)

    x_vec = z_vec.cross(y_vec)

    if z_vec[2] in [1, -1]:
        x_vec *= -1
    elif x_vec[2] in [1, -1]:
        z_vec *= -1
        x_vec *= -1
    else:
        z_vec *= -1
        y_vec *= -1
        x_vec *= -1

    m = Matrix([x_vec, y_vec, z_vec])
    m = m.to_euler()
    return m
