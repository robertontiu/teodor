# The studio manual (studio v8)

This is the painter's reference to the studio: how a canvas is made, how the hand works, how to look, how to measure and how to finish. Each medium has its own page in [`docs/manual/`](manual/) with its tools, supports, behaviour and finishing steps. The current is configured in [`studio/styles.json`](../studio/styles.json) and described in [`docs/styles/`](styles/).

Run every command as `python3 <workdir>/studio.py <command>` from anywhere; `CANVAS=<name>` selects a canvas (default `main`). Files are written next to `studio.py` as `<canvas>_*`.

## The canvas

```
new "#RRGGBB" [W H] [--medium M] [--support S] [--style ID] [--px-per-mm N]
```
Starts a canvas (default 1200x1600 px, oil on canvas) toned to the colour given (the ground: white paper for watercolour, a toned imprimatura for oil, a mid-tone paper for pastel). `--style` records the current, so `report` knows which target to compare with. `new` clears the schema, so make the canvas first.

`--px-per-mm` sets the sheet's scale (written to `<canvas>_meta.json` before the medium sets up): media that work in millimetres read it (ink: a drawing for process at about 6 px/mm, a plate at 10, engraving at 16; see the medium's page).

`media` lists every medium with its tools, supports and finishing steps.

## The schema (your drawing)

- `ref <file.svg|file.png>`: set or revise the schema the painting is matched against (rendered to canvas size).
- `scene <scene.json> [overlay.svg] [draft|final]`: render a 3D blockout as the schema, with people built to human proportions, plane-built heads with expressions, articulated hands, drapery in wind, and element masks for `elements`/`report` (see "Scene blockouts" below). For flat styles, an SVG schema is still the better drawing.
- `transfer [strength] [#color]`: lay the schema's contours on the canvas as a light drawing, once, early (recorded as the `drawing` role).
- `focus FX FY`: declare the focal point (canvas pixels). `simplify` declares it too, and an episode can carry `"focus": [x, y]`. Stroke size, `report`'s focal checks and the role checks use it.
- `elements [file.json]`: declare the picture's elements (`{"elements": [{"name": "figure", "region": {...}}, ...]}`) for the clarity check in `report`; with no file it lists them. One element at a time: the intention `{"type": "element", "name", "region"}`. Use tight regions (a polygon around the figure, not a loose box): the surround is measured just outside the outline.

**Translate the schema, don't copy it.** A painter groups the values into a few masses, keeps full detail and the hardest edges at the focal point, and simplifies everywhere else. `simplify FX FY [groups] [radius]` does that to the current schema around a focal point (FX, FY in canvas pixels; groups 3-5; radius as a fraction of the diagonal, default 0.25) and sets the result as a new schema version. Use `faithful` below 1 away from the focus too.

### Scene blockouts

A scene is a JSON file: `camera`, `sun`, `sky`, `ambient`, `fog`, `ground`, `lights`, `exposure`, `wind`, `render_scale`, `masks` and `objects`. Units are meters, y is up. Read `docs/subjects/figure.md`, `face.md` and `hands-feet.md` before you pose anyone. Example scenes: `docs/gallery/figures_*.json`.

- **camera:** `pos`, `look_at`, `fov` (degrees), `roll` (degrees, tilts the picture), `up` (a hint). Looking straight down or up works (the top of the picture is then -z): `{"pos": [0, 2.6, 0], "look_at": [0, 0, 0]}` is an overhead view; a camera near the ground looking up is a worm's-eye view.
- **wind:** a vector in m/s, e.g. `[0, 0, -16]` for a gale blowing toward -z. Drapery and long hair stream with it.
- **render_scale:** multiplies the render resolution (draft 300x400, final 450x600). Faces and hands need 1.3-2 when they are small in the frame; time grows with its square (a full figure with a dress and shawl at 1.3: about 5-15 minutes on 2 vCPU).
- **objects:** `box`, `sphere`, `ellipsoid`, `capsule`, `cylinder`, `house`, `fence`, `tree`, the old `figure` mannequin (kept for old scenes), and:

