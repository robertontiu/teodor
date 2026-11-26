# Graphite hyperrealism: light and shadow (layer 2)

How graphite hyperrealism renders light on form, written as a departure from layer 1 (`docs/subjects/light-shadow.md`), with one low late-afternoon sun in mind, soft penumbras, and skylight in the shadows. Style research: `docs/styles/graphite-hyperrealism.md`; engine data: `docs/calibration/graphite-hyperrealism.md`.

Researched 2026-11-26. **judgement** marks editorial calls; **derived** marks arithmetic from sourced values; **flag** marks a disagreement between brief and research.

## 1. Rulers
No hyperrealist drawing is named or measured (in copyright; style doc, section 1). The rulers are the measured black-and-white photographs (`studio/targets.parts/graphite-hyperrealism.json`: key L* 50 ± 12, spread 21 ± 5, p5–p95 L* 17–82, 29% darks, 32% lights, hard-edge share 0.17), photographic exposure sources for the sun-to-shade ratio and filter effects, and the calibration's measured values for what graphite and carbon reach.

## 2. The twist in one paragraph
Layer 1 gives the painter two families, a core, reflected light, occlusion, and coloured light and shadow. Graphite hyperrealism keeps the whole structure, because the camera records it, but moves it in three ways. **Colour becomes value through the film and filter**, so the "complementary" blue shadow of layer 1 becomes a *darker* shadow once a yellow-to-red filter removes the blue skylight that fills it. **The range is the photograph's**, much wider and darker than the academic graphite tradition (photographs p5 L* 17 against L* 60 in finished 19th-century graphite drawings: style doc, section 5). **Edges are the optics'**: penumbras exactly as wide as the sun's 0.5° makes them, terminators as soft as the form's curvature, and both blurred further outside the zone of focus. "Subjects aren't separated by harsh lines, but rather, changes in value" ([Skillshare, the real art of photorealistic drawing](https://www.skillshare.com/en/blog/the-real-art-of-photorealistic-drawing/)).

## 3. Departures from layer 1

**The sun-to-shadow ratio (kept as measured, then pushed by the filter):**
- In full sun the "sunny 16" table gives f/16 for sunlit subjects and f/4 for "open shade": four stops, 16 times (Wikipedia, [Sunny 16 rule](https://en.wikipedia.org/wiki/Sunny_16_rule)). A low late-afternoon sun is weaker relative to the sky, so the ratio is smaller, about 2–3 stops (**judgement**).
- **Filter:** the shadow is lit mainly by blue skylight (layer 1, Gurney); a yellow, orange or red filter darkens blue ([Ilford](https://ilfordphoto.com/colour-filters)) and keeps warm sunlit skin light (yellow gives "warm, natural, pleasing flesh tones", orange "a healthy, smooth look": [Photography Mad](https://photographymad.com/pages/view/using-coloured-filters-in-black-and-white-photography)). So the filtered photograph separates sun and shadow by about one stop more than the eye sees (**derived** from the two effects; amount **judgement**).
- **Suggested values on the hand (judgement, within the photographic ruler):** lit planes L* 75–88; halftones L* 55–70; shadow family L* 30–45 with reflected light at its top; core along the terminator L* 25–32; occlusion and contact accents L* 18–28 (carbon; graphite stops near L* 32–42: calibration). Spread over the hand about 20 L*, near the ruler's 21.
- **The light family's top is not paper white:** "even highlighted areas ... aren't pure white" (Skillshare above); reserve the paper (L* 96) for nothing but true speculars, if any (**judgement**). The hand's lit planes may still be the lightest large shape, at or above the Moon (`--moon.md` flag).

**Penumbras (kept exact, scaled by the lens):**
- Layer 1: the penumbra is about 1/110 of the distance from the casting edge to the receiving surface. A finger's shadow on the palm 1–3 cm away has a 0.1–0.3 mm penumbra; at the hand's 0.83 life size on the sheet (`--space.md`) that is 0.08–0.25 mm, under 1.5 px: **cast shadows on the hand are crisp** at the contact and only slightly softer farther along (**derived**).
- **Flag: "soft penumbras".** On the hand, a low sun's penumbras are sharp; soft cast shadows need 1 m or more between the casting edge and the receiver (a 1 cm penumbra at 1.1 m), or come from depth-of-field blur outside the focal zone. Research decides: penumbras on the hand stay sharp; softness comes from the terminators (form shadows on rounded fingers) and from blur in the near grass. If the brief needs visible soft cast shadows, they must fall at a distance (a shadow of the grass on the hand would be near; a shadow on ground far below is out of frame).
- **Terminators are soft on round forms,** narrow on sharp ones (layer 1: Lambert falloff; halftones wide where the form turns slowly). A terminator drawn as a soft *line* is a fault (calibration test: the egg's terminator "turned into a soft line" after the value bands stepped).

**Skylight in the shadows (kept, rendered as value):**
- The shadow family is not black: it is lit by the sky's large dome, so it shows the form gently, lighter on planes facing up toward the sky, darker on planes facing down or toward the ground (**judgement**, from skylight as a large overhead source; layer 1, overcast light).
- Reflected light from nearby surfaces (grass below the hand) lifts the undersides slightly; it stays darker than the darkest halftone (layer 1, Sessions).

**What a photograph adds and the style keeps:**
- **Contact and occlusion shadows** where fingers touch and fold: the darkest values in the picture, small and hard-edged (style doc, section 5: "dark contact shadows"; layer 1: occlusion value 0).
- **Highlights only where the skin is glossy** (a nail, a moist crease); a sunlit matte plane is not a highlight (layer 1, Proko).

## 4. Edges and marks
- **Order of work for the families:** decide the darks early ("there are no rules" for dark-to-light, but the darks are best decided early: Sibley, via the style doc); lay the shadow family per part with carbon first where it is darkest, then graphite bands lighter, hard over soft (style doc, sections 8–9).
- **Crisp cast-shadow edges** by masking: blend each family with `clip` so the edge between sun and shadow on the palm stays as sharp as the photograph (calibration, masked blending); never let a blender cross it.
- **Soft terminators** by an unclipped blend across the form's turn, over a width read from the schema (**judgement**).
- **Edges between two darks** (a cast shadow falling on the hand's shadow side) are the engine's weak point (calibration, limit 3): sharpen them with a hard pencil drawn along the schema's edge, or a `precision_eraser` with `seek` on the lighter side.
- **No outline:** the contour of the hand against the sky is a meeting of two tones, never a line (style doc, section 6).

## 5. What stays true to life
- One sun: every cast shadow and terminator agrees with it, and with the Moon's lit limb (`--moon.md`).
- The two families stay separate in value (layer 1's rule); the filter widens the gap, it never makes them overlap.
- Core shadow, reflected light and occlusion in their order (layer 1).
- Cast shadows sharp at contact, softer with distance; penumbra width from geometry, not taste.

## 6. Checks for Teodor
1. `notan 2` or squint: two families on the hand; nothing in shadow as light as the darkest lit halftone.
2. Values against the ruler: lit planes about L* 75–88, shadow family about L* 30–45, contact accents below L* 28; spread near 20.
3. Cast shadows on the hand are crisp (edge rise near the photograph's); terminators on fingers are gradients, not lines.
4. Shadow planes facing the sky are lighter than those facing down.
5. Every shadow direction agrees with the low sun's side, and with the Moon's lit limb.
6. No visible shine in the carbon darks under the raking-light sheen render.

## 7. Engine notes
- Families as regions (`segment` from the schema, or polygons); per family: `carbon_pencil` in the darkest band first, then `hatch` bands darkest first with `feather`, each `clip`ped (calibration recipe).
- Blending: `brush` with `clip: true` inside each family; one unclipped `tortillon` pass along rounded terminators only.
- Contact accents last with `carbon_pencil`, short; lift the reflected light and any gloss with `kneaded` or `precision_eraser` and `"seek": true` (calibration: lifts to about L* 57–60 and 88–91).
- **judgement:** the mapping and the value targets.

## 8. Sources
1. Wikipedia, [Sunny 16 rule](https://en.wikipedia.org/wiki/Sunny_16_rule) (sun vs open shade, four stops)
2. Ilford Photo, [Using colour filters](https://ilfordphoto.com/colour-filters); Photography Mad, [Using coloured filters](https://photographymad.com/pages/view/using-coloured-filters-in-black-and-white-photography)
3. Skillshare, [The real art of photorealistic drawing](https://www.skillshare.com/en/blog/the-real-art-of-photorealistic-drawing/) (edges as value changes; highlights not pure white)
4. Layer 1 `docs/subjects/light-shadow.md` (families, values, penumbra 1/110, Gurney's skylight shadows, Sessions); style doc (Sibley, Vitruvian Studio, the photographic ruler vs academic graphite); calibration note (darks reached, masked blending, edge limits, lift values)
- **Derived:** the filter widening the sun/shadow gap, penumbra widths on the sheet. **Judgement:** low-sun ratio, value targets, skylit shadow gradation, terminator handling, engine mapping. **Flag:** "soft penumbras" on a hand under a low sun are sharp; softness comes from form and blur.
