"""Scene builder: a small signed-distance-field renderer for 3D blockouts.

A painter describes a scene in JSON (camera, sun, sky, lamps, fog, ground, objects including
posed human mannequins and houses), and this renders it with perspective, proportion,
soft shadows, ambient occlusion and atmospheric perspective, as a schema to paint over.

Units are meters. y is up. The camera looks along -z by default (put it at +z looking toward
the origin). Object rotation "rot" is degrees around y. The camera can roll and look straight down
or up. People ("person"), hands, animals and water come from figure.py. Every render also records
which part of which object each pixel shows; render_file saves these as element masks
(<canvas>_elements.npz + <canvas>_elements.json; see docs/MANUAL.md, "The schema").
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
        self.owner, self.element, self.colorf, self.gloss, self.planes, self.frame, self.scale = None, "object", None, 0.0, 0.0, None, 1.0
        self.wrap = 0.0
        self.subf, self.sub, self.glossf, self.plane, self.nsmooth = None, None, None, False, 0.0


def from_part(d):
    """A render node from a figure.py part (dict)."""
    c, r = d["bound"]
    n = Node(d["f"], d["color"], d.get("emit", 0.0), (list(np.asarray(c, np.float32)), float(r)))
    n.element, n.colorf, n.gloss = d.get("element", "object"), d.get("colorf"), d.get("gloss", 0.0)
    n.planes, n.frame, n.scale = d.get("planes", 0.0), d.get("frame"), d.get("scale", 1.0)
    n.wrap = d.get("wrap", 0.0)
    n.plane = d.get("plane", False)
    n.subf, n.sub, n.glossf = d.get("subf"), d.get("sub"), d.get("glossf")
    n.nsmooth = d.get("nsmooth", 0.0)
    return n


def node_person(o):
    import figure
    parts, _ = figure.person(o)
    return [from_part(d) for d in parts]


def node_animal(o):
    import figure
    return [from_part(d) for d in figure.animal(o)]


def node_water(o):
    import figure
    return [from_part(d) for d in figure.water(o)]


def node_hand(o):
    """A lone hand for studies: pos = wrist, fingers = direction the fingers point, palm = the
    direction the palm faces, preset (see figure.HANDS), side l|r, length in meters."""
    import figure
    fdir = figure.nrm(o.get("fingers", [0, -1, 0]))
    palm = figure.nrm(o.get("palm", [0, 0, 1]))
    palm = figure.nrm(palm - (palm @ fdir) * fdir)
    M = np.stack([np.cross(-fdir, palm), -fdir, palm], 1).astype(np.float32)
    side = 1 if o.get("side", "l") == "l" else -1
    L = o.get("length", 0.18)
    pos = np.asarray(o.get("pos", [0, 1, 0]), np.float32)
    P = figure.hand_prims(M, pos, L, side, o.get("preset", "relaxed"), o.get("extra"), collide=o.get("_collide"))
    A = figure.Prims(); A.cone(pos, pos - fdir * L * 0.9 * o.get("forearm", 1.0), 0.1 * L, 0.13 * L)
    fh, fa, fn = P.fn(0.012 * L), A.fn(0.0), P.nails.fn(0.0)
    skin = hx(o.get("skin", "#c49a7e"))
    nail = np.clip(skin * np.array([1.08, 0.95, 0.95], np.float32) + 0.06, 0, 1)
    d = figure.part(lambda p: figure.smin(figure.smin(fh(p), fa(p), 0.03 * L), fn(p), 0.002 * L), skin, "hands", P.spheres() + A.spheres(), pad=0.02)
    d["colorf"] = lambda p: np.where((fn(p) < 0.0015 * L)[:, None], nail[None], skin[None])
    return [from_part(d)]


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
            "cylinder": node_simple, "house": node_house, "figure": mannequin, "fence": node_fence, "tree": node_tree,
            "person": node_person, "animal": node_animal, "water": node_water, "hand": node_hand}
LEGACY_ELEMENTS = {"figure": ["torso", "skin"]}


# ---------------------------------------------------------------- renderer
class Scene:
    def __init__(self, spec):
        self.spec = spec
        self.nodes = []
        g = spec.get("ground", {})
        counts = {}
        objs = spec.get("objects", [])
        built = [None] * len(objs)
        # people and lone hands are built last, so their hands can rest on what is already there
        # (fingers settle onto a surface instead of passing through it); the node order stays the scene's
        order = [i for i, o in enumerate(objs) if o["type"] not in ("person", "hand")] + \
                [i for i, o in enumerate(objs) if o["type"] in ("person", "hand")]
        for i in order:
            o = objs[i]
            t = o["type"]
            oo = dict(o, _ground_y=g.get("y", 0.0) if g.get("enabled", True) else -1e9, _wind=spec.get("wind", [0, 0, 0]))
            if t in ("person", "hand"):
                others = [nd for b in built if b for nd in b if not getattr(nd, "plane", False)]
                if others:
                    oo["_collide"] = self._collider(others)
            built[i] = BUILDERS[t](oo)
        for i, o in enumerate(objs):
            t = o["type"]
            new = built[i]
            owner = o.get("id") or f"{t}{counts.get(t, 0)}"
            counts[t] = counts.get(t, 0) + 1
            for j, nd in enumerate(new):
                nd.owner, nd.otype = owner, t
                if t in LEGACY_ELEMENTS:
                    nd.element = LEGACY_ELEMENTS[t][min(j, 1)]
            self.nodes += new
        self.pix = 0.0
        self.ground_y = g.get("y", 0.0)
        self.gc1, self.gc2 = hx(g.get("color", "#6a6048")), hx(g.get("color2", g.get("color", "#6a6048")))
        self.has_ground = g.get("enabled", True)

    @staticmethod
    def _collider(nodes):
        """Distance to a set of nodes (bounding spheres first), for hands touching objects."""
        def f(p):
            p = np.asarray(p, np.float32)
            d = np.full(len(p), 1e3, np.float32)
            for n in nodes:
                c, r = n.bound
                db = np.linalg.norm(p - np.asarray(c, np.float32), axis=1) - r
                near = db < 0.05
                if near.any():
                    d[near] = np.minimum(d[near], n.f(p[near]))
                d[~near] = np.minimum(d[~near], db[~near])
            return d
        return f

    def sdf(self, p, with_mat=False):
        """Distance to the scene. Each node is evaluated only on points near its bounding sphere;
        elsewhere the distance to the sphere stands in (a safe lower bound)."""
        N = p.shape[0]
        if self.has_ground:
            D = p[:, 1] - self.ground_y
            M = np.zeros(N, np.int32)
        else:
            D = np.full(N, 1e9, np.float32)
            M = np.full(N, -1, np.int32)
        off = 1 if self.has_ground else 0
        for i, n in enumerate(self.nodes):
            if getattr(n, "plane", False):
                d = n.f(p)
            else:
                c, r = n.bound
                db = np.linalg.norm(p - np.asarray(c, np.float32), axis=1) - r
                near = db < max(0.1, 0.5 * r)
                if not near.any():
                    d = db
                elif near.all():
                    d = n.f(p)
                else:
                    d = db.copy()
                    d[near] = n.f(p[near])
            if with_mat:
                closer = d < D
                M[closer] = i + off
            D = np.minimum(D, d)
        if with_mat:
            return D, M
        return D

    def normal(self, p, e=0.002):
        k = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], np.float32)
        e = np.asarray(e, np.float32).reshape(-1, 1) if np.ndim(e) else e
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
            h = d < (0.0015 * (1 + t[idx]) if not self.pix else np.maximum(0.0004, 0.6 * self.pix * t[idx]))
            hit[idx[h]] = True
            active[idx[h]] = False
            active[idx[t[idx] > tmax]] = False
            last = (idx, d)
        if self.pix and active.any():   # rays that ran out of steps grazing a surface count as hits
            idx = np.nonzero(active)[0]
            d = self.sdf(ro[idx] + rd[idx] * t[idx, None])
            ok = d < 4 * self.pix * t[idx] + 0.002
            hit[idx[ok]] = True
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

    def camera(self, W, H):
        """Ray origins and directions. camera: pos, look_at, fov, roll (degrees, clockwise in the
        picture), up (a hint; straight-down and straight-up views pick a sensible one)."""
        cam = self.spec.get("camera", {})
        ro = np.asarray(cam.get("pos", [0, 1.6, 12]), np.float32)
        ta = np.asarray(cam.get("look_at", [0, 1.4, 0]), np.float32)
        fov = R(cam.get("fov", 40))
        fw = norm(ta - ro)
        uh = np.asarray(cam.get("up", [0, 1, 0]), np.float32)
        if abs(float(fw @ norm(uh))) > 0.999:      # looking straight down or up: the top of the picture is -z
            uh = np.array([0, 0, -1], np.float32) if fw[1] < 0 else np.array([0, 0, 1], np.float32)
        rt = norm(np.cross(fw, uh))
        up = np.cross(rt, fw)
        roll = R(cam.get("roll", 0))
        if roll:
            rt, up = rt * math.cos(roll) + up * math.sin(roll), up * math.cos(roll) - rt * math.sin(roll)
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        u = (xs + 0.5 - W / 2) / (H / 2)
        v = -(ys + 0.5 - H / 2) / (H / 2)
        f = 1 / math.tan(fov / 2)
        rd = norm(u.reshape(-1, 1) * rt + v.reshape(-1, 1) * up + f * fw).astype(np.float32)
        RO = np.broadcast_to(ro, rd.shape).astype(np.float32)
        return RO, rd, fov

    def render(self, W=450, H=600):
        sp = self.spec
        RO, rd, fov = self.camera(W, H)
        fine = any(n.element != "object" or n.colorf is not None for n in self.nodes if getattr(n, "otype", "") not in LEGACY_ELEMENTS)
        self.pix = (fov / H) if fine else 0.0
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

        t, hit = self.march(RO, rd, steps=240 if fine else 180)
        img = skycol(rd)
        idx = np.nonzero(hit)[0]
        p = RO[idx] + rd[idx] * t[idx, None]
        _, mat = self.sdf(p, with_mat=True)
        n = self.normal(p) if not fine else self.normal(p, np.maximum(0.0006, 0.5 * self.pix * t[idx]))
        base = np.zeros((len(idx), 3), np.float32)
        emit = np.zeros(len(idx), np.float32)
        gloss = np.zeros(len(idx), np.float32)
        pl = np.zeros(len(idx), np.float32)
        wr = np.zeros(len(idx), np.float32)
        sublab = np.zeros(len(idx), np.int32)
        off = 1 if self.has_ground else 0
        if self.has_ground:
            g = mat == 0
            gx, gz = p[g, 0], p[g, 2]
            nz = 0.5 + 0.25 * np.sin(gx * 0.7 + np.sin(gz * 0.5) * 2) * np.sin(gz * 0.9) + 0.25 * np.sin(gx * 2.3 + gz * 1.7)
            base[g] = self.gc1 * (1 - nz[:, None]) + self.gc2 * nz[:, None]
        for i, nd in enumerate(self.nodes):
            m = mat == i + off
            if not m.any():
                continue
            base[m] = nd.colorf(p[m]) if nd.colorf is not None else nd.color
            emit[m] = nd.emit
            wr[m] = getattr(nd, "wrap", 0.0)
            gloss[m] = nd.glossf(p[m]) if nd.glossf is not None else nd.gloss
            if nd.subf is not None:
                sublab[m] = nd.subf(p[m])
            if nd.nsmooth:
                n[m] = self.normal(p[m], nd.nsmooth)
            if nd.planes > 0:
                # the plane head: the form simplified (a coarse normal over a few centimetres)
                # and, below, each plane given one value (light, two halftones, shadow)
                pm = p[m]
                nc = self.normal(pm, 0.025 * nd.scale)
                n[m] = norm(n[m] * (1 - nd.planes) + nc * nd.planes)
                pl[m] = nd.planes
        pe = p + n * 0.01 if not fine else p + n * np.maximum(0.002, 2 * self.pix * t[idx])[:, None]
        # skin scatters light under its surface, so the light wraps a little past the terminator
        # ("wrap" diffuse; 0 for everything but skin parts that ask for it)
        dif = np.clip((n @ ld + wr) / (1 + wr), 0, 1)
        sh = np.zeros(len(idx), np.float32)
        lit = dif > 0
        if lit.any():
            sh[lit] = self.shadow(pe[lit], ld, k=sun.get("softness", 10))
        ao = self.ao(pe, n)
        hemi = (0.5 + 0.5 * n[:, 1])[:, None]
        ambient = (asky * hemi + agr * (1 - hemi)) * ai
        light = dif * sh
        if pl.any():
            # value steps in the light (Bucci: "two or three values for halftone is enough"), with a
            # soft edge so the plane breaks stay where the form turns
            lv = np.array([0.0, 0.32, 0.62, 0.92], np.float32)
            edges = (lv[1:] + lv[:-1]) / 2
            q = lv[0] + sum((lv[i + 1] - lv[i]) * np.clip((light - edges[i]) / 0.1 + 0.5, 0, 1) for i in range(3))
            light = light * (1 - 0.6 * pl) + q * 0.6 * pl
        col = base * (scol * light[:, None] + ambient * ao[:, None])
        if gloss.any():
            hv = norm(ld[None, :] - rd[idx])
            spec = np.clip((n * hv).sum(1), 0, 1) ** 40 * gloss * sh * (dif > 0)
            col += scol[None, :] * spec[:, None] * 0.6
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
        col = col * (1 - fogf[:, None]) + (fcol[None, :] + (scol[None, :] * sdir[:, None] * 0.25)) * fogf[:, None]
        img[idx] = col
        exp_ = sp.get("exposure", 1.1)
        img = 1 - np.exp(-np.clip(img, 0, None) * exp_)
        img = img ** (1 / 1.08)
        # what each pixel shows: node index (-1 sky, -2 ground), and depth
        lab = np.full(W * H, -1, np.int32)
        lab[idx] = mat - off
        sl = np.zeros(W * H, np.int32)
        sl[idx] = sublab
        self.sublabels = sl.reshape(H, W)
        dep = np.full(W * H, np.inf, np.float32)
        dep[idx] = t[idx]
        self.labels, self.depth, self.size = lab.reshape(H, W), dep.reshape(H, W), (W, H)
        return (np.clip(img, 0, 1).reshape(H, W, 3) * 255).astype(np.uint8)

    def element_masks(self, full):
        """Masks per object and element at the canvas size: {key: bool (H,W)}, plus an index."""
        from PIL import Image
        Wf, Hf = full
        lab = self.labels
        groups = {}
        for i, nd in enumerate(self.nodes):
            if nd.sub:
                for j, el in enumerate(nd.sub):
                    groups.setdefault((nd.owner, nd.otype, el), []).append((i, j))
            else:
                groups.setdefault((nd.owner, nd.otype, nd.element), []).append((i, None))
        masks, index = {}, []
        owners = {}
        sub = self.sublabels

        def mask_of(ids):
            m = np.zeros(lab.shape, bool)
            for i, j in ids:
                m |= (lab == i) if j is None else ((lab == i) & (sub == j))
            return m
        for (owner, otype, el), ids in groups.items():
            m = mask_of(ids)
            if not m.any() and el not in ("head", "hands", "torso", "drapery"):
                continue
            owners.setdefault((owner, otype), []).extend(ids)
            key = f"{owner}.{el}"
            masks[key] = m
            index.append({"key": key, "object": owner, "type": otype, "element": el})
        for (owner, otype), ids in owners.items():
            if len(ids) > 1:
                masks[f"{owner}.all"] = mask_of(ids)
                index.append({"key": f"{owner}.all", "object": owner, "type": otype, "element": "all"})
        out, entries = {}, []
        for e in index:
            m = masks[e["key"]]
            big = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((Wf, Hf), Image.BILINEAR)) > 127
            ys, xs = np.nonzero(big)
            e["pixels"] = int(big.sum())
            e["share"] = round(e["pixels"] / (Wf * Hf), 5)
            if len(xs):
                e["bbox"] = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
                e["centroid"] = [round(float(xs.mean()), 1), round(float(ys.mean()), 1)]
                d = self.depth[m]
                e["depth_m"] = round(float(np.median(d[np.isfinite(d)])), 3) if np.isfinite(d).any() else None
            out[e["key"]] = big
            entries.append(e)
        return out, entries


_PLANE_DIRS = None


def plane_dirs():
    """Directions of the big planes of a head (front, sides, top, under-planes, the turn of the
    cheek and brow), as unit normals in the head's frame (x left, y up, z forward)."""
    global _PLANE_DIRS
    if _PLANE_DIRS is None:
        ds = []
        for el in (-60, -32, -10, 12, 38, 70):
            k = {-60: 4, -32: 7, -10: 9, 12: 9, 38: 7, 70: 4}[el]
            for i in range(k):
                az = -180 + 360 * i / k + (0 if el % 2 else 180 / k)
                ds.append([math.cos(R(el)) * math.sin(R(az)), math.sin(R(el)), math.cos(R(el)) * math.cos(R(az))])
        ds.append([0, 1, 0]); ds.append([0, -1, 0]); ds.append([0, 0, 1])
        _PLANE_DIRS = norm(np.array(ds, np.float32))
    return _PLANE_DIRS