**`person`** (one human):
- who: `age` (years), `sex` (`female`/`male`), `build` (`slim`, `average`, `heavy`, `muscular`, `frail`), optional `height` (m). Proportions follow the age canon (4 heads at birth, about 6 at five, 7.5 for adults), with a stoop and a forward head after 55.
- where: `pos`, `facing` (degrees about y), `anchor`: `ground` (the lowest point touches the ground; add `"float": true` to lift it by `pos[1]`, e.g. standing on a wall), `pelvis`, `chest` or `head` (that point goes to `pos`: use `head` for a swimmer or a portrait). `lie`: `back`, `front`, `left`, `right`; or `pitch`/`roll` in degrees.
- pose: `pose` is a preset or a list of presets: `stand`, `contrapposto`, `walk`, `lean_wind`, `arms_wide`, `reach`, `throw`, `throw_release`, `hand_on_head`, `kneel`, `kneel_up`, `sit`, `sit_ground`, `lie_back`, `lie_side`, `sleep_back`, `tread_water`, `slumped`, `bowed`, `look_up`. `joints` overrides any joint, in degrees: `spine`, `neck`, `head` [forward, side to the left, twist to the left]; `pelvis` [tilt, hip hike, twist]; `arm_l`/`arm_r` [forward, out, twist, elbow]; `wrist_l`/`wrist_r` [flex, deviation, pronation]; `leg_l`/`leg_r` [forward, out, twist, knee]; `ankle_l`/`ankle_r` [dorsiflex]; `shoulder_l`/`shoulder_r` [raise, forward] (in head units); `lean` [forward, side] tilts the whole body about the feet (into a wind).
- reaching: `reach_l`/`reach_r` put the palm on a target by inverse kinematics: `{"target": [x, y, z] | "head_top" | "head_back" | "forehead" | "nape" | "chest" | "belly" | "hip_l" | "hip_r" | "knee_l" | "knee_r" | "cheek_l" | "cheek_r", "offset": [..], "palm": [direction the palm faces], "fingers": [direction the fingers point], "pole": [where the elbow goes], "hand": preset}`. A hand on a cat: the cat's top as target, `"palm": [0, -1, 0]`.
- hands: `hand_l`/`hand_r` = `open`, `spread`, `relaxed`, `rest`, `hold`, `grip`, `push_hair`, `throw`, `point`, `cup`, `fist`, or your own `{"f": [[mcp, pip, dip] x 4 fingers], "spread": deg, "thumb": [out, palmar, opposition, mcp, ip], "wrist": [flex, dev]}`.
- face: `expression` = `neutral`, `calm`, `smile`, `laugh`, `gasp`, `surprise`, `fear`, `scream`, `sorrow`, `sleep`, `anger`, `disgust`, or `{"preset": "laugh", "au": {"6": 0.6, "4": 0.3}}` with FACS action units 1, 2, 4, 5, 6, 7, 9, 10, 12, 15, 17, 20, 23, 25, 26, 27, 41, 43 (0-1; `docs/subjects/face.md` has the table and how a laugh differs from a scream). `gaze` [yaw, pitch] turns the eyes. `planes` (0-1, default 0.45) simplifies the head into big planes and groups its light into light, two halftones and shadow, the way a painter blocks in a head; 0 is the smooth form.
- surface: `skin`, `color` (fitted clothing), `bare` (parts in skin: `torso`, `arms`, `legs`, `feet`), `shoes`, `lips`, `skin_gloss` (wet skin), `hair`: `{"style": "short" | "bun" | "long" | "ponytail" | "slick" | "receding" | "bald", "color", "length", "gloss"}`.
- `clothes`: a list of `{"kind": "dress", "color", "length" (0-1 of the legs), "flare", "drag", "folds"}`, `{"kind": "shawl", "color", "length" (m), "width", "drag"}`, `{"kind": "shirt", "color", "sleeves": "long" | "short" | "none", "ease", "billow", "length"}`, `{"kind": "trousers", "color", "length": "long" | "short"}`. The dress is simulated cloth hanging from the waist (it presses onto the legs on the windward side and streams on the other); the shawl's ends are simulated in the wind; the shirt billows on the leeward side.

