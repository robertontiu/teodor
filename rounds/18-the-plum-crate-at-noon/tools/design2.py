# Teodor, commission 18, second state of the blocks (phase 2): the sleeper re-drawn from a posed
# blockout (plan/blockout/b11.json): seated on an upturned crate, back against the stall, head
# fallen sideways onto the front crate, hands folded in the lap, one knee up with the boot planted,
# the other leg stretched out. The same geometry gives the schema SVG and the key-line strokes.
# The figure's outline comes from the blockout's element masks; the face, hands, folds, crates,
# fruit, setts, pigeons and passer-by are drawn here by hand in canvas px (1200x1600).
import math, random, os, sys
import numpy as np
import cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cam import P, ro, rt, up, fw, F

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1200, 1600
PAPER = "#f4eee2"
C = dict(
    pave="#e3d8c2", cob="#b9ab92", stripe=os.environ.get("STRIPE", "#b5482f"), cloth="#efe2c6", board="#c9b48a",
    wood="#e3cf9f", gap="#3a4f66", crate_ind="#33475f",
    orange="#d86a3a", lemon="#e2c25e", apple="#b9473a", peach="#d9849b", pear="#8c9a55", plum="#6a4a66",
    seat="#c9a2a0", shirt="#a9c6da", shirt_mot="#f3eee4", trousers="#2b4562", boot="#262321",
    skin="#f2e2cb", stubble="#d3d8d8", hair="#1e1c1d", key="#1b1a1c", held="#e0703c", pith="#f3eee4",
    pig="#a9a8aa", pig_dk="#5f616b", pig_neck="#7d8a83", pig_leg="#d98a8e", pig_bar="#3e3f46",
    p_tr="#9a958a", p_shoe="#3b3633", p_bag="#dcb54a", leek="#6f7d4a", leek_w="#eee6d2",
)

def crs(pts, closed=False, n=10):
    P_ = [np.array(p, float) for p in pts]
    P_ = (P_[-1:] + P_ + P_[:2]) if closed else ([P_[0]] + P_ + [P_[-1]])
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed:
        out.append(P_[-2])
    return [tuple(map(float, q)) for q in out]

def rot(pts, c, deg, s=1.0):
    a = math.radians(deg); ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + s * (x * ca - y * sa), c[1] + s * (x * sa + y * ca)) for x, y in pts]

SH, LN = [], []
def shape(name, part, fill, pts, smooth=True, key=True, n=10):
    d = crs(pts, True, n) if smooth else [tuple(map(float, p)) for p in pts]
    SH.append(dict(name=name, part=part, fill=fill, pts=d, closed=True, key=key)); return d
def line(name, part, pts, smooth=True, color=None, n=10):
    d = crs(pts, False, n) if smooth else [tuple(map(float, p)) for p in pts]
    LN.append(dict(name=name, part=part, pts=d, color=color or C["key"], z=len(SH))); return d
def wpoly(name, part, fill, corners, key=True):
    return shape(name, part, fill, [P(*c) for c in corners], smooth=False, key=key)

def ground(px, py):
    """canvas px -> world point on the ground plane y=0"""
    u = (px - W / 2) / (H / 2); v = -(py - H / 2) / (H / 2)
    d = u * rt + v * up + F * fw
    t = -ro[1] / d[1]
    return ro + t * d

# ------------------------------------------------------------------ masks of the blockout
MK = np.load(f"{HERE}/blockout/b11_elements.npz")
REN = np.asarray(Image.open(f"{HERE}/blockout/b11.png").convert("RGB"), np.float32)
def mask(k): return MK[k].astype(np.uint8)
def contour(m, eps=1.6, dil=0, smooth=3.5):
    if dil: m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * dil + 1, 2 * dil + 1)))
    if smooth:
        m = (cv2.GaussianBlur(m.astype(np.float32), (0, 0), smooth) > 0.5).astype(np.uint8)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cs:
        if cv2.contourArea(c) < 150: continue
        a = cv2.approxPolyDP(c, eps, True)[:, 0, :]
        out.append([(float(x), float(y)) for x, y in a])
    return out

