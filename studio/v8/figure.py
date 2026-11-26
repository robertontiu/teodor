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


def hand_prims(M, O, L, side, preset, extra=None, girth=1.0):
    """Hand geometry: M local->world rotation (fingers along local -y, palm +z, thumb +x*side),
    O the wrist, L the hand length. Returns Prims."""
    h = dict(HANDS.get(preset, HANDS["relaxed"])) if isinstance(preset, str) else dict(HANDS["relaxed"], **preset)
    if extra:
        h.update(extra)
    P = Prims()
    g = girth

    def W(v):
        v = np.asarray(v, np.float32) * L
        v[0] *= side
        return O + M @ v

    def Wd(v):
        v = np.asarray(v, np.float32).copy(); v[0] *= side
        return M @ v
    # palm: a flat, slightly cupped slab with the thenar and hypothenar pads
    Mp = M @ np.diag([side, 1, 1]).astype(np.float32)
    P.ell(W([0.0, -0.29, -0.01]), Mp, np.array([0.215, 0.24, 0.062 * g], np.float32) * L)
    P.ell(W([0.0, -0.46, -0.0]), Mp, np.array([0.2, 0.07, 0.058 * g], np.float32) * L)          # knuckle row
    P.ell(W([0.115, -0.21, 0.03]), Mp @ rz(R(-28)), np.array([0.095, 0.17, 0.075 * g], np.float32) * L)   # thenar
    P.ell(W([-0.13, -0.3, 0.02]), Mp, np.array([0.07, 0.17, 0.06 * g], np.float32) * L)               # hypothenar
    P.cone(W([0, -0.0, 0]), W([0, -0.12, 0]), 0.15 * L, 0.18 * L)  # wrist into palm
    flex = h["f"]
    sp = h.get("spread", 6)
    for i, (x, y, ln, rb, rt, sw) in enumerate(FING):
        mcp, pip, dip = flex[i]
        base = W([x, y, 0.0])
        P.cone(W([x * 0.55, -0.12, 0]), base, 0.055 * L * g, rb * L * g)  # metacarpal
        Rf = M @ np.diag([side, 1, 1]).astype(np.float32) @ rz(R(sp * sw)) @ rx(-R(mcp))
        p0 = base
        rads = np.linspace(rb, rt, 4) * L * g
        for j, ang in enumerate((0, pip, dip)):
            if j:
                Rf = Rf @ rx(-R(ang))
            p1 = p0 + Rf @ V(0, -ln * PHAL[j] * L, 0)
            P.cone(p0, p1, rads[j], rads[j + 1])
            p0 = p1
    t_out, t_palm, t_opp, t_mcp, t_ip = h["thumb"]
    base = W([0.1, -0.1, 0.02])
    # the thumb's pad faces across the palm, so it flexes toward the little finger, not the palm
    Rt = M @ np.diag([side, 1, 1]).astype(np.float32) @ rz(R(t_out)) @ rx(-R(t_palm * 0.7)) @ ry(-R(t_opp + 45))
    p0 = base
    for j, (ln, ang, r1, r2) in enumerate(((0.25, 0, 0.07, 0.062), (0.17, t_mcp, 0.062, 0.055), (0.145, t_ip, 0.055, 0.045))):
        if j:
            Rt = Rt @ rx(-R(ang))
        p1 = p0 + Rt @ V(0, -ln * L, 0)
        P.cone(p0, p1, r1 * L * g, r2 * L * g)
        p0 = p1
    return P


