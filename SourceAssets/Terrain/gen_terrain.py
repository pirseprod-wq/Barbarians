# Холм под село: плоская вершина + пологие склоны, лёгкие неровности. Сохраняет горы шаблона.
# Вход: height_samples.bin (высоты шаблона, см, сетка 1 м). Выход: T_Height_RG.png (R=старший, G=младший байт), z_final.npy
import numpy as np, json, os
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__))
j = json.load(open(os.path.join(here, "height_samples.json")))
n = j["n"]; step = j["step"]; x0 = j["x0"]
z = np.fromfile(os.path.join(here, "height_samples.bin"), np.float32).reshape(n, n).astype(np.float64)
z = np.nan_to_num(z, nan=0.0)
coords = x0 + np.arange(n) * step
X, Y = np.meshgrid(coords, coords)        # строка = Y, столбец = X

TOP = 2200.0          # высота вершины, см
RP = 7000.0           # радиус площадки под село
RB = 33000.0          # радиус подошвы холма
r = np.sqrt((X / 1.25) ** 2 + Y ** 2)
def smooth(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
hill = np.where(r <= RP, TOP - 150.0 * (r / RP) ** 2,
                (TOP - 150.0) * (1 - smooth((r - RP) / (RB - RP))))

def fnoise(seed, wavelength_cm, amp):
    rng = np.random.default_rng(seed)
    w = rng.standard_normal((n, n))
    f = np.fft.fftfreq(n, d=step)
    FX, FY = np.meshgrid(f, f)
    k = np.sqrt(FX ** 2 + FY ** 2)
    filt = np.exp(-(k * wavelength_cm) ** 2)
    out = np.real(np.fft.ifft2(np.fft.fft2(w) * filt))
    return out / np.abs(out).max() * amp
mask = smooth((r - RP) / 3000.0)          # на площадке села неровностей нет
noise = (fnoise(3, 8000, 150) + fnoise(4, 25000, 300)) * mask
final = z + hill + noise

H = np.clip(np.round(32768 + (final - 100.0) * 1.28), 0, 65535).astype(np.uint32)
rgba = np.zeros((n, n, 4), np.uint8)
rgba[..., 0] = H >> 8; rgba[..., 1] = H & 255; rgba[..., 3] = 255
Image.fromarray(rgba, "RGBA").save(os.path.join(here, "T_Height_RG.png"))
np.save(os.path.join(here, "z_final.npy"), final.astype(np.float32))
c = n // 2
print("top m", final[c, c] / 100, "at 150m", final[c, c + 150] / 100, "at 300m", final[c, c + 300] / 100,
      "max slope deg", np.degrees(np.arctan(np.abs(np.gradient(final, step)).max())))
