"""Photoreal reference renders of people: the scene's own meshes, camera and light, path-traced by Blender's
Cycles (G1 of docs/research/hyperrealism-gaps.md, second part).

Why: a hyperrealist copies a high-resolution photograph; the studio's z-buffer render (scene.py) is Lambert
shading with procedural normals, and it reads as a mid-2000s game character. Cycles gives what a photograph
holds and the z-buffer can't: light scattered under the skin (random-walk subsurface scattering with Jensen's
measured skin), a dielectric skin surface (index 1.38, Weyrich et al. 2006) with a micro-relief of pores and
furrows, single hair strands with a physically based hair BSDF (Chiang et al. 2016) that shadow and light each
other, lashes, brows and stubble as strands, an eye with a refracting cornea over a recessed iris, depth of field.

How it fits: `scene` with `"renderer": "cycles"` builds the scene as before (the z-buffer render still gives the
element masks, the lens report and the droplets' structure), then this module exports the people (posed MakeHuman
mesh, attributes in the base mesh's own coordinates, eyes, strands grown here in numpy), runs
`photoreal_bpy.py` in a separate Python that has the `bpy` wheel (Blender as a module, GPL; installed by
`tools/setup_photoreal.py` into ~/.cache/teodor/bpy-venv, never imported by the studio itself), tone-maps the
linear result and corrects the hair mask from the render's own coverage.

Only people (and lone hands) are rendered; a scene with other objects falls back to the z-buffer render.
Every value tuned by eye says so; the measured ones cite their source."""
import json
import math
import os
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BPY_PY = os.environ.get("TEODOR_BPY", os.path.expanduser("~/.cache/teodor/bpy-venv/bin/python"))

# Jensen, Marschner, Levoy and Hanrahan 2001, "A Practical Model for Subsurface Light Transport", table of measured
# skin ("Skin1"): sigma_s' = (0.74, 0.88, 1.01) /mm, sigma_a = (0.032, 0.17, 0.48) /mm. Cycles' random walk takes a
# mean free path per channel; the diffuse mean free path 1/sigma_tr, sigma_tr = sqrt(3 sigma_a sigma_t'), gives
# (3.67, 1.37, 0.68) mm, which is also the "skin" radius Cycles' own docs quote. [S]
SKIN_MFP_MM = (3.67, 1.37, 0.68)
SKIN_IOR = 1.38            # Weyrich et al. 2006 (after Tuchin), as scene.py's sheen [S]
CORNEA_IOR = 1.376         # the cornea's refractive index (Gullstrand's schematic eye) [S]
# eye geometry in units of the eyeball's radius (sclera radius 11.5 mm; cornea radius of curvature 7.8 mm; corneal apex
# 12.5 mm from the eye's centre; iris 11.7 mm across, pupil 3.5 mm in ordinary light: Gullstrand / Atchison & Smith,
# "Optics of the Human Eye") [S]
EYE = dict(sclera_mm=11.5, cornea_r_mm=7.8, apex_mm=12.5, iris_r_mm=5.85, pupil_r_mm=1.75, chamber_mm=3.1)
# hair: scalp density 150-250 hairs per cm2 in adults is the usual textbook range; the render uses fewer, slightly
# thicker strands (coverage, not count, is what reads): by eye [H]. Diameter of a scalp hair about 0.06-0.10 mm.
HAIR = dict(density_cm2=140.0, radius_mm=0.040, step_mm=2.0, brow_density_cm2=120.0, brow_radius_mm=0.045,
            lash_upper=(120, 7.5, 10.0), lash_lower=(65, 4.5, 6.5), lash_radius_mm=0.045,
            stubble_density_cm2=70.0, stubble_len_mm=(0.3, 0.9), stubble_radius_mm=0.045)
# stubble: beard hair grows about 0.3-0.4 mm a day, so 1-3 days is 0.4-1.2 mm [S, approximate]; density by eye [H]


def available():
    return os.path.exists(BPY_PY)


def to_b(v):
    """Studio coordinates (y up, z toward the viewer) to Blender's (z up): (x, -z, y)."""
    v = np.asarray(v, np.float64)
    return np.stack([v[..., 0], -v[..., 2], v[..., 1]], -1)


def srgb_to_lin(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, None)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, np.float64) - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- surface sampling
def vertex_normals(V, T):
    n = np.zeros_like(V)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    for k in range(3):
        np.add.at(n, T[:, k], fn)
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)


def sample_surface(Vp, R, T, n, rng, vn=None):
    """n points spread by area over triangles T: posed position, rest position, posed normal, triangle id, barycentrics."""
    a = 0.5 * np.linalg.norm(np.cross(Vp[T[:, 1]] - Vp[T[:, 0]], Vp[T[:, 2]] - Vp[T[:, 0]]), axis=1)
    if n <= 0 or a.sum() <= 0:
        z = np.zeros((0, 3))
        return z, z, z, np.zeros(0, np.int64), z
    ti = rng.choice(len(T), size=n, p=a / a.sum())
    r1, r2 = rng.random(n), rng.random(n)
    s = np.sqrt(r1)
    b = np.stack([1 - s, s * (1 - r2), s * r2], 1)
    tri = T[ti]
    P = (Vp[tri] * b[:, :, None]).sum(1)
    Pr = (R[tri] * b[:, :, None]).sum(1)
    vn = vertex_normals(Vp, T) if vn is None else vn
    N = (vn[tri] * b[:, :, None]).sum(1)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    return P, Pr, N, ti, b


