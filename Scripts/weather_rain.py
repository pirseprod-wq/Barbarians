# -*- coding: utf-8 -*-
"""
Barbarians: дождливая ночь для L_Village_Night.
 - дождь: два полупрозрачных цилиндра со струями вокруг игрока (ближний и дальний слой);
 - мокрые поверхности: глиняные стены, тёмная солома, мокрое дерево, грязь с лужами;
 - звук дождя (петля, без направления);
 - сцена темнее и мрачнее.
Запуск: py "D:/UOT/Barbarians/Scripts/weather_rain.py"  (можно повторять)
"""
import math
import unreal

ROOT = "D:/UOT/Barbarians"
SRC = ROOT + "/SourceAssets/Weather"
TEX_DIR = "/Game/_Game/Textures/Weather"
MAT_DIR = "/Game/_Game/Materials/Weather"
SURF_DIR = "/Game/_Game/Materials/Greybox"
AUDIO_DIR = "/Game/_Game/Audio/Ambience"
CHAR_DIR = "/Game/_Game/Blueprints/Characters"
CORE_DIR = "/Game/_Game/Blueprints/Core"

at = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor_sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")


LOGFILE = ROOT + "/Saved/weather_log.txt"
open(LOGFILE, "w", encoding="utf-8").close()


def _file(m):
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(m + "\n")


def log(m):
    unreal.log("[Weather] " + m)
    _file(m)


def warn(m):
    unreal.log_warning("[Weather] " + m)
    _file("WARN " + m)


def safe(label, fn):
    try:
        r = fn()
        log(label + ": ok")
        return r
    except Exception as e:
        warn("{}: не получилось ({})".format(label, e))


def get_or_create(path, name, cls, factory):
    full = path + "/" + name
    if eal.does_asset_exist(full):
        return unreal.load_asset(full)
    return at.create_asset(name, path, cls, factory)


def import_file(src, dest_dir, name):
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", src)
    t.set_editor_property("destination_path", dest_dir)
    t.set_editor_property("destination_name", name)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    at.import_asset_tasks([t])
    a = unreal.load_asset(dest_dir + "/" + name)
    if a is None:
        raise RuntimeError("не импортировался " + src)
    return a


class G:
    """Маленький помощник для сборки графа материала."""
    def __init__(self, mat):
        self.mat = mat

    def e(self, cls, x, y, **props):
        n = mel.create_material_expression(self.mat, cls, x, y)
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def c(self, a, b, inp="", out=""):
        mel.connect_material_expressions(a, out, b, inp)

    def scalar(self, name, val, x, y):
        return self.e(unreal.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=val)

    def vector(self, name, rgb, x, y):
        return self.e(unreal.MaterialExpressionVectorParameter, x, y, parameter_name=name,
                      default_value=unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))

    def out(self, node, prop, output=""):
        mel.connect_material_property(node, output, prop)


def new_material(path, name):
    mat = get_or_create(path, name, unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    return mat, G(mat)


def finish(mat):
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)


