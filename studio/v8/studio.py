"""Studio v8 - the painting studio with media as instruments.

v8 = v7 (making-and-matching against a schema, eye-hand episodes, a felt state driving the hand,
3D blockouts) + MEDIA: the paint is a pluggable module (studio/v8/media/), like an instrument in
Spectre. Oil behaves exactly as in v7. A canvas is created in one medium on one support; the
medium decides what a dab does, how paint dries and flows, how the surface looks, which tools
exist and what finishing means.

Commands (CANVAS env var selects a canvas name; default "main"):
  new "#RRGGBB" [W H] [--medium M] [--support S] [--style ID] [--px-per-mm N]   start a canvas (default 1200x1600, oil on canvas)
  media                         list the media, their tools, supports and finishing steps
  ref <file.svg|file.png>       set / revise the schema (rendered to canvas size)
  scene <scene.json> [overlay.svg] [quality]   render a 3D blockout as the schema (quality: draft|final)
  transfer [strength] [#color]  transfer the schema's contours lightly onto the canvas (like a cartoon)
  act '<json>' | act @file.json one episode: {"felt": {...}, "do": [intention, ...up to 4]}
  dry [0-1]                     let time pass
  look full|thumb|gray|crop X Y W H|ref|diff|compare|mirror|upside|squint|notan [2|3]|edges|temp|layers [ROLE]
  simplify FX FY [groups] [radius]   turn the schema into a painter's reference around a focal point
  focus FX FY                   declare the focal point (stroke size, focal checks)
  elements [file.json]          declare the picture's elements for the clarity check (or list them)
  report [style] [finish]       the canvas measured in numbers (value, colour, edges, texture, structure, marks,
                                layers, elements), against the style's measured target (studio/targets.json) if it
                                has one; `finish` adds the finishing check
  finish <op> ['<json>']        a finishing operation of the medium (varnish, fixative...)
  sign [auto|br|bl]             sign the finished painting ("Teodor"), the very last brush act
  timelapse                     build the time-lapse video from recorded frames
  detail open X Y W H [--scale N] [--margin M] | close [--resample area|sample] | cancel   a detail pass (detail.py): the region at N x;
                                work in it with --detail on any command (or CANVAS=<name>_detail); look detail
"""
import numpy as np, json, sys, math, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageFilter, ImageDraw
from scipy.ndimage import gaussian_filter, sobel, zoom
from media import MEDIA, get_medium
from media.base import hx, kmix

D = os.path.dirname(os.path.abspath(__file__))
NAME = os.environ.get("CANVAS", "main")
if "--detail" in sys.argv:            # run the command on this canvas's open detail (detail.py: <name>_detail)
    sys.argv.remove("--detail")
    if not NAME.endswith("_detail"):
        NAME = NAME + "_detail"
_PXS = 1.0      # px per canvas px of the loaded canvas: 1 on a canvas, N in an N x detail (physical sizes in the hand)
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
        global _PXS
        self.px_scale = _PXS = float(self.meta.get("px_scale", 1.0))
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
    def new(ground, w=1200, h=1600, medium="oil", support=None, extra=None):
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
        json.dump(dict({"medium": medium, "support": support, "ground": ground}, **(extra or {})), open(P("meta.json"), "w"))
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
            k = int(1 + jag * ln / max(size * 2.5, 8 * _PXS))
            for j in range(1, k + 1):
                p = a + dvec * j / (k + 1) + nrm * rng.normal(0, 1) * jag * size * 1.2
                new.append(list(p))
            new.append(list(b))
        ctrl = new
    pts = []
    spacing = max(0.7 * _PXS, size * 0.1)       # in a detail: the same points per canvas px as on the canvas
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
        trem = felt.tension * (1 - felt.care * 0.6) * size * 0.22 + felt.arousal * 0.6 * _PXS
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
    steps = max(5, int(L / max(0.5 * _PXS, brush.size * 0.055) * (1.25 - 0.35 * speed_scale)))
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
_SEG_CACHE = {}


def _schema_for_segments(W, H):
    """The current canvas's schema (its ref.npy), cached by modification time, for `segment` regions."""
    rp = P("ref.npy")
    if not os.path.exists(rp):
        sys.exit("a 'segment' region needs a schema: set one with the ref command first.")
    k = (rp, os.path.getmtime(rp))
    if _SEG_CACHE.get("key") != k:
        _SEG_CACHE.clear()
        _SEG_CACHE["key"] = k
        _SEG_CACHE["ref"] = np.load(rp).astype(np.float32)
    ref = _SEG_CACHE["ref"]
    if ref.shape[:2] != (H, W):
        sys.exit(f"a 'segment' region: the schema is {ref.shape[1]}x{ref.shape[0]}, the canvas {W}x{H}.")
    return ref


def segment_mask(reg, W, H):
    """A region cut from the schema: the connected area of similar value (or colour) around one or more points.
    {"type": "segment", "at": [x, y] | [[x, y], ...], "by": "value" | "colour", "tol": 0.08 (value, 0-1) or 10
    (colour, CIELAB delta E), "blur": 2 (px, smooths the schema first), "grow": 0 (px; negative shrinks),
    "holes": false (true fills the holes inside the area)}. Each point's area is the 8-connected set of pixels within
    `tol` of the schema's value or colour at that point; several points join their areas. Defaults are judgements."""
    from scipy.ndimage import label, binary_fill_holes, binary_dilation, binary_erosion
    ref = _schema_for_segments(W, H)
    pts = reg.get("at")
    if not pts:
        sys.exit('a segment region needs "at": [x, y] (a point inside the area), or a list of points.')
    pts = [pts] if isinstance(pts[0], (int, float)) else pts
    by = str(reg.get("by", "value")).lower()
    bl = float(reg.get("blur", 2.0))
    ck = ("seg", by, bl)
    if ck not in _SEG_CACHE:
        if by.startswith("col"):
            import eyes
            L, a, b = eyes._srgb_to_lab(np.clip(ref, 0, 1))
            f = np.stack([L, a, b], -1).astype(np.float32)
        else:
            f = ref.mean(-1, keepdims=True)
        _SEG_CACHE[ck] = np.stack([gaussian_filter(f[..., i], bl) for i in range(f.shape[-1])], -1) if bl > 0 else f
    f = _SEG_CACHE[ck]
    tol = float(reg.get("tol", 10.0 if by.startswith("col") else 0.08))
    out = np.zeros((H, W), bool)
    for p in pts:
        x, y = int(np.clip(round(p[0]), 0, W - 1)), int(np.clip(round(p[1]), 0, H - 1))
        seed = np.median(f[max(0, y - 1):y + 2, max(0, x - 1):x + 2].reshape(-1, f.shape[-1]), 0)
        near = np.sqrt(((f - seed) ** 2).sum(-1)) <= tol
        lab, _ = label(near, structure=np.ones((3, 3)))
        if lab[y, x]:
            out |= lab == lab[y, x]
    if reg.get("holes"):
        out = binary_fill_holes(out)
    g = int(reg.get("grow", 0))
    if g > 0:
        out = binary_dilation(out, iterations=g)
    elif g < 0:
        out = binary_erosion(out, iterations=-g)
    return out


def region_mask(reg, W, H, feather=1.0):
    t = reg.get("type", "canvas")
    if t == "canvas":
        return None
    if t == "segment":
        return gaussian_filter(segment_mask(reg, W, H).astype(np.float32), feather)
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
        elif t == "segment" and mask is not None:
            # a point of the segment itself (a small segment would rarely be hit by sampling the whole canvas)
            if _SEG_CACHE.get("pts_mask") is not mask:          # (holding the mask keeps its identity unique)
                _SEG_CACHE["pts_mask"], _SEG_CACHE["pts"] = mask, np.nonzero(mask > 0.5)
            yy, xx = _SEG_CACHE["pts"]
            if len(xx) == 0:
                return W / 2, H / 2
            i = int(rng.integers(len(xx)))
            x, y = float(xx[i]) + rng.random(), float(yy[i]) + rng.random()
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
    if cv is not None and getattr(cv, "px_scale", 1.0) != 1.0:     # a detail: the tool keeps its physical features
        it = dict(it, _px_scale=cv.px_scale)
    return (cv.medium if cv is not None else get_medium("oil")).make_tool(it, size, color, rng)


def palette(it):
    cs = it.get("colors", ["#888888"])
    cols = [hx(c[0]) if isinstance(c, list) else hx(c) for c in cs]
    w = np.array([c[1] if isinstance(c, list) else 1.0 for c in cs], float)
    return cols, w / w.sum()


# ---------------------------------------------------------------- intentions
def rng2(v, default):
    """A [min, max] parameter that also accepts a single number (min = max)."""
    v = default if v is None else v
    if isinstance(v, (int, float)):
        return float(v), float(v)
    return float(v[0]), float(v[-1])


def do_free_v7(cv, it, felt, rng):
    reg = it.get("region", {"type": "canvas"})
    cv.clip = region_mask(reg, cv.W, cv.H) if it.get("clip") else None
    mask = region_mask(reg, cv.W, cv.H)
    cols, w = palette(it)
    smin, smax = rng2(it.get("size"), [8, 14])
    lmin, lmax = rng2(it.get("length"), [20, 60])
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


def do_strokes_v7(cv, it, felt, rng):
    reg = it.get("region")
    cv.clip = region_mask(reg, cv.W, cv.H) if (reg and it.get("clip")) else None
    cols, w = palette(it) if it.get("colors") else ([hx("#888888")], np.array([1.0]))
    for s in it["strokes"]:
        size = s.get("size", np.mean(it.get("size", [6, 10])))
        col = hx(s["color"]) if s.get("color") else cols[rng.choice(len(cols), p=w)]
        b = make_brush(it, size, col, rng, cv)
        play(cv, b, gesture_path(s["pts"], felt, rng, size), felt, s.get("pressure", it.get("pressure", 0.85)), rng)


def do_match_v7(cv, it, felt, rng):
    """Making and matching: compare the canvas with the schema at this brush scale and lay
    strokes where they differ most, colored from the schema (as the painter interprets it),
    following the form (perpendicular to the schema's value gradient)."""
    if cv.ref is None:
        sys.exit("No schema yet: use the ref command first.")
    reg = it.get("region", {"type": "canvas"})
    mask = region_mask(reg, cv.W, cv.H)
    cv.clip = mask if it.get("clip") else None
    smin, smax = rng2(it.get("size"), [20, 40])
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
    lmin, lmax = rng2(it.get("length"), [size * 1.5, size * 5])
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


# ================================================================ studio v8 core additions (2026-11-26)
# Everything below this line up to do_hatch is the v8 hand, the layer roles and the revision tools. The
# frozen reference medium oil-v7 never reaches it: its intentions run the *_v7 functions above, unchanged, so
# test_v8.py can check it bit for bit against studio v7.
LEGACY_MEDIA = ("oil-v7",)


def legacy(cv):
    return cv.medium.name in LEGACY_MEDIA


# ---------------------------------------------------------------- layer roles
# What each layer of a passage does, from the studio practice in docs/research/process.md (2.3, 2.6: the
# monochrome lay-in or ebauche, Dutch dead colouring, pentimenti and revision), docs/FINISHING.md (last accents,
# edge pass) and the process lists of the researched currents (docs/styles/*.md). National Gallery glossary:
# an imprimatura is "a thin, translucent layer of colour applied to the ground before painting on it"; a scumble
# is "a thinly applied paint layer which is lighter in tone than the underlying colour" (a glaze is darker).
# "contour" was added from the currents' own processes: lines restated over the colour at the end (Fauvism's
# thin dark contours, Expressionism's dark contours last, ukiyo-e's key line over the colour, the icon painter's
# restored final lines); "drawing" is the underdrawing that comes first.
ROLES = ("underpainting", "drawing", "dead_colour", "body", "glaze", "scumble", "wash", "hatch", "accent",
         "contour", "correction")
ROLE_BIT = {r: 1 << i for i, r in enumerate(ROLES)}
ROLE_ALIAS = {"imprimatura": "underpainting", "ebauche": "underpainting", "verdaccio": "underpainting",
              "grisaille": "underpainting", "dead colour": "dead_colour", "dead-colour": "dead_colour",
              "dead_color": "dead_colour", "dead colouring": "dead_colour", "lay-in": "dead_colour",
              "block-in": "dead_colour", "body colour": "body", "impasto": "body", "underdrawing": "drawing",
              "line": "contour", "keyline": "contour", "key line": "contour", "outline": "contour",
              "highlight": "accent", "revision": "correction", "scrape": "correction", "wipe": "correction"}
ROLE_COLOR = {"underpainting": "#8a5a2b", "drawing": "#3b3b3b", "dead_colour": "#b08d57", "body": "#d9452b",
              "glaze": "#7b2d8e", "scumble": "#9fc5e8", "wash": "#3d85c6", "hatch": "#38761d", "accent": "#ffd966",
              "contour": "#111d4a", "correction": "#e06666"}
