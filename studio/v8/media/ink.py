"""Ink: East Asian ink and brush (shuimo, sumi-e) and Western pen and ink with washes.

How it is modelled (docs/MEDIA.md, "Ink", Engine model):
- Ink is a carbon film: every stroke darkens the paper by Beer's law, col *= exp(-density * k_ink), so
  strokes layer and darken and can never be covered or corrected. A few light colours (plant and mineral
  colours) are Kubelka-Munk films (base.km_layer) laid with the ink.
- Tone is dilution: jiao, nong, zhong, dan, qing (scorched, thick, medium, light, clear), from the `tone`
  parameter or from the lightness of the colour asked for. Thicker ink carries less water.
- The Chinese brush is a row of hairs across the tuft, each with its own load of ink and water (after
  Strassmann's hairy brush). The tip is loaded dark and the belly light and wet, so one stroke carries
  several tones; light pressure lets only the dark tip touch, pressing spreads the belly (width swells).
  Hairs run dry at different times and speed separates them: flying white (feibai), streaks of bare
  paper along the stroke.
- A stroke is laid into a stroke buffer (ink coverage and water). When it ends (the next stroke starts or
  the episode ends) its liquid ink spreads: on raw xuan a coarse-grid, MoXi-like flow along the paper's
  fibres with pinning (the front stops where too little water is left, ink piles up at the front), so wet
  ink feathers into a pale, fibrous halo with a darker rim; strokes into still-damp ink fuse. Sized xuan,
  silk, bristol and laid paper hold the ink where it lands (a slight soft edge, a darker rim when wet).
- Pens: a flexible steel nib (width swells with pressure and on down-strokes), a technical pen (even
  line), a reed pen (width set by direction); occasional blots at slow starts; a hatching tool.
State arrays: col (apparent colour), water (dampness 0..1), ink (carbon density laid), pencil (graphite
construction layer, erasable).
"""
import numpy as np, math, os, json
from scipy.ndimage import gaussian_filter, zoom
from PIL import Image, ImageDraw, ImageFont
from .base import Medium, hx, noise_field, pigment_from_hex, km_layer

# tone -> (optical density of the tip load, water in the brush)
TONES = {"jiao": (3.6, 0.32), "nong": (2.5, 0.52), "zhong": (1.3, 0.72), "dan": (0.55, 0.86), "qing": (0.2, 0.94)}
# ink kinds: relative absorption per channel (mean 1). Pine soot dilutes to a cool grey, oil soot is
# neutral, iron gall / sepia / bistre are the brown Western drawing inks.
INKS = {"pine": [1.02, 1.0, 0.95], "oil": [0.99, 1.0, 1.01], "carbon": [1.0, 1.0, 1.0],
        "iron_gall": [0.86, 1.0, 1.14], "sepia": [0.8, 0.98, 1.22], "bistre": [0.72, 0.97, 1.31]}
# support -> tone, bleed (how far liquid ink spreads, 0..1), how fast water sinks in between episodes
SUP = {"xuan_raw": dict(tone="#f3eee2", bleed=1.0, keep=0.3),
       "xuan_sized": dict(tone="#efe8d6", bleed=0.22, keep=0.55),
       "silk": dict(tone="#e6d9bb", bleed=0.15, keep=0.55),
       "bristol": dict(tone="#fbfaf6", bleed=0.06, keep=0.45),
       "laid_paper": dict(tone="#efe6d2", bleed=0.3, keep=0.5)}
ALIAS = {"brush_chinese": "brush", "round": "brush", "filbert": "brush", "liner": "brush",
         "flat": "brush_side", "fan": "brush_side", "knife": "brush_side",
         "pen_nib": "pen", "pen_tech": "pen", "pen_reed": "pen", "wash_brush": "wash",
         "blend": "water", "smudge": "water", "dots": "brush"}
NIB = {"pen_tech": "tech", "pen_reed": "reed"}
STUDIO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lum(c):
    return float(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])


def _norm(a):
    lo, hi = np.percentile(a, 1), np.percentile(a, 99)
    return np.clip((a - lo) / (hi - lo + 1e-6), 0, 1).astype(np.float32)


def fibres(h, w, seed, n, lmin, lmax, iso=True):
    """Paper fibres: many thin random line segments (xuan is made of long bark fibres)."""
    rng = np.random.default_rng(seed)
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    for _ in range(int(n)):
        x, y = rng.random() * w, rng.random() * h
        a = rng.random() * math.pi if iso else rng.normal(0, 0.35)
        L = rng.uniform(lmin, lmax)
        dx, dy = math.cos(a) * L / 2, math.sin(a) * L / 2
        # slightly curved: two segments
        bx, by = rng.normal(0, L * 0.06, 2)
        d.line([(x - dx, y - dy), (x + bx, y + by), (x + dx, y + dy)], fill=int(rng.integers(90, 256)), width=1)
    return gaussian_filter(np.asarray(img, np.float32) / 255, 0.45)


def region(reg, W, H, feather=1.5):
    t = (reg or {}).get("type", "canvas")
    if t == "canvas":
        return np.ones((H, W), np.float32)
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    if t == "ellipse":
        d.ellipse([reg["cx"] - reg["rx"], reg["cy"] - reg["ry"], reg["cx"] + reg["rx"], reg["cy"] + reg["ry"]], fill=255)
    elif t == "rect":
        d.rectangle([reg["x"], reg["y"], reg["x"] + reg["w"], reg["y"] + reg["h"]], fill=255)
    elif t == "poly":
        d.polygon([tuple(p) for p in reg["pts"]], fill=255)
    return gaussian_filter(np.asarray(m, np.float32) / 255, feather)


def seg(arr, x0, y0, x1, y1, w0, w1, val, clip=None):
    """Anti-aliased tapered line segment, max-blended into arr. Returns the bbox touched or None."""
    H, W = arr.shape
    R = max(w0, w1) / 2 + 2
    bx0, bx1 = max(0, int(min(x0, x1) - R)), min(W, int(max(x0, x1) + R) + 1)
    by0, by1 = max(0, int(min(y0, y1) - R)), min(H, int(max(y0, y1) + R) + 1)
    if bx0 >= bx1 or by0 >= by1:
        return None
    yy, xx = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
    dx, dy = x1 - x0, y1 - y0
    t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / (dx * dx + dy * dy + 1e-6), 0, 1)
    d = np.hypot(xx - (x0 + t * dx), yy - (y0 + t * dy))
    m = np.clip((w0 + (w1 - w0) * t) / 2 - d + 0.5, 0, 1)
    if clip is not None:
        m = m * clip[by0:by1, bx0:bx1]
    sl = (slice(by0, by1), slice(bx0, bx1))
    np.maximum(arr[sl], m * val, out=arr[sl])
    return bx0, by0, bx1, by1


