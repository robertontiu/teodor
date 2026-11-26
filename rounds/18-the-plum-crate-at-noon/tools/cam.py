# world (m, y up) -> canvas px for the blockout camera b11 (same maths as scene.py's camera)
import json, math, numpy as np
_s = json.load(open('/home/claude/teodor-work/18/plan/blockout/b11.json'))['camera']
W, H = 1200, 1600
ro = np.array(_s['pos'], float); ta = np.array(_s['look_at'], float)
fw = (ta - ro) / np.linalg.norm(ta - ro)
rt = np.cross(fw, [0, 1, 0]); rt /= np.linalg.norm(rt)
up = np.cross(rt, fw)
r = math.radians(_s['roll'])
rt, up = rt * math.cos(r) + up * math.sin(r), up * math.cos(r) - rt * math.sin(r)
F = 1 / math.tan(math.radians(_s['fov']) / 2)
def P(x, y, z):
    d = np.array([x, y, z], float) - ro
    u = F * (d @ rt) / (d @ fw); v = F * (d @ up) / (d @ fw)
    return (float(u * H / 2 + W / 2), float(-v * H / 2 + H / 2))
