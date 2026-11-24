"""Phase 2 helpers: new lay figure masks, projected joints, tile laying inside a mask."""
import sys, json, math, subprocess, shutil, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, binary_dilation
D = "/home/claude/v14f"; sys.path.insert(0, D)
import tiles as T
SPEC = json.load(open(f"{D}/scene_P3.json")); P = SPEC["compose"]
FIGM = np.load(f"{D}/idea_P3_fig.npy").astype(np.float32)
SHM = np.load(f"{D}/idea_P3_shadow.npy").astype(np.float32)
OLDFIG = np.load(f"{D}/idea_A3_fig.npy").astype(np.float32); OLDSH = np.load(f"{D}/idea_A3_shadow.npy").astype(np.float32)

def joints(s=1.06, origin=(0, 20.9, 0), res=420):
    J = json.load(open(f"{D}/pose_J.json")); cam = SPEC["camera"]
    out = {}
    th = math.radians(P["roll"]); z = P["zoom"]; ch = res / z; cw = ch * 0.75
    cx = res/2 + P["dx"] * res; cy = res/2 + P["dy"] * res
    for k, v in J.items():
        w = np.array(origin) + np.array(v) * s
        dz = cam["pos"][2] - w[2]; t = math.tan(math.radians(cam["fov"]) / 2)
        px = res/2 + (w[0] - cam["pos"][0]) / dz / t * res/2
        py = res/2 - (w[1] - cam["pos"][1]) / dz / t * res/2
        dx, dy = px - res/2, py - res/2            # PIL rotate: counter-clockwise by th
        rx = dx * math.cos(th) + dy * math.sin(th); ry = -dx * math.sin(th) + dy * math.cos(th)
        px, py = res/2 + rx, res/2 + ry
        out[k] = (round((px - (cx - cw/2)) / cw * 1200, 1), round((py - (cy - ch/2)) / ch * 1600, 1))
    return out
JP = joints()

def act(felt, do):
    do = do if isinstance(do, list) else [do]
    for i in range(0, len(do), 4):
        s = json.dumps({"felt": dict(zip(("arousal", "tension", "valence", "care"), felt)), "do": do[i:i+4]})
        r = subprocess.run(["python3", f"{D}/studio.py", "act", s], capture_output=True, text=True)
        if r.returncode: print(r.stderr[-1500:]); sys.exit(1)
def look(*a, to=None):
    subprocess.run(["python3", f"{D}/studio.py", "look", *map(str, a)], check=True, capture_output=True)
    if to: shutil.copy(f"{D}/main_look.png", f"/tmp/v14f/{to}.png")
def journal(line): open(f"{D}/journal.md", "a").write(line + "\n")
def dry(k=0.9): subprocess.run(["python3", f"{D}/studio.py", "dry", str(k)], check=True, capture_output=True)

def floor_colour(x, y, k, nr, rng, jit=0.03):
    """lit from lower right: pale there, deep upper left; k=0 pink, 1 turquoise/lemon"""
    hx = T.hx
    A = hx(P["A"]) * (1 - nr) + hx(P["A2"]) * nr; B = hx(P["B"]) * (1 - nr) + hx(P["B2"]) * nr
    c = B if k else A
    g = min(1, max(0, (1200 - x) / 1200 * 0.55 + (1600 - y) / 1600 * 0.45))
    deep = hx("#0a8494") if k else hx("#bf0f78")
    kd = max(0, (g - 0.42) / 0.58) ** 1.2 * 0.85 * (1 - 0.6 * nr)
    c = c * (1 - kd) + deep * kd
    kp = max(0, (0.5 - g) / 0.5) ** 1.3 * 0.6
    c = c * (1 - kp) + hx("#fff4d2") * kp
    return c + rng.normal(0, jit, 3)

