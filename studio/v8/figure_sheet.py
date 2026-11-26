"""Study sheets from the people builder (figure.py), for checking by eye and as painter's references.

  python3 figure_sheet.py expressions out.jpg [sex] [age] [planes]   one head per expression preset
  python3 figure_sheet.py hands out.jpg                              every hand preset, two views
  python3 figure_sheet.py both out.jpg                               expressions above, hands below

Heads are lit from above and to one side, the way a painter lights a model, so the planes read.
"""
import sys, math
import numpy as np
from PIL import Image, ImageDraw
import scene
import figure

EXPR_ORDER = ["neutral", "smile", "laugh", "gasp", "surprise", "fear", "sorrow", "sleep"]
HAND_ORDER = ["open", "relaxed", "rest", "hold", "grip", "push_hair", "throw", "point"]


def head_spec(expr, yaw=28, sex="female", age=30, planes=0.45, hair="#3a281e"):
    a = math.radians(yaw)
    d = 0.72
    o = {"type": "person", "id": "p", "sex": sex, "age": age, "expression": expr, "planes": planes,
         "hair": {"style": "short" if sex == "male" else "bun", "color": hair}, "color": "#4a4e58",
         "anchor": "head", "pos": [0, 1.6, 0], "masks": False}
    return {"camera": {"pos": [math.sin(a) * d, 1.6, math.cos(a) * d], "look_at": [0, 1.57, 0], "fov": 24},
            "sun": {"azimuth": 42, "elevation": 38, "intensity": 1.8, "softness": 14},
            "sky": {"zenith": "#5a626e", "horizon": "#8a9098"}, "ambient": {"intensity": 0.4, "sky": "#8090a8", "ground": "#6a5a48"},
            "ground": {"enabled": False}, "objects": [o]}


def hand_spec(preset, yaw=30, el=15):
    a, b = math.radians(yaw), math.radians(el)
    d = 0.42
    return {"camera": {"pos": [math.sin(a) * math.cos(b) * d, 0.95 + math.sin(b) * d, math.cos(a) * math.cos(b) * d], "look_at": [0, 0.93, 0], "fov": 30},
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


def expressions(sex="female", age=30, planes=0.45, w=200, h=260):
    return sheet([head_spec(e, sex=sex, age=age, planes=planes) for e in EXPR_ORDER],
                 [f"{e}  (AU {'+'.join(sorted(figure.EXPRESSIONS[e], key=lambda k: int(k))) or '-'})" for e in EXPR_ORDER], 4, w, h)


def hands(w=160, h=210):
    return sheet([hand_spec(p) for p in HAND_ORDER] + [hand_spec(p, yaw=110, el=10) for p in HAND_ORDER],
                 HAND_ORDER + [p + " (side)" for p in HAND_ORDER], 8, w, h)


if __name__ == "__main__":
    what, out = sys.argv[1], sys.argv[2]
    a = sys.argv[3:]
    if what == "expressions":
        im = expressions(a[0] if a else "female", float(a[1]) if len(a) > 1 else 30, float(a[2]) if len(a) > 2 else 0.45)
    elif what == "hands":
        im = hands()
    else:
        e, hd = expressions(), hands()
        im = Image.new("RGB", (max(e.width, hd.width), e.height + hd.height), "#1c1c1c")
        im.paste(e, ((im.width - e.width) // 2, 0)); im.paste(hd, (0, e.height))
    im.save(out, quality=92)
    print(out)
