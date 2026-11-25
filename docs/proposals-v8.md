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
- [ ] Research: emotion in visual art → `docs/research/emotion.md`
- [ ] Research: process gaps vs Spectre and human painters → `docs/research/process.md`
- [ ] Research: media and finishing → `docs/MEDIA.md`, `docs/FINISHING.md`, `studio/media.json`
- [ ] Research: 15 currents → `docs/styles/<id>.md`, `studio/styles.parts/batch-{a,b,c}.json` (merge into `studio/styles.json`)
  - batch A: byzantine-icon, renaissance, baroque, dutch-golden-age, romanticism
  - batch B: realism, impressionism, post-impressionism, fauvism, expressionism
  - batch C: cubism, surrealism, abstract-expressionism, ukiyo-e, east-asian-ink
- [ ] Engine media from `docs/MEDIA.md`: watercolour, ink, charcoal/graphite, pastel, gouache, egg tempera, woodblock look; oil finishing (varnish); each registered in `studio/v8/media/__init__.py`, passing `test_v8.py`
- [ ] `docs/MANUAL.md`: the painter's manual for v8 (commands, media, tools, views, finishing)
- [ ] Process: brief template with style config, nearest wrong feelings, an eye-path ledger, style research on demand; orchestration and AGENTS.md updated; lessons across styles
- [ ] A test painting in a new current and medium

If a research file is missing, rerun that research with the prompt shape in this plan; the other parts don't depend on each other until the engine media step (needs `docs/MEDIA.md`) and the process step (needs the research).
