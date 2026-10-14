import unreal, math
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
acts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
fa = [a for a in acts if a.get_name().startswith("SkeletalMeshActor") or "Family" in a.get_name()]
p = unreal.GameplayStatics.get_player_pawn(w, 0)
pc = unreal.GameplayStatics.get_player_controller(w, 0)
door = [a for a in acts if "BP_Door" in a.get_class().get_name() and a.get_actor_location().x > 100000][0]
# спальня: x≈-7.5 м от центра интерьера, лежанка у задней стены (+Y)
c = unreal.Vector(160000 - 600, 0, 120)
p.set_actor_location(c, False, True)
pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-20, yaw=120))
