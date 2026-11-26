"""Compare the detail's rendered L* with a study, per zone (my ruler)."""
import numpy as np, sys
from PIL import Image
from skimage.color import rgb2lab
img = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(float) / 255
Lc = rgb2lab(img)[..., 0]
S = np.load(sys.argv[2]); M = np.load(sys.argv[3]) if len(sys.argv) > 3 else None
if Lc.shape != S.shape:
    from scipy import ndimage as ndi
    S = ndi.zoom(S, (Lc.shape[0] / S.shape[0], Lc.shape[1] / S.shape[1]), order=1)
    if M is not None: M = ndi.zoom(M.astype(float), (Lc.shape[0] / M.shape[0], Lc.shape[1] / M.shape[1]), order=0) > 0.5
H, W = Lc.shape
for name, (y0, y1, x0, x1) in {"thumb": (0.08, 0.3, 0.05, 0.3), "fingers": (0.1, 0.35, 0.3, 0.75), "back": (0.35, 0.7, 0.3, 0.8), "wrist": (0.75, 0.95, 0.45, 0.8)}.items():
    sl = (slice(int(y0 * H), int(y1 * H)), slice(int(x0 * W), int(x1 * W)))
    m = M[sl] if M is not None else np.ones_like(Lc[sl], bool)
    print(f"{name:8s} canvas {Lc[sl][m].mean():5.1f} p90 {np.percentile(Lc[sl][m],90):5.1f}  study {S[sl][m].mean():5.1f} p90 {np.percentile(S[sl][m],90):5.1f}")
