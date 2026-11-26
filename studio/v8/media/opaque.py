"""The opaque water media: gouache and egg tempera.

Gouache (gum arabic, chalk-loaded pigment): mixed in place like oil, but it covers what is beneath
almost completely (light over dark works), dries fast to a flat matte field, shifts in value as it
dries (darks dry lighter, lights dry a little darker) and re-dissolves: a wet stroke over dry paint
lifts some of it into the brush and the stroke goes muddy. Diluted it behaves like a streaky wash;
starved it drags into dry-brush.

Egg tempera (egg yolk and water on gesso): dries the moment it touches the panel, so nothing blends
wet. Every stroke is a thin Kubelka-Munk film over what is already there; tone is built by many small
parallel hatched strokes and thin layers (a light flesh over a green verdaccio lets the green show
through as cool shadow). Crisp edges, satin surface. On a gold ground (or where the gilding tool lays
leaf) the support reads as metal: leaf squares, burnish, punchwork.

Both keep cv.col as the apparent colour. Extra state:
  gouache: wet (water in the paint, 0..1), thick (paint body, 0..1)
  tempera: gold (visible gold leaf, 0..1), burnish (0..1), punch (punch dimples, 0..1),
           film (accumulated paint thickness, for the satin relief of the hatching), sheen (0..1)
"""
import math
import numpy as np
from scipy.ndimage import gaussian_filter, zoom, distance_transform_edt, sobel
from PIL import Image, ImageDraw
from .base import Medium, kmix, hx, noise_field, pigment_from_hex, km_layer

BINDER = {"gouache": "gum arabic", "tempera": "egg tempera", "fresco": "fresco"}


def binder_palette(binder="egg tempera", names=None):
    """Historical pigments as hex colours in one binder, from the Pigments Checker FORS masstones in
    studio/pigments.json ("masstone_by_binder"; docs/media-data.md). The HUE is measured; lightness and chroma
    come from a relative scale normalised by hand (lamp black 0.03, titanium white 0.90), so treat value and
    chroma as approximate and judge them on the canvas."""
    from .base import load_pigments
    out = {}
    for p in load_pigments():
        for name, bd in (p.get("masstone_by_binder") or {}).items():
            if binder in bd and (names is None or name in names):
                out[name] = "#%02x%02x%02x" % tuple(int(round(min(max(v, 0), 1) * 255)) for v in bd[binder]["srgb"])
    return out


GOLD = hx("#c9a24a")
BOLE = hx("#8a4a2e")   # by eye: Armenian bole, the red clay under water gilding


def _lum(c):
    c = np.asarray(c, np.float32)
    return c[..., 0] * 0.3 + c[..., 1] * 0.59 + c[..., 2] * 0.11


def _norm(a):
    return (a - a.min()) / (a.max() - a.min() + 1e-6)


def _region(reg, W, H, feather=1.0):
    """The same region shapes as the studio's intentions (canvas, rect, ellipse, poly)."""
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
    return gaussian_filter(np.array(m, np.float32) / 255, feather)


def _patch(cv, x, y, R):
    x0, x1 = max(0, int(x) - R), min(cv.W, int(x) + R + 1)
    y0, y1 = max(0, int(y) - R), min(cv.H, int(y) + R + 1)
    return x0, x1, y0, y1


def _uv(x0, x1, y0, y1, x, y, ang):
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xx - x, yy - y
    ca, sa = math.cos(ang), math.sin(ang)
    return dx * ca + dy * sa, -dx * sa + dy * ca


