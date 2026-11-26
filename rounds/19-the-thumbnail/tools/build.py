"""Builds the scene for round 19 from a few decisions: his sightline to the moon, the head's turn,
the camera. Usage: build.py params.json out_scene.json"""
import sys, json, math, numpy as np
sys.path.insert(0, '/home/claude/teodor-work/19')
import human
P = json.load(open(sys.argv[1]))
R = math.radians
def n(a): a = np.asarray(a, float); return a / np.linalg.norm(a)
el, az = R(P["moon_el"]), R(P["moon_az"])          # az: 0 = toward his feet (+z), + = to his left (+x)
d = np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)])
man = {"type": "person", "id": "man", "sex": "male", "age": 45, "build": "average", "pose": "lie_back",
       "anchor": "head", "pos": [0, 0.115, 0], "facing": 0,
       "joints": {"neck": P["neck"], "head": P.get("head", [0, 0, 0])},
       "expression": {"preset": "neutral", "au": P["au"]}, "gaze": P["gaze"],
       "ancestry": P.get("ancestry", {"caucasian": 0.6, "african": 0.2, "asian": 0.2}),
       "skin": P.get("skin", "#c89a7c"), "beard": P.get("beard", 0.55),
       "hair": {"style": "short", "color": "#2a2420"},
       "clothes": [{"kind": "shirt", "color": P.get("shirt", "#e4e0d8"), "sleeves": "long", "ease": 0.035},
                   {"kind": "trousers", "color": "#4a4e58"}]}
mesh, parts, J = human.person(man)
V = np.asarray(mesh['verts']); eid = np.asarray(mesh['eye_id'])
eyeL = V[eid == 0].mean(0)                         # his left eye: the open, aiming one
hand_pt = eyeL + P["reach"] * d                    # the thumbnail sits on the sightline
# the wrist sits below and behind the thumbnail: offset along the arm
side = n(np.cross(d, [0, 1, 0]))
wrist = hand_pt + np.asarray(P.get("wrist_off", [0, 0, 0]))
man[P.get("arm", "reach_r")] = {"target": wrist.tolist(), "palm": P["palm"], "fingers": P["fingers"],
                  "pole": P.get("pole", [-1, -0.3, 0.2]),
                  "hand": {"f": P.get("fingers_f", [[85, 95, 40], [90, 98, 40], [92, 98, 40], [94, 98, 40]]), "spread": 0,
                           "thumb": P.get("thumb", [20, 5, 0, 0, 0])}}
moon = eyeL + 400 * n(d)
sun_az, sun_el = R(P["sun_az"]), R(P["sun_el"])
ld = np.array([math.sin(sun_az) * math.cos(sun_el), math.sin(sun_el), math.cos(sun_az) * math.cos(sun_el)])
print("eyeL", eyeL.round(3).tolist(), "thumb pt", hand_pt.round(3).tolist(), "moon-sun sep deg",
      round(math.degrees(math.acos(float(n(d) @ ld))), 1))
cam = dict(P["camera"])
if "aim_mix" in P:                                  # look between his eye and the moon
    C = np.asarray(cam["pos"], float); t = P["aim_mix"]
    f = n((1 - t) * n(eyeL - C) + t * n(d))
    cam["look_at"] = (C + f).tolist()
    print("spread face-moon deg", round(math.degrees(math.acos(float(n(eyeL - C) @ n(d)))), 1))
sc = {"camera": cam,
      "sun": {"azimuth": P["sun_az"], "elevation": P["sun_el"], "color": "#fff4e6", "intensity": P.get("sun_i", 1.8), "softness": 3},
      "sky": {"zenith": P.get("zenith", "#3a4a6a"), "horizon": P.get("horizon", "#a8b4c8"), "sun_glow": 0.0, "disc": 0},
      "ambient": {"sky": "#9aa4b8", "ground": "#5a6448", "intensity": P.get("amb", 0.45)},
      "fog": {"density": 0.0}, "ground": {"color": "#4e5e34", "color2": "#3e4c28"}, "exposure": P.get("exposure", 1.0),
      "objects": [man, {"type": "sphere", "id": "moon", "pos": moon.tolist(), "r": 400 * math.tan(R(0.26)), "color": P.get("moon_col", "#b8b4ae")}]
                 + P.get("extra", []),
      "render_scale": P.get("render_scale", 1.0)}
json.dump(sc, open(sys.argv[2], "w"), indent=1)
json.dump({"eyeL": eyeL.tolist(), "thumb": hand_pt.tolist(), "moon": moon.tolist(), "d": d.tolist()}, open(sys.argv[2] + ".geo", "w"))
