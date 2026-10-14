# Генерирует исходники погоды: текстуру струй дождя (бесшовная) и звук дождя (бесшовная петля).
import numpy as np, wave, os
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(7)

# ---- текстура струй дождя 256x1024, бесшовная по обеим осям
W, H = 256, 1024
img = np.zeros((H, W), np.float32)
for _ in range(140):
    x = rng.integers(0, W)
    y0 = rng.integers(0, H)
    length = rng.integers(60, 260)
    bright = rng.uniform(0.35, 1.0)
    width = 2 if rng.random() < 0.25 else 1
    t = np.linspace(0, 1, length)          # 0 = хвост (верх), 1 = голова (низ)
    profile = bright * t ** 1.5
    ys = (y0 + np.arange(length)) % H
    for dx in range(width):
        img[ys, (x + dx) % W] = np.maximum(img[ys, (x + dx) % W], profile * (1.0 if dx == 0 else 0.5))
# лёгкое размытие по горизонтали (с переносом через край)
img = 0.6 * img + 0.2 * np.roll(img, 1, 1) + 0.2 * np.roll(img, -1, 1)
img = np.clip(img, 0, 1)
Image.fromarray((img * 255).astype(np.uint8), "L").convert("RGB").save(os.path.join(here, "T_RainStreaks.png"))

# ---- звук дождя: 30 с, 44.1 кГц, стерео, бесшовная петля (синтез через FFT цикличен)
SR, SEC = 44100, 30
N = SR * SEC
def shaped_noise(seed):
    r = np.random.default_rng(seed)
    spec = np.fft.rfft(r.standard_normal(N))
    f = np.fft.rfftfreq(N, 1 / SR)
    f[0] = 1
    shape = (1 / np.sqrt(f)) * (1 / (1 + (f / 9000) ** 4)) * (1 - 1 / (1 + (f / 250) ** 4))
    x = np.fft.irfft(spec * shape, N)
    return x / np.abs(x).max()
def drops(seed, count):
    r = np.random.default_rng(seed)
    out = np.zeros(N)
    burst_len = int(0.012 * SR)
    env = np.exp(-np.linspace(0, 8, burst_len))
    for _ in range(count):
        p = r.integers(0, N)
        b = r.standard_normal(burst_len) * env * r.uniform(0.2, 1.0)
        b = np.diff(b, prepend=0)        # верхние частоты: «щелчок» капли
        idx = (p + np.arange(burst_len)) % N
        out[idx] += b
    return out / np.abs(out).max()
L = 0.8 * shaped_noise(1) + 0.25 * drops(11, 9000)
R = 0.8 * shaped_noise(2) + 0.25 * drops(12, 9000)
st = np.stack([L, R], 1)
st = st / np.abs(st).max() * 0.5
pcm = (st * 32767).astype(np.int16)
with wave.open(os.path.join(here, "SW_Rain_Loop.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok")