# ---------------------------------------------------------------- the head
# Action units (FACS; Ekman & Friesen) and expression presets. Values 0..1.
EXPRESSIONS = {
    "neutral": {},
    "calm": {"25": 0.05},
    "smile": {"6": 0.7, "12": 0.75},
    "laugh": {"6": 1.0, "12": 1.0, "25": 1.0, "26": 0.75, "10": 0.45, "7": 0.35},
    "gasp": {"1": 0.7, "2": 0.6, "5": 0.6, "25": 1.0, "26": 0.55, "27": 0.15},
    "surprise": {"1": 1.0, "2": 1.0, "5": 0.8, "25": 1.0, "26": 0.9},
    "fear": {"1": 1.0, "2": 0.7, "4": 0.7, "5": 1.0, "7": 0.25, "20": 1.0, "25": 1.0, "26": 0.45},
    "scream": {"1": 0.8, "2": 0.5, "4": 0.9, "5": 0.8, "7": 0.5, "20": 1.0, "25": 1.0, "26": 0.9, "27": 0.8, "10": 0.3},
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


def head_part(o, body, O, M, skin, eye_col="#e8e0d6", iris_col="#3a2a22", lip_col=None, gloss=0.0, gaze=(0, 0)):
    """A head built from the masses a painter uses (cranium ball, face front, brow ridge, cheekbones,
    nose wedge, muzzle barrel, jaw, cheek pads, lids), deformed by action units. O = head centre
    (mid height, at the ear), M = head local->world, H = head height."""
    H = body.u
    au = au_of(o.get("expression", "neutral"))
    A = lambda k: float(au.get(k, 0.0))
    fem, old, child = body.fem, body.old, body.child
    sx = body.g(1.0, 0.94)
    # ---------- action units -> parameters (normalized head units)
    jaw = R(3 + 20 * A("26") + 12 * A("27") + 2 * A("25"))
    cx = 0.105 + 0.045 * A("12") + 0.04 * A("20") - 0.02 * A("23") - 0.025 * max(A("26") - A("12") - A("20"), 0) - 0.006 * A("15")
    cy = -0.312 + 0.045 * A("12") - 0.03 * A("15") - 0.012 * A("20") + 0.01 * A("10") - 0.006 * A("17")
    up_mid = -0.298 + 0.03 * A("10") + 0.006 * A("25") + 0.005 * A("12") - 0.008 * A("17") * (1 - A("25"))
    opening = 0.0045 * A("25") + 0.30 * math.sin(jaw - R(3)) + 0.01 * A("20") * A("25")
    lo_mid = up_mid - opening - 0.004
    # outline exponents (superellipse): 2 = oval (surprise), high = square (fear's stretched mouth),
    # low upper with a deep lower = the laugh's upturned crescent
    pu = 2.0 + 3.0 * A("20") - 0.8 * A("12")
    pl = 2.0 + 2.0 * A("20") + 0.4 * A("12")
    lid_u = 0.04 + 0.022 * A("5") - 0.012 * A("7") - 0.03 * A("6") * 0.4 - 0.02 * A("41") - 0.045 * max(A("43"), A("45"))
    lid_l = -0.036 + 0.03 * A("6") + 0.012 * A("7") + 0.008 * A("43") - 0.006 * A("5")
    lid_u = max(lid_u, lid_l + 0.002)
    if A("43") > 0.6:
        lid_u = lid_l + 0.001
    brow_in = 0.035 * A("1") - 0.026 * A("4")
    brow_out = 0.032 * A("2") - 0.012 * A("4") - 0.01 * old
    knit = 0.016 * A("4")
    cheek_up = 0.045 * A("6") + 0.02 * A("12") + 0.012 * A("10")
    chin_up = 0.02 * A("17")
    sneer = A("9")

    M = np.asarray(M, np.float32)
    Mt = M.T
    pivot = V(0, -0.12, -0.035)
    Rj = rx(jaw)                      # jaw opens by rotating down about the jaw hinge
    Rjt = Rj.T
    lips = hx(lip_col) if lip_col else hx(skin) * V(1.02, 0.78, 0.78)
    sk = hx(skin)
    teeth, mouthc = hx("#d8d0c0"), hx("#3a1612")

    # ---------- primitives, normalized units (scaled by H when evaluated)
    skull = Prims()
    crn = 1 + 0.08 * child
    skull.ell(V(0, 0.1 + 0.02 * child, -0.06), np.eye(3), V(0.32 * sx, 0.385, 0.405) * crn)
    fsc = 1 - 0.12 * child                     # a child's face is smaller and sits lower
    fy = -0.03 * child
    skull.ell(V(0, -0.06 + fy, 0.1), np.eye(3), V(0.272 * sx, 0.26 * fsc, 0.24))      # face front to the upper jaw
    skull.ell(V(0, -0.15 + fy, 0.15), np.eye(3), V(0.2 * sx, 0.12 * fsc, 0.13))       # maxilla under the cheeks
    bro = body.g(0.05, 0.036) * (1 - 0.5 * child)
    for s in (1, -1):
        skull.cone(V(s * 0.205, 0.075 + fy, 0.215), V(s * 0.03, 0.07 + fy, 0.29), bro * 0.85, bro)
        skull.ell(V(s * 0.19, -0.06 + fy, 0.18), rz(R(s * 15)), V(0.08, 0.05, 0.08) * fsc)   # cheekbone
        skull.ell(V(s * 0.325, -0.07 + fy, -0.07), ry(R(s * 22)) @ rx(R(-12)), V(0.022, 0.12 + 0.02 * old, 0.065))  # ear
    mz = Prims()   # the muzzle barrel and upper lip (skull-fixed)
    mz.ell(V(0, -0.26 + fy, 0.18), np.eye(3), V(0.165 * sx, 0.085, 0.14) * fsc)         # upper muzzle (maxilla)
    mz.ell(V(0, -0.286 + fy + 0.5 * (up_mid + 0.298), 0.297), rx(R(-12)), V(0.1 * sx, 0.034 + 0.008 * fem - 0.008 * old, 0.045) * fsc)
    nose = Prims()
    nl = 1 + 0.08 * old - 0.25 * child
    tip = V(0, -0.19 * nl + fy - 0.01 * old + 0.012 * sneer, 0.4 - 0.03 * child)
    nose.cone(V(0, 0.03 + fy, 0.292), tip, 0.03, body.g(0.044, 0.038))
    for s in (1, -1):
        nose.ell(V(s * 0.048, -0.2 * nl + fy + 0.012 * sneer, 0.315), np.eye(3), V(0.038, 0.034, 0.042) * (1 + 0.1 * sneer))
    nose.ell(tip + V(0, -0.012, -0.03), np.eye(3), V(0.03, 0.03, 0.04))
    jw = Prims()   # mandible, chin, lower lip: these move with the jaw
    gx = body.g(0.255, 0.235) * (1 - 0.1 * child)
    jr = body.g(0.075, 0.06)
    for s in (1, -1):
        jw.cone(V(s * gx, -0.24 + fy, -0.05), V(s * 0.055, -0.455 + fy + chin_up * 0.5, 0.215), jr, body.g(0.062, 0.05))
        jw.ell(V(s * 0.115, -0.32 + fy, 0.1), np.eye(3), V(0.075, 0.085, 0.09))
    jw.ell(V(0, -0.435 + fy + chin_up, 0.225 + chin_up * 0.5), np.eye(3), V(body.g(0.1, 0.08), 0.075, 0.075) * fsc)
    jw.ell(V(0, -0.36 + fy, 0.17), np.eye(3), V(0.15 * sx, 0.08, 0.13) * fsc)          # lower muzzle, moves with the jaw
    lip_lo_y = -0.345 + fy + chin_up * 0.6
    jw.ell(V(0, lip_lo_y, 0.282), rx(R(14)), V(0.088 * sx, 0.036 + 0.008 * fem - 0.008 * old, 0.046) * fsc)
    soft = Prims()   # cheek pads, brows, jowls: soft tissue moved by the action units
    for s in (1, -1):
        soft.ell(V(s * (0.145 + 0.01 * A("12")), -0.15 + fy + cheek_up - 0.03 * old, 0.215 + 0.025 * cheek_up / 0.06),
                 rz(R(s * -20)), V(0.085, 0.08, 0.07) * (1 + 0.6 * cheek_up) * (1 + 0.1 * child) * (1 - 0.15 * old))
        soft.ell(V(s * (0.07 - knit), 0.068 + fy + brow_in, 0.285 + 0.01 * A("4")), rz(R(s * (8 - 25 * A("1") + 10 * A("4")))), V(0.06, 0.026, 0.038))
        soft.ell(V(s * 0.17, 0.072 + fy + brow_out, 0.248), rz(R(s * (-8 + 10 * A("2")))), V(0.07, 0.024, 0.036))
        soft.ell(V(s * 0.17, -0.2 + fy, 0.12), np.eye(3), V(0.09, 0.11, 0.1) * (1 - 0.45 * old) * (1 + 0.15 * child))  # buccal fat
        if old > 0:
            soft.ell(V(s * 0.17, -0.38 + fy, 0.11), np.eye(3), V(0.07, 0.07, 0.08) * old)      # jowls
            soft.ell(V(s * 0.115, -0.07 + fy, 0.25), np.eye(3), V(0.06, 0.025, 0.035) * old)   # under-eye bags
    eyes = [V(s * 0.108, -0.005 + fy * 0.5, 0.245) for s in (1, -1)]
    re = 0.054 * (1 + 0.1 * child)
    teeth_up = (V(0, -0.315 + fy, 0.17), V(0.082, 0.03, 0.105))
    gaze_dir = nrm(ry(R(gaze[0])) @ rx(-R(gaze[1])) @ V(0, 0, 1))
    sa, ma, na, ja, xa = skull.arrays(), mz.arrays(), nose.arrays(), jw.arrays(), soft.arrays()

    def mouth2d(q):
        x, y = np.abs(q[:, 0]), q[:, 1]
        t = np.clip(x / cx, 0, 1)
        yu = up_mid + (cy - up_mid) * (1 - (1 - t ** pu) ** (1 / pu))
        yl = lo_mid + (cy - lo_mid) * (1 - (1 - t ** pl) ** (1 / pl))
        return np.maximum.reduce([x - cx, y - yu, yl - y])

    def local(p):
        return ((p - O) @ M) / H     # world -> head local, normalized

    def sdf_local(q):
        d = smin_exp(skull.raw(q, sa), 0.06)
        d = smin(d, smin_exp(mz.raw(q, ma), 0.03), 0.06)
        qj = (q - pivot) @ Rj + pivot          # points in the jaw's rest frame
        dj = smin_exp(jw.raw(qj, ja), 0.05)
        d = smin(d, dj, 0.07)
        d = smin(d, smin_exp(soft.raw(q, xa), 0.03), 0.06)
        d = smin(d, smin_exp(nose.raw(q, na), 0.02), 0.035)
        # eye sockets
        for e in eyes:
            # no hole around the eye: only the fold between brow and upper lid, and a soft hollow
            # at the inner corner beside the nose root
            sock = np.linalg.norm((q - e - V(0, 0.036, 0.05)) / V(0.07, 0.03, 0.05), axis=1) - 1
            d = smax(d, -sock * 0.03, 0.02)
            inner = np.linalg.norm((q - e - V(-np.sign(e[0]) * 0.05, 0.0, 0.06)) / V(0.025, 0.035, 0.03), axis=1) - 1
            d = smax(d, -inner * 0.02, 0.015)
        # nasolabial furrow (deepens with the cheek raised)
        fold = 0.008 * (A("12") + 0.6 * A("10") + 0.5 * old)
        if fold > 0.002:
            for s in (1, -1):
                a = V(s * 0.065, -0.195 + fy, 0.31); b = V(s * (cx + 0.025), cy - 0.015, 0.25)
                g = rc_batch(q, a[None], b[None], np.array([fold], np.float32), np.array([fold * 0.6], np.float32))[:, 0]
                d = smax(d, -g, 0.008)
        # forehead furrows when the brows lift; a vertical crease when they knit
        lift = 0.5 * (A("1") + A("2"))
        if lift > 0.2:
            mask = np.clip(1 - np.abs(q[:, 0]) / 0.22, 0, 1) * np.clip((q[:, 1] - 0.12) / 0.04, 0, 1) * np.clip((0.3 - q[:, 1]) / 0.05, 0, 1)
            d = d + 0.0025 * lift * mask * np.sin(q[:, 1] * 160) * (q[:, 2] > 0)
        if A("4") > 0.3:
            mask = np.exp(-(q[:, 0] / 0.02) ** 2) * np.exp(-((q[:, 1] - 0.11) / 0.05) ** 2)
            d = d + 0.006 * A("4") * mask
        # the mouth: carve the opening, then the teeth and the dark inside
        mo = mouth2d(q)
        cav = np.maximum(mo, 0.14 - q[:, 2])
        if lo_mid >= up_mid - 0.006:
            t = np.clip(np.abs(q[:, 0]) / cx, 0, 1)
            yline = up_mid - 0.004 + (cy - up_mid) * t ** pu
            slit = np.maximum.reduce([np.abs(q[:, 1] - yline) - 0.003 * (1 - t ** 4), np.abs(q[:, 0]) - cx, 0.295 - q[:, 2]])
            d = smax(d, -slit, 0.004)
        if lo_mid < up_mid - 0.006:
            d = smax(d, -cav, 0.006)
            tu = np.maximum(np.abs(np.linalg.norm((q[:, [0, 2]] - teeth_up[0][[0, 2]]) / teeth_up[1][[0, 2]], axis=1) - 1) * 0.08 - 0.008,
                            np.abs(q[:, 1] - (-0.31 + fy)) - 0.022)
            tu = np.maximum(tu, -q[:, 2] + 0.16)
            tl = np.maximum(np.abs(np.linalg.norm((qj[:, [0, 2]] - teeth_up[0][[0, 2]] - V(0, 0)) / (teeth_up[1][[0, 2]] * 0.93), axis=1) - 1) * 0.08 - 0.008,
                            np.abs(qj[:, 1] - (-0.345 + fy)) - 0.02)
            tl = np.maximum(tl, -qj[:, 2] + 0.16)
            d = np.minimum(d, np.minimum(tu, tl))
            tongue = np.linalg.norm((qj - V(0, -0.37 + fy, 0.12)) / V(0.075, 0.03, 0.1), axis=1) - 1
            d = np.minimum(d, tongue * 0.03)
        # eyeballs and lids
        for i, e in enumerate(eyes):
            qe = q - e
            ball = np.linalg.norm(qe, axis=1) - re
            r_ = np.linalg.norm(qe, axis=1)
            shell = np.abs(r_ - (re + 0.009)) - 0.006
            xe = qe[:, 0]
            up = np.maximum(shell, (lid_u - 0.32 * xe ** 2 / re) - qe[:, 1])
            lo = np.maximum(shell, qe[:, 1] - (lid_l + 0.22 * xe ** 2 / re))
            lids = np.maximum(np.minimum(up, lo), -qe[:, 2] - 0.01)
            d = smin(d, smin(ball, lids, 0.004), 0.03)
        return d

    def f(p):
        return sdf_local(local(p)) * H * 0.9

    def colorf(p):
        q = local(p)
        n = len(q)
        c = np.broadcast_to(sk, (n, 3)).copy()
        # warmer cheeks, nose and ears; cooler jaw (the three colour zones of the face)
        warm = np.exp(-((np.abs(q[:, 0]) - 0.16) / 0.08) ** 2 - ((q[:, 1] + 0.14) / 0.1) ** 2) + np.exp(-(q[:, 0] / 0.05) ** 2 - ((q[:, 1] + 0.15) / 0.08) ** 2)
        c *= (1 + 0.06 * np.clip(warm, 0, 1)[:, None] * V(1, -0.6, -0.8))
        cool = np.clip((-q[:, 1] - 0.33) / 0.1, 0, 1) * (1 - fem) * 0.5
        c *= (1 - 0.06 * cool[:, None] * V(1, 0.6, -0.4))
        # lips
        qj_ = (q - pivot) @ Rj + pivot
        dl = np.minimum(ell_batch(q, ma["C"][1:2], ma["Mt"][1:2], ma["Rd"][1:2])[:, 0],
                        ell_batch(qj_, ja["C"][-1:], ja["Mt"][-1:], ja["Rd"][-1:])[:, 0])
        lipm = (dl < 0.006) & (np.abs(q[:, 0]) < cx + 0.012) & (q[:, 2] > 0.24)
        c[lipm] = c[lipm] * 0.4 + lips * 0.6
        # mouth inside, teeth
        if lo_mid < up_mid - 0.006:
            mo = mouth2d(q)
            inside = (mo < 0.004) & (q[:, 2] < 0.27)
            c[inside] = mouthc
            qj = (q - pivot) @ Rj + pivot
            tm = inside & (((np.abs(q[:, 1] - (-0.31 + fy)) < 0.024) & (q[:, 2] > 0.15)) | ((np.abs(qj[:, 1] - (-0.345 + fy)) < 0.022) & (qj[:, 2] > 0.15)))
            c[tm] = teeth
        # eyes: sclera, iris, pupil
        for e in eyes:
            qe = q - e
            on = np.abs(np.linalg.norm(qe, axis=1) - re) < 0.0015
            dirn = qe / (np.linalg.norm(qe, axis=1, keepdims=True) + 1e-9)
            cosg = dirn @ gaze_dir
            m = on
            c[m] = hx(eye_col)
            c[m & (cosg > 0.86)] = hx(iris_col)
            c[m & (cosg > 0.975)] = hx("#0c0806")
        return c
    return dict(f=f, colorf=colorf, color=sk, element="head", bound=(O, H * 0.62), gloss=gloss, planes=o.get("planes", 0.45),
                frame=M, scale=H, lift=(lid_l, lid_u))


def hair_part(o, body, O, M, wind, collide):
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
        hl = hl + 0.03 * np.cos(q[:, 0] * 14) * (z > 0)          # an irregular front edge
        t = th * np.clip((q[:, 1] - hl) / 0.1, 0.12, 1.0)        # thin at the hairline, full above
        d = np.linalg.norm((q - V(0, 0.1, -0.06)) / V(0.32, 0.385, 0.405), axis=1) - 1
        d = d * 0.37 - t - 0.004
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
    for it in range(iters):
        vel = (P - prev) * 0.94
        prev = P.copy()
        acc = g + drag * (gust - vel / dt) * 0.5
        P = P + vel + acc * dt * dt
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
                if bad.any():
                    e = 0.004
                    gr = np.stack([(collide(flat[bad] + V(*(e * np.eye(3)[k]))) - dd[bad]) / e for k in range(3)], 1)
                    flat[bad] += nrm(gr) * (r - dd[bad])[:, None]
                    pf = prev.reshape(-1, 3)
                    pf[bad] = flat[bad]
                    prev = pf.reshape(P.shape)
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
    arm_prims = []
    for side, s in ((1, "l"), (-1, "r")):
        A_ = Prims()
        sh, el, wr = J[f"sh_{s}"], J[f"el_{s}"], J[f"wr_{s}"]
        g_ = bl * (1 - 0.15 * body.fem)
        du = nrm(el - sh)
        A_.ell(sh + du * 0.22 * u + Rc @ V(side * 0.05 * u, 0, 0), Rc, V(0.24, 0.3, 0.25) * u * g_)   # deltoid
        A_.cone(sh, el, 0.21 * u * g_, 0.15 * u * g_)
        A_.cone(el, wr, 0.17 * u * g_, 0.105 * u * g_)
        A_.ell(el + (wr - el) * 0.25, frame_along(wr - el), V(0.18, 0.32, 0.16) * u * g_)       # forearm muscles
        arm_prims.append(A_)
    leg_prims, foot_prims = [], []
    for side, s in ((1, "l"), (-1, "r")):
        Lg = Prims()
        g_ = bl * body.g(1.0, 1.04)
        hp, kn, an = J[f"hip_{s}"], J[f"kn_{s}"], J[f"an_{s}"]
        Lg.cone(hp + Rp @ V(-side * 0.02 * u, 0.02 * u, 0), kn, 0.36 * u * g_ * bt ** 0.5, 0.22 * u * g_)
        Lg.ell(hp + (kn - hp) * 0.4 + J[f"Rthigh_{s}"] @ V(0, 0, 0.05 * u), J[f"Rthigh_{s}"], V(0.3, 0.7, 0.31) * u * g_)
        Lg.ell(kn + J[f"Rshin_{s}"] @ V(0, 0.03 * u, 0.02 * u), J[f"Rshin_{s}"], V(0.18, 0.22, 0.18) * u * g_)
        Lg.cone(kn, an, 0.2 * u * g_, 0.12 * u * g_)
        Lg.ell(kn + (an - kn) * 0.3 + J[f"Rshin_{s}"] @ V(0, 0, -0.07 * u), J[f"Rshin_{s}"], V(0.19, 0.42, 0.2) * u * g_)
        leg_prims.append(Lg)
        Ft = Prims()
        Rf = J[f"Rfoot_{s}"]
        Ft.ell(an + Rf @ V(0, -0.16 * u, 0.32 * u * lf ** 0.5), Rf, V(0.17, 0.12, 0.52 * lf ** 0.5) * u)
        Ft.ell(J[f"heel_{s}"] + Rf @ V(0, 0.08 * u, 0.05 * u), Rf, V(0.13, 0.15, 0.17) * u)
        foot_prims.append(Ft)
    hand_prims_ = []
    for side, s in ((1, "l"), (-1, "r")):
        hp = pose.get(f"hand_{s}", "relaxed")
        hand_prims_.append(hand_prims(J[f"Rhand_{s}"], J[f"wr_{s}"], hand_len, side, hp, girth=bl ** 0.5))

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
        groups.append(("arms", skin if "arms" in bare else torso_col, gloss_skin if "arms" in bare else 0, P.fn(0.08 * u), P.spheres(), 0.1 * u))
    for P in leg_prims:
        groups.append(("legs", col("legs"), 0, P.fn(0.12 * u), P.spheres(), 0.14 * u))
    for P in foot_prims:
        groups.append(("feet", skin if "feet" in bare else o.get("shoes", "#1e1a18"), 0, P.fn(0.06 * u), P.spheres(), 0.05 * u))
    for P in hand_prims_:
        groups.append(("hands", skin, gloss_skin, P.fn(0.012 * hand_len), P.spheres(), 0.03 * u))
    parts.append(body_part(groups, 0.1 * u, names))
    parts.append(head_part(o, body, J["head"], J["Rhead"], skin, lip_col=o.get("lips"), gloss=o.get("face_gloss", gloss_skin),
                           gaze=o.get("gaze", [0, 0])))
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
    parts += hair_part(o, body, J["head"], J["Rhead"], wind, lambda p: np.minimum(collide(p), np.linalg.norm(p - hp_, axis=1) - 0.5 * u))
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
