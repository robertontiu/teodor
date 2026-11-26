"""Given the man's geometry, find camera pos/look/roll/fov putting his open eye and the moon at
chosen picture points, and report how frontal the face is seen. Prints the best few."""
import sys, json, math, numpy as np
sys.path.insert(0, '/home/claude/teodor-work/19')
import human
P = json.load(open(sys.argv[1]))
R = math.radians
def n(a): a = np.asarray(a, float); return a / np.linalg.norm(a)
el, az = R(P["moon_el"]), R(P["moon_az"])
d = np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)])
man = {"type": "person", "sex": "male", "age": 45, "pose": "lie_back", "anchor": "head", "pos": [0, 0.115, 0],
       "joints": {"neck": P["neck"], "head": P.get("head", [0, 0, 0])}}
mesh, parts, J = human.person(man)
V = np.asarray(mesh['verts']); eid = np.asarray(mesh['eye_id'])
eyeL, eyeR = V[eid == 0].mean(0), V[eid == 1].mean(0)
mid = (eyeL + eyeR) / 2
fn = n(mid - np.asarray(J["head"]))
thumb = eyeL + P["reach"] * d
W, H = 1200, 1600
def ray(px, py, f):
    u = (px + 0.5 - W / 2) / (H / 2); v = -(py + 0.5 - H / 2) / (H / 2)
    return n([-u, v, f])   # camera x flipped so the frame is proper (renderer: rt = fw x up)
tE, tM = P["t_eye"], P["t_moon"]       # picture targets in px of 1200x1600
print("face-normal to sightline deg", round(math.degrees(math.acos(float(fn @ n(d)))), 1), "fn", fn.round(2).tolist())
best = []
for cx in np.arange(-0.6, -0.15, 0.03):
  for cy in np.arange(0.08, 0.45, 0.03):
    for cz in np.arange(-0.35, 0.3, 0.03):
        C = np.array([cx, cy, cz])
        if np.linalg.norm(C - mid) < 0.25: continue
        a = n(eyeL - C); b = n(d)
        ang = math.acos(float(a @ b))
        # fov so that target rays subtend ang
        lo, hi = 0.3, 3.0
        for _ in range(40):
            f = (lo + hi) / 2
            r = math.acos(float(ray(*tE, f) @ ray(*tM, f)))
            if r > ang: lo = f
            else: hi = f
        fov = math.degrees(2 * math.atan(1 / f))
        if not (60 <= fov <= P.get("fovmax", 92)): continue
        # rotation: camera basis such that cam->world maps ray(tE)->a, ray(tM)->b
        A = np.stack([ray(*tE, f), ray(*tM, f), n(np.cross(ray(*tE, f), ray(*tM, f)))])
        B = np.stack([a, b, n(np.cross(a, b))])
        Rm = B.T @ np.linalg.inv(A.T)           # world = Rm @ cam
        rt, up, fw = -Rm[:, 0], Rm[:, 1], Rm[:, 2]
        # thumb position
        q = thumb - C; z = q @ fw
        tu, tv = f * (q @ rt) / z, f * (q @ up) / z
        tx, ty = tu * H / 2 + W / 2, -tv * H / 2 + H / 2
        cr = n(np.asarray(J['head']) - np.asarray(J['neckb']))
        crx, cry = float(cr @ rt), float(cr @ up)
        hpx = 0.1 / z * f * H / 2
        fz = float((mid - C) @ fw); fpx = 0.15 / fz * f * H / 2
        view = math.degrees(math.acos(float(fn @ n(C - mid))))   # 0 = frontal
        roll = math.degrees(math.atan2(float(-rt[1]), float(up[1])))
        dist = np.linalg.norm(C - mid)
        best.append((view, fov, roll, C.round(2).tolist(), (round(tx), round(ty)), (C + fw).round(3).tolist(), round(dist, 2), up.round(2).tolist(), (round(crx,2), round(cry,2)), round(hpx), round(fpx)))
best.sort(key=lambda r: r[0])
ok = [b for b in best if 0 < b[4][0] < W and 0 < b[4][1] < H and b[7][1] > 0.2 and b[8][0] < P.get('crx', -0.6)]
for b in ok[:15]: print(b)
