# -*- coding: utf-8 -*-
"""Шаг 2 из 2: рисует карту высот в render target, сверяет контрольные точки и записывает в ландшафт."""
import json
import unreal
ROOT = "D:/UOT/Barbarians"
LOG = ROOT + "/Saved/terrain_log.txt"
def log(m):
    unreal.log("[Terrain] " + m)
    open(LOG, "a", encoding="utf-8").write(m + "\n")

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs if "Landscape" in str(d.native_class)])
land = [a for a in actor_sub.get_all_level_actors() if isinstance(a, unreal.Landscape)][0]

mat = unreal.load_asset("/Game/_Game/Materials/Tools/M_HeightCopy")
rt = unreal.RenderingLibrary.create_render_target2d(world, 2017, 2017, unreal.TextureRenderTargetFormat.RTF_RGBA8)
unreal.RenderingLibrary.draw_material_to_render_target(world, rt, mat)

bad = 0
for i, j, r, g in json.load(open(ROOT + "/SourceAssets/Terrain/height_checks.json")):
    c = unreal.RenderingLibrary.read_render_target_raw_pixel(world, rt, i, j)
    scale = 1 if max(c.r, c.g) > 1.5 else 255
    rr, gg = int(round(c.r * scale)), int(round(c.g * scale))
    if (rr, gg) != (r, g):
        bad += 1
    log("check %d,%d expect %d,%d got %d,%d" % (i, j, r, g, rr, gg))
if bad:
    log("ОТМЕНА: render target не совпал с картой высот, ландшафт не тронут")
else:
    ok = land.landscape_import_heightmap_from_render_target(rt, True)
    log("import ok=%s" % ok)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("saved")
