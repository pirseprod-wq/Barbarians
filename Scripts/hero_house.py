# -*- coding: utf-8 -*-
"""
Дом друга: длинный дом у въезда в село превращается в дом, куда можно войти.
Внутри: очаг с тлеющими углями, лежанки, спящая семья, перегородка с хлевом,
друг-сорвиголова, который не спит и ждёт игрока (BP_Friend: подойти и нажимать E).
Запуск: py "D:/UOT/Barbarians/Scripts/hero_house.py" (можно повторять).
"""
import math
import unreal

ROOT = "D:/UOT/Barbarians"
LOG = ROOT + "/Saved/hero_house_log.txt"
open(LOG, "w").close()
FOLDER = "Village_Greybox/HeroHouse"
SURF = "/Game/_Game/Materials/Greybox"
NPC_DIR = "/Game/_Game/Blueprints/Characters"

at = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
B = unreal.BlueprintEditorLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")
MANNY = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
QUINN = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
IDLE = unreal.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle")
LYING = unreal.load_asset("/Game/Characters/Mannequins/Anims/Death/MM_Death_Back_01")
U = 100.0

# ---------------------------------------------------------------- текст диалога (меняйте здесь)
FRIEND_LINES = [
    "Друг (шёпотом): Тише ты! Отец только уснул... Я уж думал, ты не придёшь.",
    "Друг: Всё собрал: хлеб, сыр, огниво. И отцовский нож взял - вернём, когда героями станем.",
    "Друг: Говорят, князь собирает дружину у брода за лесом. Берёт только тех, кто себя покажет.",
    "Друг: Уходим до рассвета, пока мать не проснулась. Через лес, по старой дороге на запад.",
    "Друг: Ну что, сорвиголова, - идём за славой?",
]
QUEST_TEXT = "НОВОЕ ЗАДАНИЕ: Путь в дружину. Выбраться из села до рассвета и дойти до брода за лесом, где князь собирает дружину."
AFTER_TEXT = "Друг: Чего стоишь? Идём, пока не рассвело!"


def log(m):
    unreal.log("[HeroHouse] " + m)
    open(LOG, "a", encoding="utf-8").write(m + "\n")