# ------------------------------------------------------------------ ground, stall
shape("pavement", "ground", C["pave"], [(0, 0), (W, 0), (W, H), (0, H)], smooth=False, key=False)
X0, X1 = -1.6, 4.2
wpoly("cloth", "stall", C["cloth"], [(X0, 0, 0), (X1, 0, 0), (X1, 0.9, 0), (X0, 0.9, 0)])
# the stall skirt: broad vertical stripes, vermilion and unbleached cloth (a market awning cloth)
SW = 0.13
x = X0
k = 0
while x < X1:
    if k % 2 == 0:
        wpoly(f"stripe{k}", "stall_fine", C["stripe"], [(x, 0, 0.001), (x + SW, 0, 0.001), (x + SW, 0.9, 0.001), (x, 0.9, 0.001)], key=False)
    x += SW; k += 1
if os.environ.get("TINT"):
    wpoly("skirt_tint", "stall_fine", os.environ["TINT"], [(X0, 0, 0.003), (X1, 0, 0.003), (X1, 0.9, 0.003), (X0, 0.9, 0.003)], key=False)
line("skirt_foot", "stall", [P(X0, 0, 0.002), P(X1, 0, 0.002)], smooth=False)
# the board: the stall's top, a narrow strip in front of the crates
wpoly("board", "stall", C["board"], [(X0, 0.9, 0), (X1, 0.9, 0), (X1, 0.9, -1.4), (X0, 0.9, -1.4)])

# ------------------------------------------------------------------ fruit crates on the stall, in stepped rows
random.seed(182)
ROWS = [(0.9, -0.04), (1.12, -0.46), (1.34, -0.88), (1.56, -1.30)]   # (base height, front z)
CW, CD, CH = 0.52, 0.36, 0.2
FRUIT = {  # (row, index) -> fruit; the crate behind his head (row 0, k=1) is indigo plastic holding lemons
}
order = ["orange", "pear", "peach", "apple", "lemon", "plum", "orange", "apple", "pear", "peach", "lemon"]
crates = []
for r, (yb, zf) in enumerate(ROWS):
    for k in range(-4, 9):
        x0 = -0.32 + k * (CW + 0.04) + (0.18 if r % 2 else 0)
        crates.append((r, k, x0, yb, zf))
