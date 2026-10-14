import unreal
s = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = open("D:/UOT/Barbarians/Saved/foliage_count.txt", "w")
tot = {}
ifas = 0
for a in s.get_all_level_actors():
    if isinstance(a, unreal.InstancedFoliageActor):
        ifas += 1
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            n = c.get_instance_count()
            k = c.static_mesh.get_name() if c.static_mesh else "?"
            tot[k] = tot.get(k, 0) + n
out.write("ifas=%d %s\n" % (ifas, tot))
descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
out.write("ifa descs=%d\n" % len([d for d in descs if "Foliage" in str(d.native_class)]))
out.close()
