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
                if name == "ink":
                    # raw xuan: paintout must be refused; wipe blots wet ink and must refuse dry ink with a reason
                    for it in [it for it in eps[2]["do"] if it["type"] in ("wipe", "paintout")]:
                        r = subprocess.run(py + ["act", json.dumps({"do": [it]})], env=env, capture_output=True, text=True)
                        if it["type"] == "paintout" or r.returncode != 0:
                            assert r.returncode != 0 and "can't" in (r.stderr + r.stdout), f"ink should refuse {it['type']} on raw xuan"
                        eps[2]["do"].remove(it)
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


def detail_pass(only=None):
    """The detail pass (detail.py): open a region at 4x, check the detail's arrays, cancel (the canvas must be left
    bit for bit), open again, paint in the detail, look, report, close (area), and once more with --resample sample;
    outside the region nothing may change, inside it must, roles, log and frames must be recorded."""
    sys.path.insert(0, HERE)
    from media import MEDIA
    ok = True
    for name, m in MEDIA.items():
        if name == "oil-v7" or (only and name not in only) or (not only and name not in ("oil", "watercolour", "graphite")):
            continue
        sup = list(m.supports)[0] if m.supports else None
        try:
            with tempfile.TemporaryDirectory() as w:
                env = dict(os.environ, CANVAS="t")
                run(HERE, w, name, sup, [], [])
                py = ["python3", os.path.join(w, "studio.py")]
                sh = lambda *c: subprocess.run(py + list(c), env=env, capture_output=True, text=True)
                assert sh("ref", schema(w)).returncode == 0
                tool = list(m.tools)[0]
                r = sh("act", json.dumps({"do": [{"type": "strokes", "brush": tool, "colors": ["#5a4a3a"],
                                                   "strokes": [{"pts": [[40, 200], [300, 260], [560, 220]], "size": 14}]}]}))
                assert r.returncode == 0, r.stderr[-400:]
                arrs = lambda: {a: np.load(os.path.join(w, f"t_{a}.npy")) for a in m.arrays}
                before = arrs()
                x, y, wd, ht = 200, 180, 120, 100
                r = sh("detail", "open", str(x), str(y), str(wd), str(ht), "--scale", "4")
                assert r.returncode == 0, r.stderr[-400:]
                dm = json.load(open(os.path.join(w, "t_detail_meta.json")))
                assert dm["px_scale"] == 4.0 and dm["detail"]["w"] == wd
                assert np.load(os.path.join(w, "t_detail_col.npy")).shape[:2] == (ht * 4, wd * 4)
                assert np.load(os.path.join(w, "t_detail_tex.npy")).shape == (ht * 4, wd * 4)
                assert sh("detail", "open", "0", "0", "50", "50").returncode != 0, "a second detail must be refused"
                assert sh("detail", "cancel").returncode == 0
                after = arrs()
                assert all(np.array_equal(before[a], after[a]) for a in m.arrays), "open + cancel changed the canvas"
                for rs in ("area", "sample"):
                    nfr = len(os.listdir(os.path.join(w, "t_frames")))
                    assert sh("detail", "open", str(x), str(y), str(wd), str(ht)).returncode == 0
                    r = sh("act", "--detail", json.dumps({"do": [{"type": "strokes", "brush": tool, "colors": ["#c03020"], "role": "accent",
                                                                  "strokes": [{"pts": [[80, 80], [240, 200], [400, 300]], "size": 24}]}]}))
                    assert r.returncode == 0, r.stderr[-400:]
                    for c in (["look", "detail"], ["look", "--detail", "full"], ["report", "--detail"]):
                        r = sh(*c)
                        assert r.returncode == 0, (c, r.stderr[-400:])
                    assert sh("finish", "--detail", "varnish").returncode != 0, "finish must be refused in a detail"
                    r = sh("detail", "close", "--resample", rs)
                    assert r.returncode == 0, r.stderr[-400:]
                    new = arrs()
                    out = np.ones(new["col"].shape[:2], bool); out[y:y + ht, x:x + wd] = False
                    for a in m.arrays:
                        assert np.array_equal(new[a][out], after[a][out]), f"{a} changed outside the region"
                    assert np.abs(new["col"].astype(np.float32) - after["col"].astype(np.float32))[~out].max() > 0.1, "the detail's paint did not come back"
                    bits = np.load(os.path.join(w, "t_roles.npy"))
                    assert (bits[y:y + ht, x:x + wd] & (1 << 8)).any(), "the accent role was not recorded"
                    assert len(os.listdir(os.path.join(w, "t_frames"))) >= nfr + 3, "frames missing"
                    log = [json.loads(l) for l in open(os.path.join(w, "t_log.jsonl"))]
                    assert any("in_detail" in e for e in log)
                    meta = json.load(open(os.path.join(w, "t_meta.json")))
                    assert "detail_open" not in meta and meta["details"][-1]["resample"] == rs
                    assert not any(f.startswith("t_detail_") for f in os.listdir(w))
                    after = new
            print(f"{name}: detail pass ok")
        except Exception as e:
            ok = False
            print(f"{name}: detail pass FAILED {e!r}")
    return ok


