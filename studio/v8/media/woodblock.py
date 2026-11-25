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
    for f in ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"):
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
        self.liner = kind == "key" or self.vee
        reg = float(it.get("registration", 1.0))
        if kind in ("block", "bokashi"):
            a = rng.uniform(0, 2 * math.pi)
            d = min(2.0, abs(rng.normal(0.9, 0.6))) * reg
            self.off = (int(round(d * math.sin(a))), int(round(d * math.cos(a))))
        else:
            self.off = (0, 0)
        self.goff = (int(rng.integers(-60, 61)), int(rng.integers(-60, 61)))

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        if self.cov is None:
            self.cov = np.zeros((cv.H, cv.W), np.float32)
            if self.kind == "bokashi":
                self.arc = []        # the path (x, y, distance along it): the wipe runs along the stroke
            self.med._pending = (self, cv)
        r = max(0.6, self.size / 2 * rscale)
        p = min(press, 1.2)
        if self.kind == "key":
            r *= 0.28 + 0.78 * p
            soft = 0.55
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


class Woodblock(Medium):
    name = "woodblock"
    arrays = ("col", "inked", "emb", "blk", "blkc", "keyf")
    supports = {"washi": "hosho washi: soft kozo-fibre paper sized with dosa, printed damp; long fibres and a cloudy formation show in flat colour",
                "coarse": "heavier, coarser paper for the black-and-white woodcut: a grainy tooth that starves the ink in its hollows"}
    tools = {"key": "keyblock line: a brush-drawn line (swelling with pressure, tapering at the ends) carved and printed crisp and dense",
             "block": "colour block: the stroke's area is carved and printed as a flat, slightly uneven transparent film with wood grain, baren mottle, edge pooling and a small registration slip",
             "bokashi": "graded block: colour wiped into water, full where the stroke starts and fading to the paper where it ends (\"fade\": start|end|both)",
             "gouge": "woodcut gouge: cuts white out of a black block; V-gouge wedges (\"cut\": \"v\", default under size 14) or U-gouge channels (\"u\"), splintery along the grain"}
    finishes = {"seal": "print a red seal block (cinnabar, carved text in white): params text, at (br|bl|tr|tl or [x, y]), size, color",
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
    REGION_MAX = 1600    # px: the largest half-window searched for the area (a speed bound for very large canvases)

    def _ref_lab(self, cv):
        if getattr(self, "_rlk", None) is not cv.ref:
            r = np.stack([gaussian_filter(cv.ref[..., i], 1.0) for i in range(3)], -1)
            self._rlk, self._rl = cv.ref, _lab(r)
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
        seedm = cov > 0.5
        if seedm.sum() < 3:
            return None
        seed_lab = np.median(rl[y0:y1, x0:x1][seedm], axis=0)
        # what the painter asked for beyond the schema (palette, colour shift) rides on the area's colour
        seed_rgb = np.median(cv.ref[y0:y1, x0:x1][seedm], axis=0)
        # only when the painter asked for it (palette or colour shift); match's own sampling noise is not a request
        shift = np.clip(t.color - seed_rgb, -0.25, 0.25) if (it.get("colors") or it.get("color_shift")) else np.zeros(3, np.float32)
        bi = -1 if it.get("reprint") else self._find_block(cv, np.clip(seed_rgb + shift, 0, 1))
        if bi >= 0:                     # already carved and printed here: nothing to do (cheap exit)
            done = (cv.blk[y0:y1, x0:x1] == bi + 1) & (cv.blkc[y0:y1, x0:x1] > 0.5)
            if done[seedm].mean() > 0.8:
                return "done"
        R = int(min(self.REGION_MAX, max(cv.H, cv.W)))
        cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
        wy0, wy1, wx0, wx1 = max(0, cy - R), min(cv.H, cy + R), max(0, cx - R), min(cv.W, cx + R)
        tol = float(it.get("tolerance", self.TOLERANCE))
        same = np.linalg.norm(rl[wy0:wy1, wx0:wx1] - seed_lab, axis=-1) < tol
        same &= cv.keyf[wy0:wy1, wx0:wx1] < 0.5
        if cv.clip is not None:
            same &= cv.clip[wy0:wy1, wx0:wx1] > 0.5
        seed = np.zeros_like(same)
        seed[y0 - wy0:y1 - wy0, x0 - wx0:x1 - wx0] = seedm
        if not (seed & same).any():
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
        bi = -1 if it.get("reprint") else self._find_block(cv, color)
        if bi < 0 and carved is not None and not it.get("reprint"):
            # an area already carved and printed is that block, not a new one
            ids = cv.blk[y0:y1, x0:x1][(cov > 0.5) & (cv.blkc[y0:y1, x0:x1] > 0.5)].astype(int)
            if ids.size > 0.5 * max((cov > 0.5).sum(), 1):
                k = int(np.bincount(ids).argmax())
                if k > 0 and np.mean(ids == k) > 0.6:
                    bi = k - 1           # the same carved area is the same block ("reprint": true prints over it)
        press = t.psum / max(t.n, 1)
        baren = 0.82 + 0.22 * min(press, 1.1)
        op = it.get("opacity", 0.3)
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
        s = int(p.get("size", max(28, min(cv.W, cv.H) // 18)))
        at = p.get("at", "br")
        mg = int(max(cv.W, cv.H) * 0.035)
        if isinstance(at, (list, tuple)):
            x0, y0 = int(at[0]), int(at[1])
        else:
            x0 = mg if "l" in at else cv.W - mg - s
            y0 = mg if "t" in at else cv.H - mg - s
        x0, y0 = max(0, min(cv.W - s, x0)), max(0, min(cv.H - s, y0))
        text = str(p.get("text", "T"))
        im = Image.new("L", (s, s), 0)
        d = ImageDraw.Draw(im)
        rr = max(2, s // 10)
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=rr, fill=255)
        f = _font(int(s * (0.72 if len(text) == 1 else 0.82 / math.sqrt(len(text)))))
        if len(text) <= 2:
            bb = d.textbbox((0, 0), text, font=f)
            d.text(((s - (bb[2] - bb[0])) / 2 - bb[0], (s - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=0)
        else:  # two columns, read top-right first like a Japanese seal
            half = (len(text) + 1) // 2
            for ci, col in enumerate((text[:half], text[half:])):
                for k, ch in enumerate(col):
                    bb = d.textbbox((0, 0), ch, font=f)
                    cx = s * (0.72 if ci == 0 else 0.28) - (bb[2] - bb[0]) / 2 - bb[0]
                    cy = s * (k + 0.5) / max(len(col), 1) - (bb[3] - bb[1]) / 2 - bb[1]
                    d.text((cx, cy), ch, font=f, fill=0)
        shape = np.array(im, np.float32) / 255
        rng = np.random.default_rng(len(text) * 7 + s)
        # a worn seal: chipped border and an uneven stamp
        chip = gaussian_filter(rng.random((s, s)).astype(np.float32), 1.0)
        shape = np.clip(shape - (chip > 0.62) * 0.8 * (gaussian_filter(shape, 1.5) < 0.98), 0, 1)
        shape = gaussian_filter(shape, 0.5)
        coarse = cv.meta.get("support") == "coarse"
        x = self._impression(cv, shape, y0, y0 + s, x0, x0 + s, 3, -5, 1.7, 0.12, 0.35, coarse, rng, pool=0.2)
        self._print(cv, x, y0, y0 + s, x0, x0 + s, (0, 0), hx(p.get("color", "#b8322a")), 0.55)


class _Nothing:
    """Prints cannot be blended or smudged: the colours lie where the blocks put them."""
    size, step, speedfx = 1.0, 1.0, 0.0

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        pass
