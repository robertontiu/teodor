import json, math, random, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
sys.path.insert(0, '/home/claude/v13/tools')
from run import act

REF = None
def ref(blur=0):
    global REF
    if REF is None:
        REF = np.asarray(Image.open('/home/claude/v13/main_ref.png').convert('RGB'), np.float32) / 255
    if blur:
        return np.stack([gaussian_filter(REF[..., i], blur) for i in range(3)], -1)
    return REF

def canvas():
    return np.load('/home/claude/v13/main_col.npy')

def hexc(c):
    c = np.clip(c, 0, 1)
    return '#%02x%02x%02x' % tuple(int(v * 255) for v in c)

def poly_mask(pts, W=1200, H=1600):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255)
    return np.array(m) > 127

def sky_mask(th=0.80):
    r = ref(2); lum = r.mean(-1); sat = r.max(-1) - r.min(-1)
    return (lum > th) & (sat < 0.22)

def radial(mask, center, n, length, size, colorfn, seed=0, step=6, wob=3, outward=True):
    rnd = random.Random(seed); H, W = mask.shape
    ys, xs = np.nonzero(mask); out = []
    if len(xs) == 0: return out
    for _ in range(n):
        i = rnd.randrange(len(xs)); x, y = float(xs[i]), float(ys[i])
        a = math.atan2(y - center[1], x - center[0]) + rnd.gauss(0, 0.06)
        L = rnd.uniform(*length); pts = [[x, y]]; s = 0
        while s < L:
            x += math.cos(a) * step; y += math.sin(a) * step; s += step
            if not (0 <= x < W and 0 <= y < H) or not mask[int(y), int(x)]: break
            if int(s / step) % 4 == 0: pts.append([round(x + rnd.uniform(-wob, wob)), round(y + rnd.uniform(-wob, wob))])
        if len(pts) < 2: continue
        pts[0] = [round(pts[0][0]), round(pts[0][1])]
        mx, my = pts[len(pts) // 2]
        out.append({"pts": pts, "size": round(rnd.uniform(*size), 1), "color": colorfn(mx, my, rnd)})
    return out

def field(mask, anglefn, n, length, size, colorfn, seed=0, step=5, wob=2):
    """strokes following an angle field anglefn(x,y)->radians, clipped to mask."""
    rnd = random.Random(seed); H, W = mask.shape
    ys, xs = np.nonzero(mask); out = []
    if len(xs) == 0: return out
    for _ in range(n):
        i = rnd.randrange(len(xs)); x, y = float(xs[i]), float(ys[i])
        L = rnd.uniform(*length); pts = [[round(x), round(y)]]; s = 0
        while s < L:
            a = anglefn(x, y) + rnd.gauss(0, 0.04)
            x += math.cos(a) * step; y += math.sin(a) * step; s += step
            if not (0 <= x < W and 0 <= y < H) or not mask[int(y), int(x)]: break
            if int(s / step) % 3 == 0: pts.append([round(x + rnd.uniform(-wob, wob)), round(y + rnd.uniform(-wob, wob))])
        if len(pts) < 2: continue
        mx, my = pts[len(pts) // 2]
        out.append({"pts": pts, "size": round(rnd.uniform(*size), 1), "color": colorfn(mx, my, rnd)})
    return out

def refcol(blur=3, jitter=0.03, shift=(0, 0, 0), value=1.0):
    r = ref(blur)
    def f(x, y, rnd):
        c = r[int(min(y, 1599)), int(min(x, 1199))] * value + np.array(shift)
        c = c + np.array([rnd.gauss(0, jitter) for _ in range(3)])
        return hexc(c)
    return f

def pick(colors):
    def f(x, y, rnd):
        cs = [c if isinstance(c, str) else c[0] for c in colors]; ws = [1 if isinstance(c, str) else c[1] for c in colors]
        return rnd.choices(cs, ws)[0]
    return f

def S(strokes, brush="flat", edge="soft", **kw):
    d = {"type": "strokes", "brush": brush, "edge": edge, "strokes": strokes}; d.update(kw); return d
