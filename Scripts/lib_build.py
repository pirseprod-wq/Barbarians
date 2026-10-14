# -*- coding: utf-8 -*-
"""Общие помощники для скриптов сборки: геометрия-заглушки, материалы, генерация графов Blueprint."""
import math
import unreal

ROOT = "D:/UOT/Barbarians"
U = 100.0
at = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
B = unreal.BlueprintEditorLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
SURF = "/Game/_Game/Materials/Greybox"
HUD_CLASS_PATH = "/Game/_Game/Blueprints/Core/BP_GameHUD.BP_GameHUD_C"


class Logger:
    def __init__(self, name):
        self.path = ROOT + "/Saved/%s_log.txt" % name
        self.tag = "[%s] " % name
        open(self.path, "w").close()

    def __call__(self, m):
        unreal.log(self.tag + m)
        open(self.path, "a", encoding="utf-8").write(m + "\n")


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


def load_mat(name):
    return unreal.load_asset(SURF + "/" + name)


# ---------------------------------------------------------------- геометрия в локальных координатах
class Frame:
    """Локальная система: центр (см), уровень пола (см), поворот; размеры в метрах."""
    def __init__(self, cx, cy, gz, yaw, folder):
        self.cx, self.cy, self.gz, self.yaw, self.folder = cx, cy, gz, yaw, folder

    def w(self, lx, ly, lz):
        r = math.radians(self.yaw)
        x, y = lx * U, ly * U
        return unreal.Vector(self.cx + x * math.cos(r) - y * math.sin(r),
                             self.cy + x * math.sin(r) + y * math.cos(r), self.gz + lz * U)

    def rot(self, extra_yaw=0.0, roll=0.0, pitch=0.0):
        return unreal.Rotator(roll=roll, pitch=pitch, yaw=self.yaw + extra_yaw)

    def box(self, label, lx, ly, lz, sx, sy, sz, mat, extra_yaw=0.0, roll=0.0, mesh=None, shadow=True):
        a = actor_sub.spawn_actor_from_object(mesh or CUBE, self.w(lx, ly, lz), self.rot(extra_yaw, roll))
        a.set_actor_scale3d(unreal.Vector(sx, sy, sz))
        a.set_actor_label(label)
        a.set_folder_path(self.folder)
        if mat:
            a.static_mesh_component.set_material(0, mat)
        if not shadow:
            a.static_mesh_component.set_editor_property("cast_shadow", False)
        return a

    def wall_x(self, label, x0, x1, y, h, t, mat, openings=()):
        """стена вдоль X от x0 до x1 на линии y, с проёмами [(центр, ширина, высота)]"""
        cuts = sorted(openings)
        cur = x0
        n = 0
        for c, wdt, hgt in cuts:
            a, b = c - wdt / 2, c + wdt / 2
            if a - cur > 0.02:
                self.box("%s_%d" % (label, n), (cur + a) / 2, y, h / 2 - 0.15, a - cur, t, h + 0.3, mat); n += 1
            if h - hgt > 0.02:
                self.box("%s_Top%d" % (label, n), c, y, hgt + (h - hgt) / 2, wdt, t, h - hgt, mat); n += 1
            cur = b
        if x1 - cur > 0.02:
            self.box("%s_%d" % (label, n), (cur + x1) / 2, y, h / 2 - 0.15, x1 - cur, t, h + 0.3, mat)

    def wall_y(self, label, y0, y1, x, h, t, mat, openings=()):
        cuts = sorted(openings)
        cur = y0
        n = 0
        for c, wdt, hgt in cuts:
            a, b = c - wdt / 2, c + wdt / 2
            if a - cur > 0.02:
                self.box("%s_%d" % (label, n), x, (cur + a) / 2, h / 2 - 0.15, t, a - cur, h + 0.3, mat); n += 1
            if h - hgt > 0.02:
                self.box("%s_Top%d" % (label, n), x, c, hgt + (h - hgt) / 2, t, wdt, h - hgt, mat); n += 1
            cur = b
        if y1 - cur > 0.02:
            self.box("%s_%d" % (label, n), x, (cur + y1) / 2, h / 2 - 0.15, t, y1 - cur, h + 0.3, mat)

    def light(self, label, lx, ly, lz, candela, color, radius):
        l = actor_sub.spawn_actor_from_class(unreal.PointLight, self.w(lx, ly, lz), self.rot())
        l.set_actor_label(label)
        l.set_folder_path(self.folder)
        c = l.point_light_component
        try:
            c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
        except Exception:
            pass
        c.set_editor_property("intensity", candela)
        c.set_light_color(unreal.LinearColor(color[0], color[1], color[2], 1.0))
        c.set_editor_property("attenuation_radius", radius)
        c.set_editor_property("source_radius", 20.0)
        return l

    def marker(self, label, lx, ly, lz, extra_yaw):
        t = actor_sub.spawn_actor_from_class(unreal.TargetPoint, self.w(lx, ly, lz), self.rot(extra_yaw))
        t.set_actor_label(label)
        t.set_folder_path(self.folder)
        return t


