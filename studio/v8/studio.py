"""Studio v8 - the painting studio with media as instruments.

v8 = v7 (making-and-matching against a schema, eye-hand episodes, a felt state driving the hand,
3D blockouts) + MEDIA: the paint is a pluggable module (studio/v8/media/), like an instrument in
Spectre. Oil behaves exactly as in v7. A canvas is created in one medium on one support; the
medium decides what a dab does, how paint dries and flows, how the surface looks, which tools
exist and what finishing means.

Commands (CANVAS env var selects a canvas name; default "main"):
  new "#RRGGBB" [W H] [--medium M] [--support S] [--style ID]   start a canvas (default 1200x1600, oil on canvas)
  media                         list the media, their tools, supports and finishing steps
  ref <file.svg|file.png>       set / revise the schema (rendered to canvas size)
  scene <scene.json> [overlay.svg] [quality]   render a 3D blockout as the schema (quality: draft|final)
  transfer [strength] [#color]  transfer the schema's contours lightly onto the canvas (like a cartoon)
  act '<json>' | act @file.json one episode: {"felt": {...}, "do": [intention, ...up to 4]}
  dry [0-1]                     let time pass
  look full|thumb|gray|crop X Y W H|ref|diff|compare|mirror|upside|squint|notan [2|3]|edges|temp|layers
  simplify FX FY [groups] [radius]   turn the schema into a painter's reference around a focal point
  report [style]                the canvas measured in numbers (value, colour, edges, texture, structure),
                                against the style's measured target (studio/targets.json) if it has one
  finish <op> ['<json>']        a finishing operation of the medium (varnish, fixative...)
  sign [auto|br|bl]             sign the finished painting ("Teodor"), the very last brush act
  timelapse                     build the time-lapse video from recorded frames
"""
import numpy as np, json, sys, math, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageFilter, ImageDraw
from scipy.ndimage import gaussian_filter, sobel, zoom
from media import MEDIA, get_medium
from media.base import hx, kmix

D = os.path.dirname(os.path.abspath(__file__))
NAME = os.environ.get("CANVAS", "main")
P = lambda s: os.path.join(D, f"{NAME}_{s}")
FRAMES = os.path.join(D, f"{NAME}_frames")


# ---------------------------------------------------------------- color
def shift_color(c, temp=0.0, sat=1.0, value=1.0):
    c = np.asarray(c, np.float32)
    if temp:
        c = c + np.array([0.06, 0.015, -0.06], np.float32) * temp
    g = c.mean(-1, keepdims=True)
    c = g + (c - g) * sat
    return np.clip(c * value, 0, 1)


