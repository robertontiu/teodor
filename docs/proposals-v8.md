# Work in progress: Teodor v8 (styles, media, finishing, research)

Started 2026-11-25 from Robert's notes after Spectre (github.com/robertontiu/spectre) outgrew Teodor in output quality. This file is the plan and its state, so a fresh session can pick up if this one stops. Tick items as they land.

## Robert's five points
1. **Research:** ground the painting in research on how emotion is carried by and perceived in images, as Spectre is grounded in music-emotion research.
2. **Human-analogous process:** compare with Spectre and fill the gaps with more research.
3. **Style as configuration:** a style is layered (current/movement × medium × support × technique × finishing), configured as sourced data, with research for unknown styles part of the process; the engine gains media and tools like Spectre gains instruments.
4. **Finishing as mastering:** research what the last stage is per medium and per current; build it.
5. **Styles, never authors:** only styles and movements are versioned. A request for a specific artist may get temporary research and a local configuration in `studio/styles.local/` (gitignored), never committed.

Plus anything else from Spectre that applies.

## State
- [x] Style system shape: `docs/styles/README.md` (layers, rules, doc template, JSON entry)
- [x] Author rule: brief rewritten to study movements, never one artist; `studio/styles.local/` gitignored
- [x] Engine v8 core: media as pluggable modules (`studio/v8/media/`), oil identical to v7 (`studio/v8/test_v8.py`), new views (mirror, upside, squint, notan, edges, temp), `finish`, `media`, `act @file.json`
- [x] Research: emotion in visual art → `docs/research/emotion.md`
- [x] Research: process gaps vs Spectre and human painters → `docs/research/process.md` (20 ranked proposals; some sources written from memory are flagged there for checking)
- [x] Research: media and finishing → `docs/MEDIA.md`, `docs/FINISHING.md`, `studio/media.json`
- [x] Research: 15 currents (merged into `studio/styles.json`) → `docs/styles/<id>.md`, `studio/styles.parts/batch-{a,b,c}.json` (merge into `studio/styles.json`)
  - batch A: byzantine-icon, renaissance, baroque, dutch-golden-age, romanticism
  - batch B: realism, impressionism, post-impressionism, fauvism, expressionism
  - batch C: cubism, surrealism, abstract-expressionism, ukiyo-e, east-asian-ink
- [x] Engine media from `docs/MEDIA.md` (all built and calibrated: oil, watercolour, ink, charcoal, graphite, pastel, gouache, egg tempera, woodblock): watercolour, ink, charcoal/graphite, pastel, gouache, egg tempera, woodblock look; oil finishing (varnish); each registered in `studio/v8/media/__init__.py`, passing `test_v8.py`
- [x] `docs/MANUAL.md`: the painter's manual for v8 (commands, media, tools, views, finishing)
- [x] Process: brief template (docs/prompts/painter-brief.md, filled by tools/make_brief.py) with style config, nearest wrong feelings, an eye-path ledger, style research on demand; orchestration and AGENTS.md updated; lessons across styles
- [ ] A test painting in a new current and medium

## Everything that can elevate the project (Robert, 2026-11-25: "everything that has the potential to elevate this project should go into it")
From Spectre and from `docs/research/process.md` part 3:
- [x] **Measured style targets:** (9 currents measured in `studio/targets.json`; byzantine-icon, fauvism and expressionism lack enough public-domain Met works; surrealism and abstract-expressionism are in copyright) measure each current from public-domain museum images (the Met open-access API and images are reachable from the workspace; the Art Institute of Chicago API is reachable, its IIIF images returned 403 in a first test): value key and histogram, value groups, saturation, palette spread, edge density and hard-edge share, spectral slope, where the strongest contrast sits. Store targets with provenance in `studio/targets.json`; a `report` command compares the canvas with its style's target, like Spectre's master report. The painter fixes deviations by painting.
- [~] **Numbers, not only pictures, in the views:** (`report` built: value, colour, edges, texture, structure, flags; element clarity still to do) a value report (groups, share per group, key, flags: murky middle, too few groups, one empty block), an edge report (hard/firm/soft/lost classes, hard-edge share in vs out of the focal area), a saliency check against the declared focal point, and element clarity (each blockout element's contrast at thumbnail size; flag "masked" elements), the painting version of Spectre's masking measure.
- [ ] **Translate the reference, don't copy it:** before matching, turn the blockout into a painter's reference (group values, simplify detail and edges away from a declared focal point; matching less faithful with distance from it).
- [ ] **Passages built in layers with roles:** underpainting, dead colour, body, glazes, scumbles, accents; a view that shows where a passage has only one layer or one kind of mark (Spectre's stacks and stack view).
- [ ] **A stronger hand:** articulations (drag, swell-and-taper, scumble, scrape, wipe-out), variation that drifts across a passage instead of random jitter, "model a form", "hatch a plane", faces and hands from a tonal study. The mind decides; the hand performs.
- [x] **Variants before committing:** 6-10 tiny two- or three-value thumbnails in different structures, then two or three colour studies; Robert may pick (Spectre's sound stage).
- [x] **A gallery of every tool:** a mark sheet per medium and tool, checked against real examples before painters use it (Spectre's `gallery.py`).
- [x] **Nearest wrong feelings and looks** in every brief; each critic reading scored against them.
- [x] **An expectation ledger:** the painting sets up a direction, value key, temperature and edge world, then breaks it once on purpose; the views confirm the break is the strongest point.
- [x] **Media grounded in real data (Robert, 2026-11-25: "base your utensils building on research and real data"):** a pigment library from published measurements (`studio/pigments.json`), physical figures from the literature (`docs/media-data.md`), and calibration of every tool against measured statistics of real marks in high-resolution public-domain museum images (`studio/calibration_refs.json`, `tools/calibrate_media.py`), with a calibration report per medium next to its mark sheet. Done: every medium has a calibration report in `docs/calibration/`. Oil colour mixing is spectral Kubelka-Munk (`media/spectral.py`, median ΔE2000 1.8 on 29 measured tints vs 12.6 for the old kmix). Open: `base.kmix` still serves gouache, tempera and pastel (switching costs ~25x per pixel; needs a windowed path like oil's `mix_window`); lead white and earth pigments have no usable K and S yet; charcoal hatching grain is still 1.5x the references (no dust model); values still tuned by eye are listed in each report.
- [ ] **Revision tools:** scrape back, wipe out, paint out (painters revise by taking away).
- [x] **Standing rules, lessons across styles, research beats suggestions, Robert as the eye test** in the orchestration docs.

If a research file is missing, rerun that research with the prompt shape in this plan; the other parts don't depend on each other until the engine media step (needs `docs/MEDIA.md`) and the process step (needs the research).
