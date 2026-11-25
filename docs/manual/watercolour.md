# Watercolour (`watercolour`)

**What it is.** Finely ground pigment in gum arabic, thinned with water. It is transparent: every wash is a thin coloured film, and the white of the paper shining through it is the light. You cannot paint a light over a dark; you save the lights (leave the paper, or mask it) and work from light to dark, one glaze over another once the one below is dry. While a wash is wet it moves on its own: colour dropped into it bleeds into soft feathery shapes, water creeping into a half-dry wash pushes the pigment into a cauliflower ("back-run" or "bloom") with a dark, branching edge, and a wash that dries on dry paper leaves a darker line at its edge. Pigment settles into the hollows of the paper (granulation). Colours look darker wet and dry lighter. Code: `studio/v8/media/watercolour.py`, class `Watercolour`, a simplified version of Curtis et al. 1997 (`docs/MEDIA.md`, "Engine model (watercolour)").

**Supports.**
- `cold_press` (default): cotton paper with a felt tooth. Soft ragged edges, visible granulation, medium working time.
- `hot_press`: smooth. Paint stays on the surface longer, so edges are crisp and the dried edge line is the strongest; granulation is faint; lifting works best.
- `rough`: pronounced tooth. Water sinks in fastest (shortest wet-in-wet window), granulation is strongest, fast or dry strokes break up into the paper's pits, and details are hard.
- The ground colour you give `new` is the paper's white (for example `#f6f3eb`). The paper is kept one even white: there is no coloured noise on it.

**Tools** (`"brush": ...`).
- `round` (default): a pointed sable round. Light pressure gives a hairline from the tip; pressing lays the belly down into a broad stroke. It holds a lot of water, so long strokes stay wet; at the end of a long stroke it starts to break up into dry-brush.
- `flat`: a flat wash brush. Broad, even bands with straight edges.
- `mop` (aliases `hake`, `wash`): a big soft brush with lots of water and slightly thinner colour. Even washes and skies; into a wet wash it gives wide soft wet-in-wet shapes.
- `rigger` (alias `liner`): long, thin, even lines that taper (branches, rigging, grasses).
- `dry` (alias `fan`): dry-brush. Little water, splayed hairs: only the paper's peaks take colour, in broken, sparkling streaks. Lighter pressure catches fewer peaks. Nothing flows.
- `lift` (aliases `tissue`, `knife`, `smudge`): a damp clean brush or tissue. Picks a wet wash up almost completely, a dried wash partly, staining colours least. Soft-edged light shapes and lines.
- `sponge`: a sea sponge. A mottled, porous texture (foliage, stone, gravel). Dab rather than drag.
- `water` (alias `clean_damp_brush`): clean water. Wet the paper for wet-in-wet work; laid into a wash that has started drying (damp, no shine) it makes a back-run. Over dry paint it re-dissolves a little non-staining pigment.
- `mask` (alias `masking_fluid`): masking fluid. Reserves the paper with hard edges (shown as a pale yellow film) until `finish unmask`. Paint and washes do not reach the paper under it.
- `blend` (used by the `blend` intention): a damp brush that softens dried edges and wet colour and lifts a little.

**Parameters that matter** (on any intention that makes strokes):
- `water` (or `load`; default 1, `match` uses 1.3): how much water the brush carries. More water: longer strokes, more flow, stronger edge lines, blooms. Below about 0.35 the brush is dry and the marks break up on the paper's peaks.
- `strength` (default 1): pigment concentration. The colour you give is how the paint looks at strength 1 over white; 0.3 is a pale tint.
- `granulation` (0 to 1): how much the pigment settles into the hollows. If not given, it is guessed from the colour: blues (ultramarine, cobalt) and earths granulate, most others barely.
- `staining` (0 to 1, default 0.4): how firmly the pigment binds to the paper; staining colours (phthalo, alizarin) barely lift.
- `opacity` (default 0.1): watercolour is transparent; raise it only for semi-opaque pigments (cerulean, the cadmiums).
- Felt state: fast, agitated strokes skip over the tooth (more on rough paper); pressure widens the round.
- `match`: each stamp of the brush chooses the transparent colour that, over what is already dry on the paper, gives the schema's colour; where the paper is already dark enough it skips. So match can only darken: plan the lights (mask, or leave them) before matching. Strokes laid in one episode that touch while wet fuse into one wash; over a dried wash they glaze darker with their own edges. For large areas use `glaze` or `free` with the `mop`, and keep `match` for the middle and small scale (a few hundred strokes, `dry` between rounds).

