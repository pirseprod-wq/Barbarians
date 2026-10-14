# Вторая версия растительности: кусты shrub_02 (4 вида), папоротник fern_02 (4 вида), одуванчики на лугу.
# Берёт расстановку из foliage_placement.json (кусты, подлесок) + добавляет цветы на поляну по маске земли.
import numpy as np, json, os
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__))
terr = os.path.join(here, "..", "Terrain")
rng = np.random.default_rng(33)
old = json.load(open(os.path.join(here, "foliage_placement.json")))
j = json.load(open(os.path.join(terr, "height_samples.json")))
n, step, x0 = j["n"], j["step"], j["x0"]
Z = np.load(os.path.join(terr, "z_final.npy")).astype(np.float64)
mask = np.array(Image.open(os.path.join(terr, "T_TerrainMask.png")))
out = {}

def split(items, keys):
    for it in items:
        out.setdefault(keys[rng.integers(len(keys))], []).append(it)

split(old.get("SM_Bush", []), ["shrub_02:%d" % i for i in range(4)])
ug = old.get("SM_Undergrowth", [])
keep = rng.uniform(0, 1, len(ug)) < 0.45
split([u for u, k in zip(ug, keep) if k], ["fern_02:%d" % i for i in range(4)])

# одуванчики на лугу: не лес, не грязь, пологое место, только вокруг села
cell = 220.0
g = np.arange(-30000, 30000, cell)
X, Y = np.meshgrid(g, g)
X = X.ravel() + rng.uniform(0, cell, X.size); Y = Y.ravel() + rng.uniform(0, cell, X.size)
ix = np.clip(((X - x0) / step).astype(int), 0, n - 2); iy = np.clip(((Y - x0) / step).astype(int), 0, n - 2)
forest = mask[iy, ix, 0] / 255.0; mud = mask[iy, ix, 1] / 255.0
gx = (Z[iy, ix + 1] - Z[iy, ix]) / step; gy = (Z[iy + 1, ix] - Z[iy, ix]) / step
slope = np.degrees(np.arctan(np.hypot(gx, gy)))
ok = (forest < 0.1) & (mud < 0.05) & (slope < 20) & (rng.uniform(0, 1, X.size) < 0.28)
X, Y = X[ok], Y[ok]
z = Z[iy[ok], ix[ok]] - 2
fl = np.stack([X, Y, z, rng.uniform(0, 360, X.size), rng.uniform(0.8, 1.3, X.size)], 1).round(1).tolist()
split(fl, ["dandelion_01:%d" % i for i in range(5)])
json.dump(out, open(os.path.join(here, "foliage_placement_v2.json"), "w"))
print({k: len(v) for k, v in sorted(out.items())})
