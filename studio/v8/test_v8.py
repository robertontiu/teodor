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
        shutil.copytree(os.path.join(studio_dir, "media"), os.path.join(work, "media"), dirs_exist_ok=True)
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
        c8 = run(HERE, b, "oil")
        d = float(np.abs(c7 - c8).max())
        print(f"oil v8 vs v7: max difference {d:.6f}")
        return d == 0.0


def every_medium_runs():
    sys.path.insert(0, HERE)
    from media import MEDIA
    ok = True
    for name, m in MEDIA.items():
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


if __name__ == "__main__":
    r1 = oil_matches_v7()
    r2 = every_medium_runs()
    print("PASS" if (r1 and r2) else "FAIL")
    sys.exit(0 if (r1 and r2) else 1)
