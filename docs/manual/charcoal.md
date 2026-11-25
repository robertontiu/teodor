# Charcoal (`charcoal`)

**What it is.** Burnt willow or vine sticks (soft, grey, easily erased) and compressed charcoal (pigment pressed with a binder: dense velvety blacks that are harder to erase). There is no paint and nothing dries. The dust catches on the paper's tooth: a light touch marks only the peaks and leaves speckled paper in the hollows, while pressure pushes it into the hollows. Once the tooth is full, more charcoal won't stick. Tone is built by layering, rubbing (stump, finger, chamois) and taking away with erasers. Erasing is drawing. Code: `studio/v8/media/drymedia.py`, class `Charcoal`. Graphite and pastel share the same engine (see `graphite.md` and `pastel.md`).

**Charcoal is monochrome.** The colour you ask for only sets the value the hand works toward. The stick presses as hard as that value needs, and it stops once the area under it is that dark. Pass black (`#000000`) for full strength. If you ask for a value lighter than the paper, the studio switches tools for you: white chalk on toned paper, or the kneaded eraser on white paper (it lifts toward that value). A schema works best in greys. Colour differences that charcoal can't make just waste `match` strokes.

**Supports.**
- `drawing` (default): white drawing paper with a fine, irregular tooth.
- `toned`: mid-grey toned paper (`#9a978f` when the ground you give `new` is light). Work both ways from the middle: charcoal for the darks, `white_chalk` for the lights.
- `ingres`: Ingres laid paper. Its fine laid lines and its chain lines show in every tone. It holds a little less charcoal than drawing paper.

**Tools** (`"brush": ...`). `size` is the width of the mark in px. Sticks are capped at 26 px for the end and 140 px for the side.
- `vine_tip` (default): the end of a vine stick. A grey, irregular, broken line that is very erasable. Its darkest is a soft dark grey.
- `vine_side`: the stick laid on its side, across the stroke. A broad, pale band broken by the tooth, harder at one end. At light pressure only one end touches, so bands start and end in a wedge.
- `compressed_tip`, `compressed_side`: dense near-black lines and bands. They bind to the paper, so erasing them leaves a ghost.
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

**Glaze.** `glaze` is a veil of powdered charcoal laid lightly with the side of the stick and partly rubbed in: tone on the peaks plus a soft, even film, capped at the value of the colour you give. Use it to tone the paper before drawing (the classic start), or to unify a passage.

**Time.** Nothing dries, and `dry` does nothing. Unfixed charcoal stays loose dust that any later blender can move and any eraser can lift.

**Finishing** (`studio.py finish <op> '<json>'`):
- `fixative` `{"kind": "final"|"workable", "strength": 1, "region": {...}}`: locks the dust, so it no longer smudges or erases, and darkens the drawing slightly (about 4% at full strength). `workable` (in a region, between layers) also restores some tooth so that more charcoal will take.
- `lift` `{"points": [[x, y, r], ...], "kind": "kneaded"|"eraser", "pressure": 0.8}`: highlights lifted with an eraser. Do this before the final fixative, because fixed charcoal won't lift.
- `clean` `{"margin": 30}` or `{"region": {...}}`: lifts dust and smudges from the margins or from outside a region.
- `accents` `{"strokes": [{"pts": [...], "color": "#000000", "size": 5}], "n": 6}`: the last darkest accents in compressed charcoal. It refuses more than `n` strokes.

**Order of work.** Tone the paper with `glaze`, or start white. Block in the big shapes with `vine_side`, then rub with the stump or finger. Draw into it with `vine_tip`. Take out the lights with `kneaded` and `eraser`. Put the darkest darks in with `compressed_*`, add `white_chalk` on toned paper, then `finish lift`, `finish accents` and `finish fixative`.

**Limits.** The paper's tooth is a texture (a fine noise, the laid lines on Ingres), not real fibres, so at close range the grain can look slightly regular. There is no stick wear or breakage, and there is no water (no wash with compressed charcoal). The darkening that fixative causes is a fixed small value. Charcoal can't make colour: blue and red come out as their values. `sign` signs the same way as in oil.

## Calibration

**What comes from research.** Everything here is qualitative or structural. I searched for numbers and found none I could use (see "Searched, not found" below).
- The structure of the model is Sousa & Buchanan's observational model of pencil on paper [S27] ([Graphics Interface 1999](https://graphicsinterface.org/wp-content/uploads/gi1999-21.pdf)): the paper as a height field, deposit capped by how much the tooth can hold, a blender that picks dust up and lays it down again, and erasers that lift. That paper gives the structure but not usable numbers; most of its coefficients were also lost in the PDF's text extraction.
- The behaviour comes from MEDIA.md [S12][S13]. Vine charcoal is lighter, irregular and nearly fully erasable. Compressed charcoal is denser and blacker, harder to erase, and leaves ghosts. Light pressure marks the peaks first, a full tooth takes no more charcoal, and charcoal has a velvety, matte, non-reflective black.
- The direction of fixative darkening comes from FINISHING.md: fixative darkens charcoal slightly, and less than pastel [S11][S12]. The size, 4% at strength 1, is FINISHING.md's own "engineering starting value", not a measurement.

**Hand-tuned by eye** (starting values, to be replaced by the museum-crop calibration):
- Pigment colours: vine `(0.215, 0.205, 0.20)`, compressed `(0.055, 0.052, 0.058)`, charcoal pencil 0.09, white chalk `(0.95, 0.94, 0.90)`.
- Coverage per deposit `KC = 3.5`, so one heavy pass reaches about 96% coverage.
- Tooth capacity per support (`cap`: drawing 1.0, toned 1.0, Ingres 0.85), catch softness `w` (0.38, 0.32) and `grab`.
- Pressure → reach `(0.1 + 1.25·p)·reach_tool`; the "crushed dust in the hollows" term `0.22·p²`; how hard the hand presses for an asked value `p·(0.5 + 0.75·want)`; the per-pixel overshoot 0.12 past the asked value.
- Per-tool flow, reach, loose and stain fractions (the table in `Charcoal.TOOLS`). Bound-pigment erasability 0.55.
- Blender blur, drag and pick-up rates, and the spreading boost (capped at 1.6×; its physical basis is that an even film covers more than the same dust in clumps, but the size is tuned). Eraser lift rates.
- The paper textures: the noise scales (0.85, 2.2 and 8 px), the laid-line period of 4.3 px and the chain-line spacing of 112 px. These assume about 0.4 mm per pixel, which is also an assumption.
- Render: the grain relief ±3.5% and the 6% "velvet" deepening of dense darks.
- The size caps (26 px for a tip, 140 px for a side) assume about 0.4 mm/px and typical stick sizes.

**Searched, not found.** No published reflectance for vine or compressed charcoal. The Getty "Noir" project and Trentelman et al. 2019 ([Heritage Science](https://link.springer.com/10.1186/s40494-019-0286-6)) analyse black drawing media spectroscopically, but they report no usable values and say the media differ only subtly to the eye. No measured fixative colour change on charcoal or pastel. No profilometry of artists' papers (roughness Ra) that I could reach. The museum-crop step should fit:
1. the darkest value of each tool;
2. coverage against pressure (the fraction of bare paper in mid-tones);
3. the size of the grain against the paper's texture scale;
4. the value shift caused by fixative.
