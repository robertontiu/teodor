# Teodor, commission 18: the line design (schema) of the market sleeper, high oblique view.
# Every shape is a list of control points (Catmull-Rom smoothed, or straight). The same geometry
# gives the schema SVG (flat colour areas + key lines) and, later, the key-line stroke lists.
# Ground axes of the oblique parallel view: u along the stall front (up-right), v into the street
# (down-right, the dominant slant); verticals stay vertical. Units: canvas px (1200x1600).
import math, json, random, os
import numpy as np

U = np.array([0.8, -0.6]); V = np.array([0.36, 0.933]); UP = np.array([0.0, -1.0])
W, H = 1200, 1600

PAPER = "#f4eee2"
C = dict(
    pave="#e3d8c2", cob="#b8ab93", cloth="#2d4864", hem="#f1ebdf", wood="#e3cf9f", wood_ln="#8a7550",
    gap="#3a4f66", orange="#d86a3a", lemon="#dcb54a", apple="#c8442e", peach="#d9849b", pear="#8c9a55",
    seat="#c9a2a0", shirt="#9fbfd6", shirt_mot="#f3eee4", apron="#1f4e79", trousers="#6b7448",
    boot="#262321", stubble="#d3d8d8", skin="#f2e2cb", hair="#1e1c1d", key="#1b1a1c", held="#d86a3a", pith="#f3eee4",
    pig="#a7a6a6", pig_dk="#6d6f78", pig_neck="#6f8a6e", pig_leg="#d98a8e",
    p1="#9a958a", p1b="#c9a2a0", p2="#8a8f99", shoe="#3b3633",
)

def crs(pts, closed=False, n=10):
    """Catmull-Rom through control points -> dense polyline."""
    P = [np.array(p, float) for p in pts]
    if closed:
        P = P[-1:] + P + P[:2]
    else:
        P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed:
        out.append(P[-2])
    return [tuple(map(float, q)) for q in out]

def rot(pts, c, deg, s=1.0):
    a = math.radians(deg); ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + s * (x * ca - y * sa), c[1] + s * (x * sa + y * ca)) for x, y in pts]

SH = []    # shapes: dict(name, part, fill, pts(dense), closed, key(bool), width)
LN = []    # open key lines: dict(name, part, pts, color)

def shape(name, part, fill, pts, smooth=True, key=True, n=10):
    d = crs(pts, True, n) if smooth else [tuple(map(float, p)) for p in pts]
    SH.append(dict(name=name, part=part, fill=fill, pts=d, closed=True, key=key))
    return d

def line(name, part, pts, smooth=True, color=None, n=10):
    d = crs(pts, False, n) if smooth else [tuple(map(float, p)) for p in pts]
    LN.append(dict(name=name, part=part, pts=d, color=color or C["key"], z=len(SH)))
    return d

# ---------------------------------------------------------------- ground and stall
def yG(x): return 800 - (x - 440) * 0.75          # stall front, ground line
def yT(x): return yG(x) - 400                      # top edge of the stall cloth

shape("pavement", "ground", C["pave"], [(0, 0), (W, 0), (W, H), (0, H)], smooth=False, key=False)
shape("cloth", "stall", C["cloth"], [(0, yT(0)), ((yT(0)) / 0.75, 0), (W, 0), (W, yG(W)), (0, yG(0))], smooth=False)
# hem band of the cloth: two paper-reserved stripes parallel to the ground line
for off, w in ((-34, 12), (-62, 6)):
    a, b = off, off - w
    shape(f"hem{off}", "stall", C["hem"], [(0, yG(0) + a), (W, yG(W) + a), (W, yG(W) + b), (0, yG(0) + b)], smooth=False, key=False)

# crate rows on the stepped stand above the cloth's top edge
random.seed(18)
FRUITS = ["orange", "lemon", "peach", "apple", "pear", "lemon", "orange", "peach", "pear", "apple"]
crates = []
CW, CD, STEP = 214, 150, 44
R = -V * CD + UP * STEP              # from one row's front edge to the next row's
fk = 0
for r in range(0, 7):
    for k in range(-3, 7):
        p = np.array([0.0, yT(0)]) + r * R + U * (k * (CW + 10) + (r * 61) % 120 - 20)
        q = p + U * CW
        top = [p, q, q - V * CD, p - V * CD]
        if max(t[1] for t in top) < -10 or min(t[0] for t in top) > W + 10 or max(t[0] for t in top) < -10:
            continue
        if min(yT(t[0]) - t[1] for t in top) < -5 and r == 0:
            pass
        crates.append((r, k, top, FRUITS[fk % len(FRUITS)])); fk += 1

