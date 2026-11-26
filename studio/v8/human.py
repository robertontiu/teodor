"""People from a sculpted human mesh: the MakeHuman hm08 base mesh and its targets (CC0 1.0).

The primitive rig in figure.py (ellipsoids, planes and blended capsules) has a low ceiling: heads
read as uncanny, hands as gloves. This builds `person` objects from the MakeHuman 1.x base mesh
instead, a mesh sculpted on anatomical references with morph targets for sex, age, muscle, weight and
ancestry, expression unit targets, and a 163-bone skeleton with skin weights (provenance and licence:
studio/assets/LICENSES.md; fetch with tools/fetch_human.py into ~/.cache/teodor/human/).

What happens for one person:
1. Shape: the macro targets mixed the way MakeHuman's macro modifiers mix them (sex x age x muscle x
   weight, plus ancestry), then scaled to the stature for sex and age (figure.STATURE_*).
2. Face: FACS action units (figure.EXPRESSIONS) mapped to the expression unit targets (AU_TARGETS).
3. Pose: the studio's pose presets and joint overrides (figure.POSES, the same conventions as the
   primitive rig) become one rotation per bone: every segment gets a canonical frame measured on the
   rest mesh, and its posed frame is built from the joint angles exactly as figure.person builds its
   frames; reaching (IK), hand presets (figure.HANDS) and contact with surfaces likewise. Linear blend
   skinning with MakeHuman's weights.
4. Surface: skin (sex tint as figure.sex_skin), lips, nails, inside of the mouth (MPFB2 UV masks),
   brows, iris and beard zone (procedural, per pixel, in the base mesh's own coordinates), fitted
   clothing as the body's own surface (eased out along the normals for shirts and trousers), shoes.
   Hair and loose clothes (dress, shawl) are the simulated SDF parts of figure.py, wrapped around
   this body: they collide with a distance grid built from the posed mesh.
5. Output: a mesh (rasterised by scene.py with raster.py) and SDF parts, plus a proxy distance field
   that gives ambient occlusion and lets hands, hair and cloth touch the body.
"""
import math, os
import numpy as np
import figure
from figure import V, rx, ry, rz, R, nrm, jrot, hx

ASSET = os.path.expanduser("~/.cache/teodor/human/mh_hm08.npz")
ELEMENTS = ["head", "face", "neck", "torso", "arms", "hands", "legs", "feet", "drapery"]
EL = {e: i for i, e in enumerate(ELEMENTS)}
_A = None


def available():
    return os.path.exists(ASSET)


# ---------------------------------------------------------------- assets
class Assets:
    def __init__(self, path=ASSET):
        d = np.load(path)
        self.V0 = d["verts"].astype(np.float64)
        N = len(self.V0)
        self.N = N
        groups = [str(g) for g in d["groups"]]
        fg = d["face_group"]
        F = d["faces"]
        gid = lambda name: [i for i, g in enumerate(groups) if g == name]
        def faces_of(names):
            ids = [i for n in names for i in gid(n)]
            return F[np.isin(fg, ids)]
        lash = [g for g in set(groups) if "eyelashes" in g]
        self.parts = {"body": faces_of(["body"]), "eye_l": faces_of(["helper-l-eye"]), "eye_r": faces_of(["helper-r-eye"]),
                      "teeth": faces_of(["helper-upper-teeth", "helper-lower-teeth"]), "tongue": faces_of(["helper-tongue"]),
                      "lashes": faces_of(lash)}
        q = lambda Q: np.concatenate([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
        self.tris = {k: q(v) for k, v in self.parts.items()}
        self.vset = {k: np.unique(v) for k, v in self.parts.items()}
        # targets
        names = [str(n) for n in d["t_names"]]
        off, ti, td = d["t_off"], d["t_idx"], d["t_d"]
        self.targets = {n: (ti[off[i]:off[i + 1]], td[off[i]:off[i + 1]].astype(np.float64)) for i, n in enumerate(names)}
        # skeleton
        self.bones = [str(b) for b in d["bones"]]
        self.B = {b: i for i, b in enumerate(self.bones)}
        self.parent = d["bone_parent"]
        jo, ji = d["joint_off"], d["joint_idx"]
        self.joint_verts = [ji[jo[i]:jo[i + 1]] for i in range(len(jo) - 1)]
        self.bone_head, self.bone_tail = d["bone_head"], d["bone_tail"]
        # skin weights, dense: up to K bones per vertex
        wb, wv, ww = d["w_bone"].astype(np.int64), d["w_vert"].astype(np.int64), d["w_w"].astype(np.float64)
        o = np.lexsort((-ww, wv))
        wb, wv, ww = wb[o], wv[o], ww[o]
        start = np.searchsorted(wv, np.arange(N))
        rank = np.arange(len(wv)) - start[wv]
        K = 6
        keep = rank < K
        self.widx = np.zeros((N, K), np.int64)
        self.ww = np.zeros((N, K), np.float64)
        self.widx[wv[keep], rank[keep]] = wb[keep]
        self.ww[wv[keep], rank[keep]] = ww[keep]
        s = self.ww.sum(1, keepdims=True)
        self.ww = np.where(s > 0, self.ww / np.maximum(s, 1e-9), 0)
        self.ww[s[:, 0] == 0, 0] = 1.0           # unweighted vertices follow the root
        self.widx[s[:, 0] == 0, 0] = self.B["root"]
        # per-vertex sums of weight by body region (for elements and clothes)
        def region_of(b):
            if b.startswith(("spine", "pelvis", "breast", "clavicle", "shoulder")) or b == "root":
                return "torso"
            if b.startswith("neck"):
                return "neck"
            if b.startswith(("upperarm", "lowerarm")):
                return "arms"
            if b.startswith(("wrist", "finger", "metacarpal")):
                return "hands"
            if b.startswith(("upperleg", "lowerleg")):
                return "legs"
            if b.startswith(("foot", "toe")):
                return "feet"
            return "head"
        self.bone_region = [region_of(b) for b in self.bones]
        regions = ["head", "neck", "torso", "arms", "hands", "legs", "feet"]
        rid = np.array([regions.index(r) for r in self.bone_region])
        self.region_w = np.zeros((N, len(regions)))
        for k in range(K):
            np.add.at(self.region_w, (np.arange(N), rid[self.widx[:, k]]), self.ww[:, k])
        self.regions = regions
        self.side = np.sign(self.V0[:, 0])     # +1 the person's left
        self.masks = {k[5:]: d[k].astype(np.float64) for k in d.files if k.startswith("mask_")}
        # canonical eye centres (helper spheres) in base coordinates
        self.eye_c = {s: self.V0[self.vset["eye_" + s]].mean(0) for s in "lr"}
        self.eye_r = {s: float(np.linalg.norm(self.V0[self.vset["eye_" + s]] - self.eye_c[s], axis=1).mean()) for s in "lr"}
        # vertex adjacency (body), for smoothing normals into planes
        import scipy.sparse as sp
        T = self.tris["body"]
        r_ = np.concatenate([T[:, 0], T[:, 1], T[:, 2], T[:, 1], T[:, 2], T[:, 0]])
        c_ = np.concatenate([T[:, 1], T[:, 2], T[:, 0], T[:, 0], T[:, 1], T[:, 2]])
        A = sp.coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(N, N)).tocsr()
        A.data[:] = 1.0
        deg = np.asarray(A.sum(1)).ravel()
        self.adj = sp.diags(1 / np.maximum(deg, 1)) @ A
        self.provenance = str(d["provenance"])


def assets():
    global _A
    if _A is None:
        _A = Assets()
    return _A


# ---------------------------------------------------------------- shape: macro targets
def mh_age(years):
    """MakeHuman's age slider: 0 = 1 year, 0.5 = 25 years, 1 = 90 years, linear between."""
    if years < 25:
        return float(np.clip((years - 1) / 48.0, 0, 0.5))
    return float(np.clip(0.5 + (years - 25) / 130.0, 0.5, 1))


# Builds as MakeHuman muscle and weight sliders (0.5 = average). Judgement, checked against the
# waist-to-hip ratios measured on the result (docs/subjects/sex-age.md, studio note).
BUILD_MW = {"slim": (0.45, 0.3), "average": (0.5, 0.5), "sturdy": (0.6, 0.68), "heavy": (0.45, 0.92),
            "muscular": (0.92, 0.58), "frail": (0.2, 0.18)}


def macro_weights(gender, age, muscle, weight, race):
    """Target weights the way MakeHuman's macro modifiers mix them (re-implemented from the documented
    scheme: each macro variable splits into its two or three neighbouring target levels)."""
    f, m = 1 - gender, gender
    if age < 0.5:
        old = 0.0
        baby = max(0.0, 1 - age * 5.333)
        young = max(0.0, (age - 0.1875) * 3.2)
        child = max(0.0, min(1.0, 5.333 * age) - young)
    else:
        child = baby = 0.0
        old = max(0.0, age * 2 - 1)
        young = 1 - old
    lv = lambda x, lo, hi, mid: {lo: max(0.0, 1 - x * 2), hi: max(0.0, x * 2 - 1), mid: 1 - max(0.0, 1 - x * 2) - max(0.0, x * 2 - 1)}
    mus = lv(muscle, "minmuscle", "maxmuscle", "averagemuscle")
    wt = lv(weight, "minweight", "maxweight", "averageweight")
    ages = {"baby": baby, "child": child, "young": young, "old": old}
    out = {}
    for r, rw in race.items():
        for g, gw in (("female", f), ("male", m)):
            for a, aw in ages.items():
                w = rw * gw * aw
                if w > 1e-5:
                    out[f"macrodetails/{r}-{g}-{a}"] = w
    for g, gw in (("female", f), ("male", m)):
        for a, aw in ages.items():
            for mu, mw in mus.items():
                for we, ww in wt.items():
                    w = gw * aw * mw * ww
                    if w > 1e-5:
                        out[f"macrodetails/universal-{g}-{a}-{mu}-{we}"] = w
    return out


# FACS action units -> MakeHuman expression unit targets (weight per unit of the AU). The pairing
# is by the targets' anatomy (each was looked at on its own); the weights are judgement, checked on
# the expression sheet against face.md section 5 (eye opening, mouth corners, mouth opening).
AU_TARGETS = {
    "1": [("eyebrows-{s}-inner-up", 1.0)],
    "2": [("eyebrows-{s}-extern-up", 1.0)],
    "4": [("eyebrows-{s}-down", 1.0), ("nose-compression", 0.25)],
    "5": [("eye-{s}-opened-up", 1.0)],
    "6": [("eye-{s}-slit", 0.45), ("mouth-upward-retraction", 0.25)],
    "7": [("eye-{s}-slit", 0.7)],
    "9": [("nose-{s}-elevation", 1.0), ("nose-compression", 0.6), ("mouth-elevation", 0.25)],
    "10": [("mouth-elevation", 0.9)],
    "12": [("mouth-corner-puller", 1.0)],
    "15": [("mouth-depression", 1.0)],
    "17": [("mouth-eversion", 0.8)],
    "20": [("mouth-retraction", 0.9), ("neck-platysma", 0.6)],
    "23": [("mouth-compression", 0.6)],
    "25": [("mouth-parling", 0.8)],
    "26": [("mouth-open", 0.8)],
    "27": [("mouth-open", 0.45), ("mouth-part-later", 0.6)],
    "41": [("eye-{s}-closure", 0.3)],
    "43": [("eye-{s}-closure", 1.0)],
    "45": [("eye-{s}-closure", 1.0)],
}


def expression_weights(au, race):
    out = {}
    for k, v in au.items():
        if v <= 0 or k not in AU_TARGETS:
            continue
        for name, w in AU_TARGETS[k]:
            for s in (("left", "right") if "{s}" in name else (None,)):
                n = name.format(s=s) if s else name
                for r, rw in race.items():
                    key = f"expression/units/{r}/{n}"
                    out[key] = out.get(key, 0.0) + v * w * rw
    # the mouth targets overlap (each moves the same lips): an open jaw already parts the lips and
    # stretches them, so the others give way to it, or the lips tear and the mouth's inside shows
    # through (judgement, by eye on the scream and the laugh)
    for r in race:
        k = lambda n: f"expression/units/{r}/{n}"
        op = min(out.get(k("mouth-open"), 0.0), 1.0)
        for n, f in (("mouth-parling", 1.0), ("mouth-retraction", 0.55), ("mouth-part-later", 0.5), ("mouth-elevation", 0.5),
                     ("mouth-corner-puller", 0.3)):
            if k(n) in out:
                out[k(n)] *= 1 - f * op
    # a unit target is a full movement: past 1 it caricatures
    return {k: min(v, 1.0) for k, v in out.items()}


def morph(A, weights):
    Vm = A.V0.copy()
    for n, w in weights.items():
        if n in A.targets and w:
            i, dl = A.targets[n]
            Vm[i] += w * dl
    return Vm


def joints_of(A, Vm):
    return np.stack([Vm[j].mean(0) for j in A.joint_verts])


# ---------------------------------------------------------------- pose
def _frame(y, zhint):
    """Columns x, y, z with y given and z as close to zhint as possible (x = y cross z)."""
    y = nrm(np.asarray(y, np.float64))
    z = np.asarray(zhint, np.float64)
    z = z - (z @ y) * y
    if np.linalg.norm(z) < 1e-6:
        z = np.array([0, 0, 1.0]) - y[2] * y
    z = nrm(z)
    return np.stack([np.cross(y, z), y, z], 1)


def _rmin(a, b):
    """The smallest rotation taking direction a to b."""
    a, b = nrm(np.asarray(a, np.float64)), nrm(np.asarray(b, np.float64))
    v = np.cross(a, b)
    c = float(a @ b)
    if c < -0.9999:
        ax = nrm(np.cross(a, [1, 0, 0]) if abs(a[0]) < 0.9 else np.cross(a, [0, 1, 0]))
        return _axang(ax, math.pi)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)


