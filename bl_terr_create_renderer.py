import bpy


def create_renderer(
        tileset_png: str,
        num_tiles: int,
        layers_map_png: str,
        alpha_map_png: str
):
    """
    Creates the Material's NodeTree used to render the terrain.

    :param tileset_png:    The path to the generated tileset.
    :param num_tiles:      The number of tiles contained in the tileset (including the NULL one).
    :param layers_map_png: The path to the generated layers map.
    :param alpha_map_png:  The path to the generated alpha map.
    """

    tileset_img = bpy.data.images.load(tileset_png)
    tileset_img.colorspace_settings.name = "sRGB"

    layers_map_img = bpy.data.images.load(layers_map_png)
    layers_map_img.colorspace_settings.name = "Raw"

    alpha_map_img = bpy.data.images.load(alpha_map_png)
    alpha_map_img.colorspace_settings.name = "Raw"

    mat = bpy.context.object.active_material
    mat.use_nodes = True  # Important!

    # ========================================================================
    # TileUV
    # ========================================================================

    TileUV = bpy.data.node_groups.new("TileUV", "ShaderNodeTree")

    # UVMap
    # TODO UVs can be directly retrived from terrain vertices.
    uv_map = TileUV.nodes.new("ShaderNodeUVMap")
    uv_map.uv_map = "texture_uv_layers"

    # TileUV > Divide
    divide = TileUV.nodes.new("ShaderNodeVectorMath")
    divide.operation = "DIVIDE"
    divide.inputs[1].default_value = [num_tiles, 1, 0]

    # TileUV > GroupOutput
    _out = TileUV.nodes.new("NodeGroupOutput")
    TileUV.outputs.new("NodeSocketVector", "Tile_UV")

    TileUV.links.new(uv_map.outputs[0], divide.inputs[0])
    TileUV.links.new(divide.outputs[0], _out.inputs[0])

    # ========================================================================
    # TileByXShift
    # ========================================================================

    TileByXShift = bpy.data.node_groups.new("TileByXShift", "ShaderNodeTree")

    # GroupInput
    _in = TileByXShift.nodes.new("NodeGroupInput")
    TileByXShift.inputs.new("NodeSocketFloat", "X")

    # TileUV
    tile_uv = TileByXShift.nodes.new("ShaderNodeGroup")
    tile_uv.node_tree = TileUV

    # Add
    add = TileByXShift.nodes.new("ShaderNodeVectorMath")
    add.operation = "ADD"

    # TilesetImgTex
    tileset_tex = TileByXShift.nodes.new("ShaderNodeTexImage")
    tileset_tex.image = tileset_img

    # GroupOutput
    _out = TileByXShift.nodes.new("NodeGroupOutput")
    TileByXShift.outputs.new("NodeSocketVector", "Color")

    TileByXShift.links.new(tile_uv.outputs[0], add.inputs[0])
    TileByXShift.links.new(_in.outputs[0], add.inputs[1])
    TileByXShift.links.new(add.outputs[0], tileset_tex.inputs[0])
    TileByXShift.links.new(tileset_tex.outputs[0], _out.inputs[0])

    # ========================================================================
    # OpenGL Blending
    # ========================================================================
    # https://learnopengl.com/Advanced-OpenGL/Blending

    OpenGlBlending = bpy.data.node_groups.new("OpenGlBlending", "ShaderNodeTree")

    # GroupInput
    _in = OpenGlBlending.nodes.new("NodeGroupInput")
    OpenGlBlending.inputs.new("NodeSocketColor", "Srgb")
    OpenGlBlending.inputs.new("NodeSocketFloat", "Sa")
    OpenGlBlending.inputs.new("NodeSocketColor", "Drgb")
    OpenGlBlending.inputs.new("NodeSocketFloat", "Da")

    # Sa * Srgb
    sa_srgb = OpenGlBlending.nodes.new("ShaderNodeVectorMath")
    sa_srgb.operation = "MULTIPLY"

    # 1 - Sa
    _1_sa = OpenGlBlending.nodes.new("ShaderNodeVectorMath")
    _1_sa.operation = "SUBTRACT"
    _1_sa.inputs[0].default_value = [1, 1, 1]

    # (1 - Sa) * Drgb
    _1_Sa_Drgb = OpenGlBlending.nodes.new("ShaderNodeVectorMath")
    _1_Sa_Drgb.operation = "MULTIPLY"

    # (1 - Sa) * Da
    _1_Sa_Da = OpenGlBlending.nodes.new("ShaderNodeVectorMath")
    _1_Sa_Da.operation = "MULTIPLY"

    # _Srgb + _Drgb = Orgb
    _Srgb_Drgb = OpenGlBlending.nodes.new("ShaderNodeVectorMath")
    _Srgb_Drgb.operation = "ADD"

    # _Sa + _Da = Oa
    _Sa_Da = OpenGlBlending.nodes.new("ShaderNodeVectorMath")
    _Sa_Da.operation = "ADD"

    # GroupOutput
    _out = OpenGlBlending.nodes.new("NodeGroupOutput")
    OpenGlBlending.outputs.new("NodeSocketColor", "Orgb")
    OpenGlBlending.outputs.new("NodeSocketFloat", "Oa")

    OpenGlBlending.links.new(_in.outputs["Srgb"], sa_srgb.inputs[0])
    OpenGlBlending.links.new(_in.outputs["Sa"], sa_srgb.inputs[1])
    OpenGlBlending.links.new(_in.outputs["Sa"], _1_sa.inputs[1])
    OpenGlBlending.links.new(_in.outputs["Drgb"], _1_Sa_Drgb.inputs[0])
    OpenGlBlending.links.new(_1_sa.outputs[0], _1_Sa_Drgb.inputs[1])
    OpenGlBlending.links.new(sa_srgb.outputs[0], _Srgb_Drgb.inputs[0])
    OpenGlBlending.links.new(_1_Sa_Drgb.outputs[0], _Srgb_Drgb.inputs[1])
    OpenGlBlending.links.new(_Srgb_Drgb.outputs[0], _out.inputs["Orgb"])

    OpenGlBlending.links.new(_in.outputs["Da"], _1_Sa_Da.inputs[0])
    OpenGlBlending.links.new(_1_sa.outputs[0], _1_Sa_Da.inputs[1])
    OpenGlBlending.links.new(_in.outputs["Sa"], _Sa_Da.inputs[0])
    OpenGlBlending.links.new(_1_Sa_Da.outputs[0], _Sa_Da.inputs[1])
    OpenGlBlending.links.new(_Sa_Da.outputs[0], _out.inputs["Oa"])

    # ========================================================================
    # Terrain Renderer
    # ========================================================================

    main = mat.node_tree

    # Object
    obj = main.nodes.new("ShaderNodeTexCoord")

    # ------------------------------------------------------------------------
    # Layers map
    # ------------------------------------------------------------------------

    # Image
    layers_map = main.nodes.new("ShaderNodeTexImage")
    layers_map.image = layers_map_img
    layers_map.interpolation = "Closest"

    # RGB
    layers_map_rgb = main.nodes.new("ShaderNodeSeparateRGB")

    tile_shift_1 = main.nodes.new("ShaderNodeGroup")
    tile_shift_1.node_tree = TileByXShift

    tile_shift_2 = main.nodes.new("ShaderNodeGroup")
    tile_shift_2.node_tree = TileByXShift

    tile_shift_3 = main.nodes.new("ShaderNodeGroup")
    tile_shift_3.node_tree = TileByXShift

    tile_shift_4 = main.nodes.new("ShaderNodeGroup")
    tile_shift_4.node_tree = TileByXShift

    # ------------------------------------------------------------------------
    # Alpha map
    # ------------------------------------------------------------------------

    # Image
    alpha_map = main.nodes.new("ShaderNodeTexImage")
    alpha_map.image = alpha_map_img
    alpha_map.interpolation = "Closest"

    # RGB
    alpha_map_rgb = main.nodes.new("ShaderNodeSeparateRGB")

    # ------------------------------------------------------------------------
    # Blending
    # ------------------------------------------------------------------------

    blending_1 = main.nodes.new("ShaderNodeGroup")
    blending_1.node_tree = OpenGlBlending
    blending_1.inputs["Drgb"].default_value = [0, 0, 0, 0]
    blending_1.inputs["Da"].default_value = 0

    blending_2 = main.nodes.new("ShaderNodeGroup")
    blending_2.node_tree = OpenGlBlending

    blending_3 = main.nodes.new("ShaderNodeGroup")
    blending_3.node_tree = OpenGlBlending

    blending_4 = main.nodes.new("ShaderNodeGroup")
    blending_4.node_tree = OpenGlBlending

    main.links.new(obj.outputs["Object"], layers_map.inputs[0])
    main.links.new(layers_map.outputs["Color"], layers_map_rgb.inputs[0])
    main.links.new(layers_map_rgb.outputs["R"], tile_shift_1.inputs[0])
    main.links.new(layers_map_rgb.outputs["G"], tile_shift_2.inputs[0])
    main.links.new(layers_map_rgb.outputs["B"], tile_shift_3.inputs[0])
    main.links.new(layers_map.outputs["Alpha"], tile_shift_4.inputs[0])

    main.links.new(obj.outputs["Object"], alpha_map.inputs[0])
    main.links.new(alpha_map.outputs["Color"], alpha_map_rgb.inputs[0])

    main.links.new(blending_1.inputs["Srgb"], tile_shift_1.outputs[0])
    main.links.new(blending_1.inputs["Sa"], alpha_map_rgb.outputs["R"])

    main.links.new(blending_2.inputs["Srgb"], tile_shift_2.outputs[0])
    main.links.new(blending_2.inputs["Sa"], alpha_map_rgb.outputs["G"])
    main.links.new(blending_2.inputs["Drgb"], blending_1.outputs["Orgb"])
    main.links.new(blending_2.inputs["Da"], blending_1.outputs["Oa"])

    main.links.new(blending_3.inputs["Srgb"], tile_shift_3.outputs[0])
    main.links.new(blending_3.inputs["Sa"], alpha_map_rgb.outputs["B"])
    main.links.new(blending_3.inputs["Drgb"], blending_2.outputs["Orgb"])
    main.links.new(blending_3.inputs["Da"], blending_2.outputs["Oa"])

    main.links.new(blending_4.inputs["Srgb"], tile_shift_4.outputs[0])
    main.links.new(blending_4.inputs["Sa"], alpha_map.outputs["Alpha"])
    main.links.new(blending_4.inputs["Drgb"], blending_3.outputs["Orgb"])
    main.links.new(blending_4.inputs["Da"], blending_3.outputs["Oa"])

    # ========================================================================
    # Material output
    # ========================================================================
    # The resulting Color + Alpha is attached to the Principled BSDF node of the material.

    mat_node = main.nodes.get("Principled BSDF")

    main.links.new(mat_node.inputs["Base Color"], blending_4.outputs["Orgb"])
    main.links.new(mat_node.inputs["Alpha"], blending_4.outputs["Oa"])


