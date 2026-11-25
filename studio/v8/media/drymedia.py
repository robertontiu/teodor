"""Dry media: charcoal, graphite and soft pastel (with an oil-pastel stick). No water, no oil to dry:
the medium is dust or a soft lead dragged over a paper whose surface is a landscape of tiny peaks and
hollows (its "tooth").

The model (docs/MEDIA.md, "Engine model (dry media)"; Sousa & Buchanan's pencil-on-paper model [S27]):
- The paper is a height field (cv.tex, 0..1, histogram-equalised so a threshold is a share of the
  surface). A stick touches the peaks first: its pressure (and softness) sets how far the contact
  plane sinks into the hollows. Light pressure = speckled marks on the peaks; heavy = filled.
- The tooth holds a limited amount (`cap` per support, plus `xcap` that workable fixative restores).
  `dep` is what lies in it. Deposits shrink as the tooth fills, so further layers slide; on full tooth
  a pastel stick smears instead of covering.
- Each deposit is opaque dust laid side by side with the paper: the apparent colour is an optical
  (linear) mix, col <- col*(1-f) + stick*f with f = 1 - exp(-KC*added). Pastel sits on top.
- `loose` is the unbound dust a stump, finger or chamois can move; `fix` is what no eraser lifts
  (charcoal's stain, compressed binder, fixed layers). Erasers take loose dust first, then some of the
  bound, and leave ghosts. Blenders blur and drag pigment, which fills the hollows.
- Charcoal and graphite are monochrome: the colour you ask for gives only the VALUE the hand works
  toward (the deposit stops once that value is reached). Asking for a value lighter than the paper
  picks up white chalk on toned paper or the kneaded eraser on white paper (erasing as drawing).
- Graphite has grades 4H..8B (hardness, darkness, smudginess) and builds a metallic sheen with
  pressure and burnishing; the render shows it as a silvery shine under a raking light. A stylus
  indents the paper so later tone skips the groove.

Numbers: the structure and the directions of every effect come from the sources above; the numeric
values (pigment values, KC, tooth capacities, flows, rates, render constants) are hand-tuned starting
values. docs/manual/{charcoal,graphite,pastel}.md list them under "Calibration".
"""
import math
import numpy as np
from scipy.ndimage import gaussian_filter, gaussian_filter1d, distance_transform_edt, convolve
from PIL import Image, ImageDraw
from .base import Medium, hx, noise_field, kmix

KC = 3.5   # coverage per unit of deposit: 1 - exp(-KC*dep)


def _eq(a):
    """Histogram-equalise to 0..1, so `tex > 1 - r` is a fraction r of the surface."""
    q = np.quantile(a, np.linspace(0, 1, 513))
    q = np.maximum.accumulate(q + np.arange(513) * 1e-9)
    return np.interp(a, q, np.linspace(0, 1, 513)).astype(np.float32)


def _zn(h, w, sigma, rng):
    """Gaussian-filtered white noise, zero mean and unit std (so weights are amplitudes)."""
    n = gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), sigma) if sigma > 0 else rng.standard_normal((h, w)).astype(np.float32)
    return (n - n.mean()) / (n.std() + 1e-6)


def _fibres(h, w, rng, length_px, density=0.035):
    """Short fibres at random orientations: sparse seeds drawn out along 4 directions (felted paper)."""
    L = int(np.clip(round(length_px), 3, 9)) | 1
    out = np.zeros((h, w), np.float32)
    c = L // 2
    for k in range(4):
        a = math.radians(45 * k + rng.uniform(-15, 15))
        ker = np.zeros((L, L), np.float32)
        for t in np.linspace(-c, c, 4 * L):
            ker[int(round(c + t * math.sin(a))), int(round(c + t * math.cos(a)))] = 1.0
        ker /= ker.sum()
        s = (rng.random((h, w)) < density / 4).astype(np.float32)
        out += convolve(s, ker, mode="wrap")
    return (out - out.mean()) / (out.std() + 1e-6)


def paper_texture(h, w, kind, ppm=2.5, seed=11):
    """The paper's tooth as a height field, at the studio's stated scale `ppm` (px per mm).

    Measured on the Met references (docs/calibration/charcoal.md): the tooth of drawing papers shows as
    light specks of 0.06-0.15 mm inside marks (the photographs' resolution limit), i.e. below one studio
    pixel; blank paper at the studio scale has a grain std of 0.5-1.1 L* with a correlation length of
    one pixel. So the height field is dominated by pixel-scale grain (no mm-sized blobs: the old
    0.85/2.2/8 px mixture read as camouflage), with fibres and a faint formation cloud. Laid papers:
    laid lines every 0.9 mm (two sheets measured: 0.90 and 0.91 mm; a third 1.23 mm) and chain lines
    about every 35 mm (32.8 and 37.3 mm, weak peaks). The mixing weights are tuned to the measured grain
    statistics; the fibre length (1.5 mm) and the cloud scale are tuned by eye."""
    rng = np.random.default_rng(seed)
    grain = _zn(h, w, 0.5, rng) + 0.45 * _zn(h, w, 1.0, rng)
    fib = _fibres(h, w, rng, 1.5 * ppm)
    cloud = _zn(h, w, 1.5 * ppm, rng)
    if kind == "laid":
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        per = 0.9 * ppm                                   # measured laid-line period
        wob = 0.25 * per * _zn(h, w, 6 * ppm, rng)
        lines = np.sin(2 * np.pi * (y + wob) / per)
        cper = 35.0 * ppm                                 # measured chain-line spacing
        cx = (x + 0.04 * cper * np.sin(y / (0.8 * cper))) % cper
        chain = np.exp(-((cx - cper / 2) ** 2) / (2 * (0.25 * ppm) ** 2))
        t = grain + 0.5 * fib + 0.9 * lines - 1.2 * chain + 0.3 * cloud
    elif kind == "honeycomb":           # pastel paper's honeycomb side: cells with raised rims, ~0.8 mm
        cell = max(2.0, 0.8 * ppm)
        k = int(h * w / cell ** 2)
        seeds = np.ones((h, w), bool)
        seeds[rng.integers(0, h, k), rng.integers(0, w, k)] = False
        d = distance_transform_edt(seeds).astype(np.float32)
        d = (d - d.mean()) / (d.std() + 1e-6)
        t = 0.8 * d + grain + 0.4 * fib + 0.3 * cloud
    elif kind == "sanded":              # dense fine grit: almost pure pixel-scale grain
        t = grain + 0.15 * cloud
    elif kind == "smooth":              # bristol: little tooth, a smoother, cloudier surface
        t = 0.6 * grain + 0.3 * fib + 0.8 * _zn(h, w, 0.6 * ppm, rng)
    else:                               # drawing paper: fine irregular tooth, fibres, a faint cloud
        t = grain + 0.6 * fib + 0.35 * cloud
    return _eq(t)


def _lum(c):
    return c.mean(-1)


