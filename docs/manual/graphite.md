# Graphite pencil (`graphite`)

**What it is.** Graphite mixed with clay and fired into a lead. Grades run from hard and light (6H, 2H) to soft and dark (4B, 8B), with HB in the middle. Graphite catches on the paper's tooth the way charcoal does (speckled at light pressure, filled under pressure), but it is cleaner, less dusty and smudges less. Even the softest grade only reaches a dark grey, never charcoal's black. Its flat flakes give a metallic shine when the light rakes across dark, dense or burnished passages. Hard pressure flattens the tooth into a slick dark that takes no more graphite. Code: `studio/v8/media/drymedia.py`, class `Graphite` (the same engine as charcoal and pastel).

**Graphite is monochrome.** The colour you ask for sets only the value the hand works toward, and the pencil stops once the area under it is that dark. A value lighter than the paper switches to the kneaded eraser and lifts toward it. Work from a grey schema.

**Supports.**
- `drawing` (default): white drawing paper with a medium tooth.
- `toned`: grey-buff toned paper (`#b9b2a4` when the ground is light).
- `ingres`: Ingres laid paper. Laid lines show through the tone.
- `bristol`: smooth bristol. The tone comes out even and fine, but the little tooth holds less graphite, so the darks stay limited.

**Tools** (`"brush": ...`). `size` is the width of the mark in px. Points are capped at 10 px and the side at 36 px: a pencil is not a brush. The sheet is 1200 px = 24 cm (5 px/mm), so a 2 px line is 0.4 mm.
- `pencil` (default): set `"grade"` on the intention (6H…9B; default 2B). A narrow, even line.
- `pencil_2H`, `pencil_HB`, `pencil_4B`, `pencil_8B`: fixed grades. 2H stays light and silvery on the peaks, and 8B is the darkest, shiniest and most smudgeable.
- `side`: the side of a soft (6B) lead, for broad grainy tone.
- `stump`: a paper stump. It gives smooth, modulated tone and burnishes a little (adds shine).
- `kneaded`: soft lifts.
- `eraser`: a hard eraser for crisp lights (reduction drawing). Graphite erases well, but a faint ghost of each line stays.
- `stylus`: indents the paper. It is invisible at first. Any later tone skips the groove, which shows as a crisp white line (a sharp scratch through shading).
- Oil-paint names map over: `round`, `filbert` and `liner` → `pencil`; `flat` and `fan` → `side`; `blend` and `smudge` → `stump`; `knife` → `eraser`.

**Parameters that matter.** `pressure` sets the depth into the tooth and the darkness. Above about 0.8 it also burnishes (slick, shiny, the tooth full). `grade` sets hardness, darkness and smudginess. The felt state works as in charcoal: fast strokes come out lighter and more broken.

**Hatching** (`"type": "hatch"`). The sheet is stated as 1200 px = 24 cm (5 px/mm). Real hatching measured for the calibration (Delacroix, Grandville, Bendemann) is 0.8-2 mm apart with lines about 0.3-0.35 mm wide: `"spacing": 4`–`8`, `"size": 1.5`–`2`, one grade per pass. The core's defaults (spacing 9 = 1.8 mm, size 3 = 0.6 mm) are coarse for graphite. The colour is the value of each line, and the default `#2a2a2a` presses as hard as the pencil can: give a lighter grey for light hatching.

**Glaze.** A veil of graphite powder laid with the side of the lead and rubbed in, capped at the value of the colour you give. It's a quick way to lay a light general tone before hatching.

**Time.** Nothing dries, and `dry` does nothing.

**Finishing.**
- `fixative` `{"strength": 0.5, "region": {...}}` (optional for graphite): stops smudging, dulls the shine by about 20% and darkens a hair.
- `lift` `{"points": [[x, y, r], ...], "kind": "kneaded"|"eraser"}`: eraser highlights. Lift before fixing.
- `clean` `{"margin": 30}` or `{"region": {...}}`: cleans the margins.
- `accents` `{"strokes": [...], "n": 6, "tool": "pencil_8B"}`: the last darkest accents. It refuses more than `n` strokes.

**Order of work.** Light construction with `pencil_2H`, then the big value shapes with `side` or `glaze`. Build tone with softer grades and hatching, blend with `stump` where you want it smooth, erase the lights, and finish with the darkest accents and crisp edges.

**Limits.** The shine is drawn into the image under one fixed raking light; there is no movable light. Lines thinner than about 2 px are soft ramps, not resolved into single flakes of graphite. There is no pencil wear (sharp vs blunt is just `size`). Hatched passages look a little cleaner and more contrasted than real ones (no graphite haze between the lines).

## Calibration

Calibrated against the Met graphite references (Nov 25, 2026); the full report is `docs/calibration/graphite.md` (shared engine changes in `docs/calibration/charcoal.md`).

**Set from data:**
- The darkest graphite: L* 32.5-34.7 in the references (Lachaise, Grandville). A dense 8B passage renders at L* 32.8. The soft grades' pigment values sit about 3.5 L* lower than that because the render's sheen lifts them.
- One hard-end point, weak: Ingres's portrait in fine hard pencil reaches L* 55, used for H.
- The paper's tooth at pixel scale and its grain in the render (blank paper 0.8 L*; references 0.6-1.1; it was 1.6), laid lines at 0.9 mm: as in charcoal.
- Line edges: 10-90% rise 0.3 mm (Delacroix's hatching), a softer catch fitted to the grain in hatched passages.
- The stated scale (5 px/mm, like the reference sheets) and the hatch spacing and width advice.

**The grade ramp between the ends is tuned by eye** (`GRADE_L`: 6H 72, 4H 66, 2H 60, H 55, HB 49, B 44.5, 2B 41, 3B 38, 4B 35.5, 5B 33.5, 6B 32, 7B 30.8, 8B 29.8, 9B 29 pigment L*): no per-grade darkness was found as a measurement, and which grades 19th-century draughtsmen used is not known.

**Still tuned by eye:** flow, reach, loose, stain and sheen per grade; `KC = 3.5`; tooth capacities (drawing 0.9, Ingres 0.8, bristol 0.55); the burnish threshold (0.82); the sheen render (cool silver, at most 42%, fixed raking light: a diffuse museum photograph cannot show gloss); blender, eraser and stylus rates; fixative (~20% less shine is FINISHING.md's assumption); the size caps.

**Searched, not found.** No published per-grade reflectance or optical density for graphite; a tribology study of graded pencil cores ("Tribological characteristics of graded pencil cores on paper") was behind bot protection. No gloss measurement of graphite drawings. Structure from Sousa & Buchanan [S27]; behaviour from MEDIA.md [S10][S13].
