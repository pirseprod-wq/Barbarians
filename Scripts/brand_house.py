# -*- coding: utf-8 -*-
"""
Дом Бранда (как в Скайриме): снаружи обычный длинный дом в селе, внутри - отдельный
большой интерьер на 3 комнаты, вход/выход через загрузочный экран.
  - общая зала: очаг, стол, лавки, ткацкий станок, полки;
  - спальня: отец, мать, младший брат, лавка Ульфа;
  - хлев/кладовая: солома, ясли, мешки, бочки.
Ульф спит - игрок будит его (E), диалог по ролям с выбором [1]/[2], задания.
Тексты: Design/dialogue_night_visit.json, Design/locations.json.
Нужен BP_GameHUD (ui_hud.py). Запуск: py "D:/UOT/Barbarians/Scripts/brand_house.py"
"""
import sys, importlib, json, math, os, textwrap
sys.path.insert(0, "D:/UOT/Barbarians/Scripts")
import lib_build
importlib.reload(lib_build)
from lib_build import *

log = Logger("brand_house")
FOLDER = "Interiors/BrandHouse"
CHAR = "/Game/_Game/Blueprints/Characters"
CORE = "/Game/_Game/Blueprints/Core"
STATE = ROOT + "/Saved/brand_house_target.json"
CELL = (160000.0, 0.0, 0.0)          # где стоит интерьер (за краем карты)
MANNY = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
QUINN = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
IDLE = unreal.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle")
C_PLAYER, C_NPC, C_NARR = (0.55, 0.8, 1.0), (1.0, 0.82, 0.55), (0.62, 0.62, 0.6)


def wrap(s, n=92):
    return "\n".join(textwrap.wrap(s, n)) if len(s) > n else s


def wrap_entry(e):
    who, _, txt = e.partition("|")
    return who + "|" + wrap(txt)


# ---------------------------------------------------------------- поиск дома в селе
def load_all():
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    if isinstance(descs, tuple):
        descs = [d for d in descs if isinstance(d, (list, unreal.Array))]
        descs = descs[0] if descs else []
    if descs:
        unreal.WorldPartitionBlueprintLibrary.load_actors(
            [d.guid for d in descs if not any(k in str(d.native_class) for k in ("Landscape", "Foliage", "HLOD"))])


def find_house():
    load_all()
    labels = {a.get_actor_label(): a for a in actor_sub.get_all_level_actors()}
    name = None
    if os.path.exists(STATE):
        name = json.load(open(STATE))["name"]
    if not name or name + "_Walls" not in labels:
        ps = labels.get("PS_Village")
        p = ps.get_actor_location() if ps else unreal.Vector(0, 0, 0)
        cands = [(abs((a.get_actor_location() - p).length()), lab[:-6]) for lab, a in labels.items()
                 if lab.startswith("Longhouse_") and lab.endswith("_Walls")]
        if not cands:
            raise RuntimeError("длинных домов нет - сначала build_village_night.py")
        name = min(cands)[1]
        json.dump({"name": name}, open(STATE, "w"))
    return name, labels[name + "_Walls"], labels.get(name + "_Door")


def clear():
    n = 0
    for a in actor_sub.get_all_level_actors():
        f = str(a.get_folder_path())
        if f.startswith(FOLDER) or f.startswith("Village_Greybox/HeroHouse") or a.get_actor_label() in ("NPC_Friend", "Ulf_Sleeping"):
            actor_sub.destroy_actor(a)
            n += 1
    log("убрано: %d" % n)


