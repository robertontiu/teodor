"""Oil exactly as in studio v7, frozen as the regression reference (test_v8.py). Do not edit; improve media/oil.py instead.
under raking light, canvas weave. Behaviour is identical to studio v7 (see test_v8.py)."""
import numpy as np, math
from scipy.ndimage import gaussian_filter
from PIL import Image
from .base import Medium, kmix, hx

def weave(h, w, seed=7):
    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.random((h, w)).astype(np.float32), 0.8)
    c = gaussian_filter(rng.random((h, w)).astype(np.float32), 3)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    t = 0.5 + 0.25 * np.sin(x * 1.7) * np.sin(y * 0.3) + 0.25 * np.sin(y * 1.7) * np.sin(x * 0.3)
    n = lambda a: (a - a.min()) / (a.max() - a.min() + 1e-6)
    return np.clip(0.05 * t + 0.6 * n(f) + 0.35 * n(c), 0, 1).astype(np.float32)



class Brush:
    def __init__(self, kind, size, color, rng, load=1.0, cover=0.95, pickup=0.35, thick=0.5,
                 wetmix=0.5, edge="soft", depletion=1.0):
        self.kind, self.size, self.rng = kind, size, rng
        self.color = np.asarray(color, np.float32).copy()
        self.paint = load
        self.load0 = load
        self.cover, self.pickup, self.thick, self.wetmix = cover, pickup, thick, wetmix
        self.edge, self.depletion = edge, depletion
        k = max(5, int(size / 1.3))
        self.bristles = np.clip(rng.normal(1.0, 0.2, k), 0.25, 1.25).astype(np.float32)
        if kind == "fan":
            self.bristles *= (rng.random(k) < 0.33)
        self.carry = None

    def mask(self, r, u, v):
        k = len(self.bristles)
        bi = np.clip(((v / max(r, 1e-3) + 1) / 2 * k).astype(int), 0, k - 1)
        br = self.bristles[bi]
        ex = {"hard": 0.12, "soft": 0.7, "lost": 1.6}.get(self.edge, 0.7)
        if self.kind in ("round", "fan", "smudge", "blend"):
            d = (u ** 2 + v ** 2) / max(r * r, 1e-3)
            m = np.clip(1 - d, 0, 1) ** ex
            if self.kind in ("round", "fan"):
                m = m * (br if self.edge != "lost" else 0.6 + 0.4 * br)
        elif self.kind == "flat":
            along = np.clip(1 - np.abs(u) / (r * 0.32 + 0.5), 0, 1) ** 0.3
            across = np.clip(1 - np.abs(v) / r, 0, 1) ** max(0.1, ex * 0.6)
            m = along * across * br
        elif self.kind == "knife":
            m = ((np.abs(u) < r * 0.16 + 0.6) & (np.abs(v) < r)).astype(np.float32) * (0.85 + 0.15 * br)
        else:
            m = np.clip(1 - (u ** 2 + v ** 2) / max(r * r, 1e-3), 0, 1)
        return m.astype(np.float32)

    def dab(self, cv, x, y, ang, press, rscale=1.0):
        r = max(0.7, self.size / 2 * rscale)
        R = int(math.ceil(r)) + 1
        x0, x1 = max(0, int(x) - R), min(cv.W, int(x) + R + 1)
        y0, y1 = max(0, int(y) - R), min(cv.H, int(y) + R + 1)
        if x0 >= x1 or y0 >= y1:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dx, dy = xx - x, yy - y
        ca, sa = math.cos(ang), math.sin(ang)
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        m = self.mask(r, u, v) * press
        if cv.clip is not None:
            m = m * cv.clip[y0:y1, x0:x1]
        tex = cv.tex[y0:y1, x0:x1]
        eff = self.paint - getattr(self, "speedfx", 0.0)
        if self.kind not in ("smudge", "blend") and eff < 0.55:
            thr = min(1.0, (0.55 - eff) / 0.55)
            m = m * np.clip((tex - thr * 0.95) * 4, 0, 1)
        if m.max() <= 0.01:
            return
        c = cv.col[y0:y1, x0:x1]
        w = cv.wet[y0:y1, x0:x1]
        ms = m.sum() + 1e-6
        local = (c * m[..., None]).sum((0, 1)) / ms
        localwet = float((w * m).sum() / ms)
        if self.kind == "blend":
            sig = max(0.8, r / 2.5)
            bl = np.stack([gaussian_filter(c[..., i], sig) for i in range(3)], -1)
            amt = np.clip(m * (0.25 + 0.75 * w) * 0.85, 0, 1)[..., None]
            cv.col[y0:y1, x0:x1] = c * (1 - amt) + bl * amt
            cv.ht[y0:y1, x0:x1] = cv.ht[y0:y1, x0:x1] * (1 - m * 0.25)
            return
        if self.kind in ("smudge", "knife"):
            if self.carry is None:
                self.carry = local.copy()
            src = self.carry if self.kind == "smudge" else kmix(self.color, self.carry, 0.45)
            amt = np.clip(m[..., None] * (0.25 + 0.6 * w[..., None]) * (0.9 if self.kind == "knife" else 0.7), 0, 1)
            cv.col[y0:y1, x0:x1] = kmix(c, src[None, None, :], amt)
            ck = min(0.5, 0.3 * getattr(self, "step", 1.0) / max(self.size * 0.3, 1.0))
            self.carry = self.carry * (1 - ck) + local * ck
            if self.kind == "knife":
                cv.ht[y0:y1, x0:x1] = cv.ht[y0:y1, x0:x1] * (1 - m * 0.5) + m * 0.15 * self.thick
                cv.wet[y0:y1, x0:x1] = np.clip(w + m * 0.4, 0, 1)
            else:
                cv.ht[y0:y1, x0:x1] *= (1 - m * 0.15)
            return
        pk = min(0.5, self.pickup * localwet * 0.25 * getattr(self, "step", 1.0) / max(self.size * 0.5, 1.0))
        self.color = self.color * (1 - pk) + local * pk
        dep = kmix(self.color[None, None, :], c, np.clip(w[..., None] * self.wetmix, 0, 0.8))
        amt = np.clip(m[..., None] * self.cover * min(1, self.paint * 1.6 + 0.3), 0, 1)
        cv.col[y0:y1, x0:x1] = kmix(c, dep, amt)
        cv.ht[y0:y1, x0:x1] = np.clip(cv.ht[y0:y1, x0:x1] * (1 - m * 0.08) + (m ** 1.5) * self.thick * 0.045 * self.paint, 0, 4)
        cv.wet[y0:y1, x0:x1] = np.clip(w + m * 0.7, 0, 1)
        self.paint = max(0.0, self.paint - getattr(self, "step", 1.0) / (max(self.size, 2) * 42 * max(self.load0, 0.1)))