def tri_jacobian(Vp, R, T, ti):
    """Per sampled triangle, the linear map from rest-space directions to posed-space directions."""
    tri = T[ti]
    def frame(V):
        e1 = V[tri[:, 1]] - V[tri[:, 0]]
        e2 = V[tri[:, 2]] - V[tri[:, 0]]
        nn = np.cross(e1, e2)
        nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-12
        return np.stack([e1, e2, nn], 2)          # columns
    Ep, Er = frame(Vp), frame(R)
    return Ep @ np.linalg.inv(Er)


def area_cm2(Vp, T):
    return float(0.5 * np.linalg.norm(np.cross(Vp[T[:, 1]] - Vp[T[:, 0]], Vp[T[:, 2]] - Vp[T[:, 0]]), axis=1).sum()) * 1e4


def value_noise3(q, k):
    import human
    return human._value_noise(q, k)


# ---------------------------------------------------------------- strand growth
class Skin:
    """Dense samples of a skin surface with normals: signed height of points above it (nearest sample)."""

    def __init__(self, P, N):
        from scipy.spatial import cKDTree
        self.P, self.N = P, N
        self.tree = cKDTree(P)

    def height(self, X):
        _, i = self.tree.query(X, workers=-1)
        n = self.N[i]
        return ((X - self.P[i]) * n).sum(1), n


def grow(roots, normals, dir_fn, skin, steps, step_m, lift_m, rise_m=0.004, alive_fn=None, bend=None, seed=0):
    """Strands from roots along dir_fn(P, k) (unit vectors, any length), kept at a target height above the skin that
    rises from 0 at the root to lift_m over rise_m of length (a hair leaves the skin at an angle and lies down).
    Returns (M, steps+1, 3) points and a per-strand count of valid points."""
    M = len(roots)
    out = np.zeros((M, steps + 1, 3))
    P = roots + normals * 0.0002
    out[:, 0] = roots
    alive = np.ones(M, bool)
    cnt = np.ones(M, np.int64)
    for k in range(1, steps + 1):
        ia = np.nonzero(alive)[0]
        if not len(ia):
            break
        X = P[ia]
        h, nrm = skin.height(X)
        d = dir_fn(X, k, ia)
        d = d - (d * nrm).sum(1, keepdims=True) * nrm
        d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-12
        s_ = k * step_m
        ht = lift_m[ia] * np.clip(s_ / rise_m, 0, 1)
        Xn = X + d * step_m + nrm * np.clip(ht - h, -0.6 * step_m, 0.6 * step_m)[:, None]
        if bend is not None:
            Xn = Xn + bend(Xn, k, ia) * step_m
        ok = np.ones(len(ia), bool)
        if alive_fn is not None:
            ok = alive_fn(Xn, k, ia)
        P[ia] = Xn
        out[ia, k] = Xn
        cnt[ia[ok]] = k + 1
        alive[ia[~ok]] = False
    for i in range(M):                                 # pad the dead tails with the last point (dropped on export)
        out[i, cnt[i]:] = out[i, cnt[i] - 1]
    return out, cnt


# ---------------------------------------------------------------- the person's export
def _head_frame(J):
    O = np.asarray(J["head"], np.float64)
    Mh = np.asarray(J["Rhead"], np.float64)
    return O, Mh


def _brow_mask(look, R):
    """Look.brows' mask (rest coordinates of the base mesh)."""
    x, y, z = np.abs(R[:, 0]), R[:, 1], R[:, 2]
    t = np.clip((x - 0.012) / 0.046, 0, 1)
    yb = 0.7415 + look.brow_lift + look.arch * np.sin(np.pi * np.clip(t * 1.15, 0, 1)) - 0.004 * t * t
    th = look.brow_th * (1.15 - 0.6 * t)
    m = smoothstep(th * 0.5 + 0.0012, th * 0.5 - 0.0008, np.abs(y - yb)) * smoothstep(0.009, 0.013, x) * smoothstep(0.062, 0.055, x)
    return m * (z > 0.1) * look.brow_amt * (1 - 0.35 * t), t


def _beard_mask(R):
    """Look.beard_zone's mask (rest coordinates)."""
    x, y, z = np.abs(R[:, 0]), R[:, 1], R[:, 2]
    top = 0.705 - 0.035 * np.clip((x - 0.02) / 0.05, 0, 1)
    m = smoothstep(top + 0.004, top - 0.006, y) * smoothstep(0.585, 0.605, y) * smoothstep(0.02, 0.05, z + 0.02)
    return m * smoothstep(0.075, 0.06, x)


def _kabsch(A, B):
    """Rotation R with B - mean(B) ~ R (A - mean(A))."""
    a, b = A - A.mean(0), B - B.mean(0)
    U, _, Vt = np.linalg.svd(a.T @ b)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, 1, d])
    return Vt.T @ D @ U.T


