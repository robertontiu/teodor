"""Gap measurements for round 19 (graphite hyperrealism) against a public-domain photograph.

  python3 tools/analysis/hyperreal_gaps.py --work ../teodor-work/19 --photo <public-domain photo.jpg> [--out gaps.json]

Analysis only (docs/research/hyperrealism-gaps.md). It measures, on the round's files and on one openly
licensed photograph of a similar subject (a close head-and-shoulders portrait under studio light):
  1. value range: percentiles and the share of pixels below L* 20 / 30 / 40 and above 90;
  2. texture energy by scale, in millimetres OF THE SUBJECT (face-mm), so a photograph and a render of
     different pixel sizes are compared at equal subject scale: band k is G(s_k) - G(2 s_k), s_k = 0.125 ... 4 mm;
  3. specular highlights: small blobs (< 2 subject-mm across) at least 12 L* above their 2 mm surround and in the
     region's brightest 10%, counted per 1000 subject-mm^2;
  4. edge sharpness: the 10-90% rise of the strongest edges (contrast > 10 L*), sampled along the gradient;
  5. grain inside vs outside a detail-pass rectangle (the "pasted on" seam).
Pixels per subject-mm are inputs (see the doc for how each was derived); every threshold is a judgement.
"""
import argparse, json, math, os
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, map_coordinates, label, maximum_filter, sobel


def srgb_to_L(rgb):
    rgb = np.asarray(rgb, np.float64)
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    Y = c @ np.array([0.2126, 0.7152, 0.0722]) if c.ndim == 3 else c
    f = np.where(Y > 0.008856, np.cbrt(Y), 7.787 * Y + 16 / 116)
    return 116 * f - 16


def load_L(path):
    if path.endswith(".npy"):
        a = np.load(path).astype(np.float64)
        return srgb_to_L(a) if a.ndim == 3 or a.max() <= 1.0 else a
    return srgb_to_L(np.asarray(Image.open(path).convert("RGB"), np.float64) / 255)


def crop(L, box):
    x, y, w, h = box
    return L[y:y + h, x:x + w]


def values(L):
    p = np.percentile(L, [0.1, 1, 5, 50, 95, 99])
    return dict(p01=p[0], p1=p[1], p5=p[2], p50=p[3], p95=p[4], p99=p[5], mean=L.mean(), spread=L.std(),
                below20=(L < 20).mean(), below30=(L < 30).mean(), below40=(L < 40).mean(), above90=(L > 90).mean())


SIGMAS_MM = (0.125, 0.25, 0.5, 1.0, 2.0, 4.0)


def band_energy(L, px_per_mm):
    """RMS of G(s) - G(2s) in L*, for s in subject-mm. None where s < 0.5 px (beyond what the pixels hold)."""
    out = {}
    for s in SIGMAS_MM:
        sp = s * px_per_mm
        if sp < 0.5:
            out[s] = None
            continue
        b = gaussian_filter(L, sp) - gaussian_filter(L, 2 * sp)
        m = int(math.ceil(4 * sp))
        core = b[m:-m or None, m:-m or None] if min(b.shape) > 2 * m + 4 else b
        out[s] = float(np.sqrt((core ** 2).mean()))
    return out


def speculars(L, px_per_mm, prominence=20.0):
    """Small bright blobs: peak at least `prominence` L* above the 2 mm surround, 2 px to (2 mm)^2 in area.
    Returns (count, count per 1000 subject-mm^2, the largest prominence in L*)."""
    d = L - gaussian_filter(L, 2 * px_per_mm)
    hi = d > prominence / 2
    lab, n = label(hi)
    if n == 0:
        return 0, 0.0, float(d.max())
    idx = np.arange(1, n + 1)
    from scipy.ndimage import maximum as nd_max
    peaks = np.asarray(nd_max(d, lab, idx))
    sizes = np.bincount(lab.ravel())[1:]
    ok = (peaks >= prominence) & (sizes >= 2) & (sizes <= max(2, (2 * px_per_mm) ** 2))
    area_mm2 = L.size / px_per_mm ** 2
    return int(ok.sum()), 1000 * int(ok.sum()) / area_mm2, float(d.max())


