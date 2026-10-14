import unreal
out = open("D:/UOT/Barbarians/Saved/gmcheck.txt", "w")
gm = unreal.load_asset("/Game/_Game/Blueprints/Core/BP_VillageGameMode")
cdo = unreal.get_default_object(gm.generated_class())
out.write("asset cdo hud=%s pawn=%s\n" % (cdo.get_editor_property("hud_class"), cdo.get_editor_property("default_pawn_class")))
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if w:
    g = unreal.GameplayStatics.get_game_mode(w)
    out.write("pie gm class=%s path=%s hud=%s\n" % (g.get_class().get_name(), g.get_class().get_path_name(), g.get_editor_property("hud_class")))
    pc = unreal.GameplayStatics.get_player_controller(w, 0)
    out.write("pc=%s\n" % pc.get_class().get_path_name())
out.close()
