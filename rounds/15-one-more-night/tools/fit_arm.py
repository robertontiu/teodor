# grid-search one arm's [raise, abduct, elbow] so the hand lands near a target point (planning aid only)
import sys, json, itertools, numpy as np
sys.path.insert(0, "/home/claude/v15"); import scene as S
spec = json.load(open(sys.argv[1])); name = sys.argv[2]; arm = sys.argv[3]; tgt = np.array(json.loads(sys.argv[4]))
o = [x for x in spec["objects"] if x.get("name") == name][0]
def hand(o):
    cap = {}; orig = S.Node
    def fake(*a, **k):
        f = a[0]; cap.update({n: c.cell_contents for n, c in zip(f.__code__.co_freevars, f.__closure__ or [])}); return orig(*a, **k)
    S.Node = fake; S.mannequin(o); S.Node = orig; return cap["W"]
best = None
for r, ab, el in itertools.product(range(-10, 120, 6), range(-60, 70, 6), range(0, 140, 8)):
    o["joints"][arm] = [r, ab, el]
    W = hand(o); d = np.linalg.norm(W["ha_" + arm[-1]] - tgt) + 0.0005 * el
    if best is None or d < best[0]: best = (d, [r, ab, el], W["el_" + arm[-1]])
print(best)
