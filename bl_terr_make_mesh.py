import bpy
from lr2_terrain import *
import math


def build_geometry(terrain: LR2_Terrain):
    # Vertices
    vertices = []
    faces = []
    uvs = []

    faces_offset = 0

    (min_x, min_y) = (math.inf, math.inf)
    (max_x, max_y) = (-math.inf, -math.inf)

    for grid_x in range(0, terrain.NumGridsX):
        for grid_y in range(0, terrain.NumGridsY):
            grid = terrain.grid_at(grid_x, grid_y)
            map_grid = grid.GridHeightData[0]

            offset_x = grid.StartX
            offset_z = grid.StartY

            num_x = map_grid.NumX
            num_y = map_grid.NumY

            # How textures work?
            # print_ctype("Grid[%d][%d].LayerTextureIndex" % (grid_x, grid_y), grid.LayerTextureIndex)
            # print_ctype("Grid[%d][%d].map.point[0].LayerAlpha" % (grid_x, grid_y), points_by_lod[0][map_grid.pHeightData].LayerAlpha)

            # Vertices
            num_vertices = num_x * num_y
            for pos_x in range(0, num_x):
                for pos_y in range(0, num_y):
                    point = terrain.point_at(grid_x, grid_y, 0, pos_x, pos_y)

                    if num_x != 17 or num_y != 17:
                        raise Exception("LOD is not 0! num_x=%d num_y=%d" % (num_x, num_y))

                    # Get the coordinates within the terrain, that are [0, 513).
                    vx = float(pos_x) + offset_x
                    vy = float(pos_y) + offset_z

                    # According to TDF, the height of the points is scaled by filter-scale (~0.1).
                    vz = (float(point.Height)) * terrain.FilterScale

                    # Normalizes the vertices along X and Y axes by scaling them by TerrainWidth (=TerrainDepth).
                    # The height is scaled, but not normalized.
                    vx /= terrain.TerrainWidth
                    vy /= terrain.TerrainWidth
                    vz /= terrain.TerrainWidth

                    vertices.append([vx, vy, vz])

                    uvs.append((
                        pos_x / num_x,
                        pos_y / num_y
                    ))

            # Faces
            for pos_x in range(0, num_x - 1):
                for pos_y in range(0, num_y - 1):
                    v_pool = {
                        0: pos_x + pos_y * num_x,
                        1: (pos_x + 1) + pos_y * num_x,
                        2: pos_x + (pos_y + 1) * num_x,
                        3: (pos_x + 1) + (pos_y + 1) * num_x
                    }

                    def is_hollowed(face):
                        for v_pos in face:
                            if terrain.pPointBase[0][map_grid.pHeightData + v_pos].InvisiblePoly:
                                return True
                        return False

                    def apply_offset(face):
                        for i in range(0, len(face)):
                            face[i] += faces_offset
                        return face

                    face_1 = [v_pool[0], v_pool[1], v_pool[2]]
                    faces.append(apply_offset(face_1))

                    face_2 = [v_pool[2], v_pool[1], v_pool[3]]
                    faces.append(apply_offset(face_2))

            faces_offset += num_vertices

    return vertices, faces, uvs


def create_mesh(obj_name: str, vertices, faces):
    mesh = bpy.data.meshes.new(obj_name)
    mesh.from_pydata(vertices, [], faces)
    return mesh


def create_material(obj_name: str):
    material = bpy.data.materials.new(obj_name)
    return material


def make_mesh(name: str, terrain: LR2_Terrain):
    layer = bpy.context.view_layer

    # Object
    obj_name = name.capitalize()

    (vert, faces, uvs) = build_geometry(terrain)
    mesh = create_mesh(obj_name, vert, faces)
    _object = bpy.data.objects.new(name=obj_name, object_data=mesh)

    layer.active_layer_collection.collection.objects.link(_object)
    layer.objects.active = _object
    _object.select_set(True)

    # Material
    mat = create_material(obj_name)
    bpy.ops.object.material_slot_add()
    _object.material_slots[0].material = mat
    mat.use_nodes = True

    # UV
    bpy.ops.mesh.uv_texture_add()
    mesh.uv_layers[0].name = "texture_uv_layers"

    for poly in mesh.polygons:
        for v_idx, l_idx in zip(poly.vertices, poly.loop_indices):
            mesh.uv_layers[0].data[l_idx].uv = uvs[v_idx]

