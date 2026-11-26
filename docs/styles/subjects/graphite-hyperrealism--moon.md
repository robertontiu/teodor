# Graphite hyperrealism: moon (layer 2)

How graphite hyperrealism renders the Moon, written as a departure from layer 1 (`docs/subjects/moon.md`), with a small daytime waxing gibbous in mind, meant as the brightest and hardest-edged small shape in the picture. Style research: `docs/styles/graphite-hyperrealism.md`; engine data: `docs/calibration/graphite-hyperrealism.md`. Companion pages for the same picture: `graphite-hyperrealism--sky.md`, `--space.md`, `--light-shadow.md`, `--trees-plants.md`.

Researched 2026-11-26. **judgement** marks editorial calls; **derived** marks arithmetic from sourced values; **flag** marks a place where the brief and the research disagree.

## 1. Rulers (why no works are named)
The current is contemporary and its drawings are in copyright, so no drawing is measured or named here (style doc, section 1). As in the style doc, the rulers are (a) technique sources on how graphite reaches photographic values and edges, cited below, and (b) what a black-and-white photograph of the subject shows: the measured photographic range in `studio/targets.parts/graphite-hyperrealism.json` (key L* 50, p5–p95 L* 17–82, hard-edge share 0.17) and the Moon's own photometry and optics from layer 1. A hyperrealist drawing "looks like the photograph" (style doc, section 10), so the question for every rule is: what would the photograph show?