# ---------------------------------------------------------------- материалы
def mi(name, color, rough=0.6):
    path = SURF + "/" + name
    m = unreal.load_asset(path) if eal.does_asset_exist(path) else at.create_asset(
        name, SURF, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(m, unreal.load_asset(SURF + "/M_Greybox_Wet"))
    mel.set_material_instance_vector_parameter_value(m, "BaseColor", unreal.LinearColor(color[0], color[1], color[2], 1))
    mel.set_material_instance_scalar_parameter_value(m, "Roughness", rough)
    mel.update_material_instance(m)
    eal.save_loaded_asset(m)
    return m


def emissive_material():
    path = SURF + "/M_Emissive"
    mat = unreal.load_asset(path) if eal.does_asset_exist(path) else at.create_asset(
        "M_Emissive", SURF, unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    col = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -500, 0)
    col.set_editor_property("parameter_name", "Color")
    col.set_editor_property("default_value", unreal.LinearColor(1, 0.3, 0.05, 1))
    k = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -500, 200)
    k.set_editor_property("parameter_name", "Strength")
    k.set_editor_property("default_value", 6.0)
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -250, 100)
    mel.connect_material_expressions(col, "", mul, "A")
    mel.connect_material_expressions(k, "", mul, "B")
    mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    blk = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -250, -100)
    blk.set_editor_property("constant", unreal.LinearColor(0.02, 0.015, 0.01, 1))
    mel.connect_material_property(blk, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    path = SURF + "/MI_Embers"
    m = unreal.load_asset(path) if eal.does_asset_exist(path) else at.create_asset(
        "MI_Embers", SURF, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(m, mat)
    mel.set_material_instance_scalar_parameter_value(m, "Strength", 6.0)
    mel.update_material_instance(m)
    eal.save_loaded_asset(m)
    return m


# ---------------------------------------------------------------- геометрия
class House:
    def __init__(self, cx, cy, gz, yaw, L, W, H):
        self.cx, self.cy, self.gz, self.yaw, self.L, self.W, self.H = cx, cy, gz, yaw, L, W, H

    def w(self, lx, ly, lz):
        """локальные метры -> мировые см"""
        r = math.radians(self.yaw)
        x, y = lx * U, ly * U
        return unreal.Vector(self.cx + x * math.cos(r) - y * math.sin(r),
                             self.cy + x * math.sin(r) + y * math.cos(r),
                             self.gz + lz * U)

    def rot(self, extra_yaw=0.0, roll=0.0, pitch=0.0):
        return unreal.Rotator(roll=roll, pitch=pitch, yaw=self.yaw + extra_yaw)


def box(h, label, lx, ly, lz, sx, sy, sz, mat, extra_yaw=0.0, roll=0.0, mesh=None):
    """коробка: центр в локальных метрах, размеры в метрах"""
    a = actor_sub.spawn_actor_from_object(mesh or CUBE, h.w(lx, ly, lz), h.rot(extra_yaw, roll))
    a.set_actor_scale3d(unreal.Vector(sx, sy, sz))
    a.set_actor_label(label)
    a.set_folder_path(FOLDER)
    if mat:
        a.static_mesh_component.set_material(0, mat)
    return a


def load_village_actors():
    """World Partition: подгрузить объекты села, даже если камера далеко."""
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    if isinstance(descs, tuple):
        descs = [d for d in descs if isinstance(d, (list, unreal.Array))][0] if descs else []
    if not descs:
        log("список объектов World Partition недоступен - беру то, что уже загружено")
        return
    guids = [d.guid for d in descs
             if not any(k in str(d.native_class) for k in ("Landscape", "Foliage", "HLOD"))]
    unreal.WorldPartitionBlueprintLibrary.load_actors(guids)
    log("подгружено объектов: %d" % len(guids))


STATE = ROOT + "/Saved/hero_house_target.json"


def find_target():
    """Дом друга выбирается один раз (ближайший длинный дом к въезду) и запоминается,
    чтобы повторный запуск не превращал в дом друга соседний дом."""
    import json, os
    load_village_actors()
    labels = {a.get_actor_label(): a for a in actor_sub.get_all_level_actors()}
    if os.path.exists(STATE):
        st = json.load(open(STATE))
        walls = labels.get(st["name"] + "_Walls")
        if walls is None:
            log("беру сохранённые размеры дома " + st["name"])
            return st["name"], House(*st["house"])
    else:
        ps = labels.get("PS_Village")
        p = ps.get_actor_location() if ps else unreal.Vector(0, 0, 0)
        best = None
        for lab, a in labels.items():
            if lab.startswith("Longhouse_") and lab.endswith("_Walls"):
                d = (a.get_actor_location() - p).length()
                if best is None or d < best[0]:
                    best = (d, lab[:-len("_Walls")])
        if not best:
            raise RuntimeError("длинный дом не найден - сначала запустите build_village_night.py")
        st = {"name": best[1]}
        walls = labels[best[1] + "_Walls"]
    name = st["name"]
    s = walls.get_actor_scale3d()
    loc = walls.get_actor_location()
    L, W, H = s.x, s.y, s.z - 0.3
    gz = loc.z - (H * U - 30) / 2
    yaw = walls.get_actor_rotation().yaw
    st["house"] = [loc.x, loc.y, gz, yaw, L, W, H]
    json.dump(st, open(STATE, "w"))
    return name, House(*st["house"])


def clear(name):
    n = 0
    for a in actor_sub.get_all_level_actors():
        f = str(a.get_folder_path())
        if f == "Village_Greybox/Houses/" + name or f == FOLDER or a.get_actor_label() == "NPC_Friend":
            actor_sub.destroy_actor(a)
            n += 1
    log("убрано старых объектов: %d" % n)


def build_shell(h, m):
    L, W, H = h.L, h.W, h.H
    T = 0.25
    wall_h = H + 0.3
    zc = (H - 0.3) / 2
    door_x, door_w = -L / 4, 1.3
    door_h = min(1.95, H - 0.05)
    # пол из утоптанной земли
    box(h, "Floor", 0, 0, 0.03, L - 0.3, W - 0.3, 0.1, m["floor"])
    # задняя стена (+Y) и торцы
    box(h, "Wall_Back", 0, W / 2 - T / 2, zc, L, T, wall_h, m["clay"])
    for s, tag in ((1, "E"), (-1, "W")):
        box(h, "Wall_End" + tag, s * (L / 2 - T / 2), 0, zc, T, W, wall_h, m["clay"])
    # передняя стена (-Y) с дверным проёмом
    left_len = (door_x - door_w / 2) - (-L / 2)
    right_len = L / 2 - (door_x + door_w / 2)
    box(h, "Wall_Front_A", -L / 2 + left_len / 2, -W / 2 + T / 2, zc, left_len, T, wall_h, m["clay"])
    box(h, "Wall_Front_B", L / 2 - right_len / 2, -W / 2 + T / 2, zc, right_len, T, wall_h, m["clay"])
    lintel = H - door_h
    if lintel > 0.02:
        box(h, "Wall_Front_Lintel", door_x, -W / 2 + T / 2, door_h + lintel / 2, door_w, T, lintel, m["clay"])
    # косяки и распахнутая дверь (полотно повёрнуто внутрь)
    for s in (1, -1):
        box(h, "DoorPost", door_x + s * door_w / 2, -W / 2 + T / 2, door_h / 2, 0.14, T + 0.06, door_h, m["wood"])
    box(h, "DoorLeaf", door_x - door_w / 2 + 0.05, -W / 2 + T + door_w / 2 - 0.05, door_h / 2 - 0.02,
        0.06, door_w - 0.1, door_h - 0.08, m["wood"])
    # фронтоны ступеньками (внутри пусто, не как у сплошных домов)
    rise = W / 2 * math.tan(math.radians(45))
    steps = 7
    for s, tag in ((1, "E"), (-1, "W")):
        for i in range(steps):
            frac0 = i / steps
            width = W * (1 - frac0) - 0.05
            box(h, "Gable%s_%d" % (tag, i), s * (L / 2 - T / 2), 0, H + rise * (i + 0.5) / steps,
                T, width, rise / steps + 0.01, m["clay"])
    # крыша
    a = math.radians(45)
    eave, gable_over = 0.6, 0.5
    half_span = W / 2 + eave
    slope_len = half_span / math.cos(a) + 0.15
    ridge = H + (W / 2) * math.tan(a)
    low = ridge - half_span * math.tan(a)
    zc_roof = (ridge + low) / 2 + 0.12
    for s in (1, -1):
        r = box(h, "Roof" + ("L" if s > 0 else "R"), 0, s * half_span / 2, zc_roof,
                L + 2 * gable_over, slope_len, 0.25, m["thatch"], roll=-s * 45)
        tip = r.get_actor_transform().transform_location(unreal.Vector(0, s * 50, 0))
        if tip.z > r.get_actor_location().z:
            r.set_actor_rotation(h.rot(roll=s * 45), False)
    # конёк (балка) и опорные столбы
    box(h, "RidgeBeam", 0, 0, ridge - 0.25, L, 0.2, 0.2, m["wood"])
    for x in (-L / 3, 0, L / 3):
        box(h, "Post", x, 0, (ridge - 0.25) / 2, 0.2, 0.2, ridge - 0.25, m["wood"])
    return door_x, door_w


def build_interior(h, m, embers, door_x):
    L, W, H = h.L, h.W, h.H
    T = 0.25
    living_end = L / 6          # жилая часть: от западного торца до перегородки
    # перегородка жилья и хлева (плетень с проходом)
    gap = 1.2
    seg = (W - 2 * T - gap) / 2
    for s in (1, -1):
        box(h, "Partition", living_end, s * (gap / 2 + seg / 2), 0.8, 0.1, seg, 1.6, m["wood"])
    # хлев: солома, ясли
    box(h, "Byre_Straw", (living_end + L / 2) / 2, 0, 0.1, L / 2 - living_end - 0.5, W - 0.8, 0.12, m["hay"])
    box(h, "Byre_Trough", L / 2 - 0.8, 0, 0.35, 0.6, W - 1.4, 0.5, m["wood"])
    # очаг посреди жилой части: кольцо камней, угли, свет
    hx = (-L / 2 + living_end) / 2 + 0.6
    for i in range(10):
        ang = i / 10 * 2 * math.pi
        box(h, "HearthStone", hx + 0.65 * math.cos(ang), 0.2 + 0.65 * math.sin(ang), 0.1,
            0.3, 0.25, 0.2, m["stone"], extra_yaw=math.degrees(ang))
    e = actor_sub.spawn_actor_from_object(CYL, h.w(hx, 0.2, 0.05), h.rot())
    e.set_actor_scale3d(unreal.Vector(1.0, 1.0, 0.08))
    e.set_actor_label("Hearth_Embers")
    e.set_folder_path(FOLDER)
    e.static_mesh_component.set_material(0, embers)
    e.static_mesh_component.set_editor_property("cast_shadow", False)
    for i in range(4):
        box(h, "Hearth_Log", hx, 0.2, 0.1, 0.9, 0.12, 0.12, m["wood"], extra_yaw=i * 45)
    light = actor_sub.spawn_actor_from_class(unreal.PointLight, h.w(hx, 0.2, 0.5), h.rot())
    light.set_actor_label("Hearth_Light")
    light.set_folder_path(FOLDER)
    lc = light.point_light_component
    try:
        lc.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    except Exception:
        pass
    lc.set_editor_property("intensity", 6.0)
    lc.set_light_color(unreal.LinearColor(1.0, 0.45, 0.15, 1.0))
    lc.set_editor_property("attenuation_radius", 900.0)
    lc.set_editor_property("source_radius", 25.0)
    # лежанки вдоль задней стены и у западного торца
    bench_y = W / 2 - T - 0.85
    bench_len = living_end - (-L / 2) - 0.6
    bench_cx = -L / 2 + 0.3 + bench_len / 2
    box(h, "SleepBench", bench_cx, bench_y, 0.22, bench_len, 1.6, 0.45, m["wood"])
    box(h, "SleepBench_Straw", bench_cx, bench_y, 0.5, bench_len - 0.1, 1.5, 0.12, m["hay"])
    box(h, "UlfBench", -L / 2 + T + 0.55, -0.4, 0.18, 0.95, 2.1, 0.36, m["wood"])
    box(h, "UlfBench_Straw", -L / 2 + T + 0.55, -0.4, 0.4, 0.9, 2.0, 0.1, m["hay"])
    # стол, лавка, горшки у передней стены
    tx = hx + 1.9
    box(h, "Table", tx, -W / 2 + T + 0.6, 0.72, 1.4, 0.7, 0.08, m["wood"])
    for sx in (-0.55, 0.55):
        box(h, "TableLeg", tx + sx, -W / 2 + T + 0.6, 0.35, 0.08, 0.5, 0.7, m["wood"])
    box(h, "Bench", tx, -W / 2 + T + 1.2, 0.22, 1.4, 0.3, 0.44, m["wood"])
    for i, sx in enumerate((-0.4, 0.1, 0.45)):
        p = actor_sub.spawn_actor_from_object(CYL, h.w(tx + sx, -W / 2 + T + 0.6, 0.86), h.rot())
        p.set_actor_scale3d(unreal.Vector(0.22 - i * 0.03, 0.22 - i * 0.03, 0.22))
        p.set_actor_label("Pot")
        p.set_folder_path(FOLDER)
        p.static_mesh_component.set_material(0, m["clay"])
    return hx, bench_cx, bench_y


def sleeper(h, label, mesh, lx, ly, lz, along_x, scale, m):
    """Спящий: поза «стоя спокойно» (MM_Idle), повёрнутая лицом вверх и уложенная на лежанку.
    (lx, ly, lz) - середина тела; along_x: тело вдоль оси X дома (иначе вдоль Y)."""
    a = actor_sub.spawn_actor_from_object(mesh, h.w(lx, ly, lz), h.rot())
    a.set_actor_label(label)
    a.set_folder_path(FOLDER)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    c = a.skeletal_mesh_component
    c.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    data = unreal.SingleAnimationPlayData()
    data.set_editor_property("anim_to_play", IDLE)
    data.set_editor_property("saved_looping", True)
    data.set_editor_property("saved_playing", False)
    data.set_editor_property("saved_position", 0.0)
    data.set_editor_property("saved_play_rate", 0.0)
    c.set_editor_property("animation_data", data)
    # подбираем поворот: тело горизонтально вдоль нужной оси, лицо (локальная +Y модели) вверх
    want_axis = h.w(1, 0, 0) - h.w(0, 0, 0) if along_x else h.w(0, 1, 0) - h.w(0, 0, 0)
    best = None
    for roll in (90, -90):
        for pitch in (90, -90, 0):
            for yaw_add in (0, 90, 180, 270):
                r = unreal.MathLibrary.compose_rotators(unreal.Rotator(roll=roll, pitch=0, yaw=0),
                                                       unreal.Rotator(roll=0, pitch=0, yaw=h.yaw + yaw_add))
                if pitch:
                    continue
                a.set_actor_rotation(r, False)
                t = a.get_actor_transform()
                o = t.transform_location(unreal.Vector(0, 0, 0))
                head = t.transform_location(unreal.Vector(0, 0, 170))
                face = t.transform_location(unreal.Vector(0, 100, 0))
                body = head - o
                flat = abs(body.z) < 20
                up = face.z - o.z
                along = abs(body.x * want_axis.x + body.y * want_axis.y) / (body.length() * want_axis.length() + 1e-6)
                toward = (body.x * want_axis.x + body.y * want_axis.y) > 0   # голова к стене (+Y) / к +X
                score = (flat, up > 50, round(along, 2), toward)
                if best is None or score > best[0]:
                    best = (score, r)
    a.set_actor_rotation(best[1], False)
    t = a.get_actor_transform()
    mid = t.transform_location(unreal.Vector(0, 0, 90))
    target = h.w(lx, ly, lz)
    a.set_actor_location(a.get_actor_location() + (target - mid), False, False)
    return a


def build_family(h, m, bench_cx, bench_y):
    """Отец и мать на большой лежанке, младший брат рядом с матерью, Ульф - на своей лавке у торца."""
    top = 0.56
    sleeper(h, "Family_Father", MANNY, bench_cx - 1.2, bench_y, top + 0.12, False, 1.0, m)
    sleeper(h, "Family_Mother", QUINN, bench_cx + 0.1, bench_y, top + 0.12, False, 0.95, m)
    sleeper(h, "Family_Child", QUINN, bench_cx + 1.0, bench_y, top + 0.1, False, 0.68, m)
    box(h, "Blanket_Father", bench_cx - 1.2, bench_y - 0.25, top + 0.2, 0.75, 1.25, 0.2, m["wool"])
    box(h, "Blanket_Mother", bench_cx + 0.1, bench_y - 0.25, top + 0.2, 0.7, 1.2, 0.2, m["wool"])
    box(h, "Blanket_Child", bench_cx + 1.0, bench_y - 0.15, top + 0.18, 0.55, 0.85, 0.16, m["wool"])
    ulf = sleeper(h, "Ulf_Sleeping", MANNY, -h.L / 2 + 0.25 + 0.55, -0.4, 0.55, False, 1.0, m)
    box(h, "Blanket_Ulf", -h.L / 2 + 0.25 + 0.55, -0.65, 0.62, 0.7, 1.25, 0.18, m["wool"])
    return ulf


# ---------------------------------------------------------------- BP_Friend: сон -> разговор -> выбор -> задание
def add_component(bp, cls, name, parent=None):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    if parent is None:
        parent = handles[0]
        for hd in handles:
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(
                unreal.SubobjectDataBlueprintFunctionLibrary.get_data(hd))
            if isinstance(obj, unreal.SceneComponent):
                parent = hd
                break
    res = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent, new_class=cls, blueprint_context=bp))
    hd = res[0] if isinstance(res, tuple) else res
    sds.rename_subobject(hd, unreal.Text(name))
    return unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(hd))