def _axang(ax, a):
    ax = nrm(np.asarray(ax, np.float64))
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K


def _twist(Rm, axis):
    """Angle of the twist of rotation Rm about axis (swing-twist decomposition)."""
    q = _quat(Rm)
    p = (q[1:] @ axis) * axis
    return 2 * math.atan2(float(np.linalg.norm(p)) * np.sign(q[1:] @ axis), q[0])


def _quat(M):
    t = np.trace(M)
    if t > 0:
        s = math.sqrt(t + 1) * 2
        return np.array([0.25 * s, (M[2, 1] - M[1, 2]) / s, (M[0, 2] - M[2, 0]) / s, (M[1, 0] - M[0, 1]) / s])
    i = int(np.argmax(np.diag(M)))
    j, k = (i + 1) % 3, (i + 2) % 3
    s = math.sqrt(1 + M[i, i] - M[j, j] - M[k, k]) * 2
    q = np.zeros(4)
    q[0] = (M[k, j] - M[j, k]) / s
    q[1 + i] = 0.25 * s
    q[1 + j] = (M[j, i] + M[i, j]) / s
    q[1 + k] = (M[k, i] + M[i, k]) / s
    return q


def _slerp_rot(A_, B_, t):
    Q = A_.T @ B_
    q = _quat(Q)
    ang = 2 * math.acos(float(np.clip(abs(q[0]), 0, 1)))
    if ang < 1e-6:
        return A_
    ax = q[1:] * np.sign(q[0])
    return A_ @ _axang(ax, ang * t)


FINGERS = {2: 0, 3: 1, 4: 2, 5: 3}          # MakeHuman finger number -> figure.HANDS finger (index..little)


class Rig:
    """The rest skeleton of one person (after shape targets and scaling) with canonical frames."""

    def __init__(self, A, Vr):
        self.A = A
        Jp = joints_of(A, Vr)
        self.head = Jp[A.bone_head]
        self.tail = Jp[A.bone_tail]
        b = A.B
        H, T = self.head, self.tail
        self.C = {}
        self.elb0 = {}
        for s in "LR":
            side = 1 if s == "L" else -1
            sh, el, wr = H[b[f"upperarm01.{s}"]], H[b[f"lowerarm01.{s}"]], H[b[f"wrist.{s}"]]
            du, df = nrm(el - sh), nrm(wr - el)
            self.C[f"upper_{s}"] = _frame(-du, df)
            self.elb0[s] = math.acos(float(np.clip(du @ df, -1, 1)))
            self.C[f"fore_{s}"] = self.C[f"upper_{s}"] @ rx(-self.elb0[s]).astype(np.float64)
            hp, kn, an = H[b[f"upperleg01.{s}"]], H[b[f"lowerleg01.{s}"]], H[b[f"foot.{s}"]]
            self.C[f"thigh_{s}"] = _frame(-nrm(kn - hp), [0, 0, 1])
            self.C[f"shin_{s}"] = _frame(-nrm(an - kn), [0, 0, 1])
            # the hand: fingers along -y, the palm facing +z, the thumb toward +x on the left hand
            kn_ = [H[b[f"finger{f}-1.{s}"]] for f in (2, 3, 4, 5)]
            fd = nrm(np.mean(kn_, 0) - wr)
            thumbward = nrm(kn_[0] - kn_[3])
            z = nrm(np.cross(thumbward, fd))
            C = _frame(-fd, z)
            if (C[:, 0] @ thumbward) * side < 0:
                C = _frame(-fd, -z)
            self.C[f"hand_{s}"] = C
            self.hand_len = float(np.linalg.norm(T[b[f"finger3-3.{s}"]] - wr))
        # head frame: rest is upright
        self.L1 = float(np.linalg.norm(H[b["lowerarm01.L"]] - H[b["upperarm01.L"]]))
        self.L2 = float(np.linalg.norm(H[b["wrist.L"]] - H[b["lowerarm01.L"]]))


def desired_frames(pose, o, rig, body):
    """World rotations (before lean) for every segment the pose controls: figure.person's frames."""
    G = lambda k, n=3: (list(pose.get(k, [])) + [0] * n)[:n]
    lie = pose.get("lie")
    pitch, roll = figure.LIE.get(lie, (0, 0)) if lie else (0, 0)
    pitch += o.get("pitch", 0); roll += o.get("roll", 0)
    Mroot = (ry(R(o.get("facing", 0))) @ rx(R(pitch)) @ rz(R(roll))).astype(np.float64)
    F = {}
    Rp = Mroot @ jrot(G("pelvis"))
    sp = G("spine")
    half = [a / 2 for a in sp]
    Rl = Rp @ jrot(half)
    Rc = Rl @ jrot(half)
    nk = G("neck")
    Rn = Rc @ jrot(nk)
    Rh = Rn @ jrot(G("head"))
    F.update(Rp=Rp, Rl=Rl, Rc=Rc, Rn=Rn, Rh=Rh, Mroot=Mroot)
    F["spine05"] = Rp @ jrot([a / 3 for a in half])
    F["spine04"] = Rp @ jrot([a * 2 / 3 for a in half])
    F["spine03"] = Rl
    F["spine02"] = Rl @ jrot([a / 2 for a in half])
    F["spine01"] = Rc
    F["neck01"] = Rc @ jrot([a / 3 for a in nk])
    F["neck02"] = Rc @ jrot([a * 2 / 3 for a in nk])
    F["neck03"] = Rn
    F["head"] = Rh
    for s, side in (("L", 1), ("R", -1)):
        sl = s.lower()
        fwd, out, tw, knee = G(f"leg_{sl}", 4)
        Rt = Rp @ rz(R(side * out)) @ rx(-R(fwd)) @ ry(R(side * tw))
        Rs = Rt @ rx(R(knee))
        Rf = Rs @ rx(-R(G(f"ankle_{sl}", 1)[0]))
        F[f"thigh_{s}"], F[f"shin_{s}"], F[f"foot_{s}"] = Rt, Rs, Rf
        rs_, fs_ = G(f"shoulder_{sl}", 2)
        lc = 0.095 * body.S / 1.7
        F[f"clav_{s}"] = Rc @ rz(R(side * math.degrees(math.atan2(0.06 * body.u * rs_, lc)))) @ ry(-R(side * math.degrees(math.atan2(0.08 * body.u * fs_, lc))))
        fwd, out, tw, elb = G(f"arm_{sl}", 4)
        Ru = Rc @ rz(R(side * out)) @ rx(-R(fwd)) @ ry(R(side * tw))
        Rfa = Ru @ rx(-R(elb))
        fl, dev, pron = G(f"wrist_{sl}", 3)
        hp = pose.get(f"hand_{sl}", "relaxed")
        hpd = figure.HANDS.get(hp, {}) if isinstance(hp, str) else hp
        wf_, wd_ = (list(hpd.get("wrist", [0, 0])) + [0, 0])[:2]
        Mh = Rfa @ ry(-R(side * (pron if f"wrist_{sl}" in pose else 80))) @ rx(-R(fl + wf_)) @ rz(R(side * (dev + wd_)))
        F[f"upper_{s}"], F[f"fore_{s}"], F[f"hand_{s}"] = Ru, Rfa, Mh
    return F


