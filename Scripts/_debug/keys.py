import unreal
B = unreal.BlueprintEditorLibrary
bp = unreal.load_asset("/Game/_Game/Blueprints/Core/BP_Door")
ed = unreal.BlueprintGraphEditor.get_graph_editor(B.find_event_graph(bp))
names = [n for n in ed.list_available_nodes([]) if "KeyboardEvents|" in n]
open("D:/UOT/Barbarians/Saved/keys.txt", "w", encoding="utf-8").write("\n".join(names))
