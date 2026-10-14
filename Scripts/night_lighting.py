# -*- coding: utf-8 -*-
"""Пересоздаёт ночное освещение L_Village_Night: луна, свет неба, атмосфера, тучи, туман.
Все объекты всегда загружены (не зависят от стриминга World Partition)."""
import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
FOLDER = "Lighting_Night"
KINDS = (unreal.DirectionalLight, unreal.SkyLight, unreal.SkyAtmosphere,
         unreal.VolumetricCloud, unreal.ExponentialHeightFog)

def log(m):
    unreal.log("[Village] " + m)

# убираем старое освещение шаблона
for a in actor_sub.get_all_level_actors():
    if isinstance(a, KINDS):
        log("удалён " + a.get_actor_label())
        actor_sub.destroy_actor(a)

def spawn(cls, label, loc=unreal.Vector(0, 0, 0), rot=unreal.Rotator()):
    a = actor_sub.spawn_actor_from_class(cls, loc, rot)
    a.set_actor_label(label)
    a.set_folder_path(FOLDER)
    try:
        a.set_editor_property("is_spatially_loaded", False)
    except Exception:
        a.set_is_spatially_loaded(False)
    return a

moon = spawn(unreal.DirectionalLight, "Moon_DirectionalLight", unreal.Vector(0, 0, 1000),
             unreal.Rotator(roll=0.0, pitch=-45.0, yaw=35.0))
mc = moon.get_component_by_class(unreal.DirectionalLightComponent)
mc.set_mobility(unreal.ComponentMobility.MOVABLE)
mc.set_editor_property("intensity", 0.5)
mc.set_light_color(unreal.LinearColor(0.6, 0.7, 1.0, 1.0))
mc.set_editor_property("atmosphere_sun_light", True)

spawn(unreal.SkyAtmosphere, "SkyAtmosphere")

sky = spawn(unreal.SkyLight, "SkyLight", unreal.Vector(0, 0, 1200))
sc = sky.get_component_by_class(unreal.SkyLightComponent)
sc.set_mobility(unreal.ComponentMobility.MOVABLE)
sc.set_editor_property("real_time_capture", True)
sc.set_intensity(0.4)

cloud = spawn(unreal.VolumetricCloud, "VolumetricCloud", unreal.Vector(0, 0, 1400))
cc = cloud.get_component_by_class(unreal.VolumetricCloudComponent)
cc.set_layer_bottom_altitude(1.0)
cc.set_layer_height(6.0)
try:
    if cc.get_editor_property("material") is None:
        m = unreal.load_asset("/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst")
        if m:
            cc.set_material(m)
except Exception as e:
    log("материал облаков: " + str(e))

fog = spawn(unreal.ExponentialHeightFog, "ExponentialHeightFog", unreal.Vector(0, 0, 0))
fc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
fc.set_fog_density(0.03)
try:
    fc.set_fog_inscattering_color(unreal.LinearColor(0.05, 0.06, 0.09, 1.0))
except Exception:
    pass
fc.set_volumetric_fog(True)

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
log("ночное освещение пересоздано")