def make_mi(path, name, parent, scalars=None, vectors=None):
    m = get_or_create(path, name, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(m, parent)
    for k, v in (scalars or {}).items():
        mel.set_material_instance_scalar_parameter_value(m, k, v)
    for k, v in (vectors or {}).items():
        mel.set_material_instance_vector_parameter_value(m, k, unreal.LinearColor(v[0], v[1], v[2], 1.0))
    mel.update_material_instance(m)
    eal.save_loaded_asset(m)
    return m


# ------------------------------------------------------------------ дождь
def weather_mpc():
    """MPC_Weather.RainAmount: 1 - дождь виден, 0 - в помещении (меняют двери)."""
    path = MAT_DIR + "/MPC_Weather"
    if eal.does_asset_exist(path):
        return unreal.load_asset(path)
    mpc = at.create_asset("MPC_Weather", MAT_DIR, unreal.MaterialParameterCollection,
                          unreal.MaterialParameterCollectionFactoryNew())
    p = unreal.CollectionScalarParameter()
    p.set_editor_property("parameter_name", "RainAmount")
    p.set_editor_property("default_value", 1.0)
    mpc.set_editor_property("scalar_parameters", [p])
    eal.save_loaded_asset(mpc)
    return mpc


def build_rain_material(tex):
    mat, g = new_material(MAT_DIR, "M_Rain")
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)

    # U: угол вокруг центра цилиндра (не зависит от развёртки модели)
    wp = g.e(unreal.MaterialExpressionWorldPosition, -1800, 0)
    op = g.e(unreal.MaterialExpressionObjectPositionWS, -1800, 200)
    rel = g.e(unreal.MaterialExpressionSubtract, -1600, 100)
    g.c(wp, rel, "A"); g.c(op, rel, "B")
    mx = g.e(unreal.MaterialExpressionComponentMask, -1400, 0, r=True, g=False, b=False, a=False)
    my = g.e(unreal.MaterialExpressionComponentMask, -1400, 150, r=False, g=True, b=False, a=False)
    g.c(rel, mx); g.c(rel, my)
    ang = g.e(unreal.MaterialExpressionArctangent2, -1200, 80)
    g.c(my, ang, "Y"); g.c(mx, ang, "X")
    tiles_u = g.scalar("TilesU", 18.0, -1200, 250)
    u1 = g.e(unreal.MaterialExpressionMultiply, -1000, 120)
    g.c(ang, u1, "A"); g.c(tiles_u, u1, "B")
    u = g.e(unreal.MaterialExpressionMultiply, -850, 120, const_b=1.0 / (2.0 * math.pi))
    g.c(u1, u, "A")

    # V: высота в мире + падение во времени (струи летят вниз)
    mz = g.e(unreal.MaterialExpressionComponentMask, -1400, 400, r=False, g=False, b=True, a=False)
    g.c(wp, mz)
    tile_h = g.scalar("TileHeight", 250.0, -1400, 520)
    zv = g.e(unreal.MaterialExpressionDivide, -1200, 420)
    g.c(mz, zv, "A"); g.c(tile_h, zv, "B")
    t = g.e(unreal.MaterialExpressionTime, -1400, 640, override_period=True, period=10.0)
    speed = g.scalar("SpeedTiles", 4.0, -1400, 740)
    tv = g.e(unreal.MaterialExpressionMultiply, -1200, 680)
    g.c(t, tv, "A"); g.c(speed, tv, "B")
    vsum = g.e(unreal.MaterialExpressionAdd, -1000, 500)
    g.c(zv, vsum, "A"); g.c(tv, vsum, "B")
    v = g.e(unreal.MaterialExpressionMultiply, -850, 500, const_b=-1.0)
    g.c(vsum, v, "A")

    uv = g.e(unreal.MaterialExpressionAppendVector, -650, 300)
    g.c(u, uv, "A"); g.c(v, uv, "B")
    ts = g.e(unreal.MaterialExpressionTextureSample, -450, 300, texture=tex)
    g.c(uv, ts, "UVs")

    # прячем крышки цилиндра: прозрачность только на боковых стенках
    vn = g.e(unreal.MaterialExpressionVertexNormalWS, -650, 650)
    nz = g.e(unreal.MaterialExpressionComponentMask, -450, 650, r=False, g=False, b=True, a=False)
    g.c(vn, nz)
    nabs = g.e(unreal.MaterialExpressionAbs, -300, 650)
    g.c(nz, nabs)
    side = g.e(unreal.MaterialExpressionOneMinus, -150, 650)
    g.c(nabs, side)

    opacity = g.scalar("Opacity", 0.35, -300, 480)
    o1 = g.e(unreal.MaterialExpressionMultiply, -100, 380)
    g.c(ts, o1, "A", "R"); g.c(opacity, o1, "B")
    o2 = g.e(unreal.MaterialExpressionMultiply, 80, 450)
    g.c(o1, o2, "A"); g.c(side, o2, "B")
    # укрытие: если над точкой дождя есть крыша/навес/крона (глобальное поле расстояний), дождя нет
    cover = None
    for i, k in enumerate((80.0, 180.0, 300.0, 450.0, 650.0)):
        off = g.e(unreal.MaterialExpressionConstant3Vector, -200, 820 + i * 120,
                  constant=unreal.LinearColor(0, 0, k, 0))
        pos = g.e(unreal.MaterialExpressionAdd, 0, 820 + i * 120)
        g.c(wp, pos, "A"); g.c(off, pos, "B")
        dist = g.e(unreal.MaterialExpressionDistanceToNearestSurface, 200, 820 + i * 120)
        g.c(pos, dist, "Position")
        if cover is None:
            cover = dist
        else:
            mn = g.e(unreal.MaterialExpressionMin, 400, 820 + i * 120)
            g.c(cover, mn, "A"); g.c(dist, mn, "B")
            cover = mn
    c1 = g.e(unreal.MaterialExpressionSubtract, 600, 900, const_b=40.0)
    g.c(cover, c1, "A")
    c2 = g.e(unreal.MaterialExpressionMultiply, 750, 900, const_b=1.0 / 60.0)
    g.c(c1, c2, "A")
    open_sky = g.e(unreal.MaterialExpressionSaturate, 900, 900)
    g.c(c2, open_sky)
    o3 = g.e(unreal.MaterialExpressionMultiply, 1050, 500)
    g.c(o2, o3, "A"); g.c(open_sky, o3, "B")
    amt = g.e(unreal.MaterialExpressionCollectionParameter, 1050, 700,
              collection=weather_mpc(), parameter_name="RainAmount")
    o4 = g.e(unreal.MaterialExpressionMultiply, 1200, 550)
    g.c(o3, o4, "A"); g.c(amt, o4, "B")
    g.out(o4, unreal.MaterialProperty.MP_OPACITY)

    col = g.vector("Color", (0.6, 0.7, 0.85), -300, 100)
    bright = g.scalar("Brightness", 0.15, -300, 220)
    em = g.e(unreal.MaterialExpressionMultiply, -100, 150)
    g.c(col, em, "A"); g.c(bright, em, "B")
    g.out(em, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    finish(mat)
    return mat


def build_rain():
    tex = import_file(SRC + "/T_RainStreaks.png", TEX_DIR, "T_RainStreaks")
    rain = build_rain_material(tex)
    near = make_mi(MAT_DIR, "MI_Rain_Near", rain,
                   {"TilesU": 18.0, "TileHeight": 250.0, "SpeedTiles": 4.0, "Opacity": 0.45, "Brightness": 0.25})
    far = make_mi(MAT_DIR, "MI_Rain_Far", rain,
                  {"TilesU": 45.0, "TileHeight": 500.0, "SpeedTiles": 2.0, "Opacity": 0.3, "Brightness": 0.18})
    return near, far


# ------------------------------------------------------------------ мокрые поверхности
def build_surfaces():
    mat, g = new_material(SURF_DIR, "M_Greybox_Wet")
    bc = g.vector("BaseColor", (0.3, 0.3, 0.3), -400, 0)
    rough = g.scalar("Roughness", 0.4, -400, 200)
    g.out(bc, unreal.MaterialProperty.MP_BASE_COLOR)
    g.out(rough, unreal.MaterialProperty.MP_ROUGHNESS)
    finish(mat)
    mis = {
        "clay": make_mi(SURF_DIR, "MI_Wet_Clay", mat, {"Roughness": 0.35}, {"BaseColor": (0.26, 0.22, 0.17)}),
        "thatch": make_mi(SURF_DIR, "MI_Wet_Thatch", mat, {"Roughness": 0.55}, {"BaseColor": (0.07, 0.06, 0.045)}),
        "wood": make_mi(SURF_DIR, "MI_Wet_Wood", mat, {"Roughness": 0.4}, {"BaseColor": (0.12, 0.085, 0.06)}),
        "hay": make_mi(SURF_DIR, "MI_Wet_Hay", mat, {"Roughness": 0.6}, {"BaseColor": (0.22, 0.18, 0.09)}),
    }

    mud, g = new_material(SURF_DIR, "M_WetMud")
    noise = g.e(unreal.MaterialExpressionNoise, -900, 200, scale=0.004, levels=4,
                output_min=0.0, output_max=1.0)
    sub = g.e(unreal.MaterialExpressionSubtract, -700, 200, const_b=0.62)
    g.c(noise, sub, "A")
    mul = g.e(unreal.MaterialExpressionMultiply, -550, 200, const_b=8.0)
    g.c(sub, mul, "A")
    puddle = g.e(unreal.MaterialExpressionSaturate, -400, 200)
    g.c(mul, puddle)
    c_mud = g.e(unreal.MaterialExpressionConstant3Vector, -400, -50,
                constant=unreal.LinearColor(0.075, 0.058, 0.042, 1))
    c_wet = g.e(unreal.MaterialExpressionConstant3Vector, -400, 50,
                constant=unreal.LinearColor(0.025, 0.025, 0.03, 1))
    base = g.e(unreal.MaterialExpressionLinearInterpolate, -200, 0)
    g.c(c_mud, base, "A"); g.c(c_wet, base, "B"); g.c(puddle, base, "Alpha")
    rgh = g.e(unreal.MaterialExpressionLinearInterpolate, -200, 250, const_a=0.6, const_b=0.04)
    g.c(puddle, rgh, "Alpha")
    g.out(base, unreal.MaterialProperty.MP_BASE_COLOR)
    g.out(rgh, unreal.MaterialProperty.MP_ROUGHNESS)
    finish(mud)
    return mis, mud


def apply_surfaces(mis, mud):
    n = 0
    for a in actor_sub.get_all_level_actors():
        if isinstance(a, unreal.Landscape):
            if not eal.does_asset_exist("/Game/_Game/Materials/Terrain/M_Landscape_Auto"):
                a.modify()
                a.set_editor_property("landscape_material", mud)
            continue
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        folder = str(a.get_folder_path())
        if not folder.startswith("Village_Greybox") or folder.startswith("Village_Greybox/HeroHouse"):
            continue
        label = a.get_actor_label()
        if "_Roof" in label:
            mi = mis["thatch"]
        elif "_Walls" in label or "_Gable" in label:
            mi = mis["clay"]
        elif "Haystack" in label:
            mi = mis["hay"]
        else:
            mi = mis["wood"]
        a.modify()
        a.static_mesh_component.set_material(0, mi)
        n += 1
    log("материалы назначены: {}".format(n))


# ------------------------------------------------------------------ звук
def build_sound():
    wave = import_file(SRC + "/SW_Rain_Loop.wav", AUDIO_DIR, "SW_Rain_Loop")
    wave.set_editor_property("looping", True)
    eal.save_loaded_asset(wave)
    for a in actor_sub.get_all_level_actors():
        if a.get_actor_label() == "Amb_Rain":
            actor_sub.destroy_actor(a)
    amb = actor_sub.spawn_actor_from_class(unreal.AmbientSound, unreal.Vector(0, 0, 200))
    amb.set_actor_label("Amb_Rain")
    amb.set_folder_path("Weather")
    try:
        amb.set_editor_property("is_spatially_loaded", False)
    except Exception:
        amb.set_is_spatially_loaded(False)
    ac = amb.get_component_by_class(unreal.AudioComponent)
    ac.set_sound(wave)
    ac.set_editor_property("allow_spatialization", False)
    ac.set_editor_property("volume_multiplier", 0.7)


# ------------------------------------------------------------------ игрок с дождём
def make_child_bp(path, name, parent_cls):
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", parent_cls)
    return at.create_asset(name, path, unreal.Blueprint, f)


def add_rain_cylinder(bp, name, mi, radius_m, height_m):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    root = sds.k2_gather_subobject_data_for_blueprint(bp)[0]
    params = unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.StaticMeshComponent,
                                          blueprint_context=bp)
    res = sds.add_new_subobject(params)
    handle = res[0] if isinstance(res, tuple) else res
    sds.rename_subobject(handle, unreal.Text(name))
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
    comp.set_editor_property("static_mesh", CYL)
    comp.set_editor_property("override_materials", [mi])
    comp.set_editor_property("relative_scale3d", unreal.Vector(radius_m * 2, radius_m * 2, height_m))
    comp.set_editor_property("relative_location", unreal.Vector(0, 0, height_m * 100 / 2 - 300))
    comp.set_editor_property("cast_shadow", False)
    try:
        comp.set_collision_profile_name("NoCollision")
    except Exception:
        pass