def _cov(d):
    return 1 - np.exp(-KC * np.maximum(d, 0))


# ---------------------------------------------------------------- the hand's tools
class DryTool:
    """One stick, blender, eraser or stylus. The core sets .size, .step, .speedfx while playing.

    A stick does not lay its dust dab by dab: it records the contacts along the stroke and lays the
    whole stroke when the stroke ends (`end`, which the core calls after every stroke). Per pixel the
    stroke gives the deepest reach into the tooth (which hollows it touched) and the summed rubbing
    (how much dust it left), then the tooth, the asked value and the colour are applied once. Same
    physics as one dab at a time, about five times faster, so hatching and `match` stay quick."""

    def __init__(self, medium, spec, size, color, rng, it):
        self.m, self.spec, self.rng = medium, dict(spec), rng
        self.kind = spec["kind"]
        self.size = min(size * spec.get("sizef", 1.0), spec.get("maxsize", 1e9))   # a stick is only so big
        self.color = np.asarray(color, np.float32).copy()
        self.step, self.speedfx = 1.0, 0.0
        self.tilt = float(rng.uniform(-0.35, 0.35))          # side of the stick presses harder at one end
        self.carry, self.carry_dep = None, 0.0
        self.liner = spec.get("liner", False)
        self.first = True
        self.wear = 0.0
        self.q = []
        self.edge_px = max(1.0, spec.get("edge_mm", medium.EDGE_MM) * medium.PPM / 0.8)
        # the broken face of the stick: a fixed relief along its length, so a side stroke is streaked
        # along its direction (tuned by eye: real side strokes show such striations)
        self.face = gaussian_filter1d(rng.standard_normal(64), 2.0).astype(np.float32)
        self.face = self.face / (np.abs(self.face).max() + 1e-6)

    # -- contact shapes
    def mask(self, r, u, v, pe=None, j0=0.0, j1=0.0):
        sh = self.spec["shape"]
        if pe is None:
            pe = getattr(self, "_pe", 0.7)
        if sh == "tip":                  # round end of a stick or pencil point
            # the dust thins out over the line's edge: a ramp whose 10-90% width is the medium's measured
            # edge rise (EDGE_MM; at least the 1 px of antialiasing)
            d = np.sqrt(u * u * 1.15 + v * v)
            wd = self.edge_px
            return np.clip((r - d) / wd + 0.5, 0, 1)
        if sh == "side":                 # stick laid on its side, across the stroke
            along = np.clip(1 - np.abs(u) / max(2.5, r * 0.22), 0, 1)
            # light pressure: only the end the hand tilts onto touches (wedge-shaped starts and ends).
            # The ends of the contact drift smoothly along the stroke (j0, j1: a broken stick's ends),
            # and the pressure falls off toward them (a stick is not flat): soft, wobbly band edges
            c = float(np.clip(0.15 + 0.85 * pe / 0.8, 0.15, 1.0))
            sgn = 1.0 if self.tilt >= 0 else -1.0
            lo, hi = (-r, -r + 2 * r * c) if sgn > 0 else (r - 2 * r * c, r)
            lo += j0 * r; hi += j1 * r
            e = max(1.5, 0.3 * r, self.edge_px)
            across = np.clip(np.minimum(v - lo, hi - v) / e, 0, 1)
            across = across * across * (3 - 2 * across)
            prof = np.clip(1 + self.tilt * (v / max(r, 1)) * sgn * -1, 0.3, 1.3)
            k = np.clip((v / max(r, 1) + 1) * 31.5, 0, 63).astype(np.int32)
            streak = 1 + 0.35 * self.face[k]
            return along * across * prof * streak
        if sh == "blade":
            along = np.clip(0.9 - np.abs(u) + 0.5, 0, 1)
            return along * np.clip(r - np.abs(v) + 0.5, 0, 1)
        if sh == "hard":                 # eraser corner: crisp disc
            return np.clip(r - np.sqrt(u * u + v * v) + 0.5, 0, 1)
        d2 = (u * u + v * v) / max(r * r, 1e-3)    # soft: stump, finger, kneaded eraser
        return np.clip(np.exp(-2.2 * d2) - 0.02, 0, 1)

    def _first(self, cv):
        """Monochrome media: decide, against this paper, whether the asked value is a dark (draw),
        or a light (white chalk on toned paper, kneaded lift on white paper)."""
        self.first = False
        self.pl = float(_lum(cv.paper[::16, ::16].reshape(-1, 3)).mean())
        if not self.spec.get("mono") or self.kind != "stick":
            return
        t = float(_lum(self.color))
        pl = self.pl
        if t > pl + 0.04:
            if pl < 0.82 and "white_chalk" in self.m.TOOLS:
                self.spec = dict(self.m.TOOLS["white_chalk"])
            else:
                self.spec = dict(self.m.TOOLS["kneaded"]); self.kind = "erase"
            self.spec["auto"] = True
            self.spec["mono"] = True

    def _ext(self, r):
        sh = self.spec["shape"]
        return max(2.5, r * 0.22) if sh == "side" else (1.4 if sh == "blade" else r)

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        if self.first:
            self._first(cv)
        r = max(0.6, self.size / 2 * rscale)
        if self.kind == "stick":         # recorded; laid at the end of the stroke
            self.q.append((float(x), float(y), float(ang), float(press), r, float(getattr(self, "step", 1.0)),
                           float(getattr(self, "speedfx", 0.0))))
            if len(self.q) > 4000:       # a very long stroke: lay what we have
                self.end(cv)
            return
        R = int(math.ceil(r)) + 2
        x0, x1 = max(0, int(x) - R), min(cv.W, int(x) + R + 1)
        y0, y1 = max(0, int(y) - R), min(cv.H, int(y) + R + 1)
        if x0 >= x1 or y0 >= y1:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dx, dy = xx - x, yy - y
        ca, sa = math.cos(ang), math.sin(ang)
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        self._pe = float(press)
        m = self.mask(r, u, v)
        if cv.clip is not None:
            m = m * cv.clip[y0:y1, x0:x1]
        if m.max() <= 0.01:
            return
        sl = (slice(y0, y1), slice(x0, x1))
        pe = float(press) * (1 - 0.55 * min(1.0, getattr(self, "speedfx", 0.0)))
        ds = min(1.0, getattr(self, "step", 1.0) / max(self._ext(r), 1.0))
        getattr(self, "_" + self.kind)(cv, sl, m, pe, ds, r)

    def end(self, cv):
        if self.kind == "stick" and self.q:
            q, self.q = self.q, []
            self._stroke(cv, q)

    # -- a stick lays dust on the tooth (one whole stroke)
    def _stroke(self, cv, q):
        sp, M = self.spec, self.m
        sup = M.sup(cv)
        Q = np.asarray(q, np.float32)
        xs, ys, angs, press, rs, steps, sfx = Q.T
        Rmax = int(math.ceil(float(rs.max()))) + 2
        x0, x1 = max(0, int(xs.min()) - Rmax), min(cv.W, int(xs.max()) + Rmax + 1)
        y0, y1 = max(0, int(ys.min()) - Rmax), min(cv.H, int(ys.max()) + Rmax + 1)
        if x0 >= x1 or y0 >= y1:
            return
        h, w = y1 - y0, x1 - x0
        A = np.zeros((h, w), np.float32)        # summed rubbing (amount of dust offered)
        RE = np.zeros((h, w), np.float32)       # deepest reach into the tooth
        P2 = np.zeros((h, w), np.float32)       # heaviest pressure (crushed dust, oil-pastel blending)
        BU = np.zeros((h, w), np.float32) if sp.get("burnish") else None
        SL = np.zeros((h, w), np.float32) if sp.get("slide") else None
        P = self.color if sp.get("P") is None else np.asarray(sp["P"], np.float32)
        mono = bool(sp.get("mono"))
        if mono:
            t, Pl = float(_lum(self.color)), float(_lum(P))
            want = float(np.clip((t - self.pl) / (Pl - self.pl), 0, 1)) if abs(Pl - self.pl) > 1e-3 else 0.0
            pmul = 0.5 + 0.75 * want            # the hand presses as hard as the asked value needs
        else:
            pmul = 1.0
        rk, grab = sp["reach"], sup["grab"]
        n = len(q)
        if sp["shape"] == "side":               # smooth drift of the contact's ends along the stroke
            sig = max(2.0, float(np.median(rs)) * 0.6 / max(float(np.median(steps)), 0.3))
            jit = [gaussian_filter1d(self.rng.standard_normal(n), sig, mode="nearest") for _ in range(2)]
            jit = [0.08 * j / (j.std() + 1e-6) for j in jit]
        else:
            jit = [np.zeros(n), np.zeros(n)]
        clip = cv.clip[y0:y1, x0:x1] if cv.clip is not None else None
        if sp["shape"] == "side":
            # the side of a stick lands and lifts over a stretch of travel: the contact builds up and
            # fades instead of starting and stopping on a straight cut (short side strokes in `match`
            # read as hard-edged blocks otherwise); while it lands and lifts only the end the hand tilts onto
            # touches, so the band's ends are wedges, not square cuts. Fade length 1.0 r: tuned by eye.
            arc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(xs), np.diff(ys)))])
            Lf = max(2.0, 1.0 * float(np.median(rs)))
            sm = lambda z: z * z * (3 - 2 * z)
            fade = sm(np.clip(arc / Lf, 0, 1)) * sm(np.clip((arc[-1] - arc) / Lf, 0, 1))
            fade = np.maximum(fade, 0.15)
        else:
            fade = np.ones(n, np.float32)
        for i in range(n):
            x, y, ang, pr, r = float(xs[i]), float(ys[i]), float(angs[i]), float(press[i]), float(rs[i])
            R = int(math.ceil(r)) + 2
            a0, a1 = max(x0, int(x) - R), min(x1, int(x) + R + 1)
            b0, b1 = max(y0, int(y) - R), min(y1, int(y) + R + 1)
            if a0 >= a1 or b0 >= b1:
                continue
            dx = (np.arange(a0, a1, dtype=np.float32) - x)[None, :]
            dy = (np.arange(b0, b1, dtype=np.float32) - y)[:, None]
            ca, sa = math.cos(ang), math.sin(ang)
            u, v = dx * ca + dy * sa, -dx * sa + dy * ca
            m = self.mask(r, u, v, pr * (0.3 + 0.7 * float(fade[i])), float(jit[0][i]), float(jit[1][i]))
            if clip is not None:
                m = m * clip[b0 - y0:b1 - y0, a0 - x0:a1 - x0]
            pe = pr * (1 - 0.55 * min(1.0, float(sfx[i]))) * pmul
            ds = min(1.0, float(steps[i]) / max(self._ext(r), 1.0))
            s = (slice(b0 - y0, b1 - y0), slice(a0 - x0, a1 - x0))
            m = m * float(fade[i])
            A[s] += m * (ds * (0.25 + 0.75 * pe))
            reach = min(1.3, (0.1 + 1.25 * pe) * rk * grab)
            np.maximum(RE[s], np.clip(m * 2.0, 0, 1) * reach, out=RE[s])
            np.maximum(P2[s], np.clip(m * 2.0, 0, 1) * pe, out=P2[s])
            if BU is not None and pe > 0.82:
                BU[s] += m * ((pe - 0.82) * ds * 2.5)
            if SL is not None:
                SL[s] += m * (ds * pe * 0.12)
        self.wear += 0.002 * float(np.minimum(1.0, steps / 2.0).sum())
        live = A > 1e-4
        if not live.any():
            return
        sl = (slice(y0, y1), slice(x0, x1))
        tex = cv.tex[sl]
        ind = getattr(cv, "indent", None)
        if ind is not None:
            tex = tex - 1.6 * ind[sl]
        col, dep = cv.col[sl], cv.dep[sl]
        catch = np.clip((tex - (1 - RE)) / (sup["w"] * sp.get("w", 1.0) * M.W_SUB), 0, 1)
        catch = catch + (1 - catch) * 0.22 * P2 * P2 * sp.get("smear", 1.0)    # crushed dust in the hollows
        cap = sup["cap"] + cv.xcap[sl]
        left = np.clip((cap - dep) / cap, 0, 1)
        if sp.get("oily"):
            left = np.maximum(left, 0.45)          # wax rides over full tooth as a film
        elif sp.get("grip"):
            left = np.maximum(left, sp["grip"] * (dep > 0.05))   # pastel grips pastel a little
        a = A * catch * (sp["flow"] * 0.5) * left
        f = 1 - np.exp(-KC * a)
        if sp.get("oily"):                          # oil pastel blends subtractively by pressure
            Pp = kmix(np.broadcast_to(P, col.shape), col, (0.25 * P2)[..., None])
        else:
            Pp = P[None, None, :]
        if mono:                                    # monochrome: work toward the asked value only
            # peaks may go a little past the asked value; the area as a whole stops at it
            L = _lum(col); d = Pl - L
            sg = 1.0 if Pl < self.pl else -1.0
            tp = t - sg * 0.12 * min(1.0, 4 * want)     # a value at the paper's own tone leaves (almost) nothing
            ok = np.abs(d) > 1e-3
            fmax = np.clip(np.where(ok, (tp - L) / np.where(ok, d, 1), 0), 0, 1)
            f0 = f
            f = np.minimum(f, fmax)
            w8 = (A > 0.02).astype(np.float32)
            sg2 = max(1.0, float(np.median(rs)))
            gw = gaussian_filter(w8, sg2) + 1e-6
            Lm = gaussian_filter(L * w8, sg2) / gw
            dl = gaussian_filter(f * d * w8, sg2) / gw
            sc = np.where(np.abs(dl) > 1e-6, np.clip((t - Lm) / np.where(np.abs(dl) > 1e-6, dl, 1), 0, 1), 0.0)
            f = f * sc
            a = a * f / np.maximum(f0, 1e-6)
        cv.col[sl] = col * (1 - f[..., None]) + Pp * f[..., None]
        cv.dep[sl] = dep + a
        cv.loose[sl] = cv.loose[sl] + a * sp["loose"]
        cv.fix[sl] = cv.fix[sl] + a * sp["stain"]
        if hasattr(cv, "sheen") and sp.get("sheen", 0) > 0:
            cv.sheen[sl] = np.clip(cv.sheen[sl] + a * sp["sheen"] * (0.4 + P2), 0, 1.5)
        if BU is not None and BU.max() > 0:         # graphite: hard pressure flattens the tooth, slick dark
            cv.dep[sl] = cv.dep[sl] + BU * np.clip(cap - cv.dep[sl], 0, None)
            if hasattr(cv, "sheen"):
                cv.sheen[sl] = np.clip(cv.sheen[sl] + BU * 0.6 * _cov(cv.dep[sl]), 0, 1.5)
        if SL is not None:                          # pastel on a full tooth slides and smears
            s = np.clip(SL * (1 - left), 0, 0.6)
            if s.max() > 0.01:
                c2 = cv.col[sl]
                loc = (c2 * s[..., None]).sum((0, 1)) / (s.sum() + 1e-6)     # the colour the stick drags along
                tgt = loc * 0.75 + self.color * 0.25
                cv.col[sl] = c2 + (tgt[None, None, :] - c2) * s[..., None]

    # -- blenders move the loose dust and fill the hollows
    def _smudge(self, cv, sl, m, pe, ds, r):
        sp = self.spec
        col, dep, loose, fix = cv.col[sl], cv.dep[sl], cv.loose[sl], cv.fix[sl]
        free = np.clip(dep - fix, 0, None)
        mov = np.minimum(free, loose + (free - np.minimum(loose, free)) * sp["bound"])
        mob = np.where(dep > 1e-4, mov / np.maximum(dep, 1e-4), 1.0)
        ind = getattr(cv, "indent", None)
        guard = 1 - np.clip(ind[sl], 0, 1) if ind is not None else 1.0
        amt = np.clip(m * pe * sp["blur"] * min(1.0, ds * 3.0), 0, 0.9) * guard
        sig = max(0.8, r * sp.get("sig", 0.33))
        bc = np.stack([gaussian_filter(col[..., i], sig, mode="nearest") for i in range(3)], -1)
        bd = gaussian_filter(dep, sig, mode="nearest")
        bl = gaussian_filter(loose, sig, mode="nearest")
        k = (amt * np.clip(mob * 1.6, 0, 1))
        col = col + (bc - col) * k[..., None]
        # rubbed-in dust is spread thinner and more evenly, so the same amount covers more paper:
        # cov(mean dep) >= mean(cov(dep)); bounded, and a fixed point once the tone is even
        pap = cv.paper[sl]
        bcv = gaussian_filter(_cov(dep), sig, mode="nearest")
        g = np.clip(_cov(bd) / np.maximum(bcv, 0.02), 1, 1.6)
        g = 1 + (g - 1) * k
        col = np.clip(pap + (col - pap) * g[..., None], 0, 1)
        dep = dep + (bd - dep) * k
        loose = loose + (bl - loose) * k
        # drag: the blender carries tone along the stroke (and pulls it out over bare paper)
        ms = m.sum() + 1e-6
        loc = (col * m[..., None]).sum((0, 1)) / ms
        locd = float((dep * m).sum() / ms)
        locmov = float((mov * m).sum() / ms)
        if self.carry is None:
            self.carry, self.carry_dep = loc.copy(), locd
        dr = np.clip(m * pe * sp["drag"] * min(1.0, ds * 1.2), 0, 0.6) * guard
        dr = dr * np.clip((self.carry_dep - dep) * 5, 0, 1)     # it only pulls tone toward where there is less
        col = col + (self.carry[None, None, :] - col) * dr[..., None]
        dep = dep + (self.carry_dep - dep) * dr
        loose = loose + np.clip(self.carry_dep - dep, 0, None) * dr
        ck = min(0.5, 0.35 * ds) * (0.3 + 0.7 * min(1.0, locmov / max(locd, 1e-3)))
        self.carry = self.carry * (1 - ck) + loc * ck
        self.carry_dep = self.carry_dep * (1 - ck) + locd * ck
        # pick-up: the blender takes a little away (a chamois a lot)
        pk = np.clip(m * pe * sp["pick"] * ds, 0, 0.5) * np.clip(mob, 0, 1)
        if pk.max() > 0:
            nd = dep * (1 - pk)
            ratio = np.where(dep > 1e-4, _cov(nd) / np.maximum(_cov(dep), 1e-6), 1.0)
            col = cv.paper[sl] + (col - cv.paper[sl]) * ratio[..., None]
            loose = loose * (1 - pk)
            dep = nd
        cv.col[sl], cv.dep[sl], cv.loose[sl] = col, dep, np.minimum(loose, dep)
        if hasattr(cv, "sheen") and sp.get("burnish"):
            cv.sheen[sl] = np.clip(cv.sheen[sl] + m * pe * ds * 0.03 * _cov(dep), 0, 1.5)

    # -- erasers lift: loose dust first, then some of the bound, never the stain
    def _erase(self, cv, sl, m, pe, ds, r):
        sp = self.spec
        col, dep, loose, fix = cv.col[sl], cv.dep[sl], cv.loose[sl], cv.fix[sl]
        lf = np.clip(m * (0.35 + 0.65 * pe) * sp["lift"] * min(1.0, ds * 1.3), 0, 1)
        if sp.get("auto"):          # lifting toward an asked light value: stop when it is reached
            L = _lum(col); t = float(_lum(self.color))
            lf = lf * np.clip((t - L) / 0.08, 0, 1)
        free = np.clip(dep - fix, 0, None)
        lo = np.minimum(loose, free)
        remL = lo * np.clip(lf * 1.3, 0, 1)
        remB = (free - lo) * np.clip(lf * self.m.bound_erase, 0, 1)
        nd = dep - remL - remB
        ratio = np.where(dep > 1e-4, _cov(nd) / np.maximum(_cov(dep), 1e-6), 1.0)
        cv.col[sl] = cv.paper[sl] + (col - cv.paper[sl]) * ratio[..., None]
        cv.dep[sl], cv.loose[sl] = nd, loose - remL
        if hasattr(cv, "sheen"):
            cv.sheen[sl] = cv.sheen[sl] * ratio
        if sp.get("rough"):          # a hard eraser scuffs the tooth a little (it takes more after)
            cv.xcap[sl] = np.clip(cv.xcap[sl] + m * pe * ds * 0.01, 0, 0.6)

    def _scrape(self, cv, sl, m, pe, ds, r):          # sgraffito through waxy oil pastel
        wax = np.clip(cv.sheen[sl] * 3, 0, 1) if hasattr(cv, "sheen") else 0
        lf = np.clip(m * pe * ds * 1.5, 0, 1) * wax
        dep = cv.dep[sl]
        nd = dep * (1 - lf)
        ratio = np.where(dep > 1e-4, _cov(nd) / np.maximum(_cov(dep), 1e-6), 1.0)
        cv.col[sl] = cv.paper[sl] + (cv.col[sl] - cv.paper[sl]) * ratio[..., None]
        cv.dep[sl] = nd
        cv.fix[sl] = np.minimum(cv.fix[sl], nd)
        cv.sheen[sl] = cv.sheen[sl] * (1 - lf)

    def _stylus(self, cv, sl, m, pe, ds, r):          # indent: later tone skips the groove
        if hasattr(cv, "indent"):
            cv.indent[sl] = np.clip(cv.indent[sl] + m * pe * ds * 1.2, 0, 1)


