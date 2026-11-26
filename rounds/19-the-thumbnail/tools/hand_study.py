"""Tonal study of the fist and thumb (my drawing, in L*), for the 4x hand detail
(canvas x 1260-1640, y 1100-1520; 1520 x 1680 detail px). Built on the mesh render of the hand
(plan/m/hand_sun_ref.png, registered with the detail) and the schema's sky and sleeve, with what the
mesh can't do: the blocky fingers smoothed into knuckles, dark occlusion between the curled fingers,
the thumb's straight distal crease, the nail plate, a lit rim on the thumb's upper edge, the tendons
fanning toward the wrist. Values: lit skin to L* 86, shadow side ~45, gaps ~30 (carbon floor)."""
import numpy as np, math
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

X0, Y0, W, H, N = 1260, 1100, 380, 420, 4
DW, DH = W * N, H * N
OUT = "/home/claude/teodor-work/19/plan/m/"
rgb = np.asarray(Image.open(OUT + "hand_sun_ref.png").convert("RGB")).astype(float)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
Y = 0.2126 * r + 0.7152 * g + 0.0722 * b

def to_L(y):
    y = np.clip(y / 255.0, 0, 1)
    lin = np.where(y <= 0.04045, y / 12.92, ((y + 0.055) / 1.055) ** 2.4)
    return 116 * np.cbrt(lin) - 16

# schema (sky, sleeve) upsampled to the detail
S = np.load(OUT + "schema3_L.npy")[Y0:Y0 + H, X0:X0 + W].astype(float)
S4 = ndi.zoom(S, N, order=1)[:DH, :DW]

# masks from the render: skin is warm, the sky is a cool mid grey, the sleeve a light cool grey
skin = ((r - b) > 14) & (Y > 40)
skin = ndi.binary_opening(skin, iterations=2)
skin = ndi.binary_closing(skin, iterations=3)
lab, n = ndi.label(skin)
sizes = ndi.sum(skin, lab, range(1, n + 1))
skin = lab == (1 + int(np.argmax(sizes)))
skin = ndi.binary_fill_holes(skin)
# the wrist's shadow (dark purple in the render) belongs to the hand, between skin and cuff
wrist = (Y < 120) & (np.abs(r - b) < 25) & (np.arange(DH)[:, None] > 1350) & (np.arange(DW)[None, :] > 820) & (np.arange(DW)[None, :] < 1330)
hand = ndi.binary_closing(skin | wrist, iterations=4)
hand = ndi.binary_fill_holes(hand)
hand = ndi.gaussian_filter(hand.astype(float), 5) > 0.5   # a drawn silhouette, not the mesh's facets
gaps = (Y < 45) & ndi.binary_dilation(skin, iterations=6) & (np.arange(DH)[:, None] < 800)
gaps = ndi.gaussian_filter(((Y < 62) & ndi.binary_dilation(skin, iterations=6) & (np.arange(DH)[:, None] < 800)).astype(float), 3) > 0.35   # the occlusion as shapes, not the mesh's jags

# skin value: the render's lightness smoothed (the mesh's blocks are not form), remapped
Ls = to_L(Y)
Ls = ndi.median_filter(Ls, 9)
Ls = ndi.gaussian_filter(Ls, 4)
sk = Ls[hand & ~gaps]
lo, hi = np.percentile(sk, 2), np.percentile(sk, 99.5)
Lh = 44 + (np.clip(Ls, lo, hi) - lo) / (hi - lo) * (86 - 44)

L = S4.copy()
L[hand] = Lh[hand]

yy, xx = np.mgrid[0:DH, 0:DW].astype(float)
def g2(cx, cy, sx, sy, ang=0.0):
    a = math.radians(ang); dx, dy = xx - cx, yy - cy
    u = dx * math.cos(a) + dy * math.sin(a); v = -dx * math.sin(a) + dy * math.cos(a)
    return np.exp(-(u / sx) ** 2 / 2 - (v / sy) ** 2 / 2)
