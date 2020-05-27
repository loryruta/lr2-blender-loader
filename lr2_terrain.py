from ctypes import *
from typing import *
import os


def read_ctype(file, ctype, verbose=False):
    size = sizeof(ctype)
    c_obj = ctype.from_buffer(bytearray(file.read(size)))
    if verbose:
        print("Read %s (%d)" % (ctype, size))
    if hasattr(c_obj, "value"):
        return c_obj.value
    return c_obj


class Vector(Structure):
    _fields_ = [
        ('x', c_float),
        ('y', c_float),
        ('z', c_float),
    ]


class cTextureUV(Structure):
    _fields_ = [
        ('U', c_float),
        ('V', c_float)
    ]


class sLayerAlpha(Structure):
    _fields_ = [
        ("Layer1Alpha", c_uint16, 4),
        ("Layer2Alpha", c_uint16, 4),
        ("Layer3Alpha", c_uint16, 4),
        ("Layer4Alpha", c_uint16, 4)
    ]


class sHMapPoint(Structure):
    _fields_ = [
        ("Height", c_uint16),
        ("NormalX", c_int8),
        ("NormalY", c_int8),
        ("NormalZ", c_int8),
        ("Hollowed", c_bool, 1),
        ("Padding", c_uint8, 6),
        ("InvisiblePoly", c_bool, 1),
        ("LayerAlpha", sLayerAlpha),
    ]


class sMapGrid(Structure):
    _fields_ = [
        ("pHeightData", c_uint32),
        ("NumX", c_int16),
        ("NumY", c_int16),
        ("pEdgeDataBase", c_uint32),
        ("OriEdgeDataOffset", c_int16 * 4),
        ("MIPEdgeDataOffset", c_int16 * 4),
        ("EdgeMipped", c_int8 * 4)
    ]


class sTerrCornerPos(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
        ("z", c_float),
        ("w", c_float)
    ]


class sTerrGridInf(Structure):
    _fields_ = [
        ("CentrePos", Vector),
        ("StartX", c_int16),
        ("StartY", c_int16),
        ("GridCorners", sTerrCornerPos * 8),
        ("GridHeightData", sMapGrid * 4),
        ("Pad", c_int8 * 8),
        ("LayerTextureIndex", c_int8 * 4),

        ("DetailLevel", c_int8),
        ("ClipRender", c_int8),
        ("ContiguousTextures", c_int8, 1),
        ("MaxDetailLevel", c_int8, 7),
        ("NumLayers", c_int8)
    ]


class LR2_Terrain:
    # Constants
    MagicNumber: int = ord('T') + (ord('D') << 8) + (ord('F') << 16) + (ord('1') << 24)

    NumGridsX: int = 32
    NumGridsY: int = 32
    NumGrids: int = NumGridsX * NumGridsY

    MAX_MIP_LEVELS: int = 4

    # Header
    NumTexLayers: int
    TerrainWidth: int
    TerrainDepth: int

    GridWidth: float
    GridHeight: float

    FilterScale: float
    DimensionScalar: Vector = Vector(1, 1, 1)

    NumAllocatedMipXs: int
    NumMipLevels: int
    NumAllocatedMipEdges: int

    TerrGridDataSize: int

    StepX: int
    StepY: int

    pPointBase: Dict[int, POINTER(sHMapPoint)] = {}
    pEdgeBase: Dict[int, POINTER(c_uint16)] = {}
    pTerrGrids: Dict[int, sTerrGridInf] = {}

    def __init__(self):
        pass

    def grid_idx(self, x, y) -> int:
        return x * self.NumGridsY + y

    def grid_at(self, x, y) -> sTerrGridInf:
        return self.pTerrGrids[self.grid_idx(x, y)]

    def point_at(self, grid_x, grid_y, grid_lod, x, y):
        grid = self.grid_at(grid_x, grid_y)
        map_grid = grid.GridHeightData[grid_lod]
        point_idx = y * map_grid.NumX + x
        return self.pPointBase[grid_lod][map_grid.pHeightData + point_idx]

    def load_header(self, f):
        MagicNum = read_ctype(f, c_int32)
        if MagicNum != self.MagicNumber:
            raise Exception("Incorrect magic number: %d != %d" % (MagicNum, self.MagicNumber))

        self.NumTexLayers = read_ctype(f, c_int32)
        self.TerrainWidth = read_ctype(f, c_int32)
        self.TerrainDepth = read_ctype(f, c_int32)

        self.GridWidth = ((self.TerrainWidth - 1) / self.NumGridsX) + 1
        self.GridHeight = ((self.TerrainDepth - 1) / self.NumGridsY) + 1

        self.FilterScale = read_ctype(f, c_float)
        self.DimensionScalar.y *= self.FilterScale

        self.NumAllocatedMipXs = read_ctype(f, c_int32)
        self.NumMipLevels = read_ctype(f, c_int32)
        self.NumAllocatedMipEdges = read_ctype(f, c_int32)

        self.TerrGridDataSize = self.NumGrids * sizeof(sTerrGridInf)

        self.StepX = int(self.TerrainWidth / self.NumGridsX)
        self.StepY = int(self.TerrainDepth / self.NumGridsY)

    def load_points(self, f):
        DataSizePerGrid = (self.StepX + 1) * (self.StepY + 1)
        self.pPointBase[0] = read_ctype(f, DataSizePerGrid * self.NumGrids * sHMapPoint)

        MipWidth = (self.TerrainWidth / self.NumGridsX) + 1
        MipHeight = (self.TerrainDepth / self.NumGridsY) + 1
        for MipLevel in range(1, self.NumAllocatedMipXs):
            MipWidth = int(((MipWidth - 1) / 2) + 1)
            MipHeight = int(((MipHeight - 1) / 2) + 1)

            self.pPointBase[MipLevel] = read_ctype(f, MipWidth * MipHeight * self.NumGrids * sHMapPoint)

    def load_edges(self, f):
        MipWidth = int(self.TerrainWidth / self.NumGridsX) + 1
        MipHeight = int(self.TerrainDepth / self.NumGridsY) + 1
        for MipLevel in range(0, self.MAX_MIP_LEVELS):
            if MipLevel + 1 >= self.NumMipLevels:
                break

            NumVertsInEdgeX = MipWidth
            NumVertsInEdgeY = MipHeight

            MemReq = NumVertsInEdgeX + NumVertsInEdgeY
            MemReq *= 2
            MemReq *= self.NumGrids

            self.pEdgeBase[MipLevel] = read_ctype(f, MemReq * c_uint16)

            MipWidth = int((MipWidth - 1) / 2) + 1
            MipHeight = int((MipHeight - 1) / 2) + 1

    def load_terrain_grids_info(self, f):
        self.pTerrGrids = read_ctype(f, self.NumGrids * sTerrGridInf)

        for MipLevel in range(0, self.NumMipLevels):
            for GridIdx in range(0, self.NumGrids):
                pGrid = self.pTerrGrids[GridIdx].GridHeightData[MipLevel]
                pGrid.pHeightData = int(pGrid.pHeightData / sizeof(sHMapPoint))

    def load(self, f):
        self.load_header(f)
        self.load_points(f)
        self.load_edges(f)
        self.load_terrain_grids_info(f)
        return self

    @staticmethod
    def from_file(path):
        f = open(path, "rb")
        res = LR2_Terrain().load(f)
        f.close()
        return res




