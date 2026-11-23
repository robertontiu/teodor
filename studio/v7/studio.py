"""Studio v7 - research-informed painting studio with 3D blockout schemas.

Ideas built in:
  * Gombrich's making-and-matching: the painter keeps a SCHEMA (a reference image it designs
    and may revise), places marks, compares, corrects.
  * Eye-hand cycles: many short look/act episodes; within an episode the hand keeps working.
  * Global/local switching: views for stepping back (thumb, gray) and leaning in (crop).
  * Embodied gesture: a FELT STATE (arousal, tension, valence, care) drives the hand's
    kinematics: speed profile, pressure, width, tremor, angularity, hesitation.
  * Paint: Kubelka-Munk-style pigment mixing, wetness and drying, blending (sfumato),
    edge control, glazing, impasto with raking light.

Commands (CANVAS env var selects a canvas name; default "main"):
  new "#RRGGBB" [W H]           start a canvas (default 1200x1600)
  ref <file.svg|file.png>       set / revise the schema (rendered to canvas size)
  scene <scene.json> [overlay.svg] [quality]   render a 3D blockout as the schema (quality: draft|final)
  transfer [strength]           transfer the schema's contours lightly onto the canvas (like a cartoon)
  act '<json>'                  one episode: {"felt": {...}, "do": [intention, ...up to 4]}
  dry [0-1]                     let time pass
  look full|thumb|gray|crop X Y W H|ref|diff|compare
  sign [auto|br|bl]             sign the finished painting ("T. Lisk"), the very last brush act
  timelapse                     build the time-lapse video from recorded frames
"""
import numpy as np, json, sys, math, os, subprocess
from PIL import Image, ImageFilter, ImageDraw
from scipy.ndimage import gaussian_filter, sobel, zoom

D = os.path.dirname(os.path.abspath(__file__))
NAME = os.environ.get("CANVAS", "main")
P = lambda s: os.path.join(D, f"{NAME}_{s}")
FRAMES = os.path.join(D, f"{NAME}_frames")


# ---------------------------------------------------------------- color & pigment
def hx(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)


def _ks(R):
    R = np.clip(R, 0.003, 0.997)
    return (1 - R) ** 2 / (2 * R)


def _unks(k):
    return 1 + k - np.sqrt(k * k + 2 * k)


def kmix(a, b, t):
    """Pigment mixing: Kubelka-Munk (per channel) blended with a little linear mixing
    so that tints with white stay luminous."""
    km = _unks(_ks(a) * (1 - t) + _ks(b) * t)
    lin = a * (1 - t) + b * t
    return (0.58 * km + 0.42 * lin).astype(np.float32)


def shift_color(c, temp=0.0, sat=1.0, value=1.0):
    c = np.asarray(c, np.float32)
    if temp:
        c = c + np.array([0.06, 0.015, -0.06], np.float32) * temp
    g = c.mean(-1, keepdims=True)
    c = g + (c - g) * sat
    return np.clip(c * value, 0, 1)


# ---------------------------------------------------------------- canvas
def weave(h, w, seed=7):
    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.random((h, w)).astype(np.float32), 0.8)
    c = gaussian_filter(rng.random((h, w)).astype(np.float32), 3)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    t = 0.5 + 0.25 * np.sin(x * 1.7) * np.sin(y * 0.3) + 0.25 * np.sin(y * 1.7) * np.sin(x * 0.3)
    n = lambda a: (a - a.min()) / (a.max() - a.min() + 1e-6)
    return np.clip(0.05 * t + 0.6 * n(f) + 0.35 * n(c), 0, 1).astype(np.float32)


