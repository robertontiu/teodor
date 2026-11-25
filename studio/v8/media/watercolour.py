"""Watercolour: a simplified Curtis et al. (1997) model, as docs/MEDIA.md "Engine model (watercolour)" describes.

State per pixel (besides `col`, the apparent colour):
  under       (H,W,3) reflectance of the paper with every dried wash composited on it (KM films)
  gK, gS      pigment suspended in the water of the current wash (absorption per channel, scattering)
  dK, dS      pigment of the current wash already settled on the paper (granulated into hollows)
  water       surface water (the shine); > ~0.04 is "wet"
  damp        water absorbed in the paper (0..1): soft edges and back-runs
  mask        masking fluid (reserved paper), removed by `finish unmask`
  gran        granulation tendency of the pigment in the current wash
  stain       how strongly the pigment binds to the fibres (lifting removes 1 - stain)

A film is fully described by K*x and S*x, so pigments mixed in one wash simply add, and a dried wash is
composited over what lies below with base.km_layer: the paper's white is the light and every glaze deepens.

Dabs act at full resolution (hard, ragged edges on dry paper; dry-brush on the paper's peaks). Between episodes
(`episode_end`) and when time passes (`dry`) the wash moves on a bounded crop and, for wide spreads, a
downscaled grid: wet-in-wet bleeding, back-runs where fresh water meets a drying wash, the coffee-ring flow that
darkens a drying edge, settling (granulation) and finally the dried wash is committed as a KM layer.
"""
import math
import numpy as np
from scipy.ndimage import gaussian_filter, binary_dilation, binary_erosion
from PIL import Image
from .base import Medium, hx, pigment_from_hex, km_layer

# --------------------------------------------------------------------------- supports
# absorb/air: how fast surface water sinks in / evaporates per episode; ddecay: damp paper drying;
# sig: wet-in-wet spread (px); gran: how much the paper makes pigment granulate; ring: edge darkening;
# shade: relief shading in the render; slope: how sharply dry-brush picks out peaks; ragged: edge raggedness;
# lift: how well pigment lifts (hot-press lifts best).
SUP = {
    "cold_press": dict(absorb=0.32, air=0.22, ddecay=0.35, sig=5.0, gran=0.6, ring=0.8, shade=0.045,
                       slope=5.0, ragged=0.22, lift=1.0),
    "hot_press": dict(absorb=0.18, air=0.28, ddecay=0.40, sig=6.5, gran=0.25, ring=1.0, shade=0.014,
                      slope=3.0, ragged=0.06, lift=1.3),
    "rough": dict(absorb=0.42, air=0.20, ddecay=0.32, sig=4.0, gran=1.0, ring=0.65, shade=0.075,
                  slope=7.5, ragged=0.42, lift=0.8),
}
MASKCOL = hx("#eadf9e")
WET = 0.04


def _n(a):
    return (a - a.min()) / (a.max() - a.min() + 1e-6)


def _equalize(a):
    r = np.empty(a.size, np.float32)
    r[np.argsort(a, axis=None, kind="stable")] = np.linspace(0, 1, a.size, dtype=np.float32)
    return r.reshape(a.shape)


