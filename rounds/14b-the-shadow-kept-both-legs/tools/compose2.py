"""Schema builder, second version: my hand-built lay figure (objects tagged fig), floor with a light gradient."""
import sys, json, numpy as np, math
from PIL import Image
from scipy.ndimage import gaussian_filter
sys.path.insert(0, "/home/claude/v14f")
import scene as sc
from compose import hx

def build(spec_path, out, res=420, floor_from=None):
    spec = json.load(open(spec_path)); P = spec["compose"]
    arr = sc.Scene(spec).render(res, res)
    spec2 = json.loads(json.dumps(spec))
    for o in spec2["objects"]:
        if o.get("fig"): o["color"] = "#ff00ff"
    arr2 = sc.Scene(spec2).render(res, res)
    def warp(a):
        im = Image.fromarray(a).rotate(P.get("roll", 0), resample=Image.BICUBIC)
        z = P.get("zoom", 1.0); ch = res / z; cw = ch * 0.75
        cx = res/2 + P.get("dx", 0) * res; cy = res/2 + P.get("dy", 0) * res
        im = im.crop((int(cx-cw/2), int(cy-ch/2), int(cx+cw/2), int(cy+ch/2))).resize((1200, 1600), Image.BICUBIC)
        return np.asarray(im, np.float32) / 255
    a, a2 = warp(arr), warp(arr2)
    mx, mn = a2.max(-1), a2.min(-1)
    sat = (mx - mn) / (mx + 1e-4)
    fig = gaussian_filter((sat > 0.3).astype(np.float32), 1.2)
    lum = a2.mean(-1)
    wall_l = np.percentile(lum[fig < 0.1], 90)
    shade = np.clip(lum / wall_l, 0, 1)
    shadow = gaussian_filter(np.clip((0.93 - shade) / 0.25, 0, 1), 1.0) * (1 - np.clip(fig * 2, 0, 1))
    sc_, shx, shy = P.get("sh_scale", 1.0), P.get("sh_dx", 0), P.get("sh_dy", 0)
    if sc_ != 1.0 or shx or shy:                      # painter's licence: the shadow smaller and further = higher
        from scipy.ndimage import affine_transform
        ys, xs = np.nonzero(shadow > 0.5); cy0, cx0 = ys.mean(), xs.mean()
        off = [cy0 - (cy0 + shy) / sc_, cx0 - (cx0 + shx) / sc_]
        shadow = affine_transform(shadow, [1 / sc_, 1 / sc_], offset=off, order=1)
        shadow = gaussian_filter((gaussian_filter(shadow, 7) > 0.5).astype(np.float32), 1.6) * (1 - np.clip(fig * 2, 0, 1))
    if floor_from is not None:
        floor = np.asarray(Image.open(floor_from).convert("RGB").resize((1200, 1600)), np.float32) / 255
    else:
        floor = np.ones((1600, 1200, 3), np.float32)
    y, x = np.mgrid[0:1600, 0:1200].astype(np.float32)
    f0, f1, amp, ph = P.get("furrow", [520, 760, 150, 0.4]); t = y / 1600
    xf = f0 + (f1 - f0) * t + amp * np.sin(t * math.pi * 1.6 + ph)
    d = (x - xf) / 600
    u = np.sign(d) * np.abs(d) ** P.get("pow", 0.55) * P.get("cols", 7.0)
    v = y / P.get("row", 118.0) + P.get("wave", 0.55) * np.sin(x / 230.0 + y / 310.0 + 1.0) + 0.25 * np.sin(d * 5.0)
    chk = gaussian_filter(((np.floor(u) + np.floor(v)) % 2).astype(np.float32), 1.0)[..., None]
    shf = hx(P["shadow"]) * (1 - chk) + hx(P["shadow2"]) * chk
    k = P.get("shadow_k", 0.94)
    if floor_from is None:                             # the floor, lit from lower right: bleached there, deep upper left
        near = np.exp(-(d / 0.33) ** 2)[..., None]
        A = hx(P["A"]) * (1 - near) + hx(P["A2"]) * near; B = hx(P["B"]) * (1 - near) + hx(P["B2"]) * near
        floor = A * (1 - chk) + B * chk
        g = np.clip(((1200 - x) / 1200 * 0.55 + (1600 - y) / 1600 * 0.45), 0, 1)[..., None]
        deepA, deepB = hx(P.get("A_deep", "#c4127a")), hx(P.get("B_deep", "#0c8f9c"))
        deep = deepA * (1 - chk) + deepB * chk
        kd = np.clip((g - 0.45) / 0.55, 0, 1) ** 1.3 * 0.75 * (1 - 0.6 * near)
        floor = floor * (1 - kd) + deep * kd
        kp = np.clip((0.5 - g) / 0.5, 0, 1) ** 1.4 * 0.5
        floor = floor * (1 - kp) + hx(P.get("pale", "#fff6d8")) * kp
    res_ = floor * (1 - shadow[..., None] * k) + shf * shadow[..., None] * k
    f3 = np.clip((fig - 0.3) * 4, 0, 1)[..., None]
    res_ = res_ * (1 - f3) + a * f3
    Image.fromarray((np.clip(res_, 0, 1) * 255).astype(np.uint8)).save(out)
    np.save(out.replace(".png", "_fig.npy"), fig.astype(np.float16)); np.save(out.replace(".png", "_shadow.npy"), shadow.astype(np.float16))
    print(out)