def edge_widths(L, px_per_mm, mask=None, n=4000, min_contrast=10.0, seed=0):
    """10-90% rise (mm) of strong edges, sampled along the gradient over +-R."""
    Ls = gaussian_filter(L, 0.5)
    gy, gx = sobel(Ls, 0) / 8, sobel(Ls, 1) / 8
    g = np.hypot(gx, gy)
    peak = (g == maximum_filter(g, 3)) & (g > 1.0)
    if mask is not None:
        peak &= mask
    ys, xs = np.nonzero(peak)
    if len(ys) == 0:
        return None
    rng = np.random.default_rng(seed)
    if len(ys) > 4 * n:
        k = rng.choice(len(ys), 4 * n, replace=False); ys, xs = ys[k], xs[k]
    R = max(6.0, 3.0 * px_per_mm)
    t = np.arange(-R, R + 0.01, 0.25)
    ux, uy = gx[ys, xs] / (g[ys, xs] + 1e-9), gy[ys, xs] / (g[ys, xs] + 1e-9)
    X = xs[:, None] + ux[:, None] * t[None]
    Y = ys[:, None] + uy[:, None] * t[None]
    P = map_coordinates(Ls, [Y.ravel(), X.ravel()], order=1, mode="nearest").reshape(X.shape)
    lo, hi = P[:, :8].mean(1), P[:, -8:].mean(1)
    c = hi - lo
    keep = c > min_contrast
    P, lo, c = P[keep], lo[keep], c[keep]
    if len(P) == 0:
        return None
    Q = (P - lo[:, None]) / c[:, None]
    Qm = np.maximum.accumulate(np.clip(Q, 0, 1), axis=1)
    i10 = (Qm < 0.1).sum(1); i90 = (Qm < 0.9).sum(1)
    w = (i90 - i10) * 0.25 / px_per_mm
    w = w[:n]
    return dict(n=int(len(w)), median_mm=float(np.median(w)), p10_mm=float(np.percentile(w, 10)),
                share_under_0p3mm=float((w < 0.3).mean()), share_under_1mm=float((w < 1.0).mean()),
                share_over_2mm=float((w > 2.0).mean()))


def poly_mask(shape, pts):
    im = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=1)
    return np.asarray(im, bool)


def fine_grain(L, box):
    c = crop(L, box)
    return float((c - gaussian_filter(c, 2.0)).std())


