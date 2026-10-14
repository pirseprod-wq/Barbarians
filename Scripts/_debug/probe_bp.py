import unreal
out = open("D:/UOT/Barbarians/Saved/probe_bp.txt", "w", encoding="utf-8")
at = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
P = "/Game/_Game/Blueprints/_Temp"
if eal.does_asset_exist(P + "/BP_Probe"):
    eal.delete_asset(P + "/BP_Probe")
f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.Actor)
bp = at.create_asset("BP_Probe", P, unreal.Blueprint, f)
B = unreal.BlueprintEditorLibrary
G = unreal.BlueprintGraphEditor.get_graph_editor(B.find_event_graph(bp))
G.add_member_variable("Lines", B.get_array_type(B.get_basic_type_by_name("text")))
B.compile_blueprint(bp)
names = G.list_available_nodes([])
out.write("available: %d\n" % len(names))
for n in names:
    l = n.lower()
    if any(k in l for k in ("keyboard events|e", "|e\n", "array|get", "array|length", "enhanced", "input key", "inputkey", "print string", "printstring", "|e ", "any key")) or n.endswith("|E"):
        out.write("  " + n + "\n")
def pins(node, label):
    out.write("== %s (%s)\n" % (label, type(node).__name__ if node else None))
    if node:
        for p in B.list_all_pins(node):
            out.write("   %s %s %s\n" % (p.get_pin_direction(), p.get_pin_name(), p.get_pin_type_display_string()))
lines_get = G.add_get_member_variable_node("Lines")
pins(lines_get, "get Lines")
for nm in ("Utilities|Array|Get (a copy)", "Utilities|Array|Get (a ref)", "Utilities|Array|Length", "Development|Print String", "Utilities|String|Print String"):
    try:
        n = G.create_node_from_name(nm, unreal.Vector2D(0, 0), [B.find_result_pin(lines_get)] if "Array" in nm else [])
        pins(n, nm)
    except Exception as e:
        out.write("ERR %s: %s\n" % (nm, e))
ps = G.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
pins(ps, "PrintString")
for fp in ("/Script/Engine.GameplayStatics.GetPlayerController", "/Script/Engine.Actor.EnableInput", "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", "/Script/Engine.KismetTextLibrary.Conv_TextToString", "/Script/Engine.KismetMathLibrary.Less_IntInt"):
    pins(G.add_call_function_node(fp), fp)
out.close()
