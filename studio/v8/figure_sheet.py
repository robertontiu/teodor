"""Study sheets from the people builder (human.py, the mesh rig; figure.py with "rig": "primitive"), for checking
by eye and as painter's references.

  python3 figure_sheet.py expressions out.jpg [sex] [age] [planes]   one head per expression preset
  python3 figure_sheet.py hands out.jpg                              every hand preset: back, thumb side, fingertips first
  python3 figure_sheet.py variants out.jpg                           sex, age and build: each a head and a full figure
  python3 figure_sheet.py both out.jpg                               expressions, variants, then hands

Heads are lit from above and to one side, the way a painter lights a model, so the planes read.
"""
import sys, math, os
import numpy as np
from PIL import Image, ImageDraw
import scene
import figure

EXPR_ORDER = ["neutral", "smile", "laugh", "surprise", "fear", "scream", "sorrow", "anger", "disgust", "sleep"]
# sex, age, build, label, hair, clothes (docs/subjects/sex-age.md: each must read at thumbnail size)
VARIANTS = [
    ("female", 20, "average", "woman 20", {"style": "long", "color": "#3a2618", "length": 0.3},
     [{"kind": "dress", "color": "#5a3e48", "length": 0.8, "flare": 0.12}]),
    ("female", 40, "sturdy", "woman 40 sturdy", {"style": "bun", "color": "#4a3020"},
     [{"kind": "shirt", "color": "#b0a890", "sleeves": "long", "ease": 0.012, "length": 0.0}, {"kind": "trousers", "color": "#3e4048", "ease": 0.022}]),
    ("female", 75, "average", "woman 75", {"style": "bob", "color": "#5a4030"},
     [{"kind": "dress", "color": "#4a4a5a", "length": 0.95, "flare": 0.15}]),
    ("male", 20, "average", "man 20", {"style": "short", "color": "#3a281e"},
     [{"kind": "shirt", "color": "#9aa4b0", "sleeves": "short", "ease": 0.012}, {"kind": "trousers", "color": "#3e4048"}]),
    ("male", 40, "average", "man 40", {"style": "short", "color": "#3a281e"},
     [{"kind": "shirt", "color": "#b0a890", "sleeves": "long", "ease": 0.012}, {"kind": "trousers", "color": "#3e4048"}]),
    ("male", 75, "average", "man 75", {"style": "receding", "color": "#4a3a2e"},
     [{"kind": "shirt", "color": "#8a8478", "sleeves": "long", "ease": 0.014}, {"kind": "trousers", "color": "#4a4440"}]),
    ("female", 8, "average", "girl 8", {"style": "ponytail", "color": "#5a3a22", "length": 0.22},
     [{"kind": "dress", "color": "#7a4a40", "length": 0.6, "flare": 0.4}]),
    ("male", 8, "average", "boy 8", {"style": "short", "color": "#5a3a22"},
     [{"kind": "shirt", "color": "#7a8a6a", "sleeves": "short", "ease": 0.012}, {"kind": "trousers", "color": "#4a4440", "length": "short"}]),
]
HAND_ORDER = ["open", "relaxed", "rest", "hold", "grip", "push_hair", "throw", "point"]


def head_spec(expr, yaw=28, sex="female", age=30, planes=None, hair="#3a281e", build="average", hair_spec=None):
    a = math.radians(yaw)
    d = 0.72 * float(os.environ.get("HEADDIST", "1"))
    o = {"type": "person", "id": "p", "sex": sex, "age": age, "build": build, "expression": expr,
         "hair": hair_spec or {"style": ("receding" if age >= 60 else "short") if sex == "male" else "bun", "color": hair}, "color": "#4a4e58",
         "anchor": "head", "pos": [0, 1.6, 0], "masks": False}
    if planes is not None:
        o["planes"] = planes
    return {"camera": {"pos": [math.sin(a) * d, 1.6, math.cos(a) * d], "look_at": [0, 1.57, 0], "fov": 24},
            "sun": {"azimuth": 42, "elevation": 38, "intensity": 1.8, "softness": 14},
            "sky": {"zenith": "#5a626e", "horizon": "#8a9098"}, "ambient": {"intensity": 0.4, "sky": "#8090a8", "ground": "#6a5a48"},
            "ground": {"enabled": False}, "objects": [o]}


