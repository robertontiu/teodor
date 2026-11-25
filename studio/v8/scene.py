"""Scene builder: a small signed-distance-field renderer for 3D blockouts.

A painter describes a scene in JSON (camera, sun, sky, lamps, fog, ground, objects including
posed human mannequins and houses), and this renders it with perspective, proportion,
soft shadows, ambient occlusion and atmospheric perspective, as a schema to paint over.

Units are meters. y is up. The camera looks along -z by default (put it at +z looking toward
the origin). Object rotation "rot" is degrees around y.
"""
import numpy as np, json, math, sys

# ---------------------------------------------------------------- math helpers
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


R = math.radians


def norm(v):
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-9)


# ---------------------------------------------------------------- primitive SDFs (p: (N,3))
def sd_box(p, b, r=0.0):
    q = np.abs(p) - (np.asarray(b, np.float32) - r)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0) - r


def sd_sphere(p, r):
    return np.linalg.norm(p, axis=1) - r


def sd_ellipsoid(p, r):
    r = np.asarray(r, np.float32)
    k0 = np.linalg.norm(p / r, axis=1)
    k1 = np.linalg.norm(p / (r * r), axis=1)
    return k0 * (k0 - 1) / (k1 + 1e-9)


def sd_capsule(p, a, b, r):
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    pa, ba = p - a, b - a
    h = np.clip((pa @ ba) / (ba @ ba + 1e-9), 0, 1)
    return np.linalg.norm(pa - h[:, None] * ba, axis=1) - r


def sd_cylinder(p, r, h):
    d = np.stack([np.linalg.norm(p[:, [0, 2]], axis=1) - r, np.abs(p[:, 1] - h / 2) - h / 2], 1)
    return np.minimum(d.max(1), 0) + np.linalg.norm(np.maximum(d, 0), axis=1)


def sd_gable(p, w, h, d):
    """Gable roof prism: base (width w) at y=0, ridge at y=h, along z with depth d."""
    s = math.hypot(w / 2, h)
    n1 = np.array([h / s, (w / 2) / s], np.float32)
    x, y = np.abs(p[:, 0]), p[:, 1]
    slope = (x * n1[0] + (y - h) * n1[1])
    return np.maximum.reduce([slope, -y, np.abs(p[:, 2]) - d / 2])


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


# ---------------------------------------------------------------- scene nodes
class Node:
    """An SDF node with a material. f maps world points (N,3) -> distances (N,)."""

    def __init__(self, f, color, emit=0.0, bound=None, kind="solid"):
        self.f, self.color, self.emit, self.bound, self.kind = f, hx(color) if isinstance(color, str) else color, emit, bound, kind


def local(pos, rot):
    pos = np.asarray(pos, np.float32)
    M = ry(-R(rot))
    return lambda p: (p - pos) @ M.T


def node_box(o):
    L = local(o["pos"], o.get("rot", 0))
    size = np.asarray(o["size"], np.float32) / 2
    cuts = [(np.asarray(c["pos"], np.float32), np.asarray(c["size"], np.float32) / 2) for c in o.get("cuts", [])]
    r = o.get("round", 0.0)

    def f(p):
        q = L(p)
        d = sd_box(q, size, r)
        for cp, cs in cuts:
            d = np.maximum(d, -sd_box(q - cp, cs))
        return d
    return [Node(f, o.get("color", "#888888"), o.get("emit", 0), (o["pos"], float(np.linalg.norm(size)) + 0.1))]


