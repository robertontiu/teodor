"""Regression and smoke test for studio v8.
  python3 test_v8.py            oil must match studio v7 exactly; every medium must run every tool
Runs in a temporary folder and cleans up after itself."""
import os, sys, json, shutil, subprocess, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V7 = os.path.join(HERE, "..", "v7")

EPISODES = [
    {"felt": {"arousal": 0.6, "tension": 0.4, "valence": 0.2, "care": 0.5},
     "do": [{"type": "free", "colors": ["#a04030", "#305080"], "count": 14, "size": [20, 40], "length": [60, 160]},
            {"type": "strokes", "brush": "flat", "strokes": [{"pts": [[200, 300], [500, 420], [900, 380]], "color": "#e0c080", "size": 18}]}]},
    {"felt": {"arousal": 0.3, "tension": 0.2, "valence": -0.3, "care": 0.8},
     "do": [{"type": "glaze", "color": "#203050", "opacity": 0.3, "region": {"type": "ellipse", "cx": 600, "cy": 800, "rx": 300, "ry": 400}},
            {"type": "blend", "count": 6, "size": [30, 50], "length": [80, 140]},
            {"type": "strokes", "brush": "liner", "strokes": [{"pts": [[300, 1000], [600, 1100], [900, 1000]], "color": "#101010", "size": 4}]}]},
]


def run(studio_dir, work, medium=None, support=None, episodes=EPISODES, extra=None):
    for f in os.listdir(studio_dir):
        if f.endswith(".py"):
            shutil.copy(os.path.join(studio_dir, f), work)
    if os.path.isdir(os.path.join(studio_dir, "media")):
        shutil.copytree(os.path.join(studio_dir, "media"), os.path.join(work, "media"), dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".*"))
    env = dict(os.environ, CANVAS="t")
    cmd = ["python3", os.path.join(work, "studio.py"), "new", "#d8cfc0", "600", "800"]
    if medium:
        cmd += ["--medium", medium] + (["--support", support] if support else [])
    subprocess.run(cmd, check=True, env=env, capture_output=True)
    for ep in episodes:
        subprocess.run(["python3", os.path.join(work, "studio.py"), "act", json.dumps(ep)], check=True, env=env, capture_output=True)
    for c in (extra or []):
        subprocess.run(["python3", os.path.join(work, "studio.py")] + c, check=True, env=env, capture_output=True)
    return np.load(os.path.join(work, "t_col.npy")).astype(np.float32)


def oil_matches_v7():
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        c7 = run(V7, a)
        c8 = run(HERE, b, "oil-v7")
        d = float(np.abs(c7 - c8).max())
        print(f"oil-v7 in v8 vs studio v7: max difference {d:.6f}")
        return d == 0.0


def every_medium_runs(only=None):
    sys.path.insert(0, HERE)
    from media import MEDIA
    ok = True
    for name, m in MEDIA.items():
        if only and name not in only:
            continue
        for sup in (m.supports or {None: ""}):
            eps = [{"felt": {"arousal": 0.5, "tension": 0.3, "care": 0.5},
                    "do": [{"type": "strokes", "brush": t, "colors": ["#3a4a6a"],
                            "strokes": [{"pts": [[100, 100 + 60 * i], [300, 140 + 60 * i], [500, 100 + 60 * i]], "size": 14}]}]}
                   for i, t in enumerate(m.tools)]
            eps.append({"do": [{"type": "glaze", "color": "#a05020", "opacity": 0.2}]})
            extra = [["dry", "0.5"], ["look", "full"]] + [["finish", f] for f in m.finishes]
            try:
                with tempfile.TemporaryDirectory() as w:
                    col = run(HERE, w, name, sup, eps, extra)
                    assert np.isfinite(col).all()
                print(f"{name} on {sup}: ok ({len(m.tools)} tools, {len(m.finishes)} finishes)")
            except Exception as e:
                ok = False
                print(f"{name} on {sup}: FAILED {e}")
    return ok


