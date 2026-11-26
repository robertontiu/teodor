# Graphite pencil (`graphite`)

**What it is.** Graphite mixed with clay and fired into a lead. Grades run from hard and light (6H, 2H) to soft and dark (4B, 8B), with HB in the middle. Graphite catches on the paper's tooth the way charcoal does (speckled at light pressure, filled under pressure), but it is cleaner, less dusty and smudges less. Even the softest grade only reaches a dark grey, never charcoal's black. Its flat flakes give a metallic shine when the light rakes across dark, dense or burnished passages. Hard pressure flattens the tooth into a slick dark that takes no more graphite. Code: `studio/v8/media/drymedia.py`, class `Graphite` (the same engine as charcoal and pastel).

**Graphite is monochrome.** The colour you ask for sets only the value the hand works toward, and the pencil stops once the area under it is that dark. A value lighter than the paper switches to the kneaded eraser and lifts toward it. Work from a grey schema.

**Supports.**
- `drawing` (default): white drawing paper with a medium tooth.
- `toned`: grey-buff toned paper (`#b9b2a4` when the ground is light).
- `ingres`: Ingres laid paper. Laid lines show through the tone.
- `bristol`: smooth bristol. The tone comes out even and fine, but the little tooth holds less graphite, so the darks stay limited.
- `vellum`: vellum bristol, the hyperrealist's usual sheet: a fine, even tooth that takes many layers and blends to a smooth tone (blended grain 0.2-0.4 L*).
- `plate`: plate (smooth) bristol: almost no tooth. Tone is even at once and blends smoothest (grain about 0.2 L*), but it holds few layers, so the darks stay pale.
- `hot_press`: hot-pressed cotton paper: smooth and firm, takes many layers and erasing.

**Tools** (`"brush": ...`). `size` is the width of the mark in px. Points are capped at 10 px and the side at 36 px: a pencil is not a brush. The sheet is 1200 px = 24 cm (5 px/mm), so a 2 px line is 0.4 mm.
- `pencil` (default): set `"grade"` on the intention (6H…9B; default 2B). A narrow, even line.
- `pencil_2H`, `pencil_HB`, `pencil_4B`, `pencil_8B`: fixed grades. 2H stays light and silvery on the peaks, and 8B is the darkest, shiniest and most smudgeable.
- `side`: the side of a soft (6B) lead, for broad grainy tone.
- `stump`: a paper stump. It gives smooth, modulated tone and burnishes a little (adds shine).
- `kneaded`: soft lifts.
- `eraser`: a hard eraser for crisp lights (reduction drawing). Graphite erases well, but a faint ghost of each line stays.
- `stylus`: indents the paper. It is invisible at first. Any later tone skips the groove, which shows as a crisp white line (a sharp scratch through shading). Indent **before** any tone. Grooves stay paper-white under heavy pressure, powder (`glaze`) and every blender (measured: groove L* 97.9 under a blended tone of L* 48); they can't be erased.
- **Mechanical pencils** `mech_03`, `mech_05`, `mech_07`: a lead of one diameter (0.3, 0.5, 0.7 mm = 1.5, 2.5, 3.5 px), so the line keeps its width whatever `size`, speed or pressure you give; pressure sets only its darkness. `grade` as for `pencil`, capped by what the lead is made in (0.3 mm up to 2B, 0.5 and 0.7 mm up to 4B). The tools for layered tone and fine detail.
- `carbon_pencil`: a carbon (charcoal) pencil, matte, L* 26 at full cover, for the darkest darks graphite can't reach (graphite stops near L* 40 as an area and only gets shinier). Lay it **first**, while the tooth is free: over dense graphite it can't take.
- Blenders: `brush` (a soft blending brush: dissolves hatching into continuous tone with little contact, lifts a little; the main hyperrealist blender), `tortillon` (small and pointed, for detail), `stump`, `chamois` (broad, picks graphite up and lightens). With `clip: true` a blender spreads only what lies inside the region, so a masked edge stays crisp (as tape or a careful edge does). Blenders skim over indented grooves.
- Erasers: `kneaded` (soft, partial lifts), `eraser` (hard; leaves a ghost: lifts a L* 48 tone to about 82), `precision_eraser` (an eraser pen, 2.3 mm tip at most: crisp small lights, to about L* 88), `electric_eraser` (a battery eraser: lifts almost to the paper, about L* 95 on paper 96.5; at size 2-3 px a hair-thin white line).
- **`"seek": true`** on an intention with an eraser makes it lift toward the asked value and stop there. With `match` the asked value is the schema's, so `match` with `kneaded` or `electric_eraser` and `seek` lifts exactly where the drawing is darker than the schema.
- Oil-paint names map over: `round`, `filbert` and `liner` → `pencil`; `flat` and `fan` → `side`; `blend` and `smudge` → `stump`; `knife` → `eraser`.