# ---------------------------------------------------------------- интерьер
def build_interior(m, embers):
    fr = Frame(CELL[0], CELL[1], CELL[2], 0.0, FOLDER + "/Interior")
    L, W, H, T = 22.0, 11.0, 3.4, 0.4
    door_x = 1.0
    fr.box("Floor", 0, 0, -0.1, L + 0.8, W + 0.8, 0.2, m["floor"])
    fr.wall_x("Wall_Back", -L / 2, L / 2, W / 2, H, T, m["clay"])
    fr.wall_x("Wall_Front", -L / 2, L / 2, -W / 2, H, T, m["clay"], openings=[(door_x, 1.7, 2.5)])
    fr.box("DoorLeaf_Closed", door_x, -W / 2 - 0.05, 1.25, 1.75, 0.12, 2.55, m["wood"])   # изнутри дверь закрыта
    for sx in (-0.9, 0.9):
        fr.box("DoorFrame", door_x + sx, -W / 2 + 0.05, 1.3, 0.16, 0.5, 2.6, m["wood"])
    fr.wall_y("Wall_West", -W / 2, W / 2, -L / 2, H, T, m["clay"])
    fr.wall_y("Wall_East", -W / 2, W / 2, L / 2, H, T, m["clay"])
    # перегородки: спальня | зала | хлев
    fr.wall_y("Part_Sleep", -W / 2, W / 2, -4.0, H, 0.25, m["wood"], openings=[(0.0, 1.7, 2.5)])
    fr.wall_y("Part_Byre", -W / 2, W / 2, 6.0, H, 0.25, m["wood"], openings=[(-2.0, 2.0, 2.6)])
    # фронтоны ступенями и крыша
    pitch = 40.0
    rise = (W / 2) * math.tan(math.radians(pitch))
    for s, tag in ((1, "E"), (-1, "W")):
        for i in range(9):
            fr.box("Gable%s_%d" % (tag, i), s * L / 2, 0, H + rise * (i + 0.5) / 9, T, W * (1 - i / 9) + 0.1, rise / 9 + 0.02, m["clay"])
    a = math.radians(pitch)
    half = W / 2 + 0.6
    slope = half / math.cos(a) + 0.2
    ridge = H + rise
    zc = (ridge + ridge - half * math.tan(a)) / 2 + 0.15
    for s in (1, -1):
        r = fr.box("Roof" + ("L" if s > 0 else "R"), 0, s * half / 2, zc, L + 1.2, slope, 0.3, m["thatch"], roll=-s * pitch)
        tip = r.get_actor_transform().transform_location(unreal.Vector(0, s * 50, 0))
        if tip.z > r.get_actor_location().z:
            r.set_actor_rotation(fr.rot(roll=s * pitch), False)
    # каркас: конёк, два ряда столбов, балки
    fr.box("RidgeBeam", 0, 0, ridge - 0.3, L, 0.25, 0.25, m["wood"])
    for x in (-8, -4, 0, 4, 8):
        for y in (-2.6, 2.6):
            fr.box("Post", x, y, (H + 0.6) / 2, 0.28, 0.28, H + 0.6, m["wood"])
        fr.box("TieBeam", x, 0, H + 0.45, 0.22, W, 0.22, m["wood"])

    # --- общая зала (x -4..6): очаг, стол, лавки, станок, полки
    hx, hy = 1.0, 0.6
    for i in range(12):
        ang = i / 12 * 2 * math.pi
        fr.box("HearthStone", hx + 0.85 * math.cos(ang), hy + 0.85 * math.sin(ang), 0.1, 0.34, 0.28, 0.22, m["stone"], extra_yaw=math.degrees(ang))
    e = fr.box("Hearth_Embers", hx, hy, 0.04, 1.3, 1.3, 0.08, embers, mesh=CYL, shadow=False)
    for i in range(5):
        fr.box("Hearth_Log", hx, hy, 0.12, 1.1, 0.13, 0.13, m["wood"], extra_yaw=i * 36)
    fr.light("Hearth_Light", hx, hy, 0.6, 12.0, (1.0, 0.45, 0.15), 1600.0)
    tx, ty = 2.2, 4.0
    fr.box("Table", tx, ty, 0.76, 3.0, 1.0, 0.08, m["wood"])
    for sx in (-1.3, 1.3):
        fr.box("TableLeg", tx + sx, ty, 0.36, 0.1, 0.7, 0.72, m["wood"])
    fr.box("Bench_Table", tx, ty - 0.9, 0.24, 3.0, 0.35, 0.48, m["wood"])
    for i, sx in enumerate((-1.0, -0.4, 0.5, 1.1)):
        fr.box("Bowl", tx + sx, ty, 0.84, 0.25, 0.25, 0.1, m["clay"], mesh=CYL)
    fr.box("Shelf", -2.2, W / 2 - 0.45, 1.6, 2.5, 0.4, 0.06, m["wood"])
    for i, sx in enumerate((-1.0, -0.4, 0.2, 0.8)):
        fr.box("Jar", -2.2 + sx, W / 2 - 0.45, 1.8, 0.3, 0.3, 0.35 + 0.05 * i, m["clay"], mesh=CYL)
    # ткацкий станок у передней стены
    for sx in (-0.7, 0.7):
        fr.box("Loom_Post", 4.6 + sx, -W / 2 + 0.7, 1.0, 0.12, 0.12, 2.0, m["wood"])
    fr.box("Loom_Beam", 4.6, -W / 2 + 0.7, 1.95, 1.6, 0.12, 0.12, m["wood"])
    fr.box("Loom_Cloth", 4.6, -W / 2 + 0.72, 1.2, 1.3, 0.03, 1.4, m["wool"])
    for i, (bx, by) in enumerate(((5.3, 3.8), (5.3, 3.0), (-3.4, -4.6))):
        fr.box("Barrel", bx, by, 0.45, 0.7, 0.7, 0.9, m["wood"], mesh=CYL)
    # пучки трав под балками
    for x in (-2, 0, 2, 4):
        fr.box("Herbs", x, 1.5, H + 0.15, 0.15, 0.6, 0.35, m["hay"], shadow=False)

    # --- спальня (x -11..-4)
    bench_y = W / 2 - 0.2 - 0.95
    fr.box("FamilyBed", -7.5, bench_y, 0.25, 6.6, 1.9, 0.5, m["wood"])
    fr.box("FamilyBed_Straw", -7.5, bench_y, 0.55, 6.5, 1.8, 0.12, m["hay"])
    fr.box("UlfBed", -L / 2 + 0.8, -2.2, 0.22, 1.1, 2.2, 0.44, m["wood"])
    fr.box("UlfBed_Straw", -L / 2 + 0.8, -2.2, 0.48, 1.0, 2.1, 0.1, m["hay"])
    fr.box("Chest", -6.0, -W / 2 + 0.6, 0.35, 1.2, 0.6, 0.7, m["wood"])
    fr.box("LampStand", -6.8, -1.8, 0.6, 0.12, 0.12, 1.2, m["wood"])
    fr.box("Lamp", -6.8, -1.8, 1.25, 0.18, 0.18, 0.1, embers, mesh=CYL, shadow=False)
    fr.light("Lamp_Light", -6.8, -1.8, 1.4, 2.5, (1.0, 0.55, 0.25), 700.0)

    # --- хлев/кладовая (x 6..11)
    fr.box("Byre_Straw", 8.5, 0.5, 0.03, 4.6, 9.5, 0.08, m["hay"])
    fr.box("Trough", L / 2 - 0.7, 1.5, 0.35, 0.6, 4.0, 0.6, m["wood"])
    for y in (-1.0, 1.5, 4.0):
        fr.box("StallRail", 8.5, y, 1.0, 3.6, 0.1, 0.12, m["wood"])
        fr.box("StallPost", 6.8, y, 0.6, 0.12, 0.12, 1.2, m["wood"])
    fr.box("HayPile", 9.0, -3.5, 0.5, 2.4, 2.0, 1.0, m["hay"])
    for i, (sx, sy) in enumerate(((7.0, -4.6), (7.6, -4.5), (7.3, -3.9))):
        fr.box("Sack", sx, sy, 0.35, 0.55, 0.45, 0.7, m["wool"])
    fr.light("Byre_Light", 8.5, 0, 2.5, 0.6, (0.7, 0.75, 0.9), 600.0)

    for act in actor_sub.get_all_level_actors():
        if str(act.get_folder_path()).startswith(FOLDER):
            always_loaded(act)
    return fr, door_x, W, L, bench_y


