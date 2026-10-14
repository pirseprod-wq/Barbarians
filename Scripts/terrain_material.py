# -*- coding: utf-8 -*-
"""
Материал земли M_Landscape_Auto - красит ландшафт сам, без ручной покраски:
  луг (sparse_grass) по умолчанию, лесная подстилка (forest_leaves_03) в лесу,
  грязь (brown_mud_03) на улице, во дворах и на дороге, камень (aerial_rocks_02) на крутых склонах.
Где лес/грязь - берётся из маски SourceAssets/Terrain/T_TerrainMask.png (gen_terrain_mask.py).
Поверх - мокрость от дождя, лужи в грязи, крупные пятна цвета против повторяемости.
Запуск: py "D:/UOT/Barbarians/Scripts/terrain_material.py"
"""
import sys, importlib, os
sys.path.insert(0, "D:/UOT/Barbarians/Scripts")
import lib_build
importlib.reload(lib_build)
from lib_build import *

log = Logger("terrain_material")
SRC = ROOT + "/SourceAssets/Terrain/Textures/_layers"
TEX = "/Game/_Game/Textures/Terrain"
MAT = "/Game/_Game/Materials/Terrain"
LAYERS = {   # слой: размер плитки текстуры, см
    "Meadow": 320.0, "Forest": 260.0, "Mud": 380.0, "Rock": 900.0,
}


def imp(path, dest, name):
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", path)
    t.set_editor_property("destination_path", dest)
    t.set_editor_property("destination_name", name)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", False)
    at.import_asset_tasks([t])
    a = unreal.load_asset(dest + "/" + name)
    if a is None:
        raise RuntimeError("не импортировалась " + path)
    return a


def import_layer(layer):
    d = SRC + "/" + layer
    out = {}
    for f in sorted(os.listdir(d)):
        name, ext = os.path.splitext(f)
        kind = name.split("_")[-1]
        tex = imp(d + "/" + f, TEX + "/" + layer, name)
        if kind == "nor":
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            tex.set_editor_property("srgb", False)
            tex.set_editor_property("flip_green_channel", True)       # OpenGL -> DirectX
        elif kind == "arm":
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
            tex.set_editor_property("srgb", False)
        eal.save_loaded_asset(tex)
        out[kind] = tex
    log("%s: %s" % (layer, sorted(out)))
    return out


class MG:
    def __init__(self, mat):
        self.mat = mat
        self.y = 0

    def e(self, cls, x=0, y=None, **props):
        n = mel.create_material_expression(self.mat, cls, x, self.y if y is None else y)
        self.y += 120
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def c(self, a, b, inp="", out=""):
        mel.connect_material_expressions(a, out, b, inp)

    def bin(self, cls, a, b, **props):
        n = self.e(cls, **props)
        if a is not None:
            self.c(a[0] if isinstance(a, tuple) else a, n, "A", a[1] if isinstance(a, tuple) else "")
        if b is not None:
            self.c(b[0] if isinstance(b, tuple) else b, n, "B", b[1] if isinstance(b, tuple) else "")
        return n

    def lerp(self, a, b, alpha):
        n = self.e(unreal.MaterialExpressionLinearInterpolate)
        for pin_name, v in (("A", a), ("B", b), ("Alpha", alpha)):
            if isinstance(v, (int, float)):
                n.set_editor_property("const_" + pin_name.lower(), float(v))
            else:
                self.c(v[0] if isinstance(v, tuple) else v, n, pin_name, v[1] if isinstance(v, tuple) else "")
        return n

    def sample(self, tex, uv, stype):
        n = self.e(unreal.MaterialExpressionTextureSample, texture=tex, sampler_type=stype)
        n.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
        self.c(uv, n, "UVs")
        return n


