# Engine conventions

Moved from AGENTS.md. Back to the router: [AGENTS.md](../../AGENTS.md). Where each module lives: [repo-map.md](repo-map.md).

## Rules
- **The current studio is `studio/v8/`.** Older studios (v0–v7) are records; don't change them.
- **`python3 studio/v8/test_v8.py` must pass after every change** (from `studio/v8/`; `--only a,b` runs a subset). It includes the v7 regression: `oil-v7` must reproduce v7 bit for bit, so keep new behaviour out of that path.
- **Every number rests on research or measurement** (calibration reports in `docs/calibration/`, data in `docs/media-data.md`, `studio/pigments.json`, `studio/calibration_refs.json`). Mark values tuned by eye as such, in the code and in the medium's calibration report.
- **Keep the painter's interface in sync:** `docs/MANUAL.md` (commands, intentions, views, report, finishing) and `docs/manual/<medium>.md`. They are all a painter sees.
- **Engine edits while a painting runs** must be additive and atomic (temp file plus rename). Painters work on copies in their work dirs, which `tools/make_brief.py` makes.
- **Dependencies:** `numpy scipy pillow`, plus `rsvg-convert` (librsvg) for SVG schemas and `ffmpeg` for time-lapses. People in scenes use MakeHuman's CC0 mesh: run `python3 tools/fetch_human.py` once per machine (it caches about 6 MB in `~/.cache/teodor/human/`); without it, `person` falls back to the primitive rig. Licences: `studio/assets/LICENSES.md`.
- **Canvas state** lives next to the studio as `{CANVAS}_*.npy` plus `{CANVAS}_meta.json`; the `CANVAS` env var picks a named canvas (default `main`). Every command saves a frame to `{CANVAS}_frames/` for the time-lapse.

## Adding a medium (an instrument)
A medium is a module in `studio/v8/media/` with a `Medium` subclass (`media/base.py` documents the interface; `media/oil.py` is the pattern). It registers itself. It keeps `cv.col` as the apparent colour and its own state in declared arrays. It gives `tools`, `supports` and `finishes`, plus:
- `make_tool`: a tool whose `dab` the core calls along each stroke, with pressure, speed and the felt state;
- `glaze`, `episode_end`, `dry`, `render` and `finish`.

Shared physics is in `base.py` (`kmix`, `pigment`/`km_layer` for Kubelka-Munk films) and `spectral.py` (spectral two-constant mixing, used by oil, gouache and tempera; `palette_for(medium)` gives a medium its own white and binder factor on S). For each new medium:
1. Calibrate it against measured marks in public-domain museum images (`tools/calibrate_media.py`) and write a report to `docs/calibration/`.
2. Check it with `gallery.py` and save the mark sheet to `docs/gallery/`.
3. Add it to `test_v8.py`.
4. Document it in `docs/manual/<medium>.md`, `studio/media.json` and the media table in `docs/MANUAL.md`.

## Adding a style
Follow `docs/styles/README.md`. The research batches write to `studio/styles.parts/`, and the merged result goes into `studio/styles.json`. Measured targets come from `tools/measure_targets.py` (Met and Cleveland open-access works) and go into `studio/targets.parts/`, then `targets.json`.

## Core internals (from v6, still the base)
- **The motor model:** `Felt` + `gesture_path` + `play`. A minimum-jerk speed profile drives dab spacing, pressure and width; there's a landing ramp and a lift taper. Tension adds jagged control points and tremor; negative valence switches from Catmull-Rom curves to angular polylines; care reduces scatter and adds landing hesitation.
- **`do_match`:** Hertzmann-style painterly rendering against the schema. Strokes start near the points of greatest error, follow the schema's form, and stop when the colour diverges.
- **The v8 hand (2026-11-26):** `match`, `free`, `strokes`, `model` and `blend` run `play_v8` (articulation profiles along the stroke), `Drift` (correlated variation across a passage), `FormField` (stroke direction) and size by focus and role; oil-v7 is routed to the frozen `*_v7` functions so it stays bit-identical. Every intention gets a layer role (`infer_role`), recorded per pixel in `{CANVAS}_roles.npy` and per 8 px cell in `{CANVAS}_rolefirst.npy`. Media hooks: `revise`, `revision_tools`, `glaze_role`, `first_role`, `finish_check`, `hand_defaults` (defaults merged under an intention, e.g. ink's line tools take the plain stroke at their calibrated size) and a tool's `.wave` (0 opts out of the core's pressure wave) (`media/base.py`); oil reads `_load_mul` and `deplete_mul`.
- **Performance (2 vCPU):** a full-canvas match with a 60–90 brush takes ~17 s, a 24–40 brush ~8 s, small brushes in regions 1–6 s. Spectral oil mixing is about 1.7× slower.

## History of fixes worth knowing (v6 tuning)
- Impasto looked like bubbles → smaller height deposit, gentler raking light.
- Blocky grid from matching → jittered start points, a minimum stroke length, a ceil-padded grid.
- Strokes faded after ~25% of their length → pickup and depletion are per distance, not per dab.
- Felt states looked identical → stronger tremor, jagged control points for tension, speed-driven dry brush.