def fine_measures():
    """G10 (docs/research/hyperrealism-gaps.md): eyes.measure_fine reads synthetic images right (value tails, a
    known edge rise, counted glints, fog, scale-correct bands); `report` and `report ref` print the fine measures at
    the sheet's resolution and flag missing darks against the close-up ruler; the ruler's bounds are rebuilt from
    stored photographs."""
    sys.path.insert(0, HERE)
    import eyes
    from scipy.ndimage import gaussian_filter
    ok = True
    try:
        # value tails and fog: a flat L* 50 field is all fog, no darks
        f = eyes.measure_fine(np.full((400, 400), 50.0, np.float32), 5.0)
        assert f["flat_midtone_share"] > 0.99 and f["value_below20"] == 0 and abs(f["value_p50"] - 50) < 1e-3
        # an edge blurred by sigma 1 mm: the 10-90% rise is 2.563 sigma
        L = np.where(np.arange(600)[None, :] < 300, 20.0, 80.0).astype(np.float32).repeat(200, 0)
        f = eyes.measure_fine(gaussian_filter(L, 5.0), 5.0)
        assert abs(f["edge_median_mm"] - 2.563) < 0.15, f["edge_median_mm"]
        # five glints 1 mm across, 40 L* over a mid grey; and a 6 mm bright disc that is not a glint
        L = np.full((400, 400), 50.0, np.float32)
        yy, xx = np.mgrid[0:400, 0:400]
        for cx in (50, 120, 190, 260, 330):
            L[(yy - 80) ** 2 + (xx - cx) ** 2 <= 2.5 ** 2] = 90
        L[(yy - 300) ** 2 + (xx - 200) ** 2 <= 15 ** 2] = 90
        f = eyes.measure_fine(L, 5.0)
        assert f["specular_count"] == 5 and f["specular_count_30"] == 5, f
        # the same texture at twice the pixels per mm measures the same in mm
        rng = np.random.default_rng(1)
        base = gaussian_filter(rng.standard_normal((300, 300)).astype(np.float32), 2.0) * 20 + 50
        big = np.kron(base, np.ones((2, 2), np.float32))
        b1, b2 = eyes.band_energy(base, 3.0), eyes.band_energy(big, 6.0)
        assert all(abs(b1[s] - b2[s]) / b1[s] < 0.15 for s in (0.5, 1.0, 2.0)), (b1, b2)
        assert b1[0.125] is None and b2[0.125] is not None      # finer than half a pixel: not measured
        # the close-up ruler's bounds from stored photographs
        sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
        import measure_targets as mt
        t = mt.closeup_build([{"measures": {"value_below20": 0.2, "skin_band_rms": {"0.5": 1.0}}},
                              {"measures": {"value_below20": 0.1, "skin_band_rms": {"0.5": 0.6}}}])
        assert abs(t["value_below20"]["min"] - 0.09) < 1e-6 and t["value_below20"]["n"] == 2
        assert abs(t["skin_band_rms"]["0.5"]["min"] - 0.52) < 1e-6 and abs(t["skin_band_rms"]["0.5"]["max"] - 1.08) < 1e-6
        # report and report ref on a graphite sheet, with the style's close-up ruler beside the studio
        with tempfile.TemporaryDirectory() as w:
            env = dict(os.environ, CANVAS="t")
            run(HERE, w, "graphite", "vellum", [], [])
            shutil.copy(os.path.join(HERE, "..", "targets.json"), w)
            py = ["python3", os.path.join(w, "studio.py")]
            subprocess.run(py + ["new", "#f7f6f2", "600", "800", "--medium", "graphite", "--support", "vellum",
                                 "--style", "graphite-hyperrealism"], check=True, env=env, capture_output=True)
            subprocess.run(py + ["ref", schema(w)], check=True, env=env, capture_output=True)
            r = subprocess.run(py + ["report"], env=env, capture_output=True, text=True)
            assert r.returncode == 0, r.stderr[-400:]
            assert "fine (sheet, at 5.00 px/mm)" in r.stdout and "the darks are missing" in r.stdout, r.stdout[-800:]
            assert "fine" in json.load(open(os.path.join(w, "t_report.json")))
            r = subprocess.run(py + ["report", "ref"], env=env, capture_output=True, text=True)
            assert r.returncode == 0 and "REPORT on the SCHEMA" in r.stdout and "fine (schema" in r.stdout, r.stderr[-400:]
            r = subprocess.run(py + ["report", "--crop", "100", "100", "200", "200"], env=env, capture_output=True, text=True)
            assert r.returncode == 0 and "fine (crop 100,100 200x200" in r.stdout, r.stderr[-400:]
        print("fine measures (G10): ok")
    except Exception as e:
        ok = False
        print(f"fine measures (G10): FAILED {e!r}")
    return ok


