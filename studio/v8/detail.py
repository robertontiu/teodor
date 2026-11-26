"""The detail pass (studio v8): paint a small region of the canvas on a sub-canvas at N times the resolution,
then bring it back down. Used for heads and hands that are too small on the main canvas to be built from planes
(round 17: a head 90 px wide is a handful of 2-6 px strokes, so every cue shouts or vanishes).

    detail open X Y W H [--scale N] [--margin M]   on the main canvas: open the region (canvas px) at N x (2-8, default 4)
    <any command> --detail                         run a studio command on the open detail (or CANVAS=<name>_detail)
    look detail                                    the detail at its own scale beside the region at the canvas's scale
    detail close [--resample area|sample]           bring it back down (area resampling by default, feathered over the margin)
    detail cancel                                  discard the detail

The detail is an ordinary named canvas, `<parent>_detail`, so every command works on it unchanged. What makes it a
detail is in its meta: `detail` (parent, region, scale, margin, parent size) and `px_scale` (detail px per canvas px).
At open every medium array of the region (colour, wetness, height, ...) is resampled up (bilinear on pixel
centres, so neighbours outside the region are used and there is no edge), and so are the support's texture
(the weave keeps its physical size: a 4 px thread is 16 px at 4x; a medium's `detail_texture` may restore its
statistics, as the dry media's tooth does), the schema, the element masks, the roles, the
order of first use and the passes. Media read `cv.px_scale` (the core passes it to tools as `_px_scale`), so a
tool's physical features (oil: bristle clumps, single hairs, edge widths, the render's relief; dry media: lead and
line widths, edge rise, dust haze, blender and eraser footprints) keep their size in
canvas units while the brush itself is as big as the painter says in detail px: a 4 px brush on the canvas is a
16 px brush in a 4x detail.

At close every array is area-averaged back down. Where the detail changed nothing, the canvas keeps its own pixels
exactly (the merge adds only the change: down - base, where base is the area average of the detail as it was
opened, and keeps the canvas's own fine structure in proportion to the untouched share of each block). The change
fades to zero over the margin (smoothstep of the distance to the region's edge), so there is no seam. Roles are
OR-ed in, first-use order and passes merged, the detail's episodes appended to the canvas's log, and its frames
kept: the canvas's time-lapse gets a zoomed frame after every detail command (the detail filling the frame with
the whole canvas as a locator), so the time-lapse shows the painter leaning in. Every mark is still a stroke of
the medium's tools; resampling the finished region down is the only operation that is not a stroke, and it is
the same thing as stepping back from a passage painted with a small brush (docs/MANUAL.md "Detail pass").
"""
import json
import math
import os
import shutil
import time

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import map_coordinates

SUFFIX = "_detail"
SCALES = (2, 3, 4, 5, 6, 8)


# ---------------------------------------------------------------- names and files
def parent_of(name):
    return name[:-len(SUFFIX)] if name.endswith(SUFFIX) else name


def path(core, name, s):
    return os.path.join(core.D, f"{name}_{s}")


class as_canvas:
    """Run studio code on another named canvas (the studio keeps the canvas name in module globals)."""

    def __init__(self, core, name):
        self.core, self.name = core, name

    def __enter__(self):
        self.old = (self.core.NAME, self.core.FRAMES)
        self.core.NAME = self.name
        self.core.FRAMES = os.path.join(self.core.D, f"{self.name}_frames")
        return self.core

    def __exit__(self, *a):
        self.core.NAME, self.core.FRAMES = self.old
        return False


def load_canvas(core, name):
    with as_canvas(core, name):
        return core.Canvas()


# ---------------------------------------------------------------- resampling
def upsample(a, x, y, w, h, s, order=1):
    """The region (x, y, w, h) of a (H, W) or (H, W, C) array at s times the resolution, sampled on the detail
    pixels' centres (bilinear by default; neighbours outside the region are used, clamped at the canvas edge)."""
    H, W = a.shape[:2]
    yy = y + (np.arange(h * s, dtype=np.float32) + 0.5) / s - 0.5
    xx = x + (np.arange(w * s, dtype=np.float32) + 0.5) / s - 0.5
    gy, gx = np.meshgrid(np.clip(yy, 0, H - 1), np.clip(xx, 0, W - 1), indexing="ij")
    if a.ndim == 2:
        return map_coordinates(a.astype(np.float32), [gy, gx], order=order, mode="nearest").astype(np.float32)
    return np.stack([map_coordinates(a[..., c].astype(np.float32), [gy, gx], order=order, mode="nearest")
                     for c in range(a.shape[2])], -1).astype(np.float32)