def node_simple(o):
    t = o["type"]
    if t == "sphere":
        c = np.asarray(o["pos"], np.float32)
        f = lambda p: sd_sphere(p - c, o["r"])
        b = (o["pos"], o["r"])
    elif t == "ellipsoid":
        L = local(o["pos"], o.get("rot", 0))
        f = lambda p: sd_ellipsoid(L(p), o["radii"])
        b = (o["pos"], max(o["radii"]))
    elif t == "capsule":
        f = lambda p: sd_capsule(p, o["a"], o["b"], o["r"])
        a, bb = np.asarray(o["a"]), np.asarray(o["b"])
        b = (list((a + bb) / 2), float(np.linalg.norm(a - bb)) / 2 + o["r"])
    elif t == "cylinder":
        c = np.asarray(o["pos"], np.float32)
        f = lambda p: sd_cylinder(p - c, o["r"], o["h"])
        b = (list(c + np.array([0, o["h"] / 2, 0])), o["h"] / 2 + o["r"])
    return [Node(f, o.get("color", "#888888"), o.get("emit", 0), b)]


def node_house(o):
    """House: walls (hollow shell) with door and windows on the front (+z local), gable roof,
    optional chimney; "ruined" removes the roof, chars the walls and breaks the top edge."""
    w, h, d = o.get("size", [6, 4, 8])
    t = o.get("wall", 0.25)
    rh = o.get("roof_h", w * 0.4)
    rot = o.get("rot", 0)
    pos = np.asarray(o["pos"], np.float32)
    L = local(pos, rot)
    ruined = o.get("ruined", False)
    rng = np.random.default_rng(o.get("seed", 3))
    openings = []
    door = o.get("door")
    if door:
        dh = door.get("h", 2.1)
        openings.append(dict(x=door.get("x", 0), y=dh / 2, w=door.get("w", 1.0), h=dh, color=door.get("color", "#1a1410"), emit=door.get("emit", 0), open=door.get("open", True)))
    for wi in o.get("windows", []):
        openings.append(dict(x=wi["x"], y=wi["y"], w=wi.get("w", 1.0), h=wi.get("h", 1.2), color=wi.get("color", "#141418"), emit=wi.get("emit", 0), open=True))
    for wi in o.get("side_windows", []):
        openings.append(dict(side=True, x=wi["x"], y=wi["y"], w=wi.get("w", 1.0), h=wi.get("h", 1.2), color=wi.get("color", "#141418"), emit=wi.get("emit", 0), open=True))
    breaks = []
    if ruined:
        for _ in range(12):
            side = rng.integers(0, 4)
            u = rng.uniform(-0.5, 0.5)
            bx, bz = [(u * w, d / 2), (u * w, -d / 2), (w / 2, u * d), (-w / 2, u * d)][side]
            breaks.append((bx, bz, rng.uniform(0.5, 1.6)))

    def walls(p):
        q = L(p)
        outer = sd_box(q - [0, h / 2, 0], [w / 2, h / 2, d / 2])
        inner = sd_box(q - [0, h / 2 - t / 2 + (t if ruined else 0), 0], [w / 2 - t, h / 2 - t / 2 + (t if ruined else 0), d / 2 - t])
        dd = np.maximum(outer, -inner)
        for op in openings:
            if op.get("side"):
                c = np.array([w / 2, op["y"], op["x"]], np.float32); s = [t * 1.5, op["h"] / 2, op["w"] / 2]
            else:
                c = np.array([op["x"], op["y"], d / 2], np.float32); s = [op["w"] / 2, op["h"] / 2, t * 1.5]
            if op["open"]:
                dd = np.maximum(dd, -sd_box(q - c, s))
        for bx, bz, bs in breaks:
            dd = np.maximum(dd, -sd_sphere(q - [bx, h + 0.2, bz], bs))
        return dd
    wc = o.get("color", "#c8b49a") if not ruined else o.get("color", "#1c1916")
    nodes = [Node(walls, wc, 0, (list(pos + [0, h / 2, 0]), math.hypot(w, h, d) / 2 + 1))]
    # glass / door leaves / glowing interiors
    for op in openings:
        if op["emit"] > 0 or not op["open"]:
            if op.get("side"):
                c = np.array([w / 2 - t * 0.7, op["y"], op["x"]], np.float32); s = [0.02, op["h"] / 2, op["w"] / 2]
            else:
                c = np.array([op["x"], op["y"], d / 2 - t * 0.7], np.float32); s = [op["w"] / 2, op["h"] / 2, 0.02]
            nodes.append(Node((lambda c, s: (lambda p: sd_box(L(p) - c, s)))(c, s), op["color"], op["emit"], (list(pos), math.hypot(w, h, d))))
    if not ruined:
        ov = o.get("overhang", 0.3)
        roof = lambda p: sd_gable(L(p) - [0, h, 0], w + 2 * ov, rh, d + 2 * ov)
        nodes.append(Node(roof, o.get("roof_color", "#6a3a2a"), 0, (list(pos + [0, h + rh / 2, 0]), math.hypot(w, d) / 2 + 1)))
    else:
        for i in range(o.get("beams", 3)):
            a = np.array([rng.uniform(-w / 2, w / 2), h * rng.uniform(0.4, 0.95), rng.uniform(-d / 2, d / 2)], np.float32)
            b = a + np.array([rng.uniform(-2, 2), rng.uniform(-1.5, 0.8), rng.uniform(-2, 2)], np.float32)
            nodes.append(Node((lambda a, b: (lambda p: sd_capsule(L(p), a, b, 0.12)))(a, b), "#120e0c", 0, (list(pos), math.hypot(w, h, d))))
    if o.get("chimney", False):
        cx = w * 0.25
        nodes.append(Node(lambda p: sd_box(L(p) - [cx, h + rh * 0.55, -d * 0.15], [0.3, rh * 0.6, 0.3]), o.get("chimney_color", "#5a3a2e") if not ruined else "#151210", 0, (list(pos), math.hypot(w, h + rh, d))))
    return nodes


