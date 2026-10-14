# -*- coding: utf-8 -*-
"""Шаг 1 из 2: импорт карты высот холма как текстуры и материала для перерисовки в render target."""
import unreal
ROOT = "D:/UOT/Barbarians"
at = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
LOG = ROOT + "/Saved/terrain_log.txt"
def log(m):
    unreal.log("[Terrain] " + m)
    open(LOG, "a", encoding="utf-8").write(m + "\n")
open(LOG, "w").close()

t = unreal.AssetImportTask()
t.set_editor_property("filename", ROOT + "/SourceAssets/Terrain/T_Height_RG.png")
t.set_editor_property("destination_path", "/Game/_Game/Textures/Terrain")
t.set_editor_property("destination_name", "T_Height_RG")
t.set_editor_property("automated", True)
t.set_editor_property("replace_existing", True)
t.set_editor_property("save", False)
at.import_asset_tasks([t])
tex = unreal.load_asset("/Game/_Game/Textures/Terrain/T_Height_RG")
tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_VECTOR_DISPLACEMENTMAP)
tex.set_editor_property("srgb", False)
tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
tex.set_editor_property("filter", unreal.TextureFilter.TF_NEAREST)
tex.set_editor_property("never_stream", True)
eal.save_loaded_asset(tex)
log("texture %dx%d" % (tex.blueprint_get_size_x(), tex.blueprint_get_size_y()))

path = "/Game/_Game/Materials/Tools/M_HeightCopy"
mat = unreal.load_asset(path) if eal.does_asset_exist(path) else at.create_asset(
    "M_HeightCopy", "/Game/_Game/Materials/Tools", unreal.Material, unreal.MaterialFactoryNew())
mel.delete_all_material_expressions(mat)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -400, 0)
ts.set_editor_property("texture", tex)
ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
mel.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(mat)
eal.save_loaded_asset(mat)
log("prepare done")
