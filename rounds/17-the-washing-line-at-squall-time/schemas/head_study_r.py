"""Revision head study (detail coordinates, 1040x1200): the scene_14 render's planes regrouped into Teodor's
values and colours. Lit planes warm, light; shadow side a cool storm grey lost into the hair; quiet lip and lash
shifts; the neck drawn by hand into the painted collar; hair a dark mass behind. Not painted onto the canvas:
it is the schema the head is matched against."""
import sys, json, numpy as np
from PIL import Image
from scipy import ndimage
from skimage.draw import polygon
D = "/home/claude/teodor-work/17/"
ref = np.asarray(Image.open(D + "main_detail_ref.png").convert("RGB")).astype(np.float32) / 255
cur = np.asarray(Image.open(D + "main_detail_full.png").convert("RGB")).astype(np.float32) / 255
z = np.load(D + "main_detail_elements.npz"); P = json.load(open(D + "schema/head_polys_r.json"))
H, W = 1200, 1040
def pm(pts):
    m = np.zeros((H, W), bool); rr, cc = polygon([p[1] for p in pts], [p[0] for p in pts], (H, W)); m[rr, cc] = True; return m
hx = lambda s: np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255
L = ndimage.gaussian_filter(ref.mean(-1), 2.5)
face = ndimage.binary_closing(z["she.face"] | z["she.head"] & ~z["she.hair"], iterations=3)
neck = pm(P["neck_mine"])
yy0, xx0 = np.mgrid[0:H, 0:W]
skin = ndimage.binary_fill_holes(ndimage.binary_closing(face | neck | (z["she.neck"] & (yy0 < 700) & (xx0 < 700)), iterations=12))
hair = ndimage.binary_closing(z["she.hair"], iterations=3) & ~skin
# behind the neck, under the hair: the dark fall of hair (was the render's own neck and shoulder)
behind = pm([[640, 545], [760, 520], [860, 600], [900, 760], [820, 860], [660, 820], [690, 560]]) & ~neck
# value ramp (render L -> colour): shadow side cool storm grey, halftones, light, top light
stops = [(0.00, "#4e4549"), (0.20, "#5d5457"), (0.38, "#7a6a68"), (0.52, "#a2826f"), (0.64, "#c6a38a"), (0.76, "#dcbea4"), (0.88, "#e8d2ba")]
xs = np.array([s[0] for s in stops]); cs = np.stack([hx(s[1]) for s in stops])
Lc = np.clip(L, 0, 0.88)
col = np.stack([np.interp(Lc, xs, cs[:, k]) for k in range(3)], -1)
# warm reflected light in the shadow under the jaw and on the throat's shadow (bounce from the wool)
yy, xx = np.mgrid[0:H, 0:W]
bw = (np.clip((yy - 500) / 160, 0, 1) * np.clip((0.34 - L) / 0.1, 0, 1) * skin * 0.35)[..., None]
col = col * (1 - bw) + hx("#6e5a52") * bw
# lips: a quiet colour shift where the render's lips are redder than the skin round them, kept inside the value
red = ref[..., 0] - ref[..., 1]
lips = ndimage.binary_opening((red > np.quantile(red[face], 0.93)) & face & (yy > 420) & (yy < 540), iterations=1)
lips = ndimage.gaussian_filter(lips.astype(np.float32), 2.0)
lipcol = col * np.array([1.02, 0.9, 0.88], np.float32)
col = col * (1 - lips[..., None] * 0.8) + lipcol * lips[..., None] * 0.8
# the lash line of the laughing crescents: the render's eye slits, a soft dark, never black
eyes = (L < 0.22) & face & (yy > 270) & (yy < 340) & (xx < 520)
eyes = ndimage.gaussian_filter(eyes.astype(np.float32), 1.5)
col = col * (1 - eyes[..., None] * 0.6) + hx("#44373a") * eyes[..., None] * 0.6
out = cur.copy()
hl = np.clip((L - 0.05) / 0.4, 0, 1)[..., None]
haircol = hx("#261d19") * (1 - hl) + hx("#4d3d33") * hl
out[hair | behind] = haircol[hair | behind] if True else 0
out[behind] = hx("#2a201c")
sk = ndimage.gaussian_filter(skin.astype(np.float32), 2.0)[..., None]
out = out * (1 - sk) + col * sk
Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(sys.argv[1])
print("study written", sys.argv[1])
