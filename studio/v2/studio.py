"""Studio v2: wet-paint engine + a 'hand' that turns intentions into many marks.

Usage:
  python3 studio.py new "#RRGGBB" [W H]        start a canvas (default 900x1200)
  python3 studio.py do '<intention json>'      the hand executes one intention
  python3 studio.py dry [amount]               let time pass (paint dries; default 0.9)
  python3 studio.py look full|thumb|gray       write look.png
  python3 studio.py look crop X Y W H          zoomed crop (canvas coords)
Env CANVAS=name selects a separate canvas (e.g. for thumbnail sketches).
"""
import numpy as np, json, sys, math, os, random
from PIL import Image, ImageFilter

D = os.path.dirname(os.path.abspath(__file__))
NAME = os.environ.get("CANVAS", "main")
ST = os.path.join(D, f"{NAME}.npz")
LOG = os.path.join(D, f"{NAME}.jsonl")
VIEW = os.path.join(D, f"{NAME}_view.png")
LOOK = os.path.join(D, f"{NAME}_look.png")


def hx(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)


def mixsub(a, b, t):
    """Pigment-like mix: blend of linear and subtractive (geometric) mixing."""
    lin = a * (1 - t) + b * t
    geo = np.exp(np.log(np.clip(a, 2e-3, 1)) * (1 - t) + np.log(np.clip(b, 2e-3, 1)) * t)
    return 0.35 * lin + 0.65 * geo


def weave(h, w, seed=7):
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    t = 0.5 + 0.25 * np.sin(x * 1.9) * np.sin(y * 0.35 + np.sin(x * 0.07)) \
        + 0.25 * np.sin(y * 1.9) * np.sin(x * 0.35 + np.sin(y * 0.07))
    from scipy.ndimage import gaussian_filter
    f = gaussian_filter(rng.random((h, w)).astype(np.float32), 0.8)
    f = (f - f.min()) / (f.max() - f.min() + 1e-6)
    c = gaussian_filter(rng.random((h, w)).astype(np.float32), 3)
    c = (c - c.min()) / (c.max() - c.min() + 1e-6)
    return np.clip(0.06 * t + 0.6 * f + 0.34 * c, 0, 1)


