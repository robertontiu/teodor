# Calibration: woodblock (`studio/v8/media/woodblock.py`)

Nov 25, 2026. Method: `docs/media-data.md` ("Calibration method"); statistics from `tools/calibrate_media.py`, plus two scratch statistics described below. References: the 8 ukiyo-e prints in `studio/calibration_refs.json` (Hiroshige ×5, Hokusai ×3; Met, CC0). Scale: the studio canvas (1200×1600) is taken as a print of about 30×40 cm, **4 px/mm**; reference crops were resampled (Lanczos) from their catalogued px/mm (5-13) down to 4 px/mm, so marks are compared at the same physical scale and the same pixel size. (Upsampling the renders to the photographs' ~10 px/mm instead would have measured the renders' own pixels, not marks.) 56188 has no catalogued size and drops out at 4 px/mm.

## Reference statistics

Median (IQR, n). "Auto" = the suggested crops (detail-rich passages); "flat" = hand-chosen flat colour passages (320 px squares at full resolution: Hamamatsu sky and beach, Karasaki sea, Mii Temple sky and pink ground, Sazai Hall sky, Gyotoku sky, Tsukudajima water, Ōno sky; coordinates in the notes at the end).

| statistic | auto, full res | auto, 4 px/mm | flat, full res | flat, 4 px/mm |
|---|---|---|---|---|
| texture std L* (flat parts) | 5.8 (4.9-6.3, 8) | 7.8 (6.4-8.7, 7) | 3.2 (2.6-3.8, 9) | **2.9 (2.6-3.4, 8)** |
| mottle std L* (0.25-6 mm band) [scratch] | | | **3.5 (2.9-7.9, 9)** | (crops too small) |
| hard-edge share (rise ≤ 2 px) | 0.24 (0.24-0.28, 8) | 0.28 (0.27-0.34, 7) | 0.12 | 0.33 |
| edge rise 10-90 % | 0.63 mm | 1.9 mm (bimodal: ~30 % ≤ 0.5 mm, rest 1.5-3 mm) | | |
| keyline width (stroke width) | **0.35 mm (0.32-0.43, 7)** | 0.46 mm (0.46-0.87) | | |
| width CV along marks | **0.32 (0.28-0.35, 8)** | 0.38 (0.31-0.40) | | |
| orientation coherence | 0.55 (0.51-0.59, 8) | 0.56 (0.52-0.58) | | 0.45 (0.33-0.82) |
| colour levels covering 90 % of the area (Lab cells of 6) [scratch] | 63 (36-77) | 65 (51-78) | 9 (5-12) | 10.5 (7-13) |
| bare paper (45301 margin, n = 1) | | | std 2.1, mottle 1.1 | **std 1.3**, mottle 0.9 |

## Rendered, before and after

Flat fields: three `match` blocks (light ochre, mid blue, dark indigo) from a flat schema on `washi`, 1200×500, measured at 4 px/mm.

| field (median L*) | texture std before | after | mottle before | after | target (flat, 4 px/mm) |
|---|---|---|---|---|---|
| light (80) | 0.65 | 1.31 | 0.54 | 1.1 | 2.9 (2.6-3.4); light fields in the set 1.2-3.5 |
| mid (60) | 1.43 | 2.65 | 1.18 | 2.3 | |
| dark (30) | 1.93 | 3.74 | 1.57 | (field not flat enough for the scratch measure) | |
| bare paper | 0.40 | 1.25 (`PAPER_K` 0.22) | 0.35 | 0.95 | 1.3 / 0.9 (n = 1) |

Keyline (`key`, black, three pressures, 4 px/mm): size 2 → 0.25 mm (1 px floor), **size 3 → 0.46 mm (IQR 0.25-0.75), CV 0.33**, size 4 → 0.75 mm, size 6 → 0.87 mm, CV 0.26. Target 0.35 mm (0.46 mm at 4 px/mm), CV 0.32: size 3 is the match; the manual's old advice (4-10) was 2-3 times too thick for a print-scale canvas.

Scene test (schema of flat areas, `match` at sizes 40-70 then 16-30, a bokashi sky, keyline at size 3; `docs/gallery/woodblock_washi_scene.jpg`):