def crate(r, k, top, fruit):
    p, q, qb, pb = [np.array(t) for t in top]
    nm = f"crate{r}_{k}"
    # front face (visible between this row and the row in front of it): STEP tall, plus the rim
    if r > 0:
        shape(nm + "_front", "crate", C["wood"], [p, q, q - UP * STEP, p - UP * STEP], smooth=False)
        line(nm + "_slat", "crate_fine", [p - UP * STEP * 0.5, q - UP * STEP * 0.5], smooth=False)
    else:
        shape(nm + "_front", "crate", C["wood"], [p, q, q - UP * 26, p - UP * 26], smooth=False)
    # the rim: the top as wood, the opening inset, the fruit in it
    shape(nm + "_rim", "crate", C["wood"], [p, q, qb, pb], smooth=False)
    ins = 12
    a = p + U * ins - V * ins; b = q - U * ins - V * ins; c = qb - U * ins + V * ins; d = pb + U * ins + V * ins
    shape(nm + "_in", "crate", C["gap"], [a, b, c, d], smooth=False)
    # fruit: overlapping rounds in rows along u, three rows back
    col = C[fruit]
    rr = {"lemon": 17, "orange": 19, "apple": 18, "peach": 19, "pear": 17}[fruit]
    nrow = 3; ncol = 5
    for j in range(nrow):
        for i in range(ncol):
            f = a + (b - a) * ((i + 0.5 + 0.25 * (j % 2)) / (ncol + 0.25)) + (d - a) * ((j + 0.5) / nrow)
            f = f + np.array([random.uniform(-2.5, 2.5), random.uniform(-2.5, 2.5)])
            pts = [(f[0] + rr * math.cos(t) * random.uniform(0.96, 1.04), f[1] + rr * math.sin(t) * random.uniform(0.96, 1.04))
                   for t in np.linspace(0, 2 * math.pi, 9)[:-1]]
            shape(f"{nm}_f{j}{i}", "fruit", col, pts, n=6)
            if fruit in ("apple", "pear", "orange"):
                line(f"{nm}_st{j}{i}", "fruit_fine", [f + [-2, -rr * 0.25], f + [2, -rr * 0.55]], smooth=False)

for c in sorted(crates, key=lambda t: -t[0]):
    crate(*c)

# --------------------------------------------------------------- the seat crate (upturned plastic crate)
sc = np.array([600.0, 905.0])        # centre of its top
sa, sb = 112, 70
st = [sc - U * sa - V * sb, sc + U * sa - V * sb, sc + U * sa + V * sb, sc - U * sa + V * sb]
seat_h = 150
shape("seat_front", "seat", C["seat"], [st[3], st[2], st[2] - UP * seat_h, st[3] - UP * seat_h], smooth=False)
shape("seat_side", "seat", C["seat"], [st[2], st[1], st[1] - UP * seat_h, st[2] - UP * seat_h], smooth=False)
for i in range(1, 4):
    a = st[3] - UP * seat_h * i / 4; b = st[2] - UP * seat_h * i / 4
    line(f"seat_slot{i}", "crate_fine", [a + U * 18, b - U * 18], smooth=False)
shape("seat_top", "seat", C["seat"], st, smooth=False)

# ---------------------------------------------------------------- the sleeper
# legs: two olive trouser legs from the seat to crossed ankles; the near (left) leg crosses over at the ankle
shape("leg_far", "drapery", C["trousers"], [(640, 905), (720, 940), (800, 1040), (868, 1180), (930, 1330), (955, 1402),
                                            (912, 1424), (880, 1350), (812, 1215), (740, 1100), (660, 1030), (600, 990)])
shape("boot_far", "boot", C["boot"], [(912, 1414), (958, 1396), (990, 1430), (1016, 1478), (1004, 1506), (968, 1498), (930, 1462)])
shape("leg_near", "drapery", C["trousers"], [(540, 960), (630, 985), (720, 1060), (790, 1170), (850, 1300), (905, 1415),
                                             (862, 1445), (812, 1340), (745, 1225), (670, 1130), (585, 1065), (520, 1030)])