def bone_rotations(rig, F, hands):
    """Per-bone world rotations W (rest -> posed, about each bone's head) from the frames F."""
    A = rig.A
    nb = len(A.bones)
    W = [None] * nb
    C = rig.C
    I3 = np.eye(3)
    fixed = {}
    for k in ("spine05", "spine04", "spine03", "spine02", "spine01", "neck01", "neck02", "neck03", "head"):
        fixed[k] = F[k]
    fixed["root"] = F["Rp"]
    for s in "LR":
        fixed[f"pelvis.{s}"] = F["Rp"]
        Wt = F[f"thigh_{s}"] @ C[f"thigh_{s}"].T
        fixed[f"upperleg01.{s}"] = fixed[f"upperleg02.{s}"] = Wt
        Ws = F[f"shin_{s}"] @ C[f"shin_{s}"].T
        fixed[f"lowerleg01.{s}"] = fixed[f"lowerleg02.{s}"] = Ws
        fixed[f"foot.{s}"] = F[f"foot_{s}"] @ C[f"shin_{s}"].T
        fixed[f"clavicle.{s}"] = F[f"clav_{s}"]
        Wu = F[f"upper_{s}"] @ C[f"upper_{s}"].T
        Wf = F[f"fore_{s}"] @ C[f"fore_{s}"].T
        Wh = F[f"hand_{s}"] @ C[f"hand_{s}"].T
        fixed[f"shoulder01.{s}"] = _slerp_rot(F[f"clav_{s}"], Wu, 0.3)     # the deltoid's cap goes partly with the arm (judgement)
        fixed[f"upperarm01.{s}"] = fixed[f"upperarm02.{s}"] = Wu
        fixed[f"lowerarm01.{s}"] = Wf
        ax = nrm(rig.head[A.B[f"wrist.{s}"]] - rig.head[A.B[f"lowerarm01.{s}"]])
        tw = _twist(Wf.T @ Wh, ax)
        fixed[f"lowerarm02.{s}"] = Wf @ _axang(ax, tw * 0.6)                # the forearm's twist carries most of the pronation
        fixed[f"wrist.{s}"] = Wh
        for k in range(1, 5):
            fixed[f"metacarpal{k}.{s}"] = Wh
        hd = hands[s]
        fixed.update(finger_rotations(rig, s, Wh, F[f"hand_{s}"], hd))
    gz = hands.get("gaze")
    for i, b in enumerate(A.bones):
        p = A.parent[i]
        if b in fixed:
            W[i] = fixed[b]
        elif b.startswith("eye.") and gz is not None:
            W[i] = W[p] @ (ry(R(gz[0])) @ rx(-R(gz[1]))).astype(np.float64)
        else:
            W[i] = W[p] if p >= 0 else I3
    return np.stack(W)


def hand_spec(preset, extra=None):
    h = dict(figure.HANDS.get(preset, figure.HANDS["relaxed"])) if isinstance(preset, str) else dict(figure.HANDS["relaxed"], **preset)
    if extra:
        h.update(extra)
    return h


def finger_dirs(rig, s, h, flex_override=None):
    """Desired directions of each finger segment in the hand's canonical frame (local), from a preset:
    the conventions of figure.hand_prims (flexion about the hand's x, spread in the palm's plane)."""
    side = 1 if s == "L" else -1
    A, b = rig.A, rig.A.B
    out = {}
    Ch = rig.C[f"hand_{s}"]
    flex = flex_override or h["f"]
    sp = h.get("spread", 6)
    for f, fi in FINGERS.items():
        sw = figure.FING[fi][5]
        r1 = Ch.T @ nrm(rig.tail[b[f"finger{f}-1.{s}"]] - rig.head[b[f"finger{f}-1.{s}"]])
        psi = math.atan2(-r1[0], -r1[1])          # the finger's own fan in the palm plane at rest (local x vs -y)
        base = rz(R(side * sp * sw * 0.8) + psi * 0.7)
        cum = 0.0
        for j in range(3):
            cum += flex[fi][j]
            out[(f, j + 1)] = (base @ rx(-R(cum)) @ V(0, -1, 0)).astype(np.float64)
    t_out, t_palm, t_opp, t_mcp, t_ip = h["thumb"]
    # the thumb as figure.hand_prims sets it: out from the fingers' line in the palm's plane, toward
    # the palm, and turned about its own axis so it flexes across the palm (opposition)
    Rt = rz(R(side * t_out)) @ rx(-R(t_palm * 0.7)) @ ry(-R(side * (t_opp + 45)))
    cum = 0.0
    for j, a in enumerate((0, t_mcp, t_ip)):
        cum += a
        out[(1, j + 1)] = (Rt @ rx(-R(cum)) @ V(0, -1, 0)).astype(np.float64)
    return out


def finger_rotations(rig, s, Wh, Mh, h):
    A, b = rig.A, rig.A.B
    Ch = rig.C[f"hand_{s}"]
    dirs = h.get("_dirs") or finger_dirs(rig, s, h)
    out = {}
    for (f, j), Dl in dirs.items():
        nm = f"finger{f}-{j}.{s}"
        r = nrm(rig.tail[b[nm]] - rig.head[b[nm]])
        out[nm] = Wh @ _rmin(r, Ch @ Dl)
    return out


def forward_kinematics(rig, W):
    A = rig.A
    P = np.zeros_like(rig.head)
    for i in range(len(A.bones)):
        p = A.parent[i]
        if p < 0:
            P[i] = rig.head[i]
        else:
            P[i] = P[p] + W[p] @ (rig.head[i] - rig.head[p])
    return P


def skin(A, Vr, rig, W, P):
    """Linear blend skinning: each vertex moved by its bones' transforms, weighted."""
    out = np.zeros_like(Vr)
    for k in range(A.widx.shape[1]):
        bi = A.widx[:, k]
        w = A.ww[:, k]
        m = w > 0
        if not m.any():
            continue
        bb = bi[m]
        rel = Vr[m] - rig.head[bb]
        out[m] += w[m, None] * (np.einsum("nij,nj->ni", W[bb], rel) + P[bb])
    return out


def vertex_normals(Vp, T):
    fn = np.cross(Vp[T[:, 1]] - Vp[T[:, 0]], Vp[T[:, 2]] - Vp[T[:, 0]])
    n = np.zeros_like(Vp)
    for k in range(3):
        np.add.at(n, T[:, k], fn)
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)


# ---------------------------------------------------------------- a distance field of the posed mesh
class GridSDF:
    """Signed distance to a closed mesh, sampled on a voxel grid (inside < 0). Built by marking the
    voxels the surface passes through, filling the enclosed volume and taking Euclidean distance
    transforms; near the surface (a band of a few voxels) the distance is replaced by the distance to
    dense samples of the triangles (a k-d tree), so the field is accurate to about a millimetre there.
    `smooth` evaluates it with cubic B-splines (smooth normals for hair resting on it); otherwise
    trilinear."""

    def __init__(self, Vp, T, voxel=0.01, pad=0.06, box=None, lid=False, smooth=False):
        from scipy import ndimage
        from scipy.spatial import cKDTree
        lo = Vp.min(0) - pad if box is None else np.asarray(box[0], np.float64)
        hi = Vp.max(0) + pad if box is None else np.asarray(box[1], np.float64)
        dims = np.ceil((hi - lo) / voxel).astype(int) + 1
        self.lo, self.vox, self.dims = lo, voxel, dims
        A_, B_, C_ = Vp[T[:, 0]], Vp[T[:, 1]], Vp[T[:, 2]]
        L = np.maximum.reduce([np.linalg.norm(B_ - A_, axis=1), np.linalg.norm(C_ - A_, axis=1), np.linalg.norm(C_ - B_, axis=1)])
        spacing = min(0.5 * voxel, 0.0025)
        n = np.clip(np.ceil(L / spacing).astype(int), 1, 64)
        shell = np.zeros(dims, bool)
        samples = []
        for k in np.unique(n):
            sel = n == k
            u, v = np.meshgrid(np.arange(k + 1), np.arange(k + 1), indexing="ij")
            keep = (u + v) <= k
            u, v = u[keep] / k, v[keep] / k
            pts = (A_[sel][:, None] + u[None, :, None] * (B_[sel] - A_[sel])[:, None] + v[None, :, None] * (C_[sel] - A_[sel])[:, None]).reshape(-1, 3)
            samples.append(pts)
            ijk = np.floor((pts - lo) / voxel + 0.5).astype(int)
            ok = np.all((ijk >= 0) & (ijk < dims), 1)
            ijk = ijk[ok]
            shell[ijk[:, 0], ijk[:, 1], ijk[:, 2]] = True
        if lid:          # a mesh cut off at the bottom of the box (a head without its body): close it there
            shell[:, 0, :] |= ndimage.binary_fill_holes(shell[:, 0:3, :].any(1))
        occ = ndimage.binary_fill_holes(shell)
        d_out = ndimage.distance_transform_edt(~occ) * voxel
        d_in = ndimage.distance_transform_edt(occ) * voxel
        g = np.where(occ, -d_in, d_out)
        band = np.abs(g) < 3.5 * voxel
        ii = np.nonzero(band)
        cen = lo + np.stack(ii, 1) * voxel
        P = np.concatenate(samples)
        P = P[np.all((P > lo - 4 * voxel) & (P < hi + 4 * voxel), 1)]
        dd, _ = cKDTree(P).query(cen, workers=-1)
        g[ii] = np.where(occ[ii], -dd, dd)
        self.g = g.astype(np.float32)
        self.smooth = smooth
        if smooth:
            # the samples leave millimetre ripples in the band: a light blur, then cubic splines
            self.g = ndimage.gaussian_filter(self.g, float(smooth) if not isinstance(smooth, bool) else 1.0).astype(np.float32)
            self.coef = ndimage.spline_filter(self.g, order=3, mode="nearest")
        self.hi = lo + (dims - 1) * voxel
        self.c = (lo + self.hi) / 2
        self.r = float(np.linalg.norm(self.hi - lo) / 2)

    def __call__(self, p):
        from scipy.ndimage import map_coordinates
        p = np.asarray(p, np.float64)
        q = (p - self.lo) / self.vox
        qc = np.clip(q, 0, self.dims - 1)
        if self.smooth:
            d = map_coordinates(self.coef, qc.T, order=3, mode="nearest", prefilter=False)
        else:
            d = map_coordinates(self.g, qc.T, order=1, mode="nearest")
        out = np.linalg.norm((q - qc) * self.vox, axis=1)       # outside the box: add the distance to it
        return (d + out).astype(np.float32)