def always_loaded(a):
    try:
        a.set_editor_property("is_spatially_loaded", False)
    except Exception:
        pass


def sleeper(fr, label, mesh, anim, lx, ly, lz, along_x, scale, head_positive=True):
    """Спящий: поза MM_Idle, уложенная лицом вверх. (lx,ly,lz) - середина тела."""
    a = actor_sub.spawn_actor_from_object(mesh, fr.w(lx, ly, lz), fr.rot())
    a.set_actor_label(label)
    a.set_folder_path(fr.folder)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    c = a.skeletal_mesh_component
    c.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    d = unreal.SingleAnimationPlayData()
    d.set_editor_property("anim_to_play", anim)
    d.set_editor_property("saved_looping", True)
    d.set_editor_property("saved_playing", False)
    d.set_editor_property("saved_position", 0.0)
    d.set_editor_property("saved_play_rate", 0.0)
    c.set_editor_property("animation_data", d)
    want = (fr.w(1, 0, 0) - fr.w(0, 0, 0)) if along_x else (fr.w(0, 1, 0) - fr.w(0, 0, 0))
    best = None
    for roll in (90, -90):
        for yaw_add in (0, 90, 180, 270):
            r = unreal.MathLibrary.compose_rotators(unreal.Rotator(roll=roll, pitch=0, yaw=0),
                                                   unreal.Rotator(roll=0, pitch=0, yaw=fr.yaw + yaw_add))
            a.set_actor_rotation(r, False)
            t = a.get_actor_transform()
            o = t.transform_location(unreal.Vector(0, 0, 0))
            body = t.transform_location(unreal.Vector(0, 0, 170)) - o
            up = t.transform_location(unreal.Vector(0, 100, 0)).z - o.z
            along = (body.x * want.x + body.y * want.y) / (body.length() * want.length() + 1e-6)
            score = (abs(body.z) < 20, up > 50, round(abs(along), 2), (along > 0) == head_positive)
            if best is None or score > best[0]:
                best = (score, r)
    a.set_actor_rotation(best[1], False)
    mid = a.get_actor_transform().transform_location(unreal.Vector(0, 0, 90))
    a.set_actor_location(a.get_actor_location() + (fr.w(lx, ly, lz) - mid), False, False)
    return a


# ---------------------------------------------------------------- генерация Blueprint
def new_bp(path_dir, name, parent_cls):
    full = path_dir + "/" + name
    if eal.does_asset_exist(full):
        eal.delete_asset(full)
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", parent_cls)
    return at.create_asset(name, path_dir, unreal.Blueprint, f)


def add_component(bp, cls, name):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    parent = handles[0]
    for hd in handles:
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(hd))
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


def then(n):
    return B.find_then_pin(n)


def ex(n):
    return B.find_execute_pin(n)


def chain(items):
    """exec подряд: элемент - узел или список выходных exec-пинов. Возвращает последние выходы."""
    prev = None
    for it in items:
        if prev is not None:
            for o in prev:
                link(o, ex(it))
        prev = it if isinstance(it, list) else [then(it)]
    return prev


S = "/Script/Engine.KismetStringLibrary."
M = "/Script/Engine.KismetMathLibrary."
SYS = "/Script/Engine.KismetSystemLibrary."
GS = "/Script/Engine.GameplayStatics."


def color_str(c, a=1.0):
    return "(R=%f,G=%f,B=%f,A=%f)" % (c[0], c[1], c[2], a)


