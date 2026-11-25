# Styles: how a style is configured

A painting's style is not one setting. Like a genre in Spectre, it is a configuration of the painter, built from layers that can be combined:

| Layer | What it decides | Where it lives |
|---|---|---|
| **Current** (movement or school) | the visual language: palette logic, light, composition, drawing, edges, what is considered finished, how feeling is carried | `studio/styles.json` + `docs/styles/<id>.md` |
| **Medium** | the paint's physics and the tools: oil, watercolour, ink, charcoal, graphite, pastel, gouache, tempera… | `studio/media.json` + `docs/MEDIA.md` |
| **Support** | what is painted on: canvas, panel, cold-press paper, toned paper, silk… | `studio/media.json` (per medium) |
| **Technique** | how the medium is worked: alla prima, indirect glazing, impasto, wet-in-wet, dry brush, hatching, broken colour… | the style entry, using techniques the medium supports |
| **Finishing** | the last stage: unifying glazes, last accents, varnish or fixative, presentation | the style entry, building on `docs/FINISHING.md` |

A commission names a current (or leaves it to Teodor) and may override the medium or support. A current lists the media it was historically practised in; the first is its default.

## Rules

- **Styles and movements only.** Only currents, schools and techniques are versioned. A request to paint in the manner of one specific artist is handled with temporary research distilled into a local configuration in `studio/styles.local/` (gitignored), used for that painting only and never committed. Versioned docs may name artists sparingly as historical context for a movement, never as a model to imitate, and never living artists.
- **Every value has a source.** Each style doc ends with sources (art history references, museum essays, conservation studies, technical art history). A value that is a judgement call is marked as such.
- **New styles are researched before their first painting.** If a commission asks for a current that has no entry, research it first (same template), add it to `studio/styles.json` and `docs/styles/`, then paint.

## The style doc template (`docs/styles/<id>.md`)

1. **In one paragraph:** what the current is, where and when, what it wanted.
2. **How it carries feeling:** which visual cues the current uses to make a viewer feel (colour, value, line, gesture, composition, surface), and what it avoids; link to `docs/research/emotion.md` where research supports it.
3. **Media, supports and grounds:** what was used historically, the default for Teodor, how the ground was prepared and toned.
4. **Palette:** the principle (limited earth palette, complementary broken colour, flat unmodulated fields…), typical pigments as approximate hex values, what to avoid.
5. **Light and value:** where light comes from, value range and key, how shadows are treated.
6. **Drawing and form:** how form is built (contour, modelling, planes, flatness), proportion and distortion conventions.
7. **Composition:** typical structures, viewpoints, cropping, space.
8. **Marks and edges:** tools, brush sizes, stroke direction and length, visible or hidden brushwork, edge hierarchy.
9. **Process (the order of work):** how a painting in this current was actually built, stage by stage, and how that maps to Teodor's phases.
10. **Finishing:** what "finished" meant in the current and what the last stage did (varnish, final glazes, accents, fixative, leaving it raw).
11. **Pitfalls for Teodor:** the postcard or pastiche version to avoid, the nearest wrong feelings this current drifts into, what the engine can't do yet.
12. **Engine mapping:** which engine media, tools, intentions and felt-state settings realise the above, and any gap (`docs/MANUAL.md` names).
13. **Sources.**

## The `studio/styles.json` entry

```json
"impressionism": {
  "name": "Impressionism",
  "doc": "docs/styles/impressionism.md",
  "period": "France, 1860s-1890s",
  "media": ["oil", "pastel"],
  "support": {"oil": "canvas-fine", "pastel": "paper-toned"},
  "ground": "#e8e2d4",
  "technique": ["alla prima", "wet-into-wet", "broken colour"],
  "palette": {"principle": "...", "colors": ["#...", "..."], "avoid": ["black", "..."]},
  "light": "...",
  "value_key": "high",
  "composition": "...",
  "drawing": "...",
  "edges": "...",
  "marks": {"tools": ["flat", "filbert"], "length": "short", "direction": "follows form or the light", "visible": true},
  "process": ["...", "..."],
  "finishing": ["...", "..."],
  "pitfalls": ["...", "..."],
  "felt_bias": {"arousal": 0.0, "tension": 0.0, "care": 0.0},
  "engine_gaps": ["..."],
  "sources": ["...", "..."]
}
```

Fields are short summaries; the doc holds the detail. `felt_bias` nudges the hand's default felt state for the current (a gestural current runs higher arousal, a meticulous one higher care); the painter's own feeling still decides.
