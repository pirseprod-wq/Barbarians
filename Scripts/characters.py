# -*- coding: utf-8 -*-
"""
Персонажи из Tripo (Content/TripoModels/<Имя>): IK Rig, ретаргетер с манекена и перенос анимаций.
Для каждого персонажа создаётся _Game/Art/Characters/<Имя>/:
  IK_<Имя>, RTG_Manny_to_<Имя>, анимации <Анимация>_<Имя> (стойка, ходьба, бег).
Список - в Design/characters.json. Запуск: py "D:/UOT/Barbarians/Scripts/characters.py"
"""
import sys, importlib, json
sys.path.insert(0, "D:/UOT/Barbarians/Scripts")
import lib_build
importlib.reload(lib_build)
from lib_build import *

log = Logger("characters")
OUT = "/Game/_Game/Art/Characters"
MANNY = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
ANIMS = ["/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle"]
for sub, key in (("Walk", "Walk_Fwd"), ("Jog", "Jog_Fwd")):
    d = "/Game/Characters/Mannequins/Anims/Unarmed/" + sub
    if eal.does_directory_exist(d):
        ANIMS += [p.split(".")[0] for p in eal.list_assets(d, recursive=False)
                  if key in p and "Left" not in p and "Right" not in p][:1]


def get_or_new(path, name, cls, factory):
    full = path + "/" + name
    if eal.does_asset_exist(full):
        eal.delete_asset(full)
    return at.create_asset(name, path, cls, factory)


def ik_rig(mesh, path, name):
    rig = get_or_new(path, name, unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
    c = unreal.IKRigController.get_controller(rig)
    ok = c.set_skeletal_mesh(mesh)
    auto = c.apply_auto_generated_retarget_definition()
    try:
        c.apply_auto_fbik()
    except Exception:
        pass
    log("%s: меш=%s, шаблон скелета распознан=%s, цепочек=%d" % (name, ok, auto, len(c.get_retarget_chains())))
    eal.save_loaded_asset(rig)
    return rig


def main():
    cfg = json.load(open(ROOT + "/Design/characters.json", encoding="utf-8"))
    src_mesh = unreal.load_asset(MANNY)
    src_rig = ik_rig(src_mesh, OUT + "/_Shared", "IK_Manny")
    result = {}
    for name, info in cfg["characters"].items():
        mesh_path = info.get("mesh")
        if not mesh_path or not eal.does_asset_exist(mesh_path):
            log("%s: модели нет (%s) - пропускаю" % (name, mesh_path))
            continue
        mesh = unreal.load_asset(mesh_path)
        folder = OUT + "/" + name
        tgt_rig = ik_rig(mesh, folder, "IK_" + name)
        rtg = get_or_new(folder, "RTG_Manny_to_" + name, unreal.IKRetargeter, unreal.IKRetargetFactory())
        rc = unreal.IKRetargeterController.get_controller(rtg)
        rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig)
        rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
        try:
            if rc.get_num_retarget_ops() == 0:
                rc.add_default_ops()
            rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig)
            rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
        except Exception as e:
            log("ops: %s" % e)
        rc.auto_map_chains(unreal.AutoMapChainType.EXACT, True)
        try:   # Т-поза Tripo -> под А-позу манекена
            rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
        except Exception as e:
            log("выравнивание позы: %s" % e)
        eal.save_loaded_asset(rtg)
        assets = [eal.find_asset_data(a) for a in ANIMS]
        made = unreal.IKRetargetBatchOperation.duplicate_and_retarget(
            assets, src_mesh, mesh, rtg, "", "", "", "_" + name, folder, False, False, True)
        names = [str(a.asset_name) for a in made]
        log("%s: анимации %s" % (name, names))
        result[name] = {"mesh": mesh_path, "anims": ["%s/%s" % (folder, n) for n in names]}
    json.dump(result, open(ROOT + "/Saved/characters_built.json", "w"), ensure_ascii=False, indent=1)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
    log("готово")


try:
    main()
except Exception as e:
    import traceback
    log("ОШИБКА: %s\n%s" % (e, traceback.format_exc()))
