# AGENTS.md: guide for agents continuing this project

## What this project is
An experiment in **emotion-driven painting by AI agents**. A painter agent ("Teodor Lisk") is given a hidden emotion, paints with a simulated oil-paint studio in a human-like perceive → feel → act loop, and a human tries to guess the emotion from the finished painting. The aim is to make the process as analogous as possible to how human painters work (see `docs/research.md`), and the output as close to professional quality as possible.

Roles:
- **Human (Robert Ontiu):** directs the experiment and guesses the emotions.
- **Orchestrator agent:** builds and tunes the studio, draws the hidden emotion, writes the painter brief, launches the painter as a sub-agent, and reveals results only after the human guesses.
- **Painter agent:** the persona that paints. It never sees the human, and never writes the emotion.

## Repository map
```
studio/
  v0-by-hand/paint.py     cairo bristle brush; the orchestrator painted round 0 itself, one gesture at a time
  v1-elias/paint.py       same brush, used by the first painter agent
  v2/studio.py            numpy wet-paint engine, mind/hand split, brush types, views
  v3/studio.py            v2 + "clip" (marks stay inside a region), used for rounds 3 and 4
  v4/studio.py            identical engine to v3 (copied per round)
  v5-levels/studio.py     NCM-style parallel coarse-to-fine levels, layer snapshots
  v6/studio.py            CURRENT: research-informed studio (see below)
rounds/NN-title/          painting.jpg, journal.md, intentions/levels logs, sketches, layers
docs/experiments.md       round-by-round log: setup, emotion, guess, lessons
docs/research.md          the research behind v6 and the known gaps
docs/prompts/             exact painter briefs (v6 in full)
```

## The v6 studio (current)
Single file, `studio/v6/studio.py`; dependencies: `numpy scipy pillow`, plus `rsvg-convert` (librsvg) for SVG schemas and `ffmpeg` for time-lapses. State lives next to the script as `{CANVAS}_col.npy`, `_wet.npy`, `_ht.npy`, `_ref.npy` (float16); `CANVAS` env var selects a named canvas (default `main`).

Commands: `new`, `ref <svg|png>`, `transfer`, `act '<episode json>'`, `dry`, `look full|thumb|gray|crop|ref|diff|compare`, `timelapse`. The full interface spec is in `docs/prompts/v6-painter-brief.md`.

Key internals:
- `kmix`: per-channel Kubelka–Munk mixing blended 58/42 with linear (pure single-constant KM makes tints with white too dark).
- `Brush.dab`: one stamp. Bristle mask; wet pickup scaled by distance travelled (scaling it per dab caused self-contamination; see the history below); paint depletes by distance (`size*42*load` px per full load); dry-brush breaks come from low paint **or** speed (`speedfx`) against the canvas tooth texture.
- `Felt` + `gesture_path` + `play`: the motor model. A minimum-jerk speed profile drives dab spacing, pressure and width; there's a landing ramp and a lift taper. Tension adds jagged control points and tremor; negative valence switches from Catmull-Rom curves to angular polylines; care reduces scatter and adds landing hesitation.
- `do_match`: Hertzmann-style painterly rendering against the schema. A grid at brush scale, error = |canvas − blurred schema|, strokes start near max-error points, follow perpendicular to the schema's luminance gradient, and stop when the color diverges (after a minimum of 2 steps).
- `record`: every command saves a frame to `{CANVAS}_frames/` for the time-lapse.

Performance (2 vCPU): a full-canvas match with a 60–90 brush takes ~17 s, a 24–40 brush ~8 s, small brushes in regions 1–6 s.

## How to run a round

**Current protocol: phase-based, see `docs/orchestration.md`.** Each phase is a fresh painter sub-agent with all state on disk (`handoff.md`, `critique_N.md`). Don't pause and resume one long painter session: sub-agents could not be resumed after a checkpoint, and painters can't spawn critics themselves.

Older single-session flow:
1. Copy `studio/v6/studio.py` to a work dir (the brief assumes `/home/claude/v6/`).
2. Draw the emotion: `python3 -c "import random; ..."` from the lists in `docs/experiments.md`; write the chosen line to `.secret`. Do **not** print it.
3. Launch a sub-agent with `docs/prompts/v6-painter-brief.md` (general-purpose agent).
4. Show the human only `main_full.png` and the title, plus the 8 options. Wait for the guess.
5. Reveal: read `.secret`, show the journal highlights, schema versions and time-lapse. Then add the round to `rounds/` and `docs/experiments.md`.

## Conventions and rules
- **Never commit or reveal `.secret`, and never reveal an emotion before the human has guessed** (`.gitignore` excludes it). The answer for round 5 is still unrevealed.
- Painter agents must not name the emotion. They've slipped before (near-synonyms; "stranger" contains "anger"), so grep the journal before revealing.
- Titles: the brief forbids emotion-pointing titles (*Vent* was too revealing).
- Keep persona names fictional. "Elias Varga" collided with a real painter (Elias Vargas), and "Teodor Lisk" is the current persona.

## History of fixes worth knowing (v6 tuning)
- Impasto looked like bubbles → smaller height deposit (`m**1.5 * 0.045`), gentler raking light.
- Blocky grid from matching → jittered start points, minimum stroke length, ceil-padded grid so edges are covered.
- Strokes faded after ~25% of their length → pickup was per dab (self-contamination with the dark edge) and depletion was per dab; both are now per distance.
- Felt states looked identical → stronger tremor, jagged control-point insertion for tension, speed-driven dry-brush.

## Known hiccups (fixed)
- Round 7: the in-painting critic could not run (no Agent tool inside the painter session, and `claude -p` was unauthenticated). The orchestrator now runs critics.
- Round 8: the painter stopped at checkpoint 2 and could not be resumed. Phases now replace pause/resume.
- `scene` version numbers skipped (v1, v3, …) because the counter counted .json and .png files. It now counts .png only.

## Open directions
- A learned motor vocabulary instead of parametric strokes; fatigue and session-level physiology.
- Separate K and S pigments (true two-constant Kubelka–Munk, or Mixbox).
- A test panel larger than one human; harder pairs (longing vs. tenderness, grief vs. serenity).
- A painter that keeps memory across paintings (style development).