def nearest_up(a, s):
    return np.repeat(np.repeat(a, s, 0), s, 1)


def block(a, s, how="mean"):
    """Area resampling down by an integer factor: each canvas pixel is the mean (or max, or OR) of its s x s block."""
    h, w = a.shape[0] // s, a.shape[1] // s
    b = a[:h * s, :w * s].reshape((h, s, w, s) + a.shape[2:])
    if how == "mean":
        return b.astype(np.float64).mean((1, 3)).astype(np.float32)
    if how == "max":
        return b.max((1, 3))
    if how == "or":
        out = np.zeros((h, w) + a.shape[2:], a.dtype)
        for i in range(s):
            for j in range(s):
                out |= b[:, i, :, j]
        return out
    raise ValueError(how)


def centre_sample(a, s):
    """The detail at each canvas pixel's centre: one detail pixel per block (the middle one; for an even scale the one
    just past the centre, 1/(2s) canvas px off), the way the canvas itself samples paint, so its one-pixel texture
    (dry-brush breaks and clump colours decided per pixel) comes back as it is on the canvas; thin features alias as
    they would on the canvas. Averaging even the middle 2 x 2 loses about a tenth of the finest texture (measured)."""
    h, w = a.shape[0] // s, a.shape[1] // s
    o = s // 2
    return a[o::s, o::s][:h, :w].astype(np.float32)


RESAMPLE = ("area", "sample")


def feather(w, h, margin):
    """Weight of the detail in the merge, per canvas pixel of the region: 1 inside, falling to 0 at the region's
    edge over `margin` px (smoothstep of the distance from the pixel's centre to the edge)."""
    xs = np.arange(w, dtype=np.float32) + 0.5
    ys = np.arange(h, dtype=np.float32) + 0.5
    dx = np.minimum(xs, w - xs)
    dy = np.minimum(ys, h - ys)
    d = np.minimum(dy[:, None], dx[None, :])
    t = np.clip(d / max(margin, 1e-3), 0, 1)
    return (t * t * (3 - 2 * t)).astype(np.float32)


# ---------------------------------------------------------------- regions given in canvas px, moved into the detail
def region_to_detail(reg, x, y, s):
    r = dict(reg)
    t = r.get("type", "canvas")
    f = lambda px, py: [(px - x) * s, (py - y) * s]
    if t == "rect":
        r["x"], r["y"] = f(reg["x"], reg["y"]); r["w"], r["h"] = reg["w"] * s, reg["h"] * s
    elif t == "ellipse":
        r["cx"], r["cy"] = f(reg["cx"], reg["cy"]); r["rx"], r["ry"] = reg["rx"] * s, reg["ry"] * s
    elif t == "poly":
        r["pts"] = [f(*p[:2]) for p in reg["pts"]]
    elif t == "segment":
        at = reg["at"]
        r["at"] = f(*at) if isinstance(at[0], (int, float)) else [f(*p) for p in at]
        if "grow" in reg:
            r["grow"] = int(round(reg["grow"] * s))
    return r


def ppm_of(cv):
    """The canvas's px per mm if its medium works in millimetres (ink, woodblock), else None."""
    if "px_per_mm" in cv.meta:
        return float(cv.meta["px_per_mm"])
    m = cv.medium
    if hasattr(m, "ppm"):
        try:
            return float(m.ppm(cv))
        except Exception:
            return None
    import sys
    v = getattr(sys.modules.get(type(m).__module__), "PX_PER_MM", None)
    return float(v) if v is not None else None