def pin(node, name, out=False):
    p = B.find_output_pin(node, name) if out else B.find_input_pin(node, name)
    if not p.is_valid():
        names = [str(q.get_pin_name()) for q in B.list_all_pins(node)]
        raise RuntimeError("нет пина %s у %s (есть: %s)" % (name, node.get_name(), names))
    return p


def link(a, b):
    if not a.try_create_connection(b):
        raise RuntimeError("не соединились %s -> %s" % (a.get_pin_name(), b.get_pin_name()))


S = "/Script/Engine.KismetStringLibrary."
M = "/Script/Engine.KismetMathLibrary."
C_PLAYER, C_NPC, C_NARR, C_CHOICE, C_QUEST = (0.6, 0.85, 1.0), (0.95, 0.85, 0.65), (0.6, 0.6, 0.6), (1.0, 1.0, 0.4), (1.0, 0.75, 0.2)


class G:
    """Генератор графа: каждая функция возвращает узлы/пины, позиции раскладываются по рядам."""
    def __init__(self, bp):
        self.bp = bp
        self.ed = unreal.BlueprintGraphEditor.get_graph_editor(B.find_event_graph(bp))
        self.y = 0
        self.x = 0
        self.avail = None

    def pos(self, n, dx=0, dy=0):
        B.set_node_pos(n, unreal.IntPoint(self.x + dx, self.y + dy))
        self.x += 280
        return n

    def call(self, path):
        n = self.ed.add_call_function_node(path)
        if n is None:
            raise RuntimeError("нет функции " + path)
        return self.pos(n)

    def named(self, name, ctx=None):
        n = self.ed.create_node_from_name(name, unreal.Vector2D(self.x, self.y), ctx or [])
        if n is None:
            raise RuntimeError("нет узла " + name)
        self.x += 280
        return n

    def find_name(self, suffix):
        if self.avail is None:
            self.avail = list(self.ed.list_available_nodes([]))
        for n in self.avail:
            if n.lower() == suffix.lower():
                return n
        for n in self.avail:
            if n.lower().endswith(suffix.lower()):
                return n
        raise RuntimeError("не найден узел *" + suffix)

    def get(self, var):
        n = self.pos(self.ed.add_get_member_variable_node(var), dy=160)
        return pin(n, var, True)

    def setv(self, var, value=None, src=None):
        n = self.pos(self.ed.add_set_member_variable_node(var))
        if value is not None:
            pin(n, var).set_pin_value(value)
        if src is not None:
            link(src, pin(n, var))
        return n

    def branch(self, cond):
        n = self.pos(self.ed.add_branch_node())
        link(cond, B.find_condition_pin(n))
        return n

    def int_eq(self, var, value):
        n = self.call(M + "EqualEqual_IntInt")
        link(self.get(var), pin(n, "A"))
        pin(n, "B").set_pin_value(str(value))
        return pin(n, "ReturnValue", True)

    def concat(self, *parts):
        """parts: пины-строки или литералы"""
        cur = None
        for p in parts:
            n = self.call(S + "Concat_StrStr")
            if cur is None:
                if isinstance(p, str):
                    pin(n, "A").set_pin_value(p)
                else:
                    link(p, pin(n, "A"))
                cur = n
                continue
            link(pin(cur, "ReturnValue", True), pin(n, "A"))
            if isinstance(p, str):
                pin(n, "B").set_pin_value(p)
            else:
                link(p, pin(n, "B"))
            cur = n
        return pin(cur, "ReturnValue", True)

    def prints(self, text, key, color, duration):
        n = self.call("/Script/Engine.KismetSystemLibrary.PrintString")
        pin(n, "Key").set_pin_value(key)
        pin(n, "Duration").set_pin_value(str(duration))
        pin(n, "TextColor").set_pin_value("(R=%f,G=%f,B=%f,A=1.000000)" % color)
        pin(n, "bPrintToLog").set_pin_value("false")
        if isinstance(text, str):
            pin(n, "InString").set_pin_value(text)
        else:
            link(text, pin(n, "InString"))
        return n

    def row(self):
        self.y += 700
        self.x = 0


