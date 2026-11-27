"""The fine-mark planner (`marks`; docs/research/hyperrealism-gaps.md, G7; AGENTS.md rule 2).

A hyperrealist builds hair, glints, droplets, pores, edges and lashes as designed marks, not as tone: strands stroke
by stroke "bold to begin with, but ended lightly", highlights lifted or indented, droplets as a unit (shadow side,
rim, glint, cast shadow), pores "lightly" (too dark "will look like blackheads"), crisp edges with a hard lead
(sources in the gaps doc, G7). This module reads the STRUCTURE of the painter's own reference (the schema: an
invented render or drawing, never someone's photograph) and proposes the paths of such marks; the painter chooses
the families, the regions and the counts, and every mark is laid by a studio tool through the normal hand (strokes
with the medium's pencils, pens and erasers). Nothing is pasted.

Families (each a function returning stroke dicts {pts, size, color, pressure, articulation, brush}):
  strands   streamlines of the schema's local orientation (structure tensor) through its darker (dark strands) or
            lighter threads (lifted with an eraser, or indented with the stylus before any tone: "lift": "stylus"),
            tapered (flick); "light" is the share of light strands; without "count", one strand every "spacing_mm"
  glints    small bright blobs of the schema: lifted with the battery eraser (or indented with the stylus)
  pores     small dark blobs of the schema: a light dab each, never darker than the surround by more than 12 L*
  edges     strong edges of the schema: a hard lead drawn along the dark side
  lashes    thin dark ridges of the schema (lashes, creases, fine lines): tapered strokes along them
  droplets  the scene's droplets (<canvas>_structure.json from `scene`): rim, shadow side, cast shadow, glint, bright
            far side, as one unit
Thresholds and mark sizes are judgements (from the sources' descriptions), scaled in mm of the sheet.
"""
import json, math, os
import numpy as np
from scipy.ndimage import gaussian_filter, sobel, label, maximum_filter, minimum_filter, center_of_mass

# default tools per family (graphite's kit); any medium's tool can be given per family with "brush"
DEFAULTS = {
    "strands": dict(brush="mech_03", grade="2B", lift="electric_eraser", length_mm=[3, 9], size_mm=0.3),
    "glints": dict(brush="electric_eraser", min_prominence=20.0, max_mm=2.0),
    "pores": dict(brush="mech_05", grade="HB", min_contrast=4.0, max_mm=0.8, pressure=0.6),
    "edges": dict(brush="mech_03", grade="HB", min_contrast=12.0, min_mm=1.5),
    "lashes": dict(brush="mech_03", grade="2B", min_contrast=8.0, width_mm=0.6, min_mm=1.0),
    "droplets": dict(brush="mech_03", grade="2B", shade="mech_05", lift="electric_eraser", soft_lift="kneaded"),
}


def _L(ref):
    rgb = np.clip(ref, 0, 1)
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    Y = c @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    return np.where(Y > 0.008856, 116 * np.cbrt(Y) - 16, 903.3 * Y).astype(np.float32)


def _hex_of_L(L):
    L = float(np.clip(L, 0, 100))
    Y = ((L + 16) / 116) ** 3 if L > 8 else L / 903.3
    v = 1.055 * Y ** (1 / 2.4) - 0.055 if Y > 0.0031308 else 12.92 * Y
    g = int(round(np.clip(v, 0, 1) * 255))
    return f"#{g:02x}{g:02x}{g:02x}"


def orientation(L, ppm):
    """Unit vectors along the schema's local lines (the minor axis of the structure tensor) and the coherence."""
    s = max(0.8, 0.5 * ppm)
    gx, gy = sobel(gaussian_filter(L, 0.6), 1) / 8, sobel(gaussian_filter(L, 0.6), 0) / 8
    Jxx, Jxy, Jyy = (gaussian_filter(a, s) for a in (gx * gx, gx * gy, gy * gy))
    th = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy) + math.pi / 2          # along the lines, not across them
    tr = Jxx + Jyy + 1e-9
    coh = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2) / tr
    return np.stack([np.cos(th), np.sin(th)], -1).astype(np.float32), coh


def _trace(x, y, d2, mask, n_steps, step=1.0):
    pts = [(x, y)]
    for sgn in (1, -1):
        px, py = x, y
        prev = None
        side = []
        for _ in range(n_steps):
            xi, yi = int(px), int(py)
            if not (0 <= xi < mask.shape[1] and 0 <= yi < mask.shape[0]) or not mask[yi, xi]:
                break
            d = d2[yi, xi] * sgn
            if prev is not None and d @ prev < 0:
                d = -d
            px, py = px + d[0] * step, py + d[1] * step
            side.append((px, py))
            prev = d
        pts = (side[::-1] + pts) if sgn == -1 else (pts + side)
    return pts