def export_person(node, hair_nodes, spec_o, cam, rng, frustum):
    import human
    A = human.assets()
    m = node.mesh
    Vp = m["verts"].astype(np.float64)
    R0 = A.V0.astype(np.float64)
    look = m["look"]
    elem = m["elem"]
    EL = human.EL
    body_q = A.parts["body"]
    # the person's scale against the base mesh (the rest coordinates in real metres for the procedural detail)
    hv = np.nonzero(np.isin(elem, [EL["head"], EL["face"]]))[0]
    i1, i2 = hv[rng.integers(0, len(hv), 4000)], hv[rng.integers(0, len(hv), 4000)]
    dr = np.linalg.norm(R0[i1] - R0[i2], axis=1)
    k_ = dr > 0.02
    scale = float(np.median(np.linalg.norm(Vp[i1] - Vp[i2], axis=1)[k_] / dr[k_]))
    Rm = R0 * scale

    # faces the camera can see (with a margin), so the subdivided mesh stays small
    vis = frustum(Vp)
    q_ok = vis[body_q].any(1)
    Q = body_q[q_ok]
    T = np.concatenate([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
    vn = vertex_normals(Vp, np.concatenate([body_q[:, [0, 1, 2]], body_q[:, [0, 2, 3]]]))

    # ----- per-vertex attributes
    N = len(Vp)
    col = srgb_to_lin(np.clip(m["color"].astype(np.float64), 0, 1))
    skin_w = m["wrap"].astype(np.float64)
    skin_w = skin_w / max(float(skin_w.max()), 1e-6) if skin_w.max() > 0 else (elem != EL["drapery"]).astype(np.float64)
    mouth = np.clip(A.masks["inside_mouth"] * 1.5, 0, 1)
    cloth = np.clip(1 - skin_w - mouth, 0, 1) * (elem == EL["drapery"]) + (elem == EL["drapery"]) * 0
    cloth = np.maximum(cloth, (elem == EL["drapery"]).astype(np.float64))
    face = (elem == EL["face"]).astype(np.float64)
    # face coordinates in the face's own box (as scene.py's oil map), for the T-zone and the cheeks' blood
    rf = R0[elem == EL["face"]]
    lo_, hi_ = rf.min(0), rf.max(0)
    u = (R0[:, 0] - (lo_[0] + hi_[0]) / 2) / max(hi_[0] - lo_[0], 1e-6)
    vv = (R0[:, 1] - lo_[1]) / max(hi_[1] - lo_[1], 1e-6)
    tz = np.clip(np.clip(1 - np.abs(u) / 0.16, 0, 1) * (vv > 0.3) + np.clip((vv - 0.62) / 0.1, 0, 1), 0, 1) * face
    lips = m.get("lips_w", np.zeros(N)).astype(np.float64)
    beard = _beard_mask(R0) * (look.beard > 0) * skin_w
    brow, _ = _brow_mask(look, R0)
    # blood: the cheeks, the nose's tip and wings, the ears and the lips' margins run redder (Russell: a man's skin
    # darker and redder; the distribution is the usual erythema map of a face): shapes by eye [H]
    g = lambda c, s: np.exp(-(((R0 - np.array(c)) / np.array(s)) ** 2).sum(1))
    red = (0.8 * (g([0.045, 0.700, 0.12], [0.018, 0.016, 0.03]) + g([-0.045, 0.700, 0.12], [0.018, 0.016, 0.03]))
           + 1.0 * g([0, 0.703, 0.165], [0.012, 0.01, 0.02]) + 0.6 * (np.abs(R0[:, 0]) > 0.07) * (R0[:, 1] > 0.69) * (R0[:, 1] < 0.77)
           + 0.5 * lips)
    red = np.clip(red, 0, 1) * skin_w
    # the lid margins and the inner corners are wet and pinker (the caruncle, the tear meniscus): vertices within
    # about 1.5 mm of the eyeball's surface [H]
    wet = np.zeros(N)
    eyes = []
    for k_e, s in enumerate("lr"):
        ev = A.vset["eye_" + s]
        c = Vp[ev].mean(0)
        r_h = float(np.linalg.norm(Vp[ev] - c, axis=1).mean())
        Rot = _kabsch(R0[ev] - A.eye_c[s], Vp[ev] - c)
        fwd = Rot @ np.array([0, 0, 1.0])
        # MakeHuman's eye helper (15 mm in radius on the base mesh) passes through the lids, whose margins ring the
        # eye at 12-13 mm: the eyeball is sized to rest just under the margins, which is also the anatomical eye
        # (sclera about 11.5-12 mm in radius) [S: Atchison & Smith]
        bv_ = A.vset["body"]
        Dm = Vp[bv_] - c
        dm = np.linalg.norm(Dm, axis=1)
        ring = (Dm @ fwd) / (dm + 1e-9) > 0.5
        ring &= dm < r_h
        r = float(np.percentile(dm[ring], 3)) - 0.00025 * scale if ring.sum() > 10 else 0.8 * r_h
        d = np.linalg.norm(Vp - c, axis=1) - r
        front = ((Vp - c) @ fwd) / (np.linalg.norm(Vp - c, axis=1) + 1e-9)
        near = smoothstep(0.0025 * scale, 0.0005 * scale, d) * (front > 0.2) * (np.arange(N) < A.N)
        wet = np.maximum(wet, near * (elem != EL["drapery"]))
        eyes.append(dict(c=c, r=r, R=Rot, side=s, fwd=fwd))
    # pores denser and the micro-relief per region: face 1, rest of the body lighter [H]
    # the darker, cooler skin under and around the eyes (periorbital): rings under each eye, shapes by eye [H]
    orbit = np.zeros(N)
    for s_ in (1, -1):
        dx_, dy_ = R0[:, 0] - s_ * 0.031, R0[:, 1] - 0.7205
        orbit += np.exp(-((dx_ / 0.016) ** 2 + (dy_ / 0.0075) ** 2)) * (R0[:, 2] > 0.1)
        dy2 = R0[:, 1] - 0.737
        orbit += 0.5 * np.exp(-((dx_ / 0.012) ** 2 + (dy2 / 0.004) ** 2)) * (R0[:, 2] > 0.1)
    orbit = np.clip(orbit, 0, 1) * skin_w
    attrs = dict(col=col, skin=skin_w, orbit=orbit, cloth=cloth, mouth=mouth, face=face, tz=tz, lips=lips, beard=beard, red=red,
                 wet=wet, brow=brow, rest=Rm)

    # ----- eyes as their own meshes (local frame: +z the axis)
    eye_objs = []
    for e in eyes:
        eye_objs.append(dict(c=e["c"], r=e["r"], R=e["R"]))

    # ----- strands
    rng2 = np.random.default_rng(int(spec_o.get("strand_seed", 11)))
    head_q = body_q[(np.isin(elem[body_q], [EL["head"], EL["face"]])).all(1)]
    Th = np.concatenate([head_q[:, [0, 1, 2]], head_q[:, [0, 2, 3]]])
    nsk = int(min(400000, area_cm2(Vp, Th) * 900))
    SP, SR, SN, _, _ = sample_surface(Vp, Rm, Th, nsk, rng2, vn)
    skin = Skin(SP, SN)
    strands = []
    t0 = time.time()
    hd = spec_o.get("hair")
    hcol = None
    if hd:
        hd = {"color": hd} if isinstance(hd, str) else hd
        hcol = hd.get("color", "#2a1e18")
    import figure
    age = float(spec_o.get("age", 35))
    grey = float(hd.get("grey", figure.lerp_table(figure.GREY, age))) if hd else float(figure.lerp_table(figure.GREY, age))
    for hn in hair_nodes:
        strands.append(_scalp_hair(hn, Vp, Rm, Th, vn, skin, rng2, hd or {}, spec_o))
    brow_col = look.brow_col
    strands.append(_brows(Vp, Rm, R0, Th, vn, skin, rng2, look, scale))
    strands.append(_lashes(Vp, elem, eyes, skin, rng2, A, scale))
    if look.beard > 0:
        strands.append(_stubble(Vp, Rm, R0, Th, vn, skin, rng2, look, scale))
    strands = [s for s in strands if s is not None and len(s["pts"])]
    print(f"photoreal: {sum(len(s['pts']) for s in strands)} strands grown in {time.time() - t0:.0f} s", file=sys.stderr)

    mel_hair = melanin_of(hcol) if hcol else 0.8
    mel_brow = melanin_of(brow_col if isinstance(brow_col, str) else "#%02x%02x%02x" % tuple(int(255 * float(v)) for v in np.clip(brow_col, 0, 1)))
    return dict(V=Vp, Q=Q, attrs=attrs, eyes=eye_objs, strands=strands, scale=scale,
                teeth=A.parts["teeth"], tongue=A.parts["tongue"], iris=list(srgb_to_lin(look.iris)),
                sclera=list(srgb_to_lin(look.sclera)), mel_hair=mel_hair, mel_brow=mel_brow, grey=grey,
                age=age, oil=float(spec_o.get("skin_oil", 0.5)), detail=float(spec_o.get("skin_detail", 1.0)),
                seed=int(spec_o.get("skin_seed", 7)), droplets=m.get("droplets"),
                beard_amt=float(look.beard))


def melanin_of(hexcol):
    """Principled hair's melanin from a hair colour: lightness L* to eumelanin concentration (black ~0.95, dark brown
    ~0.8 at L* 26, mid brown ~0.6, light brown ~0.45, blond ~0.25). The mapping is by eye on Blender's own hair presets [H]."""
    c = srgb_to_lin(hexc(hexcol)) if isinstance(hexcol, str) else srgb_to_lin(np.asarray(hexcol))
    Y = float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])
    L = 116 * Y ** (1 / 3) - 16 if Y > 0.008856 else 903.3 * Y
    return float(np.clip((88 - L) / 78, 0.05, 0.97))


