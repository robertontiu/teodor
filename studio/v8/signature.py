"""Teodor's signature: a handwritten "Teodor" with an underline flourish, laid down as
tapered brush strokes in a corner of a finished painting.

    python3 signature.py in.png out.png [corner]     corner: auto (default) | br | bl
    from signature import sign_array                  sign an (H, W, 3) float array in 0..1

The corner is chosen automatically (the calmer of bottom-right and bottom-left, preferring
bottom-right), and the color is taken from the paint under it: a pale warm ochre over dark
passages, a deep umber over light ones, tinted slightly toward the local hue.
"""
import math, sys
import numpy as np

# Glyph strokes in a unit box (x right, y down; width ~1.0, height ~0.8).
# Each stroke: list of (x, y, pressure).
GLYPH = [
    # T: crossbar, then the stem with a small hook
    [(0.00, 0.10, .35), (0.08, 0.07, .8), (0.15, 0.05, .9), (0.21, 0.03, .4)],
    [(0.115, 0.06, .5), (0.11, 0.25, 1.0), (0.105, 0.45, .9), (0.095, 0.56, .7), (0.065, 0.60, .35)],
    # e
    [(0.19, 0.44, .5), (0.25, 0.43, .8), (0.27, 0.37, .7), (0.23, 0.34, .6), (0.19, 0.40, .9), (0.20, 0.51, .9), (0.25, 0.55, .7), (0.30, 0.52, .4)],
    # o
    [(0.36, 0.35, .6), (0.32, 0.40, .9), (0.32, 0.50, .9), (0.37, 0.55, .8), (0.42, 0.49, .9), (0.415, 0.39, .8), (0.37, 0.35, .5)],
    # d: bowl, then the tall stem
    [(0.55, 0.40, .6), (0.50, 0.36, .8), (0.46, 0.43, .9), (0.47, 0.53, .9), (0.52, 0.55, .8), (0.56, 0.49, .6)],
    [(0.585, 0.00, .4), (0.575, 0.20, 1.0), (0.565, 0.42, .95), (0.565, 0.53, .8), (0.60, 0.56, .4)],
    # o
    [(0.68, 0.35, .6), (0.64, 0.40, .9), (0.64, 0.50, .9), (0.69, 0.55, .8), (0.74, 0.49, .9), (0.735, 0.39, .8), (0.69, 0.35, .5)],
    # r
    [(0.80, 0.36, .6), (0.795, 0.46, 1.0), (0.79, 0.555, .7)],
    [(0.797, 0.44, .5), (0.82, 0.38, .8), (0.87, 0.35, .7), (0.91, 0.37, .35)],
    # underline flourish
    [(0.03, 0.68, .2), (0.30, 0.665, .6), (0.65, 0.645, .55), (0.97, 0.61, .15)],
]


def _catmull(pts, n=10):
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = map(np.array, (p[i - 1], p[i], p[i + 1], p[i + 2]))
        for s in range(n):
            t = s / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(pts[-1]))
    return np.array(out)


def _stamp(img, x, y, r, col, a):
    H, W, _ = img.shape
    R = int(math.ceil(r)) + 1
    x0, x1, y0, y1 = max(0, int(x) - R), min(W, int(x) + R + 1), max(0, int(y) - R), min(H, int(y) + R + 1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
    m = np.clip(r + 0.6 - d, 0, 1) * a
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m[..., None]) + col * m[..., None]


def _calm(img, x0, y0, w, h):
    patch = img[y0:y0 + h, x0:x0 + w]
    lum = patch.mean(-1)
    return float(lum.std()), patch.reshape(-1, 3).mean(0), float(lum.mean())


def sign_array(img, corner="auto", rng_seed=7):
    """Sign an (H, W, 3) float image in 0..1, in place. Returns the image."""
    H, W, _ = img.shape
    sw = max(64, int(W * 0.12))           # signature width
    sh = int(sw * 0.72)
    mx, my = int(W * 0.035), int(H * 0.03)
    spots = {"br": (W - mx - sw, H - my - sh), "bl": (mx, H - my - sh)}
    if corner == "auto":
        sbr, _, _ = _calm(img, *spots["br"], sw, sh)
        sbl, _, _ = _calm(img, *spots["bl"], sw, sh)
        corner = "bl" if sbl < sbr * 0.6 else "br"
    ox, oy = spots[corner]
    _, mean, lum = _calm(img, ox, oy, sw, sh)
    hue = mean / (mean.mean() + 1e-6)
    if lum < 0.45:
        base = np.array([0.86, 0.77, 0.60]) * 0.85 + 0.15 * np.clip(hue * 0.8, 0, 1.2)
    else:
        base = np.array([0.17, 0.12, 0.09]) * 0.85 + 0.15 * np.clip(mean * 0.5, 0, 1)
    col = np.clip(base * 0.78 + mean * 0.22, 0, 1).astype(np.float32)
    rng = np.random.default_rng(rng_seed)
    width = max(1.0, sw * 0.022)
    for stroke in GLYPH:
        pts = np.array(stroke, np.float32)
        path = _catmull([tuple(p) for p in pts], n=14)
        L = np.linalg.norm(np.diff(path[:, :2], axis=0), axis=1).sum() * sw
        steps = max(4, int(L / max(0.4, width * 0.35)))
        for i in range(steps + 1):
            t = i / steps
            k = t * (len(path) - 1)
            j = min(int(k), len(path) - 2)
            f = k - j
            x, y, p = path[j] * (1 - f) + path[j + 1] * f
            taper = min(1.0, 0.35 + t / 0.15 * 0.65) * (1.0 if t < 0.75 else 1 - (t - 0.75) / 0.25 * 0.7)
            r = width * (0.45 + 0.75 * p) * taper * rng.uniform(0.92, 1.06)
            _stamp(img, ox + x * sw, oy + y * sh, r, col, 0.8)
    return img


if __name__ == "__main__":
    from PIL import Image
    src, dst = sys.argv[1], sys.argv[2]
    corner = sys.argv[3] if len(sys.argv) > 3 else "auto"
    a = np.asarray(Image.open(src).convert("RGB"), np.float32) / 255
    sign_array(a, corner)
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(dst)
    print(dst)
