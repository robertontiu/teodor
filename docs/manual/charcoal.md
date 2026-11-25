# Charcoal (`charcoal`)

**What it is.** Burnt willow or vine sticks (soft, grey, easily erased) and compressed charcoal (pigment pressed with a binder: dense velvety blacks that are harder to erase). There is no paint and nothing dries. The dust catches on the paper's tooth: a light touch marks only the peaks and leaves speckled paper in the hollows, while pressure pushes it into the hollows. Once the tooth is full, more charcoal won't stick. Tone is built by layering, rubbing (stump, finger, chamois) and taking away with erasers. Erasing is drawing. Code: `studio/v8/media/drymedia.py`, class `Charcoal`. Graphite and pastel share the same engine (see `graphite.md` and `pastel.md`).

**Charcoal is monochrome.** The colour you ask for only sets the value the hand works toward. The stick presses as hard as that value needs, and it stops once the area under it is that dark. Pass black (`#000000`) for full strength. If you ask for a value lighter than the paper, the studio switches tools for you: white chalk on toned paper, or the kneaded eraser on white paper (it lifts toward that value). A schema works best in greys. Colour differences that charcoal can't make just waste `match` strokes.

**Supports.**
- `drawing` (default): white drawing paper with a fine, irregular tooth.
- `toned`: mid-grey toned paper (`#9a978f` when the ground you give `new` is light). Work both ways from the middle: charcoal for the darks, `white_chalk` for the lights.
- `ingres`: Ingres laid paper. Its fine laid lines and its chain lines show in every tone. It holds a little less charcoal than drawing paper.

**Tools** (`"brush": ...`). `size` is the width of the mark in px; the sheet is stated as 1200 px = 48 cm (2.5 px/mm, so 1 px = 0.4 mm). Sticks are capped at 26 px for the end and 140 px for the side.
- `vine_tip` (default): the end of a vine stick. A grey, irregular, broken line that is very erasable. Its darkest is a soft dark grey (about L* 29).
- `vine_side`: the stick laid on its side, across the stroke. A broad, pale band broken by the tooth, harder at one end. At light pressure only one end touches, so bands start and end in a wedge.
- `compressed_tip`, `compressed_side`: dense near-black lines and bands (at most about L* 24, the darkest the measured conté and charcoal drawings reach: charcoal is a matte black, not a screen black). They bind to the paper, so erasing them leaves a ghost.
- `pencil`: a charcoal pencil. A fine, controlled dark line, at most 8 px.
- `white_chalk`: white chalk or Conté for added lights, mainly on toned paper.
- `stump`, `tortillon` (small): rolled-paper blenders. They blur and spread the loose dust into a smooth tone that fills the hollows, so a rubbed passage reads deeper and smoother. They pick up very little.
- `finger`: smears tone and drags it out over lighter paper in soft gradients.
- `chamois`: a wide, soft wipe. It knocks a passage back, lifting about a quarter of the dust.
- `kneaded`: a soft-edged lift. Its pressure sets how much comes off. It takes loose dust first.
- `eraser`: a hard eraser with a crisp edge. It cuts clean lights, but vine never erases fully clean and compressed even less so, so earlier lines stay as ghosts (pentimenti).
- Oil-paint names map to the nearest tool: `round`, `filbert` and `liner` → `vine_tip`; `flat` and `fan` → `vine_side`; `blend` → `stump`; `smudge` → `finger`; `knife` → `eraser`. The `blend` intention therefore rubs with the stump.

**Parameters that matter.**
- `pressure`: the most important one. It decides how deep into the tooth the dust goes (speckled → filled) and how dark the mark gets.
- Felt state: fast, agitated strokes press less and break up more; slow, careful strokes are fuller.
- `size`: the mark width. For a broad mass use a `*_side` tool with a large size. For `match`, side tools at 20–60 px block in big masses, and tips at 4–12 px draw.

**Hatching** (`"type": "hatch"`). Use the tip tools. The studio's sheet is 1200 px = 48 cm (2.5 px/mm), and the real charcoal and conté hatching measured for the calibration is 1-2 mm apart with 0.5 mm lines: `"spacing": 4`–`5`, `"size": 1.5`–`2`. The core's defaults (spacing 9, size 3) give a coarse 3.6 mm hatch. The colour is the value of each line (`#000000` presses as hard as the stick can), and `layers` are absolute values, so on toned paper set them below the paper's value.