class Canvas:
    def __init__(self):
        self.col = np.load(P("col.npy")).astype(np.float32)
        self.wet = np.load(P("wet.npy")).astype(np.float32)
        self.ht = np.load(P("ht.npy")).astype(np.float32)
        self.H, self.W = self.wet.shape
        tp = P("tex.npy")
        self.tex = np.load(tp) if os.path.exists(tp) else weave(self.H, self.W)
        if not os.path.exists(tp):
            np.save(tp, self.tex.astype(np.float16))
        self.tex = self.tex.astype(np.float32)
        rp = P("ref.npy")
        self.ref = np.load(rp).astype(np.float32) if os.path.exists(rp) else None
        self.clip = None

    @staticmethod
    def new(ground, w=1200, h=1600):
        col = np.ones((h, w, 3), np.float32) * hx(ground)
        rng = np.random.default_rng(1)
        n = gaussian_filter(rng.random((h, w, 3)).astype(np.float32), (40, 40, 0))
        n = (n - n.mean()) / (n.std() + 1e-6)
        col = np.clip(col + n * 0.012, 0, 1)
        np.save(P("col.npy"), col.astype(np.float16))
        np.save(P("wet.npy"), np.zeros((h, w), np.float16))
        np.save(P("ht.npy"), np.zeros((h, w), np.float16))
        for f in ("ref.npy", "tex.npy", "log.jsonl"):
            if os.path.exists(P(f)):
                os.remove(P(f))
        os.makedirs(FRAMES, exist_ok=True)
        for f in os.listdir(FRAMES):
            os.remove(os.path.join(FRAMES, f))
        open(P("log.jsonl"), "w").close()

    def save(self):
        np.save(P("col.npy"), self.col.astype(np.float16))
        np.save(P("wet.npy"), self.wet.astype(np.float16))
        np.save(P("ht.npy"), np.clip(self.ht, 0, 4).astype(np.float16))

    def render(self):
        ht = gaussian_filter(self.ht, 1.1)
        gy, gx = np.gradient(ht * 3.2)
        lightdot = -gx * 0.55 - gy * 0.8
        shade = 1 + np.clip(lightdot, -0.12, 0.12)
        tooth = 0.975 + 0.025 * self.tex * (1 - np.clip(self.ht * 1.5, 0, 0.85))
        img = self.col * (shade * tooth)[..., None]
        spec = np.clip(lightdot - 0.16, 0, 1) * 0.08 * np.clip(self.ht * 2, 0, 1)
        img = np.clip(img + spec[..., None], 0, 1)
        return Image.fromarray((img * 255).astype(np.uint8))


