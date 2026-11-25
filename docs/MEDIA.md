# Media: what each medium is, and how the studio should model it

Research notes for turning the studio's single oil model (`studio/v7/studio.py`) into pluggable **instruments**, one per medium, the way Spectre registers instruments per genre (`spectre/engine/instruments.py`: one function per instrument behind a shared signature, registered in a table). Each section covers materials, supports, tools and marks, visual signatures, order of work, finishing (summarised here, in full in `docs/FINISHING.md`) and an **Engine model**. `studio/media.json` holds the same facts in machine-readable form.

Citations are `[S#]`, listed under **Sources** at the end. Sources marked *(read)* were read for this document; sources marked *(cited, not read this session)* are standard references whose content is summarised from the literature and should be checked before quoting in public text. Numbers in "Engine model" sections are engineering starting values for tuning, not measurements, unless a source is given.

Contents: [Shared model](#shared-model) · [Oil](#oil) · [Watercolour](#watercolour) · [Ink](#ink) · [Charcoal](#charcoal) · [Graphite pencil](#graphite-pencil) · [Soft pastel and oil pastel](#soft-pastel-and-oil-pastel) · [Gouache](#gouache) · [Egg tempera](#egg-tempera) · [Acrylic](#acrylic) · [Fresco](#fresco) · [Woodblock print (ukiyo-e)](#woodblock-print-ukiyo-e) · [Engine priority list](#engine-priority-list) · [Sources](#sources)

---

## Shared model

What every instrument shares, so the media differ only where they physically differ.

**Support.** Every support is a height field `paper_h` (0..1) plus scalars or maps for `absorbency` (how fast water or oil is drawn in), `tooth` (how much dry pigment the surface can hold before it saturates), and a base `tone`. Curtis et al. model watercolour paper exactly this way: a height field whose slope perturbs flow and whose height sets the fluid-holding capacity `c = h(c_max − c_min) + c_min` [S1]. Sousa and Buchanan model drawing paper as a height field that abrades the pencil and catches graphite [S27]. v7's `weave()` canvas texture becomes one support among several.

**Layers.** Oil, gouache and pastel are mostly *mixed in place* (one colour per pixel, mixed subtractively). Watercolour, tempera glazes, ink washes and woodblock impressions are *layered*: each layer is a transparent film over what lies below, composited with Kubelka–Munk (KM) layer equations, reflectance `R = sinh(bSx)/c`, transmittance `T = b/c` [S1]. The engine therefore needs two compositing paths: `kmix` (in-place mixing, already in v7) and `km_layer` (film over substrate).

**Pigments.** A pigment needs absorption K and scattering S per channel. Curtis et al. derive them from two user-chosen colours, the pigment's appearance over white and over black [S1]; that is the practical way to give Teodor a palette of named pigments with real opacity. Mixbox does in-place mixing through a 7-D latent space (four pigment concentrations plus an RGB residual) and two 256³ lookup tables; mixing becomes a linear interpolation of latents [S3]. Its own limits: only opaque homogeneous mixing, no glazing, and coefficients from glossy acrylic that may over-saturate matte media [S3]. So Mixbox fits oil/gouache/acrylic/pastel mixing, and the two-constant layer model fits watercolour, glazes and ink.

**Per-pigment properties** used across media: `K, S` (from over-white/over-black colours), `granulation` and `density` (how readily it settles into paper hollows) and `staining` (how strongly it binds to fibres, so how well it lifts) [S1][S9].

**Instrument interface** (proposal, mirroring Spectre's registry):
```
class Instrument:
    name; state_fields          # extra per-pixel arrays saved as {CANVAS}_{field}.npy
    def new(canvas, support)    # initialise state on a support
    def dab(canvas, tool, x, y, angle, pressure, speed)   # one stamp along a gesture
    def step(canvas, dt)        # time passes: flow, drying, curing
    def render(canvas, light)   # state -> RGB (with surface optics)
    def finish(canvas, op, **p) # the medium's finishing operations
MEDIA = {"oil": Oil, "watercolour": Watercolour, ...}
```
The motor model (`Felt`, `gesture_path`, `play`) stays shared: it already gives speed, pressure and lift per dab, which every medium needs.

---

## Oil

### 1. Materials
- Pigment in a drying oil (linseed, also walnut, poppy). Oil does not dry by evaporation but by **oxidation**, which needs air and light; cold and humidity slow it [S7].
- Opacity ranges from transparent lakes to opaque earths and whites; a **glaze** is a transparent layer that acts "like placing a coloured sheet of glass over a picture" [S7].
- Mixing is subtractive and physical on the palette and wet-in-wet on the canvas (what v7's `kmix` models).
- **Fat over lean**: each layer should hold a little more oil/medium than the one beneath so the top stays more flexible; reversing it risks cracking as the lower layer keeps curing [S6][S7]. Thin layers dry faster than thick ones, so thick paint belongs on top [S6].
- **Sinking in**: where an absorbent underlayer has drawn oil out of a layer, it dries matte and dull; retouch varnish restores gloss and colour there [S7].

### 2. Supports and grounds
- Canvas (linen, cotton) or panel, sized and primed. "Untreated grounds draw oil out of the paint"; grounds are gesso in two layers, with an extra binder coat on very absorbent ones [S7].
- Visual: canvas weave shows through thin paint and catches dry-brush; panels are smooth and show every stroke edge.
- Toned grounds (imprimatura) are common: a thin transparent earth over white that sets the mid-value.

### 3. Tools and marks
- **Brushes:** hog bristle (stiff, leaves ridges and furrows) and soft sable/synthetic (smooth, for glazes and detail). Shapes: *round* (tapered point, line to blob by pressure), *flat* (long hair, square edge, chisel marks and planes), *bright* (short flat, stiffer, short thick dabs), *filbert* (flat with a rounded tip, soft-edged leaf-shaped marks), *fan* (sparse spread hairs, foliage, hair, softening), *rigger/liner* (very long thin hair, long continuous lines of even width) [S37].
- **Palette knife:** flat slabs of paint with crisp edges and smooth tops, scraped passages showing ground, sgraffito by scraping into wet paint.
- **Rag, finger, soft blender:** wiping out lights in the imprimatura, softening edges.
- v7 already has round, flat, fan, knife, liner, smudge and blend (`Brush.mask`); it lacks filbert and bright, and its round has no pointed tip.

### 4. Visual signatures
- Bristle furrows in the direction of the stroke and a raised **ridge at the stroke's end and edges** (impasto) under raking light [S24][S26].
- Wet-in-wet mixing and pickup: a stroke drags the colour beneath and changes hue along its length (v7 has this).
- **Broken colour/scumble:** stiff, nearly dry paint dragged over dry texture catches only the high points (v7: dry-brush by depletion and speed).
- **Glazes:** deep, jewel-like darks from transparent layers over a lighter underlayer [S7].
- **Surface optics:** gloss varies across the painting where passages sank in; a final varnish evens it and deepens darks [S4][S5][S7].
- Lost and found edges: soft where forms turn away, hard at accents.

### 5. Order of work
- Direct (alla prima): block in big masses thin and lean, then work wet-in-wet toward detail, thickest lights last.
- Indirect: drawing, monochrome underpainting (grisaille/dead colour), dry, then colour layers each fatter than the last, glazes at the end [S6][S7].
- Typical tonal logic: thin darks, thick lights; darks and shadows stay transparent, lights are built opaque and raised.

### 6. Finishing (summary; see `FINISHING.md`)
Last accents and highlights in thick paint, a final edge pass, glazes to unify; after drying, retouch varnish to even out sunken areas; final varnish once the paint is fully dry throughout (about a year for normal layers, months for thin ones, years for thick ones) [S7]. Varnish saturates colour and sets the gloss [S4][S5].

### Engine model (oil)
**What v7 already has:** `col`, `wet`, `ht` (impasto height), `tex` (canvas), per-channel single-constant KM blended 58/42 with linear (`kmix`), bristle masks, pickup, depletion, dry-brush, glaze, blend, knife, raking-light render.

**What it lacks, in priority order:**
1. **Two-constant pigment state** (`K, S` per pixel, or Mixbox latents [S3]). Today a glaze is a `kmix` toward a colour; a real glaze is a KM film over the substrate [S1], so a transparent lake over white glows and over black barely shows. Store `film_thickness` per glaze layer or composite glazes immediately with `km_layer`.
2. **Oil content per pixel (`fat`) and `sheen`.** Each dab deposits `fat` from the brush's medium setting. Drying (`step`) lowers `wet` with a rate that depends on thickness (thin dries faster [S6]). Where a layer is laid over an absorbent or leaner layer, a fraction of its oil sinks: `sheen` falls and `render` shows that passage duller and lighter in the darks (sinking in [S7]). This makes `finish retouch` and `finish varnish` meaningful.
3. **Bristle furrows that follow the stroke**: modulate `ht` by the bristle profile along the stroke direction (the per-bristle loading is already there; add a ridge at the lift point proportional to remaining load [S24]).
4. **Filbert and bright brushes, pointed round tip**: new mask shapes.
5. **Fat-over-lean warnings**: when a lean layer goes over a fatter, still-wet layer, log a craft warning (not an effect), so Teodor can learn the rule.
6. **Surface render**: a per-pixel gloss map (`sheen`) feeding the specular term and a matte "surface white" term (see FINISHING: varnish).

**Tools:** round, flat, bright, filbert, fan, rigger, knife, rag (wipe-out: remove paint toward the ground by `wet`), finger/blender, scraper (sgraffito: reveal ground where `wet` is high).

---

## Watercolour

### 1. Materials
- Finely ground pigment in **gum arabic**, which slows spreading and, when the water dries, "adheres the pigment to the paper" [S9]. Applied in thin layers it is rarely opaque [S9].
- **Transparent and layered:** washes are glazed one over another after each dries; "the different pigments are not mixed physically, but optically" [S1]. Mixing also happens wet in the palette and wet-in-wet on the paper.
- **Granulation:** pigment settles into paper hollows, strongest on very wet paper; denser pigments settle earlier, separating colours [S1]. Earths, cobalts and ultramarines granulate; most modern synthetic colours do not [S9].
- **Staining vs lifting:** staining pigments (Prussian blue, alizarin crimson) stay after blotting; older mineral pigments lift easily [S9].
- Colours dry noticeably lighter than they look wet [S18].
- Rewettable: dry paint can be rewetted and lifted with a sponge [S9].

### 2. Supports
- **Hot-pressed:** smooth, paint stays on the surface longer, sharper edges, lifts well, good for detail and line [S8].
- **Cold-pressed (NOT):** felt texture that "grips the paint and creates natural granulation and soft edges"; absorbs faster, so less working time [S8].
- **Rough:** pronounced texture, quickest absorption, strongest granulation, hard to control for detail [S8].
- Cotton papers are naturally white and archival; wood-pulp papers yellow and degrade [S8]. Around 300 gsm is standard; 190 gsm buckles when wet [S8]. **Sizing** (gelatine or synthetic) keeps the wash on the surface; it is what makes edges stop and darken [S1].

### 3. Tools and marks
- **Round** (sable or synthetic, holds a lot of water and comes to a point): the main brush; one stroke goes from hairline to broad by pressure.
- **Mop/wash brush:** large soft belly for laying even washes and wet-in-wet skies.
- **Flat/one-stroke and hake:** broad even bands, straight edges, wash laying; the hake is a wide flat Japanese goat-hair brush.
- **Rigger:** long hair for branches, rigging, long lines.
- **Sponge and tissue:** lifting (soft-edged light shapes) and texture; a damp clean brush lifts lines [S9].
- **Masking fluid:** latex that reserves white shapes with hard edges, removed after the washes [S9].
- **Salt** sprinkled into a damp wash pulls water and pigment into small starry pale spots (artists' practice; not in the read sources).
- **Granulation medium, ox gall** (flow improver) [S9].

### 4. Visual signatures
- **Edge darkening:** sizing and surface tension stop the wash spreading, and as it dries pigment migrates to the edge, "leaving a dark deposit at the edge" [S1]. Physically this is the coffee-ring effect: evaporation at a pinned edge drives an outward capillary flow that carries particles there [S31].
- **Back-runs/blooms (cauliflowers):** water added to a damp, drying wash spreads and pushes pigment, making "complex, branching shapes with severely darkened edges" [S1].
- **Granulation and colour separation** [S1][S9].
- **Wet-in-wet flow:** soft, feathery shapes with striations along the flow [S1].
- **Dry-brush:** a nearly dry brush at a low angle touches only the raised paper, "irregular gaps and ragged edges" [S1].
- **Hard vs soft edges:** a wash on dry paper ends in a hard, darkened edge; on damp paper it fades out softly.
- **The paper's white is the light:** whites are reserved, never painted (white gouache is a different medium).
- **Glazing transparency:** each dry layer shows through the next [S1].
- **Tide lines** where a wash was retouched while half-dry.

### 5. Order of work
Light to dark, preserving the white of the paper for highlights [S18]: drawing (light graphite), masking, large pale washes (sky, ground) often wet-in-wet, midtones once dry, then darks and details wet-on-dry. "Watercolor is about preserving light" [S18].

### 6. Finishing (summary)
Final darks and crisp accents, lifting of soft lights, removing masking and softening its hard edges, signing; no varnish: works go under glass [S18]. See `FINISHING.md`.

### Engine model (watercolour)
Follows Curtis et al. [S1], simplified for numpy at 1200×1600.

**State (per pixel):**
- `wet_mask` M (bool/float), `water` (shallow-layer depth), `u, v` velocity (optional: a simplified diffusion model first),
- `g[k]` pigment suspended in water and `d[k]` pigment deposited on paper, per pigment k (cap at ~4–6 active pigments per painting, or store per-layer K/S),
- `paper_h` height, `capacity` from height [S1], `sat` capillary water saturation (for back-runs),
- `layers`: committed dry glazes as (K, S, thickness) or a running composited reflectance/transmittance pair.

**Dab:** adds water and suspended pigment under the brush footprint and sets `wet_mask`; brush state = water load + pigment load, both depleting with distance; low water + high speed → only pixels with `paper_h` above a threshold become wet (dry-brush [S1]).

**Step (time):**
1. *Move water* (cheap version: diffuse `water` within `wet_mask`, biased downhill on `paper_h`; full version: shallow-water equations [S1] or the Van Laerhoven–Van Reeth thin-paint model [S32]).
2. *Edge darkening:* blur the wet mask with a K×K Gaussian (K≈10) and lower pressure near the boundary so water and pigment flow outward; strength 0.01–0.05 [S1].
3. *Move pigment* with the water flux.
4. *Adsorb/desorb:* pigment moves between `g` and `d` at a rate set by its density and staining; granulation scales how strongly `paper_h` hollows attract deposition [S1].
5. *Capillary flow:* absorbed water diffuses through the paper up to `capacity`; cells over a saturation threshold join the wet mask, which grows back-runs with branching edges where capacity varies [S1].
6. *Evaporate;* when a region is dry, commit `g+d` into a glaze layer.

**Render:** KM compositing of glazes over the paper (`paper_tone`), thickness from `g + d` [S1]; colours slightly darker while wet (dry lighter [S18]); paper texture via `paper_h` shading.

**Tools:** round, mop, flat, hake, rigger, sponge (lift: move `d` back to `g` and remove, scaled by 1 − staining [S9]), tissue blot, clean damp brush (adds water: makes blooms on damp washes), masking fluid (a `mask` field that blocks wetting; removed by `finish unmask`), salt (local sinks of `water` that pull pigment outward from tiny points), granulation medium (raise granulation).

**Priorities:** (1) wet mask + water + suspended/deposited pigment with diffusion and drying, (2) edge darkening, (3) KM glaze compositing on paper, (4) granulation on `paper_h`, (5) dry-brush threshold, (6) back-runs via capillary layer, (7) lifting and masking, (8) full shallow-water flow.

---

## Ink

Two traditions: East Asian ink and brush (Chinese *shuimo*, Japanese *sumi-e*), and Western pen and ink with washes.

### 1. Materials
- **East Asian ink:** soot from burnt oil or wood (pine soot) bound with animal glue, pressed into sticks [S20][S21]; ground with water on an inkstone, whose surface affects the ink's quality and texture [S20]. Valued for its "infinite gradations" of tone [S21]. Carbon ink is permanent once dry: later washes do not lift it.
- **Western inks:** carbon (lamp black) gives strong lines "and can be diluted to create transparent gray washes"; **iron gall** was the most widely used ink from the 12th to mid-19th century, colourless when made and oxidising to black, ageing to brown or rusty orange; **bistre** (wood soot, reddish to greyish brown, grainy if unfiltered); **sepia** (cuttlefish ink, rare; usually names a colour) [S22].
- Mixing: optical by layering washes; ink tone is set by dilution, not by mixing colours.

### 2. Supports
- **Xuan paper:** absorbent paper for painting and calligraphy. *Raw* (sheng) xuan is unsized and bleeds and feathers; *sized* (shu, "cooked") xuan is treated with alum and glue so ink sits and edges stay crisp, used for fine-line *gongbi* painting; raw paper suits expressive *xieyi* (S36, cited, not read). **Silk**, sized, for gongbi.
- Western: laid and wove papers, vellum; smooth hot-pressed or Bristol board for pen.

### 3. Tools and marks
- **Chinese brush:** a conical hair tuft (soft goat, springy wolf/weasel, or mixed) that holds a reservoir in its belly and comes to a fine tip. **Loading** sets the stroke: dip the moist brush's tip in ink and the moisture already in the brush dilutes it, so the tone lightens away from the tip; or load a light wash then dip the side in dark ink [S21]. One stroke can therefore go dark-to-light across its width.
- **Center tip vs side brush:** upright brush with the tip in the centre of the line gives round, even strokes; oblique brush gives broad strokes with a sharp edge on one side and a soft ragged one on the other [S21].
- **Speed and pressure:** fast/light vs slow/heavy strokes differ, and varying pressure in one stroke yields "gradations of ink… within a single brushstroke" [S21].
- **Flying white (feibai):** fast with little moisture; hairs separate and leave streaks of paper inside the stroke [S21].
- **Western pens:** quill and reed (broad, variable, reed is blunt and gritty), steel nib (flexible: the line swells with pressure), technical/fountain pens (even line) [S22]. Brush for washes [S22].
- **Scraping:** removing ink from the paper to create highlights [S22].

### 4. Visual signatures
- **Line weight variation with pressure**; swelling and tapering at entry and exit.
- **Tone gradation inside one stroke** from tip-to-belly loading [S21].
- **Flying white** in fast dry strokes [S21].
- **Bleeding/feathering into absorbent paper:** on raw xuan, wet ink spreads along fibres into a feathery halo with a darker boundary; MoXi was built to reproduce this "ink dispersion in absorbent paper" [S2].
- **Ink layering:** a later wet stroke over a dry one shows both; over a damp one, they fuse.
- **Pen:** hatching and cross-hatching for tone, stippling, crisp edges, occasional blots; washes with dilute ink or bistre on top of line [S22].

### 5. Order of work
- East Asian painting: the brush stroke is final; no correcting. Light ink first for structure, then darker ink, then the darkest accents and dots (moss dots, eyes) last; colour washes, if any, after the ink.
- Pen and ink with wash: light pencil drawing, ink line, then washes light to dark, then final dark accents; erase the pencil once the ink is dry.

### 6. Finishing (summary)
Last dark dots/accents, then the seal (red chop) and inscription; Chinese paintings are then mounted (backed with paper and made into scrolls or albums). Pen drawings: erase pencil, final accents, scrape highlights [S22]. See `FINISHING.md`.

### Engine model (ink)
**State:** `water` (flow layer), `ink` suspended, `ink_fixed` (deposited carbon, never lifts), `paper_fibre` (an oriented-fibre texture map giving anisotropic, branching diffusion) and `sizing` (0 raw..1 sized). MoXi uses a lattice-Boltzmann flow over paper with a *flow layer*, *surface layer* and pinning sites that block flow at the boundary [S2]; numpy can approximate it with anisotropic diffusion weighted by fibre direction and a pinning threshold that stops the front where water is low.
**Brush model:** per-bristle ink and water loads across the tuft (tip darker, belly more watery: the loading from [S21]); Strassmann's "hairy brushes" model the brush as a row of bristles each carrying its own ink, depleting over the stroke [S29]. Bristles run out at different times → flying white; speed raises separation.
**Dab:** deposit ink per bristle by pressure (width from pressure via the cone shape of the tuft: footprint grows from tip to belly); release water proportional to wetness; on raw paper, spread happens in `step`; on sized paper, almost none.
**Render:** carbon ink is near-neutral: `R = paper * exp(-k * ink_fixed)` (Beer-like darkening) plus a faint darker rim at the pinned boundary.
**Pen tool:** a nib with width `w = w0 + k*pressure` (flexible steel), constant (technical), or direction-dependent (broad/reed nib: width depends on the angle between stroke and nib edge); no spreading on sized paper; small chance of a blot at slow starts.
**Tools:** `brush_chinese` (load: tip/belly tones), `brush_side`, `pen_nib`, `pen_reed`, `pen_tech`, `wash_brush`, `scraper`.
**Priorities:** (1) tip-to-belly loaded brush with pressure-width and flying white, (2) pen nib with pressure width and hatching helper, (3) diffusion on raw xuan with fibre texture and pinned rim, (4) ink washes (reuse watercolour with one neutral pigment).

---

## Charcoal

### 1. Materials
- **Vine/willow (natural):** burnt sticks; vine is dark grey, willow blacker and denser; soft, medium, hard; lighter, irregular lines; "easily removed by dusting and by erasing" [S12]. Fragile and dusty [S13].
- **Compressed:** charcoal particles with "a binder such as clay, gum or wax"; denser, more uniform strokes and richer blacks, harder to erase, grades HB–6B [S12]; can be sharpened or used on its side for broad strokes [S13].
- **Powdered charcoal** for toning large areas; **charcoal pencils** for detail [S12].
- Matte surface that reflects little light [S13]; ranges from "intense matt black to very light greys" [S13]. Charcoal dust "catches in the paper's texture" [S13]. No mixing; tone builds by layering and smudging.

### 2. Supports
Laid or textured drawing paper (Ingres-type laid lines show in every tone), smooth Bristol for fine work, toned papers for working both ways with white chalk; the author of [S12] prefers 140 lb watercolour paper because its texture "helps to create very interesting marks".

### 3. Tools and marks
- **Stick tip:** line, sharp at a fresh broken edge [S12]; **side:** broad band whose texture is the paper's tooth [S13].
- **Fingers, chamois, stump (rolled paper) and tortillon:** smear into continuous tone; fingers "expand the mark-making capabilities of the media from just line work" [S12].
- **Kneaded (putty) eraser:** lifts by dabbing, shaped to a point for highlights; **hard eraser:** clean whites; the eraser's pressure "will determine the tone" [S12]. **Erasing is drawing**: subtractive drawing from a toned field [S12].
- **Water** on compressed charcoal gives line-and-wash effects [S12]. White chalk/Conté for lights [S12].

### 4. Visual signatures
- **Tooth catching:** light pressure deposits only on the paper's high points, leaving speckled white in the hollows; heavy pressure fills more hollows; fully saturated tooth stops taking more [S13][S27].
- **Smudged tone** with soft gradients and fingerprints of the blender.
- **Erased marks** with soft or hard edges, ghost lines of earlier attempts (pentimenti), since vine never erases fully clean.
- **Velvety matte blacks**, no sheen [S13].
- Gestural, broken line with varying pressure.

### 5. Order of work
Tone the paper (powdered charcoal) or start white; block in large shapes and tones quickly; add detail with harder sticks or pencils; refine with erasers; reserve or add whites; fix in layers and at the end [S12].

### 6. Finishing (summary)
Last darkest accents with compressed charcoal, crisp lifted highlights, final fixative (which darkens slightly) [S12][S11]. See `FINISHING.md`.

### Engine model (dry media, shared by charcoal, graphite, pastel)
**State:** `dep` (deposited medium amount, per pixel; for pastel a colour per pixel too), `loose` (unbound surface dust, smudgeable; fixative converts it to bound), `tooth_left` = `tooth_capacity(paper_h) − dep` [S27], `sheen` (graphite only), `fixed` (amount locked by fixative).
**Stick model (Sousa & Buchanan [S27]):** the stick has hardness, a contact shape (tip vs side: a thin ellipse vs a wide rectangle following the angle) and wears down. Deposit at a pixel = f(pressure, hardness, paper height above the local contact plane), capped by `tooth_left`. Light pressure touches only the peaks of `paper_h`; heavy pressure lowers the contact plane into the hollows.
**Blender (stump, finger, chamois):** move `loose` along the stroke (advection + blur), push some into hollows (filling the speckle), slightly reduce total [S27].
**Eraser:** remove `loose` first, then `dep` scaled by binder (vine lifts nearly fully, compressed partially [S12][S13]); kneaded = soft-edged dab lifting a fraction per touch; hard = crisp, full lift; leaves a faint ghost.
**Render:** `paper_tone * (1 − dep * darkness)` with paper grain shading; matte (no specular).
**Charcoal tools:** `vine_tip`, `vine_side`, `compressed_tip`, `compressed_side`, `powder` (wide soft deposit), `stump`, `tortillon`, `finger`, `chamois`, `kneaded`, `hard_eraser`, `white_chalk`.
**Priorities:** (1) tooth-capped deposit on a paper height field, (2) side vs tip contact shapes, (3) smudge (loose layer), (4) erasers as drawing tools, (5) fixative.

---

## Graphite pencil

### 1. Materials
Graphite mixed with clay, extruded and fired (Conté's process) [S10]. "A higher proportion of graphite produces harder, more silvery tones" and "a greater amount of clay yields softer and blacker pencils" (as written by the Met; most manufacturers describe more clay as harder, so treat the direction as contested and model hardness by grade) [S10]. Jackson's states that more clay makes the lead harder and lighter [S13]. Grades run from 9H (lightest) to 9B (darkest), HB in the middle [S10]. Flat particles slide easily, so marks look shiny in raking light, which distinguishes graphite from black chalk [S10]. Easy to remove: erasers and scrapers lift it for corrections and highlights [S10]. Less dusty than charcoal and adheres well; soft grades benefit from fixative [S13].

### 2. Supports
Smooth (Bristol, hot-pressed) for fine tonal work, medium-tooth drawing paper for most work, vellum historically [S10].

### 3. Tools and marks
- **Point:** narrow, even line [S10]; sharp vs blunt point; line weight from pressure and tilt.
- **Side of a soft pencil** for broad tone [S10].
- **Hatching** (parallel strokes) and **cross-hatching** (overlaps in another direction) to build tone [S10]; contour hatching following form; scumbling (small circles).
- **Stump** (rolled paper or cotton) for smooth modulated tone [S10].
- **Erasers** for correction and to "reveal bright paper for highlights" (reduction drawing) [S10]; kneaded, hard, electric/pen erasers.
- **Indenting** (impressed lines with a stylus that stay white under later tone).

### 4. Visual signatures
- **Shine/sheen** in dark passages under raking light, strongest with soft grades and burnishing [S10][S13].
- Tooth speckle at light pressure, filled hollows at high pressure; **burnishing** (high pressure or hard over soft) flattens tooth, giving a shiny slick dark that refuses more graphite.
- Hatch direction readable in the tone; crisp line edges; ghost lines from erasing.
- Darkest graphite is still mid-dark grey compared with charcoal's black [S13].

### 5. Order of work
Light construction lines with a hard grade, establish big value shapes, build tone with progressively softer grades, blend where wanted, erase lights, finish with darkest accents and crisp edges.

### 6. Finishing (summary)
Clean the margins, sharpen edges, last darkest accents, lift highlights, optional fixative for soft grades [S13]. See `FINISHING.md`.

### Engine model (graphite)
Shared dry-media model with: grade → (hardness, darkness per deposit, sheen) table from 9H to 9B; very low `loose` (little dust: smudging needs a blender tool); `sheen` accumulates with deposit and pressure, and `burnish` reduces `tooth_left` to near zero [S27]. Render: `paper*(1−dep*k_grade)` plus a view-dependent specular from `sheen` under the `look` light (a grey shine when the raking light is on). Tools: `pencil_<grade>` with `point: sharp|blunt`, `pencil_side`, `stump`, `kneaded`, `hard_eraser`, `stylus` (indent: sets `paper_h` locally low so later strokes skip it), and a `hatch` intention (parallel strokes at a set angle and spacing, with a second pass for cross-hatching, clipped to a region and modulated by target value).
**Priorities:** (1) grade table + pressure → deposit on tooth, (2) hatch/cross-hatch intention, (3) sheen in render, (4) erasers, (5) stylus indent.

---

## Soft pastel and oil pastel

### 1. Materials
- **Soft pastel:** pigment with "only a minimal amount of binder", so it stays powdery; diffuse, light-scattering surfaces; fragile [S11]. High-keyed brightness and a chalky matte surface [S11]. Mixing is mostly **optical**: colours laid side by side or over each other with underlayers showing through; Degas placed complementary hues side by side in thick layers or overlapping vertical strokes [S11]. Some blending by finger or stump.
- **Oil pastel:** pigment in a non-drying oil and wax binder; buttery, slightly glossy, never fully dries, blends by pressure and heat, can be scraped (sgraffito) and thinned with solvent (S37, cited).

### 2. Supports
Toned pastel papers with tooth (laid "Ingres" or honeycomb-textured), sanded papers and boards (hold many layers), and Degas's inexpensive machine-made wood-pulp paper chosen for its colour and rough texture, mounted on board [S11]. The paper tone shows through and works as a colour in the picture.

### 3. Tools and marks
- Stick **tip/edge** for lines and hatching; **side** for broad fields that break over the tooth.
- Degas handled the sticks "like drawing tools": linear marks, zigzags, stumped powder [S11].
- Stump, finger, chamois for blending; kneaded eraser and brush for lifting dust; workable fixative between layers to restore tooth.
- Scumbling: light pressure of a light colour over a dark layer so the dark shows through the broken top layer.

### 4. Visual signatures
- **Broken colour over tooth:** the top colour catches the peaks, paper or underlayer shows in the hollows.
- **Scumbles** and **optical mixtures** of side-by-side strokes [S11].
- **Chalky, velvety matte surface** with bright light colours [S11].
- Paper colour visible throughout; strokes stay visible as strokes.
- Once the tooth fills, new colour slides and smears instead of sticking (that is when fixative is used).

### 5. Order of work
Choose a paper tone; lay in big masses with the side of hard pastels, dark to light and lean to heavy (hard pastels first, softest last because soft pastel fills the tooth); fix lightly between layers where needed; build to the lights; final accents in the softest sticks.

### 6. Finishing (summary)
Last bright accents with soft sticks left unfixed, because fixative darkens pastel and impairs its high-keyed brightness [S11]; Degas fixed only selected areas, as a barrier between layers, never whole compositions [S11]. Frame under glass with a spacer. See `FINISHING.md`.

### Engine model (pastel)
Shared dry-media model with **colour per deposit layer**: keep up to N=3 stacked `(colour, coverage)` slots per pixel, or a single colour that changes by **coverage-weighted optical mix** when the top layer is broken (`render`: `top*cov + below*(1−cov)` in linear light, not KM, since the particles sit side by side). Tooth capacity is large on sanded paper and small on laid paper; when `tooth_left` hits zero, deposits smear (`loose` rises). `fixative` restores a fraction of tooth and darkens/desaturates (see FINISHING). Render: matte, slight lift in value and lower contrast in darks (powdery scatter). Tools: `hard_pastel_side`, `hard_pastel_tip`, `soft_pastel_side`, `soft_pastel_tip`, `stump`, `finger`, `chamois`, `kneaded`, `workable_fix`. **Oil pastel** variant: wet-like state (`wet` stays 1), subtractive `kmix` blending by pressure, a waxy low sheen, `scraper` for sgraffito, `solvent` brush to dissolve into a wash.
**Priorities:** (1) coverage-over-tooth deposit with per-layer colour, (2) side vs tip, (3) optical render, (4) tooth saturation and workable fixative, (5) oil-pastel variant.

---

## Gouache

### 1. Materials
Like watercolour, gum arabic binder, but larger particles and a higher pigment-to-binder ratio, often with opacifiers such as chalk or titanium white [S18]. **Opaque**, dries to "a flat, matte finish" [S18]. **Drying shift:** light colours dry darker and dark colours dry lighter [S18]. **Reactivatable** with water, which can disturb layers beneath (acrylic gouache cannot be reactivated) [S18]. Mixing subtractive and physical; light can go over dark [S18].

### 2. Supports
Watercolour paper, Bristol, illustration board and toned surfaces [S18].

### 3. Tools and marks
Rounds and flats (synthetic), small rounds for detail; flat, even fields from a well-mixed, creamy load; dry-brush for texture; wet-in-wet only briefly since it dries fast. A wet brush over dry gouache picks up the colour below and muddies the stroke.

### 4. Visual signatures
Matte, flat opaque fields with crisp edges; light over dark; poster-like clarity; slight streakiness where a field was laid in strokes; muddied edges where an upper layer reactivated the one below; streaky thin passages that behave like watercolour when diluted. "Gouache is about building" light [S18].

### 5. Order of work
Background and big flat shapes first (often mid tones), then darker shapes, then lights and details on top (any order works since it is opaque [S18]); final light accents last. Keep layers thin to avoid cracking.

### 6. Finishing (summary)
Last light accents and edge crispening; usually not varnished, framed under glass [S18].

### Engine model (gouache)
Reuse the watercolour state with **high S (scattering) pigments** so a layer hides what is below (KM with large S), much shorter flow distances (thicker paint), no edge darkening at normal dilution, and two specific behaviours: (1) **reactivation**: a wet dab over a dry area moves a fraction of the dry layer into the brush (`pickup` from dry paint, which oil does not do), (2) **drying shift**: `render` while wet shows lights slightly lighter and darks slightly darker than dry [S18]. Matte render (no specular, slight value lift in darks). Tools: `round`, `flat`, `detail_round`, `dry_brush`. **Priorities:** (1) opaque KM layer with drying shift, (2) reactivation pickup, (3) matte render.

---

## Egg tempera

### 1. Materials
Egg yolk binder with water; dries very quickly, so work goes section by section [S15]. Does not blend; transitions are built with crosshatching and linear strokes [S15]. Layering gives opacity, translucency and opalescence [S15]. Applied thin; heavy application cracks and flakes [S15]. Dries to a slightly glossy (satin) finish [S15]. Cures over 6–12 months and is usually left unvarnished [S15].

### 2. Supports
Rigid wooden panel (poplar in Italy) sized with rabbit-skin glue and several coats of gesso sanded smooth [S15][S14]: a brilliant white, absorbent, smooth ground. Water gilding needs a very smooth gesso [S14].

### 3. Tools and marks
Small soft rounds (sable), used almost dry: small hatched strokes, parallel and cross-hatched; burnisher (agate) and gilder's tip for gold leaf; punches for tooled patterns in the gold [S14]; stylus for incised outlines.

### 4. Visual signatures
- **Small hatched strokes** visible at close range, building form through many thin layers [S15].
- **Layered translucency**: lighter, more opaque modelling over a green **verdaccio** underlayer in flesh, which shows through as cool shadow [S14].
- No soft blending; crisp edges; clear, luminous, slightly cool colour.
- **Gold ground:** burnished water-gilt halos and backgrounds with **stippled punchwork** that shimmers [S14].

### 5. Order of work (Cennini-based reconstruction [S14][S38])
Panel → glue size → gesso, sanded smooth → drawing (charcoal, fixed with ink, shading and hatching in ink) → translucent lead-white imprimatura to mute the drawing → **gilding** (bole, gold leaf, burnishing; mordant gilding for fine rays) and punchwork → background in thin layers → **verdaccio** (terre verte and lead white) under flesh → flesh in several premixed tones, shadows and midtones in earths → fine red accents (vermilion cheeks) → in that reconstruction, oil glazes on the robes, then highlights re-strengthened in tempera [S14].

### 6. Finishing (summary)
Final hatching of highlights and accents, sometimes oil glazes (then restored highlights) [S14]; painted "gold" details in lead-tin yellow [S14]; usually no varnish [S15].

### Engine model (tempera)
**State:** opaque/translucent layered films with **instant drying** (each dab dries before the next stroke: no wet mixing), `gold` mask with `burnish` and `punch` maps, smooth gesso support (no tooth). **Dab:** small, thin, nearly opaque-to-translucent line with hard edges; KM `km_layer` per stroke with a small thickness, so tone builds by repetition. **Hatch intention:** fill a region with short parallel strokes whose density and direction follow form, multiple passes with rotating angle. **Render:** satin sheen; gold rendered as a metallic surface: base gold colour, a strong view-dependent specular where burnished, small dark dimples where punched. **Tools:** `small_round`, `hatch`, `gild` (lay leaf in a region), `burnish`, `punch` (pattern), `stylus` (incised line). **Priorities:** (1) instant-dry thin layers + hatch intention, (2) verdaccio workflow via existing layers, (3) gold ground with burnish/punch render.

---

## Acrylic

### 1. Materials
Pigment in an acrylic polymer emulsion; dries quickly by evaporation into a flexible, water-insoluble film. The milky wet binder clears as it dries, so colours shift **darker** on drying (S35, cited, not read). Glazes with medium; impasto with gels; matte or gloss depending on medium. Once dry, it cannot be reactivated (as with acrylic gouache [S18]).

### 2. Supports
Canvas, panel, paper; acrylic gesso.

### 3. Tools and marks
Synthetic brushes and knives like oil; airbrush, sponge, pouring.

### 4. Visual signatures
Crisp edges and hard-edged layering (dries before blending), flat or glossy fields, uniform colour fields, gel impasto that keeps sharp peaks.

### 5. Order of work
Fast layering, any order; often a toned ground, block-in, layers, glazes.

### 6. Finishing
Isolation coat, then a removable varnish (gloss/satin/matte) to even sheen (S35, cited).

### Engine model (acrylic)
Oil instrument with parameters: drying fast (`wet` decays in a few episodes), dark shift on drying (`render` darkens dry pixels a few percent from their wet value), no wet blending after drying, sheen per medium. **Priority:** low (parameter preset of oil).

---

## Fresco

### 1. Materials
**Buon fresco:** "alkaline-resistant pigments, ground in water, are applied to wet plaster" (intonaco); no separate binder; over hours the lime reacts with air and the carbonation "fixes the pigment particles at the plaster's surface" [S19]. Some pigments are incompatible with lime [S19]. **Fresco secco:** paint with a binder on dry plaster, used for details and incompatible pigments [S19].

### 2. Supports
Wall: rough **arriccio** undercoat, then the day's **intonaco** in sections (**giornate**, "as much as can be completed in a day") [S19].

### 3. Tools and marks
Soft brushes, watery paint; cartoons transferred by pouncing or incising; trowel.

### 4. Visual signatures
Matte, chalky, high-key colour; visible seams between giornate; watercolour-like transparency in thin passages; limited palette of earths and lime-fast pigments; secco details that flake over time.

### 5. Order of work
Arriccio, transfer of the composition, then section by section from the top, painting each intonaco while wet; secco details last [S19].

### 6. Finishing
Secco touches on dry plaster [S19]; no varnish.

### Engine model (fresco)
Watercolour-like instrument on a `plaster` support with a `giornata` mask: paint only sticks where the current giornata is "wet"; after `step` closes the giornata, further paint is secco (lower adhesion, slight opacity). Render matte with a faint value lift; seam lines where giornate meet. **Priority:** low.

---

## Woodblock print (ukiyo-e)

### 1. Materials
Water-based colours (historically plant and mineral pigments) brushed onto carved cherrywood blocks, with **nori** (rice-flour paste) dotted on the block for an even spread [S16][S17]. Pigment is brushed into the wood grain with hake brushes [S16]. Mixing is **layered**: one block per colour, printed one at a time, about ten impressions or more for an average colour print [S17]; commercial prints used about a dozen blocks, private commissions around fifteen [S16]. The lightest colour is usually printed first, darker ones on top [S16].

### 2. Supports
Kōzo-fibre washi sized with **dōsa** (animal glue, with alum) to stop pigment spreading uncontrollably [S16]; printed damp; strong enough to be pulled off the block [S17]. Its fibrous texture and the wood grain both show in flat areas.

### 3. Tools and marks
- **Keyblock:** the carver cuts away wood along the artist's brushed lines, leaving the outlines raised: the keyline [S16][S17].
- **Colour blocks** cut from proofs, each with **kentō** registration notches (corner *kagi*, long edge *hikitsuki*) [S16][S17].
- **Baren:** coiled disc in a bamboo-leaf sheath for pressing; heavier pressure gives darker colour [S16].
- **Bokashi:** graduated shading by brushing water and pigment so it diffuses into an area marked by a waterline (Hiroshige skies) [S16].
- Blind embossing (karazuri) and mica are other effects (not covered by the read sources).

### 4. Visual signatures
- **Flat colour fields** "in relatively large flat areas bordered by the fine line drawing of the design" [S17].
- **Keyline:** crisp black outlines of consistent character, carved from a brushed drawing, so they keep a brush's swell and taper.
- **Bokashi gradients** (top of sky, horizon).
- **Baren texture:** fine mottling and the wood grain visible in large fields [S16]; paper fibres.
- **Registration slips:** colour shapes offset by a hair from the keyline, small gaps or overlaps.
- **Overprinting:** where blocks overlap, colours combine subtractively (transparent water colours).

### 5. Order of work
Artist's line drawing → keyblock carved → key proofs → artist colours the proofs → one block per colour → printing light to dark, keyline usually first or last depending on workshop, one impression per colour, bokashi on its block [S16][S17].

### 6. Finishing
None beyond the impression: the print is finished when the last block is printed; the publisher's and artist's seals and signature are part of the blocks.

### Engine model (woodblock)
Not a brush medium: an instrument that **renders blocks**.
**State:** an ordered list of blocks, each a binary/soft mask (carved shape), a colour, a `bokashi` gradient spec (direction, start, end, falloff), a pressure, and a registration offset; washi support with `paper_h` fibre texture; a wood-grain texture per block.
**Carving:** the keyblock mask comes from Teodor's line strokes (brush-drawn lines, thresholded: preserving brush taper); colour blocks come from region polygons or from the schema's flat value segmentation, *drawn by Teodor*, not filled automatically, to respect "it must be a painting".
**Print step (impression):** `ink = colour * pressure * (0.85 + 0.15 * grain) * (0.9 + 0.1 * paper_h)`, edge slightly heavier where pigment pools at the block edge; transparent layer composited with KM over the paper and earlier impressions; registration jitter of 0–2 px per block. Mizuno et al. built virtual carving and multi-block printing systems along these lines [S30].
**Bokashi:** multiply the block's ink by a smooth ramp (with slight unevenness from the brush) inside the mask.
**Tools:** `carve_key` (line strokes become raised lines), `carve_block` (region), `ink_block` (colour, bokashi), `baren` (pressure), `print` (impression with registration), `emboss` (blind: modifies `paper_h` only).
**Priorities:** (1) block masks + transparent impressions with grain and paper texture, (2) keyline from brush strokes, (3) bokashi, (4) registration jitter, (5) embossing.

---

## Engine priority list

Ordered by value to the paintings divided by cost, given Robert's note that the surface reads as "a digital filter" (`docs/handover.md`).

1. **Instrument interface and shared support model** (`paper_h`, `absorbency`, `tooth`, `tone`; `kmix` + `km_layer`; per-pigment K/S from over-white/over-black colours [S1]). Everything below plugs into it. Port v7 oil as the first instrument without changing its look.
2. **Finishing stage** (`finish …` commands, `FINISHING.md`): cheap, applies to every medium, and adds the surface optics (gloss, varnish saturation, fixative dulling) that make a picture read as an object.
3. **Watercolour** (Curtis-lite [S1]): wet mask, water, suspended/deposited pigment, edge darkening, granulation, KM glazes, dry-brush; then back-runs and lifting. The largest new visual vocabulary.
4. **Dry media** (one instrument, three presets: charcoal, graphite, soft pastel): tooth-capped deposit on a paper height field, tip vs side, smudge, erasers, graphite sheen, pastel optical layering [S27]. Cheap and very different from paint.
5. **Ink**: tip-to-belly loaded Chinese brush with pressure width and flying white [S21][S29]; pen nib with pressure width and a hatch intention; diffusion on raw xuan [S2].
6. **Oil refinements**: two-constant KM or Mixbox [S3], `fat`/`sheen` with sinking-in, bristle furrows and end ridges [S24], filbert/bright brushes.
7. **Gouache** (watercolour state with high-S pigments, reactivation, drying shift, matte) [S18].
8. **Woodblock** (blocks, keyline from brush strokes, bokashi, baren grain, registration) [S16][S17][S30].
9. **Egg tempera** (instant-dry thin layers, hatching intention, gold ground) [S14][S15].
10. **Acrylic, fresco, oil pastel** as parameter presets of existing instruments.

---

## Sources

Read for this document:
- [S1] C. J. Curtis, S. E. Anderson, J. E. Seims, K. W. Fleischer, D. H. Salesin, "Computer-Generated Watercolor", SIGGRAPH 1997. https://grail.cs.washington.edu/projects/watercolor/paper_tiny.pdf *(read)*
- [S2] N. S.-H. Chu, C.-L. Tai, "MoXi: Real-Time Ink Dispersion in Absorbent Paper", ACM TOG 24(3), SIGGRAPH 2005. https://history.siggraph.org/learning/moxi-real-time-ink-dispersion-in-absorbent-paper-by-chu-and-tai-2 ; implementation talk: https://history.siggraph.org/wp-content/uploads/2023/01/2005-Talsk-Chu_MoXi-Real-Time-Ink-Dispersion-in-Absorbent-Paper.pdf *(talk read; paper not read this session: the three-layer and pinning description of the paper is from the literature)*
- [S3] Š. Sochorová, O. Jamriška, "Practical Pigment Mixing for Digital Painting" (Mixbox), ACM TOG 40(6), 2021. https://dcgi.fel.cvut.cz/wp-content/wpallimport-dist/publications/pdf/publications-2021-sochorova-tog-pigments-paper.pdf *(read)*
- [S4] Smithsonian Museum Conservation Institute, "What does a Varnish do for a Painting?" https://mci.si.edu/painting-varnishes *(read)*
- [S5] National Gallery of Art, Conservation Science, "Varnishes for Paintings". https://nga.gov/conservation/science/varnishes-for-paintings.html *(read)*
- [S6] Winsor & Newton, "Fat over lean rule explained". https://winsornewton.com/blogs/masterclass/fat-over-lean-rule-explained *(read)*
- [S7] Royal Talens, "The construction and finishing of an oil painting". https://www.royaltalens.com/blogs/oil-paint/layered-painting *(read)*
- [S8] Blick Art Materials, "Hot Press vs. Cold Press vs. Rough Press: How to Choose the Right Watercolor Paper". https://www.dickblick.com/learning-resources/buying-guides/paint/choosing-watercolor-paper/ *(read)*
- [S9] Jackson's Art, "A Guide to Watercolor". https://www.jacksonsart.com/en-us/a-guide-to-watercolor *(read)*
- [S10] The Met, "Materials and Techniques: Drawing, Graphite". https://www.metmuseum.org/en/perspectives/materials-and-techniques-drawing-graphite *(read)*
- [S11] The Met, "Precious Powder: The Fragility of Degas's Pastels" (conservation story, 2020). https://metmuseum.org/about-the-met/conservation-and-scientific-research/conservation-stories/2020/degas-woman *(read)*
- [S12] Painters Online, "Back to black: how to use charcoal". https://www.painters-online.co.uk/tips-techniques/drawing/articles/back-to-black-how-to-use-charcoal/ *(read)*
- [S13] Jackson's Art Blog, "Difference between graphite and charcoal" (2018). https://jacksonsart.com/blog/2018/08/23/difference-between-graphite-and-charcoal/ *(read)*
- [S14] Fitzwilliam Museum, Hamilton Kerr Institute, "C15th Tempera Reconstruction". https://www.hki.fitzmuseum.cam.ac.uk/node/137 *(read)*
- [S15] WebExhibits, Pigments through the Ages, "Egg tempera". https://www.webexhibits.org/pigments/intro/tempera.html *(read)*
- [S16] British Museum blog, "How to make a woodblock print like Hiroshige". https://www.britishmuseum.org/blog/how-make-woodblock-print-hiroshige *(read)*
- [S17] Asian Art Museum (San Francisco), "The ukiyo-e woodblock printing process". https://education.asianart.org/resources/the-ukiyo-e-woodblock-printing-process/ *(read)*
- [S18] Blick Art Materials, "Gouache vs. Watercolor: What's the Difference?" https://www.dickblick.com/learning-resources/how-to/gouache-vs-watercolor/ *(read)*
- [S19] Wikipedia, "Buon fresco". https://en.wikipedia.org/wiki/Buon_fresco *(read)*
- [S20] Ashmolean Museum (Cabinet, Oxford), "The four treasures of the study: ink, inkstone, brush, and paper". https://www.cabinet.ox.ac.uk/node/6964 *(read)*
- [S21] Asian Art Museum, "Inking Techniques" (education handout). https://education.asianart.org/wp-content/uploads/sites/6/2019/09/Inking-Techniques.pdf *(read)*
- [S22] The Met, "Materials and Techniques: Drawing, Ink". https://www.metmuseum.org/en/perspectives/materials-and-techniques-drawing-ink *(read)*
- [S23] Robert Genn, The Painter's Keys, "Smoke, mirrors and viewfinders". https://painterskeys.com/smoke/ *(read)*

Cited, not read this session (standard references; verify before quoting):
- [S24] W. Baxter, J. Wendt, M. C. Lin, "IMPaSTo: A Realistic, Interactive Model for Paint", NPAR 2004. https://gamma.cs.unc.edu/IMPASTO/publications/Baxter-IMPaSTo_Print-NPAR04.pdf
- [S25] W. Baxter, V. Scheib, M. C. Lin, D. Manocha, "dAb: Interactive Haptic Painting With 3D Virtual Brushes", SIGGRAPH 2001. https://history.siggraph.org/?p=116942
- [S26] W. Baxter, "Physically-Based Modeling Techniques for Interactive Digital Painting", PhD thesis, UNC 2004 (includes the viscous paint model and Kubelka–Munk rendering). https://wwwx.cs.unc.edu/~geom/papers/documents/dissertations/baxter04.pdf ; W. Baxter, Y. Liu, M. C. Lin, "A Viscous Paint Model for Interactive Applications", 2004. https://www.cs.unc.edu/techreports/04-006.pdf
- [S27] M. C. Sousa, J. W. Buchanan, "Observational Model of Blenders and Erasers in Computer-Generated Pencil Rendering", Graphics Interface 1999 (https://graphicsinterface.org/proceedings/gi1999/gi1999-21), and "Observational Models of Graphite Pencil Materials", Computer Graphics Forum 19(1), 2000 (https://diglib.eg.org/handle/10.2312/8605).
- [S28] A. Majumder, M. Gopi, "Hardware Accelerated Real Time Charcoal Rendering", NPAR 2002. https://www.cs.unc.edu/Research/ootf/publications/Majumder_NPAR02.pdf
- [S29] S. Strassmann, "Hairy Brushes", SIGGRAPH 1986. https://history.siggraph.org/?p=116042
- [S30] S. Mizuno et al., virtual woodblock carving and multi-colour printing (e.g. "Improvement of the printing model in multi-colored and multi-woodblock virtual printing", Eurographics short papers 2001; "Carving, Painting, and Printing with a Pen Tablet", 2005). https://diglib.eg.org/items/79a2119a-86bd-4b47-bcd4-090c256c647f ; https://diglib.eg.org/items/1d8eb5e3-51ca-41cc-a6e4-ccca0df22c3c
- [S31] R. D. Deegan et al., "Capillary flow as the cause of ring stains from dried liquid drops", Nature 389, 1997. https://www.doi.org/10.1038/39827
- [S32] T. Van Laerhoven, F. Van Reeth, "Real-time Simulation of Watery Paint", Computer Animation and Virtual Worlds 2005; "Real-time Simulation of Thin Paint Media", 2006. https://documentserver.uhasselt.be/handle/1942/2083 ; https://history.siggraph.org/?p=99975
- [S33] N. Chu, W. Baxter, L.-Y. Wei, N. Govindaraju, "Detail-Preserving Paint Modeling for 3D Brushes", NPAR 2010. https://microsoft.com/en-us/research/wp-content/uploads/2010/06/PaintModel_NPAR_2010.pdf
- [S34] D. Mould et al., crayon/wax-medium rendering (Computer Graphics Forum). https://people.scs.carleton.ca/~mould/papers/crayon-cgf.pdf
- [S35] Winsor & Newton, "Acrylic colour shift". https://winsornewton.com/blogs/guides/acrylic-colour-shift
- [S36] Wikipedia, "Xuan paper"; Inkston, "Shu Xuan sized or cooked Xuan paper". https://en.wikipedia.org/wiki/Xuan_paper ; https://www.inkston.com/shops/paper/sized-xuan-paper/
- [S37] R. Mayer, *The Artist's Handbook of Materials and Techniques* (5th ed., 1991); M. Doerner, *The Materials of the Artist and Their Use in Painting* (rev. ed., 1949). Brush shapes, oil pastel, general practice.
- [S38] Cennino Cennini, *Il Libro dell'Arte*, trans. D. V. Thompson (1933). https://ia801802.us.archive.org/20/items/illibrodellarte1933cenn/illibrodellarte1933cenn.pdf