# =====================================================================================  GOUACHE
class GouacheBrush:
    """Synthetic round/flat, dry-brush or liner loaded with gouache. Within one stroke a pixel is
    covered once (the stroke's own coverage is remembered), so overlapping dabs of one stroke make a
    flat even field rather than a pile of stamps."""

    def __init__(self, kind, size, color, rng, water=0.3, load=1.0, pickup=0.5, react=0.55, wetmix=0.45):
        self.kind, self.size, self.rng = kind, size, rng
        self.color = np.asarray(color, np.float32).copy()
        self.water = float(np.clip(water, 0, 1))
        self.paint = load
        self.load0 = max(load, 0.1)
        self.pickup, self.react, self.wetmix = pickup, react, wetmix
        k = max(5, int(size / 1.2))
        if kind == "dry":
            self.bristles = (rng.random(k) < 0.6) * np.clip(rng.normal(1, 0.25, k), 0.3, 1.2)
        else:
            self.bristles = np.clip(rng.normal(1.0, 0.08 + 0.1 * self.water, k), 0.7, 1.1)
        self.bristles = gaussian_filter(self.bristles.astype(np.float32), 0.6)
        # creamy gouache covers; diluted gouache turns into a streaky semi-transparent wash
        self.cover = float(np.clip(0.995 - 1.1 * max(self.water - 0.15, 0) ** 1.5, 0.2, 0.995))
        self.cov = None
        self.flick = None

    def mask(self, r, u, v):
        k = len(self.bristles)
        bi = np.clip(((v / max(r, 1e-3) + 1) / 2 * k).astype(int), 0, k - 1)
        br = self.bristles[bi]
        if self.kind == "dry":   # bristles skip and catch as the stroke travels: broken along its length too
            f = gaussian_filter(self.rng.random(k).astype(np.float32), 0.8)
            f = (f - f.min()) / (f.max() - f.min() + 1e-6)
            self.flick = f if self.flick is None else self.flick * 0.9 + f * 0.1
            br = br * np.clip((self.flick[bi] - 0.2) * 2.5, 0, 1)
        if self.kind == "flat" or (self.kind == "dry" and self.size > 8):
            # a worn synthetic flat: square-ish but with rounded corners (superellipse), not a stamp
            a = r * 0.3 + 0.6
            q = (np.abs(u) / a) ** 4 + (np.abs(v) / (r + 0.5)) ** 4
            m = np.clip((1 - q) * min(a, r) * 0.9, 0, 1)
            if self.kind == "flat":   # creamy paint fills between the bristles; diluted paint streaks
                br = 1 - (1 - br) * float(np.clip(2.5 * self.water, 0.2, 1.0))
            return (m * br).astype(np.float32)
        d = np.sqrt(u * u + v * v)
        m = np.clip(r + 0.6 - d, 0, 1)
        return (m * (0.88 + 0.12 * br) if self.kind != "dry" else m * br).astype(np.float32)

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        r = max(0.6, self.size / 2 * rscale)
        x0, x1, y0, y1 = _patch(cv, x, y, int(math.ceil(r)) + 2)
        if x0 >= x1 or y0 >= y1:
            return
        if self.cov is None:
            self.cov = np.zeros((cv.H, cv.W), np.float32)
        u, v = _uv(x0, x1, y0, y1, x, y, ang)
        m = self.mask(r, u, v) * min(1.0, 0.6 + press * 0.8)
        if cv.clip is not None:
            m = m * cv.clip[y0:y1, x0:x1]
        tex = cv.tex[y0:y1, x0:x1]
        # a starved or fast brush skips over the tooth: dry-brush
        eff = self.paint - getattr(self, "speedfx", 0.0) * (1.0 - 0.5 * self.water)
        if self.kind == "dry":
            eff = 0.32 + 0.2 * min(press, 1.0) - getattr(self, "speedfx", 0.0) * 0.5
        if self.kind != "blend" and eff < 0.6:
            thr = min(1.0, (0.6 - eff) / 0.6)
            m = m * np.clip((tex - thr * 0.9) * 6, 0, 1)
        cov = self.cov[y0:y1, x0:x1]
        delta = np.maximum(m - cov, 0)
        if delta.max() <= 0.01:
            return
        c = cv.col[y0:y1, x0:x1]
        w = cv.wet[y0:y1, x0:x1]
        th = cv.thick[y0:y1, x0:x1]
        step = getattr(self, "step", 1.0)
        ms = m.sum() + 1e-6
        # mobile paint under the brush: wet paint, and dry paint the brush's water re-dissolves
        mob = np.clip(w * 0.7 + (1 - w) * th * self.react * (0.2 + 1.3 * self.water), 0, 1)
        if self.kind == "blend":   # a clean damp brush: softens and lifts, adds nothing
            sig = max(0.8, r / 2.2)
            bl = np.stack([gaussian_filter(c[..., i], sig) for i in range(3)], -1)
            a = np.clip(m * (0.2 + 0.8 * mob) * 0.8, 0, 1)[..., None]
            cv.col[y0:y1, x0:x1] = c * (1 - a) + bl * a
            cv.wet[y0:y1, x0:x1] = np.clip(w + m * 0.3, 0, 1)
            return
        wp = m * mob * (1 - cov)
        sw = float(wp.sum())
        if sw > 1e-3:   # the brush gets dirty: it lifts wet paint and re-dissolved dry paint (not paper)
            under = (c * wp[..., None]).sum((0, 1)) / sw
            pk = min(0.3, self.pickup * (sw / ms) * step / max(self.size * 0.8, 1.0))
            self.color = self.color * (1 - pk) + under * pk
        wmob = np.clip(w * 0.7 * self.wetmix + (mob - w * 0.7).clip(0) * 0.35 * self.wetmix, 0, 0.6)
        dep = kmix(self.color[None, None, :], c, wmob[..., None])
        cover = self.cover * min(1.0, self.paint * 1.5 + 0.35)
        t = np.clip(cover * delta / (1 - cover * cov + 1e-3), 0, 1)[..., None]
        cv.col[y0:y1, x0:x1] = c * (1 - t) + dep * t     # opaque paint hides what it covers (area, not mixing)
        cv.wet[y0:y1, x0:x1] = np.clip(w + delta * (0.45 + 0.55 * self.water), 0, 1)
        cv.thick[y0:y1, x0:x1] = np.clip(th + delta * (1.0 - 0.6 * self.water) * cover, 0, 1)
        self.cov[y0:y1, x0:x1] = np.maximum(cov, m)
        # gouache is thinner than oil: a load lasts a shorter distance (longer when diluted)
        self.paint = max(0.0, self.paint - step / (max(self.size, 2) * (40 + 40 * self.water) * self.load0))


