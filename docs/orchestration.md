# Orchestrating a round (phase-based protocol)

Long painter sessions can't be paused and resumed reliably: a sub-agent that stops at a checkpoint may not be resumable ("transcript missing"), and a painter sub-agent can't spawn its own critic. So a round runs as **phases**, each a fresh painter session, with all state on disk.

## Files in the round's studio directory
| File | Written by | Purpose |
|---|---|---|
| `brief.md` | orchestrator | the painter's full brief (persona, theme, studio, process) |
| `.secret` | painter (phase 1) | the chosen feeling; never shown or committed before the human guesses |
| `journal.md` | painter | one line per episode, including felt state |
| `handoff.md` | painter (end of every phase) | where the painting stands, what each element is meant to do, open problems, the plan for the next phase |
| `critique_N.md` | orchestrator | the blind critic's reading of `crit_N.png`, verbatim |
| `crit_N.png`, `final.png` | painter | the checkpoint image and the final image |
| canvas state (`main_*.npy`, scene files, frames) | studio | survives across phases |

## Phases
1. **Phase 1, conception → block-in** (~20 episodes). Choose the feeling and write `.secret`, make idea blockouts, the final blockout, tone, transfer, block-in. End: copy `main_full.png` to `crit_1.png`, write `handoff.md`, reply `PHASE 1 DONE`.
2. **Orchestrator:** run a fresh blind critic on `crit_1.png` (it knows only the theme), save the reading verbatim to `critique_1.md`.
3. **Phase 2, development** (~30–40 episodes). A new painter session reads `brief.md`, `.secret`, `journal.md`, `handoff.md` and `critique_1.md`, then looks at the canvas. End: `crit_2.png`, updated `handoff.md`, reply `PHASE 2 DONE`.
4. **Orchestrator:** a fresh critic on `crit_2.png` → `critique_2.md`.
5. **Phase 3, finalization** (~15–25 episodes). A new session reads the same files plus `critique_2.md`, finishes, runs `timelapse`, writes `final.png`, and replies with `FINISHED`, the title and its notes.
6. **Orchestrator:** a third blind critic on `final.png` (the "visitor" reading), then the human guesses, then reveal and commit.

Use a fresh critic every time, so no critic sees an earlier state. Never give a critic `.secret`, the journal or the handoff.
