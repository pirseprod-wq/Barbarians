import unreal
out = open("D:/UOT/Barbarians/Saved/probe.txt", "w")
checks = {
 "IFA.add_instances": hasattr(unreal.InstancedFoliageActor, "add_instances"),
 "FT_ISM_Factory": hasattr(unreal, "FoliageType_InstancedStaticMeshFactory"),
 "Land.import_rt": hasattr(unreal.LandscapeProxy, "landscape_import_heightmap_from_render_target"),
 "Land.get_height": [m for m in dir(unreal.LandscapeProxy) if "height" in m.lower()],
 "GeometryScript": hasattr(unreal, "GeometryScript_Primitives") or hasattr(unreal, "GeometryScriptLibrary_MeshPrimitiveFunctions"),
 "IFA_methods": [m for m in dir(unreal.InstancedFoliageActor) if "instance" in m.lower()],
 "Foliage libs": [n for n in dir(unreal) if "oliage" in n],
}
for k, v in checks.items():
    out.write("%s: %s\n" % (k, v))
out.close()