**Parameters that matter.** `pressure` sets the depth into the tooth and the darkness. Above about 0.8 it also burnishes (slick, shiny, the tooth full). `grade` sets hardness, darkness and smudginess. The felt state works as in charcoal: fast strokes come out lighter and more broken.

**Hatching** (`"type": "hatch"`). The sheet is stated as 1200 px = 24 cm (5 px/mm). Real hatching measured for the calibration (Delacroix, Grandville, Bendemann) is 0.8-2 mm apart with lines about 0.3-0.35 mm wide: `"spacing": 4`–`8`, `"size": 1.5`–`2`, one grade per pass. The core's defaults (spacing 9 = 1.8 mm, size 3 = 0.6 mm) are coarse for graphite. The colour is the value of each line, and the default `#2a2a2a` presses as hard as the pencil can: give a lighter grey for light hatching.

**Transfer.** `transfer [strength]` traces the schema's contours with a 2H pencil, lightly (as a hyperrealist grids or traces the outline): real pencil strokes on the tooth, which later tone covers. `strength` 0.3 gives a pale line.

**Glaze.** A veil of graphite powder laid with the side of the lead and rubbed in, capped at the value of the colour you give. It's a quick way to lay a light general tone before hatching. It is recorded as `glaze` (a unifying film, as docs/styles/graphite-hyperrealism.md maps it); the first marks on bare paper as `drawing`.

