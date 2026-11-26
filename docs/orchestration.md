# Orchestrating a painting (phase-based protocol)

Long painter sessions can't be paused and resumed reliably: a sub-agent that stops at a checkpoint may not be resumable ("transcript missing"), and a painter sub-agent can't spawn its own critic. So a painting is made in **phases**, each a fresh painter session, with all state on disk.

## The owner's standing rules
Set by Robert; they apply until he changes them.
1. **The artist is called Teodor**, everywhere; every painting is signed.
2. **It must be a painting:** every mark goes through the studio's tools; nothing pasted, composited, traced or flat-filled (AGENTS.md).
3. **Styles and movements, never authors:** only currents, schools and techniques are versioned. A request for a specific artist gets temporary research and a configuration in `studio/styles.local/` (gitignored), used for that painting only. No likeness of real people.
4. **Style settings come from research, not guesses:** every value in a style entry cites a source or is marked as a judgement call. A current that isn't in `studio/styles.json` is researched first (`docs/styles/README.md`), and measured (`tools/measure_targets.py`: add a rule) where public-domain works exist.
5. **Every painting is a departure:** `docs/habits.md` is read before every painting and updated after it; at least three habits are broken on purpose.
6. **Research beats suggestions; Robert is the eye test.** His notes are symptoms to diagnose; where the research disagrees, follow the research and tell him why.
7. **Personal details stay out of the repo.** Anything personal Robert shares is context for shaping a brief, never content: not in briefs, journals, feeling files, docs, commits or the site.
8. **Feelings are published openly** with each painting.
9. **Publish without asking** when a painting is finished (below); show Robert each checkpoint as it happens.
10. **Commit as you go**, after every finished piece of work, so an interrupted session loses at most the piece in progress.
11. **Utensils rest on research and real data** (Robert, 2026-11-25): media, tools, pigments and supports are built from published measurements and calibrated against measured statistics of real marks; every value tuned by eye is marked as such until it is calibrated.
12. **It's an experiment:** report misses honestly, in the experiments log and on the site.

## Starting a painting
1. If the commission names a current that isn't researched, research it first: its doc in `docs/styles/<id>.md`, its entry in `studio/styles.json`, and a measuring rule in `tools/measure_targets.py` (then `python3 tools/measure_targets.py measure <id>`). If it names an artist, research the artist's practice into `studio/styles.local/<id>.json` (gitignored) and say in the brief that it's a temporary configuration.
2. If the current's medium isn't in the studio yet, build it first (a medium module under `studio/v8/media/`, its mark sheet in `docs/gallery/`, its page in `docs/manual/`, `test_v8.py` passing) or choose the closest medium that exists and say so to Robert.
3. Make the work dir and the brief in one step:
   ```
   python3 tools/make_brief.py ../teodor-work/NN --commission "a public exhibition on a THEME. The theme is: ..." (--theme | --feeling "...") [--style ID|free] [--medium M] [--support S]
   ```
   It copies the studio (v8, with its media), habits, a fresh contact sheet of past work, the styles and the targets, and fills in the brief.
4. Run the phases (below). Phase 1 stops after planning so the subjects can be researched before Teodor draws ("Subjects before drawing").

## Subjects before drawing
Teodor's subject library is layered (`docs/subjects/README.md`): layer 1 is how a subject really is (a face, water, a cat), and layer 2 is how a style changes it. The library starts thin and grows with every painting:
1. Phase 1 ends its planning (feeling, research, thumbnails, colour studies, the chosen composition) by writing `subjects.json` in the work dir: every subject in the picture, with a note on how it appears. The painter replies `PLAN DONE`.
2. The orchestrator runs `python3 tools/subject_gaps.py <WORKDIR>`. For each gap it runs the prompts in `docs/prompts/subject-research.md`: layer 1 first, then layer 2 for the commission's style. Gaps that write different files run in parallel. Then it merges `studio/subjects.parts/` into `studio/subjects.json` (`python3 tools/merge_subjects.py`) and commits the new pages.
3. Phase 1 continues in a fresh session ("PHASE 1, continued after planning"). Teodor reads layer 1 and layer 2 for every subject in his list, then draws: schema, tone, transfer, block-in.
A subject added later (in phase 2 or 3, say a dog walks into the picture) goes through the same check before it is painted.

