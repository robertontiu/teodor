# Ink

**Medium id:** `ink` · module `studio/v8/media/ink.py` · mark sheets in `docs/gallery/ink_<support>.jpg`, `ink_penillustration_*.jpg` and `ink_etching_*.jpg`

Three traditions in one medium. One is East Asian ink and brush (Chinese *shuimo*, Japanese *sumi-e*): soot ink ground with water and painted with a soft pointed brush on absorbent paper. The second is Western pen and ink: washes, and the steel-nib line of pen-and-ink illustration drawn for process reproduction (c. 1880-1920). The third is intaglio printmaking: the burin, the etching needle and drypoint, with the print's plate tone and platemark. Its lines are laid as if printed from a plate onto dampened paper. Ink is a carbon film: every stroke darkens the paper, strokes layer over each other, and nothing covers or corrects. A mark, once made, stays. Plan light to dark.

## Supports

| id | what it is | how ink behaves |
|---|---|---|
| `xuan_raw` (default) | raw, unsized xuan rice paper | wet ink bleeds along the fibres into a pale halo that fades outward; a microlitre of liquid wets 0.39-0.49 cm² (see Calibration); strokes into still-damp paper fuse and spread further; thick, dry strokes stay nearly crisp, with a fine fibrous fringe |
| `xuan_sized` | sized ("cooked") xuan, for fine-line *gongbi* | ink sits where it lands: crisp lines, a little softness, a darker rim on very wet strokes |
| `silk` | sized silk, warm tone, fine weave | like sized xuan, slightly less bleed |
| `bristol` | smooth hard drawing board | for pen: no bleed, crisp lines; wet washes dry with a faint darker edge |
| `laid_paper` | laid paper with laid and chain lines | slight bleed, a little grit that breaks pen and dry-brush lines |
| `illustration_board` | Bristol board for pen drawing for process reproduction | no bleed, crisp nib lines; **6 px/mm** by default (a 1200 × 1600 canvas is a 20 × 27 cm drawing) |
| `plate_laid` | dampened laid printing paper under an intaglio plate | no bleed: the plate tools print where the plate held ink; laid lines about 1 mm apart, chain lines 24 mm; **10 px/mm** by default |
| `plate_wove` | dampened wove printing paper | as `plate_laid`, an even soft surface |

The ground colour given to `new` is the paper's tone (for example `#f3eee2` for xuan, `#fbfaf6` for bristol, `#e7d9c5` for illustration board and `#e4d8c6` for plate paper: the measured median of the references as they look today). The new supports carry their own default scale. `"px_per_mm"` in `<canvas>_meta.json` still overrides it (use 16 for burin engraving, whose lines are 0.23 mm at 0.3 mm spacing).

## Tones and colour

Ink tone is set by dilution, not by mixing. Give it with `"tone"`:
`jiao` (scorched, the darkest and driest), `nong` (thick), `zhong` (medium), `dan` (light), `qing` (clear, the palest), or a number from 0 (palest) to 1 (darkest).
Without `tone`, the lightness of the colour you pass sets the tone: `#000000` is scorched ink, `#555555` is about medium, `#bbbbbb` is light. Thicker ink carries less water. That means more flying white and less bleeding. Paler ink is wetter, so it bleeds more.

**Colour:** a grey or black colour is plain ink. A coloured one (indigo, ochre, rattan yellow, cinnabar, malachite) becomes a light, transparent plant or mineral colour, darkened with ink if needed to reach the colour's value. Colours stay a little muted (`"chroma"`, default 0.85). A colour lighter than the paper is painted as a semi-opaque mineral white or pastel. Use `"ink_only": true` to turn every colour into its grey ink tone.
**Ink kind** (`"ink"`): `pine` (default: pine-soot ink, which dilutes to a cool grey), `oil` and `carbon` (neutral), the Western drawing inks `iron_gall`, `sepia` and `bistre` (browns), and three measured on the references: `india` (pen drawings, very slightly warm), `intaglio_black` and `intaglio_brown` (printing inks). The plate tools (`burin`, `needle`, `drypoint`) print one ink: the colour you pass sets only how dark the line can be (use `#000000`), and `ink` sets its colour.

## Tools (`"brush"`)