class Gouache(Medium):
    name = "gouache"
    arrays = ("col", "wet", "thick")
    supports = {"illustration_board": "smooth rigid board: crisp flat fields, almost no tooth",
                "watercolour_paper": "cold-press watercolour paper: a visible tooth that dry-brush catches",
                "toned_paper": "mid-toned drawing paper (warm grey unless a darker ground is given): build lights on top"}
    tools = {"round": "synthetic round: shapes and lines, crisp opaque edges",
             "flat": "synthetic flat: flat even fields, straight crisp edges, faint streaks when diluted",
             "dry": "dry-brush: little paint, scratchy broken marks that catch the tooth",
             "liner": "small pointed round for fine lines and light accents"}
    finishes = {"dry": "let all paint dry fully (applies the drying shift: darks lighter, lights slightly darker)",
                "protect": "a light protective matte spray; no varnish (gouache is framed under glass)"}

    BODY = 0.5    # paint-body mottle, set from flat gouache crops (docs/calibration/gouache.md)
    SHIFT = 0.1   # value shift on drying, ~3-5% at the extremes [MEDIA.md S18]

    def texture(self, h, w, support):
        if support == "watercolour_paper":
            a = noise_field(h, w, 2.2, 11); b = noise_field(h, w, 0.7, 12); c = noise_field(h, w, 7, 13)
            return np.clip(0.55 * a + 0.25 * b + 0.2 * c, 0, 1).astype(np.float32)
        if support == "toned_paper":
            a = noise_field(h, w, 1.0, 21); b = noise_field(h, w, 3.0, 22)
            return np.clip(0.6 * a + 0.4 * b, 0, 1).astype(np.float32)
        return (0.5 + 0.35 * (noise_field(h, w, 0.8, 7) - 0.5)).astype(np.float32)

    def init_state(self, cv, ground):
        cv.wet = np.zeros((cv.H, cv.W), np.float32)
        cv.thick = np.zeros((cv.H, cv.W), np.float32)
        if cv.meta.get("support") == "toned_paper" and _lum(hx(ground)) > 0.7:
            cv.col = np.clip(cv.col - hx(ground) + hx("#7d7468"), 0, 1).astype(np.float32)

    def make_tool(self, it, size, color, rng):
        kind = it.get("brush", "round")
        kind = {"filbert": "round", "fan": "dry", "dry_brush": "dry", "detail_round": "liner",
                "knife": "flat", "smudge": "blend"}.get(kind, kind)
        if kind not in ("round", "flat", "dry", "liner", "blend"):
            kind = "round"
        load = it.get("load", 1.0) * rng.uniform(0.9, 1.08)
        if kind == "liner":
            b = GouacheBrush("round", size, color, rng, water=it.get("water", 0.4), load=load * 1.6,
                             pickup=0.25, react=it.get("react", 0.4))
            b.liner = True
            return b
        if kind == "dry":
            return GouacheBrush("dry", size, color, rng, water=it.get("water", 0.03), load=load * 0.6,
                                pickup=0.1, react=0.05)
        return GouacheBrush(kind, size, color, rng, water=it.get("water", 0.25), load=load,
                            pickup=it.get("pickup", 0.4), react=it.get("react", 0.4), wetmix=it.get("wetmix", 0.45))

    def glaze(self, cv, mask, col, op):
        """A wash of diluted gouache: semi-opaque (more body than watercolour), and its water
        re-dissolves dry paint under it a little, softening what it crosses."""
        K, S = pigment_from_hex(col, opacity=0.55)
        if getattr(self, "_wkey", None) != (cv.H, cv.W):
            self._wkey, self._wn = (cv.H, cv.W), noise_field(cv.H, cv.W, 14, 31)
        uneven = 0.85 + 0.3 * self._wn + 0.12 * (cv.tex - 0.5)   # a wash is never perfectly even
        cv.col = km_layer(cv.col, K, S, mask * op * 2.2 * uneven)
        lift = np.clip(mask * op * cv.thick * (1 - cv.wet) * 0.35, 0, 1)[..., None]
        if lift.max() > 0.01:
            bl = np.stack([gaussian_filter(cv.col[..., i], 1.6) for i in range(3)], -1)
            cv.col = (cv.col * (1 - lift) + bl * lift).astype(np.float32)
        cv.wet = np.clip(cv.wet + mask * min(1.0, op * 1.5), 0, 1)
        cv.thick = np.clip(cv.thick + mask * op * 0.5, 0, 1)

    def _dry_by(self, cv, keep):
        """Water leaves; where paint dries its value shifts toward the middle (darks lighter,
        lights darker) and it turns a touch chalkier."""
        dw = cv.wet * (1 - keep) * np.clip(cv.thick * 1.5, 0, 1)
        L = _lum(cv.col)
        cv.col = np.clip(cv.col + (self.SHIFT * dw * (0.45 - L))[..., None], 0, 1).astype(np.float32)
        cv.wet = (cv.wet * keep).astype(np.float32)

    def episode_end(self, cv):
        keep = {"watercolour_paper": 0.25, "toned_paper": 0.3}.get(cv.meta.get("support"), 0.35)
        self._dry_by(cv, keep)

    def dry(self, cv, amount):
        self._dry_by(cv, 1 - float(np.clip(amount, 0, 1)))

    def render(self, cv):
        cover = np.clip(cv.thick * 1.6, 0, 1)
        tooth = 1 + 0.07 * (cv.tex - 0.5) * (1 - 0.85 * cover)
        body = gaussian_filter(cv.thick, 1.0)
        gy, gx = np.gradient(body)
        relief = 1 + np.clip(-gx * 0.5 - gy * 0.7, -0.03, 0.03)   # paint has a little body, no shine
        if getattr(self, "_bkey", None) != (cv.H, cv.W):   # uneven pigment/chalk density of the dried body
            self._bkey = (cv.H, cv.W)
            self._body = (0.6 * noise_field(cv.H, cv.W, 1.2, 41) + 0.4 * noise_field(cv.H, cv.W, 4.0, 42) - 0.5).astype(np.float32)
        body_n = 1 + self.BODY * self._body * cover
        img = cv.col * (tooth * relief * body_n)[..., None]
        # matte: diffuse surface scatter lifts the deepest darks a touch; no specular at all
        img = img + 0.025 * (1 - _lum(img))[..., None] ** 3
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

    # ---------------------------------------------------------------- revision
    def _paper(self, cv):
        g = hx(cv.meta.get("ground", "#f2efe6"))
        return hx("#7d7468") if cv.meta.get("support") == "toned_paper" and _lum(g) > 0.7 else g

    def revise(self, cv, op, mask, it, felt, rng, core):
        """Gouache re-dissolves: wipe lifts paint with a damp brush or sponge (some colour stays in the paper),
        scrape takes dry paint back to the paper with a blade, catching the tooth unevenly; paintout is the
        core's default (gouache covers, so the surrounding colour simply goes over). Amounts are eye."""
        if op not in ("wipe", "scrape"):
            return NotImplemented
        st = float(it.get("strength", 0.7))
        mot = gaussian_filter(rng.random((cv.H, cv.W)).astype(np.float32), 2.5)
        mot = (mot - mot.min()) / (mot.max() - mot.min() + 1e-6)
        if op == "wipe":
            amt = np.clip(mask * st * (0.45 + 0.35 * mot), 0, 0.9)
            cv.wet = np.maximum(cv.wet, mask * 0.5).astype(np.float32)
        else:
            amt = np.clip(mask * st * (0.5 + 0.5 * cv.tex) * (0.7 + 0.3 * mot), 0, 0.95)
        cv.col = (cv.col * (1 - amt[..., None]) + self._paper(cv) * amt[..., None]).astype(np.float32)
        cv.thick = (cv.thick * (1 - amt)).astype(np.float32)
        return True

    def finish_check(self, cv):
        ops = [f["op"] for f in cv.meta.get("finishes", [])]
        lines, flags = [f"gouache: wet {float((cv.wet > 0.05).mean()):.0%}; " + (", ".join(ops) or "no finishing steps")], []
        if float(cv.wet.max()) > 0.05:
            flags.append("gouache still wet: finish dry applies the drying shift (FINISHING.md)")
        return lines, flags

    def finish(self, cv, op, params):
        if op == "dry":
            self._dry_by(cv, 0.0)
        elif op == "protect":
            self._dry_by(cv, 0.0)
            a = float(params.get("amount", 0.5))
            L = _lum(cv.col)
            cv.col = np.clip(cv.col * (1 - 0.03 * a * (1 - L))[..., None], 0, 1).astype(np.float32)
        else:
            super().finish(cv, op, params)


