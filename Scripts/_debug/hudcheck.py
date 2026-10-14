import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
h = pc.get_hud()
gm = unreal.GameplayStatics.get_game_mode(w)
out = open("D:/UOT/Barbarians/Saved/hudcheck.txt", "w")
out.write("hud=%s gm=%s pawn=%s\n" % (h.get_class().get_name() if h else None, gm.get_class().get_name(), unreal.GameplayStatics.get_player_pawn(w,0).get_class().get_name()))
if h:
    for v in ("HintText", "HintUntil", "QuestText", "QuestUntil", "Loading"):
        try: out.write("%s=%s\n" % (v, h.get_editor_property(v)))
        except Exception as e: out.write("%s ERR %s\n" % (v, e))
out.write("time=%s\n" % unreal.GameplayStatics.get_time_seconds(w))
out.write("showhud=%s\n" % (h.get_editor_property("show_hud") if h else None))
out.close()