def build_family(fr, m, W, L, bench_y):
    top = 0.62
    sleeper(fr, "Family_Father", MANNY, IDLE, -9.4, bench_y, top + 0.12, False, 1.0)
    sleeper(fr, "Family_Mother", QUINN, IDLE, -8.1, bench_y, top + 0.12, False, 0.95)
    sleeper(fr, "Family_Child", QUINN, IDLE, -7.1, bench_y, top + 0.1, False, 0.68)
    for lab, x, w, ln in (("Father", -9.4, 0.8, 1.3), ("Mother", -8.1, 0.75, 1.25), ("Child", -7.1, 0.6, 0.9)):
        fr.box("Blanket_" + lab, x, bench_y - 0.25, top + 0.2, w, ln, 0.2, m["wool"])
    ulf = sleeper(fr, "Ulf_Sleeping", MANNY, IDLE, -L / 2 + 0.8, -2.25, 0.66, False, 0.97, head_positive=False)
    fr.box("Blanket_Ulf", -L / 2 + 0.8, -2.0, 0.72, 0.8, 1.45, 0.18, m["wool"])
    for a in (ulf,):
        always_loaded(a)
    return ulf


# ---------------------------------------------------------------- BP_Door: вход/выход через загрузочный экран
def build_door_bp():
    bp = new_bp(CORE, "BP_Door", unreal.Actor)
    zone = add_component(bp, unreal.SphereComponent, "Zone")
    zone.set_editor_property("sphere_radius", 170.0)
    zone.set_editor_property("relative_location", unreal.Vector(0, 0, 100))
    T = B.get_basic_type_by_name
    for name, typ in (("Title", T("string")), ("Prompt", T("string")), ("Tips", B.get_array_type(T("string"))),
                      ("Destination", B.get_object_reference_type(unreal.Actor)), ("Indoors", T("bool")),
                      ("RainSound", B.get_object_reference_type(unreal.Actor))):
        B.add_member_variable(bp, name, typ)
        B.set_blueprint_variable_instance_editable(bp, name, True)
        B.set_blueprint_variable_category(bp, name, unreal.Text("Дверь"))
    B.compile_blueprint(bp)
    g = G(bp)

    # вошёл в зону
    ev = g.ed.add_component_bound_event_node(zone, "OnComponentBeginOverlap"); g._pos(ev)
    eq = g.op("EqualEqual_ObjectObject", pin(ev, "OtherActor", True), pin(g.call(GS + "GetPlayerPawn"), "ReturnValue", True))
    br = g.branch(eq); link(then(ev), ex(br))
    en = g.call("/Script/Engine.Actor.EnableInput")
    link(pin(g.call(GS + "GetPlayerController"), "ReturnValue", True), pin(en, "PlayerController"))
    cast, hud = g.hud()
    s1 = g.hud_set(hud, "HintText", src=g.g("Prompt"))
    s2 = g.hud_until(hud, "HintUntil", 100000.0)
    link(then(br), ex(en)); chain([en, cast, s1, s2])

    # вышел
    g.row()
    ev2 = g.ed.add_component_bound_event_node(zone, "OnComponentEndOverlap"); g._pos(ev2)
    dis = g.call("/Script/Engine.Actor.DisableInput")
    link(pin(g.call(GS + "GetPlayerController"), "ReturnValue", True), pin(dis, "PlayerController"))
    cast2, hud2 = g.hud()
    s3 = g.hud_set(hud2, "HintUntil", value="0")
    chain([ev2, dis, cast2, s3])

    # E: загрузочный экран -> перенос -> снять экран, плавно проявить картинку
    g.row()
    k = g.key("E")
    cast3, hud3 = g.hud()
    link(pin(k, "Pressed", True), ex(cast3))
    tips = g.g("Tips")
    ln = g.named("Utilities|Array|Length", [tips]); link(tips, pin(ln, "TargetArray"))
    mx = g.op("Subtract_IntInt", pin(ln, "ReturnValue", True), 1)
    rnd = g.call(M + "RandomIntegerInRange", Min=0); link(mx, pin(rnd, "Max"))
    tips2 = g.g("Tips")
    item = g.named("Utilities|Array|Get(acopy)", [tips2])
    ins = B.list_all_pins(item, unreal.EdGraphPinDirection.EGPD_INPUT)
    arr = [p for p in ins if "array" in str(p.get_pin_name()).lower()][0]
    idx = [p for p in ins if not p.is_same_native_pin(arr)][0]
    if not arr.list_connected_pins():
        link(tips2, arr)
    link(pin(rnd, "ReturnValue", True), idx)
    a1 = g.hud_set(hud3, "LoadingTitle", src=g.g("Title"))
    a2 = g.hud_set(hud3, "LoadingTip", src=B.list_all_pins(item, unreal.EdGraphPinDirection.EGPD_OUTPUT)[0])
    a3 = g.hud_set(hud3, "Loading", value="true")
    a4 = g.hud_set(hud3, "HintUntil", value="0")
    d1 = g.call(SYS + "Delay", Duration=0.05)
    dest = g.g("Destination")
    gl = g.call("/Script/Engine.Actor.K2_GetActorLocation"); link(dest, B.find_self_pin(gl))
    gr = g.call("/Script/Engine.Actor.K2_GetActorRotation"); link(dest, B.find_self_pin(gr))
    mv = g.call("/Script/Engine.Actor.K2_SetActorLocationAndRotation", bTeleport=True)
    link(pin(g.call(GS + "GetPlayerPawn"), "ReturnValue", True), B.find_self_pin(mv))
    link(pin(gl, "ReturnValue", True), pin(mv, "NewLocation"))
    link(pin(gr, "ReturnValue", True), pin(mv, "NewRotation"))
    rotc = g.call("/Script/Engine.Controller.SetControlRotation")
    link(pin(g.call(GS + "GetPlayerController"), "ReturnValue", True), B.find_self_pin(rotc))
    link(pin(gr, "ReturnValue", True), pin(rotc, "NewRotation"))
    # погода: дождь не виден в помещении, шум дождя глуше
    sel = g.call(M + "SelectFloat", A=0.0, B=1.0); link(g.g("Indoors"), pin(sel, "bPickA"))
    mpc = g.call("/Script/Engine.KismetMaterialLibrary.SetScalarParameterValue", ParameterName="RainAmount")
    pin(mpc, "Collection").set_pin_value("/Game/_Game/Materials/Weather/MPC_Weather.MPC_Weather")
    link(pin(sel, "ReturnValue", True), pin(mpc, "ParameterValue"))
    weather_nodes = [mpc]
    try:
        comp = g.call("/Script/Engine.Actor.GetComponentByClass")
        link(g.g("RainSound"), B.find_self_pin(comp))
        pin(comp, "ComponentClass").set_pin_value("/Script/Engine.AudioComponent")
        vol = g.call("/Script/Engine.AudioComponent.SetVolumeMultiplier")
        link(pin(comp, "ReturnValue", True), B.find_self_pin(vol))
        selv = g.call(M + "SelectFloat", A=0.18, B=0.7); link(g.g("Indoors"), pin(selv, "bPickA"))
        link(pin(selv, "ReturnValue", True), pin(vol, "NewVolumeMultiplier"))
        weather_nodes.append(vol)
    except Exception as e:
        log("громкость дождя не подключена: %s" % e)
    d2 = g.call(SYS + "Delay", Duration=1.8)
    a5 = g.hud_set(hud3, "Loading", value="false")
    fade = g.call("/Script/Engine.PlayerCameraManager.StartCameraFade", FromAlpha=1.0, ToAlpha=0.0, Duration=0.8)
    link(pin(g.call(GS + "GetPlayerCameraManager"), "ReturnValue", True), B.find_self_pin(fade))
    chain([cast3, a1, a2, a3, a4, d1, mv, rotc] + weather_nodes + [d2, a5, fade])
    B.compile_blueprint(bp)
    errs = g.ed.list_nodes_with_errors()
    log("BP_Door: " + ("ошибки %s" % [n.get_name() for n in errs] if errs else "ок"))
    eal.save_loaded_asset(bp)
    return bp


