"""Teodor's schema builder: 3D render of a figure floating before a 'floor' (a wall seen plumb),
rolled in the picture plane, with a Riley-compressed checker floor laid under it."""
import sys, json, numpy as np, math
from PIL import Image
from scipy.ndimage import gaussian_filter
sys.path.insert(0, "/home/claude/v14f")
import scene as sc

def hx(h):
    h = h.lstrip("#"); return np.array([int(h[i:i+2], 16)/255 for i in (0, 2, 4)], np.float32)

def build(spec_path, out, res=420, P=None):
    spec = json.load(open(spec_path))
    P = dict(spec.get("compose", {}), **(P or {}))
    arr = sc.Scene(spec).render(res, res)
    spec2 = json.loads(json.dumps(spec))
    for o in spec2["objects"]:
        if o["type"] == "figure": o.update(color="#ff00ff", skin="#ff00ff", hair="#ff00ff")
    arr2 = sc.Scene(spec2).render(res, res)
    im = Image.fromarray(arr).rotate(P.get("roll", 0), resample=Image.BICUBIC)
    im2 = Image.fromarray(arr2).rotate(P.get("roll", 0), resample=Image.BICUBIC)
    z = P.get("zoom", 1.0)                       # crop a 3:4 window from the square
    ch = res / z; cw = ch * 0.75
    cx = res/2 + P.get("dx", 0) * res; cy = res/2 + P.get("dy", 0) * res
    im = im.crop((int(cx-cw/2), int(cy-ch/2), int(cx+cw/2), int(cy+ch/2))).resize((1200, 1600), Image.BICUBIC)
    a = np.asarray(im, np.float32) / 255
    im2 = im2.crop((int(cx-cw/2), int(cy-ch/2), int(cx+cw/2), int(cy+ch/2))).resize((1200, 1600), Image.BICUBIC)
    a2 = np.asarray(im2, np.float32) / 255
    mx, mn = a2.max(-1), a2.min(-1)
    sat = (mx - mn) / (mx + 1e-4)
    fig = gaussian_filter((sat > 0.3).astype(np.float32), 1.2)          # figure = coloured; wall = neutral
    lum = a2.mean(-1)
    wall_l = np.percentile(lum[fig < 0.1], 90)
    shade = np.clip(lum / wall_l, 0, 1)                                    # 1 = lit floor, <1 = shadow
    shadow = gaussian_filter(np.clip((0.93 - shade) / 0.35, 0, 1), 1.5) * (1 - np.clip(fig * 2, 0, 1))
    # ---- the floor: checker compressed toward a furrow
    y, x = np.mgrid[0:1600, 0:1200].astype(np.float32)
    f0, f1, amp, ph = P.get("furrow", [520, 760, 150, 0.4])
    t = y / 1600
    xf = f0 + (f1 - f0) * t + amp * np.sin(t * math.pi * 1.6 + ph)
    d = (x - xf) / 600
    pw = P.get("pow", 0.55)
    u = np.sign(d) * np.abs(d) ** pw * P.get("cols", 7.0)
    v = y / P.get("row", 118.0) + P.get("wave", 0.55) * np.sin(x / 230.0 + y / 310.0 + 1.0) + 0.25 * np.sin(d * 5.0)
    chk = ((np.floor(u) + np.floor(v)) % 2).astype(np.float32)
    chk = gaussian_filter(chk, 1.0)
    near = np.exp(-(d / 0.33) ** 2)[..., None]                               # 1 at the furrow
    A_far, B_far = hx(P.get("A", "#ff9cc4")), hx(P.get("B", "#a9f0da"))
    A_near, B_near = hx(P.get("A2", "#ff4f9e")), hx(P.get("B2", "#ffe95c"))
    A = A_far * (1 - near) + A_near * near
    B = B_far * (1 - near) + B_near * near
    floor = A * (1 - chk[..., None]) + B * chk[..., None]
    sh_col = hx(P.get("shadow", "#3a2bb0")); sh_col2 = hx(P.get("shadow2", "#1f6fc0"))
    shf = sh_col * (1 - chk[..., None]) + sh_col2 * chk[..., None]
    floor = floor * (1 - shadow[..., None] * P.get("shadow_k", 0.92)) + shf * shadow[..., None] * P.get("shadow_k", 0.92)
    f3 = np.clip((fig - 0.3) * 4, 0, 1)[..., None]
    res_ = floor * (1 - f3) + a * f3
    Image.fromarray((np.clip(res_, 0, 1) * 255).astype(np.uint8)).save(out)
    np.save(out.replace(".png", "_fig.npy"), fig.astype(np.float16)); np.save(out.replace(".png", "_shadow.npy"), shadow.astype(np.float16))
    print(out)

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 420)
