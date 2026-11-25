# Ink

**Medium id:** `ink` · module `studio/v8/media/ink.py` · mark sheets in `docs/gallery/ink_<support>.jpg`

Two traditions in one medium. One is East Asian ink and brush (Chinese *shuimo*, Japanese *sumi-e*): soot ink ground with water and painted with a soft pointed brush on absorbent paper. The other is Western pen and ink with washes. Ink is a carbon film: every stroke darkens the paper, strokes layer over each other, and nothing covers or corrects. A mark, once made, stays. Plan light to dark.

## Supports

| id | what it is | how ink behaves |
|---|---|---|
| `xuan_raw` (default) | raw, unsized xuan rice paper | wet ink bleeds and feathers along the fibres into a pale, fibrous halo with a slightly darker front; strokes into still-damp ink fuse; dry strokes stay crisp |
| `xuan_sized` | sized ("cooked") xuan, for fine-line *gongbi* | ink sits where it lands: crisp lines, a little softness, a darker rim on very wet strokes |
| `silk` | sized silk, warm tone, fine weave | like sized xuan, slightly less bleed |
| `bristol` | smooth hard drawing board | for pen: no bleed, crisp lines; wet washes dry with a faint darker edge |
| `laid_paper` | laid paper with laid and chain lines | slight bleed, a little grit that breaks pen and dry-brush lines |

The ground colour given to `new` is the paper's tone (for example `#f3eee2` for xuan, `#fbfaf6` for bristol).

## Tones and colour

Ink tone is set by dilution, not by mixing. Give it with `"tone"`:
`jiao` (scorched, the darkest and driest), `nong` (thick), `zhong` (medium), `dan` (light), `qing` (clear, the palest), or a number from 0 (palest) to 1 (darkest).
Without `tone`, the lightness of the colour you pass sets the tone: `#000000` is scorched ink, `#555555` is about medium, `#bbbbbb` is light. Thicker ink carries less water. That means more flying white and less bleeding. Paler ink is wetter, so it bleeds more.

**Colour:** a grey or black colour is plain ink. A coloured one (indigo, ochre, rattan yellow, cinnabar, malachite) becomes a light, transparent plant or mineral colour, darkened with ink if needed to reach the colour's value. Colours stay a little muted (`"chroma"`, default 0.85). A colour lighter than the paper is painted as a semi-opaque mineral white or pastel. Use `"ink_only": true` to turn every colour into its grey ink tone.
**Ink kind** (`"ink"`): `pine` (default: pine-soot ink, which dilutes to a cool grey), `oil` and `carbon` (neutral), and the Western drawing inks `iron_gall`, `sepia` and `bistre` (browns).

## Tools (`"brush"`)

- `brush`: the Chinese brush, held upright (centre tip). It is loaded with dark ink at the tip and lighter, wetter ink in the belly, so one stroke holds several tones: a dark core with paler edges. A light touch marks with the tip only (thin and dark). Pressing spreads the belly, so the line swells. Each hair carries its own ink. As hairs run dry, or when the stroke is fast (high arousal), they separate and leave streaks of bare paper (*flying white*, feibai). Slow starts and ends release more water, which bleeds into a small pool on raw xuan. Options: `belly` (belly tone relative to the tip, default 0.34), `loading: "even"` (no tip/belly difference), `water` (0..1.25), `load` (how long before the brush runs dry). `liner` gives the same brush with the core's long taper.
- `brush_side`: the side brush, held oblique. It makes a broad stroke with a sharp dark edge on the tip side and a ragged, pale, broken edge on the belly side, with lots of dry-brush texture. Use it for rocks, tree bark and texture strokes (*cun*).
- `splash`: splashed ink (*pomo*). It lays wet, irregular pools whose tone wanders from pale to dark. They fuse into each other and bleed, with a few stray droplets. Use it for mist, mountains in rain and dense foliage.
- `wash`: a soft wash brush. It lays even, wet, diluted ink (or a light colour) with soft edges and a slight mottle.
- `pen`: a dip pen. The default `nib: "flex"` is a flexible steel nib: the line swells with pressure and on down-strokes, the nib runs dry over long lines, and there is an occasional blot at a slow start (`blots`, default 0.12). `nib: "tech"` (or `pen_tech`) gives an even technical line. `nib: "reed"` (or `pen_reed`) gives a broad, gritty reed pen whose width depends on direction (`nib_angle`, default 35 degrees).
- `hatch`: pen hatching. Each stroke lays a band of parallel pen lines across its path. The band width is `band` × size, the spacing gets tighter with pressure (`spacing` to fix it), and `hatch_angle` defaults to -55 degrees. Pressing hard, or `cross: true`, adds a second family at 90 degrees (cross-hatching).
- `water`: a clean wet brush. It fuses and softens ink that is still damp and does nothing to dry ink, because carbon ink is permanent. The `blend` intention uses this.
- `pencil`: a light graphite construction line for pen-and-ink work. `finish erase-pencil` removes it later.

