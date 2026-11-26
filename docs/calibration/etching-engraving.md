# Calibration report: burin, etching needle, drypoint and the print finish (`ink` medium, supports `plate_laid`, `plate_wove`)

Nov 26, 2026. The style is `docs/styles/etching-engraving.md`. The method and the line ruler (`tools/calibrate_media.py --kind line`) are as in `docs/calibration/pen-and-ink-illustration.md` §1. The engine is `studio/v8/media/ink.py` (`BURIN_*`, `NEEDLES`, `BITE_*`, `TREMOR_MM`, `DRY_BURR`, `_line`, `_bite_profile`, `_etch_stroke`, `_bite`, `_wipe`, `_platemark`, `_lozenge`).

## 1. References

`studio/calibration_refs.parts/etching-engraving.json`: 8 burin engravings (1512-1598) and 11 etchings, four with drypoint (c. 1667-1900), public domain at The Met, photographed at 9.3-34 px/mm (engravings median 16, etchings 13). Crops are automatic, checked on a contact sheet. Two scales are approximate (434382 and 377346 differ 6-9% between height and width; 829968 differs 15% and is 5.7 px/mm). The style target (`studio/targets.parts/etching-engraving.json`) is `eyes.measure` on 60 prints from a pool of 705 cached records (the rule in `tools/measure_targets.py`).

| statistic (median of works, IQR between works) | engraving (n = 8) | etching (n = 11) |
|---|---|---|
| line width | 0.23 mm (0.18-0.29) | 0.36 mm (0.30-0.41) |
| widest tenth / median | 2.17 (2.05-2.54) | 1.92 (1.77-2.29) |
| width CV along lines | 0.35 (0.32-0.36) | 0.33 (0.30-0.36) |
| free-end ratio, lower quartile | 0.76 (0.76-0.80) | 0.80 (0.76-0.82) |
| hatch spacing | 0.30 mm (0.23-0.34) | 0.43 mm (0.42-0.47) |
| cross-hatched share, crossing angle | 0.46, 55° (50-62) | 0.46, 60° (60-75) |
| lines per mm: L* ≥ 80 / 60-80 / 40-60 / < 40 | – / 2.52 / 3.47 / 4.37 | 0.34 / 1.45 / 2.29 / 2.31 |
| cross-hatched share, same bands | – / 0.49 / 0.44 / 0.75 | 0.10 / 0.46 / 0.39 / 0.55 |
| hard-edge share, orientation coherence | 0.41, 0.62 | 0.38, 0.64 |
| paper (CIELAB as photographed) | (84.6, 1.3, 11.2) | (86.8, 1.5, 10.2) |

Ink colour: the absorption ratio -ln(core/paper) per linear RGB channel, normalised. Black ink median 0.973 : 1.003 : 1.015 (17 prints). The one print catalogued "printed in dark brown ink" reads 0.826 : 0.961 : 1.213. Record counts (MetObjects.csv, black-and-white etchings 1850-1925, n = 1,380): 77 catalogued in brown, sepia or bistre ink, 180 in black ink, the rest unstated. Papers named: laid 265, wove 67, Japan or chine 140.

`eyes` target (60 prints): key L* 67.4 ± 9.6, spread 18.5 ± 3.8, darks 0.09 ± 0.09, lights 0.61 ± 0.20, edge density 0.44 ± 0.13, hard-edge share 0.17 ± 0.06, spectral slope -0.82 ± 0.15.

## 2. What was built

