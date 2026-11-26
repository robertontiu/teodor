# Graphite hyperrealism: trees and plants (layer 2)

How graphite hyperrealism renders vegetation, written as a departure from layer 1 (`docs/subjects/trees-plants.md`), with grass blades close to the lens in mind: blurred as bokeh, with a few sharp ones. Style research: `docs/styles/graphite-hyperrealism.md`; engine data: `docs/calibration/graphite-hyperrealism.md`; the optics of this picture: `graphite-hyperrealism--space.md`.

Researched 2026-11-26. **judgement** marks editorial calls; **derived** marks arithmetic from sourced values; **flag** marks a disagreement between brief and research.

## 1. Rulers
No hyperrealist drawing is named or measured (in copyright; style doc, section 1). The rulers are the lens's optics (`--space.md` table), the measured photographs (`studio/targets.parts/graphite-hyperrealism.json`), and graphite technique sources on grass, white lines and blur, cited below.

## 2. The twist in one paragraph
Layer 1 sees vegetation at painting distance: masses, clumps, sky holes, Carlson's dark upright planes, detail only at edges and in the light. Graphite hyperrealism, working from a close photograph, inverts the scale: the nearest blades are enormous and soft, a few at the focus distance are small and razor-sharp, and the "mass" logic gives way to the lens's logic of focus. Where layer 1 simplifies by distance (Ruskin's twigs that become "a vague and slight darkness"), the camera simplifies by defocus: texture and edges dissolve, value stays. The style's technique sources for grass all work by **negative drawing** and **reserved or lifted lights**: draw the darks between blades and leave or lift the blades ([Sibley, drawing grass](https://sibleyfineart.com/tutorial--draw-grass.htm); [Wildlife Art Store, drawing realistic grass](https://www.wildlifeartstore.com/drawing-realistic-grass/)).

## 3. Departures from layer 1

**Scale and focus (stretched by the lens):**
- With a 24 mm lens focused on a hand at 0.6 m, on a 48 cm-wide sheet (`--space.md`, **derived**): a 4 mm-wide blade at 5 cm is drawn about 74 mm wide, at 10 cm about 25 mm, at 30 cm about 7 mm, at the hand's 0.6 m about 3.3 mm.
- Blur at f/16: about 14 mm at 5 cm, 6 mm at 10 cm, 1.2 mm at 30 cm, none at 0.4–1.2 m (`--space.md` table).
- So the **near blades are broad soft bands** crossing the bottom of the frame (wider than their blur, so they keep a core of their own value with soft edges); blades at 20–30 cm are **nearly sharp**; only blades at the hand's distance are **sharp**.
- **Flag: "a few sharp ones" among near, blurred blades.** Optics does not allow a sharp blade at 5–10 cm with the focus at 0.6 m: a sharp blade has to stand in the zone of focus, about 0.4–1.2 m at f/16, so it is drawn small (a few mm wide), beside or behind the hand, not among the giant near blades. Research decides: place the sharp blades at the hand's distance (their bases low in the frame or beside the wrist, their tips rising into the sky), and keep every near blade blurred by its distance.

**Value (kept, with the filter's shift):**
- Grass is green; an orange or red filter passes little green, so filtered grass prints darker than the eye sees, and a yellow filter "lightens foliage" ([Bolo's notes on filters](https://pages.cs.wisc.edu/~bolo/photo/filters.html); red helps separate flowers from foliage: [Photography Mad](https://photographymad.com/pages/view/using-coloured-filters-in-black-and-white-photography)). **judgement:** under the orange-to-red filter of this picture, sunlit blades about L* 45–65, shadowed blades and the gaps between them L* 20–35.
- Blades seen against the sky are darker than it (layer 1: vegetation is the darkest upright plane in sun); their sunlit edges lighter. With the low sun behind the camera, the blades are front-lit: few glints, little translucency (layer 1's backlit glow needs the sun ahead) (**judgement**).
- **Blur keeps value:** a near blurred blade is not lighter or greyer than a sharp one of the same tone; there is no aerial perspective at 5 cm (`--space.md`). The rule from layer 1 and the grass tutorials, "the grass in the background lighter and less detailed" (Wildlife Art Store), applies to distance, not to near blur.

**Bokeh (narrowed):**
- True bokeh discs come from small bright points (specular glints, light through gaps): "each point of light becomes an image of the aperture" ([Wikipedia, Bokeh](https://en.wikipedia.org/wiki/Bokeh)). Front-lit matte grass makes soft bands, not discs. A disc appears only where a sunlit glint on a blade falls out of focus: a polygon at f/16 (aperture blades), as wide as that depth's blur (6–14 mm at 5–10 cm), light but not paper white, even or slightly brighter at the rim (Wikipedia, Bokeh: "uniformly illuminated, brighter near the edge, or brighter near the center") (**judgement** for how many: a few, low in the frame).
- **Thin blurred blades fade:** a blade narrower than its blur becomes a translucent grey veil over whatever lies behind (`--space.md`, **derived**); draw these as ghosts, not as dark strokes.

**Kept from layer 1:**
- Each blade starts somewhere and ends somewhere: "every stalk you draw must have a beginning and an end" (Sibley); blades taper to a point and bend from the base, never ruled lines (**judgement**, layer 1 growth).
- Blades in a clump overlap and cross; their directions vary around one growth direction and one wind (layer 1, wind; **judgement**).
- The darks between blades carry the depth: "making some of these areas almost black, you can create a sense of depth and volume" (Wildlife Art Store), in focus only.

## 4. Edges and marks
- **Sharp blades:** draw the dark around them (negative drawing: "a line either side to delineate the space that constitutes the stalk and leaf", Sibley); their light edges either **indented** before any tone with the `stylus` (a groove stays white under shading: [Sibley, indenting](https://sibleyfineart.com/tutorial--indenting.htm)) or **lifted** with an eraser pen ("to draw individual blades of grass", Wildlife Art Store). Indent only the sharp, sunlit edges: grooves are permanent and crisp, which a blurred blade must not show (style doc, section 8; **judgement**).
- **Darks between sharp blades:** `mech_03`/`mech_05` 4B to 8B, then carbon for the deepest gaps, small and hard-edged.
- **Near, blurred blades:** no stylus, no visible stroke. Lay each band's value, then blend unclipped across its edge with a `brush` about as wide as its blur (6–14 mm), so the edge spreads over that width; the band's core keeps its value (`--space.md`, blur is an edge width). Decide the blur first, smudge, then add detail only where in focus ([Dessindigo, blur effect](https://dessindigo.com/en/blog/drawing-tutorial/draw-blur-effect)).
- **Glint discs:** reserve or lift a soft polygon with `kneaded` and `"seek": true` to its value; no hard rim unless the reference shows one (**judgement**).
- **Order:** sky first (it passes behind everything: `--sky.md`); indent the sharp blades' light edges before any tone; then the hand; then the near blurred bands over the sky and hand edges; sharp-blade darks and carbon accents last (**judgement**, following the style's order: indent first, darkest last).

## 5. What stays true to life
- Blade shape and growth: tapering, curved, from a base; overlapping in depth.
- One light: front-lit blades, shadows on the side away from the low sun (`--light-shadow.md`).
- Overlap: near blades over the hand and sky.
- Size by distance, exactly from the lens (`--space.md`).

## 6. Checks for Teodor
1. Every near blade's blur matches its distance in the `--space.md` table; none is sharp.
2. The few sharp blades are in the focal zone, small (a few mm), with crisp light edges and dark gaps.
3. Blurred blades keep their value; thin ones fade to translucent grey; no visible strokes in them at 1:1.
4. Bokeh discs only where glints are, polygonal at f/16, light grey, few.
5. No stylus groove in any blurred blade; no outline on any blade.

## 7. Engine notes
- Schema: the rendered or photographed scene with depth of field (`--space.md`); regions for sharp blades, near blades and gaps (`segment` or polygons).
- Sharp blades: `stylus` along their lit edges first; gaps with `mech_03`/`mech_05` `hatch` clipped to the gap regions; `carbon_pencil` accents last.
- Near blades: `hatch` bands per blade (`feather` on), then `brush` blending unclipped, sized to the blur (`size` in px about the blur diameter; **judgement**: not calibrated; test one edge and measure its 10–90% rise first).
- Glints: `kneaded` or `precision_eraser` with `"seek": true`.

## 8. Sources
1. Sibley Fine Art, [Drawing grass](https://sibleyfineart.com/tutorial--draw-grass.htm); [Indenting tutorial](https://sibleyfineart.com/tutorial--indenting.htm)
2. Wildlife Art Store, [Drawing realistic grass](https://www.wildlifeartstore.com/drawing-realistic-grass/) (negative spaces "almost black", eraser pen blades, scoring, focal point sharp and the rest out of focus)
3. Dessindigo, [How to draw a blurred effect](https://dessindigo.com/en/blog/drawing-tutorial/draw-blur-effect)
4. Wikipedia, [Bokeh](https://en.wikipedia.org/wiki/Bokeh)
5. Bolo's notes, [Filters](https://pages.cs.wisc.edu/~bolo/photo/filters.html) (yellow lightens foliage); Photography Mad, [Using coloured filters](https://photographymad.com/pages/view/using-coloured-filters-in-black-and-white-photography)
6. Layer 1 `docs/subjects/trees-plants.md`; `graphite-hyperrealism--space.md` (blur table); style doc and calibration note
- **Derived:** blade sizes and blurs on the sheet, translucent thin blades. **Judgement:** filtered grass values, front-lit with few glints, number and look of discs, order of work, brush size for blur. **Flag:** sharp blades cannot stand among the near blurred ones; they belong in the focal zone.