# ---------------------------------------------------------------- canvas
class Canvas:
    """The canvas: its medium, support, apparent colour (col) and the medium's own state."""

    def __init__(self):
        mp = P("meta.json")
        self.meta = json.load(open(mp)) if os.path.exists(mp) else {"medium": "oil", "support": "canvas"}
        self.medium = get_medium(self.meta["medium"])
        self.col = np.load(P("col.npy")).astype(np.float32)
        self.H, self.W = self.col.shape[:2]
        for a in self.medium.arrays:
            if a == "col":
                continue
            fp = P(f"{a}.npy")
            setattr(self, a, np.load(fp).astype(np.float32) if os.path.exists(fp) else np.zeros((self.H, self.W), np.float32))
        tp = P("tex.npy")
        self.tex = np.load(tp) if os.path.exists(tp) else self.medium.texture(self.H, self.W, self.meta.get("support"))
        if not os.path.exists(tp):
            np.save(tp, self.tex.astype(np.float16))
        self.tex = self.tex.astype(np.float32)
        rp = P("ref.npy")
        self.ref = np.load(rp).astype(np.float32) if os.path.exists(rp) else None
        self.clip = None

    @staticmethod
    def new(ground, w=1200, h=1600, medium="oil", support=None):
        m = get_medium(medium)
        support = support or (list(m.supports)[0] if m.supports else None)
        if m.supports and support not in m.supports:
            sys.exit(f"{medium} has no support '{support}'. Available: {', '.join(m.supports)}")
        for f in os.listdir(D):
            if f.startswith(f"{NAME}_") and f.endswith(".npy") and not f.startswith(f"{NAME}_ref"):
                os.remove(os.path.join(D, f))
        col = np.ones((h, w, 3), np.float32) * hx(ground)
        rng = np.random.default_rng(1)
        n = gaussian_filter(rng.random((h, w, 3)).astype(np.float32), (40, 40, 0))
        n = (n - n.mean()) / (n.std() + 1e-6)
        if medium != "oil-v7":  # a ground's unevenness is in value, not hue (v7's coloured blotches kept only for the reference)
            n = n.mean(-1, keepdims=True) * 1.7
        col = np.clip(col + n * 0.012, 0, 1)
        json.dump({"medium": medium, "support": support, "ground": ground}, open(P("meta.json"), "w"))
        np.save(P("col.npy"), col.astype(np.float16))
        for f in ("ref.npy", "tex.npy", "log.jsonl"):
            if os.path.exists(P(f)):
                os.remove(P(f))
        os.makedirs(FRAMES, exist_ok=True)
        for f in os.listdir(FRAMES):
            os.remove(os.path.join(FRAMES, f))
        open(P("log.jsonl"), "w").close()
        cv = Canvas()
        m.init_state(cv, ground)
        cv.save()

    def save(self):
        json.dump(self.meta, open(P("meta.json"), "w"))
        np.save(P("col.npy"), np.clip(self.col, 0, 1).astype(np.float16))
        for a in self.medium.arrays:
            if a != "col":
                arr = getattr(self, a)
                if a == "ht":
                    arr = np.clip(arr, 0, 4)
                np.save(P(f"{a}.npy"), arr.astype(np.float16))

    def render(self):
        return self.medium.render(self)


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
    if hasattr(brush, "end"):
        brush.end(cv)


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


def make_brush(it, size, color, rng, cv=None):
    return (cv.medium if cv is not None else get_medium("oil")).make_tool(it, size, color, rng)


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
        b = make_brush(it, size, col, rng, cv)
        play(cv, b, gesture_path(ctrl, felt, rng, size), felt, it.get("pressure", 0.85), rng)


def do_strokes(cv, it, felt, rng):
    reg = it.get("region")
    cv.clip = region_mask(reg, cv.W, cv.H) if (reg and it.get("clip")) else None
    cols, w = palette(it) if it.get("colors") else ([hx("#888888")], np.array([1.0]))
    for s in it["strokes"]:
        size = s.get("size", np.mean(it.get("size", [6, 10])))
        col = hx(s["color"]) if s.get("color") else cols[rng.choice(len(cols), p=w)]
        b = make_brush(it, size, col, rng, cv)
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
        b = make_brush(it2, sz, col, rng, cv)
        play(cv, b, gesture_path(ctrl, felt, rng, sz), felt, it.get("pressure", 0.9), rng)