# ---------------------------------------------------------------- the shared medium
FALLBACK = {"round": "tip", "filbert": "tip", "liner": "tip", "flat": "side", "fan": "side",
            "blend": "stump", "smudge": "finger", "knife": "eraser"}


class DryMedium(Medium):
    """Shared by Charcoal, Graphite and Pastel."""
    name = "base"
    arrays = ("col", "paper", "dep", "loose", "fix", "xcap")
    SUP = {}
    TOOLS = {}
    DEFAULT = {"tip": None, "side": None}
    bound_erase = 0.55
    MAXSIZE = {}             # widest mark per contact shape (px): a pencil point is not a brush
    veil = None              # pigment of the broad veil (glaze); None = the asked colour
    PPM = 2.5                # the stated scale: px per mm of the sheet (1200 px = 48 cm)
    EDGE_MM = 0.75           # 10-90% edge rise of a stick's line (mm), measured on the references
    # softness of the catch: the tooth (0.06-0.15 mm specks) is finer than a pixel, so a pixel is partly
    # covered. Fitted to the grain std inside hatched passages at the studio scale (docs/calibration/); the
    # ratio between media follows the number of tooth cells per pixel (about 16 at 0.4 mm, 4 at 0.2 mm)
    W_SUB = 3.0
    veil_mono = True

    @property
    def tools(self):
        return {k: v["desc"] for k, v in self.TOOLS.items()}

    @property
    def supports(self):
        return {k: v["desc"] for k, v in self.SUP.items()}

    def sup(self, cv):
        if not hasattr(cv, "_sup"):
            cv._sup = self.SUP.get(cv.meta.get("support"), next(iter(self.SUP.values())))
        return cv._sup

    def texture(self, h, w, support):
        s = self.SUP.get(support, next(iter(self.SUP.values())))
        return paper_texture(h, w, s["tex"], self.PPM)

    def init_state(self, cv, ground):
        s = self.sup(cv)
        g = hx(ground) if isinstance(ground, str) and ground.startswith("#") else cv.col[0, 0]
        if s.get("tone") and _lum(g) > 0.7:         # toned paper: a light ground means "the paper's own tone"
            cv.col = np.clip(cv.col * (hx(s["tone"]) / np.maximum(g, 0.05)), 0, 1).astype(np.float32)
        L = _lum(cv.col)[..., None]                   # paper: tone variation only, no colour blotches
        g2 = hx(s["tone"]) if (s.get("tone") and _lum(g) > 0.7) else g
        cv.col = np.clip(g2[None, None, :] * (L / max(float(_lum(g2)), 1e-3)), 0, 1).astype(np.float32)
        cv.paper = cv.col.copy()
        for a in self.arrays:
            if a not in ("col", "paper"):
                setattr(cv, a, np.zeros((cv.H, cv.W), np.float32))

    def make_tool(self, it, size, color, rng):
        name = it.get("brush") or it.get("tool")
        if name not in self.TOOLS:
            fb = FALLBACK.get(name, "tip")
            name = self.DEFAULT.get(fb, fb) if fb in ("tip", "side") else fb
            if name not in self.TOOLS:
                name = {"finger": "stump", "eraser": "kneaded"}.get(name, self.DEFAULT["tip"])
        spec = dict(self.TOOLS[name])
        spec.setdefault("maxsize", self.MAXSIZE.get(spec.get("shape"), 1e9) if spec["kind"] == "stick" else 1e9)
        spec = self.adjust(spec, it)
        t = DryTool(self, spec, size, color, rng, it)
        if it.get("brush") == "liner":
            t.liner = True
        return t

    def adjust(self, spec, it):
        return spec

    def glaze(self, cv, mask, col, op):
        """The dry 'glaze': a light veil laid with the side of the stick (catches the peaks) and
        rubbed in (fills the hollows a little), or powdered tone."""
        s = self.sup(cv)
        op = float(np.clip(op, 0, 1))
        reach = min(1.1, (0.3 + 0.6 * op) * s["grab"])
        tex = cv.tex - 1.6 * getattr(cv, "indent", 0)
        catch = np.clip((tex - (1 - reach)) / (s["w"] * self.W_SUB), 0, 1)
        cap = s["cap"] + cv.xcap
        left = np.clip((cap - cv.dep) / cap, 0, 1)
        base = mask * op * left
        soft = np.clip((tex - (1 - reach)) / 0.6 + 0.3, 0, 1)
        a = base * (0.25 * catch + 0.75 * gaussian_filter(soft, 0.8)) * 0.85
        P = hx(self.veil) if self.veil else np.asarray(col, np.float32)
        f = 1 - np.exp(-KC * a)
        if self.veil_mono:
            L = _lum(cv.col); t = float(_lum(col)); den = float(_lum(P)) - L
            fmax = np.clip((t - L) / np.where(np.abs(den) > 1e-3, den, 1), 0, 1) * (np.abs(den) > 1e-3)
            f0 = f; f = np.minimum(f, fmax); a = a * f / np.maximum(f0, 1e-6)
        cv.col = (cv.col * (1 - f[..., None]) + P[None, None, :] * f[..., None]).astype(np.float32)
        cv.dep = cv.dep + a
        cv.loose = cv.loose + a * 0.8

    def episode_end(self, cv):
        pass                     # nothing dries: dust stays dust until it is fixed

    def dry(self, cv, amount):
        pass

    # -- seeing: the paper's grain under a light from the upper left; matte
    def _grain(self, cv):
        h = cv.tex * 0.6 - 1.2 * getattr(cv, "indent", 0)
        h = gaussian_filter(h, 0.7)
        gy, gx = np.gradient(h)
        return -(gx * 0.6 + gy * 0.8)

    def render(self, cv):
        light = self._grain(cv)
        s = self.sup(cv)
        fill = np.clip(cv.dep / (s["cap"] + cv.xcap), 0, 1)
        # the paper's grain under the light: blank paper at the studio scale measures 0.5-1.1 L* (std of the
        # fine texture; four reference sheets), so the relief is scaled to about 0.8 L* on drawing paper
        shade = 1 + np.clip(light * s.get("relief", 1.0) * 0.33, -0.02, 0.02) * (1 - 0.6 * fill)
        img = self.optics(cv, cv.col * shade[..., None], light, fill)
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

    def optics(self, cv, img, light, fill):
        return img

    # -- finishing
    def finish(self, cv, op, params):
        fn = getattr(self, "fin_" + op.replace("-", "_"), None)
        if fn is None or op not in self.finishes:
            return super().finish(cv, op, params)
        fn(cv, params or {})

    def _region(self, cv, reg, feather=8):
        if not reg or reg.get("type", "canvas") == "canvas":
            return np.ones((cv.H, cv.W), np.float32)
        im = Image.new("L", (cv.W, cv.H), 0); d = ImageDraw.Draw(im)
        t = reg["type"]
        if t == "rect":
            d.rectangle([reg["x"], reg["y"], reg["x"] + reg["w"], reg["y"] + reg["h"]], fill=255)
        elif t == "ellipse":
            d.ellipse([reg["cx"] - reg["rx"], reg["cy"] - reg["ry"], reg["cx"] + reg["rx"], reg["cy"] + reg["ry"]], fill=255)
        elif t == "poly":
            d.polygon([tuple(p) for p in reg["pts"]], fill=255)
        return gaussian_filter(np.asarray(im, np.float32) / 255, feather)

    fix_dark, fix_chroma, fix_restore = 0.04, 0.0, 0.2

    def fin_fixative(self, cv, p):
        kind = p.get("kind", self.fix_default)
        s = float(p.get("strength", self.fix_strength))
        mk = self._region(cv, p.get("region"), p.get("feather", 12)) if kind == "workable" or p.get("region") else np.ones((cv.H, cv.W), np.float32)
        cv.fix = cv.fix + (cv.dep - cv.fix) * mk
        cv.loose = cv.loose * (1 - mk)
        cap = self.sup(cv)["cap"]
        rest = self.fix_restore if kind == "workable" else self.fix_restore * 0.4
        cv.xcap = np.clip(cv.xcap + rest * cap * s * mk, 0, cap)
        cov = _cov(cv.dep)
        L = _lum(cv.col)[..., None]
        d = (self.fix_dark * s * mk * (0.3 + 0.7 * cov))[..., None]
        if self.fix_chroma:
            d = d * (0.6 + 0.8 * L)                     # lights lose more (powder stops scattering)
            ch = (self.fix_chroma * s * mk * cov)[..., None]
            cv.col = L + (cv.col - L) * (1 - ch)
        cv.col = np.clip(cv.col * (1 - d), 0, 1)
        if hasattr(cv, "sheen"):
            cv.sheen = cv.sheen * (1 - self.fix_dull * s * mk)
        if kind == "final" and self.name == "pastel":
            print("note: fixative darkens pastel; lay the last bright accents after it (finish accents), or skip it")

    def fin_lift(self, cv, p):
        pts = p.get("points", [])
        if not pts:
            print("lift: give points [[x, y, r], ...] and kind kneaded|eraser"); return
        rng = np.random.default_rng(p.get("seed", 5))
        kind = p.get("kind", "kneaded")
        kind = "eraser" if kind in ("hard", "hard_eraser") else kind
        for q in pts:
            x, y, r = q[0], q[1], (q[2] if len(q) > 2 else 10)
            t = self.make_tool({"brush": kind}, 2 * r, hx("#ffffff"), rng)
            t.step = r
            for _ in range(int(p.get("touches", 2))):
                t.dab(cv, x, y, 0.0, float(p.get("pressure", 0.8)))

    def fin_clean(self, cv, p):
        """Lift the dust and smudges outside the drawing: a margin (px) or outside a region."""
        if p.get("region"):
            out = 1 - self._region(cv, p["region"], 6)
        else:
            mg = int(p.get("margin", 30))
            out = np.zeros((cv.H, cv.W), np.float32)
            out[:mg] = out[-mg:] = 1; out[:, :mg] = out[:, -mg:] = 1
            out = gaussian_filter(out, 3)
        free = np.clip(cv.dep - cv.fix, 0, None)
        nd = cv.dep - (np.minimum(cv.loose, free) + 0.7 * np.clip(free - cv.loose, 0, None)) * out
        ratio = np.where(cv.dep > 1e-4, _cov(nd) / np.maximum(_cov(cv.dep), 1e-6), 1.0)
        cv.col = cv.paper + (cv.col - cv.paper) * ratio[..., None]
        cv.loose = cv.loose * (1 - out); cv.dep = nd

    def fin_accents(self, cv, p):
        """The last few accents (darkest darks or brightest lights), guarded: at most n strokes."""
        st = p.get("strokes", [])
        n = int(p.get("n", 6))
        if not st:
            print(f"accents: give up to {n} strokes [{{'pts': [[x, y], ...], 'color': '#..', 'size': s}}]"); return
        if len(st) > n:
            raise SystemExit(f"accents are the last few marks: at most {n} strokes (got {len(st)})")
        import studio as S
        felt = S.Felt(p.get("felt", {"arousal": 0.3, "tension": 0.3, "care": 0.8}))
        rng = np.random.default_rng(p.get("seed", 9))
        tool = p.get("tool", self.accent_tool)
        for s in st:
            size = s.get("size", 5)
            b = self.make_tool({"brush": tool}, size, hx(s.get("color", "#000000")), rng)
            S.play(cv, b, S.gesture_path(s["pts"], felt, rng, size), felt, s.get("pressure", 1.0), rng)


