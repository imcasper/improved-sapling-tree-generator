import bpy
from mathutils import Vector

from add_curve_sapling_3.gen_leaf_mesh import gen_leaf_mesh


def add_leafs(child_points, leaf_obj, leaf_settings, tree_ob):
    leaf_verts = []
    leaf_faces = []
    leaf_normals = []
    leaf_mesh = None  # in case we aren't creating leaves, we'll still have the variable
    leaf_points = []
    if leaf_settings.leaves:
        old_rotation = 0.0
        # n = min(3, n+1)
        # For each of the child points we add leaves
        for leaf_number, cp in enumerate(child_points):
            # If the special flag is set then we need to add several leaves at the same location
            if leaf_settings.leafType == '4':
                old_rotation = -leaf_settings.leafRotate / 2
                for g in range(abs(leaf_settings.leaves)):
                    (vertTemp, faceTemp, normal, old_rotation) = gen_leaf_mesh(leaf_settings, cp.co, cp.quat, cp.offset, len(leaf_verts), old_rotation, leaf_number)
                    leaf_verts.extend(vertTemp)
                    leaf_faces.extend(faceTemp)
                    leaf_normals.extend(normal)
                    leaf_points.append(cp)
            # Otherwise just add the leaves like splines.
            else:
                (vertTemp, faceTemp, normal, old_rotation) = gen_leaf_mesh(leaf_settings, cp.co, cp.quat, cp.offset, len(leaf_verts), old_rotation, leaf_number)
                leaf_verts.extend(vertTemp)
                leaf_faces.extend(faceTemp)
                leaf_normals.extend(normal)
                leaf_points.append(cp)

        # Create the leaf mesh and object, add geometry using from_pydata, edges are currently added by validating the mesh which isn't great
        leaf_mesh = bpy.data.meshes.new('leaves')
        leaf_obj = bpy.data.objects.new('leaves', leaf_mesh)
        bpy.context.scene.objects.link(leaf_obj)
        leaf_obj.parent = tree_ob
        leaf_mesh.from_pydata(leaf_verts, (), leaf_faces)

        # set vertex normals for dupliVerts
        if leaf_settings.leafShape == 'dVert':
            leaf_mesh.vertices.foreach_set('normal', leaf_normals)

        # enable duplication
        if leaf_settings.leafShape == 'dFace':
            leaf_obj.dupli_type = "FACES"
            leaf_obj.use_dupli_faces_scale = True
            leaf_obj.dupli_faces_scale = 10.0
            try:
                bpy.data.objects[leaf_settings.leafDupliObj].parent = leaf_obj
            except KeyError:
                pass
        elif leaf_settings.leafShape == 'dVert':
            leaf_obj.dupli_type = "VERTS"
            leaf_obj.use_dupli_vertices_rotation = True
            try:
                bpy.data.objects[leaf_settings.leafDupliObj].parent = leaf_obj
            except KeyError:
                pass

        # add leaf UVs
        if leaf_settings.leafShape == 'rect':
            leaf_mesh.uv_textures.new("leafUV")
            uv_layer = leaf_mesh.uv_layers.active.data

            u1 = .5 * (1 - leaf_settings.leafScaleX)
            u2 = 1 - u1

            for i in range(0, len(leaf_faces)):
                uv_layer[i * 4 + 0].uv = Vector((u2, 0))
                uv_layer[i * 4 + 1].uv = Vector((u2, 1))
                uv_layer[i * 4 + 2].uv = Vector((u1, 1))
                uv_layer[i * 4 + 3].uv = Vector((u1, 0))

        elif leaf_settings.leafShape == 'hex':
            leaf_mesh.uv_textures.new("leafUV")
            uv_layer = leaf_mesh.uv_layers.active.data

            u1 = .5 * (1 - leaf_settings.leafScaleX)
            u2 = 1 - u1

            for i in range(0, int(len(leaf_faces) / 2)):
                uv_layer[i * 8 + 0].uv = Vector((.5, 0))
                uv_layer[i * 8 + 1].uv = Vector((u1, 1 / 3))
                uv_layer[i * 8 + 2].uv = Vector((u1, 2 / 3))
                uv_layer[i * 8 + 3].uv = Vector((.5, 1))

                uv_layer[i * 8 + 4].uv = Vector((.5, 0))
                uv_layer[i * 8 + 5].uv = Vector((.5, 1))
                uv_layer[i * 8 + 6].uv = Vector((u2, 2 / 3))
                uv_layer[i * 8 + 7].uv = Vector((u2, 1 / 3))

        leaf_mesh.validate()
    return leaf_mesh, leaf_obj, leaf_points