def do_hatch(cv, it, felt, rng):
    """Hatching, the way a draughtsman builds tone with lines: parallel strokes at an angle across a
    region, each layer covering only where the schema (or a flat `value`) is darker than its level;
    darker passages get more layers, each turned by `cross` degrees. Lines follow the hand (gesture
    path, speed profile, felt state); spacing and angle drift a little, never a ruler."""
    reg = it.get("region", {"type": "canvas"})
    mask = region_mask(reg, cv.W, cv.H)
    cv.clip = mask if it.get("clip") else None
    if cv.ref is None and "value" not in it:
        sys.exit("hatch needs a schema (ref) or a flat 'value' (0 dark .. 1 light).")
    val = gaussian_filter(cv.ref.mean(-1), 3) if cv.ref is not None and "value" not in it else np.full((cv.H, cv.W), float(it["value"]), np.float32)
    layers = it.get("layers", [0.75, 0.55, 0.35, 0.18])
    cross = it.get("cross", 45)
    spacing = it.get("spacing", 9)
    size = float(np.mean(it.get("size", [3, 3]))) if isinstance(it.get("size", 3), list) else float(it.get("size", 3))
    seg_max = it.get("length", 140)
    cols, w = palette(it) if it.get("colors") else ([hx("#2a2a2a")], np.array([1.0]))
    if mask is not None:
        ys, xs = np.nonzero(mask > 0.5)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    else:
        x0, x1, y0, y1 = 0, cv.W - 1, 0, cv.H - 1
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = math.hypot(x1 - x0, y1 - y0) / 2 + spacing
    n = 0
    for li, level in enumerate(layers):
        ang = math.radians(it.get("angle", 50) + li * cross + rng.normal(0, 2))
        dx, dy = math.cos(ang), math.sin(ang)
        nx, ny = -dy, dx
        off = -R + rng.uniform(0, spacing)
        while off < R:
            sp = spacing * rng.uniform(0.85, 1.15)
            px, py = cx + nx * off, cy + ny * off
            t, run = -R, []
            while t <= R:
                x, y = px + dx * t, py + dy * t
                ok = 0 <= x < cv.W and 0 <= y < cv.H and (mask is None or mask[int(y), int(x)] > 0.5) and val[int(y), int(x)] < level
                if ok:
                    run.append([x, y])
                if (not ok or len(run) * 3 >= seg_max) and len(run) >= 3:
                    a, b = run[0], run[-1]
                    a = [a[0] + rng.normal(0, 1.5), a[1] + rng.normal(0, 1.5)]
                    ctrl = [a, [(a[0] + b[0]) / 2 + rng.normal(0, 0.8), (a[1] + b[1]) / 2 + rng.normal(0, 0.8)], b]
                    col = np.clip(cols[rng.choice(len(cols), p=w)] + rng.normal(0, 0.01, 3), 0, 1)
                    br = make_brush(it, size * rng.uniform(0.85, 1.15), col, rng, cv)
                    play(cv, br, gesture_path(ctrl, felt, rng, size), felt, it.get("pressure", 0.8), rng)
                    n += 1
                    run = []
                elif not ok:
                    run = []
                t += 3
            off += sp
            if n > it.get("max_strokes", 1500):
                return


def do_glaze(cv, it, felt, rng):
    reg = it.get("region", {"type": "canvas"})
    mask = region_mask(reg, cv.W, cv.H, feather=it.get("feather", 30))
    if mask is None:
        mask = np.ones((cv.H, cv.W), np.float32)
    try:
        cv.medium.glaze(cv, mask, hx(it["color"]), it.get("opacity", 0.25), it)
    except TypeError:
        cv.medium.glaze(cv, mask, hx(it["color"]), it.get("opacity", 0.25))


def do_blend(cv, it, felt, rng):
    it = dict(it); it["brush"] = "blend"
    if "strokes" in it:
        do_strokes(cv, it, felt, rng)
    else:
        do_free(cv, it, felt, rng)


INTENT = {"free": do_free, "strokes": do_strokes, "match": do_match, "glaze": do_glaze, "blend": do_blend, "hatch": do_hatch}


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


def simplify(cv, fx, fy, groups=4, radius=0.25, keep=1.0):
    """Turn the schema into a painter's reference: values grouped into `groups` masses (colour kept
    within each mass), and detail and edges softened with distance from the focal point (fx, fy).
    Inside `radius` (fraction of the canvas diagonal) the schema is kept as it is (times `keep`)."""
    ref = cv.ref
    L = ref.mean(-1)
    qs = np.quantile(L, [i / groups for i in range(1, groups)])
    lab = np.digitize(gaussian_filter(L, 3), qs)
    grouped = np.zeros_like(ref)
    for g in range(groups):
        m = (lab == g)
        if m.any():
            grouped[m] = ref[m] * 0.45 + ref[m].mean(0) * 0.55
    yy, xx = np.mgrid[0:cv.H, 0:cv.W].astype(np.float32)
    diag = math.hypot(cv.W, cv.H)
    d = np.hypot(xx - fx, yy - fy) / diag
    w = np.clip((d - radius) / max(radius, 1e-3), 0, 1)[..., None]
    soft = np.stack([gaussian_filter(grouped[..., i], 18) for i in range(3)], -1)
    far = grouped * 0.25 + soft * 0.75
    near = ref * keep + grouped * (1 - keep)
    out = near * (1 - w) + far * w
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(P("simplified.png"))
    set_ref(cv, P("simplified.png"))


