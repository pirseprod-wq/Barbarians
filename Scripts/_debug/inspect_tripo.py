import unreal
out = open("D:/UOT/Barbarians/Saved/inspect_tripo.txt", "w", encoding="utf-8")
eal = unreal.EditorAssetLibrary
for p in eal.list_assets("/Game/TripoModels", recursive=True):
    a = unreal.load_asset(p)
    t = type(a).__name__
    line = "%s  [%s]" % (p.split(".")[0], t)
    try:
        if isinstance(a, unreal.StaticMesh):
            line += " verts=%d tris=%d" % (a.get_num_vertices(0), a.get_num_triangles(0))
            bb = a.get_bounding_box(); s = bb.max - bb.min
            line += " size=%.0fx%.0fx%.0f" % (s.x, s.y, s.z)
        elif isinstance(a, unreal.SkeletalMesh):
            sk = a.get_editor_property("skeleton")
            bones = []
            try:
                ref = unreal.SkeletalMeshEditorSubsystem
            except Exception:
                pass
            bb = a.get_bounds(); 
            line += " bounds=%s" % (bb.box_extent,)
            try:
                n = a.get_editor_property("lod_info")
                line += " lods=%d" % len(n)
            except Exception:
                pass
            try:
                sub = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
                line += " verts=%d" % sub.get_num_verts(a, 0)
            except Exception as e:
                line += " (verts?)"
            try:
                bn = [str(sk.get_reference_pose().get_bone_names()[i]) for i in range(5)]
            except Exception:
                bn = []
            try:
                names = unreal.SkeletalMeshEditorSubsystem
            except Exception:
                pass
            line += " skeleton=%s" % sk.get_name()
        elif isinstance(a, unreal.Texture2D):
            line += " %dx%d srgb=%s" % (a.blueprint_get_size_x(), a.blueprint_get_size_y(), a.get_editor_property("srgb"))
        elif isinstance(a, unreal.Skeleton):
            try:
                ref = a.get_reference_pose()
                names = ref.get_bone_names()
                line += " bones=%d: %s" % (len(names), ", ".join(str(n) for n in names[:70]))
            except Exception as e:
                line += " bones? %s" % e
        elif isinstance(a, (unreal.MaterialInstance, unreal.Material)):
            pass
    except Exception as e:
        line += " ERR %s" % e
    out.write(line + "\n")
out.close()
