# Orchestrating a painting (phase-based protocol)

Long painter sessions can't be paused and resumed reliably: a sub-agent that stops at a checkpoint may not be resumable ("transcript missing"), and a painter sub-agent can't spawn its own critic. So a painting is made in **phases**, each a fresh painter session, with all state on disk.

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
6. **Orchestrator:** a last fresh critic on `final.png` (a visitor's first reading). Show the person the painting and its title, then Teodor's feeling, the visitor's reading, journal highlights and the time-lapse.

Use a fresh critic every time, so no critic sees an earlier state. Never give a critic `feeling.md`, the journal or the handoff: its value is an honest first reading of the canvas alone.

## The critic prompt
Run each critic as a fresh general-purpose sub-agent:

> You are a thoughtful museum visitor and an experienced painting critic. Look at the image `<path>/crit_N.png` (use the Read tool). It was painted for this commission: "<commission>". 1) In a few words, what do you FEEL looking at it, in the first three seconds? 2) What in the painting makes you feel that? 3) Its weaknesses as a painting, frankly: composition, values, edges, drawing, gesture, color, finish. 4) The one change that would most improve it. Be concrete and brief.

## Phase prompts (send each to a fresh general-purpose sub-agent)
Run the phases one after another, waiting for each to finish: the next step depends on its files. A phase takes roughly 5–30 minutes.

- **Phase 1:** "Read `<WORKDIR>/brief.md` in full and become Teodor, as it describes. This is PHASE 1 (conception to block-in). Follow the brief exactly, and end phase 1 as it says."
- **Phase 2:** "Read `<WORKDIR>/brief.md` in full and become Teodor, as it describes. This is PHASE 2 (development). Begin by reading `feeling.md`, `journal.md`, `handoff.md` and `critique_1.md`, then look at the canvas (look full, thumb, gray). Continue from episode N+1 (the journal's last number) and end phase 2 as the brief says."
- **Phase 3:** the same, "PHASE 3 (finalization)", reading `critique_2.md` too. Add: "Weigh the critique as a painter: take what is true about the craft, and judge its reading against your own feeling. Finish exactly as the brief's last paragraph says (sign, time-lapse, `final.png`, reply FINISHED with the title)."

**If a phase is interrupted** (the person stops it, or it dies), don't try to resume that session. Everything is on disk: start a fresh session for the same phase, tell it the phase was resumed after episode N, and have it continue from N+1. Round 11's phase 2 was recovered this way after stopping at episode 46.

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
3. **`docs/experiments.md`:** a section "## Round NN: *Title* (Teodor, v7; theme: …)" with setup, run (episodes, scene/schema versions), feeling, the person's reaction, critics' readings and lessons.
4. **Site:** `site/public/paintings/rNN.jpg` (the same 900×1200 JPEG) and an entry in `site/app/works.ts`. That gives it a page at `/rNN/` with its share preview, and a sitemap entry.
5. **Gallery artifact** (only in Claude sessions that own it): the public multi-file artifact "Teodor: Paintings" (`index.html` + `img/rN.jpg`). Upload the image with `publish_files` (the file must sit under `/home/claude`, not `/tmp`), add its entry to the `works` list in `index.html` with `edit_version`, and pass `shared_live: "public"` and the artifact's title each time. The person has approved updating it whenever a painting is added.
6. **Commit and push** everything above in one commit.