# ---------------------------------------------------------------- the mannequin
POSES = {
    "stand": {},
    "walk": {"leg_l": [25, 15], "leg_r": [-20, 5], "arm_l": [-20, 8, 12], "arm_r": [22, 8, 18]},
    "bowed": {"spine": 18, "head": 45, "arm_l": [4, 6, 12], "arm_r": [4, 6, 12]},
    "slumped": {"spine": 28, "head": 40, "shoulders": 0.05, "arm_l": [8, 4, 10], "arm_r": [8, 4, 10]},
    "hand_on_brow": {"spine": 14, "head": 32, "arm_r": [65, -28, 112], "arm_l": [5, 6, 12]},
    "arms_crossed": {"arm_l": [35, -35, 105], "arm_r": [38, -35, 105]},
    "reach": {"arm_r": [80, 8, 8], "spine": 6},
    "wave": {"arm_r": [150, 25, 25]},
    "kneel": {"leg_l": [80, 85], "leg_r": [0, 95], "spine": 10, "head": 15},
    "kneel_bowed": {"leg_l": [0, 100], "leg_r": [0, 100], "spine": 35, "head": 40, "arm_l": [40, -10, 30], "arm_r": [40, -10, 30]},
    "sit_ground": {"leg_l": [88, 10], "leg_r": [85, 20], "arm_l": [20, 15, 10], "arm_r": [20, 15, 10]},
    "hold_child": {"arm_l": [45, -25, 80], "arm_r": [50, -30, 75]},
    "look_up": {"head": -30, "spine": -5},
}