def chain(nodes):
    """соединить exec подряд; элемент может быть узлом или списком выходных exec-пинов"""
    prev_outs = None
    for n in nodes:
        if prev_outs is not None:
            for o in prev_outs:
                link(o, B.find_execute_pin(n))
        prev_outs = [B.find_then_pin(n)] if not isinstance(n, list) else n
    return prev_outs


def show_entry(g, entry_pin):
    """'Кто|Текст' -> печать с цветом по говорящему. Возвращает (вход, [выходы])."""
    sp = g.call(S + "Split")
    link(entry_pin, pin(sp, "SourceString"))
    pin(sp, "InStr").set_pin_value("|")
    left, right = pin(sp, "LeftS", True), pin(sp, "RightS", True)
    is_p = g.call(S + "EqualEqual_StrStr")
    link(left, pin(is_p, "A"))
    link(g.get("PlayerName"), pin(is_p, "B"))
    br_p = g.branch(pin(is_p, "ReturnValue", True))
    p_player = g.prints(g.concat(left, ": ", right), "Dlg", C_PLAYER, 15.0)
    link(B.find_then_pin(br_p), B.find_execute_pin(p_player))
    is_n = g.call(S + "EqualEqual_StrStr")
    link(left, pin(is_n, "A"))
    br_n = g.branch(pin(is_n, "ReturnValue", True))
    link(B.find_else_pin(br_p), B.find_execute_pin(br_n))
    p_narr = g.prints(right, "Dlg", C_NARR, 15.0)
    link(B.find_then_pin(br_n), B.find_execute_pin(p_narr))
    p_npc = g.prints(g.concat(left, ": ", right), "Dlg", C_NPC, 15.0)
    link(B.find_else_pin(br_n), B.find_execute_pin(p_npc))
    return B.find_execute_pin(br_p), [B.find_then_pin(p_player), B.find_then_pin(p_narr), B.find_then_pin(p_npc)]