def _scalp_hair(hn, Vp, Rm, Th, vn, skin, rng, hd, o):
    """Strands grown inside the hair's simulated mass (figure.hair_part on this skull): rooted where the mass covers
    the scalp, thinning over the last 6 mm before the hairline (a hairline is a gradient of fine hairs, not an
    edge), lying along the growth from the crown, held between the scalp and the mass's outer surface, in locks."""
    f = hn.f
    area = area_cm2(Vp, Th)
    n = int(area * HAIR["density_cm2"] * float(hd.get("density", 1.0)))
    P, Pr, Nn, ti, b = sample_surface(Vp, Rm, Th, n, rng, vn)
    probe = P + Nn * 0.0012
    fv = np.asarray(f(probe.astype(np.float32)), np.float64)
    inside = fv < 0
    # the hairline gradient: how deep inside the mass's edge the root is (the field's value just above the skin)
    keep = inside & (rng.random(n) < smoothstep(0.0, 0.006, -fv))
    P, Nn = P[keep], Nn[keep]
    M = len(P)
    if not M:
        return None
    # thickness of the mass over each root
    th = np.full(M, 0.0)
    for t in np.linspace(0.001, 0.04, 40):
        fin = np.asarray(f((P + Nn * t).astype(np.float32)), np.float64) < 0
        th = np.where(fin & (th >= t - 0.0011), t, th)
    th = np.maximum(th, 0.0015)
    u = rng.random(M) ** 0.6
    lift = np.clip(u * th * 0.92, 0.0006, None)
    # a few strays stand a little out of the mass (0.4%: a real head of hair is never a clean shell) [H]
    stray = rng.random(M) < 0.004
    lift[stray] = th[stray] + 0.001 + 0.002 * rng.random(stray.sum())
    flow = hn.flowf
    jit = rng.normal(0, 1, (M, 3)) * 0.18
    curl_k = rng.integers(0, 1 << 20, M)
    lk = float(hd.get("locks_mm", 9.0)) / 1000.0         # the size of a lock: by eye [H]

    def dir_fn(X, k, ia):
        d = np.asarray(flow(X.astype(np.float32)), np.float64)
        d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-12
        d = d + np.array([0, -0.35, 0])                   # hair falls a little: by eye [H]
        # locks: a smooth vector noise shared by neighbouring strands, plus each strand's own small deviation
        q = X / lk
        nz = np.stack([value_noise3(q, 101 + a) for a in range(3)], 1)
        return d + 0.45 * nz + jit[ia]
    style = hd.get("style", "short")
    L = {"short": 0.055, "crop": 0.035, "slick": 0.07, "receding": 0.05, "bald": 0.01, "bob": 0.16, "long": 0.25}.get(style, 0.06)
    L = float(hd.get("strand_length", L))
    steps = int(math.ceil(L / (HAIR["step_mm"] / 1000)))
    Ls = L * (0.55 + 0.45 * rng.random(M))

    def alive(X, k, ia):
        fv_ = np.asarray(f(X.astype(np.float32)), np.float64)
        return ((fv_ < 0.0015) | stray[ia] & (fv_ < 0.004)) & (k * HAIR["step_mm"] / 1000 < Ls[ia])
    pts, cnt = grow(P, Nn, dir_fn, skin, steps, HAIR["step_mm"] / 1000, lift, rise_m=0.006, alive_fn=alive)
    ok = cnt >= 3
    return dict(kind="hair", pts=pts[ok], cnt=cnt[ok], radius=HAIR["radius_mm"] / 1000, taper=0.35)


