# Handover: where the project stands

Written at the end of the long chat session that built most of this (Nov 22–24, 2026) so that a fresh Claude Code session can carry on. Read `AGENTS.md` first. This file adds the current state, Robert's preferences and the open threads.

## State (Nov 26, 2026)

- **Studio v8 is built** (`studio/v8/`, manual in `docs/MANUAL.md`): a medium-agnostic core with nine media (oil, watercolour, ink, charcoal, graphite, pastel, gouache, egg tempera, woodblock), 15 researched currents in `studio/styles.json` (docs in `docs/styles/`), measured style targets for 9 of them (`studio/targets.json`, `report` command), and a v8 brief made with `tools/make_brief.py`. `oil-v7` reproduces v7 exactly for comparison.
- **Every medium is calibrated against real data** (reports in `docs/calibration/`): pigments from published measurements (`studio/pigments.json`), mark statistics from public-domain Met works (`studio/calibration_refs.json`). Oil now mixes with a spectral Kubelka-Munk model (`media/spectral.py`).
- **Round 16** (*Cold Water at the Landing Stage*, Post-Impressionism, oil) was the first v8 painting and the end-to-end test. Its lessons are in `docs/experiments.md`, and three follow-ups are at the end of `docs/proposals-v8.md`. Robert asked whether the mid-phase critics are still needed: they are (see round 16 in the experiments log).
- **Style guide:** a published artifact (Claude, private to Robert) with the 15 currents, a public-domain example each, and a filter by feeling, for picking a style.

### Earlier state (Nov 24, 2026)

- **Seventeen paintings**, rounds 0–15, with round 14 painted twice (`14-…` by Opus 5.5 and `14b-…` by Fable 5.2). Every round folder has `painting.jpg` and, where one exists, `feeling.md`, `journal.md`, `brief.md`, `handoff.md`, critiques, scenes or schemas, helper scripts and `timelapse.mp4`.
- **Site:** live at https://teodor.robertontiu.com, deployed by Vercel through a Deploy Hook: `.github/workflows/deploy-site.yml` runs when a push touches `site/`, waits 5 minutes so a burst of pushes makes one deployment, then calls the hook (Git-triggered deploys are off in `site/vercel.json`, because Vercel's Hobby plan allows 100 deployments a day and skipped builds count too). Run the workflow by hand from GitHub's Actions tab to deploy at once. Newest painting first; each painting has its own page `/rN/` with a share preview; the model that painted it is shown next to the title.
- **Process:** the phase protocol (`docs/orchestration.md`), the current brief template (`docs/prompts/painter-brief.md`) and Teodor's habit list (`docs/habits.md`) are up to date. The studio is `studio/v7/`.
- **Round 15** (*One More Night*, Opus 5.5) is finished and published.
- **Nothing is in progress.** The old studio work dirs from the chat session (`/home/claude/vN/`) are not needed: everything worth keeping was copied into `rounds/`.

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
3. **Studio gaps painters worked around in v7.** Fixed in v8: `act @file`; `free`/`blend` take a number or a range; `transfer` picks a line colour that shows on the ground; hatch seams. Still open:
   - `color_shift` `value` and `sat` are multipliers (1 = unchanged), not offsets; a negative value turns colour black.
   - Gouache and tempera mix spectrally since Nov 26 (`docs/calibration/colour.md`, section 6: titanium and lead white, binder factors from FORS); pastel still uses `base.kmix` (section 6 lists what it needs). Lead white, titanium white and the earths are in the oil palette since Nov 26; burnt umber and terre verte are approximations, and no measured oil data for earths exists openly.
4. **Elevate plan leftovers** (`docs/proposals-v8.md`): element-clarity view, revision tools, a stronger hand, layers with roles.
5. **Maybe later:** Robert has mentioned a Ko-fi / Buy Me a Coffee page for Teodor and its sister project Spectre (an AI music producer built the same way: github.com/robertontiu/spectre), run as a private person. Not started.

## Session notes

- In the chat sandbox the site build needed a Google Fonts mock (see `docs/agents/site.md`); on a normal machine `npm run build` in `site/` works as is.
- Subagents in the chat could be interrupted by server restarts. The fix is always a fresh session for the same phase, continuing from the journal's last episode number.