class InkTool:
    """One loaded brush or pen for one stroke. The core sets .size, .step, .speedfx (and .liner)."""

    def __init__(self, med, kind, size, color, rng, it, nib=None):
        self.med, self.kind, self.size, self.rng, self.it = med, kind, float(size), rng, it
        self.color = np.clip(np.asarray(color, np.float32), 0, 1)
        self.nib = it.get("nib", nib or "flex")
        self.load = float(it.get("load", 1.0)) * rng.uniform(0.88, 1.08)
        self.cv = None
        self.bb = None
        self.acc = 0.0
        self.ndab = 0
        self.wmax = 0.0
        self.pts = []
        K = int(np.clip(self.size * 1.1, 7, 72))
        self.K = K
        self.bpos = np.linspace(-1, 1, K).astype(np.float32)
        self.blen = np.clip(rng.normal(0.97, 0.05, K), 0.82, 1.06).astype(np.float32)
        if kind == "brush_side":
            self.blen = np.clip(rng.normal(0.7, 0.24, K), 0.2, 1.05).astype(np.float32)
        self.bn = rng.random(K).astype(np.float32)          # which hairs separate first
        self.brate = np.clip(rng.normal(1.0, 0.3, K), 0.45, 1.8).astype(np.float32)
        self.walk = 0.75
        self.blot = float(it.get("blots", 0.12))

    # ------------------------------------------------------------------ setup on first contact
    def _begin(self, cv):
        self.cv = cv
        self.clip = None if cv.clip is None else cv.clip.copy()
        paper = self.med.paper(cv)
        it = self.it
        c = self.color
        L, Lp = max(lum(c), 0.02), lum(paper)
        chroma = float(c.max() - c.min())
        tone = it.get("tone")
        self.tint = None
        D = None
        water = None
        if tone is not None:
            if isinstance(tone, str):
                D, water = TONES.get(tone, TONES["zhong"])
            else:
                t = float(np.clip(tone, 0, 1))
                D, water = 0.12 + 3.5 * t ** 1.3, 0.95 - 0.62 * t
        if chroma < 0.07 or it.get("ink_only"):
            if D is None:
                D = float(np.clip(-math.log(L / Lp), 0, 4.2))
        else:
            # the colour asked for is how it should look on this paper: the film over white is the ratio
            sat = float(it.get("chroma", 0.85))
            light = L > Lp - 0.03
            ratio = np.clip(c / np.maximum(paper, 0.05), 0, 1)
            hue = ratio / max(ratio.max(), 1e-3)
            cl = c if light else 0.98 * (1 - sat * (1 - hue))
            L = max(lum(ratio), 0.02) * Lp
            op = 0.65 if light else float(it.get("pigment_opacity", 0.2))
            K, S = pigment_from_hex(np.clip(cl, 0.02, 0.98), op)
            self.tint = (K, S, 1.0)
            if D is None:
                D = 0.0 if light else float(np.clip(-math.log(L / max(lum(cl) * Lp, L)), 0, 4.0))
        self.D = float(D) * float(it.get("density", 1.0))
        if water is None:
            water = float(np.clip(0.95 - 0.17 * self.D, 0.3, 0.95))
        self.water = float(it.get("water", water))
        kink = np.asarray(INKS.get(it.get("ink", "pine"), INKS["pine"]), np.float32)
        self.kink = kink / kink.mean()
        k = self.kind
        self.belly = float(it.get("belly", 1.0 if it.get("loading") == "even" else 0.34))
        if k in ("wash", "splash"):
            self.belly = float(it.get("belly", 1.0))
            self.water = float(it.get("water", min(1.25, self.water + (0.25 if k == "splash" else 0.12))))
        if k == "brush_side":
            self.water = float(it.get("water", self.water * 0.72))
        if k in ("pen", "hatch"):
            self.water = float(it.get("water", 0.32))
        # each hair's reservoir (1 = fully loaded); the belly holds more than the edges of the tuft
        res = (1 - 0.25 * self.bpos ** 2) if k == "brush" else np.ones(self.K, np.float32)
        self.wb = (res * self.load * np.clip(self.rng.normal(1, 0.08, self.K), 0.75, 1.25)).astype(np.float32)
        self.thick = 0.55 + 0.6 * min(self.water, 1.0)   # thick (dry) ink drags and empties the brush sooner
        self.ink = 1.0
        H, W = cv.H, cv.W
        self.X = np.zeros((H, W), np.float32)    # ink coverage of this stroke (1 = the stroke's full density)
        self.Wl = np.zeros((H, W), np.float32)   # liquid laid with it
        self.med._pending = self

    def _bbx(self, x0, y0, x1, y1):
        if self.bb is None:
            self.bb = [x0, y0, x1, y1]
        else:
            b = self.bb
            b[0], b[1], b[2], b[3] = min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)

    def _win(self, cv, x, y, ang, R):
        R = int(math.ceil(R)) + 1
        x0, x1 = max(0, int(x) - R), min(cv.W, int(x) + R + 1)
        y0, y1 = max(0, int(y) - R), min(cv.H, int(y) + R + 1)
        if x0 >= x1 or y0 >= y1:
            return None
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dx, dy = xx - x, yy - y
        ca, sa = math.cos(ang), math.sin(ang)
        self._bbx(x0, y0, x1, y1)
        return (slice(y0, y1), slice(x0, x1)), dx * ca + dy * sa, -dx * sa + dy * ca, dx, dy

    def _lay(self, sl, m, conc, wet):
        if self.clip is not None:
            m = m * self.clip[sl]
        np.maximum(self.X[sl], m * conc, out=self.X[sl])
        wv = m * wet
        np.maximum(self.Wl[sl], wv, out=self.Wl[sl])
        self.wmax = max(self.wmax, float(wv.max()) if wv.size else 0.0)

    # ------------------------------------------------------------------ the dab
    def dab(self, cv, x, y, ang, press, rscale=1.0):
        if self.cv is None:
            self._begin(cv)
        st = float(getattr(self, "step", 0.0)) if self.ndab else 0.0
        self.acc += st
        k = self.kind
        if k == "hatch":
            self.pts.append((x, y, ang, press))
            self.ndab += 1
            return
        rt = max(0.6, self.size / 2 * rscale)
        minsp = {"pen": 0.35, "pencil": 0.35}.get(k, max(0.45, rt * 0.12))
        if k == "splash":
            minsp = rt * 0.55
        if self.ndab and self.acc < minsp:
            return
        dist, self.acc = self.acc, 0.0
        self.ndab += 1
        f = getattr(self, "_" + k.replace("brush_side", "side"), None) or self._brush
        f(cv, x, y, ang, float(press), rt, dist, st)

    def _dwell(self, st):
        return float(np.clip(self.size * 0.035 / (st + 1e-3), 0.8, 1.3))

    def _gate(self, cv, sl, bi, wetb, press, dry_bias=0.0, patch=0.15):
        """Flying white: hairs that run dry (or move fast) stop marking, the rest catch the paper's tooth
        (fine grain, and in patches where the brush skips over the paper)."""
        eff = wetb - float(getattr(self, "speedfx", 0.0)) * 1.3 - dry_bias
        thr = np.clip((0.46 - eff) / 0.46, 0, 1.15) + max(0.0, 0.22 - press) * 2.0
        g = (0.5 - patch / 2) * cv.tex[sl] + (0.5 - patch / 2) * self.bn[bi] + patch * self.med.fields(cv)[1][sl]
        return np.clip((g + 0.22 - thr * 1.05) * 6, 0, 1)

    def _brush(self, cv, x, y, ang, press, rt, dist, st):
        c = float(np.clip(0.2 + 0.85 * max(press, 0.0) ** 0.75, 0.15, 1.12))
        r = max(0.55, rt * c)
        ru = r * 0.8
        w = self._win(cv, x, y, ang, r + 1.5)
        if w is None:
            return
        sl, u, v, _, _ = w
        t = np.clip(v / r, -1.2, 1.2)
        bi = np.clip(((t + 1) * 0.5 * (self.K - 1) + 0.5).astype(np.int32), 0, self.K - 1)
        d2 = (u / ru) ** 2 + (v / r) ** 2
        m = np.clip((self.blen[bi] - d2) * 3, 0, 1) ** 0.6
        p = np.clip(np.abs(t) * min(c, 1.0), 0, 1)
        conc = self.belly + (1 - self.belly) * (1 - p) ** 1.4
        wetb = self.wb[bi]
        conc = conc * (1 - (0.06 + 0.3 * np.clip(1 - wetb, 0, 1)) * self.bn[bi])   # hair streaks
        m = m * self._gate(cv, sl, bi, wetb, press)
        self._lay(sl, m, conc * (0.8 + 0.2 * np.minimum(1, wetb * 1.6)), self.water * np.minimum(1, wetb * 1.5) * self._dwell(st))
        touch = np.abs(self.bpos) <= min(c, 1.0) + 0.06
        self.wb -= dist * self.brate * touch * (0.35 + 0.65 * min(press, 1.0)) / (max(self.size, 2) * 26 * self.thick)
        np.maximum(self.wb, 0, out=self.wb)

    def _side(self, cv, x, y, ang, press, rt, dist, st):
        r = rt * (0.8 + 0.55 * min(press, 1.2))
        ru = max(0.9, r * 0.3)
        w = self._win(cv, x, y, ang, r + 1.5)
        if w is None:
            return
        sl, u, v, _, _ = w
        t = np.clip(v / r, -1.3, 1.3)
        bi = np.clip(((t + 1) * 0.5 * (self.K - 1) + 0.5).astype(np.int32), 0, self.K - 1)
        patch = self.med.fields(cv)[1][sl]
        across = np.clip((self.blen[bi] + 0.5 * (patch - 0.5) - t) * r * 0.5, 0, 1) * np.clip((t + 1) * r + 0.5, 0, 1)
        m = across * np.clip(1 - (u / ru) ** 2, 0, 1) ** 0.5
        pp = np.clip((t + 1) / 2, 0, 1)
        conc = self.belly + (1 - self.belly) * (1 - pp) ** 1.3
        wetb = self.wb[bi]
        conc = conc * (1 - (0.1 + 0.3 * np.clip(1 - wetb, 0, 1)) * self.bn[bi])
        m = m * self._gate(cv, sl, bi, wetb, press, dry_bias=0.24 + 0.3 * pp, patch=0.45)
        self._lay(sl, m, conc * (0.8 + 0.2 * np.minimum(1, wetb * 1.6)), self.water * np.minimum(1, wetb * 1.5) * self._dwell(st))
        self.wb -= dist * self.brate * (0.4 + 0.6 * min(press, 1.0)) / (max(self.size, 2) * 18 * self.thick)
        np.maximum(self.wb, 0, out=self.wb)

    def _wash(self, cv, x, y, ang, press, rt, dist, st):
        r = rt * (0.75 + 0.4 * min(press, 1.2))
        w = self._win(cv, x, y, ang, r + 1)
        if w is None:
            return
        sl, u, v, _, _ = w
        d2 = (u / (r * 0.9)) ** 2 + (v / r) ** 2
        m = np.clip(1 - d2, 0, 1) ** 1.6
        self.walk = float(np.clip(self.walk + self.rng.normal(0, 0.02), 0.85, 1.1))
        wet = float(self.wb.mean())
        if wet < 0.4:
            m = m * self._gate(cv, sl, np.zeros(m.shape, np.int32), wet, press)
        mot = 0.9 + 0.2 * self.med.fields(cv)[1][sl]
        self._lay(sl, m, mot * self.walk * (0.85 + 0.15 * min(1, wet * 1.5)), self.water * min(1.0, wet * 1.5) * self._dwell(st))
        self.wb -= dist * (0.4 + 0.6 * min(press, 1.0)) / (max(self.size, 2) * 60 * self.thick)
        np.maximum(self.wb, 0, out=self.wb)

    def _water(self, cv, x, y, ang, press, rt, dist, st):
        r = rt * (0.75 + 0.4 * min(press, 1.2))
        w = self._win(cv, x, y, ang, r + 1)
        if w is None:
            return
        sl, u, v, _, _ = w
        m = np.clip(1 - (u * u + v * v) / (r * r), 0, 1) ** 0.6
        if self.clip is not None:
            m = m * self.clip[sl]
        np.maximum(self.Wl[sl], m * min(1, press + 0.2), out=self.Wl[sl])

    def _splash(self, cv, x, y, ang, press, rt, dist, st):
        rng = self.rng
        R = rt * (0.7 + 0.8 * min(press, 1.2)) * rng.uniform(0.65, 1.35)
        w = self._win(cv, x + rng.normal(0, rt * 0.25), y + rng.normal(0, rt * 0.25), ang, R * 1.6 + 2)
        if w is None:
            return
        sl, u, v, dx, dy = w
        th = np.arctan2(dy, dx)
        ph = rng.random(3) * 6.283
        rad = R * (1 + 0.22 * np.sin(3 * th + ph[0]) + 0.14 * np.sin(5 * th + ph[1]) + 0.08 * np.sin(8 * th + ph[2]))
        m = np.clip((rad - np.hypot(dx, dy)) * 0.7, 0, 1)
        if self.clip is not None:
            m = m * self.clip[sl]
        self.walk = float(np.clip(self.walk + rng.normal(0, 0.22), 0.18, 1.15))
        X = self.X[sl]
        X += m * (self.walk - X) * 0.85
        np.maximum(X, 0, out=X)
        wv = m * self.water * rng.uniform(0.9, 1.25)
        np.maximum(self.Wl[sl], wv, out=self.Wl[sl])
        self.wmax = max(self.wmax, float(wv.max()))

    def _pencil(self, cv, x, y, ang, press, rt, dist, st):
        r = max(0.55, self.size * 0.05 * (0.6 + 0.6 * min(press, 1.2)))
        w = self._win(cv, x, y, ang, r + 1)
        if w is None:
            return
        sl, u, v, _, _ = w
        m = np.clip(r - np.hypot(u, v) + 0.5, 0, 1) * np.clip(cv.tex[sl] * 1.6 + 0.1, 0, 1)
        if self.clip is not None:
            m = m * self.clip[sl]
        np.maximum(self.X[sl], m * (0.35 + 0.4 * min(press, 1.0)), out=self.X[sl])

    def _pen_width(self, ang, press):
        wmax, wmin = max(1.0, self.size * 0.38), max(0.6, self.size * 0.06)
        if self.nib == "tech":
            return max(0.7, self.size * 0.14)
        down = max(0.0, math.sin(ang))     # pulling the nib toward you spreads the tines
        return wmin + (wmax - wmin) * min(press, 1.15) ** 1.6 * (0.6 + 0.4 * down)

    def _pen(self, cv, x, y, ang, press, rt, dist, st):
        fresh = self.ndab == 1
        if self.nib == "reed":
            wmax = max(1.5, self.size * 0.42)
            ea = math.radians(self.it.get("nib_angle", 35))
            w = self._win(cv, x, y, ea, wmax / 2 + 2)
            if w is None:
                return
            sl, u, v, _, _ = w
            m = np.clip(wmax / 2 - np.abs(u) + 0.5, 0, 1) * np.clip(1.1 - np.abs(v), 0, 1)
            m = m * np.clip(cv.tex[sl] * 2.2 + 0.25, 0, 1)   # blunt reed: gritty
        else:
            r = self._pen_width(ang, press) / 2
            w = self._win(cv, x, y, ang, r + 1.5)
            if w is None:
                return
            sl, u, v, _, _ = w
            m = np.clip(r - np.hypot(u, v) + 0.5, 0, 1)
        self.ink -= dist / (max(self.size, 2) * 110 * self.load)
        if self.ink < 0.3:
            m = m * np.clip((cv.tex[sl] - (0.3 - self.ink) * 2.5) * 5 + 0.5, 0, 1)
        conc = 0.55 + 0.45 * min(1.0, max(self.ink, 0) / 0.3)
        self._lay(sl, m, conc, self.water)
        if fresh and self.rng.random() < self.blot and self.nib != "tech":
            rb = self._pen_width(ang, 1.0) * self.rng.uniform(0.9, 1.6)
            w = self._win(cv, x + self.rng.normal(0, 0.6), y + self.rng.normal(0, 0.6), ang, rb + 2)
            if w is not None:
                sl, u, v, _, _ = w
                self._lay(sl, np.clip(rb - np.hypot(u, v), 0, 1), 1.05, 0.95)


