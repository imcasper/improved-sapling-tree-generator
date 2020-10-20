import bpy
from mathutils import Vector
from typing import List

from .gen_leaf_mesh import gen_leaf_mesh
from .ChildPoint import ChildPoint
from .LeafSettings import LeafSettings


def add_leafs(child_points: List[ChildPoint], leaf_settings: LeafSettings, tree_ob):
    leaf_obj = None
    leaf_verts = []
    leaf_faces = []
    leaf_normals = []
    leaf_mesh = None  # in case we aren't creating leaves, we'll still have the variable
    leaf_points = []

    def leafy(old_rotation, cp: ChildPoint, leaf_number):
        (vertTemp, faceTemp, normal, old_rotation) = gen_leaf_mesh(leaf_settings, cp.co, cp.quat, cp.offset, len(leaf_verts), old_rotation, leaf_number)
        leaf_verts.extend(vertTemp)
        leaf_faces.extend(faceTemp)
        leaf_normals.extend(normal)
        leaf_points.append(cp)

    if leaf_settings.leaves:
        old_rotation = 0.0
        # For each of the child points we add leaves
        for leaf_number, cp in enumerate(child_points):
            # If the special flag is set then we need to add several leaves at the same location
            if leaf_settings.leafType == '4':
                old_rotation = -leaf_settings.leafRotate / 2
                for g in range(abs(leaf_settings.leaves)):
                    leafy(old_rotation, cp, leaf_number)
            # Otherwise just add the leaves like splines.
            else:
                leafy(old_rotation, cp, leaf_number)

        # Create the leaf mesh and object, add geometry using from_pydata, edges are currently added by validating the mesh which isn't great
        leaf_mesh = bpy.data.meshes.new('leaves')
        leaf_obj = bpy.data.objects.new('leaves', leaf_mesh)
        bpy.context.scene.collection.objects.link(leaf_obj)
        leaf_obj.parent = tree_ob
        leaf_mesh.from_pydata(leaf_verts, (), leaf_faces)

        # set vertex normals for dupliVerts
        if leaf_settings.leafShape == 'dVert':
            leaf_mesh.vertices.foreach_set('normal', leaf_normals)

        # enable duplication
        if leaf_settings.leafShape == 'dFace':
            leaf_obj.instance_type = "FACES"
            leaf_obj.use_instance_faces_scale = True
            leaf_obj.instance_faces_scale = 10.0
            try:
                bpy.data.objects[leaf_settings.leafDupliObj].parent = leaf_obj
            except KeyError:
                pass
        elif leaf_settings.leafShape == 'dVert':
            leaf_obj.instance_type = "VERTS"
            leaf_obj.use_instance_vertices_rotation = True
            try:
                bpy.data.objects[leaf_settings.leafDupliObj].parent = leaf_obj
            except KeyError:
                pass

        # add leaf UVs
        if leaf_settings.leafShape == 'rect' or leaf_settings.leafShape == 'hex':
            unwrap_leaf_uvs(leaf_faces, leaf_mesh, leaf_settings)

        leaf_mesh.validate()

    return leaf_mesh, leaf_obj, leaf_points


def unwrap_leaf_uvs(leaf_faces, leaf_mesh, leaf_settings: LeafSettings):
    leaf_mesh.uv_layers.new(name='leafUV')
    uv_layer = leaf_mesh.uv_layers.active.data
    u1 = .5 * (1 - leaf_settings.leaf_scale_x)

    x_adj: List[float] = []
    base_x: List[float] = []
    base_y: List[float] = []

    (x_adj, base_x, base_y) = leaf_settings.get_uv_list()

    u_list1: List[float] = [e * u1 for e in x_adj]
    x_list: List[float] = []
    y_list: List[float] = base_y
    for e, f in zip(u_list1, base_x):
        x_list.append(e+f)

    num_v = len(x_list)
    ugg = (leaf_settings.leafVertSize-2)/2
    for i in range(0, int(len(leaf_faces) / ugg)):
        for j in range(num_v):
            uv_layer[i * num_v + j].uv = Vector((x_list[j], y_list[j]))