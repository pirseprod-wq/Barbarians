import unreal
s = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
A = {a.get_actor_label(): a for a in s.get_all_level_actors()}
f = A["Family_Mother"].get_actor_location()
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
    f + unreal.Vector(80, -330, 150), unreal.Rotator(roll=0, pitch=-22, yaw=100))
for a in s.get_all_level_actors():
    if str(a.get_folder_path()) == "Characters_Preview":
        s.destroy_actor(a)