# ---------------------------------------------------------------- charcoal
def _stick(desc, shape, P, flow, reach, loose, stain, **kw):
    d = dict(kind="stick", desc=desc, shape=shape, P=P, flow=flow, reach=reach, loose=loose, stain=stain)
    d.update(kw)
    return d


def _blend(desc, blur, drag, pick, bound, sizef=1.0, sig=0.33, **kw):
    d = dict(kind="smudge", desc=desc, shape="soft", blur=blur, drag=drag, pick=pick, bound=bound, sizef=sizef, sig=sig)
    d.update(kw)
    return d


def _eraser(desc, shape, lift, sizef=1.0, **kw):
    d = dict(kind="erase", desc=desc, shape=shape, lift=lift, sizef=sizef)
    d.update(kw)
    return d


def _srgb_of_L(L):
    """sRGB value (0..1, the engine's colour convention) of a neutral grey of CIE lightness L*."""
    Y = ((L + 16) / 116) ** 3 if L > 8 else L / 903.3
    return 1.055 * Y ** (1 / 2.4) - 0.055 if Y > 0.0031308 else 12.92 * Y


def _grey(L, tint=(1.0, 1.0, 1.0)):
    v = _srgb_of_L(L)
    return tuple(round(v * k, 4) for k in tint)


# Darkest values, measured on the Met references (the darkest 0.1% of each sheet, docs/calibration/charcoal.md):
# conté (Millet) L* 23.8, charcoal (Degas, Two Dancers) 21.9, black chalk (de la Fosse) 25.6,
# charcoal sketches (Mauve 28.9, Melbye 26.9). Full coverage of a stick renders at its pigment value,
# so compressed charcoal is set to L* 24 and vine to L* 29 (vine lighter: the sources; its number is the
# lighter end of the measured charcoal sheets). The old values (L* 4 and 23) were far too black.
VINE = _grey(29.0, (1.0, 0.985, 0.97))
COMP = _grey(24.0, (1.0, 0.985, 1.02))
CPENCIL = _grey(26.0)