# ---------------------------------------------------------------- colours
def _mix(a, b, t):
    t = np.asarray(t, np.float64)
    return a * (1 - t[..., None]) + b * t[..., None] if np.ndim(t) else a * (1 - t) + b * t


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


class Look:
    """Per-pixel detail evaluated in the base mesh's own coordinates (the same for every shape and
    pose): iris and pupil on the eyeballs, the brows, the beard zone. Values in meters of the base mesh."""

    def __init__(self, A, body, o, skin_c):
        self.A = A
        fem, child, old = float(np.clip(body.fs, 0, 1)), body.child, body.old
        self.eye_c, self.eye_r = A.eye_c, A.eye_r
        self.iris = hx(o.get("iris", "#4a3424"))
        self.sclera = hx(o.get("sclera", "#cfc6bb"))
        hd = o.get("hair")
        hcol = (hd if isinstance(hd, str) else hd.get("color")) if hd else None
        bc = hx(o.get("brows", hcol or "#3a2a20"))
        if "brows" not in o and hcol:
            bc = bc + (hx("#b8b4ac") - bc) * 0.5 * figure.lerp_table(figure.GREY, body.age)
        self.brow_col = bc
        # brows: a thinner, higher arch in women; heavier, lower and straighter in men (face.md section 9;
        # sex-age.md section 1); in children faint. Shapes in base-mesh meters, judgement.
        self.brow_lift = 0.0025 * (fem - 0.5) * 2 * (1 - child)
        self.brow_th = (0.0065 - 0.0025 * fem) * (1 - 0.35 * child)
        self.brow_amt = (0.85 - 0.1 * fem) * (1 - 0.55 * child) * (1 - 0.25 * old)
        self.arch = 0.002 + 0.002 * fem
        beard = float(o.get("beard", 0.35 * float(np.clip((body.age - 17) / 6, 0, 1)) if body.fs < 0.5 else 0.0))
        self.beard = beard
        self.beard_col = hx(o.get("beard_color", "#000000")) if "beard_color" in o else bc
        self.skin = skin_c
        # Russell's facial contrast: a woman's eyes stand darker off her skin (measured on the sheet's
        # frontal heads: face.md section 9, studio note); width and strength are judgement
        self.lash = 0.5 + 0.45 * fem - 0.15 * old
        self.lash_w = 0.0026 + 0.0022 * fem * (1 - child)
        self.lash_col = np.array([0.08, 0.055, 0.045]) * (1 - fem) + np.array([0.045, 0.03, 0.025]) * fem

    def eye(self, prest, side_l):
        """Sclera, iris with a darker limbal ring, pupil, by the angle from the eye's axis (+z)."""
        c = np.where(side_l[:, None], self.eye_c["l"][None], self.eye_c["r"][None])
        d = nrm(prest - c)
        ang = np.degrees(np.arccos(np.clip(d[:, 2], -1, 1)))
        # the iris is 11.7 mm across and the pupil about 3.5 mm in ordinary light; as angles on this
        # eyeball (the helper sphere, about 15.5 mm in radius in the base mesh)
        r = 0.5 * (self.eye_r["l"] + self.eye_r["r"])
        ai, ap = math.degrees(math.asin(5.85e-3 / r)), math.degrees(math.asin(1.75e-3 / r))
        col = np.tile(self.sclera, (len(prest), 1))
        col = col * (1 - 0.18 * smoothstep(1.4 * ai, 2.6 * ai, ang))[:, None]      # the sclera shades toward the corners
        ir = smoothstep(ai + 0.8, ai - 0.8, ang)
        ring = smoothstep(0.75 * ai, 0.97 * ai, ang) * 0.45                       # limbal ring
        irc = self.iris[None] * (1 - ring[:, None]) * (0.85 + 0.25 * smoothstep(ap, 0.8 * ai, ang))[:, None]
        col = _mix(col, irc, ir)
        col = _mix(col, np.array([0.03, 0.025, 0.025]), smoothstep(ap + 0.6, ap - 0.6, ang))
        return col

    def brows(self, prest, col):
        x = np.abs(prest[:, 0])
        y, z = prest[:, 1], prest[:, 2]
        # base mesh: eye centre x 0.031, y 0.728; brows from x 0.012 to 0.058
        t = np.clip((x - 0.012) / 0.046, 0, 1)
        yb = 0.7415 + self.brow_lift + self.arch * np.sin(np.pi * np.clip(t * 1.15, 0, 1)) - 0.004 * t * t
        th = self.brow_th * (1.15 - 0.6 * t)
        m = smoothstep(th * 0.5 + 0.0012, th * 0.5 - 0.0008, np.abs(y - yb)) * smoothstep(0.009, 0.013, x) * smoothstep(0.062, 0.055, x)
        m = m * (z > 0.1) * self.brow_amt
        # the hairs: thinning toward the tail, a little uneven, not a painted band
        m = m * (1 - 0.35 * t) * (0.88 + 0.12 * np.sin(x * 900 + 2.0) * np.sin(y * 1300))
        return _mix(col, self.brow_col[None], m)

    def lash_line(self, prest, col):
        """The lid margins darken where the lashes root (darker in women: Russell's facial contrast):
        a band just outside the eyeball, stronger on the upper lid and toward the outer corner."""
        out = col
        for s in "lr":
            c, r = self.eye_c[s], self.eye_r[s]
            d = np.linalg.norm(prest - c, axis=1) - r
            q = prest - c
            front = smoothstep(0.2, 0.6, q[:, 2] / (np.linalg.norm(q, axis=1) + 1e-9))
            upper = q[:, 1] > -0.001
            outer = np.clip((np.abs(prest[:, 0]) - abs(c[0])) / 0.012 + 0.5, 0, 1)
            w_ = np.where(upper, 0.9 + 0.2 * outer, 0.45 + 0.15 * outer) * self.lash
            m = smoothstep(self.lash_w, 0.0008, d) * front * w_
            out = _mix(out, self.lash_col[None], m)
        return out

    def beard_zone(self, prest, col):
        if self.beard <= 0:
            return col
        x, y, z = np.abs(prest[:, 0]), prest[:, 1], prest[:, 2]
        # under the nose and the cheekbones, down to under the jaw (base mesh: nose base y ~0.70, chin ~0.62)
        top = 0.705 - 0.035 * np.clip((x - 0.02) / 0.05, 0, 1)
        m = smoothstep(top + 0.004, top - 0.006, y) * smoothstep(0.585, 0.605, y) * smoothstep(0.02, 0.05, z + 0.02 - 0.0 * x)
        m = m * smoothstep(0.075, 0.06, x)
        b = self.beard
        if b <= 0.6:
            tint = self.skin * np.array([0.82, 0.86, 0.92])                    # a cool shaved shadow
            return _mix(col, tint[None], m * b / 0.6 * 0.55)
        return _mix(col, self.beard_col[None], m * min((b - 0.6) / 0.4, 1.0) * 0.9)


