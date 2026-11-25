# The studio manual (studio v8)

This is the painter's reference to the studio: how a canvas is made, how the hand works, how to look, how to measure and how to finish. Each medium has its own page in [`docs/manual/`](manual/) with its tools, supports, behaviour and finishing steps. The current is configured in [`studio/styles.json`](../studio/styles.json) and described in [`docs/styles/`](styles/).

Run every command as `python3 <workdir>/studio.py <command>` from anywhere; `CANVAS=<name>` selects a canvas (default `main`). Files are written next to `studio.py` as `<canvas>_*`.

## The canvas

```
new "#RRGGBB" [W H] [--medium M] [--support S] [--style ID]
```
Starts a canvas (default 1200x1600 px, oil on canvas) toned to the colour given (the ground: white paper for watercolour, a toned imprimatura for oil, a mid-tone paper for pastel). `--style` records the current, so `report` knows which target to compare with. `new` clears the schema, so make the canvas first.

`media` lists every medium with its tools, supports and finishing steps.

## The schema (your drawing)

- `ref <file.svg|file.png>`: set or revise the schema the painting is matched against (rendered to canvas size).
- `scene <scene.json> [overlay.svg] [draft|final]`: render a 3D blockout as the schema (see the brief for the scene format). The camera can't roll and the mannequin can't lie down: for overhead views and flat styles, use an SVG schema.
- `transfer [strength] [#color]`: lay the schema's contours on the canvas as a light drawing, once, early.

**Translate the schema, don't copy it.** A painter groups the values into a few masses, keeps full detail and the hardest edges at the focal point, and simplifies everywhere else. `simplify FX FY [groups] [radius]` does that to the current schema around a focal point (FX, FY in canvas pixels; groups 3-5; radius as a fraction of the diagonal, default 0.25) and sets the result as a new schema version. Use `faithful` below 1 away from the focus too.

## The hand: episodes and intentions

```
act '{"felt": {...}, "do": [up to 4 intentions]}'      or      act @episode.json
```
One episode is up to four intentions, then you look. Long stroke lists go in a JSON file (`act @file`), because the shell limits argument length.

**Felt state** (`arousal` 0-1, `tension` 0-1, `valence` -1..1, `care` 0-1) drives the hand's movement: arousal makes faster, longer strokes that break into dry-brush; tension makes tremor, jagged corners and pressure spikes; valence makes curves smooth (warm) or angular (dark); care makes placement steadier with a slight hesitation at the start. Every stroke follows a human speed profile (accelerate, cruise, slow down), which viewers read as a hand (docs/research/emotion.md).

**Intentions** (the `brush` is any tool of the canvas's medium; see `media` or the medium's page):
- `match`: strokes toward the schema where the canvas differs most, following the form and stopping at its edges. `size` [min,max], `threshold` (lower = more coverage), `faithful` 0-1, `colors` (mixed in by 1-faithful), `color_shift` {`temp`, `sat`, `value`} (**multipliers**: `value` 0.9 darkens 10%; 0 turns black), `region`, `clip`, `max_strokes`, `adaptive` (small strokes where the drawing is detailed), `edge` hard|soft|lost, `pressure`, `load`.
- `free`: gestural strokes in a region. `colors` (with weights), `count`, `size`, `length` **as a range [min,max]**, `direction` ({`angle`,`spread`}, {`around`:[x,y]}, {`toward`}, {`away`}, {`field`:true}), `curve`, `pressure`, `load`, `edge`.
- `strokes`: exact marks: `strokes: [{"pts": [[x,y],...], "size", "color", "pressure"}]`.
- `blend`: soften (where the medium allows it; not in tempera or prints).
- `glaze`: the medium's thin layer over a region: an oil glaze, a watercolour wash, an ink wash, a pastel veil, a printed flat block. `color`, `opacity`, `region`, `feather`.
- Regions: `{"type":"canvas"}`, `{"type":"rect","x","y","w","h"}`, `{"type":"ellipse","cx","cy","rx","ry"}`, `{"type":"poly","pts":[[x,y],...]}`.

`dry [0-1]` lets time pass (what that means depends on the medium: oil gets tacky, a wash dries and its edges darken).

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
| `layers` | how many separate passes built each part of the canvas (blue = one or none, yellow = many), with the shares printed: a passage built in one go reads as a filter |
| `crop X Y W H` | lean in |
| `ref`, `diff`, `compare` | the schema, where the canvas differs from it, the two side by side |

## Measuring: `report`

`report [style]` measures the canvas the way the studio measured the reference paintings of each current (`studio/targets.json`, from public-domain works in The Met's open-access collection; `tools/measure_targets.py`), and compares the two. Like Spectre's master report, it is a ruler, not a judge: read it, then decide.

- **value**: the key (mean lightness, L\* 0-100), contrast (spread), range, the shares of dark, middle and light, the *murky middle* (L\* 40-60), how many value groups the canvas holds, the notan balance.
- **colour**: average and loudest chroma, the hue spread (0 = one hue, 1 = all hues), warm and cool shares.
- **edges**: edge density, the share of hard edges, and how many of the hard edges sit near the focal point.
- **texture**: fine detail energy and how much it varies between passages. Painters vary their marks by passage.
- **structure**: the spectral slope (steeper = smoother, flatter = more fine detail and noise), the focal point (where local contrast is strongest) and how concentrated contrast is around it.
- **FLAGS**: one value mass; a murky middle; even texture everywhere; hard edges not gathered at the focus.
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
| watercolour | [manual/watercolour.md](manual/watercolour.md) | cold-press, hot-press, rough paper |
| ink | [manual/ink.md](manual/ink.md) | raw xuan, sized xuan or silk, smooth drawing paper |
| charcoal, graphite, pastel | [manual/drymedia.md](manual/drymedia.md) | drawing paper, toned paper, laid paper; pastel paper, sanded paper |
| gouache, egg tempera | [manual/opaque.md](manual/opaque.md) | board, paper; gesso panel, gold ground |
| woodblock | [manual/woodblock.md](manual/woodblock.md) | washi, coarse paper |
| oil-v7 | (frozen reference) | the oil of studio v7, kept only for the regression test |

Run `media` for the live list. Adding a medium: see `studio/v8/media/base.py` (the interface) and AGENTS.md.

## Engine checks (for whoever changes the studio)

- `python3 studio/v8/test_v8.py` checks that `oil-v7` still matches studio v7 bit for bit and that every medium runs every tool on every support with its finishing steps. `--only a,b` tests chosen media.
- `python3 studio/v8/gallery.py <medium> [support] [out.png]` renders a mark sheet of every tool: check new or changed tools by eye before painters use them (sheets in docs/gallery/).