def _brows(Vp, Rm, R0, Th, vn, skin, rng, look, scale):
    area = area_cm2(Vp, Th)
    n = int(area * HAIR["brow_density_cm2"] * 3)
    P, Pr, Nn, ti, b = sample_surface(Vp, Rm, Th, n, rng, vn)
    Pb = Pr / scale
    mk, t = _brow_mask(look, Pb)
    keep = rng.random(n) < mk / 3 * 1.6
    if not keep.any():
        return None
    P, Nn, Pb, t, ti = P[keep], Nn[keep], Pb[keep], t[keep], ti[keep]
    Jm = tri_jacobian(Vp, Rm, Th, ti)
    side = np.sign(Pb[:, 0])
    # the brow's hair stream: up at the head (medial end), turning out and lateral along the body and tail
    # (anatomy texts' brow pattern; angles by eye [H])
    dr = np.stack([side * (0.25 + 1.0 * t), 1.0 - 0.95 * t, np.zeros_like(t)], 1)
    dr += rng.normal(0, 0.18, dr.shape)
    dp = np.einsum("nij,nj->ni", Jm, dr)
    dp /= np.linalg.norm(dp, axis=1, keepdims=True) + 1e-12
    M = len(P)
    lift = 0.0004 + 0.0008 * rng.random(M)
    L = (0.006 + 0.005 * rng.random(M)) * (1 - 0.3 * t)

    def dir_fn(X, k, ia):
        return dp[ia]
    step = 0.0012
    pts, cnt = grow(P, Nn, dir_fn, skin, int(0.011 / step) + 1, step, lift, rise_m=0.002,
                    alive_fn=lambda X, k, ia: k * step < L[ia])
    return dict(kind="brow", pts=pts, cnt=cnt, radius=HAIR["brow_radius_mm"] / 1000, taper=0.2)


