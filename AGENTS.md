# AGENTS.md: guide for agents continuing this project

## What this project is
An experiment in whether an AI can **paint the way a human painter does**. A painter agent ("Teodor") paints a feeling with a simulated oil-paint studio, in a human-like perceive → feel → act loop: he builds a drawing (a 3D blockout), paints over it in many short look-and-correct episodes, and gets a fresh critic's reading between stages. The aim is a process as analogous as possible to how human painters work (see `docs/research.md`), and output as close to professional quality as possible.

Roles:
- **Person:** asks for a painting, giving a theme or a feeling (and optionally a style).
- **Orchestrator agent (you):** sets up the studio, writes the painter's brief, runs the painter's phases and the critics, and shows the result.
- **Painter agent:** Teodor, the persona that paints. It never talks to the person directly.

## Quick start: someone asked you to paint

Run one painting with the **current studio, `studio/v7/`**, the brief in `docs/prompts/painter-brief.md`, and the phase protocol in `docs/orchestration.md`:

1. Make a work dir outside the repo (for example `../teodor-work/01/`). Copy `studio/v7/*.py` into it (`studio.py`, `scene.py`, `signature.py`). Install `numpy scipy pillow`, `ffmpeg` and `librsvg` (`rsvg-convert`) if they're missing.
2. Copy `docs/habits.md` to the work dir and make `past_work.jpg` with `studio/contact_sheet.py` (see `docs/orchestration.md`). Copy the brief to `brief.md` in the work dir and fill in its placeholders (the comment at its top explains them): the work dir path, the commission, and the feeling paragraph. Given a **theme**, Teodor chooses his own feeling inside it; given a **feeling**, he paints that one.
3. Run the three phases as fresh general-purpose sub-agents, each told to read `brief.md` and do its phase, with a fresh critic between them. The painter's last acts are `studio.py sign` and `studio.py timelapse`.
4. Show the person the final painting and its title, then Teodor's feeling, the visitor critic's reading, journal highlights and the time-lapse. If they want to keep it, add it to `rounds/NN-title/` like the existing rounds and to `site/` (see `site/README.md`).

## Repository map
```
studio/
  v0-by-hand/paint.py     cairo bristle brush; the orchestrator painted round 0 itself, one gesture at a time
  v1-elias/paint.py       same brush, used by the first painter agent
  v2/studio.py            numpy wet-paint engine, mind/hand split, brush types, views
  v3/studio.py            v2 + "clip" (marks stay inside a region), used for rounds 3 and 4
  v4/studio.py            identical engine to v3 (copied per round)
  v5-levels/studio.py     NCM-style parallel coarse-to-fine levels, layer snapshots
  v6/studio.py            research-informed studio (see below)
  v7/                     CURRENT: v6 plus 3D blockouts (scene.py), the liner brush, adaptive matching and signing
  signature.py            Teodor's signature, for any image
rounds/NN-title/          painting.jpg, journal.md, intentions/levels logs, sketches, layers
docs/experiments.md       round-by-round history of the experiment and what each painting taught
docs/orchestration.md     how a painting runs: phases, handoffs, critics
docs/habits.md            Teodor's recurring habits, to break on purpose
docs/research.md          the research behind v6 and the known gaps
docs/prompts/painter-brief.md   the current painter brief (template)
docs/prompts/v6–v9        historical briefs from earlier rounds, kept as records
```

## The v6 studio (the engine v7 builds on)
Single file, `studio/v6/studio.py`; dependencies: `numpy scipy pillow`, plus `rsvg-convert` (librsvg) for SVG schemas and `ffmpeg` for time-lapses. State lives next to the script as `{CANVAS}_col.npy`, `_wet.npy`, `_ht.npy`, `_ref.npy` (float16); `CANVAS` env var selects a named canvas (default `main`).

Commands: `new`, `ref <svg|png>`, `transfer`, `act '<episode json>'`, `dry`, `look full|thumb|gray|crop|ref|diff|compare`, `timelapse`. The full interface spec is in `docs/prompts/v6-painter-brief.md`.