# ---------------------------------------------------------------- brush
class Brush:
    def __init__(self, kind, size, color, rng, load=1.0, cover=0.95, pickup=0.35, thick=0.5,
                 wetmix=0.5, edge="soft", depletion=1.0):
        self.kind, self.size, self.rng = kind, size, rng
        self.color = np.asarray(color, np.float32).copy()
        self.paint = load
        self.load0 = load
        self.cover, self.pickup, self.thick, self.wetmix = cover, pickup, thick, wetmix
        self.edge, self.depletion = edge, depletion
        k = max(5, int(size / 1.3))
        self.bristles = np.clip(rng.normal(1.0, 0.2, k), 0.25, 1.25).astype(np.float32)
        if kind == "fan":
            self.bristles *= (rng.random(k) < 0.33)
        self.carry = None

    def mask(self, r, u, v):
        k = len(self.bristles)
        bi = np.clip(((v / max(r, 1e-3) + 1) / 2 * k).astype(int), 0, k - 1)
        br = self.bristles[bi]
        ex = {"hard": 0.12, "soft": 0.7, "lost": 1.6}.get(self.edge, 0.7)
        if self.kind in ("round", "fan", "smudge", "blend"):
            d = (u ** 2 + v ** 2) / max(r * r, 1e-3)
            m = np.clip(1 - d, 0, 1) ** ex
            if self.kind in ("round", "fan"):
                m = m * (br if self.edge != "lost" else 0.6 + 0.4 * br)
        elif self.kind == "flat":
            along = np.clip(1 - np.abs(u) / (r * 0.32 + 0.5), 0, 1) ** 0.3
            across = np.clip(1 - np.abs(v) / r, 0, 1) ** max(0.1, ex * 0.6)
            m = along * across * br
        elif self.kind == "knife":
            m = ((np.abs(u) < r * 0.16 + 0.6) & (np.abs(v) < r)).astype(np.float32) * (0.85 + 0.15 * br)
        else:
            m = np.clip(1 - (u ** 2 + v ** 2) / max(r * r, 1e-3), 0, 1)
        return m.astype(np.float32)

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        r = max(0.7, self.size / 2 * rscale)
        R = int(math.ceil(r)) + 1
        x0, x1 = max(0, int(x) - R), min(cv.W, int(x) + R + 1)
        y0, y1 = max(0, int(y) - R), min(cv.H, int(y) + R + 1)
        if x0 >= x1 or y0 >= y1:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dx, dy = xx - x, yy - y
        ca, sa = math.cos(ang), math.sin(ang)
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        m = self.mask(r, u, v) * press
        if cv.clip is not None:
            m = m * cv.clip[y0:y1, x0:x1]
        tex = cv.tex[y0:y1, x0:x1]
        eff = self.paint - getattr(self, "speedfx", 0.0)
        if self.kind not in ("smudge", "blend") and eff < 0.55:
            thr = min(1.0, (0.55 - eff) / 0.55)
            m = m * np.clip((tex - thr * 0.95) * 4, 0, 1)
        if m.max() <= 0.01:
            return
        c = cv.col[y0:y1, x0:x1]
        w = cv.wet[y0:y1, x0:x1]
        ms = m.sum() + 1e-6
        local = (c * m[..., None]).sum((0, 1)) / ms
        localwet = float((w * m).sum() / ms)
        if self.kind == "blend":
            sig = max(0.8, r / 2.5)
            bl = np.stack([gaussian_filter(c[..., i], sig) for i in range(3)], -1)
            amt = np.clip(m * (0.25 + 0.75 * w) * 0.85, 0, 1)[..., None]
            cv.col[y0:y1, x0:x1] = c * (1 - amt) + bl * amt
            cv.ht[y0:y1, x0:x1] = cv.ht[y0:y1, x0:x1] * (1 - m * 0.25)
            return
        if self.kind in ("smudge", "knife"):
            if self.carry is None:
                self.carry = local.copy()
            src = self.carry if self.kind == "smudge" else kmix(self.color, self.carry, 0.45)
            amt = np.clip(m[..., None] * (0.25 + 0.6 * w[..., None]) * (0.9 if self.kind == "knife" else 0.7), 0, 1)
            cv.col[y0:y1, x0:x1] = kmix(c, src[None, None, :], amt)
            ck = min(0.5, 0.3 * getattr(self, "step", 1.0) / max(self.size * 0.3, 1.0))
            self.carry = self.carry * (1 - ck) + local * ck
            if self.kind == "knife":
                cv.ht[y0:y1, x0:x1] = cv.ht[y0:y1, x0:x1] * (1 - m * 0.5) + m * 0.15 * self.thick
                cv.wet[y0:y1, x0:x1] = np.clip(w + m * 0.4, 0, 1)
            else:
                cv.ht[y0:y1, x0:x1] *= (1 - m * 0.15)
            return
        pk = min(0.5, self.pickup * localwet * 0.25 * getattr(self, "step", 1.0) / max(self.size * 0.5, 1.0))
        self.color = self.color * (1 - pk) + local * pk
        dep = kmix(self.color[None, None, :], c, np.clip(w[..., None] * self.wetmix, 0, 0.8))
        amt = np.clip(m[..., None] * self.cover * min(1, self.paint * 1.6 + 0.3), 0, 1)
        cv.col[y0:y1, x0:x1] = kmix(c, dep, amt)
        cv.ht[y0:y1, x0:x1] = np.clip(cv.ht[y0:y1, x0:x1] * (1 - m * 0.08) + (m ** 1.5) * self.thick * 0.045 * self.paint, 0, 4)
        cv.wet[y0:y1, x0:x1] = np.clip(w + m * 0.7, 0, 1)
        self.paint = max(0.0, self.paint - getattr(self, "step", 1.0) / (max(self.size, 2) * 42 * max(self.load0, 0.1)))


# ---------------------------------------------------------------- the body: felt state -> movement
class Felt:
    """arousal 0..1 (calm..agitated), tension 0..1 (loose..tight), valence -1..1 (dark..warm),
    care 0..1 (impulsive..deliberate)."""

    def __init__(self, d):
        d = d or {}
        self.arousal = float(np.clip(d.get("arousal", 0.4), 0, 1))
        self.tension = float(np.clip(d.get("tension", 0.3), 0, 1))
        self.valence = float(np.clip(d.get("valence", 0.0), -1, 1))
        self.care = float(np.clip(d.get("care", 0.5), 0, 1))