def choice_prompt(g):
    t = g.concat("Ответить:   [1] ", g.get("ChoiceA"), "     [2] ", g.get("ChoiceB"))
    return g.prints(t, "Choice", C_CHOICE, 600.0)


def advance(g):
    """следующая реплика из очереди; очередь кончилась -> выбор (этап 1) или выдача задания (этап 3)"""
    q = g.get("Queue")
    ln = g.named("Utilities|Array|Length", [q])
    link(q, pin(ln, "TargetArray"))
    less = g.call(M + "Less_IntInt")
    link(g.get("Idx"), pin(less, "A"))
    link(pin(ln, "ReturnValue", True), pin(less, "B"))
    br = g.branch(pin(less, "ReturnValue", True))
    entry_in = br
    # есть реплика
    q2 = g.get("Queue")
    item = g.named("Utilities|Array|Get(acopy)", [q2])
    ins = B.list_all_pins(item, unreal.EdGraphPinDirection.EGPD_INPUT)
    arr = [p for p in ins if "array" in str(p.get_pin_name()).lower()][0]
    idxp = [p for p in ins if not p.is_same_native_pin(arr)][0]
    if not arr.list_connected_pins():
        link(q2, arr)
    link(g.get("Idx"), idxp)
    se_in, se_outs = show_entry(g, B.list_all_pins(item, unreal.EdGraphPinDirection.EGPD_OUTPUT)[0])
    link(B.find_then_pin(br), se_in)
    add = g.call(M + "Add_IntInt")
    link(g.get("Idx"), pin(add, "A"))
    pin(add, "B").set_pin_value("1")
    set_idx = g.setv("Idx", src=pin(add, "ReturnValue", True))
    chain([se_outs, set_idx])
    # очередь кончилась
    br_stage1 = g.branch(g.int_eq("Stage", 1))
    link(B.find_else_pin(br), B.find_execute_pin(br_stage1))
    st2 = g.setv("Stage", "2")
    link(B.find_then_pin(br_stage1), B.find_execute_pin(st2))
    chain([st2, choice_prompt(g)])
    st4 = g.setv("Stage", "4")
    link(B.find_else_pin(br_stage1), B.find_execute_pin(st4))
    chain([st4,
           g.prints(g.get("QuestDone"), "Quest", C_QUEST, 8.0),
           g.prints(g.get("QuestNew"), "Quest2", C_QUEST, 30.0)])
    return B.find_execute_pin(entry_in)