# ---------------------------------------------------------------- the person
def person(o):
    """Build a person from a scene object. Returns (mesh, sdf_parts, J): mesh is a dict for the
    rasteriser, sdf_parts figure.py-style part dicts (hair, dress, shawl and the body's proxy)."""
    A = assets()
    body = figure.Body(o)
    pose = {}
    base = o.get("pose", "stand")
    for nm in ([base] if isinstance(base, str) else base):
        pose.update(figure.POSES.get(nm, {}))
    pose.update(o.get("joints", {}))
    for k in ("reach_l", "reach_r", "hand_l", "hand_r", "lean", "lie"):
        if k in o:
            pose[k] = o[k]
    if body.old > 0 and "spine" not in o.get("joints", {}):
        sp = list(pose.get("spine", [0, 0, 0])) + [0, 0, 0]
        pose["spine"] = [sp[0] + 10 * body.old, sp[1], sp[2]]
        nk = list(pose.get("neck", [0, 0, 0])) + [0, 0, 0]
        pose["neck"] = [nk[0] - 6 * body.old, nk[1], nk[2]]

    # ---------- shape
    gender = float(np.clip(1 - body.fs, 0, 1))
    mus, wt = BUILD_MW.get(o.get("build", "average"), BUILD_MW["average"])
    mus = float(o.get("muscle", mus)); wt = float(o.get("weight", wt))
    race = o.get("ancestry", {"african": 1 / 3, "asian": 1 / 3, "caucasian": 1 / 3})
    tot = sum(race.values()) or 1
    race = {k: v / tot for k, v in race.items() if k in ("african", "asian", "caucasian")}
    w = macro_weights(gender, mh_age(body.age), mus, wt, race)
    au = figure.au_of(o.get("expression", "neutral"))
    w.update({k: w.get(k, 0) + v for k, v in expression_weights(au, race).items()})
    cl_ = o.get("clothes", [])
    cl_ = [cl_] if isinstance(cl_, dict) else cl_
    if "torso" not in set(o.get("bare", [])) or any(c.get("kind") in ("shirt", "dress") for c in cl_):
        # clothed: cloth smooths the nipples away and rounds the breast (MakeHuman's own breast targets)
        w.update({"breast/nipple-point-decr": 0.5 * float(np.clip(body.fs, 0, 1)), "breast/breast-point-decr": 0.5 * float(np.clip(body.fs, 0, 1))})
        # (on a man's chest the targets fold the mesh; the garment's smoothing is enough there)
    Vm = morph(A, w)
    bodyv = A.vset["body"]
    y0, y1 = Vm[bodyv, 1].min(), Vm[bodyv, 1].max()
    scale = body.S / (y1 - y0)
    Vr = (Vm - np.array([0, y0, 0])) * scale
    rig = Rig(A, Vr)

    # head measures (rest): crown, chin, the head frame's origin at mid height over the ear
    headv = np.nonzero((A.region_w[:, 0] > 0.5) & np.isin(np.arange(A.N), bodyv))[0]
    crown = Vr[headv, 1].max()
    front = headv[Vr[headv, 2] > np.percentile(Vr[headv, 2], 60)]
    chin = Vr[front, 1].min()
    Hh = crown - chin
    ear = headv[(np.abs(Vr[headv, 0]) > np.percentile(np.abs(Vr[headv, 0]), 97))]
    O_rest = np.array([0, (crown + chin) / 2, float(Vr[ear, 2].mean())])
    eye_rest = (rig.head[A.B["eye.L"]] + rig.head[A.B["eye.R"]]) / 2

    # ---------- pose: frames -> bone rotations -> positions
    hands = {}
    for s in "LR":
        sl = s.lower()
        hp = pose.get(f"hand_{sl}", (pose.get(f"reach_{sl}") or {}).get("hand", "relaxed"))
        hands[s] = hand_spec(hp)
        hands[s]["_preset"] = hp if isinstance(hp, str) else ""
    hands["gaze"] = o.get("gaze")
    F = desired_frames(pose, o, rig, body)

    def solve(F):
        W = bone_rotations(rig, F, hands)
        P = forward_kinematics(rig, W)
        return W, P

    W, P = solve(F)
    lean = pose.get("lean", [0, 0])
    if isinstance(lean, (int, float)):
        lean = [lean, 0]
    feet_mid = (P[A.B["foot.L"]] + P[A.B["foot.R"]]) / 2
    fc = ry(R(o.get("facing", 0))).astype(np.float64)
    Mlean = fc @ rx(R(lean[0])) @ rz(-R(lean[1])) @ fc.T

    def place(W, P, shift):
        W2 = np.einsum("ij,njk->nik", Mlean, W)
        P2 = feet_mid + (P - feet_mid) @ Mlean.T + shift
        return W2, P2

    W1, P1 = place(W, P, np.zeros(3))
    Vp = skin(A, Vr, rig, W1, P1)
    world_pos = np.asarray(o.get("pos", [0, 0, 0]), np.float64)
    anchor = o.get("anchor", "ground")
    reaching = [s for s in "lr" if f"reach_{s}" in pose]
    if anchor == "ground":
        gy = o.get("_ground_y", 0.0)
        ok = np.isin(np.arange(A.N), bodyv)
        for s in reaching:
            side = 1 if s == "l" else -1
            ok &= ~(((A.region_w[:, 3] + A.region_w[:, 4]) > 0.3) & (A.side == side))
        shift = world_pos.copy()
        shift[1] = gy - Vp[ok, 1].min() + (world_pos[1] if o.get("float") else 0)
    else:
        if anchor == "pelvis":
            ref = (P1[A.B["upperleg01.L"]] + P1[A.B["upperleg01.R"]]) / 2
        elif anchor == "head":
            ref = P1[A.B["head"]] + W1[A.B["head"]] @ (O_rest - rig.head[A.B["head"]])
        else:
            ref = P1[A.B["spine01"]]
        shift = world_pos - ref
    W1, P1 = place(W, P, shift)

    def J_of(W1, P1):
        J = {}
        hb = A.B["head"]
        J["head"] = P1[hb] + W1[hb] @ (O_rest - rig.head[hb])
        J["Rhead"] = W1[hb]
        J["Rpelvis"] = W1[A.B["root"]]
        J["Rlumbar"] = W1[A.B["spine03"]]
        J["Rchest"] = W1[A.B["spine01"]]
        J["pelvis"] = (P1[A.B["upperleg01.L"]] + P1[A.B["upperleg01.R"]]) / 2
        J["neckb"] = P1[A.B["neck01"]]
        J["atlas"] = P1[hb]
        J["lumbar"] = P1[A.B["spine03"]]
        J["waist"] = P1[A.B["spine04"]] + W1[A.B["spine04"]] @ (V(0, 0.02, 0) * body.S / 1.7)
        J["chest"] = J["neckb"] - J["Rchest"] @ V(0, 1.08 * body.tf * body.u, -0.1 * body.u)
        for s in "LR":
            sl = s.lower()
            J[f"sh_{sl}"] = P1[A.B[f"upperarm01.{s}"]]
            J[f"el_{sl}"] = P1[A.B[f"lowerarm01.{s}"]]
            J[f"wr_{sl}"] = P1[A.B[f"wrist.{s}"]]
            J[f"hip_{sl}"] = P1[A.B[f"upperleg01.{s}"]]
            J[f"kn_{sl}"] = P1[A.B[f"lowerleg01.{s}"]]
            J[f"an_{sl}"] = P1[A.B[f"foot.{s}"]]
            fb = A.B[f"foot.{s}"]
            J[f"ft_{sl}"] = P1[fb] + W1[fb] @ (rig.tail[fb] - rig.head[fb]) * 2.5
            J[f"Rhand_{sl}"] = W1[A.B[f"wrist.{s}"]] @ rig.C[f"hand_{s}"]
        return J

    J = J_of(W1, P1)
    u = body.u
    hc_, Rh_ = J["head"], J["Rhead"]
    hu = Hh                        # the mesh's head height stands for the head unit here

    def landmark(name):
        Rc = J["Rchest"]
        table = {"head_top": hc_ + Rh_ @ V(0, 0.5 * hu, -0.05 * hu), "head_back": hc_ + Rh_ @ V(0, 0.15 * hu, -0.5 * hu),
                 "forehead": hc_ + Rh_ @ V(0, 0.25 * hu, 0.42 * hu), "chest": J["chest"] + Rc @ V(0, 0.6 * u, 0.5 * u),
                 "nape": hc_ + Rh_ @ V(0, -0.3 * hu, -0.4 * hu), "belly": J["lumbar"] + J["Rlumbar"] @ V(0, 0.2 * u, 0.5 * u),
                 "hip_l": J["hip_l"] + J["Rpelvis"] @ V(0.4 * u, 0, 0), "hip_r": J["hip_r"] + J["Rpelvis"] @ V(-0.4 * u, 0, 0),
                 "knee_l": J["kn_l"], "knee_r": J["kn_r"], "cheek_l": hc_ + Rh_ @ V(0.3 * hu, -0.15 * hu, 0.2 * hu),
                 "cheek_r": hc_ + Rh_ @ V(-0.3 * hu, -0.15 * hu, 0.2 * hu)}
        return table[name]
    J["landmark"] = landmark

    # ---------- reaching (IK) and contact
    ext = o.get("_collide")
    hand_len = rig.hand_len
    Vp = skin(A, Vr, rig, W1, P1)
    arms_hands = (A.region_w[:, 3] + A.region_w[:, 4]) > 0.5
    torso_ok = np.isin(np.arange(A.N), bodyv) & ~arms_hands
    Tb = A.tris["body"]
    Tself = Tb[torso_ok[Tb].all(1)]
    self_grid = None

    def touch(p):
        nonlocal self_grid
        if self_grid is None:
            self_grid = GridSDF(Vp, Tself, voxel=0.012)
        d = self_grid(p)
        if ext is not None:
            d = np.minimum(d, ext(np.asarray(p, np.float32)))
        return d

    targets = {}
    for s in "lr":
        reach = pose.get(f"reach_{s}")
        if not reach:
            continue
        tgt = reach.get("target", [0, 0, 0])
        T_ = landmark(tgt) if isinstance(tgt, str) else np.asarray(tgt, np.float64)
        T_ = T_ + np.asarray(reach.get("offset", [0, 0, 0]), np.float64)
        palm = nrm(reach.get("palm", [0, -1, 0]))
        sh = J[f"sh_{s}"]
        fingers = reach.get("fingers")
        fdir = nrm(fingers) if fingers is not None else nrm(T_ - sh)
        fdir = nrm(fdir - (fdir @ palm) * palm)
        wr = T_ - fdir * hand_len * 0.42 - palm * 0.05 * hand_len
        Mh = np.stack([np.cross(-fdir, palm), -fdir, palm], 1)
        targets[s] = (wr, Mh, reach)
    # every hand: a palm inside something is pushed out; a reaching hand that rests settles onto what is under it
    if True:
        for s in "lr":
            S_ = s.upper()
            if s in targets:
                wr, Mh, reach = targets[s]
            else:
                wr, Mh, reach = J[f"wr_{s}"].copy(), Mlean @ F[f"hand_{S_}"], None
            pc = wr + Mh @ (V(0, -0.3, 0.075) * hand_len)
            hp_ = hands[S_].get("_preset", "")
            moved = False
            if reach is not None and hp_ in ("rest", "hold", "cup", "grip") and reach.get("settle", True):
                pn = nrm(Mh @ V(0, 0, 1))
                ts = np.linspace(0, 0.06, 25)
                dd = touch(pc[None] + pn[None] * ts[:, None])
                hit = np.nonzero(dd < 0.004 * hand_len)[0]
                if len(hit):
                    wr = wr + pn * ts[hit[0]]; pc = pc + pn * ts[hit[0]]; moved = True
            for _ in range(3):
                d0 = float(touch(pc[None])[0])
                if d0 >= 0.004 * hand_len:
                    break
                e = 0.003
                gr = nrm(np.array([float(touch((pc + e * np.eye(3)[k])[None])[0]) - d0 for k in range(3)]))
                sh_ = gr * (0.004 * hand_len - d0)
                wr = wr + sh_; pc = pc + sh_; moved = True
            if moved or reach is not None:
                targets[s] = (wr, Mh, reach)
    if targets:
        Fw = dict(F)
        for s, (wr, Mh, reach) in targets.items():
            S_ = s.upper()
            side = 1 if s == "l" else -1
            sh = J[f"sh_{s}"]
            L1, L2 = rig.L1, rig.L2
            dvec = wr - sh
            dist = float(np.linalg.norm(dvec))
            dist_c = min(dist, (L1 + L2) * 0.999)
            dn = dvec / (dist + 1e-9)
            wr = sh + dn * dist_c
            Rc = J["Rchest"]
            pole = np.asarray(reach.get("pole", list(Rc @ V(side * 0.6, -0.6, -0.5))) if reach else list(Rc @ V(side * 0.6, -0.6, -0.5)), np.float64)
            if reach is None:          # an arm only pushed out keeps its elbow on the side it was
                pole = J[f"el_{s}"] - sh
            pole = nrm(pole - (pole @ dn) * dn)
            a = math.acos(float(np.clip((L1 ** 2 + dist_c ** 2 - L2 ** 2) / (2 * L1 * dist_c), -1, 1)))
            el = sh + (dn * math.cos(a) + pole * math.sin(a)) * L1
            du, df = nrm(el - sh), nrm(wr - el)
            Ru = _frame(-du, df if abs(du @ df) < 0.999 else Rc @ V(0, 0, 1))
            elb = math.acos(float(np.clip(du @ df, -1, 1)))
            Rf = Ru @ rx(-elb)
            # frames are wanted before the lean: undo it
            Fw[f"upper_{S_}"] = Mlean.T @ Ru
            Fw[f"fore_{S_}"] = Mlean.T @ Rf
            Fw[f"hand_{S_}"] = Mlean.T @ Mh
            if reach and "hand" in reach and f"hand_{s}" not in o:
                hands[S_] = hand_spec(reach["hand"]); hands[S_]["_preset"] = reach["hand"]
        F = Fw
        W, P = solve(F)
        W1, P1 = place(W, P, shift)
        # the IK placed the wrist joint; move the arm so that it lands exactly there
        J = J_of(W1, P1)
    # fingers rest on what they touch: each joint bent just enough to stay out, and with a resting or
    # holding grip curled down onto the surface (figure._chain_pose, on the mesh's finger bones)
    if ext is not None or targets:
        changed = False
        for s in "LR":
            sl = s.lower()
            h = hands[s]
            seek = h.get("_preset", "") in ("rest", "hold", "grip", "push_hair", "cup") and (sl in targets)
            dirs = finger_contact(rig, s, W1, P1, h, touch, seek)
            if dirs is not None:
                h["_dirs"] = dirs; changed = True
        if changed:
            W, P = solve(F)
            W1, P1 = place(W, P, shift)
    J = J_of(W1, P1)
    J["landmark"] = landmark
    Vp = skin(A, Vr, rig, W1, P1)
    J["_wrist_len"] = hand_len

    # ---------- surfaces
    return finish(o, body, A, Vr, Vp, rig, W1, P1, J, au, O_rest, Hh, eye_rest, scale)