def r(x, k=3):
    if isinstance(x, dict):
        return {str(a): r(b, k) for a, b in x.items()}
    if isinstance(x, (float, np.floating)):
        return round(float(x), k)
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--photo", required=True, help="an openly licensed photograph (public domain or CC0)")
    ap.add_argument("--photo-ipd-px", type=float, default=282.0, help="pupil-to-pupil distance in the photo, px")
    ap.add_argument("--ipd-mm", type=float, default=64.0, help="adult male mean interpupillary distance (Dodgson 2004 ~63-65)")
    ap.add_argument("--photo-skin", default="1000,1050,110,110", help="x,y,w,h of a cheek patch in the photo")
    ap.add_argument("--photo-face", default="700,850,700,600")
    ap.add_argument("--photo-hair", default="1050,450,300,110")
    ap.add_argument("--canvas-face-pxmm", type=float, default=6.0, help="canvas px per face-mm (camera f 1716 px, face 0.25-0.30 m)")
    ap.add_argument("--canvas-hand-pxmm", type=float, default=2.3, help="canvas px per hand-mm (hand 0.75 m)")
    ap.add_argument("--out")
    a = ap.parse_args()
    W = a.work
    res = {}
    photo = load_L(a.photo)
    p_pxmm = a.photo_ipd_px / a.ipd_mm
    res["photo_px_per_face_mm"] = p_pxmm
    sheets = {
        "photo (whole frame, printed at 5 px/mm)": photo,
        "round 19 final": load_L(os.path.join(W, "final.png")),
        "round 19 schema (last)": load_L(os.path.join(W, "main_ref.npy")),
        "round 19 mesh render v19": load_L(os.path.join(W, "main_scene_v19.png")),
    }
    res["values_whole_sheet"] = {k: values(v) for k, v in sheets.items()}
    res["edges_whole_sheet_mm_on_sheet"] = {k: edge_widths(v, 5.0) for k, v in sheets.items()}

    def box(s):
        return tuple(int(v) for v in s.split(","))
    face_canvas = (250, 2330, 1100, 860)            # the face detail's rectangle (meta.json)
    skin_canvas = (330, 2520, 140, 140)             # the lit forehead (upside down), about 23 face-mm square
    hair_canvas = (20, 2900, 280, 280)
    faces = {
        "photo face": (crop(photo, box(a.photo_face)), p_pxmm),
        "final face": (crop(sheets["round 19 final"], face_canvas), a.canvas_face_pxmm),
        "schema face": (crop(sheets["round 19 schema (last)"], face_canvas), a.canvas_face_pxmm),
        "mesh render face": (crop(sheets["round 19 mesh render v19"], face_canvas), a.canvas_face_pxmm),
        "face study (tonal study, 1x)": (load_L(os.path.join(W, "plan/m/face_study_L.npy")), a.canvas_face_pxmm),
    }
    res["values_face"] = {k: values(v) for k, (v, _) in faces.items()}
    res["bands_face_rms_L"] = {k: band_energy(v, s) for k, (v, s) in faces.items()}
    res["speculars_face"] = {k: speculars(v, s) for k, (v, s) in faces.items()}
    res["edges_face_mm_of_face"] = {k: edge_widths(v, s) for k, (v, s) in faces.items()}
    skins = {
        "photo cheek": (crop(photo, box(a.photo_skin)), p_pxmm),
        "final forehead": (crop(sheets["round 19 final"], skin_canvas), a.canvas_face_pxmm),
        "schema forehead": (crop(sheets["round 19 schema (last)"], skin_canvas), a.canvas_face_pxmm),
        "mesh render forehead": (crop(sheets["round 19 mesh render v19"], skin_canvas), a.canvas_face_pxmm),
    }
    res["bands_skin_rms_L"] = {k: band_energy(v, s) for k, (v, s) in skins.items()}
    hairs = {
        "photo hair": (crop(photo, box(a.photo_hair)), p_pxmm),
        "final hair": (crop(sheets["round 19 final"], hair_canvas), a.canvas_face_pxmm),
        "mesh render hair": (crop(sheets["round 19 mesh render v19"], (20, 2420, 120, 260)), a.canvas_face_pxmm),
    }
    res["bands_hair_rms_L"] = {k: band_energy(v, s) for k, (v, s) in hairs.items()}
    res["values_hair"] = {k: values(v) for k, (v, _) in hairs.items()}

    # the hand
    el = json.load(open(os.path.join(W, "main_elements.json")))
    hand_pts = next(e for e in el if "fist" in e["name"])["region"]["pts"]
    arm = next((e for e in el if "arm" in e["name"]), None)
    fin = sheets["round 19 final"]
    hm = poly_mask(fin.shape, hand_pts)
    from scipy.ndimage import binary_dilation, binary_erosion
    ring = binary_dilation(hm, iterations=6) & ~binary_erosion(hm, iterations=6)
    res["hand_silhouette_edges_final_mm_on_sheet"] = edge_widths(fin, 5.0, mask=ring)
    if arm:
        am = poly_mask(fin.shape, arm["region"]["pts"]) & ~hm
        aring = binary_dilation(am, iterations=6) & ~binary_erosion(am, iterations=6) & ~binary_dilation(hm, iterations=12)
        res["arm_silhouette_edges_final_mm_on_sheet"] = edge_widths(fin, 5.0, mask=aring)
    ys, xs = np.nonzero(hm)
    res["hand_extent_canvas_px"] = dict(w=int(np.ptp(xs)), h=int(np.ptp(ys)), diag=float(math.hypot(np.ptp(xs), np.ptp(ys))))
    res["hand_values_final"] = values(fin[hm])
    hs = load_L(os.path.join(W, "plan/m/hand_study_L.npy"))
    hd = load_L(os.path.join(W, "main_details/detail_05/full.png"))
    hands = {
        "hand study (4x)": (hs, 4 * a.canvas_hand_pxmm),
        "hand detail as drawn (4x)": (hd, 4 * a.canvas_hand_pxmm),
        "final hand (1x)": (crop(fin, (1290, 1140, 310, 340)), a.canvas_hand_pxmm),
        "mesh render hand (1x)": (crop(sheets["round 19 mesh render v19"], (1290, 1140, 310, 340)), a.canvas_hand_pxmm),
    }
    res["bands_hand_rms_L"] = {k: band_energy(v, s) for k, (v, s) in hands.items()}
    res["speculars_hand"] = {k: speculars(v, s) for k, (v, s) in hands.items()}
    # the detail's seam: grain just inside vs just outside the hand detail's rectangle, in the sky
    res["detail_seam_grain_L"] = dict(inside=fine_grain(fin, (1264, 1300, 26, 200)), outside=fine_grain(fin, (1225, 1300, 26, 200)),
                                      sky_far=fine_grain(fin, (900, 600, 200, 200)))
    # fine texture on the sheet (sheet-mm, 5 px/mm) inside each declared element and in open sky
    def sheet_bands(mask):
        out = {}
        for smm in (0.2, 0.4, 0.8, 1.6):
            b = gaussian_filter(fin, smm * 5) - gaussian_filter(fin, 2 * smm * 5)
            out[smm] = float(np.sqrt((b[mask] ** 2).mean()))
        out["L_p50"] = float(np.median(fin[mask]))
        return out
    elm = {e["name"]: binary_erosion(poly_mask(fin.shape, e["region"]["pts"]), iterations=8) for e in el
           if e["region"].get("type") == "poly"}
    sky = np.zeros(fin.shape, bool); sky[300:900, 300:1100] = True
    elm["open sky"] = sky
    res["sheet_bands_by_element_rms_L"] = {k: sheet_bands(m) for k, m in elm.items() if m.sum() > 50}
    # composition: how the sheet is spent
    from scipy.ndimage import uniform_filter
    def comp(Lw, px_mm=5.0):
        k = int(5 * px_mm)
        m = uniform_filter(Lw, k); sd = np.sqrt(np.clip(uniform_filter(Lw ** 2, k) - m ** 2, 0, None))
        return dict(flat_midtone=float(((Lw > 35) & (Lw < 65) & (sd < 1.0)).mean()), bare_paper=float((Lw > 92).mean()),
                    near_black=float((Lw < 25).mean()))
    res["composition"] = {"round 19 final": comp(fin), "photo": comp(photo)}
    res["composition"]["element_area_share"] = {e["name"]: float(poly_mask(fin.shape, e["region"]["pts"]).mean())
                                                for e in el if e["region"].get("type") == "poly"}
    res = r(res)
    txt = json.dumps(res, indent=1)
    print(txt)
    if a.out:
        open(a.out, "w").write(txt)


if __name__ == "__main__":
    main()
