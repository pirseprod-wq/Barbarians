import unreal
OUT=open("D:/UOT/Barbarians/Saved/diag.txt","w",encoding="utf-8")
s = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in s.get_all_level_actors():
    if isinstance(a, (unreal.DirectionalLight, unreal.SkyLight, unreal.SkyAtmosphere, unreal.VolumetricCloud, unreal.ExponentialHeightFog, unreal.PostProcessVolume)) or "Hut_01_Walls" in a.get_actor_label():
        info = [a.get_actor_label(), type(a).__name__, str(a.get_level()), str(a.get_folder_path())]
        for p in ("is_spatially_loaded", "is_editor_only_actor", "editor_only", "hidden"):
            try: info.append("{}={}".format(p, a.get_editor_property(p)))
            except Exception as e: info.append(p + "=?")
        try: info.append("dl=" + str([str(x) for x in a.get_data_layer_assets()]))
        except Exception as e: info.append("dl=?" + str(e)[:60])
        try: info.append("outer=" + a.get_outer().get_path_name())
        except Exception: pass
        unreal.log("[Diag] " + " | ".join(info)); OUT.write(" | ".join(info)+"\n")
OUT.close()
