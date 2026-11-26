# Repository map

Back to the router: [AGENTS.md](../../AGENTS.md).

```
AGENTS.md, CLAUDE.md        the router (always-on rules, routes by role)
studio/
  v8/                       CURRENT studio
    studio.py               the core: commands, intentions, motor model, views, report, finish, sign, timelapse
    media/                  one module per medium (oil, oil-v7, watercolour, ink, drymedia: charcoal/graphite/pastel,
                            opaque: gouache/tempera, woodblock), base.py (interface, kmix, KM films), spectral.py
    eyes.py                 measures (value, colour, edges, texture, structure) and comparison with targets
    scene.py                3D blockouts (figures, camera, light) for schemas
    gallery.py, test_v8.py  mark sheets; tests including the v7 regression
  v0-by-hand … v7/          earlier studios, kept as records
  styles.json               researched currents (merged from styles.parts/); styles.local/ is gitignored
  targets.json              measured targets per current (merged from targets.parts/)
  subjects.json             subject library short form (merged from subjects.parts/)
  pigments.json             pigment library with provenance
  calibration_refs.json     public-domain museum works used to calibrate media
  media.json                the media research as data
  signature.py              Teodor's signature, for any image
  contact_sheet.py          contact sheet of past work
docs/
  agents/                   the agent handbook (this folder)
  handover.md               current state, the owner's preferences, open threads
  orchestration.md          how a painting runs: standing rules, phases, critics, publishing
  MANUAL.md, manual/        the painter's studio manual; one page per medium
  styles/                   the style system (README) and one doc per current
  subjects/                 the subject library, layer 1 (README explains both layers)
  research/, research.md    emotion, process, references, figures; the research behind v6
  MEDIA.md, FINISHING.md, media-data.md   media and finishing research, physical data
  calibration/, gallery/    calibration reports and mark sheets per medium
  habits.md, experiments.md Teodor's habits; the round-by-round history
  proposals-v8.md           the v8 plan with checkboxes
  prompts/                  painter-brief.md (template), subject-research.md; older briefs kept as records
tools/                      make_brief.py, measure_targets.py, subject_gaps.py, merge_subjects.py,
                            calibrate_media.py, find_refs.py (open-access references), pigments/
rounds/NN-title/            painting.jpg, feeling.md, journal.md, handoff.md, critiques/, schemas or scenes, timelapse.mp4, references.json
site/                       the website (Next.js); app/works.ts lists the paintings
.github/workflows/          deploy-site.yml (Vercel Deploy Hook)
```