def finger_contact(rig, s, W1, P1, h, touch, seek):
    """Bend each finger joint so its segment rests on a surface instead of passing into it."""
    A, b = rig.A, rig.A.B
    Wh = W1[b[f"wrist.{s}"]]
    Ch = rig.C[f"hand_{s}"]
    Mh = Wh @ Ch
    flex = [list(f) for f in h["f"]]
    changed = False
    for f, fi in FINGERS.items():
        base = P1[b[f"finger{f}-1.{s}"]]
        lens = [float(np.linalg.norm(rig.tail[b[f"finger{f}-{j}.{s}"]] - rig.head[b[f"finger{f}-{j}.{s}"]])) for j in (1, 2, 3)]
        r = 0.0085 * rig.hand_len / 0.19
        p0 = base
        for j in range(3):
            def end(dang):
                fl = [list(x) for x in flex]
                fl[fi][j] += dang
                dd = finger_dirs(rig, s, h, fl)[(f, j + 1)]
                return p0 + Mh @ dd * lens[j]
            def gap(dang):
                e = end(dang)
                q = np.stack([e, (p0 + e) / 2])
                return float(np.min(touch(q) - r))
            g0 = gap(0.0)
            if g0 < -0.1 * r or (seek and 0.3 * r < g0 < 2.5 * r):
                best, bc = 0.0, None
                for dlt in np.linspace(-50, 70, 25):
                    gg = gap(dlt)
                    cost = abs(dlt) * 0.002 + (10 if gg < -0.05 * r else 0) + (abs(gg) / r if seek else 0)
                    if bc is None or cost < bc:
                        best, bc = dlt, cost
                if best != 0.0:
                    flex[fi][j] += best; changed = True
            p0 = end(0.0)          # the joint as now bent (end reads the updated flex)
    if not changed:
        return None
    return finger_dirs(rig, s, h, flex)


