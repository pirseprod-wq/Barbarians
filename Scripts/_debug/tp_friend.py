import unreal, math
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
acts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
fr = [a for a in acts if "BP_Friend" in a.get_class().get_name()][0]
p = unreal.GameplayStatics.get_player_pawn(w, 0)
fwd = fr.get_actor_forward_vector()
loc = fr.get_actor_location() + fwd * 150 + unreal.Vector(0, 0, 100)
p.set_actor_location(loc, False, True)
d = fr.get_actor_location() - loc
pc = unreal.GameplayStatics.get_player_controller(w, 0)
pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-5, yaw=math.degrees(math.atan2(d.y, d.x))))
