# -*- coding: utf-8 -*-
"""
Barbarians: ночное село, черновая сборка (greybox).

Запуск в редакторе Unreal:
  Tools -> Execute Python Script...  -> выбрать этот файл
  или в Output Log (поле Cmd):  py "D:/UOT/Barbarians/Scripts/build_village_night.py"

Перед запуском сохраните открытый уровень (Ctrl+Shift+S).
Скрипт можно запускать повторно: старая заготовка села удаляется и строится заново.
Чтобы получить другую планировку, поменяйте SEED.
"""
import math
import random
import unreal

LEVEL_PATH = "/Game/_Game/Maps/L_Village_Night"
TEMPLATE = "/Engine/Maps/Templates/OpenWorld"
FOLDER = "Village_Greybox"
SEED = 17

HUT_COUNT = 13          # обычные мазанки
LONGHOUSE_COUNT = 2     # длинные дома (люди и скот под одной крышей)
VILLAGE_LENGTH_M = 90   # длина улицы
ROOF_PITCH = 45.0       # уклон соломенной крыши, градусы

U = 100.0  # 1 метр в сантиметрах Unreal

def log(m):
    unreal.log("[Village] " + m)

def warn(m):
    unreal.log_warning("[Village] " + m)

level_sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor_sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
CYLINDER = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
CONE = unreal.load_asset("/Engine/BasicShapes/Cone.Cone")

SPAWNED = []


def safe(label, fn):
    try:
        fn()
        log(label + ": ok")
    except Exception as e:
        warn("{}: не получилось ({})".format(label, e))


# ---------------------------------------------------------------- уровень
def open_or_create_level():
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        level_sub.load_level(LEVEL_PATH)
        log("уровень уже существует, открыт")
        return
    ok = False
    try:
        ok = level_sub.new_level_from_template(LEVEL_PATH, TEMPLATE)
    except Exception as e:
        warn("LevelEditorSubsystem: " + str(e))
    if not ok:
        try:
            ok = unreal.EditorLevelLibrary.new_level_from_template(LEVEL_PATH, TEMPLATE)
        except Exception as e:
            warn("EditorLevelLibrary: " + str(e))
    if not ok:
        raise RuntimeError(
            "Не удалось создать уровень из шаблона Open World. Создайте его вручную "
            "(File -> New Level -> Open World), сохраните как _Game/Maps/L_Village_Night "
            "и запустите скрипт ещё раз.")
    log("создан уровень " + LEVEL_PATH)


def all_actors():
    return actor_sub.get_all_level_actors()


def find(cls):
    return [a for a in all_actors() if isinstance(a, cls)]


def cleanup():
    n = 0
    for a in all_actors():
        folder = str(a.get_folder_path())
        label = a.get_actor_label()
        if folder.startswith(FOLDER) or label in ("PPV_NightExposure", "PS_Village"):
            actor_sub.destroy_actor(a)
            n += 1
    if n:
        log("удалена старая заготовка: {} объектов".format(n))


# ---------------------------------------------------------------- ночь
def setup_moon():
    for a in find(unreal.DirectionalLight):
        a.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=-45.0, yaw=35.0), False)
        c = a.get_component_by_class(unreal.DirectionalLightComponent)
        c.set_editor_property("intensity", 0.5)
        c.set_light_color(unreal.LinearColor(0.6, 0.7, 1.0, 1.0))
        a.set_actor_label("Moon_DirectionalLight")


def setup_skylight():
    for a in find(unreal.SkyLight):
        a.get_component_by_class(unreal.SkyLightComponent).set_intensity(0.4)


def setup_clouds():
    acts = find(unreal.VolumetricCloud)
    if not acts:
        raise RuntimeError("VolumetricCloud не найден")
    for a in acts:
        c = a.get_component_by_class(unreal.VolumetricCloudComponent)
        c.set_layer_bottom_altitude(1.0)
        c.set_layer_height(6.0)


def setup_fog():
    for a in find(unreal.ExponentialHeightFog):
        c = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
        c.set_fog_density(0.03)
        try:
            c.set_fog_inscattering_color(unreal.LinearColor(0.05, 0.06, 0.09, 1.0))
        except Exception:
            pass
        c.set_volumetric_fog(True)


def setup_exposure():
    ppv = actor_sub.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
    ppv.set_actor_label("PPV_NightExposure")
    ppv.set_editor_property("unbound", True)
    s = ppv.get_editor_property("settings")
    s.set_editor_property("override_auto_exposure_method", True)
    s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    s.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
    s.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
    s.set_editor_property("override_auto_exposure_bias", True)
    s.set_editor_property("auto_exposure_bias", 1.0)
    ppv.set_editor_property("settings", s)


# ---------------------------------------------------------------- земля
WORLD = None
DEFAULT_Z = 0.0


def init_ground():
    global WORLD, DEFAULT_Z
    WORLD = editor_sub.get_editor_world()
    lands = find(unreal.LandscapeProxy)
    if lands:
        origin, extent = lands[0].get_actor_bounds(False)
        DEFAULT_Z = origin.z
        return origin.x, origin.y
    return 0.0, 0.0


