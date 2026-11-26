# Calibration: graphite toward hyperrealism

Medium: `studio/v8/media/drymedia.py` (`Graphite`, shared `DryTool` and `DryMedium`). Style: `docs/styles/graphite-hyperrealism.md`. Base calibration of the pencil itself: `graphite.md`. Done Nov 26, 2026. Sheets: `docs/gallery/graphite_hyperreal_*.jpg`.

## The rulers (why these)

Hyperrealist drawings are in copyright, so there is no public-domain sample of the style itself. Two honest stand-ins, both in `studio/targets.parts/graphite-hyperrealism.json`:

1. **What the drawing imitates: a black-and-white photograph.** 45 random items from the Library of Congress FSA/OWI Black-and-White Negatives (public domain, "no known restrictions"), film rebate cropped, measured with `eyes.measure` as `tools/measure_targets.py` measures paintings. They are 1930s-40s documentary photographs, not the studio still lifes and close-ups a hyperrealist photographs today, so the ruler is right about photographic value range, focus and edges, and weak on subject and composition. The Met's public-domain photographs were tried first: 3000 sampled records gave mostly 19th-century albumen and salted-paper prints (faded, toned, low contrast), a poor stand-in for a modern photograph.
2. **What graphite on paper reaches when highly finished:** the most worked window (the head) of 8 finished 19th-century graphite portraits at The Met (CC0; object ids in the file), measured the same way plus fine-scale statistics at the studio's 5 px/mm.

| measure | photographs (n 45) | finished graphite drawings (n 8) |
|---|---|---|
| key, L* | 50.1 ± 12.3 | 82.9 ± 5.9 |
| spread, L* | 21.1 ± 5.0 | 10.6 ± 3.6 |
| p5 - p95, L* | 17.1 - 82.1 | 60.1 - 91.6 |
| share of darks / lights | 0.29 / 0.32 | 0.01 / 0.90 |
| edge density / hard-edge share | 0.31 / 0.17 | 0.20 / 0.03 |
| spectral slope | -1.24 ± 0.22 | -1.13 ± 0.28 |
| fine grain in flat passages (L* std, 5 px/mm) | | 0.82 ± 0.34 |
| 0.5-5 mm mottle in flat passages | | 1.59 ± 0.38 |
| darkest 0.1%, L* | | 42.0 ± 8.8 |

The two disagree sharply: academic graphite is high-key and soft-edged; a photograph is mid-key, twice as contrasted, with six times the share of hard edges. Hyperrealism aims at the photograph, so the photographs are the style target (`report`, once merged); the drawings set the smoothness a finished graphite surface reaches.

## Marks measured (vellum unless named; render at 5 px/mm)

| what | measured | set from |
|---|---|---|
| lead widths (`mech_03/05/07`, medium pressure) | 0.2-0.37 mm / 0.37-0.6 mm / 0.37-0.6 mm (distance-transform widths; a 1.5 px line is below the photo-blur limit) | lead diameters (source) |
| darkest line, 1 pass: mech_05 HB, mech_05 4B, 8B | L* 53, 40, 33-35 | grade ramp (`graphite.md`) |
| darkest **area**, 8 layers of 8B, blended | L* 42 (drawing, vellum, plate 42-44) | matches the source's Munsell value 4 (about L* 41) past which graphite only shines |
| darkest area, carbon pencil x4, blended | L* 31.6 (grain 0.1) | charcoal's measured pencil (L* 26 full cover) |
| indented groove under a blended tone of L* 48 | L* 97.9 (paper 96.5) | source: stays white under heavy shading |
| lift from a blended L* 48 tone: kneaded / hard eraser / eraser pen / battery eraser | L* 57-60 / 81-85 / 88-91 / 95-97 | order from the sources ("almost perfectly" for the battery eraser); rates by eye |
| hard over soft: 4B hatching, then 2H over it | grain 13.0 -> 6.5 L*, white flecks 5.3% -> 0.3% | direction from the sources; amount (`fill`) by eye |
| flat tone, mech_05 HB x4 then soft brush: drawing / vellum / plate | grain 0.63 / 0.24-0.40 / 0.20 L*; mottle 0.47 / 0.19 / 0.09 | finished drawings: grain 0.8 ± 0.3, mottle 1.6 ± 0.4 (so blended tone is as smooth as a finished drawing, or smoother) |
| same with a stump | grain 0.62 / 0.25-0.43 / 0.24; mottle 1.0 / 0.42 / 0.11 | |
| core `hatch` on drawing paper at the measured spacing (the old calibration test), before / after `fill` | grain in tone 7.07 / 6.82 L*, paper in marks 0.050 / 0.051 | target 5.2 (`graphite.md`): a small step toward it |

