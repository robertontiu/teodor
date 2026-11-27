# AGENTS.md: start here

**Teodor** is an experiment, not a product: can an AI paint the way a human painter does, starting from a feeling and correcting by looking, instead of generating an image from a prompt? A painter agent, working as the artist Teodor, paints in a simulated studio (`studio/v8/`): he researches, plans with thumbnails and a drawn schema, then lays every mark with simulated brushes, pens and blocks in short look-and-correct episodes, with fresh critics between phases. More: [docs/agents/project.md](docs/agents/project.md).

This file holds only what every request needs. Read the rules, then the route for your role.

## Always-on rules (every agent, every request)

1. **The artist is called Teodor, everywhere**, and every painting is signed "Teodor".
2. **It must be a painting.** Every mark on the canvas goes through the studio's tools. Schemas and references can be built with any script, but nothing is pasted, composited, traced or flat-filled onto the canvas. A planner may propose mark paths from the painter's own invented reference; the painter chooses the families, the regions and the counts, and every mark is laid by a studio tool.
3. **Styles and movements, never authors.** Only currents, schools and techniques are versioned. A request for a specific artist gets temporary research in `studio/styles.local/` (gitignored), used for that painting only.
4. **No personal details in versioned files.** Anything personal the owner (Robert) shares is context for a brief, never content: not in briefs, journals, docs, commits, the site or handoff notes.
5. **No likeness of real people, and no gore.** Shocking, satirical and dark themes are fine, painted from the inside.
6. **Research and real data decide.** Style settings, subject knowledge, media and tools rest on sources and measurement; every value tuned by eye is marked as such. Where a suggestion (a critic's, a brief's, the owner's) contradicts the research, flag it, follow the research and say why.
7. **Commit by path** (`git commit -m "..." -- <paths>`), never `git add -A` while other agents work in the tree. Author: Robert Ontiu <robertontiu@users.noreply.github.com>; push straight to `main`. A push that touches `site/` deploys the site about 5 minutes later, so batch site changes ([docs/agents/git.md](docs/agents/git.md)).
8. **Never commit** canvas state (`*.npy`, `*.npz`, frames), work dirs (`../teodor-work/`), `__pycache__`, caches (`~/.cache/teodor/`) or raw downloaded data.
9. **Engine edits while a painting runs** must be additive and written atomically (temp file plus rename). Painters work on their own copy of the studio in their work dir.
10. **Don't work around a site's bot protection**, and use only openly licensed images (CC0 or public domain) for measurement and publication.
11. **It's an experiment:** report misses honestly, in the experiments log and on the site.
12. **Clean up after yourself:** delete your scratch (`/tmp` folders, test canvases, downloads) when your task ends; keep it in a folder named for your task.

## Routes by role

**Orchestrator** (the root agent the owner talks to):
- [docs/handover.md](docs/handover.md) at the start of a fresh session: current state, the owner's preferences, open threads.
- [docs/orchestration.md](docs/orchestration.md) in full: standing rules, starting a painting, subjects before drawing, phases, critics, checking a checkpoint, publishing, comparing models.
- [docs/agents/painting-quickstart.md](docs/agents/painting-quickstart.md): the short version of running a painting.
- `tools/make_brief.py` to set up a work dir; [docs/habits.md](docs/habits.md) to update after every painting.

**Painter** (Teodor, one phase of a painting):
- Your `brief.md` is your whole brief; it names what to read ([docs/MANUAL.md](docs/MANUAL.md), your medium's page in `docs/manual/`, your style doc, the subject pages for your picture, `habits.md`).

**Critic** (a fresh reading of a checkpoint): only the prompt you were given and the image it names. Read no other file.

**Style or subject research agent:**
- Styles: [docs/styles/README.md](docs/styles/README.md) (schema and template), an existing style doc as a model, `tools/measure_targets.py` for measured targets, [docs/orchestration.md](docs/orchestration.md) "Starting a painting".
- Subjects: [docs/subjects/README.md](docs/subjects/README.md), the prompts in [docs/prompts/subject-research.md](docs/prompts/subject-research.md), `tools/subject_gaps.py`.
- Write to the `*.parts/` folders, not to the merged JSON files.

**Engine / media builder** (studio code, media, tools):
- [docs/agents/engine-rules.md](docs/agents/engine-rules.md) (conventions, adding a medium, tests, internals), [docs/agents/repo-map.md](docs/agents/repo-map.md), [docs/agents/known-limits.md](docs/agents/known-limits.md).
- [docs/proposals-v8.md](docs/proposals-v8.md) for the plan; [docs/MEDIA.md](docs/MEDIA.md), [docs/media-data.md](docs/media-data.md) and `docs/calibration/` for the data. Keep [docs/MANUAL.md](docs/MANUAL.md) and `docs/manual/` in sync: they are the painter's only interface.

**Site agent:** [docs/agents/site.md](docs/agents/site.md) (build, deploy hook, adding a painting).

## Where things are

| Folder | What |
|---|---|
| `studio/v8/` | the current studio: core (`studio.py`), media (`media/`), eyes (`eyes.py`), scene blockouts (`scene.py`), tests |
| `studio/` | styles, targets, pigments, subjects (JSON), calibration references; older studios v0–v7 kept as records |
| `docs/` | manual, orchestration, handover, habits, experiments, research, styles, subjects, calibration, gallery |
| `docs/agents/` | the agent handbook this file routes to |
| `docs/prompts/` | the painter brief template and research prompts (older briefs kept as records) |
| `tools/` | brief maker, target measuring, subject gaps, calibration and pigment scripts |
| `rounds/` | one folder per finished painting: image, feeling, journal, critiques, time-lapse |
| `site/` | the website (Next.js), deployed by a GitHub Action through a Vercel Deploy Hook |

Full map: [docs/agents/repo-map.md](docs/agents/repo-map.md).