ROLE_GRID = 8          # role order is kept per 8x8 px cell (first intention that used each role there)
REMOVERS = ("rag", "scraper", "lift", "eraser", "kneaded", "precision_eraser", "electric_eraser", "cloth", "tissue")
LINERS = ("liner", "rigger", "pen", "nib", "pencil", "key", "line", "keyblock", "detail_round", "stylus")
# a glaze in each medium is a different layer: a wash in watercolour and ink, a printed flat block in a woodcut.
# A medium can say so itself with a `glaze_role` attribute (hook for media the core does not know).
GLAZE_ROLE = {"watercolour": "wash", "ink": "wash", "woodblock": "body"}
# the first marks on bare paper in the drawing media and ink are the drawing (a charcoal block-in, an ink outline);
# hook for media the core does not know: a `first_role` attribute
FIRST_ROLE = {"charcoal": "drawing", "graphite": "drawing", "ink": "drawing", "watercolour": "wash"}


def norm_role(r):
    if r is None:
        return None
    k = str(r).strip().lower()
    k = ROLE_ALIAS.get(k, k).replace(" ", "_")
    if k not in ROLE_BIT:
        sys.exit(f"Unknown role '{r}'. Roles: {', '.join(ROLES)} (aliases: {', '.join(sorted(ROLE_ALIAS))})")
    return k


