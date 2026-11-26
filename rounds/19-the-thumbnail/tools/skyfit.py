"""Schema v24: the schema with its sky replaced by the sky as drawn (a smooth fit of the canvas's sky
outside the passages I re-blended), so corrections match the drawing's own key. The moon is kept."""
import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi
from skimage.color import rgb2lab
W = "/home/claude/teodor-work/19/"
c = rgb2lab(np.asarray(Image.open(W + "main_full.png").convert("RGB")) / 255.)[..., 0]
m = np.load(W + "plan/m/schema3_masks.npz"); S = np.load(W + "plan/m/schema3_L.npy").astype(float)
sky = m["sky"].astype(bool) & ~ndi.binary_dilation(m["moon"].astype(bool), iterations=20)
yy, xx = np.mgrid[0:3200, 0:2400]
bad = ((xx - 1420) / 560.) ** 2 + ((yy - 1300) / 520.) ** 2 < 1
good = sky & ~bad & ~ndi.binary_dilation(~m["sky"].astype(bool), iterations=25)
s = 4
cs = c[::s, ::s]; gs = good[::s, ::s].astype(float)
num = ndi.gaussian_filter(cs * gs, 40); den = ndi.gaussian_filter(gs, 40)
fit = num / np.maximum(den, 1e-4)
fit = ndi.zoom(fit, s, order=1)[:3200, :2400]
L = S.copy(); L[m["sky"].astype(bool)] = fit[m["sky"].astype(bool)]
mo = m["moon"].astype(bool); L[mo] = S[mo]
np.save(W + "plan/m/schema4_L.npy", L.astype(np.float32))
fy = (L + 16) / 116; lin = np.where(L > 8, fy ** 3, L / 903.3)
sr = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
Image.fromarray(np.clip(sr * 255, 0, 255).astype(np.uint8)).convert("RGB").save(W + "plan/m/schema4.png")
print("sky fit at hand", fit[1300, 1200], "canvas", c[1300, 1200], "outside", c[1300, 800])
