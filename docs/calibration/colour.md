# Calibration report: colour mixing (`studio/v8/media/spectral.py`, adopted by `studio/v8/media/oil.py`)

Nov 25, 2026. Target from `docs/media-data.md` ("Finding: the engine's `kmix` against measured tints" and "Top calibration targets per medium", oil 1 and 2): replace `kmix` with a measured two-constant Kubelka-Munk model and bring the median ΔE2000 on `pigments.json` `kmix_check_tints` under 3, with a held-out check. The short version is in the oil manual page (`docs/manual/oil.md`, "Calibration"); the chart is `docs/gallery/mixing_chart.jpg`.

## Summary

| | Before (`base.kmix`) | After (`spectral.mix`) | Data |
|---|---|---|---|
| 29 measured tints with zinc white, the engine's RGB path (masstone RGB in, mixed RGB out), median / max ΔE2000 | 12.6 / 38.0 | **1.8** / 44.2 (eosine lakes); 1.5 / 4.4 without the three eosine lakes (n = 23) | Revigo [P1] |
| same, held out: K and S refitted without the predicted tint (spectral model alone, leave one tint out) | | **2.7** / 11.9; 2.1 / 5.6 without eosine | |
| same, held out, whole engine path (refit without the light or without the strong tints, unmixing table rebuilt) | | 3.4 / 36.5; in-palette paints 3.2; without eosine 2.4 | |
| 19 mixtures of a paint with 1-11% bone black (never used in any fit) | 10.7 / 32.1 | 5.4 / 27.8 (spectral model alone 5.2 / 20.9) | Revigo |
| 4 tints of ~10% paint in lead white (lead white fitted only on its mixtures with black) | 14.7 / 16.6 | 7.8 / 9.6 (spectral model alone **3.0** / 4.0); since Nov 26 with a lead-white palette **2.9** / 3.9 | Revigo |
| 10 tints of earths in titanium white, 1:4 and 1:9 by volume (Nov 26; section 5) | 12.8 / 19.6 | **1.0** / 3.6 through a titanium-white palette (spectral model, each tint held out: 0.4 / 0.5) | LBNL [P7] |
| speed, `match` 300 strokes of 40-70 px on 1200 × 1600 (CPU s) | 15 | 25 | |
| speed, `match` 400 strokes of 14-24 px (CPU s) | 9-10 | 14 | |
| speed, full-canvas glaze (CPU s) | 1.0 | 3.1 | |

ΔE2000 is computed against the measured colour of each film over the white of the chart (specular excluded), as `pigments.json` does; my CIEDE2000 reproduces its numbers (kmix 12.57 here, 12.6 there; the in-sample spectral fit 1.36, 1.3 there). Run it with `cd studio/v8 && TEODOR_PIGMENT_DATA=<folder with revigo/repo/data> python3 -m media.spectral validate [--json out.json]` (without the raw spectra only the first block runs). Speeds were measured on a shared 2-vCPU machine under heavy load from other jobs: CPU seconds, not wall time; on an idle machine the big `match` takes about 25 s.

## 1. The model