def load_roles(cv):
    rp, fp = P("roles.npy"), P("rolefirst.npy")
    gh, gw = -(-cv.H // ROLE_GRID), -(-cv.W // ROLE_GRID)
    bits = np.load(rp).astype(np.uint16) if os.path.exists(rp) else np.zeros((cv.H, cv.W), np.uint16)
    first = np.load(fp).astype(np.int32) if os.path.exists(fp) else np.full((len(ROLES), gh, gw), -1, np.int32)
    return bits, first


def save_roles(bits, first):
    np.save(P("roles.npy"), bits.astype(np.uint16))
    np.save(P("rolefirst.npy"), first.astype(np.int32))


def record_role(cv, role, changed, order):
    """Mark the pixels this intention changed with its role, and the order of first use per cell."""
    if role is None or not changed.any():
        return
    bits, first = load_roles(cv)
    bits[changed] |= ROLE_BIT[role]
    gh, gw = first.shape[1:]
    pad = np.zeros((gh * ROLE_GRID, gw * ROLE_GRID), bool)
    pad[:cv.H, :cv.W] = changed
    cell = pad.reshape(gh, ROLE_GRID, gw, ROLE_GRID).any((1, 3))
    f = first[ROLES.index(role)]
    f[cell & (f < 0)] = order
    save_roles(bits, first)


def _bare_share(cv, it, kind, keep=("drawing", "underpainting")):
    """Share of the intention's area that holds no colour layer yet (only the ground and the roles in `keep`)."""
    bits, _ = load_roles(cv)
    k = 0
    for r in keep:
        k |= ROLE_BIT[r]
    colour = bits & ~np.uint16(k)
    if kind == "strokes":
        pts = [p for st in it.get("strokes", []) for p in st.get("pts", [])]
        if not pts:
            return 1.0
        v = [colour[int(np.clip(y, 0, cv.H - 1)), int(np.clip(x, 0, cv.W - 1))] == 0 for x, y in (p[:2] for p in pts)]
        return float(np.mean(v))
    m = region_mask(it.get("region", {"type": "canvas"}), cv.W, cv.H)
    sel = (colour == 0)
    return float(sel.mean()) if m is None else float(sel[m > 0.5].mean()) if (m > 0.5).any() else 1.0


def _colors_of(it):
    cs = list(it.get("colors") or [])
    cs += [st["color"] for st in it.get("strokes", []) if st.get("color")]
    out = []
    for c in cs:
        try:
            out.append(hx(c[0] if isinstance(c, list) else c))
        except Exception:
            pass
    return out


def infer_role(cv, it, kind):
    """The role of an intention: the one it names, else inferred from what it is (docs/MANUAL.md "Layers")."""
    if it.get("role"):
        return norm_role(it["role"])
    if kind in REVISIONS:
        return "correction"
    if kind == "glaze":
        return getattr(cv.medium, "glaze_role", GLAZE_ROLE.get(cv.medium.name, "glaze"))
    if kind == "hatch":
        return "hatch"
    if kind in ("blend", "element"):
        return None                       # blending softens what is there; it lays no new layer
    brush = str(it.get("brush", "")).lower()
    if brush in REMOVERS:
        return "correction"
    if it.get("articulation") == "scumble" or brush in ("scumble",):
        return "scumble"
    if kind == "model":
        return "body"
    bare = _bare_share(cv, it, kind)
    ground = _bare_share(cv, it, kind, keep=("drawing",))      # nothing but the ground or a drawing
    cols = _colors_of(it)
    if brush in LINERS:
        if ground > 0.6:
            return "drawing"
        dark = bool(cols) and float(np.mean([c.mean() for c in cols])) < 0.35
        return "contour" if dark else "accent"
    if cv.medium.name in ("watercolour", "ink") and brush in ("mop", "flat", "wash", "hake", "side"):
        return "wash"
    if kind == "strokes" and len(it.get("strokes", [])) <= 12 and ground < 0.5:
        sizes = [float(st.get("size", np.mean(it.get("size", [6, 10])))) for st in it["strokes"]]
        if np.mean(sizes) <= 0.012 * canvas_diag(cv):
            lens = [sum(math.dist(a[:2], b[:2]) for a, b in zip(st["pts"], st["pts"][1:])) for st in it["strokes"]]
            dark = bool(cols) and float(np.mean([c.mean() for c in cols])) < 0.35
            return "contour" if dark and np.mean(lens) > 15 * np.mean(sizes) else "accent"
    if bare > 0.6:
        first = getattr(cv.medium, "first_role", FIRST_ROLE.get(cv.medium.name))
        if first:
            return first
        if cols and len(cols) <= 2:
            # a monochrome lay-in: one or two colours of one muted hue family (an earth, a grey, a verdaccio)
            ch = [float(c.max() - c.min()) for c in cols]
            hues = [math.atan2(math.sqrt(3) * (c[1] - c[2]), 2 * c[0] - c[1] - c[2]) for c in cols]
            same = len(cols) == 1 or ch[0] < 0.06 or ch[1] < 0.06 or abs((hues[0] - hues[1] + math.pi) % (2 * math.pi) - math.pi) < 0.6
            if max(ch) < 0.3 and same:
                return "underpainting"
        return "dead_colour"
    if brush == "dry" or float(it.get("load", 1.0)) < 0.45:
        return "scumble"
    return "body"


# ---------------------------------------------------------------- the v8 hand
# Research basis (docs/MANUAL.md "The hand"): painters build a stroke from load, pressure and speed that change
# along it, and a passage from strokes whose size, pressure, angle and colour drift together, not from
# independent random dabs. Studio vocabulary: a loaded stroke dragged until the paint runs out (dry-brush), the
# calligraphic stroke that swells and tapers, the scumble (thin, broken, scrubbed over what is beneath; National
# Gallery glossary), the flick (fast, lifting off to a point). Correlated, smoothly drifting variation instead of
# independent jitter follows Hennig et al. 2011 (PLoS ONE 6(10): e26457: listeners, above all experienced ones,
# preferred long-range correlated timing fluctuations to random ones), the finding Spectre's humaniser adopted
# (docs/research/process.md 1.8). Selective detail by distance from the focus follows DiPaola, Riebe & Enns 2010
# (docs/research/process.md 2.5). Strokes follow the form's direction (Hertzmann 1998; docs/research.md).
# Every number in the profiles, mixes and multipliers below is a judgement tuned by eye on test canvases
# (docs/gallery/core_strokes_after.jpg), not a measurement, unless a comment says otherwise.
ARTICULATIONS = ("plain", "drag", "swell", "scumble", "flick")
AUTO_MIX = {   # which articulations a role's strokes use when the intention says "auto" (eye)
    "underpainting": {"drag": 0.55, "scumble": 0.25, "plain": 0.2},
    "dead_colour": {"drag": 0.5, "plain": 0.25, "swell": 0.25},
    "body": {"swell": 0.4, "drag": 0.35, "plain": 0.25},
    "scumble": {"scumble": 1.0},
    "accent": {"swell": 0.5, "flick": 0.5},
    "contour": {"swell": 0.8, "flick": 0.2},
    "drawing": {"swell": 0.6, "plain": 0.2, "flick": 0.2},
    "hatch": {"plain": 0.5, "flick": 0.5},
    "glaze": {"swell": 0.5, "plain": 0.5}, "wash": {"swell": 0.5, "plain": 0.5},
    "correction": {"plain": 1.0},
}
ROLE_SIZE = {"underpainting": 1.3, "dead_colour": 1.2, "scumble": 1.15, "accent": 0.6, "contour": 0.7, "drawing": 0.6}  # eye
FOCUS_NEAR, FOCUS_FAR, FOCUS_REACH = 0.65, 1.35, 0.4   # size multiplier at the focus, at FOCUS_REACH x diagonal and beyond (eye)
WAVE = 0.12            # a slow pressure wave along each stroke (amplitude; eye)
SCUMBLE_LOAD = 0.5     # a scumble's brush carries about half a full load (eye)
DRAG_DEPLETE = 2.4     # a dragged stroke runs out this many times faster (oil reads `deplete_mul`; eye)


def artic_profile(art, t, ph):
    """(pressure multiplier, width multiplier, extra dry-brush speed) at fraction t of the stroke."""
    t = min(max(t, 0.0), 1.0)
    if art == "drag":            # loaded at the start, paint running out: lighter, narrower, breaking up
        return 1.08 - 0.32 * t, 1.0 - 0.12 * t, 0.2 * t * t
    if art == "swell":           # press into the belly, lift to the tip at both ends
        sw = math.sin(math.pi * t) ** 0.7
        return 0.45 + 0.65 * sw, 0.55 + 0.55 * sw, 0.0
    if art == "scumble":         # light, scrubbed, broken over the texture beneath
        return 0.6 + 0.1 * math.sin(ph + 9 * t), 1.25, 0.2
    if art == "flick":           # fast: full at the start, lifting off to a point
        f = 1.0 if t < 0.3 else max(0.04, 1 - (t - 0.3) / 0.7) ** 1.6
        return f, 0.6 + 0.4 * f, 0.3 * t
    return 1.0, 1.0, 0.0


class Drift:
    """Smooth variation across a passage: each channel is a sum of a few long sine waves over the canvas (a
    spatial field with correlation length `scale` px) plus an AR(1) process over the stroke order (rho 0.8), so
    neighbouring strokes vary together and the passage drifts instead of jittering. Values are about N(0, 1)."""
    CH = ("size", "press", "load", "angle", "value", "temp", "sat", "art", "edge")

    def __init__(self, rng, scale, rho=0.8):
        self.rng, self.rho = rng, rho
        self.c, self.ar = {}, {}
        for ch in self.CH:
            k = 4
            f = rng.uniform(0.5, 1.5, k) / max(scale, 8.0) * 2 * math.pi
            th = rng.uniform(0, 2 * math.pi, k)
            a = rng.uniform(0.5, 1.0, k)
            a = a / math.sqrt((a * a).sum() / 2)
            self.c[ch] = (f * np.cos(th), f * np.sin(th), rng.uniform(0, 2 * math.pi, k), a)
            self.ar[ch] = float(rng.normal())

    def __call__(self, ch, x, y):
        fx, fy, ph, a = self.c[ch]
        sp = float((a * np.sin(fx * x + fy * y + ph)).sum())
        return 0.8 * sp + 0.6 * self.ar[ch]

    def next(self):
        for ch in self.CH:
            self.ar[ch] = self.rho * self.ar[ch] + math.sqrt(1 - self.rho ** 2) * float(self.rng.normal())


def new_drift(rng, it, cv, size):
    reg = it.get("region", {"type": "canvas"})
    m = region_mask(reg, cv.W, cv.H)
    if m is not None and (m > 0.5).any():
        ys, xs = np.nonzero(m > 0.5)
        ext = math.hypot(xs.max() - xs.min(), ys.max() - ys.min())
    else:
        ext = math.hypot(cv.W, cv.H)
    return Drift(np.random.default_rng(int(rng.integers(1 << 31))), max(ext * 0.35, size * 6))


def drift_colour(col, dr, x, y, amt):
    """Colour variation that drifts across the passage (value, temperature, saturation) plus a little noise."""
    c = shift_color(col, temp=amt * 10 * dr("temp", x, y), sat=1 + amt * 3 * dr("sat", x, y), value=1 + amt * 1.1 * dr("value", x, y))
    return np.clip(c + dr.rng.normal(0, amt * 0.3, 3), 0, 1)


def canvas_diag(cv):
    """The canvas's diagonal in this canvas's px (in a detail: the whole canvas's, at the detail's scale)."""
    return float(cv.meta.get("diag") or math.hypot(cv.W, cv.H))


def focus_of(cv, it):
    f = it.get("focus") or cv.meta.get("focus")
    return (float(f[0]), float(f[1])) if f else None


def size_mul(cv, it, x, y, role):
    """Stroke size by role (lay-ins broad, accents and lines small) and by distance from the declared focus
    (finer near it, broader away from it)."""
    m = ROLE_SIZE.get(role, 1.0) if it.get("role_scale", True) else 1.0
    f = focus_of(cv, it)
    if f is not None and it.get("focus_scale", True):
        d = math.hypot(x - f[0], y - f[1]) / canvas_diag(cv)
        m *= FOCUS_NEAR + (FOCUS_FAR - FOCUS_NEAR) * min(1.0, d / FOCUS_REACH)
    return m


def pick_art(spec, role, dr, x, y, rng):
    if spec and spec != "auto":
        if spec not in ARTICULATIONS:
            sys.exit(f"Unknown articulation '{spec}'. Articulations: {', '.join(ARTICULATIONS)}, auto")
        return spec
    mix = AUTO_MIX.get(role or "body", AUTO_MIX["body"])
    u = 0.5 + 0.5 * math.tanh(0.8 * dr("art", x, y))
    u = min(0.999, max(0.0, 0.8 * u + 0.2 * float(rng.random())))
    acc = 0.0
    for k, p in mix.items():
        acc += p
        if u < acc:
            return k
    return list(mix)[-1]


EDGE_MIX = {   # stroke edges a role's strokes get when the intention sets no `edge` (eye)
    "underpainting": {"lost": 0.4, "soft": 0.5, "hard": 0.1}, "dead_colour": {"lost": 0.3, "soft": 0.55, "hard": 0.15},
    "body": {"soft": 0.45, "hard": 0.4, "lost": 0.15}, "scumble": {"lost": 0.7, "soft": 0.3},
    "accent": {"hard": 0.8, "soft": 0.2}, "contour": {"hard": 0.7, "soft": 0.3}, "drawing": {"hard": 0.5, "soft": 0.5},
}
DEVIATE = 0.35   # strokes leave the form's direction by up to about 20 degrees, drifting across the passage (eye)


def tool_it(it, dr, x, y, art, role="body"):
    it2 = dict(it)
    if "edge" not in it:
        mix = EDGE_MIX.get(role, EDGE_MIX["body"])
        u = 0.5 + 0.5 * math.tanh(0.8 * dr("edge", x, y))
        acc = 0.0
        for k, p in mix.items():
            acc += p
            if u < acc:
                it2["edge"] = k
                break
        else:
            it2["edge"] = list(mix)[-1]
    it2["_load_mul"] = float(np.clip(1 + 0.15 * dr("load", x, y), 0.6, 1.4))
    if art == "scumble":
        it2["load"] = float(it.get("load", 1.0)) * SCUMBLE_LOAD
    return it2


def shape_path(path, art, size, rng):
    """A scumble is scrubbed: the brush oscillates sideways along its path."""
    if art != "scumble" or len(path) < 4:
        return path
    d = np.gradient(path, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-6)
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    per = max(4.0 * _PXS, size * 1.2)
    off = np.sin(2 * np.pi * arc / per + rng.uniform(0, 6.28)) * size * 0.7
    return (path + nrm * off[:, None]).astype(np.float32)


def play_v8(cv, brush, path, felt, base_press, rng, art="plain", wave=WAVE):
    """play() with an articulation: pressure, width, load and dry-brush that change along the stroke, a slow
    pressure wave, and tremor in pressure that is smooth along the stroke instead of new noise per dab.
    With art "plain" and no wave it is exactly play()."""
    wave = getattr(brush, "wave", wave)     # a tool with its own calibrated swell opts out of the core's wave (ink line tools)
    if art == "plain" and not wave:
        return play(cv, brush, path, felt, base_press, rng)
    n = len(path)
    if n < 2:
        return
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    arc = np.concatenate([[0], np.cumsum(seg)])
    L = arc[-1] + 1e-6
    speed_scale = 0.4 + 0.9 * felt.arousal - 0.3 * felt.care
    hes = 0.08 * (felt.care + felt.tension) / 2
    if art == "flick":
        speed_scale, hes = max(speed_scale, 1.15), 0.0
    steps = max(5, int(L / max(0.5 * _PXS, brush.size * 0.055) * (1.25 - 0.35 * speed_scale)))
    if art == "drag":
        try:
            brush.deplete_mul = DRAG_DEPLETE
        except Exception:
            pass
    trem = gaussian_filter(rng.normal(0, 1, steps + 1), max(1.0, steps / 12))
    trem = trem / (trem.std() + 1e-6) * 0.35
    wf, wph, aph = rng.uniform(0.6, 1.6), rng.uniform(0, 6.283), rng.uniform(0, 6.283)
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
        pa, wa, sa = artic_profile(art, s, aph)
        press = (base_press * land * lift * (1.0 - 0.3 * vn) * (1 + 0.35 * felt.tension * trem[i]) * pa
                 * (1 + wave * math.sin(2 * math.pi * wf * t + wph)))
        rscale = (0.8 + 0.25 * land) * (1.06 - 0.3 * vn) * (0.85 + 0.15 * lift) * wa
        brush.speedfx = 0.35 * vn * felt.arousal + sa
        if prev_xy is not None:
            brush.step = math.hypot(x - prev_xy[0], y - prev_xy[1])
        prev_xy = (x, y)
        brush.dab(cv, x, y, ang, float(np.clip(press, 0.03, 1.3)), rscale=max(0.3, rscale))
    if hasattr(brush, "end"):
        brush.end(cv)


def direction_v8(spec, x, y, rng, felt, dr):
    """direction() whose spread is mostly a drift shared by neighbouring strokes, with a little noise."""
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
    return a + sp * 0.8 * dr("angle", x, y) + rng.normal(0, sp * 0.45)


class FormField:
    """The direction of the form at every point, from a value map (the schema): the structure tensor of its
    gradient at the stroke's scale where the form has an edge or a turn, the same at a coarse scale where it is
    flat locally (strokes continue the nearest form), and a slow flow field (or the intention's direction)
    where there is no form at all, so strokes never all run at one angle. Orientations are averaged as doubled
    angles. follow: "form" (along the form: the isophotes) or "across" (cross-contour, wrapping around it)."""
    DS = 4

    def __init__(self, value, size, follow="form", spec=None, seed=0):
        ds = self.DS
        H, W = value.shape
        h2, w2 = H // ds, W // ds
        Lv = value[:h2 * ds, :w2 * ds].reshape(h2, ds, w2, ds).mean((1, 3))
        Lb = gaussian_filter(Lv, max(0.7, size / 3 / ds))
        gx, gy = sobel(Lb, 1), sobel(Lb, 0)
        prods = (gx * gx, gx * gy, gy * gy)

        def tensor(sig):
            xx, xy, yy = (gaussian_filter(p, sig) for p in prods)
            tr = xx + yy + 1e-12
            return (xx - yy) / tr, 2 * xy / tr, tr

        cf, sf, tf = tensor(max(1.0, size * 0.8 / ds))
        cc, sc, tc = tensor(max(3.0, math.hypot(H, W) / ds * 0.025))
        eref = float(np.percentile(tf, 90)) + 1e-12
        wf = np.clip(tf / (0.05 * eref), 0, 1) * np.hypot(cf, sf)
        wc = 0.6 * np.clip(tc / (0.03 * eref), 0, 1) * np.hypot(cc, sc)   # nearby form, at most 60%: no halos (eye)
        yy, xx = np.mgrid[0:h2, 0:w2].astype(np.float32) * ds
        # where there is no form: a slow flow around the intention's direction angle (or one random angle per
        # intention), varying about +-30 degrees over a third of the canvas (eye): never one angle, never a swirl
        r = np.random.default_rng(seed)
        s = 2 * math.pi / (math.hypot(H, W) * 0.35)
        a0 = math.radians(spec["angle"]) + math.pi / 2 if spec and "angle" in spec else r.uniform(0, math.pi)
        gn = a0 + 0.35 * sum(r.uniform(0.6, 1.2) * np.sin(xx * s * r.uniform(-1, 1) + yy * s * r.uniform(-1, 1) + r.uniform(0, 6.3)) for _ in range(3))
        nc, ns = np.cos(2 * gn), np.sin(2 * gn)
        ufc, ufs = cf / (np.hypot(cf, sf) + 1e-9), sf / (np.hypot(cf, sf) + 1e-9)
        ucc, ucs = cc / (np.hypot(cc, sc) + 1e-9), sc / (np.hypot(cc, sc) + 1e-9)
        inner_c = wc * ucc + (1 - wc) * nc
        inner_s = wc * ucs + (1 - wc) * ns
        vc = wf * ufc + (1 - wf) * inner_c
        vs = wf * ufs + (1 - wf) * inner_s
        th = 0.5 * np.arctan2(vs, vc) + (math.pi / 2 if follow != "across" else 0.0)
        self.c, self.s = np.cos(th).astype(np.float32), np.sin(th).astype(np.float32)
        self.h2, self.w2 = h2, w2

    def at(self, x, y):
        i = min(self.h2 - 1, max(0, int(y / self.DS)))
        j = min(self.w2 - 1, max(0, int(x / self.DS)))
        return float(self.c[i, j]), float(self.s[i, j])


def do_free(cv, it, felt, rng):
    if legacy(cv):
        return do_free_v7(cv, it, felt, rng)
    reg = it.get("region", {"type": "canvas"})
    cv.clip = region_mask(reg, cv.W, cv.H) if it.get("clip") else None
    mask = region_mask(reg, cv.W, cv.H)
    cols, w = palette(it)
    smin, smax = rng2(it.get("size"), [8 * _PXS, 14 * _PXS])
    lmin, lmax = rng2(it.get("length"), [20 * _PXS, 60 * _PXS])
    jit = it.get("color_jitter", 0.035) * (1.2 - 0.6 * felt.care)
    role = it.get("_role", "body")
    dr = new_drift(rng, it, cv, (smin + smax) / 2)
    dspec = it.get("direction")
    for _ in range(int(it.get("count", 10))):
        x, y = sample_in(mask, reg, rng, cv.W, cv.H)
        a = direction_v8(dspec, x, y, rng, felt, dr)
        L = rng.uniform(lmin, lmax) * (0.8 + 0.5 * felt.arousal)
        nc = 3 + int(rng.integers(0, 3))
        ctrl, px, py = [], x, y
        turn = it.get("curve", 0.3) * (1 + felt.tension)
        for k in range(nc):
            ctrl.append([px, py])
            if "around" in (dspec or {}) or (dspec or {}).get("field"):
                a = a * 0.5 + direction_v8(dspec, px, py, rng, felt, dr) * 0.5
            a += rng.normal(0, turn)
            px += math.cos(a) * L / (nc - 1); py += math.sin(a) * L / (nc - 1)
        u = float(np.clip(0.5 + 0.5 * math.tanh(0.9 * dr("size", x, y)) + rng.uniform(-0.1, 0.1), 0, 1))
        size = (smin + (smax - smin) * u) * size_mul(cv, it, x, y, role)
        col = drift_colour(cols[rng.choice(len(cols), p=w)], dr, x, y, jit)
        art = pick_art(it.get("articulation", "auto"), role, dr, x, y, rng)
        b = make_brush(tool_it(it, dr, x, y, art, role), size, col, rng, cv)
        path = shape_path(gesture_path(ctrl, felt, rng, size), art, size, rng)
        play_v8(cv, b, path, felt, it.get("pressure", 0.85) * (1 + 0.12 * dr("press", x, y)), rng, art)
        dr.next()


def do_strokes(cv, it, felt, rng):
    if legacy(cv):
        return do_strokes_v7(cv, it, felt, rng)
    reg = it.get("region")
    cv.clip = region_mask(reg, cv.W, cv.H) if (reg and it.get("clip")) else None
    cols, w = palette(it) if it.get("colors") else ([hx("#888888")], np.array([1.0]))
    role = it.get("_role", "body")
    dr = new_drift(rng, it, cv, 20)
    for s in it["strokes"]:
        size = s.get("size", np.mean(it.get("size", [6 * _PXS, 10 * _PXS])))
        col = hx(s["color"]) if s.get("color") else cols[rng.choice(len(cols), p=w)]
        x, y = s["pts"][0][:2]
        art = pick_art(s.get("articulation", it.get("articulation", "auto")), role, dr, x, y, rng)
        b = make_brush(tool_it(it, dr, x, y, art, role), size, col, rng, cv)
        path = shape_path(gesture_path(s["pts"], felt, rng, size), art, size, rng)
        play_v8(cv, b, path, felt, s.get("pressure", it.get("pressure", 0.85)), rng, art)
        dr.next()


def do_match(cv, it, felt, rng):
    """Making and matching (v8): like v7, but strokes follow a form field (never all one angle), their size
    depends on the detail, the role and the distance from the focus, size, colour, pressure and load drift
    across the passage, and every stroke has an articulation."""
    if legacy(cv):
        return do_match_v7(cv, it, felt, rng)
    if cv.ref is None:
        sys.exit("No schema yet: use the ref command first.")
    reg = it.get("region", {"type": "canvas"})
    mask = region_mask(reg, cv.W, cv.H)
    cv.clip = mask if it.get("clip") else None
    smin, smax = rng2(it.get("size"), [20 * _PXS, 40 * _PXS])
    size = (smin + smax) / 2
    sig = max(1.0 * _PXS, size / 3)       # pixel floors in canvas px (x _PXS in a detail)
    refb = np.stack([gaussian_filter(cv.ref[..., i], sig) for i in range(3)], -1)
    err = np.abs(cv.col - refb).sum(-1)
    if mask is not None:
        err = err * (mask > 0.5)
    g = max(int(4 * _PXS), int(size * 0.9))
    H2, W2 = -(-cv.H // g), -(-cv.W // g)
    errp = np.pad(err, ((0, H2 * g - cv.H), (0, W2 * g - cv.W)), mode="edge")
    e = errp.reshape(H2, g, W2, g).mean((1, 3))
    thr = it.get("threshold", 0.12)
    cells = [(e[r, c], r, c) for r in range(H2) for c in range(W2) if e[r, c] > thr]
    rng.shuffle(cells)
    cells = cells[: int(it.get("max_strokes", 400))]
    faithful = it.get("faithful", 0.85)
    adaptive = it.get("adaptive", True)
    sharp = np.stack([gaussian_filter(cv.ref[..., i], 1.0 * _PXS) for i in range(3)], -1)
    if adaptive:
        lf = gaussian_filter(cv.ref.mean(-1), 1.2 * _PXS)
        det = gaussian_filter(np.hypot(sobel(lf, 0), sobel(lf, 1)), max(2.0 * _PXS, size / 2))
        det = np.clip(det / (np.percentile(det, 97) + 1e-6), 0, 1)
    follow = it.get("follow", "form")
    dspec = it.get("direction")
    ff = FormField(cv.ref.mean(-1), size, follow, dspec, seed=int(rng.integers(1 << 30))) if follow != "direction" else None
    cols, w = palette(it) if it.get("colors") else (None, None)
    cs = it.get("color_shift", {})
    lmin, lmax = rng2(it.get("length"), [size * 1.5, size * 5])
    role = it.get("_role", "body")
    dr = new_drift(rng, it, cv, size)
    jit = 0.012 * (1.2 - felt.care)
    for _, r, c in cells:
        sub = errp[r * g:(r + 1) * g, c * g:(c + 1) * g]
        iy, ix = np.unravel_index(np.argmax(sub), sub.shape)
        x = int(np.clip(c * g + ix + rng.normal(0, g * 0.35), 0, cv.W - 1))
        y = int(np.clip(r * g + iy + rng.normal(0, g * 0.35), 0, cv.H - 1))
        col = sharp[y, x].copy()
        if cols is not None:
            col = col * faithful + cols[rng.choice(len(cols), p=w)] * (1 - faithful)
        col = shift_color(col, cs.get("temp", 0), cs.get("sat", 1), cs.get("value", 1))
        col = drift_colour(col, dr, x, y, jit)
        if adaptive:
            dv = float(det[y, x])
            sz = smax - (smax - smin) * dv ** 0.7
            Lsc = 1.0 - 0.55 * dv
        else:
            sz = rng.uniform(smin, smax); Lsc = 1.0
        sz *= (1 + 0.12 * dr("size", x, y)) * size_mul(cv, it, x, y, role)
        L = rng.uniform(lmin, lmax) * (0.8 + 0.5 * felt.arousal) * Lsc
        ctrl, px, py, prev = [[x, y]], float(x), float(y), None
        step = max(2.0 * _PXS, sz * 0.8)
        dev = DEVIATE * dr("angle", x, y) + rng.normal(0, 0.12)
        cd, sd = math.cos(dev), math.sin(dev)
        for k in range(int(L / step)):
            if ff is not None:
                dx, dy = ff.at(px, py)
                dx, dy = dx * cd - dy * sd, dx * sd + dy * cd
                if prev is None and rng.random() < 0.5:
                    dx, dy = -dx, -dy
            else:
                a = direction_v8(dspec or {"angle": 0, "spread": 25}, px, py, rng, felt, dr) if prev is None else math.atan2(prev[1], prev[0])
                dx, dy = math.cos(a), math.sin(a)
            if prev is not None and dx * prev[0] + dy * prev[1] < 0:
                dx, dy = -dx, -dy
            if prev is not None:
                dx, dy = 0.6 * dx + 0.4 * prev[0], 0.6 * dy + 0.4 * prev[1]
                nn = math.hypot(dx, dy) + 1e-9
                dx, dy = dx / nn, dy / nn
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
            dx, dy = ff.at(x, y) if ff is not None else (1.0, 0.0)
            ctrl.append([x + dx * sz, y + dy * sz])
        art = pick_art(it.get("articulation", "auto"), role, dr, x, y, rng)
        it2 = tool_it(it, dr, x, y, art, role); it2.setdefault("wetmix", 0.22); it2.setdefault("load", 1.3)
        if art == "scumble" and "load" not in it:
            it2["load"] = 1.3 * SCUMBLE_LOAD
        b = make_brush(it2, sz, col, rng, cv)
        path = shape_path(gesture_path(ctrl, felt, rng, sz), art, sz, rng)
        play_v8(cv, b, path, felt, it.get("pressure", 0.9) * (1 + 0.12 * dr("press", x, y)), rng, art)
        dr.next()


def do_model(cv, it, felt, rng):
    """Model a form from a value schema: the region's values (the schema's, or a value image `values`) are cut
    into `steps` bands and painted band by band (dark to light by default, as an oil painter models from the
    shadow into the light; `order`: "light_to_dark" for watercolour), each band's strokes following the form's
    direction (FormField: along the form, or `follow`: "across" to wrap around it), coloured from a value ramp
    (`colors`, dark to light) or from the schema."""
    if legacy(cv):
        sys.exit("model is a v8 intention; the frozen oil-v7 reference doesn't have it.")
    reg = it.get("region", {"type": "canvas"})
    mask = region_mask(reg, cv.W, cv.H)
    m = np.ones((cv.H, cv.W), np.float32) if mask is None else mask
    cv.clip = m if it.get("clip", True) and mask is not None else None
    if it.get("values"):
        vimg = Image.open(it["values"]).convert("L").resize((cv.W, cv.H), Image.LANCZOS)
        V = np.asarray(vimg, np.float32) / 255
        colsrc = None
    elif cv.ref is not None:
        V = cv.ref.mean(-1)
        colsrc = np.stack([gaussian_filter(cv.ref[..., i], 1.5) for i in range(3)], -1)
    else:
        sys.exit("model needs a schema (ref) or a value image ('values': file.png).")
    V = gaussian_filter(V, 2.0)
    inside = m > 0.5
    if not inside.any():
        return
    steps = int(it.get("steps", 4))
    qs = np.quantile(V[inside], np.linspace(0, 1, steps + 1))
    ramp = [hx(c) for c in it["colors"]] if it.get("colors") else None
    lo, hi = float(qs[0]), float(qs[-1])

    def colour_at(v, x, y):
        if ramp:
            t = float(np.clip((v - lo) / (hi - lo + 1e-6), 0, 1)) * (len(ramp) - 1)
            i = min(int(t), len(ramp) - 2) if len(ramp) > 1 else 0
            return ramp[0] if len(ramp) == 1 else ramp[i] * (1 - (t - i)) + ramp[i + 1] * (t - i)
        if colsrc is not None:
            return colsrc[int(y), int(x)].copy()
        return np.array([v, v, v], np.float32)

    smin, smax = rng2(it.get("size"), [10 * _PXS, 24 * _PXS])
    size = (smin + smax) / 2
    ff = FormField(V, size, it.get("follow", "form"), it.get("direction"), seed=int(rng.integers(1 << 30)))
    role = it.get("_role", "body")
    dr = new_drift(rng, it, cv, size)
    lmin, lmax = rng2(it.get("length"), [size * 1.5, size * 4])
    jit = 0.02 * (1.2 - felt.care)
    order = range(steps) if it.get("order", "dark_to_light") == "dark_to_light" else range(steps - 1, -1, -1)
    budget = int(it.get("max_strokes", 600))
    dens = float(it.get("density", 1.0))
    ys, xs = np.nonzero(inside)
    for b_i in order:
        a0, a1 = qs[b_i], qs[b_i + 1]
        band = (V[ys, xs] >= a0) & (V[ys, xs] <= a1 + 1e-6)
        nb = int(band.sum())
        if nb == 0:
            continue
        n = min(budget // steps + 1, int(dens * nb / (size * size * 1.6)) + 1)
        idx = rng.choice(np.nonzero(band)[0], size=n, replace=nb < n)
        tol = (a1 - a0) * 0.6 + 0.02
        for q in idx:
            x, y = float(xs[q]) + rng.normal(0, 2 * _PXS), float(ys[q]) + rng.normal(0, 2 * _PXS)
            x, y = float(np.clip(x, 0, cv.W - 1)), float(np.clip(y, 0, cv.H - 1))
            sz = (smin + (smax - smin) * float(np.clip(0.5 + 0.5 * math.tanh(0.9 * dr("size", x, y)), 0, 1))) * size_mul(cv, it, x, y, role)
            L = rng.uniform(lmin, lmax) * (0.8 + 0.5 * felt.arousal)
            step = max(2.0 * _PXS, sz * 0.7)
            ctrl, px, py, prev = [[x, y]], x, y, None
            dev = DEVIATE * 0.6 * dr("angle", x, y) + rng.normal(0, 0.08)
            cd, sd = math.cos(dev), math.sin(dev)
            for k in range(int(L / step)):
                dx, dy = ff.at(px, py)
                dx, dy = dx * cd - dy * sd, dx * sd + dy * cd
                if prev is None and rng.random() < 0.5:
                    dx, dy = -dx, -dy
                if prev is not None and dx * prev[0] + dy * prev[1] < 0:
                    dx, dy = -dx, -dy
                prev = (dx, dy)
                px += dx * step; py += dy * step
                if not (0 <= px < cv.W and 0 <= py < cv.H) or m[int(py), int(px)] < 0.5:
                    break
                v = V[int(py), int(px)]
                if k >= 1 and (v < a0 - tol or v > a1 + tol):
                    break
                ctrl.append([px, py])
            if len(ctrl) < 2:
                dx, dy = ff.at(x, y)
                ctrl.append([x + dx * sz, y + dy * sz])
            v = 0.5 * (a0 + a1) * 0.5 + 0.5 * float(V[int(y), int(x)])
            col = drift_colour(np.clip(colour_at(v, x, y), 0, 1), dr, x, y, jit)
            art = pick_art(it.get("articulation", "auto"), role, dr, x, y, rng)
            b = make_brush(tool_it(it, dr, x, y, art, role), sz, col, rng, cv)
            path = shape_path(gesture_path(ctrl, felt, rng, sz), art, sz, rng)
            play_v8(cv, b, path, felt, it.get("pressure", 0.85) * (1 + 0.12 * dr("press", x, y)), rng, art)
            dr.next()


# ---------------------------------------------------------------- revision: taking paint away
# Painters revise on the canvas, very often by removal (docs/research/process.md 2.6: pentimenti, Vermeer's
# removed jug rack, Matisse's scraped states; proposal 14). Three core intentions; the medium decides what each
# means. A medium implements `revise(cv, op, mask, it, felt, rng, core)` (return NotImplemented to fall back),
# or names a tool per op in `revision_tools`, or the core uses the first of the medium's tools in
# REVISE_TOOLS, then a finishing step of the same name, then a default: scrape and wipe pull the colour back
# toward the ground with a mottled, tooth-dependent amount; paintout covers the region with the colour around
# it, using the medium's own broad brush.
REVISIONS = ("scrape", "wipe", "paintout")
REVISE_TOOLS = {"scrape": ("eraser", "knife", "scraper"), "wipe": ("kneaded", "lift", "rag")}


def sweep(cv, mask, it, felt, rng, brush, extra=None, size=None, angle=None, passes=1, color=None, press=0.9, field=None):
    """Cover a masked region with strokes of one tool (clipped to the region), as a hand sweeps a knife, rag,
    eraser or loaded brush across a passage: parallel lines, each laid in pieces a few brush widths long,
    turned 70 degrees each pass. `field` (H, W, 3) gives each piece the colour under its middle."""
    ys, xs = np.nonzero(mask > 0.5)
    if len(xs) == 0:
        return
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    area = float((mask > 0.5).sum())
    sz = size or it.get("size") or float(np.clip(math.sqrt(area) / 6, 10 * _PXS, 60 * _PXS))
    sz = float(np.mean(sz)) if isinstance(sz, list) else float(sz)
    cv.clip = mask
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = math.hypot(x1 - x0, y1 - y0) / 2 + sz
    base = math.radians(angle if angle is not None else it.get("angle", rng.uniform(0, 180)))
    col = color if color is not None else np.array([0.5, 0.5, 0.5], np.float32)
    inside = lambda p: mask[int(np.clip(p[1], 0, cv.H - 1)), int(np.clip(p[0], 0, cv.W - 1))] >= 0.05
    for p in range(passes):
        ang = base + p * math.radians(70) + rng.normal(0, 0.05)
        dx, dy, nx, ny = math.cos(ang), math.sin(ang), -math.sin(ang), math.cos(ang)
        off = -R
        while off < R:
            px, py = cx + nx * off, cy + ny * off
            seg = max(sz * 4, R / 2)
            t0 = -R - rng.uniform(0, seg)
            while t0 < R:
                t1 = t0 + seg * rng.uniform(0.7, 1.3)
                a, b = [px + dx * t0, py + dy * t0], [px + dx * t1, py + dy * t1]
                t0 = t1 - sz * 0.5
                mid = [(a[0] + b[0]) / 2 + rng.normal(0, sz * 0.2), (a[1] + b[1]) / 2 + rng.normal(0, sz * 0.2)]
                if not (inside(a) or inside(mid) or inside(b)):
                    continue
                it2 = dict(it); it2["brush"] = brush
                it2.update(extra or {})
                if field is not None:
                    c = np.clip(field[int(np.clip(mid[1], 0, cv.H - 1)), int(np.clip(mid[0], 0, cv.W - 1))] + rng.normal(0, 0.008, 3), 0, 1)
                else:
                    c = np.clip(col + rng.normal(0, 0.01, 3), 0, 1) if color is not None else col
                br = make_brush(it2, sz * rng.uniform(0.9, 1.1), c, rng, cv)
                play_v8(cv, br, gesture_path([a, mid, b], felt, rng, sz), felt, it.get("pressure", press), rng, "plain", wave=0)
            off += sz * 0.75
    cv.clip = None


def ragged(mask, rng, angle=None, streak=0.6):
    """A hand's region: the edge broken by a smooth noise (no ruler edge), and streaks along the stroke direction
    where the blade or rag dragged (amounts are eye)."""
    H, W = mask.shape
    n = gaussian_filter(rng.random((H, W)).astype(np.float32), 6 * _PXS)
    n = (n - n.mean()) / (n.std() + 1e-6)
    m = np.clip((mask - 0.5 + 0.12 * n) * 3 + 0.5, 0, 1) * (mask > 0.02)
    if angle is not None and streak > 0:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        proj = -xx * math.sin(angle) + yy * math.cos(angle)
        k = int(proj.max() - proj.min()) + 2
        band = gaussian_filter(rng.random(k).astype(np.float32), 2.0)
        band = (band - band.min()) / (band.max() - band.min() + 1e-6)
        m = m * (1 - streak + streak * band[(proj - proj.min()).astype(int)])
    return gaussian_filter(m, 1.0 * _PXS).astype(np.float32)


def fill_colour(cv, mask, sigma=None):
    """The colour the surroundings would have inside the region: a normalised blur of the colour outside it
    (what a painter mixes to paint a passage out so it disappears into its neighbours)."""
    out = (mask < 0.5).astype(np.float32)
    sig = sigma or max(8.0, math.sqrt(float((mask > 0.5).sum())) * 0.4)
    wsum = gaussian_filter(out, sig) + 1e-6
    return np.stack([gaussian_filter(cv.col[..., i] * out, sig) / wsum for i in range(3)], -1).astype(np.float32)


def surround_colour(cv, mask):
    from scipy.ndimage import binary_dilation
    m = mask > 0.5
    ring = binary_dilation(m, iterations=int(max(6, math.sqrt(m.sum()) * 0.08))) & ~m
    if not ring.any():
        return np.median(cv.col.reshape(-1, 3), 0)
    return np.median(cv.col[ring], 0).astype(np.float32)


def pull_back(cv, mask, strength, rng):
    """Default removal: the colour returns toward the ground, more on the tops of the support's tooth, unevenly."""
    g = hx(cv.meta.get("ground", "#d8cfc0"))
    mot = gaussian_filter(rng.random((cv.H, cv.W)).astype(np.float32), 3 * _PXS)
    mot = (mot - mot.min()) / (mot.max() - mot.min() + 1e-6)
    amt = np.clip(mask * strength * (0.55 + 0.3 * mot + 0.25 * (cv.tex - 0.5)), 0, 1)[..., None]
    cv.col = (cv.col * (1 - amt) + g[None, None, :] * amt).astype(np.float32)


def do_revise(cv, it, felt, rng, op):
    if legacy(cv):
        sys.exit(f"{op} is a v8 intention; the frozen oil-v7 reference doesn't have it.")
    if "region" not in it:
        sys.exit(f"{op} needs a region (the passage to take back).")
    mask = region_mask(it["region"], cv.W, cv.H, feather=it.get("feather", 6))
    if mask is None:
        mask = np.ones((cv.H, cv.W), np.float32)
    it = dict(it)
    it.setdefault("angle", float(rng.uniform(0, 180)))
    if it.get("ragged", True):
        mask = ragged(mask, rng, math.radians(it["angle"]) if op != "paintout" else None, 0.5 if op == "scrape" else 0.3)
    med = cv.medium
    if hasattr(med, "revise"):
        r = med.revise(cv, op, mask, it, felt, rng, sys.modules[__name__])
        if r is not NotImplemented and r is not None:
            return
    tool = (getattr(med, "revision_tools", {}) or {}).get(op)
    if tool is None and op in REVISE_TOOLS:
        tool = next((t for t in REVISE_TOOLS[op] if t in med.tools), None)
    if tool is not None:
        sweep(cv, mask, it, felt, rng, tool, passes=int(it.get("passes", 2)))
        return
    if op == "scrape" and op in med.finishes:        # a medium's scraped-highlight finishing step (ink)
        med.finish(cv, op, {"region": it["region"], "strength": it.get("strength", 0.8)})
        return
    if op == "paintout":
        brush = it.get("brush") or next((t for t in ("flat", "round", "block", "brush") if t in med.tools), list(med.tools)[0])
        if it.get("color"):
            sweep(cv, mask, dict(it, load=it.get("load", 1.4)), felt, rng, brush, passes=int(it.get("passes", 2)), color=hx(it["color"]))
        else:
            sweep(cv, mask, dict(it, load=it.get("load", 1.4)), felt, rng, brush, passes=int(it.get("passes", 2)), field=fill_colour(cv, mask))
        return
    pull_back(cv, mask, float(it.get("strength", 0.8)), rng)


def do_scrape(cv, it, felt, rng):
    do_revise(cv, it, felt, rng, "scrape")


def do_wipe(cv, it, felt, rng):
    do_revise(cv, it, felt, rng, "wipe")


def do_paintout(cv, it, felt, rng):
    do_revise(cv, it, felt, rng, "paintout")


# ---------------------------------------------------------------- elements (for the clarity measure)
def load_elements(cv):
    ep = P("elements.json")
    return json.load(open(ep)) if os.path.exists(ep) else []


def do_element(cv, it, felt, rng):
    """Declare (or redeclare) an element of the picture for the clarity measure: {"type":"element","name","region"}."""
    els = [e for e in load_elements(cv) if e["name"] != it["name"]]
    els.append({"name": it["name"], "region": it["region"]})
    json.dump(els, open(P("elements.json"), "w"), indent=1)


def element_masks(cv):
    """Element masks: an id map from the scene renderer if it wrote one ({canvas}_elements_ids.png with
    {canvas}_elements_ids.json, {"id": "name"}), plus the declared regions ({canvas}_elements.json)."""
    out = {}
    ip, jp = P("elements_ids.png"), P("elements_ids.json")
    if os.path.exists(ip) and os.path.exists(jp):
        ids = np.asarray(Image.open(ip).convert("L").resize((cv.W, cv.H), Image.NEAREST))
        for k, name in json.load(open(jp)).items():
            m = ids == int(k)
            if m.any():
                out[name] = m.astype(np.float32)
    for e in load_elements(cv):
        m = region_mask(e["region"], cv.W, cv.H)
        out[e["name"]] = np.ones((cv.H, cv.W), np.float32) if m is None else m
    return out


def do_hatch_v7(cv, it, felt, rng):
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
            # each line starts its pieces at its own offset and length, so piece ends never line up into seams
            t, run = -R - rng.uniform(0, seg_max), []
            seg_here = seg_max * rng.uniform(0.6, 1.4)
            while t <= R:
                x, y = px + dx * t, py + dy * t
                ok = 0 <= x < cv.W and 0 <= y < cv.H and (mask is None or mask[int(y), int(x)] > 0.5) and val[int(y), int(x)] < level
                if ok:
                    run.append([x, y])
                if (not ok or len(run) * 3 >= seg_here) and len(run) >= 3:
                    a, b = run[0], run[-1]
                    a = [a[0] + rng.normal(0, 1.5), a[1] + rng.normal(0, 1.5)]
                    ctrl = [a, [(a[0] + b[0]) / 2 + rng.normal(0, 0.8), (a[1] + b[1]) / 2 + rng.normal(0, 0.8)], b]
                    col = np.clip(cols[rng.choice(len(cols), p=w)] + rng.normal(0, 0.01, 3), 0, 1)
                    br = make_brush(it, size * rng.uniform(0.85, 1.15), col, rng, cv)
                    play(cv, br, gesture_path(ctrl, felt, rng, size), felt, it.get("pressure", 0.8), rng)
                    n += 1
                    run = []
                    seg_here = seg_max * rng.uniform(0.6, 1.4)
                elif not ok:
                    run = []
                t += 3
            off += sp
            if n > it.get("max_strokes", 1500):
                return


HATCH_MAX = 20000    # default cap on hatch lines per intention (the v7 path keeps 1500); a full sheet of engraving
                     # at 16 px/mm, 0.3 mm spacing and 2-4 layers needs several thousand


def do_hatch(cv, it, felt, rng):
    """Hatching (v8). As v7, plus two options for engraving and pen systems:
    "regular": true  - a ruled system: no spacing or angle jitter, long unbroken lines (broken only where the
                       region or the value level ends), as an engraver's or a ruling machine's lines;
    "follow": "form" - the lines follow the schema's form (FormField, the same direction field as match):
                       evenly spaced streamlines (Jobard & Lefer 1997, "Creating evenly-spaced streamlines"),
                       each value layer turned by `cross` degrees from the form; contour hatching.
    max_strokes defaults to HATCH_MAX."""
    if legacy(cv):
        return do_hatch_v7(cv, it, felt, rng)
    it = dict(it)
    it.setdefault("max_strokes", HATCH_MAX)
    if it.get("follow") != "form":
        if not it.get("regular"):
            return _hatch_free(cv, it, felt, rng)
        return _hatch_regular(cv, it, felt, rng)
    return _hatch_form(cv, it, felt, rng)


# Feathered value bands (v8). A layer that stops dead where the schema crosses its level lays a smooth gradient as
# steps (docs/calibration/graphite-hyperrealism.md: faint diagonal steps on the wall and the egg). A draughtsman
# lightens the pressure as the tone thins out, so each layer's pressure falls off across its level over a band
# `feather` wide (in the schema's value, 0-1): full pressure below level - feather/2, none above level + feather/2.
# The default for the freehand hatch is HATCH_FEATHER, or 0.6 of the smallest gap between the layers when that is
# smaller (eye); "feather": 0 restores the hard stop. Ruled (`regular`) and contour (`follow: form`) hatching keep
# the hard stop unless `feather` is given, because their media were calibrated on it (engraving, pen).
HATCH_FEATHER = 0.08


def _hatch_feather(it, layers, default):
    f = it.get("feather")
    if f is None:
        if not default:
            return 0.0
        gaps = [abs(a - b) for a, b in zip(layers, layers[1:])]
        return min(HATCH_FEATHER, 0.6 * min(gaps)) if gaps else HATCH_FEATHER
    return max(0.0, float(f))


def _band_pressure(val, level, fw):
    """Pressure factor (0..1) of one value layer: 1 well inside the band, a smooth fall across its level."""
    if fw <= 0:
        return (val < level).astype(np.float32)
    t = np.clip((level + fw / 2 - val) / fw, 0, 1)
    return (t * t * (3 - 2 * t)).astype(np.float32)


class _Pressed:
    """A tool whose pressure is scaled by a per-pixel field where it touches (a feathered hatch layer)."""

    def __init__(self, b, field):
        self.__dict__["_b"], self.__dict__["_f"] = b, field

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        f = self._f
        k = float(f[min(f.shape[0] - 1, max(0, int(y))), min(f.shape[1] - 1, max(0, int(x)))])
        self._b.dab(cv, x, y, ang, press * k, rscale)

    def __getattr__(self, k):
        return getattr(self._b, k)

    def __setattr__(self, k, v):
        setattr(self._b, k, v)


def _hatch_free(cv, it, felt, rng):
    """The freehand hatch of v7 (parallel lines at `angle`, `spacing`, in value `layers` turned by `cross`, spacing
    and angle drifting a little, staggered piece ends), with feathered bands (`feather`, above)."""
    reg = it.get("region", {"type": "canvas"})
    mask = region_mask(reg, cv.W, cv.H)
    cv.clip = mask if it.get("clip") else None
    if cv.ref is None and "value" not in it:
        sys.exit("hatch needs a schema (ref) or a flat 'value' (0 dark .. 1 light).")
    val = gaussian_filter(cv.ref.mean(-1), 3) if cv.ref is not None and "value" not in it else np.full((cv.H, cv.W), float(it["value"]), np.float32)
    layers = it.get("layers", [0.75, 0.55, 0.35, 0.18])
    fw = _hatch_feather(it, layers, True)
    cross = it.get("cross", 45)
    spacing = it.get("spacing", 9 * _PXS)          # defaults and the walk along each line are in canvas px (x _PXS in a detail)
    size = float(np.mean(it.get("size", [3 * _PXS, 3 * _PXS]))) if isinstance(it.get("size", 3), list) else float(it.get("size", 3 * _PXS))
    seg_max = it.get("length", 140 * _PXS)
    cols, w = palette(it) if it.get("colors") else ([hx("#2a2a2a")], np.array([1.0]))
    if mask is not None:
        ys, xs = np.nonzero(mask > 0.5)
        if len(xs) == 0:
            return
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    else:
        x0, x1, y0, y1 = 0, cv.W - 1, 0, cv.H - 1
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = math.hypot(x1 - x0, y1 - y0) / 2 + spacing
    n = 0
    for li, level in enumerate(layers):
        pf = _band_pressure(val, level, fw)
        ang = math.radians(it.get("angle", 50) + li * cross + rng.normal(0, 2))
        dx, dy = math.cos(ang), math.sin(ang)
        nx, ny = -dy, dx
        off = -R + rng.uniform(0, spacing)
        while off < R:
            sp = spacing * rng.uniform(0.85, 1.15)
            px, py = cx + nx * off, cy + ny * off
            # each line starts its pieces at its own offset and length, so piece ends never line up into seams
            t, run = -R - rng.uniform(0, seg_max), []
            seg_here = seg_max * rng.uniform(0.6, 1.4)
            while t <= R:
                x, y = px + dx * t, py + dy * t
                ok = 0 <= x < cv.W and 0 <= y < cv.H and (mask is None or mask[int(y), int(x)] > 0.5) and pf[int(y), int(x)] > 0.02
                if ok:
                    run.append([x, y])
                if (not ok or len(run) * 3 * _PXS >= seg_here) and len(run) >= 3:
                    a, b = run[0], run[-1]
                    a = [a[0] + rng.normal(0, 1.5 * _PXS), a[1] + rng.normal(0, 1.5 * _PXS)]
                    ctrl = [a, [(a[0] + b[0]) / 2 + rng.normal(0, 0.8 * _PXS), (a[1] + b[1]) / 2 + rng.normal(0, 0.8 * _PXS)], b]
                    col = np.clip(cols[rng.choice(len(cols), p=w)] + rng.normal(0, 0.01, 3), 0, 1)
                    br = make_brush(it, size * rng.uniform(0.85, 1.15), col, rng, cv)
                    if fw > 0:
                        br = _Pressed(br, pf)
                    play(cv, br, gesture_path(ctrl, felt, rng, size), felt, it.get("pressure", 0.8), rng)
                    n += 1
                    run = []
                    seg_here = seg_max * rng.uniform(0.6, 1.4)
                elif not ok:
                    run = []
                t += 3 * _PXS
            off += sp
            if n > it.get("max_strokes", 1500):
                return


def _hatch_setup(cv, it):
    reg = it.get("region", {"type": "canvas"})
    mask = region_mask(reg, cv.W, cv.H)
    cv.clip = mask if it.get("clip") else None
    if cv.ref is None and "value" not in it:
        sys.exit("hatch needs a schema (ref) or a flat 'value' (0 dark .. 1 light).")
    val = gaussian_filter(cv.ref.mean(-1), 3) if cv.ref is not None and "value" not in it else np.full((cv.H, cv.W), float(it["value"]), np.float32)
    size = float(np.mean(it.get("size", [3 * _PXS, 3 * _PXS]))) if isinstance(it.get("size", 3), list) else float(it.get("size", 3 * _PXS))
    cols, w = palette(it) if it.get("colors") else ([hx("#2a2a2a")], np.array([1.0]))
    return mask, val, size, cols, w


def _hatch_line(cv, it, felt, rng, pts, size, cols, w, regular, pf=None):
    if len(pts) < 2:
        return
    if regular:   # a steady hand: no tremor, no scatter, the line's own shape kept
        ctrl = pts if len(pts) <= 24 else pts[::max(1, len(pts) // 24)] + [pts[-1]]
        col = cols[rng.choice(len(cols), p=w)]
        br = make_brush(it, size, col, rng, cv)
        if pf is not None:
            br = _Pressed(br, pf)
        steady = Felt({"arousal": 0.0, "tension": 0.0, "valence": 0.5, "care": 1.0})
        play(cv, br, gesture_path(ctrl, steady, rng, size), steady, it.get("pressure", 0.8), rng)
    else:
        col = np.clip(cols[rng.choice(len(cols), p=w)] + rng.normal(0, 0.01, 3), 0, 1)
        br = make_brush(it, size * rng.uniform(0.9, 1.1), col, rng, cv)
        if pf is not None:
            br = _Pressed(br, pf)
        play(cv, br, gesture_path(pts, felt, rng, size), felt, it.get("pressure", 0.8), rng)


def _hatch_regular(cv, it, felt, rng):
    mask, val, size, cols, w = _hatch_setup(cv, it)
    layers = it.get("layers", [0.75, 0.55, 0.35, 0.18])
    spacing = float(it.get("spacing", 9 * _PXS))
    if mask is not None:
        ys, xs = np.nonzero(mask > 0.5)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    else:
        x0, x1, y0, y1 = 0, cv.W - 1, 0, cv.H - 1
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = math.hypot(x1 - x0, y1 - y0) / 2 + spacing
    n = 0
    fw = _hatch_feather(it, layers, False)
    for li, level in enumerate(layers):
        pf = _band_pressure(val, level, fw)
        pw = pf if fw > 0 else None
        ang = math.radians(it.get("angle", 50) + li * it.get("cross", 45))
        dx, dy, nx, ny = math.cos(ang), math.sin(ang), -math.sin(ang), math.cos(ang)
        off = -R + (li * spacing / max(len(layers), 1)) % spacing
        while off < R:
            px, py = cx + nx * off, cy + ny * off
            t, run = -R, []
            while t <= R + 2 * _PXS:
                x, y = px + dx * t, py + dy * t
                ok = 0 <= x < cv.W and 0 <= y < cv.H and (mask is None or mask[int(y), int(x)] > 0.5) and pf[int(y), int(x)] > 0.02
                if ok:
                    run.append([x, y])
                elif len(run) >= 3:
                    _hatch_line(cv, it, felt, rng, run, size, cols, w, True, pw); n += 1; run = []
                else:
                    run = []
                t += 2 * _PXS
            if len(run) >= 3:
                _hatch_line(cv, it, felt, rng, run, size, cols, w, True, pw); n += 1
            off += spacing
            if n > it["max_strokes"]:
                return


def _hatch_form(cv, it, felt, rng):
    """Evenly spaced streamlines of the form field, per value layer (each turned by `cross` from the form)."""
    mask, val, size, cols, w = _hatch_setup(cv, it)
    layers = it.get("layers", [0.75, 0.55, 0.35, 0.18])
    spacing = float(it.get("spacing", 9 * _PXS))
    seg_max = float(it.get("length", 400 * _PXS))
    regular = bool(it.get("regular"))
    ffs = {}
    n = 0
    cell = max(1.0, spacing * 0.5)
    gh, gw = int(cv.H / cell) + 1, int(cv.W / cell) + 1
    fw = _hatch_feather(it, layers, False)
    for li, level in enumerate(layers):
        pf = _band_pressure(val, level, fw)
        pw = pf if fw > 0 else None
        turn = math.radians(it.get("angle", 0) + li * it.get("cross", 45)) if li or "angle" in it else 0.0
        key = round(turn, 3)
        if key not in ffs:
            ffs[key] = FormField(cv.ref.mean(-1) if cv.ref is not None else val, max(spacing * 2, 12 * _PXS), "form", None, seed=int(rng.integers(1 << 30)))
        ff = ffs[key]
        ct, st = math.cos(turn), math.sin(turn)
        occ = np.zeros((gh, gw), bool)
        ok = lambda x, y, pf=pf: 0 <= x < cv.W and 0 <= y < cv.H and (mask is None or mask[int(y), int(x)] > 0.5) and pf[int(y), int(x)] > 0.02

        def free(x, y):
            i, j = int(y / cell), int(x / cell)
            return not occ[max(0, i - 1):i + 2, max(0, j - 1):j + 2].any()
        seeds = [(x, y) for y in np.arange(spacing / 2, cv.H, spacing) for x in np.arange(spacing / 2, cv.W, spacing)]
        order = rng.permutation(len(seeds))
        for si in order:
            x, y = seeds[si]
            if not regular:
                x, y = x + rng.uniform(-spacing * 0.3, spacing * 0.3), y + rng.uniform(-spacing * 0.3, spacing * 0.3)
            if not ok(x, y) or not free(x, y):
                continue
            line = [[x, y]]
            for sgn in (1, -1):
                px, py, prev, L = x, y, None, 0.0
                while L < seg_max / 2:
                    dx, dy = ff.at(px, py)
                    dx, dy = dx * ct - dy * st, dx * st + dy * ct
                    if prev is None:
                        dx, dy = dx * sgn, dy * sgn
                    elif dx * prev[0] + dy * prev[1] < 0:
                        dx, dy = -dx, -dy
                    prev = (dx, dy)
                    px, py = px + dx * 2 * _PXS, py + dy * 2 * _PXS
                    L += 2 * _PXS
                    if not ok(px, py) or not free(px, py):
                        break
                    if sgn == 1:
                        line.append([px, py])
                    else:
                        line.insert(0, [px, py])
            if len(line) * 2 * _PXS < max(6 * _PXS, spacing):
                continue
            for px, py in line:
                occ[min(gh - 1, int(py / cell)), min(gw - 1, int(px / cell))] = True
            _hatch_line(cv, it, felt, rng, line[::max(1, len(line) // 24)] + [line[-1]], size, cols, w, regular, pw)
            n += 1
            if n > it["max_strokes"]:
                return


def do_glaze(cv, it, felt, rng):
    reg = it.get("region", {"type": "canvas"})
    mask = region_mask(reg, cv.W, cv.H, feather=it.get("feather", 30 * _PXS))
    if mask is None:
        mask = np.ones((cv.H, cv.W), np.float32)
    try:
        cv.medium.glaze(cv, mask, hx(it["color"]), it.get("opacity", 0.25), it)
    except TypeError:
        cv.medium.glaze(cv, mask, hx(it["color"]), it.get("opacity", 0.25))


def do_blend(cv, it, felt, rng):
    it = dict(it); it["brush"] = "blend"
    if legacy(cv):
        (do_strokes_v7 if "strokes" in it else do_free_v7)(cv, it, felt, rng)
        return
    it.setdefault("articulation", "plain")
    if "strokes" in it:
        do_strokes(cv, it, felt, rng)
    else:
        do_free(cv, it, felt, rng)


INTENT = {"free": do_free, "strokes": do_strokes, "match": do_match, "glaze": do_glaze, "blend": do_blend, "hatch": do_hatch,
          "model": do_model, "scrape": do_scrape, "wipe": do_wipe, "paintout": do_paintout, "element": do_element}


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


def transfer(cv, strength, color=None):
    if color is None:  # a line that shows on the ground: warm dark on light grounds, warm light on dark ones
        color = "#4a3a2e" if float(cv.col.mean()) > 0.45 else "#d8c8a8"
    lum = gaussian_filter(cv.ref.mean(-1), 1.5)
    e = np.hypot(sobel(lum, 0), sobel(lum, 1))
    e = np.clip(e / (np.percentile(e, 99) + 1e-6), 0, 1) ** 1.5
    line = hx(color)
    cv.col = kmix(cv.col, line[None, None, :], (e * strength)[..., None])


# ---------------------------------------------------------------- reading the layers, the elements and the finish
def finish_L(cv):
    import eyes
    L, _, _ = eyes._srgb_to_lab(eyes.load(cv.render()))
    return float(L.mean())


def role_view(cv, img, which=None):
    bits, _ = load_roles(cv)
    g = np.asarray(img.convert("L"), np.float32) / 255
    painted = bits > 0
    if which:
        r = norm_role(which)
        sel = (bits & ROLE_BIT[r]) > 0
        base = (0.35 + 0.4 * g)[..., None] * np.ones(3)
        col = hx(ROLE_COLOR[r])
        out = np.where(sel[..., None], col * (0.6 + 0.4 * g[..., None]), base)
        f = focus_of(cv, {})
        print(f"{r}: {float(sel.mean()):.0%} of the canvas" + (f", {float(sel[_focus_mask(cv, f)].mean()):.0%} of the focal area" if f else ""))
        return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    # each pixel: the colour of the latest role in the usual order of work among the roles it holds; brighter = more roles
    order = [r for r in ("drawing", "underpainting", "dead_colour", "wash", "body", "hatch", "scumble", "glaze", "contour", "accent", "correction")]
    out = np.zeros((cv.H, cv.W, 3), np.float32) + 0.12
    for r in order:
        sel = (bits & ROLE_BIT[r]) > 0
        out[sel] = hx(ROLE_COLOR[r])
    nroles = np.zeros((cv.H, cv.W), np.float32)
    for r in ROLES:
        nroles += ((bits & ROLE_BIT[r]) > 0)
    out = out * (0.45 + 0.55 * np.clip(nroles / 4, 0, 1))[..., None] * (0.7 + 0.3 * g[..., None])
    im = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    used = [r for r in ROLES if ((bits & ROLE_BIT[r]) > 0).any()]
    for i, r in enumerate(used):
        y = 10 + i * 26
        d.rectangle([10, y, 30, y + 18], fill=tuple(int(v * 255) for v in hx(ROLE_COLOR[r])), outline=(255, 255, 255))
        d.text((38, y + 2), r, fill=(255, 255, 255))
    shares = {r: float(((bits & ROLE_BIT[r]) > 0).mean()) for r in used}
    print("roles: " + ", ".join(f"{r} {v:.0%}" for r, v in sorted(shares.items(), key=lambda kv: -kv[1])) if used else "roles: none recorded yet")
    print(f"layers of different roles per pixel: none {float((nroles == 0).mean()):.0%}, one {float((nroles == 1).mean()):.0%}, "
          f"two {float((nroles == 2).mean()):.0%}, three or more {float((nroles >= 3).mean()):.0%}")
    return im


def _focus_mask(cv, f, frac=0.12):
    yy, xx = np.mgrid[0:cv.H, 0:cv.W]
    return np.hypot(xx - f[0], yy - f[1]) < frac * math.hypot(cv.W, cv.H)


# one-role passages and role order: thresholds are judgements (eye), to be tuned against critics' readings
ONE_ROLE_FLAG = 0.6     # a passage is "built from one role" when over 60% of its painted pixels hold a single role
ORDER_FLAG = 0.15       # role order is flagged when over 15% of the cells holding both roles have them reversed


def flatten_order(order):
    """A style's layer_order ({"order": [...], "source", "judgement"} in studio/styles.json, or a bare list):
    entries are role names or lists of roles that belong to the same stage."""
    if isinstance(order, dict):
        order = order.get("order", [])
    stage = {}
    for i, e in enumerate(order):
        for r in (e if isinstance(e, list) else [e]):
            stage[norm_role(r)] = i
    return stage


def roles_report(cv, style_entry, focus):
    bits, first = load_roles(cv)
    lines, flags = [], []
    # media whose areas are flat single impressions by nature (woodblock) aren't flagged for single-role passages
    flat_ok = bool(getattr(getattr(cv, "medium", None), "flat_areas_ok", False))
    painted = bits > 0
    if not painted.any():
        return ["layers: no roles recorded (a canvas painted before roles existed, or nothing painted yet)"], []
    n = np.zeros(bits.shape, np.int32)
    for r in ROLES:
        n += ((bits & ROLE_BIT[r]) > 0)
    shares = {r: float(((bits & ROLE_BIT[r]) > 0).mean()) for r in ROLES if ((bits & ROLE_BIT[r]) > 0).any()}
    lines.append("layers: " + ", ".join(f"{r} {v:.0%}" for r, v in sorted(shares.items(), key=lambda kv: -kv[1]))
                 + f"; painted pixels with one role {float((n[painted] == 1).mean()):.0%}, two {float((n[painted] == 2).mean()):.0%}, three or more {float((n[painted] >= 3).mean()):.0%}")
    if focus is not None:
        fm = _focus_mask(cv, focus) & painted
        if fm.any():
            one = float((n[fm] == 1).mean())
            lines.append(f"  focal area ({focus[0]:.0f}, {focus[1]:.0f}): one role {one:.0%}, roles there: "
                         + ", ".join(r for r in ROLES if ((bits[fm] & ROLE_BIT[r]) > 0).mean() > 0.05))
            if one > ONE_ROLE_FLAG and not flat_ok:
                flags.append("the focal area is built from one role only: add the layers your current builds it with")
    gy_, gx_ = 3, 3
    bad = []
    for r_ in range(gy_):
        for c_ in range(gx_):
            sl = (slice(r_ * cv.H // gy_, (r_ + 1) * cv.H // gy_), slice(c_ * cv.W // gx_, (c_ + 1) * cv.W // gx_))
            p = painted[sl]
            if p.mean() > 0.3 and float((n[sl][p] == 1).mean()) > ONE_ROLE_FLAG:
                bad.append(f"{['top', 'middle', 'bottom'][r_]}-{['left', 'centre', 'right'][c_]}")
    if bad and flat_ok:
        lines.append("  single-role passages not flagged: this medium builds areas as flat single impressions (" + ", ".join(bad) + ")")
    elif bad:
        flags.append("passages built from one role only (reads as a filter): " + ", ".join(bad))
    order = (style_entry or {}).get("layer_order")
    if order:
        stage = flatten_order(order)
        rev = []
        rs = [r for r in stage if r != "correction" and r in shares]
        for a in rs:
            for b in rs:
                if stage[a] < stage[b]:
                    fa, fb = first[ROLES.index(a)], first[ROLES.index(b)]
                    both = (fa >= 0) & (fb >= 0)
                    if both.sum() >= 20:
                        wrong = float((fb[both] < fa[both]).mean())
                        if wrong > ORDER_FLAG:
                            rev.append((wrong, f"{b} before {a} in {wrong:.0%} of their shared area"))
        st = " > ".join("/".join(e) if isinstance(e, list) else e for e in (order.get("order", []) if isinstance(order, dict) else order))
        lines.append(f"  expected order ({st})" + ("" if rev else ": followed"))
        if rev:
            flags.append("roles out of the current's order: " + "; ".join(t for _, t in sorted(rev, reverse=True)[:4]))
    return lines, flags


def clarity_report(cv, img):
    import eyes
    masks = element_masks(cv)
    if not masks:
        return [], []
    ref_img = Image.fromarray((np.clip(cv.ref, 0, 1) * 255).astype(np.uint8)) if cv.ref is not None else None
    res = eyes.element_clarity(img, masks, ref_img)
    lines, flags = ["elements (contrast with their surround at thumbnail size):"], []
    for name, r in res.items():
        tag = "MASKED" if r["masked"] else ("weakened" if r.get("weakened") else "clear")
        sch = f", schema {r['schema_contrast']:.0f}" if r.get("schema_contrast") is not None else ""
        lines.append(f"  {name}: value {r['dL']:.0f} L*, colour {r['dE']:.0f} ΔE, edge {r['edge']:.1f} (contrast {r['contrast']:.0f}{sch}) {tag}")
        if r["masked"]:
            flags.append(f"'{name}' is masked: it doesn't separate from its surround at thumbnail size"
                         + (" (the schema had it)" if r.get("schema_contrast") is not None and r["schema_contrast"] >= eyes.CLARITY_MIN else ""))
        elif r.get("weakened"):
            flags.append(f"'{name}' has lost more than half of the contrast it had in the schema")
    return lines, flags


def finish_report(cv, m, target):
    """The finishing check (the analogue of Spectre's post-master check, docs/FINISHING.md): did the finishing
    do its job for the medium and the current? Generic checks plus the medium's own (`finish_check`)."""
    lines, flags = [], []
    fin = cv.meta.get("finishes", [])
    ops = [f["op"] for f in fin]
    lines.append("finishing steps done: " + (", ".join(ops) if ops else "none"))
    if not cv.meta.get("signed"):
        flags.append("not signed: `sign` is the very last act")
    med = cv.medium
    if hasattr(med, "finish_check"):
        l2, f2 = med.finish_check(cv)
        lines += l2; flags += f2
    else:
        l2, f2 = default_finish_check(cv, ops, fin)
        lines += l2; flags += f2
    if target:
        import eyes
        for k in ("value_mean", "value_spread", "hard_edge_share", "hard_edges_near_focus"):
            if k in target and k in m:
                z = (m[k] - target[k]["mean"]) / max(target[k]["sd"], 1e-6)
                if abs(z) > 1.5:
                    flags.append(f"after finishing, {eyes.LABELS[k][0]} is outside the current's range (z {z:+.1f})")
    if m.get("hard_edges_near_focus", 1) < 0.12:
        flags.append("edge hierarchy: the hardest edges are not at the focal point after finishing")
    if m.get("contrast_concentration", 2) < 1.2:
        flags.append("focal contrast: contrast is no stronger at the focus than elsewhere")
    return lines, flags


def default_finish_check(cv, ops, fin):
    """Checks for media that don't define finish_check (docs/FINISHING.md). Thresholds are judgements unless noted."""
    lines, flags = [], []
    name = cv.medium.name
    if name in ("charcoal", "pastel", "graphite"):
        loose = getattr(cv, "loose", None)
        if loose is not None:
            share = float((loose > 0.05).mean())
            lines.append(f"loose dust over {share:.0%} of the sheet")
            if name == "charcoal" and "fixative" not in ops:
                flags.append("charcoal not fixed: a final fixative seals the dust (FINISHING.md)")
        for f in fin:
            if f["op"] == "fixative":
                dl = f["L_before"] - f["L_after"]
                lim = 8.0 * float(f["params"].get("strength", 1.0)) * (1.0 if name == "pastel" else 0.5) + 1.0
                lines.append(f"fixative darkened the picture by {dl:.1f} L*")
                if dl > lim:
                    flags.append(f"fixative darkened the {name} by {dl:.1f} L* (more than the studio's modelled {lim:.0f}: FINISHING.md, not a measurement)")
        if name == "pastel" and fin and fin[-1]["op"] == "fixative" and fin[-1]["params"].get("kind", "workable") == "final":
            flags.append("pastel: the last bright touches go on after the fixative (Degas fixed selected areas only; FINISHING.md)")
    elif name == "ink":
        if not any(o in ops for o in ("seal", "dots")):
            flags.append("ink: no last dark dots or seal (FINISHING.md)")
        pen = getattr(cv, "pencil", None)
        if pen is not None and float((pen > 0.05).mean()) > 0.002 and "erase-pencil" not in ops:
            flags.append("ink: pencil construction lines still show (finish erase-pencil)")
    return lines, flags


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
        s = role_view(cv, img, args[0] if args else None).resize((vw, vh), Image.LANCZOS)
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


def look_refs(cv, args):
    """`look refs [FEATURE]`: the reference sheet (refs/, tools/find_refs.py) beside the canvas, to compare structure
    and light, never to copy (docs/research/references.md). With FEATURE, only the references studied for it."""
    rdir = os.path.join(D, "refs")
    feat = " ".join(args).strip().lower()
    sheet = None
    if feat and os.path.exists(os.path.join(rdir, "refs.json")):
        refs = [r for r in json.load(open(os.path.join(rdir, "refs.json"))).get("refs", [])
                if feat in (r.get("feature") or "").lower() and os.path.exists(os.path.join(rdir, r.get("file", "")))]
        if refs:
            T, cols = 360, 2 if len(refs) <= 4 else 3
            sheet = Image.new("RGB", (cols * (T + 8) + 8, ((len(refs) + cols - 1) // cols) * (T + 8) + 8), (28, 27, 25))
            for k, r in enumerate(refs):
                im = Image.open(os.path.join(rdir, r["file"])).convert("RGB"); im.thumbnail((T, T))
                sheet.paste(im, (8 + (k % cols) * (T + 8) + (T - im.width) // 2, 8 + (k // cols) * (T + 8) + (T - im.height) // 2))
            print("\n".join(f"- {r.get('title', '')[:70]} ({r.get('artist', '')[:40]}, {r.get('date', '')}): {r.get('reason', '')}" for r in refs))
    elif os.path.exists(os.path.join(rdir, "sheet.jpg")):
        sheet = Image.open(os.path.join(rdir, "sheet.jpg")).convert("RGB")
    if sheet is None:
        print("no references" + (f" for '{feat}'" if feat else "") + ": gather them with tools/find_refs.py <workdir> ... --feature ...")
        return
    h = 800
    a = cv.render().resize((max(1, cv.W * h // cv.H), h), Image.LANCZOS)
    b = sheet.resize((max(1, sheet.width * h // sheet.height), h), Image.LANCZOS)
    if b.width > 1400:
        b = sheet.resize((1400, max(1, sheet.height * 1400 // sheet.width)), Image.LANCZOS)
    s = Image.new("RGB", (a.width + 12 + b.width, max(h, b.height)), (20, 20, 20))
    s.paste(a, (0, 0)); s.paste(b, (a.width + 12, 0))
    s.save(P("look.png"))
    print(P("look.png"))


def record(cv, img=None):
    img = img or cv.render()
    os.makedirs(FRAMES, exist_ok=True)
    n = len(os.listdir(FRAMES))
    img.resize((cv.W * 3 // 8 // 2 * 2, cv.H * 3 // 8 // 2 * 2), Image.LANCZOS).save(os.path.join(FRAMES, f"{n:05d}.jpg"), quality=88)
    img.save(P("full.png"))
    img.resize((cv.W // 2, cv.H // 2), Image.LANCZOS).save(P("view.png"))
    if cv.meta.get("detail"):          # a detail's frames go into its canvas's time-lapse too (zoomed in)
        import detail
        detail.zoom_frame(sys.modules[__name__], cv, img)


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
        for key in ("--medium", "--support", "--style", "--px-per-mm"):
            if key in args:
                i = args.index(key); opt[key[2:]] = args[i + 1]; del args[i:i + 2]
        g = args[0] if args else "#c8b89a"
        wh = list(map(int, args[1:3])) if len(args) > 2 else [1200, 1600]
        extra = {}
        if opt.get("style"):
            extra["style"] = opt["style"]
        if opt.get("px-per-mm"):
            extra["px_per_mm"] = float(opt["px-per-mm"])    # the sheet's scale, known before the medium sets up (ink, engraving at 16)
        Canvas.new(g, *wh, medium=opt.get("medium", "oil"), support=opt.get("support"), extra=extra)
        cv = Canvas(); record(cv); print(P("view.png")); sys.exit()
    if cmd == "media":
        media_list(); sys.exit()
    if cmd == "timelapse":
        timelapse(); sys.exit()
    if cmd == "detail":
        import detail as dt
        core = sys.modules[__name__]
        a = sys.argv[2:]
        sub = a[0] if a else "status"
        if sub == "open":
            if NAME.endswith("_detail"):
                sys.exit("open a detail from its canvas (without --detail).")
            opt = {}
            for key in ("--scale", "--margin"):
                if key in a:
                    i = a.index(key); opt[key[2:]] = float(a[i + 1]); del a[i:i + 2]
            if len(a) < 5:
                sys.exit("detail open X Y W H [--scale N] [--margin M]   (canvas px)")
            NAME = dt.parent_of(NAME)
            dt.open_detail(core, *map(float, a[1:5]), scale=int(opt.get("scale", 4)), margin=opt.get("margin"))
        elif sub in ("close", "cancel"):
            NAME = dt.parent_of(NAME)
            FRAMES = os.path.join(D, f"{NAME}_frames")
            rs = a[a.index("--resample") + 1] if "--resample" in a else "area"
            dt.close_detail(core, cancel=(sub == "cancel"), resample=rs)
        else:
            m = Canvas().meta
            d = m.get("detail") or m.get("detail_open")
            print(f"detail open: {d}" if d else "no detail open" + (f"; {len(m.get('details', []))} closed" if m.get("details") else ""))
        sys.exit()
    if cmd == "new" and NAME.endswith("_detail"):
        sys.exit("a detail is opened from its canvas with `detail open`, not `new`.")
    cv = Canvas()
    if cv.meta.get("detail") and cmd in ("finish", "sign", "timelapse"):
        sys.exit(f"`{cmd}` is for the whole canvas: `detail close` first.")
    if cv.meta.get("detail_open") and cmd in ("act", "dry", "transfer", "finish", "sign"):
        print("[detail] note: a detail is open on this canvas; paint in its region now is overwritten where the detail "
              "paints when it closes (work there with --detail).")
    if cmd == "ref":
        set_ref(cv, sys.argv[2]); look(cv, "ref", []); sys.exit()
    if cmd == "scene" and cv.meta.get("detail"):      # the scene, rendered for the detail's region (detail.py)
        import detail as dt
        q = sys.argv[-1] if sys.argv[-1] in ("draft", "final") else "draft"
        out = dt.scene_crop(sys.modules[__name__], cv, sys.argv[2], q)
        set_ref(cv, out); look(cv, "ref", []); sys.exit()
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
    if cmd == "look" and sys.argv[2] == "detail":
        import detail as dt
        dt.look_detail(sys.modules[__name__], sys.argv[sys.argv.index("--resample") + 1] if "--resample" in sys.argv else "area"); sys.exit()
    if cmd == "look" and sys.argv[2:3] == ["refs"]: look_refs(cv, sys.argv[3:]); sys.exit()
    if cmd == "look":
        look(cv, sys.argv[2], sys.argv[3:]); sys.exit()
    if cmd == "report":
        import eyes
        rargs = [a for a in sys.argv[2:] if a != "finish"]
        style = rargs[0] if rargs else cv.meta.get("style")
        tp = next((t for t in (os.path.join(D, "targets.json"), os.path.join(D, "..", "targets.json")) if os.path.exists(t)), "")
        targets = json.load(open(tp)) if os.path.exists(tp) else {}
        target = targets.get(style) if style else None
        sp = next((t for t in (os.path.join(D, "styles.json"), os.path.join(D, "..", "styles.json")) if os.path.exists(t)), "")
        styles = json.load(open(sp)) if sp else {}
        img = cv.render()
        m = eyes.measure(img)
        m.update(eyes.mark_stats(img))
        txt = eyes.format_report(m, target, style if target else (f"{style} (no measured target yet)" if style else None))
        n_, vs, vm = eyes.value_masses(eyes.load(img))
        extra = [f"value masses (squinted): {n_}: " + ", ".join(f"L* {a:.0f} {b:.0%}" for a, b in zip(vm, vs)),
                 f"marks: orientation coherence {m['orient_coherence']:.2f}, direction spread {m['orient_spread']:.2f}, "
                 f"mark scale {m['mark_scale']:.1f} px (spread {m['mark_scale_spread']:.2f}), edge variety {m['edge_variety']:.2f}"]
        flags = []
        if m["orient_spread"] < 0.25:
            flags.append("strokes run at nearly one angle everywhere: let them follow the form (match follow, model)")
        foc = focus_of(cv, {}) or (m["focal_x"] * cv.W, m["focal_y"] * cv.H)
        l2, f2 = roles_report(cv, styles.get(style) if style else None, foc)
        extra += l2; flags += f2
        l3, f3 = clarity_report(cv, img)
        extra += l3; flags += f3
        if "finish" in sys.argv[2:]:
            l4, f4 = finish_report(cv, m, target)
            extra += ["FINISHING CHECK:"] + ["  " + l for l in l4]
            flags += [("finish: " + f) for f in f4] if f4 else []
            if not f4:
                extra.append("  the finishing did its job by every check the studio has")
        out = txt.split("\n")
        k = next((i for i, l in enumerate(out) if l.startswith("FLAGS:") or l.startswith("against")), len(out))
        out = out[:k] + extra + out[k:]
        if flags:
            fi = next((i for i, l in enumerate(out) if l.startswith("FLAGS:")), None)
            if fi is None:
                out.insert(k + len(extra), "FLAGS: " + "; ".join(flags))
            else:
                out[fi] += "; " + "; ".join(flags)
        print("\n".join(out))
        json.dump(m, open(P("report.json"), "w"), indent=1)
        sys.exit()
    if cmd == "simplify":
        a = sys.argv[2:]
        cv.meta["focus"] = [float(a[0]), float(a[1])]
        json.dump(cv.meta, open(P("meta.json"), "w"))
        simplify(cv, float(a[0]), float(a[1]), int(a[2]) if len(a) > 2 else 4, float(a[3]) if len(a) > 3 else 0.25)
        look(cv, "ref", []); sys.exit()
    if cmd == "focus":
        cv.meta["focus"] = [float(sys.argv[2]), float(sys.argv[3])]
        json.dump(cv.meta, open(P("meta.json"), "w"))
        print(f"focal point set at ({cv.meta['focus'][0]:.0f}, {cv.meta['focus'][1]:.0f})"); sys.exit()
    if cmd == "elements":
        if len(sys.argv) > 2:
            d = json.load(open(sys.argv[2]))
            els = d.get("elements", d) if isinstance(d, dict) else d
            json.dump([{"name": e["name"], "region": e["region"]} for e in els], open(P("elements.json"), "w"), indent=1)
        for name in element_masks(cv):
            print(name)
        sys.exit()
    pre_cmd = cv.col.copy()
    if cmd == "transfer" and hasattr(cv.medium, "transfer"):
        cv.medium.transfer(cv, float(sys.argv[2]) if len(sys.argv) > 2 else 0.35, sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "transfer":
        transfer(cv, float(sys.argv[2]) if len(sys.argv) > 2 else 0.35, sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "sign":
        cv.meta["signed"] = sys.argv[2] if len(sys.argv) > 2 else "auto"
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
        l0 = finish_L(cv)
        cv.medium.finish(cv, sys.argv[2], params)
        l1 = finish_L(cv)
        cv.meta.setdefault("finishes", []).append({"op": sys.argv[2], "params": params, "L_before": round(l0, 2), "L_after": round(l1, 2)})
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
        if ep.get("focus"):
            cv.meta["focus"] = [float(v) for v in ep["focus"][:2]]
        before = cv.col.copy()
        done = []
        for k, it in enumerate(todo):
            rng = np.random.default_rng(it.get("seed", nlog * 131 + k * 17 + 3))
            kind = intent_kind(it)
            if kind not in INTENT:
                sys.exit(f"Unknown intention '{kind}'. Intentions: {', '.join(INTENT)}")
            hd = getattr(cv.medium, "hand_defaults", None)     # a medium's defaults for this intention (explicit keys win)
            if hd is not None and not legacy(cv):
                it = dict(hd(it, kind) or {}, **it)
            role = infer_role(cv, it, kind)
            pre = cv.col.copy()
            INTENT[kind](cv, dict(it, _role=role) if role else it, felt, rng)
            cv.clip = None
            if hasattr(cv.medium, "flush"):        # media that print or lay a stroke when the hand lifts
                cv.medium.flush()
            ch = np.abs(cv.col - pre).sum(-1) > 0.02
            done.append((role, ch))
        pre_end = cv.col.copy()
        cv.medium.episode_end(cv)
        late = np.abs(cv.col - pre_end).sum(-1) > 0.02      # washes settling, blocks printed at the episode's end
        if done:
            late &= ~np.any([c for _, c in done], 0)
            last = max((k for k, (r, _) in enumerate(done) if r), default=None)
            for k, (role, ch) in enumerate(done):
                record_role(cv, role, ch | late if k == last else ch, nlog * 4 + k)
        pp = P("passes.npy")
        passes = np.load(pp).astype(np.float32) if os.path.exists(pp) else np.zeros((cv.H, cv.W), np.float32)
        passes += (np.abs(cv.col - before).sum(-1) > 0.04)
        np.save(pp, np.clip(passes, 0, 255).astype(np.uint8))
        with open(P("log.jsonl"), "a") as f:
            f.write(json.dumps(ep) + "\n")
    if cmd == "transfer":
        record_role(cv, "drawing", np.abs(cv.col - pre_cmd).sum(-1) > 0.02, sum(1 for _ in open(P("log.jsonl"))) * 4)
    cv.save()
    record(cv)
    print(P("view.png"))
