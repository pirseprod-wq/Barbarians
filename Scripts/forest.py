# -*- coding: utf-8 -*-
"""
Лес вокруг холма (greybox): ели, лиственные деревья, кусты, подлесок через систему Foliage.
Модели: SourceAssets/Foliage/*.obj, расстановка: SourceAssets/Foliage/foliage_placement.json.
Запуск: py "D:/UOT/Barbarians/Scripts/forest.py" (можно повторять: старые экземпляры удаляются).
"""
import json
import unreal

ROOT = "D:/UOT/Barbarians"
SRC = ROOT + "/SourceAssets/Foliage"
MESH_DIR = "/Game/_Game/Art/Environment/Foliage"
TYPE_DIR = "/Game/_Game/Art/Environment/Foliage/Types"
MAT_DIR = "/Game/_Game/Materials/Greybox"
LOG = ROOT + "/Saved/forest_log.txt"
open(LOG, "w").close()

at = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

# ожидаемая высота модели в см и цвета материалов
MESHES = {
    "SM_Tree_Spruce":    {"height": 1680, "leaves": (0.022, 0.045, 0.028), "shadow": True},
    "SM_Tree_Broadleaf": {"height": 1270, "leaves": (0.035, 0.06, 0.025), "shadow": True},
    "SM_Bush":           {"height": 120,  "leaves": (0.03, 0.055, 0.022), "shadow": True},
    "SM_Undergrowth":    {"height": 70,   "leaves": (0.04, 0.065, 0.025), "shadow": False},
}


def log(m):
    unreal.log("[Forest] " + m)
    open(LOG, "a", encoding="utf-8").write(m + "\n")


def mi(name, color, rough):
    path = MAT_DIR + "/" + name
    m = unreal.load_asset(path) if eal.does_asset_exist(path) else at.create_asset(
        name, MAT_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(m, unreal.load_asset(MAT_DIR + "/M_Greybox_Wet"))
    mel.set_material_instance_vector_parameter_value(m, "BaseColor", unreal.LinearColor(color[0], color[1], color[2], 1))
    mel.set_material_instance_scalar_parameter_value(m, "Roughness", rough)
    mel.update_material_instance(m)
    eal.save_loaded_asset(m)
    return m


def import_mesh(name):
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", SRC + "/" + name + ".obj")
    t.set_editor_property("destination_path", MESH_DIR)
    t.set_editor_property("destination_name", name)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", False)
    at.import_asset_tasks([t])
    sm = unreal.load_asset(MESH_DIR + "/" + name)
    if not isinstance(sm, unreal.StaticMesh):
        # импортёр мог положить модель под другим именем
        for p in eal.list_assets(MESH_DIR, recursive=False):
            a = unreal.load_asset(p)
            if isinstance(a, unreal.StaticMesh) and name.lower() in a.get_name().lower():
                sm = a
                break
    if not isinstance(sm, unreal.StaticMesh):
        raise RuntimeError("модель не импортировалась: " + name)
    return sm


def orientation(sm, expected_h):
    """Подбирает поворот и масштаб так, чтобы модель стояла вертикально и имела нужную высоту."""
    box = sm.get_bounding_box()
    mn, mx = box.min, box.max
    ext = [(mx.x - mn.x), (mx.y - mn.y), (mx.z - mn.z)]
    axis = 1   # импортёр OBJ оставляет «верх» по оси Y (проверено на деревьях)
    # где «верх»: дальний от нуля край по главной оси
    lo, hi = [mn.x, mn.y, mn.z][axis], [mx.x, mx.y, mx.z][axis]
    sign = 1 if abs(hi) >= abs(lo) else -1
    up = [0.0, 0.0, 0.0]
    up[axis] = float(sign)
    up = unreal.Vector(*up)
    best = None
    for r in [unreal.Rotator(0, 0, 0), unreal.Rotator(roll=90), unreal.Rotator(roll=-90),
              unreal.Rotator(pitch=90), unreal.Rotator(pitch=-90), unreal.Rotator(roll=180)]:
        v = r.rotate_vector(up) if hasattr(r, "rotate_vector") else unreal.MathLibrary.greater_greater_vector_rotator(up, r)
        if best is None or v.z > best[1]:
            best = (r, v.z)
    unit = 1.0  # OBJ в сантиметрах, импорт 1:1 (проверено)
    log("%s: размеры %s, ось %d, поворот %s, масштаб %.3f" % (sm.get_name(), [round(e) for e in ext], axis, best[0], unit))
    return best[0], unit


def setup_mesh(sm, leaves_mi, bark_mi):
    for i, slot in enumerate(sm.static_materials):
        name = str(slot.get_editor_property("material_slot_name")).lower()
        try:
            name += " " + str(slot.get_editor_property("imported_material_slot_name")).lower()
        except Exception:
            pass
        try:
            mat = slot.get_editor_property("material_interface")
            if mat:
                name += " " + mat.get_name().lower()
        except Exception:
            pass
        sm.set_material(i, bark_mi if "bark" in name else leaves_mi)
    try:
        ns = sm.get_editor_property("nanite_settings")
        ns.set_editor_property("enabled", True)
        sm.set_editor_property("nanite_settings", ns)
    except Exception as e:
        log("nanite: " + str(e))
    eal.save_loaded_asset(sm)


def foliage_type(name, sm, shadow):
    path = TYPE_DIR + "/FT_" + name[3:]
    ft = unreal.load_asset(path) if eal.does_asset_exist(path) else at.create_asset(
        "FT_" + name[3:], TYPE_DIR, unreal.FoliageType_InstancedStaticMesh,
        unreal.FoliageType_InstancedStaticMeshFactory())
    ft.set_editor_property("mesh", sm)
    try:
        ft.set_editor_property("cast_shadow", shadow)
    except Exception:
        pass
    eal.save_loaded_asset(ft)
    return ft


def main():
    for stray in ("Bark", "Leaves"):
        if eal.does_asset_exist(MESH_DIR + "/" + stray):
            eal.delete_asset(MESH_DIR + "/" + stray)
    bark = mi("MI_Bark", (0.075, 0.055, 0.042), 0.5)
    placement = json.load(open(SRC + "/foliage_placement.json"))
    total = 0
    for name, cfg in MESHES.items():
        sm = import_mesh(name)
        leaves = mi("MI_Leaves_" + name[3:], cfg["leaves"], 0.55)
        setup_mesh(sm, leaves, bark)
        base_rot, unit = orientation(sm, cfg["height"])
        ft = foliage_type(name, sm, cfg["shadow"])
        unreal.InstancedFoliageActor.remove_all_instances(world, ft)
        transforms = []
        for x, y, z, yaw, s in placement.get(name, []):
            rot = unreal.MathLibrary.compose_rotators(base_rot, unreal.Rotator(0, 0, yaw))
            k = s * unit
            transforms.append(unreal.Transform(unreal.Vector(x, y, z), rot, unreal.Vector(k, k, k)))
        for i in range(0, len(transforms), 5000):
            unreal.InstancedFoliageActor.add_instances(world, ft, transforms[i:i + 5000])
        log("%s: %d шт." % (name, len(transforms)))
        total += len(transforms)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("готово, всего %d" % total)


try:
    main()
except Exception as e:
    log("ОШИБКА: " + str(e))
    raise
