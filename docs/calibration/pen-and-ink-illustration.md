# Calibration report: the illustration pen (`ink` medium, `pen` with `nib`, `stipple`, support `illustration_board`)

Nov 26, 2026. The style is `docs/styles/pen-and-ink-illustration.md`. The method is as in `docs/media-data.md` ("Calibration method"), with a new line ruler (below). The engine is `studio/v8/media/ink.py` (`NIBS`, `PEN_*`, `_line`, `_strip`, `_area`).

## 1. References and the ruler

**Line statistics** (`tools/calibrate_media.py --kind line`, new: `lines()`). Coverage is c = 1 - Y/Y_paper in linear luminance. At each line centre (a ridge of c across the local line direction), the profile across the line is integrated out to the valleys on either side, and the integral is divided by the darkest ink's coverage. That gives an **equivalent width** that does not depend on the photograph's blur. Also measured: the next line centre beyond the valley (**spacing**), the CV of the width along each connected line, the width at free ends over the line's median width (**end ratio**), the share of 4 mm windows with two or more line directions (**cross-hatched share**) and the angle between them, and per value band (window mean L*) the line density (mm of line per mm², i.e. lines per mm) and the cross-hatched share. Ink and paper CIELAB are read at line cores and bare paper.

Checked on synthetic hatching (blurred, sampled like a photograph): widths 2 / 3 / 4 / 6 px read 2.3 / 3.24 / 4.19 / 5.95 px. Spacings 5 / 6 / 8 / 12 / 14 / 20 px read 5.0 / 6.0 / 7.5 / 11.5 / 14.0 / 20.0 px. Free ends of tapered, blunt and blob-ended strokes read 0.36, 0.99 and 1.12 (median). Floors: lines narrower than about 2 px read up to 0.6 px wide and with a width CV of 0.22. In dense cross-hatching, junctions count as free ends, so the **lower quartile** of the end ratio is used as the taper statistic. Merged neighbours read as one wide line, so widths in very dense passages are upper bounds.

**References** (`studio/calibration_refs.parts/pen-and-ink-illustration.json`, group `pen_illustration`): 10 public-domain pen-and-ink illustration drawings at The Met, 1875-1911, photographed at 7.2-14.8 px/mm (median 9.8). Three more drawings were excluded: their images are 615-700 px, 3.7-4 px/mm, below the lines' scale. Crops are automatic (detail in mid values, away from margins), checked on a contact sheet.

**Style target** (`studio/targets.parts/pen-and-ink-illustration.json`): `eyes.measure` on 58 drawings (the rule in `tools/measure_targets.py`: Drawings, pen and ink without wash, colour, chalk or charcoal, 1875-1920, trade designs excluded). Candidates come from The Met's Open Access CSV (`measure_targets.py index-csv`), because a random sample of the 186,000 Drawings and Prints records held only one such drawing in 300.

| reference statistic (median of 10 works, IQR between works) | value |
|---|---|
| line width | 0.39 mm (0.36-0.49) |
| widest tenth / median width | 2.19 (2.0-2.64) |
| width CV along lines | 0.32 (0.315-0.34) |
| free-end width ratio, lower quartile | 0.76 (0.75-0.80) |
| hatch spacing (dense crops) | 0.62 mm (0.55-0.68) |
| cross-hatched share of 4 mm windows | 0.38 (0.34-0.41), crossing angle 62° (60-70) |
| lines per mm: L* ≥ 80 / 60-80 / 40-60 / < 40 | 0.26 / 1.21 / 1.60 / 1.98 |
| cross-hatched share by the same bands | 0.19 / 0.42 / 0.36 / 0.37 |
| hard-edge share, orientation coherence | 0.43, 0.67 |
| ink at line cores, paper (CIELAB as photographed) | (36, 2.1, 10.2), (87.4, 1.2, 11.7) |
| ink absorption ratio R:G:B (-ln core/paper, normalised) | 0.954 : 1.0 : 1.037 |

The `eyes` target (58 drawings): key L* 76.8 ± 7.9, spread 15.5 ± 6.4, lights 0.82 ± 0.15, darks 0.06 ± 0.10, hard-edge share 0.19 ± 0.13, edge density 0.30 ± 0.15, spectral slope -0.73 ± 0.16.

## 2. What was built

- **`pen` with `nib`** (`crowquill`, `mapping`, `fine`, `stub`; aliases `crowquill`, `mapping_pen`, `pen_fine`, `pen_stub`), a new line tool. The core's dabs are recorded and the whole line is laid when the stroke ends. It is resampled at 0.5 px, smoothed below `PEN_SMOOTH_MM`, and filled as a strip of quads, supersampled 4×. The width in mm is `wmin + (wmax - wmin) · pressure^g · (NIB_DOWN + (1 - NIB_DOWN) · down)` (down = moving toward the drawer), times a slow swell of the hand (`PEN_RHYTHM`). A fast line lifts off to a point over `PEN_FLICK_MM` (more with speed). There is an occasional blot at a slow start (`NIB_BLOTS`). `size` 8 is the nib's normal line (width ∝ √(size/8)). The old `pen` (`flex`, `tech`, `reed`) is unchanged.
- **`stipple`**: pen dots along the stroke.
- **Area coverage** (`_area`). The line tools mix inked and bare paper by the area a pixel's coverage stands for. Before, the anti-aliased coverage went straight into Beer's law, which turned a half-covered edge pixel almost black and widened every thin line by about a pixel: a row of isolated lines drawn 0.32 mm wide measured 0.51 mm. After this fix and the linear-light blur of the measuring step (§3) they measure 0.41 mm, and the ruler's own bias at this width is about +0.05 mm. The existing tools keep the old composite and are byte-identical (checked on xuan_raw, bristol and laid paper).
- **Support `illustration_board`**: smooth, bleed 0.04, 6 px/mm by default (`SUP[...]["ppm"]`; `px_per_mm` in the meta still overrides). Its tone `#e7d9c5` is the references' median paper. Ink kind **`india`** has the measured ratio above.
- Physical scale: `Ink.ppm` now falls back to the support's own scale before the 4 px/mm default (only the new supports have one).

