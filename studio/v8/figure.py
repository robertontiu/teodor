"""People (and a few companions) for the scene builder: a proportioned rig, plane-built heads with
expressions from facial action units, articulated hands, drapery under gravity and wind.

Everything here returns *parts*: dicts with an SDF function `f(p)` over world points (N,3), a colour
or a per-point colour function, a bounding sphere and an `element` tag (head, neck, torso, arms,
hands, legs, feet, hair, drapery, animal, water). scene.py turns parts into render nodes and writes
one mask per element (see docs/MANUAL.md, "The schema").

Units are meters, y is up. A person's own frame: x = the person's left, y = up, z = where they face.
Research behind the numbers: docs/subjects/figure.md, face.md, hands-feet.md.
"""
import math
import numpy as np

R = math.radians


# ---------------------------------------------------------------- small math
def hx(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float32)


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float32)


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float32)


def nrm(v):
    v = np.asarray(v, np.float32)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-9)


def V(*a):
    return np.array(a, np.float32)


def lerp_table(tab, x):
    xs = [t[0] for t in tab]
    if x <= xs[0]:
        return tab[0][1]
    for (x0, y0), (x1, y1) in zip(tab, tab[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return tab[-1][1]


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def smin_exp(D, k):
    """Smooth minimum over the last axis: the nearest surface blended with the second nearest by a
    polynomial smooth-min (unlike an exponential blend, a surface with no other primitive within k
    is left alone; and it costs one blend whatever the number of primitives)."""
    M = D.shape[-1]
    if M == 1:
        return D[..., 0]
    if M <= 6:
        d = D[..., 0]
        for j in range(1, M):
            d = smin(d, D[..., j], k)
        return d
    two = np.partition(D, 1, axis=-1)
    d = smin(two[..., 0], two[..., 1], k)
    if M > 3:
        third = np.partition(D, 2, axis=-1)[..., 2]
        d = smin(d, third, k * 0.7)
    return d


def rc_batch(p, A, B, r1, r2):
    """Round cones (tapered capsules) a->b with radii r1 at a, r2 at b. p (N,3) -> (N,M)."""
    ba = B - A
    l2 = np.maximum((ba * ba).sum(1), 1e-10)
    rr = r1 - r2
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = p[:, None, :] - A[None]
    y = (pa * ba[None]).sum(2)
    z = y - l2
    w = pa * l2[None, :, None] - ba[None] * y[..., None]
    x2 = (w * w).sum(2)
    y2, z2 = y * y * l2, z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d1 = np.sqrt(x2 + z2) * il2 - r2
    d2 = np.sqrt(x2 + y2) * il2 - r1
    d3 = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - r1
    return np.where(np.sign(z) * a2 * z2 > k, d1, np.where(np.sign(y) * a2 * y2 < k, d2, d3))


def ell_batch(p, C, Mt, Rd):
    """Ellipsoids: centres C (K,3), world->local rotations Mt (K,3,3), radii Rd (K,3). -> (N,K)."""
    out = np.empty((p.shape[0], C.shape[0]), np.float32)
    for k in range(C.shape[0]):
        q = (p - C[k]) @ Mt[k].T
        a = q / Rd[k]
        k0 = np.sqrt((a * a).sum(1))
        b = a / Rd[k]
        k1 = np.sqrt((b * b).sum(1))
        out[:, k] = k0 * (k0 - 1) / (k1 + 1e-9)
    return out


def tri_dist(p, A, B, C, chunk=24, bounds=None):
    """Unsigned distance from points (N,3) to a triangle soup (T,3 each). Triangles go in chunks,
    each with a bounding sphere; a chunk is evaluated only for points it could still be nearest to."""
    out = np.full(p.shape[0], np.inf, np.float32)
    dot = lambda x, y: (x * y).sum(-1)
    if bounds is None:
        bounds = tri_bounds(A, B, C, chunk)
    for i, (c0, r0) in zip(range(0, len(A), chunk), bounds):
        db = np.sqrt(((p - c0) ** 2).sum(1)) - r0
        sel = np.nonzero(db < out)[0]
        if len(sel) == 0:
            continue
        a, b, c = A[i:i + chunk][None], B[i:i + chunk][None], C[i:i + chunk][None]
        P = p[sel][:, None, :]
        ba, pa, cb, pb, ac, pc = b - a, P - a, c - b, P - b, a - c, P - c
        nor = np.cross(ba, ac)
        inside = (np.sign(dot(np.cross(ba, nor), pa)) + np.sign(dot(np.cross(cb, nor), pb)) + np.sign(dot(np.cross(ac, nor), pc))) >= 2

        def edge(e, q):
            t = np.clip(dot(e, q) / np.maximum(dot(e, e), 1e-12), 0, 1)
            v = e * t[..., None] - q
            return dot(v, v)
        de = np.minimum(np.minimum(edge(ba, pa), edge(cb, pb)), edge(ac, pc))
        dp = dot(nor, pa) ** 2 / np.maximum(dot(nor, nor), 1e-12)
        d = np.sqrt(np.where(inside, dp, de)).min(1)
        out[sel] = np.minimum(out[sel], d)
    return out


def tri_bounds(A, B, C, chunk=24):
    bs = []
    for i in range(0, len(A), chunk):
        P = np.concatenate([A[i:i + chunk], B[i:i + chunk], C[i:i + chunk]])
        c = (P.max(0) + P.min(0)) / 2
        bs.append((c, float(np.linalg.norm(P - c, axis=1).max())))
    return bs


def subdivide(G, wrap=False, times=1):
    """Smooth a grid of cloth points: Catmull-Rom midpoints along rows and columns."""
    for _ in range(times):
        def mids(X, axis, wrap_):
            X = np.moveaxis(X, axis, 0)
            n = len(X)
            idx = lambda i: (i % n) if wrap_ else min(max(i, 0), n - 1)
            out = []
            last = n if wrap_ else n - 1
            for i in range(last):
                p0, p1, p2, p3 = X[idx(i - 1)], X[idx(i)], X[idx(i + 1)], X[idx(i + 2)]
                out.append(X[i]); out.append((-p0 + 9 * p1 + 9 * p2 - p3) / 16)
            if not wrap_:
                out.append(X[-1])
            return np.moveaxis(np.stack(out), 0, axis)
        G = mids(G, 0, False)
        G = mids(G, 1, wrap)
    return G


def grid_tris(G, wrap=False):
    """Triangles from a grid of points G (rows, cols, 3); wrap joins the last column to the first."""
    R_, C_ = G.shape[:2]
    A, B, Cc = [], [], []
    cols = C_ if wrap else C_ - 1
    for i in range(R_ - 1):
        for j in range(cols):
            j2 = (j + 1) % C_
            a, b, c, d = G[i, j], G[i, j2], G[i + 1, j2], G[i + 1, j]
            A += [a, a]; B += [b, c]; Cc += [c, d]
    return np.array(A, np.float32), np.array(B, np.float32), np.array(Cc, np.float32)


def cloth_part(grids, thick, color, name, smooth_wrap=None):
    grids = [(subdivide(g, w), w) for g, w in grids]
    tris = [grid_tris(g, w) for g, w in grids]
    A = np.concatenate([t[0] for t in tris]); B = np.concatenate([t[1] for t in tris]); C = np.concatenate([t[2] for t in tris])

    bounds = tri_bounds(A, B, C)

    def f(p):
        return tri_dist(p, A, B, C, bounds=bounds) - thick
    pts = np.concatenate([g.reshape(-1, 3) for g, _ in grids])
    span = max(float(np.linalg.norm(pts.max(0) - pts.min(0))) / len(pts) ** 0.5, 0.05)
    return part(f, color, "drapery", [(q, span) for q in pts], name=name, nsmooth=thick * 2.5)


class Prims:
    """A bag of round cones and ellipsoids, blended into one smooth surface."""

    def __init__(self):
        self.cones, self.ells = [], []

    def cone(self, a, b, r1, r2):
        a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
        L = float(np.linalg.norm(b - a))
        if L < 1e-5:
            b = a + V(0, 1e-4, 0); L = 1e-4
        if abs(r1 - r2) >= L * 0.98:          # keep the round cone well defined
            m = (r1 + r2) / 2; d = L * 0.49
            r1, r2 = (m + d, m - d) if r1 > r2 else (m - d, m + d)
        self.cones.append((a, b, float(r1), float(r2)))

    def ell(self, c, M, radii):
        self.ells.append((np.asarray(c, np.float32), np.asarray(M, np.float32).T, np.asarray(radii, np.float32)))

    def empty(self):
        return not (self.cones or self.ells)

    def arrays(self):
        out = {}
        if self.cones:
            out["A"] = np.stack([c[0] for c in self.cones]); out["B"] = np.stack([c[1] for c in self.cones])
            out["r1"] = np.array([c[2] for c in self.cones], np.float32); out["r2"] = np.array([c[3] for c in self.cones], np.float32)
        if self.ells:
            out["C"] = np.stack([e[0] for e in self.ells]); out["Mt"] = np.stack([e[1] for e in self.ells])
            out["Rd"] = np.stack([e[2] for e in self.ells])
        return out

    def raw(self, p, a=None):
        a = a or self.arrays()
        cols = []
        if "A" in a:
            cols.append(rc_batch(p, a["A"], a["B"], a["r1"], a["r2"]))
        if "C" in a:
            cols.append(ell_batch(p, a["C"], a["Mt"], a["Rd"]))
        return np.concatenate(cols, 1)

    def fn(self, k):
        a = self.arrays()
        if k <= 0:
            return lambda p: self.raw(p, a).min(1)
        return lambda p: smin_exp(self.raw(p, a), k)

    def spheres(self):
        s = [(c[0], max(c[2], c[3])) for c in self.cones] + [(c[1], max(c[2], c[3])) for c in self.cones]
        s += [(e[0], float(e[2].max())) for e in self.ells]
        return s


def bound_of(spheres, pad=0.02):
    P = np.stack([s[0] for s in spheres])
    r = np.array([s[1] for s in spheres])
    lo, hi = (P - r[:, None]).min(0), (P + r[:, None]).max(0)
    c = (lo + hi) / 2
    return c, float((np.linalg.norm(P - c, axis=1) + r).max() + pad)


def part(f, color, element, spheres, **kw):
    c, r = bound_of(spheres, kw.pop("pad", 0.02))
    d = dict(f=f, color=hx(color) if isinstance(color, str) else color, element=element, bound=(c, r))
    d.update(kw)
    return d


def body_part(groups, k_join, element_names):
    """One smooth surface from several groups [(element, colour, gloss, fn, spheres, join_k)], so a
    shoulder flows into the arm and the hip into the thigh, while each point still knows which
    element it belongs to (for its colour and for the element masks)."""
    cols = np.stack([hx(g[1]) if isinstance(g[1], str) else g[1] for g in groups])
    gls = np.array([g[2] for g in groups], np.float32)
    sub = np.array([element_names.index(g[0]) for g in groups], np.int32)

    def dists(p):
        return np.stack([g[3](p) for g in groups], 1)

    def f(p):
        D = dists(p)
        d = D[:, 0]
        for j in range(1, D.shape[1]):
            d = smin(d, D[:, j], groups[j][5] if groups[j][5] is not None else k_join)
        return d

    def which(p):
        return np.argmin(dists(p), 1)

    sph = [s_ for g in groups for s_ in g[4]]
    c, r = bound_of(sph, 0.03)
    return dict(f=f, color=cols[0], colorf=lambda p: cols[which(p)], subf=lambda p: sub[which(p)], sub=element_names,
                glossf=lambda p: gls[which(p)], element=element_names[sub[0]], bound=(c, r))


# ---------------------------------------------------------------- proportions
# Heads tall by age (USF/Weigall "head to height", Tuts+ "drawing different ages"); stature in meters
# (judgement call from growth charts, rounded); hip-joint height as a fraction of stature.
HEADS = [(0, 4.0), (1, 4.3), (2, 4.6), (3, 5.0), (5, 5.6), (8, 6.0), (10, 6.3), (12, 6.7), (15, 7.1), (18, 7.5), (60, 7.5), (85, 7.3)]
STATURE_M = [(0, 0.5), (1, 0.76), (2, 0.87), (3, 0.96), (5, 1.1), (8, 1.28), (10, 1.38), (12, 1.49), (15, 1.70), (18, 1.77), (60, 1.75), (85, 1.69)]
STATURE_F = [(0, 0.5), (1, 0.75), (2, 0.86), (3, 0.95), (5, 1.09), (8, 1.27), (10, 1.38), (12, 1.51), (15, 1.61), (18, 1.64), (60, 1.62), (85, 1.56)]
LEGFRAC = [(0, 0.37), (2, 0.41), (5, 0.45), (10, 0.49), (15, 0.51), (18, 0.513)]
BUILDS = {  # torso width, limb girth, shoulder width, belly
    "slim": (0.9, 0.86, 0.96, 0.0), "average": (1.0, 1.0, 1.0, 0.0), "heavy": (1.18, 1.2, 1.04, 1.0),
    "muscular": (1.06, 1.16, 1.1, 0.0), "frail": (0.88, 0.78, 0.92, 0.0),
}


class Body:
    """Proportions for one person, in head units u (one head height)."""

    def __init__(self, o):
        self.age = float(o.get("age", 30))
        self.sex = o.get("sex", "male")
        self.fem = 1.0 if self.sex.startswith("f") else 0.0
        a = self.age
        S = o.get("height") or lerp_table(STATURE_F if self.fem else STATURE_M, a)
        n = o.get("heads") or lerp_table(HEADS, a)
        self.S, self.n = S, n
        u = self.u = S / n
        legh = lerp_table(LEGFRAC, a) * S / u           # hip-joint height in u
        tors = n - legh - 1.35                           # hip joint to sternal notch, in u
        self.tf, self.lf = tors / 2.3, legh / 3.85
        self.af = (self.tf + self.lf) / 2
        self.wf = min(self.tf, 1.0) ** 0.8
        b = BUILDS.get(o.get("build", "average"), BUILDS["average"])
        self.bt, self.bl, self.bs, self.belly = b
        self.old = float(np.clip((a - 55) / 25, 0, 1))
        self.child = float(np.clip((14 - a) / 12, 0, 1))
        if a >= 55:
            self.bl *= 1 - 0.12 * self.old

    def g(self, male, female):
        """A value interpolated by sex."""
        return male + (female - male) * self.fem


# ---------------------------------------------------------------- pose presets
# Joints (degrees): spine/neck/head [forward, side(left+), twist(left+)], pelvis [tilt fwd, hip hike
# left+, twist], arm [forward, out, twist(external+), elbow], wrist [flex(palm-ward+), deviation, pronation],
# leg [forward, out, twist, knee], ankle [dorsiflex], shoulder [raise, forward] (shrug), lean [fwd, side]
# about the feet. Any arm or hand can instead reach a target by IK (see `reach_l` / `reach_r`).
POSES = {
    "stand": {"arm_l": [4, 6, 0, 10], "arm_r": [2, 6, 0, 12]},
    "contrapposto": {"pelvis": [0, -7, 4], "spine": [0, 9, -6], "neck": [0, -4, 8], "leg_l": [8, 6, 0, 14], "leg_r": [0, -3, 0, 0],
                     "arm_l": [8, 10, 0, 18], "arm_r": [-4, 12, 0, 8]},
    "walk": {"leg_l": [28, 0, 0, 12], "leg_r": [-18, 0, 0, 18], "arm_l": [-22, 8, 0, 14], "arm_r": [24, 8, 0, 25],
             "pelvis": [0, 0, -6], "spine": [4, 0, 8]},
    "lean_wind": {"lean": [16, 0], "spine": [8, 0, 0], "neck": [-18, 0, 0], "leg_l": [22, 4, 0, 18], "leg_r": [-14, 4, 0, 4],
                  "ankle_r": [8], "arm_l": [-25, 60, 30, 15], "arm_r": [-25, 60, 30, 15], "shoulder_l": [0, -0.6], "shoulder_r": [0, -0.6]},
    "arms_wide": {"arm_l": [-10, 95, 20, 12], "arm_r": [-10, 95, 20, 12], "spine": [-6, 0, 0], "neck": [-10, 0, 0]},
    "reach": {"arm_r": [100, 10, 0, 5], "spine": [10, -4, -12], "shoulder_r": [0.5, 0.6], "leg_l": [-10, 0, 0, 5], "leg_r": [12, 0, 0, 10]},
    "throw": {"arm_r": [40, 115, 80, 70], "arm_l": [60, 20, 0, 30], "spine": [-6, -10, -35], "pelvis": [0, 0, -20],
              "leg_l": [30, 6, 0, 15], "leg_r": [-20, 8, 10, 25], "neck": [0, 0, 30]},
    "throw_release": {"arm_r": [100, 30, 10, 10], "arm_l": [-20, 40, 0, 40], "spine": [22, 4, 25], "pelvis": [0, 0, 15],
                      "leg_l": [35, 6, 0, 20], "leg_r": [-35, 4, 0, 40], "neck": [-10, 0, -15], "lean": [8, 0]},
    "hand_on_head": {"reach_r": {"target": "head_top", "offset": [0, 0.03, 0], "palm": [0, -1, 0], "hand": "rest"}, "neck": [8, -6, 0]},
    "kneel": {"leg_l": [0, 3, 0, 100], "leg_r": [0, 3, 0, 100], "ankle_l": [-40], "ankle_r": [-40], "arm_l": [10, 8, 0, 20], "arm_r": [10, 8, 0, 20]},
    "kneel_up": {"leg_l": [-5, 3, 0, 90], "leg_r": [-5, 3, 0, 90], "ankle_l": [-50], "ankle_r": [-50], "spine": [-4, 0, 0]},
    "sit_ground": {"leg_l": [80, 8, 10, 40], "leg_r": [85, 6, 10, 70], "spine": [12, 0, 0], "arm_l": [-25, 15, 0, 5], "arm_r": [-25, 15, 0, 5]},
    "sit": {"leg_l": [88, 4, 0, 90], "leg_r": [85, 4, 0, 88], "ankle_l": [0], "ankle_r": [0], "arm_l": [30, 6, 0, 50], "arm_r": [30, 6, 0, 50]},
    "lie_back": {"lie": "back", "arm_l": [0, 20, 0, 10], "arm_r": [0, 20, 0, 10], "leg_l": [0, 6, 25, 4], "leg_r": [0, 6, 25, 6], "ankle_l": [-30], "ankle_r": [-30]},
    "lie_side": {"lie": "left", "leg_l": [30, 0, 0, 40], "leg_r": [50, 0, 0, 60], "spine": [18, 0, 0], "neck": [10, 0, 0],
                 "arm_l": [80, 10, 0, 90], "arm_r": [40, 0, 0, 60]},
    "sleep_back": {"lie": "back", "arm_r": [0, 150, 70, 135], "arm_l": [10, 30, 0, 20], "neck": [6, -8, -20],
                   "leg_l": [0, 8, 30, 8], "leg_r": [14, 4, 20, 22], "ankle_l": [-30], "ankle_r": [-30], "hand_r": "relaxed", "hand_l": "relaxed"},
    "tread_water": {"arm_l": [30, 45, 0, 40], "arm_r": [30, 45, 0, 40], "leg_l": [30, 6, 0, 50], "leg_r": [-10, 6, 0, 40], "spine": [6, 0, 0]},
    "slumped": {"spine": [28, 0, 0], "neck": [30, 0, 0], "shoulder_l": [-0.4, 0.5], "shoulder_r": [-0.4, 0.5], "arm_l": [8, 4, 0, 10], "arm_r": [8, 4, 0, 10]},
    "bowed": {"spine": [18, 0, 0], "neck": [40, 0, 0], "arm_l": [4, 6, 0, 12], "arm_r": [4, 6, 0, 12]},
    "look_up": {"neck": [-25, 0, 0], "head": [-10, 0, 0], "spine": [-5, 0, 0]},
}

LIE = {"back": (-90, 0), "front": (90, 0), "left": (0, -90), "right": (0, 90)}


def jrot(a):
    """Spine-like joint: bend forward, side bend to the left, twist to the left."""
    a = list(a) + [0, 0, 0]
    return rx(R(a[0])) @ rz(-R(a[1])) @ ry(R(a[2]))


# ---------------------------------------------------------------- hands
# Finger presets: per finger [mcp, pip, dip] flexion, spread (deg), thumb [out, palmar, opposition, mcp, ip],
# wrist [flex, deviation]. Order index, middle, ring, little.
HANDS = {
    "open": {"f": [[4, 4, 2], [4, 4, 2], [5, 5, 2], [6, 6, 3]], "spread": 13, "thumb": [36, 22, 10, 4, 4]},
    "spread": {"f": [[-8, 0, 0], [-6, 0, 0], [-6, 2, 0], [-4, 2, 0]], "spread": 22, "thumb": [50, 12, 0, 0, -6], "wrist": [-12, 0]},
    "relaxed": {"f": [[14, 24, 12], [20, 32, 15], [26, 38, 18], [32, 44, 22]], "spread": 4, "thumb": [16, 34, 28, 14, 14], "wrist": [8, 0]},
    "rest": {"f": [[6, 12, 6], [7, 13, 6], [9, 15, 7], [12, 18, 9]], "spread": 7, "thumb": [22, 12, 8, 8, 4], "wrist": [-6, 0]},
    "hold": {"f": [[52, 66, 34], [56, 70, 36], [60, 72, 38], [64, 76, 40]], "spread": 2, "thumb": [18, 52, 58, 22, 22]},
    "grip": {"f": [[86, 98, 62], [88, 100, 64], [90, 100, 64], [92, 100, 64]], "spread": 0, "thumb": [8, 38, 78, 40, 34]},
    "push_hair": {"f": [[22, 28, 14], [26, 30, 15], [30, 32, 16], [34, 36, 18]], "spread": 14, "thumb": [32, 18, 14, 8, 8], "wrist": [-24, 0]},
    "throw": {"f": [[-12, 6, 4], [-10, 6, 4], [-6, 8, 4], [-2, 10, 6]], "spread": 11, "thumb": [32, 18, 8, -2, -4], "wrist": [20, 0]},
    "point": {"f": [[0, 2, 0], [88, 100, 62], [90, 100, 62], [92, 100, 62]], "spread": 2, "thumb": [10, 36, 70, 30, 30]},
    "cup": {"f": [[22, 26, 10], [22, 26, 10], [24, 26, 10], [26, 28, 12]], "spread": 0, "thumb": [8, 46, 36, 10, 6]},
    "fist": {"f": [[90, 100, 70], [90, 100, 70], [90, 100, 70], [90, 100, 70]], "spread": 0, "thumb": [8, 30, 70, 50, 40]},
}
FING = [  # x at knuckle, y at knuckle, length, base radius, tip radius, spread weight  (in hand lengths)
    (0.125, -0.505, 0.40, 0.053, 0.041, 1.0),
    (0.042, -0.53, 0.44, 0.055, 0.043, 0.0),
    (-0.042, -0.515, 0.415, 0.052, 0.041, -0.6),
    (-0.122, -0.47, 0.335, 0.046, 0.036, -1.3),
]
PHAL = (0.46, 0.30, 0.24)


class HandPrims(Prims):
    """A hand: the palm mass (palm slab, knuckle row, thenar and hypothenar pads, metacarpals, the
    web of the thumb) blended smoothly, and each finger and the thumb as its own chain of cones,
    joined to the palm but not to each other. Neighbouring fingers stay separate forms with a dark
    crease between them, so a hand seen from its fingertips still reads as fingers by overlap
    (hands-feet.md, section 2) instead of melting into a knob. Nails are kept apart for colour."""

    def __init__(self):
        super().__init__()
        self.palm, self.chains, self.nails = Prims(), [], Prims()

    def finalize(self):
        self.cones = self.palm.cones + [c for ch in self.chains for c in ch.cones]
        self.ells = self.palm.ells + [e for ch in self.chains for e in ch.ells]

    def fn(self, k):
        fp = self.palm.fn(k)
        chs = [ch.fn(k * 0.25) for ch in self.chains]

        def f(p):
            d = fp(p)
            if chs:
                dc = chs[0](p)
                for g in chs[1:]:
                    dc = np.minimum(dc, g(p))
                d = smin(d, dc, k)
            return d
        return f


def _chain_pose(base, Rf, segs, angs, collide, seek, axis_flex=True):
    """Walk a finger: segs [(length, r_start, r_end)], angs the flexion at each joint (deg). With a
    collide(p) -> distance function, each joint is bent so its segment rests on the surface instead
    of passing through it: a phalanx that would sink in is extended (or curled) to the nearest angle
    that keeps it out; with `seek`, a phalanx that hangs just above a surface curls down onto it."""
    pts, p0, R_ = [base], base, Rf
    for j, ((ln, r1, r2), ang) in enumerate(zip(segs, angs)):
        def end(a):
            Rn = R_ @ rx(-R(a))
            return Rn, p0 + Rn @ V(0, -ln, 0)
        Rn, p1 = end(ang)
        if collide is not None:
            def gap(a):
                _, q1 = end(a)
                qs = np.stack([q1, (p0 + q1) / 2]).astype(np.float32)
                return float(np.min(collide(qs) - np.array([r2, (r1 + r2) / 2])))
            g0 = gap(ang)
            if g0 < -0.1 * r2 or (seek and g0 > 0.3 * r2 and g0 < 2.5 * r1):
                best, bestc = ang, None
                for dlt in np.linspace(-50, 70, 25):
                    a = ang + dlt
                    gg = gap(a)
                    cost = abs(dlt) * 0.002 + (10 if gg < -0.05 * r2 else 0) + (abs(gg) / r2 if seek else 0)
                    if bestc is None or cost < bestc:
                        best, bestc = a, cost
                Rn, p1 = end(best)
        pts.append(p1)
        R_ = Rn
        p0 = p1
    return pts, R_


def hand_prims(M, O, L, side, preset, extra=None, girth=1.0, collide=None):
    """Hand geometry: M local->world rotation (fingers along local -y, palm +z, thumb +x*side),
    O the wrist, L the hand length. `collide` (world points -> distance to what the hand touches)
    keeps the fingers out of objects and lets a resting or holding hand settle onto them.
    Returns HandPrims."""
    h = dict(HANDS.get(preset, HANDS["relaxed"])) if isinstance(preset, str) else dict(HANDS["relaxed"], **preset)
    if extra:
        h.update(extra)
    P = HandPrims()
    g = girth
    seek = collide is not None and (preset if isinstance(preset, str) else "") in ("rest", "hold", "grip", "push_hair", "cup")

    def W(v):
        v = np.asarray(v, np.float32) * L
        v[0] *= side
        return O + M @ v
    Mp = M @ np.diag([side, 1, 1]).astype(np.float32)
    pa = P.palm
    # palm: a flat, slightly cupped slab with the thenar and hypothenar pads
    pa.ell(W([0.0, -0.29, -0.01]), Mp, np.array([0.215, 0.24, 0.062 * g], np.float32) * L)
    pa.ell(W([0.0, -0.46, -0.0]), Mp, np.array([0.2, 0.07, 0.058 * g], np.float32) * L)          # knuckle row
    pa.ell(W([-0.13, -0.3, 0.02]), Mp, np.array([0.07, 0.17, 0.06 * g], np.float32) * L)          # hypothenar
    pa.cone(W([0, -0.0, 0]), W([0, -0.12, 0]), 0.15 * L, 0.18 * L)                                 # wrist into palm
    flex = h["f"]
    sp = h.get("spread", 6)
    for i, (x, y, ln, rb, rt, sw) in enumerate(FING):
        mcp, pip, dip = flex[i]
        base = W([x, y, 0.0])
        pa.cone(W([x * 0.55, -0.12, 0]), base, 0.055 * L * g, rb * L * g)                         # metacarpal
        pa.ell(base + Mp @ V(0, 0.005, -0.03) * L, Mp, V(0.05, 0.045, 0.035) * L * g)               # the knuckle on the back of the hand
        Rf = Mp @ rz(R(sp * sw)) @ rx(-R(mcp))
        rads = np.linspace(rb, rt, 4) * L * g
        segs = [(ln * PHAL[j] * L, rads[j], rads[j + 1]) for j in range(3)]
        pts, Rend = _chain_pose(base, Rf @ rx(R(mcp)), segs, (mcp, pip, dip), collide, seek)
        ch = Prims()
        for j in range(3):
            ch.cone(pts[j], pts[j + 1], segs[j][1], segs[j][2])
            if j:
                ch.ell(pts[j], Mp, V(1.1, 1.0, 1.0) * segs[j - 1][2] * 1.04)                           # the joint, a little wider than the shaft
        P.chains.append(ch)
        tip, nail_dir = pts[3], Rend @ V(0, 0, -1)                                                  # nail on the back of the last phalanx
        P.nails.ell(tip + Rend @ V(0, 0.3 * segs[2][0], -0.66 * segs[2][2]), Rend, V(0.72, 0.3 * segs[2][0] / segs[2][2], 0.3) * segs[2][2])
    # the thumb: its real base is low on the wrist; the pad faces across the palm, so it flexes
    # toward the little finger, not toward the palm (hands-feet.md, section 1)
    t_out, t_palm, t_opp, t_mcp, t_ip = h["thumb"]
    base = W([0.1, -0.08, 0.025])
    Rt = Mp @ rz(R(t_out)) @ rx(-R(t_palm * 0.7)) @ ry(-R(t_opp + 45))
    segs = [(0.25 * L, 0.07 * L * g, 0.062 * L * g), (0.17 * L, 0.062 * L * g, 0.054 * L * g), (0.145 * L, 0.054 * L * g, 0.044 * L * g)]
    pts, Rend = _chain_pose(base, Rt, segs, (0, t_mcp, t_ip), collide, seek)
    met_mid = (pts[0] + pts[1]) / 2
    # the thenar pad wraps the thumb's metacarpal; the web joins the thumb to the index finger
    pa.ell(met_mid + (W([0.0, -0.25, 0.03]) - met_mid) * 0.4, frame_along(pts[1] - pts[0]), V(0.105, 0.17, 0.085) * L * g)
    pa.cone(pts[1] - (pts[1] - pts[0]) * 0.15, W([0.1, -0.36, 0.0]), 0.045 * L * g, 0.032 * L * g)
    ch = Prims()
    ch.cone(pts[1], pts[2], segs[1][1], segs[1][2]); ch.cone(pts[2], pts[3], segs[2][1], segs[2][2])
    ch.ell(pts[2], Mp, V(1.06, 1, 1) * segs[1][2])
    P.chains.append(ch)
    pa.cone(pts[0], pts[1], segs[0][1], segs[0][2])
    P.nails.ell(pts[3] + Rend @ V(0, 0.3 * segs[2][0], -0.66 * segs[2][2]), Rend, V(0.74, 0.3 * segs[2][0] / segs[2][2], 0.3) * segs[2][2])
    P.finalize()
    return P


# ---------------------------------------------------------------- the head
# Action units (FACS; Ekman & Friesen) and expression presets. Values 0..1.
EXPRESSIONS = {
    "neutral": {},
    "calm": {"25": 0.05},
    "smile": {"6": 0.75, "12": 0.8},
    "laugh": {"6": 1.0, "12": 1.0, "25": 1.0, "26": 0.6, "10": 0.45, "7": 0.3},
    "gasp": {"1": 0.7, "2": 0.6, "5": 0.6, "25": 1.0, "26": 0.55, "27": 0.15},
    "surprise": {"1": 1.0, "2": 1.0, "5": 0.8, "25": 1.0, "26": 0.9},
    "fear": {"1": 1.0, "2": 0.7, "4": 0.7, "5": 1.0, "20": 1.0, "25": 1.0, "26": 0.45},
    "scream": {"1": 0.9, "2": 0.6, "4": 0.9, "5": 0.9, "20": 1.0, "25": 1.0, "26": 0.8, "27": 0.9, "10": 0.3},
    "sorrow": {"1": 1.0, "4": 0.7, "15": 0.9, "17": 0.6, "41": 0.35},
    "sleep": {"43": 1.0, "25": 0.12, "26": 0.08},
    "anger": {"4": 1.0, "5": 0.5, "7": 0.8, "23": 0.9, "17": 0.3},
    "disgust": {"9": 0.9, "10": 0.5, "15": 0.5, "17": 0.5, "4": 0.3},
}


def au_of(expr):
    if expr is None:
        return {}
    if isinstance(expr, str):
        return dict(EXPRESSIONS.get(expr, {}))
    a = dict(EXPRESSIONS.get(expr.get("preset", "neutral"), {}))
    a.update({str(k): float(v) for k, v in expr.get("au", {}).items()})
    return a


class Poly:
    """A convex block as the intersection of half-spaces, mirrored in x (a symmetric head): the
    painter's big planes made literal. Planes are (normal, point); `tri` takes three landmarks."""

    def __init__(self, inside):
        self.inside = V(*inside)
        self.N, self.P = [], []

    def plane(self, n, p):
        self.N.append(nrm(V(*n))); self.P.append(V(*p))
        return self

    def tri(self, a, b, c):
        a, b, c = V(*a), V(*b), V(*c)
        n = nrm(np.cross(b - a, c - a))
        if float(n @ (self.inside - a)) > 0:
            n = -n
        self.N.append(n); self.P.append(a)
        return self

    def done(self):
        self.Na = np.stack(self.N); self.Ca = (self.Na * np.stack(self.P)).sum(1)
        return self

    def __call__(self, q, k):
        qm = q.copy(); qm[:, 0] = np.abs(qm[:, 0])
        D = qm @ self.Na.T - self.Ca
        d = D[:, 0]
        for j in range(1, D.shape[1]):
            d = smax(d, D[:, j], k)
        return d


def ell_d(q, c, r):
    """Ellipsoid distance (approximate, conservative), centre c, radii r; q (N,3)."""
    a = (q - c) / r
    k0 = np.sqrt((a * a).sum(1))
    b = a / r
    k1 = np.sqrt((b * b).sum(1))
    return k0 * (k0 - 1) / (k1 + 1e-9)


def seg_d(q, a, b, r):
    pa, ba = q - a, b - a
    h = np.clip((pa @ ba) / float(ba @ ba + 1e-12), 0, 1)
    return np.linalg.norm(pa - h[:, None] * ba, axis=1) - r


def mirror(q):
    qm = q.copy(); qm[:, 0] = np.abs(qm[:, 0])
    return qm


def face_shape(body):
    """Landmarks of a head one unit tall (crown y=+0.5, chin y=-0.5, x = the person's left, z
    forward, origin at mid height over the ear). Adult values are Farkas's North American norms
    (Farkas 2005 via Al-Sebaei 2015, docs/subjects/face.md): thirds upper/middle/lower 67.1/54.8/72.6
    mm (men) and 63.0/50.6/64.3 (women), eye fissure 31.3/30.7, intercanthal 33.3/31.8, nose width
    34.9/31.4, over a head height of about 232/218 mm (judgement, the common vertex-menton means).
    Sex, child and old modifiers follow face.md section 4."""
    fem, old, child = body.fem, body.old, body.child
    g = lambda m, f: m + (f - m) * fem
    S = {}
    fv = 1 - 0.16 * child                       # children: the face (eye line to chin) is a smaller share
    ye = -0.5 + 0.5 * fv
    S["ye"] = ye
    S["Y"] = lambda t: ye - t * (ye + 0.5)      # t: fraction of the way from the eye line to the chin
    Y = S["Y"]
    S["t_sn"] = g(0.36, 0.365) + 0.08 * child   # nose base, as a share of eye line to chin (Met references: 0.32-0.38 adults, 0.45 a boy)
    S["t_sto"] = g(0.565, 0.57) + 0.07 * child    # mouth line (references 0.54-0.61 adults, 0.65 a boy)
    S["y_sn"], S["y_sto"] = Y(S["t_sn"]), Y(S["t_sto"])
    S["y_brow"] = ye + g(0.066, 0.074) - 0.006 * child
    S["x_eye"] = g(0.134, 0.136) * (1 + 0.07 * child)          # pupil: (en-en + ex-ex) / 4; a child's eyes are wider apart (Tuts+)          # pupil: (en-en + ex-ex) / 4
    S["w_eye"] = g(0.135, 0.141) * (1 + 0.16 * child) * (1 - 0.06 * old)   # fissure; the eye gap narrows with age (Skomina 2020)
    S["re"] = g(0.052, 0.055) * (1 + 0.28 * child)             # a 24 mm eyeball
    S["z_e"] = 0.212 + 0.004 * fem
    S["zg"] = g(0.352, 0.338) - 0.012 * child                  # glabella: flatter brow region in women (Skomina 2020)
    S["tilt"] = R(g(14, 7) - 7 * child)                        # forehead slope back from vertical
    S["ridge"] = g(0.024, 0.008) * (1 - child)                 # brow ridge
    S["z_n"] = g(0.318, 0.322) - 0.018 * child                 # nasion: children's bridge is low
    S["z_tip"] = g(0.448, 0.428) - 0.06 * child + 0.006 * old
    S["x_al"] = g(0.07, 0.066) * (1 - 0.12 * child) * (1 + 0.15 * old)   # nose width about the inner-eye distance (Farkas: 34.9/33.3, 31.4/31.8 mm); wider when old
    S["bw"] = g(0.022, 0.018) * (1 - 0.2 * child)              # nose bridge half width
    S["y_tip"] = S["y_sn"] + 0.034 - 0.014 * old + 0.006 * fem + 0.008 * child   # the tip droops with age
    S["x_zy"] = g(0.283, 0.286) * (1 - 0.02 * child)              # zygomatic half width (zy-zy about 0.57-0.6 of the head height)
    S["x_t"] = g(0.268, 0.272)
    S["x_go"] = g(0.232, 0.212) * (1 - 0.14 * child)            # men: wider jaw at gonion (Skomina 2020)
    S["y_go"] = Y(g(0.72, 0.66))
    S["z_go"] = g(-0.045, -0.025)
    S["x_ch"] = g(0.085, 0.06) * (1 - 0.2 * child)
    S["z_pog"] = g(0.352, 0.338) - 0.035 * child
    S["cx"] = g(0.114, 0.116) * (1 - 0.12 * child)             # mouth half width (ch-ch 53 / 50 mm)
    S["hu"] = g(0.026, 0.032) * (1 - 0.45 * old)               # vermilion heights; they narrow with age
    S["hl"] = g(0.034, 0.042) * (1 - 0.4 * old)
    S["tu"] = g(0.011, 0.014) * (1 - 0.3 * old)
    S["tl"] = g(0.013, 0.017) * (1 - 0.3 * old)
    S["z_bar"] = g(0.372, 0.366) - 0.02 * child                # front of the muzzle barrel (upper lip)
    S["full"] = g(0.75, 1.0) + 0.9 * child - 0.3 * old         # cheek fullness
    return S


def head_part(o, body, O, M, skin, eye_col="#e8e0d6", iris_col="#3a2a22", lip_col=None, gloss=0.0, gaze=(0, 0)):
    """A head built the way a painter blocks one in: the cranium ball with its flat side, then the big
    planes of the face as literal planes (forehead front and sides, the cheek's front and side, the
    jaw's side and underside, the chin, the nose's front, sides and base), the muzzle barrel, eye
    sockets carved under the brow with eyeballs and lids in them, lips as volumes on the barrel, and
    soft masses (cheek pads, brows, jowls) that the action units move. O = head centre (mid height,
    at the ear), M = head local->world, H = head height. `planes` (0-1) sets how crisp the plane
    breaks are; 0 is a soft form."""
    H = body.u
    au = au_of(o.get("expression", "neutral"))
    A = lambda k: float(au.get(k, 0.0))
    fem, old, child = body.fem, body.old, body.child
    S = face_shape(body)
    Y, ye = S["Y"], S["ye"]
    planes = float(o.get("planes", 0.45))
    kp = (0.008 + 0.045 * (1 - planes)) * (1 + 0.5 * fem + 0.6 * child) * (1 - 0.3 * old)   # plane-break softness (judgement)

    # ---------- action units -> parameters (judgement, calibrated by eye against face.md section 5)
    au["25"] = max(A("25"), 0.7 * A("10") * (1 - A("23")))      # a raised upper lip parts the lips (AU10)
    jaw = R(2 + 22 * A("26") + 12 * A("27") + A("25"))
    drop = 0.42 * math.sin(jaw - R(2))
    sto = S["y_sto"]
    cx = S["cx"] + 0.034 * A("12") + 0.04 * A("20") - 0.02 * A("23") - 0.022 * max(A("26") - A("12") - A("20"), 0) - 0.006 * A("15")
    cy = sto + 0.042 * A("12") - 0.03 * A("15") - 0.014 * A("20") + 0.008 * A("10") - 0.004 * A("17")
    up_mid = sto + 0.002 + 0.024 * A("10") + 0.005 * A("25") + 0.01 * A("12") * A("25") - 0.006 * A("17") * (1 - A("25"))
    lo_mid = up_mid - 0.004 * A("25") - drop - 0.022 * A("20") * A("25") - 0.01 * A("27")
    if A("25") < 0.2 and drop < 0.01:
        lo_mid = up_mid
    drop_c = drop * 0.92            # how far the lower lip's edge moved with the jaw (rotation plus glide; judgement)
    pu = max(2.0 + 3.0 * A("20") - 0.9 * A("12"), 1.05)
    pl = 2.0 + 2.5 * A("20") + 0.8 * A("12")
    lid_u = 0.022 + 0.003 * fem + 0.003 * child + 0.017 * A("5") - 0.003 * A("7") - 0.002 * A("6") - 0.012 * A("41") - 0.004 * old
    lid_l = 0.019 - 0.004 * A("5") - 0.007 * A("7") - 0.006 * A("6") - 0.002 * A("12")
    closed = max(A("43"), A("45"))
    lid_u = lid_u * (1 - closed) - 0.004 * closed
    lid_l = lid_l * (1 - closed) - 0.004 * closed
    b_in = 0.03 * A("1") - 0.022 * A("4") - 0.004 * A("6")       # inner brow lift
    b_out = 0.03 * A("2") - 0.01 * A("4") - 0.012 * old - 0.004 * A("6")
    knit = 0.014 * A("4")
    cheek_up = 0.028 * A("6") + 0.014 * A("12") + 0.01 * A("10") - 0.03 * old
    sneer = A("9")
    cheek_up += 0.015 * sneer
    b_in -= 0.012 * sneer
    chin_up = 0.02 * A("17")

    M = np.asarray(M, np.float32)
    pivot = V(0, ye - 0.07, -0.03)               # the jaw hinge, in front of the ear
    Rj = rx(jaw)
    glide = V(0, -0.01, 0.16) * math.sin(jaw - R(2))   # the condyle slides forward as the mouth opens (judgement)
    sk = hx(skin)
    lips = hx(lip_col) if lip_col else sk * V(1.0, 0.8, 0.8)
    teeth, mouthc = hx("#a89e8c"), hx("#1e0c0a")
    hd = o.get("hair")
    hcol = (hd if isinstance(hd, str) else hd.get("color")) if hd else None
    brow_col = hx(o.get("brows", hcol or "#3a2a20"))

    # ---------- the cranium: a ball with its side cut flat (Loomis)
    cr_c = V(0, 0.1 + 0.02 * child, -0.06)
    cr_r = V(0.33 * body.g(1, 0.97), 0.385, 0.405) * (1 + 0.08 * child)     # head breadth about 0.65 of its height (151/232 mm)
    x_side = 0.318 * body.g(1, 0.97) * (1 + 0.05 * child)

    # ---------- the upper face: forehead, temples, cheek planes (fixed to the skull)
    zg, tl_, yb = S["zg"], S["tilt"], S["y_brow"]
    xe, re_, ze = S["x_eye"], S["re"], S["z_e"]
    zfh = lambda y: zg - (y - yb) * math.tan(tl_)            # forehead front at height y
    up = Poly((0, ye - 0.05, 0.0))
    xt, xz, xg, ygo, zgo = S["x_t"], S["x_zy"], S["x_go"], S["y_go"], S["z_go"]
    ysn = S["y_sn"]
    F1 = (0.13, yb + 0.12, zfh(yb + 0.12) - 0.024)                  # forehead: the front plane's outer edge, high and low
    F2 = (0.15, yb + 0.005, zfh(yb) - 0.03)
    T1 = (xt, yb + 0.15, 0.08)                                       # temple
    Ac = (0.075, ye - 0.06, 0.318)                                   # cheek front, beside the nose under the inner eye
    Bk = (xe + 0.062, ye - 0.075, 0.245 - 0.008 * fem)               # cheekbone corner (zygoma), under the outer eye
    Cc = (0.105, ysn - 0.005, 0.312)                                 # cheek beside the nostril
    Dz = (xz, ye - 0.04, 0.06)                                       # zygomatic arch
    Mc = (0.158, Y(0.6), 0.25 + 0.012 * fem)                         # where the muzzle turns into the side of the face
    E2 = (xz - 0.045, Y(0.5), 0.075)                                 # side of the face under the arch (masseter)
    Go = (xg, ygo, zgo)
    up.plane((0, math.sin(tl_), math.cos(tl_)), (0, yb, zg))         # forehead front
    Or = (xe + 0.08, ye + 0.01, ze + 0.0)                            # the outer rim of the orbit
    up.tri(F1, Or, T1)                                               # forehead side, turning to the temple
    up.plane((0.95, 0.05, 0.3), (xt, ye, 0.12))                      # temple
    up.plane((0, 0.8, 0.6), (0, 0.31, zfh(0.31)))                    # forehead top turns back to the crown
    up.plane((0, -0.94, 0.34), (0, ye - 0.01, zg))                   # under the brow: the socket's roof
    up.plane((0, 0, -1), (0, 0, -0.12))
    up.plane((0, 1, 0), (0, 0.33, 0))
    up.done()
    # the mandible's landmarks (its block moves with the jaw; the cheek block shares its side planes)
    xc, zp = S["x_ch"], S["z_pog"]
    zme = zp - 0.075
    Me = (0, -0.5, zme)
    J3 = (xc + 0.055, -0.475, zp - 0.1)                              # the jawline near the chin
    G = (xg + 0.012, Y(0.62), -0.06)
    Nl = (0.118, Y(0.5), 0.306)                                      # beside the top of the mouth corner (the nasolabial line)
    Bk2 = (Bk[0] + 0.02, Bk[1] - 0.045, Bk[2] - 0.045)               # just below the cheekbone corner
    ck = Poly((0, ye - 0.1, 0.0))                                    # the cheeks and the middle of the face
    jw = Poly((0, Y(0.62), 0.12))
    for P_ in (ck, jw):                                              # shared planes: no step at the side of the face
        P_.tri(Bk2, Mc, E2)                                          # lower cheek, under the zygoma down to the mouth's corner
        P_.tri(Dz, E2, G)                                            # side of the face
        P_.plane((0.25, -0.3, -0.92), Go)                            # ramus back
        P_.tri(Me, Go, (-Go[0], Go[1], Go[2]))                       # underside, rising from the chin to the jaw angle
        P_.tri(J3, Go, (xc + 0.02, -0.5, zme - 0.03))                # the jawline's lower turn
        P_.plane((0, 0, -1), (0, 0, -0.13))
    ck.tri(Ac, Bk, Nl)                                               # cheek front, its lower edge running from the zygoma to the mouth
    ck.tri(Bk, Dz, (xz - 0.045, Y(0.6), 0.2))                        # cheekbone side (gives way to the lower cheek below)
    ck.plane((0.8, 0.55, 0.22), (Dz[0], Dz[1] + 0.02, Dz[2]))         # top of the cheekbone, turning in to the temple
    ck.plane((0.95, 0.05, 0.3), (xt, ye, 0.12))                      # temple
    ck.plane((0, -0.1, 1), (0, Y(0.4), 0.33))                        # behind the barrel
    ck.plane((0, 0.2, 1), (0, ye, 0.318))                            # the nose root between the eyes
    yb0, yb1 = S["y_sto"] + 0.005, Y(0.8)
    ck.plane((0, -0.43, yb0 - yb1), (0, yb0, 0.33))                  # under the cheeks: front at the mouth, back at the jaw angle
    ck.plane((0, 1, 0), (0, yb, 0))
    ck.done()
    J1 = (Mc[0] - 0.005, Y(0.66), Mc[2] - 0.01)
    jw.plane((0, -0.12, 1), (0, Y(0.88), zp))                        # chin front
    jw.tri((xc, Y(0.8), zp - 0.015), (xc, -0.49, zp - 0.05), J3)     # chin side
    jw.plane((0, -0.7, 0.72), (0, -0.495, zme + 0.03))               # chin's lower turn
    jw.plane((0, 1, 0), (0, Y(0.45), 0))
    jw.done()

    # ---------- the nose: a wedge with front, sides and base, alae and a tip
    yn, zn = ye + 0.035, S["z_n"]
    T = V(0, S["y_tip"], S["z_tip"])
    ysn = S["y_sn"]
    zsn = S["z_tip"] - 0.068
    xa = S["x_al"]
    bw = S["bw"]
    nz = Poly((0, (yn + ysn) / 2, 0.25))
    dT = T - V(0, yn, zn)
    nz.plane((0, float(dT[2]), float(-dT[1])), (0, yn, zn))                                           # dorsum (front)
    nz.tri((bw, yn, zn - 0.012), (bw + 0.016, T[1] + 0.01, T[2] - 0.02), (xa - 0.02, ysn + 0.03, 0.335))   # side
    nz.tri((0, float(T[1]) - 0.02, float(T[2]) - 0.01), (0, ysn, zsn), (xa - 0.004, ysn + 0.004, 0.34))   # base
    nz.plane((0, 0, -1), (0, 0, 0.27))
    nz.plane((0, 1, 0.2), (0, yn + 0.02, zn))
    nz.done()
    al_c = V(xa - 0.02, ysn + 0.016 + 0.01 * sneer, 0.335)
    al_r = V(0.026, 0.025, 0.033) * (1 + 0.1 * sneer)
    tip_c = T - V(0, 0.006, 0.022)
    tip_r = V(body.g(0.031, 0.026), 0.027, 0.026) * (1 - 0.15 * child)

    # ---------- eyes
    eyes = [V(s * xe, ye, ze) for s in (1, -1)]
    lift_mean = 0.5 * (b_in + b_out)
    sock_c = V(xe + 0.004, ye + 0.014 + 0.45 * lift_mean, ze + 0.074)
    sock_r = V(0.08, 0.056 + 0.35 * max(lift_mean, 0), 0.078)
    lid_r = V(S["w_eye"] / 2 + 0.004, re_ + 0.012, re_ + 0.007)
    hw = S["w_eye"] / 2
    gaze_dir = nrm(ry(R(gaze[0])) @ rx(-R(gaze[1])) @ V(0, 0, 1))

    def fissure(q, e):
        """Signed 2D distance-like value to the eye opening (negative inside), from the frontal view:
        the upper lid's arc peaks toward the nose, the lower lid's lowest point lies outward, and the
        outer corner sits a little higher (canthal tilt)."""
        u = (np.abs(q[:, 0]) - abs(e[0]))
        s = np.clip(u / hw, -1, 1)
        v = q[:, 1] - e[1] - 0.004 * s
        base = np.maximum(1 - s * s, 0)
        vu = lid_u * base ** 0.55 * (1 - 0.15 * s)
        vl = -lid_l * base ** 0.75 * (1 + 0.2 * s)
        return np.maximum.reduce([v - vu, vl - v, np.abs(u) - hw]), v - vu, s

    # ---------- the mouth: an opening on the barrel, lips as volumes around it
    def edges(q):
        x = np.abs(q[:, 0])
        t = np.clip(x / cx, 0, 1)
        yu = up_mid + (cy - up_mid) * (1 - (1 - t ** pu) ** (1 / pu))
        yl = lo_mid + (cy - lo_mid) * (1 - (1 - t ** pl) ** (1 / pl))
        return x, t, yu, yl

    def mouth2d(q):
        x, t, yu, yl = edges(q)
        return np.maximum.reduce([x - cx, q[:, 1] - yu, yl - q[:, 1]])

    opened = lo_mid < up_mid - 0.006

    def barrel(q, y0, y1, zc_front):
        rxb, rzb = body.g(0.158, 0.148) * (1 - 0.1 * child), 0.19
        zc = zc_front - rzb
        e = np.sqrt((q[:, 0] / rxb) ** 2 + ((q[:, 2] - zc) / rzb) ** 2) - 1
        d = e * min(rxb, rzb)
        return smax(smax(d, q[:, 1] - y0, 0.02), y1 - q[:, 1], 0.02)

    def local(p):
        return ((p - O) @ M) / H

    def skull(q):
        """The cranium and the forehead block only: what the hair sits on."""
        d = ell_d(q, cr_c, cr_r)
        d = smax(d, np.abs(q[:, 0]) - x_side, 0.05)
        return smin(d, up(q, kp), 0.05)

    def sdf_local(q):
        qm = mirror(q)
        qj = (q - pivot - glide) @ Rj + pivot      # points in the jaw's rest frame
        qjm = mirror(qj)
        # cranium with its flat side plane
        d = smin(skull(q), ck(q, kp), 0.045)
        if S["ridge"] > 0.002:                          # the brow ridge (bony, fixed)
            br = seg_d(qm, V(0.03, yb - 0.004, zg - 0.012), V(xe + 0.07, yb + 0.002 - 0.01 * old, zfh(yb) - 0.085), S["ridge"])
            d = smin(d, br, 0.025)
        if child > 0:                                    # frontal bossing of the child's forehead
            d = smin(d, ell_d(qm, V(0.09, yb + 0.15, zfh(yb + 0.15) - 0.12), V(0.13, 0.13, 0.12)), 0.04 * child + 1e-3)
        if old > 0:                                      # temples hollow with age
            d = smax(d, -ell_d(qm, V(S["x_t"] + 0.02, yb + 0.05, 0.12), V(0.03, 0.06, 0.06) * (0.3 + 0.7 * old)), 0.02)
        # eye sockets: the plane under the brow turns into the socket
        d = smax(d, -ell_d(qm, sock_c, sock_r), 0.022)
        # cheek pads (malar fat): lifted and rounded by AU6/12, low and flat with age
        pad_c = V(xe - 0.005 + 0.014 * A("12"), ye - 0.088 + cheek_up, 0.248 + 0.018 * A("6"))
        pad_r = V(0.08, 0.058, 0.042) * (0.7 + 0.3 * S["full"]) * (1 + 0.18 * A("6") + 0.08 * A("12"))
        d = smin(d, ell_d(qm, pad_c, pad_r), 0.045)
        # the mandible, joined by the soft cheek; more blending as the jaw opens
        dj = jw(qj, kp)
        dj = smin(dj, ell_d(qj, V(0, Y(0.86) + chin_up, zp - 0.045 + 0.5 * chin_up), V(S["x_ch"] * 0.95, 0.055, 0.05)), 0.03)
        d = smin(d, dj, 0.045 + 0.08 * (jaw - R(2)))
        # the muzzle barrel: upper part on the skull, lower part on the jaw
        d = smin(d, barrel(q, S["y_sn"] - 0.005, sto - 0.01, S["z_bar"]), 0.035)
        d = smin(d, barrel(qj, sto + 0.01, Y(0.76), S["z_bar"] - 0.016 + chin_up * 0.5), 0.05)
        if old > 0:   # jowls just above the jawline, outside the chin, and the fold between (not a muzzle)
            d = smin(d, ell_d(qjm, V(xc + 0.065, Y(0.86), zp - 0.1), V(0.06, 0.03, 0.045) * old + 1e-3), 0.05)
            d = smin(d, ell_d(qm, V(xe - 0.01, ye - 0.055, 0.262), V(0.04, 0.014, 0.018) * old + 1e-3), 0.01)   # lower-lid bags
            d = smin(d, ell_d(qm, V(xe + 0.035, ye + 0.04, ze + 0.045), V(0.045, 0.016, 0.025) * old + 1e-3), 0.01)  # hooding
        # the nose
        dn = nz(q, kp * 0.6)
        dn = smin(dn, ell_d(qm, al_c, al_r), 0.015)
        dn = smin(dn, ell_d(q, tip_c, tip_r), 0.015)
        d = smin(d, dn, 0.022)
        # folds: nasolabial (cheek raised, age), marionette (age), glabella, forehead
        fold = 0.007 * (A("12") + 0.6 * A("10") + 0.4 * A("6")) + 0.006 * old + 0.003
        a = V(xa + 0.004, ysn + 0.024, 0.335); b = V(cx + 0.02, cy - 0.02, S["z_bar"] - 0.06)
        d = smax(d, -seg_d(qm, a, b, fold), 0.012)
        if old > 0:
            d = smax(d, -seg_d(qjm, V(S["cx"] + 0.005, sto - 0.03, S["z_bar"] - 0.04), V(xc + 0.035, Y(0.9), zp - 0.07), 0.005 * old + 1e-4), 0.012)
        lift = 0.5 * (A("1") + A("2"))
        if lift > 0.2 or old > 0.3:
            amp = 0.002 * lift + 0.0006 * old
            mk = np.clip(1 - np.abs(q[:, 0]) / 0.2, 0, 1) * np.clip((q[:, 1] - yb - 0.05) / 0.03, 0, 1) * np.clip((0.28 - q[:, 1]) / 0.05, 0, 1)
            d = d + amp * mk * np.sin(q[:, 1] * 150) * (q[:, 2] > 0)
        if A("4") > 0.3:
            mk = np.exp(-((qm[:, 0] - 0.018) / 0.01) ** 2) * np.exp(-((q[:, 1] - yb - 0.02) / 0.035) ** 2) * (q[:, 2] > 0.25)
            d = d + 0.005 * A("4") * mk
        # eyebrows: soft ridges of tissue and hair, moved by AU1/2/4
        sb = np.clip((qm[:, 0] - (0.032 - knit)) / (xe + 0.085 - 0.032), 0, 1)
        arch = body.g(0.01, 0.018)
        ybc = yb + 0.016 + arch * np.sin(math.pi * sb ** 0.8) + b_in * (1 - sb) + b_out * sb - 0.006 * sb * old
        # lips: volumes on the barrel
        x, t, yu, yl = edges(q)
        tt = np.clip(x / (cx + 0.012), 0, 1)
        wl = np.clip(1 - tt ** 2, 0, 1) ** 0.8
        front = np.clip((q[:, 2] - (S["z_bar"] - 0.07)) / 0.04, 0, 1)
        su = (q[:, 1] - yu) / (S["hu"] * (1 - 0.35 * tt))
        bu = np.clip(1 - np.clip(su, 0, 1) ** 1.6, 0, 1) * np.clip((su + 0.15) / 0.15, 0, 1)
        bu = bu * bu * (3 - 2 * bu)
        # the lower lip rides on the jaw: its edge in the jaw's rest frame
        sl = (yl + drop_c - qj[:, 1]) / (S["hl"] * (1 - 0.3 * A("20")) * (1 - 0.35 * tt))
        bl = np.clip(1 - np.clip(sl, 0, 1), 0, 1) ** 0.3 * (0.7 + 0.3 * np.clip(sl / 0.35, 0, 1)) * np.clip((sl + 0.15) / 0.15, 0, 1) * (sl < 1)
        frontj = np.clip((qj[:, 2] - (S["z_bar"] - 0.075)) / 0.04, 0, 1)
        d = d - S["tu"] * bu * wl * front - S["tl"] * bl * (1 + 0.4 * A("17") * (1 - A("25"))) * wl * frontj
        # the mouth: a closed line, or the opening with the teeth and the dark inside
        if not opened:
            yline = up_mid - 0.002 + (cy - up_mid) * t ** pu
            slit = np.maximum.reduce([np.abs(q[:, 1] - yline) - 0.0025 * (1 - t ** 4), x - cx, S["z_bar"] - 0.04 - q[:, 2]])
            d = smax(d, -slit, 0.004)
        else:
            mo = mouth2d(q)
            d = smax(d, -np.maximum(mo, 0.2 - q[:, 2]), 0.006)
            rxt, rzt = body.g(0.145, 0.136) * 0.9, 0.17
            zct = S["z_bar"] - 0.03 - rzt
            ring = lambda qq: np.abs(np.sqrt((qq[:, 0] / rxt) ** 2 + ((qq[:, 2] - zct) / rzt) ** 2) - 1) * 0.15 - 0.006
            tu_ = np.maximum.reduce([ring(q), np.abs(q[:, 1] - (sto + 0.012)) - 0.024, 0.2 - q[:, 2]])
            tl_d = np.maximum.reduce([ring(qj), np.abs(qj[:, 1] - (sto - 0.034)) - 0.022, 0.2 - qj[:, 2]])
            d = np.minimum(d, np.minimum(tu_, tl_d))
            d = np.minimum(d, ell_d(qj, V(0, sto - 0.05, 0.24), V(0.075, 0.03, 0.09)))
        # eyeballs and lids
        for e in eyes:
            fs, _, _ = fissure(q, e)
            lids = np.maximum(ell_d(q, e, lid_r), -fs)
            d = smin(d, lids, 0.01)
            d = np.minimum(d, np.linalg.norm(q - e, axis=1) - re_)
        # ears
        ear_c = V(x_side + 0.004, ye - 0.035 - 0.012 * old, -0.065)
        Me = (ry(R(-12)) @ rx(R(-14))).T
        qe = (qm - ear_c) @ Me.T
        de = ell_d(qe, V(-0.006, 0, 0), V(0.02, 0.112 + 0.016 * old, 0.062))
        de = smax(de, -ell_d(qe, V(0.018, -0.02, 0.008), V(0.016, 0.045, 0.032)), 0.01)
        if o.get("ears", True):
            d = smin(d, de, 0.015)
        return d

    def f(p):
        return sdf_local(local(p)) * H * 0.8

    def colorf(p):
        q = local(p)
        qm = mirror(q)
        n = len(q)
        c = np.broadcast_to(sk, (n, 3)).copy()
        # the three colour zones: forehead lighter and cooler, cheeks, nose and ears warmer, jaw cooler
        warm = np.exp(-((qm[:, 0] - 0.15) / 0.08) ** 2 - ((q[:, 1] - ye + 0.12) / 0.1) ** 2) + np.exp(-(q[:, 0] / 0.05) ** 2 - ((q[:, 1] - S["y_tip"]) / 0.07) ** 2)
        c *= (1 + 0.07 * np.clip(warm, 0, 1)[:, None] * V(1, -0.6, -0.8))
        cool = np.clip((S["y_sto"] - 0.02 - q[:, 1]) / 0.1, 0, 1) * (1 - fem) * (1 - child) * 0.6
        c *= (1 - 0.07 * cool[:, None] * V(1, 0.6, -0.4))
        # eyebrows (hair over the brow ridge)
        sb = np.clip((qm[:, 0] - (0.032 - knit)) / (xe + 0.085 - 0.032), 0, 1)
        arch = body.g(0.01, 0.018)
        ybc = yb + 0.016 + arch * np.sin(math.pi * sb ** 0.8) + b_in * (1 - sb) + b_out * sb - 0.006 * sb * old
        bh = 0.014 * (1.2 - 0.6 * sb) * body.g(1, 0.8)
        wgt = np.clip(1.4 - np.abs(q[:, 1] - ybc) / bh, 0, 1) * np.clip((qm[:, 0] - 0.028 + knit) / 0.015, 0, 1) \
            * np.clip((xe + 0.09 - qm[:, 0]) / 0.03, 0, 1) * (q[:, 2] > 0.2) * body.g(0.6, 0.5)
        c = c * (1 - wgt[:, None]) + brow_col[None] * wgt[:, None]
        # lips
        x, t, yu, yl = edges(q)
        su = (q[:, 1] - yu) / S["hu"]
        sl = (yl - q[:, 1]) / (S["hl"] * (1 - 0.3 * A("20")))
        on_lip = ((su > -0.05) & (su < 1.0) | (sl > -0.05) & (sl < 1.0)) & (x < cx * (1.0 - 0.04 * t)) & (q[:, 2] > S["z_bar"] - 0.06)
        lw = body.g(0.5, 0.68) * (1 - 0.3 * old)
        c[on_lip] = c[on_lip] * (1 - lw) + lips * lw
        if opened:
            mo = mouth2d(q)
            inside = (mo < 0.003) & (q[:, 2] < S["z_bar"] - 0.012)
            c[inside] = mouthc
            qj = (q - pivot - glide) @ Rj + pivot
            rxt, rzt = body.g(0.145, 0.136) * 0.9, 0.17
            zct = S["z_bar"] - 0.03 - rzt
            ring = lambda qq: np.abs(np.sqrt((qq[:, 0] / rxt) ** 2 + ((qq[:, 2] - zct) / rzt) ** 2) - 1) < 0.08
            tm = inside & ((ring(q) & (np.abs(q[:, 1] - (sto + 0.012)) < 0.025)) | (ring(qj) & (np.abs(qj[:, 1] - (sto - 0.034)) < 0.023)))
            c[tm] = teeth
        else:
            yline = up_mid - 0.002 + (cy - up_mid) * t ** pu
            ml = (np.abs(q[:, 1] - yline) < 0.004) & (x < cx) & (q[:, 2] > S["z_bar"] - 0.05)
            c[ml] = c[ml] * 0.35 + mouthc * 0.65
        # nostrils: the dark under the alae
        nos = ell_d(qm, V(xa * 0.55, ysn + 0.004, zsn + 0.022), V(0.017, 0.007, 0.016)) < 0.002
        c[nos] = c[nos] * 0.4 + mouthc * 0.3
        # eyes: sclera, iris, pupil; the lash line of the upper lid
        for e in eyes:
            qe = q - e
            r_ = np.linalg.norm(qe, axis=1)
            on = np.abs(r_ - re_) < 0.0025
            dirn = qe / (r_[:, None] + 1e-9)
            cosg = dirn @ gaze_dir
            c[on] = hx(eye_col) * 0.9
            ir = on & (cosg > 0.87)
            c[ir] = hx(iris_col)
            c[on & (cosg > 0.975)] = hx("#0c0806")
            fs, du, s = fissure(q, e)
            lash = (du > -0.002) & (du < 0.007 + 0.002 * fem) & (np.abs(s) < 0.97) & (r_ > re_ + 0.002) & (q[:, 2] > e[2]) & (closed < 0.5)
            c[lash] = c[lash] * body.g(0.35, 0.2) + brow_col * body.g(0.35, 0.5)
            if closed >= 0.5:
                lash = (np.abs(du) < 0.004) & (np.abs(s) < 0.95) & (q[:, 2] > e[2])
                c[lash] = c[lash] * 0.5 + brow_col * 0.3
        return c
    return dict(f=f, colorf=colorf, color=sk, element="head", bound=(O, H * 0.64), gloss=gloss, planes=planes,
                frame=M, scale=H, lift=(lid_l, lid_u), polys=dict(up=up, ck=ck, jw=jw, nose=nz, k=kp, sdf=sdf_local), skull=skull,
                marks=dict(crown=(0, 0.5, -0.06), chin=(0, -0.5, zp - 0.075), brow=(0, yb, zg), eye_l=(xe, ye, ze + re_), eye_r=(-xe, ye, ze + re_),
                           en_l=(xe - hw, ye, ze + 0.03), ex_l=(xe + hw, ye + 0.004, ze), en_r=(-xe + hw, ye, ze + 0.03), ex_r=(-xe - hw, ye + 0.004, ze),
                           al_l=(xa, ysn + 0.01, 0.33), al_r=(-xa, ysn + 0.01, 0.33), sn=(0, ysn, zsn),
                           ch_l=(cx, cy, S["z_bar"] - 0.04), ch_r=(-cx, cy, S["z_bar"] - 0.04), up_mid=(0, up_mid, S["z_bar"]), lo_mid=(0, lo_mid, S["z_bar"]),
                           lid_u=(xe, ye + lid_u, ze + re_), lid_l=(xe, ye - lid_l, ze + re_)))


def hair_part(o, body, O, M, wind, collide, skull=None):
    """Hair as masses: a cap following the cranium, plus a bun, a ponytail or long locks that hang
    and stream (rope simulation), or a receding/bald crown."""
    hd = o.get("hair")
    if not hd:
        return []
    if isinstance(hd, str):
        hd = {"color": hd}
    style = hd.get("style", "short")
    col = hd.get("color", "#2a1e18")
    H = body.u
    M = np.asarray(M, np.float32)
    th = hd.get("thickness", {"short": 0.035, "bun": 0.03, "long": 0.04, "slick": 0.012, "receding": 0.02, "bald": 0.02}.get(style, 0.03))
    front = hd.get("hairline", {"receding": 0.36, "slick": 0.34}.get(style, 0.3))

    def local(p):
        return ((p - O) @ M) / H

    def cap(q):
        z = q[:, 2]
        # hairline: higher in front, down to the nape at the back, above the ears at the sides
        hl = front + (np.clip(-z, 0, 0.4) / 0.4) * (-0.62 - front)
        side = np.clip((np.abs(q[:, 0]) - 0.2) / 0.1, 0, 1) * np.clip((z + 0.1) / 0.25, 0, 1)
        hl = hl + side * (0.17 - front)
        hl = hl + (0.03 if style in ("short", "receding", "slick") else 0.008) * np.cos(q[:, 0] * 14) * (z > 0)   # an irregular front edge for short hair
        t = th * np.clip((q[:, 1] - hl) / 0.1, 0.12, 1.0)        # thin at the hairline, full above
        d = np.linalg.norm((q - V(0, 0.1, -0.06)) / V(0.32, 0.385, 0.405), axis=1) - 1
        d = d * 0.37
        if skull is not None:          # sit on the head's own forehead and temple planes
            d = np.minimum(d, skull(q))
        d = d - t - 0.004
        d = np.maximum(d, (hl - q[:, 1]) * 0.5)
        if style in ("receding", "bald"):
            crown = np.linalg.norm((q[:, [0, 2]] - V(0, 0.02)) / V(0.24, 0.3), axis=1) - 1
            topcut = np.maximum(-crown * 0.2, 0.05 - q[:, 1]) if style == "receding" else -(q[:, 1] - 0.0)
            d = np.maximum(d, -topcut) if style == "receding" else np.maximum(d, q[:, 1] - 0.05)
        if style == "slick":   # wet hair combed straight back: thin, in a few loose lengthwise locks
            d = d + 0.004 * np.sin(q[:, 0] * 38 + 3 * np.sin(q[:, 2] * 9)) * np.clip(q[:, 1] + 0.2, 0, 1)
        return d
    parts = []
    extra = Prims()
    if style == "bun":
        extra.ell(V(0, 0.12, -0.47), rx(R(-20)), V(0.13, 0.12, 0.11))
    fn_extra = extra.fn(0.03) if not extra.empty() else None
    locks = None
    if style in ("long", "ponytail"):
        n_l = 7 if style == "long" else 1
        locks = []
        Ln = hd.get("length", 0.35 if style == "long" else 0.25)
        for i in range(n_l):
            a = (i / max(n_l - 1, 1) - 0.5) * 2.4 if n_l > 1 else 0
            anc = V(math.sin(a) * 0.3, 0.0 - 0.15 * abs(math.sin(a)), -0.3 - 0.1 * math.cos(a)) if n_l > 1 else V(0, 0.05, -0.44)
            aw = O + M @ (anc * H)
            pts = rope(aw, 8, Ln / 8, wind, collide, drag=hd.get("drag", 1.6), seed=i, r=0.02)
            locks.append(pts)
    gl = hd.get("gloss", 0.6 if style == "slick" else 0.15)

    def f(p):
        d = cap(local(p)) * H
        if fn_extra:
            d = smin(d, fn_extra(local(p)) * H, 0.02)
        if locks:
            for pts in locks:
                n = len(pts) - 1
                r1 = np.linspace(0.05, 0.025, n) * H
                d = smin(d, rc_batch(p, pts[:-1], pts[1:], r1, r1 * 0.85).min(1), 0.03)
        return d * 0.9
    sph = [(O, H * 0.7)]
    if locks:
        sph += [(q, 0.05) for pts in locks for q in pts]
    return [part(f, col, "hair", sph, gloss=gl)]


# ---------------------------------------------------------------- cloth: ropes under gravity and wind
def rope(anchor, n, seg, wind, collide, drag=1.5, seed=0, r=0.03, init=None, iters=260, flutter=0.35, stiff=0.6):
    """Verlet rope from a fixed anchor: gravity, wind drag with a little spatial turbulence, and a
    collision push-out against the body (collide(p) -> distance). Returns (n+1,3) points."""
    rng = np.random.default_rng(seed)
    g = V(0, -9.8, 0)
    w = np.asarray(wind, np.float32)
    d0 = nrm(init) if init is not None else nrm(V(0, -1, 0) + 0.02 * w)
    pts = np.stack([anchor + d0 * seg * i for i in range(n + 1)]).astype(np.float32)
    prev = pts.copy()
    dt = 0.016
    ph = rng.uniform(0, 6.28, 3)
    wn = np.linalg.norm(w) + 1e-6
    side = nrm(np.cross(w / wn, V(0, 1, 0))) if wn > 0.5 else V(1, 0, 0)
    for it in range(iters):
        vel = (pts - prev) * 0.94
        prev = pts.copy()
        i = np.arange(n + 1, dtype=np.float32)[:, None]
        gust = w * (1 + flutter * np.sin(i * 0.5 + ph[0])) + wn * flutter * 0.3 * (side * np.sin(i * 0.6 + ph[1]) + V(0, 0.6, 0) * np.sin(i * 0.4 + ph[2]))
        acc = g + drag * (gust - vel / dt) * 0.5
        pts = pts + vel + acc * dt * dt
        pts[0] = anchor
        for _ in range(3):
            dv = pts[1:] - pts[:-1]
            L = np.linalg.norm(dv, axis=1, keepdims=True) + 1e-9
            corr = dv * (1 - seg / L) * 0.5
            pts[1:] -= corr; pts[:-1] += corr
            if stiff > 0 and n > 2:
                dv2 = pts[2:] - pts[:-2]
                L2 = np.linalg.norm(dv2, axis=1, keepdims=True) + 1e-9
                c2 = dv2 * (1 - 1.9 * seg / L2) * 0.5 * stiff * (L2 < 1.9 * seg)
                pts[2:] -= c2; pts[:-2] += c2
            pts[0] = anchor
            if collide is not None:
                dd = collide(pts)
                bad = dd < r
                if bad.any():
                    e = 0.004
                    gr = np.stack([(collide(pts + V(*(e * np.eye(3)[k]))) - dd) / e for k in range(3)], 1)
                    pts[bad] += nrm(gr[bad]) * (r - dd[bad])[:, None]
                    prev[bad] = pts[bad]        # friction: cloth that touches the body stays put
                pts[0] = anchor
    for _ in range(4):        # settle the odd/even ripple the constraints leave behind
        pts[1:-1] = 0.25 * pts[:-2] + 0.5 * pts[1:-1] + 0.25 * pts[2:]
        pts[-1] = 0.5 * pts[-1] + 0.5 * (2 * pts[-2] - pts[-3])
    return pts


def cloth_sim(G, wind, collide, drag=1.1, r=0.035, iters=300, flutter=0.25, seed=0):
    """Mass-spring cloth on a grid G (rows down, columns around, wrapped): row 0 is pinned (the
    waistband). Lengthwise links keep their length; hoop links may shorten (cloth bunches into folds)
    but not stretch. Gravity, wind drag with a slow gust pattern, collision with friction."""
    rng = np.random.default_rng(seed)
    P = G.astype(np.float32).copy()
    prev = P.copy()
    nr, nc = P.shape[:2]
    Lv = np.linalg.norm(P[1:] - P[:-1], axis=2)                       # (nr-1, nc)
    Lh = np.linalg.norm(P - np.roll(P, -1, axis=1), axis=2) * 1.05    # (nr, nc)
    g = V(0, -9.8, 0)
    w = np.asarray(wind, np.float32)
    wn = float(np.linalg.norm(w)) + 1e-6
    side = nrm(np.cross(w / wn, V(0, 1, 0))) if wn > 0.5 else V(1, 0, 0)
    ph = rng.uniform(0, 6.28, 2)
    ii, jj = np.meshgrid(np.arange(nr), np.arange(nc), indexing="ij")
    gust = w[None, None] * (1 + flutter * np.sin(ii * 0.5 + jj * 0.7 + ph[0]))[..., None] \
        + (wn * flutter * 0.3 * np.sin(jj * 0.9 + ph[1]))[..., None] * side[None, None]
    dt = 0.016
    cm = np.zeros((nr, nc), bool)                  # in contact last step, and the surface normal there
    cn = np.zeros((nr, nc, 3), np.float32)
    for it in range(iters):
        vel = (P - prev) * 0.94
        prev = P.copy()
        acc = g + drag * (gust - vel / dt) * 0.5
        P = P + vel + acc * dt * dt
        if cm.any():
            # static friction: cloth pressed onto the body by the wind does not slide off it (a skirt
            # in a gale wraps the windward leg); only the motion along the surface normal remains
            dlt = P - prev
            dn = (dlt * cn).sum(-1, keepdims=True)
            hold = cm[..., None] & (dn < 0.002)
            P = np.where(hold, prev + dn * cn, P)
        P[0] = G[0]
        for _ in range(3):
            dv = P[1:] - P[:-1]
            L = np.linalg.norm(dv, axis=2, keepdims=True) + 1e-9
            c = dv * (1 - Lv[..., None] / L) * 0.5
            P[1:] -= c; P[:-1] += c
            nb = np.roll(P, -1, axis=1)
            dh = nb - P
            L = np.linalg.norm(dh, axis=2, keepdims=True) + 1e-9
            c = dh * (np.maximum(1 - Lh[..., None] / L, 0)) * 0.5
            P += c
            P -= np.roll(c, 1, axis=1)
            P[0] = G[0]
            if collide is not None:
                flat = P.reshape(-1, 3)
                dd = collide(flat)
                bad = dd < r
                cmf = np.zeros(len(flat), bool)
                if bad.any():
                    e = 0.004
                    gr = np.stack([(collide(flat[bad] + V(*(e * np.eye(3)[k]))) - dd[bad]) / e for k in range(3)], 1)
                    nb_ = nrm(gr)
                    flat[bad] += nb_ * (r - dd[bad])[:, None]
                    pf = prev.reshape(-1, 3)
                    pf[bad] = flat[bad]
                    prev = pf.reshape(P.shape)
                    cmf[bad] = True
                    cnf = cn.reshape(-1, 3)
                    cnf[bad] = nb_
                    cn = cnf.reshape(cn.shape)
                cm = cmf.reshape(nr, nc) | (cm & (dd.reshape(nr, nc) < r * 1.6))
                P = flat.reshape(P.shape)
                P[0] = G[0]
    for _ in range(2):
        P[1:-1] = 0.25 * P[:-2] + 0.5 * P[1:-1] + 0.25 * P[2:]
        P[:, :] = 0.25 * np.roll(P, 1, 1) + 0.5 * P + 0.25 * np.roll(P, -1, 1)
        P[0] = G[0]
    return P


def dress_part(o, cl, body, J, wind, collide, color):
    """A skirt hanging from the waist as a ring of cloth ropes (so pipe folds form between them),
    pressed to the legs on the windward side and streaming on the leeward side."""
    u = body.u
    n_r = cl.get("panels", 16)
    length = cl.get("length", 0.9) * (J["hip_l"][1] - J["ft_l"][1] + J["hip_r"][1] - J["ft_r"][1]) / 2 + 0.25 * u
    length = cl.get("length_m", length)
    waist = J["waist"]
    Mw = J["Rpelvis"]
    rw = 0.62 * u * body.wf * body.bt * body.g(1.0, 1.05)
    flare = cl.get("flare", 0.45)
    nseg = 10
    G0 = np.zeros((nseg + 1, n_r, 3), np.float32)
    for i in range(n_r):
        a = 2 * math.pi * i / n_r
        rad = Mw @ V(math.sin(a) * rw, 0, math.cos(a) * rw * 0.8)
        d0 = nrm(V(0, -1, 0) + nrm(rad) * flare)
        for k in range(nseg + 1):
            G0[k, i] = waist + rad + d0 * length * k / nseg
    P = cloth_sim(G0, wind, collide, drag=cl.get("drag", 1.1), seed=3)
    ropes = np.transpose(P, (1, 0, 2))
    # pipe folds: every other rope stands out from the skirt's axis, more toward the hem
    axis = ropes.mean(0)                        # (nseg+1, 3) the skirt's centre line
    s_ = np.linspace(0, 1, nseg + 1)[None, :, None]
    radial = nrm(ropes - axis[None])
    amp = cl.get("folds", 0.035) * (0.3 + s_)
    sign = np.array([1 if i % 2 else -1 for i in range(n_r)], np.float32)[:, None, None]
    ropes = ropes + radial * amp * sign
    G = np.transpose(ropes, (1, 0, 2))           # rows down the skirt, columns around it
    return cloth_part([(G, True)], cl.get("thickness", 0.018), cl.get("color", color), "dress")


def ribbon_from_path(pts, width, thick, lateral, up=V(0, 1, 0)):
    A, B = pts[:-1], pts[1:]
    u = nrm(B - A)
    h = 1 - np.abs(u @ up)                       # 1 = horizontal segment
    ref = nrm(lateral[None] * (1 - h[:, None]) + up[None] * h[:, None])
    Wd = nrm(ref - (ref * u).sum(1, keepdims=True) * u)
    for i in range(1, len(Wd)):                 # keep the width direction continuous along the path
        if Wd[i] @ Wd[i - 1] < 0:
            Wd[i] = -Wd[i]
    n = len(A)
    hw = np.full(n, width / 2, np.float32) if np.isscalar(width) else np.asarray(width, np.float32)
    ht = np.full(n, thick / 2, np.float32)
    return A.astype(np.float32), B.astype(np.float32), Wd.astype(np.float32), hw, ht


def shawl_part(o, cl, body, J, wind, collide, color):
    """A shawl over the shoulders: a band around the back of the neck and the shoulders, its two
    ends hanging in front under gravity or streaming downwind (ropes)."""
    u = body.u
    Mc = J["Rchest"]
    C = J["chest"]
    W = lambda v: C + Mc @ (np.asarray(v, np.float32) * u)
    tf = body.tf
    yoke = [W([0.42, 0.75 * tf, 0.42]), W([0.62, 1.02 * tf, 0.05]), W([0.38, 1.18 * tf, -0.32]), W([0, 1.18 * tf, -0.42]),
            W([-0.38, 1.18 * tf, -0.32]), W([-0.62, 1.02 * tf, 0.05]), W([-0.42, 0.75 * tf, 0.42])]
    yoke = np.stack(yoke)
    L = cl.get("length", 0.75)
    w = np.asarray(wind, np.float32)
    # the ends hang from the front of the shoulders; in a wind from ahead they leave from the shoulder
    # tops and stream back past the body
    fwd = Mc @ V(0, 0, 1)
    headwind = float(-(w @ fwd)) > 2.0
    starts = (yoke[1], yoke[-2]) if headwind else (yoke[0], yoke[-1])
    ends = []
    for k, anc in enumerate(starts):
        Ln = L * (1.0 if k == 0 else cl.get("ratio", 0.85))
        init = nrm(w + V(0, -2, 0)) if headwind else None
        ends.append(rope(anc, 10, Ln / 10, wind, collide, drag=cl.get("drag", 2.2), seed=11 + k, r=0.05, flutter=0.5, init=init))
    lateral = Mc @ V(1, 0, 0)
    wdt, thk = cl.get("width", 0.32), cl.get("thickness", 0.01)

    def strip(path, widths):
        A_, B_, Wd, hw, _ = ribbon_from_path(path, widths, thk, lateral)
        W_ = np.concatenate([Wd, Wd[-1:]])
        h_ = np.concatenate([hw, hw[-1:]])[:, None]
        nn = nrm(np.cross(np.concatenate([B_ - A_, (B_ - A_)[-1:]]), W_))
        mid = path + nn * h_ * 0.15 * np.sin(np.arange(len(path))[:, None] * 0.45)   # a lengthwise fold
        G = np.stack([path - W_ * h_, mid - W_ * h_ * 0.2 + nn * h_ * 0.18, mid + W_ * h_ * 0.2 - nn * h_ * 0.1, path + W_ * h_], 1)
        return G
    grids = [(strip(yoke, np.full(len(yoke) - 1, 0.08)), False)]
    for e in ends:
        n = len(e) - 1
        grids.append((strip(e, np.linspace(0.08, wdt / 2, n)), False))
    return cloth_part(grids, thk, cl.get("color", "#a07030"), "shawl")


def trousers_part(o, cl, body, J, prims, color):
    """Trousers: hips and legs eased out, cut at the waist and at the ankles (or the knees)."""
    u = body.u
    legs, tor = prims["legs"], prims["torso"]
    la = [l.arrays() for l in legs]
    ta = tor.arrays()
    waist_o, waist_n = J["pelvis"] + J["Rpelvis"] @ V(0, 0.42 * u, 0), J["Rpelvis"] @ V(0, 1, 0)
    cuts = []
    for s in "lr":
        a, b = (J[f"kn_{s}"], J[f"an_{s}"]) if cl.get("length", "long") == "long" else (J[f"hip_{s}"], J[f"kn_{s}"])
        cuts.append((a + (b - a) * (0.97 if cl.get("length", "long") == "long" else 1.05), nrm(b - a)))
    ease = cl.get("ease", 0.018)

    def f(p):
        dt_ = np.maximum(smin_exp(tor.raw(p, ta), 0.1 * u), (p - waist_o) @ waist_n)
        d = dt_
        for i in range(2):
            dl = smin_exp(legs[i].raw(p, la[i]), 0.1 * u)
            c, n = cuts[i]
            dl = np.maximum(dl, (p - c) @ n)
            d = smin(d, dl, 0.06 * u)
        rip = 0.004 * np.sin(p[:, 1] * 60 + p[:, 0] * 20)
        return (d - ease - rip) * 0.85
    sph = tor.spheres() + legs[0].spheres() + legs[1].spheres()
    return part(f, cl.get("color", color), "drapery", sph, name="trousers", pad=0.06)


def shirt_part(o, cl, body, J, wind, prims, color):
    """A loose shirt: the torso and arms inflated, billowing on the leeward side, with a hem and
    sleeves cut where the shirt ends."""
    u = body.u
    tor, arms = prims["torso"], prims["arms"]
    ta, aa = tor.arrays(), [a.arrays() for a in arms]
    w = np.asarray(wind, np.float32)
    wn = float(np.linalg.norm(w))
    wd = w / (wn + 1e-6)
    axis_c = J["chest"]
    hem_o, hem_n = J["pelvis"] + J["Rpelvis"] @ V(0, (0.1 - 0.3 * cl.get("length", 0.5)) * u, 0), J["Rpelvis"] @ V(0, 1, 0)
    sleeve = cl.get("sleeves", "long")
    cuts = []
    for s in "lr":
        if sleeve == "long":
            a, b = J[f"el_{s}"], J[f"wr_{s}"]; t = 0.92
        elif sleeve == "short":
            a, b = J[f"sh_{s}"], J[f"el_{s}"]; t = 0.55
        else:
            a, b = J[f"sh_{s}"], J[f"el_{s}"]; t = 0.05
        cuts.append((a + (b - a) * t, nrm(b - a)))
    base = cl.get("ease", 0.02)
    bill = cl.get("billow", 0.06) * min(wn / 12, 1.5)

    def f(p):
        dt_ = smin_exp(tor.raw(p, ta), 0.04)
        dt_ = np.maximum(dt_, (p - hem_o) @ (-hem_n))
        d = dt_
        for i, s in enumerate("lr"):
            da = smin_exp(arms[i].raw(p, aa[i]), 0.03)
            c, n = cuts[i]
            da = np.maximum(da, (p - c) @ n)
            d = smin(d, da, 0.03)
        rel = p - axis_c
        lee = np.clip(rel @ wd / (0.25), -1, 1)
        infl = base + bill * np.clip(lee, 0, 1) - 0.6 * base * np.clip(-lee, 0, 1)
        rip = 0.008 * np.sin((rel @ np.cross(wd, V(0, 1, 0))) * 40 + rel[:, 1] * 8) * (bill > 0)
        return (d - infl - rip) * 0.85
    sph = tor.spheres() + arms[0].spheres() + arms[1].spheres()
    return part(f, cl.get("color", "#d8d4c8"), "drapery", sph, name="shirt", pad=0.12)


# ---------------------------------------------------------------- the person
def person(o):
    """Build a person from a scene object. See docs/MANUAL.md, "People"."""
    body = Body(o)
    u = body.u
    pose = {}
    base = o.get("pose", "stand")
    for nm in ([base] if isinstance(base, str) else base):
        pose.update(POSES.get(nm, {}))
    pose.update(o.get("joints", {}))
    for k in ("reach_l", "reach_r", "hand_l", "hand_r", "lean", "lie"):
        if k in o:
            pose[k] = o[k]
    # old age: a stoop and a forward head unless the pose says otherwise
    if body.old > 0 and "spine" not in o.get("joints", {}):
        sp = list(pose.get("spine", [0, 0, 0])) + [0, 0, 0]
        pose["spine"] = [sp[0] + 10 * body.old, sp[1], sp[2]]
        nk = list(pose.get("neck", [0, 0, 0])) + [0, 0, 0]
        pose["neck"] = [nk[0] - 6 * body.old, nk[1], nk[2]]
    G = lambda k, n=3: (list(pose.get(k, [])) + [0] * n)[:n]
    tf, lf, af, wf = body.tf, body.lf, body.af, body.wf
    bt, bl, bs = body.bt, body.bl, body.bs

    # ---------- root orientation
    lie = pose.get("lie")
    pitch, roll = LIE.get(lie, (0, 0)) if lie else (0, 0)
    pitch += o.get("pitch", 0); roll += o.get("roll", 0)
    Mroot = ry(R(o.get("facing", 0))) @ rx(R(pitch)) @ rz(R(roll))
    J = {}
    Rp = Mroot @ jrot(G("pelvis"))
    J["pelvis"] = V(0, 0, 0); J["Rpelvis"] = Rp
    sp = G("spine")
    half = [sp[0] / 2, sp[1] / 2, sp[2] / 2]
    J["lumbar"] = Rp @ V(0, 0.55 * tf * u, -0.03 * u)
    Rl = Rp @ jrot(half)
    J["chest"] = J["lumbar"] + Rl @ V(0, 0.65 * tf * u, 0)
    Rc = Rl @ jrot(half)
    J["Rlumbar"], J["Rchest"] = Rl, Rc
    J["waist"] = J["lumbar"] + Rl @ V(0, 0.15 * tf * u, 0)
    J["neckb"] = J["chest"] + Rc @ V(0, 1.08 * tf * u, -0.1 * u)
    Rn = Rc @ jrot(G("neck"))
    J["atlas"] = J["neckb"] + Rn @ V(0, 0.42 * u * min(1, 0.6 + 0.4 * tf), 0.07 * u)
    Rh = Rn @ jrot(G("head"))
    J["Rhead"] = Rh
    J["head"] = J["atlas"] + Rh @ V(0, 0.4 * u, 0.04 * u)
    shx = body.g(0.78, 0.68) * wf * bs
    for side, s in ((1, "l"), (-1, "r")):
        rs, fs = (G(f"shoulder_{s}", 2))
        J[f"sh_{s}"] = J["chest"] + Rc @ V(side * shx * u, (0.92 * tf + 0.06 * rs) * u, (-0.08 + 0.08 * fs) * u)
        hipx = body.g(0.4, 0.45) * wf * bt
        J[f"hip_{s}"] = Rp @ V(side * hipx * u, 0, 0)
    # ---------- legs
    for side, s in ((1, "l"), (-1, "r")):
        fwd, out, tw, knee = G(f"leg_{s}", 4)
        Rt = Rp @ rz(R(side * out)) @ rx(-R(fwd)) @ ry(R(side * tw))
        J[f"kn_{s}"] = J[f"hip_{s}"] + Rt @ V(0, -1.85 * lf * u, 0)
        Rs = Rt @ rx(R(knee))
        J[f"an_{s}"] = J[f"kn_{s}"] + Rs @ V(0, -1.62 * lf * u, 0)
        Rf = Rs @ rx(-R(G(f"ankle_{s}", 1)[0]))
        J[f"Rthigh_{s}"], J[f"Rshin_{s}"], J[f"Rfoot_{s}"] = Rt, Rs, Rf
        J[f"ft_{s}"] = J[f"an_{s}"] + Rf @ V(0, -0.28 * u * lf, 0.85 * u * lf ** 0.5)
        J[f"heel_{s}"] = J[f"an_{s}"] + Rf @ V(0, -0.27 * u * lf, -0.2 * u)

    # ---------- arms: forward kinematics, or IK to a target
    def landmark(name):
        hc, Rh_ = J["head"], J["Rhead"]
        table = {"head_top": hc + Rh_ @ V(0, 0.5 * u, -0.05 * u), "head_back": hc + Rh_ @ V(0, 0.15 * u, -0.5 * u),
                 "forehead": hc + Rh_ @ V(0, 0.25 * u, 0.38 * u), "chest": J["chest"] + Rc @ V(0, 0.6 * u, 0.5 * u),
                 "nape": hc + Rh_ @ V(0, -0.3 * u, -0.4 * u), "belly": J["lumbar"] + Rl @ V(0, 0.2 * u, 0.5 * u),
                 "hip_l": J["hip_l"] + Rp @ V(0.4 * u, 0, 0), "hip_r": J["hip_r"] + Rp @ V(-0.4 * u, 0, 0),
                 "knee_l": J["kn_l"], "knee_r": J["kn_r"], "cheek_l": hc + Rh_ @ V(0.3 * u, -0.15 * u, 0.15 * u),
                 "cheek_r": hc + Rh_ @ V(-0.3 * u, -0.15 * u, 0.15 * u)}
        return table[name]

    J["landmark"] = landmark
    hands = {}
    L1, L2 = 1.45 * af * u, 1.15 * af * u
    hand_len = 0.74 * u * (0.85 + 0.15 * af)
    world_pos = np.asarray(o.get("pos", [0, 0, 0]), np.float32)
    for side, s in ((1, "l"), (-1, "r")):
        reach = pose.get(f"reach_{s}")
        sh = J[f"sh_{s}"]
        if reach:
            tgt = reach.get("target", [0, 0, 0])
            if isinstance(tgt, str):
                T = "landmark"
            else:   # world coordinates
                T = None
                J[f"_world_target_{s}"] = np.asarray(tgt, np.float32)
            off = np.asarray(reach.get("offset", [0, 0, 0]), np.float32)
            J[f"reach_{s}"] = (T, off, reach)
            continue
        fwd, out, tw, elb = G(f"arm_{s}", 4)
        Ru = Rc @ rz(R(side * out)) @ rx(-R(fwd)) @ ry(R(side * tw))
        J[f"el_{s}"] = sh + Ru @ V(0, -L1, 0)
        Rf = Ru @ rx(-R(elb))
        J[f"wr_{s}"] = J[f"el_{s}"] + Rf @ V(0, -L2, 0)
        fl, dev, pron = G(f"wrist_{s}", 3)
        hp = pose.get(f"hand_{s}", "relaxed")
        hpd = HANDS.get(hp, {}) if isinstance(hp, str) else hp
        wf_, wd_ = (hpd.get("wrist", [0, 0]) + [0, 0])[:2]
        Mh = Rf @ ry(-R(side * (pron if f"wrist_{s}" in pose else 80))) @ rx(-R(fl + wf_)) @ rz(R(side * (dev + wd_)))
        J[f"Rhand_{s}"] = Mh
    # ---------- place in the world: lean about the feet, then anchor
    lean = pose.get("lean", [0, 0])
    if isinstance(lean, (int, float)):
        lean = [lean, 0]
    feet_mid = (J["an_l"] + J["an_r"]) / 2
    Mlean = ry(R(o.get("facing", 0))) @ rx(R(lean[0])) @ rz(-R(lean[1])) @ ry(-R(o.get("facing", 0)))
    keys = [k for k, v in J.items() if isinstance(v, np.ndarray) and v.shape == (3,)]
    rots = [k for k, v in J.items() if isinstance(v, np.ndarray) and v.shape == (3, 3)]
    for k in keys:
        J[k] = feet_mid + Mlean @ (J[k] - feet_mid)
    for k in rots:
        J[k] = Mlean @ J[k]
    Rc, Rl, Rp = J["Rchest"], J["Rlumbar"], J["Rpelvis"]
    anchor = o.get("anchor", "ground")
    if anchor == "ground":
        gy = o.get("_ground_y", 0.0)
        cand = [J[k][1] - r for k, r in (("an_l", 0.13 * u), ("an_r", 0.13 * u), ("kn_l", 0.24 * u), ("kn_r", 0.24 * u),
                                          ("ft_l", 0.1 * u), ("ft_r", 0.1 * u), ("heel_l", 0.15 * u), ("heel_r", 0.15 * u),
                                          ("pelvis", 0.55 * u), ("chest", 0.5 * u), ("head", 0.45 * u), ("hip_l", 0.4 * u),
                                          ("hip_r", 0.4 * u), ("sh_l", 0.28 * u), ("sh_r", 0.28 * u))]
        for s in "lr":
            if f"el_{s}" in J:
                cand += [J[f"el_{s}"][1] - 0.15 * u, J[f"wr_{s}"][1] - 0.12 * u]
        if lie:
            cand += [J["lumbar"][1] - 0.55 * u, J["head"][1] - 0.5 * u]
        shift = world_pos.copy()
        shift[1] = gy - min(cand) + (world_pos[1] if o.get("float") else 0)
    else:
        ref = J["pelvis"] if anchor == "pelvis" else J["head"] if anchor == "head" else J["chest"]
        shift = world_pos - ref
    for k in keys:
        J[k] = J[k] + shift
    J["landmark"] = landmark   # reads the placed joints from here on
    # ---------- IK arms now that the body is placed
    for side, s in ((1, "l"), (-1, "r")):
        if f"reach_{s}" not in J:
            continue
        T, off, reach = J[f"reach_{s}"]
        if T is None:
            T = J[f"_world_target_{s}"]
        else:
            T = J["landmark"](reach["target"])
        T = T + off
        sh = J[f"sh_{s}"]
        palm = nrm(reach.get("palm", [0, -1, 0]))
        fingers = reach.get("fingers")
        # the target is where the palm centre should be: back off to the wrist
        fdir = nrm(fingers) if fingers is not None else nrm(T - sh)
        fdir = nrm(fdir - (fdir @ palm) * palm)
        wr = T - fdir * hand_len * 0.42 - palm * 0.05 * hand_len
        dvec = wr - sh
        dist = float(np.linalg.norm(dvec))
        dist_c = min(dist, (L1 + L2) * 0.999)
        dn = dvec / (dist + 1e-9)
        wr = sh + dn * dist_c
        pole = np.asarray(reach.get("pole", list(Rc @ V(side * 0.6, -0.6, -0.5))), np.float32)
        pole = nrm(pole - (pole @ dn) * dn)
        a = (L1 ** 2 + dist_c ** 2 - L2 ** 2) / (2 * L1 * dist_c)
        a = math.acos(float(np.clip(a, -1, 1)))
        el = sh + (dn * math.cos(a) + pole * math.sin(a)) * L1
        J[f"el_{s}"], J[f"wr_{s}"] = el, wr
        Y = -fdir
        Z = palm
        X = np.cross(Y, Z)
        J[f"Rhand_{s}"] = np.stack([X, Y, Z], 1).astype(np.float32)
        if "hand" in reach and f"hand_{s}" not in o:
            pose[f"hand_{s}"] = reach["hand"]
    J["_wrist_len"] = hand_len

    # ---------- surfaces
    wind = np.asarray(o.get("wind", o.get("_wind", [0, 0, 0])), np.float32)
    skin = o.get("skin", "#c49a7e")
    cloth = o.get("color", "#3a3a44")
    bare = set(o.get("bare", ["head", "hands"]))
    bare |= {"head", "hands"}
    for c_ in (o.get("clothes", []) if isinstance(o.get("clothes", []), list) else [o["clothes"]]):
        if c_.get("kind") == "shirt" and c_.get("sleeves", "long") in ("short", "none"):
            bare.add("arms")
    gloss_skin = o.get("skin_gloss", 0.0)
    parts = []
    hip_r = body.g(0.62, 0.68) * wf * bt

    torso = Prims()
    torso.ell(J["pelvis"] + Rp @ V(0, 0.12 * u, -0.02 * u), Rp, V(hip_r, 0.42 * tf, 0.42 * bt) * u)
    for side in (1, -1):
        torso.ell(J["pelvis"] + Rp @ V(side * 0.24 * u, -0.08 * u, -0.2 * u), Rp, V(0.28 * bt, body.g(0.32, 0.35), body.g(0.25, 0.28) * bt) * u)
    torso.ell(J["lumbar"] + Rl @ V(0, 0.25 * tf * u, (0.02 + 0.12 * body.belly) * u), Rl,
              V(body.g(0.52, 0.46) * bt * wf, 0.75 * tf, (0.36 + 0.18 * body.belly) * bt) * u)
    torso.ell(J["chest"] + Rc @ V(0, 0.48 * tf * u, 0.02 * u), Rc, V(body.g(0.6, 0.54) * bt * wf * bs ** 0.5, 0.7 * tf, body.g(0.44, 0.41) * bt) * u)
    for side in (1, -1):
        if body.fem and body.child < 0.5:
            sag = 0.1 * body.old
            torso.ell(J["chest"] + Rc @ V(side * 0.25 * u, (0.6 - sag) * tf * u, 0.27 * u), Rc @ rx(R(15)), V(0.18, 0.17, 0.14) * u * bt)
        else:
            torso.ell(J["chest"] + Rc @ V(side * 0.28 * u, 0.78 * tf * u, 0.24 * u), Rc, V(0.28 * bs, 0.18, 0.12) * u * bt)
        torso.cone(J["neckb"], J[f"sh_{'l' if side == 1 else 'r'}"] + Rc @ V(0, 0.05 * u, 0), 0.3 * u * wf, 0.22 * u * wf * bs)
    tprims = torso
    neck = Prims()
    nr = body.g(0.27, 0.22) * (1 - 0.15 * body.old) * wf ** 0.5
    neck.cone(J["neckb"] - Rc @ V(0, 0.08 * u, 0), J["atlas"], nr * u * 1.1, nr * u * 0.88)
    # ---------- what the hands can touch: other objects in the scene, the person's own head and body
    ext = o.get("_collide")
    head = head_part(o, body, J["head"], J["Rhead"], skin, lip_col=o.get("lips"), gloss=o.get("face_gloss", gloss_skin),
                     gaze=o.get("gaze", [0, 0]))
    hfn, tfn0 = head["f"], tprims.fn(0.05 * u)
    hc_, hr_ = J["head"], 0.75 * u

    def touch(p, legs=None):
        p = np.asarray(p, np.float32)
        d = tfn0(p)
        near = np.linalg.norm(p - hc_, axis=1) < hr_
        if near.any():
            d[near] = np.minimum(d[near], hfn(p[near]))
        for g in (legs or []):
            d = np.minimum(d, g(p))
        if ext is not None:
            d = np.minimum(d, ext(p))
        return d
    m = body.fem * 0.4 + body.child * 0.6               # how much the muscle masses show (less in women and children; judgement)
    mus = (1 - m) * (1.0 + 0.5 * (o.get("build") == "muscular")) * (1 - 0.4 * body.old)
    leg_prims, foot_prims = [], []
    for side, s in ((1, "l"), (-1, "r")):
        Lg = Prims()
        g_ = bl * body.g(1.0, 1.04)
        hp, kn, an = J[f"hip_{s}"], J[f"kn_{s}"], J[f"an_{s}"]
        Rt_, Rs_ = J[f"Rthigh_{s}"], J[f"Rshin_{s}"]
        fwd_t, med_t = Rt_ @ V(0, 0, 1), Rt_ @ V(-side, 0, 0)
        fwd_s, med_s = Rs_ @ V(0, 0, 1), Rs_ @ V(-side, 0, 0)
        Lt = float(np.linalg.norm(kn - hp))
        Lg.cone(hp + Rp @ V(-side * 0.02 * u, 0.02 * u, 0), kn, 0.35 * u * g_ * bt ** 0.5, 0.2 * u * g_)
        # thigh: the quadriceps in front, the hamstrings behind, the teardrop of vastus medialis above the knee
        Lg.ell(hp + (kn - hp) * 0.42 + fwd_t * 0.05 * u, Rt_, V(0.31, 0.38 * Lt / u, 0.29) * u * g_)
        Lg.ell(hp + (kn - hp) * 0.5 - fwd_t * 0.07 * u, Rt_, V(0.27, 0.32 * Lt / u, 0.22) * u * g_)
        Lg.ell(hp + (kn - hp) * 0.82 + med_t * 0.075 * u + fwd_t * 0.04 * u, Rt_, V(0.11, 0.17, 0.11) * u * g_ * (0.8 + 0.3 * mus))
        # the knee: a block wider than deep, the flat patella in front, the tendon down to the shin (not a ball)
        Lg.ell(kn + Rs_ @ V(0, 0.01 * u, -0.01 * u), Rs_, V(0.175, 0.13, 0.15) * u * g_)
        pat = kn + (Rt_ @ V(0, 0.03 * u, 0) + fwd_t * 0.13 * u) * g_
        Lg.ell(pat, Rt_, V(0.085, 0.1, 0.04) * u * g_)
        Lg.cone(pat - Rt_ @ V(0, 0.07 * u, 0), kn + Rs_ @ V(0, -0.2 * u, 0) + fwd_s * 0.11 * u * g_, 0.035 * u * g_, 0.04 * u * g_)
        Lg.ell(kn + med_s * 0.085 * u - Rs_ @ V(0, 0.02 * u, 0), Rs_, V(0.07, 0.09, 0.08) * u * g_)
        # shin: the calf's two heads behind (the inner one lower and fuller), the soleus under them, the ankle bones
        Lg.cone(kn, an, 0.16 * u * g_, 0.1 * u * g_)
        Ls = float(np.linalg.norm(an - kn))
        Lg.ell(kn + (an - kn) * 0.33 - fwd_s * 0.08 * u + med_s * 0.045 * u, Rs_, V(0.12, 0.25 * Ls / u, 0.13) * u * g_ * (0.9 + 0.25 * mus))
        Lg.ell(kn + (an - kn) * 0.27 - fwd_s * 0.075 * u - med_s * 0.05 * u, Rs_, V(0.1, 0.2 * Ls / u, 0.1) * u * g_ * (0.85 + 0.25 * mus))
        Lg.ell(kn + (an - kn) * 0.55 - fwd_s * 0.05 * u, Rs_, V(0.14, 0.24 * Ls / u, 0.11) * u * g_)
        Lg.ell(an + med_s * 0.07 * u + Rs_ @ V(0, 0.02 * u, 0), Rs_, V(0.045, 0.05, 0.045) * u * g_)
        Lg.ell(an - med_s * 0.075 * u - Rs_ @ V(0, 0.03 * u, 0), Rs_, V(0.04, 0.05, 0.04) * u * g_)
        leg_prims.append(Lg)
        Ft = Prims()
        Rf = J[f"Rfoot_{s}"]
        Ft.ell(an + Rf @ V(0, -0.16 * u, 0.32 * u * lf ** 0.5), Rf, V(0.17, 0.12, 0.52 * lf ** 0.5) * u)
        Ft.ell(J[f"heel_{s}"] + Rf @ V(0, 0.08 * u, 0.05 * u), Rf, V(0.13, 0.15, 0.17) * u)
        foot_prims.append(Ft)
    lfn0 = [P.fn(0.05 * u) for P in leg_prims]
    # a hand that touches something rests on it: a reaching hand with a resting grip settles onto the
    # surface under its palm (within 6 cm), and a palm inside a surface is pushed out (the wrist moves with it)
    for side, s in ((1, "l"), (-1, "r")):
        Mh = J[f"Rhand_{s}"]
        pc = J[f"wr_{s}"] + Mh @ (V(0, -0.3, 0.075) * hand_len)
        hp_ = pose.get(f"hand_{s}", (pose.get(f"reach_{s}") or {}).get("hand", "relaxed"))
        if f"reach_{s}" in pose and hp_ in ("rest", "hold", "cup", "grip") and pose[f"reach_{s}"].get("settle", True):
            pn = nrm(Mh @ V(0, 0, 1))
            for t_ in np.linspace(0, 0.06, 25):
                if float(touch((pc + pn * t_)[None], lfn0)[0]) < 0.004 * hand_len:
                    J[f"wr_{s}"] = J[f"wr_{s}"] + pn * t_
                    pc = pc + pn * t_
                    break
        for _ in range(3):
            d0 = float(touch(pc[None], lfn0)[0])
            if d0 >= 0.004 * hand_len:
                break
            e = 0.003
            gr = nrm(np.array([float(touch((pc + V(*(e * np.eye(3)[k])))[None], lfn0)[0]) - d0 for k in range(3)], np.float32))
            sh_ = gr * (0.004 * hand_len - d0)
            J[f"wr_{s}"] = J[f"wr_{s}"] + sh_
            pc = pc + sh_
    arm_prims = []
    for side, s in ((1, "l"), (-1, "r")):
        A_ = Prims()
        sh, el, wr = J[f"sh_{s}"], J[f"el_{s}"], J[f"wr_{s}"]
        g_ = bl * (1 - 0.15 * body.fem)
        du, df = nrm(el - sh), nrm(wr - el)
        L1_, L2_ = float(np.linalg.norm(el - sh)), float(np.linalg.norm(wr - el))
        bfront = Rc @ V(0, 0, 1)
        fr = df - (df @ du) * du                            # the side the elbow bends toward is the front of the arm
        fr = nrm(fr) if np.linalg.norm(fr) > 0.15 else nrm(bfront - (bfront @ du) * du + 1e-6)
        lat = nrm(np.cross(du, fr)) * side
        if float(lat @ (Rc @ V(side, 0, 0))) < 0:
            lat = -lat
        A_.ell(sh + du * 0.2 * u + lat * 0.04 * u, frame_along(du), V(0.22, 0.29, 0.23) * u * g_ * (0.9 + 0.15 * mus))   # deltoid
        A_.cone(sh, el, 0.19 * u * g_, 0.13 * u * g_)
        A_.ell(sh + du * 0.55 * L1_ + fr * 0.045 * u, frame_along(du), V(0.13, 0.3 * L1_ / u, 0.12) * u * g_ * (0.85 + 0.25 * mus))   # biceps
        A_.ell(sh + du * 0.45 * L1_ - fr * 0.05 * u, frame_along(du), V(0.14, 0.34 * L1_ / u, 0.13) * u * g_)   # triceps
        # the elbow: the olecranon's point behind, the inner epicondyle's knob
        A_.ell(el - fr * 0.06 * u, frame_along(du), V(0.06, 0.07, 0.06) * u * g_)
        A_.ell(el - lat * 0.075 * u, frame_along(du), V(0.05, 0.05, 0.05) * u * g_)
        A_.cone(el, wr, 0.13 * u * g_, 0.085 * u * g_)
        Mh = J[f"Rhand_{s}"]
        rad = nrm(Mh @ V(side, 0, 0))                       # the thumb side of the forearm
        palm_ = nrm(Mh @ V(0, 0, 1))
        A_.ell(el + (wr - el) * 0.28 + rad * 0.045 * u - fr * 0.01 * u, frame_along(df), V(0.12, 0.34 * L2_ / u, 0.11) * u * g_)   # extensors and brachioradialis
        A_.ell(el + (wr - el) * 0.3 - rad * 0.035 * u + palm_ * 0.025 * u, frame_along(df), V(0.12, 0.3 * L2_ / u, 0.11) * u * g_)  # flexors
        A_.ell(wr - df * 0.03 * u, np.stack([rad, -df, nrm(np.cross(rad, -df))], 1), V(0.11, 0.07, 0.065) * u * g_)       # the flat wrist
        arm_prims.append(A_)
    hand_prims_ = []
    for side, s in ((1, "l"), (-1, "r")):
        hp = pose.get(f"hand_{s}", "relaxed")
        wants = (f"reach_{s}" in pose) or ext is not None
        hand_prims_.append(hand_prims(J[f"Rhand_{s}"], J[f"wr_{s}"], hand_len, side, hp, girth=bl ** 0.5,
                                      collide=(lambda p: touch(p, lfn0)) if wants else None))

    def col(part_name):
        return skin if part_name in bare else cloth
    if any(c.get("kind") == "dress" for c in (o.get("clothes", []) if isinstance(o.get("clothes", []), list) else [o["clothes"]])):
        cloth = next(c.get("color", cloth) for c in o["clothes"] if c.get("kind") == "dress")
    clothes = o.get("clothes", [])
    if isinstance(clothes, dict):
        clothes = [clothes]
    torso_col = cloth
    for cl in clothes:
        if cl.get("kind") in ("dress",) and "color" in cl:
            torso_col = cl["color"]
    names = ["torso", "neck", "arms", "legs", "feet", "hands"]
    groups = [("torso", skin if "torso" in bare else torso_col, gloss_skin if "torso" in bare else 0, tprims.fn(0.13 * u), tprims.spheres(), None),
              ("neck", skin, gloss_skin, neck.fn(0.0), neck.spheres(), 0.1 * u)]
    for P in arm_prims:
        groups.append(("arms", skin if "arms" in bare else torso_col, gloss_skin if "arms" in bare else 0, P.fn(0.05 * u), P.spheres(), 0.1 * u))
    for P in leg_prims:
        groups.append(("legs", col("legs"), 0, P.fn(0.08 * u), P.spheres(), 0.14 * u))
    for P in foot_prims:
        groups.append(("feet", skin if "feet" in bare else o.get("shoes", "#1e1a18"), 0, P.fn(0.06 * u), P.spheres(), 0.05 * u))
    nail = hx(skin) * V(1.08, 0.95, 0.95) + 0.06
    for P in hand_prims_:
        groups.append(("hands", skin, gloss_skin, P.fn(0.012 * hand_len), P.spheres(), 0.03 * u))
        groups.append(("hands", np.clip(nail, 0, 1), 0.25, P.nails.fn(0.0), P.nails.spheres(), 0.002 * u))
    bp = body_part(groups, 0.1 * u, names)
    # the body's light grouped into planes like the head's (default a little less), so the muscle
    # masses read as plane changes; 0 is the smooth form
    bp.update(planes=float(o.get("body_planes", 0.35)), scale=u)
    parts.append(bp)
    parts.append(head)
    # cloth collides with the body: torso, legs and arms
    tfn = tprims.fn(0.05 * u)
    lfn = [P.fn(0.05 * u) for P in leg_prims]
    afn = [P.fn(0.04 * u) for P in arm_prims]

    def collide(p):
        d = tfn(p)
        for g in lfn + afn:
            d = np.minimum(d, g(p))
        return d
    hp_ = J["head"]
    parts += hair_part(o, body, J["head"], J["Rhead"], wind, lambda p: np.minimum(collide(p), np.linalg.norm(p - hp_, axis=1) - 0.5 * u),
                       skull=head.get("skull"))
    for cl in clothes:
        k = cl.get("kind")
        if k == "dress":
            parts.append(dress_part(o, cl, body, J, wind, collide, torso_col))
        elif k == "shawl":
            parts.append(shawl_part(o, cl, body, J, wind, collide, cloth))
        elif k == "trousers":
            parts.append(trousers_part(o, cl, body, J, {"legs": leg_prims, "torso": tprims}, cloth))
        elif k == "shirt":
            parts.append(shirt_part(o, cl, body, J, wind, {"torso": tprims, "arms": arm_prims}, cloth))
    return parts, J


def frame_along(d):
    """A rotation whose local y runs along d."""
    y = nrm(d)
    x = nrm(np.cross(y, V(0, 0, 1))) if abs(y[2]) < 0.9 else nrm(np.cross(y, V(1, 0, 0)))
    z = np.cross(x, y)
    return np.stack([x, y, z], 1).astype(np.float32)


# ---------------------------------------------------------------- companions and settings
def animal(o):
    """A simple animal: a cat curled asleep ("curled"), sitting ("sit") or lying stretched ("lie")."""
    pos = np.asarray(o.get("pos", [0, 0, 0]), np.float32)
    s = o.get("size", 1.0)
    M = ry(R(o.get("facing", 0)))
    pose = o.get("pose", "curled")
    P, T = Prims(), Prims()
    W = lambda v: pos + M @ (np.asarray(v, np.float32) * s)
    if pose == "curled":
        Rc = 0.11
        n = 9
        ang = np.linspace(R(-150), R(140), n)
        pts = [W([Rc * math.cos(a), 0.075 + 0.01 * math.sin(a * 2), Rc * math.sin(a)]) for a in ang]
        rad = [0.06, 0.075, 0.085, 0.09, 0.092, 0.09, 0.085, 0.075, 0.065]
        for i in range(n - 1):
            P.cone(pts[i], pts[i + 1], rad[i] * s, rad[i + 1] * s)
        hc = W([Rc * math.cos(R(150)) + 0.02, 0.085, Rc * math.sin(R(150)) - 0.05])
        P.ell(hc, M @ ry(R(-30)), V(0.06, 0.05, 0.055) * s)
        P.ell(hc + M @ V(0.03, -0.01, -0.045) * s, M @ ry(R(-30)), V(0.03, 0.025, 0.03) * s)
        for e in (-1, 1):
            b = hc + M @ V(0.03 * e - 0.01, 0.04, 0.02 * e) * s
            P.cone(b, b + M @ V(0.005 * e, 0.04, 0.0) * s, 0.02 * s, 0.003 * s)
        ta = np.linspace(R(-150), R(-330), 8)
        tp = [W([(Rc + 0.07) * math.cos(a), 0.03, (Rc + 0.07) * math.sin(a)]) for a in ta]
        for i in range(7):
            T.cone(tp[i], tp[i + 1], 0.024 * s, 0.02 * s)
    elif pose == "sit":
        P.ell(W([0, 0.12, 0]), M @ rx(R(-20)), V(0.09, 0.13, 0.11) * s)
        P.ell(W([0, 0.28, 0.05]), M, V(0.065, 0.055, 0.06) * s)
        for e in (-1, 1):
            P.cone(W([0.03 * e, 0.32, 0.05]), W([0.035 * e, 0.37, 0.05]), 0.02 * s, 0.003 * s)
            P.cone(W([0.04 * e, 0.15, 0.08]), W([0.04 * e, 0.0, 0.09]), 0.02 * s, 0.018 * s)
        T.cone(W([0, 0.02, -0.1]), W([0.15, 0.02, 0.05]), 0.022 * s, 0.018 * s)
    else:
        P.ell(W([0, 0.09, 0]), M, V(0.09, 0.08, 0.22) * s)
        P.ell(W([0, 0.12, 0.25]), M, V(0.06, 0.055, 0.06) * s)
        T.cone(W([0, 0.06, -0.2]), W([0.1, 0.03, -0.45]), 0.022 * s, 0.018 * s)
    fa, ta_ = P.fn(0.03 * s), T.fn(0.0) if not T.empty() else None

    def f(p):
        d = fa(p)
        if ta_:
            d = smin(d, ta_(p), 0.02 * s)
        return d * 0.95
    return [part(f, o.get("color", "#6a5a4a"), "animal", P.spheres() + T.spheres())]


def water(o):
    """A water surface at height y with a light chop and rings of ripples around given points."""
    y0 = o.get("y", 0.0)
    amp = o.get("chop", 0.015)
    rings = [np.asarray(r, np.float32) for r in o.get("ripples", [])]

    def f(p):
        x, z = p[:, 0], p[:, 2]
        h = amp * (np.sin(x * 3.1 + z * 1.7) * 0.6 + np.sin(x * 7.3 - z * 5.1) * 0.3 + np.sin(z * 11.0 + x * 2.0) * 0.15)
        for c in rings:
            r = np.hypot(x - c[0], z - c[1])
            h += o.get("ripple_amp", 0.02) * np.sin(r * 22 - 1.0) * np.exp(-r / 0.6) * np.clip(r / 0.25, 0, 1)
        return (p[:, 1] - y0 - h) * 0.7
    c = np.asarray(o.get("center", [0, y0, 0]), np.float32)
    return [dict(f=f, color=hx(o.get("color", "#2a4a50")), element="water", bound=(c, o.get("extent", 400.0)), gloss=o.get("gloss", 0.8),
                 plane=True)]