def finish(o, body, A, Vr, Vp, rig, W1, P1, J, au, O_rest, Hh, eye_rest, scale):
    """Colours, clothes, hair, the proxy field; returns (mesh, sdf_parts, J)."""
    N = A.N
    bodyv = A.vset["body"]
    isbody = np.zeros(N, bool); isbody[bodyv] = True
    rw = A.region_w
    skin_hex = figure.sex_skin(o.get("skin", "#c49a7e"), body, o.get("skin_sex", 1.0))
    sk = hx(skin_hex).astype(np.float64)
    fem, old, child = float(np.clip(body.fs, 0, 1)), body.old, body.child
    cloth = hx(o.get("color", "#3a3a44")).astype(np.float64)
    clothes = o.get("clothes", [])
    if isinstance(clothes, dict):
        clothes = [clothes]
    for c_ in clothes:
        if c_.get("kind") == "dress" and "color" in c_:
            cloth = hx(c_["color"]).astype(np.float64)
    bare = set(o.get("bare", ["head", "hands"])) | {"head", "hands"}
    for c_ in clothes:
        if c_.get("kind") == "shirt" and c_.get("sleeves", "long") in ("short", "none"):
            bare.add("arms")
    reg = np.argmax(rw, 1)                    # regions: head neck torso arms hands legs feet
    col = np.tile(sk, (N, 1))
    elem = np.zeros(N, np.int64)
    for i, r in enumerate(A.regions):
        elem[reg == i] = EL[r]
    # the fitted suit (`color`) over the parts not bare, blended by the skin weights so its edges
    # (the neckline, the cuffs) are smooth lines, not the mesh's zigzag
    ri = {r: i for i, r in enumerate(A.regions)}
    suit = sum(rw[:, ri[r]] for r in ("torso", "arms", "legs") if r not in bare) if any(r not in bare for r in ("torso", "arms", "legs")) else np.zeros(N)
    suit = smoothstep(0.35, 0.65, suit) * isbody
    col = _mix(col, cloth[None], suit)
    shoe_c = hx(o.get("shoes", "#1e1a18")).astype(np.float64)
    shoe = smoothstep(0.35, 0.65, rw[:, ri["feet"]]) * isbody * ("feet" not in bare)
    col = _mix(col, shoe_c[None], shoe)
    skinness = (1 - suit) * (1 - shoe)
    elem[(A.masks["face"] > 0.5) & (reg == 0)] = EL["face"]
    gloss = np.full(N, float(o.get("skin_gloss", 0.0)))
    wrap = float(o.get("skin_wrap", 0.25)) * skinness
    infl = np.zeros(N)
    # lips, nails, inside of the mouth (MPFB2 masks); facial contrast as figure.head_part (Russell 2009)
    # on the sculpted lips a milder tint than the primitive rig needed (judgement; measured: face.md section 9)
    lips = sk * (V(0.84, 0.68, 0.66) + (V(0.78, 0.55, 0.56) - V(0.84, 0.68, 0.66)) * fem)
    if o.get("lips"):
        lips = hx(o["lips"])
    lm = np.clip(A.masks["lips"] * 1.4, 0, 1) * isbody
    col = _mix(col, lips[None].astype(np.float64), lm * (0.8 - 0.25 * old))
    gloss = np.maximum(gloss, 0.25 * lm)
    nm = np.clip(A.masks["fingernails"] * 1.5, 0, 1) * isbody * (reg == 4)
    col = _mix(col, np.clip(sk * V(1.08, 0.95, 0.95) + 0.06, 0, 1)[None], nm)
    gloss = np.maximum(gloss, 0.3 * nm)
    mm = np.clip(A.masks["inside_mouth"] * 1.5, 0, 1) * isbody
    col = _mix(col, hx("#4a1a18")[None].astype(np.float64), mm)
    wrap = wrap * (1 - mm)
    col[A.vset["teeth"]] = hx("#d6ccb8")
    col[A.vset["tongue"]] = hx("#8a3e3c")
    for v in ("teeth", "tongue", "lashes", "eye_l", "eye_r"):
        elem[A.vset[v]] = EL["face"]
        wrap[A.vset[v]] = 0
    gloss[A.vset["teeth"]] = 0.3
    gloss[A.vset["tongue"]] = 0.4
    gloss[A.vset["eye_l"]] = gloss[A.vset["eye_r"]] = 0.9
    eye_id = np.full(N, -1, np.int64)
    eye_id[A.vset["eye_l"]] = 0
    eye_id[A.vset["eye_r"]] = 1

    # ---------- fitted clothes: shirt and trousers as the body's surface eased out along the normals
    Tb = A.tris["body"]
    b = A.B
    H_ = rig.head
    def along(v, a, c):
        d = c - a
        return np.clip(((Vr[v] - a) @ d) / (d @ d), -1, 2)
    allv = np.arange(N)
    arm_s = {}
    leg_s = {}
    for s, side in (("L", 1), ("R", -1)):
        sh, el, wr = H_[b[f"upperarm01.{s}"]], H_[b[f"lowerarm01.{s}"]], H_[b[f"wrist.{s}"]]
        t1, t2 = along(allv, sh, el), along(allv, el, wr)
        arm_s[side] = np.where(t1 < 1, t1, 1 + np.clip(t2, 0, 2))
        hp, kn, an = H_[b[f"upperleg01.{s}"]], H_[b[f"lowerleg01.{s}"]], H_[b[f"foot.{s}"]]
        t1, t2 = along(allv, hp, kn), along(allv, kn, an)
        leg_s[side] = np.where(t1 < 1, t1, 1 + np.clip(t2, 0, 2))
    side_v = np.where(Vr[:, 0] >= 0, 1, -1)
    armpos = np.where(side_v > 0, arm_s[1], arm_s[-1])
    legpos = np.where(side_v > 0, leg_s[1], leg_s[-1])
    hipy = (H_[b["upperleg01.L"]][1] + H_[b["upperleg01.R"]][1]) / 2
    wind = np.asarray(o.get("wind", o.get("_wind", [0, 0, 0])), np.float64)
    wn = float(np.linalg.norm(wind))
    u = body.u
    garments = []
    y_ = Vr[:, 1]
    for cl in clothes:
        k = cl.get("kind")
        if k == "shirt":
            sleeve = cl.get("sleeves", "long")
            lim = {"long": 1.92, "short": 0.55, "none": 0.05}.get(sleeve, 1.92)
            hem = hipy + (0.1 - 0.3 * cl.get("length", 0.5)) * u
            c = rw[:, 2] * smoothstep(hem - 0.008, hem + 0.008, y_) + rw[:, 3] * smoothstep(lim + 0.03, lim - 0.03, armpos)
            c = smoothstep(0.35, 0.65, c) * (1 - smoothstep(0.15, 0.4, rw[:, 1])) * isbody      # the neckline
            garments.append((c, hx(cl.get("color", "#d8d4c8")), cl.get("ease", 0.012), cl))
        elif k == "trousers":
            lim = 1.97 if cl.get("length", "long") == "long" else 1.05
            waist_y = hipy + 0.42 * u
            c = rw[:, 5] * smoothstep(lim + 0.03, lim - 0.03, legpos) + rw[:, 2] * smoothstep(waist_y + 0.008, waist_y - 0.008, y_)
            c = smoothstep(0.35, 0.65, c) * isbody
            garments.append((c, hx(cl.get("color", "#3e4048")), cl.get("ease", 0.014), cl))
    for c, c_, ease, cl in garments:
        col = _mix(col, np.asarray(c_, np.float64)[None], c)
        elem[c > 0.5] = EL["drapery"]
        wrap = wrap * (1 - c)
        e = ease + 0.0015 * np.sin(Vr[:, 1] * 60 + Vr[:, 0] * 20)
        if cl.get("kind") == "shirt" and wn > 0:
            rel = Vp - J["chest"]
            lee = np.clip(rel @ (wind / wn) / 0.25, -1, 1)
            bill = cl.get("billow", 0.06) * min(wn / 12, 1.5)
            e = e + bill * np.clip(lee, 0, 1) - 0.6 * ease * np.clip(-lee, 0, 1)
        infl = np.maximum(infl, e * c)
    # cloth bridges the hollows it passes over (under the bust, the small of the back, between the
    # shoulder blades) instead of sinking into them: the eased surface is relaxed (Laplacian smoothing
    # over the garment) while it is kept at least half its ease off the skin (judgement, by eye)
    nposed = vertex_normals(Vp, Tb)
    Vb = Vp.copy()
    gcov = np.zeros(N)
    for c, *_ in garments:
        gcov = np.maximum(gcov, c)
    # the fitted suit (`color`) bridges too, more lightly: a bodice does not show the nipples
    gcov = np.maximum(gcov, 0.6 * suit * (reg != 0) * (reg != 4))
    if gcov.max() > 0:
        # the garment is the body's own surface, smoothed without shrinking (Taubin's lambda-mu
        # smoothing) so small forms (nipples, the navel, the hollows of the collarbones) don't print
        # through, then eased out along the normals; it blends back into the skin over its soft edge.
        # The smoothing scale is judgement (by eye on a shirt over a man's and a woman's chest)
        gm = gcov > 0.02
        Vbs = Vb.copy()
        for _ in range(24):
            for f_ in (0.5, -0.53):
                Vbs[gm] += f_ * ((A.adj @ Vbs)[gm] - Vbs[gm])
        # then it bridges the hollows (under the bust, the small of the back): smoothing that may only
        # move the surface outward, so it rests on the convex forms and spans the concave ones
        for _ in range(40):
            Lp = (A.adj @ Vbs) - Vbs
            out_ = (Lp * nposed).sum(1)
            mv = gm & (out_ > 0)
            Vbs[mv] += 0.5 * gcov[mv, None] * Lp[mv]
        ease_full = np.where(gcov > 1e-3, infl / np.maximum(gcov, 1e-3), 0.0)
        ease_full = np.maximum(ease_full, 0.0015)
        tgt = Vbs + nposed * ease_full[:, None]
        Vp = np.where(gm[:, None], Vb + gcov[:, None] * (tgt - Vb), Vb)
    Vp = Vp + nposed * (0.004 * shoe)[:, None]

    # ---------- per-pixel detail and the mesh
    look = Look(A, body, o, sk)
    look.eye_id = eye_id
    # the eyelash cards are left out: without their alpha texture they render as black wedges; the
    # lash line is painted per pixel instead (Look.lash_line)
    rt = np.concatenate([A.tris["body"], A.tris["eye_l"], A.tris["eye_r"], A.tris["teeth"], A.tris["tongue"]])
    eye_pos = {}
    for k, s in ((0, "L"), (1, "R")):
        vs = A.vset["eye_" + "lr"[k]]
        eye_pos[k] = (Vp[vs].mean(0), float(np.linalg.norm(Vp[vs] - Vp[vs].mean(0), axis=1).mean()))
    planes = float(o.get("planes", 0.0))
    bplanes = float(o.get("body_planes", 0.0))
    pl = np.where((elem == EL["head"]) | (elem == EL["face"]), planes, bplanes)
    mesh = dict(verts=Vp.astype(np.float32), tris=rt, color=col.astype(np.float32), gloss=gloss.astype(np.float32),
                wrap=wrap.astype(np.float32), elem=elem, rest=A.V0.astype(np.float32), look=look, eye=eye_pos, eye_id=eye_id,
                planes=pl.astype(np.float32), adj=A.adj, sub=list(ELEMENTS), body_tris=Tb)

    # ---------- the proxy field (AO, contact, cloth and hair collisions)
    Tall = np.concatenate([Tb, A.tris["eye_l"], A.tris["eye_r"]])
    prox = GridSDF(Vp, Tall, voxel=float(o.get("_proxy_voxel", 0.012)))
    parts = [dict(f=prox, color=np.zeros(3, np.float32), element="proxy", bound=(list(prox.c), prox.r), proxy=True)]

    # ---------- hair (figure.hair_part on this skull) and loose clothes (figure's cloth simulation)
    wind32 = wind.astype(np.float32)
    collide = lambda p: prox(p)
    if o.get("hair"):
        O = J["head"]
        M = J["Rhead"]
        hb_ = figure.Body(o)
        hb_.u = Hh
        # the body's surface in the head's own frame, inside a box from below the chin to above the
        # crown, closed by a lid where the box cuts the neck, so the volume fills (a cut-out head leaks
        # and the field loses its sign)
        Vh = (Vp - O) @ M
        box = (np.array([-0.5, -0.62, -0.66]) * Hh, np.array([0.5, 0.62, 0.62]) * Hh)
        inb = np.all((Vh > box[0] - 0.02) & (Vh < box[1] + 0.02), 1)
        inb &= ~((rw[:, 3] + rw[:, 4]) > 0.5)          # not a hand or arm that touches the head: hair would grow round it
        Th = Tall[inb[Tall].any(1)]
        hg = GridSDF(Vh, Th, voxel=0.004, smooth=True, box=box, lid=True)
        Of, Mf = O.astype(np.float32), M.astype(np.float32)
        skull = lambda q: hg(np.asarray(q, np.float32) * Hh) / Hh
        # the eye line in this head's units (the hairline is measured from it)
        eye_w = (P1[A.B["eye.L"]] + P1[A.B["eye.R"]]) / 2
        # figure.hair_part's hairline and side lengths were set over the primitive skull, which sat a
        # little proud of the face; on the sculpted skull they land about 0.05 head high (by eye: the
        # visible hairline came out 0.37 above the eye line against Farkas's 0.29 + brow): lower them
        ye = float(((eye_w - O) @ M)[1] / Hh) - 0.05
        oh = o
        hd_ = o["hair"] if isinstance(o["hair"], dict) else {"color": o["hair"]}
        if hd_.get("style") == "receding" and "nape" not in hd_:
            # on the sculpted skull the horseshoe needs to reach the nape, or it floats as a band
            oh = dict(o, hair=dict(hd_, nape=-0.45))
        hp = figure.hair_part(oh, hb_, Of, Mf, wind32, collide, skull=skull, ye=ye, cranium=False)
        for d in hp:
            d["colorf"] = hair_streaks(d["color"], Of, Mf, Hh)
        parts += hp
    # loose clothes: figure.py's cloth simulation, drawn as meshes (the simulated grids themselves)
    meshes = [mesh]
    orig = figure.cloth_part
    figure.cloth_part = lambda grids, thick, color, name, smooth_wrap=None: dict(grids=grids, color=color, name=name)
    try:
        for cl in clothes:
            k = cl.get("kind")
            if k == "dress":
                J2 = dict(J)
                J2["_dims"] = {"a_w": waist_halfwidth(Vp, J, A, isbody)}
                meshes.append(cloth_mesh(figure.dress_part(o, cl, body, J2, wind32, collide, cloth)))
            elif k == "shawl":
                meshes.append(cloth_mesh(figure.shawl_part(o, cl, body, J, wind32, collide, cloth)))
    finally:
        figure.cloth_part = orig
    J["_proxy"] = prox
    J["_rig"] = rig
    J["_meshes"] = meshes[1:]
    return mesh, parts, J


