"""calibrate_media: measure the marks in an image region, so a medium's rendered marks can be compared with real ones.

The statistics are defined in docs/media-data.md ("Calibration method"). Run them on a crop of a real work (the
public-domain references in studio/calibration_refs.json) and on a crop of a gallery sheet or a canvas rendered by the
studio, then compare the two. Only numpy, scipy and Pillow are needed. Lengths are reported in px and, when the scale is
known (--px-per-mm, or the reference's catalogued size), in mm, because marks have to be compared at the same physical
scale: a 1200 px canvas is a painting of a stated size (see studio/media.json), a museum photo has its own resolution.

  python3 tools/calibrate_media.py image.jpg [--crop X Y W H] [--px-per-mm N] [--kind auto|line|wash|tone|paint]
  python3 tools/calibrate_media.py refs watercolour [--n 6]      # download, measure and aggregate the references
  python3 tools/calibrate_media.py compare a.json b.json         # two measurement files side by side

`refs` downloads each reference's primaryImage from The Met (CC0) into ~/.cache/teodor/met_full/ (outside git),
measures crop_xywh and writes ~/.cache/teodor/calib/<medium>.json with every crop's statistics plus the median and
quartiles per statistic. Nothing is written into the repository.

Statistics (all on the crop; L is CIE L* 0..100, D is optical density relative to the paper/ground, -log10(R/R_paper)):
  value      L* percentiles 5/25/50/75/95, share of pixels near the paper (L >= paper - 3), dark share (D > 0.5)
  colour     mean and 95th-percentile chroma C*ab, hue spread (1 - mean resultant length of the hue angles, chroma-weighted)
  spectrum   radially averaged power spectrum slope of L (log-log, 1/64..1/4 cycles per px), and its value in cycles/mm
  texture    in flat passages (low local gradient): std of L, its correlation length (autocorrelation 1/e), in px and mm:
             the granulation / tooth / canvas-weave scale
  edges      10-90% rise distance across strong edges (median, px and mm) and the share of hard edges (rise <= 2 px)
  rim        edge darkening: optical density in a 4 px band just inside each wash boundary (starting one edge-rise
             width in, past the photographed blur) over the density deeper inside
             (ratio > 1 means a darkened rim, the coffee-ring effect); reported as median and the share of washes with ratio > 1.1
  strokes    dark marks (Otsu threshold on D): width along each mark from the distance transform at its medial ridge,
             median and IQR in px and mm, coefficient of variation along marks (width change within a stroke)
  gaps       flying white / dry-brush / tooth speckle: share of paper-light pixels inside the closed hull of the marks
  hatch      orientation coherence of the structure tensor (0 isotropic .. 1 all one direction), the dominant orientation,
             and the hatch spacing from the peak of the spectrum across that orientation (px, mm)
Gloss and impasto height cannot be measured from a diffuse museum photograph; see docs/media-data.md for what can.
"""
import argparse, io, json, os, sys, time, urllib.request
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
UA = "TeodorResearch/1.0 (https://github.com/robertontiu/teodor)"
CACHE = os.path.expanduser("~/.cache/teodor")


# ---------------------------------------------------------------- colour
def srgb_to_lab(rgb):
    c = rgb.astype(np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1]); b = 200 * (f[..., 1] - f[..., 2])
    return L, a, b, lin @ M[1]


def otsu(x, bins=256):
    h, e = np.histogram(x, bins); c = (e[:-1] + e[1:]) / 2
    w0 = np.cumsum(h); w1 = w0[-1] - w0
    m0 = np.cumsum(h * c) / np.maximum(w0, 1); m1 = (np.sum(h * c) - np.cumsum(h * c)) / np.maximum(w1, 1)
    return c[np.argmax(w0 * w1 * (m0 - m1) ** 2)]


def q(a, ps=(25, 50, 75)):
    a = np.asarray(a, np.float64)
    return [round(float(v), 3) for v in np.percentile(a, ps)] if a.size else None


