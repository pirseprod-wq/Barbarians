import unreal
out = open("D:/UOT/Barbarians/Saved/probe2.txt", "w")
out.write("BEL: %s\n" % [m for m in dir(unreal.BlueprintEditorLibrary) if not m.startswith("_")])
cands = [n for n in dir(unreal) if any(k in n for k in ("Graph", "K2Node", "Blueprint", "Widget"))]
out.write("names: %s\n" % cands[:400])
out.write("DistanceToNearestSurface: %s\n" % hasattr(unreal, "MaterialExpressionDistanceToNearestSurface"))
out.write("WidgetTree: %s\n" % [m for m in dir(unreal.WidgetBlueprint) if not m.startswith("_")][:80] if hasattr(unreal, "WidgetBlueprint") else "no WB")
out.close()
