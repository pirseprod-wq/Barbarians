import unreal
out = open("D:/UOT/Barbarians/Saved/probe_umg.txt", "w", encoding="utf-8")
at = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
P = "/Game/_Game/UI/_Probe"
if eal.does_asset_exist(P + "/WBP_Probe"):
    eal.delete_asset(P + "/WBP_Probe")
try:
    f = unreal.WidgetBlueprintFactory()
    f.set_editor_property("parent_class", unreal.UserWidget)
    wb = at.create_asset("WBP_Probe", P, unreal.WidgetBlueprint, f)
    out.write("created %s\n" % wb)
    out.write("wb attrs: %s\n" % [m for m in dir(wb) if "widget" in m.lower() or "tree" in m.lower()])
    try:
        wt = wb.get_editor_property("widget_tree")
        out.write("widget_tree %s\n" % wt)
        out.write("wt attrs: %s\n" % [m for m in dir(wt) if not m.startswith("_")])
    except Exception as e:
        out.write("widget_tree ERR %s\n" % e)
    libs = [n for n in dir(unreal) if "Widget" in n and ("Library" in n or "Editor" in n or "Subsystem" in n)]
    out.write("libs %s\n" % libs)
    for lib in libs:
        c = getattr(unreal, lib)
        out.write("-- %s: %s\n" % (lib, [m for m in dir(c) if not m.startswith("_") and m not in dir(unreal.Object)]))
except Exception as e:
    out.write("ERR %s\n" % e)
out.close()
