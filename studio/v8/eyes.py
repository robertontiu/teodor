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


def _value_groups(L):
    hist, _ = np.histogram(L, bins=20, range=(0, 100))
    h = gaussian_filter(hist.astype(float), 1.0)
    h = h / (h.max() + 1e-9)
    peaks = [i for i in range(len(h)) if h[i] > 0.12 and h[i] >= h[max(0, i - 1)] and h[i] >= h[min(len(h) - 1, i + 1)]]
    # merge peaks closer than 3 bins (15 L*)
    merged = []
    for p in peaks:
        if not merged or p - merged[-1] > 2:
            merged.append(p)
    return len(merged)


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
    out["value_groups"] = _value_groups(gaussian_filter(L, 2))
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