# ---------------------------------------------------------------- BP_Friend через HUD
def show_entry(g, hud, entry):
    sp = g.call(S + "Split", InStr="|")
    link(entry, pin(sp, "SourceString"))
    left, right = pin(sp, "LeftS", True), pin(sp, "RightS", True)
    s_who = g.hud_set(hud, "DlgSpeaker", src=left)
    s_txt = g.hud_set(hud, "DlgText", src=right)
    is_p = g.call(S + "EqualEqual_StrStr"); link(left, pin(is_p, "A")); link(g.g("PlayerName"), pin(is_p, "B"))
    br_p = g.branch(pin(is_p, "ReturnValue", True))
    c_p = g.hud_set(hud, "DlgColor", value=color_str(C_PLAYER))
    is_n = g.call(S + "EqualEqual_StrStr"); link(left, pin(is_n, "A"))
    br_n = g.branch(pin(is_n, "ReturnValue", True))
    c_n = g.hud_set(hud, "DlgColor", value=color_str(C_NARR))
    c_c = g.hud_set(hud, "DlgColor", value=color_str(C_NPC))
    until = g.hud_until(hud, "DlgUntil", 600.0)
    chain([s_who, s_txt, br_p])
    link(then(br_p), ex(c_p)); link(B.find_else_pin(br_p), ex(br_n))
    link(then(br_n), ex(c_n)); link(B.find_else_pin(br_n), ex(c_c))
    for n in (c_p, c_n, c_c):
        link(then(n), ex(until))
    return ex(s_who), [then(until)]