def ground_z(x, y):
    try:
        res = unreal.SystemLibrary.line_trace_single(
            WORLD, unreal.Vector(x, y, 200000.0), unreal.Vector(x, y, -200000.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, SPAWNED,
            unreal.DrawDebugTrace.NONE, True)
        hit = res[0] if isinstance(res, tuple) else res
        if hit is not None:
            t = hit.to_tuple()
            if t[0]:
                return t[4].z
    except Exception:
        pass
    return DEFAULT_Z


# ---------------------------------------------------------------- геометрия
def to_world(cx, cy, cz, yaw, lx, ly, lz):
    r = math.radians(yaw)
    return unreal.Vector(cx + lx * math.cos(r) - ly * math.sin(r),
                         cy + lx * math.sin(r) + ly * math.cos(r),
                         cz + lz)


def spawn(mesh, loc, rot, scale_m, label, folder):
    a = actor_sub.spawn_actor_from_object(mesh, loc, rot)
    a.set_actor_scale3d(unreal.Vector(*scale_m))
    a.set_actor_label(label)
    a.set_folder_path(folder)
    SPAWNED.append(a)
    return a


def build_house(name, cx, cy, gz, yaw, L, W, H):
    folder = "{}/Houses/{}".format(FOLDER, name)
    a = math.radians(ROOF_PITCH)
    # стены (на 30 см утоплены в землю, чтобы не было щелей на склоне)
    spawn(CUBE, to_world(cx, cy, gz, yaw, 0, 0, (H * U - 30) / 2),
          unreal.Rotator(roll=0, pitch=0, yaw=yaw), (L, W, H + 0.3), name + "_Walls", folder)
    # фронтоны: ромб, повёрнутый на 45 градусов; нижняя половина прячется в стенах
    side = W / math.sqrt(2)
    for sx in (1, -1):
        spawn(CUBE, to_world(cx, cy, gz, yaw, sx * (L / 2 - 0.1) * U, 0, H * U),
              unreal.Rotator(roll=45, pitch=0, yaw=yaw), (0.2, side, side),
              "{}_Gable{}".format(name, "F" if sx > 0 else "B"), folder)
    # два ската крыши
    eave = 0.6                      # свес по бокам, м
    gable_over = 0.5                # свес над фронтонами, м
    half_span = W / 2 + eave
    slope_len = half_span / math.cos(a) + 0.15
    ridge = H * U + (W / 2) * U * math.tan(a)
    low = ridge - half_span * U * math.tan(a)
    zc = (ridge + low) / 2 + 12
    for s in (1, -1):
        loc = to_world(cx, cy, gz, yaw, 0, s * half_span * U / 2, zc)
        roll = -s * ROOF_PITCH
        slab = spawn(CUBE, loc, unreal.Rotator(roll=roll, pitch=0, yaw=yaw),
                     (L + 2 * gable_over, slope_len, 0.25),
                     "{}_Roof{}".format(name, "L" if s > 0 else "R"), folder)
        # самопроверка: внешний край ската должен быть ниже центра, иначе переворачиваем
        try:
            tip = slab.get_actor_transform().transform_location(unreal.Vector(0, s * 50, 0))
            if tip.z > loc.z:
                slab.set_actor_rotation(unreal.Rotator(roll=-roll, pitch=0, yaw=yaw), False)
        except Exception:
            pass
    # дверь: смотрит на улицу (локальная сторона -Y)
    spawn(CUBE, to_world(cx, cy, gz, yaw, 0, -(W / 2) * U - 5, 118),
          unreal.Rotator(roll=0, pitch=0, yaw=yaw), (1.5, 0.12, 2.35), name + "_Door", folder)


def build_fence(name, cx, cy, yaw, L, W):
    folder = "{}/Fences".format(FOLDER)
    back = W / 2 + 7.0
    near = W / 2 + 1.0
    half_x = L / 2 + 2.0
    segs = [
        (0, back, 2 * half_x, 0),
        (half_x, (near + back) / 2, back - near, 90),
        (-half_x, (near + back) / 2, back - near, 90),
    ]
    for i, (lx, ly, length, extra_yaw) in enumerate(segs):
        p = to_world(cx, cy, 0, yaw, lx * U, ly * U, 0)
        gz = ground_z(p.x, p.y)
        p.z = gz + 50
        spawn(CUBE, p, unreal.Rotator(roll=0, pitch=0, yaw=yaw + extra_yaw),
              (length, 0.12, 1.2), "{}_Seg{}".format(name, i), folder)


def build_haystack(name, x, y):
    folder = "{}/Props".format(FOLDER)
    gz = ground_z(x, y)
    spawn(CYLINDER, unreal.Vector(x, y, gz + 70), unreal.Rotator(), (2.4, 2.4, 1.6), name + "_Base", folder)
    spawn(CONE, unreal.Vector(x, y, gz + 220), unreal.Rotator(), (2.7, 2.7, 1.6), name + "_Top", folder)


def build_well(x, y):
    folder = "{}/Props".format(FOLDER)
    gz = ground_z(x, y)
    spawn(CYLINDER, unreal.Vector(x, y, gz + 35), unreal.Rotator(), (1.4, 1.4, 0.9), "Well_Ring", folder)
    for s in (1, -1):
        spawn(CUBE, unreal.Vector(x + s * 80, y, gz + 100), unreal.Rotator(), (0.15, 0.15, 2.0),
              "Well_Post{}".format("A" if s > 0 else "B"), folder)
    spawn(CUBE, unreal.Vector(x, y, gz + 195), unreal.Rotator(), (1.9, 0.12, 0.12), "Well_Beam", folder)


# ---------------------------------------------------------------- планировка
def street_y(x):
    return 600.0 * math.sin(x / 2500.0)


def street_yaw(x):
    dy = 600.0 / 2500.0 * math.cos(x / 2500.0)
    return math.degrees(math.atan2(dy, 1.0))


def plan_houses(vx, vy):
    rnd = random.Random(SEED)
    half = VILLAGE_LENGTH_M * U / 2
    kinds = ["Longhouse"] * LONGHOUSE_COUNT + ["Hut"] * HUT_COUNT
    placed = []
    for kind in kinds:
        if kind == "Longhouse":
            L, W, H = rnd.uniform(13, 15), 5.5, 3.0
        else:
            L, W, H = rnd.uniform(5.5, 7.5), rnd.uniform(4.0, 5.0), rnd.uniform(2.8, 3.2)
        radius = max(L, W) * U / 2
        for _ in range(500):
            x = rnd.uniform(-half, half)
            side = rnd.choice((1, -1))
            off = rnd.uniform(800, 1400) + W * U / 2
            y = street_y(x) + side * off
            if all(math.hypot(x - px, y - py) > radius + pr + 400 for px, py, pr, *_ in placed):
                yaw = street_yaw(x) + (0 if side > 0 else 180) + rnd.uniform(-12, 12)
                placed.append((x, y, radius, kind, L, W, H, yaw))
                break
        else:
            warn("не хватило места для дома " + kind)
    return [(vx + x, vy + y, r, k, L, W, H, yaw) for x, y, r, k, L, W, H, yaw in placed], rnd


def build_village():
    vx, vy = init_ground()
    houses, rnd = plan_houses(vx, vy)
    counts = {}
    built = []
    for x, y, r, kind, L, W, H, yaw in houses:
        counts[kind] = counts.get(kind, 0) + 1
        name = "{}_{:02d}".format(kind, counts[kind])
        gz = ground_z(x, y)
        build_house(name, x, y, gz, yaw, L, W, H)
        built.append((name, x, y, yaw, L, W))
    # плетни за частью дворов, стога
    for i, (name, x, y, yaw, L, W) in enumerate(rnd.sample(built, min(7, len(built)))):
        build_fence("Fence_" + name, x, y, yaw, L, W)
    for i, (name, x, y, yaw, L, W) in enumerate(rnd.sample(built, min(4, len(built)))):
        p = to_world(x, y, 0, yaw, rnd.uniform(-2, 2) * U, (W / 2 + 4.5) * U, 0)
        build_haystack("Haystack_{:02d}".format(i + 1), p.x, p.y)
    # колодец посреди улицы
    build_well(vx, vy + street_y(0))
    # точка появления игрока на въезде в село
    sx = -(VILLAGE_LENGTH_M / 2 + 15) * U
    px, py = vx + sx, vy + street_y(sx)
    ps = actor_sub.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(px, py, ground_z(px, py) + 120),
        unreal.Rotator(roll=0, pitch=0, yaw=street_yaw(sx)))
    ps.set_actor_label("PS_Village")
    # камера редактора над въездом, смотрит на село
    try:
        editor_sub.set_level_viewport_camera_info(
            unreal.Vector(px - 2500, py, ground_z(px, py) + 2500),
            unreal.Rotator(roll=0, pitch=-30, yaw=0))
    except Exception:
        pass
    log("построено домов: {}".format(len(built)))


# ---------------------------------------------------------------- запуск
def main():
    open_or_create_level()
    cleanup()
    safe("луна", setup_moon)
    safe("небесный свет", setup_skylight)
    safe("тучи", setup_clouds)
    safe("туман", setup_fog)
    safe("ночная экспозиция", setup_exposure)
    safe("село", build_village)
    # освещение шаблона не грузится в игре: пересоздаём его и чиним режим игры
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    for extra in ("night_lighting.py", "fix_village_world.py", "weather_rain.py", "ui_hud.py", "brand_house.py"):
        safe(extra, lambda f=extra: exec(open(os.path.join(here, f), encoding="utf-8").read(), {}))
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        log("всё сохранено")
    except Exception as e:
        warn("сохраните вручную (Ctrl+Shift+S): " + str(e))
    log("готово")


main()