def _blur(a, sig):
    """Gaussian blur over the first two axes; wide blurs run on a downscaled grid (the coarse fluid grid)."""
    sg = (sig, sig) + (0,) * (a.ndim - 2)
    if sig < 3.0:
        return gaussian_filter(a, sg)
    f = int(min(6, max(2, sig // 2)))
    h, w = a.shape[:2]
    H2, W2 = -(-h // f), -(-w // f)
    pad = ((0, H2 * f - h), (0, W2 * f - w)) + ((0, 0),) * (a.ndim - 2)
    ap = np.pad(a, pad, mode="edge")
    sm = ap.reshape((H2, f, W2 * f) + a.shape[2:]).mean(1).reshape((H2, W2, f) + a.shape[2:]).mean(2)
    sm = gaussian_filter(sm, (sig / f, sig / f) + (0,) * (a.ndim - 2))
    return _up(_up(sm, f, h, 0), f, w, 1)


def _up(a, f, n, axis):
    """Bilinear upsampling by an integer factor along one axis (cell centres aligned), cropped to n."""
    m = a.shape[axis]
    pos = np.clip((np.arange(n, dtype=np.float32) + 0.5) / f - 0.5, 0, m - 1)
    i0 = np.minimum(pos.astype(np.int64), m - 1)
    i1 = np.minimum(i0 + 1, m - 1)
    fr = (pos - i0).astype(np.float32)
    shp = [1] * a.ndim
    shp[axis] = n
    fr = fr.reshape(shp)
    return (np.take(a, i0, axis) * (1 - fr) + np.take(a, i1, axis) * fr).astype(np.float32)


def _normconv(a, R, sig):
    """Average of `a` over the region R only (pigment cannot travel across dry paper)."""
    Rb = _blur(R, sig)
    if a.ndim == 3:
        return _blur(a * R[..., None], sig) / (Rb[..., None] + 1e-4)
    return _blur(a * R, sig) / (Rb + 1e-4)


def _guess_granulation(c):
    r, g, b = c
    if b > r + 0.08 and b >= g:                       # ultramarine, cobalt, cerulean
        return 0.65
    sat = max(c) - min(c)
    if r > b and sat < 0.45 and 0.15 < c.mean() < 0.7:  # earths: siennas, umbers, ochres
        return 0.5
    return 0.22


# --------------------------------------------------------------------------- tools
KINDS = {
    #          water hold  conc  sharp arate spacing
    "round":  (1.00, 30.0, 1.00, 7.0, 0.85, 0.25),
    "flat":   (0.95, 20.0, 1.00, 9.0, 0.88, 0.22),
    "mop":    (1.50, 90.0, 0.85, 2.5, 0.75, 0.25),
    "rigger": (0.90, 90.0, 1.05, 8.0, 0.88, 0.30),
    "dry":    (0.22, 25.0, 1.15, 8.0, 0.60, 0.30),
    "sponge": (0.30, 60.0, 0.90, 6.0, 0.85, 1.1),
    "lift":   (0.15, 40.0, 0.00, 2.5, 0.50, 0.30),
    "soften": (0.20, 40.0, 0.00, 2.0, 0.45, 0.30),
    "water":  (1.20, 60.0, 0.00, 4.0, 0.50, 0.30),
    "mask":   (1.00, 60.0, 0.00, 9.0, 1.00, 0.30),
}
ALIAS = {"liner": "rigger", "filbert": "round", "fan": "dry", "knife": "lift", "smudge": "lift", "blend": "soften",
         "hake": "mop", "wash": "mop", "tissue": "lift", "clean_damp_brush": "water", "masking_fluid": "mask",
         "drybrush": "dry", "dry-brush": "dry"}


class WBrush:
    def __init__(self, med, kind, size, color, rng, it, sup):
        self.med, self.kind, self.size, self.rng, self.sup = med, kind, size, rng, sup
        w, hold, conc, sharp, arate, spacing = KINDS[kind]
        self.W = w * float(it.get("water", it.get("load", 1.0))) * rng.uniform(0.92, 1.05)
        self.hold, self.sharp, self.arate, self.spacing = hold, sharp, arate, spacing
        self.conc = conc * float(it.get("strength", 1.0))
        self.color = np.asarray(color, np.float32)
        K, S = pigment_from_hex(self.color, float(it.get("opacity", 0.1)))
        self.K, self.S = K, float(S.mean())
        self.gran = float(it.get("granulation", _guess_granulation(self.color)))
        self.stain = float(it.get("staining", 0.4))
        self.lift = float(it.get("lift", 0.5))
        self.target = self.color.copy() if it.get("type") == "match" else None
        self.step, self.speedfx = 1.0, 0.0
        self.travel, self.started, self.noop = 0.0, False, False
        if kind == "rigger":
            self.liner = True
        if kind == "sponge":
            self.pores = (noise(64, 64, 1.3, int(rng.integers(1 << 30))) > 0.4).astype(np.float32)
        if kind == "dry":
            k = max(5, int(size / 1.5))
            self.bristles = np.clip(rng.normal(1.0, 0.35, k), 0.0, 1.3).astype(np.float32) * (rng.random(k) > 0.25)

    # the shape of the hairs on the paper (u along the stroke, v across)
    def footprint(self, cv, r, u, v, tex, press):
        k = self.kind
        if k in ("round", "rigger"):
            rr = r * (0.28 + 0.72 * min(press, 1.1) ** 1.2) if k == "round" else r * (0.4 + 0.6 * min(press, 1.0))
            ru = np.where(u < 0, rr * 1.45, rr * 0.95)    # belly ahead, tip trailing: a teardrop
            d = (u / ru) ** 2 + (v / rr) ** 2
        elif k in ("flat", "dry"):
            along = np.abs(u) / (r * 0.32 + 1.0)
            across = np.abs(v) / r
            d = np.maximum(along, across) ** 2
        else:
            d = (u * u + v * v) / max(r * r, 1e-3)
        d = d + (tex - 0.5) * self.sup["ragged"] * 2.0 * (d > 0.5)   # paper breaks the edge
        m = np.clip((1 - d) * self.sharp, 0, 1)
        if k == "dry":
            nb = len(self.bristles)
            bi = np.clip(((v / max(r, 1e-3) + 1) / 2 * nb).astype(int), 0, nb - 1)
            m = m * self.bristles[bi]
        elif k == "sponge":
            oy, ox = self.rng.integers(0, 64, 2)
            yy = ((np.arange(m.shape[0]) + oy) % 64)[:, None]
            xx = ((np.arange(m.shape[1]) + ox) % 64)[None, :]
            m = m * self.pores[yy, xx]
        return m.astype(np.float32)

    def _match_pigment(self, cv, x, y):
        """Match: choose the transparent colour that, laid over what is already on the paper here, gives the
        target (how a watercolourist thinks: you can only go darker)."""
        yi, xi = int(np.clip(y, 0, cv.H - 1)), int(np.clip(x, 0, cv.W - 1))
        y0, y1, x0, x1 = max(0, yi - 2), yi + 3, max(0, xi - 2), xi + 3
        base = km_layer(cv.under[y0:y1, x0:x1], cv.dK[y0:y1, x0:x1], cv.dS[y0:y1, x0:x1, None] + 1e-4, 1.0)
        base = base.reshape(-1, 3).mean(0)
        need = np.clip(-0.5 * np.log(np.clip(self.target, 1e-3, 1) / np.clip(base, 1e-3, 1)), 0, 3.5).astype(np.float32)
        if need.max() < 0.025:
            return False      # already dark enough here: the painter skips it
        K = need if not self.started else 0.5 * self.K + 0.5 * need
        self.K, self.S, self.conc = K, float(0.02 * K.mean() + 1e-3), 1.0
        return True

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        st = getattr(self, "step", 1.0)
        self.W = max(0.0, self.W - st / (max(self.size, 2) * self.hold))
        r = max(0.8, self.size / 2 * rscale)
        self.travel += st
        if self.started and self.travel < self.spacing * r:
            return
        self.travel = 0.0
        if self.target is not None and not self._match_pigment(cv, x, y):
            return
        self.started = True
        if self.noop:
            return
        R = int(math.ceil(r * 1.5)) + 2
        x0, x1 = max(0, int(x) - R), min(cv.W, int(x) + R + 1)
        y0, y1 = max(0, int(y) - R), min(cv.H, int(y) + R + 1)
        if x0 >= x1 or y0 >= y1:
            return
        sl = (slice(y0, y1), slice(x0, x1))
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dx, dy = xx - x, yy - y
        ca, sa = math.cos(ang), math.sin(ang)
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        tex = cv.tex[sl]
        m = self.footprint(cv, r, u, v, tex, press)
        if self.kind not in ("round", "rigger"):
            m = m * min(1.0, 0.35 + 0.65 * press)
        if self.kind != "mask":
            m = m * (1 - cv.mask[sl])
        if cv.clip is not None:
            m = m * cv.clip[sl]
        # a brush running dry, or moving fast, only touches the paper's peaks (dry-brush)
        eff = self.W - 0.4 * getattr(self, "speedfx", 0.0)
        if self.kind == "dry":
            thr = 0.5 + 0.3 * (1 - min(press, 1.0)) + 0.6 * getattr(self, "speedfx", 0.0)
            m = m * np.clip((tex - thr) * self.sup["slope"] * 2 + 0.5, 0, 1)
        elif self.kind not in ("mask", "lift", "soften", "water", "sponge") and eff < 0.35:
            thr = min(0.95, (0.35 - eff) / 0.35)
            m = m * np.clip((tex - thr * 0.9) * self.sup["slope"] + 0.3, 0, 1)
        if m.max() <= 0.01:
            return
        k = self.kind
        if k == "mask":
            cv.mask[sl] = np.maximum(cv.mask[sl], (m > 0.35).astype(np.float32))
        elif k in ("lift", "soften"):
            self._lift(cv, sl, m)
        elif k == "water":
            self._water(cv, sl, m)
        else:
            self._paint(cv, sl, m)
        cv.col[sl] = self.med.appear(cv, sl)

    def _paint(self, cv, sl, m):
        a = np.clip(m * self.arate, 0, 1)
        Wb = self.W
        todry = {"dry": 0.9, "sponge": 0.5}.get(self.kind, float(np.clip(1 - Wb / 0.35, 0, 1)))
        w = cv.water[sl]
        # the dirty brush: it picks up a little of a wet wash it passes through
        ms = m.sum() + 1e-6
        lw = float((w * m).sum() / ms)
        if lw > 0.1 and self.conc > 0:
            loc = (cv.gK[sl] * m[..., None]).sum((0, 1)) / ms / max(self.conc, 1e-3)
            pk = min(0.25, 0.04 * lw * self.step / max(self.size * 0.3, 1.0))
            self.K = self.K * (1 - pk) + loc * pk
        Kt, St = self.K * self.conc, self.S * self.conc
        wetp = float(((w + cv.damp[sl] * 0.6) * (m > 0.05)).sum() / ((m > 0.05).sum() + 1e-6))
        if wetp > 0.2 and self.kind != "dry":   # into wet paper the charge blooms out softly at once
            m = gaussian_filter(m, max(1.0, self.size * 0.25 * min(wetp, 1.2)))
            a = np.clip(m * self.arate, 0, 1)
        if todry < 1:
            aw = (a * (1 - todry))
            g = cv.gK[sl]
            g += (Kt[None, None, :] - g) * aw[..., None]
            cv.gS[sl] += (St - cv.gS[sl]) * aw
            cv.water[sl] = np.maximum(w, m * Wb * (0.8 + 0.2 * m)) + m * 0.03 * Wb
            cv.gran[sl] += (self.gran - cv.gran[sl]) * aw
        if todry > 0:
            ad = a * todry
            d = cv.dK[sl]
            d += np.maximum(Kt[None, None, :] - d, 0) * ad[..., None]
            cv.dS[sl] += np.maximum(St - cv.dS[sl], 0) * ad
        cv.stain[sl] += (self.stain - cv.stain[sl]) * a * 0.5

    def _water(self, cv, sl, m):
        """Clean water: wets the paper; re-dissolves a little dried, non-staining pigment."""
        cv.water[sl] = np.maximum(cv.water[sl], m * self.W)
        f = m * 0.06 * (1 - cv.stain[sl]) * self.sup["lift"]
        self.med.relift(cv, sl, f, into_wash=True)

    def _lift(self, cv, sl, m):
        """A damp clean brush (or tissue): picks the wet wash up easily, dried pigment less, staining least."""
        s = self.lift * (1.6 if self.kind == "lift" else 0.7)
        a = np.clip(m * self.arate * s, 0, 1)
        cv.gK[sl] *= (1 - np.clip(a * 1.2, 0, 0.95))[..., None]
        cv.gS[sl] *= (1 - np.clip(a * 1.2, 0, 0.95))
        fd = np.clip(a * 0.6 * (1 - 0.7 * cv.stain[sl]), 0, 0.9)
        cv.dK[sl] *= (1 - fd)[..., None]
        cv.dS[sl] *= (1 - fd)
        f = np.clip(a * 0.35 * (1 - cv.stain[sl]) * self.sup["lift"], 0, 0.8)
        if self.kind == "soften":  # scrub: soften dried edges as well as lift a little
            u = cv.under[sl]
            b = gaussian_filter(u, (max(1.0, self.size / 6),) * 2 + (0,))
            cv.under[sl] = u + (b - u) * np.clip(m * 0.5, 0, 1)[..., None]
            gb = gaussian_filter(cv.gK[sl], (max(1.0, self.size / 6),) * 2 + (0,))
            cv.gK[sl] += (gb - cv.gK[sl]) * np.clip(m * 0.5, 0, 1)[..., None]
            f = f * 0.4
        self.med.relift(cv, sl, f, into_wash=False)
        cv.water[sl] = np.maximum(cv.water[sl], m * self.W * 0.5)
        cv.damp[sl] = np.maximum(cv.damp[sl], m * 0.3)


def noise(h, w, sigma, seed):
    rng = np.random.default_rng(seed)
    return _n(gaussian_filter(rng.random((h, w)).astype(np.float32), sigma))


# --------------------------------------------------------------------------- the medium
class Watercolour(Medium):
    name = "watercolour"
    arrays = ("col", "under", "gK", "gS", "dK", "dS", "water", "damp", "mask", "gran", "stain")
    supports = {"cold_press": "cold-pressed (NOT) cotton paper, 300 gsm: felt tooth, granulation, soft ragged edges",
                "hot_press": "hot-pressed paper: smooth, paint stays on the surface, crisp edges, lifts well",
                "rough": "rough paper: pronounced tooth, fast absorption, strong granulation and broken dry-brush"}
    tools = {"round": "pointed sable round: belly and tip, hairline to broad by pressure, holds a lot of water",
             "flat": "flat wash brush: broad even bands, straight edges",
             "mop": "big soft mop: lots of water, even washes and wet-in-wet skies",
             "rigger": "long-haired rigger: long thin even lines (branches, rigging)",
             "dry": "dry-brush: little water, splayed hairs catch only the paper's peaks",
             "lift": "damp clean brush or tissue: lifts pigment back up (wet easily, staining colours least)",
             "sponge": "sea sponge: mottled porous texture (foliage, stone)",
             "water": "clean wet brush: wets paper for wet-in-wet; into a drying wash it makes back-runs",
             "mask": "masking fluid: reserves the white paper with hard edges until `finish unmask`"}
    finishes = {"darks": "final darks and crisp accents wet-on-dry where the schema is darkest ('{\"n\":30,\"size\":8}')",
                "lift": "lift soft lights: a region ('{\"region\":{...},\"strength\":0.6}') or the schema's highlights",
                "unmask": "remove the masking fluid, revealing the paper ('{\"soften\":2}' softens its hard edges)",
                "dry": "let the painting dry completely",
                "mount": "no varnish: mounted under a mat and glass (dries the painting; the surface is unchanged)"}

    # ---------------------------------------------------------------- canvas life
    def _sup(self, cv):
        return SUP.get((getattr(cv, "meta", None) or {}).get("support") or "cold_press", SUP["cold_press"])

    def texture(self, h, w, support):
        support = support or "cold_press"
        if support == "hot_press":
            t = 0.75 * noise(h, w, 0.6, 7) + 0.25 * noise(h, w, 2.5, 8)
        elif support == "rough":
            t = 0.2 * noise(h, w, 1.0, 7) + 0.45 * noise(h, w, 3.5, 8) + 0.35 * noise(h, w, 8.0, 9)
        else:  # cold press: felt marks a few px across
            t = 0.35 * noise(h, w, 1.0, 7) + 0.5 * noise(h, w, 2.6, 8) + 0.15 * noise(h, w, 7.0, 9)
        return _equalize(t)

    def init_state(self, cv, ground):
        H, W = cv.H, cv.W
        # the paper is one white: keep only a faint, colourless unevenness of the sheet
        lum = cv.col.mean(-1, keepdims=True)
        cv.col = (hx(ground) * (1 + (lum - lum.mean()) * 0.5)).astype(np.float32)
        cv.under = cv.col.copy()
        for a in ("gK", "dK"):
            setattr(cv, a, np.zeros((H, W, 3), np.float32))
        for a in ("gS", "dS", "water", "damp", "mask", "gran"):
            setattr(cv, a, np.zeros((H, W), np.float32))
        cv.stain = np.full((H, W), 0.4, np.float32)

    def paper(self, cv):
        return hx((getattr(cv, "meta", None) or {}).get("ground", "#f6f3eb"))

    # ---------------------------------------------------------------- appearance
    def appear(self, cv, sl):
        K = cv.gK[sl] + cv.dK[sl]
        S = (cv.gS[sl] + cv.dS[sl])[..., None] + 1e-4
        wf = np.clip(cv.water[sl] * 1.6 + cv.damp[sl] * 0.5, 0, 1)[..., None]
        R = km_layer(cv.under[sl], K * (1 + 0.25 * wf), S, 1.0)   # wet colour looks darker; it dries lighter
        R = R * (1 - 0.05 * wf)
        mk = cv.mask[sl][..., None] * 0.5
        return (R * (1 - mk) + MASKCOL * mk).astype(np.float32)

    def relift(self, cv, sl, f, into_wash):
        """Take a fraction f of the dried pigment off the paper (transparent-film inversion: the film's
        optical density scales with its pigment). into_wash: re-dissolve it into the current wash."""
        if not np.any(f > 1e-4):
            return
        P = self.paper(cv)
        u = cv.under[sl]
        ratio = np.clip(u / P, 1e-3, 1.0)
        f3 = f[..., None]
        if into_wash:
            cv.gK[sl] += -0.5 * np.log(ratio) * f3
            cv.gran[sl] = np.maximum(cv.gran[sl], 0.3 * (f > 1e-3))
        cv.under[sl] = P * ratio ** (1 - f3)

    # ---------------------------------------------------------------- the hand
    def _snap(self, cv):
        if not getattr(cv, "_wc_snap", False):
            cv._w0, cv._d0, cv._wc_snap = cv.water.copy(), cv.damp.copy(), True

    def make_tool(self, it, size, color, rng):
        cv = getattr(self, "_cv", None)
        kind = it.get("brush", "round")
        kind = ALIAS.get(kind, kind)
        if kind not in KINDS:
            kind = "round"
        b = WBrush(self, kind, size, color, rng, it, SUP.get(getattr(self, "_support", "cold_press"), SUP["cold_press"]))
        return _Bound(self, b)

    def glaze(self, cv, mask, col, op):
        """A wash: a flat transparent film of water and pigment laid over the region with a big brush."""
        self._bind(cv)
        m = np.clip(mask, 0, 1) * (1 - cv.mask)
        K, S = pigment_from_hex(np.asarray(col, np.float32), 0.1)
        wet = m > 0.03
        cv.water = np.where(wet, np.maximum(cv.water, 0.9 * np.clip(m * 1.3, 0, 1)), cv.water)
        cv.gK += K[None, None, :] * (m * op)[..., None]
        cv.gS += float(S.mean()) * m * op
        cv.gran += (_guess_granulation(np.asarray(col, np.float32)) - cv.gran) * m
        cv.col = self.appear(cv, (slice(None), slice(None)))

    def _bind(self, cv):
        self._cv = cv
        self._support = (getattr(cv, "meta", None) or {}).get("support") or "cold_press"
        self._snap(cv)

    # ---------------------------------------------------------------- time
    def episode_end(self, cv):
        self._advance(cv, 1.0, episode=True)
        cv._wc_snap = False

    def dry(self, cv, amount):
        amount = float(np.clip(amount, 0, 1))
        if amount <= 0:
            return
        t = 12.0 if amount >= 0.99 else -math.log(1 - amount) * 2.5
        self._advance(cv, t, episode=False, force=amount >= 0.99)

    def _advance(self, cv, t, episode, force=False):
        sp = self._sup(cv)
        pig = cv.gK.sum(-1) + cv.dK.sum(-1)
        act = (cv.water > 0.003) | (cv.damp > 0.01) | (pig > 1e-5)
        if not act.any():
            return
        ys, xs = np.nonzero(act.any(1))[0], np.nonzero(act.any(0))[0]
        pad = 40
        sl = (slice(max(0, ys[0] - pad), min(cv.H, ys[-1] + pad + 1)), slice(max(0, xs[0] - pad), min(cv.W, xs[-1] + pad + 1)))
        W, D = cv.water[sl].copy(), cv.damp[sl].copy()
        g, gS, d, dS = cv.gK[sl].copy(), cv.gS[sl].copy(), cv.dK[sl].copy(), cv.dS[sl].copy()
        tex, free = cv.tex[sl], (cv.mask[sl] < 0.5)
        gran = cv.gran[sl]
        tt = min(t, 1.5)  # flow happens while the wash is wet; long waits do not move pigment further

        # 1. flow: wet-in-wet bleeding inside the wet area (paper that is wet or damp), feathered
        wetR = (((W > WET) | (D > 0.22)) & free).astype(np.float32)
        if wetR.any():
            feather = 0.72 + 0.34 * _n(gaussian_filter(tex, 2.0)) + 0.22 * _n(gaussian_filter(tex, (1.2, 4.0)))
            rec = np.clip(W * 2.0 + D * 0.8, 0, 1) * wetR * feather + 1e-4 * wetR   # where pigment can go
            mob = np.clip(W * 1.1 + D * 0.25, 0, 0.85) * wetR * min(1.0, tt)              # how much leaves
            mob2 = np.clip((W - 0.2) * 1.4, 0, 0.7) * wetR * min(1.0, tt)
            for s, mb in ((sp["sig"], mob), (sp["sig"] * 5.0, mob2)):
                if mb.max() < 0.01:
                    continue
                rb = _blur(rec, s) + 1e-5
                for arr in (g, gS, gran):
                    o = arr * (mb[..., None] if arr.ndim == 3 else mb)
                    inflow = _blur(o, s) / (rb[..., None] if arr.ndim == 3 else rb)
                    arr -= o
                    arr += inflow * (rec[..., None] if arr.ndim == 3 else rec)
            W += (_normconv(W, wetR, sp["sig"]) - W) * 0.5 * wetR * min(1.0, tt)

        # 2. back-runs: fresh water flooding into a wash that is already drying (damp, little surface water)
        if episode and getattr(cv, "_wc_snap", False):
            w0, d0 = cv._w0[sl], cv._d0[sl]
            fresh = np.clip(W - w0, 0, None)
            zone = (d0 > 0.12) & (w0 < 0.35) & ((g.sum(-1) + d.sum(-1)) > 0.03) & free
            src = (fresh > np.maximum(0.3, w0 + 0.22)) & free
            if zone.any() and src.any() and binary_dilation(src, iterations=3)[zone].any():
                reach = _blur(src.astype(np.float32) * np.clip(fresh, 0, 1.5), 16.0) * 2.0
                bn = 0.45 * _n(gaussian_filter(tex, 1.5)) + 0.35 * _n(gaussian_filter(tex, 4.0)) + 0.2 * _n(gaussian_filter(tex, 9.0))
                bloom = (zone | src) & (reach > 0.04 + 0.3 * bn)
                if bloom.any():
                    push = np.where(src, 0.25, 0.6) * bloom
                    rg = g * push[..., None]
                    rd = d * (bloom * 0.45)[..., None]
                    g -= rg; d -= rd
                    gS -= gS * push; dS -= dS * bloom * 0.45
                    front = binary_dilation(bloom, iterations=2) & ~binary_erosion(bloom, iterations=1) & (zone | bloom)
                    fr = front.astype(np.float32)
                    moved = rg + rd
                    g += _blur(moved, 5.0) / (_blur(fr, 5.0)[..., None] + 1e-3) * fr[..., None] * 0.9
                    W = np.where(bloom, np.maximum(W, 0.25), W)

        # 3. evaporation and absorption; the coffee-ring flow carries suspended pigment to pinned edges
        Wb = W.copy()
        k = sp["absorb"] + sp["air"]
        loss = W * (1 - math.exp(-k * t))
        W = W - loss
        D = np.clip(D + loss * sp["absorb"] / k * 0.9, 0, 1) * math.exp(-sp["ddecay"] * t)
        wet = (Wb > WET) & free
        if wet.any():
            frac = np.clip(loss / (Wb + 1e-4), 0, 1)
            drysides = ((~wet) & (D < 0.2)).astype(np.float32)
            band = wet * np.clip(gaussian_filter(drysides, 1.3) * 3.0, 0, 1)
            if band.max() > 0:
                prox = np.clip(gaussian_filter(band, 5.0) * 4.0, 0, 1)
                rs = sp["ring"] * frac * prox * wet * np.clip(Wb * 1.4, 0.25, 1)   # wetter washes ring harder
                tau = g * rs[..., None]
                tS = gS * rs
                g -= tau; gS -= tS
                nb = gaussian_filter(band, 5.0)[..., None] + 1e-4
                g += gaussian_filter(tau, (5.0, 5.0, 0)) / nb * band[..., None]
                gS += gaussian_filter(tS, 5.0) / nb[..., 0] * band

        # 4. settling: pigment leaves the water for the paper, granulating into the hollows when wet
        rate = 1 - np.exp(-t * (0.25 + 1.5 * np.clip(1 - W / 0.45, 0, 1)))
        G = gran * sp["gran"] * np.clip(Wb * 1.5 + 0.2, 0, 1)
        tg = _n(gaussian_filter(tex, 0.7) - gaussian_filter(tex, 4.0))
        gfac = np.clip(1 + G * (0.5 - tg) * 2.2, 0.25, 2.0)
        dep = g * rate[..., None]
        g -= dep; d += dep * gfac[..., None]
        depS = gS * rate
        gS -= depS; dS += depS * gfac

        # 5. dried pixels: the wash becomes a KM film over everything below
        drymask = (W < WET) & (D < 0.1) if not force else np.ones_like(W, bool)
        if drymask.any():
            sel = drymask & (((g + d).sum(-1) > 1e-6))
            if sel.any():
                u = cv.under[sl]
                u[sel] = km_layer(u[sel], (g + d)[sel], ((gS + dS)[sel])[:, None] + 1e-4, 1.0)
                cv.under[sl] = u
            g[drymask] = 0; d[drymask] = 0; gS[drymask] = 0; dS[drymask] = 0
            W[drymask] = 0; D[drymask] = 0; gran[drymask] = 0
        W[W < 0.003] = 0
        cv.water[sl], cv.damp[sl] = W, D
        cv.gK[sl], cv.gS[sl], cv.dK[sl], cv.dS[sl], cv.gran[sl] = g, np.clip(gS, 0, None), np.clip(d, 0, None), np.clip(dS, 0, None), gran
        cv.col[sl] = self.appear(cv, sl)

    # ---------------------------------------------------------------- seeing
    def render(self, cv):
        sp = self._sup(cv)
        t = gaussian_filter(cv.tex, 1.0)
        gy, gx = np.gradient(t)
        shade = 1 + np.clip(-gx * 0.7 - gy * 0.9, -0.2, 0.2) * sp["shade"] * 4
        img = np.clip(cv.col * shade[..., None], 0, 1)
        return Image.fromarray((img * 255).astype(np.uint8))

    # ---------------------------------------------------------------- the last stage
    def finish(self, cv, op, params):
        self._bind(cv)
        if op == "dry":
            self.dry(cv, 1.0)
        elif op == "mount":
            self.dry(cv, 1.0)
            print("watercolour: no varnish; mounted under a mat and glass. The paint surface is unchanged.")
        elif op == "unmask":
            self._unmask(cv, params)
        elif op == "lift":
            self._finish_lift(cv, params)
        elif op == "darks":
            self._finish_darks(cv, params)
        else:
            super().finish(cv, op, params)
        cv._wc_snap = False

    def _unmask(self, cv, params):
        if cv.mask.max() <= 0:
            print("watercolour: no masking fluid on the paper")
            return
        self.dry(cv, 1.0)
        old = cv.mask > 0.5
        cv.mask[:] = 0
        s = float(params.get("soften", 0))
        if s > 0:
            edge = binary_dilation(old, iterations=int(math.ceil(s)) + 1) & ~binary_erosion(old, iterations=int(math.ceil(s)) + 1)
            b = gaussian_filter(cv.under, (s, s, 0))
            w = gaussian_filter(edge.astype(np.float32), s * 0.7)[..., None]
            cv.under = cv.under + (b - cv.under) * np.clip(w * 1.5, 0, 1)
        cv.col = self.appear(cv, (slice(None), slice(None)))

    def _finish_lift(self, cv, params):
        import studio as S
        strength = float(params.get("strength", 0.6))
        soft = float(params.get("soften", 6))
        if params.get("region"):
            m = S.region_mask(params["region"], cv.W, cv.H, feather=soft)
            if m is None:
                m = np.ones((cv.H, cv.W), np.float32)
        elif cv.ref is not None:
            lr = gaussian_filter(cv.ref.mean(-1), 2)
            lc = gaussian_filter(cv.col.mean(-1), 2)
            m = ((lr > np.percentile(lr, 85)) & (lr > lc + 0.06)).astype(np.float32)
            m = gaussian_filter(m, soft)
        else:
            print("watercolour: no region and no schema; nothing lifted")
            return
        self.dry(cv, 1.0)
        f = np.clip(m * strength * (1 - 0.75 * cv.stain) * self._sup(cv)["lift"], 0, 0.95)
        self.relift(cv, (slice(None), slice(None)), f, into_wash=False)
        cv.col = self.appear(cv, (slice(None), slice(None)))
        print(f"watercolour: lifted {float((f > 0.05).mean()) * 100:.1f}% of the paper")

    def _finish_darks(self, cv, params):
        """Final darks: small crisp strokes, wet-on-dry, only where the schema is darkest and the painting is
        not yet dark enough. At most n strokes."""
        import studio as S
        if cv.ref is None:
            print("watercolour: no schema; final darks need one")
            return
        self.dry(cv, 1.0)
        n, size = int(params.get("n", 30)), float(params.get("size", 8))
        lr = gaussian_filter(cv.ref.mean(-1), 1.5)
        lc = gaussian_filter(cv.col.mean(-1), 1.5)
        err = np.where(lr < np.percentile(lr, 12), lc - lr, 0)
        g = max(4, int(size * 2.5))
        H2, W2 = -(-cv.H // g), -(-cv.W // g)
        ep = np.pad(err, ((0, H2 * g - cv.H), (0, W2 * g - cv.W))).reshape(H2, g, W2, g)
        e = ep.max((1, 3))
        order = np.argsort(e, axis=None)[::-1][:n]
        rng = np.random.default_rng(int(params.get("seed", 5)))
        felt = S.Felt({"arousal": 0.25, "tension": 0.25, "care": 0.85})
        gy, gx = np.gradient(gaussian_filter(cv.ref.mean(-1), 3))
        sharp = gaussian_filter(cv.ref, (1, 1, 0))
        k = 0
        for idx in order:
            r, c = divmod(int(idx), W2)
            if e[r, c] < 0.05:
                break
            sub = ep[r, :, c, :]
            iy, ix = np.unravel_index(np.argmax(sub), sub.shape)
            y, x = min(cv.H - 1, r * g + iy), min(cv.W - 1, c * g + ix)
            a = math.atan2(gx[y, x], -gy[y, x]) if abs(gx[y, x]) + abs(gy[y, x]) > 1e-5 else rng.uniform(0, 6.28)
            L = size * rng.uniform(1.5, 3.5)
            ctrl = [[x - math.cos(a) * L / 2, y - math.sin(a) * L / 2], [x, y], [x + math.cos(a) * L / 2, y + math.sin(a) * L / 2]]
            b = self.make_tool({"type": "match", "brush": params.get("brush", "round")}, size, sharp[y, x], rng)
            S.play(cv, b, S.gesture_path(ctrl, felt, rng, size), felt, 0.9, rng)
            k += 1
        self._advance(cv, 1.0, episode=False)
        print(f"watercolour: {k} final darks")


class _Bound:
    """A tool bound to the canvas: the first dab tells the medium which canvas and support it works on."""

    def __init__(self, med, b):
        self.__dict__["_med"], self.__dict__["_b"] = med, b

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        b = self._b
        if getattr(self._med, "_cv", None) is not cv or not getattr(cv, "_wc_snap", False):
            self._med._bind(cv)
            b.sup = SUP.get(self._med._support, SUP["cold_press"])
        b.dab(cv, x, y, ang, press, rscale)

    def __getattr__(self, k):
        return getattr(self._b, k)

    def __setattr__(self, k, v):
        setattr(self._b, k, v)
