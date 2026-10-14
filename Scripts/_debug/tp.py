import unreal, math
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
acts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
A = {a.get_actor_label() if hasattr(a, "get_actor_label") else a.get_name(): a for a in acts}
TARGET = open("D:/UOT/Barbarians/Saved/tp_target.txt").read().strip()
p = unreal.GameplayStatics.get_player_pawn(w, 0)
pc = unreal.GameplayStatics.get_player_controller(w, 0)
t = [a for a in acts if TARGET in a.get_name() or TARGET in a.get_class().get_name()]
if TARGET == "door":
    d = [a for a in acts if "BP_Door" in a.get_class().get_name() and a.get_actor_location().x < 100000][0]
    loc = d.get_actor_location() + d.get_actor_forward_vector() * 120 + unreal.Vector(0, 0, 100)
    yaw = d.get_actor_rotation().yaw + 180
elif TARGET == "exit":
    d = [a for a in acts if "BP_Door" in a.get_class().get_name() and a.get_actor_location().x > 100000][0]
    loc = d.get_actor_location() + d.get_actor_right_vector() * 0 + unreal.Vector(0, 100, 100)
    yaw = -90
elif TARGET == "ulf":
    f = [a for a in acts if "BP_Friend" in a.get_class().get_name()][0]
    loc = f.get_actor_location() + unreal.Vector(150, 0, 100)
    yaw = 180
p.set_actor_location(loc, False, True)
pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=yaw))
