import unreal
out = open("D:/UOT/Barbarians/Saved/probe_ik.txt", "w", encoding="utf-8")
eal = unreal.EditorAssetLibrary
for d in ("Brund", "Mother", "Swirg_Shaman", "Vardo", "Ulf"):
    if not eal.does_directory_exist("/Game/TripoModels/" + d):
        out.write("%s: нет\n" % d); continue
    for p in eal.list_assets("/Game/TripoModels/" + d, recursive=True):
        a = unreal.load_asset(p)
        s = "%s [%s]" % (p.split(".")[0], type(a).__name__)
        if isinstance(a, unreal.Texture2D):
            s += " %dx%d" % (a.blueprint_get_size_x(), a.blueprint_get_size_y())
        if isinstance(a, unreal.SkeletalMesh):
            s += " ext=%s" % a.get_bounds().box_extent
        if isinstance(a, unreal.Skeleton):
            s += " bones=%d" % len(a.get_reference_pose().get_bone_names())
        out.write(s + "\n")
for cls in ("IKRigDefinition", "IKRigController", "IKRetargeter", "IKRetargeterController", "IKRetargetBatchOperation", "IKRigDefinitionFactory", "IKRetargetFactory"):
    c = getattr(unreal, cls, None)
    out.write("## %s: %s\n" % (cls, [m for m in dir(c) if not m.startswith("_") and m not in dir(unreal.Object)] if c else None))
for n in ("get_controller", "apply_auto_generated_retarget_definition", "apply_auto_fk_retargeting", "set_skeletal_mesh", "auto_map_chains", "set_ik_rig", "duplicate_and_retarget"):
    for cls in ("IKRigController", "IKRetargeterController", "IKRetargetBatchOperation"):
        c = getattr(unreal, cls, None)
        if c and hasattr(c, n):
            out.write("--- %s.%s: %s\n" % (cls, n, getattr(c, n).__doc__))
out.close()