- **`burin`** (alias `graver`): a whole-line tool like the illustration pen, smoothed below `BURIN_SMOOTH_MM` (the plate is turned against a steady push, so there is no tremor). Its width is `BURIN_W` × an entry taper (`BURIN_IN_MM`: the burin enters at a low angle) × an exit taper (`BURIN_OUT_MM`: lifted out) × √(pressure) × a slow swell (`BURIN_SWELL`). With a schema, it swells where the schema is darker: the engraver cuts deeper into shadow. A shallow cut holds less ink, so the tapers print greyer (ink 0.5-1 by width).
- **`needle`** (alias `etching_needle`): even width (`NEEDLES` fine / medium / coarse), round ends, a slight tremble (`TREMOR_MM`, more when fast). Each line opens the ground (`etch` array) and is bitten `bite` minutes (default `BITE_DEFAULT`; the `bite` array keeps the minutes). The printed line is `1 - exp(-minutes/BITE_TAU)` of the darkest ink, widened by `BITE_LAT` mm per minute on each side.
- **`finish bite`**: a further biting stage for every open line inside `region` and/or where the schema is darker than `where_darker` (the rest is stopped out). Lines bitten for different times keep their own depth.
- **`drypoint`** (alias `dry_point`): a fine furrow (0.04-0.1 mm, ink 0.7) and a burr band on one side (`burr_side`), soft, ragged along the line, density `DRY_BURR`.
- **`finish lozenge`**: dot-and-lozenge. Enclosed paper cells of lozenge size (0.12-1.3 mm across) inside the region (and darker than `level` in the schema) get a burin dot drawn out to a point.
- **`finish wipe`**: plate tone (`tone`, default 0.05), streaked along a wiping direction, wiped cleaner in the lights (`clean_lights`), with `retroussage` spreading ink from the lines. It stays inside the platemark.
- **`finish platemark`**: the plate's edge with a margin (`margin`, `margin_mm` or `rect`). The margin takes no ink and is wiped back to paper. In renders the paper inside the plate is pressed smoother and the bevel shades top/left and catches light bottom/right.
- **Supports `plate_laid`** (laid lines about 1 mm, chain lines 24 mm, as `laid_paper`) and **`plate_wove`**: no bleed, 10 px/mm by default, tone `#e4d8c6` (the references' median paper). **Ink kinds** `intaglio_black` and `intaglio_brown` (measured ratios). Plate tools print one ink: a colour asked for gives only the darkness.
- The illustration pen's area-coverage fix (`_area`) applies to all of these.

## 3. Before and after

Patches as for the pen: 420 × 420 px at 10 px/mm on `plate_laid`, the core's `hatch` at 0.4 mm spacing (one family, or two crossing at 55°), resampled to 16 px/mm (engraving) or 13 px/mm (etching), blurred σ 0.6 px in linear light. "Before" is the old flexible pen, the nearest tool there was.

| statistic | before: flex pen, one / crossed | burin, one / crossed | needle (10 min), one / crossed | references: engraving / etching |
|---|---|---|---|---|
| line width, mm | 0.29 / 0.44 | 0.24 / 0.35 | 0.20 / 0.28 | 0.23 / 0.36 |
| widest tenth / median | 1.72 / 2.0 | 1.53 / 1.81 | 1.53 / 1.69 | 2.17 / 1.92 |
| width CV along lines | 0.26 / 0.49 | 0.25 / 0.31 | 0.27 / 0.37 | 0.35 / 0.33 |
| free-end ratio, lower quartile | 0.96 / 1.0 | 0.51 / 0.85 | 0.91 / 0.79 | 0.76 / 0.80 |
| coherence | 0.90 / 0.38 | 0.97 / 0.57 | 0.88 / 0.46 | 0.62 / 0.64 |

The burin's tapers show in sparse hatching (0.51). The needle's round ends stay blunt (0.91), as the references' difference suggests (etching 0.80 against engraving 0.76).

**Bite, as modelled (shown on the mark sheet as Lalanne's test strip, 3 / 6 / 10 / 20 / 30 minutes, medium needle):** printed ink 0.31 / 0.53 / 0.71 / 0.92 / 0.98 of the darkest. Width 0.185 / 0.20 / 0.22 / 0.27 / 0.32 mm (needle 0.17 mm + 2 × 0.0025 mm per minute).

**Etching test** (`docs/gallery/ink_etching_drawing.jpg`): a public-domain Met etching (829968, 1865) greyed and softened as the schema, 1000 × 1240 px at 10 px/mm. Needle `hatch` (spacing 5 px, `cross` 60, `layers` [0.72, 0.5, 0.3], `bite` 4), needle `match` (`bite` 4), `finish bite` 6 min where darker than 0.55, then 8 min where darker than 0.33, drypoint accents, `platemark`, `wipe` (tone 0.05, retroussage 0.25). Line measures are on five crops at 13 px/mm.

| statistic | etching test | etching references / target |
|---|---|---|
| line width | 0.38 mm | 0.36 (0.30-0.41) |
| widest tenth / median | 1.84 | 1.92 |
| width CV along lines | 0.29 | 0.33 |
| free-end ratio, lower quartile | 0.81 | 0.80 |
| spacing; cross-hatched share; angle | 0.50 mm; 0.59; 50° | 0.43; 0.46; 60° |
| lines per mm: L* ≥ 80 / 60-80 / 40-60 / < 40 | 0.23 / 1.73 / 2.68 / 3.10 | 0.34 / 1.45 / 2.29 / 2.31 |
| key, spread, darks (eyes) | 60.5, 24.7, 0.20 | 67.4 ± 9.6, 18.5 ± 3.8, 0.09 ± 0.09 |
| hard-edge share, spectral slope (eyes) | 0.10, -0.91 | 0.17 ± 0.06, -0.82 ± 0.15 |

The first version had `BITE_LAT` 0.0045 mm/min, a 0.2 mm needle, four hatch layers and a 30-minute total bite. It measured 0.87 mm lines, widest tenth 3.7×, key 48 and darks 0.42: the darks closed into black mud. That set the lateral bite and the needle (data: width and its p90/median).

**Engraving test** (`docs/gallery/ink_etching_burin_drawing.jpg`): a public-domain Met engraving (397373, c. 1587) as the schema, 800 × 1100 px at 16 px/mm. Burin `match`, then burin `hatch` (spacing 5 px = 0.31 mm, `cross` 55, `layers` [0.75, 0.5, 0.3], length 260), `lozenge` (level 0.5), `platemark`, `wipe` (tone 0.02). Measured at 16 px/mm: line width 0.38 mm (references 0.23), widest tenth / median 3.25 (2.17), CV 0.40 (0.35), free-end ratio 0.63 (0.76), spacing 0.41 mm (0.30), cross-hatched share 0.28 (0.46), lines per mm 1.0 / 2.1 / 2.9 at L* 60-80 / 40-60 / < 40 (2.5 / 3.5 / 4.4). Eyes: key 61, spread 34 (18.5 ± 3.8), darks 0.27 (0.09 ± 0.09).

## 4. What is from data and what is by eye

- From data (the reference statistic named): `BURIN_W` 0.18 mm (engraving width), `BURIN_IN_MM` / `BURIN_OUT_MM` 1.0 / 1.6 (free-end ratio and CV), `BURIN_SWELL` 0.25 (width CV), `BITE_LAT` 0.0025 mm/min and the medium needle 0.17 mm (etching width and its widest tenth), the ink ratios, the paper tone, and the spacings and crossing angles recommended in the style.
- From the literature: that bite deepens **and** widens lines and that deeper lines print darker (Met). Biting stages of 3-30 minutes with stopping-out (Lalanne). A fine and a coarse needle (Lalanne, sewing and embroidery needles). The burr's velvety black and one-sidedness (Met; Lalanne). Plate tone and retroussage (Met; Lalanne §89). The platemark (Met).
- By eye: `BITE_TAU` 8 min (darkness against minutes; Lalanne's strip only says the lightest is a "fine gray"), the fine and coarse needle sizes, `TREMOR_MM`, `BURIN_SMOOTH_MM`, `DRY_BURR` and the burr's width, the plate-tone density and streaks, the retroussage spread, the platemark bevel (0.5 mm) and its shading, the lozenge cell sizes and dot size, and the plate papers' textures and default scale.

## 5. What still falls short

- **Engraving systems.** The core `hatch` is a draughtsman's: spacing jitters ±15%, lines are pieces with offset ends, and each layer has one direction for the whole region. Engravings are regular, long, curved with the form, and finer: 4.4 lines per mm in the darks against 2.9 in the test. Lines also merge (the measured width doubles in crossed darks). Needed: a regular, form-following hatch in `studio.py` (see the list of requested changes). Until then, burin systems are best drawn as `strokes`.
- **Dot-and-lozenge** finds few lozenges in the test (crossed lines merge before cells form). It works where the crossing is open (mark sheet, top right).
- **Darks:** both tests are darker than the target (darks 0.20 and 0.27 against 0.09). The schemas are dark prints, and the test hatching's levels were not tuned to the target.
- **The etching test's hard-edge share at eyes' scale** is 0.10 against 0.17: plate tone and retroussage soften more than the references show. Use less tone for a crisp impression.
- Not modelled: aquatint, mezzotint, soft-ground, the reversal by the press, foul biting, the plate's wear across an edition, embossing of the lines themselves, chine collé.

## 6. The v8 hand and the plate tools (Nov 26, 2026)

`strokes` patches with the burin (30 parallel lines, pressure 0.75, 10 px/mm on `plate_laid`, measured at 16 px/mm), two seeds: plain 0.252 mm, auto articulation 0.237 mm, explicit swell 0.249; widest tenth / median 1.43-1.49, CV 0.26-0.28, end ratio 0.34-0.36 in every case. The burin normalises pressure by its own 90th percentile and takes its square root, so the v8 articulations barely move it; the drift is in `match` and `free` through the role size (see `pen-and-ink-illustration.md` §6). The plate tools take the same opt-out as the pen (plain stroke, no role or focus size, no core wave): after it, plain and auto are identical (0.256 mm, CV 0.27).

**Revision and finishing** (manual/ink.md): `scrape` on a plate takes the lines out of the metal (lighter print, `etch` and `bite` reduced, so a later bite doesn't restore them); `wipe` lays the plate wipe in that passage; `paintout` is refused. `report finish` checks the platemark, that the plate was wiped, and plate tone evenness: the median tone between the lines in a 4 × 4 grid of the plate, flagged when one cell holds 4× another's (eye).