## 3. Before and after

Same ruler, same procedure: a 420 × 420 px patch at 6 px/mm, hatched with the core's `hatch` (value 0.1, 0.9 mm spacing, one family, or two crossing at 62°, size 8, pressure 0.75, felt arousal 0.45 / care 0.65). It is resampled to the references' 9.8 px/mm and blurred σ 0.6 px **in linear light** (an optical blur; blurring sRGB codes widened dark lines by about 0.1 mm), then cropped and measured. "Before" is the old flexible pen (the only pen there was) on `bristol`.

| statistic | before: flex pen, one family / crossed | after: crowquill, one family / crossed | references |
|---|---|---|---|
| line width, mm | 0.44 / 0.58 | 0.40 / 0.55 | 0.39 (0.36-0.49) |
| widest tenth / median | 1.16 / 1.69 | 1.44 / 1.60 | 2.19 |
| width CV along lines | 0.17 / 0.43 | 0.28 / 0.30 | 0.32 |
| free-end ratio, lower quartile | 0.91 / 1.00 | 0.70 / 0.73 | 0.76 |
| hard-edge share | 0.73 / 0.64 | 0.70 / 0.53 | 0.43 |

**Test drawing** (`docs/gallery/ink_penillustration_drawing.jpg`): a public-domain Met drawing (365760, 1883) greyed and softened as the schema, on 900 × 1280 px (15 × 21 cm). One `hatch` with the crowquill (spacing 6 px = 1 mm, `cross` 62, `layers` [0.72, 0.52, 0.35, 0.2], length 90, pressure 0.68). One `match` with the crowquill in `jiao` (sizes 6-12, threshold 0.35, `faithful` 0.3). The `eyes` measures are on the full drawing, the line measures on five crops resampled to 9.8 px/mm.

| statistic | test drawing | references / target |
|---|---|---|
| line width | 0.42 mm | 0.39 (0.36-0.49) |
| widest tenth / median | 1.65 | 2.19 |
| width CV along lines | 0.29 | 0.32 |
| free-end ratio, lower quartile | 0.71 | 0.76 |
| cross-hatched share, crossing angle | 0.19, 60° | 0.38, 62° |
| lines per mm: L* 40-60 / 60-80 / ≥ 80 | 1.48 / 0.86 / 0.00 | 1.60 / 1.21 / 0.26 |
| ink at cores, L* / b* | 30 / 6.7 | 36 / 10.2 (aged ink and photo blur) |
| key, spread, lights (eyes) | 72.7, 24.8, 0.73 | 76.8 ± 7.9, 15.5 ± 6.4, 0.82 ± 0.15 |
| edge density, hard-edge share (eyes) | 0.54, 0.31 | 0.30 ± 0.15, 0.19 ± 0.13 |
| spectral slope (eyes) | -0.82 | -0.73 ± 0.16 |

## 4. What is from data and what is by eye

- From data (the reference statistic named): the crowquill's mm range (`NIBS["crowquill"]` 0.09-0.5 mm, from the width median and spread), `PEN_RHYTHM` 0.38 (width CV), `PEN_FLICK_MM` 0.7 (free-end ratio), the `india` ink ratio, the board's tone, and the hatch spacing and crossing angle recommended in the style.
- From the literature, as an ordering only (Maginnis 1898): the mapping pen has the widest range, the crowquill is fine but responsive, the 303 is "average" and more uniform, the stub is broad. Their mm values are scaled from the crowquill **by eye**.
- By eye: `NIB_DOWN` 0.6, the pressure exponents, `PEN_SMOOTH_MM` 0.6, `NIB_BLOTS` 0.03, the stipple spacing (2.5 dot widths), the 6 px/mm default scale (a judgement within Harper's reduction ratios).

## 5. What still falls short

- **Too little width contrast.** The widest tenth is 1.4-1.65× the median against 2.2. The references mix heavy contours and accents with fine hatching. The test's `match` lays short marks, not the bold outlines an illustrator draws, so outlines belong to `strokes` drawn by the painter (`nib: "stub"` or pressure 1.1).
- **Too few lines in the half-lights and lights** (0.86 / 0 lines per mm against 1.21 / 0.26), **too few crossings** (0.19 against 0.38) and **too many edges** (eyes 0.54 against 0.30). These come from how the core `hatch` builds tone: one direction per value layer over the whole picture, a level cut-off, and pieces with seams. It is the hatching intention, not the pen. A form-following, value-graded hatch in `studio.py` (`do_hatch`) would close this; see the report's list of requested changes.
- Hard-edge share 0.53-0.70 against 0.43: the renders are cleaner than photographs of 130-year-old ink on aged board, which has bled slightly, faded and lost contrast. Not tuned away.
- Not modelled: reduction for print (lines thickening and greys closing up in the block), Chinese white, clay-board, scraping as a drawing tool.