- **Palette.** 13 measured oil paints from Revigo (Geldof et al. 2018, CC0): zinc white, bone black, red lead, vermilion, eosine lake, cochineal lake, chrome yellow, lemon chrome yellow, emerald green, viridian, Prussian blue, cobalt blue, synthetic ultramarine. K and S per wavelength (400-700 nm, 10 nm) per 100 µm film, as `tools/pigments/build_pigments.py` fitted them into `studio/pigments.json` (a copy is embedded in `spectral.py` for work dirs without the file). The two other eosine variants, lead white and the extenders are left out: one paint per pigment, and lead white's constants in `pigments.json` come from its masstone film alone (no tints), so its scattering is undetermined there.
- **Mixing** is Duncan's rule (K and S of a mixture are the weight-fraction sums), the same rule the constants were fitted with. Forward: R∞ per band (in the stable form 1/(1 + q + √(q² + 2q)), q = K/S, since transparent lakes have S near 1e-4), the Saunderson surface with the paper's k1 = 0.04, k2 = 0.49 and the specular part excluded, CIE 1931 2° observer, D65, sRGB.
- **RGB interface (Mixbox-like).** A colour is unmixed into palette concentrations with a 49³ lookup table over the sRGB cube (built in about 2 s, cached in `~/.cache/teodor/`), interpolated trilinearly; the part the palette does not explain is kept as an RGB residual. Concentrations and residuals mix linearly; mix(a, a, t) = a and mix(a, b, 0) = a hold to 1e-7. Each node holds the cheapest of about 160 000 sampled mixtures (any two paints; one or two chromatic paints with white and black, on logit-spaced fractions because tinting strengths span three orders of magnitude): cost = CIELAB distance + 2.5 per chromatic paint, 1.0 for black, 0.5 for white. This sparsity prior is a judgement: it makes a colour that one paint matches that paint, and a grey white and black (zinc white and bone black give a slightly cool grey, b* −6.7 at L* 54, so neutral greys take a trace of chrome yellow).
- **Engine bands.** The engine evaluates every other band (16 bands, 20 nm) with the colour-matching weights renormalised to the same white: against all 31 bands, random palette mixtures differ by ΔE2000 0.18 (median), 0.85 (95th percentile), 9 at worst (a few saturated mixtures). It costs 0.05 in the tint median (1.75 → 1.80). The validation's spectral reference uses all 31.
- **Films.** `film_over`/`glaze` lay a film over a substrate per band with the hyperbolic Kubelka-Munk solution (R and T of the film, then R + T²R₀/(1 − R R₀)) in internal reflectance, the surface counted once on top; the substrate is the unmixed canvas colour, its residual passes through the film's luminance transmittance. Thickness is in units of the 100 µm drawdown.

## 2. How it is used in oil