**The hand.** Pencils keep the widths you ask for: the v8 hand's articulations, pressure wave and drift apply, its role sizes don't (they pushed graphite's marks away from the references: docs/calibration/charcoal.md, "The v8 hand"). `"role_scale": true` brings them back for one intention.

**Haze.** Each grade sheds a little of what it lays as loose graphite around the line (2H about 8%, 2B 14%, 8B 24%), so hatching carries a faint haze between its lines, as real sheets do. Blenders spread it, erasers lift it.

**Revision** (`scrape`, `wipe`, `paintout`; docs/MANUAL.md): `scrape` sweeps the hard eraser; `wipe` the kneaded eraser (graphite has little loose dust to knock back first); `paintout` erases the passage (kneaded, then hard eraser) and lays the surrounding tone again with `side` (or the `brush` you give): graphite can't cover a dark with a light. A ghost of the old marks stays, and a fixed passage is refused.

**Time.** Nothing dries, and `dry` does nothing.

**Finishing.**
- `fixative` `{"strength": 0.5, "region": {...}}` (optional for graphite): stops smudging, dulls the shine by about 20% and darkens a hair.
- `lift` `{"points": [[x, y, r], ...], "kind": "kneaded"|"eraser"}`: eraser highlights. Lift before fixing.
- `clean` `{"margin": 30}` or `{"region": {...}}`: cleans the margins.
- `accents` `{"strokes": [...], "n": 6, "tool": "pencil_8B"}`: the last darkest accents. It refuses more than `n` strokes.

`report finish` checks: the `transfer` guide lines erased or covered (flagged when they still read along more than 15% of their length, darker than the tone around them by 3 L*), the sheen not overworked (more than 20% of the drawn area burnished to a strong shine reads as glare), the fixative's darkening against the studio's model, and smudges in margins the schema leaves bare. Thresholds are judgements.

**Hyperrealism** (docs/styles/graphite-hyperrealism.md; the tested recipe and its numbers are in docs/calibration/graphite-hyperrealism.md):
1. `new "#f7f6f2" 2400 3200 --support vellum`, a greyscale photograph or rendered scene as `ref`, `transfer 0.3`; indent white lines with `stylus` now.
2. Tone in value bands, **darkest first** (each band's pressure fades across its level, so the bands don't step: `feather`, docs/MANUAL.md): one `hatch` per band, `"layers": [band]`, `"colors"` a little darker than the band (blending lightens a hatched band, because it averages the lines with the paper between them), `spacing` 3, a new `angle` per band, `clip: true` per part of the picture (wall, table, object...: a `{"type": "segment", "at": [x, y]}` region cut from the schema around a point, holes included, or a `poly`). Grades: `carbon_pencil` below about 0.30 sRGB, `pencil` 8B to 0.37, `mech_05` 4B, 2B, HB, 2H toward the lights.
3. Blend each part on its own: `hatch` with `"brush": "brush"`, `"value": 0`, `"layers": [1.0]`, `spacing` a third of the `size`, three angles, `clip: true`; a large brush (60-90 px) for out-of-focus passages, smaller on the subject.
4. Look and correct, two or three rounds: `match` with `mech_05` (or `carbon_pencil` in the darks) `faithful: 1`, a falling `threshold` (0.06, 0.04, 0.03), `clip: true`, then the same masked blend, smaller each round. `report` and `look diff` between rounds.
5. Lights: `match` with `kneaded` and `"seek": true` for soft lights, then `electric_eraser` or `precision_eraser` with `seek` for crisp ones; 2H over soft passages to fill their white flecks ("hard over soft").
6. The darkest accents last (`pencil_8B`, `carbon_pencil`), small and clipped.

**Order of work.** Light construction with `pencil_2H`, then the big value shapes with `side` or `glaze`. Build tone with softer grades and hatching, blend with `stump` where you want it smooth, erase the lights, and finish with the darkest accents and crisp edges.

**Size and speed** (2 vCPU, Nov 2026; at 5 px/mm 2400 x 3200 is a 48 x 64 cm sheet): one empty episode (load, save, render) 0.7 s at 1200 x 1600 and 1.9 s at 2400 x 3200; a one-layer `hatch` with a 2 px pencil at 1 mm spacing over an eighth of the sheet 2.8 s and 10.9 s (it was 6.2 s and 26 s before the point's contacts were vectorised); a `stump` pass over the same area 6.7 s and 30 s. Time grows with the area. A full hyperrealist drawing at 2400 x 3200 took 70 minutes plus a 9-minute second sitting (calibration note); 1200 x 1600 is about four times faster. 3600 x 4800 runs, but every episode costs about 12 s before the first mark.

**Limits for hyperrealism** (details in docs/calibration/graphite-hyperrealism.md): value bands laid with `hatch` now fade into each other (feathered), but each band's grade and grain still show faintly after blending; graphite stops near L* 40 as an area and carbon near L* 32, far from a photograph's blacks; edges between two dark passages get lost; `match` leaves short marks that need blending.

**Limits.** The shine is drawn into the image under one fixed raking light; there is no movable light. Lines thinner than about 2 px are soft ramps, not resolved into single flakes of graphite. There is no pencil wear (sharp vs blunt is just `size`). Hatched passages are still a little more contrasted than real ones (grain 6.3 against 5.2 L* in the references; it was 8.7).

## Calibration

Calibrated against the Met graphite references (Nov 25, 2026); the full report is `docs/calibration/graphite.md` (shared engine changes in `docs/calibration/charcoal.md`).

**Set from data:**
- The darkest graphite: L* 32.5-34.7 in the references (Lachaise, Grandville). A dense 8B passage renders at L* 32.8. The soft grades' pigment values sit about 3.5 L* lower than that because the render's sheen lifts them.
- One hard-end point, weak: Ingres's portrait in fine hard pencil reaches L* 55, used for H.
- The paper's tooth at pixel scale and its grain in the render (blank paper 0.8 L*; references 0.6-1.1; it was 1.6), laid lines at 0.9 mm: as in charcoal.
- Line edges: 10-90% rise 0.3 mm (Delacroix's hatching), a softer catch fitted to the grain in hatched passages.
- The stated scale (5 px/mm, like the reference sheets) and the hatch spacing and width advice.

**The grade ramp between the ends is tuned by eye** (`GRADE_L`: 6H 72, 4H 66, 2H 60, H 55, HB 49, B 44.5, 2B 41, 3B 38, 4B 35.5, 5B 33.5, 6B 32, 7B 30.8, 8B 29.8, 9B 29 pigment L*): no per-grade darkness was found as a measurement, and which grades 19th-century draughtsmen used is not known.

**Still tuned by eye:** flow, reach, loose, stain and sheen per grade; `KC = 3.5`; tooth capacities (drawing 0.9, Ingres 0.8, bristol 0.55); the burnish threshold (0.82); the sheen render (cool silver, at most 42%, fixed raking light: a diffuse museum photograph cannot show gloss); blender, eraser and stylus rates; fixative (~20% less shine is FINISHING.md's assumption); the size caps.

**Searched, not found.** No published per-grade reflectance or optical density for graphite; a tribology study of graded pencil cores ("Tribological characteristics of graded pencil cores on paper") was behind bot protection. No gloss measurement of graphite drawings. Structure from Sousa & Buchanan [S27]; behaviour from MEDIA.md [S10][S13].
