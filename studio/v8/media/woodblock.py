"""Woodblock: a Japanese multi-block colour print (ukiyo-e), and the black-and-white woodcut of German
Expressionism. Not a brush medium: every stroke of a tool defines a carved block, and the block is
printed once, as a whole, when the hand lifts (at the next tool, glaze or episode end).

- key:     the keyblock line. A brush-drawn line (swells with pressure, tapers at the ends) that the
           carver leaves standing; printed dense and crisp, in register (no slip).
- block:   a colour block, one carved plank printed once. With a schema (match) the stroke marks which
           area: the carver cuts the schema's connected area of that colour, bounded by the keyline; without
           one, the stroke's area is carved. Strokes of the same colour (or over an area that block already
           printed) add to the same block instead of printing over it. It prints as a flat, slightly uneven
           transparent film (KM layer) with baren mottle, wood grain, paper fibre, pigment pooling at the
           block's edge and a registration slip of 0-2 px. Texture amplitudes are set from Met ukiyo-e
           prints (docs/calibration/woodblock.md).
- bokashi: a block whose colour is wiped into water: full strength where the stroke starts, fading to
           nothing where it ends (or as "fade" says), with the brush's unevenness.
- gouge:   cuts white out of a black block (woodcut): V-gouge wedges or U-gouge channels with splintery,
           grain-torn edges; the cut shows the paper.
State: col (apparent colour), inked (total film printed per pixel), emb (paper relief for karazuri),
blk/blkc (which colour block printed a pixel and how fully), keyf (keyblock film); the block table
(colour, film, registration, wood offset) is kept in the canvas meta as "blocks".
"""
import math, os, sys
import numpy as np
from scipy.ndimage import gaussian_filter, label, binary_dilation, zoom
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont
from .base import Medium, hx, pigment_from_hex, km_layer

_CACHE = {}
# The key line (docs/calibration/woodblock.md, "Key line": public-domain Met ukiyo-e figure and landscape prints, their
# widths along lines; the tool measured on its key film): width = size/2 x weight x (KEY_MIN + (1.06 - KEY_MIN) p^KEY_EXP)
# x a slow swell.
KEY_MIN, KEY_EXP = 0.28, 1.0     # pressure response (unchanged from before; eye)
KEY_RHYTHM = 0.5                 # amplitude of the along-line swell (data: width CV along key lines)
KEY_WAVE = (10.0, 18.0)          # its wavelength, in brush sizes (eye)
PX_PER_MM = 4.0                  # the canvas's scale unless `new --px-per-mm` says otherwise (1200 x 1600 = a 30 x 40 cm sheet)
HAIR_SPACING_MM = 0.65           # centre-to-centre spacing of the hair strands (data, weak: 0.61-0.79 mm on three hair crops)
KEY_UNIFORM = 1.6                # `report finish` flags a key line whose widest tenth / median is below this (judgement)
KEY_WEIGHT = 0.4                 # spread (sd of log) of the weight from stroke to stroke (data: widest tenth / median)


def _norm(a):
    return ((a - a.min()) / (a.max() - a.min() + 1e-6)).astype(np.float32)


def _fields(H, W, support):
    """Wood grain, baren mottle and splinter noise, padded so each block can take its own offset."""
    key = (H, W, support)
    if key in _CACHE:
        return _CACHE[key]
    P = 64
    h, w = H + 2 * P, W + 2 * P
    rng = np.random.default_rng(11)
    coarse = support == "coarse"
    # grain: growth rings along x, warped, plus streaky figure
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    warp = gaussian_filter(rng.random((h // 8 + 1, w // 8 + 1)).astype(np.float32), (2, 6))
    warp = np.kron(_norm(warp), np.ones((8, 8), np.float32))[:h, :w]
    warp = gaussian_filter(warp, 4)
    period = 11.0 if coarse else 8.0
    rings = 0.5 + 0.5 * np.sin(2 * math.pi * (y + 60 * warp + 4 * np.sin(x / 140.0)) / period)
    rings = rings ** (3 if coarse else 4)
    streak = _z(gaussian_filter(rng.random((h, w)).astype(np.float32), (0.7, 30 if coarse else 22)))
    grain = _norm(0.3 * rings + 0.7 * streak)   # by eye: the references show streaky figure more than regular rings
    # baren: mid-frequency mottle plus fine speckle
    mot = _z(0.45 * _z(gaussian_filter(rng.random((h, w)).astype(np.float32), 4.0))
             + 0.55 * _z(gaussian_filter(rng.random((h, w)).astype(np.float32), 1.0)), 2.0)   # by eye: more fine speckle
    # splinters: torn along the grain
    spl = 0.6 * _z(gaussian_filter(rng.random((h, w)).astype(np.float32), (0.7, 4.0)), 1.5) \
        + 0.4 * _z(gaussian_filter(rng.random((h, w)).astype(np.float32), (1.2, 14.0)), 1.5)
    _CACHE[key] = (P, grain, mot, spl)
    return _CACHE[key]


def _lab(rgb):
    """sRGB (0..1) to CIE L*a*b* (D65), for colour tolerances in delta-E units."""
    c = np.asarray(rgb, np.float32)
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]], np.float32)
    xyz = lin @ M.T / np.array([0.9505, 1.0, 1.089], np.float32)
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1).astype(np.float32)


def _z(a, spread=2.5):
    """Normalise a smooth noise field by its spread (not its extremes), so it keeps contrast."""
    return np.clip(0.5 + (a - a.mean()) / (2 * spread * a.std() + 1e-6), 0, 1).astype(np.float32)


def _sl(field, P, y0, y1, x0, x1, oy, ox):
    return field[P + y0 + oy:P + y1 + oy, P + x0 + ox:P + x1 + ox]


def _region(reg, W, H):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    t = reg.get("type", "canvas")
    if t == "ellipse":
        d.ellipse([reg["cx"] - reg["rx"], reg["cy"] - reg["ry"], reg["cx"] + reg["rx"], reg["cy"] + reg["ry"]], fill=255)
    elif t == "rect":
        d.rectangle([reg["x"], reg["y"], reg["x"] + reg["w"], reg["y"] + reg["h"]], fill=255)
    elif t == "poly":
        d.polygon([tuple(p) for p in reg["pts"]], fill=255)
    else:
        return np.ones((H, W), np.float32)
    return np.array(m, np.float32) / 255


