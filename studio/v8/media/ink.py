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
- A stroke is laid into a stroke buffer (ink coverage and liquid). When it ends (the next stroke starts or
  the episode ends) its liquid ink spreads. On raw xuan the spread conserves volume: the liquid beyond what
  the paper under the stroke can hold flows out along the fibres until every wetted cell holds the paper's
  capacity, so a microlitre wets 0.39-0.49 cm2 by xuan type (Wu et al. 2016, measured drops); soot is
  filtered out on the way, so the halo is paler than the core and fades outward; strokes into still-damp
  paper fuse and spread further. Sized xuan, silk, bristol and laid paper hold the ink where it lands (a
  slight soft edge, a darker rim when wet).
- Physical scale: PX_PER_MM (4 px/mm: a 1200x1600 canvas is a 30 x 40 cm sheet); liquid in films of
  FILM_UM. Which parameters rest on data and which are by eye: docs/calibration/ink.md.
- Pens: a flexible steel nib (width swells with pressure and on down-strokes), a technical pen (even
  line), a reed pen (width set by direction); occasional blots at slow starts; a hatching tool.
State arrays: col (apparent colour), water (dampness 0..1), ink (carbon density laid), pencil (graphite
construction layer, erasable).
"""
import numpy as np, math, os, json
from scipy.ndimage import gaussian_filter, uniform_filter, zoom, distance_transform_edt
from PIL import Image, ImageDraw, ImageFont
from .base import Medium, hx, noise_field, pigment_from_hex, km_layer

# tone -> (optical density of the tip load, water in the brush)
TONES = {"jiao": (3.6, 0.32), "nong": (2.5, 0.52), "zhong": (1.3, 0.72), "dan": (0.55, 0.86), "qing": (0.2, 0.94)}
# ink kinds: relative absorption per channel (mean 1). Pine soot dilutes to a cool grey, oil soot is
# neutral, iron gall / sepia / bistre are the brown Western drawing inks.
INKS = {"pine": [1.02, 1.0, 0.95], "oil": [0.99, 1.0, 1.01], "carbon": [1.0, 1.0, 1.0],
        "iron_gall": [0.86, 1.0, 1.14], "sepia": [0.8, 0.98, 1.22], "bistre": [0.72, 0.97, 1.31],
        # measured: -ln(line core / paper) per linear RGB channel on the Met references (docs/calibration/
        # pen-and-ink-illustration.md, etching-engraving.md): India ink in the pen drawings (n = 10), intaglio black
        # (17 engravings and etchings) and the one "printed in dark brown ink" etching (n = 1)
        "india": [0.954, 1.0, 1.037], "intaglio_black": [0.973, 1.003, 1.015], "intaglio_brown": [0.826, 0.961, 1.213]}
# support -> tone, bleed (how far liquid ink spreads, 0..1), how fast water sinks in between episodes
SUP = {"xuan_raw": dict(tone="#f3eee2", bleed=1.0, keep=0.3),
       "xuan_sized": dict(tone="#efe8d6", bleed=0.22, keep=0.55),
       "silk": dict(tone="#e6d9bb", bleed=0.15, keep=0.55),
       "bristol": dict(tone="#fbfaf6", bleed=0.06, keep=0.45),
       "laid_paper": dict(tone="#efe6d2", bleed=0.3, keep=0.5),
       # pen-and-ink illustration and intaglio prints: tone = the median paper colour measured on the references
       # (as they look today); ppm = the support's default scale (a drawing for process at about 6 px/mm, a plate at 10)
       "illustration_board": dict(tone="#e7d9c5", bleed=0.04, keep=0.45, ppm=6.0),
       "plate_wove": dict(tone="#e4d8c6", bleed=0.0, keep=0.4, ppm=10.0),
       "plate_laid": dict(tone="#e4d8c6", bleed=0.0, keep=0.4, ppm=10.0)}
ALIAS = {"brush_chinese": "brush", "round": "brush", "filbert": "brush", "liner": "brush",
         "flat": "brush_side", "fan": "brush_side", "knife": "brush_side",
         "pen_nib": "pen", "pen_tech": "pen", "pen_reed": "pen", "wash_brush": "wash",
         "blend": "water", "smudge": "water", "dots": "brush",
         "crowquill": "nib", "mapping_pen": "nib", "pen_fine": "nib", "pen_stub": "nib", "graver": "burin",
         "etching_needle": "needle", "dry_point": "drypoint"}
NIB = {"pen_tech": "tech", "pen_reed": "reed", "crowquill": "crowquill", "mapping_pen": "mapping", "pen_fine": "fine", "pen_stub": "stub"}
LINE_KINDS = ("nib", "burin", "needle", "drypoint", "stipple")
STUDIO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- physical scale and liquid units (docs/calibration/ink.md)
# A canvas is a sheet at PX_PER_MM (cv.meta["px_per_mm"] overrides): 1200x1600 px = 30 x 40 cm.
PX_PER_MM = 4.0
# The liquid a tool lays (Wl) is a film on the paper: Wl = 1 is FILM_UM micrometres of ink, i.e.
# FILM_UM * 1e-3 / ppm^2 microlitres per pixel (2.8 nL per px at 4 px/mm). Estimate, not measured: about
# the diameter of a brush hair (wolf/goat hair 50-100 um), the film a fully wet tuft leaves when pressed.
FILM_UM = 45.0
# Raw xuan, Wu et al. 2016 [I1]: spread of a 50 uL ink drop (area per uL), contact angle 0.02 s after a 4 uL
# drop lands, fibre overlaps per mm (SEM). The paper holds 10/area nL per mm2 (um of liquid) once the ink
# has stopped spreading: capacity 20-26 um, against a ~100 um sheet of web density 360-460 kg/m3.
XUAN = {"qianlong": dict(area=24.5 / 50, contact=36.8, overlaps=77),
        "bamboo": dict(area=22.7 / 50, contact=50.1, overlaps=52),
        "jingpi": dict(area=19.6 / 50, contact=60.6, overlaps=40)}
XUAN_DEFAULT = "bamboo"
DRAIN = 18.0     # px of stroke per px of brush size until a hair runs dry (x load x thickness); set by flying white
RES_MIN = 16.0   # a fine line is drawn with the tip of a brush that holds more (reservoir ~ max(size, RES_MIN)^2); by eye
SPEED_DRY = 4.0  # how much brush speed opens flying white (x the core's speedfx); set by flying white
CLUMP = 0.08     # hair bundles in flying white, as a share of the tuft's hairs; by eye
PLATEAU = 0.55   # share of the half-width in the tip's full tone before the belly's paler ink; set by edge rise
RHYTHM = 0.3     # along-stroke swell and thinning of the brush (lifting and pressing); set by width CV
ROUGH = 0.45     # permeability noise of the fibre web on bamboo xuan (scaled by sqrt(52/overlaps)); by eye
FEATHER = 0.6    # how far the full-resolution front breaks along fibres; by eye
EVEN = 5         # free liquid evens out inside saturated paper over this many coarse cells per step; by eye
WICK_MM = 0.3    # fibre wicking fringe at every edge on raw xuan (bamboo); set by the hard-edge share
DAMP_FILL = 0.5  # share of the paper's capacity that damp from earlier strokes still fills (the rest has gone into
                 # the felt underlay or evaporated); by eye
# ---- pen-and-ink illustration and intaglio line tools (docs/calibration/pen-and-ink-illustration.md and
# etching-engraving.md). Widths in mm at the drawing's or plate's scale; "data" = set by a statistic measured on the
# Met references with tools/calibrate_media.py --kind line; "eye" = tuned by eye.
# Steel nibs: finest line, widest swell (mm), pressure exponent. The ranking (mapping pen widest range, crowquill
# fine but responsive, 303 "average" and more uniform, stub broad) is Maginnis 1898; the mm are set by the measured
# line width (median 0.39 mm, p90 / median 2.2) on the crowquill, the others scaled from it by eye.
NIBS = {"crowquill": (0.12, 0.62, 1.5), "mapping": (0.08, 0.72, 1.8), "fine": (0.24, 0.5, 1.2), "stub": (0.5, 0.85, 1.0)}
PEN_SMOOTH_MM = 0.35  # a practised pen line is fluent: the hand's jitter below this scale is smoothed out; eye
NIB_BLOTS = 0.03    # chance of a blot where a slow pen line starts (the core's default 0.12 is for the flexible pen); eye
NIB_DOWN = 0.6      # share of the swell an up- or side-stroke still gets (tines spread on the pull toward you); eye
PEN_RHYTHM = 0.18   # slow swell and thinning of the hand's pressure along a pen line; data (width CV along lines)
PEN_FLICK_MM = 1.2  # a fast pen line lifts off over this length (hatching flicks); data (free-end width ratio)
BURIN_W = 0.30      # widest burin line at full pressure, mm; data (engraving width median 0.23 mm, p90 / median 2.2)
BURIN_IN_MM, BURIN_OUT_MM = 1.6, 2.4   # the burin enters at a low angle and is lifted out: entry and exit tapers; data (ends, CV)
BURIN_SMOOTH_MM = 0.9   # the plate is turned against a steady push: no hand tremor below this scale; eye
NEEDLES = {"fine": 0.10, "medium": 0.16, "coarse": 0.24}   # needle diameters: sewing to embroidery needle (Lalanne); mm by eye
BITE_LAT = 0.0045   # lateral bite, mm per minute on each side (deeper lines are wider); data (etching width median and p90/median)
BITE_TAU = 8.0      # minutes for a line to hold 63% of the darkest ink (deeper holds more ink); eye, from Lalanne's 3-30 min test plate
BITE_DEFAULT = 10.0 # minutes a needle line is bitten when no stage is given; eye
TREMOR_MM = 0.035   # an etching needle's slight tremble across the line; eye
DRY_BURR = 0.9      # density of the burr's velvety ink beside a drypoint furrow, relative to a deep line; eye
SOOT_STEPS = 30  # soot filtered out of the liquid moving through wet paper: 1/e per SOOT_STEPS front steps; by eye


def _sh(a, dy, dx):
    """b[y, x] = a[y + dy, x + dx], zero outside (a neighbour's value)."""
    b = np.zeros_like(a)
    H, W = a.shape
    b[max(0, -dy):H - max(0, dy), max(0, -dx):W - max(0, dx)] = a[max(0, dy):H - max(0, -dy), max(0, dx):W - max(0, -dx)]
    return b


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
        self.nib = it.get("nib", nib or ("crowquill" if kind == "nib" else "flex"))
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
        # which hairs separate first: drying hairs cling together in bundles (CLUMP hairs across)
        from scipy.ndimage import gaussian_filter1d
        bn = gaussian_filter1d(rng.random(K), max(0.5, K * CLUMP), mode="wrap")
        self.bn = ((np.argsort(np.argsort(bn)) + 0.5) / K).astype(np.float32)
        self.brate = np.clip(1 + 0.3 * (self.bn - 0.5) / 0.29 + rng.normal(0, 0.1, K), 0.45, 1.8).astype(np.float32)
        self.walk = 0.75
        self.blot = float(it.get("blots", 0.12))
        sz = max(self.size, 2.0)
        self.rh = (2 * math.pi / (max(sz, 12) * rng.uniform(5, 10)), rng.uniform(0, 6.283))

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
        if k in ("pen", "hatch", "nib", "stipple"):
            self.water = float(it.get("water", 0.32))
        if k in ("burin", "needle", "drypoint"):
            self.water = 0.0      # printing ink pressed from a plate: no liquid on the paper
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
        if k in LINE_KINDS:
            # line tools are laid whole when the stroke ends, so the width can follow the full stroke (entry, swell, exit)
            self.pts.append((x, y, ang, press, float(getattr(self, "speedfx", 0.0))))
            self.ndab += 1
            return
        if k in ("brush", "brush_side") and RHYTHM > 0:
            a = self.acc_arc = getattr(self, "acc_arc", 0.0) + st
            ph = self.rh
            rscale = rscale * (1 + RHYTHM * math.sin(a * ph[0] + ph[1]))
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
        # pressing squeezes ink from the belly into the tip; speed lets hairs skip (closing again as the
        # brush slows), so fast strokes open streaks in their middle, dry brushes at their tail
        sp = 0.45 * math.tanh(float(getattr(self, "speedfx", 0.0)) * SPEED_DRY / 0.45)   # saturates: a fast brush still marks
        eff = wetb + 0.3 * float(np.clip(press - 0.7, 0, 0.4)) - sp - dry_bias
        thr = np.clip((0.46 - eff) / 0.46, 0, 1.15) + max(0.0, 0.22 - press) * 2.0
        g = (1 - patch) * (0.3 * cv.tex[sl] + 0.7 * self.bn[bi]) + patch * self.med.fields(cv)[1][sl]
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
        rr = np.sqrt((u / ru) ** 2 + (v / r) ** 2)
        # the tuft's edge is the ends of its hairs: sharp (about one pixel), ragged hair by hair
        m = np.clip((np.sqrt(self.blen[bi]) - rr) * r + 0.5, 0, 1)
        p = np.clip(np.abs(t) * min(c, 1.0), 0, 1)
        # tone across the stroke: the dark tip's ink fills the middle, the pale belly shows only at the margins
        z = np.clip((p - PLATEAU) / (1.05 - PLATEAU), 0, 1)
        conc = 1 - (1 - self.belly) * z * z * (3 - 2 * z)
        wetb = self.wb[bi]
        conc = conc * (1 - (0.06 + 0.3 * np.clip(1 - wetb, 0, 1)) * self.bn[bi])   # hair streaks
        m = m * self._gate(cv, sl, bi, wetb, press)
        self._lay(sl, m, conc * (0.8 + 0.2 * np.minimum(1, wetb * 1.6)), self.water * np.minimum(1, wetb * 1.5) * self._dwell(st))
        touch = np.abs(self.bpos) <= min(c, 1.0) + 0.06
        self.wb -= dist * self.brate * touch * (0.35 + 0.65 * min(press, 1.0)) / (max(self.size, RES_MIN) ** 2 / max(self.size, 2) * DRAIN * self.thick)
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
        m = m * self._gate(cv, sl, bi, wetb, press, dry_bias=0.2 * pp, patch=0.45)
        self._lay(sl, m, conc * (0.8 + 0.2 * np.minimum(1, wetb * 1.6)), self.water * np.minimum(1, wetb * 1.5) * self._dwell(st))
        self.wb -= dist * self.brate * (0.4 + 0.6 * min(press, 1.0)) / (max(self.size, RES_MIN) ** 2 / max(self.size, 2) * DRAIN * 0.7 * self.thick)
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
    arrays = ("col", "water", "ink", "pencil", "etch", "bite")
    supports = {"xuan_raw": "raw (unsized) xuan rice paper: absorbent, wet ink bleeds and feathers along the fibres; no correcting",
                "xuan_sized": "sized ('cooked') xuan: ink sits where it lands, crisp lines (gongbi)",
                "silk": "sized silk, warm tone, fine weave, very little bleed",
                "bristol": "smooth hard drawing board for pen and ink; no bleed",
                "laid_paper": "laid paper with laid and chain lines; slight bleed, a little grit for pen",
                "illustration_board": "Bristol board for pen drawing for process reproduction: smooth, hard, no bleed (6 px/mm by default)",
                "plate_wove": "dampened wove printing paper under an intaglio plate: soft, even (10 px/mm by default)",
                "plate_laid": "dampened laid printing paper under an intaglio plate: laid and chain lines (10 px/mm by default)"}
    tools = {"brush": "Chinese brush, upright (centre tip): dark tip, wet pale belly; width swells with pressure; flying white when dry or fast",
             "brush_side": "side brush (oblique): broad stroke, sharp dark edge on the tip side, ragged pale edge on the belly side, much flying white",
             "splash": "splashed ink (pomo): wet irregular pools of varying tone that fuse and bleed, a few droplets",
             "wash": "soft wash brush: even, wet, diluted ink (or light colour) over an area",
             "pen": "dip pen: flexible steel nib, line swells with pressure and on down-strokes; occasional blot at a slow start (nib: flex|tech|reed)",
             "hatch": "pen hatching: each stroke lays a band of parallel pen lines across its path (cross-hatched when pressed hard or cross: true)",
             "water": "clean wet brush: fuses and softens ink that is still damp (also used for 'blend')",
             "pencil": "light graphite construction line, removed later by finish erase-pencil",
             "nib": "steel drawing nib for pen-and-ink illustration (nib: crowquill|mapping|fine|stub): hairline to swell with pressure and on down-strokes, fast lines lift off to a point",
             "stipple": "pen stippling: dots along the stroke (dot_spacing_mm), for tone",
             "burin": "engraver's burin: a steady, smooth cut that enters as a point, swells with the push and tapers out; tapers print greyer",
             "needle": "etching needle through the ground: even width, round ends, a slight tremble; bitten for `bite` minutes (deeper = wider and darker)",
             "drypoint": "drypoint needle on the bare plate: a fine furrow with a velvety, ragged burr to one side (burr_side left|right)"}
    finishes = {"dots": "the last dark accents: dots in scorched ink with a small upright brush (pts or region+count, at most 40)",
                "seal": "stamp the red cinnabar seal (text, at br|bl|tr|tl|[x,y], size, style baiwen|zhuwen)",
                "erase-pencil": "erase the graphite construction lines wherever ink does not cover them",
                "scrape": "scrape ink off for a highlight (region, amount 0..1); leaves the paper slightly roughened",
                "mount": "presentation: show the work mounted (style scroll|album|mat, color) in renders; the paint is unchanged",
                "bite": "etching: another biting stage for the needle lines inside region (the rest is stopped out): minutes (default 10)",
                "lozenge": "dot-and-lozenge: a burin dot in each paper lozenge between crossed lines (region, level, size)",
                "wipe": "printing: plate tone left by wiping (tone, clean_lights, retroussage 0..1, angle), inside the platemark",
                "platemark": "printing: the plate's edge pressed into the paper (margin 0..0.3 of the short side, margin_mm, or rect); the margin takes no ink"}

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
        if support == "plate_laid":
            # laid lines about 1 mm apart, chain lines 24 mm (as laid_paper), at the plate's 10 px/mm; dampened and pressed: soft
            y, x = np.mgrid[0:h, 0:w].astype(np.float32)
            laid = 0.5 + 0.5 * np.sin(y * 2 * math.pi / 10.5)
            chain = 0.5 * np.exp(-((x % 240) - 120) ** 2 / 30.0)
            return _norm(0.25 * laid + 0.12 * chain + 0.33 * noise_field(h, w, 1.2, 5) + 0.3 * noise_field(h, w, 14, 3))
        if support == "plate_wove":
            return _norm(0.5 * noise_field(h, w, 1.0, 5) + 0.3 * noise_field(h, w, 4, 9) + 0.2 * noise_field(h, w, 16, 3))
        # bristol, illustration board: smooth
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
        if kind == "pen" and it.get("nib") in NIBS:
            kind = "nib"
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
        if t.kind in LINE_KINDS:
            if t.pts:
                self._line(t)
            if t.kind not in ("nib", "stipple") and t.bb is not None:
                # printed from a plate: the ink sits where the plate held it, no liquid spreads
                x0, y0, x1, y1 = t.bb
                sl = (slice(y0, y1), slice(x0, x1))
                total = t.X[sl]
                if t.kind == "needle":
                    total = self._etch_stroke(cv, sl, total, t)
                self._composite(cv, sl, total, t.D, t.kink, t.tint)
                return
        if t.bb is None:
            return
        sp = self.sup(cv)
        bleed = sp["bleed"]
        x0, y0, x1, y1 = t.bb
        wl = min(1.4, t.wmax)
        if t.kind in ("brush", "brush_side", "wash", "splash", "pen", "hatch", "nib", "stipple"):
            if bleed >= 0.5:
                # the halo can reach at most as far as the excess liquid would cover as a disc
                b0 = (slice(y0, y1), slice(x0, x1))
                ex = float(np.maximum(t.Wl[b0] / self.capacity(cv) + cv.water[b0] * DAMP_FILL - 1, 0).sum())
                pad = int(6 + 1.15 * math.sqrt(ex / math.pi))
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
    def xuan(self, cv):
        return XUAN.get(cv.meta.get("xuan", XUAN_DEFAULT), XUAN[XUAN_DEFAULT])

    def ppm(self, cv):
        return float(cv.meta.get("px_per_mm", self.sup(cv).get("ppm", PX_PER_MM)))

    def capacity(self, cv):
        """Raw xuan's capacity, in units of the laid liquid Wl: 10/area um of ink per mm2 (Wu et al. 2016)."""
        return 10.0 / self.xuan(cv)["area"] / FILM_UM

    def _bleed_raw(self, cv, sl, X, Wl, t, bleed):
        """Raw xuan: the liquid beyond what the paper under the stroke can hold flows out along the fibres
        until every wetted cell holds the paper's capacity, so the wetted area is the volume over the
        capacity: 0.39-0.49 cm2 per uL by xuan type (Wu et al. 2016). The free liquid evens out inside the
        saturated paper and is pushed into the dry cells at its edge, faster where the fibre network is
        dense (permeability noise, smoother on papers with more fibre overlaps). Soot is carried with the
        liquid but fibres hold some of it back, so the halo is paler than the core and fades outward."""
        h, w = X.shape
        C = self.capacity(cv)
        xt = self.xuan(cv)
        damp = cv.water[sl]
        liq = Wl / C
        # coarse grid: fine enough for the stroke, coarse enough that the halo is reached in ~40 steps
        reach = math.sqrt(float(np.maximum(liq + damp * DAMP_FILL - 1, 0).sum()) / math.pi)
        f = int(max(2 if h * w < 300_000 else (3 if h * w < 1_200_000 else 4), min(8, math.ceil(reach / 40))))
        H2, W2 = -(-h // f), -(-w // f)
        P = lambda a: np.pad(a, ((0, H2 * f - h), (0, W2 * f - w)), mode="edge").reshape(H2, f, W2, f).mean((1, 3))

        def U(a):
            u = zoom(a, f, order=1)[:h, :w]
            return np.pad(u, ((0, h - u.shape[0]), (0, w - u.shape[1])), mode="edge") if u.shape != (h, w) else u
        Lc, d0 = P(liq), P(damp) * DAMP_FILL
        s = np.minimum(Lc + d0, 1.0)
        e = (Lc + d0 - s).astype(np.float32)
        mob = np.clip(e / (Lc + 1e-6), 0, 1)
        # soot in the excess liquid moves; the rest stays where the brush laid it (full resolution)
        mob_full = np.clip(U(mob), 0, 1)
        st0 = X * (1 - mob_full)
        # the part that stays keeps a crisp edge where the brush was nearly dry, a soft one where it was wet
        stay = (1 - mob_full) * gaussian_filter(st0, 0.45) + mob_full * gaussian_filter(st0, 0.6 + 0.5 * f)
        qf = (P(X) * mob).astype(np.float32)
        qd = np.zeros_like(qf)
        fibf, pinf = self.fields(cv)
        fib = fibf[sl]
        rough = ROUGH * math.sqrt(52.0 / xt["overlaps"])
        perm = np.clip(1 + rough * 2 * (P(fib) - 0.5) + 0.5 * rough * 2 * (P(pinf[sl]) - 0.5), 0.08, None).astype(np.float32)
        mine = (Lc > 0.01).astype(np.float32)       # cells holding this stroke's liquid
        e0 = float(e.sum())
        filt = 1 - math.exp(-1.0 / SOOT_STEPS)
        it = 0
        while e0 > 1e-3 and it < 48 and float(e.sum()) > 0.02 * e0:
            it += 1
            # the free liquid evens out inside the saturated paper (and its soot with it)
            sat = (s > 0.995) * mine
            Gs = uniform_filter(sat, EVEN) + 1e-6
            for a in (e, qf):
                tot = float(a.sum())
                b = sat * uniform_filter(a * sat, EVEN) / Gs + a * (1 - sat)
                a[...] = b * (tot / max(float(b.sum()), 1e-9))
            # ... and is pushed into neighbouring cells that still have room
            room = 1 - s
            op = perm * (room > 1e-3)
            opn = [_sh(op, 0, 1), _sh(op, 0, -1), _sh(op, 1, 0), _sh(op, -1, 0)]   # right, left, down, up
            norm = opn[0] + opn[1] + opn[2] + opn[3] + 1e-6
            give = e * (norm > 1e-3) / norm
            o = [give * k for k in opn]          # wanted outflow to each neighbour
            inc = _sh(o[0], 0, -1) + _sh(o[1], 0, 1) + _sh(o[2], -1, 0) + _sh(o[3], 1, 0)
            acc = np.where(inc > room, room / (inc + 1e-9), 1.0).astype(np.float32)
            T = [o[0] * _sh(acc, 0, 1), o[1] * _sh(acc, 0, -1), o[2] * _sh(acc, 1, 0), o[3] * _sh(acc, -1, 0)]
            out = T[0] + T[1] + T[2] + T[3]
            conc = qf / (e + 1e-6)
            e -= out
            np.maximum(e, 0, out=e)
            qf -= out * conc
            Tin = _sh(T[0], 0, -1) + _sh(T[1], 0, 1) + _sh(T[2], -1, 0) + _sh(T[3], 1, 0)
            ct = [k * conc for k in T]
            cin = _sh(ct[0], 0, -1) + _sh(ct[1], 0, 1) + _sh(ct[2], -1, 0) + _sh(ct[3], 1, 0)
            s += Tin
            mine = np.maximum(mine, (Tin > 1e-4).astype(np.float32))
            qd += cin                              # liquid soaking into dry paper leaves its soot there
            np.maximum(qf, 0, out=qf)
            # the fibres filter soot out of the liquid moving through saturated paper, so the liquid
            # that reaches the front late is paler: the halo fades outward
            dq = qf * sat * filt
            qd += dq
            qf -= dq
        E = float(e.sum())
        if E > 1e-3:
            # what is still free when the steps run out (a large pool) wets the nearest dry cells, so the
            # wetted area keeps to volume / capacity
            dist = distance_transform_edt(s < 0.995) / perm
            room = (1 - s).ravel()
            order = np.argsort(np.where(room > 1e-3, dist.ravel(), np.inf), kind="stable")
            cum = np.cumsum(room[order])
            k = int(np.searchsorted(cum, E)) + 1
            idx = order[:k]
            add = np.zeros(s.size, np.float32)
            add[idx] = room[idx]
            add[idx[-1]] -= max(0.0, float(cum[min(k, cum.size) - 1]) - E)
            add = add.reshape(s.shape)
            s += add
            cfree = float(qf.sum()) * 0.5
            qd += add * (cfree / max(float(add.sum()), 1e-9))
            qf *= 0.5
            e[:] = 0
        qd += qf                                   # what is still free settles where it is
        s_up = np.clip(U(s), 0, 1)
        # the front at full resolution: the wetted edge breaks along the fibres
        laid = np.clip(Wl * 6, 0, 1)
        thr = 0.5 + FEATHER * rough * (gaussian_filter(fib, 0.6) - 0.5)
        front = np.maximum(np.clip((s_up - thr) * 5 + 0.5, 0, 1), laid)
        halo = U(qd) * front
        inside = np.clip(Wl * 4, 0, 1)            # fibre texture shows in the fringe, not inside the stroke
        halo = halo * (1 + (1 - inside) * (0.3 * gaussian_filter(fib, 0.6) - 0.15))
        total = stay + halo
        # capillary wicking along the fibres that cross the stroke's edge, even where no liquid is left to
        # spread: a fringe whose length scales as sqrt(cos(contact angle)) (Washburn), so it is longest on
        # Qianlong xuan (36.8 deg) and shortest on Jingpi (60.6 deg); WICK_MM itself is by eye
        lw = WICK_MM * self.ppm(cv) * math.sqrt(math.cos(math.radians(xt["contact"])) / math.cos(math.radians(XUAN["bamboo"]["contact"])))
        if lw > 0.2:
            fr = gaussian_filter(total, lw) * (0.55 + 0.9 * gaussian_filter(fib, 0.5))
            total = np.maximum(total, fr * 0.85)
        self._last_bleed = dict(C=C, iters=it, wet_px=float((s_up * front > 0.5).sum()), vol=float(liq.sum() * C), e_left=float(e.sum()) / max(e0, 1e-9))
        return total, np.clip(s_up * front, 0, 1)

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


    # ------------------------------------------------------------------ line tools: nib, burin, needle, drypoint, stipple
    def _line(self, t):
        """Lay a whole pen or plate line from the recorded path: resampled at 0.5 px, smoothed at the tool's scale (a
        burin cannot tremble, a needle trembles a little), then filled as a strip of quads whose width and ink follow
        the tool's profile along the stroke. Supersampled 4x for clean anti-aliased edges."""
        from scipy.ndimage import gaussian_filter1d
        cv, k, it, rng = t.cv, t.kind, t.it, t.rng
        ppm = self.ppm(cv)
        P = np.asarray(t.pts, np.float64)
        if len(P) == 1:
            P = np.vstack([P, P + [0.6, 0, 0, 0, 0]])
        xy = P[:, :2]
        d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))])
        S = float(d[-1])
        if S < 0.5:
            xy = xy[[0, -1]] + np.array([[0, 0], [0.6, 0]]); d = np.array([0, 0.6]); S = 0.6; P = P[[0, -1]]
        n = max(3, int(S / 0.5) + 1)
        sa = np.linspace(0, S, n)
        x, y = np.interp(sa, d, xy[:, 0]), np.interp(sa, d, xy[:, 1])
        pr, spd = np.interp(sa, d, P[:, 3]), np.interp(sa, d, P[:, 4])
        sm = {"burin": BURIN_SMOOTH_MM, "needle": 0.2, "drypoint": 0.15}.get(k, PEN_SMOOTH_MM) * ppm / 0.5
        sm = min(sm, n / 6)
        if sm > 0.3:
            x0, y0, x1, y1 = x[0], y[0], x[-1], y[-1]
            x, y = gaussian_filter1d(x, sm, mode="nearest"), gaussian_filter1d(y, sm, mode="nearest")
            # keep the ends where the hand put them (smoothing pulls them in)
            ramp = np.clip(1 - sa / max(3 * sm * 0.5, 1e-6), 0, 1); x += (x0 - x[0]) * ramp; y += (y0 - y[0]) * ramp
            ramp = np.clip(1 - (S - sa) / max(3 * sm * 0.5, 1e-6), 0, 1); x += (x1 - x[-1]) * ramp; y += (y1 - y[-1]) * ramp
        tx, ty = np.gradient(x), np.gradient(y)
        tn = np.hypot(tx, ty) + 1e-9
        tx, ty = tx / tn, ty / tn
        nx, ny = -ty, tx
        smm = sa / ppm                      # arc length in mm
        Smm = S / ppm
        scale = float(np.clip(t.size / 8.0, 0.5, 2.0)) ** 0.5 * float(it.get("width_scale", 1.0))

        def noise1(corr_mm, seed):
            m = max(4, int(Smm / max(corr_mm, 1e-3) * 4) + 4)
            v = gaussian_filter1d(rng.normal(0, 1, m), 2.0)
            v = v / (v.std() + 1e-9)
            return np.interp(smm / max(Smm, 1e-6) * (m - 1), np.arange(m), v)
        conc = np.ones(n)
        caps = False
        if k == "nib" or k == "stipple":
            wmin, wmax, g = NIBS.get(t.nib, NIBS["crowquill"])
            down = np.clip(ty, 0, 1)                          # moving toward the drawer spreads the tines
            w = wmin + (wmax - wmin) * np.clip(pr, 0, 1.2) ** g * (NIB_DOWN + (1 - NIB_DOWN) * down)
            w = w * scale * np.clip(1 + PEN_RHYTHM * noise1(3.0, 1), 0.4, 1.8)
            # a fast stroke lifts off: the line thins to a point over the last PEN_FLICK_MM (more with speed)
            fl = PEN_FLICK_MM * (0.4 + 2.5 * float(np.clip(spd[-max(1, n // 5):].mean(), 0, 0.4)))
            w = w * np.clip((Smm - smm) / max(fl, 1e-3), 0.15, 1) ** 0.8
            w = w * np.clip(smm / 0.15 + 0.6, 0, 1)          # the nib lands: a short rounding in
            caps = True
            if k == "stipple":
                return self._stipple(t, x, y, smm, w * ppm, ppm)
        elif k == "burin":
            wmax = BURIN_W * float(it.get("pressure_width", 1.0)) * scale
            ein, eout = min(BURIN_IN_MM, 0.3 * Smm), min(BURIN_OUT_MM, 0.4 * Smm)
            a = np.clip(smm / max(ein, 1e-3), 0, 1); b = np.clip((Smm - smm) / max(eout, 1e-3), 0, 1)
            env = (a * a * (3 - 2 * a)) * (b * b * (3 - 2 * b))
            pn = np.clip(pr / max(float(np.percentile(pr, 90)), 1e-3), 0, 1.2)
            w = wmax * (0.04 + 0.96 * env) * pn ** 0.5 * np.clip(1 + 0.06 * noise1(4.0, 2), 0.8, 1.2)
            conc = 0.5 + 0.5 * np.clip(w / wmax, 0, 1)         # a shallow cut holds less ink: greyer at the tapers
        elif k == "needle":
            wn = NEEDLES.get(it.get("needle", "medium"), NEEDLES["medium"]) * scale
            w = np.full(n, wn) * np.clip(1 + 0.05 * noise1(2.0, 3), 0.85, 1.15)
            trem = TREMOR_MM * (1 + 2.0 * float(np.clip(spd.mean(), 0, 0.5))) * noise1(0.8, 4) * ppm
            x, y = x + nx * trem, y + ny * trem
            caps = True
        elif k == "drypoint":
            w = 0.07 * (0.6 + 0.8 * np.clip(pr, 0, 1.2)) * scale * np.ones(n)
            conc = 0.7 * np.ones(n)
            caps = True
        wpx = np.maximum(w * ppm, 0.35)
        self._strip(t, x, y, nx, ny, wpx, conc, caps)
        if k == "drypoint":
            # the burr: metal thrown up beside the furrow (to one side, as the needle leans) holds a velvety film
            side = 1.0 if it.get("burr_side", "right") == "right" else -1.0
            bw = (0.12 + 0.18 * np.clip(pr, 0, 1.2)) * scale * ppm
            rag = np.clip(1 + 0.45 * noise1(0.5, 5), 0.2, 1.6)
            off = side * (wpx / 2 + bw * 0.45)
            Xs = np.zeros_like(t.X)
            t2 = _Buf(Xs, t.clip)
            self._strip(t2, x + nx * off, y + ny * off, nx, ny, bw * rag, DRY_BURR * np.clip(pr, 0.3, 1.0), True)
            if t2.bb:
                bx0, by0, bx1, by1 = t2.bb
                pad = int(2 + 0.08 * ppm * 3)
                sl = (slice(max(0, by0 - pad), by1 + pad), slice(max(0, bx0 - pad), bx1 + pad))
                soft = gaussian_filter(Xs[sl], max(0.5, 0.06 * ppm)) * (0.7 + 0.6 * cv.tex[sl])
                np.maximum(t.X[sl], soft, out=t.X[sl])
                t._bbx(sl[1].start, sl[0].start, min(cv.W, sl[1].stop), min(cv.H, sl[0].stop))
        if k == "nib" and t.rng.random() < float(it.get("blots", NIB_BLOTS)) * float(np.clip(1 - 3 * spd[:3].mean(), 0, 1)):
            r = wpx[:4].max() * t.rng.uniform(0.6, 1.0)
            self._strip(t, x[:2] + np.array([0, 0.3]), y[:2], nx[:2], ny[:2], np.array([2 * r, 2 * r]), np.ones(2), True)

    def _strip(self, t, x, y, nx, ny, wpx, conc, caps):
        """Fill a strip of quads (width wpx along the centre line) with conc into t.X (and liquid into t.Wl)."""
        cv = getattr(t, "cv", None)
        H, W = t.X.shape
        R = float(wpx.max()) / 2 + 2
        bx0, bx1 = max(0, int(x.min() - R)), min(W, int(x.max() + R) + 2)
        by0, by1 = max(0, int(y.min() - R)), min(H, int(y.max() + R) + 2)
        if bx0 >= bx1 or by0 >= by1:
            return
        SS = 4
        im = Image.new("L", ((bx1 - bx0) * SS, (by1 - by0) * SS), 0)
        dr = ImageDraw.Draw(im)
        hw = wpx / 2
        lx, ly = (x + nx * hw - bx0) * SS, (y + ny * hw - by0) * SS
        rx, ry = (x - nx * hw - bx0) * SS, (y - ny * hw - by0) * SS
        cv8 = np.clip(conc * 255, 0, 255).astype(int)
        step = 2 if len(x) > 6 else 1
        idx = list(range(0, len(x) - 1, step)) + [len(x) - 1]
        for a, b in zip(idx[:-1], idx[1:]):
            dr.polygon([(lx[a], ly[a]), (lx[b], ly[b]), (rx[b], ry[b]), (rx[a], ry[a])], fill=int(max(cv8[a], cv8[b])))
        if caps:
            for j in (0, len(x) - 1):
                r = hw[j] * SS
                cx, cy = (x[j] - bx0) * SS, (y[j] - by0) * SS
                dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=int(cv8[j]))
        m = np.asarray(im, np.float32).reshape(by1 - by0, SS, bx1 - bx0, SS).mean((1, 3)) / 255
        sl = (slice(by0, by1), slice(bx0, bx1))
        if t.clip is not None:
            m = m * t.clip[sl]
        np.maximum(t.X[sl], m, out=t.X[sl])
        if getattr(t, "Wl", None) is not None and getattr(t, "water", 0) > 0:
            np.maximum(t.Wl[sl], (m > 0.02) * t.water, out=t.Wl[sl])
            t.wmax = max(t.wmax, t.water)
        t._bbx(bx0, by0, bx1, by1)

    def _stipple(self, t, x, y, smm, wpx, ppm):
        """Pen stippling: dots along the path, spaced about two and a half dot widths, a little scattered."""
        rng = t.rng
        sp = float(t.it.get("dot_spacing_mm", 2.5 * np.median(wpx) / ppm))
        s = rng.uniform(0, sp)
        while s < smm[-1] + 1e-6:
            j = int(np.clip(np.searchsorted(smm, s), 0, len(x) - 1))
            r = max(0.45, wpx[j] / 2 * rng.uniform(0.8, 1.25))
            cx, cy = x[j] + rng.normal(0, r * 0.8), y[j] + rng.normal(0, r * 0.8)
            self._strip(t, np.array([cx, cx + 0.3]), np.array([cy, cy]), np.zeros(2), np.ones(2), np.array([2 * r, 2 * r]), np.ones(2), True)
            s += sp * rng.uniform(0.8, 1.2)

    # ------------------------------------------------------------------ etching: biting in stages
    def _bite_profile(self, cv, etch, bite):
        """Printed density of etched lines (0..1 of the ink's full density) from the needle's opening (etch) and the
        minutes each line was bitten (bite): deeper lines hold more ink (1 - exp(-minutes / BITE_TAU)) and are wider,
        BITE_LAT mm per minute on each side (Met, Etching: "longer exposure will cause deeper and wider recesses",
        which "hold more ink and will thus print darker lines")."""
        ppm = self.ppm(cv)
        out = np.zeros_like(etch)
        q_ = np.round(bite * 2) / 2
        for tv in np.unique(q_[(etch > 0.05) & (q_ > 0)]):
            m = etch * (q_ == tv)
            if m.max() <= 0.05:
                continue
            r = BITE_LAT * tv * ppm
            if r > 0.05:
                dist = distance_transform_edt(m < 0.5)
                m = np.maximum(m, np.clip(r + 0.5 - dist, 0, 1) * (dist < r + 1.5))
            np.maximum(out, m * (1 - math.exp(-tv / BITE_TAU)), out=out)
        return out

    def _etch_stroke(self, cv, sl, X, t):
        """A needle line through the ground, bitten for its `bite` minutes (default BITE_DEFAULT): store the opening
        and the bite so later `finish bite` stages can deepen it, and return what this line prints."""
        mins = float(t.it.get("bite", BITE_DEFAULT))
        H, W = X.shape
        pad = int(BITE_LAT * 60 * self.ppm(cv)) + 3
        y0, x0 = max(0, sl[0].start - pad), max(0, sl[1].start - pad)
        y1, x1 = min(cv.H, sl[0].stop + pad), min(cv.W, sl[1].stop + pad)
        big = (slice(y0, y1), slice(x0, x1))
        Xb = np.zeros((y1 - y0, x1 - x0), np.float32)
        Xb[sl[0].start - y0:sl[0].start - y0 + H, sl[1].start - x0:sl[1].start - x0 + W] = X
        old = self._bite_profile(cv, cv.etch[big], cv.bite[big])
        cv.etch[big] = np.maximum(cv.etch[big], Xb)
        cv.bite[big] = np.where(Xb > 0.5, np.maximum(cv.bite[big], mins), cv.bite[big])
        new = self._bite_profile(cv, cv.etch[big], cv.bite[big])
        cv.meta["etch_D"], cv.meta["etch_ink"] = float(t.D), t.it.get("ink", "intaglio_black")
        out = np.clip(new - old, 0, None)
        self._composite(cv, big, out, t.D, t.kink, t.tint)
        return np.zeros_like(X)       # already composited (on the padded window)

    def _bite(self, cv, params):
        """A further biting stage: every needle line inside `region` (the parts not stopped out) bites `minutes` more."""
        if not (cv.etch > 0.05).any():
            print("bite: no needle lines on the plate yet")
            return
        mins = float(params.get("minutes", 10))
        reg = region(params.get("region"), cv.W, cv.H, 1.0) if params.get("region") else np.ones((cv.H, cv.W), np.float32)
        ys, xs = np.nonzero(cv.etch > 0.05)
        pad = int(BITE_LAT * (cv.bite.max() + mins + 5) * self.ppm(cv)) + 3
        sl = (slice(max(0, ys.min() - pad), min(cv.H, ys.max() + pad + 1)), slice(max(0, xs.min() - pad), min(cv.W, xs.max() + pad + 1)))
        old = self._bite_profile(cv, cv.etch[sl], cv.bite[sl])
        cv.bite[sl] = cv.bite[sl] + mins * (reg[sl] > 0.5) * (cv.etch[sl] > 0.05)
        new = self._bite_profile(cv, cv.etch[sl], cv.bite[sl])
        kink = np.asarray(INKS.get(cv.meta.get("etch_ink", "intaglio_black"), INKS["intaglio_black"]), np.float32)
        self._composite(cv, sl, np.clip(new - old, 0, None), float(cv.meta.get("etch_D", 3.6)), kink / kink.mean(), None)

    # ------------------------------------------------------------------ printing: plate tone, platemark, lozenge dots
    def plate_rect(self, cv):
        r = cv.meta.get("platemark")
        return (0, 0, cv.W, cv.H) if not r else tuple(int(v) for v in r)

    def _wipe(self, cv, params):
        """Plate tone: the thin film of ink the printer leaves on the plate's surface when wiping (Met: "leave a thin
        layer of ink on the plate to create tone"), streaked by the hand and wiped cleaner in the lights; retroussage
        draws ink out of the lines with a soft rag and spreads it along their edges (Lalanne, §89)."""
        x0, y0, x1, y1 = self.plate_rect(cv)
        sl = (slice(y0, y1), slice(x0, x1))
        h, w = y1 - y0, x1 - x0
        tone = float(params.get("tone", 0.05))
        rng = np.random.default_rng(int(params.get("seed", 3)))
        a = math.radians(params.get("angle", rng.uniform(0, 180)))
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        u = (xx * math.cos(a) + yy * math.sin(a))
        streak = 0.5 + 0.5 * np.sin(u / max(6.0, 0.0015 * (h + w) * 8) + 3 * noise_field(h, w, 25, 7))
        film = 0.55 + 0.25 * noise_field(h, w, max(8, (h + w) / 30), 5) + 0.2 * streak
        lines = gaussian_filter(np.clip(cv.ink[sl] / 2.0, 0, 1), max(2.0, (h + w) / 120))
        clean = float(params.get("clean_lights", 0.6))
        film = film * (1 - clean + clean * np.clip(lines * 3, 0, 1))
        total = tone * film
        rt = float(params.get("retroussage", 0.0))
        if rt > 0:
            total = total + rt * 0.5 * gaussian_filter(np.clip(cv.ink[sl] / 3.0, 0, 1), max(0.8, 0.15 * self.ppm(cv)))
        kink = np.asarray(INKS.get(cv.meta.get("etch_ink", params.get("ink", "intaglio_black")), INKS["intaglio_black"]), np.float32)
        self._composite(cv, sl, total, float(cv.meta.get("etch_D", 3.6)), kink / kink.mean(), None)

    def _platemark(self, cv, params):
        """The plate's outline pressed into the dampened paper (Met: "an outline of the outer edges of the metal plate
        in the paper"). The margin outside it takes no ink: it is wiped back to paper here."""
        ppm = self.ppm(cv)
        if params.get("rect"):
            x0, y0, w, h = (int(v) for v in params["rect"])
        else:
            mg = int(params.get("margin_mm", 0) * ppm) or int(min(cv.W, cv.H) * float(params.get("margin", 0.08)))
            x0, y0, w, h = mg, mg, cv.W - 2 * mg, cv.H - 2 * mg
        x1, y1 = x0 + w, y0 + h
        out = np.ones((cv.H, cv.W), bool); out[y0:y1, x0:x1] = False
        paper = self.paper(cv)
        n = (cv.tex - 0.5) * 0.012
        cv.col[out] = np.clip(paper[None, :] * (1 + n[out][:, None]), 0, 1)
        cv.ink[out] = 0
        cv.meta["platemark"] = [x0, y0, x1, y1]
        cv.meta["platemark_bevel"] = float(params.get("bevel_mm", 0.5))

    def _lozenge(self, cv, params):
        """Dot-and-lozenge: a dot cut into the paper-white lozenges left between crossed burin lines, to carry the tone
        through them (Prints and Principles, "Dotted Lozenge"). Lozenges are found in the canvas itself: enclosed
        paper cells of lozenge size inside the region (and, with a schema, darker there than `level`)."""
        from scipy.ndimage import label, find_objects
        ppm = self.ppm(cv)
        reg = region(params.get("region"), cv.W, cv.H, 1.0) if params.get("region") else np.ones((cv.H, cv.W), np.float32)
        ink = cv.ink > float(params.get("line_density", 0.8))
        cells, n = label(~ink & (reg > 0.5))
        amin, amax = (0.12 * ppm) ** 2, (1.3 * ppm) ** 2
        level = float(params.get("level", 0.65))
        val = gaussian_filter(cv.ref.mean(-1), 2) if getattr(cv, "ref", None) is not None else None
        rng = np.random.default_rng(int(params.get("seed", 11)))
        X = np.zeros((cv.H, cv.W), np.float32)
        cnt = 0
        for i, ob in enumerate(find_objects(cells)):
            if ob is None:
                continue
            m = cells[ob] == i + 1
            A = int(m.sum())
            if not (amin <= A <= amax) or ob[0].start == 0 or ob[1].start == 0 or ob[0].stop == cv.H or ob[1].stop == cv.W:
                continue
            if A / m.size < 0.3:
                continue
            yy, xx = np.nonzero(m)
            cy, cx = ob[0].start + yy.mean(), ob[1].start + xx.mean()
            if val is not None and val[int(cy), int(cx)] > level:
                continue
            r = float(np.clip(0.2 * math.sqrt(A), 0.5, 0.18 * ppm)) * float(params.get("size", 1.0))
            ang = rng.uniform(0, math.pi)
            # a short burin flick: a dot drawn out to a point
            pts = np.array([[cx - math.cos(ang) * r * 0.9, cy - math.sin(ang) * r * 0.9], [cx + math.cos(ang) * r * 0.9, cy + math.sin(ang) * r * 0.9]])
            b = _Buf(X, None)
            self._strip(b, pts[:, 0], pts[:, 1], np.full(2, -math.sin(ang)), np.full(2, math.cos(ang)), np.array([2 * r, 1.2 * r]), np.ones(2), True)
            cnt += 1
            if cnt >= int(params.get("max", 20000)):
                break
        kink = np.asarray(INKS.get(cv.meta.get("etch_ink", params.get("ink", "intaglio_black")), INKS["intaglio_black"]), np.float32)
        sl = (slice(0, cv.H), slice(0, cv.W))
        self._composite(cv, sl, X, float(cv.meta.get("etch_D", 3.6)), kink / kink.mean(), None)
        print(f"lozenge: {cnt} dots")

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
        k = {"silk": 0.06, "laid_paper": 0.05, "bristol": 0.015, "illustration_board": 0.012, "plate_wove": 0.03, "plate_laid": 0.035}.get(sup, 0.045)
        ink = np.clip(cv.ink, 0, 4)
        shade = 1 + k * (cv.tex - 0.5) * (1 - np.clip(ink / 3, 0, 0.8))
        pm = cv.meta.get("platemark")
        if pm:
            # inside the plate the paper was pressed flat against polished metal: less tooth; the bevel throws a
            # shadow on the top and left edge and catches the light on the bottom and right (light from the top left)
            x0, y0, x1, y1 = (int(v) for v in pm)
            shade[y0:y1, x0:x1] = 1 + (shade[y0:y1, x0:x1] - 1) * 0.45
            b = max(1, int(round(cv.meta.get("platemark_bevel", 0.5) * self.ppm(cv))))
            e = np.ones_like(shade)
            e[y0:y1, max(0, x0 - b):x0] *= 0.93; e[max(0, y0 - b):y0, x0:x1] *= 0.93
            e[y0:y1, x1:x1 + b] *= 1.025; e[y1:y1 + b, x0:x1] *= 1.025
            e[y0:y1, x0:x0 + 1] *= 0.97; e[y0:y0 + 1, x0:x1] *= 0.97
            shade = shade * gaussian_filter(e, 0.6)
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
        if op == "bite":
            return self._bite(cv, params)
        if op == "wipe":
            return self._wipe(cv, params)
        if op == "platemark":
            return self._platemark(cv, params)
        if op == "lozenge":
            return self._lozenge(cv, params)
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


class _Buf:
    """A bare stroke buffer for _strip (burr, lozenge dots)."""

    def __init__(self, X, clip):
        self.X, self.clip, self.bb, self.Wl, self.water, self.wmax = X, clip, None, None, 0, 0.0

    def _bbx(self, x0, y0, x1, y1):
        self.bb = [x0, y0, x1, y1] if self.bb is None else [min(self.bb[0], x0), min(self.bb[1], y0), max(self.bb[2], x1), max(self.bb[3], y1)]


class _Shim:
    def __init__(self, cv):
        self.meta, self.clip, self.H, self.W = cv.meta, None, 1, 1