def _lashes(Vp, elem, eyes, skin, rng, A, scale):
    """Lashes rooted along each lid's margin (the body vertices that ring the eyeball in front), curving away from the
    eye. Counts and lengths: upper 90-160 lashes of 8-12 mm, lower 75-80 of 6-8 mm (the textbook ranges) [S]."""
    out_p, out_c = [], []
    for e in eyes:
        c, r, Rt = e["c"], e["r"], e["R"]
        fwd, up = Rt @ np.array([0, 0, 1.0]), Rt @ np.array([0, 1.0, 0])
        rt = np.cross(up, fwd)
        bv = A.vset["body"]
        D = Vp[bv] - c
        dist = np.linalg.norm(D, axis=1)
        fr = (D @ fwd) / (dist + 1e-9)
        cand = bv[(fr > 0.3) & (dist < r + 0.004)]
        if len(cand) < 10:
            continue
        D = Vp[cand] - c
        ang = np.arctan2(D @ up, D @ rt)
        nb = 72
        bins = ((ang + np.pi) / (2 * np.pi) * nb).astype(int) % nb
        rim = np.full((nb, 3), np.nan)
        for k in range(nb):
            s = np.nonzero(bins == k)[0]
            if len(s):
                j = s[np.argmin(np.linalg.norm(D[s], axis=1))]
                rim[k] = Vp[cand[j]]
        okb = ~np.isnan(rim[:, 0])
        angs = (np.arange(nb) + 0.5) / nb * 2 * np.pi - np.pi
        for upper, (cnt, l0, l1) in ((True, HAIR["lash_upper"]), (False, HAIR["lash_lower"])):
            sel = okb & ((angs > 0.15) & (angs < np.pi - 0.15) if upper else (angs < -0.25) & (angs > -np.pi + 0.25))
            if sel.sum() < 4:
                continue
            a_s = angs[sel]
            o_ = np.argsort(a_s)
            a_s, rs = a_s[o_], rim[sel][o_]
            # roots along the margin, a little outside it
            tq = rng.random(cnt)
            aq = a_s[0] + (a_s[-1] - a_s[0]) * tq
            Pq = np.stack([np.interp(aq, a_s, rs[:, i]) for i in range(3)], 1)
            rad = Pq - c
            rad -= (rad @ fwd)[:, None] * fwd
            rad /= np.linalg.norm(rad, axis=1, keepdims=True) + 1e-12
            Pq = Pq + rad * 0.0004 + fwd * 0.0003
            mid = np.sin(np.clip(tq, 0, 1) * np.pi)            # longer in the middle of the lid
            L = (l0 + (l1 - l0) * mid * rng.random(cnt) ** 0.5) / 1000.0
            steps = 10
            pts = np.zeros((cnt, steps + 1, 3))
            pts[:, 0] = Pq
            curl = (0.9 if upper else 0.5) + 0.3 * rng.random(cnt)
            jit = rng.normal(0, 0.1, (cnt, 3))
            for k in range(1, steps + 1):
                s = k / steps
                # out of the lid margin mostly forward, then curling away from the eye (up for the upper lid, down for
                # the lower); lower lashes are shorter and less curled: by eye [H]
                d = fwd[None] * (1.0 - 0.55 * curl * s)[:, None] + rad * (0.2 + 0.9 * curl * s)[:, None] + jit
                d /= np.linalg.norm(d, axis=1, keepdims=True)
                pts[:, k] = pts[:, k - 1] + d * (L / steps)[:, None]
            out_p.append(pts)
            out_c.append(np.full(cnt, steps + 1))
    if not out_p:
        return None
    return dict(kind="lash", pts=np.concatenate(out_p), cnt=np.concatenate(out_c), radius=HAIR["lash_radius_mm"] / 1000, taper=0.15)


def _stubble(Vp, Rm, R0, Th, vn, skin, rng, look, scale):
    area = area_cm2(Vp, Th)
    n = int(area * HAIR["stubble_density_cm2"])
    P, Pr, Nn, ti, b = sample_surface(Vp, Rm, Th, n, rng, vn)
    mk = _beard_mask(Pr / scale) * min(1.0, look.beard / 0.6)
    keep = rng.random(n) < mk
    if not keep.any():
        return None
    P, Nn, ti = P[keep], Nn[keep], ti[keep]
    Jm = tri_jacobian(Vp, Rm, Th, ti)
    dr = np.array([0, -1.0, 0.25]) + rng.normal(0, 0.35, (len(P), 3))
    dp = np.einsum("nij,nj->ni", Jm, dr)
    dp /= np.linalg.norm(dp, axis=1, keepdims=True) + 1e-12
    lo, hi = HAIR["stubble_len_mm"]
    L = (lo + (hi - lo) * rng.random(len(P))) / 1000
    k = 3
    pts = np.zeros((len(P), k + 1, 3))
    pts[:, 0] = P
    for j in range(1, k + 1):
        # stubble leaves the skin at about 30-45 degrees [H]
        d = dp * 0.75 + Nn * (0.6 - 0.15 * j)
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        pts[:, j] = pts[:, j - 1] + d * (L / k)[:, None]
    return dict(kind="stubble", pts=pts, cnt=np.full(len(P), k + 1), radius=HAIR["stubble_radius_mm"] / 1000, taper=0.5)


def pupils(mesh):
    """The centre of each pupil (posed, studio coordinates): the eye's centre plus its axis times its radius, the axis
    from the rotation of the eye's helper vertices from rest (Kabsch). [(xyz, side)], left eye first."""
    import human
    A = human.assets()
    Vp = mesh["verts"].astype(np.float64)
    out = []
    if "eye_id" not in mesh:
        return out
    for s in "lr":
        ev = A.vset["eye_" + s]
        c = Vp[ev].mean(0)
        Rot = _kabsch(A.V0[ev] - A.eye_c[s], Vp[ev] - c)
        r = float(np.linalg.norm(Vp[ev] - c, axis=1).mean())
        out.append((c + Rot @ np.array([0, 0, 1.0]) * r * 0.82, s))
    return out


def project(cam, P, W, H):
    """Studio-coordinate points to canvas pixels (x, y) for scene.cam = (ro, rt, up, fw, f)."""
    ro, rt, up, fw, f = cam
    D = np.atleast_2d(np.asarray(P, np.float64)) - np.asarray(ro, np.float64)
    z = D @ np.asarray(fw, np.float64)
    x = f * (D @ np.asarray(rt, np.float64)) / z * (H / 2) + W / 2 - 0.5
    y = -f * (D @ np.asarray(up, np.float64)) / z * (H / 2) + H / 2 - 0.5
    return np.stack([x, y], 1)