# ---------------------------------------------------------------- open
def open_detail(core, x, y, w, h, scale=4, margin=None):
    name = core.NAME
    cv = core.Canvas()
    if cv.meta.get("detail"):
        raise SystemExit("this canvas is itself a detail: close it first (details don't nest).")
    if cv.meta.get("detail_open"):
        d = cv.meta["detail_open"]
        raise SystemExit(f"a detail is already open at {d['x']},{d['y']} {d['w']}x{d['h']}: `detail close` or `detail cancel` first.")
    if core.legacy(cv):
        raise SystemExit("the frozen oil-v7 reference has no detail pass.")
    s = int(scale)
    if s not in SCALES:
        raise SystemExit(f"--scale must be one of {', '.join(map(str, SCALES))} (integer, so the way back down is an exact area average).")
    x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(cv.W, x + w), min(cv.H, y + h)
    x, y, w, h = x0, y0, x1 - x0, y1 - y0
    if w < 16 or h < 16:
        raise SystemExit("the region must be at least 16 x 16 canvas px inside the canvas.")
    if w * h * s * s > 4200 * 4200:
        raise SystemExit(f"a {w}x{h} region at {s}x is {w * s}x{h * s} px: too big. Choose a smaller region or scale.")
    margin = float(margin) if margin is not None else float(max(3, round(0.08 * min(w, h))))
    dn = name + SUFFIX
    for f in os.listdir(core.D):                       # a stale detail of this canvas (a cancelled run)
        if f.startswith(dn + "_") and os.path.isfile(os.path.join(core.D, f)):
            os.remove(os.path.join(core.D, f))
    fr = os.path.join(core.D, f"{dn}_frames")
    if os.path.isdir(fr):
        shutil.rmtree(fr)
    os.makedirs(fr)
    t0 = time.time()
    orig = {}
    for a in cv.medium.arrays:
        arr = upsample(getattr(cv, a), x, y, w, h, s)
        if a == "col":
            arr = np.clip(arr, 0, 1)
        elif a == "ht":
            arr = np.clip(arr, 0, 4)
        arr = arr.astype(np.float16)
        np.save(path(core, dn, f"{a}.npy"), arr)
        orig[a] = arr
    np.savez(path(core, dn, "orig.npz"), **orig)
    # the support's texture at its physical size (cubic, so threads and grain stay round, not faceted)
    tex = np.clip(upsample(cv.tex, x, y, w, h, s, order=3), 0, 1)
    dtx = getattr(cv.medium, "detail_texture", None)     # a medium may restore the texture's statistics (dry media's tooth)
    if dtx is not None:
        tex = dtx(tex, cv.tex[y:y + h, x:x + w])
    np.save(path(core, dn, "tex.npy"), tex.astype(np.float16))
    if cv.ref is not None:
        ref = np.clip(upsample(cv.ref, x, y, w, h, s), 0, 1)
        np.save(path(core, dn, "ref.npy"), ref.astype(np.float16))
        Image.fromarray((ref * 255).astype(np.uint8)).save(path(core, dn, "schema_v1.png"))
    # roles: bits per pixel (nearest), first use per 8 px cell (the canvas cell under each detail cell's centre)
    bits, first = core.load_roles(cv)
    np.save(path(core, dn, "roles.npy"), nearest_up(bits[y:y + h, x:x + w], s).astype(np.uint16))
    G = core.ROLE_GRID
    gh, gw = -(-h * s // G), -(-w * s // G)
    pi = np.clip(((y + (np.arange(gh) * G + G / 2) / s) // G).astype(int), 0, first.shape[1] - 1)
    pj = np.clip(((x + (np.arange(gw) * G + G / 2) / s) // G).astype(int), 0, first.shape[2] - 1)
    np.save(path(core, dn, "rolefirst.npy"), first[:, pi][:, :, pj].astype(np.int32))
    pp = path(core, name, "passes.npy")
    if os.path.exists(pp):
        np.save(path(core, dn, "passes.npy"), nearest_up(np.load(pp)[y:y + h, x:x + w], s).astype(np.uint8))
    # elements: scene masks cropped and enlarged, declared regions moved into the detail's coordinates
    ep = path(core, name, "elements.npz")
    if os.path.exists(ep):
        mk = np.load(ep)
        out = {k: nearest_up(mk[k][y:y + h, x:x + w], s) for k in mk.files if mk[k].shape == (cv.H, cv.W)}
        np.savez_compressed(path(core, dn, "elements.npz"), **{k: v for k, v in out.items() if v.any()})
    el = path(core, name, "elements.json")
    if os.path.exists(el):
        try:
            els = json.load(open(el))
            if isinstance(els, list):
                json.dump([{"name": e["name"], "region": region_to_detail(e["region"], x, y, s)} for e in els],
                          open(path(core, dn, "elements.json"), "w"), indent=1)
        except Exception:
            pass
    # the log continues the canvas's (seeds and the order of roles carry on)
    lp = path(core, name, "log.jsonl")
    nlog = sum(1 for _ in open(lp)) if os.path.exists(lp) else 0
    if os.path.exists(lp):
        shutil.copy(lp, path(core, dn, "log.jsonl"))
    else:
        open(path(core, dn, "log.jsonl"), "w").close()
    info = {"parent": name, "x": x, "y": y, "w": w, "h": h, "scale": s, "margin": margin,
            "parent_size": [cv.W, cv.H], "log_base": nlog, "opened": time.strftime("%Y-%m-%d %H:%M:%S")}
    meta = {k: v for k, v in cv.meta.items() if k not in ("detail_open", "details", "finishes", "signed")}
    meta["detail"] = info
    meta["px_scale"] = float(getattr(cv, "px_scale", 1.0)) * s
    meta["diag"] = math.hypot(cv.W, cv.H) * s           # the canvas's diagonal in detail px (focus and role sizes)
    if cv.meta.get("focus"):
        fx, fy = cv.meta["focus"]
        meta["focus"] = [(fx - x) * s, (fy - y) * s]
    ppm = ppm_of(cv)
    if ppm:
        meta["px_per_mm"] = ppm * s
    json.dump(meta, open(path(core, dn, "meta.json"), "w"))
    cv.meta["detail_open"] = info
    json.dump(cv.meta, open(path(core, name, "meta.json"), "w"))
    # the canvas as it is, for the time-lapse locator
    cv.render().save(path(core, dn, "parent_view.png"))
    with open(lp if os.path.exists(lp) else path(core, name, "log.jsonl"), "a") as f:
        f.write(json.dumps({"detail": "open", "region": [x, y, w, h], "scale": s}) + "\n")
    with open(path(core, dn, "log.jsonl"), "a") as f:
        f.write(json.dumps({"detail": "open", "region": [x, y, w, h], "scale": s}) + "\n")
    dcv = load_canvas(core, dn)
    with as_canvas(core, dn):
        core.record(dcv)
    aware = getattr(dcv.medium, "detail_scale_aware", False)
    print(f"detail open: canvas region {x},{y} {w}x{h} at {s}x -> {w * s}x{h * s} px (margin {margin:.0f} canvas px, "
          f"{margin * s:.0f} detail px; {time.time() - t0:.1f} s).")
    print(f"Work on it with --detail (or CANVAS={dn}); sizes and coordinates are detail px "
          f"(a {4} px brush on the canvas is a {4 * s} px brush here).")
    if not aware:
        print(f"[{dcv.medium.name}] note: this medium's tools are not yet scale-aware: the brush is as big as you say, "
              "but its inner texture (grain, hairs, granulation) is finer than on the canvas. Check `look detail`.")
    return dcv


# ---------------------------------------------------------------- merge (close and preview)
def merge(core, parent, dcv, dn, resample="area"):
    """The canvas's arrays with the detail brought back down (only the region is changed). Returns
    ({array: new full array}, info) without saving anything. resample: "area" (the mean of each block: antialiased,
    the default) or "sample" (centre_sample: the canvas's own pixel texture; see docs/MANUAL.md "Detail pass")."""
    down_f = (lambda a: block(a, dcv.meta["detail"]["scale"])) if resample == "area" else (lambda a: centre_sample(a, dcv.meta["detail"]["scale"]))
    d = dcv.meta["detail"]
    x, y, w, h, s = d["x"], d["y"], d["w"], d["h"], d["scale"]
    wt = feather(w, h, d["margin"])
    orig = np.load(path(core, dn, "orig.npz"))
    out = {}
    for a in parent.medium.arrays:
        P = getattr(parent, a)
        Dn = getattr(dcv, a).astype(np.float32)
        if a == "col":
            Dn = np.clip(Dn, 0, 1)
        elif a == "ht":
            Dn = np.clip(Dn, 0, 4)
        O = orig[a].astype(np.float32)
        if Dn.shape != O.shape:
            continue
        ch = (Dn.astype(np.float16) != O.astype(np.float16))      # what the detail changed (at the precision kept on disk)
        if ch.ndim == 3:
            ch = ch.any(-1)
        if not ch.any():
            out[a] = P
            continue
        T = block(ch.astype(np.float32), s)                          # the changed share of each canvas pixel
        down, base = down_f(Dn), down_f(O)
        Pr = P[y:y + h, x:x + w]
        Tt = T[..., None] if Pr.ndim == 3 else T
        Wt = wt[..., None] if Pr.ndim == 3 else wt
        # down + (P - base)(1 - T): the canvas's own fine structure survives where the detail left it alone
        delta = (down - base) - Tt * (Pr - base)
        new = P.copy()
        new[y:y + h, x:x + w] = np.where(Tt > 0, Pr + Wt * delta, Pr)
        out[a] = new
    return out, {"weight": wt}


def _open_pair(core):
    """(parent canvas, parent name, detail canvas, detail name) from either side."""
    name = core.NAME
    pn = parent_of(name)
    parent = load_canvas(core, pn)
    if not parent.meta.get("detail_open"):
        raise SystemExit(f"no detail is open on canvas '{pn}': `detail open X Y W H [--scale N]` first.")
    dn = pn + SUFFIX
    if not os.path.exists(path(core, dn, "meta.json")):
        raise SystemExit(f"the detail's files ({dn}_*) are missing: `detail cancel` to clear the open detail.")
    dcv = load_canvas(core, dn)
    return parent, pn, dcv, dn


def close_detail(core, cancel=False, resample="area"):
    parent, pn, dcv, dn = _open_pair(core)
    d = dcv.meta["detail"]
    x, y, w, h, s = d["x"], d["y"], d["w"], d["h"], d["scale"]
    t0 = time.time()
    lp_d = path(core, dn, "log.jsonl")
    dlog = open(lp_d).read().splitlines()[d["log_base"] + 1:] if os.path.exists(lp_d) else []
    eps = [json.loads(l) for l in dlog if l.strip()]
    eps = [e for e in eps if "detail" not in e]
    if not cancel:
        if resample not in RESAMPLE:
            raise SystemExit(f"--resample must be one of {', '.join(RESAMPLE)}")
        new, info = merge(core, parent, dcv, dn, resample)
        for a, arr in new.items():
            setattr(parent, a, arr)
        wt = info["weight"]
        keep = wt > 0.25
        with as_canvas(core, pn):
            # roles: OR the detail's bits in; first use: the earliest order per canvas cell; passes: the most
            bits, first = core.load_roles(parent)
            dbits = np.load(path(core, dn, "roles.npy")).astype(np.uint16)
            ob = block(dbits, s, "or")
            sub = bits[y:y + h, x:x + w]
            bits[y:y + h, x:x + w] = np.where(keep, sub | ob, sub)
            dfirst = np.load(path(core, dn, "rolefirst.npy")).astype(np.int32)
            G = core.ROLE_GRID
            for i in range(dfirst.shape[1]):
                for j in range(dfirst.shape[2]):
                    cy_, cx_ = (i * G + G / 2) / s, (j * G + G / 2) / s
                    if cy_ >= h or cx_ >= w or wt[int(cy_), int(cx_)] <= 0.25:
                        continue
                    pi, pj = int((y + cy_) // G), int((x + cx_) // G)
                    if pi >= first.shape[1] or pj >= first.shape[2]:
                        continue
                    v = dfirst[:, i, j]
                    cur = first[:, pi, pj]
                    upd = (v >= 0) & ((cur < 0) | (v < cur))
                    cur[upd] = v[upd]
            core.save_roles(bits, first)
            pp_d, pp = path(core, dn, "passes.npy"), path(core, pn, "passes.npy")
            if os.path.exists(pp_d):
                passes = np.load(pp).astype(np.uint8) if os.path.exists(pp) else np.zeros((parent.H, parent.W), np.uint8)
                bm = block(np.load(pp_d).astype(np.uint8), s, "max")
                sub = passes[y:y + h, x:x + w]
                passes[y:y + h, x:x + w] = np.where(keep, np.maximum(sub, bm), sub)
                np.save(pp, passes)
    # the log: the detail's episodes, tagged with the region, then the close
    with open(path(core, pn, "log.jsonl"), "a") as f:
        for e in eps:
            f.write(json.dumps(dict(e, in_detail=[x, y, w, h, s])) + "\n")
        f.write(json.dumps({"detail": "cancel" if cancel else "close", "region": [x, y, w, h], "scale": s, "resample": resample,
                            "episodes": len(eps)}) + "\n")
    # keep the detail's own frames and log as a record; the state files go
    arch = os.path.join(core.D, f"{pn}_details")
    os.makedirs(arch, exist_ok=True)
    k = len([f for f in os.listdir(arch) if f.startswith("detail_")]) + 1
    ad = os.path.join(arch, f"detail_{k:02d}")
    os.makedirs(ad)
    fr = os.path.join(core.D, f"{dn}_frames")
    if os.path.isdir(fr):
        shutil.move(fr, os.path.join(ad, "frames"))
    for keepf in ("log.jsonl", "meta.json", "full.png"):
        if os.path.exists(path(core, dn, keepf)):
            shutil.copy(path(core, dn, keepf), os.path.join(ad, keepf))
    for f in os.listdir(core.D):
        if f.startswith(dn + "_") and os.path.isfile(os.path.join(core.D, f)):
            os.remove(os.path.join(core.D, f))
    info = parent.meta.pop("detail_open")
    rec = dict(info, resample=None if cancel else resample, closed=time.strftime("%Y-%m-%d %H:%M:%S"), episodes=len(eps), cancelled=bool(cancel), record=os.path.relpath(ad, core.D))
    parent.meta.setdefault("details", []).append(rec)
    with as_canvas(core, pn):
        parent.save()
        core.record(parent)
    print(("detail cancelled" if cancel else "detail closed") + f": region {x},{y} {w}x{h} at {s}x, {len(eps)} episode(s)"
          + ("" if cancel else f", brought back down ({resample}) with a {d['margin']:.0f} px feathered margin")
          + f" ({time.time() - t0:.1f} s). Its frames and log are in {os.path.relpath(ad, core.D)}/.")
    return parent


# ---------------------------------------------------------------- views
def look_detail(core, resample="area"):
    """The detail at its own scale (left) beside the region as it will look on the canvas after `detail close`,
    with its surroundings, at 1:1 canvas px enlarged 2x without smoothing (right); the region and its feathered
    margin outlined."""
    parent, pn, dcv, dn = _open_pair(core)
    d = dcv.meta["detail"]
    x, y, w, h, s, mg = d["x"], d["y"], d["w"], d["h"], d["scale"], d["margin"]
    new, _ = merge(core, parent, dcv, dn, resample)
    for a, arr in new.items():
        setattr(parent, a, arr)
    for k in ("_oil_ok",):
        if hasattr(parent, k):
            delattr(parent, k)
    full = parent.render()
    pad = int(max(w, h) * 0.35)
    bx0, by0 = max(0, x - pad), max(0, y - pad)
    bx1, by1 = min(parent.W, x + w + pad), min(parent.H, y + h + pad)
    ctx = full.crop((bx0, by0, bx1, by1))
    k2 = max(1, min(3, 760 // max(ctx.width, ctx.height)))
    ctx = ctx.resize((ctx.width * k2, ctx.height * k2), Image.NEAREST)
    dr = ImageDraw.Draw(ctx)
    dr.rectangle([(x - bx0) * k2, (y - by0) * k2, (x - bx0 + w) * k2 - 1, (y - by0 + h) * k2 - 1], outline=(255, 210, 60))
    dr.rectangle([(x - bx0 + mg) * k2, (y - by0 + mg) * k2, (x - bx0 + w - mg) * k2 - 1, (y - by0 + h - mg) * k2 - 1], outline=(120, 100, 40))
    dimg = dcv.render()
    sc = 760 / max(dimg.width, dimg.height)
    if sc < 1:
        dimg = dimg.resize((int(dimg.width * sc), int(dimg.height * sc)), Image.LANCZOS)
    Hh = max(dimg.height, ctx.height) + 28
    out = Image.new("RGB", (dimg.width + ctx.width + 30, Hh), (24, 24, 24))
    out.paste(dimg, (10, 24)); out.paste(ctx, (dimg.width + 20, 24))
    t = ImageDraw.Draw(out)
    t.text((10, 6), f"detail {w * s}x{h * s} px ({s}x)" + (f", shown at {sc:.2f}" if sc < 1 else ""), fill=(230, 230, 230))
    t.text((dimg.width + 20, 6), f"on the canvas after close, 1:1 px shown {k2}x (yellow: region, dim: margin)", fill=(230, 230, 230))
    with as_canvas(core, core.NAME):
        out.save(core.P("look.png"))
        print(core.P("look.png"))


def zoom_frame(core, dcv, img):
    """A frame for the canvas's time-lapse while the painter works in the detail: the detail fills the frame,
    with the whole canvas small in a corner and the region marked (so the time-lapse shows the leaning in)."""
    d = dcv.meta["detail"]
    pn = d["parent"]
    W, H = d["parent_size"]
    fw, fh = W * 3 // 8 // 2 * 2, H * 3 // 8 // 2 * 2
    fr = os.path.join(core.D, f"{pn}_frames")
    if not os.path.isdir(fr):
        return
    out = Image.new("RGB", (fw, fh), (18, 18, 18))
    sc = min(fw / img.width, fh / img.height)
    di = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.LANCZOS)
    out.paste(di, ((fw - di.width) // 2, (fh - di.height) // 2))
    pv = path(core, pn + SUFFIX, "parent_view.png")
    if os.path.exists(pv):
        p = Image.open(pv).convert("RGB")
        ls = (fw // 4) / p.width
        loc = p.resize((max(1, int(p.width * ls)), max(1, int(p.height * ls))), Image.LANCZOS)
        ImageDraw.Draw(loc).rectangle([d["x"] * ls, d["y"] * ls, (d["x"] + d["w"]) * ls, (d["y"] + d["h"]) * ls], outline=(255, 210, 60), width=2)
        out.paste(loc, (fw - loc.width - 6, fh - loc.height - 6))
        ImageDraw.Draw(out).rectangle([fw - loc.width - 7, fh - loc.height - 7, fw - 6, fh - 6], outline=(200, 200, 200))
    n = len(os.listdir(fr))
    out.save(os.path.join(fr, f"{n:05d}.jpg"), quality=88)


# ---------------------------------------------------------------- the scene, rendered for the region
def _basis(cam):
    def norm(v):
        v = np.asarray(v, np.float64)
        return v / (np.linalg.norm(v) + 1e-12)
    ro = np.asarray(cam.get("pos", [0, 1.6, 12]), np.float64)
    ta = np.asarray(cam.get("look_at", [0, 1.4, 0]), np.float64)
    fw = norm(ta - ro)
    uh = np.asarray(cam.get("up", [0, 1, 0]), np.float64)
    if abs(float(fw @ norm(uh))) > 0.999:
        uh = np.array([0, 0, -1.0]) if fw[1] < 0 else np.array([0, 0, 1.0])
    rt = norm(np.cross(fw, uh))
    up = np.cross(rt, fw)
    roll = math.radians(cam.get("roll", 0))
    if roll:
        rt, up = rt * math.cos(roll) + up * math.sin(roll), up * math.cos(roll) - rt * math.sin(roll)
    return ro, fw, rt, up


SCENE_ASPECT = 0.75      # the studio's scene renders are 300x400 (draft) or 450x600 (final): u spans +-0.75 of v


def scene_crop(core, cv, scene_json, quality="draft"):
    """Render a scene for the detail's region: the same camera, turned toward the region's centre with a narrower
    field of view (a rotation about the camera's centre, so no parallax: the picture is an exact projective map
    of the canvas's scene render), at the detail's resolution (draft: half, final: full), warped onto the detail's
    pixels. Writes <detail>_scene_vN.png as the schema and the element masks for the region."""
    import scene as sc
    d = cv.meta["detail"]
    x, y, w, h, s = d["x"], d["y"], d["w"], d["h"], d["scale"]
    Wp, Hp = d["parent_size"]
    spec = json.load(open(scene_json))
    cam = dict(spec.get("camera", {}))
    ro, fw, rt, up = _basis(cam)
    f = 1 / math.tan(math.radians(cam.get("fov", 40)) / 2)

    def rays(X, Y):
        u = ((X + 0.5) / Wp - 0.5) * 2 * SCENE_ASPECT
        v = -((Y + 0.5) / Hp - 0.5) * 2
        return u[..., None] * rt + v[..., None] * up + f * fw
    Wd, Hd = cv.W, cv.H
    X = x + (np.arange(Wd) + 0.5) / s - 0.5
    Y = y + (np.arange(Hd) + 0.5) / s - 0.5
    GX, GY = np.meshgrid(X, Y)
    dirs = rays(GX, GY)
    c = rays(np.array(x + w / 2 - 0.5), np.array(y + h / 2 - 0.5))
    fw2 = c / np.linalg.norm(c)
    rt2 = np.cross(fw2, up); rt2 /= np.linalg.norm(rt2)
    up2 = np.cross(rt2, fw2)
    dz = dirs @ fw2
    tx, ty = (dirs @ rt2) / dz, (dirs @ up2) / dz
    q = 1.0 if quality == "final" else 0.5
    Wr, Hr = max(32, int(Wd * q)), max(32, int(Hd * q))
    f2 = 0.985 * min(1 / np.abs(ty).max(), (Wr / Hr) / np.abs(tx).max())
    cam2 = dict(cam, look_at=list(map(float, ro + fw2)), up=list(map(float, up)), roll=0, fov=math.degrees(2 * math.atan(1 / f2)))
    spec2 = dict(spec, camera=cam2)
    t0 = time.time()
    scn = sc.Scene(spec2)
    arr = scn.render(Wr, Hr)
    xs = f2 * tx * (Hr / 2) + Wr / 2 - 0.5
    ys = -f2 * ty * (Hr / 2) + Hr / 2 - 0.5
    img = np.stack([map_coordinates(arr[..., k].astype(np.float32), [ys, xs], order=1, mode="nearest") for k in range(3)], -1)
    k = len([fn for fn in os.listdir(core.D) if fn.startswith(f"{core.NAME}_scene_v") and fn.endswith(".png")]) + 1
    out = core.P(f"scene_v{k}.png")
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out)
    shutil.copy(scene_json, core.P(f"scene_v{k}.json"))
    if spec.get("masks", True):
        mk, entries = scn.element_masks((Wr, Hr))
        masks, index = {}, []
        for e in entries:
            m = map_coordinates(mk[e["key"]].astype(np.float32), [ys, xs], order=0, mode="constant") > 0.5
            if not m.any():
                continue
            yy, xx = np.nonzero(m)
            masks[e["key"]] = m
            index.append(dict(e, pixels=int(m.sum()), share=round(float(m.mean()), 5),
                              bbox=[int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1],
                              centroid=[round(float(xx.mean()), 1), round(float(yy.mean()), 1)]))
        np.savez_compressed(core.P("elements.npz"), **masks)
        json.dump({"format": "teodor-elements/1", "image": os.path.basename(out), "scene": os.path.basename(scene_json),
                   "size": [Wd, Hd], "detail_of": [x, y, w, h, s], "elements": index}, open(core.P("elements.json.scene"), "w"), indent=1)
    print(f"scene rendered for the detail: camera turned to the region, fov {cam2['fov']:.2f} deg, {Wr}x{Hr} px "
          f"warped to {Wd}x{Hd} ({time.time() - t0:.0f} s)")
    return out
