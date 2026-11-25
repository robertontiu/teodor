# Egg tempera (`tempera`)

**What it is.** Pigment bound with egg yolk and water, painted on a smooth white gesso panel. It dries the moment it touches the panel, so nothing blends wet. Tone is built from many small parallel hatched strokes and thin layers, one over another. Every stroke is a thin translucent film (a Kubelka-Munk layer) over what is already there. Light colours are more opaque, since they carry lead white, while dark earths and glazes are translucent. So a warm flesh hatched over a green underlayer (verdaccio) lets the green show through as cool shadow. Edges are crisp and the surface has a satin sheen. Where gold leaf is laid, the panel reads as metal: you can see the leaf squares, burnished areas reflect, and punchwork catches the light. Code: `studio/v8/media/opaque.py`, class `Tempera`.

**Supports.**
- `gesso_panel` (default): a wooden panel with gesso sanded smooth. It is brilliant white, unless the ground you give to `new` is a tone (an imprimatura). Its only texture is faint sanding marks.
- `gold_ground`: the whole panel is water-gilt (gold leaf on bole, burnished). Leave it bare where the gold should stay. Paint over it elsewhere; opaque light colours need several passes to hide the gold, as they would in reality.

**Tools** (`"brush": ...`):
- `hatch` (default, so `match` and `free` hatch unless told otherwise): a small fine round that lays short parallel strokes. The path is the hand travelling across the passage. Every couple of line widths it lays one short line across the path. Each line lands a little blunt and flicks off thin. `size` is the length of each line. One pass leaves visible strokes on the panel, and tone deepens with each pass. Parameters:
  - `hatch_angle` (degrees to the path, default 75)
  - `hand` (0 to 1, default 0.5): how much the lines lean toward the painter's own natural slant.
  - `hand_angle` (default -60): that natural slant.
  - `cross: true`: every other line is crossed at 55 degrees.
  - `line`: line width in pixels (default about 9% of size, at least 1.3).
  - `film`: thickness per line (default 0.55).
  - `opacity_paint`: overrides the automatic opacity.
  - Pressure packs lines closer; speed makes them longer, sloppier and broken.
- `round`: a small soft round used nearly dry. It lays a continuous thin film with crisp edges. One pass is translucent, and repeated passes build up toward the colour. Use it for flat areas such as skies and robes, and for underlayers. `film` defaults to 0.55.
- `liner`: a fine pointed round for contours, hair, and painted "gold" details in lead-tin yellow. Its film is thicker (0.8).
- `gilding`: lays gold leaf along the stroke as opaque metal with a slightly ragged edge. It is burnished to `burnish` (default 0.75). Gild before painting, as painters did: paint laid over gold dims it.
- `blend` (used by the `blend` intention): tempera cannot blend. Instead it cross-hatches short lines in the tone sampled from the area, which is how tempera painters bridge two values.
- Other names: `small_round` → round, `detail_round` and `stylus` → liner, `gild` → gilding.

**Intentions.**
- `match` with `hatch` builds the schema up gradually. Expect three or more passes at falling sizes (for example 22 to 34, then 10 to 16) before a region reaches its value. Use `clip: true` with a region to keep hatching off the gold. A 1200x1600 panel takes about 6 to 8 seconds per 400-stroke pass.
- `match` with `round` (size 20 to 30) is a quick way to lay flat underlayers.
- `glaze` lays a thin translucent tempera layer (little white, more water). Use it for verdaccio (green earth, for example `#6b7650`) under flesh, and for tinting skies and grounds.
- Felt state: careful hatching stays parallel and even; agitated hatching gets longer, looser and broken.

**Order of work** (after Cennini): drawing (`transfer`); `gilding` and `finish punch` while the gold is bare; thin underlayers and background (`glaze`, `round`); `glaze` verdaccio under the flesh; then flesh and forms hatched in several premixed values, from dark to light; fine accents last. Optionally finish with `oil-glaze` on robes, then `hatch-lights` to restore the highlights it sank.

**Drying and time.** Paint dries instantly, so `dry` and the time between episodes change nothing. Every stroke dries before the next one lands.

**Finishing:**
- `finish hatch-lights '{"region": {...}, "color": "#f3ead6", "count": 120, "size": 14}'`: the final hatching of highlights. It finds the local lights in the region and lays small groups of light, opaque strokes that start in the light and flick off toward the shadow.
- `finish oil-glaze '{"color": "#7a2a1a", "opacity": 0.3, "region": {...}}'`: a transparent oil glaze. It deepens and saturates the area, sinks the tempera highlights beneath it, and makes that area glossier. Follow it with `hatch-lights`.
- `finish punch '{"pattern": "border", "radius": 3, "spacing": 10}'`: punchwork in the gold. `border` lays rows of ring punches just inside every edge of the leaf (halo rims, frame borders); `rows` gives their distances from the edge. `rosette` adds scattered six-petal rosettes. `stipple` makes a granular field of small dots (`density`, default 0.01). Punches only show where the gold is not painted over. They are meant to be made before painting.
- `finish burnish '{"region": {...}, "amount": 1.0}'`: burnish the leaf (everywhere if no region is given) for a brighter, more mirror-like gold.
- `finish sheen '{"amount": 0.35}'`: sets the satin sheen of the whole surface. There is no varnish by default.

**Limits.**
- Gold is drawn for one fixed light: burnish shows as a soft, steady play of light and dark, not as a reflection that changes when you move.
- There is no mordant gilding, no sgraffito (scratching paint off the gold) and no incised stylus line.
- Paint over gold dims it gradually rather than flaking.
- Hatch lines are straight, not curved.
- `hatch-lights` chooses its lights from the current painting, so give it a region on the forms you mean. On a white panel it otherwise also picks gaps of bare gesso.
- The core `sign` command signs the same way as in oil.