def plan_strands(L, mask, ppm, opt, rng):
    o = dict(DEFAULTS["strands"], **opt)
    d2, coh = orientation(L, ppm)
    loc = gaussian_filter(L, max(1.0, 1.0 * ppm))
    diff = L - loc
    if "count" in o:
        n = int(o["count"])
    else:                       # enough strands to cover the region: one every spacing_mm across the flow
        n = int(mask.sum() / max(o.get("spacing_mm", 0.35) * ppm * np.mean(o["length_mm"]) * ppm, 1.0))
    lift_share = float(o.get("light", 0.25))
    ys, xs = np.nonzero(mask & (coh > 0.3))
    if not len(ys):
        return []
    out = []
    for want_light in (False, True):
        k = int(round(n * (lift_share if want_light else 1 - lift_share)))
        sel = diff[ys, xs] > 1.0 if want_light else diff[ys, xs] < -1.0
        cy, cx = ys[sel], xs[sel]
        if not len(cy) or k == 0:
            continue
        idx = rng.choice(len(cy), size=min(k, len(cy)), replace=False)
        for i in idx:
            Lmm = rng.uniform(*o["length_mm"]) * ppm
            pts = _trace(float(cx[i]) + 0.5, float(cy[i]) + 0.5, d2, mask, int(Lmm / 2))
            if len(pts) < 4:
                continue
            pts = pts[::2] if len(pts) > 12 else pts
            v = float(np.median([L[int(p[1]), int(p[0])] for p in pts if 0 <= int(p[1]) < L.shape[0] and 0 <= int(p[0]) < L.shape[1]]))
            if want_light:      # lifted with an eraser (seek), or indented with the stylus before any tone
                stylus = o["lift"] == "stylus"
                out.append(dict(pts=[list(map(float, p)) for p in pts], size=max(1.0, (0.15 if stylus else 0.25) * ppm),
                                color=_hex_of_L(min(100, v + 6)), pressure=0.7 if stylus else 0.6, articulation="flick",
                                brush=o["lift"], seek=not stylus))
            else:
                out.append(dict(pts=[list(map(float, p)) for p in pts], size=o["size_mm"] * ppm, color=_hex_of_L(max(0, v - 4)),
                                pressure=0.85, articulation="flick", brush=o["brush"], grade=o["grade"]))
    return out


def _blobs(D, mask, ppm, thr, max_mm, bright=True):
    hi = (D > thr / 2) if bright else (D < -thr / 2)
    hi &= mask
    lab, n = label(hi)
    if n == 0:
        return []
    idx = np.arange(1, n + 1)
    from scipy.ndimage import maximum as nd_max, minimum as nd_min
    pk = np.asarray(nd_max(D, lab, idx) if bright else -np.asarray(nd_min(D, lab, idx)))
    sz = np.bincount(lab.ravel())[1:]
    ok = (pk >= thr) & (sz >= 1) & (sz <= max(2.0, (max_mm * ppm) ** 2))
    cm = center_of_mass(hi, lab, idx)
    return [(float(c[1]), float(c[0]), math.sqrt(s / math.pi), float(p)) for c, s, p, k in zip(cm, sz, pk, ok) if k]


def _dot(x, y, r):
    """A dot as a hand makes it: a tiny circling touch (a single contact lays too little)."""
    rr = max(0.4, 0.35 * r)
    return [[x + rr * math.cos(t), y + rr * math.sin(t)] for t in np.linspace(0, 2 * math.pi, 7)]


def plan_glints(L, mask, ppm, opt, rng):
    o = dict(DEFAULTS["glints"], **opt)
    D = L - gaussian_filter(L, 2 * ppm)
    bl = sorted(_blobs(D, mask, ppm, o["min_prominence"], o["max_mm"]), key=lambda b: -b[3])[:int(o.get("count", 50))]
    out = []
    for x, y, r, p in bl:
        v = float(L[int(y), int(x)])
        out.append(dict(pts=_dot(x, y, r), size=max(1.5, 2 * r), color=_hex_of_L(v), pressure=0.9,
                        articulation="plain", brush=o["brush"], seek=o["brush"] != "stylus"))
    return out