def transfer(cv, strength, color="#4a3a2e"):
    lum = gaussian_filter(cv.ref.mean(-1), 1.5)
    e = np.hypot(sobel(lum, 0), sobel(lum, 1))
    e = np.clip(e / (np.percentile(e, 99) + 1e-6), 0, 1) ** 1.5
    line = hx(color)
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
    elif mode == "mirror":
        s = img.transpose(Image.FLIP_LEFT_RIGHT).resize((vw, vh), Image.LANCZOS)
    elif mode == "upside":
        s = img.rotate(180).resize((vw, vh), Image.LANCZOS)
    elif mode == "squint":
        s = img.resize((cv.W // 16, cv.H // 16), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2)).resize((vw, vh), Image.BICUBIC)
    elif mode == "notan":
        k = int(args[0]) if args else 2
        g = gaussian_filter(np.asarray(img.convert("L"), np.float32) / 255, 3)
        qs = np.quantile(g, [i / k for i in range(1, k)])
        lv = np.digitize(g, qs).astype(np.float32) / max(k - 1, 1)
        s = Image.fromarray((lv * 255).astype(np.uint8)).resize((vw, vh), Image.NEAREST).convert("RGB")
    elif mode == "edges":
        g = gaussian_filter(np.asarray(img.convert("L"), np.float32) / 255, 1.2)
        e = np.hypot(sobel(g, 0), sobel(g, 1))
        e = np.clip(e / (np.percentile(e, 99.5) + 1e-6), 0, 1) ** 0.8
        s = Image.fromarray(((1 - e) * 255).astype(np.uint8)).resize((vw, vh), Image.LANCZOS).convert("RGB")
    elif mode == "temp":
        a = np.asarray(img, np.float32) / 255
        t = gaussian_filter((a[..., 0] - a[..., 2]), 4)
        sat = gaussian_filter(a.max(-1) - a.min(-1), 4)
        warm = np.clip(t * 3, 0, 1); cool = np.clip(-t * 3, 0, 1)
        out = np.stack([0.5 + 0.5 * warm - 0.35 * cool, 0.5 + 0.1 * warm - 0.1 * cool, 0.5 + 0.5 * cool - 0.35 * warm], -1)
        out = 0.5 + (out - 0.5) * (0.4 + 0.6 * np.clip(sat * 2.5, 0, 1))[..., None]
        s = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).resize((vw, vh), Image.LANCZOS)
    elif mode == "layers":
        pp = P("passes.npy")
        n = np.load(pp).astype(np.float32) if os.path.exists(pp) else np.zeros((cv.H, cv.W), np.float32)
        lv = np.clip(n / 6.0, 0, 1)
        g = np.asarray(img.convert("L"), np.float32) / 255
        rgb = np.stack([0.25 + 0.75 * lv, 0.25 + 0.5 * lv * (1 - lv) * 4 * 0.5 + 0.2 * lv, 0.6 * (1 - lv)], -1) * (0.55 + 0.45 * g[..., None])
        s = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).resize((vw, vh), Image.LANCZOS)
        print(f"passes: one or none {float((n <= 1).mean()):.0%} of the canvas, two or three {float(((n >= 2) & (n <= 3)).mean()):.0%}, four or more {float((n >= 4).mean()):.0%}")
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
def media_list():
    for k, m in MEDIA.items():
        print(f"{k}: supports {', '.join(m.supports) or '-'}")
        for t, d in m.tools.items():
            print(f"    tool {t}: {d}")
        for t, d in m.finishes.items():
            print(f"    finish {t}: {d}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "new":
        args = sys.argv[2:]
        opt = {}
        for key in ("--medium", "--support", "--style"):
            if key in args:
                i = args.index(key); opt[key[2:]] = args[i + 1]; del args[i:i + 2]
        g = args[0] if args else "#c8b89a"
        wh = list(map(int, args[1:3])) if len(args) > 2 else [1200, 1600]
        Canvas.new(g, *wh, medium=opt.get("medium", "oil"), support=opt.get("support"))
        if opt.get("style"):
            mp = P("meta.json"); meta = json.load(open(mp)); meta["style"] = opt["style"]; json.dump(meta, open(mp, "w"))
        cv = Canvas(); record(cv); print(P("view.png")); sys.exit()
    if cmd == "media":
        media_list(); sys.exit()
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
    if cmd == "report":
        import eyes
        style = sys.argv[2] if len(sys.argv) > 2 else cv.meta.get("style")
        tp = next((t for t in (os.path.join(D, "targets.json"), os.path.join(D, "..", "targets.json")) if os.path.exists(t)), "")
        targets = json.load(open(tp)) if os.path.exists(tp) else {}
        target = targets.get(style) if style else None
        m = eyes.measure(cv.render())
        print(eyes.format_report(m, target, style if target else (f"{style} (no measured target yet)" if style else None)))
        json.dump(m, open(P("report.json"), "w"), indent=1)
        sys.exit()
    if cmd == "simplify":
        a = sys.argv[2:]
        simplify(cv, float(a[0]), float(a[1]), int(a[2]) if len(a) > 2 else 4, float(a[3]) if len(a) > 3 else 0.25)
        look(cv, "ref", []); sys.exit()
    if cmd == "transfer" and hasattr(cv.medium, "transfer"):
        cv.medium.transfer(cv, float(sys.argv[2]) if len(sys.argv) > 2 else 0.35, sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "transfer":
        transfer(cv, float(sys.argv[2]) if len(sys.argv) > 2 else 0.35, sys.argv[3] if len(sys.argv) > 3 else "#4a3a2e")
    elif cmd == "sign":
        if hasattr(cv.medium, "sign"):
            cv.medium.sign(cv, sys.argv[2] if len(sys.argv) > 2 else "auto")
        else:
            sys.path.insert(0, os.path.join(D, "..")); sys.path.insert(0, D)
            from signature import sign_array
            sign_array(cv.col, sys.argv[2] if len(sys.argv) > 2 else "auto")
    elif cmd == "dry":
        cv.medium.dry(cv, float(sys.argv[2]) if len(sys.argv) > 2 else 0.9)
    elif cmd == "finish":
        params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        cv.medium.finish(cv, sys.argv[2], params)
        with open(P("log.jsonl"), "a") as f:
            f.write(json.dumps({"finish": sys.argv[2], "params": params}) + "\n")
    elif cmd == "act":
        arg = sys.argv[2]
        ep = json.load(open(arg[1:])) if arg.startswith("@") else json.loads(arg)
        felt = Felt(ep.get("felt"))
        todo = ep.get("do", [])
        todo = todo if isinstance(todo, list) else [todo]
        if len(todo) > 4:
            sys.exit("An episode holds at most 4 intentions; look again before continuing.")
        nlog = sum(1 for _ in open(P("log.jsonl")))
        before = cv.col.copy()
        for k, it in enumerate(todo):
            rng = np.random.default_rng(it.get("seed", nlog * 131 + k * 17 + 3))
            INTENT[intent_kind(it)](cv, it, felt, rng)
            cv.clip = None
        cv.medium.episode_end(cv)
        pp = P("passes.npy")
        passes = np.load(pp).astype(np.float32) if os.path.exists(pp) else np.zeros((cv.H, cv.W), np.float32)
        passes += (np.abs(cv.col - before).sum(-1) > 0.04)
        np.save(pp, np.clip(passes, 0, 255).astype(np.uint8))
        with open(P("log.jsonl"), "a") as f:
            f.write(json.dumps(ep) + "\n")
    cv.save()
    record(cv)
    print(P("view.png"))