Key internals:
- `kmix`: per-channel Kubelka–Munk mixing blended 58/42 with linear (pure single-constant KM makes tints with white too dark).
- `Brush.dab`: one stamp. Bristle mask; wet pickup scaled by distance travelled (scaling it per dab caused self-contamination; see the history below); paint depletes by distance (`size*42*load` px per full load); dry-brush breaks come from low paint **or** speed (`speedfx`) against the canvas tooth texture.
- `Felt` + `gesture_path` + `play`: the motor model. A minimum-jerk speed profile drives dab spacing, pressure and width; there's a landing ramp and a lift taper. Tension adds jagged control points and tremor; negative valence switches from Catmull-Rom curves to angular polylines; care reduces scatter and adds landing hesitation.
- `do_match`: Hertzmann-style painterly rendering against the schema. A grid at brush scale, error = |canvas − blurred schema|, strokes start near max-error points, follow perpendicular to the schema's luminance gradient, and stop when the color diverges (after a minimum of 2 steps).
- `record`: every command saves a frame to `{CANVAS}_frames/` for the time-lapse.

Performance (2 vCPU): a full-canvas match with a 60–90 brush takes ~17 s, a 24–40 brush ~8 s, small brushes in regions 1–6 s.

## The signature
Every painting is signed "Teodor" (`studio/signature.py`): a handwritten mark with an underline flourish, laid as tapered brush strokes in the calmer bottom corner, colored from the paint under it. In the studio it's the painter's last act (`studio.py sign`). To sign any image: `python3 studio/signature.py in.png out.png`.

## How to run a painting
Phase-based, see `docs/orchestration.md`. Each phase is a fresh painter sub-agent with all state on disk (`feeling.md`, `journal.md`, `handoff.md`, `critique_N.md`). Don't pause and resume one long painter session: sub-agents could not be resumed after a checkpoint, and painters can't spawn critics themselves.

## Operating notes (for a new session)
- **Running a painting:** `docs/orchestration.md` has the phase prompts, the critic prompt, how to recover an interrupted phase, and the publishing checklist (round folder, experiments log, site, gallery, commit).
- **Never resume a painter sub-agent:** always start a fresh session that reads the files. Run critics yourself, because painters can't spawn agents.
- **Re-signing:** `python3 studio/signature.py in.png out.png` signs any image "Teodor". To re-sign, start from an unsigned image.
- **Site build without network access:** the build fetches Google Fonts. In a sandbox without it, mock the font: put `module.exports = new Proxy({}, { get: (_, url) => typeof url === "string" ? "@font-face { font-family: 'Cormorant Garamond'; font-style: normal; font-weight: 500; src: local('Georgia'); }" : undefined, has: () => true });` in `/tmp/fontmock.cjs`, then run `NEXT_FONT_GOOGLE_MOCKED_RESPONSES=/tmp/fontmock.cjs npx next build --webpack` in `site/` (Turbopack ignores the mock). Delete `node_modules`, `.next` and `out` afterwards. Vercel builds normally.
- **Images for chat:** the studio's PNGs can be rejected by chat uploads; send a JPEG export instead.
- **Commits:** author "Robert Ontiu <robertontiu@users.noreply.github.com>", pushed straight to `main`.
- **The person:** Robert Ontiu directs the project. What he has decided so far:
  - The painter is called "Teodor" everywhere.
  - Every painting is signed.
  - The guessing game from the early rounds is retired: feelings are shared openly with the painting.
  - Public text should be plain and non-technical, with the research cited.
  - The code is MIT; Teodor's paintings are CC BY 4.0.

## Keep it fresh
Teodor drifts into one look: a lone figure from behind, a lit doorway in a dark warm room, a hushed bittersweet mood. Every painting should be a departure. `docs/habits.md` lists the habits; the brief makes him study his past work, research painters he hasn't used, and break at least three habits on purpose. The orchestrator checks the first checkpoint against the contact sheet and updates `docs/habits.md` after every painting. If the person asks for a specific style or mood, that request wins over any habit.

## Conventions and rules
- Titles are a painter's titles, not labels for the feeling.
- Critics see only the canvas and the commission, never the feeling, journal or handoff.
- The painter persona is called **Teodor** (first name only). Until round 10 it was "Teodor Lisk" and signed "T. Lisk"; the name was shortened on Robert's request and every painting was re-signed "Teodor".
- Keep persona names fictional. "Elias Varga" collided with a real painter (Elias Vargas), and "Teodor" is the current persona.

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
- More viewers than one person and one critic, to see how widely a painting's feeling is shared.
- A painter that keeps memory across paintings (style development).
