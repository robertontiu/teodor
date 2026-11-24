"""Teodor's own lay figure: joints placed by hand (figure frame: x right, y to the head, z toward the eye),
built from capsules and ellipsoids so legs can splay, the back arch and limbs foreshorten."""
import json, sys, numpy as np
J = dict(
 pelvis=(0, 0, 0), lumbar=(0.0, 0.17, 0.08), chest=(0.03, 0.34, 0.15), neck=(0.05, 0.50, 0.10),
 head=(0.10, 0.615, -0.01),
 sh_l=(0.21, 0.45, 0.09), sh_r=(-0.15, 0.47, 0.09),
 el_l=(0.42, 0.62, -0.01), ha_l=(0.38, 0.88, -0.14),
 el_r=(-0.40, 0.37, 0.06), ha_r=(-0.58, 0.21, 0.23),
 hip_l=(0.10, 0, 0), hip_r=(-0.10, 0, 0),
 kn_l=(0.34, -0.30, 0.18), an_l=(0.20, -0.62, -0.05), toe_l=(0.25, -0.77, -0.10),
 kn_r=(-0.20, -0.42, -0.02), an_r=(-0.36, -0.80, -0.16), toe_r=(-0.44, -0.94, -0.21),
)
def build(base, out, origin=(0, 20.9, 0), s=1.06, J=J, cam=None, compose=None):
    spec = json.load(open(base))
    o = np.array(origin, float)
    W = {k: (o + np.array(v, float) * s).round(3).tolist() for k, v in J.items()}
    shirt, trou, skin, hair = "#fbf8ec", "#e9ecfb", "#f59a62", "#12357a"
    ob = [x for x in spec["objects"] if x["type"] == "box"]
    def cap(a, b, r, c): ob.append({"type": "capsule", "a": W[a], "b": W[b], "r": round(r * s, 3), "color": c, "fig": True})
    cap("pelvis", "lumbar", 0.125, shirt); cap("lumbar", "chest", 0.14, shirt); cap("chest", "neck", 0.10, shirt)
    cap("sh_l", "sh_r", 0.07, shirt); cap("hip_l", "hip_r", 0.115, trou)
    cap("neck", "head", 0.048, skin)
    for n in "lr":
        cap(f"sh_{n}", f"el_{n}", 0.052, shirt); cap(f"el_{n}", f"ha_{n}", 0.042, shirt)
        cap(f"hip_{n}", f"kn_{n}", 0.082, trou); cap(f"kn_{n}", f"an_{n}", 0.058, trou)
        cap(f"an_{n}", f"toe_{n}", 0.04, skin)
        ob.append({"type": "ellipsoid", "pos": W[f"ha_{n}"], "radii": [round(0.05*s, 3), round(0.06*s, 3), round(0.03*s, 3)], "color": skin, "fig": True})
    ob.append({"type": "ellipsoid", "pos": W["head"], "radii": [round(0.085*s, 3), round(0.105*s, 3), round(0.095*s, 3)], "color": skin, "fig": True})
    spec["objects"] = ob
    if cam: spec["camera"].update(cam)
    if compose: spec["compose"].update(compose)
    json.dump(spec, open(out, "w"), indent=1)
    return W
