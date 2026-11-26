# Soft pastel (`pastel`)

**What it is.** Pure pigment with only a minimal binder, pressed into sticks. It is opaque, chalky and very bright, and it sits on top of what is under it. It doesn't mix like paint. Colour builds optically: strokes laid side by side or over each other, with the paper or the layers below showing through the broken top layer. The paper's tooth catches the colour on its peaks first. A light touch of a light colour over a dark one (a scumble) leaves the dark showing in the hollows. Once the tooth is full, new colour slides and smears instead of covering, which is when painters use a workable fixative. The surface is matte and velvety, and darks look slightly lifted by the powder. Code: `studio/v8/media/drymedia.py`, class `Pastel` (the same engine as charcoal and graphite). An oil-pastel stick is included as a tool.

**Supports.** The paper's tone shows through everywhere and acts as a colour in the picture. On every support, a light ground given to `new` (luminance above 0.7) means the paper's own tone; give a darker ground to choose the toning colour.
- `toned` (default): toned pastel paper, honeycomb side (`#857b6d`, warm grey). Real tooth, two to three layers.
- `sanded`: sanded pastel paper (`#b4a184`, buff). A fine grit that grabs colour and holds many layers.
- `ingres`: toned Ingres laid paper (`#9b9384`). Modest tooth, and the laid lines show.

**Tools** (`"brush": ...`). The colour is the stick's colour. `size` is the width of the mark, capped at 28 px for the end and 120 px for the side.
- `soft_tip` (default): the end of a soft pastel. Thick, opaque strokes, for the brightest accents.
- `soft_side`: on its side. Rich, broad colour broken by the tooth. It fills the tooth fast.
- `hard_side`, `hard_tip`: hard pastels. Lighter and grainier, they leave tooth free for later layers. Use them for early masses, lines and hatching.
- `stump`, `finger`: blend the powder (the colours do mix when rubbed). The finger drags colour into the next.
- `chamois`: knocks an area back and lifts dust.
- `kneaded`: lifts dust back toward the paper.
- `oil_pastel`: a buttery, waxy stroke. It rides over a full tooth as a film, blends with what is under it by pressure, and has a slight waxy sheen.
- `scraper`: sgraffito. It scratches through oil pastel to the paper.
- Oil-paint names map over: `round`, `filbert` and `liner` → `soft_tip`; `flat` and `fan` → `soft_side`; `blend` → `stump`; `smudge` → `finger`; `knife` → `kneaded`.

**Parameters that matter.** `pressure` sets how deep the colour goes into the tooth: about 0.3–0.4 scumbles over the peaks, and 0.85 or more covers. The felt state matters too: fast strokes break up more. Work hard to soft and dark to light. Soft pastel fills the tooth, so save it for the later layers.

**Hatching** (`"type": "hatch"`). Give `colors`: pastel is not monochrome, and the core's default is a dark grey. The sheet is stated as 1200 px = 48 cm (2.5 px/mm); Degas's hatched and broken strokes are 4-6 mm wide, laid side by side: with `hard_tip`, `"size": 8`–`12`, `"spacing": 10`–`14`.

**Glaze.** A light veil of colour laid with the side of a stick and partly rubbed in: broken over the peaks, with a soft film between. It does not tint like a transparent glaze. Use it for a coloured underlayer or to cool or warm a passage. It is recorded as `scumble` (a broken layer over what is beneath); tag a coloured underlayer on bare paper `"role": "underpainting"`.

**The hand.** Sticks keep the widths you ask for: the v8 hand's articulations, pressure wave and drift apply, its role sizes don't (as for charcoal and graphite; docs/calibration/pastel.md). `"role_scale": true` brings them back.

**Revision** (`scrape`, `wipe`, `paintout`; docs/MANUAL.md):
- `scrape`: a blade scrapes the built-up pastel off the tooth (loose dust first, then much of the bound) and cuts through oil pastel to the paper. Because each pixel holds one apparent colour, the passage goes back toward the paper, not to the layer beneath.
- `wipe`: the chamois knocks the passage back, then the kneaded eraser lifts it.
- `paintout`: pastel covers: the colour the surroundings have there (or `color`) is laid over the passage as a dust veil, `passes` times (default 2, `opacity` 0.9). On a full tooth little takes, and the studio says so: fix the region first (`finish fixative` with `kind: workable` and a `region`) to restore tooth.

