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

- **Grain contrast inside hatching** was 1.7x the references (12.3 vs 7.4 L*): see "Charcoal dust" below (Nov 26, 2026) for the model that brought it to 0.8-1.5x.
- **Vine vs compressed**: the references are not labelled vine or compressed; the vine value is the lighter end of the measured charcoal sheets, a reasonable assignment, not a measurement of vine itself.
- **Everything not listed above stays tuned by eye**: KC = 3.5; tooth capacities; the pressure-to-reach curve; tool flow, loose and stain fractions; blender, eraser and fixative rates; the velvet render; fibre length and cloud scale; the side stroke's streaks, fade and wedge.
- **The `match` drawing test is a weak ruler for the medium**: its coherence and paper share depend mostly on the core's matching (stroke lengths, thresholds), not on charcoal. It is used here to check by eye that side tools no longer make hard blocks, and for orders of magnitude.
- **Core issues seen while calibrating (studio.py, not edited here):** `hatch` cuts every line into 140 px segments starting at the same offset, so the segment ends line up into visible seams across a hatched area; its default spacing (9 px) and size (3 px) are 3.6 mm and 1.2 mm at the charcoal scale, coarser than the measured 1-2 mm, and the default colour `#2a2a2a` makes monochrome tools press as hard as they can. Its `layers` are absolute values, so on toned paper they must be set below the paper's value.

## Charcoal dust (Nov 26, 2026)