**`hand`** (a lone hand for studies): `pos` (the wrist), `preset`, `fingers`, `palm`, `side` (`l`/`r`), `length` (m).
**`animal`**: a cat, `pose` `curled` (asleep), `sit` or `lie`, `pos`, `facing`, `size`, `color`.
**`water`**: a surface at height `y` with `color`, `chop`, `ripples` (a list of [x, z] centres), `ripple_amp`, `gloss`. It hides what is under it, so a swimmer's body ends at the waterline.

**Element masks.** Every `scene` render also writes `<canvas>_elements.npz` and `<canvas>_elements.json` next to the canvas (outside the studio: `<image>_elements.*`; turn off with `"masks": false`). The npz holds one boolean mask (canvas height x width) per visible element, keyed `<object>.<element>`: a person's `head`, `neck`, `torso`, `arms`, `hands`, `legs`, `feet`, `hair`, `drapery`, and `<object>.all`; `animal`, `water`; other objects as `<object>.object` (the old `figure` as `torso` and `skin`). Objects are named by their `id`, or `<type><n>`. Masks cover only what is visible from the camera. The JSON index (`"format": "teodor-elements/1"`) lists for each key: `object`, `type`, `element`, `pixels`, `share` of the canvas, `bbox` [x0, y0, x1, y1], `centroid` [x, y] and `depth_m` (median distance from the camera). Use them for `elements` regions, for `clip` regions around a face or a hand, and for checking that the focal element is where you meant it.

**Study sheets:** `python3 figure_sheet.py expressions out.jpg [sex] [age] [planes]` and `python3 figure_sheet.py hands out.jpg` render every expression and hand preset (`docs/gallery/figures_sheet.jpg`).

**What the blockout still can't do** (paint these from knowledge, not from the render): faces are generic and read best from the front or three-quarter; small heads (under about 60 px tall in the render) lose their features, so raise `render_scale` or crop closer; cloth is a coarse simulation (pipe folds, no fine creases, a skirt can bell rather than stream); fingers can pass through objects they touch; feet are simple wedges.

## The hand: episodes and intentions

```
act '{"felt": {...}, "do": [up to 4 intentions]}'      or      act @episode.json
```
One episode is up to four intentions, then you look. Long stroke lists go in a JSON file (`act @file`), because the shell limits argument length.

**Felt state** (`arousal` 0-1, `tension` 0-1, `valence` -1..1, `care` 0-1) drives the hand's movement: arousal makes faster, longer strokes that break into dry-brush; tension makes tremor, jagged corners and pressure spikes; valence makes curves smooth (warm) or angular (dark); care makes placement steadier with a slight hesitation at the start. Every stroke follows a human speed profile (accelerate, cruise, slow down), which viewers read as a hand (docs/research/emotion.md).

**The hand (v8).** A stroke is not one dab repeated. Pressure, width, load and dry-brush change along every stroke, and a slow pressure wave runs through it. Size, pressure, load, angle, colour and edge **drift** across a passage, so neighbouring strokes vary together instead of jittering one by one (correlated variation, as Hennig et al. 2011 found listeners prefer in human timing; docs/research/process.md 1.8). Strokes are smaller near the declared focus and broader away from it (×0.65 at the focus to ×1.35 at 0.4 of the diagonal), and smaller or broader by role (lay-ins broad, accents and lines small). `"focus_scale": false` and `"role_scale": false` switch that off for an intention. These numbers are judgements tuned by eye; the before/after measurements are in docs/proposals-v8.md.