class Charcoal(DryMedium):
    name = "charcoal"
    SUP = {"drawing": dict(desc="white drawing paper with a fine irregular tooth", tex="drawing", cap=1.0, grab=1.0, w=0.38),
           "toned": dict(desc="mid-grey toned drawing paper, for working dark and light (white chalk)", tex="drawing",
                         tone="#9a978f", cap=1.0, grab=1.0, w=0.38),
           "ingres": dict(desc="Ingres laid paper: fine laid lines and chain lines show in every tone", tex="laid",
                          cap=0.85, grab=0.95, w=0.32, relief=1.2)}
    TOOLS = {
        "vine_tip": _stick("vine charcoal, the end: grey, irregular, very erasable line", "tip", VINE, 0.8, 0.8, 0.88, 0.03, mono=True),
        "vine_side": _stick("vine charcoal on its side: broad pale band broken by the tooth", "side", VINE, 0.65, 0.58, 0.9, 0.03, mono=True),
        "compressed_tip": _stick("compressed charcoal, the end: dense velvety black line, harder to erase", "tip", COMP, 1.05, 0.95, 0.5, 0.22, mono=True),
        "compressed_side": _stick("compressed charcoal on its side: broad dense dark band", "side", COMP, 0.95, 0.75, 0.55, 0.2, mono=True),
        "pencil": _stick("charcoal pencil: fine controlled dark line (at most 8 px)", "tip", CPENCIL, 0.85, 0.75, 0.4, 0.25, mono=True, maxsize=8),
        "white_chalk": _stick("white chalk / Conte: added lights, best on toned paper", "tip", (0.95, 0.94, 0.9), 0.85, 0.72, 0.7, 0.1),
        "stump": _blend("paper stump: smooth blended tone, fills the tooth", 0.8, 0.22, 0.03, 0.3),
        "tortillon": _blend("tortillon: small pointed blender for detail", 0.75, 0.2, 0.03, 0.3, sizef=0.6),
        "finger": _blend("finger: smears tone into soft gradients, drags it out", 0.6, 0.5, 0.02, 0.2, sig=0.45),
        "chamois": _blend("chamois: wide soft wipe that knocks back tone", 0.9, 0.15, 0.25, 0.15, sizef=1.6, sig=0.4),
        "kneaded": _eraser("kneaded eraser: soft lifts, tone by pressure", "soft", 0.6),
        "eraser": _eraser("hard eraser: crisp clean lights, leaves a ghost", "hard", 1.0, rough=True),
    }
    DEFAULT = {"tip": "vine_tip", "side": "vine_side"}
    MAXSIZE = {"tip": 26, "side": 140}
    finishes = {"fixative": "spray fixative {kind: final|workable, strength, region}: locks the dust, darkens slightly; workable restores some tooth",
                "lift": "eraser highlights {points: [[x,y,r],...], kind: kneaded|eraser}",
                "clean": "lift dust and smudges from the margins {margin} or outside {region}",
                "accents": "last darkest accents, at most n strokes (compressed charcoal) {strokes, n}"}
    bound_erase = 0.55
    veil = "#2a2928"
    fix_default, fix_strength, fix_dull = "final", 1.0, 0.0
    accent_tool = "compressed_tip"

    def optics(self, cv, img, light, fill):
        # velvety: charcoal dust drinks the light; dense darks lose the paper's grain highlights
        cov = _cov(cv.dep)[..., None]
        return img * (1 - 0.06 * cov * (1 - _lum(cv.col)[..., None]))