shape("boot_near", "boot", C["boot"], [(860, 1428), (905, 1405), (950, 1440), (1000, 1470), (1030, 1505), (1012, 1534),
                                       (962, 1530), (900, 1498), (866, 1470)])
line("leg_near_knee", "fold", [(700, 1075), (735, 1110), (748, 1150)])
line("leg_near_shin", "fold", [(790, 1250), (822, 1320), (846, 1380)])
line("leg_far_knee", "fold", [(780, 1020), (810, 1062)])
line("boot_lace_n", "boot_fine", [(930, 1440), (960, 1455)], smooth=False, color="#f4eee2")
line("sole_n", "boot_fine", [(1012, 1534), (962, 1530), (900, 1498)], color="#5a524b")

# torso: the shirt, leaning back against the cloth
shirt = shape("shirt", "drapery", C["shirt"], [(352, 772), (410, 722), (448, 696), (540, 710), (606, 682), (662, 650),
                                               (705, 690), (722, 770), (716, 860), (690, 945), (640, 985), (560, 1005),
                                               (490, 990), (440, 930), (400, 860)])
# shirt motif: small paper-reserved crosses at one size, flat across the folds (one per lattice cell)
MOT = []
for i in range(-14, 16):
    for j in range(-14, 16):
        m = np.array([540.0, 850.0]) + U * (i * 30) + V * (j * 30) + (np.array([8, 0]) if j % 2 else 0)
        MOT.append(m)

# arms: his right (viewer left) hangs, then the forearm crosses the belly; his left comes over to meet it
shape("arm_r_upper", "drapery", C["shirt"], [(352, 772), (405, 760), (440, 820), (462, 880), (470, 922), (424, 936),
                                             (390, 884), (360, 825)])
shape("arm_l_upper", "drapery", C["shirt"], [(662, 650), (706, 682), (730, 760), (740, 830), (702, 846), (682, 790),
                                             (660, 720)])
MOTIF_AFTER = "arm_l_upper"

# apron: indigo panel over chest, belly and lap, with its ties
apron = shape("apron", "drapery", C["apron"], [(492, 775), (560, 750), (622, 728), (650, 790), (672, 880), (700, 980),
                                               (735, 1065), (690, 1100), (620, 1085), (570, 1040), (528, 960), (505, 870)])
line("apron_strap", "fold", [(492, 775), (478, 740), (470, 712)])
line("apron_strap2", "fold", [(622, 728), (628, 700), (636, 668)])
line("apron_sag", "fold", [(600, 975), (640, 1015), (690, 1040)])
line("apron_sag2", "fold", [(556, 930), (596, 960)])

# forearms, bare (sleeves rolled to the elbow), meeting at the orange
shape("forearm_r", "skin", C["skin"], [(426, 912), (470, 902), (512, 890), (552, 872), (566, 904), (522, 924),
                                       (474, 942), (432, 946)])
shape("forearm_l", "skin", C["skin"], [(704, 822), (738, 830), (718, 866), (690, 886), (662, 902), (650, 874), (676, 852)])
shape("cuff_r", "drapery", C["shirt"], [(412, 906), (444, 898), (452, 942), (420, 950)], smooth=False)
shape("cuff_l", "drapery", C["shirt"], [(694, 814), (742, 820), (738, 846), (702, 850)], smooth=False)

# the half-peeled orange, cupped loosely in both hands on the apron
O = np.array([602.0, 868.0]); ro = 32
shape("orange", "held", C["held"], [(O[0] + ro * math.cos(t), O[1] + ro * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 11)[:-1]], n=6)
shape("pith", "held", C["pith"], [(578, 852), (590, 840), (608, 836), (622, 842), (610, 852), (596, 860), (584, 862)])
line("segment1", "hand_fine", [(596, 846), (604, 858)])
shape("peel", "held", C["held"], [(612, 896), (624, 902), (626, 924), (616, 950), (600, 968), (590, 962), (604, 940), (608, 918)])
shape("peel_in", "held", C["pith"], [(616, 912), (622, 920), (616, 944), (606, 956), (610, 934)])
# his right hand (viewer left): a blunt working hand under the orange, thumb up its left side
shape("hand_r", "hand", C["skin"], [(540, 872), (560, 862), (576, 858), (584, 846), (594, 846), (594, 862), (588, 880),
                                    (600, 892), (618, 896), (634, 892), (640, 902), (626, 914), (602, 920), (574, 920),
                                    (552, 912), (538, 894)])