## Files in the round's studio directory
| File | Written by | Purpose |
|---|---|---|
| `brief.md` | orchestrator | the painter's full brief, from `docs/prompts/painter-brief.md` (persona, commission, studio, process) |
| `feeling.md` | painter (phase 1) | the feeling the painting is about, in Teodor's words |
| `journal.md` | painter | one line per episode, including felt state |
| `handoff.md` | painter (end of every phase) | where the painting stands, what each element is meant to do, open problems, the plan for the next phase |
| `critique_N.md` | orchestrator | a fresh critic's reading of `crit_N.png`, verbatim |
| `crit_N.png`, `final.png` | painter | the checkpoint image and the final image |
| canvas state (`main_*.npy`, scene files, frames) | studio | survives across phases |

## Phases
1. **Phase 1, conception → block-in** (~20 episodes). Settle the feeling and write `feeling.md`, make idea blockouts, the final blockout, tone, transfer, block-in. End: copy `main_full.png` to `crit_1.png`, write `handoff.md`, reply `PHASE 1 DONE`.
2. **Orchestrator:** run a fresh critic on `crit_1.png` (it knows only the commission), save the reading verbatim to `critique_1.md`.
3. **Phase 2, development** (~30–40 episodes). A new painter session reads `brief.md`, `feeling.md`, `journal.md`, `handoff.md` and `critique_1.md`, then looks at the canvas. End: `crit_2.png`, updated `handoff.md`, reply `PHASE 2 DONE`.
4. **Orchestrator:** a fresh critic on `crit_2.png` → `critique_2.md`.
5. **Phase 3, finalization** (~15–25 episodes). A new session reads the same files plus `critique_2.md`, finishes, **signs** (`studio.py sign`), runs `timelapse`, writes `final.png`, and replies with `FINISHED`, the title and its notes.
6. **Orchestrator:** a last fresh critic on `final.png`, given `past_work.jpg` too (question 5 below) (a visitor's first reading). Show the person the painting and its title, then Teodor's feeling, the visitor's reading, journal highlights and the time-lapse.

Use a fresh critic every time, so no critic sees an earlier state. Never give a critic `feeling.md`, the journal or the handoff: its value is an honest first reading of the canvas alone.

## The critic prompt
Run each critic as a fresh general-purpose sub-agent:

> You are a thoughtful museum visitor and an experienced painting critic. Look at the image `<path>/crit_N.png` (use the Read tool). It was painted for this commission: "<commission>". 1) In a few words, what do you FEEL looking at it, in the first three seconds? 2) What in the painting makes you feel that? 3) Its weaknesses as a painting, frankly: composition, values, edges, drawing, gesture, color, finish. 4) The one change that would most improve it. Be concrete and brief.

For the final visitor reading, also give the critic `past_work.jpg` and add: 5) Compared with the painter's earlier work on the contact sheet, is this a new departure or more of the same? Name what it repeats.

## Before phase 1: keep Teodor from repeating himself
In the work dir, besides `brief.md`:
- `cp docs/habits.md <WORKDIR>/habits.md`
- `python3 studio/contact_sheet.py rounds <WORKDIR>/past_work.jpg`

The brief tells Teodor to read both, research painters he hasn't drawn on, and break at least three habits. When you check `crit_1.png`, compare it with the contact sheet yourself. If it's another sibling of the old work (a lone figure from behind, a lit doorway, a warm dark room), say so in the studio manager's note under critique 1, naming the habits it repeats.

## Phase prompts (send each to a fresh general-purpose sub-agent)
Run the phases one after another, waiting for each to finish: the next step depends on its files. A phase takes roughly 5–30 minutes.