Oil brush names are accepted and mapped: `round`, `filbert` and `liner` go to `brush`; `flat` and `fan` to `brush_side`; `blend` and `smudge` to `water`.

## Intentions

- `strokes` and `free` are the natural intentions for ink: deliberate brush or pen strokes, or a number of loose strokes in a region. Pressure (`pressure`) sets the width. The felt state matters: arousal makes strokes faster and drier (more flying white), care makes them slower and wetter (more pooling and bleed).
- `match` works and is fast enough (a few hundred strokes on 1200×1600 take about 15 s). But matching lays many short strokes, which is not how ink is painted. Use it with `wash` at large sizes for the broad tonal masses. Draw the lines and accents with `strokes`.
- `glaze` is an ink wash laid flat over a region: the colour gives the tone (or a light colour), and `opacity` scales it. On raw xuan its edge feathers and the tone mottles slightly. On sized paper and bristol its edge darkens a little.
- Over **dry** ink, every new layer adds: the overlap shows darker. Into **wet** ink, the same ink mostly re-wets what is there, so repeated strokes of one tone build up slowly instead of doubling. Fibres saturate at about scorched-ink density.

## Drying and time

Water sinks into raw xuan fast: about 70% of the dampness is gone after each episode. Sized paper, silk and bristol stay damp longer. Strokes in the same episode are laid wet-in-wet and fuse. `dry 1` makes everything dry, so later strokes sit on top as separate layers. Nothing ever lifts: ink is permanent once laid, except by scraping.

## Finishing (`finish <op> '<json>'`)

- `dots`: the last dark accents (moss dots, eyes): short upright dabs of scorched ink. Give `{"pts": [[x, y], ...]}` or `{"region": {...}, "count": n}`, plus optional `size`, `tone` and `angle`. At most 40 (`max`); it refuses more, because accents are few.
- `seal`: stamps the red cinnabar seal with an uneven, printed impression. `text` (default `"TEO\nDOR"`), `at` (`br`, `bl`, `tr`, `tl` or `[x, y]`), `size`, `style` (`baiwen`: white characters cut out of red, the default; `zhuwen`: red characters and border), `color`. The seal goes with or instead of `sign`.
- `erase-pencil`: removes the `pencil` construction lines wherever ink does not cover them.
- `scrape`: scrapes ink off for a highlight: `{"region": {...}, "amount": 0.5}`. It is uneven and greyish, like real scraping.
- `mount`: presentation only. Renders (looks, frames, the time-lapse) show the work mounted as a hanging `scroll` (default), an `album` leaf or a `mat`, with `color` for the silk. The painting itself is unchanged.

There is no varnish or fixative for ink.

## Limits

- The bleeding is a simplified flow on a half- or third-resolution grid. Feathering follows a fibre map and pins at the front, but it is not a full lattice-Boltzmann (MoXi) simulation, and very wide splashes on raw paper are approximate.
- A stroke's ink spreads when the stroke ends (when the next stroke starts or the episode ends). If a `match` runs right after another intention in the same episode, it does not yet see the last stroke of that intention.
- The `transfer` command and `sign` write into the picture directly, not as ink or pencil. Use `pencil` strokes for an erasable under-drawing and `finish seal` for an ink-painting signature.
- Colours are a few light, transparent films, not a full pigment palette. Heavy colour belongs in watercolour or gouache.