def darks_first():
    """G2: graphite's charcoal darks. Compressed charcoal on bare vellum goes far darker than graphite can; over unfixed,
    burnished 8B it hardly takes; over the same 8B after a workable fixative it takes again; the carbon is recorded,
    hides the shine and lifts with an eraser; a canvas saved before the carbon array existed still loads."""
    ok = True
    try:
        with tempfile.TemporaryDirectory() as w:
            env = dict(os.environ, CANVAS="t")
            run(HERE, w, "graphite", "vellum", [], [])
            py = ["python3", os.path.join(w, "studio.py")]
            sh = lambda *c: subprocess.run(py + [str(x) for x in c], env=env, capture_output=True, text=True, check=True)
            R = lambda x: {"type": "rect", "x": x, "y": 30, "w": 80, "h": 180}
            hat = lambda tool, x, ang, size=8, sp=3: {"type": "hatch", "brush": tool, "value": 0.0, "layers": [1.0], "size": size,
                                                     "spacing": sp, "angle": ang, "colors": ["#000000"], "pressure": 1.0,
                                                     "region": R(x), "length": 400, "clip": True}
            sh("new", "#f7f6f2", 360, 240, "--medium", "graphite", "--support", "vellum")
            g8 = [hat("pencil_8B", x, a) for x in (130, 250) for a in (20, 110)]
            sh("act", json.dumps({"do": g8[:4]}))
            sh("finish", "fixative", json.dumps({"kind": "workable", "strength": 1.0, "region": R(250)}))
            sh("act", json.dumps({"do": [hat("compressed_charcoal", x, a, 12, 4) for x in (10, 130, 250) for a in (60,)] }))
            sh("act", json.dumps({"do": [hat("compressed_charcoal", x, a, 12, 4) for x in (10, 130, 250) for a in (150,)]}))
            col = np.load(os.path.join(w, "t_col.npy")).astype(np.float32).mean(-1)
            med = [float(np.median(col[60:180, x + 15:x + 65])) for x in (10, 130, 250)]
            bare, over, fixed = med
            assert bare < fixed < over, med                    # bare paper darkest, unfixed graphite refuses charcoal
            assert over - bare > 0.06, med
            carbon = np.load(os.path.join(w, "t_carbon.npy")).astype(np.float32)
            assert carbon[60:180, 25:75].mean() > 0.2 and carbon[60:180, 145:195].mean() < carbon[60:180, 265:315].mean()
            sh("act", json.dumps({"do": [{"type": "strokes", "brush": "electric_eraser", "colors": ["#ffffff"],
                                          "strokes": [{"pts": [[50, 60], [50, 180]], "size": 20, "pressure": 1.0}]}]}))
            c2 = np.load(os.path.join(w, "t_carbon.npy")).astype(np.float32)
            assert c2[80:160, 45:55].mean() < 0.5 * carbon[80:160, 45:55].mean(), "the eraser should lift the charcoal"
            os.remove(os.path.join(w, "t_carbon.npy"))        # a canvas from before the carbon array
            sh("look", "full")
        print("darks first (G2): ok")
    except Exception as e:
        ok = False
        print(f"darks first (G2): FAILED {e!r}")
    return ok