## The test drawing

A self-rendered "photograph" (an egg and a crumpled sheet of paper on a table, one light from the upper left, the wall and far table out of focus: `graphite_hyperreal_reference.jpg`), drawn at **2400 x 3200 px on vellum** (48 x 64 cm) with the tools only: a 2H `transfer`; nine value bands of `hatch` per part, darkest first (carbon, 8B, mechanical 0.5 mm 4B to 2H), each `clip`ped to its part (wall, table, egg, paper as polygons); masked `brush` blending; three rounds of value-seeking `match` and blending; carbon darks; `kneaded`, `precision_eraser` and `electric_eraser` lifts with `"seek": true`; an 8B contact accent. Then, after the sheen fix below, a second sitting: one more blending pass on the egg, a large soft brush over wall and table, carbon darks and lifts again. `graphite_hyperreal_test.jpg` (final), `_compare.jpg` (reference, first sitting, second sitting), `_details.jpg` (egg and paper at 1:1 beside the reference).

| measure | drawing, sitting 1 | drawing, sitting 2 | reference |
|---|---|---|---|
| mean L* error per part: egg / paper / wall / table | 6.4 / 1.9 / 0.9 / 1.1 | 5.9 / 1.9 / 0.75 / 1.2 | 0 |
| key / spread / p5 / p95, L* | 62.2 / 9.2 / 48.1 / 75.9 | 62.3 / 9.2 / 48.1 / 75.9 | 62.0 / 11.0 / 46.0 / 76.6 |
| darkest 0.1%, L* | 36.2 | 35.8 | 8.8 |
| egg mean L* | 58.8 | 58.5 | 53.1 |
| smooth passages, grain / mottle: wall | 0.38 / 0.25 | 0.34 / 0.07 | 0.00 / 0.06 |
| egg | 0.79 / 1.40 | 0.54 / 1.40 | 0.11 / 2.75 |
| table | 0.30 / 0.44 | 0.30 / 0.31 | 0.00 / 0.58 |
| edge rise 10-90%: egg silhouette / paper facets, mm | 1.3 / 1.9 | 1.5 / 1.9 | 1.7 / 1.7 |
| edge density / hard-edge share | 0.028 / 0.015 | 0.024 / 0.010 | 0.036 / 0.116 |
| spectral slope | -1.69 | -1.63 | -1.54 |

Against the photographs' target the drawing is too low in contrast (spread 9 vs 21) and has too few hard edges, but so is the reference scene itself (spread 11, z -2.0): it is a soft, mid-key still life. Against its own reference the drawing gets the values of the out-of-focus wall and table within 1 L*, as smooth as the reference at 0.5-5 mm, and the paper's facets with photographic edge widths. It misses the darks (graphite and carbon stop at L* 32-36; the reference goes to 9), the egg's core shadow (too light by 5 L*), and the hard edges where the egg's shadow side meets its cast shadow.

**Timings (2 vCPU), first sitting 70 min:** new 16 s, transfer 5 s, tone bands 33 min (the long full-width middle bands cost about 3 min per layer), blending 26 min, three correction rounds 7 min, darks, lifts and accents 3 min. Second sitting 9 min (two large-brush passes over wall and table 7.5 min).

## Engine changes (Nov 26, 2026)

