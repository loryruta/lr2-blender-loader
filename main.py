# http://web.purplefrog.com/~thoth/blender/python-cookbook/import-python.html

LR2_IMPORTER_PATH = "C:\\Users\\rutayisire\\PycharmProjects\\lr2"  # Edit here

# ================================================================================================

import sys
import os

if not os.path.isdir(LR2_IMPORTER_PATH):
    raise Exception("Invalid path: %s" % LR2_IMPORTER_PATH)

_dir = LR2_IMPORTER_PATH
if _dir not in sys.path:
    sys.path.append(_dir)

import lr2_importer

import importlib
importlib.reload(lr2_importer)

import lr2_importer


def import_terrain(
        gamedata_path: str,
        png_pack_path: str,
        terrain_name: str
):
    if len(sys.argv) > 1 and sys.argv[1] == 'bundle':
        lr2_importer.bundle_terrain(gamedata_path, png_pack_path, terrain_name)
        print(terrain_name + " bundled!")
    else:
        lr2_importer.import_terrain(gamedata_path, png_pack_path, terrain_name)
        print(terrain_name + " imported!")

# ================================================================================================

# Edit here
import_terrain(
    "C:\\Users\\rutayisire\\Desktop\\LR2\\GAMEDATA",
    "C:\\Users\\rutayisire\\Desktop\\LR2\\LEGO Racers 2 Textures (PNG)",
    "MARS"
)
