# Running a painting: the short version

Back to the router: [AGENTS.md](../../AGENTS.md). The full protocol is [docs/orchestration.md](../orchestration.md).

1. Install `numpy scipy pillow`, `ffmpeg` and `librsvg` (`rsvg-convert`) if they're missing, and run `python3 tools/fetch_human.py` once (the CC0 human mesh).
2. If the commission names a current that isn't in `studio/styles.json`, or a medium the studio doesn't have, research or build it first. A request to paint like a specific artist gets a temporary, gitignored configuration in `studio/styles.local/`.
3. Set up the work dir and the brief, outside the repo:
   `python3 tools/make_brief.py ../teodor-work/NN --commission "a public exhibition on a theme. The theme is: ..." --theme [--style ID|free] [--medium M] [--support S]`
   (`--feeling "..."` instead of `--theme` if the person named the feeling).
4. Phase 1 plans, then stops with `subjects.json`. Run `tools/subject_gaps.py`, research the gaps, and continue phase 1 ("Subjects before drawing").
5. Run the phases as fresh general-purpose sub-agents. Each reads `brief.md` and does its phase. Between phases, a fresh critic reads the checkpoint, and the orchestrator checks it (`report`, nearest wrong feelings, habits) and writes the studio manager's note. Never resume a painter sub-agent: start a fresh one that reads the files. Painters can't spawn critics, so the orchestrator runs them.
6. Show the person each checkpoint (as JPEG: chat uploads can reject the studio's PNGs), then the final painting, title, feeling, visitor reading, journal highlights and time-lapse.
7. Publish without asking ("Publishing" in orchestration.md): round folder, experiments log, habits, site, one commit.