**Glaze (a wash).** `glaze` lays a flat wash of water and pigment over the region: a transparent Kubelka-Munk film. `opacity` is the film's thickness (0.2 to 0.4 is a normal wash, 0.8 to 1 is the colour at full strength). The region's `feather` decides the edge: a small feather gives a hard edge that dries with a dark line; a large one fades out softly. A wash over a dry wash deepens it (yellow over blue gives green, layer by layer); a wash into a wet wash mixes with it wet-in-wet.

**Drying and time.** A wash stays shiny-wet for about two episodes (the wet-in-wet window: drop colour in and it bleeds softly), then damp for one or two more (adding wetter paint or water now makes back-runs), then it dries; rough paper is quicker, hot-press slower. Between episodes the water flows inside the wet area, pigment settles and granulates, and suspended pigment drifts to the edges where the wash meets dry paper. When a pixel dries its wash becomes a film over everything below. `dry 0.5` lets about two episodes pass; `dry 1` dries everything. Dry before painting crisp details, or they will bleed.

**Finishing** (`finish <op> ['<json>']`):
- `darks '{"n": 30, "size": 8}'`: final darks and crisp accents, wet-on-dry, at most `n` short strokes where the schema is darkest and the painting is not yet dark enough (needs a schema). Dries the painting first.
- `lift '{"region": {...}, "strength": 0.6, "soften": 6}'`: lift soft lights from the dried paint (`rect`, `ellipse` or `poly`, as in intentions). Without a region it lifts where the schema is lightest and the painting has gone too dark. Staining colours lift less; hot-press lifts best.
- `unmask '{"soften": 2}'`: rub off the masking fluid, revealing the paper; `soften` (px) blurs the hard edges it leaves.
- `dry`: let the painting dry completely.
- `mount`: no varnish (watercolour goes under glass, with a mat); it dries the painting and changes nothing else.
- Then `sign`, the very last act.

**Order of work.** Light drawing (`transfer`, lightly). Mask the brightest whites. Large pale washes (sky, ground), often wet-in-wet: wet the area with `water` or lay a pale `glaze`, then drop colour in with the `mop` or `round` in the next episode. `dry 1`. Midtone glazes and shapes wet-on-dry. Darks and details with the `round` and `rigger`, dry-brush for texture. `finish darks`, `finish lift`, `finish unmask`, then `sign`.

**Gallery.** `docs/gallery/watercolour_cold_press.jpg`, `_hot_press.jpg`, `_rough.jpg` (one row per tool; note that the gallery's ground is dry, so the `lift` and `water` rows only show where they cross the dark band, and the `mask` row shows the masking film). `docs/gallery/watercolour_effects_cold_press.jpg` shows the signatures: a flat wash with its dark edge, glazes layered (yellow under blue), lifting, granulating ultramarine and sienna, wet-in-wet drops, back-runs, dry-brush, sponge, a masked line revealed after a wash, rounds by pressure, a rigger line and flats. `docs/gallery/watercolour_scene_test.jpg` is a small painting made with washes, `match`, dry-brush and all the finishes.

**Limits.** The pigments of one wash are summed into one film (absorption per channel and one scattering value), so two pigments in one wash do not separate by granulation, and the order of dried layers is kept only in the composited colour (lifting treats all dried layers alike). The water flow is diffusion inside the wet area, not real fluid dynamics: no running downhill when the paper is tilted, and blooms grow from noise in the paper rather than from capillary flow. There is no salt, spattering or scratching out. The wet area moves only at episode ends, so within one episode strokes do not yet bleed into each other beyond the softening of a stroke laid into wet paper. Glazing many hard-edged strokes over dried ones builds up dark edge lines quickly: for smooth gradations use washes.
