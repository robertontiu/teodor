# Graphite hyperrealism: sky (layer 2)

How graphite hyperrealism renders the sky, written as a departure from layer 1 (`docs/subjects/sky.md`), with a clear afternoon sky in mind as a filtered black-and-white photograph renders it: darker at the zenith, with thin cirrus. Style research: `docs/styles/graphite-hyperrealism.md`; engine data: `docs/calibration/graphite-hyperrealism.md`.

Researched 2026-11-26. **judgement** marks editorial calls; **derived** marks arithmetic from sourced values; **flag** marks a disagreement between brief, research and medium.

## 1. Rulers
No hyperrealist drawing is named or measured (in copyright; style doc, section 1). The rulers are the photographic ones (`studio/targets.parts/graphite-hyperrealism.json`: key L* 50, p5–p95 L* 17–82), photographers' sources on how colour filters render a blue sky in black and white, graphite technique sources on smooth skies, and the engine's measured smoothness and darks (calibration).

## 2. The twist in one paragraph
Layer 1's sky is a colour field with two gradients, toward the horizon and away from the Sun, carried by at least four mixtures. A black-and-white photograph keeps both gradients but turns hue into value, and a colour filter decides how far: yellow "darkens the sky slightly", orange records blue skies "in very dark tones", red "as black" ([Ilford, colour filters](https://ilfordphoto.com/colour-filters)); a red filter will "turn a blue sky almost black" and "make clouds really stand out" ([Photography Mad](https://photographymad.com/pages/view/using-coloured-filters-in-black-and-white-photography)). Because haze near the horizon is whitish and the deep blue lies high and away from the Sun (layer 1), the filter steepens the vertical gradient: the zenith falls much more than the horizon (**judgement**, from the filters' action on blue). Graphite hyperrealism then has to lay that gradient as one seamless, grainless tone the width of the sheet, the hardest smooth passage in the style.

## 3. Departures from layer 1

**Value (pushed by the filter, capped by graphite):**
- **The gradient:** darkest at the top of the frame, lightest just above the horizon; across the frame, darker on the side away from the Sun (layer 1's two gradients, in value only). For a late-afternoon sky with the Sun behind the camera, the part of the sky in frame is 90°–150° from the Sun, near the darkest region (layer 1: the darkest blue lies about 65° from the Sun at other times than sunrise and sunset; **judgement** for the exact placement).
- **Suggested values (judgement):** horizon band L* 70–80; at the Moon's height (about 20–30° up) L* 45–55; top of the frame L* 35–45. With an orange filter in mind rather than a deep red one.
- **Flag: "almost black" is out of graphite's reach over a large area.** Blended graphite stops near L* 42 as an area and shines past Munsell value 4 (calibration; [Vitruvian Studio](https://vitruvianstudio.com/blog/3-ways-to-reduce-graphite-shine-in-your-drawings/)); carbon pencil reaches about L* 32. A red-filter sky near black across the top of a 48 × 64 cm sheet would be a large field of carbon, mottled and shiny. Research decides: draw an orange-filter sky (top L* 35–45: carbon blended over a graphite base, as the style's darks recipe), and say so in the journal.
- **Smaller dynamic range than the photographic ruler:** the sky spans about L* 35–80, inside the photographs' p5–p95 of 17–82; the deepest darks of the picture belong to contact shadows, not to the sky (`--light-shadow.md`; **judgement**).

**Texture (removed):**
- A clear sky in a photograph has no texture. The calibration's rendered reference shows smooth out-of-focus passages at grain 0.00 L*; blended graphite reaches grain 0.24–0.40 L* and 0.5–5 mm mottle 0.19 on vellum, 0.20 / 0.09 on plate (calibration, flat tone). The sky is where that residue shows most (**judgement**). Mottle, not grain, is the risk: a 1–2 L* blotch across 2 cm of sky reads as a stain.
- **No banding:** the gradient must be monotonic from top to bottom. The calibration's ramp test still left a residual of 0.44 L* (max 2.0) after blending with feathered bands; over a sky's height that is visible as faint steps (calibration, limit 1).

**Cirrus (kept, simplified):**
- Cirrus: "white, delicate filaments ... a fibrous (hair-like) appearance, or a silky sheen" (WMO, in layer 1). Thin and translucent, so in a filtered photograph they are a few to about 15 L* above the sky behind them, brightest where densest; the filter makes them "stand out" by darkening the sky, not by whitening them (Photography Mad; **judgement** for the value).
- All filaments follow one wind and recede toward the horizon, shorter and more crowded lower down (layer 1).
- They are at infinity, so at f/16 they are as sharp as the Moon; their softness is their own (fibrous, feathered), not blur (`--space.md`).

