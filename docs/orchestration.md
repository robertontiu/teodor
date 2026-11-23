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
