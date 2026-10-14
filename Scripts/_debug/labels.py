import unreal
s = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = open("D:/UOT/Barbarians/Saved/labels.txt", "w", encoding="utf-8")
L = sorted(a.get_actor_label() + " | " + str(a.get_folder_path()) for a in s.get_all_level_actors())
out.write("total %d\n" % len(L))
out.write("\n".join(l for l in L if "ouse" in l or "Hut_01" in l or "PS_" in l))
out.close()