# ---------------------------------------------------------------- graphite
GRADES = ["6H", "4H", "2H", "H", "HB", "B", "2B", "3B", "4B", "5B", "6B", "7B", "8B", "9B"]


# Lightness (L*) of a full cover of each grade. Measured anchors (docs/calibration/graphite.md): the darkest
# graphite in the references is L* 32.5-34.7 (Lachaise, Grandville: dense soft-pencil passages) -> 9B 32.5,
# 6B 35; the darkest of Ingres's fine portrait (hard pencils) is L* 55 -> about H. The other grades are
# interpolated by eye: no per-grade measurement was found.
# The values are of the pigment; the render's sheen lifts a dense soft dark by about 3.5 L*, so the soft end
# sits that much below the measured anchors (8B three heavy passes renders at L* 33-34, darkest 0.1%).
GRADE_L = {"6H": 72.0, "4H": 66.0, "2H": 60.0, "H": 55.0, "HB": 49.0, "B": 44.5, "2B": 41.0, "3B": 38.0,
           "4B": 35.5, "5B": 33.5, "6B": 32.0, "7B": 30.8, "8B": 29.8, "9B": 29.0}


def grade_spec(g):
    g = str(g).upper()
    if g not in GRADES:
        g = "2B"
    i = GRADES.index(g) / (len(GRADES) - 1)          # 0 hardest .. 1 softest
    lum = _srgb_of_L(GRADE_L[g])
    return dict(P=(lum * 0.97, lum * 0.98, lum * 1.03), flow=0.45 + 0.75 * i, reach=0.42 + 0.75 * i,
                loose=0.1 + 0.4 * i, stain=0.12 - 0.08 * i, sheen=0.25 + 0.75 * i, grade=g)


