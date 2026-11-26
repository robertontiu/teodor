"""Teodor's eyes with numbers: measurements of an image that a painter judges by eye, made
explicit so the canvas can be compared with its style's measured target (studio/targets.json),
the way Spectre's master report compares a mix with its genre's target curve.

The same function measures the canvas and the reference paintings, at the same scale.

Measures (see docs/MANUAL.md "Report" for how to read them):
  value      CIELAB lightness L* (0-100): mean (the key), spread, p5/p95 range, shares of dark / middle /
             light, the "murky middle" share (L* 40-60), the notan balance (share darker than an
             Otsu split) and how many value groups the histogram holds.
  colour     chroma C*: mean, p90 (how loud the loudest colour is), the hue spread (entropy of the
             hue histogram of chromatic pixels, 0 = one hue, 1 = all hues evenly), warm-cool balance.
  edges      gradient of L* at the viewing scale: density (share of pixels on any edge), hard-edge share
             (share of edge pixels that are hard), and where the hard edges sit (share inside the
             focal region).
  texture    fine detail energy and how UNIFORM it is across the picture (the coefficient of variation
             of detail energy over a 6x8 grid). Low variation = the same texture everywhere, which is
             what critics call "a digital filter"; painters vary their marks by passage.
  structure  the slope of the radial amplitude spectrum (natural scenes and many artworks fall near
             -1 to -1.4 in amplitude; steeper = smoother, flatter = noisier) and the focal point (centre
             of the strongest local contrast) with how concentrated contrast is around it.
Research basis: statistical image properties of artworks (Graham & Field 2007; Redies, Hasenstein &
Denzler 2007; Redies, Brachmann & Wagemans 2017), value grouping and notan in studio practice,
edge hierarchy in painting (docs/research/process.md).
"""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, sobel, uniform_filter

SIZE = 512  # long side used for every measurement


def _srgb_to_lab(rgb):
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return L, a, b


def load(img):
    if isinstance(img, str):
        img = Image.open(img)
    img = img.convert("RGB")
    w, h = img.size
    s = SIZE / max(w, h)
    img = img.resize((max(8, round(w * s)), max(8, round(h * s))), Image.LANCZOS)
    return np.asarray(img, np.float32) / 255


def _otsu(x, bins=100):
    hist, edges = np.histogram(x, bins=bins, range=(0, 100))
    p = hist / max(hist.sum(), 1)
    w = np.cumsum(p); mu = np.cumsum(p * (edges[:-1] + 0.5))
    mt = mu[-1]
    var = (mt * w - mu) ** 2 / (w * (1 - w) + 1e-9)
    return float(edges[int(np.argmax(var))])


def _value_groups_hist(L):
    """The first measure (until round 16): peaks of the L* histogram. Kept for comparison only: it merged
    neighbouring masses and counted 2 groups all through round 16, where the squint view showed three."""
    hist, _ = np.histogram(L, bins=20, range=(0, 100))
    h = gaussian_filter(hist.astype(float), 1.0)
    h = h / (h.max() + 1e-9)
    peaks = [i for i in range(len(h)) if h[i] > 0.12 and h[i] >= h[max(0, i - 1)] and h[i] >= h[min(len(h) - 1, i + 1)]]
    merged = []
    for p in peaks:
        if not merged or p - merged[-1] > 2:
            merged.append(p)
    return len(merged)


# Value groups as the eye counts them (docs/MANUAL.md "report"): the picture is squinted (48 px on the long
# side plus a little blur, like `look squint`), its L* is split optimally into k groups (Fisher-Jenks, exact 1-D
# clustering), and k grows while every new split is still a MASS: each group holds at least VG_MIN_SHARE of
# the picture with a connected piece of at least VG_MIN_PIECE, neighbouring groups differ by at least one step
# of a 7-step value scale (14 L*; less in a narrow-range picture: 30% of its p2-p98 range, never under 6), the
# split explains at least VG_GAIN more of the variance, and the boundaries between groups are sharper than the
# picture's average gradient (VG_SHARP: a smooth gradient or noise has no masses). Checked against round 16
# (crit_2 and final: 3 groups, as the gray and squint views showed; the old histogram measure said 2), 14
# public-domain Met oils (2-3 groups), a linear gradient and noise (1 each). All five thresholds are tuned by eye
# on those images (docs/proposals-v8.md).
VG_LONG, VG_MIN_SHARE, VG_MIN_PIECE, VG_GAP, VG_GAP_FRAC, VG_GAIN, VG_SHARP = 48, 0.04, 0.02, 14.0, 0.3, 0.04, 1.2


