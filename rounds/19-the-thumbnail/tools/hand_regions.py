"""Polygons (detail px) from the hand study: the whole hand, the gaps, and the sky ring around it."""
import numpy as np, json
from skimage import measure
from scipy import ndimage as ndi
M = np.load("/home/claude/teodor-work/19/plan/m/hand_study_mask.npy")
L = np.load("/home/claude/teodor-work/19/plan/m/hand_study_L.npy")
def poly(mask, tol=2.0):
    c = measure.find_contours(np.pad(mask, 1).astype(float), 0.5)
    c = max(c, key=len)
    c = measure.approximate_polygon(c, tol)
    return [[round(float(p[1]) - 1, 1), round(float(p[0]) - 1, 1)] for p in c]
out = {"hand": poly(M), "hand_in": poly(ndi.binary_erosion(M, iterations=6)),
       "hand_out": poly(ndi.binary_dilation(M, iterations=10))}
# upper hand (above the wrist) for the finer work
up = M.copy(); up[1380:] = False
out["hand_upper"] = poly(up)
json.dump(out, open("/home/claude/teodor-work/19/plan/m/hand_regions.json", "w"))
print({k: len(v) for k, v in out.items()})
