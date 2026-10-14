import os
here = "D:/UOT/Barbarians/Scripts"
for f in ("brand_house.py", "foliage_v2.py", "terrain_material.py"):
    exec(open(os.path.join(here, f), encoding="utf-8").read(), {"__name__": "__main__"})