| crop | std L* before | after | mottle before | after | colour levels before | after |
|---|---|---|---|---|---|---|
| sky (bokashi) | 1.10 | 2.93 | 1.9 | (graded) | 5 | 9 |
| ground | 1.08 | 1.31 | 3.8 | 1.0 | 9 | 5 |
| hills | 2.28 | 3.40 | 6.1 | 7.1 | 16 | 4 |
| whole sheet: hard-edge share | 0.54 | 0.60 | | | 49 | 22 |

Time for the scene (600 `match` strokes, bokashi, keylines, render) was 26 s before and 37-39 s after on this machine.

## What changed

1. **Block structure (the "sausage" weakness).** The data say printed colour is flat fields bounded by the keyline, so a `block` is now a carved plank printed once:
   - with a schema (`match`, or `"carve": "region"`), the stroke marks which area; the carved shape is the schema's connected area within 12 delta-E of the colour under the stroke, stopping at printed keylines and running into their middle;
   - strokes of a colour within 8 delta-E of an earlier block, or whose carved area is more than 60 % already printed by one block, are that block: they add only the unprinted part with the block's film, registration slip and wood, so fields built from many strokes print as one even impression; `"reprint": true` overrides;
   - the block's colour is the area's schema colour plus any palette or `color_shift` the painter asked for (`match`'s sampling noise near region edges used to create near-duplicate blocks that printed over each other).
   - New state: `blk`, `blkc` (block id and coverage per pixel), `keyf` (key film), `meta["blocks"]` (colour, Lab, film, registration, wood offset). Canvases from before load with zeros and work.
2. **Bokashi** fades along the stroke's path (nearest path point), not by first touch of the round footprint; a wide bokashi stroke no longer leaves a curved edge with full-strength colour below it.
3. **Texture amplitudes from data:** `GRAIN` 0.2 → 0.3, `MOTTLE` 0.22 → 0.55, `FIBRE` (paper modulation of the film) 0.32 → 0.5, `PAPER_K` 0.07 → 0.22; the same constants now drive `glaze`. By eye (looking at the Hamamatsu sky at full resolution): the grain is more streaky figure (70 %) than regular rings (30 %, was 55 %), and the mottle more fine speckle (55 %, was 35 %).
4. **Keyline advice** in the manual: size 3 on a print-scale canvas.

## What could not be calibrated, and why

- **The sausage fix is not shown by a statistic.** The two scratch statistics (colour levels, mottle band) move in opposite directions between before and after for different crops: overlapping translucent shapes and printing texture both make value variation. The judgement that the new prints look like the references is by eye.
- **Hard-edge share** (0.28 at 4 px/mm) depends on the composition: the references' soft edges are bokashi and painted gradients. Carved edges render with a 10-90 % rise ≤ 0.5 mm, inside the references' hard mode.
- **Bare paper**: one margin crop (n = 1); washi fibre at full resolution (0.1 mm) is below the canvas's pixel.
- **Mottle (0.25-6 mm)**: the reference spread is wide (2.9-7.9) because flat passages include faint bokashi; the large-scale baren unevenness is not separable from gradients in these photographs.
- **Not measured, no data found:** baren pressure, pigment load per impression, registration error (kept at 0-2 px), the coarse woodcut paper and the gouge (no woodcut references in the set).
- **Colours:** ukiyo-e colourants (safflower, dayflower, plant yellows, gofun) are not in the FORS set; the manual lists the nearest measured pigments in gum arabic (hue measured, value approximate).

## Notes

Flat crops (x, y, w, h at full resolution): 37224 (986,604,320,320) and (986,2056,…); 56188 (616,2091); 57052 (614,305) and (614,2162); 55740 (1008,229); 57062 (989,146); 45301 (617,2140); 56212 (227,30); bare paper 45301 (70,1400,100,500). Scratch statistics: `mottle` = std of L* smoothed at 0.25 mm minus L* smoothed at 6 mm, in flat passages; `levels` = number of 6-unit Lab cells covering 90 % of the area.

## Key line (Nov 26, 2026)

Round 18's critic read the print as "a friendly editorial illustration", and the painter named the cause: one even black outline round everything. Ukiyo-e key lines are a brush drawing carved in the block: they swell and taper, are finer on faces and hands, heavier on outer contours and drapery, and hair is cut as many fine parallel lines (kewari).

**References.** 10 crops from 7 public-domain Met figure prints (Utamaro: 54860, 45100, 54859, 55043, 51137; Eishi: 53657; at 9.9-10.9 px/mm from their catalogued heights): 4 faces, 1 hand, 4 hair passages, 1 neck and collar contour; plus the 7 landscape references above. Solid black masses (hair masses, dark fields) were painted out to paper first (coverage over 0.5 surviving an opening of 0.6 mm), so the rulers see lines only. Two rulers: `tools/calibrate_media.py` `lines()` (equivalent width from integrated coverage) and the `strokes` method (Otsu threshold, width at the medial ridge, plus the widest tenth and the free-end ratio).

| | width, mm (lines / threshold) | widest tenth / median | width CV along lines | free-end ratio, lower quartile |
|---|---|---|---|---|
| faces (n = 4) | 0.29 / 0.14 | 2.0 / 2.9 | 0.35 / 0.40 | 0.74 / 0.94 |
| hands and fine contours (n = 2) | 0.21-0.22 / 0.10-0.19 | 2.8-3.2 / 1.9-4.7 | 0.36-0.38 / 0.37-0.40 | 0.74-0.77 / 0.76-0.81 |
| hair (n = 4) | 0.39 / 0.18; spacing 0.61-0.79 mm | 2.2 / 2.6 | 0.34 / 0.37 | 0.74 / 0.87 |
| landscapes (n = 7) | 0.46 / 0.18 | 2.1 / 2.6 | 0.35 / 0.41 | 0.77 / 0.81 |

The threshold widths sit at the photographs' one-pixel floor (0.1 mm) for the finest face lines, so the finest lines are 0.1 mm or less. The `lines()` widths include the paper's texture: on the studio's own washi a constant 2 px line reads 5.3 px with a CV of 0.29, so that ruler cannot resolve the tool's changes; the tool was measured on its key film (`keyf`, no paper texture), which is how the numbers below were taken.

**The tool, before and after** (40 curved `key` strokes of one size, auto articulation, care 0.8; key film at 20 px/mm, three seeds):

| | before | after | references |
|---|---|---|---|
| widest tenth / median | 1.32 | 1.97 | 2.0-2.7 |
| width CV along lines | 0.28 | 0.33 | 0.35-0.40 |
| free-end ratio, lower quartile | 0.47 | 0.72 | 0.74-0.84 |

Changes in `Cut` (woodblock.py): a slow swell along the line (`KEY_RHYTHM` 0.5, two incommensurate waves of 10-18 sizes and 0.43 of that: amplitude from the CV, wavelength by eye); a weight per stroke (`KEY_WEIGHT`, lognormal sd 0.4: from the widest tenth; the rest of the references' spread is the artist's choice of size by part); the core's ordinary landing and lift instead of the liner's long point (the end ratio: the old 0.47 was a brush point, the prints' ends are blunter, as a cut line); no break into dashes at light pressure. New: `"width_mm"` (the canvas's `px_per_mm`), and `"lines"`/`"spacing"` for hair (default spacing 0.65 mm: weak data, three hair crops; strands gather where the pressure is light and end one by one: eye). `report finish` measures the printed key line's widest tenth over its median and flags an even wire (below 1.6, a judgement).

## Reprints, seeds and the seal (Nov 26, 2026)

- **Reprint**: before, `"reprint": true` made every stroke a new block and printed its whole carved area, so a `match` with 70 seeds printed 70 impressions (round 18: the cat's head went maroon). Now a reprint is one more impression of the existing block per intention (`"reprint": n` for n), each stroke adding only the area this impression has not printed. Test (a 160 px disc, then a reprint `match` of 200 seeds, then a reprint of 3 strokes): the disc's colour went (0.77, 0.55, 0.30) → (0.70, 0.39, 0.16) → (0.64, 0.31, 0.12), one impression each.
- **Seeds**: the seed now ignores keyline pixels and the schema's anti-aliased edges (Lab gradient under 3 per px, eye), and takes the area of the stroke's own colour when the stroke touches it, else the colour most of it covers. Before, the median colour under a stroke bigger than a small area mixed it with its surround and found nothing (round 18's ears). Seeds that still find no area carve the stroke's shape and are reported at the episode's end with their position and colour.
- **Seal**: the brief forbids fake seals and fake Japanese signatures (`docs/styles/ukiyo-e.md`), and the manual had suggested a seal in Japanese script. The seal is now Teodor's own mark, TEO / DOR in Latin letters cut out of a red block; non-Latin text is refused. `sign` (and `finish seal {"mark": "signature"}`) cuts his handwritten signature in the keyblock.
