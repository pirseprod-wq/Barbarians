import unreal, math, sys
s = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
A = {a.get_actor_label(): a for a in s.get_all_level_actors()}
f = A["NPC_Friend"].get_actor_location()
t = A[TARGET].get_actor_location() if "TARGET" in dir() else A["Family_Father"].get_actor_location()
fwd = A["NPC_Friend"].get_actor_forward_vector()
cam = unreal.Vector(f.x + fwd.x * 120, f.y + fwd.y * 120, f.z + 165)
d = t - cam
yaw = math.degrees(math.atan2(d.y, d.x)); pitch = math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(cam, unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
