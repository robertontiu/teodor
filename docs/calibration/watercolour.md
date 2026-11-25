# Calibration report: watercolour (`studio/v8/media/watercolour.py`)

Nov 25, 2026. Method as in `docs/media-data.md` ("Calibration method"); targets from its "Top calibration targets per medium" for watercolour. The short version is in the manual page (`docs/manual/watercolour.md`, "Calibration").

## Summary

| Target | Before | After | Real / data |
|---|---|---|---|
| Pigment attributes | guessed from the hue (every blue granulates 0.65, earths 0.5, staining 0.4 for all, opacity 0.1) | per pigment from `studio/pigments.json` (handprint): granulation Gr/4, staining St/4, opacity 0.6·(1 − Tr/4), darkest single wash 94 − VR; named (`"pigment": "PB29"`, `"burnt sienna"`) or nearest by hue, chroma and value | handprint [P3] |
| Darkest single wash | none (any colour, any depth) | saturating toward the pigment's darkest: Prussian blue L* 24.0 (data 25), ultramarine 29.3 (30), quinacridone violet 38.9 (39.5), ivory black 22.6 (23.5) at 4× the full-strength amount | handprint value range |
| Wet-to-dry shift | one shift for all (K × 1.25 wet) | per pigment: Prussian blue dries 62% lighter (data 68%), quinacridone violet 11% (15%), chromium oxide green darkens 6.5% (−13%); unmeasured paints take the median density ratio of the 12 measured | handprint notes [P3] |
| Edge darkening (rim ratio, isolated washes, 8 px/mm) | 1.05-1.13 for every pigment, falling with load | coarse (ultramarine, earths) 0.96-1.00, flat with load; fine (quinacridone, alizarin) 1.05-1.13, rising with load (alizarin 1.05 → 1.10 → 1.13) and the dark band widening (0.5 → 0.75 mm) | real washes 0.92-1.06 (n = 3); trend from [W1] |
| Drying time (water 1, cold press) | 6 episodes whatever the load (exponential) | 4.1 episodes (continuous), 4 at episode steps; proportional to the load (water 0.45: 2.1, 1.5: 5.8) | t_c = 2490 s = 4.15 episodes of 10 min [W1] |
| Flat-field texture std L* (8 px/mm) | phthalo 2.00, ultramarine 1.97, cobalt 1.77, sienna 0.92 | paper 1.14, phthalo 1.13, cobalt 1.13, sienna 1.13, ultramarine 2.19 (manganese blue 3.37) | paper 1.11, non-granulating washes 1.15-1.30, a granulating wash 2.13 |
| Match painting, edges (4 px/mm) | edge rise 2.6 mm, hard-edge share 0.13 | 1.9 mm, 0.26 | 1.9 mm (1.75-2.06), 0.24 (0.21-0.30), n = 7 |
| Match painting, look | ringed "sausages" with light interiors, a patchwork of dark outlines | mid strokes fuse into soft passages; small strokes are flat, crisp dabs without outlines | the reference's dabs: flat, crisp, no outline |

## 1. The real targets

