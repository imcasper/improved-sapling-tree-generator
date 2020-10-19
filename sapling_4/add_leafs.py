import bpy
from mathutils import Vector
from typing import List

from .gen_leaf_mesh import gen_leaf_mesh
from .ChildPoint import ChildPoint
from .LeafSettings import LeafSettings


def add_leafs(childP: ChildPoint, leafObj, leaf_settings, lvl, treeOb):
    leafVerts = []
    leafFaces = []
    leafNormals = []
    leafMesh = None  # in case we aren't creating leaves, we'll still have the variable
    leafP = []

    def leafy(old_rotation, cp: ChildPoint, ln):
        (vertTemp, faceTemp, normal, old_rotation) = gen_leaf_mesh(leaf_settings, cp.co, cp.quat, cp.offset, len(leafVerts), old_rotation, ln)
        leafVerts.extend(vertTemp)
        leafFaces.extend(faceTemp)
        leafNormals.extend(normal)
        leafP.append(cp)

    if leaf_settings.leaves:
        oldRot = 0.0
        lvl = min(3, lvl + 1)
        # For each of the child points we add leaves
        for ln, cp in enumerate(childP):
            # If the special flag is set then we need to add several leaves at the same location
            if leaf_settings.leafType == '4':
                oldRot = -leaf_settings.leafRotate / 2
                for g in range(abs(leaf_settings.leaves)):
                    leafy(oldRot, cp, ln)
            # Otherwise just add the leaves like splines.
            else:
                leafy(oldRot, cp, ln)

        # Create the leaf mesh and object, add geometry using from_pydata, edges are currently added by validating the mesh which isn't great
        leafMesh = bpy.data.meshes.new('leaves')
        leafObj = bpy.data.objects.new('leaves', leafMesh)
        bpy.context.scene.collection.objects.link(leafObj)
        leafObj.parent = treeOb
        leafMesh.from_pydata(leafVerts, (), leafFaces)

        # set vertex normals for dupliVerts
        if leaf_settings.leafShape == 'dVert':
            leafMesh.vertices.foreach_set('normal', leafNormals)

        # enable duplication
        if leaf_settings.leafShape == 'dFace':
            leafObj.instance_type = "FACES"
            leafObj.use_instance_faces_scale = True
            leafObj.instance_faces_scale = 10.0
            try:
                bpy.data.objects[leaf_settings.leafDupliObj].parent = leafObj
            except KeyError:
                pass
        elif leaf_settings.leafShape == 'dVert':
            leafObj.instance_type = "VERTS"
            leafObj.use_instance_vertices_rotation = True
            try:
                bpy.data.objects[leaf_settings.leafDupliObj].parent = leafObj
            except KeyError:
                pass

        # add leaf UVs
        if leaf_settings.leafShape == 'rect' or leaf_settings.leafShape == 'hex':
            unwrap_leaf_uvs(leafFaces, leafMesh, leaf_settings)

        leafMesh.validate()

    return leafMesh, leafObj, leafP

# def unwrap_leaf_uvs_hex(leafFaces, leafMesh, leaf_settings):
#     leafMesh.uv_layers.new(name="leafUV")
#     uvlayer = leafMesh.uv_layers.active.data
#     u1 = .5 * (1 - leaf_settings.leafScaleX)
#     u2 = 1 - u1
#     for i in range(0, int(len(leafFaces) / 2)):
#         uvlayer[i * 8 + 0].uv = Vector((.5, 0))
#         uvlayer[i * 8 + 1].uv = Vector((u1, 1 / 3))
#         uvlayer[i * 8 + 2].uv = Vector((u1, 2 / 3))
#         uvlayer[i * 8 + 3].uv = Vector((.5, 1))
#
#         uvlayer[i * 8 + 4].uv = Vector((.5, 0))
#         uvlayer[i * 8 + 5].uv = Vector((.5, 1))
#         uvlayer[i * 8 + 6].uv = Vector((u2, 2 / 3))
#         uvlayer[i * 8 + 7].uv = Vector((u2, 1 / 3))
#
#
# def unwrap_leaf_uvs_rect(leafFaces, leafMesh, leaf_settings):
#     leafMesh.uv_layers.new(name="leafUV")
#     uvlayer = leafMesh.uv_layers.active.data
#     u1 = .5 * (1 - leaf_settings.leafScaleX)
#     u2 = 1 - u1
#     for i in range(0, len(leafFaces)):
#         uvlayer[i * 4 + 0].uv = Vector((u2, 0))
#         uvlayer[i * 4 + 1].uv = Vector((u2, 1))
#         uvlayer[i * 4 + 2].uv = Vector((u1, 1))
#         uvlayer[i * 4 + 3].uv = Vector((u1, 0))


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