# Builds the episode files from the line design: which areas each colour block prints (seed strokes),
# and the visible key lines by part (hidden contours removed by overlap, as a carver would not cut them).
import json, math, sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design3 as D

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = D.W, D.H
SH, LN = D.SH, D.LN
NOT_OCCLUDER = {"stubble", "peel_ground_in"}

def zbuffer():
    im = Image.new("I", (W, H), 0)
    dr = ImageDraw.Draw(im)
    for i, s in enumerate(SH):
        if s["name"] in NOT_OCCLUDER or s["name"].startswith("hem") or s["name"].startswith("stripe"):
            continue
        dr.polygon([(x, y) for x, y in s["pts"]], fill=i + 1)
    return np.array(im, np.int32)

REF = None
def ref_lab():
    global REF
    if REF is None:
        import subprocess
        subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), f"{OUT}/plan/schema_p3_blocks.svg", "-o", "/tmp/t18p3/ref.png"], check=True)
        a = np.asarray(Image.open("/tmp/t18p3/ref.png").convert("RGB"), np.float32) / 255
        REF = a
    return REF

def close_to(fill):
    a = ref_lab()
    c = np.array([int(fill[1:3], 16), int(fill[3:5], 16), int(fill[5:7], 16)], np.float32) / 255
    return np.abs(a - c).max(-1) < 0.035

def interior_point(s, zb, i):
    """A seed point well inside the visible part of shape i, on its own colour (not on a motif or a line)."""
    m = (zb == i + 1) & close_to(s["fill"])
    if s["name"] in NOT_OCCLUDER or s["name"].startswith("stripe"):
        im = Image.new("L", (W, H), 0); ImageDraw.Draw(im).polygon([(x, y) for x, y in s["pts"]], fill=1)
        m = (np.array(im) > 0) & close_to(s["fill"])
    if m.sum() < 6:
        return None
    from scipy.ndimage import distance_transform_edt, label
    lb, n = label(m)
    res = []
    for k in range(1, n + 1):
        mk = lb == k
        if mk.sum() < 40:
            continue
        res.append(_inner(mk))
    return res

def _inner(m):
    from scipy.ndimage import distance_transform_edt
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    d = distance_transform_edt(np.pad(m[y0:y1, x0:x1], 1))[1:-1, 1:-1]
    k = np.argmax(d)
    yy, xx = np.unravel_index(k, d.shape)
    return float(xx + x0), float(yy + y0), float(d.max())

def visible_runs(pts, zmax, zb, minlen=5.0):
    """Split a polyline into the runs not covered by shapes above zmax (index+1 <= zmax is visible)."""
    dense = []
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L / 2))
        for k in range(n):
            t = k / n; dense.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    dense.append(pts[-1])
    runs, cur = [], []
    for x, y in dense:
        xi, yi = int(round(x)), int(round(y))
        if not (0 <= xi < W and 0 <= yi < H):
            vis = False
        else:
            nb = zb[max(0, yi - 1):yi + 2, max(0, xi - 1):xi + 2]
            vis = nb.min() <= zmax
        if vis:
            cur.append((round(x, 1), round(y, 1)))
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    out = []
    for r in runs:
        L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(r[:-1], r[1:]))
        if L >= minlen:
            step = max(1, len(r) // 40)       # thin the points: the hand interpolates
            rr = r[::step]
            if rr[-1] != r[-1]: rr.append(r[-1])
            out.append(rr)
    return out

def build():
    zb = zbuffer()
    np.save("/tmp/t18p3/zb.npy", zb)
    # ---- block seeds, grouped by colour
    seeds = {}
    for i, s in enumerate(SH):
        if s["name"].startswith("hem") or s["fill"].lower() in ("#f3eee4", D.PAPER):
            continue
        ps = interior_point(s, zb, i)
        if not ps:
            continue
        for x, y, r in ps:
            sz = max(2.0, min(8.0, r * 0.8))
            seeds.setdefault(s["fill"], []).append({"pts": [[x - sz * 0.3, y], [x + sz * 0.3, y + 0.5]], "size": round(sz, 1), "color": s["fill"], "name": s["name"]})
    # ---- key lines by part
    keys = {}
    for i, s in enumerate(SH):
        if not s["key"]:
            continue
        pts = s["pts"] + [s["pts"][0]]
        for run in visible_runs(pts, i + 1, zb):
            keys.setdefault(s["part"], []).append({"pts": run, "color": D.C["key"], "name": s["name"]})
    for l in LN:
        for run in visible_runs(l["pts"], l["z"], zb, minlen=3.0):
            keys.setdefault(l["part"], []).append({"pts": run, "color": l["color"], "name": l["name"]})
    # cobble lines: visible only on the pavement (index 1)
    for c in D.COB:
        for run in visible_runs([tuple(c[0]), tuple(c[1])], 1, zb, minlen=8.0):
            keys.setdefault("cobble", []).append({"pts": run, "color": D.C["cob"], "name": "cobble"})
    json.dump(seeds, open(f"{OUT}/plan/seeds3.json", "w"))
    json.dump(keys, open(f"{OUT}/plan/keys3.json", "w"))
    for k, v in seeds.items():
        print("block", k, len(v))
    for k, v in keys.items():
        print("key", k, len(v))

if __name__ == "__main__":
    build()