def gesture_path(ctrl, felt, rng, size):
    """Turn control points into a path the way a hand moves: smooth curves when easy,
    straighter segments with corners when tense; tremor from tension."""
    ctrl = [list(p[:2]) for p in ctrl]
    angular = felt.tension * 0.7 + max(0, -felt.valence) * 0.3
    jag = felt.tension * (1 - 0.5 * felt.care)
    if jag > 0.35 and len(ctrl) >= 2:
        new = [ctrl[0]]
        for i in range(len(ctrl) - 1):
            a, b = np.array(ctrl[i]), np.array(ctrl[i + 1])
            dvec = b - a
            ln = np.linalg.norm(dvec) + 1e-6
            nrm = np.array([-dvec[1], dvec[0]]) / ln
            k = int(1 + jag * ln / max(size * 2.5, 8))
            for j in range(1, k + 1):
                p = a + dvec * j / (k + 1) + nrm * rng.normal(0, 1) * jag * size * 1.2
                new.append(list(p))
            new.append(list(b))
        ctrl = new
    pts = []
    spacing = max(0.7, size * 0.1)
    if angular < 0.55 and len(ctrl) > 2:
        p = [ctrl[0]] + ctrl + [ctrl[-1]]
        for i in range(1, len(p) - 2):
            p0, p1, p2, p3 = map(np.array, (p[i - 1], p[i], p[i + 1], p[i + 2]))
            n = max(2, int(np.linalg.norm(p2 - p1) / spacing))
            for s in range(n):
                t = s / n
                pts.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                  + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        pts.append(np.array(ctrl[-1]))
    else:
        for i in range(len(ctrl) - 1):
            a, b = np.array(ctrl[i]), np.array(ctrl[i + 1])
            n = max(2, int(np.linalg.norm(b - a) / spacing))
            for s in range(n):
                pts.append(a + (b - a) * s / n)
        pts.append(np.array(ctrl[-1]))
    pts = np.array(pts, np.float32)
    if len(pts) > 3:
        trem = felt.tension * (1 - felt.care * 0.6) * size * 0.22 + felt.arousal * 0.6
        if trem > 0.05:
            d = np.gradient(pts, axis=0)
            nrm = np.stack([-d[:, 1], d[:, 0]], 1)
            nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-6)
            f = rng.uniform(0.15, 0.45)
            noise = gaussian_filter(rng.normal(0, 1, len(pts)), 1.0 / f) * trem * 2.5
            pts = pts + nrm * noise[:, None]
    return pts


def play(cv, brush, path, felt, base_press, rng):
    """Lay a path with human kinematics: minimum-jerk speed profile; faster = thinner,
    lighter, more broken; slow ends pool paint; hesitation at the start when careful or tense."""
    n = len(path)
    if n < 2:
        return
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    arc = np.concatenate([[0], np.cumsum(seg)])
    L = arc[-1] + 1e-6
    speed_scale = 0.4 + 0.9 * felt.arousal - 0.3 * felt.care
    steps = max(5, int(L / max(0.5, brush.size * 0.055) * (1.25 - 0.35 * speed_scale)))
    hes = 0.08 * (felt.care + felt.tension) / 2
    prev_xy = None
    for i in range(steps + 1):
        t = i / steps
        tt = min(1, max(0, (t - hes) / (1 - hes))) if hes > 0 else t
        s = 10 * tt ** 3 - 15 * tt ** 4 + 6 * tt ** 5
        vel = 30 * tt * tt * (1 - tt) ** 2 / 1.875
        d = s * L
        j = int(np.searchsorted(arc, d))
        j = min(max(j, 1), n - 1)
        a0, a1 = arc[j - 1], arc[j]
        f = 0 if a1 == a0 else (d - a0) / (a1 - a0)
        x, y = path[j - 1] + (path[j] - path[j - 1]) * f
        ang = math.atan2(path[j][1] - path[j - 1][1], path[j][0] - path[j - 1][0])
        vn = vel * speed_scale
        land = min(1.0, 0.55 + t / 0.08 * 0.45)
        lift = 1.0 if t < 0.8 else 1 - (t - 0.8) / 0.2 * (0.55 + 0.35 * felt.arousal)
        if getattr(brush, "liner", False):
            land = min(1.0, 0.25 + t / 0.15 * 0.75)
            lift = 1.0 if t < 0.55 else max(0.08, 1 - (t - 0.55) / 0.45)
        press = base_press * land * lift * (1.0 - 0.3 * vn) * (1 + 0.35 * felt.tension * rng.normal(0, 0.35))
        rscale = (0.8 + 0.25 * land) * (1.06 - 0.3 * vn) * (0.85 + 0.15 * lift)
        brush.speedfx = 0.35 * vn * felt.arousal
        if prev_xy is not None:
            brush.step = math.hypot(x - prev_xy[0], y - prev_xy[1])
        prev_xy = (x, y)
        brush.dab(cv, x, y, ang, float(np.clip(press, 0.03, 1.3)), rscale=max(0.3, rscale))


