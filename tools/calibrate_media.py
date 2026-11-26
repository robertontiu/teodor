"""calibrate_media: measure the marks in an image region, so a medium's rendered marks can be compared with real ones.

The statistics are defined in docs/media-data.md ("Calibration method"). Run them on a crop of a real work (the
public-domain references in studio/calibration_refs.json) and on a crop of a gallery sheet or a canvas rendered by the
studio, then compare the two. Only numpy, scipy and Pillow are needed. Lengths are reported in px and, when the scale is
known (--px-per-mm, or the reference's catalogued size), in mm, because marks have to be compared at the same physical
scale: a 1200 px canvas is a painting of a stated size (see studio/media.json), a museum photo has its own resolution.

  python3 tools/calibrate_media.py image.jpg [--crop X Y W H] [--px-per-mm N] [--kind auto|line|wash|tone|paint]
  python3 tools/calibrate_media.py refs watercolour [--n 6]      # download, measure and aggregate the references
  python3 tools/calibrate_media.py refs etching --file studio/calibration_refs.parts/etching-engraving.json
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
  lines      (--kind line) line centres: equivalent width from integrated ink coverage, its variation along each line,
             free-end width ratio (taper or blob), hatch spacing, cross-hatched share and crossing angle, line density and
             cross-hatching per value band, ink and paper colour; see lines()
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
    if kind in ("line", "lines"):
        out["lines"] = lines(rgb, ppm, L, Y)
    return out


# ---------------------------------------------------------------- line work (pen, burin, etching needle)
def lines(rgb, ppm=None, L=None, Y=None):
    """Line statistics for pen-and-ink, engraving and etching, measured on the line centres (ridges of ink coverage).
    Coverage c = 1 - Y / Y_paper (linear luminance), so the integral of c across a line is its width times its ink
    density whatever the photograph's blur; widths are that integral over the darkest ink's coverage (c_full, 99th pct).
      width        equivalent width of each line at its centre, median and IQR (px, mm)
      width_cv     coefficient of variation of the width along each connected line (>= 12 centre px), median
      end_ratio    width within 2 px of a line's free end over that line's median width (taper < ~0.7 < blunt or blob)
      spacing      centre-to-centre distance to the next parallel line across the line (hatch spacing), median, IQR
      families     4 mm windows (or 48 px): share with two or more line directions (cross-hatching), the angle between
                   the two main directions, and per value band (window mean L*) the line density (mm of line per mm2 =
                   lines per mm) and the share cross-hatched: how tone is built from lines
      ink          CIELAB of line cores (c > 0.6) and of the paper: black or brown ink, warm or white paper"""
    if L is None:
        L, A, B, Y = srgb_to_lab(rgb)
    else:
        _, A, B, _ = srgb_to_lab(rgb)
    H, W = L.shape
    mm = (lambda px: None if (ppm is None or px is None) else round(float(px) / ppm, 4))
    Yp = np.percentile(Y, 98)
    c = np.clip(1 - Y / max(Yp, 1e-4), 0, 1)
    cs = ndi.gaussian_filter(c, 0.7)
    c_full = max(float(np.percentile(c, 99)), 0.3)
    # line direction from the structure tensor of coverage
    gx, gy = ndi.sobel(cs, 1), ndi.sobel(cs, 0)
    Jxx, Jyy, Jxy = (ndi.gaussian_filter(v, 1.5) for v in (gx * gx, gy * gy, gx * gy))
    th = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)          # gradient direction = across the line
    nx, ny = np.cos(th), np.sin(th)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = ndi.map_coordinates(cs, [yy + ny, xx + nx], order=1, mode="nearest")
    b = ndi.map_coordinates(cs, [yy - ny, xx - nx], order=1, mode="nearest")
    ridge = (cs >= a) & (cs >= b) & (cs > 0.25 * c_full)
    ridge &= ~((cs == a) & (cs == b))
    m = 6
    ridge[:m] = ridge[-m:] = False; ridge[:, :m] = ridge[:, -m:] = False
    ys, xs = np.nonzero(ridge)
    out = {"n_centres": int(len(ys)), "c_full": round(c_full, 3)}
    if len(ys) < 50:
        return out
    K = 24; st = 0.5
    t = np.arange(-K, K + st, st)
    k0 = len(t) // 2
    ux, uy = nx[ys, xs], ny[ys, xs]
    PX = xs[:, None] + t[None, :] * ux[:, None]; PY = ys[:, None] + t[None, :] * uy[:, None]
    P = ndi.map_coordinates(c, [PY.ravel(), PX.ravel()], order=1, mode="nearest").reshape(PX.shape)
    Ps = ndi.map_coordinates(cs, [PY.ravel(), PX.ravel()], order=1, mode="nearest").reshape(PX.shape)
    eps = 0.01
    # walk out from the centre while coverage keeps falling (stops at the valley between two lines)
    right = Ps[:, k0:]; left = Ps[:, k0::-1]
    def extent(side):
        dec = np.diff(side, axis=1) <= eps
        ok = np.minimum.accumulate(dec & (side[:, 1:] > 0.03), axis=1)
        return ok
    okr, okl = extent(right), extent(left)
    wr = (P[:, k0 + 1:] * okr).sum(1) * st; wl = (P[:, k0 - 1::-1] * okl).sum(1) * st
    width = (wr + wl + P[:, k0] * st) / c_full
    # spacing: the next centre beyond the valley on either side (a rise after the walk-out)
    def nextpeak(side, ok):
        n = ok.sum(1)
        d = np.full(len(side), np.nan)
        for i in np.nonzero(n < side.shape[1] - 3)[0]:
            j = n[i]                                   # the valley
            seg = side[i, j:]
            dd = np.diff(seg)
            up = np.nonzero(dd > eps / 2)[0]
            if up.size == 0:
                continue
            fall = np.nonzero(dd[up[0]:] < -eps / 2)[0]      # first fall after the rise = the next line's centre
            if fall.size == 0:
                continue
            q_ = int(up[0] + fall[0])
            if seg[q_] > 0.25 * c_full and seg[q_] > seg[0] + 0.02:
                d[i] = (j + q_) * st
        return d
    sel = np.random.default_rng(0).permutation(len(ys))[:6000]
    dr, dl = nextpeak(right[sel], okr[sel]), nextpeak(left[sel], okl[sel])
    sp = np.fmin(dr, dl); sp = sp[np.isfinite(sp)]
    out["width_px"] = q(width); out["width_mm"] = [mm(v) for v in q(width)] if ppm else None
    out["width_p90_px"] = round(float(np.percentile(width, 90)), 2)
    out["spacing_px"] = q(sp) if sp.size > 20 else None
    out["spacing_mm"] = [mm(v) for v in q(sp)] if (ppm and sp.size > 20) else None
    # along-line variation and free ends
    wmap = np.zeros((H, W), np.float32); wmap[ys, xs] = width
    lab, n = ndi.label(ridge, structure=np.ones((3, 3)))
    cnt = np.bincount(lab.ravel())
    nb = ndi.convolve(ridge.astype(np.int32), np.ones((3, 3), np.int32), mode="constant") - 1
    cvs, ends = [], []
    order = np.argsort(cnt[1:])[::-1][:400] + 1
    objs = ndi.find_objects(lab)
    for k in order:
        if cnt[k] < 12:
            break
        sl = objs[k - 1]
        mk = lab[sl] == k
        wv = wmap[sl][mk]
        med = float(np.median(wv))
        if med <= 0:
            continue
        cvs.append(float(wv.std() / med))
        e = mk & (nb[sl] <= 1)
        for (ey, ex) in zip(*np.nonzero(e)):
            y0, x0 = max(0, ey - 2), max(0, ex - 2)
            win = mk[y0:ey + 3, x0:ex + 3]
            ends.append(float(np.median(wmap[sl][y0:ey + 3, x0:ex + 3][win]) / med))
    out["width_cv_along"] = q(cvs) if cvs else None
    out["end_ratio"] = q(ends) if len(ends) > 10 else None
    out["n_lines"] = len(cvs)
    # direction families and how tone is built per value band
    win = int(round(4 * ppm)) if ppm else 48
    win = int(np.clip(win, 24, max(24, min(H, W) // 3)))
    ang = (np.degrees(th[ys, xs]) + 90) % 180       # line direction
    fam, xang, bands = [], [], {}
    for y0 in range(0, H - win + 1, win // 2):
        for x0 in range(0, W - win + 1, win // 2):
            inw = (ys >= y0) & (ys < y0 + win) & (xs >= x0) & (xs < x0 + win)
            Lm = float(L[y0:y0 + win, x0:x0 + win].mean())
            dens = inw.sum() / (win * win) * (ppm or 1)          # px of centre line per px2 -> lines per mm
            nf = 0
            if inw.sum() >= win:
                h, _ = np.histogram(ang[inw], bins=18, range=(0, 180))
                h = ndi.gaussian_filter1d(h.astype(float), 0.8, mode="wrap")
                pk = [i for i in range(18) if h[i] >= h[i - 1] and h[i] >= h[(i + 1) % 18] and h[i] > 0.3 * h.max()]
                nf = len(pk)
                if nf >= 2:
                    top = sorted(pk, key=lambda i: -h[i])[:2]
                    dd = abs(top[0] - top[1]) * 10
                    xang.append(min(dd, 180 - dd))
            fam.append(nf >= 2)
            bk = "L<40" if Lm < 40 else ("L40-60" if Lm < 60 else ("L60-80" if Lm < 80 else "L>=80"))
            bd = bands.setdefault(bk, [[], []])
            bd[0].append(dens); bd[1].append(nf >= 2)
    out["window_px"] = win
    out["cross_share"] = round(float(np.mean(fam)), 3) if fam else None
    out["cross_angle_deg"] = q(xang) if len(xang) > 3 else None
    out["by_value"] = {k: dict(n=len(v[0]), lines_per_mm=round(float(np.median(v[0])), 3) if ppm else None,
                               cross_share=round(float(np.mean(v[1])), 3)) for k, v in sorted(bands.items())}
    core = c > 0.6 * c_full
    pap = c < 0.03
    if core.sum() > 30:
        out["ink_lab"] = [round(float(np.median(v[core])), 1) for v in (L, A, B)]
    if pap.sum() > 30:
        out["paper_lab"] = [round(float(np.median(v[pap])), 1) for v in (L, A, B)]
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


def refs(medium, n=None, scale_mm=None, file=None, kind="auto"):
    data = json.load(open(file or os.path.join(ROOT, "studio", "calibration_refs.json")))
    items = data["media"][medium][:n] if n else data["media"][medium]
    os.makedirs(os.path.join(CACHE, "met_full"), exist_ok=True); os.makedirs(os.path.join(CACHE, "calib"), exist_ok=True)
    res = []
    for it in items:
        p = fetch(it["primaryImage"], os.path.join(CACHE, "met_full", f"{it['objectID']}.jpg"))
        im = Image.open(p).convert("RGB")
        x, y, w, h = it["crop_xywh"]
        crop = np.asarray(im.crop((x, y, x + w, y + h)))
        m = measure(crop, it.get("px_per_mm"), kind)
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
        ap.add_argument("--kind", default="auto", help="line: add the line statistics (width, spacing, families, ends, ink colour)")
        ap.add_argument("--file", help="a reference file other than studio/calibration_refs.json, e.g. studio/calibration_refs.parts/<style>.json")
        a = ap.parse_args(); refs(a.medium, a.n, file=a.file, kind=a.kind); return
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