V8_EPISODES = [
    {"felt": {"arousal": 0.5, "tension": 0.3, "care": 0.5}, "focus": [300, 400],
     "do": [{"type": "match", "size": [24, 40], "threshold": 0.05, "colors": ["#6a4a30"], "faithful": 0.2},
            {"type": "free", "colors": ["#a04030", "#305080"], "count": 6, "size": [10, 20], "articulation": "drag"}]},
    {"felt": {"arousal": 0.4, "care": 0.6},
     "do": [{"type": "match", "size": [10, 20], "threshold": 0.04, "role": "body"},
            {"type": "model", "region": {"type": "ellipse", "cx": 300, "cy": 400, "rx": 120, "ry": 140},
             "colors": ["#40281a", "#b07050", "#f0d0a8"], "size": [8, 14], "max_strokes": 80},
            {"type": "strokes", "strokes": [{"pts": [[100, 600], [300, 560], [500, 620]], "size": 10, "color": "#202020", "articulation": "swell"},
                                            {"pts": [[120, 700], [260, 690]], "size": 8, "color": "#f0e0c0", "articulation": "flick"}]},
            {"type": "element", "name": "head", "region": {"type": "ellipse", "cx": 300, "cy": 400, "rx": 120, "ry": 140}}]},
    {"felt": {"arousal": 0.4, "care": 0.6},
     "do": [{"type": "scrape", "region": {"type": "rect", "x": 60, "y": 80, "w": 160, "h": 120}},
            {"type": "wipe", "region": {"type": "rect", "x": 380, "y": 80, "w": 160, "h": 120}},
            {"type": "paintout", "region": {"type": "rect", "x": 60, "y": 620, "w": 200, "h": 120}},
            {"type": "free", "colors": ["#e0d0b0"], "count": 4, "size": [12, 18], "articulation": "scumble"}]},
    {"felt": {"arousal": 0.3, "care": 0.8},
     "do": [{"type": "hatch", "regular": True, "angle": 20, "spacing": 8, "layers": [0.4], "size": 2, "colors": ["#202020"],
             "region": {"type": "rect", "x": 0, "y": 560, "w": 600, "h": 240}},
            {"type": "hatch", "follow": "form", "spacing": 10, "layers": [0.7, 0.45], "size": 2, "colors": ["#202020"], "length": 200,
             "region": {"type": "ellipse", "cx": 300, "cy": 400, "rx": 120, "ry": 140}}]},
]


def schema(work):
    from PIL import Image, ImageDraw, ImageFilter
    im = Image.new("RGB", (600, 800), (70, 90, 120)); d = ImageDraw.Draw(im)
    d.rectangle([0, 500, 600, 800], fill=(60, 80, 50)); d.ellipse([180, 260, 420, 540], fill=(220, 170, 120))
    im.filter(ImageFilter.GaussianBlur(4)).save(os.path.join(work, "ref.png"))
    return os.path.join(work, "ref.png")


def v8_intentions(only=None):
    """The v8 intentions (match, free, strokes with articulations, model, scrape, wipe, paintout, element) on
    every medium; roles are recorded; `look layers`, `report` and `report finish` run. Woodblock must refuse
    the revision tools with a clear error, tempera must refuse wipe."""
    sys.path.insert(0, HERE)
    from media import MEDIA
    ok = True
    for name, m in MEDIA.items():
        if name == "oil-v7" or (only and name not in only):
            continue
        sup = list(m.supports)[0] if m.supports else None
        try:
            with tempfile.TemporaryDirectory() as w:
                env = dict(os.environ, CANVAS="t")
                run(HERE, w, name, sup, [], [])
                py = ["python3", os.path.join(w, "studio.py")]
                subprocess.run(py + ["ref", schema(w)], check=True, env=env, capture_output=True)
                eps = json.loads(json.dumps(V8_EPISODES))
                if name in ("woodblock", "tempera"):
                    bad = [it for it in eps[2]["do"] if it["type"] in (("scrape", "wipe", "paintout") if name == "woodblock" else ("wipe",))]
                    for it in bad:
                        r = subprocess.run(py + ["act", json.dumps({"do": [it]})], env=env, capture_output=True, text=True)
                        assert r.returncode != 0 and ("can't" in (r.stderr + r.stdout)), f"{name} should refuse {it['type']}"
                        eps[2]["do"].remove(it)
                for ep in eps:
                    r = subprocess.run(py + ["act", json.dumps(ep)], env=env, capture_output=True, text=True)
                    assert r.returncode == 0, r.stderr[-400:]
                for c in (["look", "layers"], ["look", "layers", "correction"], ["report"], ["report", "finish"]):
                    r = subprocess.run(py + c, env=env, capture_output=True, text=True)
                    assert r.returncode == 0, r.stderr[-400:]
                bits = np.load(os.path.join(w, "t_roles.npy"))
                with tempfile.TemporaryDirectory() as w2:
                    run(HERE, w2, name, sup, [], [])
                    subprocess.run(["python3", os.path.join(w2, "studio.py"), "new", "#e8e0d0", "300", "400", "--medium", name,
                                    "--px-per-mm", "16"], check=True, env=env, capture_output=True)
                    assert json.load(open(os.path.join(w2, "t_meta.json")))["px_per_mm"] == 16.0
                assert bits.any(), "no roles recorded"
                col = np.load(os.path.join(w, "t_col.npy")).astype(np.float32)
                assert np.isfinite(col).all()
                assert "elements" in subprocess.run(py + ["report"], env=env, capture_output=True, text=True).stdout
            print(f"{name}: v8 intentions ok")
        except Exception as e:
            ok = False
            print(f"{name}: v8 intentions FAILED {e}")
    return ok


if __name__ == "__main__":
    # python3 test_v8.py [--only medium1,medium2]   (--only skips the v7 regression)
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    r1 = oil_matches_v7() if not only else True
    r2 = every_medium_runs(only)
    r3 = v8_intentions(only)
    print("PASS" if (r1 and r2 and r3) else "FAIL")
    sys.exit(0 if (r1 and r2 and r3) else 1)