# ---------------------------------------------------------------- the whole scene
def supported(spec):
    return all(o.get("type") in ("person", "hand") for o in spec.get("objects", []))


def export(scene, W, H, path):
    sp = scene.spec
    cyc = dict(sp.get("cycles", {}))
    ro, rt, up, fw, f = scene.cam
    ro, rt, up, fw = (np.asarray(v, np.float64) for v in (ro, rt, up, fw))
    fov = 2 * math.atan(1 / f)

    def frustum(V, margin=0.25):
        D = V - ro
        z = D @ fw
        x = (D @ rt) / np.maximum(z, 1e-3) * f
        y = (D @ up) / np.maximum(z, 1e-3) * f
        a = W / H
        return (z > 0.05) & (np.abs(x) < a * (1 + margin)) & (np.abs(y) < 1 + margin)
    rng = np.random.default_rng(5)
    people = []
    objs = sp.get("objects", [])
    for nd in scene.meshes:
        if "look" not in nd.mesh:
            continue
        o = next((o_ for i, o_ in enumerate(objs) if (o_.get("id") or f"{o_['type']}{sum(1 for x in objs[:i] if x['type'] == o_['type'])}") == nd.owner), {})
        hair_nodes = [n for n in scene.nodes if getattr(n, "owner", None) == nd.owner and getattr(n, "element", "") == "hair" and n.f is not None]
        people.append(export_person(nd, hair_nodes, o, None, rng, frustum))
    sun = sp.get("sun", {})
    az, el = math.radians(sun.get("azimuth", 40)), math.radians(sun.get("elevation", 25))
    ld = np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)])
    amb = sp.get("ambient", {})
    sky = sp.get("sky", {})
    # the focus: the nearer eye of the first person (a portrait photographer focuses on the near eye)
    focus = None
    if people and people[0]["eyes"]:
        cs = [e["c"] + 0 for e in people[0]["eyes"]]
        focus = float(min(np.linalg.norm(c - ro) for c in cs))
    arrays = {}
    meta = dict(W=W, H=H, fov=fov, cam=dict(pos=list(to_b(ro)), rt=list(to_b(rt)), up=list(to_b(up)), fw=list(to_b(fw))),
                sun=dict(dir=list(to_b(ld)), color=list(srgb_to_lin(hexc(sun.get("color", "#fff0d8")))),
                         strength=float(sun.get("intensity", 1.6)) * math.pi, angle=float(sun.get("angle", 2.0))),
                world=dict(sky=list(srgb_to_lin(hexc(amb.get("sky", sky.get("zenith", "#6a7890"))))),
                           ground=list(srgb_to_lin(hexc(amb.get("ground", "#5a4a3a")))),
                           strength=float(amb.get("intensity", 0.45))),
                lights=[dict(pos=list(to_b(L["pos"])), color=list(srgb_to_lin(hexc(L.get("color", "#ffc070")))),
                             power=float(L.get("intensity", 2.0)) * 4 * math.pi * float(L.get("radius", 3.0)) ** 2)
                        for L in sp.get("lights", [])],
                samples=int(cyc.get("samples", 96)), fstop=float(cyc.get("fstop", 8)), focus=focus,
                denoise=bool(cyc.get("denoise", True)), threads=int(cyc.get("threads", 0)), region=cyc.get("region"), people=[])
    for i, p in enumerate(people):
        pre = f"p{i}_"
        arrays[pre + "V"] = to_b(p["V"]).astype(np.float32)
        arrays[pre + "Q"] = p["Q"].astype(np.int32)
        arrays[pre + "teeth"] = p["teeth"].astype(np.int32)
        arrays[pre + "tongue"] = p["tongue"].astype(np.int32)
        for k, v in p["attrs"].items():
            arrays[pre + "a_" + k] = (to_b(v) if k == "rest" else v).astype(np.float32)
        pm = dict(eyes=[], strands=[], iris=p["iris"], sclera=p["sclera"], mel_hair=p["mel_hair"], mel_brow=p["mel_brow"],
                  grey=p["grey"], age=p["age"], oil=p["oil"], detail=p["detail"], seed=p["seed"], scale=p["scale"],
                  beard=p["beard_amt"])
        for j, e in enumerate(p["eyes"]):
            # the eye's frame in Blender coordinates: columns are the local x, y, z (z the visual axis)
            Rb = np.stack([to_b(e["R"][:, a]) for a in range(3)], 1)
            pm["eyes"].append(dict(c=list(to_b(e["c"])), r=e["r"], R=Rb.tolist()))
        for j, s in enumerate(p["strands"]):
            key = f"{pre}s{j}"
            pts, cnt = s["pts"], s["cnt"]
            flat = np.concatenate([pts[a, :cnt[a]] for a in range(len(pts))])
            arrays[key + "_pts"] = to_b(flat).astype(np.float32)
            arrays[key + "_cnt"] = cnt.astype(np.int32)
            pm["strands"].append(dict(key=key, kind=s["kind"], radius=s["radius"], taper=s["taper"]))
        d = p["droplets"]
        if d is not None:
            arrays[pre + "drop_c"] = to_b(d["c"]).astype(np.float32)
            arrays[pre + "drop_n"] = to_b(d["n"]).astype(np.float32)
            arrays[pre + "drop_r"] = np.asarray(d["r"], np.float32)
            pm["droplets"] = True
        meta["people"].append(pm)
    np.savez(path + ".npz", **arrays)
    json.dump(meta, open(path + ".json", "w"), indent=1)
    return meta