def build_friend_bp(d):
    path = NPC_DIR + "/BP_Friend"
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", unreal.Actor)
    bp = at.create_asset("BP_Friend", NPC_DIR, unreal.Blueprint, f)

    body = add_component(bp, unreal.SkeletalMeshComponent, "Body")
    body.set_editor_property("skeletal_mesh_asset", MANNY)
    body.set_editor_property("relative_rotation", unreal.Rotator(0, 0, -90))
    body.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    ad = unreal.SingleAnimationPlayData()
    ad.set_editor_property("anim_to_play", IDLE)
    ad.set_editor_property("saved_looping", True)
    ad.set_editor_property("saved_playing", True)
    ad.set_editor_property("saved_play_rate", 1.0)
    body.set_editor_property("animation_data", ad)
    try:
        body.set_editor_property("visible", False)
    except Exception:
        body.set_visibility(False)
    zone = add_component(bp, unreal.SphereComponent, "TalkZone")
    zone.set_editor_property("sphere_radius", 230.0)
    zone.set_editor_property("relative_location", unreal.Vector(0, 0, 90))

    T = B.get_basic_type_by_name
    strs = B.get_array_type(T("string"))
    for name, typ in (("PlayerName", T("string")), ("NPCName", T("string")), ("QuestStart", T("string")),
                      ("Intro", strs), ("ChoiceA", T("string")), ("ChoiceB", T("string")),
                      ("RepliesA", strs), ("RepliesB", strs), ("Outro", strs),
                      ("QuestDone", T("string")), ("QuestNew", T("string")), ("After", T("string")),
                      ("Queue", strs), ("Idx", T("int")), ("Stage", T("int")),
                      ("SleepingBody", B.get_object_reference_type(unreal.Actor))):
        B.add_member_variable(bp, name, typ)
    for v in ("PlayerName", "NPCName", "QuestStart", "Intro", "ChoiceA", "ChoiceB", "RepliesA", "RepliesB",
              "Outro", "QuestDone", "QuestNew", "After", "SleepingBody"):
        B.set_blueprint_variable_instance_editable(bp, v, True)
        B.set_blueprint_variable_category(bp, v, unreal.Text("Диалог"))
    B.compile_blueprint(bp)

    g = G(bp)
    # BeginPlay: показать стартовое задание
    bpn = B.add_event_override(bp, "ReceiveBeginPlay", unreal.IntPoint(0, 0))
    g.x = 280
    chain([bpn, g.prints(g.get("QuestStart"), "Quest", C_QUEST, 20.0)])

    # Вошёл в зону: включить ввод и подсказать
    g.row()
    ev_in = g.ed.add_component_bound_event_node(zone, "OnComponentBeginOverlap")
    g.pos(ev_in)
    eq = g.call(M + "EqualEqual_ObjectObject")
    link(pin(ev_in, "OtherActor", True), pin(eq, "A"))
    link(pin(g.call("/Script/Engine.GameplayStatics.GetPlayerPawn"), "ReturnValue", True), pin(eq, "B"))
    br = g.branch(pin(eq, "ReturnValue", True))
    link(B.find_then_pin(ev_in), B.find_execute_pin(br))
    en = g.call("/Script/Engine.Actor.EnableInput")
    link(pin(g.call("/Script/Engine.GameplayStatics.GetPlayerController"), "ReturnValue", True), pin(en, "PlayerController"))
    link(B.find_then_pin(br), B.find_execute_pin(en))
    br_sleep = g.branch(g.int_eq("Stage", 0))
    link(B.find_then_pin(en), B.find_execute_pin(br_sleep))
    h1 = g.prints(g.concat("[E] - разбудить ", g.get("NPCName")), "Hint", (0.9, 0.9, 0.9), 4.0)
    link(B.find_then_pin(br_sleep), B.find_execute_pin(h1))
    h2 = g.prints("[E] - говорить", "Hint", (0.9, 0.9, 0.9), 4.0)
    link(B.find_else_pin(br_sleep), B.find_execute_pin(h2))

    # Вышел из зоны: выключить ввод
    g.row()
    ev_out = g.ed.add_component_bound_event_node(zone, "OnComponentEndOverlap")
    g.pos(ev_out)
    dis = g.call("/Script/Engine.Actor.DisableInput")
    link(pin(g.call("/Script/Engine.GameplayStatics.GetPlayerController"), "ReturnValue", True), pin(dis, "PlayerController"))
    link(B.find_then_pin(ev_out), B.find_execute_pin(dis))

    # E
    g.row()
    key_e = g.named(g.find_name("Input|KeyboardEvents|E"))
    e_pressed = pin(key_e, "Pressed", True)
    br0 = g.branch(g.int_eq("Stage", 0))
    link(e_pressed, B.find_execute_pin(br0))
    #   этап 0: разбудить - спящее тело прячем, стоящее показываем, очередь = вступление
    hide = g.call("/Script/Engine.Actor.SetActorHiddenInGame")
    link(g.get("SleepingBody"), pin(hide, "self"))
    pin(hide, "bNewHidden").set_pin_value("true")
    vis = g.call("/Script/Engine.SceneComponent.SetVisibility")
    link(g.get("Body"), pin(vis, "self"))
    pin(vis, "bNewVisibility").set_pin_value("true")
    s_q = g.setv("Queue", src=g.get("Intro"))
    s_i = g.setv("Idx", "0")
    s_s = g.setv("Stage", "1")
    link(B.find_then_pin(br0), B.find_execute_pin(hide))
    outs = chain([hide, vis, s_q, s_i, s_s])
    g.row()
    adv1 = advance(g)
    for o in outs:
        link(o, adv1)
    #   этапы 1 и 3: следующая реплика
    g.row()
    orr = g.call(M + "BooleanOR")
    link(g.int_eq("Stage", 1), pin(orr, "A"))
    link(g.int_eq("Stage", 3), pin(orr, "B"))
    br13 = g.branch(pin(orr, "ReturnValue", True))
    link(B.find_else_pin(br0), B.find_execute_pin(br13))
    g.row()
    adv2 = advance(g)
    link(B.find_then_pin(br13), adv2)
    #   этап 2: напомнить выбор, этап 4: короткая реплика
    g.row()
    br2 = g.branch(g.int_eq("Stage", 2))
    link(B.find_else_pin(br13), B.find_execute_pin(br2))
    cp = choice_prompt(g)
    link(B.find_then_pin(br2), B.find_execute_pin(cp))
    g.row()
    af_in, _ = show_entry(g, g.get("After"))
    link(B.find_else_pin(br2), af_in)

    # 1 и 2: выбор ответа
    for key_name, choice, replies in (("One", "ChoiceA", "RepliesA"), ("Two", "ChoiceB", "RepliesB")):
        g.row()
        k = g.named(g.find_name("Input|KeyboardEvents|" + key_name))
        brc = g.branch(g.int_eq("Stage", 2))
        link(pin(k, "Pressed", True), B.find_execute_pin(brc))
        say = g.prints(g.concat(g.get("PlayerName"), ": ", g.get(choice)), "Dlg", C_PLAYER, 15.0)
        clear_choice = g.prints(" ", "Choice", C_CHOICE, 0.1)
        s_q = g.setv("Queue", src=g.get(replies))
        app = g.named("Utilities|Array|Append", [g.get("Queue")])
        ins = B.list_all_pins(app, unreal.EdGraphPinDirection.EGPD_INPUT)
        tgt = [p for p in ins if "target" in str(p.get_pin_name()).lower()][0]
        src = [p for p in ins if "source" in str(p.get_pin_name()).lower()][0]
        if not tgt.list_connected_pins():
            link(g.get("Queue"), tgt)
        link(g.get("Outro"), src)
        s_i = g.setv("Idx", "0")
        s_s = g.setv("Stage", "3")
        link(B.find_then_pin(brc), B.find_execute_pin(say))
        chain([say, clear_choice, s_q, app, s_i, s_s])

    B.compile_blueprint(bp)
    errs = g.ed.list_nodes_with_errors()
    if errs:
        log("ОШИБКИ КОМПИЛЯЦИИ в узлах: %s" % [n.get_name() for n in errs])
    cdo = unreal.get_default_object(bp.generated_class())
    for k, v in (("PlayerName", d["player_name"]), ("NPCName", d["npc_name"]), ("QuestStart", d["quest_start"]),
                 ("Intro", d["intro"]), ("ChoiceA", d["choice_a"]), ("ChoiceB", d["choice_b"]),
                 ("RepliesA", d["replies_a"]), ("RepliesB", d["replies_b"]), ("Outro", d["outro"]),
                 ("QuestDone", d["quest_done"]), ("QuestNew", d["quest_new"]), ("After", d["after"])):
        cdo.set_editor_property(k, v)
    eal.save_loaded_asset(bp)
    log("BP_Friend собран")
    return bp


