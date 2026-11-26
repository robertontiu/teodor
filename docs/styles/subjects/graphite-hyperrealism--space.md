# Graphite hyperrealism: space (layer 2)

How graphite hyperrealism renders space and depth, written as a departure from layer 1 (`docs/subjects/space.md`), with this picture in mind: a close wide-angle lens, a shallow depth of field with the focus on a hand at arm's length, grass very near the lens, and the Moon at infinity. Style research: `docs/styles/graphite-hyperrealism.md`; engine data: `docs/calibration/graphite-hyperrealism.md`.

Researched 2026-11-26. **judgement** marks editorial calls; **derived** marks arithmetic from sourced formulas; **flag** marks a disagreement between brief and research.

## 1. Rulers
No hyperrealist drawing is named or measured (in copyright; style doc, section 1). The rulers are the lens's optics, which the current copies ("depth of field, perspective and range of focus" are the photographic limitations it uses: [Wikipedia, Hyperrealism](https://en.wikipedia.org/wiki/Hyperrealism_(visual_arts))), the measured black-and-white photographs (`studio/targets.parts/graphite-hyperrealism.json`: hard-edge share 0.17 ± 0.07, edge density 0.31), and technique sources on drawing focus and blur, cited below.

## 2. The twist in one paragraph
Layer 1 constructs space for the eye: one horizon, vanishing points, aerial perspective, everything in focus, as painting did before photography ([Eclectic Light, depth of field](https://eclecticlight.co/2023/10/13/painting-on-the-edge-depth-of-field/): traditionally "visual art conformed with human perception in not showing depth of field effects"). Graphite hyperrealism does not construct space at all; it **transfers** it from a photograph, so its perspective is the lens's and the camera's position (style doc, sections 6–7). Two cues are added that the eye does not see: **depth of field**, a zone of sharpness with blur growing before and behind it, and the **wide-angle extension** of a lens used close. Aerial perspective, which needs hundreds of metres, plays no part in a picture whose depths are 5 cm, 60 cm and the Moon.

## 3. Departures from layer 1

**Perspective is the lens's (extended, not corrected):**
- A 24 mm lens on 35 mm covers 73.7° × 53.1° (layer 1 table). Used close, it makes near things huge and far things tiny (layer 1, [Wikipedia, Perspective distortion](https://en.wikipedia.org/wiki/Perspective_distortion)).
- **Scale on the sheet (derived):** with the frame's 24 mm side across Teodor's 48 cm sheet (20×), an object at distance d appears at 20·f/(d − f) of life size: the hand at 0.6 m at about 0.83 life size (a 19 cm hand about 16 cm on the sheet); a grass blade at 10 cm at 6.3× life size; at 5 cm at 18×; the Moon 4.3 mm (22 px).
- **Corners stretch:** a round thing near the corner of a 24 mm frame is drawn about 1.2–1.35× longer radially (layer 1 of `moon.md`, **derived** from the projection). Keep the Moon away from the corners, or draw it oval there.
- **Corner darkening (judgement):** wide-angle lenses darken the corners of an even sky (natural vignetting); in a drawing whose sky is already darker at the top it reads as photographic. Keep it slight; it is not sourced to a measured lens.

**Depth of field (added):**
- Blur of a point at distance d, focused at s: b = f²·|s − d| / (N·d·(s − f)) on the sensor; at infinity b = f²/(N(s − f)); hyperfocal distance H = f²/(N·c) (thin-lens optics; [Wikipedia, Depth of field](https://en.wikipedia.org/wiki/Depth_of_field), [Hyperfocal distance](https://en.wikipedia.org/wiki/Hyperfocal_distance); c is 0.025–0.03 mm for 35 mm). Blur "increases with the distance from the subject" (Wikipedia, Depth of field).
- **For this picture (24 mm, focus 0.6 m, c 0.03 mm, blur in px on the 48 cm sheet at 5 px/mm; derived):**

| f-number | sharp zone | Moon (infinity) | grass at 30 cm | at 20 cm | at 10 cm | at 5 cm |
|---|---|---|---|---|---|---|
| f/2.8 | 0.55–0.66 m | 36 px (larger than the 22 px Moon) | 36 | 71 | 179 | 393 |
| f/5.6 | 0.51–0.73 m | 18 | 18 | 36 | 89 | 196 |
| f/8 | 0.48–0.80 m | 12.5 | 12.5 | 25 | 62 | 138 |
| f/11 | 0.45–0.91 m | 9 | 9 | 18 | 45 | 100 |
| f/16 | 0.40–1.2 m | 6 | 6 | 12.5 | 31 | 69 |
| f/22 | 0.36–1.9 m | 4.5 | 4.5 | 9 | 23 | 50 |

- **Flag: "shallow depth of field" with a Moon that must be the hardest-edged small shape.** At f/2.8–f/5.6 the Moon's blur is as large as the Moon, so it smears into a dim blot (`--moon.md`). At **f/16** the zone of sharpness is still only 0.4–1.2 m, grass at 5–10 cm is blurred by 31–69 px (6–14 mm), and the Moon is crisp with about 1.2 mm of rim softening. Research decides: **f/16** (or f/11–f/22), which keeps every part of the brief except a blurred background; nothing in this picture lies in the "background" between 1.2 m and the Moon except the sky, which has no edges to blur.
- **Blur is continuous with depth.** It grows smoothly away from the focal plane, so the transition from the sharp hand to the blurred grass follows each blade's distance, never a line (Wikipedia, Depth of field). A sharp subject on an evenly blurred field reads as cut out: painters who did it were criticised for figures "so sharp against [the] landscape that they appear cut out" (Eclectic Light, on Renoir). Grade the blur by distance.

**Left out:**
- **Aerial perspective:** no haze at 5 cm or 60 cm; and the Moon's veil is the sky's own (`--moon.md`). Blurred near grass is **not** lighter or greyer for being near or blurred; it keeps its own value (**judgement**, from optics: blur spreads light, it doesn't add any).
- **Constructed vanishing points:** none to construct; the transfer carries the lens's geometry (style doc, section 6).

## 4. How blur is drawn in graphite
- **Blur is an edge width, not a value change.** An out-of-focus object keeps its mean value; its edges spread over about its blur diameter, its texture disappears and its small details merge (**judgement**, from the blur-disc model above). Calibration measures this as the 10–90% edge rise in mm; set it from the table.
- **Thin things thinner than their blur fade:** a dark blade narrower than its blur disc becomes a translucent veil, its contrast against the sky cut to about its width divided by the blur (**derived**, from spreading the blade's light over the disc). Draw such blades as grey ghosts, not dark lines.
- **Points of light become discs:** "each point of light becomes an image of the aperture, generally a more or less round disc," polygonal when stopped down ([Wikipedia, Bokeh](https://en.wikipedia.org/wiki/Bokeh)); bokeh "is most visible around small background highlights, such as specular reflections" (same). At f/16 the disc is polygonal (the aperture's blades). Only specular glints make discs; matte grass makes soft bands (**judgement**).
- **Technique sources:** decide what is blurred before adding detail, smudge it with a stump or rag, then add the details "only visible on a well-focused object" ([Dessindigo, how to draw a blur effect](https://dessindigo.com/en/blog/drawing-tutorial/draw-blur-effect)); "drawing the focal point in sharp detail and leaving the rest out of focus" ([Wildlife Art Store, drawing realistic grass](https://www.wildlifeartstore.com/drawing-realistic-grass/)); soft edges come from layering thin passes and soft blending brushes ([Wyndham, painting out-of-focus objects](https://www.wyndhamartsupplies.com/blogs/artist-features/how-to-paint-the-illusion-of-out-of-focus-or-blurry-objects-by-drew-steadman), a paint source; the same principle in graphite is the `brush` blender).
- **Sharpness where it is sharp:** in the focal plane, edges are as hard as the photograph's (edge rise near the reference's 1.3–1.7 mm in the calibration test; hard-edge share near 0.17 for the whole sheet). The hand's contour is the hardest edge set in the picture (**judgement**).

## 5. What stays true to life
- Overlap order: near grass over the hand over the sky and Moon (strongest depth cue, layer 1).
- Relative size by distance (the scale numbers above).
- One eye level and one lens for the whole sheet: no part drawn as if with another lens (a telephoto Moon in a wide-angle picture).
- Shadows agree with one sun (`--light-shadow.md`).

## 6. Checks for Teodor
1. The schema states the lens (24 mm or as chosen), the focus distance (0.6 m), and the f-number (f/16 recommended); every blur on the sheet follows the table.
2. The Moon is the lens's size (22 px at 24 mm on a 48 cm sheet) and not in a corner (or oval if so).
3. Blur grows smoothly with each blade's distance; no uniform blur field and no cut-out edge round the hand.
4. Blurred things keep their value; thin blurred blades fade to translucent grey; only glints make discs.
5. Sharp edges only in the 0.4–1.2 m zone (the hand and any blades at its distance).

## 7. Engine notes
- Schema: a rendered scene (`scene.py`) with the camera's vertical `fov` set to the lens (layer 1 mapping: for 24 mm, 74 on a portrait sheet, whose height is the frame's 36 mm side, as assumed in the scale numbers here; 53 on a landscape sheet) and depth of field rendered per the table, or a photograph; greyscale.
- Blur in the drawing: lay the part's tone with `hatch` bands (`feather` on), then blend with `brush` sized near the part's blur, **unclipped** across its edge, so the edge spreads by the blur width; sharp parts blended with `clip: true` so their edges stay crisp (calibration, masked blending).
- Check edge widths with the eyes' edge measures against the table (**judgement**: the mapping of brush size to edge rise is not calibrated; measure a test edge first).

## 8. Sources
1. Wikipedia, [Hyperrealism (visual arts)](https://en.wikipedia.org/wiki/Hyperrealism_(visual_arts)); [Depth of field](https://en.wikipedia.org/wiki/Depth_of_field); [Hyperfocal distance](https://en.wikipedia.org/wiki/Hyperfocal_distance); [Bokeh](https://en.wikipedia.org/wiki/Bokeh); [Perspective distortion](https://en.wikipedia.org/wiki/Perspective_distortion)
2. Eclectic Light, [Painting on the edge: depth of field](https://eclecticlight.co/2023/10/13/painting-on-the-edge-depth-of-field/)
3. Dessindigo, [How to draw a blurred effect](https://dessindigo.com/en/blog/drawing-tutorial/draw-blur-effect); Wildlife Art Store, [Drawing realistic grass](https://www.wildlifeartstore.com/drawing-realistic-grass/); Wyndham Art Supplies, [How to paint the illusion of out-of-focus objects](https://www.wyndhamartsupplies.com/blogs/artist-features/how-to-paint-the-illusion-of-out-of-focus-or-blurry-objects-by-drew-steadman)
4. Layer 1 `docs/subjects/space.md` (angles of view, `fov` mapping) and `docs/subjects/moon.md` (Moon size, corner stretch); style doc and calibration note (edge measures, masked blending, photographic ruler)
- **Derived:** the blur table, sheet scale by distance, thin-blade contrast. **Judgement:** vignetting, blur keeps value, glints only make discs, the hand as the hardest edges, engine mapping. **Flag:** shallow focus vs a crisp Moon, resolved at f/16.
