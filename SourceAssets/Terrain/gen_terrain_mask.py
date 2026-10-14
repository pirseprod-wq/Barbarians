# Маска раскраски земли (1 пиксель = 1 м): R - лес (лесная подстилка), G - грязь (улица, дворы, дорога).
# Остальное - луг; камень материал добавляет сам по крутизне склона.
import numpy as np, json, os
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__))
j = json.load(open(os.path.join(here, "height_samples.json")))
n, step, x0 = j["n"], j["step"], j["x0"]
c = x0 + np.arange(n) * step
X, Y = np.meshgrid(c, c)

def lowfreq(x, y, seed, wl):        # та же функция, что в расстановке леса
    r = np.random.default_rng(seed)
    v = np.zeros_like(x)
    for _ in range(6):
        a = r.uniform(0, 2 * np.pi); f = r.uniform(0.7, 1.4) / wl; ph = r.uniform(0, 2 * np.pi)
        v += np.sin((x * np.cos(a) + y * np.sin(a)) * 2 * np.pi * f + ph)
    return v / 6

def smooth(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)

def street_y(x):
    return np.where(x > -4500, 600.0 * np.sin(x / 2500.0), 600.0 * np.sin(-4500 / 2500.0))

rc = np.sqrt((X / 1.3) ** 2 + Y ** 2)
clearing = 11500 + lowfreq(X, Y, 1, 9000) * 2500
forest = smooth((rc - clearing + 300) / 1800) * (1 - smooth((np.sqrt(X ** 2 + Y ** 2) - 47000) / 3000))
d_street = np.abs(Y - street_y(X))
street = (1 - smooth((d_street - 250) / 300)) * (X > -48000) * (1 - smooth((X - 5000) / 800))
yard = smooth((0.75 + 0.45 * lowfreq(X, Y, 5, 1200) - rc / 6000.0) * 3) * (rc < 9000)
mud = np.clip(np.maximum(street, yard * 0.85), 0, 1)
forest = forest * (1 - mud)
img = np.zeros((n, n, 4), np.uint8)
img[..., 0] = (forest * 255).round()
img[..., 1] = (mud * 255).round()
img[..., 3] = 255
Image.fromarray(img, "RGBA").save(os.path.join(here, "T_TerrainMask.png"))
Image.fromarray(img[::8, ::8, :3]).save(os.path.join(here, "_mask_preview.png"))
print("ok", forest.mean(), mud.mean())