def tiles_in(mask, mode="floor", sel=None, seed=1, skip_fig=True, scale=0.88, colour=None):
    x, y, d, u, v, xf = T.fields(P)
    iu, iv = np.floor(u).astype(int), np.floor(v).astype(int)
    lab = np.where(mask, (iu + 50) * 1000 + (iv + 50), -1)
    chk = (iu + iv) % 2; near = np.exp(-(d / 0.33) ** 2)
    rng = np.random.default_rng(seed)
    gy_, gx_ = np.gradient(gaussian_filter(np.sign(d) * np.abs(d) ** 0.9, 3))
    st = []
    for c in T.cells(lab, gu=(gx_, gy_)):
        cx, cy = c["c"]; ix, iy = int(min(1199, cx)), int(min(1599, cy))
        if skip_fig and FIGM[iy, ix] > 0.6: continue
        k = int(chk[iy, ix]); nr = float(near[iy, ix])
        if sel is not None and k != sel: continue
        if colour: col = colour(cx, cy, k, nr, rng)
        elif mode == "shadow":
            col = (T.hx("#1d4fa8") if k else T.hx("#2a1a96")) + rng.normal(0, 0.025, 3)
        else: col = floor_colour(cx, cy, k, nr, rng)
        L, S = c["L"], c["S"]; size = max(3.0, S * scale); h = max(2.0, (L - S * 0.55) / 2)
        ax = c["ax"] * (1 if rng.random() < 0.5 else -1)
        npass = 2 if S > 1.25 * L else 1
        for p in range(npass):
            off = (p - (npass - 1) / 2) * S * 0.45; nx, ny = -ax[1] * off, ax[0] * off
            sz = size / npass * 1.1 if npass > 1 else size
            st.append({"pts": [[round(cx - ax[0]*h + nx, 1), round(cy - ax[1]*h + ny, 1)], [round(cx + nx, 1), round(cy + ny, 1)], [round(cx + ax[0]*h + nx, 1), round(cy + ax[1]*h + ny, 1)]],
                       "size": round(sz, 1), "color": T.tohex(col)})
    return st
def lay(felt, st, B=250, **kw):
    base = dict(type="strokes", brush="flat", edge="hard", load=1.1, impasto=0.45, pressure=0.9); base.update(kw)
    for i in range(0, len(st), B): act(felt, [dict(base, strokes=st[i:i+B])])
def poly(mask, step=6):
    from skimage import measure
    c = max(measure.find_contours(mask.astype(float), 0.5), key=len)[::step]
    return [[round(float(p[1]), 1), round(float(p[0]), 1)] for p in c]

LIT = np.array([0.87, 0.5])
def along(keys, off, size, col):
    """one stroke parallel to a limb, offset (px) toward the light (+) or the shade (-)"""
    pts = np.array([JP[k] if isinstance(k, str) else k for k in keys], float); q = []
    for i, p in enumerate(pts):
        t = pts[min(i+1, len(pts)-1)] - pts[max(i-1, 0)]; t /= np.linalg.norm(t)
        n = np.array([-t[1], t[0]]); n = n if n @ LIT > 0 else -n
        q.append((p + n * off).round(1).tolist())
    return {"pts": q, "size": size, "color": col}
def at(a, b, t, off=0.0):
    """point at fraction t from joint a to joint b, pushed off (px) toward the light"""
    pa, pb = np.array(JP[a] if isinstance(a, str) else a, float), np.array(JP[b] if isinstance(b, str) else b, float)
    d = (pb - pa) / np.linalg.norm(pb - pa); n = np.array([-d[1], d[0]]); n = n if n @ LIT > 0 else -n
    return (pa + (pb - pa) * t + n * off).round(1).tolist()
FIG = {"type": "poly", "pts": json.load(open(f"{D}/fig2_poly.json"))}
SH = {"type": "poly", "pts": json.load(open(f"{D}/shadow2_poly.json"))}