def _font(px):
    # Latin letters only: Teodor's own mark, never imitation Japanese or Chinese script (the brief forbids fake seals)
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, px)
            except Exception:
                pass
    return ImageFont.load_default()


class Cut:
    """One stroke of a woodblock tool: it collects the carved shape dab by dab; the medium prints it
    (flush) when the stroke is over."""

    def __init__(self, med, kind, size, color, rng, it):
        self.med, self.kind, self.size, self.rng = med, kind, size, rng
        self.color = np.asarray(color, np.float32).copy()
        self.it = it
        self.cov = None
        self.arc = None
        self.dist = 0.0
        self.bb = [10 ** 9, 10 ** 9, -1, -1]
        self.psum, self.n = 0.0, 0
        self.step = 1.0
        self.speedfx = 0.0
        self.vee = kind == "gouge" and it.get("cut", "v" if size < 14 else "u") == "v"
        self.liner = self.vee     # the key line's ends are the core's ordinary landing and lift (data: end ratio)
        reg = float(it.get("registration", 1.0))
        if kind in ("block", "bokashi"):
            a = rng.uniform(0, 2 * math.pi)
            d = min(2.0, abs(rng.normal(0.9, 0.6))) * reg
            self.off = (int(round(d * math.sin(a))), int(round(d * math.cos(a))))
        else:
            self.off = (0, 0)
        self.goff = (int(rng.integers(-60, 61)), int(rng.integers(-60, 61)))
        if kind == "key":
            # the carved brush line (docs/calibration/woodblock.md, "Key line"): a slow swell along the line (two
            # incommensurate waves, KEY_RHYTHM), and, with "lines": n, a bundle of n fine parallel lines (hair, kewari)
            # `spacing` px apart that gather where the pressure is light, each line ending at its own point
            self.ph = rng.uniform(0, 2 * math.pi, 2)
            # each stroke of the brush drawing has its own weight (some pressed, some light): lognormal (KEY_WEIGHT)
            ws = float(it.get("weight_spread", KEY_WEIGHT * (0.5 if int(it.get("lines", 1)) > 1 else 1.0)))   # a hair bundle varies less
            self.wt = float(np.exp(np.clip(rng.normal(0, ws), -2.5, 2.5)))
            self.fq = 2 * math.pi / (max(size, 3.0) * rng.uniform(KEY_WAVE[0], KEY_WAVE[1]) * np.array([1.0, 0.43]))
            n = max(1, int(it.get("lines", 1)))
            self.nl = n
            if n > 1:
                self.loff = (np.arange(n) - (n - 1) / 2) + rng.normal(0, 0.12, n)      # in units of the spacing
                self.lw = np.clip(rng.lognormal(0, 0.25, n), 0.6, 1.6)
                self.lcut = rng.uniform(0.12, 0.5, n)      # pressure below which each strand has ended (staggered ends)
                self.lph = rng.uniform(0, 2 * math.pi, n)

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        if self.cov is None:
            self.cov = np.zeros((cv.H, cv.W), np.float32)
            if self.kind == "key":
                ppm = float(cv.meta.get("px_per_mm", PX_PER_MM))
                if "width_mm" in self.it:          # the line's width in mm at the print's scale
                    self.size = float(self.it["width_mm"]) * ppm
                if self.nl > 1:
                    self.loff = self.loff * float(self.it.get("spacing", HAIR_SPACING_MM * ppm))
            if self.kind == "bokashi":
                self.arc = []        # the path (x, y, distance along it): the wipe runs along the stroke
            self.med._pending = (self, cv)
        r = max(0.6, self.size / 2 * rscale)
        p = min(press, 1.2)
        if self.kind == "key":
            a = self.dist + (self.step if self.n else 0.0)
            r *= self.wt * (KEY_MIN + (1.06 - KEY_MIN) * p ** KEY_EXP) * (1 + KEY_RHYTHM * 0.7 * (math.sin(a * self.fq[0] + self.ph[0])
                                                                              + 0.6 * math.sin(a * self.fq[1] + self.ph[1])))
            r = max(r, 0.55)          # a carved line thins but does not break into dashes
            soft = 0.55
            if self.nl > 1:
                return self._strands(cv, x, y, ang, p, r, soft)
        elif self.kind == "gouge":
            r *= min(1.0, 1.15 * p ** 1.4) if self.vee else min(1.0, 0.35 + 0.9 * p)
            soft = 2.2
        else:
            r *= 0.92 + 0.08 * min(p, 1)
            soft = 0.6
        R = int(math.ceil(r + 2 * soft)) + 1
        x0, x1 = max(0, int(x) - R), min(cv.W, int(x) + R + 1)
        y0, y1 = max(0, int(y) - R), min(cv.H, int(y) + R + 1)
        self.dist += self.step if self.n else 0.0
        self.psum += press; self.n += 1
        if x0 >= x1 or y0 >= y1 or r < 0.5:
            return
        yy, xx = np.ogrid[y0:y1, x0:x1]
        d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2, dtype=np.float32)
        m = np.clip(0.5 + (r - d) / (2 * soft), 0, 1)
        if cv.clip is not None:
            m = m * cv.clip[y0:y1, x0:x1]
        c = self.cov[y0:y1, x0:x1]
        if self.arc is not None:
            self.arc.append((x, y, self.dist))
        np.maximum(c, m, out=c)
        b = self.bb
        b[0], b[1], b[2], b[3] = min(b[0], y0), min(b[1], x0), max(b[2], y1), max(b[3], x1)

    def _strands(self, cv, x, y, ang, p, r, soft):
        """Hair as the carver cuts it: many fine parallel lines along the stroke, gathering toward its tapers."""
        if self.cov is None:
            return
        self.dist += self.step if self.n else 0.0
        self.psum += p; self.n += 1
        nx, ny = -math.sin(ang), math.cos(ang)
        gather = 0.35 + 0.65 * min(1.0, p)
        for k in range(self.nl):
            if p < self.lcut[k]:
                continue
            rk = max(0.5, r * self.lw[k] * (1 + 0.15 * math.sin(self.dist * self.fq[0] * 1.7 + self.lph[k])))
            o = self.loff[k] * gather
            cx, cy = x + nx * o, y + ny * o
            R = int(math.ceil(rk + 2 * soft)) + 1
            x0, x1 = max(0, int(cx) - R), min(cv.W, int(cx) + R + 1)
            y0, y1 = max(0, int(cy) - R), min(cv.H, int(cy) + R + 1)
            if x0 >= x1 or y0 >= y1:
                continue
            yy, xx = np.ogrid[y0:y1, x0:x1]
            d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2, dtype=np.float32)
            m = np.clip(0.5 + (rk - d) / (2 * soft), 0, 1)
            if cv.clip is not None:
                m = m * cv.clip[y0:y1, x0:x1]
            c = self.cov[y0:y1, x0:x1]
            np.maximum(c, m, out=c)
            b = self.bb
            b[0], b[1], b[2], b[3] = min(b[0], y0), min(b[1], x0), max(b[2], y1), max(b[3], x1)