def mannequin(o):
    """Anatomically proportioned figure (7.5 heads). pose: a preset name; any joint can be
    overridden: spine, head, head_yaw (deg), arm_l/arm_r [raise_forward, abduct_out, elbow],
    leg_l/leg_r [hip_forward, knee]. clothing: coat (long), dress, shawl."""
    H = o.get("height", 1.75)
    s = H / 1.70
    pose = dict(POSES.get(o.get("pose", "stand"), {}))
    pose.update(o.get("joints", {}))
    Rs = rx(R(pose.get("spine", 0)))
    Rh = Rs @ rx(R(pose.get("head", 0))) @ ry(R(pose.get("head_yaw", 0)))

    def limb_dir(p_deg, ab_deg, side):
        d = np.array([0, -math.cos(R(p_deg)), math.sin(R(p_deg))], np.float32)
        return rz(side * R(ab_deg)) @ d

    J = {}
    J["pelvis"] = np.zeros(3, np.float32)
    J["chest"] = Rs @ np.array([0, 0.33, 0], np.float32)
    J["neck"] = Rs @ np.array([0, 0.50, 0], np.float32)
    J["head"] = J["neck"] + Rh @ np.array([0, 0.12, 0.015], np.float32)
    drop = pose.get("shoulders", 0.0)
    for side, nm in ((1, "l"), (-1, "r")):
        sh = Rs @ np.array([side * 0.18, 0.45 - drop, 0], np.float32)
        a = pose.get(f"arm_{nm}", [0, 7, 10])
        du = Rs @ limb_dir(a[0], a[1], side)
        df = Rs @ limb_dir(a[0] + a[2], a[1], side)
        J[f"sh_{nm}"], J[f"el_{nm}"] = sh, sh + du * 0.29
        J[f"ha_{nm}"] = J[f"el_{nm}"] + df * 0.26
        hp = np.array([side * 0.095, 0, 0], np.float32)
        lg = pose.get(f"leg_{nm}", [0, 0])
        dt = limb_dir(lg[0], 0, side)
        ds = limb_dir(lg[0] - lg[1], 0, side)
        J[f"hip_{nm}"], J[f"kn_{nm}"] = hp, hp + dt * 0.44
        J[f"an_{nm}"] = J[f"kn_{nm}"] + ds * 0.42
        J[f"ft_{nm}"] = J[f"an_{nm}"] + np.array([0, -0.03, 0.13], np.float32)
    low = min(min(J[f"an_{n}"][1] - 0.05, J[f"kn_{n}"][1] - 0.06, J[f"ft_{n}"][1] - 0.035) for n in "lr")
    lift = -low
    pos = np.asarray(o.get("pos", [0, 0, 0]), np.float32)
    Mr = ry(R(o.get("facing", 0)))
    W = {k: pos + Mr @ ((v + np.array([0, lift, 0], np.float32)) * s) for k, v in J.items()}
    caps = [("pelvis", "chest", 0.13), ("neck", "head", 0.05), ("hip_l", "hip_r", 0.11)]
    for n in "lr":
        caps += [(f"sh_{n}", f"el_{n}", 0.048), (f"el_{n}", f"ha_{n}", 0.038), (f"hip_{n}", f"kn_{n}", 0.075),
                 (f"kn_{n}", f"an_{n}", 0.055), (f"an_{n}", f"ft_{n}", 0.04)]
    caps.append(("sh_l", "sh_r", 0.06))
    coat, dress, shawl = o.get("coat", False), o.get("dress", False), o.get("shawl", False)
    knee_mid = (W["kn_l"] + W["kn_r"]) / 2
    shin_mid = (W["an_l"] + W["an_r"] + W["kn_l"] + W["kn_r"]) / 4
    k = 0.04 * s
    Mt = Mr @ Rs

    def body(p):
        d = sd_ellipsoid((p - W["chest"]) @ Mt, np.array([0.16, 0.13, 0.10]) * s)
        for a, b, r in caps:
            d = smin(d, sd_capsule(p, W[a], W[b], r * s), k)
        if coat:
            d = smin(d, sd_capsule(p, W["chest"], knee_mid + (shin_mid - knee_mid) * 0.4, 0.17 * s), 0.06 * s)
        if dress:
            d = smin(d, sd_capsule(p, W["pelvis"] + (W["chest"] - W["pelvis"]) * 0.3, shin_mid, 0.19 * s), 0.08 * s)
        if shawl:
            d = smin(d, sd_ellipsoid((p - (W["chest"] + (W["neck"] - W["chest"]) * 0.5)) @ Mt, np.array([0.22, 0.12, 0.15]) * s), 0.05 * s)
        return d

    def skin(p):
        d = sd_ellipsoid((p - W["head"]) @ (Mr @ Rh), np.array([0.075, 0.105, 0.09]) * s)
        for n in "lr":
            d = np.minimum(d, sd_sphere(p - W[f"ha_{n}"], 0.042 * s))
        return d

    b = (list(pos + [0, H / 2, 0]), H)
    nodes = [Node(body, o.get("color", "#2a2a30"), 0, b), Node(skin, o.get("skin", "#c09078"), 0, b)]
    if o.get("hair"):
        nodes.append(Node(lambda p: sd_ellipsoid((p - W["head"] - Mr @ Rh @ np.array([0, 0.02, -0.01]) * s) @ (Mr @ Rh), np.array([0.082, 0.1, 0.095]) * s), o["hair"], 0, b))
    return nodes


