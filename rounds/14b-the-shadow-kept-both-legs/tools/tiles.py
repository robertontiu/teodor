"""Lay the floor tile by tile, like a mosaicist: one flat stroke per tile along its long axis."""
import sys, json, math, subprocess, numpy as np
from scipy.ndimage import gaussian_filter
D = "/home/claude/v14f"
def hx(h):
    h = h.lstrip("#"); return np.array([int(h[i:i+2], 16)/255 for i in (0, 2, 4)], np.float32)
def tohex(c):
    c = np.clip(c, 0, 1); return "#%02x%02x%02x" % tuple(int(round(v*255)) for v in c)

def fields(P):
    y, x = np.mgrid[0:1600, 0:1200].astype(np.float32)
    f0, f1, amp, ph = P.get("furrow", [520, 760, 150, 0.4])
    t = y / 1600
    xf = f0 + (f1 - f0) * t + amp * np.sin(t * math.pi * 1.6 + ph)
    d = (x - xf) / 600
    u = np.sign(d) * np.abs(d) ** P.get("pow", 0.55) * P.get("cols", 7.0)
    v = y / P.get("row", 118.0) + P.get("wave", 0.55) * np.sin(x / 230.0 + y / 310.0 + 1.0) + 0.25 * np.sin(d * 5.0)
    return x, y, d, u, v, xf

def cells(label, minpix=30, gu=None):
    x, y = np.meshgrid(np.arange(1200, dtype=np.float64), np.arange(1600, dtype=np.float64))
    ids, inv = np.unique(label, return_inverse=True); inv = inv.ravel()
    n = np.bincount(inv); sx = np.bincount(inv, x.ravel()); sy = np.bincount(inv, y.ravel())
    cx, cy = sx/n, sy/n
    dx, dy = x.ravel()-cx[inv], y.ravel()-cy[inv]
    sxx = np.bincount(inv, dx*dx)/n; syy = np.bincount(inv, dy*dy)/n; sxy = np.bincount(inv, dx*dy)/n
    out = []
    for i in range(len(ids)):
        if ids[i] < 0 or n[i] < minpix: continue
        C = np.array([[sxx[i], sxy[i]], [sxy[i], syy[i]]])
        g = np.array([gu[0][int(cy[i]), int(cx[i])], gu[1][int(cy[i]), int(cx[i])]], float)
        g /= (np.linalg.norm(g) + 1e-9); t = np.array([-g[1], g[0]])
        L, S = math.sqrt(12*max(t @ C @ t, 1e-3)), math.sqrt(12*max(g @ C @ g, 1e-3))
        out.append(dict(id=int(ids[i]), c=(cx[i], cy[i]), ax=t, L=L, S=S, n=int(n[i])))
    return out

def act(felt, intents):
    for it in intents:
        r = subprocess.run(["python3", f"{D}/studio.py", "act", json.dumps({"felt": felt, "do": [it]})], capture_output=True, text=True)
        if r.returncode: print(r.stderr[-800:]); sys.exit(1)

def lay(mode, seed=1):
    spec = json.load(open(f"{D}/main_scene_final.json")); P = spec["compose"]
    x, y, d, u, v, xf = fields(P)
    fig = np.load(f"{D}/idea_A3_fig.npy").astype(np.float32); sh = np.load(f"{D}/idea_A3_shadow.npy").astype(np.float32)
    iu, iv = np.floor(u).astype(int), np.floor(v).astype(int)
    lab = (iu + 50) * 1000 + (iv + 50)
    chk = (iu + iv) % 2
    near = np.exp(-(d / 0.33) ** 2)
    rng = np.random.default_rng(seed)
    A, B, A2, B2 = hx(P["A"]), hx(P["B"]), hx(P["A2"]), hx(P["B2"])
    S1, S2 = hx(P["shadow"]), hx(P["shadow2"])
    if mode == "shadow":
        lab = np.where(sh > 0.5, lab, -1)
    strokes = []
    gy_, gx_ = np.gradient(gaussian_filter(np.sign(d) * np.abs(d) ** 0.9, 3))
    for c in cells(lab, gu=(gx_, gy_)):
        cx, cy = c["c"]; ix, iy = int(min(1199, cx)), int(min(1599, cy))
        if fig[iy, ix] > 0.75 and c["n"] < 9000: continue
        k = chk[iy, ix]; nr = near[iy, ix]
        if mode == "shadow":
            col = (S2 if k else S1) + rng.normal(0, 0.03, 3)
            col = col * (0.9 + 0.25 * nr)
        else:
            col = ((B * (1 - nr) + B2 * nr) if k else (A * (1 - nr) + A2 * nr)) + rng.normal(0, 0.035, 3)
        L, S = c["L"], c["S"]
        size = max(3.0, S * 0.88)
        h = max(2.0, (L - S * 0.55) / 2)
        ax = c["ax"] * (1 if rng.random() < 0.5 else -1)
        npass = 2 if S > 1.25 * L else 1
        for p in range(npass):
            off = (p - (npass - 1) / 2) * S * 0.45
            nx, ny = -ax[1] * off, ax[0] * off
            sz = size / npass * 1.1 if npass > 1 else size
            strokes.append({"pts": [[cx - ax[0]*h + nx, cy - ax[1]*h + ny], [cx + nx, cy + ny], [cx + ax[0]*h + nx, cy + ax[1]*h + ny]],
                            "size": round(sz, 1), "color": tohex(col), "_k": int(k), "_near": float(nr), "_x": cx})
    return strokes

if __name__ == "__main__":
    mode, sel = sys.argv[1], sys.argv[2]
    felt = json.loads(sys.argv[3])
    st = lay(mode)
    if sel == "k0": st = [s for s in st if s["_k"] == 0]
    if sel == "k1": st = [s for s in st if s["_k"] == 1]
    for s in st:
        for q in ("_k", "_near", "_x"): s.pop(q)
        s["pts"] = [[round(a, 1), round(b, 1)] for a, b in s["pts"]]
    print(len(st), "tiles")
    B = 250
    act(felt, [{"type": "strokes", "brush": "flat", "edge": "hard", "load": 1.1, "impasto": 0.45, "pressure": 0.9, "strokes": st[i:i+B]} for i in range(0, len(st), B)])