line("hand_r_f1", "hand_fine", [(596, 902), (608, 914)])
line("hand_r_f2", "hand_fine", [(612, 898), (624, 909)])
line("hand_r_thumb", "hand_fine", [(570, 868), (582, 872), (588, 880)])
# his left hand (viewer right): lying over the orange's right side, fingers loose
shape("hand_l", "hand", C["skin"], [(666, 858), (676, 876), (664, 898), (644, 906), (628, 900), (620, 884), (622, 866),
                                    (632, 850), (646, 846), (658, 850)])
line("hand_l_f1", "hand_fine", [(632, 862), (640, 884)])
line("hand_l_f2", "hand_fine", [(645, 858), (652, 880)])
line("hand_l_knuckle", "hand_fine", [(656, 852), (664, 864)])

# neck and throat: long and stretched, because the head lies back against the cloth
shape("neck", "skin", C["skin"], [(452, 704), (452, 646), (476, 636), (530, 652), (578, 636), (598, 642), (606, 694),
                                  (540, 712)])
line("throat1", "face_fine", [(548, 662), (556, 680), (554, 698)])
shape("collar_l", "drapery", C["shirt"], [(444, 694), (470, 700), (540, 712), (512, 738), (470, 736)])
shape("collar_r", "drapery", C["shirt"], [(540, 712), (606, 684), (622, 700), (604, 730), (566, 728)])

# the head, in its own coordinates (x right, y down, centre 0,0; crown -140, chin +130), turned three-quarter
# toward his left (viewer right) and tipped back so the crown points up-left; it rests against the cloth.
HC = (488, 540); HR = -32
def head(pts):
    return rot(pts, HC, HR)
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
# closed eyes: relaxed downward-sagging arcs (the near one longer), a short crease above, a crow's-foot tick
line("eye_n", "face_fine", head([(-40, 4), (-18, 13), (4, 6)]))
line("eye_n_crease", "face_fine", head([(-34, -8), (-16, -11), (-2, -7)]))
line("crow_n", "face_fine", head([(-46, 6), (-56, 10)]), smooth=False)
line("eye_f", "face_fine", head([(38, 2), (54, 10), (70, 4)]))
line("eye_f_crease", "face_fine", head([(44, -8), (58, -10), (66, -6)]))
# brows: short thick commoner strokes, smooth and level
line("brow_n", "face_brow", head([(-50, -24), (-26, -31), (-2, -27)]))
line("brow_f", "face_brow", head([(34, -28), (54, -32), (74, -25)]))
# nose: bridge down the turned side, hooked tip, nostril; one nose-to-mouth line for his age
line("nose", "face_fine", head([(26, -6), (34, 20), (48, 46), (44, 56), (30, 58)]))
line("nostril", "face_fine", head([(14, 54), (22, 58)]), smooth=False)
line("nasolabial", "face_fine", head([(4, 62), (-4, 72), (-8, 82)]))
# mouth: slack, lips barely parted, the corner ticking up by a hair; cheeks do not rise
line("mouth", "face_fine", head([(-2, 86), (14, 89), (30, 88), (44, 83)]))
line("mouth_tick", "face_fine", head([(44, 83), (48, 79)]), smooth=False)
line("lip_low", "face_fine", head([(14, 97), (30, 96)]), smooth=False)