def portrait_camera():
    """G4: lens <-> field conversions; a scene with a person and no fov gets a 100 mm lens; `frame` puts the camera at
    the portrait distance with the head filling the asked share; the lens report gives distance and perspective, and a
    wide close-up warns. Acceptance: the framed head at >= 1.2 m and the nose within 5% of orthographic."""
    sys.path.insert(0, HERE)
    import scene as sc
    ok = True
    try:
        assert abs(sc.fov_to_lens(sc.lens_to_fov(85, 0.75), 0.75) - 85) < 1e-6
        assert abs(sc.lens_to_fov(50, 1.5) - 27.0) < 0.1          # 50 mm on a 3:2 landscape frame: 27 deg vertical
        o = {"type": "person", "id": "man", "age": 40, "sex": "male", "pos": [0, 1.62, 0], "anchor": "head",
             "hair": {"style": "short", "color": "#3a2e26"}}
        base = {"sun": {"azimuth": 50, "elevation": 30}, "ground": {"enabled": False}, "fog": {"density": 0}, "objects": [o]}
        r = sc.resolve_camera(dict(base, camera={"pos": [0, 1.6, 3], "look_at": [0, 1.6, 0]}), 0.75)
        assert abs(r["camera"]["lens_equiv_mm"] - sc.PORTRAIT_LENS_MM) < 0.5
        r = sc.resolve_camera({"camera": {}, "objects": [{"type": "box"}]}, 0.75)
        assert r["camera"]["fov"] == 40.0                          # scenes without people keep the old default
        S = sc.Scene(dict(base, camera={"frame": {"on": "man.head", "fill": 0.7}}))
        S.render(90, 120)
        lines, warn = S.lens_report()
        cam = S.spec["camera"]
        d = float(np.linalg.norm(np.asarray(cam["pos"]) - np.asarray(cam["look_at"])))
        assert abs(d - sc.PORTRAIT_DISTANCE_M) < 1e-6 and not warn, (lines, warn)
        infl = float(lines[1].split("magnifies the nose ")[1].split("%")[0])
        assert abs(infl) < 5.0, lines                             # acceptance: within 5% of the orthographic value
        S2 = sc.Scene(dict(base, camera={"pos": [0, 1.62, 0.42], "look_at": [0, 1.62, 0], "fov": 86}))
        S2.render(90, 120)
        lines2, warn2 = S2.lens_report()
        assert warn2 and "close-up" in warn2[0], (lines2, warn2)
        print(f"portrait camera (G4): ok ({lines[1]}; wide: {lines2[1]})")
    except Exception as e:
        ok = False
        print(f"portrait camera (G4): FAILED {e!r}")
    return ok