def _squint_L(rgb):
    h, w = rgb.shape[:2]
    s = VG_LONG / max(h, w)
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).resize((max(4, round(w * s)), max(4, round(h * s))), Image.LANCZOS)
    L, _, _ = _srgb_to_lab(np.asarray(im, np.float32) / 255)
    return gaussian_filter(L, 0.8)


def _jenks(x, kmax=6, bins=100):
    """Exact optimal 1-D clustering of x (0..100) on a histogram: {k: (within-group SSE, breaks)}, total SSE."""
    h, e = np.histogram(x, bins=bins, range=(0, 100))
    c = (e[:-1] + e[1:]) / 2
    w = h.astype(float)
    n = len(w)
    cw = np.concatenate([[0], np.cumsum(w)]); cs = np.concatenate([[0], np.cumsum(w * c)]); cq = np.concatenate([[0], np.cumsum(w * c * c)])
    i_, j_ = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
    Wt = cw[j_] - cw[i_]
    St = cs[j_] - cs[i_]
    sse = np.where(Wt > 0, cq[j_] - cq[i_] - St * St / np.maximum(Wt, 1e-12), 0.0)
    sse = np.where(j_ > i_, sse, np.inf)
    D = np.full((kmax + 1, n + 1), np.inf); B = np.zeros((kmax + 1, n + 1), int); D[0, 0] = 0
    for k in range(1, kmax + 1):
        tot = D[k - 1][:, None] + sse            # [i, j]
        B[k] = np.argmin(tot, 0); D[k] = tot[B[k], np.arange(n + 1)]
    out = {}
    for k in range(1, kmax + 1):
        br, j = [], n
        for kk in range(k, 0, -1):
            i = B[kk, j]; br.append(i); j = i
        out[k] = (float(D[k, n]), [float(e[b]) for b in sorted(br)[1:]])
    return out, float(sse[0, n])


def value_masses(rgb):
    """(number of value groups, their shares dark to light, their mean L*), counted as described above."""
    from scipy.ndimage import label
    L = _squint_L(rgb)
    res, tot = _jenks(L.ravel())
    if tot <= 1e-6:
        return 1, [1.0], [float(L.mean())]
    p2, p98 = np.percentile(L, [2, 98])
    gap_min = min(VG_GAP, max(6.0, VG_GAP_FRAC * (p98 - p2)))
    gm = np.hypot(sobel(L, 0), sobel(L, 1)) / 8
    base = float(gm.mean()) + 1e-6
    best = (1, [1.0], [float(L.mean())])
    for k in range(2, 7):
        sse_k, br = res[k]
        lab = np.digitize(L, br)
        shares = [float((lab == g).mean()) for g in range(k)]
        if min(shares) < VG_MIN_SHARE:
            break
        means = [float(L[lab == g].mean()) for g in range(k)]
        gain = (res[k - 1][0] - sse_k) / tot
        bnd = np.zeros(lab.shape, bool)
        bnd[:-1] |= lab[:-1] != lab[1:]; bnd[:, :-1] |= lab[:, :-1] != lab[:, 1:]
        sharp = float(gm[bnd].mean()) / base if bnd.any() else 0.0
        piece = min((np.bincount(label(lab == g)[0].ravel())[1:].max() / L.size) if (lab == g).any() else 0 for g in range(k))
        if min(np.diff(means)) < gap_min or gain < VG_GAIN or piece < VG_MIN_PIECE or sharp < VG_SHARP:
            break
        best = (k, shares, means)
    return best