**Time.** Nothing dries, and `dry` does nothing.

**Finishing.**
- `fixative` `{"kind": "workable"|"final", "strength": 1, "region": {...}}`: with no region it covers the whole sheet; give a region to fix selectively (Degas never fixed whole compositions). It locks the dust, restores tooth for more layers, and darkens and dulls the fixed area (value about −8%, chroma −10%; the lights lose the most). `final` warns you to lay the last bright accents after it.
- `accents` `{"strokes": [{"pts": [...], "color": "#f4ecd8", "size": 8}], "n": 6}`: the final, brightest touches in soft pastel, laid after any fixative and left unfixed. It refuses more than `n` strokes.
- Framing under glass is presentation only; there is no op for it.

`report finish` checks: the last bright touches (`finish accents`) come after the last fixative, no final fixative over the whole sheet (Degas fixed selected areas only), and how much all fixative passes darkened the picture against one full pass of the studio's model (more than 1.5 passes' worth is flagged; no measurement exists). Thresholds are judgements.

**Order of work.** Choose the paper tone. Lay big masses with `hard_side`, or with `glaze`. Build from dark to light and from hard to soft, using a workable `fixative` in a region where the tooth is full. Rub only where you want it soft. Finish with `soft_tip` lights and then `finish accents`.

**Limits.** Each pixel holds one apparent colour, so lifting the top layer reveals the paper rather than the layer below it. Colours laid over each other mix optically (side by side), and rubbed colours average linearly; a spectral model for rubbed pastel was not adopted because no measured pastel blends exist to validate it (docs/calibration/pastel.md). Loose pastel dust does not fall or haze around strokes. Oil pastel is simplified: no solvent wash, no warmth or blending by heat, and its sheen is faint. The tooth is a texture (pixel-scale grain, honeycomb cells of 0.8 mm, laid lines), not fibres.

## Calibration

Calibrated against the Met pastel references (Nov 25, 2026); the full report is `docs/calibration/pastel.md` (shared engine changes in `docs/calibration/charcoal.md`).

**Set from data:**
- Stroke edges: 10-90% rise 1.0 mm (Degas, *The Singer in Green*: 0.98 mm; others 1.4-2.2), the softest of the dry media.
- The catch softness from the coarser tooth of pastel papers (paper specks inside strokes 0.2-0.4 mm).
- Laid lines (Ingres) at 0.9 mm and chain lines at 35 mm; the pixel-scale grain and the paper relief in the render, as in charcoal.
- Checked against the data, not changed: the darkest pastel values (three heavy passes of a near-black stick render at L* 10.4; the references' blacks are L* 9.6-13.4), and the share of paper left in a drawing (0.03 in the test drawing; the references 0.04).
- The stated scale (2.5 px/mm) and the stroke width advice for hatching.

**Still tuned by eye:**
- The paper tones `#857b6d`, `#b4a184` and `#9b9384`, and the tooth capacities: toned 1.7, sanded 3.4, Ingres 1.2. Their ratio (sanded holds about twice as much) follows the sources; the numbers are tuned. The honeycomb cell size (0.8 mm).
- Per-stick flow, reach, loose, stain and "grip" (0.5 soft, 0.3 hard); the slide/smear rate on a full tooth (0.12); `KC = 3.5`.
- The powder lift in the render: `+0.05·cov·(1−v)²`.
- Oil pastel's subtractive blend `0.25·p`, its film floor (0.45) and its sheen.
- The side strokes' streaks, smooth wobble and wedge-shaped landing (they replace the hard rectangles `match` used to make).
- Blender and eraser rates; the fixative amounts (value −8%, chroma −10%, tooth +30%: FINISHING.md's starting values); the size caps (28 px for the end, 120 px for the side).

**Searched, not found.** No measured colour change of pastel after fixative that I could reach (Heritage Science DOI 10.1186/s40494-020-00396-x could not be opened; the ICOM-CC 2017 paper on La Tour and Valade gives no numbers). No opacity measurements for soft pastel against tooth fill. The grain inside soft-pastel strokes is now lower than in Degas's broken strokes; fitting it needs single strokes at known pressure. Structure from Sousa & Buchanan [S27]; behaviour and optical mixing from MEDIA.md [S11].