# =====================================================================================  EGG TEMPERA
def tempera_line(cv, x, y, a, L, hw, dx, K, S, hide, rng, tex_break=0.0):
    """One short hatched stroke: a thin film line from (x, y) along angle a, length L, half width hw,
    blunt where the brush lands and tapering where it flicks off. Dries instantly."""
    ca, sa = math.cos(a), math.sin(a)
    R = int(max(L, 2) / 2 + hw + 2)
    cx, cy = x + ca * L / 2, y + sa * L / 2
    x0, x1, y0, y1 = _patch(cv, cx, cy, R)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    px, py = xx - x, yy - y
    t = np.clip((px * ca + py * sa) / max(L, 1e-3), 0, 1)
    dist = np.hypot(px - t * ca * L, py - t * sa * L)
    prof = np.minimum(1.0, 0.45 + t / 0.12 * 0.55) * np.clip(1 - (t - 0.55) / 0.45, 0, 1) ** 0.6
    m = np.clip(hw * (0.35 + 0.65 * prof) + 0.5 - dist, 0, 1) * (0.55 + 0.45 * prof)
    if cv.clip is not None:
        m = m * cv.clip[y0:y1, x0:x1]
    if tex_break > 0:
        m = m * np.clip((cv.tex[y0:y1, x0:x1] - tex_break * 0.9) * 6, 0, 1)
    if m.max() <= 0.02:
        return
    th = dx * m
    cv.col[y0:y1, x0:x1] = km_layer(cv.col[y0:y1, x0:x1], K, S, th)
    cv.gold[y0:y1, x0:x1] *= np.exp(-hide * th)
    cv.film[y0:y1, x0:x1] += th


def _tempera_pigment(color, opacity=None):
    c = np.asarray(color, np.float32)
    # light mixes carry lead white and cover; dark earths and glazes are translucent
    op = opacity if opacity is not None else float(np.clip(0.22 + 0.5 * _lum(c) ** 1.4, 0.15, 0.72))
    K, S = pigment_from_hex(c, opacity=op)
    return K, S, op


class TemperaHatch:
    # angle scatter of the lines (radians): per line and per stroke of the hand; lowers the orientation
    # coherence of a dense hatched field toward the flesh references (docs/calibration/tempera.md)
    JITTER, TILT = 0.08, 0.2
    """A small fine round making short parallel strokes. The path is the hand's travel across the
    passage; every few pixels of travel it lays one short line across it (hatch_angle, default 75
    degrees to the travel). size = the length of each hatched stroke."""

    def __init__(self, size, color, rng, film=0.55, angle=75.0, cross=False, width=None, sample=False, opacity=None,
                 hand=0.5, hand_angle=-60.0):
        self.size, self.rng = size, rng
        self.color = np.asarray(color, np.float32).copy()
        self.K, self.S, op = _tempera_pigment(self.color, opacity)
        self.opacity = opacity
        self.hide = 0.8 + 2.0 * op
        self.film, self.off, self.cross, self.sample = film, math.radians(angle), cross, sample
        self.hw = (width if width else max(1.3, size * 0.09)) / 2
        self.travel = 1e9
        self.n = 0
        self.dir = None
        # a painter's hand has its own natural hatching slant; lines lean toward it (axial average)
        self.hand, self.hand_a = float(np.clip(hand, 0, 1)), math.radians(hand_angle)
        self.tilt = float(rng.normal(0, self.TILT))   # each stroke of the hand sets the lines at a slightly new angle

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        self.travel += getattr(self, "step", 0.0)
        fx = getattr(self, "speedfx", 0.0)
        sp = self.hw * 2 * (1.35 + 1.2 * (1 - min(press, 1.0))) * (1 + 1.5 * fx)
        if self.travel < sp:
            return
        self.travel = 0.0
        rng = self.rng
        L = self.size * rscale * rng.uniform(0.8, 1.15) * (1 + 0.5 * fx)
        # the hand keeps the hatching angle steady while it travels; it only slowly follows the path
        cvec = (math.cos(ang), math.sin(ang))
        if self.dir is None:
            self.dir = cvec
        else:
            k = 0.12
            dx_, dy_ = self.dir[0] * (1 - k) + cvec[0] * k, self.dir[1] * (1 - k) + cvec[1] * k
            n_ = math.hypot(dx_, dy_) + 1e-9
            self.dir = (dx_ / n_, dy_ / n_)
        a = math.atan2(self.dir[1], self.dir[0]) + self.off
        if self.hand > 0:
            h = self.hand
            vx = (1 - h) * math.cos(2 * a) + h * math.cos(2 * self.hand_a)
            vy = (1 - h) * math.sin(2 * a) + h * math.sin(2 * self.hand_a)
            a = math.atan2(vy, vx) / 2
        a += self.tilt + rng.normal(0, self.JITTER + 0.3 * fx)
        if self.cross and self.n % 2:
            a += math.radians(55)
        self.n += 1
        # the line straddles the travel path
        sx, sy = x - math.cos(a) * L / 2 + rng.normal(0, 0.4), y - math.sin(a) * L / 2 + rng.normal(0, 0.4)
        K, S, hide = self.K, self.S, self.hide
        if self.sample:   # "blend" in tempera: hatch the in-between tone sampled from both sides
            R = int(L)
            x0, x1, y0, y1 = _patch(cv, x, y, R)
            if x0 >= x1 or y0 >= y1:
                return
            c = cv.col[y0:y1, x0:x1].reshape(-1, 3)
            col = np.clip(c.mean(0) + rng.normal(0, 0.01, 3), 0, 1)
            K, S, op = _tempera_pigment(col, self.opacity)
            hide = 0.8 + 2.0 * op
        tempera_line(cv, sx, sy, a, L, self.hw * (0.7 + 0.3 * min(press, 1.0)), self.film * min(1.0, 0.3 + press * 0.8),
                     K, S, hide, rng, tex_break=min(0.6, fx * 0.8))


