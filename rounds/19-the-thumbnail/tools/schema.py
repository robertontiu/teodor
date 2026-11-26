"""Round 19 value schema: the 3D render (structure, lens, light) translated into the values of an
orange-filtered black-and-white photograph at f/16, as my drawing to work from. Not the painting."""
import json, math, sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
W, H = 2400, 3200
src = sys.argv[1]; scene = json.load(open(sys.argv[2])); out = sys.argv[3]
rgb = np.asarray(Image.open(src).convert("RGB"), float) / 255
def lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def Lstar(c):
    y = lin(c); return np.where(y > 0.008856, 116 * np.cbrt(y) - 16, 903.3 * y)
def from_L(L):
    L = np.clip(L, 0, 100); y = np.where(L > 8, ((L + 16) / 116) ** 3, L / 903.3)
    return np.where(y <= 0.0031308, 12.92 * y, 1.055 * y ** (1 / 2.4) - 0.055)
# orange filter: weight R and G heavily, blue little (a filtered pan film's response, judgement)
Lr = Lstar(0.55 * rgb[..., 0] + 0.38 * rgb[..., 1] + 0.07 * rgb[..., 2])
M = np.load("/home/claude/teodor-work/19/main_elements.npz")
m = {k.split(".")[-1] if k.startswith("man.") else k: M[k] for k in M.files}
man = m["all"]; moon_m = M["moon.object"]
skin = (m["face"] | m["head"] | m["neck"] | m["hands"]) & ~m["hair"]
cloth = (m["drapery"] | m["arms"] | m["torso"]) & ~skin & ~m["hair"]
green = (rgb[..., 1] > rgb[..., 2] + 0.02) & ~man & ~moon_m
green[:1500] = False
sky = ~man & ~green & ~moon_m
S = np.zeros((H, W))
def remap(L, mask, lo, hi, plo=2, phi=98):
    a, b = np.percentile(L[mask], [plo, phi])
    return np.clip(lo + (L - a) / max(b - a, 1e-3) * (hi - lo), lo - 6, hi + 4)