def build_material(layers, mask_tex):
    path = MAT + "/M_Landscape_Auto"
    mat = unreal.load_asset(path) if eal.does_asset_exist(path) else at.create_asset(
        "M_Landscape_Auto", MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    g = MG(mat)
    wp = g.e(unreal.MaterialExpressionWorldPosition, -2400)
    xy = g.e(unreal.MaterialExpressionComponentMask, -2200, r=True, g=True, b=False, a=False)
    g.c(wp, xy)

    # маска леса/грязи: мировые координаты -> 0..1 по всей карте
    off = g.e(unreal.MaterialExpressionAdd, -2000, const_b=100800.0); g.c(xy, off, "A")
    muv = g.e(unreal.MaterialExpressionDivide, -1800, const_b=201600.0); g.c(off, muv, "A")
    mask = g.sample(mask_tex, muv, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)

    # крутизна склона -> камень
    vn = g.e(unreal.MaterialExpressionVertexNormalWS, -2000)
    nz = g.e(unreal.MaterialExpressionComponentMask, -1800, r=False, g=False, b=True, a=False); g.c(vn, nz)
    slope = g.e(unreal.MaterialExpressionOneMinus, -1600); g.c(nz, slope)
    s1 = g.e(unreal.MaterialExpressionSubtract, -1400, const_b=0.15); g.c(slope, s1, "A")
    s2 = g.e(unreal.MaterialExpressionMultiply, -1200, const_b=9.0); g.c(s1, s2, "A")
    w_rock = g.e(unreal.MaterialExpressionSaturate, -1000); g.c(s2, w_rock)

    # каждый слой: цвет, нормаль, шероховатость, затенение
    L = {}
    for name, tile in LAYERS.items():
        uv = g.e(unreal.MaterialExpressionDivide, -1400, const_b=tile); g.c(xy, uv, "A")
        t = layers[name]
        diff = g.sample(t["diff"], uv, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
        nor = g.sample(t["nor"], uv, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        if "arm" in t:
            arm = g.sample(t["arm"], uv, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
            rough, ao = (arm, "G"), (arm, "R")
        else:
            rough = g.e(unreal.MaterialExpressionConstant, -1000, r=0.75 if name == "Rock" else 0.5)
            ao = g.e(unreal.MaterialExpressionConstant, -1000, r=1.0)
        L[name] = {"c": (diff, "RGB"), "n": (nor, "RGB"), "r": rough, "ao": ao}

    def blend(key):
        v = L["Meadow"][key]
        v = g.lerp(v, L["Forest"][key], (mask, "R"))
        v = g.lerp(v, L["Mud"][key], (mask, "G"))
        v = g.lerp(v, L["Rock"][key], w_rock)
        return v

    color, normal, rough, ao = blend("c"), blend("n"), blend("r"), blend("ao")

    # крупные пятна цвета (против повторяемости)
    macro = g.e(unreal.MaterialExpressionNoise, -600, scale=0.0006, levels=3, output_min=0.0, output_max=1.0)
    var = g.lerp(0.78, 1.12, macro)
    color = g.bin(unreal.MaterialExpressionMultiply, color, var)
    # дождь: всё мокрое и темнее, в грязи лужи
    pn = g.e(unreal.MaterialExpressionNoise, -600, scale=0.004, levels=4, output_min=0.0, output_max=1.0)
    p1 = g.e(unreal.MaterialExpressionSubtract, -400, const_b=0.58); g.c(pn, p1, "A")
    p2 = g.e(unreal.MaterialExpressionMultiply, -300, const_b=8.0); g.c(p1, p2, "A")
    p3 = g.e(unreal.MaterialExpressionSaturate, -200); g.c(p2, p3)
    puddle = g.bin(unreal.MaterialExpressionMultiply, p3, (mask, "G"))
    wet_c = g.e(unreal.MaterialExpressionMultiply, 0, const_b=0.68); g.c(color, wet_c, "A")
    dark = g.e(unreal.MaterialExpressionMultiply, 0, const_b=0.45); g.c(wet_c, dark, "A")
    final_c = g.lerp(wet_c, dark, puddle)
    wet_r = g.e(unreal.MaterialExpressionMultiply, 0, const_b=0.6); g.c(rough, wet_r, "A")
    final_r = g.lerp(wet_r, 0.04, puddle)
    flat = g.e(unreal.MaterialExpressionConstant3Vector, 0, constant=unreal.LinearColor(0, 0, 1, 0))
    final_n = g.lerp(normal, flat, puddle)

    mel.connect_material_property(final_c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(final_n, "", unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(final_r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(ao[0] if isinstance(ao, tuple) else ao, ao[1] if isinstance(ao, tuple) else "",
                                  unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    return mat


def main():
    layers = {name: import_layer(name) for name in LAYERS}
    mask = imp(ROOT + "/SourceAssets/Terrain/T_TerrainMask.png", TEX, "T_TerrainMask")
    mask.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    mask.set_editor_property("srgb", False)
    eal.save_loaded_asset(mask)
    mat = build_material(layers, mask)
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    if descs:
        unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs if "Landscape" in str(d.native_class)])
    for a in actor_sub.get_all_level_actors():
        if isinstance(a, unreal.Landscape):
            a.modify()
            a.set_editor_property("landscape_material", mat)
            log("материал назначен ландшафту")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("готово")


try:
    main()
except Exception as e:
    import traceback
    log("ОШИБКА: %s\n%s" % (e, traceback.format_exc()))
