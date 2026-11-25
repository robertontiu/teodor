# Media data: measured figures for the studio's media, and how to calibrate against real marks

The rule for the studio's media ("utensils") is that they rest on research and real data, not on values tuned by eye. This file collects the data found for that (Nov 25, 2026), says which engine parameter each figure should set, and defines a calibration method: statistics measured the same way on real marks and on the studio's rendered marks. It is the painting counterpart of Spectre's measured instruments (`spectre/engine/chamber.py`, `spectre/tools/refcurve.py`).

Files that go with it:
- `studio/pigments.json`: the pigment library (147 pigments by Colour Index name) with provenance per entry.
- `studio/calibration_refs.json`: 78 public-domain Met works in 9 media groups, with full-resolution image URLs, verified downloads, scale (px per mm) and suggested crops.
- `tools/calibrate_media.py`: measures the calibration statistics on any image region, on the references (`refs <medium>`), and compares two measurement files.

Status marks used below:
- **[data]**: numbers computed here from a downloaded, citable dataset (the computation is reproducible from the files named).
- **[read]**: a figure read in the source itself, quoted as given.
- **[measured here]**: measured by `tools/calibrate_media.py` on the Met reference crops (the photographs, not the objects).
- **[not verified]**: known from the literature but not read this session; check before relying on it.
- **[not found]**: searched for and not found as a measurement.