def photoreal_reference():
    """G1: the human render's skin micro-structure, sheen, strands and droplets. A head at portrait distance under a
    hard light: with skin_detail the cheek holds several times the fine texture it holds without, the face has glints,
    the hair is coherent strands, and droplets add bright glints with darker rims. Deterministic (seeded)."""
    sys.path.insert(0, HERE)
    import scene as sc, eyes
    ok = True
    try:
        def head(extra):
            o = dict({"type": "person", "id": "man", "age": 45, "sex": "male", "pos": [0, 1.62, 0], "anchor": "head",
                      "hair": {"style": "short", "color": "#4a3a2e"}}, **extra)
            S = sc.Scene({"camera": {"frame": {"on": "man.head", "fill": 0.82, "from": [0.35, 0.05, 1]}},
                          "sun": {"azimuth": 62, "elevation": 22, "intensity": 2.0, "softness": 60}, "ambient": {"intensity": 0.1},
                          "ground": {"enabled": False}, "fog": {"density": 0}, "objects": [o]})
            a = S.render(450, 600)
            mk, ent = S.element_masks((450, 600))
            return eyes.lightness(a.astype(np.float32) / 255)[0], mk, next(e for e in ent if e["key"] == "man.face")["px_per_subject_mm"]
        L0, mk, ppm = head({"skin_detail": 0, "strands": False})
        L1, _, _ = head({})
        face = mk["man.face"]
        b0 = eyes.band_energy(L0, ppm, face)[0.5]
        b1 = eyes.band_energy(L1, ppm, face)[0.5]
        assert b1 > 1.25 * b0, (b0, b1)
        hair = mk["man.hair"]
        from scipy.ndimage import binary_erosion
        hm = binary_erosion(hair, iterations=4)
        c1 = eyes.coherence(L1, ppm, hm)
        h0, h1 = eyes.band_energy(L0, ppm, hm)[0.5], eyes.band_energy(L1, ppm, hm)[0.5]
        assert c1 >= 0.5 and h1 > 1.5 * h0, (c1, h0, h1)          # strands: coherent, with strand-scale texture
        L2, _, _ = head({"droplets": {"count": 40, "size_mm": [2, 4], "on": ["face"]}})
        s1 = eyes.specular_blobs(L1, ppm, face)["specular_count"]
        s2 = eyes.specular_blobs(L2, ppm, face)["specular_count"]
        assert s2 > s1, (s1, s2)
        print(f"photoreal reference (G1): ok (face texture at 0.5 mm {b0:.2f} -> {b1:.2f} L*, hair texture at 0.5 mm {h0:.2f} -> {h1:.2f} L* (coherence {c1:.2f}), "
              f"glints {s1} -> {s2} with droplets)")
    except Exception as e:
        ok = False
        print(f"photoreal reference (G1): FAILED {e!r}")
    return ok


EXTRA = {"fine": fine_measures, "darks": darks_first, "camera": portrait_camera, "render": photoreal_reference}


if __name__ == "__main__":
    # python3 test_v8.py [--only medium1,medium2] [--tests fine,...]
    #   --only skips the v7 regression; --tests runs only the named extra tests (and nothing else)
    if "--tests" in sys.argv:
        names = sys.argv[sys.argv.index("--tests") + 1].split(",")
        res = [EXTRA[n]() for n in names]
        print("PASS" if all(res) else "FAIL")
        sys.exit(0 if all(res) else 1)
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    r1 = oil_matches_v7() if not only else True
    r2 = every_medium_runs(only)
    r3 = v8_intentions(only)
    r4 = detail_pass(only)
    r5 = all(t() for t in EXTRA.values()) if not only else True
    print("PASS" if (r1 and r2 and r3 and r4 and r5) else "FAIL")
    sys.exit(0 if (r1 and r2 and r3 and r4 and r5) else 1)