# --- sky: the render's own gradient, remapped to top L* 40 -> horizon 70
Ls = Lr.copy()
S[sky] = remap(Ls, sky, 43, 70, 1, 99)[sky]
S = np.where(sky, S, 0)
# fill sky behind everything so blurs below can sample it
skyfull = ndi.gaussian_filter(np.where(sky, S, 0), 40) / np.maximum(ndi.gaussian_filter(sky.astype(float), 40), 1e-3)
# cirrus: a few fibrous streaks along one wind (upper left to right, falling), lighter by 4-10 L*
rng = np.random.default_rng(19)
yy, xx = np.mgrid[0:H, 0:W].astype(float)
ang = math.radians(-14)
u = xx * math.cos(ang) + yy * math.sin(ang); v = -xx * math.sin(ang) + yy * math.cos(ang)
noise = ndi.gaussian_filter(rng.standard_normal((H // 8, W // 8)), (0.6, 7))
noise = ndi.zoom(noise, 8, order=1)[:H, :W]
cir = np.zeros((H, W))
for (v0, wid, amp, u0, u1) in [(260, 70, 5.5, -200, 1500), (560, 45, 4, 700, 2700), (1150, 40, 3.5, 200, 1600)]:
    band = np.exp(-((v - v0 - 60 * np.sin(u / 700)) / wid) ** 2)
    ends = np.clip((u - u0) / 300, 0, 1) * np.clip((u1 - u) / 300, 0, 1)
    fib = np.clip(0.55 + 1.4 * noise, 0, 1.5)
    cir += amp * band * ends * fib
cam = scene["camera"]
C = np.array(cam["pos"]); fw = np.array(cam["look_at"]) - C; fw /= np.linalg.norm(fw)
rt = np.cross(fw, cam.get("up", [0, 1, 0])); rt /= np.linalg.norm(rt); up = np.cross(rt, fw)
f = 1 / math.tan(math.radians(cam["fov"]) / 2)
def proj_dir(dv):
    q = np.asarray(dv, float); z = q @ fw
    return (f * (q @ rt) / z) * H / 2 + W / 2, -(f * (q @ up) / z) * H / 2 + H / 2
moon_obj = [o for o in scene["objects"] if o.get("id") == "moon"][0]
mdir = np.array(moon_obj["pos"]) - C; mdir /= np.linalg.norm(mdir)
mx, my = proj_dir(mdir)
# keep the cirrus off the moon (thin there) so the disc stays the sky's brightest small shape
cir *= 1 - 0.85 * np.exp(-((xx - mx) ** 2 + (yy - my) ** 2) / (2 * 140 ** 2))
S = np.where(sky, S + cir, S)
mm_ = ndi.binary_dilation(moon_m, iterations=4)
S = np.where(mm_, ndi.gaussian_filter(np.where(mm_, 0, S), 6) / np.maximum(ndi.gaussian_filter((~mm_).astype(float), 6), 1e-3), S)
# --- moon: true size from the render's mask, phase from the sun
sun = scene["sun"]; az, el = math.radians(sun["azimuth"]), math.radians(sun["elevation"])
ld = np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)])
phase = math.pi - math.acos(float(np.clip(ld @ mdir, -1, 1)))   # sun-moon-observer = 180 - elongation
sx, sy = proj_dir(mdir + 0.02 * ld)
sd = np.array([sx - mx, sy - my]); sd /= np.linalg.norm(sd)
ys_, xs_ = np.nonzero(moon_m); r = 0.5 * max(np.ptp(xs_), np.ptp(ys_)) * 0.92
k = (1 + math.cos(phase)) / 2
dx, dy = xx - mx, yy - my
a = dx * sd[0] + dy * sd[1]; b = -dx * sd[1] + dy * sd[0]
inside = dx ** 2 + dy ** 2 <= r ** 2
semi = r * abs(2 * k - 1)
lit = inside & ((a >= 0) | (a ** 2 / max(semi, 1e-3) ** 2 + b ** 2 / r ** 2 <= 1) if k > 0.5 else (a >= 0) & ~(a ** 2 / max(semi, 1e-3) ** 2 + b ** 2 / r ** 2 <= 1))
litf = ndi.gaussian_filter(lit.astype(float), 1.0)
# terminator dimming over the last third of the lit width; two soft maria (judgement placement)
tw = np.clip((a + semi) / (0.6 * r + semi), 0, 1) if k > 0.5 else np.clip(a / r, 0, 1)
mval = 76 - 6 * (1 - tw)
for (pa, pb, rr, dd) in [(0.25, -0.35, 0.33, 6), (0.45, 0.2, 0.28, 5), (-0.05, -0.1, 0.22, 4)]:
    mval -= dd * np.exp(-(((a / r) - pa) ** 2 + ((b / r) - pb) ** 2) / (2 * rr ** 2))
moonL = np.where(litf > 0, mval, 0)
S = np.where(litf > 0.02, S * (1 - litf) + moonL * litf, S)
print("moon centre", round(mx), round(my), "radius px", round(r, 1), "phase deg", round(math.degrees(phase)), "lit frac", round(k, 2), "sun dir in picture", sd.round(2))
# --- far grass (ground): L* 34 near to 44 at the horizon, little texture (out of the sky, in focus far off)
gy = np.where(green)[0]
Lg = remap(Lr, green, 33, 45)
S = np.where(green, Lg, S)
# --- a distant treeline on the horizon (soft: beyond the focal zone, infinity's blur 12 px)
hor = np.zeros(W, int)
for x in range(W):
    col = green[:, x]
    hor[x] = np.argmax(col) if col.any() else H
tops = ndi.gaussian_filter1d(rng.standard_normal(W), 18) * 60 + ndi.gaussian_filter1d(rng.standard_normal(W), 4) * 14
tl = np.zeros((H, W), bool)
for x in range(W):
    if hor[x] < H:
        t0 = int(hor[x] - 70 - max(tops[x], -60)); tl[max(t0, 0):hor[x] + 2, x] = True