- `brush`: the Chinese brush, held upright (centre tip). It is loaded with dark ink at the tip and lighter, wetter ink in the belly, so one stroke holds several tones: a dark core with paler edges. A light touch marks with the tip only (thin and dark). Pressing spreads the belly, so the line swells. Each hair carries its own ink. As hairs run dry, or when the stroke is fast (high arousal), they separate and leave streaks of bare paper (*flying white*, feibai). Slow starts and ends release more water, which bleeds into a small pool on raw xuan. Options: `belly` (belly tone relative to the tip, default 0.34), `loading: "even"` (no tip/belly difference), `water` (0..1.25), `load` (how long before the brush runs dry). `liner` gives the same brush with the core's long taper.
- `brush_side`: the side brush, held oblique. It makes a broad stroke with a sharp dark edge on the tip side and a ragged, pale, broken edge on the belly side, with lots of dry-brush texture. Use it for rocks, tree bark and texture strokes (*cun*).
- `splash`: splashed ink (*pomo*). It lays wet, irregular pools whose tone wanders from pale to dark. They fuse into each other and bleed, with a few stray droplets. Use it for mist, mountains in rain and dense foliage.
- `wash`: a soft wash brush. It lays even, wet, diluted ink (or a light colour) with soft edges and a slight mottle.
- `pen`: a dip pen. The default `nib: "flex"` is a flexible steel nib: the line swells with pressure and on down-strokes, the nib runs dry over long lines, and there is an occasional blot at a slow start (`blots`, default 0.12). `nib: "tech"` (or `pen_tech`) gives an even technical line. `nib: "reed"` (or `pen_reed`) gives a broad, gritty reed pen whose width depends on direction (`nib_angle`, default 35 degrees).
- `hatch`: pen hatching. Each stroke lays a band of parallel pen lines across its path. The band width is `band` × size, the spacing gets tighter with pressure (`spacing` to fix it), and `hatch_angle` defaults to -55 degrees. Pressing hard, or `cross: true`, adds a second family at 90 degrees (cross-hatching).
- **Illustration pen** (`pen` with `nib`: `crowquill`, `mapping`, `fine` or `stub`; also as brush names `crowquill`, `mapping_pen`, `pen_fine`, `pen_stub`): a steel drawing nib for pen-and-ink illustration. The line is laid whole when the stroke ends and smoothed like a practised hand. Its width goes from the nib's hairline to its swell with pressure and on down-strokes (toward you), with a slow swell and thinning along the line. A fast line lifts off to a point (hatching flicks), and a slow start can blot. Widths are in mm at the drawing's scale: the crowquill draws 0.09-0.5 mm (`size` 8 is the normal line, width ∝ √(size/8)). The mapping pen has the widest range, `fine` is even, `stub` is broad.
- `stipple`: pen dots along the stroke (`dot_spacing_mm`, default 2.5 dot widths), for a stippled tone.
- `burin`: the engraver's tool. A steady, smooth cut (no tremor). It enters as a point, swells with the push and tapers out where it is lifted, and the thin tapers print greyer (a shallow cut holds less ink). With a schema the line swells where the schema is darker (`swell_with_value`, default true). `width_scale` scales it.
- `needle`: the etching needle through the ground. Even width (`needle`: `fine`, `medium` (default), `coarse`), round ends, a slight tremble. Every line is bitten `bite` minutes (default 10). A longer bite makes the line deeper, so wider (0.0025 mm per minute on each side) and darker (0.31 of the darkest ink at 3 minutes, 0.71 at 10, 0.98 at 30). Draw with a short bite and deepen the darks later with `finish bite`.
- `drypoint`: a needle scratched into the bare plate. A fine furrow with a velvety, ragged burr to one side (`burr_side`: `right` (default) or `left`), heavier with pressure.
- `water`: a clean wet brush. It fuses and softens ink that is still damp and does nothing to dry ink, because carbon ink is permanent. The `blend` intention uses this.
- `pencil`: a light graphite construction line for pen-and-ink work. `finish erase-pencil` removes it later.

Oil brush names are accepted and mapped: `round`, `filbert` and `liner` go to `brush`; `flat` and `fan` to `brush_side`; `blend` and `smudge` to `water`.

## Intentions

