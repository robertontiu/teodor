import sys, json, numpy as np
sys.path.insert(0, "/home/claude/v15")
import scene as S
spec = json.load(open(sys.argv[1]))
# monkeypatch to capture W
for o in spec["objects"]:
    if o["type"] != "figure": continue
    src = S.mannequin.__code__
    import types
    cap = {}
    orig_node = S.Node
    def fake(*a, **k):
        f = a[0]
        try:
            cap.update({n: c.cell_contents for n, c in zip(f.__code__.co_freevars, f.__closure__ or [])})
        except Exception: pass
        return orig_node(*a, **k)
    S.Node = fake
    S.mannequin(o); S.Node = orig_node
    W = cap.get("W", {})
    print(o.get("name", o["pos"]), {k: [round(float(x), 2) for x in v] for k, v in W.items() if k[:2] in ("ha", "el", "he", "sh")})