# ---------------------------------------------------------------- regions, sampling, directions
def region_mask(reg, W, H, feather=1.0):
    t = reg.get("type", "canvas")
    if t == "canvas":
        return None
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    if t == "ellipse":
        d.ellipse([reg["cx"] - reg["rx"], reg["cy"] - reg["ry"], reg["cx"] + reg["rx"], reg["cy"] + reg["ry"]], fill=255)
    elif t == "rect":
        d.rectangle([reg["x"], reg["y"], reg["x"] + reg["w"], reg["y"] + reg["h"]], fill=255)
    elif t == "poly":
        d.polygon([tuple(p) for p in reg["pts"]], fill=255)
    return gaussian_filter(np.array(m, np.float32) / 255, feather)


def sample_in(mask, reg, rng, W, H):
    t = reg.get("type", "canvas")
    for _ in range(500):
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
        if 0 <= x < W and 0 <= y < H and (mask is None or mask[int(y), int(x)] > 0.5):
            return x, y
    return W / 2, H / 2


def direction(spec, x, y, rng, felt):
    d = spec or {"angle": 0, "spread": 20}
    sp = math.radians(d.get("spread", 15)) * (1.3 - 0.6 * felt.care + 0.4 * felt.arousal)
    if "around" in d:
        cx, cy = d["around"]
        a = math.atan2(y - cy, x - cx) + math.pi / 2 * (1 if d.get("cw", True) else -1)
    elif "toward" in d:
        a = math.atan2(d["toward"][1] - y, d["toward"][0] - x)
    elif "away" in d:
        a = math.atan2(y - d["away"][1], x - d["away"][0])
    elif d.get("field"):
        s = d.get("scale", 0.005)
        a = math.sin(x * s + y * s * 0.6) * 1.5 + math.cos(y * s * 1.3 - x * s * 0.4) * 1.2 + math.radians(d.get("angle", 0))
    else:
        a = math.radians(d.get("angle", 0))
    return a + rng.normal(0, sp)


def make_brush(it, size, color, rng):
    kind = it.get("brush", "round")
    if kind == "liner":
        b = Brush("round", size, color, rng, load=it.get("load", 1.0), cover=it.get("cover", 0.97),
                  pickup=0.1, thick=it.get("impasto", 0.3), wetmix=it.get("wetmix", 0.2), edge="hard")
        b.bristles[:] = 1.0
        b.liner = True
        return b
    return Brush(kind, size, color, rng, load=it.get("load", 1.0) * rng.uniform(0.85, 1.1),
                 cover=it.get("cover", 0.95), pickup=it.get("pickup", 0.35), thick=it.get("impasto", 0.5),
                 wetmix=it.get("wetmix", 0.5), edge=it.get("edge", "soft"))


def palette(it):
    cs = it.get("colors", ["#888888"])
    cols = [hx(c[0]) if isinstance(c, list) else hx(c) for c in cs]
    w = np.array([c[1] if isinstance(c, list) else 1.0 for c in cs], float)
    return cols, w / w.sum()


# ---------------------------------------------------------------- intentions
def do_free(cv, it, felt, rng):
    reg = it.get("region", {"type": "canvas"})
    cv.clip = region_mask(reg, cv.W, cv.H) if it.get("clip") else None
    mask = region_mask(reg, cv.W, cv.H)
    cols, w = palette(it)
    smin, smax = it.get("size", [8, 14])
    lmin, lmax = it.get("length", [20, 60])
    jit = it.get("color_jitter", 0.035) * (1.2 - 0.6 * felt.care)
    for _ in range(int(it.get("count", 10))):
        x, y = sample_in(mask, reg, rng, cv.W, cv.H)
        a = direction(it.get("direction"), x, y, rng, felt)
        L = rng.uniform(lmin, lmax) * (0.8 + 0.5 * felt.arousal)
        nc = 3 + int(rng.integers(0, 3))
        ctrl, px, py = [], x, y
        turn = it.get("curve", 0.3) * (1 + felt.tension)
        for k in range(nc):
            ctrl.append([px, py])
            if "around" in (it.get("direction") or {}) or (it.get("direction") or {}).get("field"):
                a = a * 0.5 + direction(it.get("direction"), px, py, rng, felt) * 0.5
            a += rng.normal(0, turn)
            px += math.cos(a) * L / (nc - 1); py += math.sin(a) * L / (nc - 1)
        size = rng.uniform(smin, smax)
        col = np.clip(cols[rng.choice(len(cols), p=w)] + rng.normal(0, jit, 3), 0, 1)
        b = make_brush(it, size, col, rng)
        play(cv, b, gesture_path(ctrl, felt, rng, size), felt, it.get("pressure", 0.85), rng)