- `strokes` and `free` are the natural intentions for ink: deliberate brush or pen strokes, or a number of loose strokes in a region. Pressure (`pressure`) sets the width. The felt state matters: arousal makes strokes faster and drier (more flying white), care makes them slower and wetter (more pooling and bleed).
- `hatch` (the core intention) works with every pen and plate tool: give the brush (`"brush": "pen", "nib": "crowquill"`, `"brush": "burin"`, `"brush": "needle", "bite": 4`), `spacing` in px (mm × px/mm), `cross` and `layers`. The measured spacings and crossing angles are in the style docs (`docs/styles/pen-and-ink-illustration.md`, `etching-engraving.md`). Raise `max_strokes` (for example 40000) for a whole sheet: the default 1500 stops part-way.
- `match` works and is fast enough (a few hundred strokes on 1200×1600 take about 15 s). But matching lays many short strokes, which is not how ink is painted. Use it with `wash` at large sizes for the broad tonal masses. Draw the lines and accents with `strokes`.
- `glaze` is an ink wash laid flat over a region: the colour gives the tone (or a light colour), and `opacity` scales it. On raw xuan its edge feathers and the tone mottles slightly. On sized paper and bristol its edge darkens a little.
- Over **dry** ink, every new layer adds: the overlap shows darker. Into **wet** ink, the same ink mostly re-wets what is there, so repeated strokes of one tone build up slowly instead of doubling. Fibres saturate at about scorched-ink density.

**The line tools and the v8 hand.** `nib`, `stipple`, `burin`, `needle` and `drypoint` were calibrated on the plain stroke: their width in mm comes from the nib or the cut, and their swell along the line from their own measured rhythm. So with these tools `match`, `free`, `strokes` and `model` default to `"articulation": "plain"`, no role or focus size scaling and no extra pressure wave (with the v8 defaults a crowquill `match` came out 20% too narrow: 0.31 mm against 0.39). Ask for an articulation (`"swell"` for a calligraphic contour) or `"role_scale": true` and you get it.

## Revision: scrape, wipe, paintout

Ink is a carbon film in the paper's fibres, so what can be taken back depends on the support:

| | paper (xuan, silk, bristol, illustration board, laid paper) | plate supports (`plate_wove`, `plate_laid`) |
|---|---|---|
| `scrape` | a knife takes carbon off the top fibres: lighter, uneven, the fibres raised (the same as `finish scrape`) | the scraper and burnisher take the lines out of the metal: the passage prints lighter, and a later `bite` does not deepen it |
| `wipe` | blotting lifts ink that is **still wet** (water > 0): much on sized paper and board, little on raw xuan, where the ink sinks in at once. Dry ink is refused with the reason: wipe in the same episode, or scrape. | the printer wipes that passage of the plate: plate tone, cleaner in the lights (`tone`, `clean_lights`, `retroussage`, `angle`, as `finish wipe`) |
| `paintout` | **Chinese white** on bristol, illustration board and laid paper: a near-opaque matte white (`#f4f1ea` unless `color` is given) brushed over the passage, the pen draughtsman's correction over waterproof ink (Harper 1894; Maginnis 1898). It shows on the drawing; a line block reproduces it as paper. On xuan and silk it is refused: ink painting is not corrected. | refused: scrape the lines out of the metal and engrave or etch again |

## Drying and time

Water sinks into raw xuan fast: about 70% of the dampness is gone after each episode. Sized paper, silk and bristol stay damp longer. Strokes in the same episode are laid wet-in-wet and fuse. `dry 1` makes everything dry, so later strokes sit on top as separate layers. Nothing ever lifts: ink is permanent once laid, except by scraping.

## Finishing (`finish <op> '<json>'`)

- `dots`: the last dark accents (moss dots, eyes): short upright dabs of scorched ink. Give `{"pts": [[x, y], ...]}` or `{"region": {...}, "count": n}`, plus optional `size`, `tone` and `angle`. At most 40 (`max`); it refuses more, because accents are few.
- `seal`: stamps the red cinnabar seal with an uneven, printed impression. `text` (default `"TEO\nDOR"`), `at` (`br`, `bl`, `tr`, `tl` or `[x, y]`), `size`, `style` (`baiwen`: white characters cut out of red, the default; `zhuwen`: red characters and border), `color`. The seal goes with or instead of `sign`: a sealed sheet counts as signed.
- `erase-pencil`: removes the `pencil` construction lines wherever ink does not cover them.
- `scrape`: scrapes ink off for a highlight: `{"region": {...}, "amount": 0.5}`. It is uneven and greyish, like real scraping.
- `bite`: etching, a further biting stage. Every needle line inside `region` and/or where the schema is darker than `where_darker` bites `minutes` more (default 10). The rest counts as stopped out. Lines bitten in different stages keep their own depth. Lalanne's sequence: draw everything (`bite` 3-4), then for example `{"minutes": 6, "where_darker": 0.55}` and `{"minutes": 8, "where_darker": 0.33}`.
- `lozenge`: dot-and-lozenge. A burin dot in each paper lozenge left between crossed lines, inside `region`. With a schema, only where it is darker than `level` (default 0.65). `size` scales the dots.
- `platemark`: the plate's edge pressed into the paper, `margin` (share of the short side, default 0.08), `margin_mm` or `rect` [x, y, w, h]. The margin outside takes no ink and is wiped back to paper. In renders the paper inside the plate is pressed smoother, and the bevel is shaded on the top and left and lit on the bottom and right.
- `wipe`: printing. Plate tone, a thin film of ink left by wiping (`tone`, default 0.05), streaked along the wiping direction (`angle`) and wiped cleaner in the lights (`clean_lights`, 0..1, default 0.6). `retroussage` (0..1) draws ink out of the lines into a soft tint around them. Inside the platemark. A clean-wiped engraving: tone 0.02. An etching with plate tone: 0.04-0.06, retroussage 0.2-0.4.
- `mount`: presentation only. Renders (looks, frames, the time-lapse) show the work mounted as a hanging `scroll` (default), an `album` leaf or a `mat`, with `color` for the silk. The painting itself is unchanged.