def node_fence(o):
    a, b = np.asarray(o["a"], np.float32), np.asarray(o["b"], np.float32)
    h = o.get("h", 1.1)
    n = max(2, int(np.linalg.norm(b - a) / o.get("spacing", 1.8)) + 1)
    col = o.get("color", "#5a4a3a")
    nodes = []
    for i in range(n):
        c = a + (b - a) * i / (n - 1)
        nodes += node_simple({"type": "capsule", "a": [c[0], 0, c[2]], "b": [c[0], h, c[2]], "r": 0.06, "color": col})
    for y in o.get("rails", [h * 0.45, h * 0.9]):
        nodes += node_simple({"type": "capsule", "a": [a[0], y, a[2]], "b": [b[0], y, b[2]], "r": 0.035, "color": col})
    return nodes


def node_tree(o):
    p = np.asarray(o["pos"], np.float32)
    h = o.get("h", 6)
    rng = np.random.default_rng(o.get("seed", 1))
    nodes = node_simple({"type": "capsule", "a": list(p), "b": list(p + [0, h * 0.6, 0]), "r": h * 0.03, "color": o.get("trunk", "#3a2a20")})
    if not o.get("bare"):
        for i in range(5):
            c = p + [rng.normal(0, h * 0.12), h * rng.uniform(0.6, 0.9), rng.normal(0, h * 0.12)]
            nodes += node_simple({"type": "sphere", "pos": list(c), "r": h * rng.uniform(0.16, 0.24), "color": o.get("color", "#3a4a2a")})
    return nodes


BUILDERS = {"box": node_box, "sphere": node_simple, "ellipsoid": node_simple, "capsule": node_simple,
            "cylinder": node_simple, "house": node_house, "figure": mannequin, "fence": node_fence, "tree": node_tree}


