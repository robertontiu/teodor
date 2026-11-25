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
  fine        share of fine (colloidal) pigment in the current wash: its edge darkening grows with concentration
  wq          the current wash's wet-to-dry shift (how much darker it looks while wet), per pigment

A film is fully described by K*x and S*x, so pigments mixed in one wash simply add, and a dried wash is
composited over what lies below with base.km_layer: the paper's white is the light and every glaze deepens.

Calibration (docs/calibration/watercolour.md, docs/media-data.md "Watercolour"): every colour is a measured
watercolour pigment (studio/pigments.json, handprint ratings): named with "pigment": "PB29", or the nearest
pigment by hue, chroma and value. Its granulation, staining, transparency, darkest single-wash value and
wet-to-dry shift come from the data; edge darkening grows with concentration only for fine pigments
(Gonzalez-Gutierrez et al. 2019); drying time is scaled from their 50 uL drop (t_c = 2490 s) on 300 g/m2
cold-press paper. Values still set by eye are marked "eye"; constants with no citation (the tool table KINDS,
the flow, back-run and lifting constants) are eye as well.

Dabs act at full resolution (hard, ragged edges on dry paper; dry-brush on the paper's peaks). Between episodes
(`episode_end`) and when time passes (`dry`) the wash moves on a bounded crop and, for wide spreads, a
downscaled grid: wet-in-wet bleeding, back-runs where fresh water meets a drying wash, the coffee-ring flow that
darkens a drying edge, settling (granulation) and finally the dried wash is committed as a KM layer.
"""
import math
import numpy as np
from scipy.ndimage import gaussian_filter, binary_dilation, binary_erosion
from PIL import Image
from functools import lru_cache
from .base import Medium, hx, pigment_from_hex, km_layer, load_pigments

# --------------------------------------------------------------------------- time
# One episode is taken as EPISODE_MIN minutes of studio time (eye: a painter's working spell; it keeps the
# wet-in-wet window of the earlier, uncalibrated model). Water is counted in "drop loads": water = 1 is the
# load of the measured 50 uL drop on 300 g/m2 cold-press paper, which dries in t_c = 2490 s at 22 C, 35% RH
# (Gonzalez-Gutierrez et al. 2019, [W1] in docs/media-data.md). A thin film evaporates at a constant rate, so a
# wash's drying time is proportional to its water (thin-film assumption, not measured).
EPISODE_MIN = 10.0
TC_EPISODES = 2490.0 / 60.0 / EPISODE_MIN          # 4.15 episodes: a water = 1 wash on cold press is dry by then

# --------------------------------------------------------------------------- supports
# air/absorb: surface water lost per episode to the air / into the sheet (constant-flux thin film), set so that
# water = 1 on cold press is dry to the touch after TC_EPISODES (see the calibration report); ddecay: the
# sheet's own drying (damp, per episode); hot and rough paper keep the earlier relative rates (eye: no
# measurement of drying on those papers was found).
# sig: wet-in-wet spread (px, eye); gran: how much the paper makes pigment granulate (cold press calibrated on
# the flat-field texture, the others relative, eye); ring: edge darkening (cold press calibrated on the rim
# ratio of isolated washes, the others relative, eye); shade: relief shading in the render (calibrated on the
# texture of blank paper); slope: how sharply dry-brush picks out peaks; ragged: edge raggedness; lift: how well
# pigment lifts (hot-press lifts best) (eye).
SUP = {
    "cold_press": dict(absorb=0.13, air=0.20, ddecay=0.9, sig=5.0, gran=0.75, ring=0.8, shade=0.05,
                       slope=5.0, ragged=0.22, lift=1.0),
    "hot_press": dict(absorb=0.07, air=0.21, ddecay=1.03, sig=6.5, gran=0.31, ring=1.0, shade=0.016,
                      slope=3.0, ragged=0.06, lift=1.3),
    "rough": dict(absorb=0.17, air=0.21, ddecay=0.82, sig=4.0, gran=1.25, ring=0.65, shade=0.083,
                  slope=7.5, ragged=0.42, lift=0.8),
}
DAMP_GAIN = 2.0            # eye: damp (0..1, sheet saturated at 1) per unit of water absorbed
MASKCOL = hx("#eadf9e")
WET = 0.04
# edge darkening (calibrated, see the report): ring strength = ring * (RING0 + RING1 * fine * phi), phi = the
# suspended pigment's absorption / RING_PHI; SETTLE_COARSE: extra settling rate of coarse pigment (eye)
RING0, RING1, RING_PHI, RING_WIDEN, SETTLE_COARSE, COARSE_SUSP = 0.05, 0.8, 1.2, 4.0, 2.0, 0.4

# --------------------------------------------------------------------------- measured pigments (handprint)
# Ratings per Colour Index name in studio/pigments.json -> media.watercolour (MacEvoy, handprint.com, [P3]).
OPACITY_SCALE = 0.6        # eye: handprint "opaque" (Tr 0) -> base.pigment_from_hex opacity 0.6
DEFAULT_Q = None           # wet density gain where not measured: the median over the measured pigments (set below)
PAPER_L = 94.0             # handprint's paper value (the value range is measured from it)
KNEE = 0.6                 # eye: a wash darkens linearly with pigment up to 60% of its darkest, then saturates


def _lab(c):
    c = np.asarray(c, np.float64)
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return 116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])


def _L_to_v(L):
    """CIE L* of a grey -> the engine's sRGB-encoded value."""
    Y = ((L + 16) / 116) ** 3 if L > 8 else L / 903.3
    return 12.92 * Y if Y <= 0.0031308 else 1.055 * Y ** (1 / 2.4) - 0.055


def _shift_q(pct, darkest_L):
    """Wet-to-dry lightness shift (% of the masstone's dry L*) -> the factor by which the wet film's optical
    density exceeds the dry one's (K_wet = K (1 + q))."""
    Ld = max(darkest_L, 8.0)
    Lw = Ld / (1 + pct / 100.0)
    vp = _L_to_v(PAPER_L)
    Dd, Dw = -math.log(_L_to_v(Ld) / vp), -math.log(max(_L_to_v(Lw), 1e-3) / vp)
    return float(np.clip(Dw / max(Dd, 1e-3) - 1, -0.5, 1.5))


_TABLE = None


def _table():
    """The watercolour pigments of pigments.json with the engine's attributes."""
    global _TABLE
    if _TABLE is None:
        rows = []
        for p in load_pigments():
            w = (p.get("media") or {}).get("watercolour")
            if not w or p["ci"].startswith("PW"):
                continue
            row = _row(p, w)
            if row:
                rows.append(row)
        # a shift measured as % of the masstone's lightness does not transfer to paints of another value; the
        # density ratio q does, so unmeasured paints get the median q of the measured ones
        global DEFAULT_Q
        qs = [r["q"] for r in rows if r["q"] is not None]
        DEFAULT_Q = float(np.median(qs)) if qs else 0.15
        for r in rows:
            if r["q"] is None:
                r["q"] = DEFAULT_Q
        _TABLE = rows
    return _TABLE


def _row(p, w):
    Gr, St, Tr = w.get("granulation_0_4"), w.get("staining_0_4"), w.get("transparency_0_4")
    VR, HA = w.get("value_range"), w.get("hue_angle_cielab")
    if None in (Gr, St, Tr, VR, HA):
        return None
    dark = PAPER_L - float(VR)
    jab = w.get("ciecam_Jab_masstone")
    if jab:
        C = math.hypot(jab[1], jab[2])
    else:   # no masstone colour: a typical chroma for the class (eye)
        C = 5.0 if p["ci"].startswith("PBk") else 40.0
    sh = w.get("drying_shift_lightness_pct")
    return dict(ci=p["ci"], name=p.get("name") or p["ci"], gran=float(Gr) / 4, stain=float(St) / 4,
                opacity=(1 - float(Tr) / 4) * OPACITY_SCALE, darkest_L=dark, L=dark, C=C, h=float(HA),
                shift=sh, q=_shift_q(float(sh), dark) if sh is not None else None,
                # particle size: granulation is the visible sign of large, dense particles; the four pigments
                # measured by DLS in [W1] fit it (quinacridone, madder: Gr 0, fine; ultramarine, Mars black:
                # Gr >= 1.5, coarse). A proxy, not a measurement of each pigment.
                fine=float(np.clip(1 - float(Gr) / 1.5, 0, 1)), n=int(w.get("n_paints", 1) or 1))


@lru_cache(maxsize=4096)
def _nearest(key):
    """Nearest measured pigment to an sRGB colour (quantised key) by hue, chroma and value."""
    c = np.array(key, np.float64) / 255.0
    L, a, b = _lab(c)
    Ch, hh = math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360
    best, bc = None, 1e9
    for r in _table():
        dh = abs((hh - r["h"] + 180) % 360 - 180)
        cost = (dh / 25.0) ** 2 * min(1.0, Ch / 15.0)                           # hue, when the colour has one
        Cexp = r["C"] * float(np.clip((100 - L) / (100 - r["L"] + 1e-3), 0, 1.2))   # a tint's chroma at this value
        cost += ((Ch - Cexp) / 20.0) ** 2
        if L < r["darkest_L"] - 2:                                              # darker than one wash can go
            cost += ((r["darkest_L"] - L) / 10.0) ** 2
        cost -= 0.25 * math.log(1 + r["n"])                                     # prefer common paints (eye)
        if cost < bc:
            best, bc = r, cost
    return best


def wc_pigment(color=None, name=None):
    """A measured watercolour pigment: by Colour Index name or common name ('PB29', 'burnt sienna'), else the
    nearest to the colour. Returns the engine's attributes (dict) or None if the library is missing."""
    if name:
        k, p = str(name).strip().lower(), None
        for q in load_pigments():
            bn = ((q.get("media") or {}).get("watercolour") or {}).get("by_name") or {}
            if k in ((q.get("ci") or "").lower(), (q.get("name") or "").lower()) or k in bn:
                p = q          # (natural earths are split by marketing name under PBr7)
                break
        if p is not None and (p.get("media") or {}).get("watercolour"):
            w = dict(p["media"]["watercolour"])
            bn = (w.get("by_name") or {}).get(k)
            if bn:   # the ratings of that marketing name (e.g. burnt sienna within PBr7)
                w.update(granulation_0_4=bn["Gr"], staining_0_4=bn["St"], transparency_0_4=bn["Tr"], value_range=bn["VR"])
                p = dict(p, name=k)
            r = _row(p, w)
            if r:
                _table()
                if r["q"] is None:
                    r["q"] = DEFAULT_Q
                return r
        print(f"watercolour: no measured watercolour pigment '{name}'; using the nearest by colour")
    if color is None or not _table():
        return None
    key = tuple(int(v) for v in np.clip(np.round(np.asarray(color, np.float64) * 255), 0, 255))
    return _nearest(key)


def _kmax(darkest_L, paper):
    """For a transparent film (S ~ 0, as match lays): the luminance-weighted absorption at which a single wash
    reaches the pigment's darkest value (handprint value range) over this paper (R = R0 exp(-2K))."""
    v = _L_to_v(darkest_L)
    vp = float(np.dot(paper, (0.3, 0.59, 0.11)))
    return max(0.05, -0.5 * math.log(max(v, 1e-3) / max(vp, 1e-3)))


@lru_cache(maxsize=4096)
def _mmax_cached(K, S, darkest_L, paper):
    K, S, P = np.array(K, np.float32), np.array(S, np.float32), np.array(paper, np.float32)[None, :]
    L = lambda m: float(_lab(km_layer(P, K * m, S * m + 1e-4, np.ones(1, np.float32))[0])[0])
    if L(64.0) > darkest_L:
        return 64.0
    lo, hi = 0.0, 64.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if L(mid) > darkest_L else (lo, mid)
    return max(0.05, 0.5 * (lo + hi))


def _mmax(K, S, darkest_L, paper):
    """The amount of this paint (a multiple of the unit film whose colour over white is the given colour) at
    which one wash reaches the pigment's darkest value over this paper."""
    r = lambda a: tuple(round(float(v), 3) for v in np.atleast_1d(a))
    S3 = np.broadcast_to(np.asarray(S, np.float32), (3,))
    return _mmax_cached(r(K), r(S3), round(float(darkest_L), 1), r(paper))


def _sat(c, cmax):
    """Pigment in one wash: linear up to KNEE of the pigment's darkest, then saturating exponentially toward it
    (deposit density vs concentration saturates exponentially, [W1]). c, cmax: amounts of paint."""
    a = KNEE * cmax
    if c <= a:
        return c
    return a + (cmax - a) * (1 - math.exp(-(c - a) / (cmax - a)))


def _saturate(K, kmax):
    """_sat for a transparent film given by its absorption K (luminance-weighted against kmax)."""
    K = np.asarray(K, np.float32)
    kl = float(np.dot(K, (0.3, 0.59, 0.11)))
    if kl <= KNEE * kmax or kl <= 0:
        return K
    return (K * (_sat(kl, kmax) / kl)).astype(np.float32)


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


def _pigment_attrs(it, color):
    """Granulation, staining, opacity, darkest value, wet shift and fineness of the paint: from the measured
    pigment (named or nearest), with any explicit value in the intention taking precedence."""
    r = wc_pigment(color, it.get("pigment")) or {}
    return dict(ci=r.get("ci"),
                gran=float(it.get("granulation", r.get("gran", 0.25))),
                stain=float(it.get("staining", r.get("stain", 0.75))),
                opacity=float(it.get("opacity", r.get("opacity", 0.15))),
                darkest_L=float(r.get("darkest_L", 30.0)),
                q=float(r.get("q", DEFAULT_Q if DEFAULT_Q is not None else 0.14)),
                fine=float(it.get("fine", r.get("fine", 0.5))))


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
# match (eye): skip a stroke whose start needs less than this optical density (about a 5% darkening); strokes of
# at least HALO_MIN px get a wet margin HALO_SPREAD x their size wide with HALO_WATER x their water
MATCH_SKIP, HALO_MIN, HALO_SPREAD, HALO_WATER = 0.05, 14, 0.3, 0.5
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
        pa = _pigment_attrs(it, self.color)
        K, S = pigment_from_hex(self.color, pa["opacity"])
        self.K, self.S = K, float(S.mean())
        self.gran, self.stain, self.fine, self.q = pa["gran"], pa["stain"], pa["fine"], pa["q"]
        self.darkest_L, self.kmax = pa["darkest_L"], None
        self.lift = float(it.get("lift", 0.5))
        self.target = self.color.copy() if it.get("type") == "match" else None
        # match: a watercolourist does not glaze over a passage for a small difference (each glaze over dry paint
        # costs an edge), and lays wash-sized strokes with a soft, wet margin so neighbours fuse (eye)
        self.skip = float(it.get("skip", MATCH_SKIP))
        self.halo = self.target is not None and kind in ("round", "flat", "mop") and size >= HALO_MIN
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
        target (how a watercolourist thinks: you can only go darker). The decision to paint is taken once, at
        the start of the stroke: once the brush is down the stroke is continuous (no fragments), carrying less
        pigment where little is needed."""
        yi, xi = int(np.clip(y, 0, cv.H - 1)), int(np.clip(x, 0, cv.W - 1))
        y0, y1, x0, x1 = max(0, yi - 2), yi + 3, max(0, xi - 2), xi + 3
        base = km_layer(cv.under[y0:y1, x0:x1], cv.dK[y0:y1, x0:x1], cv.dS[y0:y1, x0:x1, None] + 1e-4, 1.0)
        base = base.reshape(-1, 3).mean(0)
        need = np.clip(-0.5 * np.log(np.clip(self.target, 1e-3, 1) / np.clip(base, 1e-3, 1)), 0, 3.5).astype(np.float32)
        if not self.started:
            if need.max() < self.skip:
                self.noop = True      # already close enough here: the painter leaves it
                return False
            K = need
        else:
            K = 0.5 * self.K + 0.5 * need
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
        if self.noop:
            return
        if self.target is not None and not self._match_pigment(cv, x, y):
            return
        self.started = True
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
        if self.target is not None:      # match lays a transparent film computed from the need
            if self.kmax is None:
                self.kmax = _kmax(self.darkest_L, self.med.paper(cv))
            Kt = _saturate(self.K * self.conc, self.kmax)
            St = self.S * self.conc
        else:                            # the paint's amount saturates toward its darkest single wash
            if self.kmax is None:
                self.kmax = _mmax(self.K, self.S, self.darkest_L, self.med.paper(cv))
            c = _sat(self.conc, self.kmax)
            Kt, St = self.K * c, self.S * c
        # into paper that was already wet (or damp) before this episode the charge blooms out at once; strokes of
        # the same episode lie side by side crisply and join when the water moves (episode_end)
        wp = getattr(cv, "_wpre", None)
        w_pre = wp[sl] if getattr(cv, "_wc_snap", False) and wp is not None and wp.shape == cv.water.shape else w
        wetp = float(((w_pre + cv.damp[sl] * 0.6) * (m > 0.05)).sum() / ((m > 0.05).sum() + 1e-6))
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
            cv.fine[sl] += (self.fine - cv.fine[sl]) * aw
            cv.wq[sl] += (self.q - cv.wq[sl]) * aw
        if todry > 0:
            ad = a * todry
            d = cv.dK[sl]
            d += np.maximum(Kt[None, None, :] - d, 0) * ad[..., None]
            cv.dS[sl] += np.maximum(St - cv.dS[sl], 0) * ad
        cv.stain[sl] += (self.stain - cv.stain[sl]) * a * 0.5
        if self.halo and self.kind != "dry":
            # a wet margin of clean water around the stroke: the edge bleeds out softly when the water moves, and
            # strokes laid next to each other in one episode join into one wash
            free = 1 - cv.mask[sl]
            hm = np.clip(gaussian_filter(m, max(1.0, self.size * HALO_SPREAD)) * 1.8, 0, 1) * free
            if cv.clip is not None:
                hm = hm * cv.clip[sl]
            cv.water[sl] = np.maximum(cv.water[sl], hm * Wb * HALO_WATER)

    def _water(self, cv, sl, m):
        """Clean water: wets the paper; re-dissolves a little dried, non-staining pigment."""
        cv.water[sl] = np.maximum(cv.water[sl], m * self.W)
        if getattr(cv, "_wpre", None) is not None:
            cv._wpre[sl] = np.maximum(cv._wpre[sl], cv.water[sl])
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
    arrays = ("col", "under", "gK", "gS", "dK", "dS", "water", "damp", "mask", "gran", "stain", "fine", "wq")
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
        for a in ("gS", "dS", "water", "damp", "mask", "gran", "fine", "wq"):
            setattr(cv, a, np.zeros((H, W), np.float32))
        cv.stain = np.full((H, W), 0.75, np.float32)    # the median handprint staining rating (3 of 4)

    def paper(self, cv):
        return hx((getattr(cv, "meta", None) or {}).get("ground", "#f6f3eb"))

    # ---------------------------------------------------------------- appearance
    def appear(self, cv, sl):
        K = cv.gK[sl] + cv.dK[sl]
        S = (cv.gS[sl] + cv.dS[sl])[..., None] + 1e-4
        wf = np.clip(cv.water[sl] * 1.6 + cv.damp[sl] * 0.5, 0, 1)[..., None]
        # wet colour looks darker and dries lighter, by the pigment's measured drying shift (wq); the wet paper's
        # own darkening (5%) is eye
        R = km_layer(cv.under[sl], K * (1 + cv.wq[sl][..., None] * wf), S, 1.0)
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
            cv._wpre = cv.water.copy()     # water a stroke of this episode finds already there (washes, clean water)

    def make_tool(self, it, size, color, rng):
        cv = getattr(self, "_cv", None)
        kind = it.get("brush", "round")
        kind = ALIAS.get(kind, kind)
        if kind not in KINDS:
            kind = "round"
        b = WBrush(self, kind, size, color, rng, it, SUP.get(getattr(self, "_support", "cold_press"), SUP["cold_press"]))
        return _Bound(self, b)

    def glaze(self, cv, mask, col, op, it=None):
        """A wash: a flat transparent film of water and pigment laid over the region with a big brush. The
        pigment is the measured one named in the intention ("pigment") or the nearest to the colour."""
        self._bind(cv)
        it = it or {}
        col = np.asarray(col, np.float32)
        pa = _pigment_attrs(it, col)
        m = np.clip(mask, 0, 1) * (1 - cv.mask)
        K, S = pigment_from_hex(col, pa["opacity"])
        c = _sat(float(op), _mmax(K, float(S.mean()), pa["darkest_L"], self.paper(cv)))
        Ks, sf = K * c, c / max(float(op), 1e-6)
        wet = m > 0.03
        water = float(it.get("water", 1.0))
        cv.water = np.where(wet, np.maximum(cv.water, 0.9 * water * np.clip(m * 1.3, 0, 1)), cv.water)
        if getattr(cv, "_wpre", None) is not None:
            cv._wpre = np.maximum(cv._wpre, cv.water)
        cv.gK += Ks[None, None, :] * m[..., None]
        cv.gS += float(S.mean()) * c * m
        cv.gran += (pa["gran"] - cv.gran) * m
        cv.fine += (pa["fine"] - cv.fine) * m
        cv.wq += (pa["q"] - cv.wq) * m
        cv.stain += (pa["stain"] - cv.stain) * m * 0.5
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
        gran, fine, wq = cv.gran[sl], cv.fine[sl], cv.wq[sl]
        tt = min(t, 1.5)  # flow happens while the wash is wet; long waits do not move pigment further

        # 1. flow: wet-in-wet bleeding inside the wet area (paper that is wet or damp), feathered
        wetR = (((W > WET) | (D > 0.22)) & free).astype(np.float32)
        if wetR.any():
            feather = 0.72 + 0.34 * _n(gaussian_filter(tex, 2.0)) + 0.22 * _n(gaussian_filter(tex, (1.2, 4.0)))
            mu = np.clip(W * 1.1 + D * 0.25, 0, 0.85) * wetR                                 # mobility of the water
            # where pigment can go: in proportion to the mobility, so pigment does not pile up where the water thins
            # toward the edge (that drift made every wash ring alike); edge darkening is the ring flow of step 3
            rec = mu / 0.85 * feather + 1e-4 * wetR
            mob = mu * min(1.0, tt)                                                           # how much leaves
            mob2 = np.clip((W - 0.2) * 1.4, 0, 0.7) * wetR * min(1.0, tt)
            for s, mb in ((sp["sig"], mob), (sp["sig"] * 5.0, mob2)):
                if mb.max() < 0.01:
                    continue
                rb = _blur(rec, s) + 1e-5
                for arr in (g, gS, gran, fine, wq):
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
                # the bloom grows inside the damp wash only (fresh paint laid in the same episode elsewhere does not
                # take part: that drew a dark line around every new wash), and its dark front forms away from where
                # the fresh water came in, not along the contact line
                bloom = zone & (reach > 0.04 + 0.3 * bn)
                if bloom.any():
                    push = np.where(src, 0.25, 0.6) * bloom
                    rg = g * push[..., None]
                    rd = d * (bloom * 0.45)[..., None]
                    g -= rg; d -= rd
                    gS -= gS * push; dS -= dS * bloom * 0.45
                    front = binary_dilation(bloom, iterations=2) & ~binary_erosion(bloom, iterations=1) & zone
                    front &= ~binary_dilation(src & ~zone, iterations=3)
                    fr = gaussian_filter(front.astype(np.float32), 1.0) * (zone | bloom)   # a front of a few px, not one
                    moved = rg + rd
                    nf = _blur(fr, 5.0)
                    keep = (nf > 1e-3)[..., None]          # pigment with no front within reach stays put
                    # each source hands its pigment to the front within reach, in proportion (mass-conserving)
                    g += moved * ~keep + _blur(moved * keep / (nf[..., None] + 1e-4), 5.0) * fr[..., None] * 0.9
                    W = np.where(bloom, np.maximum(W, 0.25), W)

        # 3. evaporation and absorption: a thin film loses water at a constant rate (to the air, and into the sheet
        # while the sheet has room), so drying time grows with the load (TC_EPISODES for water = 1 on cold press);
        # the sheet then dries from inside. The coffee-ring flow carries suspended pigment to pinned edges.
        Wb = W.copy()
        ev, ab = sp["air"] * t, sp["absorb"] * t * np.clip(1 - D, 0, 1)
        loss = np.minimum(W, ev + ab)
        W = W - loss
        D = np.clip(D + loss * ab / (ev + ab + 1e-6) * DAMP_GAIN, 0, 1) * math.exp(-sp["ddecay"] * t)
        wet = (Wb > WET) & free
        if wet.any():
            frac = np.clip(loss / (Wb + 1e-4), 0, 1)
            drysides = ((~wet) & (D < 0.2)).astype(np.float32)
            phi = np.clip(g.sum(-1) / RING_PHI, 0, 2.0)
            grow = np.clip(fine * phi, 0, 1)         # the ring widens with concentration for fine pigments [W1]
            band = wet * np.clip(gaussian_filter(drysides, 1.3) * 3.0 * (1 - grow) + gaussian_filter(drysides, 1.3 + RING_WIDEN) * 3.0 * grow, 0, 1)
            if band.max() > 0:
                prox = np.clip(gaussian_filter(band, 5.0) * 4.0, 0, 1)
                # edge darkening: every pigment rings a little (the coffee-ring effect is universal); for fine,
                # colloidal pigments the ring grows with the concentration in suspension, for coarse ones it does
                # not (they settle within seconds) [W1]. RING0, RING1 calibrated on the rim ratio.
                # only what is still suspended can travel: coarse pigment has mostly settled (factor eye)
                susp = fine + (1 - fine) * COARSE_SUSP
                rs = sp["ring"] * frac * prox * wet * np.clip(Wb * 1.4, 0.25, 1) * (RING0 + RING1 * fine * phi) * susp
                nb = gaussian_filter(band, 5.0)
                rs = np.clip(rs, 0, 0.5) * (nb > 1e-3)
                tau = g * rs[..., None]
                tS = gS * rs
                g -= tau; gS -= tS
                # each source hands its pigment to the band pixels within reach, in proportion (mass-conserving;
                # dividing at the receiver instead piled pigment into one-pixel lines at the wet boundary)
                nbi = 1.0 / (nb + 1e-4)
                g += gaussian_filter(tau * nbi[..., None], (5.0, 5.0, 0)) * band[..., None]
                gS += gaussian_filter(tS * nbi, 5.0) * band

        # 4. settling: pigment leaves the water for the paper, granulating into the hollows when wet
        # coarse pigment settles out of the water faster than fine (settling velocities in [W1]; the factor is eye)
        rate = 1 - np.exp(-t * (0.25 * (1 + SETTLE_COARSE * (1 - fine)) + 1.5 * np.clip(1 - W / 0.45, 0, 1)))
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
            W[drymask] = 0; D[drymask] = 0; gran[drymask] = 0; fine[drymask] = 0; wq[drymask] = 0
        W[W < 0.003] = 0
        cv.water[sl], cv.damp[sl] = W, D
        cv.gK[sl], cv.gS[sl], cv.dK[sl], cv.dS[sl], cv.gran[sl] = g, np.clip(gS, 0, None), np.clip(d, 0, None), np.clip(dS, 0, None), gran
        cv.fine[sl], cv.wq[sl] = fine, wq
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
