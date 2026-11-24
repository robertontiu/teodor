import math, random, sys
sys.path.insert(0, '/home/claude/v13/tools')
import numpy as np
from paint2 import poly_mask
from hatch import hatch_mask
from shapes import jit

class Frame:
    def __init__(self, P, theta, scale=1.0):
        self.P, self.t, self.s = P, math.radians(theta), scale
    def __call__(self, u, v):
        c, s = math.cos(self.t), math.sin(self.t)
        x, y = u * self.s, v * self.s
        return (self.P[0] + x * c - y * s, self.P[1] + x * s + y * c)

def finger_poly(F, base, ang, L, w0, w1, bend=0.0):
    # centerline with 3 segments, slight bend
    pts = [base]; a = math.radians(ang); x, y = base
    segs = [0.45, 0.32, 0.23]
    for k, f in enumerate(segs):
        a += math.radians(bend) * (k > 0)
        x += math.sin(a) * L * f * -1 * 0 + math.sin(a) * L * f; y += math.cos(a) * L * f
        pts.append((x, y))
    left, right = [], []
    n = len(pts)
    for i, (px, py) in enumerate(pts):
        j, k = min(i + 1, n - 1), max(i - 1, 0)
        dx, dy = pts[j][0] - pts[k][0], pts[j][1] - pts[k][1]; d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d; w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((px + nx * w, py + ny * w)); right.append((px - nx * w, py - ny * w))
    # rounded tip
    tip = pts[-1]; dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]; d = math.hypot(dx, dy) or 1
    cap = [(tip[0] + dx / d * w1 * 0.45 + (-dy / d) * w1 * 0.25 * s, tip[1] + dy / d * w1 * 0.45 + (dx / d) * w1 * 0.25 * s) for s in (1, 0, -1)]
    poly_local = left + cap + right[::-1]
    return [F(*p) for p in poly_local], [F(*p) for p in pts], [F(*p) for p in left], [F(*p) for p in right]

def open_hand(P=(775, 1280), theta=32, scale=1.0):
    F = Frame(P, theta, scale)
    palm = [F(*p) for p in [(-48, -80), (52, -80), (76, -30), (80, 8), (66, 46), (35, 60), (0, 66), (-35, 62), (-64, 50), (-70, 6), (-62, -36)]]
    thenar = [F(*p) for p in [(30, -70), (66, -36), (76, 6), (54, 34), (30, 8), (22, -36)]]
    hollow = [F(*p) for p in [(-50, -30), (10, -40), (25, 20), (-10, 50), (-55, 40)]]
    fingers = {
        'little': finger_poly(F, (-54, 50), -24, 86, 26, 21, 8),
        'ring': finger_poly(F, (-20, 60), -10, 112, 30, 24, 5),
        'middle': finger_poly(F, (15, 63), 2, 122, 31, 25, 0),
        'index': finger_poly(F, (50, 52), 15, 108, 30, 24, -5),
        'thumb': finger_poly(F, (68, -46), 100, 112, 40, 27, -22),
    }
    return F, palm, thenar, hollow, fingers

def fill(poly, angle, colors, size, seed, spacing=None, seglen=(20, 60), jitter=6, wob=1.2):
    m = poly_mask(poly)
    rnd = random.Random(seed)
    cs = colors if isinstance(colors, list) else [colors]
    return hatch_mask(m, angle, spacing or size[0] * 0.6, size, cs, seglen=seglen, seed=seed, wobble=wob, step=3,
                      colorfn=lambda x, y, r: jit(r.choice(cs), r, jitter))

def pulse_hand(P=(405,1405),theta=-38,scale=1.0):
    F=Frame(P,theta,scale)
    palm=[F(*p) for p in [(-44,-70),(46,-70),(64,-20),(66,20),(52,50),(20,58),(-16,58),(-50,48),(-60,10),(-56,-36)]]
    fs={'little':finger_poly(F,(-42,44),-10,34,28,26,50),
        'ring':finger_poly(F,(-16,52),-4,38,30,28,50),
        'middle':finger_poly(F,(10,58),1,126,31,25,-1),
        'index':finger_poly(F,(40,52),6,118,30,24,-3),
        'thumb':finger_poly(F,(58,-34),58,84,36,26,-22)}
    return F,palm,fs