## 2. The twist in one paragraph
Layer 1 describes the Moon as the eye sees it; graphite hyperrealism draws it as the camera records it. That changes three things. Its **size** is the lens's, not the mind's: a wide lens makes it a dot, and the style never enlarges it, because a hyperrealist's perspective is the lens's ("perspective" is among the photographic limitations hyperrealism uses: [Wikipedia, Hyperrealism](https://en.wikipedia.org/wiki/Hyperrealism_(visual_arts))). Its **value** is the film's and the filter's: a red or orange filter darkens the blue sky and leaves the brownish-grey Moon almost untouched ([Ilford](https://ilfordphoto.com/colour-filters); layer 1), so the day Moon becomes a light disc on a grey sky instead of a pale ghost on a light one. Its **edge** is the depth of field's: sharp only if infinity is inside the zone of focus. Everything else stays astronomically true, because a viewer of a hyperrealist drawing checks it against photographs.

## 3. Departures from layer 1

**Size (kept, not enlarged):**
- On Teodor's 48 cm-wide sheet a 24 mm lens gives a Moon 4.3 mm (22 px) across, a 35 mm lens 6.3 mm (32 px), a 50 mm lens 9 mm (45 px) (layer 1 table, **derived** from f/110). That is the size to draw. A big Moon is a telephoto picture taken from far away, not a wide one (`--space.md`).
- At 22 px the disc carries only its gross pattern: the lit semicircle, the bowed terminator and two or three soft maria. Hyperrealists "draw it enlarged" to get detail (calibration, limit 6: a 0.3 mm lead is 1.5 px); the Moon is the one subject that cannot be enlarged without changing the lens, so it stays simple (**judgement**).

**Value (pushed by the filter, ordered by the light):**
- **Unfiltered, the day Moon is barely there:** 1.1 to 1.7 times the sky's luminance beside it, under one stop, about 5–10 L* above a sky of L* 65–75 (layer 1, **derived** and **judgement**).
- **Filtered (the brief's "filtered black-and-white photograph"):** orange records blue skies "in very dark tones", red "as black" (Ilford); the Moon keeps its value, so the gap opens to about 15–30 L* (**judgement**, from the filters' action; no public-domain filtered day-Moon photograph was found to measure).
- **Flag: "the brightest small shape".** In daylight the Moon has the value of sunlit worn asphalt (albedo 0.12; "Looney 11" is one stop under "sunny 16": layer 1). Anything sunlit and lighter in tone (skin, paper, a white nail edge, a lit cloud) is brighter than the Moon in the photograph. Research decides: keep the photograph's order, **lit skin ≥ Moon > sky**. The Moon can still be the brightest *small* shape and the brightest thing in the *sky*, if (a) the sky is filter-darkened, and (b) no other small sunlit light (a glint on a grass blade, a nail highlight) is drawn lighter than it. The hand's lit planes, a large shape, may equal or pass it. If the brief insists on the Moon at paper white, the photograph's logic needs the lit hand at or above paper white too (blown highlights), which raises the whole key; say so in the journal if chosen.
- **Suggested targets (judgement, from the above, for a red-to-orange-filtered sky):** sky beside the Moon L* 45–55; Moon highlands L* 70–80; maria 4–8 L* darker than the highlands, the day sky's veil having cut their contrast (layer 1: maria about L* 50 against highlands L* 80 on a black ground); the unlit part of the disc exactly the sky's value.

**Left out (true to the photograph):**
- No outline of the full circle and no earthshine: by day the dark part of the disc is the sky (layer 1).
- No craters: at 22 px they are below the drawing's resolution; only the maria and the limb read (**judgement**).
- No glow or halo around a day Moon: the glow measured round a clipped night Moon (layer 1: L* 30 falling to 18 within two radii) belongs to an overexposed disc on a black sky, not to a day Moon (**judgement**).

## 4. Edges
- **Flag: "the hardest-edged small shape" with "a shallow depth of field focused on a hand".** The Moon is at infinity. With a 24 mm lens focused at 0.6 m, infinity's blur disc on the sensor is f²/(N(s − f)) (thin-lens optics; [Wikipedia, Depth of field](https://en.wikipedia.org/wiki/Depth_of_field) and [Hyperfocal distance](https://en.wikipedia.org/wiki/Hyperfocal_distance)): 0.36 mm at f/2.8, larger than the Moon's 0.22 mm image, which smears it into a soft, dimmed blot (peak contrast about (0.22/0.36)² ≈ 0.37 of the sharp Moon's) (**derived**). At f/16 the blur is 0.06 mm, a rim softened over about 1.2 mm of a 4.3 mm disc on the sheet, and the disc reads as a crisp round shape (**derived**; numbers in `--space.md`). So the brief holds only at a small aperture (f/11–f/22), where the foreground grass is still deeply blurred because it is very near the lens (`--trees-plants.md`). Research decides: draw the Moon as an f/16 photograph would show it, crisp but with a rim softening of about a quarter of its diameter in total, not as a cut-out hole.
- **The lit limb is the hardest edge on the disc** (no atmosphere on the Moon: layer 1); the terminator is softer, a gradient over roughly the last third of the lit width at telephoto scale, which at 22 px becomes a soft 2–4 px transition (**judgement**, scaled from the measured rendering in layer 1).
- Hard-edge share: the whole photograph's is about 0.17 (style doc); the Moon contributes one short arc of it.

## 5. Marks and order of work
- **Reserve, don't lift from dark.** The disc is smaller than the battery eraser's 5 mm cap and only twice the eraser pen's 2.3 mm tip (calibration, engine tools), and an erased tone never returns to clean paper (Sibley, indenting explained, via the style doc). Keep the disc free of sky tone from the start: the sky is laid with `clip` to a region that has the disc as a hole (a `segment` region or a polygon with a slit: calibration, limit 5) (**judgement**).
- **Then tone the disc up from the paper:** a very light 2H/HB pass with `mech_03` for the general disc value (paper is L* 96, the target about L* 70–80), the maria as two or three soft patches with `mech_03` HB, blended with a small `tortillon`, and the terminator side faded into the sky value. Hard over soft and light passes, as for any smooth passage (Vitruvian Studio; Sibley, via the style doc).
- **Soften the rim last,** one light unclipped `tortillon` pass round the limb (about 1 mm, the f/16 blur), slightly more on the terminator side (**judgement**).
- **Check its value against the sky and the hand** with `look` and the eyes' value sampling: the Moon is the lightest small shape, the sky darker by 15–30 L*, the hand's lit planes as light or lighter.
- **No stylus:** an indent makes a crisp white line, which the Moon's soft rim and the maria are not; there is nothing line-like on a 22 px Moon (style doc, indenting; **judgement**).

## 6. What stays true to life
- The lit limb faces the Sun along the great circle; for a waxing gibbous in the late afternoon (Northern Hemisphere) the Moon is low in the east and its lit side faces the Sun behind the camera, toward the side the hand is lit from (layer 1; `--light-shadow.md`).
- The phase shape: lit limb a semicircle, terminator a half-ellipse bowed into the dark half (about half a radius at 75% lit).
- The maria pattern of the real near side, the right way up for the hemisphere and the hour.
- Its size, about 0.5° of the field of view; slightly oval if it sits near the corner of a wide frame (layer 1, corner stretch).

## 7. Checks for Teodor
1. Diameter = the lens's (22 px on a 48 cm sheet for 24 mm, 45 px for 50 mm); no enlargement.
2. The disc is the lightest small shape on the sheet, 15–30 L* above the sky beside it; no other small light (glints, nail highlights) is lighter; the lit hand may be as light or lighter.
3. The unlit part is indistinguishable from the sky; no circle outline, no earthshine, no halo.
4. Lit limb crisp with about 1 mm of softening; terminator a soft half-ellipse on the side away from the Sun.
5. Two or three soft maria, 4–8 L* darker, no craters.
6. The lit side points toward the Sun that lights the hand.

## 8. Engine notes
- Region for the disc: `{"type": "segment", "at": [x, y]}` on the schema's disc or a circle polygon; sky `hatch` bands with that region excluded (`clip`), darkest first as the style's recipe (calibration, test drawing).
- Disc: `mech_03` with `grade` 2H/HB at low pressure, `tortillon` blending clipped to the disc; one unclipped `tortillon` pass round the rim. If the disc took stray tone, `precision_eraser` with `"seek": true` (lifts to about L* 88 at most).
- Value check: the eyes' sampling of the disc, the sky ring around it (1.5–2 radii), and the hand's lit plane.
- **judgement:** the whole mapping; the reserve-first order follows from the eraser sizes and the calibration's lift values.

## 9. Sources
1. Wikipedia, [Hyperrealism (visual arts)](https://en.wikipedia.org/wiki/Hyperrealism_(visual_arts)) (photographic limitations: depth of field, perspective, range of focus)
2. Ilford Photo, [Using colour filters for black and white photography](https://ilfordphoto.com/colour-filters) (yellow, orange, red on blue sky; filter factors); Photography Mad, [Using coloured filters](https://photographymad.com/pages/view/using-coloured-filters-in-black-and-white-photography) ("turn a blue sky almost black")
3. Wikipedia, [Depth of field](https://en.wikipedia.org/wiki/Depth_of_field), [Hyperfocal distance](https://en.wikipedia.org/wiki/Hyperfocal_distance) (circle of confusion 0.025–0.03 mm for 35 mm; blur grows with distance from the focal plane)
4. Layer 1, `docs/subjects/moon.md` (size table, luminances, Looney 11, measured NASA images, filter effect on the Moon)
5. Style and calibration: `docs/styles/graphite-hyperrealism.md` (Sibley on indenting and hard over soft; Vitruvian Studio on light passes and shine; Wildlife Art Store on erasers), `docs/calibration/graphite-hyperrealism.md` (eraser lifts, tool caps, regions, resolution limit), `studio/targets.parts/graphite-hyperrealism.json` (photographic ruler)
- **Judgement calls:** filtered Moon/sky gap, the value targets, no craters at 22 px, no glow by day, reserve-first order, rim and terminator softening widths, engine mapping. **Flags:** "brightest" (kept as brightest small shape and brightest in the sky; lit skin may be lighter), "hardest-edged" with shallow focus (holds only at f/11–f/22).