def crisp_tiles(zone, felt=(0.25, 0.05, 0.8, 0.97), sat=1.22, val=1.02, minpix=150, colour=None, extra=None):
    """Hard-edge tiles: each tile filled with a few parallel flat strokes clipped to its exact outline."""
    import colorsys
    from skimage import measure
    x, y, d, u, v, xf = T.fields(P)
    iu, iv = np.floor(u).astype(int), np.floor(v).astype(int)
    lab = np.where(zone, (iu + 50) * 1000 + (iv + 50), -1); chk = (iu + iv) % 2
    cur = np.load(f"{D}/main_col.npy").astype(np.float32)
    gy_, gx_ = np.gradient(gaussian_filter(np.sign(d) * np.abs(d) ** 0.9, 3))
    its = []
    for c in T.cells(lab, minpix=minpix, gu=(gx_, gy_)):
        m = lab == c["id"]
        cs = measure.find_contours(np.pad(m, 1).astype(float), 0.5)
        ct = max(cs, key=len) - 1; step = max(1, len(ct) // 60)
        pts = [[round(float(q[1]), 1), round(float(q[0]), 1)] for q in ct[::step]]
        if len(pts) < 4: continue
        cx, cy = c["c"]; k = int(chk[int(cy), int(cx)])
        if colour: col = colour(cx, cy, k)
        else:
            r, g, b = np.median(cur[m], 0); h, s, vv = colorsys.rgb_to_hsv(r, g, b)
            col = np.array(colorsys.hsv_to_rgb(h, min(1, s * sat), min(1, vv * val)))
        ax, L, S = c["ax"], c["L"], c["S"]; n = np.array([-ax[1], ax[0]])
        size = float(min(46, max(6, S * 0.75))); k_ = int(np.ceil(S / (size * 0.7)))
        st = []
        for j in range(k_):
            off = (j - (k_ - 1) / 2) * size * 0.7; p0 = np.array([cx, cy]) + n * off
            st.append({"pts": [(p0 - ax * (L / 2 + size)).round(1).tolist(), p0.round(1).tolist(), (p0 + ax * (L / 2 + size)).round(1).tolist()], "size": round(size, 1), "color": T.tohex(col)})
        it = {"type": "strokes", "brush": "flat", "strokes": st, "region": {"type": "poly", "pts": pts}, "clip": True, "edge": "hard", "load": 1.5, "pressure": 1.0, "impasto": 0.35}
        if extra: it.update(extra)
        its.append(it)
    act(felt, its); return len(its)

def quad(a, b, w, e0=0, e1=0):
    a, b = np.array(a, float), np.array(b, float); d = (b - a) / np.linalg.norm(b - a); n = np.array([-d[1], d[0]])
    a2, b2 = a - d * e0, b + d * e1
    return [(a2 + n * w / 2).tolist(), (b2 + n * w / 2).tolist(), (b2 - n * w / 2).tolist(), (a2 - n * w / 2).tolist()]
def mask_poly(pts, with_fig=True):
    from PIL import ImageDraw
    from skimage import measure
    im = Image.new("L", (1200, 1600), 0); ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=255)
    m = np.array(im) > 0
    if with_fig: m &= FIGM > 0.5
    c = max(measure.find_contours(np.pad(m, 1).astype(float), 0.5), key=len) - 1
    return {"type": "poly", "pts": [[round(float(q[1]), 1), round(float(q[0]), 1)] for q in c[::max(1, len(c) // 120)]]}
def part(a, b, w, region, base, shade, deep, light, ext=90, felt=(0.4, 0.05, 0.9, 0.9), imp=0.6):
    """a limb or a garment as cloth: long parallel strokes running past both ends, cut by the region; tone in planes"""
    a, b = np.array(a, float), np.array(b, float); d = (b - a) / np.linalg.norm(b - a); n = np.array([-d[1], d[0]]); n = n if n @ LIT > 0 else -n
    def s(off, size, col): return {"pts": [(a - d * ext + n * off * w).round(1).tolist(), ((a + b) / 2 + n * off * w).round(1).tolist(), (b + d * ext + n * off * w).round(1).tolist()], "size": round(size * w, 1), "color": col}
    basest = [s(o, 0.34, base) for o in (-0.42, -0.21, 0, 0.21, 0.42)]
    act(felt, [{"type": "strokes", "brush": "flat", "strokes": basest, "region": region, "clip": True, "edge": "hard", "load": 1.6, "impasto": imp, "pressure": 1.0},
               {"type": "strokes", "brush": "round", "strokes": [s(-0.31, 0.30, shade), s(-0.44, 0.13, deep)], "region": region, "clip": True, "edge": "soft", "load": 1.2, "impasto": 0.3},
               {"type": "strokes", "brush": "round", "strokes": [s(0.22, 0.30, light)], "region": region, "clip": True, "edge": "soft", "load": 1.5, "impasto": 0.8}])
def contour_lines(skip=62, lit_col="#ffffff", sh_col="#7a72cf", lit_size=5.0, sh_size=3.2, only=None):
    from skimage import measure
    from scipy.ndimage import uniform_filter1d
    m = gaussian_filter((FIGM > 0.5).astype(float), 5)
    c = max(measure.find_contours(m, 0.5), key=len)
    c = np.stack([uniform_filter1d(c[:, 0], 25, mode="wrap"), uniform_filter1d(c[:, 1], 25, mode="wrap")], 1)
    t = np.roll(c, -6, 0) - np.roll(c, 6, 0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-9
    n = np.stack([t[:, 1], -t[:, 0]], 1)
    out = np.array([m[int(np.clip(p[0] + q[0] * 6, 0, 1599)), int(np.clip(p[1] + q[1] * 6, 0, 1199))] < 0.5 for p, q in zip(c, n)]); n[~out] *= -1
    lit = n[:, 1] * 0.87 + n[:, 0] * 0.5
    sp = np.array([JP["head"], JP["ha_l"], JP["ha_r"], (np.array(JP["an_l"]) + JP["toe_l"]) / 2, (np.array(JP["an_r"]) + JP["toe_r"]) / 2])
    keep = np.array([np.min(np.hypot(sp[:, 0] - p[1], sp[:, 1] - p[0])) > skip for p in c])
    if only is not None: keep &= np.array([only(p[1], p[0]) for p in c])
    def runs(mask):
        R, cur = [], []
        for i in range(0, len(c), 7):
            if mask[i]: cur.append([round(float(c[i, 1]), 1), round(float(c[i, 0]), 1)])
            else:
                if len(cur) >= 4: R.append(cur)
                cur = []
        if len(cur) >= 4: R.append(cur)
        o = []
        for r in R:
            for j in range(0, len(r), 14):
                if len(r[j:j+15]) >= 3: o.append(r[j:j+15])
        return o
    return ([{"pts": p, "size": lit_size, "color": lit_col} for p in runs(keep & (lit > 0.25))],
            [{"pts": p, "size": sh_size, "color": sh_col} for p in runs(keep & (lit < -0.25))])

SK, SL, SD = "#f7a48c", "#ffd9c2", "#de6f8c"
def _rot(v, deg):
    r = math.radians(deg); return np.array([v[0]*math.cos(r) - v[1]*math.sin(r), v[0]*math.sin(r) + v[1]*math.cos(r)])
def hand(wrist, u, scale, angles, thumb, curl=0.0):
    u = np.array(u, float); u /= np.linalg.norm(u); n = np.array([-u[1], u[0]]); w = np.array(wrist, float); s = []
    palm = w + u * 24 * scale
    s.append({"pts": [(w - u * 6 * scale).tolist(), (palm + u * 10 * scale).tolist()], "size": 46 * scale, "color": SK})
    s.append({"pts": [(w + n * 4).tolist(), (palm + n * 4).tolist()], "size": 26 * scale, "color": SL})
    for i, (ang, Lf) in enumerate(angles):
        d = _rot(u, ang); base = palm + u * 12 * scale + n * ((i - 1.5) * 11.5 * scale)
        mid = base + d * Lf * 0.55 * scale; tip = mid + _rot(d, curl) * Lf * 0.5 * scale
        s.append({"pts": [base.round(1).tolist(), mid.round(1).tolist(), tip.round(1).tolist()], "size": 11.5 * scale, "color": SK})
        s.append({"pts": [(base + n * 1.5).round(1).tolist(), (mid + n * 1.5).round(1).tolist()], "size": 5 * scale, "color": SL})
        s.append({"pts": [(base - n * 6.5 * scale).round(1).tolist(), (base - n * 6.5 * scale + d * Lf * 0.35 * scale).round(1).tolist()], "size": 2.5, "color": SD})
    d = _rot(u, thumb[0]); base = w + u * 8 * scale + n * math.copysign(17, thumb[0]) * scale
    s.append({"pts": [base.round(1).tolist(), (base + d * thumb[1] * 0.6 * scale).round(1).tolist(), (base + _rot(d, -thumb[0] * 0.35) * thumb[1] * scale).round(1).tolist()], "size": 13 * scale, "color": SK})
    return s