tl &= ~man
tlv = ndi.gaussian_filter(tl.astype(float), 6)
S = np.where(tlv > 0.01, S * (1 - tlv) + 33 * tlv, S)
# --- figure
S = np.where(m["hair"], remap(Lr, m["hair"], 22, 34), S)
S = np.where(cloth, remap(Lr, cloth, 28, 70), S)
S = np.where(m["face"] & ~m["hair"] | m["neck"], remap(Lr, (m["face"] | m["neck"]) & ~m["hair"], 30, 84), S)
S = np.where(m["hands"], remap(Lr, m["hands"], 44, 86), S)
# --- near grass: blades near the lens as soft bands (blur by distance, f/16 table), blades at the
# head's distance nearly sharp, a few small sharp ones at the hand's distance on the ground beyond the arm
def blade_mask(x0, y0, h, w, lean, curve=0.0):
    img = Image.new("L", (W, H), 0); d = ImageDraw.Draw(img)
    pts_l, pts_r = [], []
    for t in np.linspace(0, 1, 24):
        x = x0 + lean * t ** 1.6 + curve * math.sin(math.pi * t); y = y0 - h * t
        ww = w * (1 - t) ** 0.8 / 2
        pts_l.append((x - ww, y)); pts_r.append((x + ww, y))
    d.polygon(pts_l + pts_r[::-1], fill=255)
    return np.asarray(img, float) / 255
grass_val = np.zeros((H, W)); grass_a = np.zeros((H, W))
def add(mask, val, blur, op=1.0):
    global grass_val, grass_a
    if blur > 0: mask = ndi.gaussian_filter(mask, blur)
    al = np.clip(mask * op, 0, 1)
    grass_val = grass_val * (1 - al) + val * al; grass_a = grass_a + al * (1 - grass_a)
# nearest (5-8 cm): blur ~ 31-69 px at 1200 scale -> sigma ~ 30-55 px on this sheet
for x, h, w, lean, val, bl in [(2300, 900, 230, -260, 30, 50), (1900, 760, 170, 220, 44, 44), (2420, 1100, 250, -200, 26, 55),
                               (1500, 700, 140, 300, 38, 38), (60, 760, 190, 120, 30, 48), (210, 520, 150, -90, 42, 40)]:
    add(blade_mask(x, 3300, h, w, lean, rng.uniform(-80, 80)), val, bl, 0.95)
# 15-25 cm: sigma ~ 10-18
for i in range(12):
    x = rng.choice([rng.uniform(1250, 2400), rng.uniform(0, 260)])
    add(blade_mask(x, 3260, rng.uniform(420, 900), rng.uniform(50, 80), rng.uniform(-260, 260), rng.uniform(-60, 60)),
        rng.choice([28, 36, 50, 56]), rng.uniform(10, 18), 0.9)
# at the head's distance (25-40 cm), crossing the hair and the ground line: sigma 2-5
for i in range(26):
    x = rng.uniform(0, 900); y = rng.uniform(2380, 2520) - x * 0.06
    add(blade_mask(x, y, rng.uniform(80, 230), rng.uniform(9, 16), rng.uniform(-70, 70), rng.uniform(-20, 20)),
        rng.choice([24, 30, 52, 60]), rng.uniform(2, 5), 1.0)
# at the hand's distance on the ground beyond the arm: small and sharp (focal zone)
for i in range(14):
    x = rng.uniform(1560, 2390); y = 1880 - (x - 1560) * 0.09 + rng.uniform(0, 40)
    add(blade_mask(x, y, rng.uniform(36, 95), rng.uniform(5, 9), rng.uniform(-24, 24), rng.uniform(-8, 8)),
        rng.choice([22, 28, 54]), 0.6, 1.0)
S = S * (1 - grass_a) + grass_val * grass_a
np.save(out.replace(".png", "_L.npy"), S.astype(np.float32))
np.savez_compressed(out.replace(".png", "_masks.npz"), sky=sky & ~mm_, moon=mm_, ground=green, tree=tlv > 0.5, grass=grass_a, man=man, hair=m["hair"], cloth=cloth, skin=skin, hands=m["hands"], face=m["face"] & ~m["hair"])
Image.fromarray((from_L(S) * 255).astype(np.uint8)).save(out)
print("sky top", S[40:120, 900:1500].mean().round(1), "by moon", S[int(my) - 80:int(my) - 50, int(mx) - 30:int(mx) + 30].mean().round(1),
      "moon max", S[int(my) - 15:int(my) + 15, int(mx) - 15:int(mx) + 15].max().round(1))