# ---------------------------------------------------------------- pigeons: two, low-left, unbothered
def pigeon(nm, c, deg, s, pecking):
    T = lambda pts: rot(pts, c, deg, s)
    body = [(-60, -4), (-30, -26), (10, -30), (44, -20), (62, -6), (56, 12), (30, 24), (-10, 26), (-46, 16)]
    tail = [(-58, -8), (-100, -14), (-112, -2), (-100, 12), (-56, 10)]
    if pecking:
        neck = [(40, -18), (64, -8), (84, 8), (90, 22), (76, 28), (60, 14), (44, 8)]
        headp = [(80, 12), (96, 10), (104, 22), (98, 34), (84, 34), (76, 24)]
        beak = [(102, 26), (112, 36), (100, 34)]; eye = (92, 20)
    else:
        neck = [(36, -22), (56, -34), (64, -46), (52, -54), (36, -46), (26, -30)]
        headp = [(48, -58), (64, -64), (78, -56), (76, -44), (60, -42), (48, -48)]
        beak = [(76, -54), (90, -52), (76, -48)]; eye = (64, -54)
    for lx in (-6, 14):
        leg = T([(lx, 20), (lx + 2, 38), (lx - 6, 46), (lx + 2, 40), (lx + 10, 46)])
        line(nm + f"_leg{lx}", "bird_fine", leg, smooth=False, color=C["pig_leg"])
    shape(nm + "_tail", "bird", C["pig_dk"], T(tail))
    shape(nm + "_body", "bird", C["pig"], T(body))
    shape(nm + "_wing", "bird", C["pig"], T([(-44, -10), (-10, -22), (30, -16), (40, -2), (10, 10), (-30, 10)]))
    line(nm + "_bar1", "bird_fine", T([(-20, -8), (0, -12), (18, -8)]), color=C["pig_dk"])
    line(nm + "_bar2", "bird_fine", T([(-28, 2), (-6, -2), (12, 2)]), color=C["pig_dk"])
    shape(nm + "_neck", "bird", C["pig_neck"], T(neck))
    shape(nm + "_head", "bird", C["pig_dk"], T(headp))
    shape(nm + "_beak", "bird", "#c9b9a6", T(beak), smooth=False)
    e = T([eye])[0]
    shape(nm + "_eye", "bird_fine", C["key"], [(e[0] + 2.5 * math.cos(t), e[1] + 2.5 * math.sin(t)) for t in np.linspace(0, 6.28, 7)[:-1]], key=False)

shape("peel_ground", "held", C["held"], [(392, 1318), (420, 1300), (452, 1306), (462, 1326), (440, 1322), (414, 1322), (398, 1334)])
pigeon("pig1", (236, 1318), -8, 1.3, True)
pigeon("pig2", (330, 1490), 14, 1.25, False)

# ---------------------------------------------------------------- passers-by, cut hard by the frame
# 1, top right: a coat hem cut by the top edge, two trouser legs mid-stride, a tote bag swinging
shape("p1_bag", "passer", C["p1b"], [(978, 128), (1036, 118), (1048, 236), (1038, 262), (992, 266), (970, 200)], smooth=False)
line("p1_handle", "fold", [(990, 128), (1004, 60), (1026, 120)])
shape("p1_leg_back", "passer", C["p2"], [(1066, 160), (1112, 160), (1110, 300), (1100, 400), (1066, 404), (1070, 290)])
shape("p1_shoe_b", "passer", C["shoe"], [(1062, 396), (1102, 392), (1108, 420), (1078, 446), (1052, 444), (1050, 420)])
shape("p1_leg_front", "passer", C["p2"], [(1132, 160), (1188, 160), (1200, 280), (1200, 410), (1164, 420), (1152, 300)])
shape("p1_shoe_f", "passer", C["shoe"], [(1160, 410), (1200, 404), (1200, 460), (1164, 470), (1150, 446)], smooth=False)
shape("p1_coat", "passer", C["p1"], [(1040, 0), (1200, 0), (1200, 168), (1160, 182), (1118, 170), (1076, 186), (1048, 170), (1036, 90)])
line("p1_fold", "fold", [(1110, 20), (1104, 100), (1096, 176)])
# 2, lower right: one shoe planted by his boots, the other lifted heel-first, stepping round them
shape("p2_leg", "passer", C["p2"], [(1200, 1130), (1200, 1310), (1176, 1360), (1130, 1372), (1124, 1330), (1146, 1230), (1166, 1140)])
shape("p2_shoe", "passer", C["shoe"], [(1122, 1340), (1178, 1350), (1170, 1384), (1120, 1414), (1078, 1418), (1070, 1396), (1092, 1370)])
line("p2_sole", "boot_fine", [(1078, 1418), (1120, 1414), (1170, 1384)], color="#9a958a")
line("p2_fold", "fold", [(1176, 1180), (1164, 1260), (1150, 1330)])
shape("p2_leg2", "passer", C["p2"], [(1118, 1600), (1140, 1520), (1200, 1470), (1200, 1600)])
shape("p2_shoe2", "passer", C["shoe"], [(1072, 1600), (1080, 1562), (1128, 1546), (1150, 1600)], smooth=False)