class Canvas:
    def __init__(self):
        z = np.load(ST)
        self.col, self.wet, self.ht = z["col"], z["wet"], z["ht"]
        self.H, self.W = self.wet.shape
        self.tex = weave(self.H, self.W)

    @staticmethod
    def new(ground, w=900, h=1200):
        col = np.ones((h, w, 3), np.float32) * hx(ground)
        rng = np.random.default_rng(1)
        n = rng.random((h // 60 + 2, w // 60 + 2, 3)).astype(np.float32)
        n = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
        col = np.clip(col + (n - 0.5) * 0.04, 0, 1)
        np.savez_compressed(ST, col=col, wet=np.zeros((h, w), np.float32), ht=np.zeros((h, w), np.float32))
        open(LOG, "w").close()

    def save(self):
        np.savez_compressed(ST, col=self.col, wet=self.wet, ht=self.ht)

    def render(self):
        from scipy.ndimage import gaussian_filter
        ht = gaussian_filter(self.ht, 1.2)
        gy, gx = np.gradient(ht * 6.0)
        shade = 1 + np.clip(-gx * 0.6 - gy * 0.8, -0.35, 0.35)
        weaveshade = 0.97 + 0.03 * self.tex * (1 - np.clip(self.ht * 1.5, 0, 0.8))
        img = self.col * (shade * weaveshade)[..., None]
        spec = np.clip(-gx * 0.6 - gy * 0.8 - 0.18, 0, 1) * 0.5
        img = np.clip(img + spec[..., None], 0, 1)
        return Image.fromarray((img * 255).astype(np.uint8))


# ---------------- the brush ----------------

class Brush:
    def __init__(self, kind, size, color, rng, load=1.0, cover=0.85, pickup=0.35, thick=0.5, wetmix=0.5):
        self.kind, self.size, self.rng = kind, size, rng
        self.color = color.copy()
        self.paint = load
        self.cover, self.pickup, self.thick, self.wetmix = cover, pickup, thick, wetmix
        k = max(4, int(size / 1.5))
        self.bristles = np.clip(rng.normal(1.0, 0.22, k), 0.2, 1.25).astype(np.float32)
        if kind == "fan":
            self.bristles *= (rng.random(k) < 0.35)
        self.carry = None

    def mask(self, r, ang, u, v):
        k = len(self.bristles)
        bi = np.clip(((v / max(r, 1e-3) + 1) / 2 * k).astype(int), 0, k - 1)
        br = self.bristles[bi]
        if self.kind in ("round", "fan", "smudge", "glaze"):
            d = (u ** 2 + v ** 2) / max(r * r, 1e-3)
            m = np.clip(1 - d, 0, 1) ** (0.35 if self.kind != "glaze" else 1.5)
            if self.kind != "glaze":
                m = m * br
        elif self.kind == "flat":
            m = (np.clip(1 - np.abs(u) / (r * 0.32 + 0.5), 0, 1) ** 0.3) * (np.clip(1 - np.abs(v) / r, 0, 1) ** 0.25) * br
        elif self.kind == "knife":
            m = ((np.abs(u) < r * 0.18 + 0.6) & (np.abs(v) < r)).astype(np.float32) * (0.85 + 0.15 * br)
        else:
            m = np.clip(1 - (u ** 2 + v ** 2) / max(r * r, 1e-3), 0, 1)
        return m.astype(np.float32)

    def dab(self, cv, x, y, ang, press):
        r = max(0.8, self.size / 2 * (0.55 + 0.45 * press))
        R = int(math.ceil(r)) + 1
        x0, x1 = max(0, int(x) - R), min(cv.W, int(x) + R + 1)
        y0, y1 = max(0, int(y) - R), min(cv.H, int(y) + R + 1)
        if x0 >= x1 or y0 >= y1:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dx, dy = xx - x, yy - y
        ca, sa = math.cos(ang), math.sin(ang)
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        m = self.mask(r, ang, u, v) * press
        if self.kind == "glaze":
            m = m * self.cover
        tex = cv.tex[y0:y1, x0:x1]
        if self.kind not in ("smudge", "glaze") and self.paint < 0.6:
            thr = (0.6 - self.paint) / 0.6
            m = m * np.clip((tex - thr * 0.9) * 4, 0, 1)
        if m.max() <= 0.01:
            return
        c = cv.col[y0:y1, x0:x1]
        w = cv.wet[y0:y1, x0:x1]
        ms = m.sum() + 1e-6
        local = (c * m[..., None]).sum((0, 1)) / ms
        localwet = float((w * m).sum() / ms)
        if self.kind in ("smudge", "knife"):
            if self.carry is None:
                self.carry = local.copy()
            src = self.carry if self.kind == "smudge" else mixsub(self.color, self.carry, 0.5)
            amt = m[..., None] * (0.25 + 0.6 * w[..., None]) * (0.9 if self.kind == "knife" else 0.7)
            cv.col[y0:y1, x0:x1] = mixsub(c, src, np.clip(amt, 0, 1))
            self.carry = self.carry * 0.7 + local * 0.3
            if self.kind == "knife":
                cv.ht[y0:y1, x0:x1] = cv.ht[y0:y1, x0:x1] * (1 - m * 0.5) + m * 0.15 * self.thick
                cv.wet[y0:y1, x0:x1] = np.clip(w + m * 0.4, 0, 1)
            else:
                cv.ht[y0:y1, x0:x1] = cv.ht[y0:y1, x0:x1] * (1 - m * 0.15)
            return
        if self.kind != "glaze":
            self.color = self.color * (1 - self.pickup * localwet * 0.25) + local * (self.pickup * localwet * 0.25)
            dep = mixsub(self.color[None, None, :], c, np.clip(w[..., None] * self.wetmix, 0, 0.8))
            amt = np.clip(m[..., None] * self.cover * min(1, self.paint * 1.6 + 0.3), 0, 1)
            cv.col[y0:y1, x0:x1] = mixsub(c, dep, amt)
            cv.ht[y0:y1, x0:x1] = np.clip(cv.ht[y0:y1, x0:x1] + m * self.thick * 0.12 * self.paint, 0, 3)
            cv.wet[y0:y1, x0:x1] = np.clip(w + m * 0.7, 0, 1)
            self.paint = max(0.0, self.paint - 0.012 * float(m.mean()) * (6 / max(self.size, 2)) ** 0.3)
        else:
            amt = np.clip(m[..., None], 0, 1)
            cv.col[y0:y1, x0:x1] = mixsub(c, self.color[None, None, :], amt)


# ---------------- the hand ----------------

def catmull(pts, spacing):
    if len(pts) < 2:
        return pts
    p = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = map(np.array, (p[i - 1], p[i], p[i + 1], p[i + 2]))
        n = max(2, int(np.linalg.norm(p2[:2] - p1[:2]) / spacing))
        for s in range(n):
            t = s / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(pts[-1]))
    return out


def in_region(reg, x, y, W, H):
    t = reg.get("type", "canvas")
    if t == "canvas":
        return 0 <= x < W and 0 <= y < H
    if t == "ellipse":
        return ((x - reg["cx"]) / reg["rx"]) ** 2 + ((y - reg["cy"]) / reg["ry"]) ** 2 <= 1
    if t == "rect":
        return reg["x"] <= x <= reg["x"] + reg["w"] and reg["y"] <= y <= reg["y"] + reg["h"]
    if t == "poly":
        pts, inside, j = reg["pts"], False, len(reg["pts"]) - 1
        for i in range(len(pts)):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
                inside = not inside
            j = i
        return inside
    return True


def sample(reg, rng, W, H):
    t = reg.get("type", "canvas")
    for _ in range(400):
        if t == "ellipse":
            a, r = rng.random() * 6.283, math.sqrt(rng.random())
            x, y = reg["cx"] + math.cos(a) * r * reg["rx"], reg["cy"] + math.sin(a) * r * reg["ry"]
        elif t == "rect":
            x, y = reg["x"] + rng.random() * reg["w"], reg["y"] + rng.random() * reg["h"]
        elif t == "poly":
            xs, ys = [p[0] for p in reg["pts"]], [p[1] for p in reg["pts"]]
            x, y = rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys))
        else:
            x, y = rng.random() * W, rng.random() * H
        if in_region(reg, x, y, W, H):
            return x, y
    return W / 2, H / 2


