# Calibration: charcoal (and the shared dry-media engine)

Medium: `studio/v8/media/drymedia.py`, class `Charcoal` (Graphite and Pastel share the engine; see `graphite.md` and `pastel.md` here). Calibrated Nov 25, 2026 against the Met references in `studio/calibration_refs.json` with `tools/calibrate_media.py` plus a few extra dry-media statistics (below). No published numbers for charcoal were found (docs/media-data.md, "Charcoal, graphite, pastel"), so the references are the data.

## Method

- **References.** The 8 charcoal / black chalk / conté sheets in `calibration_refs.json`, measured three ways: (1) the automatic crops at the photographs' resolution (`calibrate_media.py refs charcoal`); (2) hand-chosen crops at full resolution: Millet, *A Seated Shepherd* (337802; conté: light strokes, dark hatching, darkest band), de la Fosse (337511; black chalk on grey laid paper: darks and background hatching), Melbye (365663; a rubbed sky), Mauve (399579; a dense charcoal figure); (3) the same crops and the whole sheets (central 60%) **resampled down to the studio's scale**.
- **Scale.** The studio's charcoal sheet is stated as 1200 px = 48 cm, **2.5 px/mm** (`DryMedium.PPM`; the manual's old 0.4 mm/px assumption, now explicit). References are 3-28 px/mm, so the honest common scale is the studio's: the renders cannot be resampled up to 12 px/mm without inventing detail. Renders are blurred by the photographs' own blur before measuring (narrowest 10-90% edge rise in the set, 0.38 mm: Gaussian sigma 0.15 mm), as docs/media-data.md asks.
- **Scale fixes found.** Mauve (399579): the catalogue's `size_mm_hw` is swapped (the sheet is 150 x 93 mm landscape); the true scale is about 25 px/mm, not 27.8. Grandville (graphite, 812726): the photograph includes the mount; measured on the sheet edges the scale is 14.2 px/mm, not 23.8.
- **Extra statistics** (scratch code, same definitions as `calibrate_media.py` where they overlap): darkest L* of each sheet (the darkest 0.1% of the central 80%); optical density D percentiles relative to the sheet's paper (the modal luminance of the sheet, not the crop's own lightest pixels); `grain std`: std of L* minus its 0.5 mm blur inside toned passages; light-speck size inside marks; laid- and chain-line periods from the profile spectra of blank paper.
- **Test renders.** 600 x 600 patches: hatch with the core's defaults; hatch at the measured spacing (light and dark); side strokes rubbed with the stump; the darkest a tool reaches (three heavy cross passes); blank paper; and a full `match` + `hatch` drawing using the Millet sheet (greyed, in the paper's tone) as the schema, compared with that sheet at the same scale.

## Real targets

At the photographs' resolution (automatic crops, n = 8, median and IQR; docs/media-data.md): orientation coherence 0.29 (0.24-0.34), paper in marks 0.014 (0.002-0.043), edge rise 0.93 mm (0.72-1.91).

Measured here:

| statistic | value | n / source |
|---|---|---|
| darkest L* per sheet (0.1%) | conté (Millet) 23.8; charcoal (Degas, *Two Dancers*) 21.9; black chalk (de la Fosse) 25.6; charcoal sketches (Mauve 28.9, Melbye 26.9) | 5 sheets on light/mid papers |
| line edge rise (hand crops, 10-90%) | Millet hatching 0.75 mm, dense band 0.82, de la Fosse hatching 0.74, Mauve (25 px/mm) 0.38 | 4 crops |
| light specks of paper inside marks | 0.06 mm (Mauve, 25 px/mm), 0.12-0.18 mm elsewhere = the resolution limit (1-2 px) | 7 crops: the tooth is finer than about 0.15 mm |
| blank paper texture at 2.5 px/mm | std 0.50 L* (Millet's wove), 2.9 (de la Fosse's grey laid paper with chalk dust); correlation length 1 px | 2 sheets |
| laid-line period | 0.90 mm (Delacroix), 0.91 (de la Fosse), 1.23 (Degas, *Singer in Green*) | strong spectral peaks (30-3000x median) |
| chain-line spacing | 32.8 mm (de la Fosse), 37.3 (Singer), 42.6 (Delacroix, weak) | weak peaks: an estimate |
| hatch spacing, by eye on mm-ruled zooms | Millet 1.5-2 mm, line 0.5 mm; de la Fosse about 1 mm | 2 crops (the spectrum-peak spacing of `calibrate_media.py` locks onto 3-6 mm drawing structure on these crops and is not usable) |
| at the studio scale (2.5 px/mm): whole sheets | coherence 0.51 (0.35-0.60), paper share 0.18 (0.10-0.34), paper in marks 0.013 (0.009-0.041), flat texture std 2.5 (1.7-2.8) L* | 8 sheets |
| at the studio scale: Millet crops | grain std in tone 5.7 (light strokes), 7.4 (dark hatching), 7.3 (darkest band); rubbed sky (Melbye) 1.8; de la Fosse 2.8-3.0 | 6 crops |

Coherence depends on scale: the same sheets give 0.29 at full resolution (the tooth speckle is isotropic and dominates the structure tensor) and 0.51 at 2.5 px/mm. The studio renders must be compared with the second number.

## What changed (shared engine)

