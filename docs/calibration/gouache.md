# Calibration: gouache (`studio/v8/media/opaque.py`, class `Gouache`)

Nov 25, 2026. Method: `docs/media-data.md`; statistics from `tools/calibrate_media.py` plus the scratch `mottle` statistic described in `docs/calibration/woodblock.md`. References: the 7 gouache works in `studio/calibration_refs.json`. Scale: the canvas as a 30×40 cm sheet, **4 px/mm**; reference crops resampled down to it (386569 has no catalogued size and drops out at 4 px/mm).

**The data are weak.** Five of the seven references are design drawings (pen, watercolour and bodycolour on paper) whose automatic crops are mostly paper and line; only two hand-chosen crops are flat passages of gouache paint (Degas, *Dancer Onstage*, the green floor; Pissarro, *The Cabbage Gatherers*, the sky). Three more hand-chosen crops (carriage bodies, a cabinet panel) turned out to be mostly paper or ink at the scale they were cut and were not used for targets.

## Reference statistics

| statistic | auto crops, full res (n = 7) | auto, 4 px/mm (n = 6) | flat gouache crops (Degas, Pissarro) full res → 4 px/mm |
|---|---|---|---|
| texture std L* (flat parts) | 4.5 (2.5-5.5) | 6.4 (3.1-7.5) | 3.0, 3.4 → **2.8, 2.7** |
| mottle std L* [scratch] | | | 6.4, 2.9 (full res) |
| orientation coherence | 0.57 (0.36-0.76) | 0.56 (0.39-0.76) | 0.36, 0.36 (all six hand crops: 0.50, 0.32-0.75) |
| hard-edge share | 0.16 (0.13-0.23) | 0.28 (0.13-0.48) | |
| edge rise | 0.68 mm (0.54-1.03) | | |
| paper share | 0.09 (0.06-0.18) | 0.09 (0.06-0.25) | |
| width CV along marks | 0.29 (0.26-0.33) | 0.36 (0.33-0.37) | |

## Rendered, before and after

Three flat fields (light ochre, green, dark blue), 20 overlapping `flat` strokes each at size 30, water 0.25, on `illustration_board`, dried, 4 px/mm (`watercolour_paper` gives the same numbers to two decimals: creamy paint hides the tooth).

| field (L*) | std L* before | after | mottle before | after | coherence before | after |
|---|---|---|---|---|---|---|
| light (79) | 1.80 | 2.80 | 1.5 | 2.1 | 0.96 | 0.25 |
| mid (57) | 2.36 | 2.34 | 1.8 | 1.9 | 0.94 | 0.36 |
| dark (31) | 3.61 | 2.31 | 1.2 | 1.2 | 0.94 | 0.75 |

Target: std about 2.7-2.8 (two crops), within the automatic crops' 2.5-5.5 at full resolution; coherence 0.36-0.50. Before, the field's texture was stripes: each single-coverage band between overlapping strokes let ~10-15 % of the board through (measured on a column profile: paint L 118 in overlaps, 131-147 in single coverage, for a paint of 115), which read as light seams and gave a coherence of 0.94-0.96.

## What changed

1. **Covering power of creamy paint** (by eye, no hiding-power data found): `cover` = 0.995 - 1.1·max(water - 0.15, 0)^1.5 (was 0.99 - 0.75·water^1.5): one creamy pass (water 0.25) now hides 96 % (was 90 %), water 0.5 77 %, water 0.8 42 %. Pressure scales coverage from 0.6 + 0.8p (was 0.45 + 0.8p).
2. **Bristle streaks of the flat scale with dilution** (by eye; the manual already said "diluted, it leaves faint streaks"): creamy paint fills between the bristles.
3. **Paint-body mottle** `BODY` 0.5 (new, in `render`): dried gouache is a slightly uneven chalky film; a noise at ~0.3 and ~1 mm modulates the value where paint covers, amplitude set to the flat crops' std L* (sweep: 0.12 → 1.6-2.1, 0.4 → 2.1-2.4, 0.6 → 2.4-3.2; 0.5 chosen).
4. **Colours:** `binder_palette("gum arabic")` returns the FORS masstones in gum arabic from `pigments.json` (hue measured, value and chroma approximate); listed in the manual page.

## What could not be calibrated, and why

- Flat-field targets rest on **two crops**; the other references are drawings.
- **Opacity / hiding power** of gouache: not found as data (handprint rates watercolour whites only: zinc white Tr 1, titanium white Tr 2 of 4, which says gouache whites should cover better than that but not by how much). The top target in `docs/media-data.md` (opaque white K and S from the oil whites) was not done: gouache still mixes with `kmix` and covers by area, so a two-constant model is the prerequisite (same finding as for oil: RGB `kmix` gets tinting strength wrong).
- **Paper share, hard-edge share, stroke widths**: properties of the compositions (design drawings with ink outlines), not of the medium.
- **Drying shift** (`SHIFT`): no measurement found.
- Rendered fields still show faint lighter seams between strokes at 4 % paper; the dark field's coherence (0.75) stays at the top of the reference range.