## 4. Edges and marks
- **The sky has no edges.** The only edges in it are the cirrus's soft fibres, the Moon's limb and the silhouettes against it (the hand, the grass). An edge anywhere else in the sky is a fault (**judgement**).
- **Technique, from graphite sky tutorials:** lay the sky with pressure falling toward the horizon, a second layer perpendicular to the first, loose graphite rubbed in with a cotton swab, blended with a tortillon, smoothed with a folded paper towel, then a final blend with a soft brush; lift lights with a kneaded eraser and a white eraser, "some edges sharp and others soft"; and "draw the sky darker than it looks in real life" ([Empty Easel, luminous clouds in graphite](https://emptyeasel.com/?p=23357)). Powder brushed on as a base layer ([Creative Bloq](https://www.creativebloq.com/how-to/get-more-from-graphite-with-these-tips), style doc); many light layers, not one heavy pass (Vitruvian Studio); blend in stages, and don't overblend into a plastic surface ([Wildlife Art Store, blending tools](https://www.wildlifeartstore.com/drawing-tools-for-blending-pencil/)).
- **Cirrus are lifted, not drawn:** pull them out of the finished sky tone with a `kneaded` eraser in strokes along the wind, then a few brightest fibres with the battery eraser at its smallest (a line "as thin as human hair": [Wildlife Art Store, white lines](https://www.wildlifeartstore.com/white-lines-in-a-pencil-drawing/)), then soften the fibres' edges with a light brush pass (**judgement** for the order).
- **No stylus in the sky:** an indented groove is a crisp pure-white line ([Sibley, indenting](https://sibleyfineart.com/_blog/?p=780)); cirrus are soft and only a little lighter than the sky, so a groove would read as a scratch (**judgement**).

## 5. What stays true to life
- Both gradients and their direction relative to the Sun (layer 1).
- Cirrus at its WMO height, one wind, perspective toward the horizon.
- The Moon's disc darker on the unlit side only as dark as the sky (`--moon.md`).
- The sky darker than the sunlit hand and lighter than the hand's contact shadows (`--light-shadow.md`).

## 6. Checks for Teodor
1. A vertical profile of the sky (column means after a 1 mm blur) falls monotonically from about L* 75 at the horizon to about L* 40 at the top; no step over 0.5 L* per mm.
2. Across the frame the side away from the Sun is the darker one.
3. Mottle over 0.5–5 mm in clear sky at or below the photographic reference's (calibration measure); no blotches, no hatching visible at 1:1.
4. Cirrus 5–15 L* above the sky around them, fibrous, aligned with one wind; no hard white scratches.
5. The top of the sky is drawn in carbon over graphite without visible shine (`look` under the raking-light sheen render).

## 7. Engine notes
- Lay the sky first, before the hand and grass (it passes behind them), as one `glaze` base at the horizon value, then feathered `hatch` bands darkest first: `carbon_pencil` for the top band, then 8B, `mech_05` 4B, 2B, HB (the calibration recipe), each band `clip`ped to the sky region (a `segment` region with the Moon as a hole; `--moon.md`).
- Blend with the largest `brush` at three angles across the whole sky, repeated (the calibration's second sitting brought wall mottle from 0.25 to 0.07); `chamois` once for the broad field if mottle stays (it lifts a little: re-check the top value).
- Cirrus: `kneaded` with `"seek": true` toward the cirrus values in the schema, then `electric_eraser` at size 2–3 px for a few fibres, then one light `brush` pass.
- Expect the vertical residual of about 0.4 L* after blending (calibration); a final very light long `brush` pass along the gradient helps (**judgement**).

## 8. Sources
1. Ilford Photo, [Using colour filters for black and white photography](https://ilfordphoto.com/colour-filters)
2. Photography Mad, [Using coloured filters in black and white photography](https://photographymad.com/pages/view/using-coloured-filters-in-black-and-white-photography)
3. Empty Easel, [How to draw perfect, luminous clouds with graphite pencils](https://emptyeasel.com/?p=23357)
4. Vitruvian Studio, [3 ways to reduce graphite shine](https://vitruvianstudio.com/blog/3-ways-to-reduce-graphite-shine-in-your-drawings/); Creative Bloq, [Get more from graphite](https://www.creativebloq.com/how-to/get-more-from-graphite-with-these-tips); Wildlife Art Store, [blending tools](https://www.wildlifeartstore.com/drawing-tools-for-blending-pencil/), [white lines](https://www.wildlifeartstore.com/white-lines-in-a-pencil-drawing/); Sibley Fine Art, [indenting explained](https://sibleyfineart.com/_blog/?p=780)
5. Layer 1 `docs/subjects/sky.md` (Gurney's gradients, WMO cirrus); style doc; calibration note (darks, smoothness, ramp residual); `studio/targets.parts/graphite-hyperrealism.json`
- **Judgement calls:** filter steepening the vertical gradient, the value targets, cirrus values, no edges in the sky, cirrus by lifting, no stylus, engine mapping. **Flag:** a red-filter near-black sky is beyond graphite over a large area; draw an orange-filter sky.
