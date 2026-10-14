import unreal, collections
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
out = open("D:/UOT/Barbarians/Saved/diag2.txt", "w", encoding="utf-8")
acts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
c = collections.Counter(type(a).__name__ for a in acts)
out.write("world=%s total=%d\n" % (w.get_path_name() if w else None, len(acts)))
for k, v in c.most_common(): out.write("%s %d\n" % (k, v))
pc = unreal.GameplayStatics.get_player_controller(w, 0)
if pc:
    p = pc.get_controlled_pawn()
    out.write("pawn=%s loc=%s\n" % (p.get_name() if p else None, p.get_actor_location() if p else None))
    cam = unreal.GameplayStatics.get_player_camera_manager(w, 0)
    out.write("cam=%s\n" % cam.get_camera_location())
for a in acts:
    if isinstance(a, (unreal.DirectionalLight, unreal.SkyLight, unreal.SkyAtmosphere, unreal.PlayerStart, unreal.PostProcessVolume)):
        out.write("%s %s %s\n" % (type(a).__name__, a.get_actor_label() if hasattr(a,'get_actor_label') else a.get_name(), a.get_actor_location()))
out.close()
