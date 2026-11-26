"""Oil (studio v8): paint that behaves like oil paint.

What it models (docs/MEDIA.md "Engine model (oil)", docs/FINISHING.md "Oil"):
- Bristle brushes made of individual bristle clumps. Each clump has its own load, density, height and a
  slightly different colour (paint is never perfectly mixed on the brush) and picks up wet paint on its
  own, so strokes show furrows along their direction, streaks of mixed and underlying colour, ragged
  edges, and run out unevenly into dry-brush that catches only the tops of the weave.
- Height: every stroke lays a film whose top carries the bristle furrows, small ridges at its edges and
  a ridge where the brush lifts (proportional to the paint left on it). Brushing into wet paint
  reshapes it; dried layers keep their relief under new paint (`hdry`).
- Shapes: round with a pointed tip (line to blob with pressure), flat, bright, filbert, fan, liner
  (rigger), palette knife (slabs with crisp edges; a nearly empty knife scrapes back to the layer
  beneath), rag (wipes wet paint out toward the layer beneath), finger smudge, soft blender, scraper
  (sgraffito through wet paint).
- Colour mixing in pigment space (media/spectral.py): every colour is unmixed into measured oil paints
  (Revigo: spectral two-constant Kubelka-Munk K and S, plus zinc white and bone black), mixed by
  concentration and turned back into RGB, so each pigment keeps its tinting strength (docs/calibration/colour.md).
  Paint mixes into wet paint; over dry paint (or the ground) it lies on top as a spectral film.
  The canvas keeps the pigment mixture of the paint laid on it while a command runs.
- Glazes are spectral Kubelka-Munk films of the glaze paint (thickness in units of the measured 100 um
  film) over what is there, pooling in hollows.
- Oil content (`fat`) and gloss (`sheen`): wet paint looks glossy; lean or thin paint over an absorbent
  layer sinks in and dries dull. Lean-over-fat is reported as a craft warning.
- Finishing: retouch, oil-out, glaze and varnish (gloss/satin/matte; refuses while wet).

State arrays: col (apparent colour), wet, ht (paint height), hdry (height of the dried layers), fat,
sheen (dry gloss), under (colour of the dried layer beneath the wet paint, RGB), varn (varnish film).
"""
import math
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw
from .base import Medium, hx, noise_field
from . import spectral


# ---------------------------------------------------------------- supports
def weave(h, w, seed=7, period=4.0):
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    def wob(s, amp):
        n = gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), s)
        return n / (n.std() + 1e-6) * amp
    p = period
    xw = x + wob(14, 0.9)
    yw = y + wob(14, 0.9)
    ix = np.floor(xw / p); iy = np.floor(yw / p)
    fx = xw / p - ix; fy = yw / p - iy
    # thread cross-section (rounded) and the rise and fall where it passes over/under the other thread
    across_warp = np.sin(np.pi * fx) ** 0.8
    across_weft = np.sin(np.pi * fy) ** 0.8
    par = ((ix + iy) % 2).astype(np.float32)
    rise_warp = 0.5 - 0.5 * np.cos(np.pi * (yw / p + 0.5 + ix))   # period 2p, phase per warp thread
    rise_weft = 0.5 - 0.5 * np.cos(np.pi * (xw / p + iy))
    # slubs: each thread a little thicker or thinner along its length
    tx = rng.standard_normal((int(w / p) + 3,)).astype(np.float32)
    ty = rng.standard_normal((int(h / p) + 3,)).astype(np.float32)
    slx = gaussian_filter(rng.standard_normal((h, int(w / p) + 3)).astype(np.float32), (25, 0))
    sly = gaussian_filter(rng.standard_normal((int(h / p) + 3, w)).astype(np.float32), (0, 25))
    slx = slx / slx.std(); sly = sly / sly.std()
    ixc = np.clip(ix.astype(int), 0, slx.shape[1] - 1); iyc = np.clip(iy.astype(int), 0, sly.shape[0] - 1)
    thx = 1 + 0.12 * tx[ixc] + 0.15 * slx[np.arange(h)[:, None], ixc]
    thy = 1 + 0.12 * ty[iyc] + 0.15 * sly[iyc, np.arange(w)[None, :]]
    hw = across_warp * (0.45 + 0.55 * rise_warp) * thx
    hf = across_weft * (0.45 + 0.55 * rise_weft) * thy
    tw = np.maximum(hw, hf)
    fine = gaussian_filter(rng.random((h, w)).astype(np.float32), 0.6)
    n = lambda a: (a - a.min()) / (a.max() - a.min() + 1e-6)
    return np.clip(0.75 * n(tw) + 0.15 * n(fine) + 0.10 * n(wob(4, 1)), 0, 1).astype(np.float32)

ABSORB = {"canvas": 0.25, "panel": 0.4}
# glaze film thickness per unit of `opacity`, in units of the Revigo drawdown (100 um wet): opacity 1 is a 30 um
# film, 0.25 a 7.5 um one. The range is measured (glaze layers of 10-50 um, a translucent layer of 30-40 um in a
# cross-section: docs/media-data.md [O1]); mapping `opacity` onto it is a judgement. The glaze colour is what the
# film shows over white at opacity 1 (spectral.glaze_paint: transparent pigments thinned with oil for dark and
# saturated colours, white for light ones).
GLAZE_FILM = 0.3
MIX_MIN = 1e-3          # mixing amounts below this are skipped (a 0.1% change; tuned for speed)


