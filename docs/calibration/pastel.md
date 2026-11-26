# Calibration: soft pastel

Medium: `studio/v8/media/drymedia.py`, class `Pastel`. The shared engine changes are in `charcoal.md`. Calibrated Nov 25, 2026.

## Scale and references

- **Stated scale: 2.5 px/mm** (1200 px = 48 cm; the references are 47-80 cm sheets at 4.6-8.2 px/mm).
- **References:** the 8 pastels in `calibration_refs.json` (Degas x4, Redon, Rosalba Carriera, Perronneau, William Russell). Hand-chosen crops: Degas, *The Singer in Green* (436159; broken vertical strokes over laid paper), *Mrs. William Bell* (436124; hatching on the face), *Three Dancers* (436163; broken strokes), *Woman Having Her Hair Combed* (436173; the sofa's hatching); Carriera (438544) and Perronneau (438615) for rubbed, blended passages.

## Real targets

| statistic | value | n |
|---|---|---|
| automatic crops, full resolution (docs/media-data.md) | coherence 0.24 (0.22-0.30), paper in marks 0.000, edge rise 1.34 mm (1.03-1.87) | 8 |
| whole sheets at 2.5 px/mm | coherence 0.35 (0.31-0.43), paper share 0.04 (0.035-0.054), paper in marks 0.000, flat texture 1.9 (1.2-3.0) L*, spectrum slope -2.48 | 8 |
| paper specks inside strokes | 0.2-0.4 mm (resolved at 5-8 px/mm), elongated along the stroke | 6 crops |
| stroke edge rise (10-90%) | Singer 0.98 mm, Dancers 1.41, Bell 1.52, sofa 2.2 | 4 |
| laid-line period (Singer) | 1.23 mm | 1 |
| darkest L* (0.1%) | Redon 9.6, Degas *Three Dancers* 9.9, Russell 12.2, Carriera 13.4; Degas others 21-30 | 8 |
| at 2.5 px/mm: grain std in tone | broken strokes (Singer) 7.6, Dancers 4.4; hatching (Bell, sofa) 1.1-1.7; rubbed (Carriera) 1.1 | 6 crops |
| stroke spacing in the Singer's background | strokes 4-6 mm wide, laid side by side | by eye |

## Changes specific to pastel

- `EDGE_MM = 1.0` (the Singer's strokes: 0.98 mm); `W_SUB = 1.2` (pastel papers' tooth is coarser, 0.2-0.4 mm specks: about 2 cells per 0.4 mm pixel).
- Honeycomb cells at 0.8 mm (were about 5 px = 2 mm at this scale; tuned toward the measured speck spacing, no direct measurement of a honeycomb paper); laid lines at 0.9 mm and chain lines at 35 mm (Ingres; measured on laid sheets, see `charcoal.md`).
- The slide-and-smear on a full tooth now drags the stroke's own average colour (was a Gaussian blur of the area under it: same effect, much cheaper).
- The shared changes: whole-stroke deposit, side strokes with soft wedge ends and streaks instead of hard rectangles, pixel-scale tooth.

## Before and after (2.5 px/mm, photo blur on the renders)

| statistic | target | before | after |
|---|---|---|---|
| Singer-schema drawing (`match` with `soft_side` then `hard_tip`): coherence | 0.23 (that sheet), 0.35 (all sheets) | 0.50 | 0.24 |
| same: paper share | 0.04 | 0.03 | 0.03 |
| same: hard-edge share | 0.28 (that sheet) | 0.45 | 0.10 |
| same: grain std in tone | 5.1 (that sheet) | 4.2 | 1.1 |
| darkest (three heavy passes, `#141414`), L* (0.1%) | 9.6-13.4 | 10.0 | 10.4 |
| blank paper texture std, L* | 1.2-3.0 (whole sheets, pastel-covered: not blank) | 1.20 | 0.61 |

The before drawing test also cross-hatched the whole sheet with the core's default dark colour, which pastel (not monochrome) lays as dark grey; the after test leaves `hatch` out. So the coherence and edge rows compare different procedures and only show that the side strokes no longer read as hard blocks; they are not a calibration result.

## What remains uncalibrated

- Grain in the drawing test is now too low (1.1 vs 5.1 L*): the soft side strokes cover the tooth more evenly than Degas's broken strokes. A pressure-dependent breakup for soft pastel needs a cleaner comparison (a single broken stroke at known pressure), not attempted.
- Pastel opacity, the paper tones, tooth capacities (toned 1.7, sanded 3.4, Ingres 1.2), grip, slide rate, the powder lift in the render, oil pastel, blenders and fixative: tuned by eye. No measurements of pastel opacity or fixative darkening were found.
- Pastel `hatch` uses the colour given; with no colours it uses the core's dark grey default, which is rarely what a pastellist means.

## The v8 hand, dust and spectral mixing (Nov 26, 2026)

- **The v8 hand:** on the Singer-schema drawing (`match` `soft_side` 20-40 px, then `hard_tip` 6-12 px; one seed) the v8 hand gives coherence 0.24, hard-edge share 0.08, grain 1.05; without the role sizes 0.27, 0.10, 1.06 (the sheet: 0.30, 0.14, 2.9). No drift away from the reference; pastel opts out of the role sizes with charcoal and graphite (`docs/calibration/charcoal.md`, "The v8 hand").
- **Dust:** pastel does not use the dust haze (`DUST_K = 0`). Its grain is already under the references (above), and a haze would lower it further; no haze profile was measured on the pastel references. Pastel's real fall-out of loose dust (why pastels are framed with a spacer [S11]) is not modelled.
- **Spectral mixing: not moved, because it cannot be validated.** `docs/calibration/colour.md` section 5 sets three conditions: a film path for a stroke over another (pastel lays opaque dust side by side, which the engine already treats as an optical, linear mix of the covered area: that is the physics of juxtaposed particles, and needs no Kubelka-Munk), a white for the medium, and a binder correction to S. The rubbed part (blenders) would be a subtractive mixture of pigment particles in air, not in oil: air's refractive index (1.0 against linseed's 1.48) makes the same pigment scatter several times more, which is why pastels look lighter and chalkier, but by how much per pigment is not published that I could find. Searched: pastel reflectance or K and S data, pastel blends measured on paper (none; a Munsell colour survey of artists' pastels could not be reached; a 2025 hyperspectral database of manuscript paints, Analytical and Bioanalytical Chemistry 10.1007/s00216-025-05948-3, has gum arabic and egg glair, no pastel, and finds the binder alone shifts colour by ΔE 9.6 on average). Without measured pastel blends there is nothing to fit the S correction to or to test against, so pastel keeps the engine's optical deposit, a linear blur for rubbing, and `base.kmix` for oil pastel only. What would allow it: drawdowns of a few pastel sticks rubbed together in known proportions on a white card, measured with a spectrophotometer (masstones plus two blends per pair), which would fix S per pigment in air and validate the rubbed path through `spectral.py`.

