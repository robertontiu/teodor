"""The tool gallery: a mark sheet for every tool of a medium, so each instrument can be checked by eye
(and against real examples) before a painter uses it. Spectre's engine/gallery.py does the same with
spectrograms of every instrument.

  python3 gallery.py <medium> [support] [out.png]

Rows, one per tool: a straight stroke at light, medium and full pressure; an S-curve fast (agitated)
and slow (careful); a short hatch of five strokes; then a glaze/wash swatch over a dark band, a second
colour crossing the first (mixing or layering), and a dry-then-overlap test.
Runs in a temporary folder; nothing is left behind except the sheet.
"""
import os, sys, json, shutil, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def sheet(medium, support=None, out=None):
    sys.path.insert(0, HERE)
    from media import get_medium
    m = get_medium(medium)
    tools = list(m.tools)
    W, rowh = 1200, 150
    H = rowh * (len(tools) + 2) + 40
    out = out or os.path.join(os.getcwd(), f"gallery_{medium}{'_' + support if support else ''}.png")
    env = dict(os.environ, CANVAS="g")
    with tempfile.TemporaryDirectory() as w:
        for f in os.listdir(HERE):
            if f.endswith(".py"):
                shutil.copy(os.path.join(HERE, f), w)
        shutil.copytree(os.path.join(HERE, "media"), os.path.join(w, "media"), ignore=shutil.ignore_patterns("__pycache__", ".*"))
        S = lambda *a: subprocess.run(["python3", os.path.join(w, "studio.py"), *a], check=True, env=env, capture_output=True, text=True)
        ground = "#efe9dc"
        S("new", ground if ground.startswith("#") else "#efe9dc", str(W), str(H), "--medium", medium, *(["--support", support] if support else []))
        # a dark band to test transparency and covering power
        S("act", json.dumps({"do": [{"type": "glaze", "color": "#1a1a22", "opacity": 0.9,
                                       "region": {"type": "rect", "x": 900, "y": 10, "w": 280, "h": H - 20}, "feather": 2}]}))
        S("dry", "1.0")
        for i, t in enumerate(tools):
            y = 40 + i * rowh + rowh // 2
            strokes = []
            for k, p in enumerate((0.35, 0.7, 1.0)):
                strokes.append({"pts": [[30 + k * 90, y - 40], [60 + k * 90, y], [90 + k * 90, y + 40]], "pressure": p})
            ep = {"felt": {"arousal": 0.3, "tension": 0.2, "care": 0.7},
                  "do": [{"type": "strokes", "brush": t, "colors": ["#2b3f6b"], "size": [12, 12], "strokes": strokes}]}
            S("act", json.dumps(ep))
            for k, (felt, x0) in enumerate((({"arousal": 0.9, "tension": 0.6, "care": 0.2}, 330), ({"arousal": 0.2, "tension": 0.1, "care": 0.9}, 520))):
                S("act", json.dumps({"felt": felt, "do": [{"type": "strokes", "brush": t, "colors": ["#7a2e1e"], "size": [14, 14],
                                                             "strokes": [{"pts": [[x0, y + 35], [x0 + 60, y - 35], [x0 + 120, y + 35], [x0 + 170, y - 30]]}]}]}))
            S("act", json.dumps({"felt": {"arousal": 0.4, "care": 0.6}, "do": [{"type": "strokes", "brush": t, "colors": ["#3a3a30"], "size": [6, 6],
                                 "strokes": [{"pts": [[720 + j * 30, y - 40], [690 + j * 30, y + 40]]} for j in range(5)]}]}))
            S("act", json.dumps({"felt": {"arousal": 0.4, "care": 0.6}, "do": [{"type": "strokes", "brush": t, "colors": ["#d9a520"], "size": [16, 16],
                                 "strokes": [{"pts": [[880, y - 10], [1000, y], [1180, y + 10]]}]}]}))
        y0 = 40 + len(tools) * rowh
        S("act", json.dumps({"do": [{"type": "glaze", "color": "#b03a2e", "opacity": 0.35,
                                       "region": {"type": "rect", "x": 30, "y": y0, "w": 500, "h": rowh - 20}, "feather": 4}]}))
        S("act", json.dumps({"do": [{"type": "glaze", "color": "#2e5ab0", "opacity": 0.35,
                                       "region": {"type": "rect", "x": 300, "y": y0 + 30, "w": 500, "h": rowh - 20}, "feather": 4}]}))
        S("dry", "1.0")
        S("act", json.dumps({"do": [{"type": "free", "brush": tools[0], "colors": ["#e8d8b0"], "count": 12, "size": [18, 26], "length": [60, 120],
                                       "region": {"type": "rect", "x": 30, "y": y0 + rowh, "w": 800, "h": rowh - 30}}]}))
        shutil.copy(os.path.join(w, "g_full.png"), out)
    print(out)
    return out


if __name__ == "__main__":
    sheet(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, sys.argv[3] if len(sys.argv) > 3 else None)
