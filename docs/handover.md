# Handover: where the project stands

Written at the end of the long chat session that built most of this (Nov 22–24, 2026) so that a fresh Claude Code session can carry on. Read `AGENTS.md` first. This file adds the current state, Robert's preferences and the open threads.

## State (Nov 24, 2026)

- **Sixteen paintings**, rounds 0–14, with round 14 painted twice (`14-…` by Opus 5.5 and `14b-…` by Fable 5.2). Every round folder has `painting.jpg` and, where one exists, `feeling.md`, `journal.md`, `brief.md`, `handoff.md`, critiques, scenes or schemas, helper scripts and `timelapse.mp4`.
- **Site:** live at https://teodor.robertontiu.com, deployed by Vercel from `site/` on every push that touches it. Newest painting first; each painting has its own page `/rN/` with a share preview; the model that painted it is shown next to the title.
- **Process:** the phase protocol (`docs/orchestration.md`), the current brief template (`docs/prompts/painter-brief.md`) and Teodor's habit list (`docs/habits.md`) are up to date. The studio is `studio/v7/`.
- **Round 15** ("Love, now and in the afterlife", read as neverending love; Opus 5.5) was started at the end of the chat session; if its round folder is missing, it didn't finish there.
- **Nothing else is in progress.** The old studio work dirs from the chat session (`/home/claude/vN/`) are not needed: everything worth keeping was copied into `rounds/`.

## How Robert works with this project

- **He gives a theme** (sometimes a style, sometimes "free style") and Teodor finds his own feeling inside it. Feelings are published openly with each painting.
- **He likes to see progress:** after each phase, show him the checkpoint image (as a JPEG) and a short plain summary: what Teodor painted, his feeling, what the critic felt, what you told Teodor. Then the final painting with its time-lapse.
- **When a painting is finished, publish it without asking:** round folder, `docs/experiments.md`, `docs/habits.md`, `site/` (image and `works.ts` entry), one commit, push to `main`. Vercel does the rest.
- **He wants Teodor to keep surprising:** break the habits in `docs/habits.md`, research painters he hasn't used, and don't let critics' advice drag him back into old habits (the studio manager's note under each critique is where you push back).
- **"Shocking" is welcome, gore is not.** Death, drugs and satire are all fine as themes, painted from the inside, without graphic injury, instructions or glamorizing.
- **No likeness of real people.** When a theme pointed at a real politician (round 12, "The Orange Buffoon"), the ruler became Teodor's own invented archetype, with the theme's color living in the world around him, not in a recognizable face. Robert agreed to that.
- **It must look and feel like a painting.** He accepted round 14b, but felt Fable's compositing and flat tile fills "cheated a bit": it didn't feel like a painting. The rule is now in the brief and `AGENTS.md`. He also prefers Opus 5.5 as the painter for now.
- **Model comparisons:** he's curious how different models paint the same brief. Run them in parallel (see "Comparing models" in `docs/orchestration.md`) and record the model in `works.ts` and the round folder.
- **Public text stays plain:** the README and site are for people, not engineers; cite the research with links; keep technical detail in `AGENTS.md` and `docs/`.
- **Licensing:** code MIT, Teodor's paintings CC BY 4.0 (credit the repo); paintings other people make with the project are theirs and their responsibility.
- **Permissions:** `.claude/settings.json` allows WebSearch and WebFetch without prompting, because Teodor researches before he paints.

## What to work on next (open threads)

1. **Staging habits.** Round 14 broke palette, light and mood but kept one central figure in a field with a radial pull. The next brief should target those (several figures, no centre, an off-balance composition, landscape-like crops).
2. **Craft is now the ceiling,** for both models:
   - Figures still read as mannequins: faces near-identical, hands like tubes or mitts, stiff gestures. Teodor wrote his own helpers for this (`rounds/13-black-noon/tools/p3/facegen.py` for shaded heads; Fable's figure rig in `rounds/14b-…/tools/pose2.py`). Folding a better figure and face builder into the studio would help every painting.
   - The surface reads as "a digital filter": square dabs everywhere and uniform edges. The stroke vocabulary needs variety in width, pressure and direction within one stroke.
3. **Studio gaps painters worked around** (worth fixing in `studio/v7` or a v8):
   - The 3D camera can't roll and the mannequin can't lie down; two painters wrote their own compositing to get an overhead view of a lying figure (`rounds/14-…/tools/compose.py`, `rounds/14b-…/tools/compose.py`).
   - Long stroke lists hit the shell's "argument list too long"; painters pass acts through a JSON file instead (`tools/actf.py`, `tools/ep.py`). `studio.py act` could read from a file natively.
   - `free` needs `length` as a `[min, max]` range (a number crashes it), and `blend` needs `size` and `length` as ranges.
   - `color_shift` values multiply the color rather than shifting it (a value of −0.25 turned a corner black).
   - `transfer` lines (#4a3a2e) are invisible on dark grounds.
4. **Maybe later:** Robert has mentioned a Ko-fi / Buy Me a Coffee page for Teodor and its sister project Spectre (an AI music producer built the same way: github.com/robertontiu/spectre), run as a private person. Not started.

## Session notes

- In the chat sandbox the site build needed a Google Fonts mock (see `AGENTS.md`); on a normal machine `npm run build` in `site/` works as is.
- Subagents in the chat could be interrupted by server restarts. The fix is always a fresh session for the same phase, continuing from the journal's last episode number.