class OilV7(Medium):
    name = "oil-v7"
    arrays = ("col", "wet", "ht")
    supports = {"canvas": "linen or cotton canvas, primed; the weave shows through thin paint",
                "panel": "gessoed wooden panel: smooth, hard, no weave"}
    finishes = {}
    tools = {"round": "round bristle brush", "flat": "flat bristle brush", "filbert": "filbert (a flat with rounded corners)",
             "fan": "fan brush, sparse bristles", "liner": "rigger/liner: long thin hair brush for lines",
             "knife": "palette knife: drags and scrapes paint", "smudge": "finger or rag: pushes wet paint",
             "blend": "soft dry brush: blends wet paint (sfumato)"}

    def texture(self, h, w, support):
        if support == "panel":
            from .base import noise_field
            return (0.5 + 0.15 * (noise_field(h, w, 0.6, 7) - 0.5)).astype(np.float32)
        return weave(h, w)

    def make_tool(self, it, size, color, rng):
        kind = it.get("brush", "round")
        if kind == "filbert":
            kind = "round"
        if kind == "liner":
            b = Brush("round", size, color, rng, load=it.get("load", 1.0), cover=it.get("cover", 0.97),
                      pickup=0.1, thick=it.get("impasto", 0.3), wetmix=it.get("wetmix", 0.2), edge="hard")
            b.bristles[:] = 1.0
            b.liner = True
            return b
        return Brush(kind, size, color, rng, load=it.get("load", 1.0) * rng.uniform(0.85, 1.1),
                     cover=it.get("cover", 0.95), pickup=it.get("pickup", 0.35), thick=it.get("impasto", 0.5),
                     wetmix=it.get("wetmix", 0.5), edge=it.get("edge", "soft"))

    def glaze(self, cv, mask, col, op):
        amt = (mask * op * (1 - 0.5 * cv.wet))[..., None]
        cv.col = kmix(cv.col, col[None, None, :], amt)

    def episode_end(self, cv):
        cv.wet *= 0.93

    def dry(self, cv, amount):
        cv.wet *= (1 - amount)

    def render(self, cv):
        ht = gaussian_filter(cv.ht, 1.1)
        gy, gx = np.gradient(ht * 3.2)
        lightdot = -gx * 0.55 - gy * 0.8
        shade = 1 + np.clip(lightdot, -0.12, 0.12)
        tooth = 0.975 + 0.025 * cv.tex * (1 - np.clip(cv.ht * 1.5, 0, 0.85))
        img = cv.col * (shade * tooth)[..., None]
        spec = np.clip(lightdot - 0.16, 0, 1) * 0.08 * np.clip(cv.ht * 2, 0, 1)
        img = np.clip(img + spec[..., None], 0, 1)
        return Image.fromarray((img * 255).astype(np.uint8))



