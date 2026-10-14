# Расстановка леса вокруг холма: поляна под село, дорога на запад, ели/лиственные, кусты, подлесок.
import numpy as np, json, os
here = os.path.dirname(os.path.abspath(__file__))
terr = os.path.join(here, "..", "Terrain")
j = json.load(open(os.path.join(terr, "height_samples.json")))
n, step, x0 = j["n"], j["step"], j["x0"]
Z = np.load(os.path.join(terr, "z_final.npy")).astype(np.float64)
rng = np.random.default_rng(21)

def height(x, y):
    fx = (x - x0) / step; fy = (y - x0) / step
    i = np.clip(np.floor(fx).astype(int), 0, n - 2); jj = np.clip(np.floor(fy).astype(int), 0, n - 2)
    tx = fx - i; ty = fy - jj
    return (Z[jj, i] * (1 - tx) * (1 - ty) + Z[jj, i + 1] * tx * (1 - ty) +
            Z[jj + 1, i] * (1 - tx) * ty + Z[jj + 1, i + 1] * tx * ty)

def slope_deg(x, y):
    d = 100.0
    gx = (height(x + d, y) - height(x - d, y)) / (2 * d)
    gy = (height(x, y + d) - height(x, y - d)) / (2 * d)
    return np.degrees(np.arctan(np.sqrt(gx * gx + gy * gy)))

def lowfreq(x, y, seed, wl):
    r = np.random.default_rng(seed)
    v = np.zeros_like(x)
    for _ in range(6):
        a = r.uniform(0, 2 * np.pi); f = r.uniform(0.7, 1.4) / wl; ph = r.uniform(0, 2 * np.pi)
        v += np.sin((x * np.cos(a) + y * np.sin(a)) * 2 * np.pi * f + ph)
    return v / 6

def street_y(x):
    return np.where(x > -4500, 600.0 * np.sin(x / 2500.0), 600.0 * np.sin(-4500 / 2500.0))

def jittered(cell, extent):
    g = np.arange(-extent, extent, cell)
    X, Y = np.meshgrid(g, g)
    X = X.ravel() + rng.uniform(0, cell, X.size); Y = Y.ravel() + rng.uniform(0, cell, Y.size)
    return X, Y

EXT = 46000.0
def forest_mask(x, y, edge_noise):
    rc = np.sqrt((x / 1.3) ** 2 + y ** 2)
    clearing = 11500 + edge_noise * 2500                 # рваный край поляны
    road = (x < -4000) & (np.abs(y - street_y(x)) < 450)
    far = np.sqrt(x ** 2 + y ** 2) < EXT
    return (rc > clearing) & ~road & far & (slope_deg(x, y) < 32), rc - clearing

def place(cell, prob, kind_fn, sink, smin, smax, edge_bonus=0.0):
    x, y = jittered(cell, EXT)
    en = lowfreq(x, y, 1, 9000)
    m, dist = forest_mask(x, y, en)
    dens = prob * (0.75 + 0.25 * lowfreq(x, y, 2, 12000)) + edge_bonus * np.exp(-np.maximum(dist, 0) / 1500)
    keep = m & (rng.uniform(0, 1, x.size) < dens)
    x, y = x[keep], y[keep]
    z = height(x, y) - sink
    out = {}
    kinds = kind_fn(x, y)
    for k in set(kinds):
        s = kinds == k
        cnt = int(s.sum())
        out[k] = np.stack([x[s], y[s], z[s], rng.uniform(0, 360, cnt), rng.uniform(smin, smax, cnt)], 1).round(1).tolist()
    return out

def trees_kind(x, y):
    mix = 0.55 + 0.3 * lowfreq(x, y, 7, 15000)          # где-то ельник, где-то смешанный лес
    return np.where(rng.uniform(0, 1, x.size) < mix, "SM_Tree_Spruce", "SM_Tree_Broadleaf")

result = {}
for part in (place(450, 0.9, trees_kind, 30, 0.75, 1.25),
             place(300, 0.45, lambda x, y: np.full(x.size, "SM_Bush"), 10, 0.6, 1.4, edge_bonus=0.5),
             place(180, 0.4, lambda x, y: np.full(x.size, "SM_Undergrowth"), 5, 0.6, 1.4, edge_bonus=0.3)):
    for k, v in part.items():
        result.setdefault(k, []).extend(v)
json.dump(result, open(os.path.join(here, "foliage_placement.json"), "w"))
print({k: len(v) for k, v in result.items()})