def _ensure(cv):
    """Per-canvas caches, and repair of arrays an older canvas may lack."""
    if getattr(cv, "_oil_ok", False):
        return cv
    if getattr(cv, "under", None) is None or cv.under.ndim != 3:
        cv.under = cv.col.copy()
    lo, hi = np.percentile(cv.tex[::4, ::4], [2, 98])
    t = np.clip((cv.tex - lo) / (hi - lo + 1e-6), 0, 1)
    if cv.meta.get("support") == "panel":       # smooth: a dry brush breaks along its bristles, not the surface
        t = 0.5 + 0.3 * (t - 0.5)
    cv._oil_tooth = t.astype(np.float32)
    cv._oil_fol = 0
    cv._oil_ok = True
    return cv


# ---------------------------------------------------------------- brushes
SPEC = {
    # k: bristle clumps per px of size; dens: density range (gaps between clumps); furrow: depth of the
    # furrows; cap: stroke length per px of size per full load; thick: film thickness; rough: how
    # ragged the edges break; fat: default oil content of the paint it carries
    "round":   dict(k=0.55, dens=(0.55, 1.0), furrow=0.75, cap=60, thick=1.0, rough=0.8, fat=0.5),
    "flat":    dict(k=0.6, dens=(0.5, 1.0), furrow=0.85, cap=55, thick=1.0, rough=0.9, fat=0.5),
    "bright":  dict(k=0.6, dens=(0.6, 1.0), furrow=1.0, cap=28, thick=1.7, rough=1.0, fat=0.45),
    "filbert": dict(k=0.55, dens=(0.6, 1.0), furrow=0.75, cap=55, thick=0.9, rough=0.55, fat=0.5),
    "fan":     dict(k=1.4, dens=(0.6, 1.0), furrow=1.0, cap=80, thick=0.25, rough=1.0, fat=0.5),
    "liner":   dict(k=0.5, dens=(0.9, 1.0), furrow=0.15, cap=160, thick=0.45, rough=0.1, fat=0.65),
    "knife":   dict(k=0.5, dens=(0.95, 1.0), furrow=0.08, cap=22, thick=2.2, rough=0.0, fat=0.5),
    "rag":     dict(k=0.35, dens=(0.3, 1.0), furrow=0.0, cap=1e9, thick=0.0, rough=0.0, fat=0.5),
    "scraper": dict(k=0.5, dens=(1.0, 1.0), furrow=0.0, cap=1e9, thick=0.0, rough=0.0, fat=0.5),
    "smudge":  dict(k=0.4, dens=(0.8, 1.0), furrow=0.2, cap=1e9, thick=0.0, rough=0.0, fat=0.5),
    "blend":   dict(k=0.8, dens=(0.85, 1.0), furrow=0.25, cap=1e9, thick=0.0, rough=0.0, fat=0.5),
}
ALIAS = {"rigger": "liner", "blender": "blend", "finger": "smudge", "sgraffito": "scraper", "cloth": "rag"}
EDGE = {"hard": 0.12, "soft": 0.7, "lost": 1.6}


