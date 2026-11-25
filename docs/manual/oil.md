# Oil (`oil`)

**What it is.** Pigment in linseed oil. It stays wet for a long time, so strokes mix into each other on the canvas, and it has body, so every stroke keeps the shape the brush gave it: the furrows the bristles drag through it, a ridge where the brush lifts, broken edges where a nearly empty brush skims the weave. Dark, transparent paint can be laid as a glaze, a coloured film that glows over light paint and deepens darks. When it dries, it dries glossy where it holds enough oil and dull ("sunk in") where a lean or absorbent layer beneath drew the oil out. Varnish evens that out at the end. Code: `studio/v8/media/oil.py`, class `Oil`. (`oil-v7` is the frozen v7 paint, kept only as a regression reference.)

**Supports.**
- `canvas` (default): primed linen. A plain weave with uneven threads shows through thin paint under the raking light, and it catches dry-brush and scraping: paint stays on the thread tops or in the hollows.
- `panel`: a gessoed wooden panel. Smooth and hard: no weave, so stroke edges and knife slabs read crisply and dry-brush breaks along the bristles instead of the surface. It is a little more absorbent, so lean paint sinks in more.
- The ground colour is the colour you give `new` (for example `#a98a68` for a toned ground). A transparent earth `glaze` over a white ground gives a real imprimatura, which the rag can wipe back to white while it is wet.

**Tools** (`"brush": ...`). Each brush is a set of bristle clumps with their own paint load and their own slightly unmixed colour, so every stroke differs a little from the last one.
- `round` (default): a round hog brush with a pointed tip. Light pressure gives a thin line; pressing spreads it into a fat teardrop. Strokes taper in and out with the hand's pressure.
- `flat`: a long flat. Square-edged planes and chisel strokes with strong furrows along the stroke.
- `bright`: a short, stiff flat. Short, thick, heavily furrowed dabs. It holds little paint and runs out fast into dry-brush.
- `filbert`: a flat with a rounded tip. Soft-edged, leaf-shaped marks with gentler furrows, wider when pressed.
- `fan`: sparse spread hairs. Bundles of fine parallel lines (grass, hair, foliage) and broken textures.
- `liner` (alias `rigger`): long soft hair. Long, even, thin lines of fluid paint, tapering at the ends.
- `knife`: a palette knife. Flat slabs of paint with smooth tops and crisp edges, a small ridge at the sides and where it lifts. It holds little, and when it is nearly empty (or with `"scrape": true`) it scrapes instead: wet paint is taken off the thread tops back toward the dried layer or ground beneath, leaving colour in the weave's hollows. On dry impasto it shaves the peaks.
- `rag` (alias `cloth`): wipes wet paint off toward the layer beneath, leaving a streaky, mottled stain. The classic use: wipe the lights out of a wet imprimatura. It does nothing to dry paint.
- `smudge` (alias `finger`): pushes and smears wet paint, carrying colour along.
- `blend` (alias `blender`; used by the `blend` intention): a soft dry brush that softens wet paint and edges (sfumato) and flattens the relief a little.
- `scraper` (alias `sgraffito`): the wrong end of a brush. Thin lines scratched through wet paint to the layer beneath, with the displaced paint as a small rim. On dry paint it barely marks.

**Parameters that matter** (on any intention that makes strokes):
- `load` (default 1; `match` uses 1.3): how much paint the brush carries. As the load runs out, the stroke thins and breaks up over the weave, clump by clump.
- `impasto` (default 0.5): how thick the paint is laid. It sets the furrow depth, edge ridges and the ridge at the lift.
- `fat` (0 to 1, default 0.5; liner 0.65, bright 0.45): oil content of the paint. Lean paint (0.2 to 0.35) for a block-in, more oil in later layers. Lean paint over a lean or absorbent layer dries dull. Lean paint laid over a fatter layer that has started drying prints a craft note ("fat over lean") after the episode.
- `wetmix` (default 0.5; `match` uses 0.22): how much a stroke mixes into wet paint beneath. `pickup` (default 0.35): how fast the bristles take on the wet colours they cross, so the colour drags and streaks along the stroke.
- `cover` (default 0.95): how opaque the paint is. `streak` (default 0.5): how unmixed the colour on the brush is (0 gives clean strokes).
- `edge` (`hard`, `soft`, `lost`): edge softness of the brush footprint.
- Felt state: fast, agitated strokes break into dry-brush; slow, careful strokes stay full. Pressure from the hand widens the round and the filbert.

**Glaze.** `glaze` lays a transparent Kubelka-Munk film over what is there; it does not mix toward the colour. A dark or saturated colour (a lake, a transparent earth) acts as a glazing pigment: over white it glows with full colour, over dark paint it deepens and tints it without lightening it, and it pools a little in the weave and in the hollows of the brushwork. A light colour carries white and acts as a veil (velatura or scumble): it lightens darks. `opacity` sets the film's thickness (0.2 to 0.35 is a normal glaze; 1 is a heavy film). Over wet paint a glaze partly mixes in. A glaze is oil-rich, wet and glossy, so lean paint over it triggers the fat-over-lean note.

**Drying and time.** Oil stays wet across episodes: each episode end dries it only a little (thin paint faster than thick, oil-rich paint a little slower). Wet paint renders glossy. `dry 0.5` is a few days, `dry 1` is fully dry. Once paint is touch-dry it becomes the layer beneath: the rag, the scraper and the scraping knife reveal it, and its relief stays under new paint. Paint laid on wet paint mixes into it and reshapes its relief.

**Finishing** (`finish <op> ['<json>']`):
- `retouch`: retouch varnish. Where the paint is touch-dry, sunken (dull) passages come back to an even gloss and their darks deepen. Use it when the surface looks patchy, or before judging the final values.
- `oil-out`: rub a thin film of oil over sunken passages before painting on. Like retouch, but the passages become slightly wet and fatter.
- `glaze '{"color": "#5a3020", "opacity": 0.15, "region": {...}, "feather": 30}'`: a last unifying glaze over the whole or a region (`rect`, `ellipse` or `poly`, as in intentions).
- `varnish '{"gloss": 0.85}'`: the final varnish, gloss 1 (glossy) to 0 (matte). It refuses while any paint is still wet (in reality it would trap the solvent and stay tacky): run `dry 1` first. It evens the sheen. Gloss deepens darks (about 10 to 20%), raises chroma a little and smooths the surface glints; matte flattens the picture and lifts the darks slightly.
- Then `sign`, which is the very last act.

**Order of work.** Toned ground (or a transparent earth glaze; wipe lights out with the `rag` while it is wet). Lean block-in with big flats (`"fat": 0.3`). Then colour wet-in-wet or layer by layer, each layer as fat as the last or fatter. Thin darks, thick lights (raise `impasto` and use the `knife` or `bright` for the last lights). Glazes once the paint below is dry. Then `dry 1`, `retouch` if passages sank in, and `varnish`.

**Limits.** The paint is one colour per pixel (KM mixing in place). Only glazes are true layered films, and the paint underneath is not tracked layer by layer: "the layer beneath" is the last state that was touch-dry. The fat-over-lean rule is reported, never enforced: nothing cracks. There is no flow, levelling or sagging of very wet paint, and no yellowing or ageing. Brush clumps are a model of bristles, not individual hairs, so at very small sizes (under about 6 px) the marks lose their texture. Sinking-in, gloss and varnish are optical effects in the render; `col` stays the paint colour. The removal tools (rag, scraper, scraping knife) only work on wet paint, so on the gallery sheet (where the ground is dry) their rows stay empty; see `docs/gallery/oil_wipeout.jpg` for them over wet paint.
