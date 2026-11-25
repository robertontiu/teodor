# Calibration report: ink (`studio/v8/media/ink.py`)

Nov 25-26, 2026. Method as in `docs/media-data.md` ("Calibration method"); targets from its "Top calibration targets per medium" for ink. The short version is in the manual page (`docs/manual/ink.md`, "Calibration").

## Summary

| Target | Before | After | Real / data |
|---|---|---|---|
| Raw-xuan spread per µL (50 µL drop, visible stain) | 0.17 cm²/µL, the same for every xuan, and falling with volume (0.24 at 5 µL, 0.19 at 20, 0.17 at 50) | volume-conserving: Qianlong 0.50, bamboo 0.46, Jingpi 0.40 cm²/µL at every volume (wetted area exactly 0.490 / 0.454 / 0.392) | 24.5 / 22.7 / 19.6 cm² for 50 µL = 0.49 / 0.454 / 0.392 cm²/µL [I1] |
| Flying white (share of a stroke's envelope where paper shows; upright brush, 18 strokes × 6 seeds) | median 0.0016 (0-0.0033): no flying white except when a stroke ran fully dry | median 0.027 (0.019-0.047) | `paper_in_marks` 0.031 (0.007-0.068), n = 10 |
| Width CV along strokes, calligraphy passage | 0.163 | 0.235 | calligraphy refs 0.24 (0.19-0.26), n = 3; all refs 0.28 (0.26-0.30), n = 10 |
| Width CV along strokes, landscape passage | 0.206 | 0.296 | painting and drawing refs 0.29 (0.26-0.38), n = 7 |
| Edge rise, landscape passage (3 px/mm) | 1.17 mm | 0.83 mm | 0.88 mm (0.75-1.66) |
| Edge rise, isolated strokes (3 px/mm) | 2.17 mm (the belly's tone ramp read as a soft edge) | 1.17 mm | 0.88 mm (0.75-1.66) |
| Hard-edge share, raw / sized xuan (landscape) | 0.22 / 0.47 | 0.34 / 0.51 | 0.28 (0.16-0.42); raw lower than sized |
| Orientation coherence | 0.75 (calligraphy), 0.78 (landscape) | 0.75, 0.79 | calligraphy refs 0.79 (0.73-0.83); all 0.58 (0.50-0.72): set by the composition, see 4 |
| Spectrum slope | -3.64 (calligraphy), -3.39 (landscape) | -3.40, -3.31 (sized and silk: -3.26, -2.92) | -2.85 (-2.87 – -2.08); calligraphy refs -2.87 to -3.18: still too smooth, see 4 |

## 1. The real targets

Ten Met ink paintings (`studio/calibration_refs.json` group `ink_brush`; `python3 tools/calibrate_media.py refs ink_brush`): three calligraphy scrolls (Hai Rui 48903, Seigan Sōi 902217, Mi Wanzhong 48967), four landscape and figure scrolls (Gu Yun 737736, Tani Bunchō 916565, Liu Shiru 36084 on silk, an unidentified Mountain Retreat 51415 on silk), a 12th-century iconographic drawing (45620) and two Hokusai ink drawings (57262, 57261). Automatic crops, measured at the photographs' resolution (1.3-14.8 px/mm; the scroll scales include the mounting and are too small, so only dimensionless statistics are compared for the scrolls).

| statistic | median (IQR), n = 10 | per work (737736, 916565, 48903, 902217, 36084, 48967, 45620, 51415, 57262, 57261) |
|---|---|---|
| width CV along marks | 0.276 (0.256-0.303) | 0.30, 0.38, 0.24, 0.26, 0.45, 0.19, 0.31, 0.26, 0.26, 0.29 |
| paper in marks (gap share) | 0.031 (0.007-0.068) | 0.068, 0.027, 0.035, 0.009, 0.093, 0.000, 0.067, 0.215, 0.007, 0.001 |
| orientation coherence | 0.58 (0.50-0.72) | 0.58, 0.39, 0.83, 0.73, 0.27, 0.79, 0.70, 0.50, 0.50, 0.57 |
| spectrum slope | -2.85 (-2.87 – -2.08) | -2.87, -1.75, -3.18, -2.87, -1.93, -2.87, -1.04, -2.54, -2.84, -2.91 |
| hard-edge share | 0.28 (0.16-0.42) | 0.24, 0.40, 0.53, 0.29, 0.10, 0.42, 0.50, 0.28, 0.13, 0.10 |
| edge rise 10-90%, mm | 0.88 (0.75-1.66) | 0.91, 0.90, 0.86, 0.74, 3.37, 1.91, 0.75, 3.10, 0.74, 0.71 |
| texture std L* (flat) | 2.54 (1.84-3.16) | 3.37, 1.34, 2.19, 1.72, 2.68, 1.54, 4.46, 2.44, 3.32, 2.65 |

What the gap share measures on these crops: on the calligraphy it is flying white (0, 0.009, 0.035); on the silk paintings (0.093, 0.215) it is mostly the weave and the light silk between dense texture strokes; on the line drawing (0.067) it is paper enclosed by lines. So the median 0.03 mixes flying white with composition; the calligraphy subset (median 0.009, max 0.035) is the cleanest flying-white figure and the target 0.03 is at its top.

The physical data [I1] (Wu, Wu & Chu 2016, read again this session): 50 µL drops released from 1 mm on three raw xuan papers spread to 24.5, 22.7 and 19.6 cm² (Qianlong, bamboo, Jingpi); the contact angle 0.02 s after a 4 µL drop lands is 36.8°, 50.1° and 60.6° (averages over 200 positions); fibres overlap 77, 52 and 40 times per mm (SEM; the paper gives the unit per millimetre, no further definition); web densities 463, 356, 429 kg/m³; thickness "of the order of 10⁻⁴ m". The paper does not say when the spread area was read, nor describe a halo structure (dark core, pale fringe, water ring); it notes that the boundary on Qianlong xuan "looks smoother".

## 2. Scale and units (new, and documented in the module)

- **Pixels to millimetres.** A canvas is a sheet at `PX_PER_MM` = 4 (1200 × 1600 px = 30 × 40 cm, the same convention as the watercolour report); `cv.meta["px_per_mm"]` overrides it. A brush `size` of 40 is a 10 mm footprint.
- **Brush load to microlitres.** Every tool lays liquid `Wl` with its ink (the stroke buffer). `Wl` = 1 is a film of `FILM_UM` = 45 µm, i.e. 2.8 nL per pixel at 4 px/mm, so a stroke's release in µL is Σ Wl × 45e-3 / ppm². The 45 µm is an estimate, not a measurement (about one brush-hair diameter, 50-100 µm for wolf and goat hair; no measured brush release was found, see `docs/media-data.md` "Not available"). It decides which strokes bleed: with bamboo xuan's capacity (below), a stroke spreads only where it lays more than 0.49 of a full film, so scorched and thick ink (`jiao`, `nong`: water 0.32, 0.52) barely bleed, medium to clear ink (0.72-0.94, more with slow dwell) does.
- **Paper capacity.** At rest the spread ink fills the paper to `10 / area` µm of liquid per mm² (area in cm²/µL): 20.4 µm (Qianlong), 22.0 µm (bamboo), 25.5 µm (Jingpi). Against a ~100 µm sheet of 360-460 kg/m³ (pores ~70% of the volume) that is about a third of the pore volume: plausible for ink that stops spreading before the sheet is saturated.
- **Xuan type.** `cv.meta["xuan"]`: `qianlong`, `bamboo` (default), `jingpi`; set it in `<canvas>_meta.json`.

## 3. What changed in the model

**Raw-xuan bleed (structural).** The old flow (a fixed number of diffusion steps with a pinning threshold and 2.2% absorption per step) did not conserve volume: the stained area per µL fell with volume and had no relation to any paper. The new `_bleed_raw`:
1. converts the stroke's liquid into units of the paper's capacity; the share above capacity is free liquid, and the same share of the stroke's soot is mobile (the rest stays where the brush laid it, at full resolution, with a crisp edge where the brush was nearly dry and a soft one where it was wet);
2. on a coarse grid (2-8 px per cell, chosen so the halo is reached in ~40 steps) the free liquid evens out inside the saturated paper and is pushed into neighbouring cells that still have room, in proportion to a fibre-web permeability; cells fill to capacity and stop;
3. liquid still free when the steps run out wets the nearest dry cells (distance over permeability), so the wetted area is always volume / capacity: the drop test reproduces Wu's areas to within 0.3% for the water, 2% for the visible stain (the wicking fringe below adds a little);
4. soot moves with the liquid; liquid soaking into dry paper leaves its soot there, and soot is filtered out of the liquid still moving through wet paper (1/e per `SOOT_STEPS` = 30 steps), so the halo is paler than the core and fades outward. The filtering strength is by eye; it was set so the visible stain (optical density ≥ 0.02 over the bare paper) still reaches the wetted front, as Wu's measured areas are stain areas;
5. the front at full resolution breaks along the fibre field (`FEATHER`), and a fibre-wicking fringe (`WICK_MM` = 0.3 mm on bamboo xuan) feathers every edge, even where no liquid is left to spread.

**Where the xuan figures enter.** Area per µL sets the capacity (data). Fibre overlaps set the roughness of the front: permeability noise amplitude ∝ 1/√(overlaps), i.e. 0.37 / 0.45 / 0.51 on Qianlong / bamboo / Jingpi (the relative scaling assumes the local permeability averages over the fibres crossing a cell; the bamboo amplitude `ROUGH` = 0.45 is by eye; Wu's smoother Qianlong boundary is the qualitative check). The contact angle sets the wicking fringe's length relative to bamboo by √(cos θ) (Washburn's law: penetration length ∝ √(γ r cos θ t / 2μ)): 1.12× on Qianlong, 0.87× on Jingpi; the fringe's absolute length is by eye (set by the hard-edge share, below). The contact angle has no other effect: its influence on the end state of a drop is already inside the measured spread area. Fibre overlaps of 40-77 per mm mean 10-19 fibres per pixel at 4 px/mm, so single fibres are below the canvas's resolution; the visible fibrous texture in halos is fibre bundles and formation, drawn by eye.

**Damp paper.** Paper still damp from earlier strokes in the episode fills `DAMP_FILL` = 0.5 of its capacity (by eye: the felt underlay and evaporation take the rest). Without this, wet-in-wet `match` washes travelled across saturated paper to the edge of each stroke's bounding box and left rectangular stains.

**The brush's mark.**
- Edge: the tuft's edge is the hairs' ends, about one pixel wide and ragged hair by hair (it was a ramp over the outer 20% of the radius, raised to 0.6).
- Tone across the stroke: the tip's full tone fills the middle (`PLATEAU` = 0.55 of the half-width), the belly's paler ink shows only at the margins. Before, the tone fell from the centre over the whole half-width, which the edge statistic read as a 2 mm soft edge on isolated strokes. Set by the edge rise.
- Width along the stroke: a slow swell and thinning of the contact (lifting and pressing), `RHYTHM` = 0.3 of the radius over a wavelength of 5-10 brush widths. Set by the width CV (sweep: 0 → calligraphy 0.14, landscape 0.19; 0.3 → 0.24, 0.30; 0.45 → 0.28, 0.34). A first version with a second, short wavelength gave a beaded look and was dropped (by eye).
- Flying white: hairs dry in bundles (`CLUMP` = 8% of the tuft's hairs) instead of one by one, so the white streaks are wide enough to read at the references' resolution; speed opens streaks in the middle of a fast stroke that close again as the brush slows (`SPEED_DRY` = 4.0, saturating at 0.45 so a very fast brush still marks); pressing squeezes ink into the tip; a brush runs dry after `DRAIN` = 18 brush widths of stroke per unit of load and thickness, with the reservoir of a fine line taken as at least a 16 px brush's (`RES_MIN`; before, thin lines ran dry within a few centimetres and drew dashed "stitches"). `DRAIN` and `SPEED_DRY` were swept together against the flying-white share (DRAIN 13/16/18 → median 0.074/0.041/0.027 at SPEED_DRY 4). The side brush keeps its old dryness (envelope share 0.28 before, 0.28 after; by eye).

**Speed.** The bleed loop runs on shifted array slices and a box filter. `match` on 1200 × 1600: 250 wash strokes 17.7 s CPU (before 12.6 s), 300 brush strokes 9.3 s (before 8.0 s).

## 4. Measurements before and after

Test passages (scripts in a scratch folder, not kept): a calligraphy passage (6 "characters" of 5-8 strokes each: horizontals, verticals, sweeps, dots; brush sizes 21-36 px; nong and jiao; arousal 0.4-0.75; 720 × 1000 px) and a landscape passage (two dan washes, seven tree trunks drawn as pairs of contour lines, 90 texture strokes in side brush, nong and jiao, 40 foliage dots; 1000 × 1000 px), on xuan_raw, xuan_sized and silk, plus a sheet of 18 isolated strokes (sizes 14-44, tones jiao to dan, arousal 0.25-0.8). Rendered at 4 px/mm, resampled (Lanczos) and blurred by σ = 0.6 px as the photographs' blur: the landscape and the single strokes to 3 px/mm (the references' median scale); the calligraphy to 0.4× (1.6 px/mm) so that its stroke widths in pixels (~14 px) match the calligraphy references', whose scroll scale is unreliable.

| passage, support | width CV | gap share | coherence | slope | hard share | edge rise mm | texture std L* |
|---|---|---|---|---|---|---|---|
| calligraphy, raw, before | 0.163 | 0.102 | 0.746 | -3.64 | 0.333 | n/a | 2.94 |
| calligraphy, raw, after | **0.235** | 0.062 | 0.746 | -3.40 | 0.312 | n/a | 3.40 |
| calligraphy, sized, before → after | 0.168 → 0.221 | 0.109 → 0.077 | 0.738 → 0.734 | -3.51 → -3.26 | 0.391 → 0.438 | | 3.11 → 3.45 |
| calligraphy, silk, before → after | 0.155 → 0.208 | 0.113 → 0.080 | 0.739 → 0.736 | -3.51 → -3.27 | 0.388 → 0.471 | | 2.62 → 2.87 |
| landscape, raw, before | 0.206 | 0.004 | 0.781 | -3.39 | 0.218 | 1.17 | 2.06 |
| landscape, raw, after | **0.296** | 0.004 | 0.789 | -3.31 | **0.335** | **0.83** | 2.52 |
| landscape, sized, before → after | 0.225 → 0.318 | 0.010 → 0.011 | 0.771 → 0.784 | -3.11 → -2.93 | 0.465 → 0.510 | 0.83 → 0.50 | 2.28 → 2.66 |
| landscape, silk, before → after | 0.228 → 0.321 | 0.011 → 0.012 | 0.774 → 0.787 | -3.11 → -2.92 | 0.361 → 0.498 | 0.83 → 0.83 | 1.70 → 1.97 |
| isolated strokes, raw, before → after | 0.131 → 0.321 | 0 → 0 | 0.919 → 0.913 | -4.15 → -3.66 | 0.066 → 0.061 | 2.17 → 1.17 | 1.50 → 1.65 |

Flying white needed its own measurement: the tool's gap share counts paper only inside the closed hull of the marks, and a stroke whose hairs separate toward its end leaves streaks open at the tail, which never count; on the passages it mostly measures paper enclosed by crossing strokes (the calligraphy's counters: 0.06-0.10). So the isolated-stroke sheet was rendered twice, with and without the flying-white gate, and the share of the gate-less envelope (L* < paper − 12) that shows paper (L* ≥ paper − 6) in the real render was measured, over six seeds: before 0.0006, 0.0020, 0.0030, 0.0011, 0.0033, 0.0000 (median 0.0016); after 0.019, 0.023, 0.047, 0.035, 0.028, 0.026 (median 0.027). On sized xuan the same sheet gives 0.064 (raw xuan's bleed fills part of the white). Side brush: 0.276 before, 0.283 after.

Drop test (a disc of liquid film 1.6, i.e. 72 µm, at the given volume; stained = optical density ≥ 0.02 over the same canvas before the drop):

| xuan | 5 µL | 20 µL | 50 µL | wetted area per µL | Wu et al. |
|---|---|---|---|---|---|
| before (one paper) | 0.241 | 0.193 | 0.171 | (not defined) | |
| Qianlong | 0.509 | 0.502 | 0.499 | 0.490 | 0.490 |
| bamboo | 0.476 | 0.466 | 0.463 | 0.454 | 0.454 |
| Jingpi | 0.416 | 0.403 | 0.401 | 0.392 | 0.392 |

## 5. What could not be calibrated, and why

- **Spectrum slope** stays steeper (smoother) than the references: -3.3 to -3.4 on raw xuan against -2.85 overall and -2.87 to -3.18 for the calligraphy. It moved the right way (from -3.6/-3.4). A soot mottle inside marks (tested, ±15-30%) did not change it, because the slope is dominated by the size distribution of the marks in the passage, which is the painter's, not the medium's; the references also carry aged, foxed paper, silk weave and JPEG noise. The slope is also sensitive to the assumed photographic blur: σ = 0 / 0.3 / 0.6 px gives -3.15 / -3.16 / -3.47 on the calligraphy passage (and hard-edge share 0.71 / 0.71 / 0.32). All before/after numbers use σ = 0.6.
- **Orientation coherence** (0.75-0.79 against 0.58) is a property of the composition: the calligraphy passage matches the calligraphy references (0.73-0.83); the landscape passage has long parallel trunks and horizontal texture strokes, and the low references (silk paintings 0.27, 0.50; Tani Bunchō 0.39) have dense multidirectional texture and silk weave. No medium parameter was moved for it.
- **The liquid film (`FILM_UM`)**: not measured. It sets which strokes bleed and how far; the area per µL is exact only relative to it. A measurement of the ink a loaded brush releases per cm² of stroke (weighing the brush before and after) would fix it.
- **Halo structure** (pale fringe, darker front line, water ring beyond the soot): Wu et al. measured only the area; `SOOT_STEPS`, `FEATHER` and `ROUGH` are by eye. The old model's darker front rim is gone (nothing in the data supports it, and the references' rim ratio is below 1); the halo now fades outward.
- **Contact angle**: used only for the relative length of the wicking fringe (√cos θ); its absolute length `WICK_MM` was set by the hard-edge share on raw xuan (0.34 against 0.28, sized 0.51), not by a measurement.
- **Brush geometry** (hair counts, footprint versus pressure, reservoir): not found as data [I2][I3]; `RES_MIN`, `CLUMP`, the pressure-to-width curve and the tip/belly tones remain by eye.
- **Wet-in-wet** (`DAMP_FILL`, the old `keep` per support) and the sized supports' slight bleed: by eye.
- **Gap share against composition**: the reference figure (0.03) mixes flying white with enclosed paper; the isolated-stroke measurement above is our own definition, calibrated to the reference median.
- **By eye after calibration**: the strokes now taper, swell and break into flying white in their fast middles; wet strokes still end in round pooled blobs with a halo on raw xuan (the core's slow ends release more water), which is plausible but more regular than in the references.