class Brush:
    def __init__(self, kind, size, color, rng, load=1.0, cover=0.95, pickup=0.35, thick=0.5,
                 wetmix=0.5, edge="soft", fat=None, streak=0.5, scrape=None):
        self.kind, self.size, self.rng = kind, float(size), rng
        sp = SPEC[kind]
        self.sp = sp
        self.color = np.asarray(color, np.float32).copy()
        self.cover, self.pickup, self.thick, self.wetmix, self.edge = cover, pickup, thick, wetmix, edge
        self.fat = float(sp["fat"] if fat is None else fat)
        self.load0 = max(float(load), 0.05)
        k = max(5, int(size * sp["k"]) + 1)
        self.k = k
        spread = 0.03 if kind in ("knife", "liner") else 0.3
        self.bload = (load * rng.uniform(1 - spread, 1 + spread, k)).astype(np.float32)
        lo, hi = sp["dens"]
        self.dens = rng.uniform(lo, hi, k).astype(np.float32)
        if kind == "fan":
            self.dens *= (rng.random(k) < 0.42)
        fv = sp["furrow"] * rng.uniform(0.25, 0.65)               # how sharply this stroke's furrows show
        self.prof = (1 - fv * rng.random(k) ** 0.8).astype(np.float32)
        self.brate = rng.uniform(0.75, 1.3, k).astype(np.float32)
        # paint is never perfectly mixed on the brush: neighbouring clumps carry slightly lighter or
        # darker, warmer or cooler versions of the mixture
        z = rng.standard_normal(k).astype(np.float32)
        tint = rng.normal(0, 1, 3).astype(np.float32)
        tint -= tint.mean()
        st = 0.08 * streak * (0.2 if kind == "knife" else 1.0)
        self.bcol = np.clip(self.color[None, :] * (1 + st * z[:, None]) + 0.25 * st * z[:, None] * tint[None, :],
                            0, 1).astype(np.float32)
        # the finest scale: single hairs, about 1.5 px apart, leave their own fine grooves
        self.kf = max(6, int(size / 1.5))
        self.fine = (1 - 0.3 * fv * rng.random(self.kf)).astype(np.float32)
        self.pdrift = np.zeros(k, np.float32)   # furrows wander along the stroke: hairs splay, merge, part
        self.lat = 0.0
        self.step = None
        self.pprev = None
        self.bow = 0.0                 # paint pushed ahead of the brush; left as a ridge where it lifts
        self.carry = None
        self.scrape = scrape

    @property
    def paint(self):
        return float(self.bload.mean())

    # ------------------------------------------------------------ the contact patch
    def extent(self, r, press):
        """Half length (along the stroke) and half width of the footprint, for the dab's window."""
        kind, p = self.kind, min(press, 1.2)
        if kind == "round":
            w = r * (0.2 + 0.8 * p ** 1.25)
            return w * (1.15 + 0.9 * min(p, 1.0)), w
        if kind in ("flat", "bright", "knife"):
            return r * {"flat": 0.3, "bright": 0.42, "knife": 0.7}[kind] + 0.6, r
        if kind == "filbert":
            w = r * (0.55 + 0.45 * min(p, 1.1))
            return w * 0.5 + 0.5, w
        if kind == "fan":
            return r * 0.18 + 0.7, r * 1.35
        if kind == "scraper":
            w = max(0.9, r * 0.22)
            return w + 1, w + 1
        return r, r

    def footprint(self, r, u, v, press):
        """Footprint F (0..1), across-coordinate s (-1..1 for the bristle lookup), half width, front length."""
        kind = self.kind
        ex = EDGE.get(self.edge, 0.7)
        if kind == "round":
            w = r * (0.2 + 0.8 * min(press, 1.2) ** 1.25)               # the tip spreads with pressure
            lf, lb = w * 0.95, w * (1.15 + 0.9 * min(press, 1.0))         # the belly drags behind the tip
            un = np.where(u >= 0, u / lf, u / lb)
            F = np.clip(1 - un * un - (v / w) ** 2, 0, 1) ** (ex * 0.8)
            return F, v / w, w, lf
        if kind in ("flat", "bright", "knife"):
            across = r * (0.85 if kind == "bright" else 1.0)
            la = r * {"flat": 0.3, "bright": 0.42, "knife": 0.7}[kind] + 0.6
            ef = 0.0 if kind == "knife" else {"hard": 0.03, "soft": 0.14, "lost": 0.45}.get(self.edge, 0.14)
            A = np.clip((across - np.abs(v)) / max(0.7, across * ef), 0, 1)
            if kind == "knife":
                L = np.clip((la - np.abs(u)) / 0.8, 0, 1)
            else:
                L = np.clip(1 - np.abs(u) / la, 0, 1) ** 0.3
            return A * L, v / across, across, la
        if kind == "filbert":
            w = r * (0.55 + 0.45 * min(press, 1.1))
            la = w * 0.5 + 0.5
            d = (np.abs(u) / la) ** 2 + (np.abs(v) / w) ** 2.4
            return np.clip(1 - d, 0, 1) ** max(0.35, ex * 0.9), v / w, w, la
        if kind == "fan":
            across, la = r * 1.35, r * 0.18 + 0.7
            F = np.clip(1 - np.abs(u) / la, 0, 1) ** 0.5 * np.clip((across - np.abs(v)) / 1.2, 0, 1)
            return F, v / across, across, la
        if kind == "liner":
            d = (u * u + v * v) / max(r * r, 0.3)
            return np.clip(1 - d, 0, 1) ** 0.35, v / max(r, 0.5), r, r
        if kind == "scraper":
            w = max(0.9, r * 0.22)
            d = np.sqrt(u * u + v * v)
            return np.clip((w - d) / 0.6 + 0.5, 0, 1), v / w, w, w
        if kind == "rag":
            d = (u / (r * 0.8)) ** 2 + (v / r) ** 2
            return np.clip(1 - d, 0, 1) ** 0.7, v / r, r, r * 0.8
        d = (u * u + v * v) / max(r * r, 1e-3)                                # smudge, blend
        return np.clip(1 - d, 0, 1) ** ex, v / r, r, r

    # ------------------------------------------------------------ one stamp
    def dab(self, cv, x, y, ang, press, rscale=1.0):
        _ensure(cv)
        r = max(0.7, self.size / 2 * rscale)
        la_, ac_ = self.extent(r, press)                          # a tight box around the rotated footprint
        ca, sa = math.cos(ang), math.sin(ang)
        hx_ = int(la_ * abs(ca) + ac_ * abs(sa)) + 2
        hy_ = int(la_ * abs(sa) + ac_ * abs(ca)) + 2
        x0, x1 = max(0, int(x) - hx_), min(cv.W, int(x) + hx_ + 1)
        y0, y1 = max(0, int(y) - hy_), min(cv.H, int(y) + hy_ + 1)
        if x0 >= x1 or y0 >= y1:
            return
        stp = self.step if self.step else max(0.5, self.size * 0.055)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dx, dy = xx - x, yy - y
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        F, s, wid, la = self.footprint(r, u, v, press)
        if cv.clip is not None:
            F = F * cv.clip[y0:y1, x0:x1]
        if F.max() <= 0.01:
            self.pprev = press
            return
        sl = (slice(y0, y1), slice(x0, x1))
        k = self.k
        dd = min(1.0, stp / max(self.size, 2))
        self.pdrift = (self.pdrift * (1 - 0.6 * dd) + self.rng.normal(0, 0.16 * math.sqrt(dd), k)).astype(np.float32)
        self.lat = self.lat * (1 - 0.3 * dd) + self.rng.normal(0, 0.5 * math.sqrt(dd))
        fb = np.clip((s + 1) * 0.5 * (k - 1) + self.lat, 0, k - 1)
        i0 = fb.astype(np.int32)
        i1 = np.minimum(i0 + 1, k - 1)
        fr = fb - i0
        inear = np.where(fr < 0.5, i0, i1)
        f = min(1.5, stp / max(wid * 0.5, 0.5))                  # deposit per unit of travel, not per dab
        kind = self.kind
        if kind in ("smudge", "blend", "rag", "scraper") or (kind == "knife" and self._scraping()):
            self._remove(cv, sl, F, s, u, la, press, f, inear)
            self.pprev = press
            return
        tooth = cv._oil_tooth[sl]
        # dry-brush: each clump's effective load against the weave; the edges break first
        eff = self.bload - getattr(self, "speedfx", 0.0)
        thr_b = np.clip((0.42 - eff) / 0.42, 0, 1.05) * 0.95
        thr = thr_b[inear] + np.clip((np.abs(s) - 0.7) / 0.3, 0, 1) * 0.55 * self.sp["rough"] * float(np.clip(1.25 - self.paint, 0.25, 1))
        gate = np.clip(4.0 * (tooth - thr) + 1.0, 0, 1)
        q_b = self.dens * np.clip(self.bload * 2.5, 0, 1)
        Q = q_b[i0] * (1 - fr) + q_b[i1] * fr
        a = F * min(press, 1.2) * gate * Q * f                   # paint transferred by this dab, per pixel
        if a.max() <= 0.003:
            self._deplete(stp, press, 0.3)
            self.pprev = press
            return
        c = cv.col[sl]
        w = cv.wet[sl]
        # pickup: every clump takes on some of the wet paint it passes through
        wa = a * w * (u > la * 0.15)                               # the leading edge meets the paint ahead
        ir = inear.ravel()
        sw = np.bincount(ir, wa.ravel(), k)
        if sw.max() > 1e-4:
            loc = np.stack([np.bincount(ir, (wa * c[..., ch]).ravel(), k) for ch in range(3)], 1) / (sw[:, None] + 1e-6)
            lw = sw / (np.bincount(ir, a.ravel(), k) + 1e-6)
            pk = np.clip(self.pickup * lw * 0.3 * stp / max(self.size * 0.5, 1.0), 0, 0.5)[:, None] * (sw[:, None] > 1e-4)
            self.bcol = (self.bcol * (1 - pk) + loc * pk).astype(np.float32)
        # colour: each clump's paint, partly lost into the wet paint beneath (wet-in-wet)
        cover = self.cover * (1.2 if kind in ("knife", "bright") else 1.0)
        t = np.clip(a * 3.2 * cover * (1 - np.clip(w * self.wetmix, 0, 0.8) * 0.45), 0, 1)
        if getattr(self, "_latsrc", None) is not self.bcol:                # the clumps' paint, unmixed into pigments
            self._lat, self._latsrc = spectral.latent(self.bcol), self.bcol
        spectral.mix_window(cv, sl, t, self._lat, index=inear, thr=MIX_MIN, wet=w)
        # height: the film's top carries the furrows, a small ridge at each side, and the lift ridge
        hd = cv.hdry[sl]
        hw = np.maximum(cv.ht[sl] - hd, 0)
        pr = np.clip(self.prof + self.pdrift * self.sp["furrow"], 0.15, 1.15)
        prof = (pr[i0] * (1 - fr) + pr[i1] * fr) * self.fine[np.clip(((s + 1) * 0.5 * self.kf).astype(np.int32), 0, self.kf - 1)]
        lb = self.bload[i0] * (1 - fr) + self.bload[i1] * fr
        tk = self.thick * self.sp["thick"] * 0.42
        T = tk * np.clip(lb, 0, 1.4) ** 0.4 * prof
        side = np.exp(-((np.abs(s) - 0.93) / 0.09) ** 2) * (0.3 if kind != "knife" else 1.0)
        T = T * (1 + side * np.clip(w + 0.4, 0, 1) * (F > 0.3))
        if kind == "knife":                                       # a smooth slab: level the top
            m = (hw * F).sum() / (F.sum() + 1e-6)
            T = T + 0.5 * (m - hw) * (F > 0.5)
        if self.pprev is not None and press < self.pprev:          # the brush is lifting: leave the bow wave
            drop = (self.pprev - press) / max(self.pprev, 1e-3)
            front = F * np.clip(u / max(la, 0.5) + 0.3, 0, 1)
            ridge = front * self.bow * drop * 3.0 * tk * np.clip(lb * 2, 0, 1)
            self.bow *= (1 - min(0.9, drop * 1.5))
        else:
            ridge = 0.0
        hw = hw + np.clip(a * 2.5, 0, 1) * (T - hw) + ridge
        cv.ht[sl] = np.clip(hd + hw, 0, 4)
        # oil: fat, and the gloss the passage will dry to (sinking in over an absorbent or lean layer)
        fw = cv.fat[sl]
        newlayer = (w < 0.3)
        bare = hd < 0.02
        absorb = np.where(bare, ABSORB.get(cv.meta.get("support"), 0.3), 0.55 * (1 - fw)) * newlayer
        thin = 1.0 / (1.0 + 4.0 * hw)
        sh_new = 0.38 + 0.6 * self.fat - 0.9 * absorb * (1 - 0.6 * self.fat) * thin
        # wet-in-wet the passage keeps the sinking it got when it was laid; only its oil content changes
        sh_new = np.where(newlayer, sh_new, cv.sheen[sl] + 0.6 * (self.fat - fw))
        ab = np.clip(a * 1.5, 0, 1)
        if self.fat < 0.88:
            lean = newlayer & (~bare) & (fw > self.fat + 0.15) & (a > 0.03)
            cv._oil_fol += int(lean.sum())
        cv.sheen[sl] = cv.sheen[sl] + ab * (np.clip(sh_new, 0.05, 0.95) - cv.sheen[sl])
        cv.fat[sl] = fw + ab * (self.fat - fw)
        cv.varn[sl] = cv.varn[sl] * (1 - ab)
        cv.wet[sl] = np.clip(w + a * 2.0, 0, 1)
        self.bow = min(self.bow + stp / max(self.size, 2) * 0.15 * self.paint * min(press, 1), 0.8 * self.paint + 0.05)
        self._deplete(stp, press, 1.0)
        self.pprev = press

    def _deplete(self, stp, press, frac):
        use = stp * (0.35 + 0.65 * min(press, 1.2)) * frac / (max(self.size, 2) * self.sp["cap"]) * getattr(self, "deplete_mul", 1.0)
        self.bload = np.maximum(0, self.bload - use * self.brate).astype(np.float32)

    def _scraping(self):
        if self.scrape is not None:
            return bool(self.scrape)
        return self.paint < 0.18

    # ------------------------------------------------------------ tools that move or remove paint
    def _remove(self, cv, sl, F, s, u, la, press, f, inear):
        kind = self.kind
        c = cv.col[sl]
        w = cv.wet[sl]
        m = F * min(press, 1.2)
        hd = cv.hdry[sl]
        hw = np.maximum(cv.ht[sl] - hd, 0)
        if kind == "blend":
            r = max(1.0, self.size / 2)
            sig = max(0.8, r / 2.5)
            bl = np.stack([gaussian_filter(c[..., i], sig) for i in range(3)], -1)
            amt = np.clip(m * (0.25 + 0.75 * w) * 0.85 * min(1, f * 1.5), 0, 1)
            cv.col[sl] = c * (1 - amt[..., None]) + bl * amt[..., None]
            soft = self.prof[inear]                                   # soft hair leaves faint fine lines
            cv.ht[sl] = hd + hw * (1 - amt * w * (0.25 + 0.1 * soft))
            return
        if kind == "smudge":
            ms = m.sum() + 1e-6
            local = (c * m[..., None]).sum((0, 1)) / ms
            if self.carry is None:
                self.carry = local.copy()
            amt = np.clip(m * (0.2 + 0.65 * w) * 0.75 * min(1, f * 1.5), 0, 1)
            spectral.mix_window(cv, sl, amt, self.carry, thr=MIX_MIN)
            ck = min(0.5, 0.3 * (self.step or 1.0) / max(self.size * 0.3, 1.0))
            self.carry = self.carry * (1 - ck) + local * ck
            cv.ht[sl] = hd + hw * (1 - amt * 0.35 * w)
            return
        under = cv.under[sl]
        tooth = cv._oil_tooth[sl]
        if self.carry is None:
            self.carry = c[m > 0.3].mean(0) if (m > 0.3).any() else c.mean((0, 1))
        if kind == "rag":
            mot = getattr(cv, "_oil_mottle", None)
            if mot is None:
                mot = cv._oil_mottle = noise_field(cv.H, cv.W, 3.5, 11)
            # folds of the cloth (streaks along the wipe), its crumpled contact (mottling) and the weave
            cloth = self.dens[inear] * np.clip(0.2 + 1.3 * mot[sl], 0, 1.2) * (0.75 + 0.5 * tooth)
            amt = np.clip(m * cloth * 0.9 * min(1, f * 1.2), 0, 1) * np.clip(w * 1.4, 0, 1) ** 0.8
            tgt = spectral.mix(under, self.carry[None, None, :], 0.12)    # a little of what the cloth holds smears back
            spectral.mix_window(cv, sl, amt, tgt, thr=MIX_MIN)
            sa_ = amt.sum()
            if sa_ > 0.01:
                self.carry = self.carry * 0.9 + 0.1 * (c * amt[..., None]).sum((0, 1)) / sa_
            cv.ht[sl] = hd + hw * (1 - amt * 0.85)
            cv.wet[sl] = w * (1 - amt * 0.6)
            cv.fat[sl] = cv.fat[sl] * (1 - amt * 0.3)
            cv.sheen[sl] = cv.sheen[sl] * (1 - amt * 0.15)
            return
        if kind == "scraper":
            amt = np.clip(m * 1.2 * min(1, f * 2.0), 0, 1) * np.clip(w * 1.5, 0, 1) ** 0.5
            spectral.mix_window(cv, sl, amt, under, thr=MIX_MIN)
            pushed = float((hw * amt).sum())
            rim = np.exp(-((np.abs(s) - 1.3) / 0.35) ** 2) * (np.abs(u) < 2 * max(la, 1)) * (w > 0.2)
            h2 = hd + hw * (1 - amt * 0.95) + rim * pushed / (rim.sum() + 1e-6) * 0.8
            h2 = h2 - m * (1 - w) * 0.04 * min(1, f * 2) * hw          # on dry paint: a faint burnished line
            cv.ht[sl] = np.maximum(h2, 0)
            cv.wet[sl] = w * (1 - amt * 0.5)
            return
        if kind == "knife":   # scraping with the flat of the blade: paint stays in the weave's hollows
            amt = np.clip(m * min(1, f * 1.3) * (0.45 + 0.55 * tooth), 0, 1) * np.clip(w * 1.3, 0, 1)
            spectral.mix_window(cv, sl, amt * 0.9, spectral.mix(under, self.carry[None, None, :], 0.18), thr=MIX_MIN)
            ms = m.sum() + 1e-6
            local = (c * m[..., None]).sum((0, 1)) / ms
            self.carry = self.carry * 0.85 + local * 0.15
            h2 = hd + hw * (1 - amt * 0.9)
            shave = (m * (1 - w) * min(1, f)) > 0.2                     # dry impasto: the blade shaves the peaks
            if shave.any():
                lvl = float(np.percentile(hw[shave], 40))
                h2 = np.where(shave, np.minimum(h2, hd + lvl + np.maximum(hw - lvl, 0) * 0.5), h2)
            cv.ht[sl] = h2
            cv.wet[sl] = w * (1 - amt * 0.5)


