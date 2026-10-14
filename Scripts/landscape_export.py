# -*- coding: utf-8 -*-
"""Загружает весь ландшафт и выгружает карту высот в SourceAssets/Terrain/height_export.png (+ info json)."""
import json
import unreal

ROOT = "D:/UOT/Barbarians"
OUT_DIR = ROOT + "/SourceAssets/Terrain"
info = {}
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

# 1) загрузить все куски ландшафта (World Partition)
try:
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    guids = [d.guid for d in descs if "Landscape" in str(d.native_class)]
    info["landscape_descs"] = len(guids)
    unreal.WorldPartitionBlueprintLibrary.load_actors(guids)
except Exception as e:
    info["load_error"] = str(e)

lands = [a for a in actor_sub.get_all_level_actors() if isinstance(a, unreal.Landscape)]
proxies = [a for a in actor_sub.get_all_level_actors() if isinstance(a, unreal.LandscapeProxy)]
info["landscapes"] = len(lands)
info["proxies_loaded"] = len(proxies)
land = lands[0]
loc = land.get_actor_location()
sc = land.get_actor_scale3d()
info["location"] = [loc.x, loc.y, loc.z]
info["scale"] = [sc.x, sc.y, sc.z]
for p in ("component_size_quads", "subsection_size_quads", "num_subsections"):
    try:
        info[p] = land.get_editor_property(p)
    except Exception as e:
        info[p] = "?"
# границы по всем кускам
xs, ys = [], []
for p in proxies:
    o, ext = p.get_actor_bounds(False)
    xs += [o.x - ext.x, o.x + ext.x]
    ys += [o.y - ext.y, o.y + ext.y]
info["bounds_x"] = [min(xs), max(xs)]
info["bounds_y"] = [min(ys), max(ys)]
w = int(round((max(xs) - min(xs)) / sc.x)) + 1
h = int(round((max(ys) - min(ys)) / sc.y)) + 1
info["verts"] = [w, h]
try:
    info["edit_layers"] = land.get_editor_property("can_have_layers_content")
except Exception:
    info["edit_layers"] = "?"

rt = unreal.RenderingLibrary.create_render_target2d(world, w, h, unreal.TextureRenderTargetFormat.RTF_RGBA8)
ok = land.landscape_export_heightmap_to_render_target(rt, True, True)
info["export_ok"] = ok
unreal.RenderingLibrary.export_render_target(world, rt, OUT_DIR, "height_export.png")
json.dump(info, open(OUT_DIR + "/landscape_info.json", "w"), indent=1)
unreal.log("[Terrain] export done " + json.dumps(info))