class Ink(Medium):
    name = "ink"
    arrays = ("col", "water", "ink", "pencil")
    supports = {"xuan_raw": "raw (unsized) xuan rice paper: absorbent, wet ink bleeds and feathers along the fibres; no correcting",
                "xuan_sized": "sized ('cooked') xuan: ink sits where it lands, crisp lines (gongbi)",
                "silk": "sized silk, warm tone, fine weave, very little bleed",
                "bristol": "smooth hard drawing board for pen and ink; no bleed",
                "laid_paper": "laid paper with laid and chain lines; slight bleed, a little grit for pen"}
    tools = {"brush": "Chinese brush, upright (centre tip): dark tip, wet pale belly; width swells with pressure; flying white when dry or fast",
             "brush_side": "side brush (oblique): broad stroke, sharp dark edge on the tip side, ragged pale edge on the belly side, much flying white",
             "splash": "splashed ink (pomo): wet irregular pools of varying tone that fuse and bleed, a few droplets",
             "wash": "soft wash brush: even, wet, diluted ink (or light colour) over an area",
             "pen": "dip pen: flexible steel nib, line swells with pressure and on down-strokes; occasional blot at a slow start (nib: flex|tech|reed)",
             "hatch": "pen hatching: each stroke lays a band of parallel pen lines across its path (cross-hatched when pressed hard or cross: true)",
             "water": "clean wet brush: fuses and softens ink that is still damp (also used for 'blend')",
             "pencil": "light graphite construction line, removed later by finish erase-pencil"}
    finishes = {"dots": "the last dark accents: dots in scorched ink with a small upright brush (pts or region+count, at most 40)",
                "seal": "stamp the red cinnabar seal (text, at br|bl|tr|tl|[x,y], size, style baiwen|zhuwen)",
                "erase-pencil": "erase the graphite construction lines wherever ink does not cover them",
                "scrape": "scrape ink off for a highlight (region, amount 0..1); leaves the paper slightly roughened",
                "mount": "presentation: show the work mounted (style scroll|album|mat, color) in renders; the paint is unchanged"}

    _pending = None

    # ------------------------------------------------------------------ support
    def texture(self, h, w, support):
        support = support if support in SUP else "xuan_raw"
        a = h * w
        if support.startswith("xuan"):
            # the tooth: fine grain and cloudy formation, with only a faint trace of the fibres
            fib = fibres(h, w, 11, a / 260, 6, 30)
            t = 0.55 * noise_field(h, w, 0.7, 5) + 0.27 * noise_field(h, w, 4, 3) + 0.18 * _norm(fib)
            if support == "xuan_sized":
                t = 0.6 * t + 0.4 * gaussian_filter(t, 1.2)
            return _norm(t)
        if support == "silk":
            y, x = np.mgrid[0:h, 0:w].astype(np.float32)
            wv = 0.5 + 0.25 * np.sin(x * 2.1) * np.sign(np.sin(y * 1.05)) + 0.25 * np.sin(y * 2.1) * np.sign(np.sin(x * 1.05))
            return _norm(0.45 * wv + 0.3 * noise_field(h, w, 0.7, 5) + 0.25 * noise_field(h, w, 9, 9))
        if support == "laid_paper":
            y, x = np.mgrid[0:h, 0:w].astype(np.float32)
            laid = 0.5 + 0.5 * np.sin(y * 2 * math.pi / 4.2)
            chain = 0.5 * np.exp(-((x % 96) - 48) ** 2 / 6.0)
            fib = fibres(h, w, 13, a / 400, 6, 25)
            return _norm(0.3 * laid + 0.15 * chain + 0.25 * _norm(fib) + 0.2 * noise_field(h, w, 0.8, 5) + 0.1 * noise_field(h, w, 12, 3))
        # bristol: smooth
        return (0.55 + 0.3 * (noise_field(h, w, 0.7, 7) - 0.5) + 0.15 * (noise_field(h, w, 10, 3) - 0.5)).astype(np.float32)

    _fcache = {}

    def fields(self, cv):
        """The paper's fibre network for the flow (permeability 0..1) and a pinning noise, both full size.
        Deterministic for a canvas size and support, so they are recomputed rather than stored."""
        key = (cv.H, cv.W, cv.meta.get("support"))
        if key not in self._fcache:
            h, w = cv.H, cv.W
            fib = _norm(fibres(h, w, 17, h * w / 60, 10, 60))
            fib = _norm(0.7 * gaussian_filter(fib, 0.8) + 0.3 * noise_field(h, w, 3, 8))
            pin = _norm(noise_field(h, w, 3.5, 23) * 0.6 + noise_field(h, w, 1.2, 29) * 0.4)
            Ink._fcache = {key: (fib, pin)}
        return self._fcache[key]

    def init_state(self, cv, ground):
        super().init_state(cv, ground)
        # paper is not tinted in blotches: replace the core's coloured ground noise with a faint
        # neutral formation (cloudiness) of the sheet
        g = cv.col.mean((0, 1))
        n = (noise_field(cv.H, cv.W, 24, 41) - 0.5) * 0.02 + (cv.tex - 0.5) * 0.012
        cv.col = np.clip(g[None, None, :] * (1 + n[..., None]), 0, 1).astype(np.float32)

    def sup(self, cv):
        return SUP.get(cv.meta.get("support", "xuan_raw"), SUP["xuan_raw"])

    def paper(self, cv):
        return hx(cv.meta.get("ground") or self.sup(cv)["tone"])

    # ------------------------------------------------------------------ tools
    def make_tool(self, it, size, color, rng):
        self.flush()
        raw = it.get("brush", "brush")
        kind = ALIAS.get(raw, raw)
        if kind not in self.tools:
            kind = "brush"
        t = InkTool(self, kind, size, color, rng, it, nib=NIB.get(raw))
        if raw == "liner":
            t.liner = True
        return t

    def flush(self):
        """Finish the pending stroke: its liquid ink spreads into the paper and the ink is fixed."""
        t, self._pending = self._pending, None
        if t is None or t.cv is None:
            return
        cv = t.cv
        if t.kind == "hatch":
            self._hatch(t)
        if t.bb is None:
            return
        sp = self.sup(cv)
        bleed = sp["bleed"]
        x0, y0, x1, y1 = t.bb
        wl = min(1.4, t.wmax)
        if t.kind in ("brush", "brush_side", "wash", "splash", "pen", "hatch"):
            if bleed >= 0.5:
                pad = int(3 + bleed * (5 + t.size * 0.45 + 16) * wl * (1.3 if t.kind == "splash" else 1.0))
            else:
                pad = int(3 + 8 * bleed * wl)
            x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
            x1, y1 = min(cv.W, x1 + pad), min(cv.H, y1 + pad)
        sl = (slice(y0, y1), slice(x0, x1))
        X, Wl = t.X[sl], t.Wl[sl]
        if t.kind == "pencil":
            old = cv.pencil[sl]
            new = np.maximum(old, X)
            g = np.array([0.30, 0.29, 0.27], np.float32)
            cv.col[sl] = cv.col[sl] * ((1 - new[..., None] * g) / (1 - old[..., None] * g))
            cv.pencil[sl] = new
            return
        if t.kind == "water":
            self._soften(cv, sl, Wl, t.size)
            return
        if X.max() <= 1e-3:
            return
        if bleed >= 0.5:
            total, wet = self._bleed_raw(cv, sl, X, Wl, t, bleed)
        else:
            total, wet = self._bleed_sized(cv, sl, X, Wl, t, bleed)
        if t.clip is not None:
            total = total * np.clip(t.clip[sl] * 1.5, 0, 1)
        self._composite(cv, sl, total, t.D, t.kink, t.tint)
        cv.water[sl] = np.clip(np.maximum(cv.water[sl], wet), 0, 1)
        if t.kind == "splash":
            self._droplets(cv, t)

    # ------------------------------------------------------------------ spreading
    def _bleed_raw(self, cv, sl, X, Wl, t, bleed):
        """Raw xuan: liquid ink flows along fibres on a coarse grid; the front pins where water runs out."""
        h, w = X.shape
        f = 2 if h * w < 300_000 else (3 if h * w < 1_200_000 else 4)
        H2, W2 = -(-h // f), -(-w // f)
        P = lambda a: np.pad(a, ((0, H2 * f - h), (0, W2 * f - w)), mode="edge").reshape(H2, f, W2, f).mean((1, 3))
        damp = cv.water[sl]
        mob = np.clip(0.62 * bleed * np.minimum(Wl, 1.0) + 0.45 * damp * (Wl > 0.02), 0, 0.88)
        if t.kind == "splash":
            mob = np.clip(mob * 1.2, 0, 0.9)
        q0 = X * mob
        stay = X - q0
        fibf, pinf = self.fields(cv)
        fib = fibf[sl]
        fc, pc = P(fib), P(pinf[sl])
        wat = P(Wl) * 1.15 + P(damp) * 0.8
        q = P(q0)
        perm = (0.02 + 0.22 * fc ** 1.5).astype(np.float32)
        pin = (0.03 + 0.16 * pc ** 1.5 + 0.04 * (1 - bleed)).astype(np.float32)
        n = int(np.clip(10 + 26 * min(1.3, t.wmax) + 14 * float(damp.max()), 8, 56))
        dep = self._diffuse(wat.astype(np.float32), q.astype(np.float32), perm, pin, n, 0.085, 0.022)
        up = zoom(dep, f, order=1)[:h, :w]
        if up.shape != (h, w):
            up = np.pad(up, ((0, h - up.shape[0]), (0, w - up.shape[1])), mode="edge")
        inside = np.clip(Wl * 4, 0, 1)   # fibre texture shows in the feathered fringe, not inside the stroke
        halo = up * (1 + (1 - inside) * (0.7 * gaussian_filter(fib, 0.6) - 0.35))
        stay = gaussian_filter(stay, 0.45)
        # the darker rim where the wet stroke's own edge pinned (the ink core outline)
        wetc = zoom(np.minimum(wat, 1.2), f, order=1)[:h, :w]
        wetc = np.pad(wetc, ((0, h - wetc.shape[0]), (0, w - wetc.shape[1])), mode="edge") if wetc.shape != (h, w) else wetc
        return stay + halo, np.clip(wetc * 0.8, 0, 1)

    @staticmethod
    def _diffuse(w, q, perm, pin, n, dk, ab):
        dep = np.zeros_like(q)
        px = np.minimum(perm[:, :-1], perm[:, 1:])
        py = np.minimum(perm[:-1], perm[1:])
        for _ in range(n):
            act = w > pin
            cs = q / (w + 1e-4)
            d = w[:, :-1] - w[:, 1:]
            pos = d > 0
            F = px * d * np.where(pos, act[:, :-1], act[:, 1:]) * (0.35 + 0.65 * np.minimum(np.where(pos, w[:, :-1], w[:, 1:]), 1))
            Q = F * np.where(pos, cs[:, :-1], cs[:, 1:])
            e = w[:-1] - w[1:]
            pos = e > 0
            G = py * e * np.where(pos, act[:-1], act[1:]) * (0.35 + 0.65 * np.minimum(np.where(pos, w[:-1], w[1:]), 1))
            Qy = G * np.where(pos, cs[:-1], cs[1:])
            # carbon also diffuses inside the water film where both cells are wet (wet-in-wet fusing)
            wa = np.minimum(w, 1.0) * act
            Q += 0.16 * np.minimum(wa[:, :-1], wa[:, 1:]) * (q[:, :-1] - q[:, 1:])
            Qy += 0.16 * np.minimum(wa[:-1], wa[1:]) * (q[:-1] - q[1:])
            w[:, :-1] -= F; w[:, 1:] += F; w[:-1] -= G; w[1:] += G
            q[:, :-1] -= Q; q[:, 1:] += Q; q[:-1] -= Qy; q[1:] += Qy
            np.maximum(q, 0, out=q)
            np.maximum(w, 0, out=w)
            dd = q * dk
            dep += dd
            q -= dd
            w *= (1 - ab)
        return dep + q

    def _bleed_sized(self, cv, sl, X, Wl, t, bleed):
        """Sized paper, silk, bristol: the ink sits; a slight soft edge and a darker rim where it was wet."""
        wl = np.minimum(Wl, 1.2)
        mob = np.clip(0.5 * wl + 0.3 * cv.water[sl] * (wl > 0.02), 0, 0.7)
        q = X * mob
        s = 0.35 + 3.0 * bleed * min(1.2, t.wmax)
        total = X - q + gaussian_filter(q, s)
        if t.wmax > 0.5 and t.kind in ("wash", "splash", "brush", "brush_side"):
            cov = np.clip(wl * 1.8, 0, 1)
            rim = np.clip(cov - gaussian_filter(cov, 2.0 + t.size * 0.05), 0, 1)
            total = total + rim * gaussian_filter(X, 2.0) * (0.9 if t.kind == "splash" else 0.45)
        return total, np.clip(gaussian_filter(wl, 1.0), 0, 1)

    def _droplets(self, cv, t):
        rng = t.rng
        x0, y0, x1, y1 = t.bb
        for _ in range(int(rng.integers(1, 5))):
            cx, cy = rng.uniform(x0 - t.size, x1 + t.size), rng.uniform(y0 - t.size, y1 + t.size)
            r = rng.uniform(0.8, 0.12 * t.size + 1.5)
            R = int(r + 3)
            xa, xb, ya, yb = max(0, int(cx) - R), min(cv.W, int(cx) + R + 1), max(0, int(cy) - R), min(cv.H, int(cy) + R + 1)
            if xa >= xb or ya >= yb:
                continue
            yy, xx = np.mgrid[ya:yb, xa:xb].astype(np.float32)
            m = np.clip(r - np.hypot(xx - cx, yy - cy) + 0.5, 0, 1) * rng.uniform(0.4, 1.0)
            m = gaussian_filter(m, 0.3 + 0.6 * self.sup(cv)["bleed"])
            if t.clip is not None:
                m = m * t.clip[ya:yb, xa:xb]
            self._composite(cv, (slice(ya, yb), slice(xa, xb)), m, t.D, t.kink, t.tint)

    def _soften(self, cv, sl, Wl, size):
        damp = np.clip(cv.water[sl] * 2.2, 0, 1)
        wgt = np.clip(Wl * damp, 0, 1)
        if wgt.max() > 0.01:
            s = 1.2 + size * 0.12
            c = cv.col[sl]
            bl = np.stack([gaussian_filter(c[..., i], s) for i in range(3)], -1)
            cv.col[sl] = c * (1 - wgt[..., None]) + bl * wgt[..., None]
            cv.ink[sl] = cv.ink[sl] * (1 - wgt) + gaussian_filter(cv.ink[sl], s) * wgt
        cv.water[sl] = np.clip(np.maximum(cv.water[sl], Wl * 0.8), 0, 1)

    def _composite(self, cv, sl, total, D, kink, tint):
        """Lay the stroke's ink. Over dry ink the layers add (the overlap shows darker, nothing covers);
        into ink that is still wet, the same ink mostly re-wets what is there, so repeated strokes of
        one tone converge instead of stacking. Fibres saturate at about scorched-ink density."""
        total = np.maximum(total, 0)
        c = cv.col[sl]
        if D > 0:
            old = cv.ink[sl]
            wetf = np.clip(cv.water[sl] * 2.2, 0, 1)
            sat = np.clip(1 - old / (2.4 * D), 0.3, 1)
            f = (1 - wetf * (1 - sat)) * np.clip(1 - old / 5.0, 0.05, 1)
            total_c = total * f
            c = c * np.exp(-(total_c * D)[..., None] * kink[None, None, :])
            cv.ink[sl] += total_c * D
        if tint is not None:
            K, S, amt = tint
            c = km_layer(c, K, S, total * amt)
        cv.col[sl] = c

    def _hatch(self, t):
        cv = t.cv
        pts = t.pts
        if len(pts) < 2:
            return
        it = t.it
        xy = np.array([[p[0], p[1]] for p in pts], np.float32)
        arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))])
        pr = np.array([p[3] for p in pts], np.float32)
        base = math.radians(it.get("hatch_angle", -55))
        hw = t.size * float(it.get("band", 1.3))
        sp0 = float(it.get("spacing", max(1.8, t.size * 0.55)))
        fams = [base]
        if it.get("cross") or pr.max() > 0.95:
            fams.append(base + math.pi / 2)
        rng = t.rng
        for fi, a0 in enumerate(fams):
            s = rng.uniform(0, sp0)
            while s < arc[-1]:
                j = int(np.clip(np.searchsorted(arc, s), 1, len(xy) - 1))
                f = (s - arc[j - 1]) / max(arc[j] - arc[j - 1], 1e-6)
                cx, cy = xy[j - 1] + (xy[j] - xy[j - 1]) * f
                p = float(pr[j])
                a = a0 + rng.normal(0, 0.05)
                L = hw * rng.uniform(0.75, 1.1) * (0.6 + 0.4 * min(p, 1))
                off = rng.normal(0, hw * 0.08)
                dx, dy = math.cos(a), math.sin(a)
                ax, ay = cx - dx * L + off * dx, cy - dy * L + off * dy
                bx, by = cx + dx * L + off * dx, cy + dy * L + off * dy
                mx, my = (ax + bx) / 2 + rng.normal(0, 0.3), (ay + by) / 2 + rng.normal(0, 0.3)
                wd = max(0.6, t.size * 0.09 * (0.5 + 0.7 * min(p, 1.2)))
                for (qa, qb, wa, wb) in (((ax, ay), (mx, my), wd * 0.55, wd), ((mx, my), (bx, by), wd, wd * 0.5)):
                    bb = seg(t.X, qa[0], qa[1], qb[0], qb[1], wa, wb, 1.0, t.clip)
                    if bb:
                        seg(t.Wl, qa[0], qa[1], qb[0], qb[1], wa, wb, t.water)
                        t._bbx(*bb)
                t.wmax = max(t.wmax, t.water)
                s += sp0 * (1.45 - 0.55 * min(p, 1.2)) * rng.uniform(0.85, 1.15)

    # ------------------------------------------------------------------ washes
    def glaze(self, cv, mask, col, op):
        """An ink wash (or a light colour wash) laid flat over the masked area. On raw xuan its edge
        feathers along the fibres and the tone mottles a little; on sized paper the edge darkens."""
        self.flush()
        t2 = _Analyse(InkTool(self, "wash", 20, col, np.random.default_rng(5), {}), cv)
        sp = self.sup(cv)
        x = np.clip(mask * op, 0, 1.5).astype(np.float32)
        tex = cv.tex
        if sp["bleed"] >= 0.5:
            edge = np.clip(1 - np.abs(mask - 0.5) * 2, 0, 1)
            x = x * (1 - edge * (0.9 - 1.1 * tex)).clip(0, 1.3)
            x = x * (0.88 + 0.24 * gaussian_filter(tex, 3))
        else:
            cov = np.clip(mask * 1.5, 0, 1)
            x = x * (1 + 0.35 * np.clip(cov - gaussian_filter(cov, 4), 0, 1))
        sl = (slice(0, cv.H), slice(0, cv.W))
        self._composite(cv, sl, x, t2.D, t2.kink, t2.tint)
        cv.water = np.clip(np.maximum(cv.water, mask * min(1.0, op * 2.5) * 0.9), 0, 1)

    # ------------------------------------------------------------------ time
    def episode_end(self, cv):
        self.flush()
        cv.water *= self.sup(cv)["keep"]

    def dry(self, cv, amount):
        self.flush()
        cv.water *= (1 - amount)

    # ------------------------------------------------------------------ seeing
    def render(self, cv):
        self.flush()
        sup = cv.meta.get("support", "xuan_raw")
        k = {"silk": 0.06, "laid_paper": 0.05, "bristol": 0.015}.get(sup, 0.045)
        ink = np.clip(cv.ink, 0, 4)
        shade = 1 + k * (cv.tex - 0.5) * (1 - np.clip(ink / 3, 0, 0.8))
        img = np.clip(cv.col * shade[..., None], 0, 1)
        im = Image.fromarray((img * 255).astype(np.uint8))
        mt = cv.meta.get("mount")
        if mt:
            im = self._mounted(im, mt)
        return im

    def _mounted(self, im, mt):
        W, H = im.size
        style = mt.get("style", "scroll")
        col = tuple(int(v * 255) for v in hx(mt.get("color", "#d8ccb0")))
        if style == "scroll":
            top, bot, side = 0.13, 0.17, 0.08
        elif style == "album":
            top, bot, side = 0.08, 0.08, 0.08
        else:
            top, bot, side = 0.1, 0.12, 0.1
        iw, ih = int(W * (1 - 2 * side)), int(H * (1 - top - bot))
        sc = min(iw / W, ih / H)
        pw, ph = int(W * sc), int(H * sc)
        out = Image.new("RGB", (W, H), col)
        arr = np.asarray(out, np.float32) / 255
        n = noise_field(H, W, 0.7, 21)[..., None] * 0.05 + noise_field(H, W, 30, 4)[..., None] * 0.04
        y = np.arange(H, dtype=np.float32)[:, None, None]
        damask = 0.012 * np.sin(y * 0.9)
        out = Image.fromarray((np.clip(arr * (0.96 + n + damask), 0, 1) * 255).astype(np.uint8))
        ox, oy = (W - pw) // 2, int(H * top) + (ih - ph) // 2
        d = ImageDraw.Draw(out)
        b = max(2, int(W * 0.006))
        dark = tuple(int(v * 0.72) for v in col)
        d.rectangle([ox - b * 3, oy - b * 3, ox + pw + b * 3, oy + ph + b * 3], fill=dark)
        d.rectangle([ox - b, oy - b, ox + pw + b, oy + ph + b], fill=tuple(min(255, int(v * 1.06)) for v in col))
        out.paste(im.resize((pw, ph), Image.LANCZOS), (ox, oy))
        if style == "scroll":
            rod = max(4, int(H * 0.012))
            d.rectangle([0, H - rod, W, H], fill=(70, 45, 30))
            d.rectangle([0, 0, W, rod // 2], fill=(90, 70, 50))
        return out

    # ------------------------------------------------------------------ finishing
    def finish(self, cv, op, params):
        self.flush()
        params = params or {}
        if op == "dots":
            return self._dots(cv, params)
        if op == "seal":
            return self._seal(cv, params)
        if op == "erase-pencil":
            p = cv.pencil
            r = np.clip(1 - cv.ink / 1.5, 0, 1) * float(params.get("amount", 1.0))
            g = np.array([0.30, 0.29, 0.27], np.float32)
            newp = p * (1 - r)
            cv.col = cv.col * ((1 - newp[..., None] * g) / (1 - p[..., None] * g))
            cv.pencil = newp.astype(np.float32)
            return
        if op == "scrape":
            if "region" not in params:
                print("scrape: give a region, e.g. {\"region\": {\"type\": \"ellipse\", \"cx\": 300, \"cy\": 200, \"rx\": 20, \"ry\": 12}, \"amount\": 0.5}")
                return
            m = region(params["region"], cv.W, cv.H, params.get("feather", 1.5))
            a = np.clip(m * float(params.get("amount", 0.5)), 0, 0.95)
            # scraping takes carbon off the top fibres, unevenly, and raises the fibres (a little lighter, fuzzy)
            a = a * (0.6 + 0.8 * cv.tex)
            a = np.clip(a, 0, 0.97)
            paper = self.paper(cv) * 0.97
            cv.col = cv.col + (paper[None, None, :] - cv.col) * (a * 0.85)[..., None]
            cv.ink = cv.ink * (1 - a * 0.85)
            return
        if op == "mount":
            self._set_meta(cv, "mount", {"style": params.get("style", "scroll"), "color": params.get("color", "#d8ccb0")})
            return
        return super().finish(cv, op, params)

    def _set_meta(self, cv, key, val):
        cv.meta[key] = val
        mp = os.path.join(STUDIO, f"{os.environ.get('CANVAS', 'main')}_meta.json")
        if os.path.exists(mp):
            json.dump(cv.meta, open(mp, "w"))

    def _dots(self, cv, params):
        rng = np.random.default_rng(params.get("seed", 7))
        pts = params.get("pts")
        if not pts and "region" in params:
            m = region(params["region"], cv.W, cv.H)
            ys, xs = np.nonzero(m > 0.5)
            if len(xs):
                idx = rng.choice(len(xs), size=min(int(params.get("count", 8)), len(xs)), replace=False)
                pts = [[float(xs[i]), float(ys[i])] for i in idx]
        if not pts:
            print("dots: give pts [[x, y], ...] or a region with count")
            return
        mx = int(params.get("max", 40))
        if len(pts) > mx:
            raise SystemExit(f"dots: {len(pts)} dots asked, at most {mx}: accents are few")
        size = float(params.get("size", max(4.0, min(cv.W, cv.H) / 130)))
        col = hx(params.get("color", "#0a0a0a"))
        it = {"tone": params.get("tone", "jiao"), "water": params.get("water", 0.55)}
        for p in pts:
            t = self.make_tool(it, size * rng.uniform(0.8, 1.2), col, rng)
            a = math.radians(params.get("angle", 80)) + rng.normal(0, 0.35)
            ln = size * rng.uniform(0.2, 0.7)
            n = 6
            for i in range(n):
                f = i / (n - 1)
                t.step = ln / (n - 1) if i else 0.0
                t.speedfx = 0.0
                press = 0.5 + 0.55 * math.sin(math.pi * min(1, f * 1.3))
                t.dab(cv, p[0] + math.cos(a) * ln * f, p[1] + math.sin(a) * ln * f, a, press, 1.0)
            self.flush()

    def _seal(self, cv, params):
        size = int(params.get("size", max(24, min(cv.W, cv.H) * 0.065)))
        text = params.get("text", "TEO\nDOR")
        style = params.get("style", "baiwen")
        at = params.get("at", "br")
        mg = int(min(cv.W, cv.H) * 0.05)
        if isinstance(at, (list, tuple)):
            x0, y0 = int(at[0]), int(at[1])
        else:
            x0 = mg if "l" in at[1:] else cv.W - mg - size
            y0 = mg if at.startswith("t") else cv.H - mg - size
        x0, y0 = int(np.clip(x0, 0, cv.W - size)), int(np.clip(y0, 0, cv.H - size))
        S = size * 4
        im = Image.new("L", (S, S), 0)
        d = ImageDraw.Draw(im)
        rng = np.random.default_rng(len(text) * 7 + size)
        jitter = lambda: int(rng.normal(0, S * 0.012))
        d.polygon([(jitter(), jitter()), (S - 1 + jitter(), jitter()), (S - 1 + jitter(), S - 1 + jitter()), (jitter(), S - 1 + jitter())], fill=255)
        lines = text.split("\n")
        font = None
        for fp in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
            if os.path.exists(fp):
                font = ImageFont.truetype(fp, int(S * 0.78 / max(len(lines), 1)))
                break
        font = font or ImageFont.load_default()
        txt = Image.new("L", (S, S), 0)
        dt = ImageDraw.Draw(txt)
        lh = S * 0.84 / max(len(lines), 1)
        for i, ln in enumerate(lines):
            bb = dt.textbbox((0, 0), ln, font=font)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            sx = (S * 0.84) / max(tw, 1)
            g = Image.new("L", (max(1, tw), max(1, th)), 0)
            ImageDraw.Draw(g).text((-bb[0], -bb[1]), ln, font=font, fill=255)
            g = g.resize((int(S * 0.84), int(lh * 0.86)))
            txt.paste(g, (int(S * 0.08), int(S * 0.08 + i * lh)), g)
        border = Image.new("L", (S, S), 0)
        ImageDraw.Draw(border).rectangle([int(S * 0.035), int(S * 0.035), int(S * 0.965), int(S * 0.965)], outline=255, width=int(S * 0.035))
        A = np.asarray(im, np.float32) / 255
        T = np.asarray(txt, np.float32) / 255
        if style == "zhuwen":   # red characters and border, paper ground
            A = np.clip(T + np.asarray(border, np.float32) / 255, 0, 1) * A
        else:                   # baiwen: white characters carved out of a red block
            A = A * (1 - T)
        A = np.asarray(Image.fromarray((A * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS), np.float32) / 255
        sl = (slice(y0, y0 + size), slice(x0, x0 + size))
        tex = cv.tex[sl]
        imp = np.clip(0.75 + 0.6 * (noise_field(size, size, 2.0, int(rng.integers(1e6))) - 0.5) + 0.5 * (tex - 0.5), 0, 1)
        imp = imp * (rng.random((size, size)) > 0.04)
        K, S_ = pigment_from_hex(params.get("color", "#b8281e"), 0.7)
        cv.col[sl] = km_layer(cv.col[sl], K, S_, A * imp * 1.6)


class _Analyse:
    """The colour analysis of a tool (density, tint, ink kind) without stroke buffers, for washes."""

    def __init__(self, t, cv):
        t._begin(_Shim(cv))
        t.med._pending = None
        self.D, self.kink, self.tint = t.D, t.kink, t.tint


class _Shim:
    def __init__(self, cv):
        self.meta, self.clip, self.H, self.W = cv.meta, None, 1, 1