**What the sources say about loose dust.**
- A dry stick dragged over a rough surface breaks into fragments of every size: for graphite, fragments torn off by the cellulose fibres with "a scale-free, power-law size distribution spanning several decades", and the grey level of a drawing is the surface covered by fragments (V. Bertin, "The physics of pencil drawing", Research Square preprint, 2026, abstract only: https://www.researchsquare.com/article/rs-10448967/v1; seminar abstract https://www.loma.cnrs.fr/bertin-24-march-2026/: "sparse, heterogeneous deposition").
- Charcoal has large particles and no binder: it "can be lifted easily" and its particles "readily crumble when spread" (The Met, "Materials and Techniques: Charcoal", https://www.metmuseum.org/perspectives/materials-and-techniques-drawing-charcoal). Its dust "catches in the paper's texture but can be easily wiped away unless fixed" and "can leave some staining due to dust getting trapped in the surface texture"; graphite "produces far less dust" (Jackson's [S13]). Vine "is easily removed by dusting" [S12].
- Loose granular dust that a tool or hand sweeps pools in the low regions of the surface (a granular-media model for digital charcoal and chalk, US patent 11531450, "Digital imaging of granular media", https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11531450; not a measurement). Sousa & Buchanan's blender pushes loose graphite into the hollows [S27].
- Not found: any measurement of how much dust a stroke sheds or how far it travels. One reference (Heritage Science 10.1186/s40494-022-00649-x, charcoal underdrawing reconstructions: charcoal over gesso "easily dusted away by a feather") was read through its repository copy (https://dspace.uevora.pt/rdpc/bitstream/10174/35161/1/s40494-022-00649-x.pdf); it is about panel underdrawings, not paper.

**Measured here: the haze around strokes.** On Millet's *A Seated Shepherd* (337802, conté), the paper's median optical density by distance from the nearest mark (marks: density above 0.12 after a 0.12 mm blur), relative to the crop's 95th-percentile luminance, at 2.5 and 10 px/mm, four crops:

| distance from a mark | 0-0.6 mm | 0.6-1.2 | 1.2-2 | 2-3.2 | 3.2-6 | 6-12 |
|---|---|---|---|---|---|---|
| density (2.5 px/mm), four crops | 0.046-0.056 | 0.023-0.037 | 0.017-0.032 | 0.013-0.023 | 0.005-0.018 | 0.004-0.012 |
| above the far floor, relative to the marks' density | 0.062 | 0.025 | 0.015 | 0.0075 | 0.0035 | 0 |

So the paper carries a haze that thins over about 2-3 mm from each mark, and its mass is about a fifth of the line's.

**The model** (`drymedia.py`, `DUST_*`, `DryTool._stroke`). A stick's stroke keeps `1 - dust` of what it rubs off in the line; the rest (`dust = DUST_K x the tool's loose fraction`) lands around it as two Gaussian hazes, sigma 0.5 mm (45% of it) and 2.6 mm (55%), settling more into the hollows (x0.6 on the peaks to x1.4 in the deepest hollows) and never into an indented groove or outside a clip mask. The haze is loose dust: blenders spread it, erasers lift it, fixative locks it. Charcoal `DUST_K = 0.55` (vine sheds 0.48 of a stroke, compressed 0.28, the charcoal pencil 0.22, white chalk 0.39). Kernel widths, weights and `DUST_K` were fitted to the profile above with sparse compressed strokes (0.6-0.9 mm wide): the render gives 0.047, 0.025, 0.017, 0.012, 0.004 (relative, same bins) against 0.062, 0.025, 0.015, 0.0075, 0.0035. The fraction per tool (in proportion to `loose`) is a judgement: only conté was measured.

A crumbling-stick term (pressure varying along each line, for the "lines too even" diagnosis) was tried and left out: at the same tone it **raised** the grain in hatching (compressed hatch 9.6 -> 10.1 L*, vine 5.6 -> 6.3), so the even lines are not what makes the grain too high; the clean paper between them is.

**Before and after** (studio scale 2.5 px/mm, photo blur on the renders; my measuring script reproduces the earlier reference numbers within 0.3-0.8 L*: Millet dark hatching 7.06 here, 7.4 in the table above):

| statistic | reference | before | after |
|---|---|---|---|
| vine hatch at 1.75 mm, 2 layers (`#000000`): grain in tone, L* (mean L*) | 7.06 (Millet dark hatching, L* 64) | 12.9 (69) | **6.8** (66) |
| same: hard-edge share | 0.24 | 0.64 | 0.48 |
| compressed hatch, same settings: grain (mean L*) | 7.06 (64) | 15.9 (58) | **11.1** (55) |
| same: hard-edge share | 0.24 | 0.68 | 0.63 |
| same: paper in marks | 0.004-0.014 (Millet), 0.12 (de la Fosse) | 0.17 | 0.11 |
| vine light hatch, 1 layer (`#606060`): grain (mean L*) | 5.45 (Millet light strokes, L* 75) | 10.4 (82) | **6.1** (80) |
| sparse compressed strokes: hard-edge share | 0.17-0.28 (Millet crops) | 0.64 | **0.18** |
| darkest compressed, three heavy passes, L* (0.1%) | 21.9-28.9 | 24.6 | 24.6 |
| Millet-schema drawing (below, 2 seeds): grain / hard-edge share / paper share / coherence | 7.2 / 0.17 / 0.38 / 0.60 | 10.0 / 0.43 / 0.45 / 0.35 (v8 hand) | 5.4 / 0.18 / 0.32 / 0.32 |

Sheet: `docs/gallery/charcoal_dust.jpg` (Millet's hatching at the studio scale beside vine and compressed hatches before and after). Still off: compressed hatching stays 1.5x the conté reference in grain and keeps too many hard edges (its lines are darker than Millet's, 0.86 against about 0.6 in density); the Millet drawing's grain now falls under the reference (5.4 vs 7.2), and its coherence is the core `match`'s, not charcoal's.

## The v8 hand (Nov 26, 2026)

The core's v8 hand (`play_v8`: articulations, the pressure wave, drift; role and focus sizes) arrived after this calibration. The Millet-schema drawing (the sheet greyed and normalised to the paper's tone as the schema; `match` with `vine_side` 16-32 px, `vine_tip` 3-8 px, `compressed_tip` 2-5 px; central 60% measured), two seeds, before the dust model:

| hand | grain | hard-edge share | paper share | coherence |
|---|---|---|---|---|
| reference (the sheet) | 7.2 | 0.17 | 0.38 | 0.60 |
| v7 stroke (plain, no role sizes, no wave) | 8.3 | 0.31 | 0.36 | 0.32 |
| v8 hand | 10.0 | 0.43 | 0.45 | 0.35 |
| v8 hand without the wave | 10.2 | 0.39 | 0.45 | 0.35 |
| v8 hand with plain articulation | 10.3 | 0.45 | 0.43 | 0.36 |
| v8 hand without role sizes | 8.4 | 0.34 | 0.40 | 0.29 |

The drift comes from the role sizes (a `drawing`-role stroke is drawn at 0.6 of the asked width, which narrows calibrated sticks), not from the articulations or the wave. The dry media now opt out of the role sizes (`DryMedium.hand_defaults`: `"role_scale": false` under `match`, `free`, `strokes`, `model`, `blend`; an intention's own key wins) and keep the rest of the hand. Graphite (Grandville sheet, one seed): v8 hand grain 7.9, hard 0.35; without role sizes 7.1, 0.27; v7 stroke 6.9, 0.21 (reference 5.2, 0.16). Pastel (Singer, one seed): v8 hand coherence 0.24, hard 0.08; without role sizes 0.27, 0.10 (reference 0.30, 0.14): no drift away from the reference, the opt-out applies anyway.

## Reproducing

The scratch scripts were not kept. To reproduce: `python3 tools/calibrate_media.py refs charcoal`; take the hand-chosen crops above (object, x, y, size in px: 337802 2500,1780,350 / 850,820,300 / 1150,1000,300; 337511 300,2700,400 / 2250,500,400; 365663 600,300,400; 399579 1300,1100,400), resample them to 2.5 px/mm, and measure them and studio renders (blurred by sigma 0.15 mm) with `calibrate_media.measure`.