def _pencil(desc, g, shape="tip"):
    s = grade_spec(g)
    return dict(kind="stick", desc=desc, shape=shape, mono=True, burnish=True, w=0.9, smear=1.5, **s)


class Graphite(DryMedium):
    name = "graphite"
    arrays = ("col", "paper", "dep", "loose", "fix", "xcap", "sheen", "indent")
    SUP = {"drawing": dict(desc="white drawing paper, medium tooth", tex="drawing", cap=0.9, grab=1.0, w=0.36),
           "toned": dict(desc="toned (grey-buff) drawing paper", tex="drawing", tone="#b9b2a4", cap=0.9, grab=1.0, w=0.36),
           "ingres": dict(desc="Ingres laid paper: laid lines show through the tone", tex="laid", cap=0.8, grab=0.95, w=0.22, relief=1.2),
           "bristol": dict(desc="smooth bristol: even, fine tone; little tooth, so darks stay limited", tex="smooth",
                           cap=0.55, grab=1.15, w=0.55, relief=0.5)}
    TOOLS = {
        "pencil": _pencil("pencil; set the grade with \"grade\" (6H..9B, default 2B): narrow even line", "2B"),
        "pencil_2H": _pencil("2H: hard, light silvery line that stays on the peaks", "2H"),
        "pencil_HB": _pencil("HB: the middle grade", "HB"),
        "pencil_4B": _pencil("4B: soft, dark, smudgeable", "4B"),
        "pencil_8B": _pencil("8B: softest, darkest graphite (still a dark grey), shiny", "8B"),
        "side": _pencil("side of a soft (6B) lead: broad grainy tone", "6B", "side"),
        "stump": _blend("paper stump: smooth modulated tone, burnishes a little", 0.75, 0.15, 0.02, 0.45, burnish=True),
        "kneaded": _eraser("kneaded eraser: soft lifts", "soft", 0.6),
        "eraser": _eraser("hard eraser: crisp lights (reduction drawing), leaves a ghost", "hard", 1.0, rough=True),
        "stylus": dict(kind="stylus", desc="stylus: indents the paper; later tone skips the groove (white lines)", shape="tip", sizef=0.5),
    }
    DEFAULT = {"tip": "pencil", "side": "side"}
    MAXSIZE = {"tip": 10, "side": 36}
    PPM = 5.0                # graphite sheets are smaller: 1200 px = 24 cm
    W_SUB = 1.6
    EDGE_MM = 0.3            # graphite lines are crisper (Delacroix's hatching: 0.31 mm)
    finishes = {"fixative": "optional fixative {strength (0.5), region}: no more smudging, dulls the shine ~20%",
                "lift": "eraser highlights {points: [[x,y,r],...], kind: kneaded|eraser}",
                "clean": "clean the margins {margin} or outside {region}",
                "accents": "last darkest accents in a soft grade, at most n strokes {strokes, n, tool}"}
    bound_erase = 0.85
    veil = "#4a4b4f"
    fix_default, fix_strength, fix_dull, fix_dark = "final", 0.5, 0.4, 0.015
    accent_tool = "pencil_8B"

    def adjust(self, spec, it):
        if "grade" in it and spec["kind"] == "stick":
            g = grade_spec(it["grade"])
            spec.update({k: v for k, v in g.items()})
        return spec

    def optics(self, cv, img, light, fill):
        # graphite's metallic shine under a raking light: the flattened flakes catch it, strongest on
        # dense soft darks and burnished passages; silvery, cool
        sh = gaussian_filter(np.clip(cv.sheen, 0, 1.5), 0.6) * _cov(cv.dep)
        rk = np.clip(0.55 + light * 7, 0.15, 1.3)
        k = np.clip(sh * rk * 0.32, 0, 0.42)[..., None]
        shine = np.array([0.6, 0.615, 0.65], np.float32)
        return img + (shine - img) * k * (img < shine)