def curve(pts, width, soft):
    im = Image.new("L", (DW, DH), 0); d = ImageDraw.Draw(im)
    d.line([tuple(map(float, p)) for p in pts], fill=255, width=int(width), joint="curve")
    return ndi.gaussian_filter(np.asarray(im, float) / 255, soft)
def bez(p0, p1, p2, n=30):
    t = np.linspace(0, 1, n)[:, None]; p0, p1, p2 = map(np.array, (p0, p1, p2))
    return ((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2).tolist()

hm = hand.astype(float)
# 0. the light: low sun behind and to the left. The planes facing up-left are lit, the back of the hand
# turned to us falls into half-light, the right (little-finger) side into shadow.
dv = np.array([0.62, 0.78]); t = (xx - 150) * dv[0] + (yy - 150) * dv[1]
t = np.clip(t / 1500.0, 0, 1)
L -= (22 * t ** 1.3 - 4) * hm
L -= 8 * np.clip((xx - 1150) / 250, 0, 1) * hm         # the turning edge on the little-finger side
L = np.where(hand, ndi.gaussian_filter(np.where(hand, L, 60), 1.0) / np.maximum(ndi.gaussian_filter(hm, 1.0), 1e-3), L)
# 1. occlusion between and under the curled fingers: the carbon darks
dark_gap = ndi.gaussian_filter((gaps | ((Y < 70) & hand & (yy < 760))).astype(float), 2.0)
L = L * (1 - dark_gap) + 30 * dark_gap
# 2. the lit rim on the thumb's upper-left edge (sun behind, to the left): a thin bright band inside the silhouette
edge_in = hand & ~ndi.binary_erosion(hand, iterations=9)
rim = edge_in & (xx < 560) & (yy < 700) & (yy + 0.4 * xx < 640)
rimf = ndi.gaussian_filter(rim.astype(float), 3) * hm
L += 12 * rimf
# 3. the thumb's IP crease: short creases across the back of the thumb, each a valley with a lit lip
ax = np.array([0.55, 0.835]); pr = np.array([0.835, -0.55])
c0 = np.array([318.0, 395.0])
for k, (off, dep, ln) in enumerate([(0, 7, 60), (17, 4, 46), (-16, 3, 40)]):
    c = c0 + ax * off
    p0, p2 = c - pr * ln, c + pr * ln; p1 = c + ax * 8
    L -= dep * curve(bez(p0, p1, p2), 8, 4.5) * hm
    L += 0.5 * dep * curve(bez(p0 + ax * 9, p1 + ax * 9, p2 + ax * 9), 8, 5) * hm
# the MP joint of the thumb: a soft knob of light where it bends
L += 4 * g2(470, 610, 45, 30, 50) * hm
# 4. the nail plate at the tip: a smoother, slightly lighter plate with a darker lateral fold
nail = (r - g > 38) & (yy < 380) & (xx < 300) & skin
nail = ndi.binary_opening(nail, iterations=2)
nf = ndi.gaussian_filter(nail.astype(float), 2)
L = L * (1 - nf) + (ndi.gaussian_filter(np.where(nail, L, 0), 6) / np.maximum(ndi.gaussian_filter(nail.astype(float), 6), 1e-3) + 3) * nf
fold = nail ^ ndi.binary_erosion(nail, iterations=3)
fold &= (xx > 175)  # the fold on the shadow side only
L -= 8 * ndi.gaussian_filter(fold.astype(float), 1.5)
# 4b. the nail plate drawn: from the indented free edge down the thumb's axis, a smooth lighter plate,
# darker lateral folds, the cuticle's soft dark arc at its root
na = np.array([0.47, 0.88]); nw = np.array([0.88, -0.47]); fe = np.array([195.0, 209.0])
u = (xx - fe[0]) * na[0] + (yy - fe[1]) * na[1]; v = (xx - fe[0]) * nw[0] + (yy - fe[1]) * nw[1]
plate = (u > 4) & (u < 150) & (np.abs(v) < 44 - 10 * np.clip((u - 110) / 40, 0, 1) ** 2 * 3) & hand
pf = ndi.gaussian_filter(plate.astype(float), 2.5)
L += 4 * pf
L -= 7 * ndi.gaussian_filter((plate ^ ndi.binary_erosion(plate, iterations=4)).astype(float) * (np.abs(v) > 30), 2)
L -= 8 * ndi.gaussian_filter(((u > 148) & (u < 160) & (np.abs(v) < 38) & hand).astype(float), 3)
L += 5 * ndi.gaussian_filter(((u > 162) & (u < 178) & (np.abs(v) < 34) & hand).astype(float), 4)
# 5. the knuckle heads of the curled fingers: lit tops, a dark underside (read off the render's finger tops)
for (cx, cy, sx, sy, a) in [(735, 300, 55, 40, 20), (960, 330, 50, 38, 30), (1120, 440, 45, 34, 40), (1270, 560, 38, 30, 50)]:
    L += 6 * g2(cx, cy, sx, sy, a) * hm
    L -= 7 * g2(cx + 30, cy + 70, sx * 0.9, sy * 0.6, a) * hm
# 6. the extensor tendons fanning from the knuckles toward the wrist: faint lit ridges with a shadow beside
for (p0, p2) in [((760, 680), (930, 1350)), ((960, 700), (1010, 1360)), ((1150, 760), (1080, 1360))]:
    p1 = ((p0[0] + p2[0]) / 2 + 15, (p0[1] + p2[1]) / 2)
    L += 3.0 * curve(bez(p0, p1, p2), 18, 9) * hm
    L -= 2.0 * curve(bez((p0[0] + 26, p0[1]), (p1[0] + 26, p1[1]), (p2[0] + 26, p2[1])), 18, 9) * hm
# 7. the wrist darkens into the cuff (the cuff's cast shadow is sharp: low sun)
cuff_sh = (yy > 1400 + (xx - 850) * 0.06) & hand
L -= 8 * ndi.gaussian_filter(cuff_sh.astype(float), 3)
# the mesh's wrist cut: let the wrist's value run on smoothly from the hand above it
wr = hand & (yy > 1330)
Lw = ndi.gaussian_filter(np.where(hand, L, 0), 25) / np.maximum(ndi.gaussian_filter(hm, 25), 1e-3)
L = np.where(wr, 0.35 * L + 0.65 * Lw, L)
# the render's antialiased fringe: replace the outer 3 px ring of the hand by the values just inside it
inner = ndi.binary_erosion(hand, iterations=3); ring = hand & ~inner
Lin = ndi.gaussian_filter(np.where(inner, L, 0), 3) / np.maximum(ndi.gaussian_filter(inner.astype(float), 3), 1e-3)
L = np.where(ring, Lin, L)
# soften the silhouette by a hair (focal plane: crisp), clamp
L = np.where(hand & ~gaps & ~(dark_gap > 0.5), np.maximum(L, 42 + 0 * L), L)
# the sky next to the hand: the schema's old silhouette left a light fringe; take the sky from further out
skyz = ~ndi.binary_dilation(hand, iterations=40)
Ssky = ndi.gaussian_filter(np.where(skyz, S4, 0), 30) / np.maximum(ndi.gaussian_filter(skyz.astype(float), 30), 1e-3)
near = ~hand & ~skyz & (S4 < 66) & (yy < 1350)
L = np.where(near, Ssky, L)
L = np.clip(L, 28, 90)
np.save(OUT + "hand_study_L.npy", L.astype(np.float32))
np.save(OUT + "hand_study_mask.npy", hand)

def L_to_srgb(Lv):
    fy = (Lv + 16) / 116; lin = np.where(Lv > 8, fy ** 3, Lv / 903.3)
    s = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
    return np.clip(s * 255, 0, 255).astype(np.uint8)
im = L_to_srgb(L)
Image.fromarray(im).convert("RGB").save(OUT + "hand_study_4x.png")
Image.fromarray(im).resize((DW // 2, DH // 2), Image.LANCZOS).save("/tmp/r19_hand_study_half.png")
print("hand px", hand.sum(), "L range in hand", L[hand].min(), L[hand].max())