def crate(r, k, x0, yb, zf, fi):
    x1, zb, yt = x0 + CW, zf - CD, yb + CH
    corners = [P(x0, yt, zf), P(x1, yt, zf), P(x1, yt, zb), P(x0, yt, zb)]
    if all(c[1] < -20 for c in corners) or all(c[0] > W + 20 for c in corners) or all(c[0] < -20 for c in corners): return
    plastic = (r == 0 and k == 1)
    face = C["crate_ind"] if plastic else C["wood"]
    nm = f"crate{r}_{k}"
    wpoly(nm + "_front", "crate", face, [(x0, yb, zf), (x1, yb, zf), (x1, yt, zf), (x0, yt, zf)])
    if not plastic:
        line(nm + "_slat", "crate_fine", [P(x0 + 0.01, yb + CH / 2, zf), P(x1 - 0.01, yb + CH / 2, zf)], smooth=False)
    else:   # a hand-hold slot in the plastic front
        wpoly(nm + "_hold", "crate_fine", C["gap"], [(x0 + 0.19, yt - 0.07, zf), (x1 - 0.19, yt - 0.07, zf), (x1 - 0.19, yt - 0.035, zf), (x0 + 0.19, yt - 0.035, zf)])
    wpoly(nm + "_rim", "crate", face, [(x0, yt, zf), (x1, yt, zf), (x1, yt, zb), (x0, yt, zb)])
    t = 0.025
    wpoly(nm + "_in", "crate", C["gap"], [(x0 + t, yt, zf - t), (x1 - t, yt, zf - t), (x1 - t, yt, zb + t), (x0 + t, yt, zb + t)], key=False)
    cc = np.mean([P(x0, yt, zf), P(x1, yt, zb)], axis=0)
    dh = math.hypot(cc[0] - 381, cc[1] - 440)
    if plastic: fruit = "plum"            # the dark field his head lies on
    elif dh < 420: fruit = ["pear", "pear", "lemon"][fi % 3]   # quiet near the face
    else: fruit = order[fi % len(order)]
    rr = {"lemon": 0.036, "orange": 0.038, "apple": 0.037, "peach": 0.038, "pear": 0.034, "plum": 0.028}[fruit]
    nx, nz = (6, 4) if fruit != "plum" else (8, 5)
    for j in range(nz):
        for i in range(nx):
            fx = x0 + t + (x1 - x0 - 2 * t) * (i + 0.5 + 0.22 * (j % 2)) / (nx + 0.22) + random.uniform(-0.004, 0.004)
            fz = zf - t - (CD - 2 * t) * (j + 0.5) / nz + random.uniform(-0.004, 0.004)
            c = np.array(P(fx, yt + 0.005, fz)); e = np.array(P(fx + rr, yt + 0.005, fz))
            rp = float(np.hypot(*(e - c))) * random.uniform(0.95, 1.05)
            pts = [(c[0] + rp * math.cos(a) * random.uniform(0.96, 1.04), c[1] + rp * math.sin(a) * random.uniform(0.96, 1.04)) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
            shape(f"{nm}_f{j}{i}", "fruit", C[fruit], pts, n=6)
            if fruit in ("apple", "pear", "orange"):
                line(f"{nm}_st{j}{i}", "fruit_fine", [(c[0] - 1, c[1] - rp * 0.2), (c[0] + 2, c[1] - rp * 0.55)], smooth=False)
fi = 0
for c in sorted(crates, key=lambda t: (t[4], t[0])):    # far rows first
    crate(*c, fi); fi += 1

# ------------------------------------------------------------------ the seat: an upturned plastic crate
sx0, sx1, sz0, sz1, sh = 0.06, 0.58, 0.08, 0.44, 0.34
wpoly("seat_side", "seat", C["seat"], [(sx0, 0, sz1), (sx0, 0, sz0), (sx0, sh, sz0), (sx0, sh, sz1)])
wpoly("seat_front", "seat", C["seat"], [(sx0, 0, sz1), (sx1, 0, sz1), (sx1, sh, sz1), (sx0, sh, sz1)])
wpoly("seat_top", "seat", C["seat"], [(sx0, sh, sz1), (sx1, sh, sz1), (sx1, sh, sz0), (sx0, sh, sz0)])
for i in range(1, 4):      # the crate's slatted wall, as ruled slots
    yy = sh * i / 4
    line(f"seat_slot{i}", "crate_fine", [P(sx0 + 0.05, yy, sz1), P(sx1 - 0.05, yy, sz1)], smooth=False)
    line(f"seat_slotS{i}", "crate_fine", [P(sx0, yy, sz1 - 0.04), P(sx0, yy, sz0 + 0.04)], smooth=False)
wpoly("seat_hold", "crate_fine", C["gap"], [(sx0 + 0.2, sh - 0.06, sz1), (sx1 - 0.2, sh - 0.06, sz1), (sx1 - 0.2, sh - 0.03, sz1), (sx0 + 0.2, sh - 0.03, sz1)])

# ------------------------------------------------------------------ the sleeper, from the blockout masks
drap = mask("man.drapery")
blue = (REN[..., 2] > REN[..., 1] + 4).astype(np.uint8)
trous = (drap & (1 - blue)).astype(np.uint8)
shirt = (drap & blue).astype(np.uint8)
def from_mask(name, part, fill, m, dil=3, eps=1.6, key=True):
    for i, c in enumerate(contour(m, eps=eps, dil=dil)):
        shape(f"{name}{i}", part, fill, c, smooth=False, key=key)
for i, c in enumerate(contour(trous, eps=2.0, dil=4, smooth=6)):
    shape(f"trousers{i}", "drapery", C["trousers"], c, smooth=False)
from_mask("boot", "boot", C["boot"], mask("man.feet") | mask("man.legs"), dil=3)
# the boots' soles and laces
line("lace", "boot_fine", [(1020, 1290), (1040, 1296)], smooth=False, color="#cfc6b6")
# trouser folds: the bent knee and the stretched leg, the lap's sag
line("fold_knee1", "fold", [(698, 1088), (736, 1060), (774, 1052)])
line("fold_knee2", "fold", [(712, 1126), (748, 1110)])
line("fold_hip", "fold", [(700, 900), (760, 930), (800, 980)])
line("fold_lap", "fold", [(640, 905), (690, 960), (716, 1010)])
line("fold_shin", "fold", [(960, 1130), (1000, 1200), (1020, 1250)])
line("fold_kneeR", "fold", [(890, 1000), (930, 1030), (950, 1062)])
line("cuff_out", "fold", [(1010, 1262), (1040, 1250), (1066, 1262)])

for i, c in enumerate(contour(shirt, eps=2.0, dil=4, smooth=5)):
    shape(f"shirt{i}", "drapery", C["shirt"], c, smooth=False)
MOTIF_AFTER = None
line("placket", "fold", [(512, 540), (546, 600), (590, 670), (636, 760)])
line("fold_arm1", "fold", [(420, 610), (470, 650), (520, 700)])
line("fold_arm2", "fold", [(700, 600), (690, 660), (676, 720)])
line("fold_waist", "fold", [(560, 760), (610, 790), (680, 800)])
from_mask("arm", "skin", C["skin"], mask("man.arms"), dil=3)
line("elbow_r", "hand_fine", [(500, 800), (512, 818)])
# the orange, loosely held under the fingers of his right hand, half peeled
O = (566, 900); ro_ = 36
shape("orange", "held", C["held"], [(O[0] + ro_ * math.cos(a), O[1] + ro_ * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 11)[:-1]], n=6)
shape("pith", "held", C["pith"], [(538, 902), (552, 890), (564, 900), (560, 918), (546, 922)])
line("segment", "hand_fine", [(546, 902), (556, 914)])
from_mask("hand", "hand", C["skin"], mask("man.hands"), dil=2, eps=1.2)
# fingers: his right hand, palm down over the orange, fingers loose; his left lying across the wrist
for i, f in enumerate([[(602, 852), (586, 868), (572, 884)], [(616, 858), (600, 874), (586, 894)], [(628, 866), (612, 884), (600, 900)]]):
    line(f"finger_r{i}", "hand_fine", f)
line("knuckle_r", "hand_fine", [(618, 838), (632, 848)])
for i, f in enumerate([[(736, 788), (770, 784), (806, 780)], [(742, 802), (776, 800), (810, 796)], [(744, 816), (774, 816)]]):
    line(f"finger_l{i}", "hand_fine", f)
line("thumb_l", "hand_fine", [(712, 812), (730, 826), (748, 830)])

# ------------------------------------------------------------------ neck, collar, head
# the open collar under the fallen chin: a small V of throat between two soft points
shape("throat", "skin", C["skin"], [(452, 494), (488, 468), (512, 478), (522, 512), (502, 534), (476, 520)])
shape("collar_n", "drapery", C["shirt"], [(420, 506), (452, 494), (480, 516), (502, 536), (510, 566), (478, 552), (444, 530)])
shape("collar_f", "drapery", C["shirt"], [(506, 466), (530, 462), (552, 476), (540, 506), (520, 530), (512, 500)])
# the head: phase 1's face (a typified adult face, 3/4, eyes shut, a corner of the mouth up by a hair),
# fallen onto the crate: turned -54 deg and set to the blockout's size.
HC, HR, HS = (381, 440), -54, 0.76
def head(pts): return rot(pts, HC, HR, HS)
face = [(66, -64), (80, -38), (84, -20), (78, -4), (88, 20), (88, 48), (80, 78), (66, 104), (44, 122), (20, 130),
        (-6, 124), (-36, 104), (-62, 74), (-76, 40), (-84, 0), (-86, -40), (-72, -78), (-30, -98), (24, -98)]
shape("face", "face", C["skin"], head(face))
shape("stubble", "stubble", C["stubble"], head([(-58, 80), (-36, 92), (-12, 100), (-2, 96), (16, 104), (34, 102), (54, 96),
        (70, 88), (72, 92), (62, 106), (44, 122), (20, 130), (-6, 124), (-36, 104)]), key=False)
shape("ear", "face", C["skin"], head([(-66, -12), (-90, -18), (-102, 4), (-96, 32), (-80, 48), (-66, 38)]))
line("ear_in", "face_fine", head([(-76, -4), (-90, 6), (-88, 26), (-78, 32)]))
HAIR = [(-64, -6), (-92, -30), (-106, -70), (-96, -108), (-60, -134), (-6, -144), (44, -134), (78, -108), (86, -80),
        (70, -62), (40, -70), (8, -74), (-22, -68), (-48, -54), (-60, -30)]
shape("hair", "hair", C["hair"], head(HAIR))
line("eye_n", "face_fine", head([(-40, 4), (-18, 13), (4, 6)]))
line("eye_n_crease", "face_fine", head([(-34, -8), (-16, -11), (-2, -7)]))
line("crow_n", "face_fine", head([(-46, 6), (-56, 10)]), smooth=False)
line("eye_f", "face_fine", head([(38, 2), (54, 10), (70, 4)]))
line("eye_f_crease", "face_fine", head([(44, -8), (58, -10), (66, -6)]))
line("brow_n", "face_brow", head([(-50, -24), (-26, -31), (-2, -27)]))
line("brow_f", "face_brow", head([(34, -28), (54, -32), (74, -25)]))
line("nose", "face_fine", head([(26, -6), (34, 20), (48, 46), (44, 56), (30, 58)]))
line("nostril", "face_fine", head([(14, 54), (22, 58)]), smooth=False)
line("nasolabial", "face_fine", head([(4, 62), (-4, 72), (-8, 82)]))
line("mouth", "face_fine", head([(-2, 86), (14, 89), (30, 88), (44, 83)]))
line("mouth_tick", "face_fine", head([(44, 83), (48, 79)]), smooth=False)
line("lip_low", "face_fine", head([(14, 97), (30, 96)]), smooth=False)

# ------------------------------------------------------------------ pigeons: real proportions (small head, plump body)
def pigeon(nm, c, deg, s, pecking, mirror=False):
    T = lambda pts: rot([(-x, y) if mirror else (x, y) for x, y in pts], c, deg, s)
    body = [(-56, -2), (-36, -22), (-6, -30), (26, -28), (50, -16), (60, 0), (52, 16), (26, 26), (-12, 26), (-44, 14)]
    tail = [(-50, -8), (-96, -12), (-108, -2), (-98, 10), (-50, 10)]
    if pecking:
        neck = [(40, -20), (58, -10), (72, 6), (70, 18), (56, 18), (44, 6)]
        headp = [(64, 6), (80, 8), (86, 20), (78, 28), (66, 24)]
        beak = [(84, 20), (96, 28), (82, 26)]; eye = (76, 14); patch = [(46, -8), (60, -2), (66, 10), (54, 10)]
    else:
        neck = [(34, -24), (50, -36), (58, -48), (48, -56), (34, -48), (26, -30)]
        headp = [(44, -58), (58, -64), (70, -58), (68, -48), (54, -44), (44, -48)]
        beak = [(68, -56), (82, -55), (68, -51)]; eye = (58, -56); patch = [(32, -34), (46, -40), (50, -32), (38, -26)]
    for lx in (-4, 16):
        line(nm + f"_leg{lx}", "bird_fine", T([(lx, 22), (lx + 1, 32), (lx - 6, 38), (lx + 1, 34), (lx + 9, 38)]), smooth=False, color=C["pig_leg"])
    shape(nm + "_tail", "bird", C["pig_dk"], T(tail))
    if os.environ.get("PIG2", "1") == "1":   # state 2b: a plumper, rounder body over the first one (back raised, chest deeper)
        shape(nm + "_body2", "bird", C["pig"], T([(-58, -6), (-40, -32), (-6, -42), (26, -40), (50, -26), (64, -4), (56, 20), (28, 34), (-12, 34), (-46, 20)]))
        line(nm + "_oldback", "bird_fine", T([(-36, -22), (-6, -30), (26, -28), (50, -16)]))
    shape(nm + "_body", "bird", C["pig"], T(body), key=os.environ.get("PIG2", "1") != "1")
    shape(nm + "_wingc", "bird_fine", "#8e8d93", T([(-36, -22), (-6, -30), (26, -28), (50, -16), (44, 2), (14, 12), (-26, 12), (-50, 2)]), key=False)
    shape(nm + "_neck", "bird", C["pig_dk"], T(neck))
    shape(nm + "_patch", "bird_fine", C["pig_neck"], T(patch), key=False)
    shape(nm + "_head", "bird", C["pig_dk"], T(headp))
    shape(nm + "_beak", "bird", "#c9b9a6", T(beak), smooth=False)
    line(nm + "_wing", "bird", T([(-48, -6), (-20, -18), (16, -18), (40, -8)]))
    line(nm + "_bar1", "bird_fine", T([(-22, -4), (-4, -9), (14, -6)]), color=C["pig_bar"])
    line(nm + "_bar2", "bird_fine", T([(-30, 6), (-10, 1), (8, 3)]), color=C["pig_bar"])
    line(nm + "_tailband", "bird_fine", T([(-92, -10), (-100, -1), (-93, 8)]), color=C["pig_bar"])
    e = T([eye])[0]
    shape(nm + "_eye", "bird_fine", "#c8442e", [(e[0] + 3 * math.cos(t), e[1] + 3 * math.sin(t)) for t in np.linspace(0, 6.28, 7)[:-1]], key=False)
shape("peel_ground", "held", C["held"], [(404, 1418), (426, 1404), (456, 1408), (470, 1428), (448, 1424), (424, 1426), (410, 1436)])
shape("peel_ground_in", "held", C["pith"], [(424, 1414), (450, 1414), (458, 1422), (432, 1420)], key=False)
shape("peel_ground2", "held", C["held"], [(520, 1300), (540, 1292), (556, 1304), (540, 1310)])
pigeon("pig1", (280, 1390), -10, 1.25, True)
pigeon("pig2", (190, 1530), 8, 1.2, False, mirror=True)

# ------------------------------------------------------------------ the passer-by, cut by the right edge: walking past his boot
# (feet below the frame; seen from above, the body rises up the right edge: coat, hanging arm, a bag of leeks)
shape("p_leg", "passer", C["p_tr"], [(1200, 1470), (1200, 1600), (1110, 1600), (1126, 1530), (1150, 1478)])
shape("p_coat", "passer", "#6f7d4a", [(1200, 940), (1200, 1500), (1160, 1512), (1134, 1470), (1126, 1380), (1132, 1250), (1120, 1120), (1110, 1040), (1140, 990)])
line("p_coatfold", "fold", [(1170, 1180), (1164, 1300), (1166, 1420)])
shape("p_head", "hair", C["hair"], [(1200, 790), (1200, 960), (1172, 968), (1146, 930), (1142, 870), (1164, 812)])
shape("p_arm", "passer", "#6f7d4a", [(1112, 1040), (1150, 1060), (1158, 1160), (1150, 1260), (1146, 1320), (1118, 1322), (1112, 1240), (1100, 1140)])
line("p_armfold", "fold", [(1120, 1100), (1130, 1180), (1128, 1250)])
shape("p_hand", "hand", C["skin"], [(1114, 1318), (1146, 1316), (1150, 1342), (1130, 1356), (1110, 1344)])
line("p_handle", "fold", [(1112, 1346), (1098, 1376), (1092, 1404)])
line("p_handle2", "fold", [(1144, 1348), (1150, 1380), (1150, 1404)])
for i, (a, b) in enumerate([((1082, 1408), (1020, 1350)), ((1098, 1404), (1050, 1338)), ((1114, 1402), (1088, 1334))]):
    shape(f"leek{i}", "passer", C["leek"], [a, b, (b[0] + 13, b[1] + 3), (a[0] + 13, a[1])], smooth=False)
    shape(f"leekw{i}", "passer", C["leek_w"], [a, (a[0] + 13, a[1]), (a[0] + 13 - 0.25 * (a[0] - b[0]), a[1] - 0.25 * (a[1] - b[1])), (a[0] - 0.25 * (a[0] - b[0]), a[1] - 0.25 * (a[1] - b[1]))], smooth=False)
shape("p_bag", "passer", C["p_bag"], [(1070, 1404), (1160, 1400), (1172, 1500), (1080, 1512)], smooth=False)
for s_ in SH + LN:      # hand, handles, leeks and bag hang 40 px lower, clear of his boot
    if s_["name"].startswith(("p_hand", "leek", "p_bag")):
        s_["pts"] = [(x, y + 40) for x, y in s_["pts"]]
    if s_["name"] == "p_arm":
        s_["pts"] = [(x, y + 40 * max(0, (y - 1150) / 170)) for x, y in s_["pts"]]

# ------------------------------------------------------------------ the setts: segmental arcs on the street (no texture gradient fake: real perspective)
COB = []
def arcs():
    rng = random.Random(7)
    row = 0.11
    for j in range(0, 40):
        z = 0.03 + j * row
        COB.append([P(-3, 0, z), P(5, 0, z)])
        x = -3 + rng.uniform(0, 0.2)
        while x < 5:
            COB.append([P(x, 0, z), P(x, 0, z + row)])
            x += rng.uniform(0.13, 0.24)
arcs()

def path_d(pts, closed):
    s = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return s + ("Z" if closed else "")

KEYW = dict(ground=0, stall=2.4, stall_fine=1.2, crate=2.0, crate_fine=1.2, fruit=1.4, fruit_fine=1.2, seat=2.2, drapery=3.0,
            fold=2.2, boot=2.6, boot_fine=1.6, skin=1.8, hand=1.4, hand_fine=1.1, held=1.4, face=1.6, face_fine=1.1,
            face_brow=2.6, hair=1.6, stubble=0, bird=1.4, bird_fine=1.2, passer=2.2)

def svg(with_key=True, cobbles=True):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
    byz = {}
    for l in LN: byz.setdefault(l["z"], []).append(l)
    for i, s in enumerate(SH):
        for l in byz.get(i, []):
            if with_key: o.append(f'<path d="{path_d(l["pts"], False)}" fill="none" stroke="{l["color"]}" stroke-width="{KEYW[l["part"]]}" stroke-linecap="round"/>')
        stroke = f' stroke="{C["key"]}" stroke-width="{KEYW[s["part"]]}" stroke-linejoin="round"' if (with_key and s["key"]) else ""
        o.append(f'<path d="{path_d(s["pts"], True)}" fill="{s["fill"]}"{stroke}/>')
        if s["name"] == "pavement" and with_key and cobbles:
            for c in COB:
                if len(c) > 1: o.append(f'<path d="{path_d(c, False)}" stroke="{C["cob"]}" stroke-width="1.3" fill="none"/>')
    for l in byz.get(len(SH), []):
        if with_key: o.append(f'<path d="{path_d(l["pts"], False)}" fill="none" stroke="{l["color"]}" stroke-width="{KEYW[l["part"]]}" stroke-linecap="round"/>')
    o.append("</svg>")
    return "\n".join(o)

if __name__ == "__main__":
    import subprocess
    name = sys.argv[1] if len(sys.argv) > 1 else "schema_p2"
    open(f"{HERE}/{name}.svg", "w").write(svg())
    open(f"{HERE}/{name}_blocks.svg", "w").write(svg(cobbles=False))
    subprocess.run(["rsvg-convert", "-w", "600", "-h", "800", f"{HERE}/{name}.svg", "-o", f"{HERE}/{name}_preview.png"], check=True)
    print(len(SH), "shapes", len(LN), "lines")
