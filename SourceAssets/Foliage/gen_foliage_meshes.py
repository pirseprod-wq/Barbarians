# Черновые (greybox) модели растительности, низкополигональные, OBJ (Y вверх, сантиметры).
# Слоты материалов: Bark (кора) и Leaves (листва/хвоя).
import numpy as np, os
here = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(5)

class Mesh:
    def __init__(self): self.v = []; self.groups = {"Bark": [], "Leaves": []}
    def tri(self, g, a, b, c):
        base = len(self.v); self.v += [a, b, c]; self.groups[g].append((base, base + 1, base + 2))
    def save(self, name):
        p = os.path.join(here, name + ".obj")
        with open(p, "w") as f:
            f.write("# greybox foliage\no %s\n" % name)
            for x, y, z in self.v:              # Z вверх у нас -> Y вверх в OBJ
                f.write("v %.2f %.2f %.2f\n" % (x, z, -y))
            vn = []
            for g, tris in self.groups.items():
                for a, b, c in tris:
                    A, B, C = (np.array(self.v[i]) for i in (a, b, c))
                    nrm = np.cross(B - A, C - A); nrm = nrm / (np.linalg.norm(nrm) + 1e-9)
                    vn.append(nrm)
            for nx, ny, nz in vn:
                f.write("vn %.4f %.4f %.4f\n" % (nx, nz, -ny))
            k = 0
            for g, tris in self.groups.items():
                if not tris: continue
                f.write("usemtl %s\n" % g)
                for a, b, c in tris:
                    k += 1
                    f.write("f %d//%d %d//%d %d//%d\n" % (a + 1, k, b + 1, k, c + 1, k))

def frustum(m, g, r0, r1, z0, z1, sides, cap=True, jitter=0.0, off=(0, 0)):
    ang = np.linspace(0, 2 * np.pi, sides, endpoint=False) + rng.uniform(0, 1)
    j0 = 1 + rng.uniform(-jitter, jitter, sides); j1 = 1 + rng.uniform(-jitter, jitter, sides)
    ox, oy = off
    for i in range(sides):
        a, b = ang[i], ang[(i + 1) % sides]
        p0 = (ox + r0 * j0[i] * np.cos(a), oy + r0 * j0[i] * np.sin(a), z0)
        p1 = (ox + r0 * j0[(i + 1) % sides] * np.cos(b), oy + r0 * j0[(i + 1) % sides] * np.sin(b), z0)
        if r1 > 0:
            q0 = (ox + r1 * j1[i] * np.cos(a), oy + r1 * j1[i] * np.sin(a), z1)
            q1 = (ox + r1 * j1[(i + 1) % sides] * np.cos(b), oy + r1 * j1[(i + 1) % sides] * np.sin(b), z1)
            m.tri(g, p0, p1, q1); m.tri(g, p0, q1, q0)
        else:
            m.tri(g, p0, p1, (ox, oy, z1))
        if cap:
            m.tri(g, p1, p0, (ox, oy, z0))

def blob(m, g, center, radius, squash=1.0, sub=2, jitter=0.18):
    t = (1 + 5 ** 0.5) / 2
    verts = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
             (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    verts = [np.array(v, float) / np.linalg.norm(v) for v in verts]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
             (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
             (8, 6, 7), (9, 8, 1)]
    for _ in range(sub):
        cache = {}; nf = []
        def mid(a, b):
            key = tuple(sorted((a, b)))
            if key not in cache:
                v = verts[a] + verts[b]; verts.append(v / np.linalg.norm(v)); cache[key] = len(verts) - 1
            return cache[key]
        for a, b, c in faces:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = nf
    js = 1 + rng.uniform(-jitter, jitter, len(verts))
    P = [np.array(center) + radius * js[i] * np.array([v[0], v[1], v[2] * squash]) for i, v in enumerate(verts)]
    for a, b, c in faces:
        m.tri(g, tuple(P[a]), tuple(P[b]), tuple(P[c]))

# Ель: ствол + 4 яруса конусов, ~16 м
m = Mesh()
frustum(m, "Bark", 28, 12, -30, 1300, 7)
for k, (r, z0, z1) in enumerate([(380, 150, 750), (310, 520, 1050), (230, 850, 1350), (150, 1150, 1650)]):
    frustum(m, "Leaves", r, 0, z0, z1, 9, cap=True, jitter=0.12)
m.save("SM_Tree_Spruce")

# Лиственное дерево (дуб/ясень): ствол + 3 кроны-сгустка, ~13 м
m = Mesh()
frustum(m, "Bark", 35, 18, -30, 650, 7)
frustum(m, "Bark", 14, 6, 450, 850, 5, off=(60, 0))
blob(m, "Leaves", (0, 0, 900), 430, squash=0.8)
blob(m, "Leaves", (180, 120, 750), 260, squash=0.8)
blob(m, "Leaves", (-170, -90, 800), 240, squash=0.8)
m.save("SM_Tree_Broadleaf")

# Куст ~1.5 м
m = Mesh()
blob(m, "Leaves", (0, 0, 55), 90, squash=0.75, sub=1, jitter=0.25)
blob(m, "Leaves", (55, 30, 40), 60, squash=0.75, sub=1, jitter=0.25)
blob(m, "Leaves", (-45, -35, 35), 55, squash=0.75, sub=1, jitter=0.25)
frustum(m, "Bark", 6, 3, -10, 30, 4)
m.save("SM_Bush")

# Подлесок (папоротник/молодая поросль) ~0.6 м
m = Mesh()
for i in range(7):
    a = i / 7 * 2 * np.pi + rng.uniform(-0.2, 0.2)
    d = rng.uniform(15, 35); h = rng.uniform(35, 65)
    frustum(m, "Leaves", rng.uniform(9, 14), 0, 0, h, 4, off=(d * np.cos(a), d * np.sin(a)), jitter=0.2)
frustum(m, "Bark", 3, 1, -5, 15, 3)
m.save("SM_Undergrowth")
print("ok")