- **Brush strokes into wet paint** mix in pigment space (`spectral.mix_window`, which replaces `kmix` in the bristle deposit, smudge, rag, scraper and scraping knife). The canvas keeps the pigment state of the paint laid on it while a command runs (`CanvasLatent`: concentrations and residual per pixel, checked against `cv.col` pixel by pixel, so anything else that changes the colour forces a fresh unmixing); it is not saved with the canvas, so the next command unmixes from RGB again.
- **Brush strokes over dry paint or the ground** (wetness below 0.15, the engine's touch-dry threshold) are no longer mixed with what is beneath: the paint lies on top as a film of t × 50 µm (`BODY_FILM = 0.5`, within the 10-80 µm of single layers in the cross-section [O1]; the exact value is a judgement). Opaque paint (chrome yellow, vermilion) covers in one pass; a transparent one (ultramarine, the lakes) stains. This was needed: with pure pigment mixing, a chrome-yellow stroke over a dry dark (mixed from black, vermilion and a little Prussian blue) turned green, because 1% of Prussian blue is strong (measured) and a dry layer does not mix into wet paint.
- **Glaze** (`glaze` intention and `finish glaze`): the colour is read as what the glaze shows over white at opacity 1 (`spectral.glaze_paint`): darker and saturated colours become transparent paints thinned with clear oil (K = S = 0; white costs an extra 4 ΔE in the choice, so a transparent paint is preferred), colours lighter than L* 70 carry white and act as a veil; then the film is laid at thickness `opacity` × 30 µm (`GLAZE_FILM = 0.3`: glaze layers of 10-50 µm and a translucent layer of 30-40 µm in the cross-section [O1]). Both thresholds are judgements. Over wet paint the glaze's pigments (not its oil) partly mix in. Results in sRGB for `opacity` 0.25 / 1 (before → after):

| glaze colour | over white | over a dark (#1a1a22) | the paint found |
|---|---|---|---|
| #5a1020 (crimson) | #a95d6f → #b4737e, #3f0710 → #560f1d | #150b12 → #170d13 | cochineal lake + a little black, 92% oil |
| #2e5ab0 (blue) | #88a5c3 → #9ab2d2, #1b3e89 → #1e61b2 | #101522 → #111522 | ultramarine, 92% oil |
| #203050 (navy) | #788696 → #838e9c, #111c33 → #192c44 | #0e111a → #0d101a | ultramarine and black, 88% oil |
| #b03a2e (red) | #d48f7d → #e1907d | #1c1215 → #3f2b28 | vermilion, 82% oil: vermilion is opaque, so it lightens a dark a little (physically right; the old model could not) |
| #e8d8b0 (light veil) | #e8ddc3 → #ece4c8 | #3c3a38 → #737f8f | zinc white: a veil, lightens and cools darks more than before (zinc white's measured scattering) |

## 3. Validation in detail

**Tints with zinc white, engine path** (masstone sRGB of the paint and of zinc white in, `spectral.mix` out; `pigment_fraction_by_weight` as t), ΔE2000 kmix → spectral: red lead 28.2 → 0.8 (9%), 11.6 → 1.2 (51%); vermilion 10.5 → 0.7, 6.6 → 0.2; cochineal 13.3 → 1.4, 11.3 → 1.6, 13.5 → 1.5 (0.8%); chrome yellow 13.4 → 1.9, 7.5 → 4.4; lemon chrome 3.5 → 3.2, 3.9 → 0.9; emerald 9.1 → 1.0, 6.2 → 1.0; viridian 2.3 → 1.2, 9.1 → 4.0; ultramarine 16.9 → 1.7, 8.5 → 2.9; cobalt 12.6 → 0.4, 5.9 → 2.2; Prussian blue 31.8 → 3.3 (6.3%), 20.8 → 2.8, 1.6 → 1.8 (99%), 38.0 → 1.4 (1.1%); eosine lakes 15-33 → 7.4-42.

Where the RGB path loses against the spectral model itself: (1) small amounts of white or black that the trilinear interpolation adds to a masstone (viridian 4.0 vs 0.5 in the model, chrome yellow 4.4 vs 1.4); (2) **dark masstones are ambiguous in RGB**. Eosine lake's masstone (L* 14, a dull red-brown) is matched equally well by vermilion and black, and its tints are extraordinarily light and pink (50% in white: L* 65, a* 52); the two eosine variants not in the palette (with wax, on lead) are unmixed as other paints and miss by 12-42. Prussian blue's masstone has L* 0.7, indistinguishable from black: the main palette gets it right, but in the held-out fold whose refit masstone came out a shade different, it was unmixed as black and cochineal, and its light tints missed by 29-31. A colour cannot say which paint it is when several paints share it; only a named paint could (see "What remains").

**Held-out checks.**
- Leave one tint out (spectral model; each paint's K and S refitted from its masstone film and its other tints, `_fit` = `build_pigments.fit_joint`): median 2.68, max 11.9 (eosine); without eosine 2.10, max 5.6 (n = 23). Most paints have only two tints, so each prediction rests on the masstone and one tint.
- The whole engine path held out (two folds: all light tints, c < 0.3, held out, then all strong ones; every paint refitted without them, the unmixing table rebuilt): median 3.38 (n = 29), 3.17 for paints in the palette (n = 25), 2.44 without eosine (n = 23). The difference to the spectral model is the near-black ambiguity above (Prussian blue 13B, 13G).
- Mixtures with bone black (19; codes D, E): median 5.4 engine, 5.2 spectral model, 10.7 kmix. These are dark colours (L* 0.3-71, median 29), where ΔE2000 is large for small reflectance errors, and a 1% of black is a strong test of black's tinting strength (bone black was fitted only on its tints with zinc white). Worst: eosine on lead + 1% black (14-28), lemon chrome + 10% black (9.3), emerald + 1% black (9-11).
- Tints in lead white (4; lead white's own K and S fitted here on its film and its two mixtures with black, the paints' on their zinc-white tints): the spectral model predicts them at 3.0 median (max 4.0), so the model carries over to another white. The engine path gets 7.8 because RGB cannot tell lead white (slightly brighter) from zinc white: it unmixes lead white as zinc white, whose scattering is weaker, so tints come out too strong.

## 4. What remains uncalibrated, and why

- **The sparsity prior** (2.5 / 1.0 / 0.5 ΔE per paint), the glaze choices (white +4 ΔE below L* 70, veil above), `BODY_FILM` 50 µm per full deposit, `GLAZE_FILM` 30 µm per unit of opacity, and the 0.15 wetness threshold between mixing and layering are judgements; the thicknesses are set within the measured range of layer thicknesses [O1] but not fitted to anything.
- **Earth pigments** (added Nov 26, section 5): raw and burnt sienna and raw umber are measured (as acrylics); yellow and red ochre are stood in for by synthetic iron oxides; burnt umber and terre verte are approximations. Their strength relative to the Revigo paints rests on one cross-dataset factor (uncertain by about ×/÷2.7).
- **One white per palette** (Nov 26, section 5): zinc white by default; lead white and titanium white are in the palette but used only when chosen, because RGB cannot tell the whites apart.
- **Medium (oil) is clear** (K = S = 0) in glazes; real linseed oil yellows and absorbs a little in the blue. Not measured here.
- **Mixed paint does not persist** between commands: the canvas file stores RGB, so the next command re-unmixes from RGB (a mixture of white and 2% Prussian blue becomes whatever the table says that colour is). Saving the concentrations (13 more channels per pixel) would keep the paint's identity across commands; I did not add it to keep the canvas files small.
- **Other media** still use `base.kmix`. Switching it to spectral mixing is planned; section 5 lists what that needs.

## 5. Lead white, titanium white and the earths (Nov 26, 2026)

`pigments.json` gained K and S for lead white, titanium white and seven earths, and the spectral palette went from 13 to 22 paints. Built by `tools/pigments/build_pigments.py` (+ `tools/pigments/lbnl_charts.py`); checked by `python3 -m media.spectral validate`.

**Lead white** (Revigo 08A). Its 100 µm film nearly hides, so the film alone leaves its scattering undetermined. Its two mixtures with bone black (08B: 0.9%, 08C: 10.2%) fix it against black's measured absorption (Duncan, weight fractions; rms 0.020 in internal reflectance). Lead white scatters about half as much as the Revigo zinc white per film (S 5.6 against 11 at 460 nm). Its four tints (~10% cochineal, viridian, cobalt blue or chrome yellow in lead white; never used in a fit) are predicted at a median ΔE2000 of 3.0 by the model and **2.9** through the engine with a lead-white palette (before: 7.8, when the engine could only read lead white as zinc white).

**Earths and titanium white: where the data came from.** No open dataset of K and S, or of masstone and tints, for earth pigments in oil was found (searched: Zenodo, the RIT/Golden acrylic dataset [P8], the Munch Aula oil libraries, IFAC FORS, Centore, the Abed thesis; see `docs/media-data.md`, "Pigments"). The usable source is the LBNL Pigment Database [P7]: artists' acrylics (Liquitex) as 15-30 µm films measured over a void, white and black, with K and S per film, masstones and 1:4 and 1:9 tints in titanium white (W03). Its numeric files are encrypted for the project's partners, so `lbnl_charts.py` reads K and S out of the public charts, which are vector drawings (each curve a 441-point polyline; values exact to the plotted precision, about 0.3%).

| palette name | measured paint | status |
|---|---|---|
| titanium white | LBNL W03, Liquitex titanium white (PW6) | measured (acrylic) |
| raw sienna | LBNL B14 (PBr7) | measured (acrylic) |
| burnt sienna | LBNL B13 (PBr7) | measured (acrylic) |
| raw umber | LBNL B15 (PBr7) | measured (acrylic) |
| yellow ochre | LBNL Y01, synthetic yellow iron oxide (PY42) | proxy: the ochre's chromophore without its clay; its masstone differs from the FORS natural yellow ochre by ΔE2000 14.6 |
| red ochre | LBNL R04, synthetic red iron oxide (PR101) | proxy, as above; ΔE2000 15.4 from the FORS red ochre |
| burnt umber | FORS linseed-oil masstone, scattering of raw umber | **approximation (tuned)**: the same FORS normalisation misses LBNL's measured raw umber, raw and burnt sienna by ΔE2000 10.8, 8.1 and 20.7 |
| terre verte | FORS linseed-oil masstone, scattering of raw sienna | **approximation (tuned)**, as above |

- **Fit.** Each earth's K and S are fitted by the masstone-tint method: per wavelength, Duncan mixtures by volume with W03 reproduce the R∞ of the masstone film and of both tints (rms 0.0002-0.0034). Duncan from the masstone film's own charted K and S alone misses the tints by 2.0-9.1; the fitted constants are 0.9× (raw sienna) to 2.2× (red iron oxide) the masstone film's, mostly larger: those paints tint more strongly in white than their masstone films imply.
- **Units.** Revigo's constants are per film of its 100 µm drawdown (hand-ground oil), LBNL's per mm of dry acrylic. One factor converts them: 0.398 mm per Revigo film, the geometric mean of K_revigo/K_lbnl over the four pigments both measured (cobalt blue 0.29, Prussian blue 1.97, ultramarine 0.13, bone black 0.34). The spread (×/÷2.7) is the honest uncertainty of every earth's and titanium white's strength against the Revigo paints. Against titanium white the earths' strength is measured. At this factor titanium white scatters about 20-40× more per film than the Revigo zinc white.
- **One white per palette.** The three whites differ by only 1-5 L* in RGB, but by 20-40× in scattering. With all three in the unmixing table, near-white colours were read as titanium white, and zinc-white tints missed by a median of **18.6** instead of 1.8. Now the palette has one white (`spectral.DEFAULT_WHITE`, zinc white unless `TEODOR_OIL_WHITE` says `lead white` or `titanium white`, or `Palette(white=...)`): the unmixing table and the glazes use only that white. A style could choose lead white (before about 1850) or titanium white (after about 1920); nothing in the studio does that yet (a judgement left to whoever wires styles to palettes).
- **Results** (median / max ΔE2000, before → after):
  - 29 tints with zinc white, engine path: 1.80 / 44.2 → 1.80 / 45.6. Without eosine: 1.58 → 1.69 (viridian 1.0 → 1.7 and 3.8 → 4.2; the eosine variants not in the palette 0.7-2.3 worse).
  - The same, held out (engine path): 3.38 → 3.45.
  - 19 bone-black mixtures: 5.13 → 5.13.
  - 4 lead-white tints: 7.77 → 2.86.
  - 10 earth tints in titanium white: kmix 12.8 → **0.95** (max 3.55, red iron oxide). That number is through the engine, but the earths' constants were fitted on these same tints, so it is not a prediction. The spectral model with each tint held out gets 0.40 (max 0.50); with two tints per paint, that check is weak.
- **How colours unmix now.** With zinc white, a mid brown (#6b4a2b) is no longer lemon chrome yellow, vermilion, cochineal and black: it becomes mostly terre verte with eosine lake and a little raw sienna, because the approximated terre verte's masstone is a dull olive. An ochre (#c8962e) is yellow ochre in white; a brick red (#9c4a32) is red lead with some burnt sienna. The approximated paints can take over browns and olives; that is the largest risk of this change.
- **Cost.** `spectral.mix` is 1.4× the CPU time per pixel (22 paints instead of 13). The unmixing table took 8 s to build on a heavily loaded machine (section 1: about 2 s before; built once, then cached).

**What switching `base.kmix` to spectral mixing (gouache, pastel, tempera) would need.**
1. **A windowed path.** Those media call `kmix` per dab on small windows. `spectral.mix` costs about 25× `kmix` per pixel (now 1.4× more), so they need oil's `mix_window` (mixing only where the dab's amount exceeds a threshold, with the canvas's pigment state cached in a `CanvasLatent`), or a cheaper three-paint-at-a-time path.
2. **A white per medium.** Gouache and tempera whites are not oil whites. Gouache uses zinc or titanium white with chalk or blanc fixe and gum arabic; egg tempera historically uses lead white. The binder changes S (refractive index: gum arabic and egg are lower than oil, so they scatter more and look paler and more opaque), so the oil constants are only a first approximation. Each medium should pick its palette white (`Palette(white=...)`) and, ideally, scale S for its binder. FORS [P2] has the same pigments in gum arabic, egg tempera and oil, which bounds that shift for masstones.
3. **Pastel** is not a mixture in a binder but juxtaposed or rubbed particles: its "mixing" on paper is partly optical (side by side) and partly physical (rubbed). Spectral Kubelka-Munk fits the rubbed part; a pastel stroke over another should rather be the film path (`film_over`), as oil does over dry paint.
4. **Validation per medium.** No tint data for gouache or tempera was found. handprint's watercolour ratings (opacity, value range) are the nearest check.

