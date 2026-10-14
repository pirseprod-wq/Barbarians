# -*- coding: utf-8 -*-
"""
Настоящая растительность вместо заглушек: кусты shrub_02 и папоротник fern_02 (Poly Haven, CC0),
одуванчики на лугу. Черновые кусты и подлесок убираются, черновые деревья остаются до появления моделей деревьев.
Запуск (в уровне L_Village_Night): py "D:/UOT/Barbarians/Scripts/foliage_v2.py"
"""
import sys, importlib, json, os
sys.path.insert(0, "D:/UOT/Barbarians/Scripts")
import lib_build
importlib.reload(lib_build)
from lib_build import *

log = Logger("foliage_v2")
SRC = ROOT + "/SourceAssets/Foliage/PolyHaven"
DST = "/Game/_Game/Art/Environment/Foliage/PolyHaven"
TYPES = "/Game/_Game/Art/Environment/Foliage/Types"
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
PLANTS = ("shrub_02", "fern_02", "dandelion_01")


def import_plant(name):
    folder = DST + "/" + name
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", "%s/%s/%s_2k.gltf" % (SRC, name, name))
    t.set_editor_property("destination_path", folder)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    at.import_asset_tasks([t])
    meshes = []
    for p in sorted(eal.list_assets(folder, recursive=True)):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            meshes.append(a)
    for m in meshes:
        try:
            ns = m.get_editor_property("nanite_settings")
            ns.set_editor_property("enabled", True)
            m.set_editor_property("nanite_settings", ns)
        except Exception:
            pass
        eal.save_loaded_asset(m)
        bb = m.get_bounding_box(); s = bb.max - bb.min
        log("%s/%s: %.0f x %.0f x %.0f см" % (name, m.get_name(), s.x, s.y, s.z))
    return meshes


def ftype(mesh, label, shadow=True, cull=0):
    path = TYPES + "/FT_" + label
    ft = unreal.load_asset(path) if eal.does_asset_exist(path) else at.create_asset(
        "FT_" + label, TYPES, unreal.FoliageType_InstancedStaticMesh, unreal.FoliageType_InstancedStaticMeshFactory())
    ft.set_editor_property("mesh", mesh)
    ft.set_editor_property("cast_shadow", shadow)
    if cull:
        try:
            ft.set_editor_property("cull_distance", unreal.Int32Interval(int(cull * 0.8), int(cull)))
        except Exception:
            pass
    eal.save_loaded_asset(ft)
    return ft


def main():
    placement = json.load(open(ROOT + "/SourceAssets/Foliage/foliage_placement_v2.json"))
    # убрать черновые кусты и подлесок
    for old in ("FT_Bush", "FT_Undergrowth"):
        if eal.does_asset_exist(TYPES + "/" + old):
            unreal.InstancedFoliageActor.remove_all_instances(world, unreal.load_asset(TYPES + "/" + old))
            log("убраны заглушки " + old)
    total = 0
    for plant in PLANTS:
        meshes = import_plant(plant)
        if not meshes:
            log("%s: не импортировался" % plant)
            continue
        for key, items in placement.items():
            pname, idx = key.split(":")
            if pname != plant:
                continue
            mesh = meshes[int(idx) % len(meshes)]
            small = plant != "shrub_02"
            ft = ftype(mesh, "%s_%s" % (plant, idx), shadow=not small, cull=6000 if plant == "dandelion_01" else (12000 if plant == "fern_02" else 0))
            unreal.InstancedFoliageActor.remove_all_instances(world, ft)
            tr = [unreal.Transform(unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw), unreal.Vector(s, s, s))
                  for x, y, z, yaw, s in items]
            for i in range(0, len(tr), 5000):
                unreal.InstancedFoliageActor.add_instances(world, ft, tr[i:i + 5000])
            total += len(tr)
            log("%s: %d шт." % (key, len(tr)))
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("готово, всего %d" % total)


try:
    main()
except Exception as e:
    import traceback
    log("ОШИБКА: %s\n%s" % (e, traceback.format_exc()))