# ---------------------------------------------------------------- the pavement's setts (drawn right after the pavement)
COB = []
o0 = np.array([0.0, yG(0) + 20])
for j in range(-40, 40):
    a = o0 + V * (58 * j)
    p0, p1 = a - U * 2600, a + U * 2600
    COB.append([tuple(p0), tuple(p1)])
    for i in range(-30, 30):
        q = a + U * (104 * i + 52 * (j % 2))
        if -20 < q[0] < W + 20 and -20 < q[1] < H + 80:
            COB.append([tuple(q), tuple(q + V * 58)])

# ---------------------------------------------------------------- output
def path_d(pts, closed):
    s = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return s + ("Z" if closed else "")

KEYW = dict(ground=0, stall=2.6, crate=2.0, crate_fine=1.2, fruit=1.4, fruit_fine=1.2, seat=2.0, drapery=3.0, fold=2.2,
            boot=2.6, boot_fine=1.6, skin=1.8, hand=1.4, hand_fine=1.1, held=1.4, face=1.6, face_fine=1.1, face_brow=2.6,
            hair=1.6, stubble=0, bird=1.4, bird_fine=1.2, passer=2.2)

def svg(with_key=True, motifs=True, cobbles=True):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
    sid = {s["name"]: i for i, s in enumerate(SH)}
    shirt_i = sid["shirt"]
    o.append(f'<defs><clipPath id="sc"><path d="{path_d(SH[sid["shirt"]]["pts"], True)}"/>'
             f'<path d="{path_d(SH[sid["arm_r_upper"]]["pts"], True)}"/><path d="{path_d(SH[sid["arm_l_upper"]]["pts"], True)}"/></clipPath></defs>')
    lines_by_z = {}
    for l in LN:
        lines_by_z.setdefault(l["z"], []).append(l)
    for i, s in enumerate(SH):
        for l in lines_by_z.get(i, []):
            if with_key: o.append(f'<path d="{path_d(l["pts"], False)}" fill="none" stroke="{l["color"]}" stroke-width="{KEYW[l["part"]]}" stroke-linecap="round"/>')
        stroke = f' stroke="{C["key"]}" stroke-width="{KEYW[s["part"]]}" stroke-linejoin="round"' if (with_key and s["key"]) else ""
        o.append(f'<path d="{path_d(s["pts"], True)}" fill="{s["fill"]}"{stroke}/>')
        if s["name"] == "pavement" and with_key and cobbles:
            for c in COB:
                o.append(f'<path d="{path_d(c, False)}" stroke="{C["cob"]}" stroke-width="1.3" fill="none"/>')
        if s["name"] == MOTIF_AFTER and motifs:
            # motifs over shirt and upper arms (drawn after them, under the apron which comes later in z)
            o.append('<g clip-path="url(#sc)">')
            for m in MOT:
                x, y = m
                o.append(f'<path d="M{x-4:.1f},{y:.1f} H{x+4:.1f} M{x:.1f},{y-4:.1f} V{y+4:.1f}" stroke="{C["shirt_mot"]}" stroke-width="2.6"/>')
            o.append('</g>')
    for l in lines_by_z.get(len(SH), []):
        if with_key: o.append(f'<path d="{path_d(l["pts"], False)}" fill="none" stroke="{l["color"]}" stroke-width="{KEYW[l["part"]]}" stroke-linecap="round"/>')
    o.append("</svg>")
    return "\n".join(o)

if __name__ == "__main__":
    import subprocess, sys
    out = os.path.dirname(os.path.abspath(__file__))
    name = sys.argv[1] if len(sys.argv) > 1 else "schema_v1"
    open(f"{out}/{name}.svg", "w").write(svg())
    open(f"{out}/{name}_blocks.svg", "w").write(svg(cobbles=False))
    subprocess.run(["rsvg-convert", "-w", "600", "-h", "800", f"{out}/{name}.svg", "-o", f"{out}/{name}_preview.png"], check=True)
    print(len(SH), "shapes", len(LN), "lines")
