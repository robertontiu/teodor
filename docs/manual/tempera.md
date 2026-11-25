# Egg tempera (`tempera`)

**What it is.** Pigment bound with egg yolk and water, painted on a smooth white gesso panel. It dries the moment it touches the panel, so nothing blends wet. Tone is built from many small parallel hatched strokes and thin layers, one over another. Every stroke is a thin translucent film (a Kubelka-Munk layer) over what is already there. Light colours are more opaque, since they carry lead white, while dark earths and glazes are translucent. So a warm flesh hatched over a green underlayer (verdaccio) lets the green show through as cool shadow. Edges are crisp and the surface has a satin sheen. Where gold leaf is laid, the panel reads as metal: you can see the leaf squares, burnished areas reflect, and punchwork catches the light. Code: `studio/v8/media/opaque.py`, class `Tempera`.

**Supports.**
- `gesso_panel` (default): a wooden panel with gesso sanded smooth. It is brilliant white, unless the ground you give to `new` is a tone (an imprimatura). Its only texture is faint sanding marks.
- `gold_ground`: the whole panel is water-gilt (gold leaf on bole, burnished). Leave it bare where the gold should stay. Paint over it elsewhere; opaque light colours need several passes to hide the gold, as they would in reality.

**Tools** (`"brush": ...`):
- `hatch` (default, so `match` and `free` hatch unless told otherwise): a small fine round that lays short parallel strokes. The path is the hand travelling across the passage. Every couple of line widths it lays one short line across the path; each stroke of the hand sets its lines at a slightly new angle (about 11 degrees of scatter), and each line scatters a little more (about 5 degrees). Each line lands a little blunt and flicks off thin. `size` is the length of each line. One pass leaves visible strokes on the panel, and tone deepens with each pass. Parameters:
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
- `glaze` lays a thin translucent tempera layer (little white, more water). Use it for verdaccio (green earth, for example `#76744c`: the hue of green earth in egg tempera) under flesh, and for tinting skies and grounds.
- Felt state: careful hatching stays parallel and even; agitated hatching gets longer, looser and broken.

**Order of work** (after Cennini): drawing (`transfer`); `gilding` and `finish punch` while the gold is bare; thin underlayers and background (`glaze`, `round`); `glaze` verdaccio under the flesh; then flesh and forms hatched in several premixed values, from dark to light; fine accents last. Optionally finish with `oil-glaze` on robes, then `hatch-lights` to restore the highlights it sank.

**Drying and time.** Paint dries instantly, so `dry` and the time between episodes change nothing. Every stroke dries before the next one lands.

**Finishing:**
- `finish hatch-lights '{"region": {...}, "color": "#f3ead6", "count": 120, "size": 14}'`: the final hatching of highlights. It finds the local lights in the region and lays small groups of light, opaque strokes that start in the light and flick off toward the shadow.
- `finish oil-glaze '{"color": "#7a2a1a", "opacity": 0.3, "region": {...}}'`: a transparent oil glaze. It deepens and saturates the area, sinks the tempera highlights beneath it, and makes that area glossier. Follow it with `hatch-lights`.
- `finish punch '{"pattern": "border", "radius": 3, "spacing": 10}'`: punchwork in the gold. `border` lays rows of ring punches just inside every edge of the leaf (halo rims, frame borders); `rows` gives their distances from the edge. `rosette` adds scattered six-petal rosettes. `stipple` makes a granular field of small dots (`density`, default 0.01). Punches only show where the gold is not painted over. They are meant to be made before painting.
- `finish burnish '{"region": {...}, "amount": 1.0}'`: burnish the leaf (everywhere if no region is given) for a brighter, more mirror-like gold.
- `finish sheen '{"amount": 0.35}'`: sets the satin sheen of the whole surface. There is no varnish by default.
- `finish age '{"amount": 1.0, "cell": 40}'`: the look of a panel centuries old. A network of cracks in the gesso (craquelure, cells about `cell` px across) darkens paint and gold alike, and the gold is rubbed through to the red bole in places. New panels have neither; every museum photograph of a gold ground shows both.

**Calibration** (Nov 2026; report: `docs/calibration/tempera.md`). Measured against 8 Met gold-ground panels (Duccio, Daddi, Gaddi, Fra Angelico, Lorenzetti, Sassetta, Giovanni da Milano, Crivelli), automatic crops plus hand-chosen crops of hatched flesh (Duccio, Crivelli; n = 7) and of plain gold (n = 3), at full resolution and at the canvas scale of 4 px/mm.
- Set from data: the scatter of the hatch angle (`TemperaHatch.JITTER` 0.08 and `TILT` 0.2 rad) toward the orientation coherence of hatched flesh (0.65, IQR 0.62-0.75 at 4 px/mm); a dense one-direction field now measures 0.71-0.90 (before 0.76-0.96): lower still only when passes change direction, as the painter's do. Gold texture: leaf grain `LEAF_GRAIN` 3 and crack darkness `CRACK_DARK` 0.8 so that an aged gold ground (`finish age`) has the references' flat-field std L* (5.3, IQR 5.0-6.4, n = 3; rendered 4.9; new leaf 1.5, before 0.6) and orientation coherence (0.57, IQR 0.47-0.60; rendered 0.61).
- Checked against data, unchanged: hatch spacing (Crivelli flesh 0.7-1.2 mm at full resolution; rendered 0.8-1.2 mm), line width (0.33 mm, at the canvas's 1-px floor: 0.25 mm), width variation along lines (flesh CV 0.26, IQR 0.23-0.41; rendered 0.30-0.41).
- Still by eye: the opacity rule (light mixes opaque, darks translucent), film per line, the hand's slant, the gold colour and burnish, the leaf squares, punch sizes, the oil glaze, the crack pattern.
- Colours: historical pigments in egg tempera from `studio/pigments.json` (FORS masstones; hue measured, value and chroma approximate: judge them on the canvas). In Python: `media.opaque.binder_palette("egg tempera")`. madder lake `#8f3935`, ultramarine `#2c3d66`, azurite `#1e415c`, vine black `#30302e`, raw umber `#45361f`, burnt sienna `#623733`, verdigris `#0a5240`, green earth `#575643`, malachite `#477562`, red ochre `#6c3c37`, vermilion `#9e3b36`, lead white `#f1ebe0`, yellow ochre `#ac723d`, lead-tin yellow I `#e5e297`. The default verdaccio follows green earth's hue (105 degrees; it was 120); the highlight `#f3ead6` agrees with lead white (90 degrees).
- Not calibrated: hatch stroke length (an autocorrelation proxy gives 1.5 mm, IQR 1.1-2.3, in the references, but it is disturbed by crossing lines and cracks; the sizes recommended above are unchanged); flesh texture (references std L* 4.3, IQR 3.8-4.7; a three-pass hatched test 2.2-3.5, which depends on the painter's values); chroma of the gold (references 42, rendered 54: the photographed gold is aged and dirty).

**Limits.**
- Gold is drawn for one fixed light: burnish shows as a soft, steady play of light and dark, not as a reflection that changes when you move.
- There is no mordant gilding, no sgraffito (scratching paint off the gold) and no incised stylus line.
- Paint over gold dims it gradually rather than flaking.
- Hatch lines are straight, not curved.
- `hatch-lights` chooses its lights from the current painting, so give it a region on the forms you mean. On a white panel it otherwise also picks gaps of bare gesso.
- The core `sign` command signs the same way as in oil.
