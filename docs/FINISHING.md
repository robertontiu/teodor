# Finishing: the last stage of a painting, per medium, as engine operations

Companion to `docs/MEDIA.md` (same source numbers `[S#]`, listed there under **Sources**). Each medium gets: what painters do at the end, then the concrete `finish` operations the studio should offer. Today Teodor's last acts are `studio.py sign` and `studio.py timelapse`; these operations go before `sign`.

Numbers in the engine operations are starting values for tuning, chosen to match the direction and rough size of the effect the sources describe; they are not measurements.

## General practice (all media)

What painters describe doing when a picture is nearly done:
- **Step back and come back fresh.** Leave the studio and return to see the work "as if you've never seen it before"; catching it "as a surprised stranger" is one of the best tools [S23].
- **Squint** to see the big tonal design [S23].
- **Mirror or flip:** a mirror shows the painting reversed and from twice the distance, which breaks familiarity and regains objectivity; a black mirror mutes colour to check values; flipping a photo or turning the canvas upside down exposes weak spots [S23].
- **Reduce:** a reducing glass or a blurred photo shows the whole at once; a viewfinder warns of compositional faults [S23].
- **The last few accents:** the darkest darks and brightest lights, and the sharpest edges, go in last and sparingly, where the eye should land (oil: thick lights last [MEDIA: oil]; pastel: softest sticks last; watercolour: final darks; tempera: final highlight hatching [S14]).
- **Edge pass:** decide which edges stay hard (focal accents) and which are lost.
- **Sign.** Then the medium's protective step (varnish, fixative, glass, mounting).

**Engine operations (general):**
| Operation | What it does | Exists? |
|---|---|---|
| `look thumb`, `look gray` | step back, squint | yes (v7) |
| `look mirror` | render the canvas flipped horizontally (and `look mirror gray` for a "black mirror" value check) [S23] | new |
| `look fresh` | the canvas only, no schema overlay, after a forced pause: the orchestrator runs a fresh critic, as a "surprised stranger" [S23] | partly (critics) |
| `look blur` | heavy Gaussian blur, for the big design [S23] | new |
| `finish accents n=…` | a guarded intention: at most *n* small strokes, each must be the darkest dark, the lightest light or a hard edge in its neighbourhood; refuses more than *n* | new |
| `finish edges` | an edge pass: lists the schema's major edges and lets the painter mark each `hard`, `soft` or `lost`; soft and lost apply a short blend along the edge, hard does nothing | new |
| `sign` | already the last brush act; should use the active medium's instrument (charcoal signs in charcoal, ink in ink, woodblock with a seal block) | yes, oil only |

---

## Oil

**Practice.** Last thick lights and accents, final glazes to unify or deepen [S7]. Then drying: "A painting has to be completely dry throughout before it is varnished" [S7]. **Retouch varnish** (thin, porous) restores gloss and colour where passages sank in, and can protect an unfinished painting temporarily; wait at least 2–3 months for normal layers [S7]. **Final varnish** after about a year for normal layers (months for thin, years for thick) [S7]. Varnish has protective and aesthetic roles, the aesthetic probably the more important [S5]; it intensifies the pigments by refraction, "saturation" [S4], and sets colour saturation and gloss: low-molecular-weight resins level over rough paint and give higher gloss and more saturated colour [S5]. Gloss varnish is resin in solvent; matte varnish adds a matting agent and should go on in one even layer [S7]. Many 20th-century painters wanted a matte, unvarnished surface [S4].

**Why varnish deepens darks (optics).** An unvarnished, rough or sunken surface scatters a little white light from the paint's surface on top of the colour that comes from inside it; that surface white lifts dark values and greys colours. A varnish with a refractive index close to the binder's fills the roughness, so the surface reflection goes into one specular direction and the darks show at full depth [S4][S5] (the magnitude depends on the varnish and surface; the 3–5% figure used below is the order of Fresnel reflection at an air/resin interface, a modelling assumption).

**Engine operations:**
- `finish retouch` — where `sheen < 0.6`, raise `sheen` to 0.7 and remove the sunken-in surface white (see render model below). Allowed any time after the paint is touch-dry (`wet < 0.2`).
- `finish varnish gloss=G` (G 0 matte … 1 gloss) — requires `wet < 0.05` everywhere (else warn: in reality it would trap solvent and stay tacky [S7]). Sets `sheen = G` everywhere (evening out gloss), then the render model below. With G=1 the darks (luminance < 0.25) get about 10–20% darker and chroma rises ~5–10%; with G=0 (matte varnish) the surface white rises slightly and the painting reads flatter and lighter in the darks.
- `finish glaze …` — the existing `glaze` with the KM layer model: a final unifying glaze over the whole or part [S7].
- `finish oil-out` — rub a thin oil layer over sunken areas before working on (same optical effect as retouch, plus `wet` slightly up).