def _spectral_slope(L):
    g = L - L.mean()
    h, w = g.shape
    win = np.outer(np.hanning(h), np.hanning(w))
    F = np.abs(np.fft.fftshift(np.fft.fft2(g * win)))
    cy, cx = h // 2, w // 2
    y, x = np.indices(F.shape)
    r = np.hypot(y - cy, x - cx).astype(int)
    rmax = min(cy, cx)
    amp = np.bincount(r.ravel(), F.ravel())[:rmax] / np.maximum(np.bincount(r.ravel())[:rmax], 1)
    f = np.arange(rmax)
    sel = (f >= 8) & (f <= rmax * 0.8)
    if sel.sum() < 5:
        return float("nan")
    k, _ = np.polyfit(np.log(f[sel]), np.log(amp[sel] + 1e-9), 1)
    return float(k)


def measure(img):
    rgb = load(img)
    L, a, b = _srgb_to_lab(rgb)
    H, W = L.shape
    out = {}
    # value
    out["value_mean"] = float(L.mean())
    out["value_spread"] = float(L.std())
    out["value_p5"], out["value_p95"] = map(float, np.percentile(L, [5, 95]))
    out["value_dark"] = float((L < 33).mean())
    out["value_light"] = float((L > 66).mean())
    out["value_middle"] = float(1 - out["value_dark"] - out["value_light"])
    out["value_murky"] = float(((L > 40) & (L < 60)).mean())
    t = _otsu(L)
    out["notan_dark_share"] = float((L < t).mean())
    out["value_groups"] = value_masses(rgb)[0]   # scalars only: tools/measure_targets.py averages every key
    # colour
    C = np.hypot(a, b)
    out["chroma_mean"] = float(C.mean())
    out["chroma_p90"] = float(np.percentile(C, 90))
    hue = np.degrees(np.arctan2(b, a)) % 360
    chrom = C > 12
    if chrom.sum() > 50:
        hh, _ = np.histogram(hue[chrom], bins=12, range=(0, 360))
        p = hh / hh.sum()
        out["hue_spread"] = float(-(p[p > 0] * np.log(p[p > 0])).sum() / math.log(12))
    else:
        out["hue_spread"] = 0.0
    warm = ((hue < 90) | (hue > 330)) & chrom
    cool = (hue > 150) & (hue < 300) & chrom
    out["warm_share"], out["cool_share"] = float(warm.mean()), float(cool.mean())
    # edges at the viewing scale
    Ls = gaussian_filter(L, 1.0)
    g = np.hypot(sobel(Ls, 0), sobel(Ls, 1)) / 8.0  # L* per pixel
    edge = g > 2.0
    hard = g > 8.0
    out["edge_density"] = float(edge.mean())
    out["hard_edge_share"] = float(hard.sum() / max(edge.sum(), 1))
    # texture uniformity ("filter" look)
    fine = np.abs(L - gaussian_filter(L, 2.0))
    out["detail_energy"] = float(fine.mean())
    gy, gx = 8, 6
    tiles = [fine[r * H // gy:(r + 1) * H // gy, c * W // gx:(c + 1) * W // gx].mean() for r in range(gy) for c in range(gx)]
    out["texture_variation"] = float(np.std(tiles) / (np.mean(tiles) + 1e-9))
    # structure
    out["spectral_slope"] = _spectral_slope(L)
    lc = np.sqrt(np.clip(uniform_filter(L ** 2, 15) - uniform_filter(L, 15) ** 2, 0, None))
    lc = gaussian_filter(lc, 6)
    thr = np.percentile(lc, 98)
    ys, xs = np.nonzero(lc >= thr)
    fy, fx = float(ys.mean() / H), float(xs.mean() / W)
    out["focal_x"], out["focal_y"] = fx, fy
    yy, xx = np.indices(L.shape)
    near = np.hypot(yy / H - fy, xx / W - fx) < 0.18
    out["hard_edges_near_focus"] = float((hard & near).sum() / max(hard.sum(), 1))
    out["contrast_concentration"] = float(lc[near].mean() / (lc.mean() + 1e-9))
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out.items()}


# ---------------------------------------------------------------- marks: how the strokes are built
# Brushwork studies describe strokes by orientation, length and width, and find them distinctive of a painter's
# hand (Lamberti, Sanna & Paravati 2014, EURASIP J. Image Video Proc. 2014:53; Li, Yao, Hendriks & Wang 2012,
# IEEE TPAMI 34(6): van Gogh's strokes are "rhythmic", regular strokes tightly arranged). Extracting single
# strokes is fragile, so these are field measures of the same properties, made on the same 512 px image for the
# canvas and the reference paintings:
#   orient_coherence   how strongly marks are oriented locally (structure-tensor coherence weighted by energy;
#                      0 = no direction, 1 = parallel lines)
#   orient_spread      how much the dominant direction changes across the picture (circular spread of the
#                      dominant orientation of 8x6 tiles, 0 = all one angle, 1 = every angle): "never all one angle"
#   mark_scale         median characteristic scale of the marks (px at 512 px long side; the sigma where the
#                      scale-normalised Laplacian energy peaks, per tile) and mark_scale_spread (sd of log2 of it
#                      across tiles: 0 = one mark size everywhere, the "uniform dab")
#   edge_variety       entropy of the edge classes lost/soft/firm/hard (L* gradient 1-2, 2-4, 4-8, >8 per px)
#                      among edge pixels, 0..1: one kind of edge everywhere scores low
# The integration scales (sigma 3 for the tensor, sigmas 1-8 for the scale) are chosen for the 512 px image, a
# judgement.
SCALES = (1.0, 1.4, 2.0, 2.8, 4.0, 5.6, 8.0, 11.3, 16.0)


def mark_stats(img):
    from scipy.ndimage import gaussian_laplace
    rgb = load(img)
    L, _, _ = _srgb_to_lab(rgb)
    H, W = L.shape
    Ls = gaussian_filter(L, 1.0)
    gx, gy = sobel(Ls, 1) / 8, sobel(Ls, 0) / 8
    Jxx, Jxy, Jyy = (gaussian_filter(a, 3.0) for a in (gx * gx, gx * gy, gy * gy))
    tr = Jxx + Jyy + 1e-9
    coh = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2) / tr
    out = {"orient_coherence": float((coh * tr).sum() / tr.sum())}
    c2, s2 = (Jxx - Jyy) / tr, 2 * Jxy / tr               # doubled-angle vector, length = coherence
    gy_, gx_ = 6, 8
    angs, wts = [], []
    for r in range(gy_):
        for c in range(gx_):
            sl = (slice(r * H // gy_, (r + 1) * H // gy_), slice(c * W // gx_, (c + 1) * W // gx_))
            w = tr[sl]
            vc, vs = (c2[sl] * w).sum() / w.sum(), (s2[sl] * w).sum() / w.sum()
            angs.append(math.atan2(vs, vc)); wts.append(math.hypot(vc, vs) * w.mean())
    angs, wts = np.array(angs), np.array(wts) + 1e-12
    R = math.hypot((wts * np.cos(angs)).sum(), (wts * np.sin(angs)).sum()) / wts.sum()
    out["orient_spread"] = float(1 - R)
    # characteristic mark scale per tile
    E = np.stack([(s * s * gaussian_laplace(L, s)) ** 2 for s in SCALES])
    ls = np.log2(np.array(SCALES))
    sc = []
    for r in range(gy_):
        for c in range(gx_):
            e = E[:, r * H // gy_:(r + 1) * H // gy_, c * W // gx_:(c + 1) * W // gx_].mean((1, 2))
            sc.append(ls[int(np.argmax(e))] if e.max() > 0 else 0.0)
    sc = np.array(sc)
    out["mark_scale"] = float(2 ** np.median(sc))
    out["mark_scale_spread"] = float(sc.std())
    g = np.hypot(*np.gradient(gaussian_filter(L, 1.0)))
    cls = np.digitize(g[g > 1.0], [2.0, 4.0, 8.0])
    p = np.bincount(cls, minlength=4) / max(cls.size, 1)
    out["edge_variety"] = float(-(p[p > 0] * np.log(p[p > 0])).sum() / math.log(4))
    return {k: round(v, 4) for k, v in out.items()}


# ---------------------------------------------------------------- element clarity (Spectre's masking measure)
# Each element of the picture (a figure, a head, a hand, the sky...) against its immediate surround, at thumbnail
# size (the canvas at 1/12, like `look thumb`, blurred 0.7 px): the difference in mean L* (value), in mean colour
# (Delta E ab), and the mean L* gradient along the element's outline (the edge). Spectre flags a stem as "not
# in the mix" when it is masked; an element whose contrast (the larger of the value difference and half the
# colour difference) is under CLARITY_MIN and whose outline edge is under CLARITY_EDGE is "masked": at a
# glance it does not separate from its neighbours. Both thresholds are judgements (eye), to be tuned against
# critics' readings; the same measure on the schema says whether the drawing had the element clear, and an element
# with under half the schema's contrast is "weakened". Declare tight regions (a polygon around the figure, not a
# loose ellipse): the surround ring is taken just outside the declared outline.
CLARITY_MIN, CLARITY_EDGE, THUMB = 8.0, 3.0, 12


def _clarity_one(Lab, m):
    from scipy.ndimage import binary_dilation, binary_erosion
    L, a, b = Lab
    inside = m > 0.5
    if inside.sum() < 3:
        return None
    r = int(np.clip(round(0.35 * math.sqrt(inside.sum())), 2, 8))
    ring = binary_dilation(inside, iterations=r) & ~inside
    if ring.sum() < 3:
        return None
    dL = abs(float(L[inside].mean() - L[ring].mean()))
    dE = math.sqrt(dL ** 2 + float(a[inside].mean() - a[ring].mean()) ** 2 + float(b[inside].mean() - b[ring].mean()) ** 2)
    edge_px = inside & ~binary_erosion(inside)
    g = np.hypot(*np.gradient(L))
    edge = float(g[binary_dilation(edge_px)].mean())
    return dL, dE, edge


def element_clarity(img, masks, ref_img=None):
    """{name: {dL, dE, edge, contrast, masked, schema_contrast}} for full-size masks (H, W) of the canvas."""
    if isinstance(img, str):
        img = Image.open(img)
    img = img.convert("RGB")
    W, H = img.size
    tw, th = max(8, W // THUMB), max(8, H // THUMB)

    def lab(im):
        a = np.asarray(im.convert("RGB").resize((tw, th), Image.LANCZOS), np.float32) / 255
        a = np.stack([gaussian_filter(a[..., i], 0.7) for i in range(3)], -1)
        return _srgb_to_lab(a)
    Lab = lab(img)
    Lr = lab(ref_img) if ref_img is not None else None
    out = {}
    for name, m in masks.items():
        ms = np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).resize((tw, th), Image.BOX), np.float32) / 255
        r = _clarity_one(Lab, ms)
        if r is None:
            out[name] = dict(dL=0, dE=0, edge=0, contrast=0, masked=False, schema_contrast=None, note="too small at thumbnail size")
            continue
        dL, dE, edge = r
        con = max(dL, 0.5 * dE)
        sc = None
        if Lr is not None:
            rr = _clarity_one(Lr, ms)
            sc = max(rr[0], 0.5 * rr[1]) if rr else None
        out[name] = dict(dL=dL, dE=dE, edge=edge, contrast=con,
                         masked=bool(con < CLARITY_MIN and (edge < CLARITY_EDGE or con < CLARITY_MIN / 2)),
                         weakened=bool(sc is not None and sc >= CLARITY_MIN and con < 0.5 * sc),
                         schema_contrast=sc)
    return out


# ---------------------------------------------------------------- comparing with a target
LABELS = {
    "value_mean": ("key (mean lightness, L* 0-100)", "lighter", "darker"),
    "value_spread": ("value contrast (L* spread)", "more contrast", "less contrast"),
    "value_dark": ("share of darks", "more darks", "fewer darks"),
    "value_light": ("share of lights", "more lights", "fewer lights"),
    "value_murky": ("murky middle (L* 40-60)", "more middle values", "fewer middle values: group the values"),
    "chroma_mean": ("average colour strength", "more saturated", "more muted"),
    "chroma_p90": ("strongest colours", "louder accents", "quieter accents"),
    "hue_spread": ("hue spread", "more hues", "fewer hues: a tighter palette"),
    "edge_density": ("edge density", "more edges", "fewer edges: simplify"),
    "hard_edge_share": ("share of hard edges", "harder edges", "softer edges: lose more of them"),
    "texture_variation": ("texture variation between passages", "vary the marks more by passage", "more even surface"),
    "spectral_slope": ("spectral slope (amplitude)", "flatter: more fine detail and noise", "steeper: smoother, broader"),
    "hard_edges_near_focus": ("hard edges near the focal point", "concentrate hard edges at the focus", "spread them"),
}


def compare(m, target):
    """Rows of (key, value, target mean, target sd, z, verdict) for measures the target has."""
    rows = []
    for k, (label, up, down) in LABELS.items():
        if k not in target or k not in m or m[k] is None:
            continue
        t = target[k]
        mu, sd = t["mean"], max(t["sd"], 1e-6)
        z = (m[k] - mu) / sd
        verdict = "within the style's range" if abs(z) <= 1.0 else ("outside: " + (down if z > 0 else up))
        rows.append((k, label, m[k], mu, t["sd"], z, verdict))
    return rows


def format_report(m, target=None, style=None):
    lines = [f"REPORT{' against ' + style if style else ''}"]
    lines.append(f"value: key {m['value_mean']:.0f}, spread {m['value_spread']:.0f}, range {m['value_p5']:.0f}-{m['value_p95']:.0f}, "
                 f"dark/middle/light {m['value_dark']:.0%}/{m['value_middle']:.0%}/{m['value_light']:.0%}, murky {m['value_murky']:.0%}, "
                 f"{m['value_groups']} value groups, notan dark share {m['notan_dark_share']:.0%}")
    lines.append(f"colour: chroma mean {m['chroma_mean']:.0f}, loudest {m['chroma_p90']:.0f}, hue spread {m['hue_spread']:.2f}, "
                 f"warm {m['warm_share']:.0%} / cool {m['cool_share']:.0%}")
    lines.append(f"edges: density {m['edge_density']:.0%}, hard {m['hard_edge_share']:.0%}, hard edges near the focal point {m['hard_edges_near_focus']:.0%}")
    lines.append(f"texture: detail {m['detail_energy']:.2f}, variation between passages {m['texture_variation']:.2f}")
    lines.append(f"structure: spectral slope {m['spectral_slope']:.2f}, focal point at ({m['focal_x']:.2f}, {m['focal_y']:.2f}), "
                 f"contrast concentration {m['contrast_concentration']:.2f}")
    flags = []
    if m["value_groups"] < 2:
        flags.append("one value mass: no clear light/dark structure")
    if m["value_murky"] > 0.45:
        flags.append("murky middle: too much of the canvas sits in L* 40-60")
    if m["texture_variation"] < 0.25:
        flags.append("even texture everywhere: reads as a filter; vary marks by passage")
    if m["hard_edges_near_focus"] < 0.12:
        flags.append("hard edges are not gathered at the focal point")
    if flags:
        lines.append("FLAGS: " + "; ".join(flags))
    if target:
        lines.append(f"against the measured target ({target.get('_n', '?')} reference paintings):")
        for k, label, v, mu, sd, z, verdict in compare(m, target):
            lines.append(f"  {label}: {v:.2f} (target {mu:.2f} ± {sd:.2f}, z {z:+.1f}) {verdict}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(json.dumps(measure(sys.argv[1]), indent=1))