def advance(g, hud):
    q = g.g("Queue")
    ln = g.named("Utilities|Array|Length", [q]); link(q, pin(ln, "TargetArray"))
    br = g.branch(g.op("Less_IntInt", g.g("Idx"), pin(ln, "ReturnValue", True)))
    q2 = g.g("Queue")
    item = g.named("Utilities|Array|Get(acopy)", [q2])
    ins = B.list_all_pins(item, unreal.EdGraphPinDirection.EGPD_INPUT)
    arr = [p for p in ins if "array" in str(p.get_pin_name()).lower()][0]
    idx = [p for p in ins if not p.is_same_native_pin(arr)][0]
    if not arr.list_connected_pins():
        link(q2, arr)
    link(g.g("Idx"), idx)
    se_in, se_out = show_entry(g, hud, B.list_all_pins(item, unreal.EdGraphPinDirection.EGPD_OUTPUT)[0])
    link(then(br), se_in)
    inc = g.setv("Idx", src=g.op("Add_IntInt", g.g("Idx"), 1))
    chain([se_out, inc])
    # очередь кончилась
    br1 = g.branch(g.int_eq("Stage", 1))
    link(B.find_else_pin(br), ex(br1))
    st2 = g.setv("Stage", "2")
    ch = g.hud_set(hud, "ChoiceText", src=g.concat("[1] ", g.g("ChoiceA"), "        [2] ", g.g("ChoiceB")))
    keep = g.hud_until(hud, "DlgUntil", 600.0)
    link(then(br1), ex(st2)); chain([st2, ch, keep])
    st4 = g.setv("Stage", "4")
    qt = g.hud_set(hud, "QuestText", src=g.concat(g.g("QuestDone"), "\n", g.g("QuestNew")))
    qu = g.hud_until(hud, "QuestUntil", 30.0)
    dl = g.hud_until(hud, "DlgUntil", 3.0)
    link(B.find_else_pin(br1), ex(st4)); chain([st4, qt, qu, dl])
    return ex(br)