def render_file(path_json, out_png, W=450, H=600, overlay_svg=None, full=(1200, 1600)):
    """Render a scene JSON to out_png at the canvas size. "render_scale" in the scene multiplies the
    render resolution (faces and hands need 1.5-2; costs time). Also writes element masks next to
    the image: <canvas>_elements.npz and <canvas>_elements.json when out_png is a studio scene
    version (<canvas>_scene_vN.png), else <out>_elements.npz/.json."""
    from PIL import Image
    import subprocess, os, tempfile, re
    spec = json.load(open(path_json))
    sc = max(0.25, min(float(spec.get("render_scale", 1.0)), 4.0))
    W, H = int(round(W * sc)), int(round(H * sc))
    scene = Scene(spec)
    arr = scene.render(W, H)
    im = Image.fromarray(arr).resize(full, Image.LANCZOS if sc > 1 else Image.BICUBIC)
    if overlay_svg:
        tmp = tempfile.mktemp(suffix=".png")
        subprocess.run(["rsvg-convert", "-w", str(full[0]), "-h", str(full[1]), "-o", tmp, overlay_svg], check=True)
        ov = Image.open(tmp).convert("RGBA")
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
        os.remove(tmp)
    im.save(out_png)
    if spec.get("masks", True):
        mk, entries = scene.element_masks(full)
        m = re.match(r"(.*)_scene_v(\d+)\.png$", out_png)
        stem = m.group(1) if m else os.path.splitext(out_png)[0]
        np.savez_compressed(stem + "_elements.npz", **mk)
        json.dump({"format": "teodor-elements/1", "image": os.path.basename(out_png), "scene": os.path.basename(path_json),
                   "size": list(full), "elements": entries}, open(stem + "_elements.json", "w"), indent=1)
    return out_png


if __name__ == "__main__":
    a = sys.argv
    render_file(a[1], a[2], int(a[3]) if len(a) > 3 else 450, int(a[4]) if len(a) > 4 else 600, a[5] if len(a) > 5 else None)
    print(a[2])