1. **Paper tooth** (`paper_texture`): the old height field mixed noise at 0.85, 2.2 and 8 px; histogram-equalised and thresholded, the 2.2 and 8 px parts made mm-sized blobs with smooth outlines: the "camouflage" look. The tooth measures finer than a studio pixel, so the new field is pixel-scale grain (sigma 0.5 px plus 0.45 x sigma 1 px), short fibres (1.5 mm, tuned by eye) and a faint formation cloud. It is built at the stated scale (`PPM`): laid lines every 0.9 mm and chain lines every 35 mm from the measurements above (were 4.3 px = 1.7 mm and 112 px = 45 mm).
2. **Catch softness** (`W_SUB`): a pixel holds about 16 tooth cells at 0.4 mm, so it is partly covered rather than on/off. The catch band is widened by 3.0 for charcoal (graphite 1.6, pastel 1.2: the ratio follows tooth cells per pixel), fitted to the grain std inside hatching; it lowered that std about 15% (the rest of the gap is below).
3. **Line edges** (`EDGE_MM`): the tip mask was a 1 px antialiased disc (hard-edge share 0.69 on hatching). Its edge is now a ramp with the measured 10-90% rise: 0.75 mm for charcoal (Millet, de la Fosse), 0.3 mm graphite, 1.0 mm pastel.
4. **Pigment values from the darkest measured values**: compressed charcoal L* 24 (was 4: three heavy passes rendered at L* 5.6, far blacker than any reference), vine L* 29 (was 23), charcoal pencil L* 26 (tuned between). Three heavy compressed passes now render at L* 24.6 (darkest 0.1%), in the measured 21.9-28.9.
5. **Paper grain in the render**: relief scaled from +-3.5% to +-2%; blank paper measures 1.08 L* (was 2.05; references 0.5-1.1 on white papers).
6. **Sticks lay a whole stroke at once**: the stick records its contacts and deposits when the core ends the stroke (`DryTool.end`): per pixel the deepest reach (which hollows were touched) and the summed rubbing, then tooth, asked value and colour once. The asked-value cap is now local (a Gaussian of the stroke's own footprint) instead of the mean over one dab. Hatching a 520 px square (graphite pencil, the core's defaults) went from 64 s to about 10-12 s; `match` with 300 side strokes on 1200 x 1600 takes about 6 s (was 10.5), 300 tip strokes about 3 s (was 6.4).
7. **Blocky side strokes**: the old side mask had per-dab random end jitter (torn edges) and started and stopped on a straight cut; short `match` strokes became hard rectangles. Now the contact ends drift smoothly along the stroke, the pressure falls off toward the stick's ends, the stick's broken face streaks the band along its direction, and the band lands and lifts over one stick radius as a wedge (only the tilted end touching). The streaks, the fade length and the wedge are tuned by eye.
8. **Asked value at the paper's tone**: a stroke asked for (nearly) the paper's value no longer leaves the 0.12 overshoot on the peaks; the overshoot scales with how dark the asked value is. This removed the faint speckle `match` laid over blank paper wherever the schema differed only in hue.

## Before and after (studio scale, photo blur applied to both)

| statistic | target | before | after |
|---|---|---|---|
| darkest compressed, L* (0.1%) | 21.9-28.9 (conté 23.8) | 5.6 | 24.6 |
| blank paper texture std, L* | 0.5-1.1 (white wove) | 2.05 | 1.08 |
| `hatch` with the core defaults (spacing 9 px, size 3): hard-edge share | 0.15-0.19 (Millet crops) | 0.69 | 0.70 (the default is 3.6 mm spacing: too coarse, see below) |
| `hatch` at the measured spacing (4.4 px = 1.75 mm, size 1.5 px), dark: grain std | 7.4 (Millet dark hatching) | 12.9 (defaults) | 12.3 |
| dark hatch: paper in marks | 0.02 (Millet), 0.13 (de la Fosse) | 0.19 | 0.11 |
| Millet-schema drawing: coherence | 0.59 (the sheet at 2.5 px/mm) | 0.37 | 0.49 |
| Millet-schema drawing: paper share | 0.38 | 0.24 | 0.44 |
| Millet-schema drawing: hard-edge share | 0.19 | 0.38 | 0.34 |

## What remains uncalibrated, and why

- **Grain contrast inside hatching is still 1.7x the references** (12.3 vs 7.4 L*). The lines are too uniform in darkness and the paper between them too clean: real hatching carries smudged dust between lines and lines of varying pressure. A model of loose dust settling around a line would be the next step; I did not invent one.
- **Vine vs compressed**: the references are not labelled vine or compressed; the vine value is the lighter end of the measured charcoal sheets, a reasonable assignment, not a measurement of vine itself.
- **Everything not listed above stays tuned by eye**: KC = 3.5; tooth capacities; the pressure-to-reach curve; tool flow, loose and stain fractions; blender, eraser and fixative rates; the velvet render; fibre length and cloud scale; the side stroke's streaks, fade and wedge.
- **The `match` drawing test is a weak ruler for the medium**: its coherence and paper share depend mostly on the core's matching (stroke lengths, thresholds), not on charcoal. It is used here to check by eye that side tools no longer make hard blocks, and for orders of magnitude.
- **Core issues seen while calibrating (studio.py, not edited here):** `hatch` cuts every line into 140 px segments starting at the same offset, so the segment ends line up into visible seams across a hatched area; its default spacing (9 px) and size (3 px) are 3.6 mm and 1.2 mm at the charcoal scale, coarser than the measured 1-2 mm, and the default colour `#2a2a2a` makes monochrome tools press as hard as they can. Its `layers` are absolute values, so on toned paper they must be set below the paper's value.

## Reproducing

The scratch scripts were not kept. To reproduce: `python3 tools/calibrate_media.py refs charcoal`; take the hand-chosen crops above (object, x, y, size in px: 337802 2500,1780,350 / 850,820,300 / 1150,1000,300; 337511 300,2700,400 / 2250,500,400; 365663 600,300,400; 399579 1300,1100,400), resample them to 2.5 px/mm, and measure them and studio renders (blurred by sigma 0.15 mm) with `calibrate_media.measure`.