def build_friend_bp(d):
    bp = new_bp(CHAR, "BP_Friend", unreal.Actor)
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
    zone.set_editor_property("sphere_radius", 260.0)
    zone.set_editor_property("relative_location", unreal.Vector(0, 0, 90))
    T = B.get_basic_type_by_name
    strs = B.get_array_type(T("string"))
    edit = ("PlayerName", "QuestStart", "WakeHint", "TalkHint", "Intro", "ChoiceA", "ChoiceB",
            "RepliesA", "RepliesB", "Outro", "QuestDone", "QuestNew", "After", "SleepingBody")
    for name, typ in (("PlayerName", T("string")), ("QuestStart", T("string")), ("WakeHint", T("string")),
                      ("TalkHint", T("string")), ("Intro", strs), ("ChoiceA", T("string")), ("ChoiceB", T("string")),
                      ("RepliesA", strs), ("RepliesB", strs), ("Outro", strs), ("QuestDone", T("string")),
                      ("QuestNew", T("string")), ("After", T("string")), ("Queue", strs), ("Idx", T("int")),
                      ("Stage", T("int")), ("SleepingBody", B.get_object_reference_type(unreal.Actor))):
        B.add_member_variable(bp, name, typ)
        if name in edit:
            B.set_blueprint_variable_instance_editable(bp, name, True)
            B.set_blueprint_variable_category(bp, name, unreal.Text("Диалог"))
    B.compile_blueprint(bp)
    g = G(bp)

    # старт: показать первое задание
    bpn = g.event("ReceiveBeginPlay")
    # гарантируем наш HUD (режим игры иногда отдаёт стандартный)
    sethud = g.call("/Script/Engine.PlayerController.ClientSetHUD")
    link(pin(g.call(GS + "GetPlayerController"), "ReturnValue", True), B.find_self_pin(sethud))
    pin(sethud, "NewHUDClass").set_pin_value(HUD_CLASS_PATH)
    d1 = g.call(SYS + "Delay", Duration=1.0)
    c0, h0 = g.hud()
    chain([bpn, sethud, d1, c0, g.hud_set(h0, "QuestText", src=g.g("QuestStart")), g.hud_until(h0, "QuestUntil", 20.0)])

    # вошёл в зону
    g.row()
    ev = g.ed.add_component_bound_event_node(zone, "OnComponentBeginOverlap"); g._pos(ev)
    br = g.branch(g.op("EqualEqual_ObjectObject", pin(ev, "OtherActor", True), pin(g.call(GS + "GetPlayerPawn"), "ReturnValue", True)))
    link(then(ev), ex(br))
    en = g.call("/Script/Engine.Actor.EnableInput")
    link(pin(g.call(GS + "GetPlayerController"), "ReturnValue", True), pin(en, "PlayerController"))
    c1, h1 = g.hud()
    link(then(br), ex(en)); chain([en, c1])
    brs = g.branch(g.int_eq("Stage", 0))
    link(then(c1), ex(brs))
    hw = g.hud_set(h1, "HintText", src=g.g("WakeHint"))
    ht = g.hud_set(h1, "HintText", src=g.g("TalkHint"))
    hu = g.hud_until(h1, "HintUntil", 100000.0)
    link(then(brs), ex(hw)); link(B.find_else_pin(brs), ex(ht))
    link(then(hw), ex(hu)); link(then(ht), ex(hu))

    # вышел
    g.row()
    ev2 = g.ed.add_component_bound_event_node(zone, "OnComponentEndOverlap"); g._pos(ev2)
    dis = g.call("/Script/Engine.Actor.DisableInput")
    link(pin(g.call(GS + "GetPlayerController"), "ReturnValue", True), pin(dis, "PlayerController"))
    c2, h2 = g.hud()
    chain([ev2, dis, c2, g.hud_set(h2, "HintUntil", value="0"), g.hud_set(h2, "DlgUntil", value="0")])

    # E
    g.row()
    k = g.key("E")
    c3, h3 = g.hud()
    link(pin(k, "Pressed", True), ex(c3))
    br0 = g.branch(g.int_eq("Stage", 0)); link(then(c3), ex(br0))
    hide = g.call("/Script/Engine.Actor.SetActorHiddenInGame", bNewHidden=True); link(g.g("SleepingBody"), B.find_self_pin(hide))
    vis = g.call("/Script/Engine.SceneComponent.SetVisibility", bNewVisibility=True); link(g.g("Body"), B.find_self_pin(vis))
    s_q = g.setv("Queue", src=g.g("Intro")); s_i = g.setv("Idx", "0"); s_s = g.setv("Stage", "1")
    hint = g.hud_set(h3, "HintText", src=g.g("TalkHint"))
    link(then(br0), ex(hide))
    outs = chain([hide, vis, s_q, s_i, s_s, hint])
    g.row()
    a1 = advance(g, h3)
    for o in outs:
        link(o, a1)
    g.row()
    br13 = g.branch(g.op("BooleanOR", g.int_eq("Stage", 1), g.int_eq("Stage", 3)))
    link(B.find_else_pin(br0), ex(br13))
    g.row()
    link(then(br13), advance(g, h3))
    g.row()
    br4 = g.branch(g.int_eq("Stage", 4))
    link(B.find_else_pin(br13), ex(br4))
    af_in, _ = show_entry(g, h3, g.g("After"))
    link(then(br4), af_in)

    # 1/2: выбор
    for key_name, choice, replies in (("1", "ChoiceA", "RepliesA"), ("2", "ChoiceB", "RepliesB")):
        g.row()
        kk = g.key(key_name)
        brc = g.branch(g.int_eq("Stage", 2))
        cc, hh = g.hud()
        link(pin(kk, "Pressed", True), ex(brc)); link(then(brc), ex(cc))
        n1 = g.hud_set(hh, "ChoiceText", value="")
        n2 = g.hud_set(hh, "DlgSpeaker", src=g.g("PlayerName"))
        n3 = g.hud_set(hh, "DlgText", src=g.g(choice))
        n4 = g.hud_set(hh, "DlgColor", value=color_str(C_PLAYER))
        n5 = g.hud_until(hh, "DlgUntil", 600.0)
        n6 = g.setv("Queue", src=g.g(replies))      # ответы уже содержат концовку (Outro)
        n7 = g.setv("Idx", "0"); n8 = g.setv("Stage", "3")
        chain([cc, n1, n2, n3, n4, n5, n6, n7, n8])

    B.compile_blueprint(bp)
    errs = g.ed.list_nodes_with_errors()
    log("BP_Friend: " + ("ошибки %s" % [n.get_name() for n in errs] if errs else "ок"))
    cdo = unreal.get_default_object(bp.generated_class())
    vals = {"PlayerName": d["player_name"], "QuestStart": wrap(d["quest_start"]), "WakeHint": d["wake_hint"],
            "TalkHint": d["talk_hint"], "Intro": [wrap_entry(x) for x in d["intro"]],
            "ChoiceA": d["choice_a"], "ChoiceB": d["choice_b"],
            "RepliesA": [wrap_entry(x) for x in d["replies_a"] + d["outro"]],
            "RepliesB": [wrap_entry(x) for x in d["replies_b"] + d["outro"]],
            "Outro": [wrap_entry(x) for x in d["outro"]], "QuestDone": wrap(d["quest_done"]),
            "QuestNew": wrap(d["quest_new"]), "After": wrap_entry(d["after"])}
    for k2, v in vals.items():
        cdo.set_editor_property(k2, v)
    eal.save_loaded_asset(bp)
    return bp


