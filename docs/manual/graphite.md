# Graphite pencil (`graphite`)

**What it is.** Graphite mixed with clay and fired into a lead. Grades run from hard and light (6H, 2H) to soft and dark (4B, 8B), with HB in the middle. Graphite catches on the paper's tooth the way charcoal does (speckled at light pressure, filled under pressure), but it is cleaner, less dusty and smudges less. Even the softest grade only reaches a dark grey, never charcoal's black. Its flat flakes give a metallic shine when the light rakes across dark, dense or burnished passages. Hard pressure flattens the tooth into a slick dark that takes no more graphite. Code: `studio/v8/media/drymedia.py`, class `Graphite` (the same engine as charcoal and pastel).

**Graphite is monochrome.** The colour you ask for sets only the value the hand works toward, and the pencil stops once the area under it is that dark. A value lighter than the paper switches to the kneaded eraser and lifts toward it. Work from a grey schema.

**Supports.**
- `drawing` (default): white drawing paper with a medium tooth.
- `toned`: grey-buff toned paper (`#b9b2a4` when the ground is light).
- `ingres`: Ingres laid paper. Laid lines show through the tone.
- `bristol`: smooth bristol. The tone comes out even and fine, but the little tooth holds less graphite, so the darks stay limited.

**Tools** (`"brush": ...`). `size` is the width of the mark in px. Points are capped at 10 px and the side at 36 px: a pencil is not a brush.
- `pencil` (default): set `"grade"` on the intention (6H…9B; default 2B). A narrow, even line.
- `pencil_2H`, `pencil_HB`, `pencil_4B`, `pencil_8B`: fixed grades. 2H stays light and silvery on the peaks, and 8B is the darkest, shiniest and most smudgeable.
- `side`: the side of a soft (6B) lead, for broad grainy tone.
- `stump`: a paper stump. It gives smooth, modulated tone and burnishes a little (adds shine).
- `kneaded`: soft lifts.
- `eraser`: a hard eraser for crisp lights (reduction drawing). Graphite erases well, but a faint ghost of each line stays.
- `stylus`: indents the paper. It is invisible at first. Any later tone skips the groove, which shows as a crisp white line (a sharp scratch through shading).
- Oil-paint names map over: `round`, `filbert` and `liner` → `pencil`; `flat` and `fan` → `side`; `blend` and `smudge` → `stump`; `knife` → `eraser`.

**Parameters that matter.** `pressure` sets the depth into the tooth and the darkness. Above about 0.8 it also burnishes (slick, shiny, the tooth full). `grade` sets hardness, darkness and smudginess. The felt state works as in charcoal: fast strokes come out lighter and more broken. There is no hatch intention yet: to hatch, use `strokes` with parallel lines, then a second pass at another angle for cross-hatching.

**Glaze.** A veil of graphite powder laid with the side of the lead and rubbed in, capped at the value of the colour you give. It's a quick way to lay a light general tone before hatching.

**Time.** Nothing dries, and `dry` does nothing.

**Finishing.**
- `fixative` `{"strength": 0.5, "region": {...}}` (optional for graphite): stops smudging, dulls the shine by about 20% and darkens a hair.
- `lift` `{"points": [[x, y, r], ...], "kind": "kneaded"|"eraser"}`: eraser highlights. Lift before fixing.
- `clean` `{"margin": 30}` or `{"region": {...}}`: cleans the margins.
- `accents` `{"strokes": [...], "n": 6, "tool": "pencil_8B"}`: the last darkest accents. It refuses more than `n` strokes.

**Order of work.** Light construction with `pencil_2H`, then the big value shapes with `side` or `glaze`. Build tone with softer grades and hatching, blend with `stump` where you want it smooth, erase the lights, and finish with the darkest accents and crisp edges.

**Limits.** The shine is drawn into the image under one fixed raking light; there is no movable light. Lines thinner than about 2 px are antialiased, not resolved into single fibres of graphite. There is no pencil wear (sharp vs blunt is just `size`), and there is no hatch intention.

## Calibration

**What comes from research.**
- The model's structure follows Sousa & Buchanan [S27] ([GI 1999](https://graphicsinterface.org/wp-content/uploads/gi1999-21.pdf)): the paper as a height field, deposit capped by the tooth, blenders and erasers that move or lift graphite. The paper says the more graphite a lead contains, the softer and darker it is, and that graphite particles are about 2–10 µm. It gives no per-grade darkness, and its numeric coefficients didn't survive the PDF's text extraction.
- The behaviour comes from MEDIA.md [S10][S13]. Grades run from hard and light to soft and dark, HB in the middle. Even the darkest graphite is a mid-dark grey next to charcoal. The flat flakes shine under raking light, most in soft grades and when burnished. Graphite erases easily and needs little fixative.
- The fixative's "~20% less shine" is FINISHING.md's own modelling assumption, not a measurement.

**Hand-tuned by eye:**
- The grade table in `grade_spec`. Pigment luminance runs `0.6 − 0.44·i^0.8` from 6H (0.60) to 9B (0.16); flow, reach, loose and stain rise linearly with softness; sheen runs from 0.25 to 1.0. The darkness ordering is from the sources; every number is tuned.
- Coverage `KC = 3.5`; tooth capacity (drawing 0.9, Ingres 0.8, bristol 0.55) and catch softness; the burnish threshold (pressure 0.82).
- The sheen render: a cool silver `(0.60, 0.615, 0.65)`, at most 42% toward it, with a fixed raking-light direction from the upper left.
- Blender, eraser and stylus rates; bound-pigment erasability 0.85.
- The size caps (10 px for a point, 36 px for the side) assume about 0.4 mm/px.

**Searched, not found.** No published per-grade reflectance or optical density for graphite. Manufacturer and blog pages describe the grades only qualitatively. A tribology study of graded pencil cores on paper exists ("Tribological characteristics of graded pencil cores on paper"), but its record was behind bot protection, so I could not read its load and deposit data. No gloss measurement of graphite drawings. These are worth fitting from real crops or from swatch scans of real pencils:
1. the darkest value per grade;
2. darkness against pressure and number of passes;
3. how strong the shine is in raking light.
