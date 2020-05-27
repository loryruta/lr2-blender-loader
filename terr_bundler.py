from lr2_terrain import *
import re


def get_bundle_info(terr_png_textures: str):
    return (
        os.path.join(terr_png_textures, "tileset.png"),
        len([file for file in os.listdir(terr_png_textures) if re.match(r'TEXTURE[0-9]+\.png$', file)]),  # num_tiles
        os.path.join(terr_png_textures, "layers_map.png"),
        os.path.join(terr_png_textures, "alpha_map.png")
    )


def create_terrain_tileset(terrain_path: str, out: str):
    from PIL import Image

    num_tiles = 0
    while True:
        path = os.path.join(terrain_path, "TEXTURE%i.png" % (num_tiles + 1))
        if not os.path.exists(path):
            break
        num_tiles += 1

    num_tiles += 1  # Leaves space for the empty layer.

    tile_side = 256
    tileset = Image.new("RGBA", (tile_side * num_tiles, tile_side), color=(0, 0, 0, 255))

    for tile_id in range(1, num_tiles):
        path = os.path.join(terrain_path, "TEXTURE%i.png" % tile_id)

        tile = Image.open(path)
        if tile.width != tile.height:
            raise Exception("Tile isn't a quad:", path)

        if tile.width != tile_side:
            tile = tile.resize((tile_side, tile_side))
            #print("resized:", path)

        tileset.paste(tile, (tile_id * 256, 0))

    tileset.save(out, format="png")
    return num_tiles


def create_layers_map(terrain: LR2_Terrain, num_tiles: int, out: str):
    from PIL import Image

    width = terrain.NumGridsX
    height = terrain.NumGridsY

    img = Image.new("RGBA", (width, height))

    for grid_x in range(0, terrain.NumGridsX):
        for grid_y in range(0, terrain.NumGridsY):
            grid = terrain.grid_at(grid_x, grid_y)

            rgba = [0, 0, 0, 0]
            for layer_idx in range(0, grid.NumLayers):
                tile_id = grid.LayerTextureIndex[layer_idx]  # [-1, 11]
                tile_id += 1
                tile_id /= num_tiles

                rgba[layer_idx] = int(tile_id * 255)

            img.putpixel((grid_x, height - grid_y - 1), tuple(rgba))

    img.save(out, format="png")


def create_alpha_map(terrain: LR2_Terrain, out: str):
    from PIL import Image

    GridNumX = 17
    GridNumY = 17

    width = terrain.NumGridsX * GridNumX
    height = terrain.NumGridsY * GridNumY

    img = Image.new("RGBA", (width, height))

    for grid_x in range(0, terrain.NumGridsX):
        for grid_y in range(0, terrain.NumGridsY):
            grid = terrain.grid_at(grid_x, grid_y)

            for x in range(0, GridNumX):
                for y in range(0, GridNumY):
                    point = terrain.point_at(grid_x, grid_y, 0, x, y)

                    tiles_alpha = [
                        int(point.LayerAlpha.Layer1Alpha / 0xf * 0xff),
                        int(point.LayerAlpha.Layer2Alpha / 0xf * 0xff),
                        int(point.LayerAlpha.Layer3Alpha / 0xf * 0xff),
                        int(point.LayerAlpha.Layer4Alpha / 0xf * 0xff)
                    ]

                    for i in range(0, len(tiles_alpha)):
                        tile_alpha = tiles_alpha[i]
                        tile_idx = grid.LayerTextureIndex[i]
                        if tile_alpha > 0 and tile_idx < 0:
                            #print("Tile alpha is > 0, but the tile doesn't exist! tile_alpha=%d tile_idx=%d" % (tile_alpha, tile_idx))
                            tiles_alpha[i] = 0

                    img.putpixel((grid_x * GridNumX + x, height - (grid_y * GridNumY + y) - 1), tuple(tiles_alpha))

    img.save(out, format="png")


def bundle(lr2_terrain: LR2_Terrain, terr_png_textures: str):
    """
    Having the terrain and the set of tiles that lies on it.
    This script creates 3 different textures that, if mixed up wisely, will give the whole terrain texture.

    :param lr2_terrain:       Actually, the loaded TDF file.
    :param terr_png_textures: The path to the terrain's PNG textures.
    """

    if not os.path.isdir(terr_png_textures):
        raise Exception("Invalid path: %s" % terr_png_textures)

    (tileset_path, _, layers_map_path, alpha_map_path) = get_bundle_info(terr_png_textures)

    # Tileset
    num_tiles = create_terrain_tileset(terr_png_textures, tileset_path)
    print("Tileset (num_tiles=%d): %s" % (num_tiles, tileset_path))

    # Layers map
    create_layers_map(lr2_terrain, num_tiles, layers_map_path)
    print("Layers map: %s" % layers_map_path)

    # Alpha map
    create_alpha_map(lr2_terrain, alpha_map_path)
    print("Alpha map: %s" % alpha_map_path)