class G:
    def __init__(self, bp):
        self.bp = bp
        self.ed = unreal.BlueprintGraphEditor.get_graph_editor(B.find_event_graph(bp))
        self.x = 0
        self.y = 0
        self.avail = None

    def _pos(self, n, dy=0):
        B.set_node_pos(n, unreal.IntPoint(self.x, self.y + dy))
        self.x += 300
        return n

    def row(self):
        self.y += 600
        self.x = 0

    def call(self, path, **lits):
        n = self.ed.add_call_function_node(path)
        if n is None:
            raise RuntimeError("нет функции " + path)
        for k, v in lits.items():
            pin(n, k).set_pin_value(str(v).lower() if isinstance(v, bool) else str(v))
        return self._pos(n)

    def find_name(self, name):
        if self.avail is None:
            self.avail = list(self.ed.list_available_nodes([]))
        for n in self.avail:
            if n.lower() == name.lower():
                return n
        for n in self.avail:
            if n.lower().endswith(name.lower()):
                return n
        raise RuntimeError("не найден узел " + name)

    def named(self, name, ctx=None):
        n = self.ed.create_node_from_name(name, unreal.Vector2D(self.x, self.y), ctx or [])
        if n is None:
            raise RuntimeError("нет узла " + name)
        self.x += 300
        return n

    def event(self, name):
        n = B.add_event_override(self.bp, name, unreal.IntPoint(self.x, self.y))
        if n is None:
            raise RuntimeError("нет события " + name)
        self.x += 300
        return n

    def key(self, key_name):
        return self.named(self.find_name("Input|KeyboardEvents|" + key_name))

    def get(self, var, cls_path=""):
        n = self._pos(self.ed.add_get_member_variable_node(var, cls_path), dy=180)
        return pin(n, var, True), n

    def g(self, var):
        return self.get(var)[0]

    def setv(self, var, value=None, src=None, target=None, cls_path=""):
        n = self._pos(self.ed.add_set_member_variable_node(var, cls_path))
        if value is not None:
            pin(n, var).set_pin_value(value)
        if src is not None:
            link(src, pin(n, var))
        if target is not None:
            link(target, B.find_self_pin(n))
        return n

    def branch(self, cond):
        n = self._pos(self.ed.add_branch_node())
        link(cond, B.find_condition_pin(n))
        return n

    def op(self, fn, a, b):
        n = self.call(M + fn)
        for nm, v in (("A", a), ("B", b)):
            if isinstance(v, (int, float, str)) and not hasattr(v, "get_pin_name"):
                pin(n, nm).set_pin_value(str(v))
            else:
                link(v, pin(n, nm))
        return pin(n, "ReturnValue", True)

    def int_eq(self, var, value):
        return self.op("EqualEqual_IntInt", self.g(var), value)

    def concat(self, *parts):
        cur = None
        for p in parts:
            n = self.call(S + "Concat_StrStr")
            if cur is not None:
                link(cur, pin(n, "A"))
                tgt = pin(n, "B")
            else:
                tgt = pin(n, "A")
            if isinstance(p, str):
                tgt.set_pin_value(p)
            else:
                link(p, tgt)
            cur = pin(n, "ReturnValue", True)
        return cur

    def now(self):
        return pin(self.call(GS + "GetTimeSeconds"), "ReturnValue", True)

    def hud(self):
        """GetPlayerController -> GetHUD -> Cast to BP_GameHUD. Возвращает (узел-каст, пин HUD)."""
        pc = self.call(GS + "GetPlayerController")
        gh = self.call("/Script/Engine.PlayerController.GetHUD")
        link(pin(pc, "ReturnValue", True), B.find_self_pin(gh))
        cast = self.named(self.find_name("CastToBP_GameHUD"))
        ins = B.list_all_pins(cast, unreal.EdGraphPinDirection.EGPD_INPUT)
        obj_in = [p for p in ins if str(p.get_pin_name()) == "Object"][0]
        link(pin(gh, "ReturnValue", True), obj_in)
        outs = B.list_all_pins(cast, unreal.EdGraphPinDirection.EGPD_OUTPUT)
        as_pin = [p for p in outs if str(p.get_pin_name()).startswith("As")][0]
        return cast, as_pin

    def hud_set(self, hud_pin, var, value=None, src=None):
        return self.setv(var, value=value, src=src, target=hud_pin, cls_path=HUD_CLASS_PATH)

    def hud_until(self, hud_pin, var, seconds):
        t = self.op("Add_DoubleDouble", self.now(), seconds)
        return self.hud_set(hud_pin, var, src=t)
