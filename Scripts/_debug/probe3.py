import unreal
out = open("D:/UOT/Barbarians/Saved/probe3.txt", "w", encoding="utf-8")
B = unreal.BlueprintEditorLibrary
for n in ["add_event_override","add_function_override","call_method","cast","find_event_graph","find_execute_pin","find_then_pin","find_input_pin","find_output_pin","find_data_input_pin","find_condition_pin","find_else_pin","find_result_pin","find_self_pin","list_all_pins","list_events","list_functions","add_member_variable","get_basic_type_by_name","get_array_type","add_function_graph","set_node_pos","get_create_delegate_function","set_create_delegate_function","list_compatible_functions_for_delegate","get_struct_type","get_object_reference_type","get_class_reference_type","pin_type_to_json_schema"]:
    out.write("=== %s\n%s\n" % (n, getattr(B, n).__doc__))
for cls in ("BlueprintGraphPinLibrary", "BlueprintGraphPin", "BlueprintGraphEditor"):
    c = getattr(unreal, cls)
    out.write("##### %s: %s\n%s\n" % (cls, [m for m in dir(c) if not m.startswith("_")], c.__doc__))
    for m in dir(c):
        if not m.startswith("_") and m not in dir(unreal.Object):
            try: out.write("--- %s.%s\n%s\n" % (cls, m, getattr(c, m).__doc__))
            except Exception: pass
out.close()
