import os
from lr2_terrain import LR2_Terrain

import terr_bundler
import bl_terr_make_mesh
import bl_terr_create_renderer


def _solve_terrain_simplified_name(terrain_name: str):
    _dict = {
        "SANDY BAY": "SANDY ISLAND",
        "ADVENTURE ISLAND": "ADVENTURERS",
        "MARS": os.path.join("LOM", "OKSES_LOVECHILD"),
        "ARCTIC": os.path.join("ARCTIC", "ROBS LOVE CHILD"),
        "XALAX/TRACK01": os.path.join("CAR_CRAZE", "TRACK01"),
        "XALAX/TRACK02": os.path.join("CAR_CRAZE", "TRACK02"),
        "XALAX/TRACK03": os.path.join("CAR_CRAZE", "TRACK03"),
        "XALAX/TRACK04": os.path.join("CAR_CRAZE", "TRACK04"),
        "XALAX/TRACK05": os.path.join("CAR_CRAZE", "TRACK05")
    }
    if terrain_name not in _dict:
        return None
    return _dict[terrain_name]


def _solve_terrain_paths(
        lr2_gamedata_path: str,
        png_textures_pack_path: str,
        terrain_name: str
):
    if not os.path.isdir(lr2_gamedata_path):
        raise Exception("Invalid path: %s" % lr2_gamedata_path)

    if not os.path.isdir(png_textures_pack_path):
        raise Exception("Invalid path: %s" % png_textures_pack_path)

    raw_terr_name = _solve_terrain_simplified_name(terrain_name)
    if not raw_terr_name:
        raise Exception("Invalid terrain name: %s" % terrain_name)

    return (
        os.path.join(lr2_gamedata_path, "GAME DATA", "EDITOR GEN", "TERRAIN", raw_terr_name),
        os.path.join(png_textures_pack_path, "EDITOR GEN", "TERRAIN", raw_terr_name)
    )


def bundle_terrain(
        lr2_gamedata_path: str,
        png_textures_pack_path: str,
        terrain_name: str
):
    (terr_path, terr_png_tex_path) = _solve_terrain_paths(lr2_gamedata_path, png_textures_pack_path, terrain_name)

    tdf_path = os.path.join(terr_path, "TERRDATA.TDF")
    lr2_terr = LR2_Terrain.from_file(tdf_path)

    terr_bundler.bundle(lr2_terr, terr_png_tex_path)


def import_terrain(
        lr2_gamedata_path: str,
        png_textures_pack_path: str,
        terrain_name: str
):
    (terr_path, terr_png_tex_path) = _solve_terrain_paths(lr2_gamedata_path, png_textures_pack_path, terrain_name)

    tdf_path = os.path.join(terr_path, "TERRDATA.TDF")
    lr2_terr = LR2_Terrain.from_file(tdf_path)

    (tileset_tex, num_tiles, layers_map_tex, alpha_map_tex) = terr_bundler.get_bundle_info(terr_png_tex_path)

    # Bundle errors
    if not os.path.isfile(tileset_tex) or not os.path.isfile(layers_map_tex) or not os.path.isfile(alpha_map_tex):
        raise Exception("Some of the bundle info are missing. Run this script outside Blender to generate them.")

    if num_tiles <= 0:
        raise Exception("num_tiles <= 0, is the PNG texture pack valid?")

    bl_terr_make_mesh.make_mesh(terrain_name, lr2_terr)
    bl_terr_create_renderer.create_renderer(tileset_tex, num_tiles, layers_map_tex, alpha_map_tex)