def build_player(near, far):
    char_cls = unreal.load_class(None, "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter.BP_FirstPersonCharacter_C")
    gm_cls = unreal.load_class(None, "/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode.BP_FirstPersonGameMode_C")
    for full in (CORE_DIR + "/BP_VillageGameMode", CHAR_DIR + "/BP_VillagePlayer"):
        if eal.does_asset_exist(full):
            eal.delete_asset(full)
    player = make_child_bp(CHAR_DIR, "BP_VillagePlayer", char_cls)
    add_rain_cylinder(player, "RainNear", near, 4.0, 25.0)
    add_rain_cylinder(player, "RainFar", far, 11.0, 30.0)
    unreal.BlueprintEditorLibrary.compile_blueprint(player)
    eal.save_loaded_asset(player)

    gm = make_child_bp(CORE_DIR, "BP_VillageGameMode", gm_cls)
    unreal.BlueprintEditorLibrary.compile_blueprint(gm)
    cdo = unreal.get_default_object(gm.generated_class())
    cdo.set_editor_property("default_pawn_class", player.generated_class())
    if eal.does_asset_exist(CORE_DIR + "/BP_GameHUD"):
        cdo.set_editor_property("hud_class", unreal.load_asset(CORE_DIR + "/BP_GameHUD").generated_class())
    eal.save_loaded_asset(gm)

    ws = editor_sub.get_editor_world().get_world_settings()
    ws.modify()
    ws.set_editor_property("default_game_mode", gm.generated_class())


# ------------------------------------------------------------------ мрачнее
def darker():
    for a in actor_sub.get_all_level_actors():
        if isinstance(a, unreal.DirectionalLight):
            a.modify()
            a.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("intensity", 0.3)
        elif isinstance(a, unreal.SkyLight):
            a.modify()
            a.get_component_by_class(unreal.SkyLightComponent).set_intensity(0.3)
        elif isinstance(a, unreal.ExponentialHeightFog):
            a.modify()
            fc = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
            fc.set_fog_density(0.05)
            try:
                fc.set_fog_inscattering_color(unreal.LinearColor(0.035, 0.04, 0.055, 1.0))
            except Exception:
                pass


def main():
    rain = safe("дождь (материалы)", build_rain)
    surf = safe("мокрые материалы", build_surfaces)
    if surf:
        safe("назначение материалов", lambda: apply_surfaces(*surf))
    safe("звук дождя", build_sound)
    if rain:
        safe("игрок с дождём", lambda: build_player(*rain))
    safe("мрачнее", darker)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("готово")


main()
