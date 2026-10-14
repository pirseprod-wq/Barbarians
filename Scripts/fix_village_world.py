# -*- coding: utf-8 -*-
"""Исправления для L_Village_Night: небо и свет всегда загружены, один PlayerStart, режим игры от первого лица."""
import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor_sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

ALWAYS = (unreal.DirectionalLight, unreal.SkyLight, unreal.SkyAtmosphere,
          unreal.VolumetricCloud, unreal.ExponentialHeightFog, unreal.PostProcessVolume)

for a in actor_sub.get_all_level_actors():
    if isinstance(a, ALWAYS):
        a.modify()
        try:
            a.set_editor_property("is_spatially_loaded", False)
        except Exception:
            a.set_is_spatially_loaded(False)
        unreal.log("[Village] always loaded: " + a.get_actor_label())
    elif isinstance(a, unreal.PlayerStart) and a.get_actor_label() != "PS_Village":
        unreal.log("[Village] removed extra player start: " + a.get_actor_label())
        actor_sub.destroy_actor(a)

world = editor_sub.get_editor_world()
gm = unreal.load_class(None, "/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode.BP_FirstPersonGameMode_C")
ws = world.get_world_settings()
ws.modify()
ws.set_editor_property("default_game_mode", gm)
unreal.log("[Village] game mode: " + str(gm))

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log("[Village] fix done")
