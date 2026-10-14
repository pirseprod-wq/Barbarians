import unreal
s = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
P = [a for a in s.get_all_level_actors() if str(a.get_folder_path()) == "Characters_Preview"]
for a in P:
    a.set_actor_scale3d(unreal.Vector(1.85, 1.85, 1.85))
c = P[len(P)//2].get_actor_location()
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(c + unreal.Vector(-650, 0, 120), unreal.Rotator(roll=0, pitch=-3, yaw=0))
