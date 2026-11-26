# Calibration: egg tempera and gold ground (`studio/v8/media/opaque.py`, class `Tempera`)

Nov 25, 2026. Method: `docs/media-data.md`; statistics from `tools/calibrate_media.py` plus two scratch measures: `mottle` (see `docs/calibration/woodblock.md`) and an autocorrelation proxy for hatch stroke length (the 1/e length of the high-passed L* autocorrelation along the dominant line direction). References: the 8 gold-ground panels in `studio/calibration_refs.json`. Scale: the canvas as a 30×40 cm panel, **4 px/mm**; reference crops resampled down to it.

## Reference statistics

Hand-chosen crops: **hatched flesh** (Duccio, *Madonna and Child*: cheek, neck, the Child's face, 20 mm squares at 12.8 px/mm; Crivelli, *Pietà*: chest, belly, arm, the Magdalene's cheek, 20 mm at 5.6 px/mm; n = 7) and **plain gold** (Duccio, Daddi, Gaddi; n = 3).

| statistic | auto, full res (n = 8) | auto, 4 px/mm | flesh, full res | flesh, 4 px/mm | gold, full res | gold, 4 px/mm |
|---|---|---|---|---|---|---|
| hard-edge share | **0.25 (0.23-0.28)** | 0.24 (0.19-0.27) | 0.12 (0.10-0.20) | 0.00 (0-0.15) | 0.36 | 0.08 |
| texture std L* | 6.5 (5.8-7.3) | 6.1 (5.5-6.8) | 3.7 (3.2-4.1) | **4.3 (3.8-4.7)** | 6.0 (5.2-6.8) | **5.3 (5.0-6.4)** |
| orientation coherence | 0.37 (0.35-0.39) | 0.40 (0.37-0.45) | 0.64 (0.46-0.70) | **0.65 (0.62-0.75)** | 0.42 | **0.57 (0.47-0.60)** |
| width CV along marks | 0.41 (0.31-0.42) | 0.36 | **0.26 (0.23-0.41)** | 0.27 (0.25-0.42) | 0.42 | |
| line width | 0.35 mm | | 0.55 mm (0.33-0.79); Crivelli torso **0.33 mm** | | | |
| hatch spacing | 7.6 mm (spectral peak, not hatching) | | Crivelli torso **0.7-1.2 mm** (n = 3); Duccio 2.2-5.0 (cracks dominate) | 0.9-6.7 | | |
| stroke-length proxy | | | 0.8-3.7 mm | **1.5 mm (1.1-2.3)** | | |
| mean chroma | 34 (29-42) | | 28 (23-30) | | **42 (38-44)** | |

## Rendered, before and after

Hatching test: a verdaccio glaze (`#76744c`), then three passes of flesh tones (`hatch`, 21 hand paths per pass, care 0.8) at size 10 and 24, measured at 4 px/mm. Size 10 in this layout leaves rows; size 24 is a dense field.

| | coherence | stroke-length proxy | std L* | CV along | spacing |
|---|---|---|---|---|---|
| before, size 10 / 24 | 0.76 / 0.96 | 0.75 / 2.4 mm | 2.1 / 3.4 | 0.39 / 0.41 | 0.80 / 1.16 mm |
| after, size 10 / 24 | 0.71 / 0.90 | 0.62 / 1.0 mm | 2.2 / 3.5 | 0.30 / 0.41 | 0.76 / 1.16 mm |
| target (flesh, 4 px/mm) | 0.65 (0.62-0.75) | 1.5 (1.1-2.3) | 4.3 (3.8-4.7) | 0.27 (0.25-0.42) | 0.7-1.2 mm (full res) |

Angle scatter sweep (size 24 coherence / proxy): jitter 0.04 → 0.96 / 2.5 mm; 0.12+tilt 0.1 → 0.92 / 1.25; 0.1+0.3 → 0.85 / 0.75; 0.25+0.2 → 0.81 / 0.88. Scatter lowers coherence but also shortens the length proxy (crossing lines decorrelate), so the two targets pull against each other; jitter 0.08 + tilt 0.2 was chosen as the compromise.

Gold ground (bare `gold_ground`, 800×800, three 60 mm crops): std L* before 0.63, after **1.53** (new leaf), **4.86 with `finish age`** (target 5.3, IQR 5.0-6.4); coherence 0.61 aged (target 0.57); mean chroma 54-56 (target 42).

## What changed

1. **Hatch angle scatter** from data: per line `JITTER` 0.04 → 0.08 rad; new per-stroke `TILT` 0.2 rad (each stroke of the hand sets its lines at a new angle).
2. **Gold leaf texture** `LEAF_GRAIN` 3 (the fine leaf noise only; the square-to-square tilt is unchanged) and a new finish **`age`**: craquelure (cell walls of a warped Voronoi network, 1 px wide, cells `cell` 40 px ≈ 10 mm, broken by noise; darkness `CRACK_DARK` 0.8) and wear (gold rubbed through to the red bole). Amplitudes set to the plain-gold crops' std L*; the pattern is by eye. Every reference is centuries old: their gold texture is craquelure and wear, which a new panel should not have, so it is a finish, not the default.
3. **Colours:** `binder_palette("egg tempera")` (FORS masstones from `pigments.json`, hue measured, value approximate), listed in the manual; the manual's verdaccio moves from hue 120 to green earth's 105 (`#6b7650` → `#76744c`). The highlight `#f3ead6` (hue 91) agrees with lead white in egg (90).

## What could not be calibrated, and why

- **Hard-edge share** (0.25) is a property of the compositions (gilded haloes, contours against gold); hatched flesh itself has few hard edges (0.12). The medium's edges were not changed.
- **Stroke length:** the proxy is disturbed by crossing lines, cracks and modelling; the recommended sizes were left as they were.
- **Flesh texture** (std 4.3 at 4 px/mm) depends on the values the painter hatches; a three-pass test reaches 2.2-3.5.
- **Line width** 0.33 mm is at the canvas's pixel floor (0.25 mm); finer hatching needs a larger canvas.
- **Gold chroma** (42 in the photographs, 54-56 rendered): aged, dirty and varnished gold versus new leaf; not changed.
- **Not found as data:** punch sizes, burnish reflectance, the opacity of each pigment in egg (the opacity rule stays by eye); the FORS values are hue-only by the dataset's normalisation.

## Spectral mixing (Nov 26, 2026)

Every hatched line and `round`/`liner` stroke is now a spectral film (lead-white palette, egg S ×1.24 from FORS; `opaque._tempera_film`), 10 µm per unit of `film` (fitted to the old RGB films: tuned). The opacity rule now comes from the paints. No egg-tempera tint data exists to validate it; the carry-over check (4 lead-white tints: 2.6 median ΔE2000, kmix 14.7), speed (3× the old `match` time) and the binder factor are in `colour.md`, section 6. `opacity_paint`, `glaze`, `oil-glaze` and `hatch-lights` keep the RGB films; `TEODOR_SPECTRAL=0` restores them everywhere.