**Render model for the surface (used by every medium with a `sheen` map):**
```
surface_white = s0 * (1 - sheen)              # s0 ≈ 0.04 (assumption: order of Fresnel reflectance)
col_seen      = col * (1 - surface_white) + surface_white * light_colour
saturate      = 1 + 0.08 * sheen              # small chroma gain from a wetted, saturated surface
spec          = sheen * phong(ht normals, raking light)   # existing impasto specular, scaled by sheen
```
Unvarnished oil starts with `sheen` from its oil content (0.5–0.8, lower where it sank in), so v7's look corresponds to sheen ≈ 0.7.

---

## Watercolour

**Practice.** Final darks and crisp accents wet-on-dry; lifting soft lights with a damp brush, sponge or tissue (works best with non-staining pigments) [S9]; removing masking fluid and softening the hard edges it leaves [S9]; signing in paint or pencil. No varnish: watercolour and traditional gouache are protected under glass or UV acrylic, since varnish alters the paint and is effectively permanent [S18]. Mounted with a mat (window mount) that keeps the paper off the glass.

**Engine operations:**
- `finish lift region=… strength=…` — rewet and remove deposited pigment, scaled by `1 − staining` per pigment [S9]; soft edge.
- `finish unmask` — remove the masking-fluid mask, revealing paper; optionally `soften=px` to blend the hard edges into the surrounding wash.
- `finish darks` — a guarded `accents` pass with wet-on-dry, small brush.
- `finish dry` — run `step` until every wet pixel has dried and committed its glaze (colours settle lighter [S18]); required before `sign`.
- `finish mount colour=#… width=…` — a presentation step: render a mat border around the image in `look` and exports only. No varnish operation exists for this medium (by design).

---

## Ink (East Asian brush; Western pen and wash)

**Practice.** East Asian: last dark accents (dots, eyes, moss dots), then inscription and the red seal (chop); the painting is then mounted (backed with paper, made into a hanging scroll or album) [S20 context]. Western: erase pencil under-drawing once the ink is dry; scrape highlights [S22]; last dark accents.

**Engine operations:**
- `finish dots` — guarded accents in the darkest ink with a small upright brush.
- `finish seal text=… at=…` — stamp a red seal (cinnabar-red, slightly uneven impression on the paper texture, like a print) as part of the signature; replaces or accompanies `sign`.
- `finish erase-pencil` — remove the construction layer (kept as a separate faint graphite layer) where it is not covered by ink.
- `finish scrape region=…` — remove a fraction of fixed ink and roughen `paper_h` slightly (scraped highlight) [S22].
- `finish mount` — presentation only (silk or paper border).

---

## Charcoal

**Practice.** The darkest accents with compressed charcoal, crisp lifted highlights with a kneaded or hard eraser, white chalk touches; then a permanent final fixative to seal the dust; workable fixative was used between layers [S12]. Charcoal "can be easily wiped away unless fixed" [S13].