def tone(rgb_lin, alpha, sp, subject):
    """Linear render to display values: an exposure that puts the subject's bright skin where a photograph puts it,
    then a filmic curve (Narkowicz's fit of the ACES reference rendering transform, 2015), then sRGB. The exposure
    target (the subject's 99th percentile luminance at `white`, default 0.82, after the curve) is by eye [H]; `exposure` in the scene
    (EV, default 0) shifts it."""
    Y = 0.2126 * rgb_lin[..., 0] + 0.7152 * rgb_lin[..., 1] + 0.0722 * rgb_lin[..., 2]
    sel = subject & (alpha > 0.99)
    cyc = sp.get("cycles", {})
    ref = float(cyc["ref_lum"]) if "ref_lum" in cyc else (float(np.percentile(Y[sel], 99)) if sel.sum() > 100 else float(np.percentile(Y, 99)))
    print(f"photoreal: exposure reference (the subject's 99th percentile luminance) {ref:.4f}", file=sys.stderr)
    white = float(cyc.get("white", 0.82))
    aces = lambda x: np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0, 1)
    # the exposure k with aces(k * ref) = 0.95 (bisection)
    lo, hi = 1e-4, 1e4
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if aces(np.array(mid * ref)) < white else (lo, mid)
    k = math.sqrt(lo * hi) * 2 ** float(sp.get("cycles", {}).get("exposure", 0.0))
    out = lin_to_srgb(aces(rgb_lin * k))
    return out, ref


def render(scene, W, H, workdir=None):
    """Render the scene's people with Cycles at W x H. Returns (uint8 image, hair coverage (H,W) or None, info)."""
    if not available():
        raise RuntimeError(f"no bpy Python at {BPY_PY}: run python3 tools/setup_photoreal.py")
    sp = scene.spec
    tmp = workdir or tempfile.mkdtemp(prefix="teodor_cycles_")
    os.makedirs(tmp, exist_ok=True)
    base = os.path.join(tmp, "scene")
    t0 = time.time()
    export(scene, W, H, base)
    t1 = time.time()
    # a render is cached by what it was given (the exported scene and both scripts): `scene` run again, or a detail
    # of the same scene, reuses it instead of path-tracing again (~/.cache/teodor/cycles, the newest 8 kept)
    import hashlib
    hsh = hashlib.sha1()
    for f_ in (base + ".npz", base + ".json", os.path.join(HERE, "photoreal_bpy.py")):
        hsh.update(open(f_, "rb").read())
    cdir = os.path.expanduser("~/.cache/teodor/cycles")
    cpath = os.path.join(cdir, hsh.hexdigest()[:20] + ".npz")
    if os.path.exists(cpath):
        z = np.load(cpath)
        beauty, ids = z["beauty"].astype(np.float32), z["ids"].astype(np.float32)
        print(f"photoreal: cached render {os.path.basename(cpath)}", file=sys.stderr)
    else:
        r = subprocess.run([BPY_PY, os.path.join(HERE, "photoreal_bpy.py"), base], capture_output=True, text=True)
        if r.returncode != 0:
            sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
            raise RuntimeError("photoreal: the Cycles render failed")
        for ln in r.stdout.splitlines():
            if ln.startswith("photoreal"):
                print(ln, file=sys.stderr)
        beauty = np.load(base + "_beauty.npy")          # (H, W, 4) linear, top row first
        ids = np.load(base + "_ids.npy")                # (H, W, 4): R skin and eyes, G hair, B cloth, A coverage
        try:
            os.makedirs(cdir, exist_ok=True)
            tmpc = cpath + ".tmp.npz"
            np.savez_compressed(tmpc, beauty=beauty.astype(np.float16), ids=ids.astype(np.float16))
            os.replace(tmpc, cpath)
            old_ = sorted((os.path.join(cdir, f_) for f_ in os.listdir(cdir) if f_.endswith(".npz")), key=os.path.getmtime)
            for f_ in old_[:-8]:
                os.remove(f_)
        except OSError:
            pass
    rgb, a = beauty[..., :3].astype(np.float64), beauty[..., 3].astype(np.float64)
    subject = (ids[..., 0] > 0.5)
    # Cycles' transparent film is premultiplied: unpremultiply, tone, then lay it over the paper with its coverage
    aa = np.clip(a, 0, 1)[..., None]
    straight = np.where(aa > 1e-4, rgb / np.maximum(aa, 1e-4), 0)
    disp, ref_lum = tone(straight, a, sp, subject)
    bg = sp.get("background")
    bgc = hexc(bg) if bg else hexc(sp.get("sky", {}).get("horizon", "#e8d0b0"))
    img = np.clip(disp * aa + (1 - aa) * bgc[None, None], 0, 1)
    info = dict(export_s=round(t1 - t0, 1), render_s=round(time.time() - t1, 1), ref_lum=round(ref_lum, 6))
    if not workdir:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    hair = ids[..., 1] / np.maximum(ids[..., 3], 1e-6) * (ids[..., 3] > 0.3)
    return (img * 255 + 0.5).astype(np.uint8), hair, info