# ---------------------------------------------------------------- сборка
def main():
    loc = json.load(open(ROOT + "/Design/locations.json", encoding="utf-8"))
    dlg = json.load(open(ROOT + "/Design/dialogue_night_visit.json", encoding="utf-8"))
    name, walls, door_marker = find_house()
    log("дом в селе: " + name)
    clear()
    m = {"clay": load_mat("MI_Wet_Clay"), "thatch": load_mat("MI_Wet_Thatch"), "wood": load_mat("MI_Wet_Wood"),
         "hay": load_mat("MI_Wet_Hay"), "floor": mi("MI_Floor_Earth", (0.08, 0.065, 0.05), 0.85),
         "wool": mi("MI_Wool", (0.2, 0.08, 0.05), 0.95), "stone": mi("MI_Stone", (0.13, 0.13, 0.12), 0.7)}
    embers = unreal.load_asset(SURF + "/MI_Embers")
    fr, door_x, W, L, bench_y = build_interior(m, embers)
    ulf = build_family(fr, m, W, L, bench_y)
    door_bp = build_door_bp()
    friend_bp = build_friend_bp(dlg)
    tips = [wrap(t) for t in loc["tips"]]

    # --- снаружи: дверь дома в селе
    yaw = walls.get_actor_rotation().yaw
    wloc = walls.get_actor_location()
    dloc = door_marker.get_actor_location() if door_marker else wloc
    out_dir = unreal.Vector(dloc.x - wloc.x, dloc.y - wloc.y, 0)
    out_dir = out_dir * (1.0 / max(out_dir.length(), 1.0))
    ground = dloc.z - 118
    ext = Frame(dloc.x, dloc.y, ground, math.degrees(math.atan2(out_dir.y, out_dir.x)), FOLDER + "/Exterior")
    ext_arrive = ext.marker("Arrive_Village", 3.2, 0, 1.0, 0)          # лицом от дома
    ext_door = actor_sub.spawn_actor_from_class(door_bp.generated_class(), ext.w(0.6, 0, 0), ext.rot())
    ext_door.set_actor_label("Door_BrandHouse_Enter")
    ext_door.set_folder_path(FOLDER + "/Exterior")

    # --- внутри: точка появления у входа, дверь наружу
    in_arrive = fr.marker("Arrive_BrandHouse", door_x, -W / 2 + 2.6, 1.0, 90)   # лицом в залу
    in_door = actor_sub.spawn_actor_from_class(door_bp.generated_class(), fr.w(door_x, -W / 2 + 0.3, 0), fr.rot())
    in_door.set_actor_label("Door_BrandHouse_Exit")
    in_door.set_folder_path(FOLDER + "/Interior")

    rain = [a for a in actor_sub.get_all_level_actors() if a.get_actor_label() == "Amb_Rain"]
    for dr, title, prompt, dest, indoors in ((ext_door, loc["brand_house"], loc["enter_prompt"], in_arrive, True),
                                             (in_door, loc["village"], loc["exit_prompt"], ext_arrive, False)):
        dr.set_editor_property("Indoors", indoors)
        if rain:
            dr.set_editor_property("RainSound", rain[0])
        dr.set_editor_property("Title", title)
        dr.set_editor_property("Prompt", prompt)
        dr.set_editor_property("Tips", tips)
        dr.set_editor_property("Destination", dest)
        always_loaded(dr)
    for a in (ext_arrive, in_arrive):
        always_loaded(a)

    # --- Ульф: стоячий появится у своей лавки, лицом в спальню
    f_loc = fr.w(-L / 2 + 1.9, -2.2, 0.0)
    friend = actor_sub.spawn_actor_from_class(friend_bp.generated_class(), f_loc, fr.rot(0))
    friend.set_actor_label("NPC_Friend")
    friend.set_folder_path(FOLDER + "/Interior")
    friend.set_editor_property("SleepingBody", ulf)
    always_loaded(friend)

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    cam = fr.w(-2.0, -4.0, 1.7)
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
        cam, unreal.Rotator(roll=0, pitch=-10, yaw=150))
    log("готово")


try:
    main()
except Exception as e:
    import traceback
    log("ОШИБКА: %s\n%s" % (e, traceback.format_exc()))
    raise