def cloth_mesh(d):
    """A simulated cloth (figure.dress_part / shawl_part grids) as a two-sided triangle mesh."""
    V_, T_ = [], []
    off = 0
    for G, wrap in d["grids"]:
        G = figure.subdivide(np.asarray(G, np.float64), wrap)
        nr, nc = G.shape[:2]
        ii, jj = np.meshgrid(np.arange(nr - 1), np.arange(nc if wrap else nc - 1), indexing="ij")
        a = ii * nc + jj
        b = ii * nc + (jj + 1) % nc
        c = (ii + 1) * nc + jj
        e = (ii + 1) * nc + (jj + 1) % nc
        T_.append(np.concatenate([np.stack([a, c, b], -1).reshape(-1, 3), np.stack([b, c, e], -1).reshape(-1, 3)]) + off)
        V_.append(G.reshape(-1, 3))
        off += nr * nc
    Vc = np.concatenate(V_)
    col = hx(d["color"]) if isinstance(d["color"], str) else np.asarray(d["color"], np.float64)
    n = len(Vc)
    return dict(verts=Vc.astype(np.float32), tris=np.concatenate(T_), color=np.tile(col, (n, 1)).astype(np.float32),
                gloss=np.zeros(n, np.float32), wrap=np.zeros(n, np.float32), elem=np.zeros(n, np.int64), planes=np.zeros(n, np.float32),
                sub=["drapery"], two_sided=True, name=d["name"])


def hair_streaks(col, O, M, H):
    """Hair reads as hair by its strands: the colour streaked along the direction the hair grows,
    around and down from the crown (two interfering frequencies so it does not band; judgement)."""
    c0 = np.asarray(col, np.float32)
    crown = np.array([0, 0.42, -0.12], np.float32)

    def colorf(p):
        q = ((np.asarray(p, np.float32) - O) @ M) / H
        r = q - crown
        ang = np.arctan2(r[:, 0], r[:, 2])
        s1 = np.sin(ang * 90 + 3 * np.sin(q[:, 1] * 14) + 1.3 * np.sin(ang * 23))
        s2 = np.sin(ang * 37 + 1.7 + 2 * np.sin(q[:, 1] * 9 + q[:, 0] * 5))
        s3 = np.sin(ang * 151 + 5 * np.sin(q[:, 1] * 21 + ang * 3))
        v = 0.88 + 0.045 * s1 + 0.05 * s2 + 0.03 * s3
        return np.clip(c0[None] * v[:, None], 0, 1)
    return colorf


def waist_halfwidth(Vp, J, A, isbody):
    y = J["waist"][1]
    torso = isbody & (np.argmax(A.region_w, 1) == 2) & (np.abs(Vp[:, 1] - y) < 0.015)
    if torso.sum() < 4:
        return 0.13
    c = J["waist"]
    x = Vp[torso] - c
    return float(np.percentile(np.abs(x[:, 0]), 95))


# ---------------------------------------------------------------- a lone hand
def hand(o):
    """A lone hand (and forearm) cut from the mesh: pos = the wrist, fingers = where the fingers
    point, palm = where the palm faces, preset, side l|r, length (wrist to fingertip, m)."""
    A = assets()
    side = o.get("side", "l")
    p = {"type": "person", "sex": o.get("sex", "female"), "age": o.get("age", 30), "build": o.get("build", "average"),
         "skin": o.get("skin", "#c49a7e"), "bare": ["arms", "hands"], "pose": "stand", "masks": False,
         f"hand_{side}": o.get("preset", "relaxed") if not o.get("extra") else dict(hand_spec(o.get("preset", "relaxed"), o.get("extra")))}
    p["joints"] = {f"arm_{side}": [0, 0, 0, 0], f"wrist_{side}": [0, 0, 0]}
    mesh, parts, J = person(p)          # built alone: a lone mesh hand does not rest on other objects
    rig = J["_rig"]
    keep = (A.region_w[:, 4] + A.region_w[:, 3]) > 0.5
    keep &= np.sign(A.V0[:, 0]) == (1 if side == "l" else -1)
    Vp = mesh["verts"].astype(np.float64)
    wr = J[f"wr_{side}"]
    el = J[f"el_{side}"]
    fore = o.get("forearm", 1.0)
    t = ((Vp - wr) @ nrm(el - wr)) / np.linalg.norm(el - wr)
    keep &= t < 0.9 * fore
    T = mesh["tris"]
    T = T[keep[T].all(1)]
    Mh = J[f"Rhand_{side}"]
    fdir = figure.nrm(o.get("fingers", [0, -1, 0])).astype(np.float64)
    palm = figure.nrm(o.get("palm", [0, 0, 1])).astype(np.float64)
    palm = nrm(palm - (palm @ fdir) * fdir)
    Mt = np.stack([np.cross(-fdir, palm), -fdir, palm], 1)
    Rw = Mt @ Mh.T
    L = o.get("length", 0.18)
    sc = L / rig.hand_len
    pos = np.asarray(o.get("pos", [0, 1, 0]), np.float64)
    Vn = (Vp - wr) @ Rw.T * sc + pos
    mesh["verts"] = Vn.astype(np.float32)
    mesh["tris"] = T
    return mesh


# ---------------------------------------------------------------- measuring
def body_stats(o, step=None):
    """A standing person measured like a tape: waist (narrowest girth between hips and chest) and hip
    (widest around hips and buttocks) girths from horizontal slices of the mesh (convex hull, arms
    left out), their ratio, the biacromial breadth (shoulder joints plus 2 cm each side, as figure's
    rig places them) and the hip breadth, in meters; and the height in heads."""
    from scipy.spatial import ConvexHull
    o = dict(o, pose="stand", joints={}, anchor="ground", pos=[0, 0, 0], _ground_y=0.0, clothes=[], hair=None, lie=None,
             expression="neutral")
    for k in ("reach_l", "reach_r", "lean", "pitch", "roll", "facing"):
        o.pop(k, None)
    mesh, parts, J = person(o)
    A = assets()
    Vp = mesh["verts"].astype(np.float64)
    T = A.tris["body"]
    reg = np.argmax(A.region_w, 1)
    trunk = np.isin(reg, [2, 5]) & ~((A.region_w[:, 3] + A.region_w[:, 4]) > 0.2)
    Tt = T[trunk[T].all(1)]

    def girth(y):
        a, b_, c = Vp[Tt[:, 0]], Vp[Tt[:, 1]], Vp[Tt[:, 2]]
        pts = []
        for p, q in ((a, b_), (b_, c), (c, a)):
            s = (y - p[:, 1]) / (q[:, 1] - p[:, 1] + 1e-12)
            m = (s >= 0) & (s <= 1)
            pts.append(p[m] + s[m, None] * (q[m] - p[m]))
        P_ = np.concatenate(pts)[:, [0, 2]]
        if len(P_) < 3:
            return 0.0, 0.0
        h = ConvexHull(P_)
        return float(h.area), float(np.ptp(P_[:, 0]))
    hy = float(J["pelvis"][1])
    cy = float(J["sh_l"][1])
    ys_w = np.linspace(hy + 0.06, hy + 0.6 * (cy - hy), 24)
    ys_h = np.linspace(hy - 0.14, hy + 0.04, 16)
    gw = min((girth(y) + (y,) for y in ys_w), key=lambda t: t[0])
    gh = max((girth(y) + (y,) for y in ys_h), key=lambda t: t[0])
    S = Vp[A.vset["body"], 1].max() - Vp[A.vset["body"], 1].min()
    hb = np.nonzero(reg == 0)[0]
    front = hb[Vp[hb, 2] > np.percentile(Vp[hb, 2], 60)]
    Hh = Vp[hb, 1].max() - Vp[front, 1].min()
    return dict(waist=round(gw[0], 3), hip=round(gh[0], 3), whr=round(gw[0] / gh[0], 3), waist_breadth=round(gw[1], 3),
                hip_breadth=round(gh[1], 3), biacromial=round(float(np.linalg.norm(J["sh_l"] - J["sh_r"])) + 0.04, 3),
                stature=round(float(S), 3), heads=round(float(S / Hh), 2))