# ---------------------------------------------------------------- statistics
def measure(rgb, ppm=None, kind="auto"):
    L, A, B, Y = srgb_to_lab(rgb)
    H, W = L.shape
    mm = (lambda px: None if (ppm is None or px is None) else round(float(px) / ppm, 3))
    out = {"size_px": [W, H], "px_per_mm": ppm}
    paper_Y = np.percentile(Y, 98)
    paper_L = float(np.percentile(L, 98))
    D = -np.log10(np.clip(Y / max(paper_Y, 1e-4), 1e-3, None))
    D = np.clip(D, 0, 3)
    # value
    out["value"] = dict(L_pct_5_25_50_75_95=q(L, (5, 25, 50, 75, 95)), paper_L=round(paper_L, 1),
                        paper_share=round(float(np.mean(L >= paper_L - 3)), 3), dark_share=round(float(np.mean(D > 0.5)), 3),
                        D_pct_50_95=q(D, (50, 95)))
    # colour
    C = np.hypot(A, B); h = np.arctan2(B, A)
    w = C / (C.sum() + 1e-9)
    R = np.hypot((w * np.cos(h)).sum(), (w * np.sin(h)).sum())
    out["colour"] = dict(chroma_mean=round(float(C.mean()), 2), chroma_p95=round(float(np.percentile(C, 95)), 2), hue_spread=round(float(1 - R), 3))
    # spectrum slope
    n = min(H, W) // 2 * 2
    sub = L[:n, :n] - L[:n, :n].mean()
    win = np.outer(np.hanning(n), np.hanning(n))
    P = np.abs(np.fft.fftshift(np.fft.fft2(sub * win))) ** 2
    yy, xx = np.indices(P.shape); r = np.hypot(yy - n / 2, xx - n / 2).astype(int)
    radial = np.bincount(r.ravel(), P.ravel()) / np.maximum(np.bincount(r.ravel()), 1)
    f = np.arange(radial.size) / n
    sel = (f >= 1 / 64) & (f <= 1 / 4)
    slope = float(np.polyfit(np.log(f[sel]), np.log(radial[sel] + 1e-9), 1)[0]) if sel.sum() > 4 else None
    out["spectrum"] = dict(slope=None if slope is None else round(slope, 3), band_cycles_per_px=[1 / 64, 1 / 4],
                           band_cycles_per_mm=None if ppm is None else [round(ppm / 64, 3), round(ppm / 4, 3)])
    # texture in flat passages
    gm = ndi.gaussian_gradient_magnitude(L, 2.0)
    flat = gm < np.percentile(gm, 30)
    hp = L - ndi.gaussian_filter(L, 6)
    tex = {}
    if flat.sum() > 500:
        tex["std_L_flat"] = round(float(hp[flat].std()), 3)
        m = ndi.binary_erosion(flat, iterations=3)
        z = np.where(flat, hp, 0.0)
        ac = np.fft.ifft2(np.abs(np.fft.fft2(z)) ** 2).real
        ac = np.fft.fftshift(ac) / max(ac.max(), 1e-9)
        cy, cx = H // 2, W // 2
        prof = [(ac[cy, cx + d] + ac[cy, cx - d] + ac[cy + d, cx] + ac[cy - d, cx]) / 4 for d in range(1, min(cy, cx, 60))]
        below = [i + 1 for i, v in enumerate(prof) if v < 1 / np.e]
        cl = below[0] if below else None
        tex.update(corr_length_px=cl, corr_length_mm=mm(cl))
    out["texture"] = tex
    # edges: 10-90% rise across strong edges
    gy, gx = ndi.sobel(ndi.gaussian_filter(L, 0.7), 0), ndi.sobel(ndi.gaussian_filter(L, 0.7), 1)
    g = np.hypot(gx, gy)
    thr = np.percentile(g, 98)
    ys, xs = np.nonzero((g >= thr) & (g == ndi.maximum_filter(g, 3)))
    rng = np.random.default_rng(0)
    idx = rng.permutation(len(ys))[:600]
    rises = []
    for i in idx:
        y, x = ys[i], xs[i]
        ux, uy = gx[y, x] / (g[y, x] + 1e-9), gy[y, x] / (g[y, x] + 1e-9)
        t = np.arange(-12, 13)
        px, py = np.clip(x + t * ux, 0, W - 1), np.clip(y + t * uy, 0, H - 1)
        p = ndi.map_coordinates(L, [py, px], order=1)
        lo, hi = np.percentile(p[:5], 50), np.percentile(p[-5:], 50)
        if abs(hi - lo) < 8:
            continue
        s = (p - lo) / (hi - lo)
        a10 = np.argmax(s >= 0.1); a90 = np.argmax(s >= 0.9)
        if s[a10] >= 0.1 and s[a90] >= 0.9 and a90 >= a10:
            rises.append(a90 - a10 + 0.5)
    out["edges"] = dict(n=len(rises), rise_10_90_px=q(rises), rise_10_90_mm_median=mm(np.median(rises)) if rises else None,
                        hard_share=round(float(np.mean(np.array(rises) <= 2)), 3) if rises else None)
    edge_px = float(np.median(rises)) if rises else None
    # marks: Otsu on density
    t = otsu(D[D > 0.02]) if (D > 0.02).sum() > 100 else 0.3
    ink = D > max(t, 0.08)
    ink = ndi.binary_opening(ink, iterations=1)
    # rim (edge darkening) on washes: connected regions of the mark mask large enough to have an interior
    lab, nl = ndi.label(ink)
    ratios = []
    if nl:
        sizes = ndi.sum(np.ones_like(D), lab, range(1, nl + 1))
        for k in np.argsort(sizes)[::-1][:40]:
            if sizes[k] < 400:
                break
            reg = lab == (k + 1)
            dt = ndi.distance_transform_edt(reg)
            e = int(np.ceil(edge_px)) if edge_px else 2       # step past the photographed edge blur (the 10-90% rise)
            band = (dt >= e) & (dt <= e + 4); inner = dt >= e + 14
            if band.sum() > 30 and inner.sum() > 30:
                ratios.append(float(np.median(D[band]) / max(np.median(D[inner]), 1e-3)))
    out["rim"] = dict(n=len(ratios), ratio_edge_over_interior=q(ratios),
                      share_darkened=round(float(np.mean(np.array(ratios) > 1.1)), 3) if ratios else None)
    # stroke widths along medial ridges
    dt = ndi.distance_transform_edt(ink)
    ridge = ink & (dt >= ndi.maximum_filter(dt, 3) - 0.75) & (dt >= 1)   # near-maximal: connected medial lines
    widths = 2 * dt[ridge] - 1
    cv = []
    if ridge.sum() > 20:
        rl, nr = ndi.label(ridge, structure=np.ones((3, 3)))
        lab_r = rl[ridge]
        cnt = np.bincount(lab_r)
        for k in np.argsort(cnt)[::-1][:300]:
            if k == 0 or cnt[k] < 20:
                continue
            wv = widths[lab_r == k]
            cv.append(float(wv.std() / max(wv.mean(), 1e-6)))
    out["strokes"] = dict(threshold_D=round(float(t), 3), coverage=round(float(ink.mean()), 3),
                          width_px=q(widths) if widths.size else None,
                          width_mm=[mm(v) for v in q(widths)] if (widths.size and ppm) else None,
                          width_cv_along=q(cv) if cv else None)
    # gaps inside marks: paper showing within the closed hull of the marks
    hull = ndi.binary_fill_holes(ndi.binary_closing(ink, iterations=4))
    light = L >= paper_L - 6
    out["gaps"] = dict(paper_in_marks=round(float((hull & light).sum() / max(hull.sum(), 1)), 3))
    # hatch: structure tensor coherence and spacing across the dominant orientation
    Ix, Iy = ndi.sobel(L, 1), ndi.sobel(L, 0)
    Jxx, Jyy, Jxy = (ndi.gaussian_filter(v, 4) for v in (Ix * Ix, Iy * Iy, Ix * Iy))
    lam = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2)
    coh_map = lam / (Jxx + Jyy + 1e-9)
    wgt = Jxx + Jyy
    coh = float((coh_map * wgt).sum() / (wgt.sum() + 1e-9))
    theta = 0.5 * np.arctan2(2 * (Jxy * wgt).sum(), ((Jxx - Jyy) * wgt).sum())   # gradient direction (across the lines)
    ang = np.arctan2(yy - n / 2, xx - n / 2)
    d = np.abs(np.angle(np.exp(1j * 2 * (ang - theta)))) < 0.25
    rr = r[d]; pp = P[d]
    spec = np.bincount(rr, pp) / np.maximum(np.bincount(rr), 1)
    lo_k, hi_k = max(3, n // 64), n // 3
    spacing = None
    if hi_k > lo_k + 2 and spec.size > hi_k:
        k = lo_k + int(np.argmax(spec[lo_k:hi_k] * np.arange(lo_k, hi_k)))
        spacing = round(n / k, 2)
    out["hatch"] = dict(coherence=round(coh, 3), line_direction_deg=round(float(np.degrees(theta + np.pi / 2)) % 180, 1),
                        spacing_px=spacing, spacing_mm=mm(spacing))
    return out


# ---------------------------------------------------------------- references
def fetch(url, path):
    if os.path.exists(path):
        return path
    req = urllib.request.Request(url.replace(" ", "%20"), headers={"User-Agent": UA})
    for a in range(4):
        try:
            data = urllib.request.urlopen(req, timeout=180).read()
            tmp = path + ".part"; open(tmp, "wb").write(data); os.replace(tmp, path)
            return path
        except Exception:
            if a == 3:
                raise
            time.sleep(2 + 3 * a)


def refs(medium, n=None, scale_mm=None):
    data = json.load(open(os.path.join(ROOT, "studio", "calibration_refs.json")))
    items = data["media"][medium][:n] if n else data["media"][medium]
    os.makedirs(os.path.join(CACHE, "met_full"), exist_ok=True); os.makedirs(os.path.join(CACHE, "calib"), exist_ok=True)
    res = []
    for it in items:
        p = fetch(it["primaryImage"], os.path.join(CACHE, "met_full", f"{it['objectID']}.jpg"))
        im = Image.open(p).convert("RGB")
        x, y, w, h = it["crop_xywh"]
        crop = np.asarray(im.crop((x, y, x + w, y + h)))
        m = measure(crop, it.get("px_per_mm"))
        m["objectID"] = it["objectID"]
        res.append(m)
        print(f"{it['objectID']}: edges {m['edges']['rise_10_90_mm_median']} mm, strokes {m['strokes']['width_mm']} mm, "
              f"rim {m['rim']['ratio_edge_over_interior']}, texture {m['texture'].get('corr_length_mm')} mm, "
              f"gaps {m['gaps']['paper_in_marks']}, hatch {m['hatch']['coherence']}", flush=True)
    agg = aggregate(res)
    out = os.path.join(CACHE, "calib", f"{medium}.json")
    json.dump(dict(medium=medium, n=len(res), aggregate=agg, items=res), open(out, "w"), indent=1)
    print("written", out)
    print(json.dumps(agg, indent=1))


def flatten(d, pre=""):
    o = {}
    for k, v in d.items():
        key = f"{pre}{k}"
        if isinstance(v, dict):
            o.update(flatten(v, key + "."))
        elif isinstance(v, (int, float)) and v is not None and not isinstance(v, bool):
            o[key] = v
        elif isinstance(v, list) and len(v) == 3 and all(isinstance(t, (int, float)) for t in v):
            o[key + ".median"] = v[1]
    return o


def aggregate(res):
    flat = [flatten(r) for r in res]
    keys = sorted(set(k for f in flat for k in f) - {"objectID", "px_per_mm"})
    return {k: q([f[k] for f in flat if k in f]) for k in keys if sum(k in f for f in flat) >= 2}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "refs":
        ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("medium"); ap.add_argument("--n", type=int)
        a = ap.parse_args(); refs(a.medium, a.n); return
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        A, B = (flatten(json.load(open(p)).get("aggregate") or json.load(open(p))) for p in sys.argv[2:4])
        for k in sorted(set(A) | set(B)):
            print(f"{k:45s} {str(A.get(k)):>24s} {str(B.get(k)):>24s}")
        return
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("image"); ap.add_argument("--crop", nargs=4, type=int); ap.add_argument("--px-per-mm", type=float)
    ap.add_argument("--kind", default="auto"); ap.add_argument("--json")
    a = ap.parse_args()
    im = Image.open(a.image).convert("RGB")
    if a.crop:
        x, y, w, h = a.crop; im = im.crop((x, y, x + w, y + h))
    m = measure(np.asarray(im), a.px_per_mm, a.kind)
    s = json.dumps(m, indent=1)
    if a.json:
        open(a.json, "w").write(s)
    print(s)


if __name__ == "__main__":
    main()