- **Phase 1, planning:** "Read `<WORKDIR>/brief.md` in full and become Teodor, as it describes. This is PHASE 1, PLANNING. Follow the brief exactly, and end with PLAN DONE as it says."
- **Phase 1, continued:** "Read `<WORKDIR>/brief.md` in full and become Teodor, as it describes. This is PHASE 1, continued after planning. Read feeling.md, journal.md and subjects.json, then the subject pages the brief names, then draw. Continue from the journal's last episode and end phase 1 as the brief says."
- **Phase 2:** "Read `<WORKDIR>/brief.md` in full and become Teodor, as it describes. This is PHASE 2 (development). Begin by reading `feeling.md`, `journal.md`, `handoff.md` and `critique_1.md`, then look at the canvas (look full, thumb, gray). Continue from episode N+1 (the journal's last number) and end phase 2 as the brief says."
- **Phase 3:** the same, "PHASE 3 (finalization)", reading `critique_2.md` too. Add: "Weigh the critique as a painter: take what is true about the craft, and judge its reading against your own feeling. Finish exactly as the brief's last paragraph says (sign, time-lapse, `final.png`, reply FINISHED with the title)."

**If a phase is interrupted** (the person stops it, or it dies), don't try to resume that session. Everything is on disk: start a fresh session for the same phase, tell it the phase was resumed after episode N, and have it continue from N+1. Round 11's phase 2 was recovered this way after stopping at episode 46.

## Checking a checkpoint (the orchestrator, after each phase)
- Read `feeling.md` (the feeling, the nearest wrong feelings and looks), look at the checkpoint, and run `python3 <WORKDIR>/studio.py report` there.
- In the studio manager's note under the critique: say which of the nearest wrong feelings the critic read, if any; name any report flag and any measure far outside the current's target; name repeated habits (compare with `past_work.jpg`); and push back on critic advice that would drag the painting into an old habit or out of its current. Never write the feeling itself into the note.
- At phase 1, if Robert is around, offer him the thumbnails and colour studies (the painter saves them as images) before the painter commits; his pick is a strong signal.

## Critic readings
Save each reading verbatim to `critique_N.md` with a header such as `# Critique 1 (a fresh critic; knew only the commission "…"; read crit_1.png)`. The final reading of `final.png` goes to `visitor.md`. If the reading is pulled toward the commission's title rather than the painting, the orchestrator may add one line under it ("Studio manager's note: …") pointing the painter back to his own feeling; never add the feeling itself.

## Publishing a finished painting
1. **Show the person** the final image (export PNGs to JPEG before sending; some chat uploads reject the studio's PNGs), the title, Teodor's feeling, the visitor's reading, and a few journal lines.
2. **Round folder** `rounds/NN-title-slug/`, like round 9:
   - `painting.jpg`: `final.png` resized to 900×1200, JPEG quality ~90 (already signed)
   - `feeling.md`: Teodor's feeling in his words, plus the commission
   - `journal.md`, `handoff.md`, `episodes.jsonl` (copy of `main_log.jsonl`), `timelapse.mp4`
   - `critiques/`: `crit_N.jpg` (600×800), `critique_N.md`, `visitor.md`
   - `scenes/` (scene JSON and overlay SVGs) or `schemas/` (schema SVGs for abstract work)
3. **`docs/experiments.md`:** a section "## Round NN: *Title* (Teodor, v7, <model>; theme: …)" with setup, run (episodes, scene/schema versions), feeling, the person's reaction, critics' readings and lessons.
4. **Habits:** update `docs/habits.md`: add any new habit this painting showed, and note under "Broken so far" what it broke.
5. **Site:** `site/public/paintings/rNN.jpg` (the same 900×1200 JPEG) and an entry in `site/app/works.ts`, with `model` set if the painter was not Opus 5.5 (the site shows the model next to the title). That gives it a page at `/rNN/` with its share preview, and a sitemap entry.
6. **Commit and push** everything above in one commit. A GitHub Action deploys the site (teodor.robertontiu.com) about 5 minutes after the last push that touched `site/`; there is nothing else to update. Keep site changes in as few pushes as you can.

## Comparing models
To compare models, run the same commission in parallel: one work dir per model (for example `v14/` and `v14f/`), the same brief with its paths changed, and the painter sub-agents launched with the `model` parameter. Each painting gets its own round folder (`14-…` and `14b-…`), its own site id (`r14`, `r14b`) and its `model` in `works.ts`. Round folders record the model in `feeling.md`. Rounds 0–13 were all painted by Opus 5.5.