# ---------------------------------------------------------------- pastel
class Pastel(DryMedium):
    name = "pastel"
    arrays = ("col", "paper", "dep", "loose", "fix", "xcap", "sheen")
    SUP = {"toned": dict(desc="toned pastel paper (honeycomb side): warm grey, real tooth; its colour shows through",
                         tex="honeycomb", tone="#857b6d", cap=1.7, grab=1.0, w=0.32, relief=1.15),
           "sanded": dict(desc="sanded pastel paper: fine grit that grabs and holds many layers", tex="sanded",
                          tone="#b4a184", cap=3.4, grab=1.25, w=0.38, relief=0.8),
           "ingres": dict(desc="Ingres laid paper, toned: modest tooth, laid lines show", tex="laid", tone="#9b9384",
                          cap=1.2, grab=0.95, w=0.3, relief=1.2)}
    W_SUB = 1.2              # pastel papers have a coarser tooth (specks 0.2-0.4 mm)
    EDGE_MM = 1.0            # pastel strokes are softest (Degas, The Singer in Green: 0.98 mm)
    TOOLS = {
        "soft_side": _stick("soft pastel on its side: rich broad colour broken by the tooth; fills it fast", "side", None, 1.0, 0.8, 0.85, 0.04, slide=True, grip=0.5),
        "soft_tip": _stick("soft pastel, the end: thick opaque strokes, the brightest accents", "tip", None, 1.1, 0.88, 0.85, 0.04, slide=True, grip=0.5),
        "hard_side": _stick("hard pastel on its side: lighter grainy masses, leaves tooth for later layers", "side", None, 0.65, 0.62, 0.6, 0.1, slide=True, grip=0.3),
        "hard_tip": _stick("hard pastel, the edge: lines and hatching", "tip", None, 0.7, 0.7, 0.6, 0.1, slide=True, grip=0.3),
        "stump": _blend("stump: blends the powder into smooth tone (colours mix)", 0.75, 0.2, 0.03, 0.25),
        "finger": _blend("finger: blends and softens, drags colour into the next", 0.65, 0.45, 0.03, 0.2, sig=0.45),
        "chamois": _blend("chamois: knocks back an area, lifting dust", 0.85, 0.12, 0.3, 0.1, sizef=1.6, sig=0.4),
        "kneaded": _eraser("kneaded eraser: lifts dust back toward the paper", "soft", 0.55),
        "oil_pastel": _stick("oil pastel: buttery waxy stroke, blends with what's under it by pressure, slight sheen", "tip", None,
                             1.3, 1.05, 0.0, 0.6, oily=True, sheen=0.7, w=1.6),
        "scraper": dict(kind="scrape", desc="scraper: sgraffito, scratches through oil pastel to the paper", shape="blade"),
    }
    DEFAULT = {"tip": "soft_tip", "side": "soft_side"}
    MAXSIZE = {"tip": 28, "side": 120}
    finishes = {"fixative": "workable fixative {kind: workable|final, strength, region}: restores tooth, locks dust, darkens and dulls (lights most)",
                "accents": "final bright accents in soft pastel, after any fixative; at most n strokes {strokes, n}"}
    bound_erase = 0.35
    veil = None
    veil_mono = False
    fix_default, fix_strength, fix_dull, fix_dark, fix_chroma, fix_restore = "workable", 1.0, 0.0, 0.08, 0.10, 0.3
    accent_tool = "soft_tip"

    def optics(self, cv, img, light, fill):
        cov = _cov(cv.dep)[..., None]
        # powdery scatter: a slight lift in value, lower contrast in the darks, chalky
        img = img + 0.05 * cov * (1 - img) ** 2
        if hasattr(cv, "sheen"):                    # oil pastel: a low waxy sheen
            w = np.clip(cv.sheen, 0, 1)[..., None]
            img = img + np.clip(light * 6, 0, 0.6)[..., None] * w * 0.12
        return img