**Articulations** (`"articulation"` on `match`, `free`, `model`, `strokes`, or on one stroke of `strokes`; default `auto`):
- `drag`: a loaded stroke dragged until the paint runs out: lighter, narrower and breaking into dry-brush toward its end.
- `swell`: the calligraphic stroke: it lands on the tip, presses into the belly and lifts to a point.
- `scumble`: a thin, half-loaded, scrubbed layer that breaks over what is beneath (the National Gallery's definition: a thin layer lighter than the colour under it; a glaze is darker).
- `flick`: fast, full at the start, lifting off to a point.
- `plain`: the v7 stroke (constant intent, landing and lift only).
- `auto`: each stroke picks from a mix that suits its role (body: swell, drag and plain; dead colour: mostly drag; accents: swell and flick), drifting across the passage so neighbouring strokes share it.
Without `edge`, each stroke's edge also comes from its role (body strokes mix soft, hard and lost; accents are hard; scumbles lost).

**Intentions** (the `brush` is any tool of the canvas's medium; see `media` or the medium's page). Every intention may carry `"role"` (see "Layers with roles"):
- `match`: strokes toward the schema where the canvas differs most, following the form and stopping at its edges. `size` [min,max], `threshold` (lower = more coverage), `faithful` 0-1, `colors` (mixed in by 1-faithful), `color_shift` {`temp`, `sat`, `value`} (**multipliers**: `value` 0.9 darkens 10%; 0 turns black), `region`, `clip`, `max_strokes`, `adaptive` (small strokes where the drawing is detailed), `edge` hard|soft|lost, `pressure`, `load`, `articulation`. Direction: `follow` `form` (default: along the form, from the schema's structure; where the schema is flat the strokes continue the nearest form or follow a slow flow around one angle, never all one angle), `across` (cross-contour, wrapping around the form) or `direction` (use `direction` everywhere). `direction` {`angle`, `spread`} also sets the flow angle in flat passages. Strokes leave the form direction by a drifting angle of up to about 20°, so passages cross instead of stacking.
- `model`: model a form from a value schema. The `region`'s values (the schema's, or a value image `"values": "file.png"`) are cut into `steps` bands (default 4) and painted band by band, dark to light (`"order": "light_to_dark"` for watercolour), each band's strokes following the form's direction (`follow` `form` or `across`). Colours come from a ramp `colors` (dark to light) or from the schema. `size`, `length`, `density`, `max_strokes`, `articulation`, `clip` (default on). Use it for heads, hands, drapery and every rounded form, after a tonal study set as the schema.
- `free`: gestural strokes in a region. `colors` (with weights), `count`, `size`, `length` **as a range [min,max]**, `direction` ({`angle`,`spread`}, {`around`:[x,y]}, {`toward`}, {`away`}, {`field`:true}), `curve`, `pressure`, `load`, `edge`, `articulation`.
- `strokes`: exact marks: `strokes: [{"pts": [[x,y],...], "size", "color", "pressure", "articulation"}]`.
- `hatch`: tone built from lines, the way a draughtsman or tempera painter does: parallel strokes at `angle` with `spacing` across a `region`, in `layers` (value levels, default [0.75, 0.55, 0.35, 0.18]): each layer covers only where the schema (or a flat `value` 0-1) is darker than its level, turned by `cross` degrees (default 45), so darker passages get denser cross-hatching. `size`, `colors`, `length` (longest line segment), `pressure`, `max_strokes`. Lines follow the hand; spacing and angle drift slightly, and each line starts its pieces at its own offset so piece ends never line up. The defaults are coarse: use the measured settings in each medium's manual page (e.g. graphite 0.8-2 mm spacing). Pass `colors` with monochrome tools (the default #2a2a2a presses as hard as the tool can) and set `layers` below the paper's value on toned paper. Works with any medium (pencil, pen, tempera hatch brush, charcoal tip). Two systems for engraving and pen work: `"regular": true` rules the lines (no spacing or angle jitter, long unbroken lines, broken only where the region or the value level ends, a steady hand); `"follow": "form"` lays contour hatching, evenly spaced lines that follow the schema's form (the same direction field as `match`), each value layer turned by `cross` degrees from the form (`angle` turns the first; `length` caps a line). `max_strokes` defaults to 20000 lines (enough for a full engraved sheet at 16 px/mm), so a hatch no longer stops part-way across the sheet.
- `blend`: soften (where the medium allows it; not in tempera or prints).
- `glaze`: the medium's thin layer over a region: an oil glaze, a watercolour wash, an ink wash, a pastel veil, a printed flat block. `color`, `opacity`, `region`, `feather`.
- **Revision: taking paint away** (painters revise on the canvas, very often by removal: docs/research/process.md 2.6). Each needs a `region`; `strength` 0-1 (default about 0.7), `angle` of the sweep, `passes`, `size`, `feather`; edges are broken by hand (`"ragged": false` for a clean edge). The medium decides what each means:
  - `scrape`: scrape back. Oil: the palette knife scrapes wet paint toward the layer beneath, and on dry paint the blade shaves the impasto and bares the ground on the tops of the weave. Watercolour: a blade takes paint off the paper's peaks. Gouache: back to the paper. Tempera: back to the gesso or the gold. Charcoal and graphite: the hard eraser; pastel: the scraper. Ink: its scraped-highlight step (`finish scrape`).
  - `wipe`: wipe out. Oil: the rag lifts wet paint (it warns when the passage is dry: scrape it instead). Watercolour: blotting and lifting (wet pigment comes up most, staining pigments least). Gouache: a damp brush re-dissolves it. Charcoal, graphite, pastel: the kneaded eraser. Tempera can't be wiped (it dries at once). Ink has no wipe of its own yet and falls back to the default.
  - `paintout`: paint a passage out with the colour its surroundings would have there (a blur of the colour around it), in the medium's broad brush (`brush`, `color` to choose). Watercolour lifts the passage first and then washes it, because it can't cover.
  - Woodblock refuses all three with the reason: a print can't be taken back; recarve and print the block again. Media without their own way fall back to pulling the colour back toward the ground.
- Regions: `{"type":"canvas"}`, `{"type":"rect","x","y","w","h"}`, `{"type":"ellipse","cx","cy","rx","ry"}`, `{"type":"poly","pts":[[x,y],...]}`.

`dry [0-1]` lets time pass (what that means depends on the medium: oil gets tacky, a wash dries and its edges darken).

## Layers with roles

A passage in a real painting is several layers that each do a job (docs/research/process.md; docs/FINISHING.md; each current's process in docs/styles/). The studio records, per pixel, which roles built it (`<canvas>_roles.npy`, with the order of first use per 8 px cell in `<canvas>_rolefirst.npy`). The roles:

| Role | What it is |
|---|---|
| `underpainting` | the imprimatura, the monochrome lay-in, the abbozzo or verdaccio (aliases: imprimatura, ebauche, grisaille, verdaccio) |
| `drawing` | the underdrawing, the transfer, the first lines on bare ground |
| `dead_colour` | the first colour lay-in over the ground or underpainting (Dutch dead colouring, the academy's ébauche in colour) |
| `body` | body colour: the opaque working up, impasto (alias: impasto) |
| `glaze` | a transparent darker film over dry paint |
| `scumble` | a thin broken lighter layer over what is beneath |
| `wash` | a watercolour or ink wash |
| `hatch` | tone built from lines |
| `accent` | the last few touches: the darkest darks, the brightest lights, highlights |
| `contour` | lines restated over the colour at the end (a key line, dark contours) |
| `correction` | scraping, wiping, painting out, lifting, erasing |

Tag each intention with `"role"`; without it the studio infers one: `glaze` → glaze (wash in watercolour and ink, body in woodblock), `hatch` → hatch, revision tools and rags, lifts and erasers → correction, `articulation: scumble` or a starved brush → scumble, liners on bare ground → drawing and over paint → contour (dark) or accent, a few small `strokes` → accent, the first colour over bare ground → underpainting (one or two colours of one muted hue) or dead colour (charcoal, graphite and ink: drawing; watercolour: wash), later colour → body. Each current in `studio/styles.json` has a `layer_order` from its research doc, and `report` checks the canvas against it.

## Looking

`look <view>` writes `<canvas>_look.png`; `<canvas>_view.png` (half size) updates after every act.

| View | What it is for |
|---|---|
| `full` | the whole canvas at half size |
| `thumb` | a tiny blurred version: does it read at a glance and across the room? |
| `squint` | the masses only: the old trick of half-closing the eyes |
| `gray` | values only, in 8 steps |
| `notan [2\|3]` | the canvas split into 2 or 3 value groups: is the light/dark design strong? |
| `edges` | where the edges are and how hard: is the hierarchy planned (hardest at the focus)? |
| `temp` | warm and cool: does temperature do work, or is it all one temperature? |
| `mirror` | flipped left-right: a fresh eye for the drawing and the balance |
| `upside` | rotated 180°: the design as shapes, not things |
| `layers [ROLE]` | the role map: each pixel in the colour of its latest role in the usual order of work, brighter where more roles built it, with a legend; prints each role's share, how much of the canvas has one, two or three roles, and the number of passes. `layers body` (any role) shows where that role is and its share of the focal area. A passage built from one role reads as a filter |
| `crop X Y W H` | lean in |
| `ref`, `diff`, `compare` | the schema, where the canvas differs from it, the two side by side |

## Measuring: `report`

`report [style]` measures the canvas the way the studio measured the reference paintings of each current (`studio/targets.json`, from public-domain works in The Met's open-access collection; `tools/measure_targets.py`), and compares the two. Like Spectre's master report, it is a ruler, not a judge: read it, then decide.

- **value**: the key (mean lightness, L\* 0-100), contrast (spread), range, the shares of dark, middle and light, the *murky middle* (L\* 40-60), the notan balance, and the **value masses** as the eye counts them when squinting: the canvas is squinted (48 px on the long side), its L\* split into the best 2, 3, 4... groups, and a group counts only if it is a mass (at least 4% of the canvas with a connected piece of 2%), differs from its neighbour by about one step of a 7-step value scale (14 L\*, less in a narrow-range picture), and its boundaries are sharper than the picture's average gradient. Printed with each mass's L\* and share. (It counts 3 masses in round 16, where the old histogram measure said 2; public-domain Met oils hold 2-3.)
- **colour**: average and loudest chroma, the hue spread (0 = one hue, 1 = all hues), warm and cool shares.
- **edges**: edge density, the share of hard edges, and how many of the hard edges sit near the focal point.
- **texture**: fine detail energy and how much it varies between passages. Painters vary their marks by passage.
- **structure**: the spectral slope (steeper = smoother, flatter = more fine detail and noise), the focal point (where local contrast is strongest) and how concentrated contrast is around it.
- **marks**: orientation coherence (how strongly marks are oriented locally), direction spread (how much the stroke direction changes over the picture: 0 is all one angle), mark scale and its spread between passages, and edge variety (lost, soft, firm and hard edges all present). Flag under a direction spread of 0.25 (round 16: 0.14; Met oils 0.35-0.87).
- **layers**: each role's share, how much of the painted canvas holds one, two or three roles, the roles in the focal area, and the current's expected order. Flags: the focal area or a large region (a 3×3 grid) built from one role only (over 60% single-role pixels); roles out of the current's `layer_order` (a later role first used before an earlier one in over 15% of the cells holding both). Corrections are never ordered. Thresholds are judgements.
- **elements**: each declared element's contrast with its surround at thumbnail size (value difference, colour ΔE, the gradient along its outline) and the schema's contrast for comparison. *Masked*: contrast under 8 and a weak outline, the painting version of Spectre's masking measure: at a glance the element isn't in the picture. *Weakened*: under half the contrast the schema had. Thresholds are judgements.
- **FLAGS**: one value mass; a murky middle; even texture everywhere; hard edges not gathered at the focus; strokes at one angle; one-role passages; roles out of order; masked or weakened elements.

`report finish` adds the **finishing check** (Spectre's post-master check; docs/FINISHING.md), run after the finishing stage: the finishing steps done; signed or not; the medium's own checks (oil: still wet, sunken matte passages over 3%, uneven gloss; watercolour: final darks reached, lifted or reserved lights, masking fluid removed, dry; gouache: dry; woodblock: a seal or signature; charcoal: fixed; pastel and charcoal: how much the fixative darkened against the studio's modelled range, and the last bright touches after the fixative; ink: last dots or seal, pencil lines erased); and whether the key, contrast, hard edges and focal contrast are still in the current's range after finishing.
- **against the target**: each measure with the current's mean ± sd and whether the canvas is inside the range, and if not, which way to move.

A current without a target (Surrealism and Abstract Expressionism are still in copyright, so there is no public-domain sample) still gets the numbers and flags.

## Finishing and signing

- `finish <op> ['<json>']`: the medium's finishing steps (varnish, retouch, fixative, lift, seal, impression...; see the medium's page and docs/FINISHING.md). The finishing stage also includes painter's moves: the last few accents, an edge pass at the focus, the unifying layer the current used. Then check `mirror` and `squint` once more.
- `sign [auto|br|bl]`: sign "Teodor", the very last mark (a medium can sign in its own way: a woodblock print gets a seal).
- `timelapse`: build the time-lapse video from the recorded frames.

## Media

| Medium | Page | Supports |
|---|---|---|
| oil | [manual/oil.md](manual/oil.md) | canvas, panel |
| watercolour | [manual/watercolour.md](manual/watercolour.md) | cold_press, hot_press, rough |
| ink | [manual/ink.md](manual/ink.md) | xuan_raw, xuan_sized, silk, bristol, laid_paper, illustration_board, plate_wove, plate_laid; tools: brush, brush_side, splash, wash, pen, hatch, water, pencil, nib (`nib`: crowquill, mapping, fine, stub), stipple, burin, needle, drypoint; finishes: dots, seal, erase-pencil, scrape, mount, bite, lozenge, wipe, platemark |
| charcoal | [manual/charcoal.md](manual/charcoal.md) | drawing, toned, ingres |
| graphite | [manual/graphite.md](manual/graphite.md) | drawing, toned, ingres, bristol, vellum, plate, hot_press (the smooth papers for hyperrealism; mechanical pencils, carbon pencil, blending brush, tortillon, chamois, precision and electric erasers with `"seek"`: see the medium page) |
| pastel | [manual/pastel.md](manual/pastel.md) | toned, sanded, ingres |
| gouache | [manual/gouache.md](manual/gouache.md) | illustration_board, watercolour_paper, toned_paper |
| tempera | [manual/tempera.md](manual/tempera.md) | gesso_panel, gold_ground |
| woodblock | [manual/woodblock.md](manual/woodblock.md) | washi, coarse |
| oil-v7 | (frozen reference) | the oil of studio v7, kept only for the regression test |

Run `media` for the live list. Adding a medium: see `studio/v8/media/base.py` (the interface) and AGENTS.md.

## Engine checks (for whoever changes the studio)

- `python3 studio/v8/test_v8.py` checks that `oil-v7` still matches studio v7 bit for bit and that every medium runs every tool on every support with its finishing steps. `--only a,b` tests chosen media.
- `python3 studio/v8/gallery.py <medium> [support] [out.png]` renders a mark sheet of every tool: check new or changed tools by eye before painters use them (sheets in docs/gallery/).