class Oil(Medium):
    name = "oil"
    arrays = ("col", "wet", "ht", "hdry", "fat", "sheen", "under", "varn")
    supports = {"canvas": "linen or cotton canvas, primed; the weave shows through thin paint and catches dry-brush",
                "panel": "gessoed wooden panel: smooth, hard, no weave; every stroke edge shows"}
    tools = {"round": "round hog brush with a pointed tip: a thin line at light pressure, a fat teardrop blob when pressed",
             "flat": "long flat hog brush: square-edged planes, chisel strokes, strong furrows",
             "bright": "short stiff flat: short, thick, heavily furrowed dabs; runs out fast",
             "filbert": "flat with a rounded tip: soft-edged leaf-shaped marks, gentler furrows",
             "fan": "fan brush: sparse spread hairs, parallel fine lines (grass, hair, foliage)",
             "liner": "rigger/liner: long thin soft hair, long even lines of fluid paint (alias: rigger)",
             "knife": "palette knife: flat slabs with crisp edges and smooth tops; empty (or scrape: true) it scrapes back toward the layer beneath",
             "rag": "rag: wipes wet paint out toward the dried layer or ground beneath (lights in an imprimatura)",
             "smudge": "finger: pushes and smears wet paint (alias: finger)",
             "blend": "soft dry blender: softens wet paint and edges (sfumato) (alias: blender)",
             "scraper": "scraper / brush handle: sgraffito lines through wet paint, revealing the layer beneath"}
    finishes = {"varnish": "final varnish once fully dry ({\"gloss\": 0 matte .. 1 gloss, default 0.85}): evens the sheen, deepens darks, raises chroma; refuses while wet",
                "retouch": "retouch varnish where touch-dry: brings sunken (dull) passages back to an even gloss",
                "oil-out": "rub a thin film of oil over sunken passages before working on (like retouch, slightly wet)",
                "glaze": "a final unifying glaze ({\"color\", \"opacity\", optional \"region\" {type rect/ellipse/poly}, \"feather\"})"}

    # ---------------------------------------------------------------- canvas life
    def texture(self, h, w, support):
        if support == "panel":
            return (0.5 + 0.15 * (noise_field(h, w, 0.6, 7) - 0.5) + 0.04 * (noise_field(h, w, 6, 8) - 0.5)).astype(np.float32)
        return weave(h, w)

    def init_state(self, cv, ground):
        H, W = cv.H, cv.W
        cv.wet = np.zeros((H, W), np.float32)
        cv.ht = np.zeros((H, W), np.float32)
        cv.hdry = np.zeros((H, W), np.float32)
        cv.fat = np.full((H, W), 0.3, np.float32)        # a primed ground is lean
        cv.sheen = np.full((H, W), 0.35, np.float32)      # a primed ground is semi-matte
        cv.under = cv.col.copy()
        cv.varn = np.zeros((H, W), np.float32)

    # ---------------------------------------------------------------- the hand
    def make_tool(self, it, size, color, rng):
        kind = it.get("brush", "round")
        kind = ALIAS.get(kind, kind)
        if kind not in SPEC:
            kind = "round"
        if kind == "liner":
            b = Brush("liner", size, color, rng, load=it.get("load", 1.0), cover=it.get("cover", 0.97),
                      pickup=0.1, thick=it.get("impasto", 0.3), wetmix=it.get("wetmix", 0.2), edge="hard",
                      fat=it.get("fat"), streak=it.get("streak", 0.2))
            b.liner = True
            return b
        # the core's v8 hand passes a load that drifts across the passage (_load_mul) instead of a random one per stroke
        lm = it["_load_mul"] if "_load_mul" in it else rng.uniform(0.82, 1.12)
        return Brush(kind, size, color, rng, load=it.get("load", 1.0) * lm,
                     cover=it.get("cover", 0.95), pickup=it.get("pickup", 0.35), thick=it.get("impasto", 0.5),
                     wetmix=it.get("wetmix", 0.5), edge=it.get("edge", "soft"), fat=it.get("fat"),
                     streak=it.get("streak", 0.5), scrape=it.get("scrape"))

    # ---------------------------------------------------------------- glaze: a transparent film
    def glaze(self, cv, mask, col, op):
        _ensure(cv)
        col = np.asarray(col, np.float32)
        # the glaze paint is unmixed into the measured pigments: transparent lakes and ultramarine stay clear,
        # opaque paints (vermilion, chrome yellow, bone black) and white (a veil, scumble) cover more; the
        # film is laid over the colour beneath band by band (spectral Kubelka-Munk, media/spectral.py)
        hs = self._surface(cv)
        hollow = np.clip((gaussian_filter(hs, 2.5) - hs) * 6, -0.5, 1)   # a glaze pools in the hollows
        x = mask * op * GLAZE_FILM * (1 + 0.5 * hollow)
        before = cv.col
        film = spectral.glaze(before, col, x, ref=GLAZE_FILM)
        w = cv.wet
        # over wet paint the glaze's pigments (not its oil) partly mix in
        cg, med = spectral.glaze_paint(col, GLAZE_FILM)
        tm = np.clip(mask * op * 0.8 * (1 - med), 0, 1)
        mixed = before.copy()
        sel = (w > 0.005) & (tm > MIX_MIN)
        if sel.any():
            gpaint = spectral.forward(cg / max(float(cg.sum()), 1e-6))
            mixed[sel] = spectral.mix(before[sel], gpaint, tm[sel][:, None])
        ww = np.clip(w * 0.6, 0, 0.6)[..., None]                         # over wet paint it partly mixes in
        cv.under = np.where((w < 0.15)[..., None], before, cv.under)
        cv.hdry = np.where(w < 0.15, cv.ht, cv.hdry)
        cv.col = (film * (1 - ww) + mixed * ww).astype(np.float32)
        g = np.clip(mask * min(1.0, op * 3), 0, 1)
        cv.wet = np.maximum(cv.wet, g * 0.85)
        cv.fat = cv.fat + g * (0.72 - cv.fat)
        cv.sheen = cv.sheen + g * (0.82 - cv.sheen)
        cv.varn = cv.varn * (1 - g)

    # ---------------------------------------------------------------- time
    def _dry(self, cv, amount):
        _ensure(cv)
        # thin paint dries faster than thick; oil-rich paint a little slower
        k = 1.7 / (1 + 2.5 * np.maximum(cv.ht - cv.hdry, 0) + 1.2 * cv.ht) * (1.15 - 0.3 * cv.fat)
        cv.wet = (cv.wet * (1 - min(amount, 1.0)) ** k).astype(np.float32)
        if amount >= 0.999:
            cv.wet[:] = 0
        set_ = cv.wet < 0.15
        cv.under = np.where(set_[..., None], cv.col, cv.under).astype(np.float32)
        cv.hdry = np.where(set_, cv.ht, cv.hdry).astype(np.float32)

    def episode_end(self, cv):
        self._dry(cv, 0.07)
        n = getattr(cv, "_oil_fol", 0)
        if n > 400:
            print(f"[oil] craft note: lean paint over a fatter, drying layer in about {n} px. Fat over lean: each "
                  f"layer should hold as much oil as the one beneath or more (raise \"fat\").")
        cv._oil_fol = 0

    def dry(self, cv, amount):
        self._dry(cv, float(amount))

    # ---------------------------------------------------------------- seeing
    def _surface(self, cv):
        """Height of the visible surface: paint relief plus the weave showing through thin paint."""
        relief = 0.12 if cv.meta.get("support") != "panel" else 0.05
        return cv.ht + relief * cv.tex * np.exp(-cv.ht * 5.0)

    def render(self, cv):
        _ensure(cv)
        hs = self._surface(cv)
        hs = gaussian_filter(hs, 0.75) * (1 - 0.3 * cv.varn) + gaussian_filter(hs, 1.6) * 0.3 * cv.varn
        gy, gx = np.gradient(hs * 2.6)
        lightdot = -gx * 0.55 - gy * 0.8                        # raking light from the upper left
        g = np.clip(cv.sheen + (0.92 - cv.sheen) * cv.wet, 0, 1)   # wet paint is glossy; dry paint shows its sheen
        col = cv.col
        m = col.mean(-1, keepdims=True)
        col = m + (col - m) * (1 + 0.12 * (g - 0.6))[..., None]    # a wetted, glossy surface is more saturated
        sw = (0.085 * (1 - g) ** 1.5)[..., None]                   # the surface white of a dull or sunken surface
        col = col * (1 - sw) + sw * np.array([0.96, 0.95, 0.92], np.float32)
        shade = 1 + np.clip(lightdot, -0.16, 0.16)
        img = col * shade[..., None]
        spec = (np.clip(lightdot - 0.07, 0, 0.6) ** 1.3) * (0.04 + 0.28 * g ** 2)
        img = np.clip(img + spec[..., None], 0, 1)
        return Image.fromarray((img * 255).astype(np.uint8))

    # ---------------------------------------------------------------- revision
    def revise(self, cv, op, mask, it, felt, rng, core):
        """scrape: the palette knife scrapes wet paint back toward the layer beneath (its scrape mode), and on
        dry paint the blade shaves the impasto and bares the ground on the tops of the weave (how a scraped-back
        canvas looks); wipe: the rag lifts wet paint toward the dried layer or ground; paintout: the core's
        default (the surrounding colour brushed over the passage)."""
        _ensure(cv)
        if op == "scrape":
            core.sweep(cv, mask, it, felt, rng, "knife", extra={"scrape": True}, passes=int(it.get("passes", 2)))
            dry = mask * np.clip(1 - cv.wet * 2, 0, 1)
            if dry.max() > 0.05:
                g = hx(cv.meta.get("ground", "#c8b89a"))
                # the blade takes the tops of the weave first (tooth^2), more with strength (0..1); eye
                amt = np.clip(dry * float(it.get("strength", 0.7)) * (0.15 + 0.85 * cv._oil_tooth ** 2) * 0.8, 0, 0.95)
                cv.col = (cv.col * (1 - amt[..., None]) + g * amt[..., None]).astype(np.float32)
                cv.ht = np.maximum(cv.ht - amt * np.maximum(cv.ht - 0.05, 0), 0).astype(np.float32)
                cv.hdry = np.minimum(cv.hdry, cv.ht)
                cv.under = np.where((amt > 0.01)[..., None], cv.col, cv.under).astype(np.float32)
            return True
        if op == "wipe":
            wet = float((cv.wet[mask > 0.5] > 0.15).mean()) if (mask > 0.5).any() else 0.0
            if wet < 0.2:
                print(f"[oil] wipe: only {wet:.0%} of the passage is still wet; a rag lifts wet paint only. Scrape dry paint back instead.")
            core.sweep(cv, mask, it, felt, rng, "rag", passes=int(it.get("passes", 2)))
            return True
        return NotImplemented

    def finish_check(self, cv):
        """Did the finishing do its job (docs/FINISHING.md "Oil")? Dry before varnish, no sunken (matte)
        passages left after retouch or varnish, an even gloss. Thresholds are judgements (eye)."""
        _ensure(cv)
        lines, flags = [], []
        ops = [f["op"] for f in cv.meta.get("finishes", [])]
        wet = float((cv.wet > 0.05).mean())
        dry = cv.wet < 0.2
        sunk = float((dry & (cv.sheen < 0.6)).mean())
        even = float(cv.sheen[dry].std()) if dry.any() else 0.0
        lines.append(f"oil: wet {wet:.0%} of the surface, sunken (matte) {sunk:.0%}, gloss spread {even:.2f}, "
                     + ("varnished" if "varnish" in ops else "not varnished"))
        if wet > 0.05 and "varnish" not in ops:
            flags.append(f"{wet:.0%} of the paint is still wet: dry it before varnishing")
        if sunk > 0.03:
            flags.append(f"sunken (matte) passages over {sunk:.0%} of the surface: retouch or oil out" + (" (the varnish should have evened them)" if "varnish" in ops else ""))
        if even > 0.12:
            flags.append(f"uneven gloss (sheen spread {even:.2f}): retouch the dull passages or varnish")
        return lines, flags

    # ---------------------------------------------------------------- finishing
    def _region(self, cv, params):
        reg = params.get("region")
        if not reg or reg.get("type", "canvas") == "canvas":
            return np.ones((cv.H, cv.W), np.float32)
        m = Image.new("L", (cv.W, cv.H), 0)
        d = ImageDraw.Draw(m)
        t = reg["type"]
        if t == "ellipse":
            d.ellipse([reg["cx"] - reg["rx"], reg["cy"] - reg["ry"], reg["cx"] + reg["rx"], reg["cy"] + reg["ry"]], fill=255)
        elif t == "rect":
            d.rectangle([reg["x"], reg["y"], reg["x"] + reg["w"], reg["y"] + reg["h"]], fill=255)
        elif t == "poly":
            d.polygon([tuple(p) for p in reg["pts"]], fill=255)
        return gaussian_filter(np.asarray(m, np.float32) / 255, params.get("feather", 30))

    def finish(self, cv, op, params):
        _ensure(cv)
        params = params or {}
        if op == "varnish":
            wmax = float(cv.wet.max())
            if wmax > 0.05:
                frac = float((cv.wet > 0.05).mean()) * 100
                print(f"[oil] varnish refused: the paint is not dry throughout ({frac:.0f}% of the surface still "
                      f"wet, max {wmax:.2f}); varnish over wet paint traps solvent and stays tacky. Run `dry 1` first.")
                return
            G = float(np.clip(params.get("gloss", 0.85), 0, 1))
            cv.sheen[:] = G
            cv.varn[:] = 1.0
            print(f"[oil] varnished (gloss {G:.2f})")
            return
        if op in ("retouch", "oil-out"):
            ok = cv.wet < 0.2
            sunk = ok & (cv.sheen < 0.6)
            if op == "retouch":
                cv.sheen = np.where(sunk, 0.7, cv.sheen).astype(np.float32)
                cv.varn = np.where(ok, np.maximum(cv.varn, 0.3), cv.varn).astype(np.float32)
            else:
                cv.sheen = np.where(sunk, 0.72, cv.sheen).astype(np.float32)
                cv.wet = np.where(sunk, np.maximum(cv.wet, 0.12), cv.wet).astype(np.float32)
                cv.fat = np.where(sunk, np.minimum(1, cv.fat + 0.15), cv.fat).astype(np.float32)
            skipped = float((~ok & (cv.ht > 0.02)).mean()) * 100
            print(f"[oil] {op}: {float(sunk.mean()) * 100:.0f}% of the surface was sunken in"
                  + (f"; {skipped:.0f}% still too wet, left alone" if skipped > 0.5 else ""))
            return
        if op == "glaze":
            col = hx(params.get("color", "#6b4a2e"))
            self.glaze(cv, self._region(cv, params), col, float(params.get("opacity", 0.15)))
            return
        raise SystemExit(f"oil has no finishing step '{op}'. Available: {', '.join(self.finishes)}")