There is no varnish or fixative for ink. The order for a print: `bite` stages and drypoint, then `lozenge` (engraving), `platemark`, `wipe`, `sign`.

**The finishing check** (`report finish`) depends on the tradition, read from the support:
- Chinese ink (xuan, silk): a seal or a signature, the last dark dots, no pencil showing.
- Pen illustration (bristol, illustration board, laid paper): printable as a line block. It flags grey wash over 1.5% of the sheet ("a line block prints black or nothing", Harper), more than four value groups ("have the values few and positive", Maginnis: a light, one or two half-tones, a black), hatched greys that close into black when the lines thicken by 0.04 mm in a two-thirds reduction (over 25% of them; `"reduction"` in the meta sets another scale), and pencil still showing. The thresholds and the line gain are judgements.
- Intaglio (plate papers): a platemark, the plate wiped (`finish wipe` or a `wipe` intention), and plate tone even across the plate (flagged when one part holds four times the tone of another).

## Scale, liquid and xuan type

- A canvas is a sheet at 4 px/mm: 1200 × 1600 px is 30 × 40 cm, and a brush `size` of 40 is a 10 mm footprint. `"px_per_mm"` in `<canvas>_meta.json` changes it.
- The liquid a tool lays is a film: a full film is 45 µm, 2.8 nL per pixel at 4 px/mm. On raw xuan only the liquid above what the paper under the stroke can hold spreads, so `jiao` and `nong` strokes barely bleed and `zhong` to `qing` strokes (and slow, wet ones) do.
- Raw xuan comes in three types, from Wu et al.'s measurements: `qianlong` (spreads most, 0.49 cm² per µL, smoothest front), `bamboo` (the default, 0.454) and `jingpi` (0.392, roughest front). Set `"xuan"` in `<canvas>_meta.json`.

## Calibration

Measured against ten Met ink paintings (`calibration_refs.json` group `ink_brush`) and the raw-xuan data of Wu et al. 2016. Full report: `docs/calibration/ink.md`.

From data:
- **Bleed on raw xuan** conserves volume. Liquid beyond the paper's capacity flows out until every wetted cell holds the capacity. So the wetted area is volume / capacity: 0.490 / 0.454 / 0.392 cm² per µL for Qianlong / bamboo / Jingpi xuan, as Wu et al. measured with 50 µL drops. Before, the area was 0.17-0.24 cm² per µL, the same for every paper, and it fell as the volume grew.
- **Front roughness** scales as 1/√(fibre overlaps per mm), using the measured 77 / 52 / 40. **Edge wicking** scales as √(cos contact angle), using the measured 36.8° / 50.1° / 60.6° (Washburn). Both are relative scalings. Their absolute sizes are by eye.
- **Width variation along a stroke** (`RHYTHM` 0.3, a slow swell and thinning) is set by the width CV. Calligraphy passage: 0.16 before, 0.235 after, references 0.24 (0.19-0.26). Landscape passage: 0.21 before, 0.30 after, references 0.29.
- **Flying white** is set by the share of paper showing within the strokes: 0.0016 before, 0.027 (0.019-0.047) after, references 0.03 (0.007-0.068). Hairs now dry in bundles. Speed opens streaks in a fast stroke's middle that close again as the brush slows (`SPEED_DRY`, saturating). A brush runs dry after `DRAIN` 18 brush widths of stroke. A fine line drains like a brush of at least 16 px.
- **Edges**: the tuft's edge is now about one pixel wide, and the belly's paler ink shows only at the stroke's margins (`PLATEAU` 0.55). Landscape edge rise: 1.17 mm before, 0.83 mm after, references 0.88 mm. Hard-edge share: 0.34 on raw xuan and 0.51 on sized, references 0.28 (0.16-0.42). Raw xuan is softer through its fibre fringe (`WICK_MM` 0.3, set by this share).