def plan_pores(L, mask, ppm, opt, rng):
    o = dict(DEFAULTS["pores"], **opt)
    sur = gaussian_filter(L, 1.0 * ppm)
    D = L - sur
    bl = _blobs(D, mask, ppm, o["min_contrast"], o["max_mm"], bright=False)
    if len(bl) > int(o.get("count", 500)):
        bl = [bl[i] for i in rng.choice(len(bl), int(o.get("count", 500)), replace=False)]
    out = []
    for x, y, r, p in bl:
        s0 = float(sur[int(y), int(x)])
        v = max(float(L[int(y), int(x)]), s0 - 12.0)          # never a blackhead
        out.append(dict(pts=_dot(x, y, r), size=max(1.0, 2 * r), color=_hex_of_L(v - 4), pressure=o["pressure"],
                        articulation="plain", brush=o["brush"], grade=o["grade"]))
    return out


def _chains(on, L, ppm, min_px, max_len_px):
    """Ordered point chains along thin structures (edge or ridge pixels), split into pieces of at most max_len_px."""
    lab, n = label(on, structure=np.ones((3, 3)))
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(xs) < min_px:
            continue
        P = np.stack([xs, ys], 1).astype(np.float32)
        c = P.mean(0)
        _, sv, vt = np.linalg.svd(P - c, full_matrices=False)
        if sv[1] / math.sqrt(len(P)) > max(1.0, 0.25 * ppm):      # not a line: a blob (a droplet, a dark patch)
            continue
        u = vt[0]
        t = (P - c) @ u
        o = np.argsort(t)
        P = P[o]
        for a in range(0, len(P), int(max_len_px)):
            seg = P[a:a + int(max_len_px)]
            if len(seg) >= min_px:
                out.append(seg[::max(1, int(len(seg) / 12))])
    return out


def plan_edges(L, mask, ppm, opt, rng):
    o = dict(DEFAULTS["edges"], **opt)
    Ls = gaussian_filter(L, 0.6)
    gx, gy = sobel(Ls, 1) / 8, sobel(Ls, 0) / 8
    g = np.hypot(gx, gy)
    thr = o["min_contrast"] / max(2.0, 0.6 * ppm)                 # L* per px of a crisp edge of that contrast
    on = (g >= maximum_filter(g, 3)) & (g > thr) & mask
    out = []
    for seg in _chains(on, L, ppm, int(o["min_mm"] * ppm), 8 * ppm)[:int(o.get("count", 300))]:
        # the line on the darker side of the edge
        xi, yi = seg[:, 0].astype(int), seg[:, 1].astype(int)
        nx, ny = -gx[yi, xi], -gy[yi, xi]
        nn = np.hypot(nx, ny) + 1e-6
        pts = np.stack([seg[:, 0] + 0.5 + 0.6 * nx / nn, seg[:, 1] + 0.5 + 0.6 * ny / nn], 1)
        v = float(np.percentile(L[yi, xi], 25))
        out.append(dict(pts=pts.tolist(), size=0.3 * ppm, color=_hex_of_L(v - 3), pressure=0.8, articulation="plain",
                        brush=o["brush"], grade=o["grade"]))
    return out


def plan_lashes(L, mask, ppm, opt, rng):
    o = dict(DEFAULTS["lashes"], **opt)
    w = max(0.7, o["width_mm"] * ppm)
    R = L - gaussian_filter(L, w)
    # the ridge: darker than its surround and darker than its neighbours across it (the smaller Hessian direction)
    Ls = gaussian_filter(L, max(0.6, 0.15 * ppm))
    Lyy, Lxx = np.gradient(np.gradient(Ls, axis=0), axis=0), np.gradient(np.gradient(Ls, axis=1), axis=1)
    Lxy = np.gradient(np.gradient(Ls, axis=0), axis=1)
    lam = (Lxx + Lyy) / 2 + np.sqrt(((Lxx - Lyy) / 2) ** 2 + Lxy ** 2)        # the larger curvature: > 0 across a dark line
    on = (R < -o["min_contrast"]) & (lam > np.percentile(lam[mask], 70) if mask.any() else lam > 0) & mask
    out = []
    for seg in _chains(on, L, ppm, int(o["min_mm"] * ppm), 6 * ppm)[:int(o.get("count", 200))]:
        xi, yi = seg[:, 0].astype(int), seg[:, 1].astype(int)
        v = float(np.min(L[yi, xi]))
        out.append(dict(pts=(seg + 0.5).tolist(), size=0.3 * ppm, color=_hex_of_L(v), pressure=0.85, articulation="flick",
                        brush=o["brush"], grade=o["grade"]))
    return out