def direction(spec, x, y, rng):
    d = spec or {"angle": 0, "spread": 20}
    sp = math.radians(d.get("spread", 15))
    if "around" in d:
        cx, cy = d["around"]
        a = math.atan2(y - cy, x - cx) + math.pi / 2 * (1 if d.get("cw", True) else -1)
    elif "toward" in d:
        a = math.atan2(d["toward"][1] - y, d["toward"][0] - x)
    elif "away" in d:
        a = math.atan2(y - d["away"][1], x - d["away"][0])
    elif d.get("field"):
        s = d.get("scale", 0.006)
        a = math.sin(x * s + y * s * 0.6) * 1.5 + math.cos(y * s * 1.3 - x * s * 0.4) * 1.2 + math.radians(d.get("angle", 0))
    else:
        a = math.radians(d.get("angle", 0))
    return a + rng.normal(0, sp)


def hand(cv, it, seed):
    rng = np.random.default_rng(seed)
    kind = it.get("brush", "round")
    smin, smax = it.get("size", [8, 14])
    colors = [(hx(c[0]) if isinstance(c, list) else hx(c), c[1] if isinstance(c, list) else 1.0) for c in it.get("colors", ["#888888"])]
    wts = np.array([c[1] for c in colors]); wts = wts / wts.sum()
    pres = it.get("pressure", 0.8)
    load = it.get("load", 1.0)
    jit = it.get("color_jitter", 0.04)
    kw = dict(cover=it.get("cover", 0.15 if kind == "glaze" else 0.97), pickup=it.get("pickup", 0.35),
              thick=it.get("impasto", 0.5), wetmix=it.get("wetmix", 0.5))
    marks = []
    for s in it.get("strokes", []):
        pts = [list(p) + ([pres] if len(p) == 2 else []) for p in s["pts"]]
        marks.append((pts, s.get("size", (smin + smax) / 2), s.get("color")))
    reg = it.get("region", {"type": "canvas"})
    lmin, lmax = it.get("length", [20, 60])
    curve = it.get("curve", 0.3)
    for _ in range(int(it.get("count", 0 if marks else 1))):
        x, y = sample(reg, rng, cv.W, cv.H)
        a = direction(it.get("direction"), x, y, rng)
        L = rng.uniform(lmin, lmax)
        bend = rng.normal(0, curve) / max(L, 1)
        pts, step = [], max(1.0, L / 6)
        for i in range(7):
            pts.append([x, y, pres * rng.uniform(0.75, 1.1)])
            if "around" in (it.get("direction") or {}) or (it.get("direction") or {}).get("field"):
                a = a * 0.6 + direction(it.get("direction"), x, y, rng) * 0.4
            a += bend * step
            x += math.cos(a) * step; y += math.sin(a) * step
        marks.append((pts, rng.uniform(smin, smax), None))
    order = rng.permutation(len(marks)) if it.get("shuffle", True) and not it.get("strokes") else range(len(marks))
    for mi in order:
        pts, size, col = marks[mi]
        if col:
            c = hx(col)
        else:
            c = colors[rng.choice(len(colors), p=wts)][0]
        c = np.clip(c + rng.normal(0, jit, 3).astype(np.float32), 0, 1)
        b = Brush(kind, size, c, rng, load=load * rng.uniform(0.8, 1.1), **kw)
        path = catmull(pts, max(0.8, size * (0.12 if kind != "glaze" else 0.3)))
        n = len(path)
        for i in range(n):
            t = i / max(1, n - 1)
            px, py, pp = path[i]
            q, o = path[min(n - 1, i + 1)], path[max(0, i - 1)]
            ang = math.atan2(q[1] - o[1], q[0] - o[0])
            env = min(1, t / 0.12 + 0.25) * (1 - max(0, (t - 0.72) / 0.28) * 0.75)
            b.dab(cv, px, py, ang, float(np.clip(pp * env, 0.05, 1.2)))
    cv.wet *= 0.9