**Glaze.** `glaze` is a veil of powdered charcoal laid lightly with the side of the stick and partly rubbed in: tone on the peaks plus a soft, even film, capped at the value of the colour you give. Use it to tone the paper before drawing (the classic start), or to unify a passage.

**Time.** Nothing dries, and `dry` does nothing. Unfixed charcoal stays loose dust that any later blender can move and any eraser can lift.

**Finishing** (`studio.py finish <op> '<json>'`):
- `fixative` `{"kind": "final"|"workable", "strength": 1, "region": {...}}`: locks the dust, so it no longer smudges or erases, and darkens the drawing slightly (about 4% at full strength). `workable` (in a region, between layers) also restores some tooth so that more charcoal will take.
- `lift` `{"points": [[x, y, r], ...], "kind": "kneaded"|"eraser", "pressure": 0.8}`: highlights lifted with an eraser. Do this before the final fixative, because fixed charcoal won't lift.
- `clean` `{"margin": 30}` or `{"region": {...}}`: lifts dust and smudges from the margins or from outside a region.
- `accents` `{"strokes": [{"pts": [...], "color": "#000000", "size": 5}], "n": 6}`: the last darkest accents in compressed charcoal. It refuses more than `n` strokes.

**Order of work.** Tone the paper with `glaze`, or start white. Block in the big shapes with `vine_side`, then rub with the stump or finger. Draw into it with `vine_tip`. Take out the lights with `kneaded` and `eraser`. Put the darkest darks in with `compressed_*`, add `white_chalk` on toned paper, then `finish lift`, `finish accents` and `finish fixative`.

**Limits.** The paper's tooth is a texture (pixel-scale grain with short fibres, the laid lines on Ingres), not real fibres; the real tooth is finer than a pixel, so it shows as a fine speckle, not as visible cells. Hatched passages still look a little cleaner and more contrasted than real ones (no dust settling between the lines). There is no stick wear or breakage, and there is no water (no wash with compressed charcoal). The darkening that fixative causes is a fixed small value. Charcoal can't make colour: blue and red come out as their values. `sign` signs the same way as in oil.

## Calibration

Calibrated against the Met charcoal, black chalk and conté references (Nov 25, 2026); the full report, with the targets, the before and after numbers and the method, is `docs/calibration/charcoal.md`.

**Set from data** (the references, measured with `tools/calibrate_media.py` and hand-chosen crops at the studio scale):
- Darkest values: compressed charcoal L* 24 (conté, Millet: 23.8; charcoal, Degas: 21.9; black chalk, de la Fosse: 25.6), vine L* 29 (the lighter charcoal sheets: Mauve 28.9, Melbye 26.9). They were L* 4 and 23. The charcoal pencil (L* 26) is placed between them by eye.
- The paper's tooth: the light specks inside real marks are 0.06-0.15 mm, below one studio pixel, so the tooth is pixel-scale grain (it was a mix of 0.85, 2.2 and 8 px noise that read as camouflage blobs). Laid lines every 0.9 mm and chain lines every 35 mm (measured on laid sheets; they were 1.7 mm and 45 mm).
- The paper's grain in the render: about 1 L* on blank paper (references 0.5-1.1; it was 2.1).
- Line edges: a 10-90% rise of 0.75 mm (Millet, de la Fosse), where the tip was a hard 1 px edge.
- The catch's softness (a pixel is partly covered because it holds many tooth cells): fitted to the grain inside hatched passages.
- The stated scale (2.5 px/mm) and the hatch spacing advice (1-2 mm, measured by eye on mm-ruled zooms).

**Still tuned by eye:** coverage `KC = 3.5`; tooth capacities (`cap`) and `grab`; the pressure-to-reach curve and the crushed-dust term; how hard the hand presses for an asked value and the overshoot on the peaks (now scaled down for values near the paper's); per-tool flow, loose and stain; blender, eraser and fixative rates (fixative 4% is FINISHING.md's starting value); the velvet render; fibre length and cloud scale; the side stroke's streaks, its smooth wobble and its soft wedge-shaped landing and lift (they replace the hard square ends that made blocks in `match`); the size caps.

**Not measurable here:** reflectance of vine vs compressed charcoal as materials (the references are not labelled, and photographs of drawings give what a viewer sees, not the material), fixative darkening, coverage against pressure (needs swatches drawn at known pressure). Structure from Sousa & Buchanan [S27]; behaviour from MEDIA.md [S12][S13].