Contents: [Pigments](#pigments) · [Oil](#oil) · [Watercolour](#watercolour) · [Gouache](#gouache) · [Ink](#ink) · [Charcoal, graphite, pastel](#charcoal-graphite-pastel) · [Egg tempera and gold ground](#egg-tempera-and-gold-ground) · [Woodblock (ukiyo-e)](#woodblock-ukiyo-e) · [Not available](#not-available) · [Calibration method](#calibration-method) · [Top calibration targets per medium](#top-calibration-targets-per-medium) · [Sources](#sources)

---

## Pigments

### What was found and downloaded
| Dataset | What it holds | Licence | Used for |
|---|---|---|---|
| **Revigo** (Geldof et al. 2018) [P1] | 16 hand-ground 19th-century oil paints (Van Gogh's palette: eosine and cochineal lakes, red lead, vermilion, zinc and lead white, viridian, emerald green, ultramarine, cobalt blue, Prussian blue, chrome yellows, bone black, extenders) plus their mixtures with zinc white and bone black; each as a 100 µm drawdown over the black and the white of a BYK chart; Konica Minolta CM-2600d, SCI, 400-700 nm / 10 nm | CC0 | oil K and S (two-constant Kubelka-Munk), masstone, glaze and tint colours, the kmix check |
| **Pigments Checker FORS** (Cosentino 2014) [P2] | 54 historical pigments in gum arabic, egg tempera, linseed oil and fresco (and powder), 360-1000 nm | free download, no licence stated | approximate masstone hue per binder |
| **handprint** (MacEvoy, rev. 2015) [P3] | ratings of 750+ commercial watercolours: transparency, staining, granulation, blossom, diffusion (0-4), value range, CIELAB hue angle (GretagMacbeth spectrophotometer); CIECAM J,a,b masstone and drying shift in the notes | web pages, quoted as data with credit | watercolour granulation, staining, opacity, darkest value, drying shift |
| **Curtis et al. 1997, Fig. 5** [P4] | 12 watercolour pigments' K, S (RGB), density, staining power, granularity | paper | kept as the graphics baseline; **not measured** (colours chosen by eye) |

Not available: the RIT Munsell Color Science Laboratory artist-paint database (Okumura 2005, "Developing a Spectral and Colorimetric Database of Artist Paint Materials") is listed by RIT's repository as withdrawn, physical copy only [P5]; the Mixbox paper's pigment measurements are not published as data (only the latent lookup table, under a non-commercial licence) [P6]; ColourLex and CAMEO pages refused the workspace's requests (403/redirect), so their spectra and historical notes were not used.

### How `pigments.json` was computed [data]
- **Oil (Revigo).** The paper's Saunderson correction (k1 = 0.04, k2 = 0.49, SCI [read] [P1]) is removed from every spectrum; then per wavelength the pigment's K and S (per film of the 100 µm drawdown) are fitted so that the film over the chart's black and over its white, *and* the pigment's mixtures with zinc white (Duncan's rule, weight fractions), are reproduced by the two-constant KM layer equation. Zinc white is fitted first from its own (non-hiding) film; bone black from its four mixtures with zinc white. The fit's rms error in internal reflectance is stored per pigment (0.002-0.016; the eosine lake fits worst, 0.06).
- **Colours** are computed with the CIE 1931 2° observer and D65, specular excluded (the 4% first-surface reflection removed: the colour away from glare). Each oil entry has `masstone` (R∞), the measured film over white and over black, the 100 µm film over ideal white and black, and a **glaze** (a tenth of the drawdown) over ideal white and black.
- **`engine`** gives `over_white`/`over_black` of the glaze in the engine's convention (sRGB-encoded 0..1, like `hx()`), ready for `media.base.pigment()`, plus `K_rgb`/`S_rgb` from that function and band-averaged spectral K and S.
- **Watercolour (handprint)**: medians over the brands tested per Colour Index name; `engine.granulation = Gr/4`, `engine.staining = St/4`, `engine.opacity = 1 - Tr/4`, `engine.darkest_L` ≈ paper value (about 94) minus the value range. Natural iron oxides (PBr7) are also split by marketing name (raw/burnt sienna and umber).
- **FORS**: the CSV scale is relative (titanium white reads 108-133%, carbon blacks about 10%), so each binder set was normalised per wavelength to lamp black = 0.03 and titanium white = 0.90. These colours are approximate; use them for hue, not value.

### Finding: the engine's `kmix` against measured tints [data]
`kmix` (per-channel single-constant KM, blended 58/42 with linear) was checked against the 29 measured Revigo tints with zinc white (pigment weight fractions 1-99%), using the measured masstones as inputs:

| Mixing model | median ΔE2000 | max ΔE2000 |
|---|---|---|
| engine `kmix` (RGB, single-constant, 58/42 linear) | **12.6** | 37.9 (Prussian blue 1:99 in white) |
| RGB two-constant KM (K and S averaged into three bands) | 9.1 | 36.7 (chrome yellow) |
| spectral two-constant KM, 31 bands (Duncan) | 1.3 | 7.9 (eosine lake) |

The spectral result is an in-sample fit (the tints were used to fit K and S), so it shows that the two-constant model with these constants explains the data, not that it predicts new mixtures; the two RGB rows are predictions. What fails in RGB is **tinting strength**: 6% Prussian blue in zinc white is still a strong mid blue (measured), while `kmix` at t = 0.94 white gives a near-white. A colour model with a per-pigment strength (two-constant K and S, spectral or at least 6-8 bands; or Mixbox's latent mixing) is needed for oil, gouache and pastel mixing. `kmix_check_tints` in `pigments.json` lists every case.

### Watercolour pigment attributes [data, from handprint]
- **Granulation** is rare: of 115 pigments, 71 rate 0, 21 rate 1, 19 rate 2, 1 rates 3 and 3 rate 4 (cobalt violet light PV49, cobalt green PG19, manganese blue PB33). Ultramarine (PB29) rates 2, cobalt blue (PB28) 1, phthalo blue (PB15:3) 0, Prussian blue (PB27) 0, the natural earths (PBr7) 1 (median). The studio's `_guess_granulation` gives 0.65 to every blue and 0.5 to earths; the data say about 0.5 for ultramarine, 0.25 for cobalt and earths and 0 for phthalo and Prussian blue. **Engine parameter:** `watercolour.gran` per pigment from `pigments.json`, not from the hue.
- **Staining** is common: ratings 0/1/2/3/4 for 4/8/27/39/37 pigments. The studio's default staining 0.4 sits below the median (3/4 = 0.75). **Engine parameter:** `watercolour.stain`.
- **Value range** (paper value minus masstone value): 10th/50th/90th percentile 9/48/64 steps of 100. **Engine parameter:** the darkest a single full-strength wash can go per pigment (`darkest_L`).
- **Drying shift** (lightness change from glistening wet to dry), read from the notes for 12 pigments: Prussian blue +68%, indanthrone blue +50%, dioxazine violet +38%, phthalo cyan and turquoise +20%, perylene scarlet +17%, quinacridone violet +15%, quinacridone burnt orange, benzimidazolone carmine and cobalt blue deep +10%, chrome titanate -5%, chromium oxide green -13% (it darkens); earth pigments up to +30% for the darkest umbers [read] [P3]; lamp black "increasing in lightness by 180%" [read] [P3]. **Engine parameter:** the watercolour render's wet-to-dry shift per pigment (today one shift for all).

---

## Oil

| Figure | Value | Status | Engine parameter |
|---|---|---|---|
| Drawdown thickness of the Revigo films | "relatively uniform layer of 100 µm thickness" (applicator) | [read] [P1] | the unit thickness of `pigments.json` oil K and S; a glaze of x = 0.1 is about 10 µm wet |
| First-surface reflection of an oil/varnish surface | k1 = 0.04 (Saunderson, used for the SCI data) | [read] [P1] | `oil.render` gloss: a matte or sunken passage adds up to ~4% diffuse white to the darks |
| Effect of that 4% on a dark | a black at 0.4% reflectance (glossy, specular excluded) reads L* ≈ 3.6; with 4% diffuse surface scatter added, L* ≈ 25 | [data] (computed from Y) | `finish varnish`/`retouch`: what varnish restores in the darks (sinking in) |
| Varnish refractive indices | dammar 1.535-1.539, mastic 1.536, Laropal K80 1.529, ketone-resin varnish 1.53, MS2A 1.505 | [read] [V1] (citing de la Rie & McGlinchey 1990) | `finish varnish` index per varnish; Fresnel reflectance at normal incidence ((n-1)/(n+1))² is 4.5% for n = 1.535, 4.2% for n = 1.505 [data] |
| Varnish, saturation and matteness | under a high-index, low-viscosity varnish (dammar) paint "appear[s] saturated", the resin "flows into and fills roughnesses"; a varnish "negates any differences of saturation"; "the less-saturated areas will become darker" | [read] [V1] [V2] | `finish varnish` evens `sheen` and darkens unsaturated (sunken) areas most |
| Berns & de la Rie, "The effect of the refractive index of a varnish on the appearance of oil paintings" (Studies in Conservation 2003) | quantitative ΔL* by varnish index | [not verified]: only the catalogue record was found [V3] | the size of the varnish effect in the darks |
| Paint layer thickness in a historical cross-section (*The Descent of the Cattle*): 16 layers of 10-50 µm; a "translucent green brown" layer 30-40 µm; reddish-brown layer >80 µm | as given | [read] [O1] | glaze `film thickness` (10-40 µm), body layers up to ~80 µm |
| Vermeer, *Girl with a Pearl Earring*: the pearl highlight's moat "approximately 200 µm deep", linked to the original impasto | as given | [read] [O2] | impasto height order of magnitude: 0.1-0.3 mm (the engine's `ht` scale per mm of canvas) |
| OCT on acrylic mock-ups: layers 45-350 µm, std below 6 µm | as given | [read] [O3] | (method reference for measuring layer thickness) |
| Real marks, 14 oil paintings (Van Gogh ×4, Rembrandt, Pissarro, Sisley, Renoir, Cézanne, Degas, Courbet, Guardi, van der Goes, Gerard David) | see the table under Calibration method | [measured here] | stroke width, edge rise, orientation coherence, texture scale targets |

## Watercolour

| Figure | Value | Status | Engine parameter |
|---|---|---|---|
| Drying of a 50 µL drop of watercolour on Fabriano cold-press paper (25% cotton, 300 g/m²), 22 °C, 35% RH | complete evaporation t_c "around 2500 s" (2490 s: time for the drop's mass to fall by 1/e) | [read] [W1] | `watercolour` drying rate (`air`, `absorb`): a wash stays workable for tens of minutes at that load |
| Stages on wet paper | ink first diffuses radially in the water body (t/t_c = 0.06), then a slow capillary diffusion toward the periphery (t/t_c = 0.12-0.36); on damp paper sharp tips appear by t/t_c = 0.016, the body vanishes at t/t_c = 1.8 | [read] [W1] | order and relative timing of spread vs edge growth in `episode_end` |
| Deposit vs concentration | mean intensity inside the ring follows μ = -μ0·e^(-φ/k) + μs: exponential saturation with concentration, the same for every pigment tested | [read] [W1] | wash density vs pigment load: saturating, not linear |
| Coffee ring vs particle size | ring thickness grows with concentration for colloidal pigments (Permanent Rose quinacridone 272 nm / 99 nm; Rose Genuine madder 164.5 / 573 nm) and does not change for larger particles (Ultramarine 3810 / 1669 nm; Mars Black 1528 / 258 / 5322 nm) | [read] [W1] (particle sizes by dynamic light scattering) | `ring` (edge darkening) per pigment: strong for fine organic pigments, weak for coarse minerals |
| Ring stains are the coffee-ring effect (capillary flow to a pinned edge) | | [not verified] (Deegan et al. 1997, cited in MEDIA.md) | physical basis of `ring` |
| Curtis et al.: μ = 0.1, κ = 0.01, edge darkening η = 0.01-0.05 with a 10×10 Gaussian | simulation settings | [read] [P4]; **not measurements** | current defaults; replace with the above where possible |
| Paper roughness | no measurement of watercolour (hot/cold/rough) papers found. For scale: printing papers Ra 2.2-2.7 µm (coated 0.51), tissue and towel 5.8-14.1 µm (profilometry, machine direction) | [read] [W2]; [not found] for art papers | bounds for `paper_h` amplitude; measure art papers from the references instead (texture statistics) |
| Real marks, 7 watercolours | see the Calibration method table | [measured here] | edge rise, texture, rim ratio targets |

## Gouache
| Figure | Value | Status | Engine parameter |
|---|---|---|---|
| Opaque whites in watercolour (handprint): zinc white PW4 Tr 1, titanium white PW6 Tr 2 | as rated | [data] [P3] | gouache white opacity |
| Real marks, 7 works (Pissarro gouache on silk, Degas, a textile design, John Frederick Lewis, carriage designs) | Calibration method table | [measured here] | flat-field texture (std L*), paper share, edge rise |
| Drying shift of gouache, opacifier content | | [not found] (only the Blick statement in MEDIA.md) | |

## Ink
| Figure | Value | Status | Engine parameter |
|---|---|---|---|
| Spread of a 50 µL ink drop (dropped from 1 mm) on three xuan papers | 24.5 cm² (Qianlong), 22.7 cm² (bamboo), 19.6 cm² (Jingpi): equivalent diameters 55.9, 53.8 and 50.0 mm, i.e. 0.39-0.49 cm² per µL | [read] [I1]; diameters [data] | `ink` bleed on `xuan_raw`: area per unit of water released |
| Contact angle 0.02 s after a 4 µL drop lands | 36.8° (Qianlong), 50.1° (bamboo), 60.6° (Jingpi) | [read] [I1] | absorbency ordering of xuan types |
| Fibre structure | fibre overlaps 77, 52, 40 per mm; fibre web density 463, 356, 429 kg/m³ | [read] [I1] | `fibres()` density in the xuan texture (about 40-80 crossings per mm) |
| Soot particle size | about 10-150 nm (an estimate in the paper, not their measurement) | [read] [I1] | carbon ink does not granulate; it stains (permanent once dry) |
| Brush geometry, hair counts, footprint vs pressure | | [not found]: the brush-simulation papers checked (Chu & Tai 2002; Xu et al. 2005) give no measured brush data [I2][I3] | |
| Real marks, 10 works (Chinese and Japanese scrolls, calligraphy, Hokusai ink drawings) | Calibration method table | [measured here] | stroke width and its variation along the stroke, flying-white gap share, hard-edge share |

Note on scale: hanging-scroll dimensions in The Met's records usually include the mounting, so `px_per_mm` for scrolls is too small (widths in mm too large). Use those references for dimensionless statistics (CV, coherence, gap share), or set the scale from the image dimensions ("Image: ...") where the record gives them.

## Charcoal, graphite, pastel
| Figure | Value | Status | Engine parameter |
|---|---|---|---|
| Graphite particle size in pencil marks | "typically between 2 and 10 micrometers"; 19 grades 9H-8B | [read] [D1] | the scale of graphite speckle (far below a studio pixel: speckle comes from the paper, not the particles) |
| Darkness and gloss per pencil grade, charcoal darkness, pastel opacity | | [not found] as measurements. The Getty's *Noir* project (charcoal, black chalk, conté, lithographic crayon; FORS, Raman, MA-XRF) lists its publications but the page gives no numbers [D2] | the studio's `GRADES` lightness ramp (0.6 at 6H to 0.16 at 9B) stays unverified; measure it from the references (darkest L* in hatched passages) |
| Real marks: 8 charcoal / black chalk / conté, 8 graphite, 8 pastel drawings (Ingres, Delacroix, Millet, Mauve, Degas, Redon, Rosalba Carriera, Perronneau...) | Calibration method table | [measured here] | tooth speckle (paper in marks), hatch coherence and spacing, texture, paper share |

## Egg tempera and gold ground
| Figure | Value | Status | Engine parameter |
|---|---|---|---|
| FORS masstones in egg tempera for 54 pigments | `pigments.json` → `masstone_by_binder` | [data] [P2] | tempera palette hues |
| Real marks, 8 gold-ground panels (Duccio, Daddi, Taddeo Gaddi, Fra Angelico, Lorenzetti, Sassetta, Giovanni da Milano, Crivelli) | highest chroma of all groups (mean C* 34), high hard-edge share | [measured here] | hatch stroke widths and the flat-field texture of gold |
| Hatch stroke dimensions, punch sizes | | [not found] as measurements | measure from the crops at full resolution |

## Woodblock (ukiyo-e)
| Figure | Value | Status | Engine parameter |
|---|---|---|---|
| Real marks, 8 prints (Hiroshige ×5, Hokusai ×3) | the highest hard-edge share after tempera (0.24), flat-field texture std L* 5.8 (baren mottle, paper fibre, wood grain) | [measured here] | keyline width and edge hardness, the `grain`/`paper_h` amplitude in flat fields, bokashi gradient length |
| Baren pressure, pigment load per impression | | [not found] | |

## Not available
- Measured roughness of artists' papers (watercolour hot/cold/rough, pastel, Ingres, xuan) as Ra or height spectra: not found. The closest data are printing papers and tissues [W2] and a WPI student project on museum papers that reports area-scale fractal results only [W3].
- Brush hair counts and pressure-to-width curves for brushes and pens: not found as measurements; the brush-simulation literature checked models them without measuring.
- Graphite grade darkness and gloss, charcoal darkness, pastel opacity: not found as numbers.
- Oil impasto heights for named paintings beyond the Vermeer figure: not found (3D-scan papers report scanner resolution, not stroke heights, in the parts read).
- Quantitative varnish ΔL* (Berns & de la Rie 2003): catalogue record only.
- The RIT artist-paint database and the Mixbox pigment measurements: not published (see Pigments).
- The FORS data's absolute scale: unverified; binder-to-binder lightness differences computed from it (oil minus gum arabic: median -0.7 L*, IQR -2.7 to +1.5, n = 53) are within the normalisation's noise and are **not** evidence about binder darkening.

---

## Calibration method

The principle (as in Spectre's reference curves): measure the same statistics, the same way, on real marks and on rendered marks, and move the medium's parameters until the rendered statistics fall inside the real works' range. A statistic is a ruler, not the goal; check the gallery sheet by eye afterwards.

### 1. Same physical scale
Marks must be compared in millimetres. A reference crop has its scale from the catalogued size (`px_per_mm` in `calibration_refs.json`; check `px_per_mm_note`). A studio canvas needs a stated size: a 1200×1600 canvas painted as a 30×40 cm watercolour has 4 px/mm. Before measuring a rendered crop, **resample it to the reference's px/mm**, and blur it by the reference photograph's own blur (the narrowest 10-90% edge rise found in the reference set, about 0.4-0.6 mm at these resolutions), otherwise the edge and texture statistics compare photographs with renders rather than marks with marks.

### 2. Crops
Use the suggested crops (automatic: the highest local detail energy away from margins, checked by eye) or better, medium-specific crops chosen by hand: an isolated wash with its whole boundary for edge darkening; a passage of hatching; a single calligraphic stroke from entry to exit; a flat field for granulation and paper texture. Note the chosen crop in `calibration_refs.json`.

### 3. The statistics (`tools/calibrate_media.py`)
| Statistic | Definition | What it calibrates |
|---|---|---|
| value histogram | L* percentiles 5/25/50/75/95, share of paper-light pixels, share with optical density D > 0.5 | the medium's darkest value per layer, coverage (`KC` in drymedia, watercolour concentration) |
| colour | mean and 95th-percentile chroma, chroma-weighted hue spread | pigment strength and the mixing model |
| spectrum slope | slope of the radially averaged power spectrum of L* between 1/64 and 1/4 cycles/px | overall fine-detail energy (steeper = smoother) |
| texture | std of high-passed L* in flat passages and its autocorrelation length (px, mm) | paper tooth / canvas weave / granulation scale and amplitude (`paper_h`, `gran`, the support textures) |
| edge rise | 10-90% distance across strong edges (median, mm) and the share of hard edges (≤ 2 px) | edge sharpness per tool and support (`sharp`, `ragged`, `EDGE`) |
| rim ratio | optical density in a band just inside a wash boundary (past the edge rise) over the density deeper inside; > 1 = darkened edge | watercolour edge darkening (`ring`), back-run rims |
| stroke width | widths along the medial lines of the dark marks (distance transform), median and IQR in mm; coefficient of variation along each mark | brush and nib pressure-to-width, taper; `TONES`, nib `w0 + k·p` |
| gap share | share of paper-light pixels inside the closed hull of the marks | flying white, dry-brush, tooth speckle (`slope`, `speedfx`, stick `reach`) |
| hatch | structure-tensor orientation coherence (0 isotropic, 1 one direction), dominant line direction, line spacing from the spectrum across it | hatching in graphite, tempera, pen; directional brushwork |
| gloss, impasto height | **not measurable** from a diffuse museum photograph | use the literature figures above (100-300 µm impasto, 10-40 µm glazes, the 4% surface term) |

### 4. Procedure
1. `python3 tools/calibrate_media.py refs <medium>` downloads the references (to `~/.cache/teodor/met_full/`), measures the crops and writes `~/.cache/teodor/calib/<medium>.json` (per-work statistics, medians and quartiles).
2. Render the medium's gallery sheet or a test canvas with a stated physical size; crop the comparable passages; resample and blur as in step 1; measure with `calibrate_media.py image --crop ... --px-per-mm ... --json out.json`.
3. `calibrate_media.py compare ~/.cache/teodor/calib/<medium>.json out.json` prints the two side by side.
4. Change one parameter at a time, toward the reference's interquartile range; record the change and the before/after statistics in the medium's manual page, with the reference set it was fitted to.

### 5. First reference measurements [measured here]
Median (interquartile range) over each reference set, on the automatic crops, at the photographs' resolution (about 2-25 px/mm; median about 8). The edge rise and the texture correlation length are close to the photographs' resolution limit (0.1-0.2 mm = 1-2 px is the floor), so treat them as upper bounds on sharpness and as a resolution check, not as the marks' own scale. The rim ratio comes out below 1 on these crops because they are detail-rich passages where washes overlap; it needs crops of isolated washes.

| medium (n) | edge rise mm | hard-edge share | texture corr. length mm | texture std L* | spectrum slope | paper in marks | orientation coherence | width CV along marks | paper share | mean chroma |
|---|---|---|---|---|---|---|---|---|---|---|
| oil (14) | 1.43 (1.22–2.29) | 0.18 (0.11–0.28) | 0.23 (0.21–0.33) | 6.2 (2.6–7.4) | -1.98 (-2.13 – -1.46) | 0.005 (0.001–0.008) | 0.51 (0.37–0.59) | 0.36 (0.25–0.42) | 0.04 (0.03–0.05) | 15.3 (14.4–16.5) |
| tempera, gold ground (8) | 0.98 (0.74–1.56) | 0.25 (0.23–0.28) | 0.15 (0.11–0.22) | 6.5 (5.8–7.3) | -1.65 (-1.90 – -1.49) | 0.004 (0.001–0.015) | 0.37 (0.35–0.39) | 0.41 (0.31–0.42) | 0.04 (0.04–0.05) | 34.5 (29.4–42.3) |
| watercolour (7) | 0.63 (0.58–0.66) | 0.13 (0.11–0.27) | 0.17 (0.14–0.19) | 4.0 (2.7–4.3) | -2.57 (-2.79 – -2.40) | 0.010 (0.005–0.035) | 0.55 (0.41–0.63) | 0.28 (0.25–0.32) | 0.06 (0.05–0.10) | 14.0 (12.5–20.2) |
| gouache (7) | 0.68 (0.54–1.03) | 0.16 (0.13–0.23) | 0.16 (0.14–0.20) | 4.5 (2.5–5.5) | -2.63 (-2.70 – -2.30) | 0.028 (0.004–0.107) | 0.57 (0.36–0.76) | 0.29 (0.26–0.33) | 0.09 (0.06–0.18) | 13.7 (10.2–16.5) |
| ink, brush (10) | 0.88 (0.75–1.66) | 0.28 (0.16–0.42) | 0.48 (0.30–0.73) | 2.5 (1.8–3.2) | -2.85 (-2.87 – -2.08) | 0.031 (0.007–0.068) | 0.58 (0.50–0.72) | 0.28 (0.26–0.30) | 0.19 (0.17–0.26) | 15.2 (12.9–19.6) |
| charcoal, black chalk (8) | 0.93 (0.72–1.91) | 0.13 (0.08–0.17) | 0.16 (0.14–0.21) | 3.7 (3.2–4.8) | -1.81 (-2.05 – -1.73) | 0.014 (0.002–0.043) | 0.29 (0.24–0.34) | 0.41 (0.35–0.42) | 0.11 (0.08–0.16) | 11.1 (8.3–14.8) |
| graphite (8) | 0.67 (0.51–1.05) | 0.11 (0.10–0.18) | 0.10 (0.09–0.12) | 1.9 (1.4–3.7) | -2.09 (-2.62 – -1.72) | 0.021 (0.001–0.107) | 0.43 (0.36–0.61) | 0.37 (0.36–0.38) | 0.42 (0.18–0.48) | 10.4 (8.3–11.7) |
| pastel (8) | 1.34 (1.03–1.87) | 0.14 (0.10–0.21) | 0.19 (0.15–0.30) | 2.9 (2.5–3.7) | -1.88 (-2.05 – -1.57) | 0.000 (0–0.006) | 0.24 (0.22–0.30) | 0.35 (0.28–0.36) | 0.05 (0.04–0.05) | 11.1 (8.1–18.3) |
| ukiyo-e (8) | 0.63 (0.61–0.74) | 0.24 (0.24–0.28) | 0.19 (0.18–0.20) | 5.8 (4.9–6.3) | -2.41 (-2.50 – -2.17) | 0.022 (0.008–0.040) | 0.55 (0.51–0.59) | 0.32 (0.28–0.35) | 0.07 (0.06–0.08) | 14.3 (12.7–16.2) |

What already separates the media in these numbers: ink and watercolour have the steepest spectra (smooth washes with few fine marks) and oil, tempera, charcoal and pastel the flattest; pastel and charcoal have the lowest orientation coherence (marks in many directions, broken over tooth) and ink the highest; tempera and ukiyo-e have the most hard edges; graphite drawings leave the most paper (0.42). These are the first targets for the gallery sheets.

## Top calibration targets per medium

- **Oil:** (1) replace `kmix` with two-constant KM using `pigments.json` (spectral or ≥ 6 bands) and check against `kmix_check_tints` (target median ΔE2000 < 3, today 12.6); (2) glazes as KM films of 10-40 µm with the glaze K and S; (3) the 4% surface term for sunken versus varnished darks; (4) spectrum slope about -2.0 and orientation coherence about 0.5 at the reference scale.
- **Watercolour:** (1) per-pigment `gran`, `stain`, opacity and darkest value from handprint instead of hue guesses; (2) per-pigment drying shift; (3) edge darkening strong for fine organic pigments, weak for coarse minerals (the particle-size finding), checked with the rim ratio on isolated-wash crops; (4) drying time scale (a 50 µL load: ~40 min to dry at 22 °C, 35% RH) setting `air`/`absorb` per episode.
- **Gouache:** opaque white K/S from the oil whites as a first approximation; flat-field texture std L* about 4.5 and paper share about 0.09 at the reference scale.
- **Ink:** raw-xuan spread of about 0.4-0.5 cm² per µL of water released, by xuan type; stroke-width CV along a stroke about 0.28 and flying-white gap share about 0.03 (up to 0.07); hard-edge share 0.28 (sized supports higher, raw xuan lower).
- **Charcoal:** low orientation coherence (0.29) and gap share 0.01-0.04 (tooth speckle) with spectrum slope about -1.8; measure the darkest L* per tool on hand-chosen crops.
- **Graphite:** hatch coherence 0.43 (0.36-0.61) and spacing from hand-chosen hatched crops; paper share about 0.4; the grade-to-darkness ramp needs its own measurement (not found).
- **Pastel:** coherence 0.24 and near-zero paper inside marks at full resolution (the paper shows between strokes, not inside them); edge rise ~1.3 mm (soft edges).
- **Egg tempera, gold ground:** hard-edge share 0.25 and width CV 0.41; chroma 34 is mostly the gold: measure flesh hatching separately on hand-chosen crops.
- **Woodblock:** hard-edge share 0.24 and flat-field texture std L* about 5.8 (baren and paper); keyline widths from hand-chosen crops.

---

## Sources

Pigments:
- [P1] M. Geldof, A. Proaño Gaibor, F. Ligterink, E. Hendriks, E. Kirchner, "Reconstructing Van Gogh's palette to determine the optical characteristics of his paints", *Heritage Science* 6:17 (2018), https://doi.org/10.1186/s40494-018-0181-6 (methods read). Data: https://github.com/fligt/revigo-spectra (`data/revigo-aggregated-palette-spectral-data.txt`, `data/revigo-mixture-specifications.txt`), CC0 1.0 (downloaded).
- [P2] A. Cosentino, "FORS spectral database of historical pigments in different binders", *e-conservation Journal* 2 (2014) 57-68; data: https://chsopensource.org/new-free-pigments-fors-spectroscopy-database (zip of CSV, downloaded; licence not stated).
- [P3] B. MacEvoy, handprint.com, "guide to watercolor pigments" (rev. 7 Jan 2015), https://www.handprint.com/HP/WCL/waterfs.html and the colour pages waterc/r/o/e/y/g/b/v/w.html (downloaded and parsed; the ratings key is quoted in `pigments.json`).
- [P4] C. J. Curtis, S. E. Anderson, J. E. Seims, K. W. Fleischer, D. H. Salesin, "Computer-Generated Watercolor", SIGGRAPH 1997, https://doi.org/10.1145/258734.258896 ; https://grail.cs.washington.edu/projects/watercolor/paper_tiny.pdf (read).
- [P5] Y. Okumura, "Developing a Spectral and Colorimetric Database of Artist Paint Materials", MS thesis, RIT, 2005, https://repository.rit.edu/theses/8126/ (record read: "This paper has been withdrawn").
- [P6] Š. Sochorová, O. Jamriška, "Practical Pigment Mixing for Digital Painting", *ACM TOG* 40(6), 2021 (see MEDIA.md [S3]); https://github.com/scrtwpns/mixbox (README read).

Oil and varnish:
- [V1] AIC Wiki, "Varnishes and Surface Coatings: Low Molecular Weight Varnishes", https://www.conservation-wiki.com/wiki/IV._Low_Molecular_Weight_Varnishes (read; refractive indices cite de la Rie & McGlinchey 1990 and de la Rie 1990).
- [V2] L. Mayer, G. Myers, "American Impressionism, Matteness, and Varnishing", *JAIC* 43(3) (2004) 237-254, https://cool.culturalheritage.org/jaic/articles/jaic43-03-003_4.html (read).
- [V3] R. S. Berns, E. R. de la Rie, "The Effect of the Refractive Index of a Varnish on the Appearance of Oil Paintings", *Studies in Conservation* 48 (2003) (catalogue record only: https://katalog.snk.sk/vufind/Record/3366503/Description) [not verified].
- [O1] "Analytical imaging studies of the migration of degraded orpiment, realgar, and emerald green pigments in historic paintings and related conservation issues", *Heritage Science* (2016), Table 1, https://doi.org/10.1186/s40494-016-0078-1 (table read; authors not checked).
- [O2] W. S. Elkhuizen et al., "Comparison of three 3D scanning techniques for paintings, as applied to Vermeer's 'Girl with a Pearl Earring'", *Heritage Science* 7:89 (2019), https://doi.org/10.1186/s40494-019-0331-5 (read in part).
- [O3] A. Dal Fovo et al., "Reflectance Spectroscopy as a Novel Tool for Thickness Measurements of Paint Layers", *Molecules* 28 (2023) 4683, https://doi.org/10.3390/molecules28124683 (read).

Watercolour and paper:
- [W1] J. González-Gutiérrez, O. Moctezuma, V. Angeles, M. Rios-Ramirez, S. Zetina, A. Marin, R. Zenit, "Pattern formation by droplet evaporation and imbibition in watercolor paintings", arXiv:1909.09098 (2019), https://arxiv.org/abs/1909.09098 (PDF downloaded and read: methods, Table I, results).
- [W2] Y. J. Lee, Y. C. Ko, B. G. Moon, H. J. Kim, "Paper analysis by profilometry", *BioResources* 18(2) (2023) 3978-3994, https://doi.org/10.15376/biores.18.2.3978-3994 (read).
- [W3] J. Chopra, A. Yadav, "Conservation and Paper Roughness of Art Artifacts", WPI Interactive Qualifying Project (2008), https://digitalwpi.wpi.edu/downloads/8336h2246 (read; no Ra values).

Ink:
- [I1] S. Wu, X. Wu, P. K. Chu, "Ink Dispersion on Qianlong Xuan Paper with Improved Ink Expression", *Journal of Materials Science & Technology* 32(2) (2016) 182-188, https://www.jmst.org/article/2016/1005-0302/1005-0302-32-2-182.html (read).
- [I2] N. S.-H. Chu, C.-L. Tai, "An Efficient Brush Model for Physically-Based 3D Painting", Pacific Graphics 2002, https://cse.hkust.edu.hk/VCB/PG02.pdf (read: no measured brush data).
- [I3] S. Xu et al., virtual brush model, *Science in China Ser. F* 48(3) (2005) 285-303, https://i.cs.hku.hk/~fcmlau/papers/brush-sic.pdf (read: no measured brush data).

Dry media:
- [D1] M. C. Sousa, J. W. Buchanan, "Observational Model of Blenders and Erasers in Computer-Generated Pencil Rendering", Graphics Interface 1999, https://graphicsinterface.org/wp-content/uploads/gi1999-21.pdf (read).
- [D2] J. Paul Getty Museum, "Noir: Technical Examination and Analysis of 19th-century Black Drawing Materials", https://www.getty.edu/projects/noir/ (read; no numbers on the page).

Reference images: The Met Collection API, https://collectionapi.metmuseum.org/public/collection/v1/objects/{id} (records and images CC0); the object list is `studio/calibration_refs.json`.
