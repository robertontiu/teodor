"""Tonal study of the face (my drawing, in L*), built on the schema's region of the face and the
mesh render's planes, with what the mesh can't do: the near eye clenched, crow's feet, the bunched
cheek, the deepened nasolabial fold, the grin's corner, the stubble zone. Region: canvas x 250-1350,
y 2330-3190. Output: a 4x study for the face detail."""
import numpy as np, math
from PIL import Image
from scipy import ndimage as ndi
X0, Y0, W, H = 250, 2330, 1100, 860
S = np.load("/home/claude/teodor-work/19/plan/m/schema3_L.npy")[Y0:Y0 + H, X0:X0 + W].astype(float)
yy, xx = np.mgrid[0:H, 0:W].astype(float)
def g(cx, cy, sx, sy, ang=0.0):
    a = math.radians(ang); dx, dy = xx - cx, yy - cy
    u = dx * math.cos(a) + dy * math.sin(a); v = -dx * math.sin(a) + dy * math.cos(a)
    return np.exp(-(u / sx) ** 2 / 2 - (v / sy) ** 2 / 2)
def curve_mask(pts, width, soft):
    from PIL import ImageDraw
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    d.line([tuple(p) for p in pts], fill=255, width=int(width), joint="curve")
    return ndi.gaussian_filter(np.asarray(im, float) / 255, soft)
def bez(p0, p1, p2, n=30):
    t = np.linspace(0, 1, n)[:, None]; p0, p1, p2 = map(np.array, (p0, p1, p2))
    return ((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2).tolist()
L = S.copy()
skin = (S > 30) & (xx > 25)
# 1. the brow lowered and pressed (AU4 on the near side): the socket's shadow deepens under the ridge
L -= 9 * g(470, 470, 22, 120, 5) * skin
# 2. the closed near eye: the upper lid lit, a pressed dark slit, the lower lid rolled up by the cheek
L += 6 * g(515, 460, 22, 110, 3) * skin                       # upper lid catching light
fis = bez((560, 338), (640, 450), (556, 592), 40)             # the fissure: along the lid bulge's edge, bowed toward the cheek
L -= 22 * curve_mask(fis, 6, 3.0)                             # lash line pressed into the fold (a crease, not a line)
lash = bez((566, 360), (628, 455), (560, 575), 30)
L -= 9 * curve_mask(lash, 18, 5)                              # the clumped lashes as a soft dark band
roll = bez((594, 345), (650, 465), (580, 605), 40)
L += 12 * curve_mask(roll, 22, 6)                             # the lower lid and cheek rolled up, lit
L -= 10 * curve_mask(bez((622, 360), (676, 475), (608, 620), 40), 16, 7)   # the shadow under the roll
# the squeeze folds the upper lid: two soft arcs parallel to the lid margin
for off, dep in ((-28, 7), (-52, 5)):
    arc = bez((560 + off * 0.6, 345), (640 + off, 455), (556 + off * 0.6, 585), 30)
    L -= dep * curve_mask(arc, 6, 4); L += 0.6 * dep * curve_mask([(q[0] - 8, q[1]) for q in arc], 6, 4)
# 3. crow's feet: creases fanning from the outer corner (toward the temple: down-left), each a valley with a lit lip
oc = np.array([556, 600])
for ang, ln, dep in [(196, 110, 11), (216, 140, 13), (236, 130, 12), (256, 105, 10), (276, 75, 7)]:
    a = math.radians(ang); d = np.array([math.cos(a), -math.sin(a)])
    nrm = np.array([-d[1], d[0]])
    p0 = oc + d * 14; p2 = oc + d * ln; p1 = (p0 + p2) / 2 + nrm * 9
    L -= 0.8 * dep * curve_mask(bez(p0, p1, p2, 24), 7, 4.0)
    L += 0.5 * dep * curve_mask(bez(p0 + nrm * 9, p1 + nrm * 9, p2 + nrm * 9, 24), 8, 4.5)
# 4. the cheek bunched up toward the eye (AU6): a lit ball with a soft lower shadow
L += 8 * g(690, 520, 75, 95, 20) * skin
L -= 7 * g(770, 640, 60, 50, 30) * skin
# 5. the nasolabial fold deepened, curving round the lifted cheek to the mouth's corner
nl = bez((835, 345), (842, 520), (930, 610), 50)
L -= 16 * curve_mask(nl, 10, 5)
L += 6 * curve_mask([(p[0] - 14, p[1]) for p in nl], 10, 6)  # its lit lip on the cheek side
# 6. the grin's near corner: pulled up and back, a small dimple shadow and the lit upper lip over it
L -= 14 * g(950, 600, 14, 22, 30)
L += 5 * g(930, 560, 20, 18)
# 7. the stubble zone (beyond the fold: upper lip, around the mouth, the jaw): darker, a few L*, with a fine mottle
rng = np.random.default_rng(19)
beard = np.clip((xx - 860) / 60, 0, 1) * skin
beard = np.maximum(beard, np.clip((yy - 700) / 80, 0, 1) * np.clip((xx - 600) / 80, 0, 1) * skin)
mott = ndi.gaussian_filter(rng.standard_normal((H, W)), 1.6)
L -= beard * (6 + 1.2 * mott / mott.std())
# 8. the forehead: two faint long folds, very soft (out of the focal plane), so it isn't an empty block
for cx in (200, 300):
    L -= 3 * curve_mask(bez((cx, 120), (cx - 25, 330), (cx + 10, 540), 30), 10, 9) * skin
L = ndi.gaussian_filter(L, 1.2)            # the face sits about 1 mm in front of the focal plane
np.save("/home/claude/teodor-work/19/plan/m/face_study_L.npy", L.astype(np.float32))
def to8(L):
    L = np.clip(L, 0, 100); y = np.where(L > 8, ((L + 16) / 116) ** 3, L / 903.3)
    return (np.where(y <= 0.0031308, 12.92 * y, 1.055 * y ** (1 / 2.4) - 0.055) * 255).clip(0, 255).astype(np.uint8)
Image.fromarray(to8(L)).save("/home/claude/teodor-work/19/plan/m/face_study.png")
big = Image.fromarray(to8(L)).resize((W * 4, H * 4), Image.BICUBIC)
big.save("/home/claude/teodor-work/19/plan/m/face_study_4x.png")