def plan_droplets(L, mask, ppm, opt, rng, structure):
    o = dict(DEFAULTS["droplets"], **opt)
    parts = set(o.get("parts", ["rim", "shade", "cast", "glint", "caustic"]))      # the unit's parts to lay now
    out = []
    for d in (structure or {}).get("droplets", [])[:int(o.get("count", 200))]:
        x, y, R = d["x"], d["y"], d["r"]
        if not (0 <= int(y) < mask.shape[0] and 0 <= int(x) < mask.shape[1]) or not mask[int(y), int(x)] or R < 1.5:
            continue
        a, (lx, ly) = d.get("squash", 1.0), d.get("light", [0.0, -1.0])
        e1 = np.array(d.get("axis", [1.0, 0.0]))
        e2 = np.array([-e1[1], e1[0]])
        ell = lambda t, k=1.0: [x + k * R * (a * math.cos(t) * e1[0] + math.sin(t) * e2[0]), y + k * R * (a * math.cos(t) * e1[1] + math.sin(t) * e2[1])]
        th0 = math.atan2(ly, lx)
        sur = float(np.median(L[max(0, int(y - 3 * R)):int(y + 3 * R), max(0, int(x - 3 * R)):int(x + 3 * R)]))
        # the rim, darker toward the light (a whole ellipse, then the light side again)
        rim = dict(pts=[ell(t) for t in np.linspace(0, 2 * math.pi, 24)], size=max(1.0, 0.22 * R), color=_hex_of_L(sur - 25),
                   pressure=0.75, articulation="plain", brush=o["brush"], grade=o["grade"])
        if "rim" in parts:
            out.append(rim)
        shade = dict(pts=[ell(t, 0.82) for t in np.linspace(th0 - 1.2, th0 + 1.2, 10)], size=max(1.0, 0.3 * R), color=_hex_of_L(sur - 18),
                     pressure=0.6, articulation="swell", brush=o["shade"], grade="HB")
        if "shade" in parts:
            out.append(shade)
        if d.get("lit", True):
            # the cast shadow: a crescent outside, away from the light
            if "cast" in parts:
                out.append(dict(pts=[ell(t, 1.18) for t in np.linspace(th0 + math.pi - 1.0, th0 + math.pi + 1.0, 10)], size=max(1.0, 0.3 * R),
                                color=_hex_of_L(sur - 12), pressure=0.55, articulation="swell", brush=o["shade"], grade="HB"))
            # the glint toward the light and the bright far side
            gx, gy = x + lx * 0.42 * R, y + ly * 0.42 * R
            if "glint" in parts:
                out.append(dict(pts=_dot(gx, gy, 0.3 * R), size=max(1.5, 0.3 * R), color="#ffffff", pressure=1.0,
                                articulation="plain", brush=o["lift"], seek=o["lift"] != "stylus"))
            fx, fy = x - lx * 0.5 * R, y - ly * 0.5 * R
            if "caustic" in parts:
                out.append(dict(pts=_dot(fx, fy, 0.7 * R), size=max(1.5, 0.7 * R), color=_hex_of_L(min(100, sur + 10)), pressure=0.7,
                                articulation="plain", brush=o["soft_lift"], seek=o["soft_lift"] != "stylus"))
    return out


PLANNERS = {"strands": plan_strands, "glints": plan_glints, "pores": plan_pores, "edges": plan_edges, "lashes": plan_lashes}


def plan(ref, mask_of, ppm, families, rng, structure=None):
    """{family: [strokes]} for the families asked ({family: options with "region"}), from the schema `ref` (H, W, 3)."""
    L = _L(ref)
    out = {}
    for fam, opt in families.items():
        if fam not in PLANNERS and fam != "droplets":
            raise SystemExit(f"marks: unknown family '{fam}'. Families: {', '.join(list(PLANNERS) + ['droplets'])}")
        m = mask_of(opt.get("region"))
        if fam == "droplets":
            out[fam] = plan_droplets(L, m, ppm, opt, rng, structure)
        else:
            out[fam] = PLANNERS[fam](L, m, ppm, opt, rng)
    return out


def preview(ref, planned, path):
    """The planned paths drawn over the schema (red dark marks, cyan lifts), for `"dry": true`."""
    from PIL import Image, ImageDraw
    im = Image.fromarray((np.clip(ref, 0, 1) * 255).astype(np.uint8)).convert("RGB")
    d = ImageDraw.Draw(im)
    for fam, st in planned.items():
        for s in st:
            lift = "eraser" in s["brush"] or s["brush"] == "kneaded"
            pts = [tuple(p) for p in s["pts"]]
            if len(pts) > 1:
                d.line(pts, fill=(0, 200, 255) if lift else (230, 30, 30), width=1)
    im.save(path)