def place_friend(h, bp, ulf_sleeping, door_x):
    # стоячий Ульф появится рядом со своей лавкой, лицом к двери
    loc = h.w(-h.L / 2 + 1.45, -0.6, 0.0)
    door = h.w(door_x, -h.W / 2, 0.0)
    yaw = math.degrees(math.atan2(door.y - loc.y, door.x - loc.x))
    a = actor_sub.spawn_actor_from_class(bp.generated_class(), loc, unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    a.set_actor_label("NPC_Friend")
    a.set_folder_path(FOLDER)
    a.set_editor_property("SleepingBody", ulf_sleeping)
    try:
        a.set_editor_property("is_spatially_loaded", False)
        ulf_sleeping.set_editor_property("is_spatially_loaded", False)
    except Exception:
        pass


def main():
    name, h = find_target()
    log("дом друга: %s, %.1f x %.1f м" % (name, h.L, h.W))
    clear(name)
    m = {
        "clay": unreal.load_asset(SURF + "/MI_Wet_Clay"),
        "thatch": unreal.load_asset(SURF + "/MI_Wet_Thatch"),
        "wood": unreal.load_asset(SURF + "/MI_Wet_Wood"),
        "hay": unreal.load_asset(SURF + "/MI_Wet_Hay"),
        "floor": mi("MI_Floor_Earth", (0.08, 0.065, 0.05), 0.85),
        "wool": mi("MI_Wool", (0.2, 0.08, 0.05), 0.95),
        "stone": mi("MI_Stone", (0.13, 0.13, 0.12), 0.7),
    }
    embers = emissive_material()
    door_x, _ = build_shell(h, m)
    hx, bench_cx, bench_y = build_interior(h, m, embers, door_x)
    ulf = build_family(h, m, bench_cx, bench_y)
    import json
    d = json.load(open(ROOT + "/Design/dialogue_night_visit.json", encoding="utf-8"))
    bp = build_friend_bp(d)
    place_friend(h, bp, ulf, door_x)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    # камера редактора: в дверях, смотрит внутрь
    cam = h.w(door_x, -h.W / 2 - 2.5, 1.7)
    look = h.w(door_x + 1.5, 0.5, 0.8)
    yaw = math.degrees(math.atan2(look.y - cam.y, look.x - cam.x))
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
        cam, unreal.Rotator(roll=0, pitch=-12, yaw=yaw))
    log("готово")


try:
    main()
except Exception as e:
    import traceback
    log("ОШИБКА: %s\n%s" % (e, traceback.format_exc()))
    raise
