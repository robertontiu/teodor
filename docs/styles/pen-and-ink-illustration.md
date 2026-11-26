# Pen-and-ink illustration (the golden age of drawing for process, c. 1880-1920)

Researched 2026-11. Every value names its source. Values marked **judgement** have no published source and are editorial choices for Teodor. Values marked **measured** come from The Met's public-domain works (`studio/targets.parts/pen-and-ink-illustration.json`, `studio/calibration_refs.parts/pen-and-ink-illustration.json`, `docs/calibration/pen-and-ink-illustration.md`). This is a technique and a period. Illustrators are named only as historical context in the reference records. No setting follows one person's manner (rule 3, `docs/orchestration.md`).

## 1. In one paragraph
Between about 1880 and 1920, book and magazine illustration was drawn in pen and black ink for photomechanical "process" reproduction. A photograph of the drawing was printed onto a sensitised zinc plate, and the plate was etched in acid to a relief block that printed with the type. Charles G. Harper describes the albumen and bitumen processes on zinc, "generally three etchings ... each successive bath being of progressively stronger acid", and blocks cut from zinc "one-sixteenth to one-eighth of an inch in thickness" ([Harper 1894, *A Practical Hand-book of Drawing for Modern Methods of Reproduction*](https://archive.org/stream/apracticalhandb00harpgoog/apracticalhandb00harpgoog_djvu.txt)). A line block prints only black or nothing. So a pen drawing builds every value from black lines on white paper. In Charles Maginnis's words, "sharp black lines, of varying thickness, placed more or less closely together upon white paper", while "natural form depends primarily for its representation upon arbitrary boundary lines" ([Maginnis 1898, *Pen Drawing: An Illustrated Treatise*](https://archive.org/details/pendrawingillust00magi), also [Project Gutenberg #17502](https://www.gutenberg.org/ebooks/17502)). The aim was brilliance and economy. "The chief element of style is Economy of Means" (Maginnis).

## 2. How it carries feeling
- **Economy and air.** "If a shadow can be rendered with twenty strokes do not crowd in forty, as you will endanger its transparency" (Maginnis, rule 2). Light is the untouched paper. A drawing "pitched in a high key" has "brilliant blacks and large light areas, with often just enough half-tone to soften the effect" (Maginnis). The feeling is sunlit, clear and witty. Lightness itself is part of what it says (**judgement**).
- **The outline speaks.** "By mere outline, one may express the texture of a coat or a tree or a wall without any rendering whatever ... nothing in pen drawing is really of so much importance" (Maginnis). A broken outline, "sometimes omitting it altogether for a considerable space", lets light eat the form (Maginnis).
- **A few positive values.** "Have the values few and positive" (Maginnis, rule 3). Tone is grouped into a light, one or two half-tones and a black. This suits narrative and characterisation: a scene read at a glance (**judgement**).
- **Fit for Teodor's feelings:** wit, curiosity, nostalgia for a story, crisp morning light, a crowded street's bustle, comedy, gentle satire, the uncanny (a single black mass against white) (**judgement**). Poor fit: atmospheric vagueness and colour moods. The medium has no soft edges and no colour.
- **Avoided:** muddy, closely knit grey tones. They "darken and thicken in the printing" (Maginnis). Also avoid fussy over-neatness, the "curious bugbear of neatness" that "causes want of breadth and vigour" (Harper).

## 3. Media, supports and grounds
- **Nibs** (Maginnis, Materials): the Gillott crowquill ("the normal thickness of its line is extremely small, but ... it will respond vigorously to a big sweeping stroke"); the Gillott mapping pen ("surpasses the crow-quill in range ... It is astonishing how large a line may be made"); the 192 and 303 ("a very good average size", for "work demanding more or less uniformity of line"); the 404, beyond which coarse points are "stupid, unreliable affairs"; the commercial "stub" for decorative drawing; the quill for "broad, vigorous rendering of foreground effects"; the glass pen, "an absolutely uniform line". Steel pens first give "a hard, wiry line", then "grow sympathetic, and, finally, lose their temper" (Maginnis). Several sizes are used in one drawing (Maginnis).
- **Ink:** the blackest and least shiny. Prepared India inks had replaced ink ground from the stick, among them "Higgins' American (general and waterproof)" and "Encre de Chine Liquide" (Maginnis). Use waterproof ink over pencil or wherever Chinese white corrections go on top (Harper; Maginnis).
- **Paper:** "Bristol-board is probably the most popular of all surfaces for pen drawing. It is certainly that most approved by the process engraver" (Maginnis). Only the best board will take erasure with a knife. Whatman's hot-pressed paper is the alternative. Cold-pressed paper "gives an interesting broken line" (Maginnis). Early on, draughtsmen were told to use "only the blackest of Indian ink, upon Bristol-board, the thickest and smoothest and whitest that could be obtained" (Harper).
- **Scale and reduction.** Drawings were made larger than printed. "In the American magazines, the reduction is to about one quarter scale of the original drawing; but, working for process in England, the drawing should, generally speaking, be from two-thirds to one-half larger than the reproduction". The early rule was "a reduction in scale of one-third" (Harper). "In reproduction the lines tend to thicken and so to crowd out the light between them" and "the gray tones darken in proportion to the degree of reduction" (Maginnis). A concave "diminishing glass" previews the reduced drawing (Harper).
- **Measured on the originals:** line width median 0.39 mm at drawing scale (works 0.36-0.49), the widest tenth about 2.2 times the median, hatch spacing in dense passages 0.62 mm, paper L* 87 with b* 12 as photographed today (aged board) (**measured**, n = 10).
- **Teodor default:** medium `ink`, support `illustration_board` (6 px/mm: a 1200 × 1600 canvas is a 20 × 27 cm drawing, about 1.5-2× a magazine page's picture) (**judgement**, within Harper's reductions), ground `#e7d9c5` (the measured median board colour), ink `india`.

## 4. Palette
- **Principle:** one black ink on white board. Tone comes from line density, never from grey ink. A line block prints black or nothing (Harper, on the zinc processes). Grey washes belong to a different kind of reproduction (Harper treats wash drawings in their own chapter), so they are not part of this style (**judgement** on the consequence).
- **Colours:** ink `#000000` with `ink: "india"`, whose measured absorption is slightly warm (`[0.954, 1.0, 1.037]`, **measured**). Board `#e7d9c5` as the references look today. Fresh board was white, `#f7f4ec` (**judgement**). Chinese white `#f4f1ea` for corrections only, via `finish scrape` (**judgement**).
- **Avoid:** grey or diluted ink, washes, colour, tinted shadows.

## 5. Light and value
- A single, clear light. Shadows are rendered by hatching. Most of the sheet stays paper (**measured**: share of lights 0.82 ± 0.15 and key L* 77 ± 8 across 58 drawings; `eyes` measures in `targets.parts`).
- "Have the values few and positive": a gray tone kept distinct from the next, because "the blacks cannot ... grow blacker" while greys darken in reduction (Maginnis). The measured value spread is L* 15.5 ± 6.4. The histogram mostly shows one value group (1.1 ± 0.3), the paper (**measured**).
- Deep, quiet shadows can be cross-hatched (Maginnis: "the cross-hatch also affords a satisfactory method of obtaining deep, quiet shadows"). Shadows in sunlight are better left as open parallel lines, "sharp and clean, with never a suggestion of cross-hatch" (Maginnis).

## 6. Drawing and form
- The outline is the main convention. It is broken where light falls and heavier on the shadow side and under objects (Maginnis on broken outline; **judgement** on weight).
- Texture by line character. Maginnis's plate of "elementary combinations of line in expressing textures" (hats) shows stone, cloth and foliage each with its own stroke (Maginnis).
- Lines are made "clear and distinct". A weak line is not patched: "erase the offensive part completely" or paste a fresh piece of board and redraw (Maginnis, rule 1).
- Hatching follows a plane's direction or a constant angle. Cross-hatching at a sharp angle is "the only satisfactory cross-hatch at a large scale" (Maginnis). Measured crossing angle: median 62° (50-70) (**measured**).

## 7. Composition
- Vignettes and full-page plates. Large white areas carry the light and let the text page breathe (**judgement**; Maginnis on high key).
- A foreground accent of black and a light middle distance. For architecture, Maginnis gives two alternative "color-schemes": the archway as the principal dark with the walls light, or the reverse (Maginnis, Architectural drawing).
- Figures and story first. Backgrounds are suggested, and a few lines often stand for a whole wall (**judgement**).

## 8. Marks and edges
- **All edges hard.** Pen marks have no soft edge. The measured hard-edge share is 0.43 at the photographs' resolution (n = 10, `calibration_refs`) and 0.19 ± 0.13 at eyes' viewing scale (n = 58). Fine hatching reads as tone from a distance (**measured**).
- **Line width:** median 0.39 mm, IQR across works 0.36-0.49. The width varies along a line, CV 0.32, from the hand's pressure. Free ends: the lower quartile of the end-width ratio is 0.76, so many lines lift off thinner (**measured**).
- **Spacing and density by value:** lines per mm of 0.26 in the lights (L* ≥ 80), 1.2 at L* 60-80, 1.6 at L* 40-60 and 2.0 below L* 40. The share of cross-hatched passages is 0.19 / 0.42 / 0.36 / 0.37 in the same bands (**measured**, median of 10 works). Tone is built more by closing the spacing than by crossing.
- **Expedients, sparingly:** spatter, thumb prints and canvas grain rubbed with litho crayon (Maginnis, "fanciful expedients"). Stipple dots (**judgement**: a pen tone of its own, used for flesh and sky by some).

## 9. Process (the order of work)
Historical (Maginnis; Harper):
1. Pencil study, transferred or redrawn on Bristol board (or traced through thin bond paper).
2. Outline and principal darks in pen. Several nibs: fine for distance, broader for the foreground.
3. Tones by hatching, light to dark, with few and positive values. Keep the work open.
4. Corrections by scraping with a knife or Chinese white over waterproof ink. Clean up with stale bread, not rubber (Harper).
5. Mark the reproduction size ("< 4½ inches >", not "⅓ scale") and send to the process engraver (Harper).

Teodor's phases:
- **Drawing:** `pencil` construction lines from the schema (or `transfer`). Then `strokes` with `brush: "pen", nib: "crowquill"` for the outlines, `nib: "stub"` or pressure 1.1 for the heaviest accents.
- **Lay-in of tone:** `hatch` with the pen at the measured spacing (5-6 px at 6 px/mm = 0.8-1 mm). Cross-hatch only in the deepest shadow (`layers` with only the last level crossing). `angle` per plane.
- **Development:** a second, closer `hatch` (spacing 3.7 px = 0.62 mm) in the darks. `match` with the pen and `tone: "jiao"` at small sizes for edge accents. `stipple` sparingly.
- **Finishing:** `finish erase-pencil`, a few last blacks, `finish scrape` for a lost light, sign.

## 10. Finishing
- Finished meant **printable**. Every line clear and black, nothing patched, values few and distinct, work open enough to survive reduction (Maginnis rules 1-3; Harper). The original needed no "appearance of a finished picture or of delicate execution, so only it will wear this appearance when reduced" (Harper).
- Erase the pencil, check the drawing at reduced size (`look thumb`, the "diminishing glass"), then stop.

## 11. Pitfalls for Teodor
- **Grey mush:** tones too close or too dense, which close up in "reduction" (Maginnis's warning). Check `report`: the share of lights should stay near 0.8.
- **Mechanical hatching:** uniform machine-ruled lines everywhere ("the old mechanical process of constructing tones by cross-hatching is now almost obsolete", Maginnis). Vary the direction by plane, leave lights open, break the outline.
- **Pastiche of a famous illustrator's look** (Art Nouveau black masses, period costume romance) instead of Teodor's own subject drawn in the technique (**judgement**).
- **Nearest wrong feelings:** quaint nostalgia, a greeting-card "olde" charm, colouring-book outline (**judgement**).
- **Engine:** the core `hatch` lays one direction per value layer over the whole region. It does not turn with the form. Contour hatching needs `strokes` drawn by hand.

## 12. Engine mapping
- `new "#e7d9c5" 1200 1600 --medium ink --support illustration_board` (6 px/mm).
- Tools: `pen` with `nib` `crowquill` (default for this style), `mapping` (hairline to big swell), `fine` (even), `stub` (broad). Also `stipple`, `pencil` and `finish scrape`. Ink `"ink": "india"`, colour `#000000` (`tone: "jiao"` in `match`).
- `hatch` intention: `brush: "pen", nib: "crowquill", spacing: 5-6` (lights and half-tones), `3.7` (darks), `cross: 62`, `layers: [0.72, 0.52, 0.35, 0.2]`, `length: 90`, `pressure: 0.65-0.75`, `max_strokes: 40000` for a full sheet.
- Measured targets: `studio/targets.parts/pen-and-ink-illustration.json` (`report pen-and-ink-illustration` once merged).
- Felt bias: arousal +0.05, tension 0.0, care +0.3 (**judgement**: a sure, unhurried hand that still flicks its hatching).
- Gaps: the core `hatch` cannot follow the form or vary spacing within one intention. The pen does not yet model reduction for print (a `look` at the print scale would help). No Chinese white (opaque correction). No clay-board or scratchboard.

## 13. Sources
- C. D. Maginnis, *Pen Drawing: An Illustrated Treatise* (Boston: Bates & Guild, 1898), full text [archive.org](https://archive.org/download/pendrawingillust00magi/pendrawingillust00magi_djvu.txt), [Project Gutenberg #17502](https://www.gutenberg.org/ebooks/17502) (Gutenberg was down for maintenance during this research; the archive.org text was read). Covers nibs, inks, papers, rules for reproduction, cross-hatching, outline and economy.
- C. G. Harper, *A Practical Hand-book of Drawing for Modern Methods of Reproduction* (London: Chapman & Hall, 1894), full text [archive.org](https://archive.org/stream/apracticalhandb00harpgoog/apracticalhandb00harpgoog_djvu.txt). Covers zinc line blocks, reduction scales, Bristol board and Indian ink, the diminishing glass, cleaning with bread.
- The Met Open Access: 58 public-domain pen-and-ink drawings 1875-1920 (rule in `tools/measure_targets.py`, list in `targets.parts`), 10 measured at full resolution (`calibration_refs.parts`). Records and images CC0, [metmuseum.org/about-the-met/policies-and-documents/open-access](https://www.metmuseum.org/about-the-met/policies-and-documents/open-access). Candidates found with [MetObjects.csv](https://github.com/metmuseum/openaccess).
- Not read (catalogue records only): J. Pennell, *Pen Drawing and Pen Draughtsmen* (1889; [HathiTrust record](https://catalog.hathitrust.org/Record/001468914)); *The Studio* 1893, "Pen-Drawing for Process" ([Heidelberg digi](https://digi.ub.uni-heidelberg.de/diglit/studio1893/0170), refused automated requests). Nib widths in mm therefore come from the measurements, not from a period source.
