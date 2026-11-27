"""The 2x test head: an invented head (MakeHuman CC0) at about twice life on a 48 x 64 cm sheet of vellum, drawn by
script through the studio's own tools, then measured against its reference and the close-up ruler
(docs/research/hyperrealism-gaps.md, "The final acceptance test" and part 2).

  python3 tools/analysis/test_head.py <workdir> [--from STAGE] [--to STAGE] [--scene docs/gallery/test_head_2x.json]

Stages (each a few studio commands; --from resumes on the canvas the earlier stages left):
  setup    copy the studio, new sheet, `scene` (the Cycles reference), `toneref`, `report ref`, transfer
  indent   stylus glints and catchlights (before any tone)
  darks    three darks-first cycles in charcoal on the schema's darks, workable fixative between
  tone     continuous graphite tone (hatch "target": "schema"), lead by value, kept off the charcoal
  blend    blending by part: face, hair, neck, clothes, each with its own brush
  correct  two rounds: tone where too light, kneaded and battery lifts where too dark, smaller blends
  fine     workable fixative, then marks: strands, pores, lashes, edges; the darkest accents
  details  4x details over the eyes and the mouth, drawn with the same recipe, closed and related back
  finish   clean, sign, report
This script is a test of the engine, not a painting: no feeling, no critic. Everything it lays goes through the
studio's tools (AGENTS.md rule 2)."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
STUDIO = os.path.join(ROOT, "studio", "v8")
FELT = {"arousal": 0.15, "tension": 0.1, "valence": 0.3, "care": 0.95}
STAGES = ["setup", "indent", "darks", "tone", "blend", "correct", "fine", "details", "finish"]


class Run:
    def __init__(self, wd):
        self.wd = wd
        self.log = open(os.path.join(wd, "test_head.log"), "a")

    def sh(self, *args, detail=False):
        cmd = [sys.executable, os.path.join(self.wd, "studio.py")] + [str(a) for a in args] + (["--detail"] if detail else [])
        t = time.time()
        r = subprocess.run(cmd, cwd=self.wd, capture_output=True, text=True)
        dt = time.time() - t
        out = (r.stdout + r.stderr).strip()
        self.log.write(f"\n$ {' '.join(str(a) for a in args)}{' --detail' if detail else ''}  ({dt:.0f} s)\n{out[-4000:]}\n")
        self.log.flush()
        print(f"[{dt:5.0f} s] {' '.join(str(a) for a in args)[:110]}", flush=True)
        if r.returncode != 0:
            print(out[-3000:])
            raise SystemExit(f"studio command failed: {args[:2]}")
        return out

    def act(self, *intentions, detail=False):
        p = os.path.join(self.wd, "_ep.json")
        json.dump({"felt": FELT, "do": list(intentions)}, open(p, "w"))
        return self.sh("act", "@" + p, detail=detail)

    def finish(self, op, params=None, detail=False):
        return self.sh("finish", op, json.dumps(params or {}), detail=detail)


# regions (the scene's own element masks and the schema's values)
EL = lambda k, grow=0: {"type": "element", "key": f"person0.{k}", "grow": grow}
PERSON = EL("all", 2)
DARK = 0.30          # the schema's value (sRGB grey) under which the darks are laid in charcoal


def darks_region(within=None, below=DARK):
    r = {"type": "value", "below": below, "blur": 1.5}
    r["within"] = within or PERSON
    return r


def no_darks(region, below=DARK):
    return dict(region, minus={"type": "value", "below": below - 0.02, "blur": 1.5})


def stage_setup(R, scene):
    wd = R.wd
    for f in os.listdir(STUDIO):
        if f.endswith(".py") and f != "test_v8.py":
            shutil.copy(os.path.join(STUDIO, f), wd)
    shutil.copytree(os.path.join(STUDIO, "media"), os.path.join(wd, "media"), dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__"))
    for f in ("styles.json", "targets.json", "pigments.json"):
        shutil.copy(os.path.join(ROOT, "studio", f), wd)
    shutil.copy(scene, os.path.join(wd, "scene.json"))
    R.sh("new", "#f7f6f2", 2400, 3200, "--medium", "graphite", "--support", "vellum", "--style", "graphite-hyperrealism",
         "--px-per-mm", 5)
    R.sh("scene", "scene.json", "final")
    R.sh("toneref")
    R.sh("report", "ref")
    st = json.load(open(os.path.join(wd, "main_structure.json")))
    pu = st.get("pupils") or []
    if pu:
        lit = max(pu, key=lambda p: -p["x"])          # the eye nearer the light (the light is on the picture's left)
        R.sh("focus", int(lit["x"]), int(lit["y"]))
    R.sh("transfer", 0.22)


def stage_indent(R):
    # catchlights and glints indented before any tone, so later tone skips them (the manual's order)
    R.act({"type": "marks", "families": {"glints": {"region": EL("face"), "brush": "stylus", "count": 60}}})


def stage_darks(R):
    reg = darks_region()
    for cyc in range(3):
        R.act({"type": "hatch", "brush": "charcoal_powder", "target": "schema", "target_shift": -0.01,
               "angles": [20, 110], "size": 40, "spacing": 14, "pressure": 0.8, "region": reg, "clip": True,
               "colors": ["#111111"]},
              {"type": "hatch", "brush": "compressed_charcoal", "target": "schema", "target_shift": -0.01,
               "angles": [35, 125], "size": 8, "spacing": 3.5, "pressure": 0.85, "region": reg, "clip": True,
               "colors": ["#111111"]},
              {"type": "hatch", "brush": "brush", "value": 0, "layers": [1.0], "size": 18, "spacing": 6, "angle": 60,
               "cross": 60, "region": reg, "clip": True})
        R.finish("fixative", {"kind": "workable", "strength": 1, "region": darks_region(below=DARK + 0.04)})


TONE_PASSES = [
    # (lead, grade, region above value, size px, spacing px): darker leads where the schema is darker; each pass
    # works toward the schema's own value under it and stops there (target mode)
    ("mech_07", "4B", 0.0, 3.5, 3.0),
    ("mech_05", "2B", 0.40, 2.5, 2.6),
    ("mech_05", "HB", 0.55, 2.5, 2.6),
    ("mech_03", "2H", 0.70, 1.5, 2.2),
]


def tone_pass(R, region, angles, shift=-0.015, passes=TONE_PASSES, detail=False, k=1.0):
    for lead, grade, above, size, spacing in passes:
        reg = dict(no_darks(region))
        reg = {"type": "value", "above": above, "blur": 1.5, "within": reg} if above > 0 else reg
        R.act({"type": "hatch", "brush": lead, "grade": grade, "target": "schema", "target_shift": shift, "angles": angles,
               "size": size * k, "spacing": spacing * k, "pressure": 0.75, "region": reg, "clip": True,
               "colors": ["#222222"], "length": 90 * k}, detail=detail)


def stage_tone(R):
    tone_pass(R, PERSON, [15, 60, 105, 150])


BLENDS = [("face", 22, 7), ("head", 26, 8), ("neck", 30, 10), ("hair", 14, 5), ("drapery", 40, 13)]


def blend_parts(R, scale=1.0, detail=False):
    for part, size, sp in BLENDS:
        R.act({"type": "hatch", "brush": "brush", "value": 0, "layers": [1.0], "size": size * scale, "spacing": sp * scale,
               "angle": 25, "cross": 60, "region": no_darks(EL(part)), "clip": True}, detail=detail)


def stage_blend(R):
    blend_parts(R)


def stage_correct(R):
    for rnd, (thr, bs) in enumerate(((0.05, 0.8), (0.035, 0.6))):
        tone_pass(R, PERSON, [40 + 20 * rnd, 130 + 20 * rnd], shift=-0.01, passes=TONE_PASSES[1:])
        R.act({"type": "match", "brush": "kneaded", "seek": True, "faithful": 1, "threshold": thr, "size": [6, 14],
               "region": no_darks(PERSON), "clip": True, "max_strokes": 3000})
        blend_parts(R, bs)


def stage_fine(R):
    R.finish("fixative", {"kind": "workable", "strength": 1, "region": PERSON})
    R.act({"type": "marks", "families": {
        "strands": {"region": EL("hair"), "brush": "mech_03", "grade": "2B"},
        "pores": {"region": EL("face"), "count": 2500},
        "lashes": {"region": EL("face"), "count": 500},
        "edges": {"region": EL("all", 4), "count": 600}}})
    R.act({"type": "hatch", "brush": "compressed_charcoal", "target": "schema", "target_shift": -0.02, "angles": [45],
           "size": 5, "spacing": 3, "pressure": 0.9, "region": darks_region(below=0.22), "clip": True, "colors": ["#111111"]})


def stage_details(R):
    st = json.load(open(os.path.join(R.wd, "main_structure.json")))
    for p in st.get("pupils") or []:
        x, y = int(p["x"]) - 160, int(p["y"]) - 110
        R.sh("detail", "open", x, y, 320, 220, "--scale", 4)
        R.sh("scene", "scene.json", "final", detail=True)
        R.sh("toneref", detail=True)
        tone_pass(R, {"type": "canvas"}, [30, 120], shift=-0.01, passes=TONE_PASSES[1:], detail=True, k=4.0)
        R.act({"type": "hatch", "brush": "brush", "value": 0, "layers": [1.0], "size": 60, "spacing": 20, "angle": 25,
               "cross": 60}, detail=True)
        R.act({"type": "marks", "families": {"lashes": {"count": 160}, "edges": {"count": 200}, "glints": {"count": 6}}},
              detail=True)
        R.sh("detail", "close")


def stage_finish(R):
    R.finish("clean", {"margin": 30})
    R.sh("sign", "auto")
    R.sh("report")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("--from", dest="frm", default="setup")
    ap.add_argument("--to", default="finish")
    ap.add_argument("--scene", default=os.path.join(ROOT, "docs", "gallery", "test_head_2x.json"))
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    R = Run(os.path.abspath(a.workdir))
    i0, i1 = STAGES.index(a.frm), STAGES.index(a.to)
    t0 = time.time()
    for st in STAGES[i0:i1 + 1]:
        print(f"== {st}", flush=True)
        f = globals()["stage_" + st]
        f(R, a.scene) if st == "setup" else f(R)
        shutil.copy(os.path.join(R.wd, "main_render.png") if os.path.exists(os.path.join(R.wd, "main_render.png")) else os.devnull,
                    os.path.join(R.wd, f"after_{st}.png")) if os.path.exists(os.path.join(R.wd, "main_render.png")) else None
    print(f"done in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
