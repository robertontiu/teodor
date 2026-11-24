# probe joint positions for candidate arm angles (planning aid)
import sys, json, numpy as np
sys.path.insert(0, "/home/claude/v15"); import scene as S
spec = json.load(open(sys.argv[1])); name, arm = sys.argv[2], sys.argv[3]
o = [x for x in spec["objects"] if x.get("name") == name][0]
def W_of(o):
    cap = {}; orig = S.Node
    def fake(*a, **k):
        f = a[0]
        if "W" in f.__code__.co_freevars: cap["W"] = f.__closure__[f.__code__.co_freevars.index("W")].cell_contents
        return orig(*a, **k)
    S.Node = fake; S.mannequin(o); S.Node = orig; return cap["W"]
tgt = np.array(json.loads(sys.argv[4]))
res = []
for r in range(-10, 100, 5):
    for ab in range(-60, 70, 5):
        for el in range(10, 130, 5):
            o["joints"][arm] = [r, ab, el]; W = W_of(o)
            res.append((float(np.linalg.norm(W["ha_" + arm[-1]] - tgt)), [r, ab, el], W["el_" + arm[-1]].round(2).tolist(), W["ha_" + arm[-1]].round(2).tolist()))
res.sort(key=lambda x: x[0]); [print(x) for x in res[:4]]