- **Speed:** a point's stroke (pencil, mechanical pencil, charcoal and pastel tips) lays all its contacts at once (vectorised; bit-identical up to float16 rounding): a 1-layer pencil hatch over an eighth of the sheet 6.2 -> 2.8 s at 1200 x 1600 and 26 -> 10.9 s at 2400 x 3200. Blenders blur colour, deposit, loose dust, coverage and sheen in one call (identical result). The new blenders and erasers act once per 0.3 radii of travel with the travel summed, instead of at every contact the core lays.
- **Canvas size** (graphite, vellum): an empty episode (load, save, render) 0.7 s at 1200 x 1600, 1.9 s at 2400 x 3200, about 12 s at 3600 x 4800 (with another job on the CPU), where the canvas state is 516 MB on disk. A full-sheet glaze 0.75 / 2.2 / 16 s. Stroke work scales with the area: 2400 x 3200 is practical (an hour or so per drawing); 3600 x 4800 runs but every episode carries 12 s before the first mark.
- **Supports** `vellum`, `plate`, `hot_press`, with a `tooth` depth (how far the same pressure reaches into a shallower relief). Their order (plate smoothest, holds least, palest darks; vellum deeper darks; hot press many layers) is from the sources; `cap`, `w`, `tooth`, `relief` are tuned by eye against the flat-tone grain above.
- **Tools:** `mech_03/05/07` (fixed lead width, grade capped by the lead: source), `carbon_pencil` (charcoal's measured pencil), `brush`, `tortillon`, `chamois`, `precision_eraser` (2.3 mm tip at most), `electric_eraser` (removes 97% of bound graphite: "almost perfectly"; 5 mm at most, **judgement**). All rates tuned by eye.
- **Hard over soft:** every grade now smooths the graphite already in the tooth under its stroke by `fill` = 0.7 (1 - softness)^2 (6H 0.70, 2H 0.50, HB 0.33, 2B 0.20, 4B 0.10, 8B 0.004): direction from the sources, amount by eye.
- **Indents stay white:** the crushed-dust smear, powder (`glaze`) and blenders skip a groove; a blender no longer spreads a groove's white into the tone around it.
- **Masked blending:** with `clip`, a blender spreads only what lies inside the region (edges stay crisp). Applies to charcoal and pastel blenders too.
- **Sheen:** blenders smear the shine with the graphite (it stayed in the shape of the hatching and showed as line texture after blending: blended 8B grain 2.7 -> 1.7 L*); the raking-light term of the shine is scaled by the support's relief (unchanged on drawing paper).
- **`"seek": true`** on an eraser: lift toward the asked value and stop (with `match`, the schema's).
- **`transfer`** for graphite: the schema's contours drawn with a 2H pencil on the tooth (the core's transfer mixed a brown line into the colour).
- `brush` pick-up 0.05 -> 0.02 (tuned by eye: at 0.05 repeated passes lifted the darks).

## What still limits hyperrealism

1. **Value bands step.** Core `hatch` stopped a layer abruptly where the schema crosses its level, so a smooth gradient was laid as steps; blending softened them, but faint diagonal steps stayed on the wall and the egg's terminator turned into a soft line. **Since Nov 26, 2026** the freehand hatch feathers each layer's pressure across its level (`feather`, default 0.08 of the value range; docs/MANUAL.md). Test: a 600 x 400 px ramp (schema value 0.30 to 0.92) on vellum, hatched in seven one-layer bands darkest first as in the recipe (carbon, 8B, `mech_05` 4B, 2B, HB, 2H x2; spacing 3, size 2), then blended with a 30 px `brush` at three angles; column means of L* after a 1 mm blur, residual from a 5 mm smoothing: unblended, the steepest step fell from 1.14 to 0.41 L* per px and the residual from 1.57 to 0.96 L* (max 4.8 -> 2.4); blended, the steepest step from 0.32 to 0.27 and the residual from 0.52 to 0.44 L* (max 2.6 -> 2.0). `docs/gallery/graphite_hatch_feather.jpg`. What is left after blending is mostly the bands' different grades and grain, not their edges.
2. **The darks.** Graphite stops near L* 40 as an area (as the source says) and carbon near L* 32; a photograph reaches L* 9-17. Even darks that carbon could reach (the egg's core shadow) stay about 5 L* light, because blending passes lift them and the tooth is full after the bands (lay the carbon first and blend it less).
3. **Edges between two dark tones** (the egg's shadow side against its cast shadow) are lost: `match` lays dashes that follow the form, and blending clipped to one part can't sharpen the line between two dark parts. A tool that sharpens an edge along a contour (a precision eraser or a hard pencil drawn along the schema's edge) is missing.
4. **`match` leaves dashes** that need blending, and the contact accent stays a visible strip of short marks. In the darks the hand's marks are still legible at 1:1.
5. **Masks were polygons written by hand** (a part with a hole is one polygon with a slit). Since Nov 26, 2026 a region can be a part of the schema: `{"type": "segment", "at": [x, y]}`, the connected area of similar value (or colour) around the point, with its holes (docs/MANUAL.md, "Regions"). Its tolerance is a judgement; on a photograph with gradients a part may leak into a neighbour of similar value, so check it (or `grow` -2) before a long hatch.
6. **Resolution:** at 5 px/mm a 0.3 mm lead is 1.5 px, below the photograph's blur, so hair-fine detail has to be drawn enlarged (which is what hyperrealists do: large sheets).
7. **Fixed raking light** for the shine; no movable light, no gloss measurement.
8. **Time:** about 80 minutes for one 48 x 64 cm drawing on 2 vCPU, two thirds of it in full-width tone layers and large blending passes.