def look(cv, mode, args):
    img = cv.render()
    if mode == "thumb":
        s = img.resize((cv.W // 10, cv.H // 10), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.8))
        s = s.resize((cv.W // 3, cv.H // 3), Image.BICUBIC)
    elif mode == "gray":
        s = img.convert("L").resize((cv.W // 2, cv.H // 2), Image.LANCZOS)
        s = s.point(lambda v: (v // 32) * 32 + 16)
    elif mode == "crop":
        x, y, w, h = map(int, args)
        s = img.crop((x, y, x + w, y + h))
        sc = 700 / max(w, h)
        s = s.resize((int(w * sc), int(h * sc)), Image.LANCZOS)
    else:
        s = img.resize((cv.W * 2 // 3, cv.H * 2 // 3), Image.LANCZOS)
    s.save(LOOK)
    return img


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "new":
        g = sys.argv[2] if len(sys.argv) > 2 else "#c8b89a"
        wh = list(map(int, sys.argv[3:5])) if len(sys.argv) > 4 else [900, 1200]
        Canvas.new(g, *wh)
        cv = Canvas()
    else:
        cv = Canvas()
        if cmd == "do":
            its = json.loads(sys.argv[2])
            its = its if isinstance(its, list) else [its]
            n0 = sum(1 for _ in open(LOG))
            for k, it in enumerate(its):
                hand(cv, it, it.get("seed", n0 * 31 + k * 7 + 1))
                with open(LOG, "a") as f:
                    f.write(json.dumps(it) + "\n")
            cv.save()
        elif cmd == "dry":
            amt = float(sys.argv[2]) if len(sys.argv) > 2 else 0.9
            cv.wet *= (1 - amt)
            cv.save()
        elif cmd == "look":
            look(cv, sys.argv[2], sys.argv[3:])
            print(LOOK)
            sys.exit()
    img = cv.render()
    img.save(os.path.join(D, f"{NAME}_full.png"))
    img.resize((cv.W * 2 // 3, cv.H * 2 // 3), Image.LANCZOS).save(VIEW)
    print(VIEW)