class TemperaBrush:
    """Small soft round (or liner) used nearly dry: a continuous thin film with crisp edges. Each
    pixel takes the stroke's film once; tone builds only by repetition."""

    def __init__(self, kind, size, color, rng, film=0.55, opacity=None, gild_burnish=0.75):
        self.kind, self.size, self.rng = kind, size, rng
        self.color = np.asarray(color, np.float32).copy()
        self.K, self.S, op = _tempera_pigment(self.color, opacity)
        self.hide = 0.8 + 2.0 * op
        self.film, self.gb = film, gild_burnish
        self.paint = 1.0
        self.cov = None

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        r = max(0.5, self.size / 2 * rscale)
        x0, x1, y0, y1 = _patch(cv, x, y, int(math.ceil(r)) + 2)
        if x0 >= x1 or y0 >= y1:
            return
        if self.cov is None:
            self.cov = np.zeros((cv.H, cv.W), np.float32)
        u, v = _uv(x0, x1, y0, y1, x, y, ang)
        d = np.sqrt(u * u + v * v)
        if self.kind == "gild":
            r = max(1.0, self.size / 2)
        m = np.clip(r + 0.5 - d, 0, 1)
        if self.kind != "gild":
            m = m * min(1.0, 0.2 + press * 0.9)
        if cv.clip is not None:
            m = m * cv.clip[y0:y1, x0:x1]
        tex = cv.tex[y0:y1, x0:x1]
        step = getattr(self, "step", 1.0)
        if self.kind == "gild":
            # leaf laid over bole: opaque, slightly ragged where the leaf tears
            m = np.clip((m - 0.35 * (1 - tex) * (m < 1)) * 1.6, 0, 1)
            cov = self.cov[y0:y1, x0:x1]
            delta = np.maximum(m - cov, 0)
            if delta.max() <= 0.01:
                return
            c = cv.col[y0:y1, x0:x1]
            t = np.clip(delta / (1 - cov + 1e-3), 0, 1)[..., None]
            cv.col[y0:y1, x0:x1] = c * (1 - t) + GOLD * t
            cv.gold[y0:y1, x0:x1] = np.maximum(cv.gold[y0:y1, x0:x1], m)
            cv.leaf[y0:y1, x0:x1] = np.maximum(cv.leaf[y0:y1, x0:x1], m)
            cv.burnish[y0:y1, x0:x1] = np.maximum(cv.burnish[y0:y1, x0:x1], m * self.gb)
            cv.film[y0:y1, x0:x1] *= (1 - m)
            self.cov[y0:y1, x0:x1] = np.maximum(cov, m)
            return
        # a nearly dry brush: as it empties or moves fast the film breaks on the (smooth) gesso
        eff = self.paint - getattr(self, "speedfx", 0.0)
        if eff < 0.5:
            m = m * np.clip((tex - (0.5 - eff) * 1.6) * 6, 0, 1)
        cov = self.cov[y0:y1, x0:x1]
        delta = np.maximum(m - cov, 0)
        if delta.max() <= 0.01:
            return
        th = self.film * delta
        cv.col[y0:y1, x0:x1] = km_layer(cv.col[y0:y1, x0:x1], self.K, self.S, th)
        cv.gold[y0:y1, x0:x1] *= np.exp(-self.hide * th)
        cv.film[y0:y1, x0:x1] += th
        self.cov[y0:y1, x0:x1] = np.maximum(cov, m)
        self.paint = max(0.0, self.paint - step / (max(self.size, 2) * 60))