Seven Met watercolours (`studio/calibration_refs.json`, `tools/calibrate_media.py refs watercolour`). The crops were measured three ways: at the photographs' own resolution (the table in `docs/media-data.md`), resampled to 8 px/mm (the references' median scale is 7.8-24.8 px/mm; this is the comparison scale for rims and flat fields) and to 4 px/mm (the canvas's own scale: a 1200 × 1600 canvas painted as 30 × 40 cm; detail above its Nyquist limit cannot exist in a render, so the spectrum and texture of whole paintings are compared here). Object 390390 has no scale in the file; its record ("6-3/8 x 9-3/8 in") gives 16.1 px/mm on both axes, used here.

**Automatic crops at 8 px/mm** (per work: 819278, 420544, 390390, 363700, 364366, 383837, 356060):

| statistic | median (IQR), n = 7 | per work |
|---|---|---|
| edge rise 10-90%, mm | 1.06 (0.94-1.06) | 1.19, 0.94, 1.06, 1.06, 1.06, 0.69, 0.94 |
| hard-edge share | 0.23 (0.19-0.30) | 0.15, 0.32, 0.27, 0.23, 0.22, 0.34, 0.16 |
| texture std L* (flat passages) | 4.5 (3.6-4.8) | 3.8, 4.5, 2.0, 5.1, 3.4, 4.9, 4.6 |
| spectrum slope | -2.54 (-2.67 – -2.38) | -2.74, -2.41, -2.61, -2.54, -2.34, -2.24, -2.83 |
| orientation coherence | 0.61 (0.45-0.65) | 0.74, 0.37, 0.68, 0.43, 0.63, 0.61, 0.46 |
| width CV along marks | 0.25 (0.22-0.34) | 0.19, 0.24, 0.37, 0.25, 0.32, 0.36, 0.20 |
| paper share | 0.057 (0.048-0.101) | 0.12, 0.04, 0.48, 0.04, 0.06, 0.08, 0.06 |
| mean chroma C* | 14.0 (12.5-20.2) | 17.3, 24.2, 11.7, 14.0, 13.3, 9.9, 23.0 |

At 4 px/mm the same crops give: edge rise 1.88 mm (1.75-2.06), hard-edge share 0.24 (0.21-0.30), texture std L* 5.6 (4.8-6.1), spectrum slope -2.34 (-2.43 – -2.12), coherence 0.57 (0.43-0.62), width CV 0.28 (0.22-0.37), paper share 0.056, chroma 13.9.

**Hand-chosen crops** (full-resolution px, x y w h), because the automatic crops are detail-rich passages where washes overlap and the rim ratio comes out below 1 there:

| crop | object | box | statistic at 8 px/mm |
|---|---|---|---|
| isolated pink ground wash (Fierro) | 819278 | 60 2540 640 660 | rim ratio 0.99 |
| isolated blue wash, upper left (Richmond) | 420544 | 330 220 200 480 | rim ratio 1.06 |
| blue wash with an inner back-run (Richmond) | 420544 | 1100 470 280 450 | rim ratio 0.92 |
| green wash (Richmond) | 420544 | 40 700 200 500 | 1.38, **not used**: brown leaf dabs sit on its edge |
| flat wash interior (Fierro) | 819278 | 300 2700 300 300 | texture std L* 1.15 |
| ground wash (Fierro) | 819278 | 2000 3150 600 150 | 1.23 |
| sky (Dudley, Valentia) | 364366 | 1500 30 700 500 | 1.30 |
| blank paper (Fierro) | 819278 | 1000 800 400 400 | 1.11 |
| granulating blue (Richmond) | 420544 | 1150 560 150 150 | 2.13 (pigment not identified) |

The rim ratio here is a purpose-made profile (`rim_profile`, not in the repository's tool): the wash is segmented by Otsu on the smoothed optical density, the crop border does not count as an edge, and the ratio is the median density 0.3-0.8 mm inside the boundary over the median beyond 2.3 mm. The tool's own rim statistic (fixed px bands, Otsu with a floor of D = 0.08) found no wash in the pale Fierro crop.

## 2. What was rendered and how

Scratch scripts (not kept) drove the studio exactly as a painter does (`studio.py new/act/dry/finish` in a temporary folder) with the old module and the new one:
- **Isolated washes:** 1200 × 900 cold press at 4 px/mm; glazes (feather 1.5) of quinacridone violet PV19, alizarin PR83, ultramarine PB29 and natural earth PBr7 at opacity 0.15, 0.35 and 0.7, plus a round-brush blob per pigment; `dry 1`; each wash cropped, upsampled to 8 px/mm, measured with the rim profile and the tool.
- **Flat fields:** opacity 0.4 glazes of phthalo PB15:3, ultramarine PB29, cobalt PB28, earth PBr7, manganese blue PB33 and blank paper; centre crops at 8 px/mm.
- **A match painting:** Richmond's *Study of a tree* (420544) as the schema, 740 × 920 px (185 × 225 mm at 4 px/mm, the sheet's size); match with the mop (40-64 px, 160 strokes), `dry 1`, round (18-32 px, 300), `dry 1`, small round (7-14 px, 400), `finish darks`. Measured whole and at the reference's crop, at 4 and 8 px/mm. The gallery's scene test is the same procedure at 960 × 1200 with a pale ground wash, dry-brush, `finish lift` and `mount`.
- **Drying:** a 120 px glaze with water 0.5, 1 and 1.5 on each paper, counting episodes until the centre is dry (water < 0.04 and damp < 0.1).

## 3. Changes, one by one

**Pigments.** `wc_pigment()` reads every watercolour entry of `pigments.json` (113 pigments, whites excluded). Nearest-pigment choice: squared hue difference (/25°, weighted by the colour's chroma), squared chroma difference against the chroma a tint of that pigment would have at the colour's value, a penalty when the colour is darker than the pigment's darkest single wash, and a preference for paints tested in more brands (−0.25 ln(1 + n)). Examples: #2f4aa0 → PB29 ultramarine, #1f4e8c → PB27 Prussian blue, #c2346e → PV19, #9a4a22 → PR101 (a synthetic iron oxide; name "burnt sienna" to get PBr7 with the burnt-sienna ratings), #808080 → PBk9, #6b8e5a → PG17, #d9a520 → PY150. The CIECAM masstone (J, a, b) is used as an approximate Lab masstone where given; otherwise a chroma of 40 (5 for blacks), eye.

**Darkest single wash and saturation.** The amount of paint at which one wash reaches the pigment's darkest value over the paper is found by bisection on the Kubelka-Munk film; the amount laid grows linearly up to 60% of it (eye) and then saturates exponentially toward it, as the deposit vs concentration does in [W1]. Match films (transparent, S ≈ 0) use the same rule on their luminance-weighted absorption.

**Drying shift.** Each wash carries `wq`, the ratio by which the wet film's optical density exceeds the dry one's, computed from the pigment's measured lightness shift at its masstone value. A shift measured as % of lightness does not transfer between paints of different value (16% of a near-white yellow would be a huge change), so unmeasured paints take the median q of the 12 measured ones (0.143).

**Edge darkening.** The old model made every wash ring alike, mostly through an artefact: the flow step pulled pigment toward low-water edges (pigment received in proportion to a clipped water term, sent in proportion to an unclipped one) and deposited the ring flow by dividing at the receiver, which piles pigment into one-pixel lines. Now pigment is received in proportion to the water's mobility, the ring flow is mass-conserving, and its strength is `ring × (RING0 + RING1 × fine × phi) × suspended`, where `fine` is the wash's share of colloidal pigment, `phi` its concentration in suspension, and `suspended` = fine + 0.4 (1 − fine) (coarse pigment has mostly settled before it can travel; [W1]: "most of the particles in the black and blue pigments sediment in the order of seconds"). For fine pigments the band also widens with concentration ([W1]: "the thickness of the coffee ring increase[s]" for colloidal pigments and "does not change significantly" for larger particles). Particle size is not in the handprint data; granulation is used as the proxy (Gr 0 → fine, Gr ≥ 1.5 → coarse), which agrees with the four pigments measured by DLS in [W1]. RING0 = 0.05 and RING1 = 0.8 were fitted so that light and middle washes fall in the real rim range and coarse washes stay flat with load:

| wash (cold press, feather 1.5) | before rim | after rim | after: dark band > 3% (mm) |
|---|---|---|---|
| quinacridone violet 0.15 / 0.35 / 0.7 | 1.13 / 1.10 / 1.08 | 1.07 / 1.05 / 1.08 | 0.5 / 0.5 / 0.75 |
| alizarin 0.15 / 0.35 / 0.7 | 1.11 / 1.11 / 1.08 | 1.05 / 1.10 / 1.13 | 0.5 / 0.75 / 0.75 |
| ultramarine 0.15 / 0.35 / 0.7 | 1.11 / 1.10 / 1.09 | 0.96 / 0.98 / 0.98 | 0 / 0 / 0 |
| natural earth PBr7 0.15 / 0.35 / 0.7 | 1.05 / 1.06 / 1.07 | 0.98 / 0.99 / 1.00 | 0 / 0.25 / 0.25 |

The heaviest fine washes (1.10-1.13) sit above the three real washes measured (0.92-1.06); none of those is known to be a fine pigment at a heavy load, so this follows [W1] rather than the references.

**Two bugs in back-runs**, found while checking the sheets: when any damp wash existed, every fresh wash laid in the same episode was treated as part of the bloom, and its whole boundary received a dark line; and the bloom's front was deposited by dividing at the receiver (one-pixel lines). The bloom now grows only inside the damp wash, its front forms away from the contact line, a few pixels wide, mass-conserving.

**Drying time.** Water is lost at a constant rate (a thin film), to the air and into the sheet while it has room; the sheet then dries from inside. On cold press air = 0.20, absorb = 0.13 per episode, damp gain 2, damp decay 0.9 per episode give a water-1 wash: shine gone at 3.1 episodes, dry at 4.1 (continuous time), against t_c = 2490 s = 4.15 episodes of 10 minutes. Hot press (0.21 / 0.07) keeps the shine to 3.5 and dries at 3.8; rough (0.21 / 0.17) loses the shine at 2.8 and dries at 4.2 (relative rates eye). At episode steps: water 0.45 dries in 2, 1 in 4, 1.5 in 6 on every paper. Before: 6-7 episodes whatever the load (the old glaze also ignored `water`).

**Granulation and paper texture.** With per-pigment granulation, the cold-press `gran` was raised 0.6 → 0.75 and the relief shading 0.045 → 0.05 so that blank paper, a non-granulating wash and a granulating wash all land on the real flat fields (table in the summary). Hot press and rough were scaled by the same factors (eye).

**Match, the watercolourist's hand.** The old brush decided per stamp whether to paint, so strokes broke into fragments, each of which dried with its own edge and ring; that, with the ring artefact, made the patchwork of outlined "sausages". Now: the decision is taken once per stroke (skip below about 5% darkening, `skip`); the stroke is continuous; strokes of 14 px and more lay a soft margin of clean water (0.3 × size wide, half the stroke's water) so that neighbours of one episode join into one wash and their edges bleed softly when the water moves; smaller strokes stay crisp. Strokes laid on dry paper no longer bloom into the wet trail of strokes laid in the same episode (only into water that was there before: earlier washes, clean water, a glaze of this episode). The count of strokes is decided by `studio.py` (`do_match`), which this calibration did not touch.

Match painting statistics (Richmond schema; real = the seven references):

| statistic | real 4 px/mm | before | after | real 8 px/mm | before | after |
|---|---|---|---|---|---|---|
| edge rise, mm | 1.88 (1.75-2.06) | 2.63 | **1.88** | 1.06 (0.94-1.06) | 1.19 | 0.81 |
| hard-edge share | 0.24 (0.21-0.30) | 0.13 | **0.26** | 0.23 (0.19-0.30) | 0.11 | **0.22** |
| texture std L* | 5.6 (4.8-6.1) | 2.1 | 1.8 | 4.5 (3.6-4.8) | 1.4 | 1.3 |
| spectrum slope | -2.34 (-2.43 – -2.12) | -2.70 | -2.91 | -2.54 (-2.67 – -2.38) | -3.42 | -3.20 |
| coherence | 0.57 (0.43-0.62) | 0.47 | 0.46 | 0.61 (0.45-0.65) | 0.59 | 0.56 |
| width CV along marks | 0.28 (0.22-0.37) | 0.23 | 0.17 | 0.25 (0.22-0.34) | 0.18 | 0.15 |
| paper share | 0.056 (0.047-0.103) | 0.064 | 0.083 | 0.057 | 0.063 | 0.083 |
| mean chroma | 13.9 (12.4-20.2) | 17.7 | 17.1 | 14.0 | 17.7 | 17.1 |
| mean error to the schema (RGB) | | 0.076 | 0.076 | | | |

Speed: three match episodes of 200, 300 and 400 strokes on a 1200 × 1600 canvas took 18.5, 10.7 and 7.1 s (before 15.4, 11.4, 9.4 s). `python3 test_v8.py --only watercolour` passes.

## 4. What could not be calibrated, and weak data

- **The rim target rests on three isolated washes in two works** (pigments unknown). The literature trend [W1] is qualitative here: its figure of ring thickness vs concentration was not read as numbers, so the size of the growth for fine pigments is fitted by eye to stay plausible.
- **Particle size per pigment is a proxy** (the granulation rating); only four pigments have measured sizes.
- **The granulating target is one 150 px crop** of an unidentified blue in Richmond's study.
- **Episode length (10 minutes)** is an assumption; the measured drying time sets the ratio between drying and the episode, not the episode itself. The thin-film proportionality of drying time to water is an assumption, and the drop's spread area in [W1] was not found in the text, so "water 1 = the drop's load" is a definition, not a conversion from µL/cm². The paper's own evaporation rate for wet sheets ("−1.405 gr/s") was not used: its units are unclear in the text.
- **Hot-press and rough papers:** no drying, texture or edge measurements; rates kept relative to cold press.
- **Whole-painting texture and spectrum** stay below the references (a match painting is smoother than a real one, with fewer small marks and more uniform stroke widths). These statistics are dominated by how the painter works (stroke count and shapes in `studio.py`), not by the paint; they were not used to tune the medium. By eye the after-painting reads more like watercolour (soft fused passages, crisp flat accents, no outlines) but its marks are rounder and more uniform than Richmond's angular dabs, which no statistic here captures well (width CV comes closest: 0.17 vs 0.28).
- **Lifting, the wet-in-wet spread and back-run size** have no measurements; lifting now scales with the pigment's measured staining, so lifts from most paints (median staining 3 of 4) are faint; the effects sheet lifts from viridian (staining 1).
- **Mixed colours** are matched to one nearest pigment; a wash cannot hold two pigments with separate behaviours.

## Sources
[P3], [W1] as in `docs/media-data.md`: B. MacEvoy, handprint.com "guide to watercolor pigments" (ratings via `studio/pigments.json`); J. González-Gutiérrez et al., "Pattern formation by droplet evaporation and imbibition in watercolor paintings", arXiv:1909.09098 (2019), read again for this calibration (results and methods: t_c = 2490 s; ring thickness vs particle size; settling of the coarse pigments; Table I particle sizes). References: The Met Open Access (CC0) works listed in `studio/calibration_refs.json`.
