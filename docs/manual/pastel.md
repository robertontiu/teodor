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

**Glaze.** A light veil of colour laid with the side of a stick and partly rubbed in: broken over the peaks, with a soft film between. It does not tint like a transparent glaze. Use it for a coloured underlayer or to cool or warm a passage.

**Time.** Nothing dries, and `dry` does nothing.

**Finishing.**
- `fixative` `{"kind": "workable"|"final", "strength": 1, "region": {...}}`: with no region it covers the whole sheet; give a region to fix selectively (Degas never fixed whole compositions). It locks the dust, restores tooth for more layers, and darkens and dulls the fixed area (value about −8%, chroma −10%; the lights lose the most). `final` warns you to lay the last bright accents after it.
- `accents` `{"strokes": [{"pts": [...], "color": "#f4ecd8", "size": 8}], "n": 6}`: the final, brightest touches in soft pastel, laid after any fixative and left unfixed. It refuses more than `n` strokes.
- Framing under glass is presentation only; there is no op for it.

**Order of work.** Choose the paper tone. Lay big masses with `hard_side`, or with `glaze`. Build from dark to light and from hard to soft, using a workable `fixative` in a region where the tooth is full. Rub only where you want it soft. Finish with `soft_tip` lights and then `finish accents`.

**Limits.** Each pixel holds one apparent colour, so lifting the top layer reveals the paper rather than the layer below it. Oil pastel is simplified: no solvent wash, no warmth or blending by heat, and its sheen is faint. The tooth is a texture, not fibres.

## Calibration

**What comes from research.**
- The model's structure is shared with the other dry media (Sousa & Buchanan [S27], [GI 1999](https://graphicsinterface.org/wp-content/uploads/gi1999-21.pdf)).
- The mixing rule is optical: coverage-weighted and linear, not Kubelka-Munk, because pastel particles sit side by side (MEDIA.md, "Engine model (pastel)").
- The behaviour comes from MEDIA.md [S11]. Pastel has very little binder, so it stays chalky, matte and bright. Colour builds optically, with the paper tone showing through. Sanded paper holds many layers. A full tooth makes new colour slide. Fixative darkens pastel and dulls its brightness, which is why the last bright touches are left unfixed and why Degas fixed only selected areas.
- The fixative amounts (value −8%, chroma −10%, tooth +30%) are FINISHING.md's engineering starting values, not measurements.

**Hand-tuned by eye:**
- The paper tones `#857b6d`, `#b4a184` and `#9b9384`, and the tooth capacities: toned 1.7, sanded 3.4, Ingres 1.2. Their ratio (sanded holds about twice as much) follows the sources; the numbers are tuned.
- Per-stick flow, reach, loose, stain and "grip" (how much fresh pastel catches on pastel already in the tooth: 0.5 for soft, 0.3 for hard).
- The slide/smear rate on a full tooth (0.12).
- Coverage `KC = 3.5`.
- The powder lift in the render: `+0.05·cov·(1−v)²`.
- Oil pastel's subtractive blend `0.25·p`, its film floor (0.45) and its sheen.
- Blender and eraser rates; the size caps (28 px for the end, 120 px for the side).

**Searched, not found.** No measured colour change of pastel after fixative that I could reach. One promising Heritage Science article (DOI 10.1186/s40494-020-00396-x) could not be opened, and a pastel-practice paper on La Tour and Valade (ICOM-CC 2017) gives no numbers. No opacity measurements for soft pastel against tooth fill. These are worth fitting from real crops:
1. the share of paper visible against pressure and layer count;
2. scumble coverage;
3. value and chroma shift after fixative, from before/after photos if a conservation study provides them.
