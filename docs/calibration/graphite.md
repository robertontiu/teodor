# Calibration: graphite

Medium: `studio/v8/media/drymedia.py`, class `Graphite`. The engine, the method and the changes shared with charcoal and pastel (paper tooth, catch softness, line edges, whole-stroke deposit, side strokes) are in `charcoal.md`; this page has graphite's own data and numbers. Calibrated Nov 25, 2026.

## Scale and references

- **Stated scale: 5 px/mm** (`Graphite.PPM`): 1200 x 1600 px is a 24 x 32 cm sheet, like the references (11-34 cm; median about 22 x 16 cm). The old manual assumed 0.4 mm/px, which made a 1200 px graphite drawing 48 cm wide and every pencil line 1 mm or more.
- **References:** the 8 graphite sheets in `calibration_refs.json` (Lachaise's sheet has no usable scale: a montage of several sheets). Hand-chosen hatched crops: Grandville, *Dog in doghouse* (812726; dense hatching inside the doghouse, light hatching on the wall; scale corrected to 14.2 px/mm, the photograph includes the mount), Delacroix, *Studies of a Fallen Male Nude* (355649; two hatched passages), Bendemann, *Studies of a Seated Woman* (384261; two).

## Real targets

| statistic | value | n / source |
|---|---|---|
| automatic crops, full resolution (docs/media-data.md) | coherence 0.43 (0.36-0.61), paper share 0.42 (0.18-0.48), paper in marks 0.021 | 8 |
| whole sheets at 5 px/mm | coherence 0.56 (0.44-0.62), paper share 0.61 (0.53-0.73), paper in marks 0.087 (0.013-0.111), flat texture 0.96 (0.80-1.31) L*, spectrum slope -1.90 | 7 |
| darkest L* per sheet (0.1%) | Lachaise 32.5, Grandville 34.7, Delacroix 39.9, Bendemann 40.4, Waldmüller 47.5, Ingres 55.1, two ornament designs 49.0 and 64.6 | 8 |
| hatch spacing (by eye, mm-ruled zooms) | Delacroix 0.9-1.1 mm (line about 0.35 mm, broken by the tooth into 0.1-0.2 mm specks); Grandville dense hatching 0.8-1.0 mm; Bendemann 1.5-2 mm (line 0.3 mm). The automatic autocorrelation spacing confirms 0.89 mm on Delacroix (peak 0.24) and fails elsewhere | 4 crops |
| line edge rise (10-90%, hand crops) | Delacroix 0.31 and 0.49 mm; Grandville 0.70-0.74; Bendemann 0.72 | 6 |
| hatched crops at 5 px/mm | grain std in tone 5.2 (3.7-5.7); paper in marks 0.00-0.16; coherence 0.42-0.60 single-direction, 0.22 cross-hatched (Delacroix 2); Grandville dark: D50 0.53, D95 0.80 | 6 |
| blank paper at 5 px/mm | texture std 0.63, 0.94, 1.09 L*; correlation length 1 px | 3 sheets |

## Grade-to-darkness ramp

No published measurement of darkness per grade was found (searched: manufacturers, the Getty *Noir* project, a tribology study behind bot protection; see the manual). What the references allow:

- **The soft end is measured:** the darkest graphite in the references is L* 32.5-34.7 (dense soft-pencil passages, Lachaise and Grandville). A dense 8B passage (three heavy passes) renders at L* 32.8 (darkest 0.1%), with the render's sheen included (the sheen lifts a dense soft dark about 3.5 L*, so the pigment values of the soft grades sit that much lower).
- **One point at the hard end, weak:** Ingres's portrait drawn with fine, hard pencils reaches L* 55 at its darkest: used for H.
- **Everything between is interpolated by eye:** `GRADE_L` in drymedia.py: 6H 72, 4H 66, 2H 60, H 55, HB 49, B 44.5, 2B 41, 3B 38, 4B 35.5, 5B 33.5, 6B 32, 7B 30.8, 8B 29.8, 9B 29 (pigment L*). The old ramp (sRGB 0.6 - 0.44 i^0.8) put 8B at L* 19, which only the sheen kept from reading as charcoal.
- Which grade the 19th-century artists used is not known, so "the darkest the references reach" is assigned to the soft end, not measured per grade.

## Before and after (5 px/mm, photo blur sigma 0.15 mm on the renders)

| statistic | target | before | after |
|---|---|---|---|
| darkest dense 8B, L* (0.1%) | 32.5-34.7 | 32.8 (with pigment L* 19, lifted by the sheen) | 32.8 (pigment L* 29.8) |
| blank paper texture std, L* | 0.63-1.09 | 1.60 | 0.79 |
| `hatch`, core defaults (9 px = 1.8 mm, size 3 = 0.6 mm): hard-edge share | 0.05-0.16 (hand crops, full resolution 0.05-0.40) | 0.67 | 0.63 |
| `hatch` at the measured spacing (5 px = 1 mm, size 2 px = 0.4 mm), mid: hard-edge share | as above | | 0.40 |
| same, dark cross-hatched: grain std in tone | 5.2 (3.7-5.7) | 10.8 (defaults) | 8.0 |
| same: paper in marks | 0-0.16 | 0.12 (defaults) | 0.07 |
| same: D50 | 0.53 (Grandville dense) | | 0.46 |
| same, mid: coherence | 0.42-0.60 | 0.58 (defaults) | 0.52 |
| Grandville-schema drawing: coherence | 0.56 | 0.39 | 0.46 |

## What remains uncalibrated

- The grade ramp between the measured ends (by eye, see above); the sheen strength and its raking light (a diffuse museum photograph cannot show gloss); burnish threshold; flow, reach, loose and stain per grade; blender, eraser and stylus rates; bristol's capacity.
- Grain contrast in hatching is still about 1.5x the references (8.0 vs 5.2 L*): lines too even, paper between them too clean (no graphite haze).
- The Grandville-schema drawing leaves much more paper (0.57 vs 0.20): that is the core's `match` stopping strokes early and the hatch levels used in the test, not the pencil.
- Core `hatch` seams and coarse defaults: see `charcoal.md`. For graphite at 5 px/mm the data say spacing 4-5 px, size 1.5-2 px.
