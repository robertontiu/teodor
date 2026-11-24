"""Phase 3 helpers."""
import sys, json, math, numpy as np
D = "/home/claude/v14f"; sys.path.insert(0, D)
from ep2 import *
import ep2, tiles as T
from skimage import measure
from scipy.ndimage import gaussian_filter, binary_dilation, binary_erosion
X_, Y_, D_, U_, V_, XF_ = T.fields(P)
IU, IV = np.floor(U_).astype(int), np.floor(V_).astype(int)
CHK = (IU + IV) % 2; NEAR = np.exp(-(D_ / 0.33) ** 2)
GY, GX = np.gradient(gaussian_filter(np.sign(D_) * np.abs(D_) ** 0.9, 3))
def tile_fill(zone, colour, felt=(0.25, 0.05, 0.8, 0.97), minpix=60, edge="hard", load=1.5, impasto=0.35, shrink=0.75):
    """colour(cx, cy, k, nr, cur_median, mask) -> rgb or None"""
    lab = np.where(zone, (IU + 50) * 1000 + (IV + 50), -1)
    cur = np.load(f"{D}/main_col.npy").astype(np.float32); its = []
    for c in T.cells(lab, minpix=minpix, gu=(GX, GY)):
        m = lab == c["id"]
        cs = measure.find_contours(np.pad(m, 1).astype(float), 0.5)
        ct = max(cs, key=len) - 1; step = max(1, len(ct) // 60)
        pts = [[round(float(q[1]), 1), round(float(q[0]), 1)] for q in ct[::step]]
        if len(pts) < 4: continue
        cx, cy = c["c"]; iy, ix = int(cy), int(cx)
        col = colour(cx, cy, int(CHK[iy, ix]), float(NEAR[iy, ix]), np.median(cur[m], 0), m)
        if col is None: continue
        ax, L, S = c["ax"], c["L"], c["S"]; n = np.array([-ax[1], ax[0]])
        size = float(min(46, max(6, S * shrink))); k_ = int(np.ceil(S / (size * 0.7)))
        st = []
        for j in range(k_):
            off = (j - (k_ - 1) / 2) * size * 0.7; p0 = np.array([cx, cy]) + n * off
            st.append({"pts": [(p0 - ax * (L / 2 + size)).round(1).tolist(), p0.round(1).tolist(), (p0 + ax * (L / 2 + size)).round(1).tolist()], "size": round(size, 1), "color": T.tohex(col)})
        its.append({"type": "strokes", "brush": "flat", "strokes": st, "region": {"type": "poly", "pts": pts}, "clip": True, "edge": edge, "load": load, "pressure": 1.0, "impasto": impasto})
    if its: act(felt, its)
    return len(its)
RNG = np.random.default_rng(5)
def fc(x, y, k, nr, jit=0.015): return np.clip(floor_colour(x, y, k, nr, RNG, jit), 0, 1)
def crop(x, y, w, h, name): look("crop", x, y, w, h, to=name)
def tile_glaze(zone, fn, felt=(0.25, 0.05, 0.8, 0.9), minpix=60, feather=3):
    """fn(cx, cy, k, nr) -> (rgb, opacity) or None"""
    lab = np.where(zone, (IU + 50) * 1000 + (IV + 50), -1); its = []
    for c in T.cells(lab, minpix=minpix, gu=(GX, GY)):
        m = lab == c["id"]
        ct = max(measure.find_contours(np.pad(m, 1).astype(float), 0.5), key=len) - 1; step = max(1, len(ct) // 60)
        pts = [[round(float(q[1]), 1), round(float(q[0]), 1)] for q in ct[::step]]
        if len(pts) < 4: continue
        cx, cy = c["c"]; r = fn(cx, cy, int(CHK[int(cy), int(cx)]), float(NEAR[int(cy), int(cx)]))
        if r is None: continue
        its.append({"type": "glaze", "color": T.tohex(r[0]), "opacity": round(float(r[1]), 3), "region": {"type": "poly", "pts": pts}, "feather": feather})
    if its: act(felt, its)
    return len(its)

from ep2 import _rot
SK, SL, SD = "#f7a48c", "#ffd9c2", "#de6f8c"
def hand2(wrist, u, sc, fingers, thumb, curl=0.0):
    u = np.array(u, float); u /= np.linalg.norm(u); n = np.array([-u[1], u[0]]); w = np.array(wrist, float)
    body, light, line = [], [], []
    palm = w + u * 26 * sc
    R = lambda q: np.asarray(q).round(1).tolist()
    body.append({"pts":[R(w - u*4*sc), R(palm + u*8*sc)], "size":44*sc, "color":SK})
    body.append({"pts":[R(w + u*6*sc - n*10*sc), R(palm - n*8*sc)], "size":20*sc, "color":SD})      # heel/shade side
    light.append({"pts":[R(w + u*10*sc + n*6*sc), R(palm + u*4*sc + n*7*sc)], "size":18*sc, "color":SL})
    for i, (ang, Lf) in enumerate(fingers):
        d = _rot(u, ang); base = palm + u*12*sc + n*((i-1.5)*11*sc)
        k1 = base + d*Lf*0.42*sc; d2 = _rot(d, curl*0.6); k2 = k1 + d2*Lf*0.32*sc; d3 = _rot(d2, curl*0.6); tip = k2 + d3*Lf*0.26*sc
        body += [{"pts":[R(base - d*4*sc), R(k1)], "size":11.5*sc, "color":SK}, {"pts":[R(k1), R(k2)], "size":10*sc, "color":SK}, {"pts":[R(k2), R(tip)], "size":7.6*sc, "color":SK}]
        nn = np.array([-d[1], d[0]]); nn = nn if nn@LIT>0 else -nn
        light.append({"pts":[R(base + nn*2*sc), R(k1 + nn*2*sc), R(k2 + nn*1.5*sc)], "size":4.2*sc, "color":SL})
        line.append({"pts":[R(base - nn*5.6*sc), R(k1 - nn*5.0*sc), R(k2 - nn*4.2*sc)], "size":1.8, "color":SD})
        line.append({"pts":[R(tip - d3*3*sc + nn*1.5*sc), R(tip - d3*0.5*sc + nn*1*sc)], "size":2.2, "color":"#fff0e6"})
    d = _rot(u, thumb[0]); sg = math.copysign(1, thumb[0]); base = w + u*8*sc + n*sg*17*sc
    m = base + d*thumb[1]*0.55*sc; t = m + _rot(d, -thumb[0]*0.4)*thumb[1]*0.45*sc
    body += [{"pts":[R(base - d*8*sc), R(m)], "size":15*sc, "color":SK}, {"pts":[R(m), R(t)], "size":10*sc, "color":SK}]
    line.append({"pts":[R(base), R(m), R(t)], "size":2.6, "color":SL})
    return body, light, line
hands = [((265.3,1009.9), (-0.95,0.31), 1.3, [(-30,40),(-11,47),(7,45),(26,37)], (68,36), 10, (215,1022,125)),
         ((566.1,1505.8), (-0.66,0.75), 0.95, [(-24,38),(-8,44),(8,42),(24,34)], (-62,32), 30, (545,1540,95))]

def paint_hands(felt=(0.3,0.05,0.85,0.97)):
    its=[]
    for w,u,sc,f,th,curl,_ in hands:
        b,l,ln = hand2(w,u,sc,f,th,curl)
        uu = np.array(u)/np.linalg.norm(u); nn = np.array([-uu[1],uu[0]]); ww = np.array(w)
        cs = [{"pts":[(ww+uu*1*sc+nn*22*sc).round(1).tolist(), (ww+uu*3*sc).round(1).tolist(), (ww+uu*1*sc-nn*22*sc).round(1).tolist()], "size":5*sc, "color":"#d06a8e"}]
        n = nn if nn@LIT>0 else -nn
        R=lambda q: np.asarray(q).round(1).tolist()
        sl=[{"pts":[R(ww-uu*60*sc+n*o*sc), R(ww-uu*30*sc+n*o*sc), R(ww-uu*5*sc+n*o*sc)],"size":15*sc,"color":c} for o,c in ((-19,"#cfc6f2"),(-8,"#f3effb"),(3,"#fffdf4"),(14,"#ffffff"),(21,"#ffffff"))]
        cuff=[{"pts":[R(ww-uu*3*sc-n*26*sc), R(ww-uu*1*sc), R(ww-uu*3*sc+n*26*sc)],"size":3,"color":"#8a80d8"}]
        its += [{"type":"strokes","brush":"round","strokes":b,"edge":"hard","load":1.7,"impasto":0.4,"pressure":1.0},
                {"type":"strokes","brush":"round","strokes":cs+l,"edge":"soft","load":1.3,"impasto":0.5},
                {"type":"strokes","brush":"liner","strokes":ln,"load":1.2},
                {"type":"strokes","brush":"flat","strokes":sl,"edge":"hard","load":1.7,"impasto":0.6,"pressure":1.0},
                {"type":"strokes","brush":"liner","strokes":cuff,"load":1.2}]
    act(felt, its)
from PIL import Image as _I, ImageDraw as _ID
def hair_mask():
    im = _I.new("L",(1200,1600),0); _ID.Draw(im).polygon([tuple(q) for q in json.load(open(f"{D}/hair_poly.json"))], fill=255); return np.array(im)>0
LAB = (IU + 50) * 1000 + (IV + 50)
def whole_tiles(seed_zone):
    return np.isin(LAB, np.unique(LAB[seed_zone]))