# ---------------------------------------------------------------- renderer
class Scene:
    def __init__(self, spec):
        self.spec = spec
        self.nodes = []
        for o in spec.get("objects", []):
            self.nodes += BUILDERS[o["type"]](o)
        g = spec.get("ground", {})
        self.ground_y = g.get("y", 0.0)
        self.gc1, self.gc2 = hx(g.get("color", "#6a6048")), hx(g.get("color2", g.get("color", "#6a6048")))
        self.has_ground = g.get("enabled", True)

    def sdf(self, p, with_mat=False):
        ds = []
        if self.has_ground:
            ds.append(p[:, 1] - self.ground_y)
        for n in self.nodes:
            c, r = n.bound
            db = np.linalg.norm(p - np.asarray(c, np.float32), axis=1) - r
            if with_mat or db.min() < 0.5:
                ds.append(np.maximum(n.f(p), db - 0.0) if False else n.f(p))
            else:
                ds.append(db)
        D = np.stack(ds, 1)
        if with_mat:
            return D.min(1), D.argmin(1)
        return D.min(1)

    def normal(self, p):
        e = 0.002
        k = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], np.float32)
        n = sum(k[i][None, :] * self.sdf(p + k[i] * e)[:, None] for i in range(4))
        return norm(n)

    def march(self, ro, rd, tmax=400, steps=180):
        N = rd.shape[0]
        t = np.full(N, 0.05, np.float32)
        hit = np.zeros(N, bool)
        active = np.ones(N, bool)
        for _ in range(steps):
            idx = np.nonzero(active)[0]
            if len(idx) == 0:
                break
            p = ro[idx] + rd[idx] * t[idx, None]
            d = self.sdf(p)
            t[idx] += d * 0.8
            h = d < 0.0015 * (1 + t[idx])
            hit[idx[h]] = True
            active[idx[h]] = False
            active[idx[t[idx] > tmax]] = False
        return t, hit

    def shadow(self, p, ld, k=8.0, steps=56, tmax=60):
        N = p.shape[0]
        res = np.ones(N, np.float32)
        t = np.full(N, 0.03, np.float32)
        active = np.ones(N, bool)
        for _ in range(steps):
            idx = np.nonzero(active)[0]
            if len(idx) == 0:
                break
            q = p[idx] + ld[idx] * t[idx, None] if ld.ndim == 2 else p[idx] + ld[None, :] * t[idx, None]
            d = self.sdf(q)
            res[idx] = np.minimum(res[idx], np.clip(k * d / t[idx], 0, 1))
            t[idx] += np.clip(d, 0.02, 1.5)
            done = (d < 0.001) | (t[idx] > tmax)
            res[idx[d < 0.001]] = 0
            active[idx[done]] = False
        return np.clip(res, 0, 1) ** 1.2

    def ao(self, p, n):
        occ = np.zeros(p.shape[0], np.float32)
        sca = 1.0
        for i in range(5):
            h = 0.03 + 0.12 * i
            d = self.sdf(p + n * h)
            occ += (h - d) * sca
            sca *= 0.75
        return np.clip(1 - 1.8 * occ, 0.15, 1)

    def render(self, W=450, H=600):
        sp = self.spec
        cam = sp.get("camera", {})
        ro = np.asarray(cam.get("pos", [0, 1.6, 12]), np.float32)
        ta = np.asarray(cam.get("look_at", [0, 1.4, 0]), np.float32)
        fov = R(cam.get("fov", 40))
        fw = norm(ta - ro)
        rt = norm(np.cross(fw, [0, 1, 0]))
        up = np.cross(rt, fw)
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        u = (xs + 0.5 - W / 2) / (H / 2)
        v = -(ys + 0.5 - H / 2) / (H / 2)
        f = 1 / math.tan(fov / 2)
        rd = norm(u.reshape(-1, 1) * rt + v.reshape(-1, 1) * up + f * fw).astype(np.float32)
        RO = np.broadcast_to(ro, rd.shape).astype(np.float32)
        sun = sp.get("sun", {})
        az, el = R(sun.get("azimuth", 40)), R(sun.get("elevation", 25))
        ld = np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)], np.float32)
        scol = hx(sun.get("color", "#fff0d8")) * sun.get("intensity", 1.6)
        sky = sp.get("sky", {})
        zen, hor = hx(sky.get("zenith", "#5a7090")), hx(sky.get("horizon", "#e8d0b0"))
        glow = sky.get("sun_glow", 0.6)
        amb = sp.get("ambient", {})
        asky, agr, ai = hx(amb.get("sky", sky.get("zenith", "#6a7890"))), hx(amb.get("ground", "#5a4a3a")), amb.get("intensity", 0.45)
        fog = sp.get("fog", {})
        fcol, fden = hx(fog.get("color", sky.get("horizon", "#d8c8b0"))), fog.get("density", 0.008)

        def skycol(d):
            t = np.clip(d[:, 1] * 1.6, 0, 1)[:, None]
            c = hor * (1 - t) + zen * t
            sd = np.clip(d @ ld, 0, 1)
            c = c + (scol / max(scol.max(), 1e-6)) * (glow * sd ** 8 + 0.9 * (sd > math.cos(R(sun.get("disc", 1.6)))))[:, None]
            return c

        t, hit = self.march(RO, rd)
        img = skycol(rd)
        idx = np.nonzero(hit)[0]
        p = RO[idx] + rd[idx] * t[idx, None]
        _, mat = self.sdf(p, with_mat=True)
        n = self.normal(p)
        base = np.zeros((len(idx), 3), np.float32)
        emit = np.zeros(len(idx), np.float32)
        off = 1 if self.has_ground else 0
        if self.has_ground:
            g = mat == 0
            gx, gz = p[g, 0], p[g, 2]
            nz = 0.5 + 0.25 * np.sin(gx * 0.7 + np.sin(gz * 0.5) * 2) * np.sin(gz * 0.9) + 0.25 * np.sin(gx * 2.3 + gz * 1.7)
            base[g] = self.gc1 * (1 - nz[:, None]) + self.gc2 * nz[:, None]
        for i, nd in enumerate(self.nodes):
            m = mat == i + off
            base[m] = nd.color
            emit[m] = nd.emit
        pe = p + n * 0.01
        dif = np.clip(n @ ld, 0, 1)
        sh = np.zeros(len(idx), np.float32)
        lit = dif > 0
        if lit.any():
            sh[lit] = self.shadow(pe[lit], ld, k=sun.get("softness", 10))
        ao = self.ao(pe, n)
        hemi = (0.5 + 0.5 * n[:, 1])[:, None]
        ambient = (asky * hemi + agr * (1 - hemi)) * ai
        col = base * (scol * (dif * sh)[:, None] + ambient * ao[:, None])
        for L in sp.get("lights", []):
            lp = np.asarray(L["pos"], np.float32)
            lv = lp - p
            dist = np.linalg.norm(lv, axis=1)
            lvn = lv / dist[:, None]
            att = L.get("intensity", 2.0) / (1 + (dist / L.get("radius", 3.0)) ** 2)
            col += base * hx(L.get("color", "#ffc070")) * (np.clip((n * lvn).sum(1), 0, 1) * att * ao)[:, None]
        col += base * emit[:, None]
        fogf = 1 - np.exp(-t[idx] * fden)
        sdir = np.clip(rd[idx] @ ld, 0, 1) ** 6 * 0.5
        col = col * (1 - fogf[:, None]) + (fcol + scol * sdir[:, None] * 0.25)[None, :] * fogf[:, None] if False else col * (1 - fogf[:, None]) + (fcol[None, :] + (scol[None, :] * sdir[:, None] * 0.25)) * fogf[:, None]
        img[idx] = col
        exp_ = sp.get("exposure", 1.1)
        img = 1 - np.exp(-np.clip(img, 0, None) * exp_)
        img = img ** (1 / 1.08)
        return (np.clip(img, 0, 1).reshape(H, W, 3) * 255).astype(np.uint8)


def render_file(path_json, out_png, W=450, H=600, overlay_svg=None, full=(1200, 1600)):
    from PIL import Image
    import subprocess, os, tempfile
    spec = json.load(open(path_json))
    arr = Scene(spec).render(W, H)
    im = Image.fromarray(arr).resize(full, Image.BICUBIC)
    if overlay_svg:
        tmp = tempfile.mktemp(suffix=".png")
        subprocess.run(["rsvg-convert", "-w", str(full[0]), "-h", str(full[1]), "-o", tmp, overlay_svg], check=True)
        ov = Image.open(tmp).convert("RGBA")
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
        os.remove(tmp)
    im.save(out_png)
    return out_png


if __name__ == "__main__":
    a = sys.argv
    render_file(a[1], a[2], int(a[3]) if len(a) > 3 else 450, int(a[4]) if len(a) > 4 else 600, a[5] if len(a) > 5 else None)
    print(a[2])
