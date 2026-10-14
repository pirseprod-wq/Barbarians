# -*- coding: utf-8 -*-
"""Импорт моделей персонажей из SourceAssets/Characters/<Имя>/<Имя>.fbx в _Game/Art/Characters/<Имя>.
Пока без скелета (модели из Tripo пришли статичными) - импорт как статичные модели + витрина для осмотра."""
import sys, importlib, os
sys.path.insert(0, "D:/UOT/Barbarians/Scripts")
import lib_build
importlib.reload(lib_build)
from lib_build import *

log = Logger("import_characters")
SRC = ROOT + "/SourceAssets/Characters"
DST = "/Game/_Game/Art/Characters"
PREVIEW = "Characters_Preview"


def main():
    for a in actor_sub.get_all_level_actors():
        if str(a.get_folder_path()) == PREVIEW:
            actor_sub.destroy_actor(a)
    ps = [a for a in actor_sub.get_all_level_actors() if a.get_actor_label() == "PS_Village"]
    base = ps[0].get_actor_location() if ps else unreal.Vector(0, 0, 0)
    i = 0
    for name in sorted(os.listdir(SRC)):
        fbx = os.path.join(SRC, name, name + ".fbx").replace("\\", "/")
        if not os.path.isfile(fbx):
            continue
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", fbx)
        t.set_editor_property("destination_path", DST + "/" + name)
        t.set_editor_property("automated", True)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("save", True)
        at.import_asset_tasks([t])
        meshes = [unreal.load_asset(p) for p in eal.list_assets(DST + "/" + name, recursive=True)]
        meshes = [m for m in meshes if isinstance(m, (unreal.StaticMesh, unreal.SkeletalMesh))]
        if not meshes:
            log("%s: модель не импортировалась" % name)
            continue
        m = meshes[0]
        if isinstance(m, unreal.StaticMesh):
            bb = m.get_bounding_box()
            size = bb.max - bb.min
            log("%s: %s %s, размеры %.0f x %.0f x %.0f см, низ z=%.0f" % (name, type(m).__name__, m.get_name(), size.x, size.y, size.z, bb.min.z))
            a = actor_sub.spawn_actor_from_object(m, base + unreal.Vector(400, -300 + i * 150, 0), unreal.Rotator(0, 0, 180))
        else:
            log("%s: %s %s (со скелетом)" % (name, type(m).__name__, m.get_name()))
            a = actor_sub.spawn_actor_from_object(m, base + unreal.Vector(400, -300 + i * 150, 0), unreal.Rotator(0, 0, 180))
        a.set_actor_label("Preview_" + name)
        a.set_folder_path(PREVIEW)
        i += 1
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("готово")


try:
    main()
except Exception as e:
    import traceback
    log("ОШИБКА: %s\n%s" % (e, traceback.format_exc()))