**Engine operations:**
- `finish lift` — kneaded-eraser highlights (soft-edged), hard-eraser highlights (crisp).
- `finish fixative kind=workable|final strength=…` — converts `loose` to `fixed` (no further smudging), restores a little tooth (workable: `tooth_left += 0.2*capacity`) and **darkens slightly**: values multiply by `1 − 0.04*strength` and the paper shows a touch less light through the dust. (Fixative's darkening is documented for pastel [S11]; it is milder on charcoal because charcoal is already near-neutral dark.)
- `finish clean` — remove smudges from margins (dust outside the drawing's bounding region).

---

## Graphite

**Practice.** Clean margins, sharpen edges, darkest accents in soft grades, lift highlights with erasers [S10]; soft grades may be fixed, but graphite "adheres to surfaces easier without much need, if any, for fixative" [S13].

**Engine operations:** `finish lift`, `finish clean`, `finish accents` (soft grade), optional `finish fixative kind=final strength=0.5` (removes smudgeability; reduces `sheen` by ~20% because the fixative film dulls the graphite's metallic shine: a modelling assumption).

---

## Soft pastel (and oil pastel)

**Practice.** The final, brightest touches in the softest pastels are left **unfixed**, because fixative darkens pastel and impairs "its hallmark, high-keyed brightness"; it is generally avoided [S11]. Degas fixed only selected areas, as a barrier between layers, and never whole compositions [S11]. Finished pastels are framed under glass (with a spacer) because the powder stays fragile [S11]. Oil pastel: no fixative needed in the same way; it never fully dries, so it is framed under glass or sealed with a dedicated fixative (S37, cited).

**Engine operations:**
- `finish fixative kind=workable region=… strength=s` — restores tooth (`tooth_left += 0.3*capacity*s`), locks `loose`, and **darkens and dulls** the fixed area: value × (1 − 0.08·s), chroma × (1 − 0.10·s), and light colours lose more than dark (the powder's scattering is reduced by the wetting film). Intended for *between* layers.
- `finish fixative kind=final` — same effect over the whole sheet; the studio warns that the last bright accents should go on *after* it or be skipped [S11].
- `finish accents tool=soft_pastel` — the guarded accents pass in the softest sticks, after any fixative.
- `finish glaze-frame` — presentation only.

---

## Gouache

**Practice.** Final light accents and edge crispening; avoid reworking dry areas (reactivation muddies them); usually unvarnished, framed under glass [S18].

**Engine operations:** `finish accents` (opaque lights), `finish edges` (crispen with a small flat, low water so it does not reactivate), `finish dry` (applies the drying shift: lights darken and darks lighten slightly [S18], ~3–5% in value as a starting value). No varnish.

---

## Egg tempera

**Practice.** Final hatching of highlights and accents; in the 15th-century reconstruction, oil glazes on the robes, then highlights lost under the oil restored in tempera, and painted "gold" dots in lead-tin yellow [S14]. Gilding is done early (before painting) on a very smooth gesso, with bole, leaf, burnishing and punchwork [S14]. Usually not varnished; cures over months [S15].

**Engine operations:**
- `finish hatch-lights region=…` — a final hatching pass of light, thin strokes over modelled forms.
- `finish oil-glaze colour=… region=…` — KM glaze layer that also lowers the value of tempera highlights below it (so a later `hatch-lights` is needed to restore them [S14]).
- `finish punch pattern=… region=gold` — punchwork in the gold ground (if not done during gilding) [S14].
- `finish sheen 0.35` — tempera's satin surface [S15]; no varnish by default.

---

## Acrylic

**Practice.** Isolation coat, then a removable varnish to even the sheen (S35, cited).
**Engine operations:** `finish varnish gloss=…` exactly as oil (same render model); no drying wait beyond `wet < 0.05`.

## Fresco

**Practice.** Secco touches on dry plaster for details and lime-incompatible pigments [S19]; no varnish.
**Engine operations:** `finish secco` — paint with lower adhesion and slightly more opacity on closed giornate. No varnish.

## Woodblock print

**Practice.** No finishing beyond the impression: the print is complete when the last block is printed [S16][S17]. Seals and signature are part of the blocks.
**Engine operations:** `finish seal` as a printed block (the artist's signature cartouche and seal are carved and printed, not hand-signed); no varnish, no fixative.

---

## Summary table

| Medium | Last painting acts | Protective/optical step | Engine ops |
|---|---|---|---|
| Oil | thick lights, accents, unifying glaze | retouch varnish (2–3 months), final varnish (~1 year) [S7] | `accents`, `edges`, `glaze`, `retouch`, `varnish gloss=` |
| Watercolour | final darks, lifting, unmask | none; glass and mat [S18] | `darks`, `lift`, `unmask`, `dry`, `mount` |
| Ink | dark dots, inscription | seal; mounting | `dots`, `seal`, `erase-pencil`, `scrape`, `mount` |
| Charcoal | compressed darks, lifted lights | final fixative (darkens slightly) [S12] | `lift`, `clean`, `fixative final` |
| Graphite | darkest accents, lifts | optional fixative [S13] | `lift`, `clean`, `accents`, `fixative` |
| Soft pastel | brightest soft accents, unfixed | fixative avoided or selective (darkens) [S11]; glass | `fixative workable`, `accents`, `glaze-frame` |
| Gouache | light accents, edges | none; glass [S18] | `accents`, `edges`, `dry` |
| Tempera | hatched highlights, optional oil glazes, gold details | usually none [S15] | `hatch-lights`, `oil-glaze`, `punch`, `sheen` |
| Acrylic | as oil | isolation coat + varnish | `varnish` |
| Fresco | secco details [S19] | none | `secco` |
| Woodblock | last block | none | `seal` |

Sources: see `docs/MEDIA.md#sources`.