By eye, still uncalibrated:
- The liquid film thickness (45 µm). It decides which strokes bleed, and no measured brush release was found.
- Halo shading: soot filtering (`SOOT_STEPS`), front breakup (`FEATHER`, `ROUGH`), and how much earlier damp still fills the paper (`DAMP_FILL` 0.5).
- Hair bundles (`CLUMP`), the fine-line reservoir (`RES_MIN`), the pressure-to-width curve, the tip and belly tones, and the side brush's dryness (kept as before).
- The sized supports' slight bleed, the pens, the hatch tool and the washes on sized paper.
- **Spectrum slope** is still too smooth: -3.3 to -3.4 on raw xuan, references -2.85. It mostly reflects the size mix of the marks in a passage.
- **Orientation coherence** (0.75-0.79, references 0.58) is set by the composition, not the medium. The calligraphy passage matches the calligraphy references (0.73-0.83).

### Pen-and-ink illustration and intaglio (Nov 26, 2026)

Measured against 10 pen-and-ink illustration drawings (1875-1911), 8 burin engravings (1512-1598) and 11 etchings (c. 1667-1900) at The Met (`studio/calibration_refs.parts/`), with a new line ruler (`tools/calibrate_media.py --kind line`): equivalent line width, its CV along the line, free-end taper, spacing, crossing angle and cross-hatched share, and line density by value. Full reports: `docs/calibration/pen-and-ink-illustration.md` and `docs/calibration/etching-engraving.md`.

From data:
- Crowquill width 0.09-0.5 mm, along-line swell `PEN_RHYTHM` 0.38, lift-off `PEN_FLICK_MM` 0.7. Hatched patch: width 0.40 mm, CV 0.28, end ratio 0.70; references 0.39, 0.32, 0.76. The old flex pen: 0.44, 0.17, 0.91.
- Burin 0.18 mm with 1.0 / 1.6 mm entry and exit tapers and a 0.25 swell. Patch: 0.24 mm, CV 0.25 (crossed 0.31); engravings 0.23 mm, 0.35.
- Needle 0.17 mm plus 0.0025 mm per minute of bite on each side. Etching test: 0.38 mm, widest tenth 1.84× the median, end ratio 0.81; etchings 0.36 mm, 1.92×, 0.80.
- Ink colours (`india`, `intaglio_black`, `intaglio_brown`) and the paper tones of the new supports.
- **Area coverage.** The line tools mix inked and bare paper by area at anti-aliased edges. Laying coverage straight into Beer's law had widened every thin line by about a pixel. The older tools are unchanged.

By eye: the other nibs' widths (ordered as Maginnis 1898 ranks them), `BITE_TAU` 8 min, the needle's tremble, the burr, plate tone, retroussage, the platemark bevel, the lozenge sizes.

Still short: the core `hatch` is a draughtsman's hatching (jittered spacing, one direction per layer), so engravings' regular, form-following systems are not reached (test: 2.9 lines per mm in the darks against 4.4, lines merging). Pen drawings keep too little width contrast unless contours are drawn with `strokes`.

## Limits

- The bleeding is a volume-conserving flow on a coarse grid (2-8 px cells) with a fibre-noise front at full resolution. It is not a full lattice-Boltzmann (MoXi) simulation. The time course of spreading is not modelled, only where the ink ends up.
- A stroke's ink spreads when the stroke ends (when the next stroke starts or the episode ends). If a `match` runs right after another intention in the same episode, it does not yet see the last stroke of that intention.
- The `transfer` command and `sign` write into the picture directly, not as ink or pencil. Use `pencil` strokes for an erasable under-drawing and `finish seal` for an ink-painting signature.
- Colours are a few light, transparent films, not a full pigment palette. Heavy colour belongs in watercolour or gouache.
- Prints: no aquatint, mezzotint or soft-ground. The press's reversal of the image is not modelled: draw the image as it should appear. Plate tone and platemark are by eye. The line tools lay a stroke when it ends, so a very long `free` or `match` run costs about as much as with the brush.