class Tempera(Medium):
    name = "tempera"
    # gold texture, set from the gold-ground references (docs/calibration/tempera.md): with `finish age` the
    # flat-field std L* of the gold is 5.2 at 4 px/mm (references 5.3, IQR 5.0-6.4, n=3); new leaf alone ~1.5
    LEAF_GRAIN, CRACK_DARK = 3.0, 0.8
    arrays = ("col", "gold", "leaf", "burnish", "punch", "film", "sheen", "age")
    supports = {"gesso_panel": "wooden panel with gesso sanded smooth: brilliant white, absorbent, no tooth",
                "gold_ground": "panel water-gilt all over (gold leaf on bole, burnished): paint over it, or leave it as metal"}
    tools = {"hatch": "small fine round making many short parallel strokes across the path (size = stroke length); tone builds by passes",
             "round": "small soft round used nearly dry: a thin crisp-edged film",
             "liner": "fine pointed round for contours, hair and gold-coloured details",
             "gilding": "lays gold leaf over bole along the stroke (water gilding, burnished)"}
    finishes = {"hatch-lights": "a final pass of light hatched strokes on the highlights (params: region, color, count, size)",
                "oil-glaze": "a transparent oil glaze (params: color, opacity, region); it sinks the lights below, restore them with hatch-lights",
                "punch": "punchwork in the gold (params: pattern border|stipple|rosette, region, radius, spacing)",
                "burnish": "burnish the gold with the agate (params: region, amount)",
                "sheen": "set the satin sheen of the surface (params: amount, default 0.35); no varnish",
                "age": "the look of a panel centuries old: craquelure in the gesso and gold rubbed through to the red bole (params: amount 0..1, cell in px)"}

    def texture(self, h, w, support):
        n = noise_field(h, w, 0.7, 7)
        # gesso sanded smooth: only faint long sanding marks
        sand = gaussian_filter(np.random.default_rng(9).random((h, w)).astype(np.float32), (0.6, 9))
        return np.clip(0.5 + 0.12 * (n - 0.5) + 0.15 * (_norm(sand) - 0.5), 0, 1).astype(np.float32)

    def init_state(self, cv, ground):
        z = lambda: np.zeros((cv.H, cv.W), np.float32)
        cv.gold, cv.leaf, cv.burnish, cv.punch, cv.film, cv.age = z(), z(), z(), z(), z(), z()
        cv.sheen = np.full((cv.H, cv.W), 0.35, np.float32)
        if cv.meta.get("support") == "gold_ground":
            cv.gold[:] = 1.0
            cv.leaf[:] = 1.0
            cv.burnish[:] = 0.85
            cv.col = np.clip(cv.col - hx(ground) + GOLD, 0, 1).astype(np.float32)

    def make_tool(self, it, size, color, rng):
        kind = it.get("brush", "hatch")
        kind = {"small_round": "round", "detail_round": "liner", "gild": "gilding", "filbert": "round",
                "flat": "round", "stylus": "liner"}.get(kind, kind)
        op = it.get("opacity_paint")
        if kind == "gilding":
            b = TemperaBrush("gild", size, color, rng, gild_burnish=it.get("burnish", 0.75))
            b.cov = None
            return b
        if kind == "round":
            return TemperaBrush("round", size, color, rng, film=it.get("film", 0.55), opacity=op)
        if kind == "liner":
            b = TemperaBrush("round", size, color, rng, film=it.get("film", 0.8), opacity=op)
            b.liner = True
            return b
        if kind == "blend":   # tempera cannot blend wet: transitions are hatched in sampled tones
            return TemperaHatch(max(size * 0.6, 6), color, rng, film=it.get("film", 0.35), angle=it.get("hatch_angle", 75),
                                cross=True, sample=True, opacity=op, hand=it.get("hand", 0.5), hand_angle=it.get("hand_angle", -60))
        return TemperaHatch(size, color, rng, film=it.get("film", 0.55), angle=it.get("hatch_angle", 75),
                            cross=it.get("cross", False), width=it.get("line"), opacity=op,
                            hand=it.get("hand", 0.5), hand_angle=it.get("hand_angle", -60))

    def glaze(self, cv, mask, col, op):
        """A thin translucent layer of tempera (more water, little white): a KM film."""
        K, S = pigment_from_hex(col, opacity=0.15)
        th = mask * op * 1.6
        cv.col = km_layer(cv.col, K, S, th)
        cv.gold *= np.exp(-th * 1.1)
        cv.film += th * 0.3

    # instant drying: nothing happens between episodes
    def episode_end(self, cv):
        pass

    def dry(self, cv, amount):
        pass

    # ------------------------------------------------------------ seeing
    def _env(self, H, W):
        """What burnished gold reflects: a soft room of light and dark (fixed per canvas size)."""
        key = (H, W)
        if getattr(self, "_envkey", None) != key:
            h, w = max(8, H // 8), max(8, W // 8)
            n = gaussian_filter(np.random.default_rng(5).random((h, w)).astype(np.float32), max(h, w) / 10)
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            g = 0.5 * np.sin((xx / w * 1.1 - yy / h * 0.7) * math.pi * 1.2) + 0.5
            e = _norm(0.3 * _norm(n) + 0.7 * g)
            e = zoom(e, (H / h, W / w), order=1)[:H, :W]
            e = np.pad(e, ((0, H - e.shape[0]), (0, W - e.shape[1])), mode="edge")
            # gold leaf squares: seams with a doubled (overlap) strip
            s = max(40, int(min(H, W) / 11))
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            row = (yy // s).astype(int)
            xo = (xx + (row * 0.37 % 1) * s) % s
            yo = yy % s
            seam = np.maximum(np.clip(1.6 - xo, 0, 1), np.clip(1.6 - yo, 0, 1))
            overlap = np.maximum(((xo > 1.6) & (xo < 4.5)), ((yo > 1.6) & (yo < 4.5))).astype(np.float32)
            leaf = noise_field(H, W, 0.6, 17)
            col_ = ((xx + (row * 0.37 % 1) * s) // s).astype(int)
            tile = np.random.default_rng(23).normal(0, 1, (row.max() + 2, col_.max() + 2)).astype(np.float32)
            leaf = (leaf - 0.5) * self.LEAF_GRAIN + 0.5 + 0.4 * tile[row, col_]   # every square of leaf sits at its own slight angle
            # wear of the leaf: fine abrasion and rubbed patches where the red bole shows through
            rub = 0.55 * noise_field(H, W, 1.0, 29) + 0.45 * noise_field(H, W, 7.0, 30)
            rub = (rub - rub.mean()) / (rub.std() + 1e-6)
            self._envkey, self._envv = key, (e.astype(np.float32), seam.astype(np.float32), overlap, leaf, rub.astype(np.float32))
        return self._envv

    def render(self, cv):
        img = cv.col.copy()
        # satin: the hatching has a faint relief that catches the light; oil-glazed areas shine more
        f = gaussian_filter(np.minimum(cv.film, 3) * (1 - cv.gold), 0.7)
        gy, gx = np.gradient(f)
        ld = -gx * 0.6 - gy * 0.8
        img = img * (1 + np.clip(ld * 0.25, -0.025, 0.025))[..., None]
        img = img + (np.clip(ld, 0, 1) * 0.12 * cv.sheen)[..., None]
        img = img * (0.992 + 0.016 * cv.tex)[..., None]
        g = cv.gold
        if g.max() > 0.01:
            e, seam, overlap, leaf, rub = self._env(cv.H, cv.W)
            b = cv.burnish
            contrast = 0.15 + 0.35 * b
            lf = 1 + contrast * (e - 0.5) * 1.2
            metal = GOLD[None, None, :] * lf[..., None]
            hi = np.clip(e - 0.7, 0, 1) * b * 0.9
            metal = metal + hi[..., None] * np.array([0.3, 0.27, 0.12], np.float32)
            grain = (leaf - 0.5) * (0.035 + 0.05 * (1 - b))
            metal = metal * (1 + (grain + overlap * 0.025 - seam * 0.045))[..., None]
            wear = float(cv.meta.get("wear", 0.0))
            if wear > 0:   # aged leaf (finish age): rubbed through to the bole in speckle and soft patches
                w = np.clip((rub - (3.0 - 1.2 * wear)) * 0.8, 0, 0.85)[..., None]
                metal = metal * (1 - w) + BOLE * w
            p = gaussian_filter(cv.punch, 0.6)
            py, px = np.gradient(p)
            metal = metal * (1 - 0.3 * p + np.clip(-px * 1.6 - py * 2.2, -0.5, 0.6))[..., None]
            img = img + g[..., None] * (metal - GOLD)
        if cv.age.max() > 0:   # craquelure: the gesso cracks in a network and the cracks hold dirt
            img = img * (1 - self.CRACK_DARK * cv.age)[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

    # ------------------------------------------------------------ the last stage
    # ---------------------------------------------------------------- revision
    def revise(self, cv, op, mask, it, felt, rng, core):
        """Egg tempera dries the moment it touches the panel: it can be scraped back with a blade to the gesso (or
        the gold), never wiped; painting out is the core's default (hatched film over it). Amounts are eye."""
        if op == "wipe":
            raise SystemExit("tempera can't be wiped: egg tempera dries the moment it touches the panel. "
                             "Scrape it back to the gesso (scrape) or paint it out (paintout).")
        if op != "scrape":
            return NotImplemented
        st = float(it.get("strength", 0.7))
        amt = np.clip(mask * st * (0.6 + 0.4 * cv.tex), 0, 0.97)
        base = np.where((cv.leaf > 0.5)[..., None], GOLD, hx(cv.meta.get("ground", "#f4f0e6"))).astype(np.float32)
        cv.col = (cv.col * (1 - amt[..., None]) + base * amt[..., None]).astype(np.float32)
        cv.film = (cv.film * (1 - amt)).astype(np.float32)
        cv.gold = np.maximum(cv.gold, amt * cv.leaf).astype(np.float32)
        return True

    def finish(self, cv, op, params):
        rng = np.random.default_rng(int(params.get("seed", 3)))
        if op == "hatch-lights":
            self._hatch_lights(cv, params, rng)
        elif op == "oil-glaze":
            col = hx(params.get("color", "#7a2a1a"))
            a = float(params.get("opacity", 0.3))
            mask = _region(params.get("region"), cv.W, cv.H, params.get("feather", 6)) * a
            K, S = pigment_from_hex(col, opacity=0.06)
            L = _lum(cv.col)
            cv.col = km_layer(cv.col, K, S, mask * 2.4)
            # the oil sinks the egg highlights beneath it [S14]
            cv.col = np.clip(cv.col * (1 - 0.12 * mask * L ** 2)[..., None], 0, 1).astype(np.float32)
            cv.sheen = np.clip(cv.sheen + mask * 1.5, 0, 1)
            cv.gold *= np.exp(-mask * 1.5)
        elif op == "burnish":
            reg = params.get("region")
            m = _region(reg, cv.W, cv.H, 2) * cv.leaf if reg else cv.leaf
            cv.burnish = np.maximum(cv.burnish, m * float(params.get("amount", 1.0)))
        elif op == "sheen":
            cv.sheen = np.full((cv.H, cv.W), float(params.get("amount", 0.35)), np.float32)
        elif op == "punch":
            self._punch(cv, params, rng)
        elif op == "age":
            self._age(cv, params, rng)
        else:
            super().finish(cv, op, params)

    def _hatch_lights(self, cv, params, rng):
        mask = _region(params.get("region"), cv.W, cv.H, 2)
        col = hx(params.get("color", "#f3ead6"))
        n = int(params.get("count", 120))
        size = float(params.get("size", 14))
        K, S, op = _tempera_pigment(col, 0.7)
        L = gaussian_filter(_lum(cv.col), 1.5)
        Lb = gaussian_filter(L, size)
        score = np.clip(L - Lb, 0, None) * np.clip(L - np.percentile(L, 45), 0, None) * mask * (1 - cv.gold)
        if score.max() <= 0:
            print("hatch-lights: no lights found in the region")
            return
        p = (score / score.sum()).ravel()
        idx = rng.choice(p.size, size=n, p=p)
        gy, gx = sobel(Lb, 0), sobel(Lb, 1)
        for k in idx:
            y, x = divmod(int(k), cv.W)
            a = math.atan2(gy[y, x], gx[y, x]) if abs(gy[y, x]) + abs(gx[y, x]) > 1e-5 else rng.uniform(0, 6.28)
            nx, ny = -math.sin(a), math.cos(a)
            for j in range(int(rng.integers(3, 7))):   # a small group of parallel strokes
                o = (j - 2) * size * 0.22
                ln = size * rng.uniform(0.7, 1.1)
                # each stroke starts in the light and flicks off toward the shadow (down the gradient)
                tempera_line(cv, x + nx * o, y + ny * o, a + math.pi + rng.normal(0, 0.08), ln, 0.75, 0.4,
                             K, S, 2.2, rng)

    def _punch(self, cv, params, rng):
        reg = params.get("region")
        gl = gaussian_filter(cv.leaf, 2) > 0.5          # where leaf was laid, painted over or not
        gm = gl if not reg else (_region(reg, cv.W, cv.H, 1) > 0.5) & gl
        if gm.sum() < 50:
            print("punch: no gold to punch")
            return
        pattern = params.get("pattern", "border")
        rad = float(params.get("radius", 3.0))
        sp = float(params.get("spacing", rad * 3.2))
        pts = []
        if pattern in ("border", "rosette"):
            # ring punches in rows just inside the edge of the gold (halo rims, frame borders)
            d = distance_transform_edt(gm)
            for off in params.get("rows", [rad * 3, rad * 6]):
                band = np.argwhere(np.abs(d - off) < 0.7)
                pts += self._spread(band, sp, rng)
            if pattern == "rosette":
                band = np.argwhere((d > rad * 10) & (rng.random(gm.shape) < 0.002))
                for y, x in self._spread(band, sp * 6, rng, shuffle=True):
                    pts.append((y, x))
                    for k in range(6):
                        a = k * math.pi / 3
                        pts.append((y + math.sin(a) * rad * 2.6, x + math.cos(a) * rad * 2.6))
        else:  # stipple: a granular field of small dot punches
            band = np.argwhere(gm & (rng.random(gm.shape) < float(params.get("density", 0.01))))
            pts = [tuple(p) for p in band]
            rad = min(rad, 1.4)
        ring = pattern != "stipple"
        R = int(rad + 2)
        for y, x in pts:
            x0, x1, y0, y1 = _patch(cv, x, y, R)
            if x0 >= x1 or y0 >= y1:
                continue
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            dd = np.hypot(xx - x, yy - y)
            if ring:
                m = np.clip(1 - np.abs(dd - rad * 0.65) / (rad * 0.35), 0, 1)
            else:
                m = np.clip(rad + 0.5 - dd, 0, 1) * 0.6
            if cv.gold[min(int(y), cv.H - 1), min(int(x), cv.W - 1)] < 0.4:
                continue   # paint over the leaf here: the punch would not show (punching is done before painting)
            cv.punch[y0:y1, x0:x1] = np.maximum(cv.punch[y0:y1, x0:x1], m)

    def _age(self, cv, params, rng):
        """Craquelure: a network of cracks around irregular cells (the gesso shrinks and splits), drawn as the
        boundaries between the nearest and second-nearest of random seeds, ragged with noise; plus wear of the
        leaf (rendered from cv.meta["wear"])."""
        from scipy.spatial import cKDTree
        amt = float(np.clip(params.get("amount", 1.0), 0, 1))
        cell = float(params.get("cell", 40))
        n = max(8, int(cv.H * cv.W / cell ** 2))
        seeds = rng.random((n, 2)) * [cv.H, cv.W]
        st = 1
        yy, xx = np.mgrid[0:cv.H:st, 0:cv.W:st].astype(np.float32)
        warp = (noise_field(cv.H, cv.W, cell / 3, 51)[::st, ::st] - 0.5) * cell * 0.8
        d, _ = cKDTree(seeds).query(np.stack([yy.ravel() + warp.ravel(), xx.ravel() - warp.ravel()], -1), k=2)
        gap = (d[:, 1] - d[:, 0]).reshape(yy.shape)
        crack = np.clip(1.0 - gap / 2.0 / 0.7, 0, 1)      # about 1 px wide along the cell walls
        crack = crack * np.clip(noise_field(cv.H, cv.W, cell / 2, 52) * 2.2 - 0.4, 0, 1)   # not every cell wall opens
        cv.age = np.maximum(cv.age, (crack * amt).astype(np.float32))
        cv.meta["wear"] = max(float(cv.meta.get("wear", 0.0)), amt)

    @staticmethod
    def _spread(cands, sp, rng, shuffle=False):
        """Keep candidate points at least sp apart (greedy, with a grid of accepted points)."""
        if len(cands) == 0:
            return []
        if shuffle:
            rng.shuffle(cands)
        cell = sp / 1.5
        grid, out = {}, []
        for y, x in cands:
            gy, gx = int(y // cell), int(x // cell)
            ok = True
            for j in range(gy - 2, gy + 3):
                for i in range(gx - 2, gx + 3):
                    q = grid.get((j, i))
                    if q is not None and (q[0] - y) ** 2 + (q[1] - x) ** 2 < sp * sp:
                        ok = False; break
                if not ok:
                    break
            if ok:
                grid[(gy, gx)] = (y, x)
                out.append((float(y), float(x)))
        return out