def do_strokes(cv, it, felt, rng):
    reg = it.get("region")
    cv.clip = region_mask(reg, cv.W, cv.H) if (reg and it.get("clip")) else None
    cols, w = palette(it) if it.get("colors") else ([hx("#888888")], np.array([1.0]))
    for s in it["strokes"]:
        size = s.get("size", np.mean(it.get("size", [6, 10])))
        col = hx(s["color"]) if s.get("color") else cols[rng.choice(len(cols), p=w)]
        b = make_brush(it, size, col, rng)
        play(cv, b, gesture_path(s["pts"], felt, rng, size), felt, s.get("pressure", it.get("pressure", 0.85)), rng)


def do_match(cv, it, felt, rng):
    """Making and matching: compare the canvas with the schema at this brush scale and lay
    strokes where they differ most, colored from the schema (as the painter interprets it),
    following the form (perpendicular to the schema's value gradient)."""
    if cv.ref is None:
        sys.exit("No schema yet: use the ref command first.")
    reg = it.get("region", {"type": "canvas"})
    mask = region_mask(reg, cv.W, cv.H)
    cv.clip = mask if it.get("clip") else None
    smin, smax = it.get("size", [20, 40])
    size = (smin + smax) / 2
    sig = max(1.0, size / 3)
    refb = np.stack([gaussian_filter(cv.ref[..., i], sig) for i in range(3)], -1)
    lum = refb.mean(-1)
    gy, gx = sobel(lum, 0), sobel(lum, 1)
    err = np.abs(cv.col - refb).sum(-1)
    if mask is not None:
        err = err * (mask > 0.5)
    g = max(4, int(size * 0.9))
    H2, W2 = -(-cv.H // g), -(-cv.W // g)
    errp = np.pad(err, ((0, H2 * g - cv.H), (0, W2 * g - cv.W)), mode="edge")
    e = errp.reshape(H2, g, W2, g).mean((1, 3))
    thr = it.get("threshold", 0.12)
    cells = [(e[r, c], r, c) for r in range(H2) for c in range(W2) if e[r, c] > thr]
    rng.shuffle(cells)
    cells = cells[: int(it.get("max_strokes", 400))]
    faithful = it.get("faithful", 0.85)
    adaptive = it.get("adaptive", True)
    sharp = np.stack([gaussian_filter(cv.ref[..., i], 1.0) for i in range(3)], -1)
    if adaptive:
        lf = gaussian_filter(cv.ref.mean(-1), 1.2)
        det = gaussian_filter(np.hypot(sobel(lf, 0), sobel(lf, 1)), max(2.0, size / 2))
        det = np.clip(det / (np.percentile(det, 97) + 1e-6), 0, 1)
    cols, w = palette(it) if it.get("colors") else (None, None)
    cs = it.get("color_shift", {})
    lmin, lmax = it.get("length", [size * 1.5, size * 5])
    for _, r, c in cells:
        sub = errp[r * g:(r + 1) * g, c * g:(c + 1) * g]
        iy, ix = np.unravel_index(np.argmax(sub), sub.shape)
        x = int(np.clip(c * g + ix + rng.normal(0, g * 0.35), 0, cv.W - 1))
        y = int(np.clip(r * g + iy + rng.normal(0, g * 0.35), 0, cv.H - 1))
        col = sharp[y, x].copy()
        if cols is not None:
            col = col * faithful + cols[rng.choice(len(cols), p=w)] * (1 - faithful)
        col = shift_color(col, cs.get("temp", 0), cs.get("sat", 1), cs.get("value", 1))
        col = np.clip(col + rng.normal(0, 0.012 * (1.2 - felt.care), 3), 0, 1)
        if adaptive:
            dv = float(det[y, x])
            sz = smax - (smax - smin) * dv ** 0.7
            sz *= rng.uniform(0.9, 1.1)
            Lsc = 1.0 - 0.55 * dv
        else:
            sz = rng.uniform(smin, smax); Lsc = 1.0
        L = rng.uniform(lmin, lmax) * (0.8 + 0.5 * felt.arousal) * Lsc
        ctrl, px, py, prev = [[x, y]], float(x), float(y), None
        step = max(2.0, sz * 0.8)
        for k in range(int(L / step)):
            ix_, iy_ = int(np.clip(px, 0, cv.W - 1)), int(np.clip(py, 0, cv.H - 1))
            dx, dy = -gy[iy_, ix_], gx[iy_, ix_]
            nrm = math.hypot(dx, dy)
            if nrm < 1e-4:
                if prev is None:
                    a = direction(it.get("direction", {"angle": 0, "spread": 40}), px, py, rng, felt)
                    dx, dy = math.cos(a), math.sin(a)
                else:
                    dx, dy = prev
            else:
                dx, dy = dx / nrm, dy / nrm
                if prev is not None and dx * prev[0] + dy * prev[1] < 0:
                    dx, dy = -dx, -dy
            if prev is not None:
                dx, dy = 0.6 * dx + 0.4 * prev[0], 0.6 * dy + 0.4 * prev[1]
            prev = (dx, dy)
            px += dx * step; py += dy * step
            if not (0 <= px < cv.W and 0 <= py < cv.H):
                break
            if k >= 1 and np.abs(sharp[int(py), int(px)] - col).sum() > 0.22 + 0.3 * (1 - faithful):
                break
            if k >= 2 and np.abs(refb[int(py), int(px)] - col).sum() > 0.3 + 0.3 * (1 - faithful):
                break
            ctrl.append([px, py])
        if len(ctrl) < 2:
            ctrl.append([x + rng.normal(0, sz), y + rng.normal(0, sz)])
        it2 = dict(it); it2.setdefault("wetmix", 0.22); it2.setdefault("load", 1.3)
        b = make_brush(it2, sz, col, rng)
        play(cv, b, gesture_path(ctrl, felt, rng, sz), felt, it.get("pressure", 0.9), rng)


def do_glaze(cv, it, felt, rng):
    reg = it.get("region", {"type": "canvas"})
    mask = region_mask(reg, cv.W, cv.H, feather=it.get("feather", 30))
    if mask is None:
        mask = np.ones((cv.H, cv.W), np.float32)
    col = hx(it["color"])
    op = it.get("opacity", 0.25)
    amt = (mask * op * (1 - 0.5 * cv.wet))[..., None]
    cv.col = kmix(cv.col, col[None, None, :], amt)


def do_blend(cv, it, felt, rng):
    it = dict(it); it["brush"] = "blend"
    if "strokes" in it:
        do_strokes(cv, it, felt, rng)
    else:
        do_free(cv, it, felt, rng)


INTENT = {"free": do_free, "strokes": do_strokes, "match": do_match, "glaze": do_glaze, "blend": do_blend}


def intent_kind(it):
    if "type" in it:
        return it["type"]
    if it.get("strokes"):
        return "strokes"
    return "free"


# ---------------------------------------------------------------- schema
def set_ref(cv, path):
    out = P("ref.png")
    if path.endswith(".svg"):
        subprocess.run(["rsvg-convert", "-w", str(cv.W), "-h", str(cv.H), "-o", out, path], check=True)
    else:
        Image.open(path).convert("RGB").resize((cv.W, cv.H), Image.LANCZOS).save(out)
    im = Image.open(out).convert("RGBA")
    bg = Image.new("RGBA", im.size, (128, 128, 128, 255))
    im = Image.alpha_composite(bg, im).convert("RGB")
    cv.ref = np.array(im, np.float32) / 255
    np.save(P("ref.npy"), cv.ref.astype(np.float16))
    k = len([f for f in os.listdir(D) if f.startswith(f"{NAME}_schema_v")]) + 1
    im.resize((cv.W // 2, cv.H // 2), Image.LANCZOS).save(P(f"schema_v{k}.png"))
    print(f"schema version {k} set")


def transfer(cv, strength):
    lum = gaussian_filter(cv.ref.mean(-1), 1.5)
    e = np.hypot(sobel(lum, 0), sobel(lum, 1))
    e = np.clip(e / (np.percentile(e, 99) + 1e-6), 0, 1) ** 1.5
    line = hx("#4a3a2e")
    cv.col = kmix(cv.col, line[None, None, :], (e * strength)[..., None])


# ---------------------------------------------------------------- views & frames
def look(cv, mode, args):
    img = cv.render()
    vw, vh = cv.W // 2, cv.H // 2
    if mode == "thumb":
        s = img.resize((cv.W // 12, cv.H // 12), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.7)).resize((vw * 2 // 3, vh * 2 // 3), Image.BICUBIC)
    elif mode == "gray":
        s = img.convert("L").resize((vw, vh), Image.LANCZOS).point(lambda v: (v // 32) * 32 + 16)
    elif mode == "crop":
        x, y, w, h = map(int, args)
        s = img.crop((x, y, x + w, y + h))
        sc = 760 / max(w, h)
        s = s.resize((int(w * sc), int(h * sc)), Image.LANCZOS)
    elif mode == "ref":
        s = Image.fromarray((cv.ref * 255).astype(np.uint8)).resize((vw, vh), Image.LANCZOS)
    elif mode == "diff":
        e = np.abs(cv.col - cv.ref).sum(-1)
        e = gaussian_filter(e, 4)
        s = Image.fromarray((np.clip(e / 1.2, 0, 1) * 255).astype(np.uint8)).resize((vw, vh)).convert("RGB")
    elif mode == "compare":
        a = Image.fromarray((cv.ref * 255).astype(np.uint8)).resize((vw * 3 // 4, vh * 3 // 4), Image.LANCZOS)
        b = img.resize((vw * 3 // 4, vh * 3 // 4), Image.LANCZOS)
        s = Image.new("RGB", (a.width * 2 + 10, a.height), (20, 20, 20))
        s.paste(a, (0, 0)); s.paste(b, (a.width + 10, 0))
    else:
        s = img.resize((vw, vh), Image.LANCZOS)
    s.save(P("look.png"))
    print(P("look.png"))


def record(cv, img=None):
    img = img or cv.render()
    os.makedirs(FRAMES, exist_ok=True)
    n = len(os.listdir(FRAMES))
    img.resize((cv.W * 3 // 8 // 2 * 2, cv.H * 3 // 8 // 2 * 2), Image.LANCZOS).save(os.path.join(FRAMES, f"{n:05d}.jpg"), quality=88)
    img.save(P("full.png"))
    img.resize((cv.W // 2, cv.H // 2), Image.LANCZOS).save(P("view.png"))


def timelapse():
    out = P("timelapse.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "8", "-i", os.path.join(FRAMES, "%05d.jpg"),
                    "-vf", "tpad=stop_mode=clone:stop_duration=3", "-c:v", "libx264", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", out], check=True)
    print(out)


# ---------------------------------------------------------------- main
if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "new":
        g = sys.argv[2] if len(sys.argv) > 2 else "#c8b89a"
        wh = list(map(int, sys.argv[3:5])) if len(sys.argv) > 4 else [1200, 1600]
        Canvas.new(g, *wh)
        cv = Canvas(); record(cv); print(P("view.png")); sys.exit()
    if cmd == "timelapse":
        timelapse(); sys.exit()
    cv = Canvas()
    if cmd == "ref":
        set_ref(cv, sys.argv[2]); look(cv, "ref", []); sys.exit()
    if cmd == "scene":
        import scene as sc
        ov = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3].endswith(".svg") else None
        q = sys.argv[-1] if sys.argv[-1] in ("draft", "final") else "draft"
        rw, rh = (300, 400) if q == "draft" else (450, 600)
        k = len([f for f in os.listdir(D) if f.startswith(f"{NAME}_scene_v") and f.endswith(".png")]) + 1
        out = P(f"scene_v{k}.png")
        sc.render_file(sys.argv[2], out, rw, rh, ov, (cv.W, cv.H))
        import shutil; shutil.copy(sys.argv[2], P(f"scene_v{k}.json"))
        set_ref(cv, out); look(cv, "ref", []); sys.exit()
    if cmd == "look":
        look(cv, sys.argv[2], sys.argv[3:]); sys.exit()
    if cmd == "transfer":
        transfer(cv, float(sys.argv[2]) if len(sys.argv) > 2 else 0.35)
    elif cmd == "sign":
        sys.path.insert(0, os.path.join(D, "..")); sys.path.insert(0, D)
        from signature import sign_array
        sign_array(cv.col, sys.argv[2] if len(sys.argv) > 2 else "auto")
        cv.ht *= 1.0
    elif cmd == "dry":
        cv.wet *= (1 - (float(sys.argv[2]) if len(sys.argv) > 2 else 0.9))
    elif cmd == "act":
        ep = json.loads(sys.argv[2])
        felt = Felt(ep.get("felt"))
        todo = ep.get("do", [])
        todo = todo if isinstance(todo, list) else [todo]
        if len(todo) > 4:
            sys.exit("An episode holds at most 4 intentions; look again before continuing.")
        nlog = sum(1 for _ in open(P("log.jsonl")))
        for k, it in enumerate(todo):
            rng = np.random.default_rng(it.get("seed", nlog * 131 + k * 17 + 3))
            INTENT[intent_kind(it)](cv, it, felt, rng)
            cv.clip = None
        cv.wet *= 0.93
        with open(P("log.jsonl"), "a") as f:
            f.write(json.dumps(ep) + "\n")
    cv.save()
    record(cv)
    print(P("view.png"))