def hand_spec(preset, yaw=30, el=15):
    a, b = math.radians(yaw), math.radians(el)
    d = 0.42
    return {"camera": {"pos": [math.sin(a) * math.cos(b) * d, 0.93 + math.sin(b) * d, math.cos(a) * math.cos(b) * d], "look_at": [0, 0.93, 0], "fov": 34},
            "sun": {"azimuth": 40, "elevation": 45, "intensity": 1.8, "softness": 14}, "sky": {"zenith": "#5a626e", "horizon": "#8a9098"},
            "ambient": {"intensity": 0.45}, "ground": {"enabled": False},
            "objects": [{"type": "hand", "pos": [0, 1.02, 0], "preset": preset, "fingers": [0, -1, 0], "palm": [0, 0, 1], "side": "l"}]}


def sheet(specs, labels, cols, w, h):
    rows = math.ceil(len(specs) / cols)
    out = Image.new("RGB", (cols * w, rows * (h + 18)), "#1c1c1c")
    dr = ImageDraw.Draw(out)
    for i, (sp, lb) in enumerate(zip(specs, labels)):
        im = Image.fromarray(scene.Scene(sp).render(w, h))
        x, y = (i % cols) * w, (i // cols) * (h + 18)
        out.paste(im, (x, y))
        dr.text((x + 5, y + h + 3), lb, fill="#d8d8d8")
    return out


def figure_spec(sex, age, build, hair, clothes, yaw=20):
    """A whole person standing, at thumbnail scale: the sex and age must read from the silhouette."""
    a = math.radians(yaw)
    o = {"type": "person", "id": "p", "sex": sex, "age": age, "build": build, "pose": "contrapposto", "hair": hair,
         "clothes": clothes, "color": clothes[0]["color"] if clothes else "#4a4e58", "shoes": "#2a2420", "anchor": "ground", "pos": [0, 0, 0]}
    return {"camera": {"pos": [math.sin(a) * 5.4, 0.95, math.cos(a) * 5.4], "look_at": [0, 0.86, 0], "fov": 24},
            "sun": {"azimuth": 42, "elevation": 40, "intensity": 1.8, "softness": 10},
            "sky": {"zenith": "#5a626e", "horizon": "#8a9098"}, "ambient": {"intensity": 0.45, "sky": "#8090a8", "ground": "#6a5a48"},
            "ground": {"color": "#6a6258"}, "masks": False, "objects": [o]}


def expressions(sex="female", age=30, planes=None, w=200, h=260):
    return sheet([head_spec(e, sex=sex, age=age, planes=planes) for e in EXPR_ORDER],
                 [f"{e}  (AU {'+'.join(sorted(figure.EXPRESSIONS[e], key=lambda k: int(k))) or '-'})" for e in EXPR_ORDER], 5, w, h)


def variants(planes=None, w=200, h=260):
    """Each variant as a neutral head and as a full figure (sex-age.md; face.md section 4; figure.md section 1)."""
    heads = [head_spec("neutral", sex=sx, age=a, planes=planes, build=b, hair_spec=hr) for sx, a, b, _, hr, _ in VARIANTS]
    figs = [figure_spec(sx, a, b, hr, cl) for sx, a, b, _, hr, cl in VARIANTS]
    return sheet(heads + figs, [lb for *_, lb, _, _ in VARIANTS] + [lb + " (figure)" for *_, lb, _, _ in VARIANTS], len(VARIANTS), w, h)


def hands(w=160, h=210):
    """Every hand preset from the back, from the thumb side, and fingertips first (foreshortened)."""
    return sheet([hand_spec(p) for p in HAND_ORDER] + [hand_spec(p, yaw=110, el=10) for p in HAND_ORDER]
                 + [hand_spec(p, yaw=25, el=-62) for p in HAND_ORDER],
                 HAND_ORDER + [p + " (side)" for p in HAND_ORDER] + [p + " (tips first)" for p in HAND_ORDER], 8, w, h)


if __name__ == "__main__":
    what, out = sys.argv[1], sys.argv[2]
    a = sys.argv[3:]
    if what == "expressions":
        im = expressions(a[0] if a else "female", float(a[1]) if len(a) > 1 else 30, float(a[2]) if len(a) > 2 else None)
    elif what == "hands":
        im = hands()
    elif what == "variants":
        im = variants()
    else:
        e, v, hd = expressions(), variants(), hands()
        im = Image.new("RGB", (max(e.width, v.width, hd.width), e.height + v.height + hd.height), "#1c1c1c")
        im.paste(e, ((im.width - e.width) // 2, 0)); im.paste(v, ((im.width - v.width) // 2, e.height)); im.paste(hd, ((im.width - hd.width) // 2, e.height + v.height))
    im.save(out, quality=92)
    print(out)