class Woodblock(Medium):
    name = "woodblock"
    arrays = ("col", "inked", "emb", "blk", "blkc", "keyf")
    supports = {"washi": "hosho washi: soft kozo-fibre paper sized with dosa, printed damp; long fibres and a cloudy formation show in flat colour",
                "coarse": "heavier, coarser paper for the black-and-white woodcut: a grainy tooth that starves the ink in its hollows"}
    tools = {"key": "keyblock line: a brush-drawn line (swelling with pressure, tapering at the ends) carved and printed crisp and dense",
             "block": "colour block: the stroke's area is carved and printed as a flat, slightly uneven transparent film with wood grain, baren mottle, edge pooling and a small registration slip",
             "bokashi": "graded block: colour wiped into water, full where the stroke starts and fading to the paper where it ends (\"fade\": start|end|both)",
             "gouge": "woodcut gouge: cuts white out of a black block; V-gouge wedges (\"cut\": \"v\", default under size 14) or U-gouge channels (\"u\"), splintery along the grain"}
    finishes = {"seal": "print Teodor's mark as a block: a red seal with TEO/DOR cut out in white (Latin letters only; params text, at br|bl|tr|tl|[x, y], size, color), or {\"mark\": \"signature\"}: his signature carved in the keyblock",
                "impression": "the final pressing: printed areas sink slightly into the damp paper; with a region, blind embossing (karazuri) raises it without ink"}

    def __init__(self):
        self._pending = None

    # --- support
    def texture(self, h, w, support):
        rng = np.random.default_rng(5)
        if support == "coarse":
            tooth = _z(gaussian_filter(rng.random((h, w)).astype(np.float32), 1.1), 2.0)
            cloud = _z(gaussian_filter(rng.random((h, w)).astype(np.float32), 14))
            fib_n, fib_alpha = int(h * w / 1800), 40
            base = 0.65 * tooth + 0.35 * cloud
        else:
            fine = _z(gaussian_filter(rng.random((h, w)).astype(np.float32), 0.7))
            cloud = _z(gaussian_filter(rng.random((h, w)).astype(np.float32), 22))
            fib_n, fib_alpha = int(h * w / 900), 120
            base = 0.4 * fine + 0.6 * cloud
        im = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(im)
        for _ in range(fib_n):
            x, y = rng.random() * w, rng.random() * h
            a = rng.uniform(0, math.pi)
            L = rng.uniform(15, 70)
            bend = rng.normal(0, 0.3)
            pts = [(x + math.cos(a + bend * t) * L * t, y + math.sin(a + bend * t) * L * t) for t in np.linspace(0, 1, 5)]
            d.line(pts, fill=int(rng.uniform(0.4, 1) * fib_alpha), width=1)
        fib = gaussian_filter(np.array(im, np.float32) / 255, 0.6)
        return np.clip(0.75 * base + 0.9 * fib, 0, 1).astype(np.float32)

    def _paper(self, cv, ys, xs):
        g = hx(cv.meta.get("ground", "#f1ead9"))
        t = cv.tex[ys, xs]
        k = 0.09 if cv.meta.get("support") == "coarse" else self.PAPER_K
        return np.clip(g[None, None, :] * (1 - k * 0.6 + k * t)[..., None], 0, 1).astype(np.float32)

    def init_state(self, cv, ground):
        cv.inked = np.zeros((cv.H, cv.W), np.float32)
        cv.emb = np.zeros((cv.H, cv.W), np.float32)
        cv.blk = np.zeros((cv.H, cv.W), np.float32)    # which colour block (id + 1) printed each pixel last
        cv.blkc = np.zeros((cv.H, cv.W), np.float32)   # how much of that block's area covers the pixel (0..1)
        cv.keyf = np.zeros((cv.H, cv.W), np.float32)   # keyblock film (colour blocks stop at the keyline)
        cv.col = self._paper(cv, slice(None), slice(None))

    # --- tools
    def make_tool(self, it, size, color, rng):
        self.flush()
        kind = it.get("brush", "block")
        if kind in ("blend", "smudge"):
            return _Nothing()
        if kind in ("liner", "line", "keyblock", "carve_key"):
            kind = "key"
        if kind not in self.tools:
            kind = "block"
        return Cut(self, kind, size, color, rng, it)

    def flush(self):
        if self._pending is None:
            return
        t, cv = self._pending
        self._pending = None
        if t.cov is None or t.bb[2] < 0:
            return
        pad = 6
        y0, x0 = max(0, t.bb[0] - pad), max(0, t.bb[1] - pad)
        y1, x1 = min(cv.H, t.bb[2] + pad), min(cv.W, t.bb[3] + pad)
        cov = t.cov[y0:y1, x0:x1]
        P, grain, mot, spl = _fields(cv.H, cv.W, cv.meta.get("support"))
        gy, gx = t.goff
        coarse = cv.meta.get("support") == "coarse"
        if t.kind == "gouge":
            sp = _sl(spl, P, y0, y1, x0, x1, gy, gx)
            edge = np.clip(4 * cov * (1 - cov) * 2.5, 0, 1)
            rag = cov + (sp - 0.5) * (1.0 if t.vee else 1.3) * edge
            cut = np.clip((rag - 0.5) * 4 + 0.5, 0, 1)
            cut = np.maximum(cut, np.clip((cov - 0.96) * 25, 0, 1))  # the gouge's own path always clears
            # the floor of a wide, shallow cut still catches a little ink along the grain
            if not t.vee:
                gr = _sl(grain, P, y0, y1, x0, x1, gy, gx)
                cut = cut * (1 - 0.35 * np.clip((gr - 0.82) * 6, 0, 1) * np.clip((cov - 0.95) * 20, 0, 1))
            ys, xs = slice(y0, y1), slice(x0, x1)
            pc = self._paper(cv, ys, xs)
            cv.col[ys, xs] = cv.col[ys, xs] * (1 - cut[..., None]) + pc * cut[..., None]
            cv.inked[ys, xs] *= (1 - cut)
            return
        it = t.it
        if t.kind == "block":
            return self._print_block(t, cv, cov, y0, y1, x0, x1, coarse)
        shape = gaussian_filter(cov, 0.7)
        shape = np.clip((shape - 0.5) * 2.5 + 0.5, 0, 1)
        press = t.psum / max(t.n, 1)
        baren = 0.82 + 0.22 * min(press, 1.1)
        if t.kind == "key":
            op = it.get("opacity", 0.6)
            dens = it.get("density", 2.4) * baren
            gstr, mstr = (0.10 if not coarse else 0.25), 0.12
        else:
            op = it.get("opacity", 0.3)
            dens = it.get("density", 1.0) * baren
            if t.kind == "block" and "density" not in it:
                dens = self._aim(cv, shape, y0, y1, x0, x1, t.off, t.color, op, baren)
            gstr = it.get("grain", self.GRAIN_COARSE if coarse else self.GRAIN)
            mstr = self.MOTTLE
        x = self._impression(cv, shape, y0, y1, x0, x1, gy, gx, dens, gstr, mstr, coarse, t.rng,
                             pool=(0.12 if t.kind == "key" else self.POOL))
        if t.kind == "bokashi":
            # distance along the stroke of the nearest point of its path: the colour fades along the
            # stroke's direction, not with the round footprint of its first dab
            pts = np.asarray(t.arc, np.float32)
            st = 4
            gy_, gx_ = np.mgrid[y0:y1:st, x0:x1:st].astype(np.float32)
            _, ix = cKDTree(pts[:, :2]).query(np.stack([gx_.ravel(), gy_.ravel()], -1))
            arc = pts[ix, 2].reshape(gy_.shape)
            arc = zoom(arc, (st, st), order=1)[:y1 - y0, :x1 - x0]
            arc = np.pad(arc, ((0, y1 - y0 - arc.shape[0]), (0, x1 - x0 - arc.shape[1])), mode="edge")
            tt = gaussian_filter(arc, max(1.5, min(t.size / 4, 40))) / max(t.dist, 1.0)
            tt = np.clip(tt + 0.06 * (_sl(mot, P, y0, y1, x0, x1, -gy, gx) - 0.5), 0, 1)
            fade = it.get("fade", "start")
            if fade == "end":
                tt = 1 - tt
            elif fade == "both":
                tt = np.abs(2 * tt - 1)
            ramp = np.clip(1 - tt, 0, 1) ** 1.6
            x = x * ramp
        self._print(cv, x, y0, y1, x0, x1, t.off, t.color, op)
        if t.kind == "key":
            cv.keyf[y0:y1, x0:x1] = np.maximum(cv.keyf[y0:y1, x0:x1], shape)

    # ------------------------------------------------------------------ colour blocks
    # A colour block is one carved plank, printed once per sheet. The carver cuts it from the artist's
    # colour notes on a keyblock proof, so its area is a flat field bounded by the keyline, not the
    # trace of a brush. Two things follow and are modelled here:
    #  1. carving: with a schema (match), the block's shape is the area of the schema around the stroke
    #     that has the block's colour (within `tolerance` delta-E), stopping at printed keylines; the
    #     stroke only says which area. Without a schema, or with "carve": "stroke", the stroke's own
    #     area is carved.
    #  2. one block per colour: strokes whose colour is within BLOCK_DE of an earlier block are more of
    #     the same plank: they add only the area that block has not printed yet, with its film,
    #     registration and wood, so a field built of many strokes prints as one even impression
    #     instead of a pile of overlapping shapes. "reprint": true forces a second impression.
    # flat-field texture, set from hand-chosen flat passages of 8 Met ukiyo-e prints at 4 px/mm (std L* 2.9,
    # IQR 2.6-3.4) and a bare margin (std L* 1.3): GRAIN, MOTTLE, FIBRE, PAPER_K. GRAIN_COARSE and POOL by eye.
    GRAIN, GRAIN_COARSE, MOTTLE, POOL, FIBRE, PAPER_K = 0.3, 0.38, 0.55, 0.45, 0.5, 0.22
    BLOCK_DE = 8.0       # by eye: two colours closer than this are mixed from the same inks
    TOLERANCE = 12.0     # by eye: colour distance in the schema that the carver treats as the same area
    FLAT_DE = 3.0        # by eye: seed pixels must lie inside an area of the schema, not on its anti-aliased edge
    REGION_MAX = 1600    # px: the largest half-window searched for the area (a speed bound for very large canvases)

    def _ref_lab(self, cv):
        if getattr(self, "_rlk", None) is not cv.ref:
            r = np.stack([gaussian_filter(cv.ref[..., i], 1.0) for i in range(3)], -1)
            self._rlk, self._rl = cv.ref, _lab(r)
            # interior pixels of the schema's areas (no anti-aliased boundary colours): Lab gradient < FLAT_DE per px
            g = sum(np.hypot(np.gradient(self._rl[..., i], axis=0), np.gradient(self._rl[..., i], axis=1)) ** 2 for i in range(3))
            self._flat = np.sqrt(g) < self.FLAT_DE
        return self._rl

    def _find_block(self, cv, color):
        lab = _lab(np.asarray(color, np.float32))
        best, bi = 1e9, -1
        for i, b in enumerate(cv.meta.get("blocks", [])):
            d = float(np.linalg.norm(np.asarray(b.get("lab") or _lab(np.asarray(b["c"], np.float32)).tolist(), np.float32) - lab))
            if d < best:
                best, bi = d, i
        return bi if best < self.BLOCK_DE else -1

    def _carve(self, t, cv, cov, y0, y1, x0, x1):
        """The block's carved area around the stroke: the connected area of the schema that has the colour
        under the stroke. Returns (area, window, colour) or None (carve the stroke's own area)."""
        it = t.it
        mode = it.get("carve", "region" if it.get("type") == "match" else "stroke")
        if mode != "region" or cv.ref is None:
            return None
        rl = self._ref_lab(cv)
        tol = float(it.get("tolerance", self.TOLERANCE))
        # the seed: the pixels under the stroke that are not keyline, and of those the colour most of them share
        # (a small area such as an ear is smaller than the brush: the stroke's median would mix it with its
        # surround and the keyline, and find no area of that colour)
        kf = (cv.keyf[y0:y1, x0:x1] < 0.5)
        if (kf & self._flat[y0:y1, x0:x1] & (cov > 0.05)).sum() >= 2:
            kf = kf & self._flat[y0:y1, x0:x1]
        seedm = (cov > 0.5) & kf
        if seedm.sum() < 3:
            seedm = (cov > 0.05) & kf
        if seedm.sum() < 1:
            self._miss(t, cov, y0, x0, "lies on the keyline")
            return None
        # first choice: the pixels with the stroke's own colour (match samples it where the stroke starts; a painter
        # names it); otherwise the colour most of the seed pixels share
        want = np.linalg.norm(rl[y0:y1, x0:x1] - _lab(np.clip(t.color, 0, 1)), axis=-1) < tol * 0.5
        if (seedm & want).sum() >= 2:
            seedm = seedm & want
        else:
            labs = rl[y0:y1, x0:x1][seedm]
            sub = labs[::max(1, len(labs) // 400)]
            near = np.linalg.norm(sub[:, None, :] - sub[None, :, :], axis=-1) < tol * 0.5
            mode = sub[int(np.argmax(near.sum(1)))]
            seedm = seedm & (np.linalg.norm(rl[y0:y1, x0:x1] - mode, axis=-1) < tol * 0.5)
        seed_lab = np.median(rl[y0:y1, x0:x1][seedm], axis=0)
        # what the painter asked for beyond the schema (palette, colour shift) rides on the area's colour
        seed_rgb = np.median(cv.ref[y0:y1, x0:x1][seedm], axis=0)
        # only when the painter asked for it (palette or colour shift); match's own sampling noise is not a request
        shift = np.clip(t.color - seed_rgb, -0.25, 0.25) if (it.get("colors") or it.get("color_shift")) else np.zeros(3, np.float32)
        bi = self._find_block(cv, np.clip(seed_rgb + shift, 0, 1))
        if bi >= 0:                     # already carved and printed here (in this pass, for a reprint): nothing to do
            if it.get("reprint"):
                pc = self._pass_cov(t, bi, cv, create=False)
                done = (pc[y0:y1, x0:x1] > 0.5) if pc is not None else np.zeros_like(seedm)
            else:
                done = (cv.blk[y0:y1, x0:x1] == bi + 1) & (cv.blkc[y0:y1, x0:x1] > 0.5)
            if done[seedm].mean() > 0.8:
                return "done"
        R = int(min(self.REGION_MAX, max(cv.H, cv.W)))
        cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
        wy0, wy1, wx0, wx1 = max(0, cy - R), min(cv.H, cy + R), max(0, cx - R), min(cv.W, cx + R)
        same = np.linalg.norm(rl[wy0:wy1, wx0:wx1] - seed_lab, axis=-1) < tol
        same &= cv.keyf[wy0:wy1, wx0:wx1] < 0.5
        if cv.clip is not None:
            same &= cv.clip[wy0:wy1, wx0:wx1] > 0.5
        seed = np.zeros_like(same)
        seed[y0 - wy0:y1 - wy0, x0 - wx0:x1 - wx0] = seedm
        if not (seed & same).any():
            self._miss(t, cov, y0, x0, "found no area of its colour in the schema")
            return None
        lb, n = label(same)
        ids = np.unique(lb[seed & same])
        area = np.isin(lb, ids[ids > 0])
        colour = np.clip(cv.ref[wy0:wy1, wx0:wx1][area].mean(0) + shift, 0, 1).astype(np.float32)
        # the colour block runs into the middle of the keyline, so no paper shows between them
        area |= binary_dilation(area, iterations=2) & (cv.keyf[wy0:wy1, wx0:wx1] >= 0.5)
        return area.astype(np.float32), (wy0, wy1, wx0, wx1), colour

    def _print_block(self, t, cv, cov, y0, y1, x0, x1, coarse):
        it = t.it
        carved = self._carve(t, cv, cov, y0, y1, x0, x1)
        if carved == "done":
            return
        color = t.color
        if carved is not None:
            area, (y0, y1, x0, x1), color = carved      # area in the search window's coordinates
            ys, xs = np.nonzero(area)
            ys, xs = ys + y0, xs + x0
            pad = 6
            by0, by1 = max(y0, ys.min() - pad), min(y1, ys.max() + 1 + pad)
            bx0, bx1 = max(x0, xs.min() - pad), min(x1, xs.max() + 1 + pad)
            cov = area[by0 - y0:by1 - y0, bx0 - x0:bx1 - x0]
            y0, y1, x0, x1 = by0, by1, bx0, bx1
        shape = gaussian_filter(cov, 0.7)
        shape = np.clip((shape - 0.5) * 2.5 + 0.5, 0, 1)
        blocks = cv.meta.setdefault("blocks", [])
        rp = it.get("reprint")
        nimp = (1 if rp is True else max(0, int(rp))) if rp else 0     # extra impressions of the block
        bi = self._find_block(cv, color)
        if bi < 0 and carved is not None:
            # an area already carved and printed is that block, not a new one
            ids = cv.blk[y0:y1, x0:x1][(cov > 0.5) & (cv.blkc[y0:y1, x0:x1] > 0.5)].astype(int)
            if ids.size > 0.5 * max((cov > 0.5).sum(), 1):
                k = int(np.bincount(ids).argmax())
                if k > 0 and np.mean(ids == k) > 0.6:
                    bi = k - 1           # the same carved area is the same block ("reprint": true prints over it)
        press = t.psum / max(t.n, 1)
        baren = 0.82 + 0.22 * min(press, 1.1)
        op = it.get("opacity", 0.3)
        if nimp and bi >= 0:
            # a reprint is the same carved plank inked and printed again: one more impression of the block per
            # reprint intention, however many strokes (seeds) mark its areas. Every stroke of this intention adds
            # only the area this pass has not printed yet.
            b = blocks[bi]
            pc = self._pass_cov(t, bi, cv)
            prev = pc[y0:y1, x0:x1]
            new = np.clip(shape - prev, 0, 1)
            if new.max() < 0.05 or new.sum() < 4:
                return
            union = np.maximum(shape, prev)
            color, off, g, op = np.asarray(b["c"], np.float32), tuple(b["off"]), tuple(b["g"]), b["op"]
            dens = float(it["density"]) * baren if it.get("density") is not None else b["d"] * nimp
            gstr = it.get("grain", self.GRAIN_COARSE if coarse else self.GRAIN)
            x = self._impression(cv, union, y0, y1, x0, x1, g[0], g[1], dens, gstr, self.MOTTLE, coarse, t.rng, pool=self.POOL)
            x = x * np.where(union > 1e-3, new / np.maximum(union, 1e-3), 0)
            self._print(cv, x, y0, y1, x0, x1, off, color, op)
            pc[y0:y1, x0:x1] = union
            return
        if nimp:
            print("[woodblock] reprint: no block of this colour was printed yet, so this is its first impression")
        if bi >= 0:
            b = blocks[bi]
            same = (cv.blk[y0:y1, x0:x1] == bi + 1)
            prev = np.where(same, cv.blkc[y0:y1, x0:x1], 0.0)
            new = np.clip(shape - prev, 0, 1)
            if new.max() < 0.05 or new.sum() < 4:
                return                       # this part of the block is already printed
            union = np.maximum(shape, prev)
            color, dens, off, g, op = np.asarray(b["c"], np.float32), b["d"], tuple(b["off"]), tuple(b["g"]), b["op"]
        else:
            new, union, off, g = shape, shape, t.off, t.goff
            dens = it.get("density", None)
            dens = dens * baren if dens is not None else self._aim(cv, shape, y0, y1, x0, x1, off, color, op, baren)
            blocks.append({"c": [round(float(v), 4) for v in color], "lab": [round(float(v), 2) for v in _lab(color)],
                           "d": round(float(dens), 4), "off": list(off),
                           "g": list(g), "op": op})
            bi = len(blocks) - 1
        gstr = it.get("grain", self.GRAIN_COARSE if coarse else self.GRAIN)
        x = self._impression(cv, union, y0, y1, x0, x1, g[0], g[1], dens, gstr, self.MOTTLE, coarse, t.rng, pool=self.POOL)
        x = x * np.where(union > 1e-3, new / np.maximum(union, 1e-3), 0)
        self._print(cv, x, y0, y1, x0, x1, off, color, op)
        upd = new > 0.02
        sub_b, sub_c = cv.blk[y0:y1, x0:x1], cv.blkc[y0:y1, x0:x1]
        keep = sub_b == bi + 1
        sub_c[:] = np.where(upd, np.where(keep, np.maximum(sub_c, union), union), sub_c)
        sub_b[upd] = bi + 1

    def _pass_cov(self, t, bi, cv, create=True):
        """The area of block bi printed in the current reprint pass. A pass is one intention: the strokes of one
        intention share its random generator (t.rng), so a new generator starts a new pass; the episode's end
        closes it."""
        rp = getattr(self, "_rp", None)
        if rp is None or rp["rng"] is not t.rng:
            if not create:
                return None
            rp = self._rp = {"rng": t.rng, "cov": {}}
        if bi not in rp["cov"]:
            if not create:
                return None
            rp["cov"][bi] = np.zeros((cv.H, cv.W), np.float32)
        return rp["cov"][bi]

    def _miss(self, t, cov, y0, x0, why):
        ys, xs = np.nonzero(cov > 0.05)
        at = (int(x0 + xs.mean()), int(y0 + ys.mean())) if len(xs) else (x0, y0)
        self.__dict__.setdefault("_misses", []).append((at, "#%02x%02x%02x" % tuple(int(v * 255) for v in np.clip(t.color, 0, 1)), why))

    def _report_misses(self):
        ms = self.__dict__.pop("_misses", [])
        if ms:
            show = "; ".join(f"({x}, {y}) {c} {w}" for (x, y), c, w in ms[:8]) + (f"; and {len(ms) - 8} more" if len(ms) > 8 else "")
            print(f"[woodblock] {len(ms)} block seed(s) carved the stroke's own area instead of a schema area: {show}. "
                  "Put the stroke inside the area it means (off the keyline), or carve it with \"carve\": \"stroke\".")

    def _aim(self, cv, shape, y0, y1, x0, x1, off, color, op, baren):
        """The printer mixes the ink for the colour the artist asked for: choose the film thickness
        that brings what is under the block closest to that colour (transparent colour can only
        darken, so a light colour over a dark area stays nearly invisible)."""
        oy, ox = off
        cy0, cy1, cx0, cx1 = max(0, y0 + oy), min(cv.H, y1 + oy), max(0, x0 + ox), min(cv.W, x1 + ox)
        w = shape[cy0 - y0 - oy:cy1 - y0 - oy, cx0 - x0 - ox:cx1 - x0 - ox]
        if w.size == 0 or w.sum() < 1e-3:
            return baren
        under = (cv.col[cy0:cy1, cx0:cx1] * w[..., None]).sum((0, 1)) / w.sum()
        K, S = pigment_from_hex(color, op)
        ts = np.linspace(0.12, 1.7, 14, dtype=np.float32) * baren
        out = km_layer(np.broadcast_to(under, (len(ts), 1, 3)).copy(), K, S, ts[:, None])[:, 0]
        return float(ts[np.argmin(np.abs(out - color).sum(-1))])

    def _impression(self, cv, shape, y0, y1, x0, x1, gy, gx, dens, gstr, mstr, coarse, rng, pool=0.3):
        """Film thickness of one impression: flat ink, heavier at the block's edge, broken by the
        wood grain, the baren's mottle and the paper's fibres and tooth."""
        P, grain, mot, spl = _fields(cv.H, cv.W, cv.meta.get("support"))
        gr = _sl(grain, P, y0, y1, x0, x1, gy, gx)
        mo = _sl(mot, P, y0, y1, x0, x1, gx // 2, gy // 2)
        tex = cv.tex[y0:y1, x0:x1]
        rim = np.clip(shape - gaussian_filter(shape, 1.8), 0, 1)
        x = dens * shape * (1 + pool * rim * 2)
        x = x * (1 - gstr * gr) * (1 - mstr / 2 + mstr * mo)
        if coarse:
            x = x * np.clip(0.55 + 0.75 * tex, 0, 1.15)
        else:
            x = x * (1 - self.FIBRE / 2 + self.FIBRE * tex)
        return x.astype(np.float32)

    def _print(self, cv, x, y0, y1, x0, x1, off, color, op):
        oy, ox = off
        ty0, ty1, tx0, tx1 = y0 + oy, y1 + oy, x0 + ox, x1 + ox
        cy0, cy1, cx0, cx1 = max(0, ty0), min(cv.H, ty1), max(0, tx0), min(cv.W, tx1)
        if cy0 >= cy1 or cx0 >= cx1:
            return
        xs = x[cy0 - ty0:cy1 - ty0, cx0 - tx0:cx1 - tx0]
        K, S = pigment_from_hex(color, op)
        sub = cv.col[cy0:cy1, cx0:cx1]
        cv.col[cy0:cy1, cx0:cx1] = km_layer(sub, K, S, xs)
        cv.inked[cy0:cy1, cx0:cx1] += xs

    # --- the glaze intention: a light flat colour block over the region
    def glaze(self, cv, mask, col, op):
        self.flush()
        rng = np.random.default_rng(int(cv.inked.sum() * 1000) % (2 ** 31))
        shape = np.clip((mask - 0.5) * 6 + 0.5, 0, 1).astype(np.float32)
        ys, xs = np.nonzero(shape > 0.01)
        if len(ys) == 0:
            return
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        shape = gaussian_filter(shape[y0:y1, x0:x1], 0.6)
        coarse = cv.meta.get("support") == "coarse"
        g = (int(rng.integers(-60, 61)), int(rng.integers(-60, 61)))
        x = self._impression(cv, shape, y0, y1, x0, x1, g[0], g[1], 1.6 * op, self.GRAIN_COARSE if coarse else self.GRAIN,
                             self.MOTTLE, coarse, rng)
        a = rng.uniform(0, 2 * math.pi)
        d = min(2.0, abs(rng.normal(0.9, 0.6)))
        self._print(cv, x, y0, y1, x0, x1, (int(round(d * math.sin(a))), int(round(d * math.cos(a)))), col, 0.3)

    # --- time: water-based colour on damp paper; nothing flows once printed
    def episode_end(self, cv):
        self.flush()
        self._rp = None
        self._report_misses()

    def dry(self, cv, amount):
        self.flush()

    # --- seeing
    def render(self, cv):
        self.flush()
        img = cv.col
        if np.abs(cv.emb).max() > 1e-4:
            e = gaussian_filter(cv.emb, 1.2)
            gy, gx = np.gradient(e)
            shade = 1 + np.clip(-gx * 0.5 - gy * 0.8, -0.1, 0.1)
            img = np.clip(img * shade[..., None], 0, 1)
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

    # --- revision: a print can't be taken back
    glaze_role = "body"
    flat_areas_ok = True         # each area is one flat impression by nature: report doesn't flag single-role passages
    first_role = "body"          # every colour block is body colour, printed once (ukiyo-e: drawing, body, contour)

    def revise(self, cv, op, mask, it, felt, rng, core):
        raise SystemExit(f"woodblock can't {op}: a printed impression is in the paper's fibres and the inks are "
                         "transparent, so nothing can be scraped, wiped or painted out. Plan the change in the next "
                         "block: recarve it (a new schema version) and print the corrected block, or start a new impression.")

    def finish_check(self, cv):
        """Is the print finished (docs/FINISHING.md "Woodblock print": complete when the last block is printed; the
        signature and seal are blocks)? Signed or sealed; for ukiyo-e on washi, a key line whose width varies like a
        carved brush line: the widest tenth of its width over the median, measured on the key film along its medial
        line (references 2.6-2.7 on Met prints, docs/calibration/woodblock.md; a single even wire reads as a vector
        drawing: flagged below 1.6, a judgement)."""
        from scipy.ndimage import distance_transform_edt, maximum_filter
        self.flush()
        ops = [f["op"] for f in cv.meta.get("finishes", [])]
        nb = len(cv.meta.get("blocks", []))
        lines, flags = [f"woodblock: {nb} colour blocks; " + (", ".join(ops) or "no finishing steps")
                        + f"; signed: {cv.meta.get('signed') or 'no'}"], []
        if not cv.meta.get("signed") and "seal" not in ops:
            flags.append("no seal or signature: a print is signed in its blocks (finish seal, or sign: the signature cut in the keyblock)")
        key = cv.keyf > 0.5
        if cv.meta.get("support") != "coarse" and key.mean() > 0.002:
            dt = distance_transform_edt(key)
            ridge = key & (dt >= maximum_filter(dt, 3) - 0.75) & (dt >= 1)
            w = 2 * dt[ridge] - 1
            if w.size > 50:
                ratio = float(np.percentile(w, 90) / max(np.median(w), 1e-6))
                ppm = float(cv.meta.get("px_per_mm", PX_PER_MM))
                lines.append(f"key line: median {np.median(w) / ppm:.2f} mm, widest tenth / median {ratio:.1f} (Met prints 2.6-2.7)")
                if ratio < KEY_UNIFORM:
                    flags.append(f"key line nearly uniform (widest tenth / median {ratio:.1f}): ukiyo-e key lines swell and taper, finer on "
                                 "faces and hands, heavier on outer contours and drapery; one even wire reads as a flat vector drawing")
        elif cv.meta.get("support") != "coarse":
            flags.append("no key line printed (the keyblock carries the drawing in ukiyo-e)")
        return lines, flags

    # --- finishing: nothing beyond the impression
    def finish(self, cv, op, params):
        self.flush()
        if op == "seal":
            return self._seal(cv, params)
        if op == "impression":
            if params.get("region"):
                m = gaussian_filter(_region(params["region"], cv.W, cv.H), 1.5)
                cv.emb += m * float(params.get("height", 1.6))
            else:
                cv.emb -= gaussian_filter(np.clip(cv.inked, 0, 1.5), 1.0) * float(params.get("depth", 0.5))
            return
        return super().finish(cv, op, params)

    def _seal(self, cv, p):
        """Teodor's own mark printed as a block: a red seal with TEO / DOR cut out in white (Latin letters; no imitation
        Japanese or Chinese script, which the brief forbids), or ("mark": "signature") his signature carved in the
        keyblock. The worn border and uneven stamp are eye."""
        text = str(p.get("text", "TEO\nDOR"))
        if any(ord(ch) > 0x2FF for ch in text):
            raise SystemExit("woodblock can't cut that seal: Teodor's seal carries his own name in Latin letters (default "
                             "TEO/DOR); imitation Japanese or Chinese characters are a fake seal, which the brief forbids.")
        if p.get("mark") == "signature":
            return self.sign(cv, p.get("at", "auto"), color=p.get("color"))
        s = int(p.get("size", max(28, min(cv.W, cv.H) // 16)))
        at = p.get("at", "br")
        mg = int(max(cv.W, cv.H) * 0.035)
        if isinstance(at, (list, tuple)):
            x0, y0 = int(at[0]), int(at[1])
        else:
            x0 = mg if "l" in at else cv.W - mg - s
            y0 = mg if "t" in at else cv.H - mg - s
        x0, y0 = max(0, min(cv.W - s, x0)), max(0, min(cv.H - s, y0))
        S = s * 4
        im = Image.new("L", (S, S), 0)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, S - 1, S - 1], radius=max(2, S // 10), fill=255)
        lines = [ln for ln in text.split("\n") if ln] or ["T"]
        lh = S * 0.8 / len(lines)
        f = _font(int(lh * 0.9))
        for k, ln in enumerate(lines):
            g = Image.new("L", (S, S), 0)
            gd = ImageDraw.Draw(g)
            bb = gd.textbbox((0, 0), ln, font=f)
            gd.text((-bb[0], -bb[1]), ln, font=f, fill=255)
            g = g.crop((0, 0, max(1, bb[2] - bb[0]), max(1, bb[3] - bb[1]))).resize((int(S * 0.8), int(lh * 0.86)))
            im.paste(0, (int(S * 0.1), int(S * 0.1 + k * lh)), g)        # the letters are cut away: white in red
        im = im.resize((s, s), Image.LANCZOS)
        shape = np.array(im, np.float32) / 255
        rng = np.random.default_rng(len(text) * 7 + s)
        # a worn seal: chipped border and an uneven stamp
        chip = gaussian_filter(rng.random((s, s)).astype(np.float32), 1.0)
        shape = np.clip(shape - (chip > 0.62) * 0.8 * (gaussian_filter(shape, 1.5) < 0.98), 0, 1)
        shape = gaussian_filter(shape, 0.5)
        coarse = cv.meta.get("support") == "coarse"
        x = self._impression(cv, shape, y0, y0 + s, x0, x0 + s, 3, -5, 1.7, 0.12, 0.35, coarse, rng, pool=0.2)
        self._print(cv, x, y0, y0 + s, x0, x0 + s, (0, 0), hx(p.get("color", "#b8322a")), 0.55)
        cv.meta["signed"] = cv.meta.get("signed") or "seal"     # the seal block is the print's signature (FINISHING.md)

    def sign(self, cv, corner="auto", color=None):
        """The signature carved in the keyblock and printed with it: Teodor's handwritten 'Teodor' (signature.GLYPH)
        cut as a key line, in sumi unless a colour is given. Called by the core's `sign` command and by
        `finish seal {"mark": "signature"}`."""
        self.flush()
        try:
            from signature import GLYPH, _catmull
        except ImportError:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from signature import GLYPH, _catmull
        sw = max(64, int(cv.W * 0.12)); sh = int(sw * 0.72)
        mx, my = int(cv.W * 0.035), int(cv.H * 0.03)
        spots = {"br": (cv.W - mx - sw, cv.H - my - sh), "bl": (mx, cv.H - my - sh),
                 "tr": (cv.W - mx - sw, my), "tl": (mx, my)}
        if corner not in spots:
            # the calmer of the bottom corners (the least printed)
            corner = min(("br", "bl"), key=lambda c: float(cv.inked[spots[c][1]:spots[c][1] + sh, spots[c][0]:spots[c][0] + sw].std()))
        ox, oy = spots[corner]
        cov = np.zeros((cv.H, cv.W), np.float32)
        width = max(1.0, sw * 0.02)
        im = Image.new("L", (cv.W, cv.H), 0)
        d = ImageDraw.Draw(im)
        for stroke in GLYPH:
            path = _catmull([tuple(q) for q in np.array(stroke, np.float32)], n=14)
            for a, b in zip(path[:-1], path[1:]):
                w = width * (0.45 + 0.75 * (a[2] + b[2]) / 2)
                d.line([(ox + a[0] * sw, oy + a[1] * sh), (ox + b[0] * sw, oy + b[1] * sh)], fill=255, width=max(1, int(round(w))))
                r = w / 2
                d.ellipse([ox + b[0] * sw - r, oy + b[1] * sh - r, ox + b[0] * sw + r, oy + b[1] * sh + r], fill=255)
        cov = gaussian_filter(np.asarray(im, np.float32) / 255, 0.6)
        y0, y1, x0, x1 = max(0, oy - 4), min(cv.H, oy + sh + 4), max(0, ox - 4), min(cv.W, ox + sw + 4)
        shape = np.clip((cov[y0:y1, x0:x1] - 0.5) * 2.5 + 0.5, 0, 1)
        coarse = cv.meta.get("support") == "coarse"
        x = self._impression(cv, shape, y0, y1, x0, x1, 0, 0, 2.4, 0.10, 0.12, coarse, np.random.default_rng(7), pool=0.12)
        self._print(cv, x, y0, y1, x0, x1, (0, 0), hx(color or "#1b1a1c"), 0.6)
        cv.keyf[y0:y1, x0:x1] = np.maximum(cv.keyf[y0:y1, x0:x1], shape)
        cv.meta["signed"] = cv.meta.get("signed") or "signature"

class _Nothing:
    """Prints cannot be blended or smudged: the colours lie where the blocks put them."""
    size, step, speedfx = 1.0, 1.0, 0.0

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        pass
