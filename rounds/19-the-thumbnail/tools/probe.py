import sys, json, numpy as np
sys.path.insert(0, '/home/claude/teodor-work/19')
import human
o = json.load(open(sys.argv[1]))
o = [x for x in o["objects"] if x.get("type") == "person"][0]
mesh, parts, J = human.person(o)
for k in sorted(J):
    v = J[k]
    try:
        a = np.asarray(v, float)
        if a.shape == (3,): print(k, a.round(3).tolist())
    except Exception: pass
print(type(mesh), list(mesh.keys())[:20] if isinstance(mesh, dict) else '')
V = np.asarray(mesh['verts']); eid = np.asarray(mesh['eye_id'])
print('verts', V.shape, 'eye_id', eid.shape, np.unique(eid)[:5])
for i in (0, 1):
    m = eid == i
    if m.sum(): print('eye', i, V[m].mean(0).round(3).tolist(), m.sum())
