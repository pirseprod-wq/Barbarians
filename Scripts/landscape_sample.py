# -*- coding: utf-8 -*-
"""Снимает высоты ландшафта лучами на сетке 1 м -> SourceAssets/Terrain/height_samples.bin (float32, NaN = промах)."""
import array, json, time
import unreal

OUT = "D:/UOT/Barbarians/SourceAssets/Terrain/"
STEP = 100.0
X0, X1 = -100800.0, 100800.0
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ignore = [a for a in actor_sub.get_all_level_actors() if not isinstance(a, unreal.LandscapeProxy)]
n = int((X1 - X0) / STEP) + 1
data = array.array("f")
t0 = time.time()
hits = 0
for j in range(n):
    y = X0 + j * STEP
    for i in range(n):
        x = X0 + i * STEP
        z = float("nan")
        try:
            res = unreal.SystemLibrary.line_trace_single(
                world, unreal.Vector(x, y, 60000.0), unreal.Vector(x, y, -60000.0),
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore,
                unreal.DrawDebugTrace.NONE, True)
            hit = res[0] if isinstance(res, tuple) else res
            if hit is not None:
                tp = hit.to_tuple()
                if tp[0]:
                    z = tp[4].z
                    hits += 1
        except Exception:
            pass
        data.append(z)
with open(OUT + "height_samples.bin", "wb") as f:
    data.tofile(f)
json.dump({"n": n, "step": STEP, "x0": X0, "hits": hits, "sec": time.time() - t0},
          open(OUT + "height_samples.json", "w"))
unreal.log("[Terrain] samples done hits=%d of %d" % (hits, n * n))
