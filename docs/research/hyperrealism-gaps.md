# Hyperrealism gaps: round 19 against what the style produces

Written 2026-11-27, after round 19 (*The Thumbnail*, `rounds/19-the-thumbnail/`, work dir `../teodor-work/19`) was compared with contemporary hyperrealist pencil drawings and found far short of them. The examples (described, not downloaded or measured: they are in copyright) were a young woman's head and hand holding a twist of braids, a crying child's face streaming with water, and a man's face covered in cracked plaster. What they share: a full value range from near-black to bare paper; photographic skin with pores, sheen and droplets that have their own rims and highlights; single hair strands and braids; crisp specular highlights; smooth gradients without blotches; hands with real anatomy; one subject isolated on white paper; no fog.

This document lists every gap found, in priority order, with the evidence, the root cause, a proposed fix, an acceptance test to pass before the drawing is redone, and a rough effort. It is analysis only: no engine code was changed.

Labels, as in `docs/research/process.md`: **[M]** measured here; **[S]** a named source; **[H]** a judgement of this document.

## 0. Rulers and method

**The script.** `tools/analysis/hyperreal_gaps.py` (run: `python3 tools/analysis/hyperreal_gaps.py --work ../teodor-work/19 --photo <photo>`). It measures:
- value percentiles and the share of pixels below L* 20, 30 and 40;
- texture energy by scale: the RMS, in L*, of a difference of Gaussians G(s) - G(2s), with s in **millimetres of the subject** (face-mm or hand-mm). This lets a photograph and a render of different pixel sizes be compared at equal subject scale;
- specular highlights: blobs at least 20 L* above their 2 mm surround and smaller than 2 mm, plus the largest such prominence;
- the 10-90% rise of strong edges;
- texture inside each declared element of the drawing;
- how the sheet's area is spent.

Every threshold is a judgement **[H]**.

**The photograph.** NASA JSC still `jsc2003e41874`: a studio head-and-shoulders portrait of an adult man, 2400 × 3000 px, by a NASA staff photographer. It is a US government work, so public domain. It was fetched from `images-assets.nasa.gov`, measured, and deleted. It was never shown, published or used as a reference, and it is a real person, so nothing of his likeness goes anywhere (rule 5).

At its pupil distance of 282 px, against a mean adult male interpupillary distance of about 64 mm, it holds **4.4 px per face-mm** **[M]**. Round 19's face, at 0.25-0.30 m from a camera with a focal length of 1718 px, holds about **6 px per face-mm** on the canvas **[M]**. The subject scales are therefore comparable.

The photograph is a conservative ruler: a soft-lit 2003 JPEG. A modern hyperrealist's reference, a close-up of 40-60 megapixels under hard light, holds several times more detail. Where round 19 fails against this photograph, it fails by more against the style.

**Tried and not used.** Two other sources were tried:
- Wikimedia Commons answered 429 (rate limit) and the Library of Congress 503. Neither was retried around (rule 10).
- Two NASA "hand close-ups" turned out to be photographs of a TV screen. They were discarded.

**No public-domain, high-resolution photograph of a hand was found this session.** That is an open item (G5's acceptance test needs one).

**The existing ruler.** `studio/targets.json` → `graphite-hyperrealism` (45 Library of Congress FSA/OWI photographs, `docs/calibration/graphite-hyperrealism.md`). The photographs are cached at about 624 px, and `eyes.measure` reads every image at 512 px on its long side (section G10).

## Summary, in priority order

| # | Gap | Key evidence [M] | Root cause | Effort |
|---|---|---|---|---|
| G1 | The reference holds almost none of a photograph's information | Skin texture at 0.25-2 face-mm: render 3-40% of the photo's; no specular in the skin; hair a flat cap; the schema then removed the darks | reference (renderer), process | XL |
| G2 | No darks | Final: 0.0% below L* 20, 0.2% below L* 30, p5 41. Photo: 16.7% below L* 20, p5 5.5. Ruler: p5 17, 29% below L* 33 | rules/docs, process, engine | M-L |
| G3 | Composition spends the sheet on fog | 73% of the sheet is flat mid-tone (photo 2.4%); the fist is 0.7% of the sheet; the face is upside down | composition | S (decision) |
| G4 | Wide lens at 0.3 m: the hand shrinks, the face swells | The hand appears at 0.41 face-lengths (canon 1.0); hand at 0.47× life, face at 1.2× life; about 19 mm lens at 12 in (+30% nose) | composition, reference | S |
| G5 | The hand: a straight, unopposed thumb and knobbed fingers read as a pointing finger | Spec thumb `[30,0,10,0,0]`; fingers' last joints 55°; thumb axis about 32° off vertical | reference (pose, mesh), process | M |
| G6 | The face: inverted, smooth, without darks, so it reads as a child and the grin doesn't read | Forehead texture 10-20% of the photo's; face p1 39; no specular (photo 4, up to 44 L*) | composition, reference, process | M |
| G7 | No tool draws a designed fine mark | `match`/`hatch` lay dashes and bands; 1 stylus intention in 287; strands, droplets, pores, lashes only by hand-written `strokes` | engine | L-XL |
| G8 | Process: whole-sheet blends before darks; details not related back | 3 full-sheet blends by ep 15; the fist has 5× the arm's texture at 0.4-0.8 mm; 39% of intentions were blends | process | S (rules) |
| G9 | Resolution and time | Hair-fine lines are 1.5 px at 5 px/mm; a face of 10^3-10^4 pores against 2,300 hand-placed strokes in the whole round; 8.5 h against about 200 h | engine, process | M |
| G10 | Measurement can't see the gaps | `eyes.measure` works at 512 px (1.25 mm per px on this sheet); "hard edges 18%, within range" while the drawing read as fog; no darks gate | engine (eyes), targets | M |
| G11 | The rules: likeness, tracing, references | Hyperrealism copies one photograph of one real person; rules 2 and 5 forbid that | rules | S (decision) + XL (G1) |

---

## G1. The reference holds almost none of what a photograph holds

You can't draw more than the reference holds. Round 19's reference was the mesh render (`main_scene_v1-19.png`), turned into a value schema (`plan/m/schema*.png`, `main_ref.npy`) and two tonal studies (`plan/m/face_study*`, `hand_study*`).

**Evidence [M].** The table compares the photograph's cheek with the round-19 forehead, all at equal subject scale (RMS L* of the band at scale s, in face-mm):

| s (face-mm) | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| photo, cheek | 0.22 | 0.38 | 0.62 | 1.03 | 1.75 | 1.71 |
| mesh render, forehead | 0.10 | 0.15 | 0.19 | 0.16 | 0.06 | 0.63 |
| schema, forehead | 0.05 | 0.09 | 0.14 | 0.15 | 0.08 | 0.50 |
| final drawing, forehead | 0.14 | 0.10 | 0.11 | 0.20 | 0.30 | 0.60 |

From 0.25 to 2 face-mm (the scale of pores, which are 0.06-0.37 mm² in area and 10-90 per cm² on the cheek [S: Flament et al. 2015, *Clin Cosmet Investig Dermatol*, PMC4337418]) the render holds 3-40% of the photograph's texture. The schema holds 5-25%.

- **Whole face** (features included): the photograph has 0.67 / 1.30 / 2.15 L* at 0.25 / 0.5 / 1 mm. The schema has 0.50 / 0.90 / 1.49, the final drawing 0.22 / 0.36 / 0.60.
- **Speculars:** the photograph's face has 4 (catchlights, nose, lip), with the largest standing 44 L* above its surround. The render has 3, all on the eyeball (`gloss` 0.9). The schema and the face study have 0. The final drawing has 0, the largest bright spot 21 L* above its surround.
- **Hair:** the photograph has strand texture of 0.55 / 0.98 / 1.24 L* at 0.125-0.5 mm and a spread of 12 L*. The render's "hair" scores high (0.97-1.87) only from its aliased cap edge and cylinder "strands" (`face_study_4x.png`, `main_ref.png`: sticks, not hair). In the final drawing the hair is a flat mass: spread 3.3 L*, p1 37.
- **Darks:** the render had them: 19% of the face and 5.3% of the sheet below L* 20. The schema removed them by plan (journal, phase 1: "nothing large is planned below L* 33"). The face's p1 went from 3 (render) to 22 (schema) to 39 (drawing).
- **Sharp edges:** the schema had 7.2% of its strong edges rising in under 0.3 mm; the final drawing has 0.2%.

**Root cause.**
- **Renderer** (`studio/v8/scene.py`, `human.py`): Lambert shading plus ambient occlusion plus one Phong lobe (`** 40`). `skin_gloss` defaults to 0. There are no normal or bump maps, so no pores or micro-wrinkles, and the skin colour texture is coarse and blocky (`render_face.png` crop: 10-20 px blocks). Hair is a streaked cap plus cylinders. There is no water and no refraction. `face.md` says it plainly: "the skin has no texture".
- **Process:** the schema compressed the render's values and softened it further (the orange-filter remap, f/16 blur, "lifted cirrus").

**Proposed fix.** Build a reference that can be drawn from (G11 explains why it must be a render):
1. **Skin:** a micro-normal map and a roughness map for the mesh. The detail comes from **anonymous CC0 or public-domain macro photographs of skin patches** (cheek, forehead, back of hand; a patch of skin is not a likeness), synthesised into tileable detail textures, or procedurally (pores as a Poisson-disc field at the measured density and size, plus micro-wrinkle noise oriented along Langer's lines). Add a two-lobe specular (a sharp oily sheen plus a broad lobe) and a rough subsurface approximation (a wrapped diffuse is already there as `wrap`).
2. **Hair:** strands as curves (thousands of thin cylinders or ribbons, grown along the existing `hair_streaks` flow field), with a Kajiya-Kay-style specular; braids as three interleaved strand bundles.
3. **Water:** droplets as refractive ellipsoids with a Fresnel specular, a dark rim and a bright caustic on the side away from the light (G7). Film and rivulets as height-field sheets.
4. **Optics:** a real depth of field (the round faked it in the schema), and rendering in tiles at the drawing's detail resolution (G9). The face's 4× render was killed for memory in round 19 (journal ep 16).
5. **Rule for the schema:** keep the render's values. Don't compress toward what the medium can reach; G2 gives the medium a deeper floor instead.

Files: `studio/v8/scene.py`, `human.py`, `raster.py`; MANUAL "Scene blockouts".

**Acceptance test (before the redo).** Render an invented head (MakeHuman CC0) at portrait distance under one hard light, and measure it with `hyperreal_gaps.py` against the public-domain portrait at equal face-mm scale:
- skin band energy at 0.25, 0.5, 1 and 2 face-mm each within ±35% of the photo's cheek;
- at least 3 speculars of prominence ≥ 30 L* in the face;
- face p1 ≤ 10 and at least 5% of the face below L* 20 under a hard light;
- hair strand energy at 0.125-0.5 face-mm ≥ 70% of the photo's, with an orientation coherence (structure tensor) ≥ 0.5 (to be added to the script);
- a viewer test: the render shown at thumbnail and at 1:1 beside a photograph crop, and called "photo or render?" no worse than chance by one fresh critic **[H]**.

**Effort.** XL: skin maps and specular M; strand hair L; water M; tiled render M.

## G2. No darks: the value range stops at L* 40

**Evidence [M].**

| | p1 | p5 | below L* 20 | below 30 | below 40 |
|---|---|---|---|---|---|
| final drawing (whole sheet) | 39.5 | 41.2 | 0.0% | 0.2% | 2.0% |
| schema | 27.5 | 35.7 | 0.0% | 1.9% | 9.5% |
| mesh render | 3.6 | 19.2 | 5.3% | 9.0% | 44% |
| public-domain portrait | 0.8 | 5.5 | 16.7% | 39.6% | 55% |
| LoC ruler (45 photos) | | 17.1 ± 12.7 | | 29% below L* 33 | |

Hair is the darkest mass in the examples: the photograph's hair has a p5 of 21.5, round 19's a p5 of 38.2.

**What the research says [S].**
- **Graphite alone** stops where its sheen takes over: "although graphite naturally draws with a black mark, it doesn't look black due to the surface sheen" (Sibley, "Drawing dark values", sibleyfineart.com/draw-with-mike-videos/dwm102). Past about Munsell value 4, draughtsmen switch to powder or black pencils (Vitruvian Studio, cited in the style doc).
- **Graphite can go further by cycles:** "Apply your 6B / Burnish with 2B / Then lightly spray the area with a workable fixative / Then repeat the operation as many times as you need to"; the fixative "dries with a matt finish, which provides an artificial tooth that will accept additional shading" (Sibley, same page). A finished drawing sprayed with matt fixative loses "much of the sheen" (Sibley, "Graphite v charcoal", sibleyfineart.com/_blog/2013/03).
- **Charcoal** gives "intense matt black" and willow "a rich, deep almost velvety black"; portraitists combine graphite (hair, eyes) with charcoal (Jackson's Art, "Difference between graphite and charcoal", 2018).
- **Which goes over which:** a realist charcoal portraitist reports that charcoal "layers really well over graphite and completely covers it", that "graphite will leak through charcoal", that powdered charcoal goes on "with a brush or q-tip", and that blacks deepen "the more layers you will build up", with at least three thin coats of matte workable fixative (Desdain Art, FAQ).
- **Measured floors** (`docs/calibration/charcoal.md`): 19th-century charcoal, conté and black chalk sheets reach a darkest 0.1% of L* 21.9-28.9, and the engine's compressed charcoal 24.6. In the graphite medium, carbon pencil reaches L* 31.6 blended (`graphite-hyperrealism.md`). Photographed fresh drawings on bright white bristol will be darker than 19th-century sheets **[H]**. No modern measurement exists in the repo.

**Conflict to flag (rule 6).** `docs/manual/graphite.md` says carbon "can't take" over dense graphite, so lay it first. The charcoal portraitist above says charcoal covers graphite well. Both can hold: unburnished graphite leaves tooth, burnished graphite doesn't. The engine's model (one shared tooth capacity `cap`, filled by any deposit) has no such distinction, and its values are tuned by eye. Follow the research: lay the darks first, as both sources allow, and calibrate "charcoal over light graphite" before relying on either claim.

**Root cause.**
- **Rules and docs.** The calibration note's "graphite stops near L* 40, carbon near 32" became a planning rule: the schema was built without darks.
- **Process.** All-over value bands and three full-sheet blends by episode 15 filled the tooth before any carbon (ep 60: "the darks did not move (the tooth is full)").
- **Engine and docs.** The graphite medium has no compressed charcoal or powder, and `workable` fixative (which restores tooth: `drymedia.py`, `fin_fixative`, `xcap`) is documented for graphite only as a finishing step. Round 19 used it once, at the end.

**Proposed fix.**
1. Add `charcoal_powder` (brushed base) and `compressed_charcoal` to the graphite medium, reusing the charcoal medium's measured tools.
2. Document and allow `finish fixative {"kind": "workable"}` mid-drawing in `docs/manual/graphite.md`, as the dark-building cycle: soft graphite or carbon, burnish two grades harder, workable fixative, repeat.
3. In `docs/styles/graphite-hyperrealism.md` and the calibration note, replace "darks stop at L* 36-41" with the measured floor of that recipe, and add the rule: **the schema keeps the reference's values; the darks are laid first, in carbon or charcoal, before any blending pass touches them.**

**Acceptance test.**
- A 600 × 600 px patch on vellum, darks-first recipe (charcoal powder, compressed charcoal, workable fixative, three cycles): median L* ≤ 22, darkest 0.1% ≤ 18, sheen share under the 20% glare flag, grain ≤ 1.5 L* after blending.
- Then a still life with a black object (the egg test with a dark bowl): the drawing's p5 within 5 L* of the reference's p5, and its share below L* 25 within a factor of 1.5 of the reference's.

**Effort.** M for tools and docs, plus L if the tooth model needs to know burnished graphite from open tooth.

## G3. Composition: the sheet is spent on a flat field of fog

**Evidence [M].**
- 73.3% of round 19's sheet is flat mid-tone (L* 35-65 with a local standard deviation under 1 L* over 5 mm). The photograph has 2.4%.
- Bare paper (L* > 92) is 0.0% of the sheet; near-black (< L* 25) is 0.1%, against the photograph's 22.6%.
- Declared elements as shares of the sheet: fist 0.7%, arm 4.4%, face 11.4% (the face is cropped by the frame and upside down).

**Why the idea read as longing, a hitchhiker or reaching [S, H].**
- Viewers name the loudest half of a mixed feeling (`docs/research/emotion.md`). The loud half, the clenched-eye grin, was illegible (G6). The quiet half was huge: two-thirds of the sheet is an even grey sky with a 27 px moon. A big sky with a tiny moon, plus a raised arm, is the stock "reaching or longing" picture. Teodor himself listed the raised arm as a habit to watch (rounds 12, 13, 16, 17; journal, phase 1).
- The thumb sticks out diagonally from a small fist, which is the hitchhiker's sign (G5).
- Both critics put it in words: "the distance between the hand and the dot carries the whole emotion" (critique 2), and "foggy, dreamlike loneliness" (critique 1).

**Against the examples' conventions** (described by the owner, not measured; **[H]** from that description and the style doc's "close crops, extreme close-ups, objects and faces filling the frame"):
- one subject, large, with the face as the event;
- a tight crop;
- the rest is bare white paper, an isolating vignette, not a rendered environment;
- the whole value range lives inside the subject.

Round 19 inverted every one of these: an environment-first picture with the face at the edge and upside down, and the subject small.

**Root cause.** Composition. The thumbnail chosen in planning (A) optimised the physics of the joke (eye, thumb and moon on one line) over the style's conventions. Thumbnails C (the face filling the frame, the moon in the eye) and D (the moon in his glasses) were rejected because "the moon is a speck". At a hyperrealist's scale a reflected moon in an eye 2-3× life is several millimetres across and can carry its phase (G9).

**Proposed fix.**
1. Add a "Composition conventions" checklist to `docs/styles/graphite-hyperrealism.md` section 7: subject ≥ 40% of the sheet, the event inside the subject, background bare paper or one simple tone, no large flat mid-tone field.
2. Add the measures below to `report` (G10).

**Acceptance test** (on the redo's schema, before any mark):
- flat mid-tone share ≤ 15%;
- bare paper ≥ 15% if the white-sheet convention is chosen;
- focal element ≥ 5% of the sheet, and the face (if any) ≥ 25%;
- the face upright within ±30° in the frame;
- a fresh critic reading the schema thumbnail names the intended feeling, or at least not one of the listed wrong ones.

**Effort.** S (a decision and a checklist).

## G4. Perspective and proportion: the hand shrinks and the face swells

**Evidence [M].** From `plan/m/s19.json` and its `.geo`:
- The camera sat 0.303 m from his open eye and 0.747 m from the thumb, with a vertical field of 85.9° (focal length 1718 px; a 19 mm lens on 35 mm film, portrait orientation).
- So the hand appears at 0.303 / 0.747 = **0.41 face-lengths** in the picture. The canon is 1.0: "hands are as long as the face" (`docs/subjects/hands-feet.md`, `figure.md`).
- On the sheet: the hand's element spans 303 × 330 px (diagonal 448 px, about 90 mm), so **0.47× life** for a 19 cm hand. The face spans about 1,100 px (about 225 mm), so **1.2× life**.

At 12 inches a camera "increase[s] nasal size by 30% in males and 29% in females"; 5 feet is "a standard portrait distance" with "essentially no difference" [S: Ward et al. 2018, *JAMA Facial Plastic Surgery*, PMC5876805]. The hyperrealist's photograph is taken at portrait distance **[H]** (the examples show no wide-angle distortion).

**Root cause.** Composition and reference. The wide-lens solution to the eye-thumb-moon line put the face in the lens's near field and the hand 2.5× farther away. A viewer doesn't correct for perspective: a hand under half a face long reads as a small, child's or doll's hand (critique 2: "plastic and doll-like"). That feeds G6.

**Proposed fix.**
1. Default the camera to ≥ 1.2 m from the subject, with a field equivalent to 85-135 mm, for any picture whose subject is a face.
2. When a hand and a face share a picture, keep them within 20% of each other's distance from the camera.
3. Add a projected-proportion check to the scene step: the hand's projected length over the face's, printed after every render (`scene.py` can project the landmarks it already has).

**Acceptance test.**
- The redo's render prints a hand-to-face projected ratio of 0.8-1.2 (if both are shown) and a camera distance ≥ 1.2 m from the face.
- Nose width over bizygomatic width within 5% of the frontal orthographic value of the same mesh.

**Effort.** S.

## G5. The hand: why the thumb reads as a pointing finger, and why it looks pasted on

**What the mesh gave.** `reach_l.hand`:
- fingers `f` = [92°, 105°, 55°] at the three joints (the last joint only half-curled), spread 0;
- thumb [30, 0, 10, 0, 0]: abducted 30°, no opposition and no flexion at its joints.

So the thumb is a straight cylinder in the plane of the hand, and the four fingertips poke out as separate knobs (`main_scene_v19.png`, `hand_study_4x.png`). `hands-feet.md` section 9 already records that the mesh's `grip` and `fist` thumbs fold "a little stiffly".

**Why it reads as a pointing finger [M, S, H].**
1. The thumb is straight and tubular, with its nail facing the camera, like an index finger's nail when pointing. A real thumb in a fist rises from a thick thenar mass low on the wrist and bends at its two joints (`hands-feet.md` section 1: "its real base ... is very low on the hand"). Neither shows: the thenar is hidden behind the wrist from this camera.
2. The four fingers, seen from their tips at 0.75 m and foreshortened, shrink to a small knot. The thumb is then the longest digit in the picture, which is the silhouette of a pointing hand.
3. Its axis runs about 32° off vertical, up and to the left: from (1296, 1158) to (1371, 1276) on the element polygon. That is the hitchhiker's angle, not the vertical thumbs-up (critique 1).
4. Teodor's own value studies warned: "drawn as a stick, the thumb reads as a pointing finger or a thumbs-up" (journal, phase 1).

**What the detail pass changed [M].**
- The hand study smoothed the mesh's blocky fingers and invented the light (it was "raised" by eye: "back ~66, lit thumb 81-85").
- The drawn detail reached 50-80% of the study's texture energy at 0.25-1 hand-mm.
- The erasers left 14 small bright flecks at 4× (prominence up to 35 L*): "white dashes" (journal ep 28-29), not designed highlights.
- The hand has no dark at all: p1 46, against a gap between curled fingers that should be among the darkest accents (`hands-feet.md` section 3).

**Why it looks pasted on [M].** In sheet-scale texture energy (RMS L*), the fist carries 5× the arm's at 0.4 mm and 6× at 0.8 mm, though the arm sits at almost the same distance and, by the round's own f/16 table, in focus:

| sheet-mm | 0.4 | 0.8 | 1.6 |
|---|---|---|---|
| fist | 0.54 | 1.48 | 2.82 |
| raised arm | 0.11 | 0.23 | 0.57 |
| face | 0.31 | 0.56 | 0.97 |
| sky | 0.09 | 0.03 | 0.01 |

The hand is a modelled island on an unmodelled tube. The cuff meets it as a "sawn cylinder" (critique 2). The hand also took 15 episodes of seam repair (journal ep 25-39) for the halos and rectangles its separate session left. The grain inside and outside the detail's rectangle now matches (0.28 against 0.29 L*), so the seam is no longer grain. It is relation: the texture, the light, and the missing wrist and cuff structure.

**Root cause.** Reference (pose spec and mesh thumb), process (the study invented light without the scene; the detail wasn't related back), and composition (G4: the hand at 0.47× life can't carry knuckle and crease detail).

**Proposed fix.**
1. In `figure.HANDS`, add a `thumbs_up` / `fist_thumb` preset: fingers 95-100° at all three joints so the tips tuck into the palm; thumb opposed and rotated so its pad faces the index; its distal joint slightly hyperextended; the thenar mass visible.
2. Add a hand sheet render from 8 directions to check the read.
3. In `docs/orchestration.md` "Checking a checkpoint", add: "a hand study's light comes from the scene's render, never by eye".
4. After closing any detail, run the relation check (G8).
5. Find ≥ 3 public-domain or CC0 photographs of a fist with the thumb up, or of thumbs, with `tools/find_refs.py` (feature "thumb up fist"), for structure.

**Acceptance test.**
- A lone-hand test drawing (`hand` object, fist and thumb up, at life size on the sheet, i.e. ≥ 5 px per hand-mm) compared with a public-domain hand photograph at equal hand-mm scale: texture band energy at 0.25-2 hand-mm within ±35%; the darkest gap between fingers ≤ L* 25; ≥ 2 speculars ≥ 25 L* (nail, knuckle).
- A fresh critic names the gesture "thumbs up / thumb raised", not "pointing", from the thumbnail.
- The hand-to-face ratio from G4.

**Effort.** M (preset S, references S, test drawing M). The photograph must be found first.

## G6. The face: why it read as a child, and why the grin didn't read

**Evidence [M, S].**
- **Orientation:** the face sat upside down and foreshortened at the bottom edge. Inverted faces lose accuracy for sex, among other things (Bruce et al. 1993, cited in `docs/subjects/sex-age.md`). `face.md` lists "lost face from below" as a common mistake: "turn the head or move the camera".
- **Skin:** forehead texture is 10-20% of the photograph's at 0.25-2 face-mm (G1). Skin texture and wrinkles explain a large share of perceived age, and even skin reads younger (Fink and Matts 2008; Fink, Grammer and Matts 2006; both in `sex-age.md`).
- **Beard:** the beard (`"beard": 0.55` in the scene) became a "stubble zone" softened to nothing. The male cue of a "darker ... beard shadow around mouth and chin" (`sex-age.md`) is gone.
- **Darks:** the face's p1 is 39 (the photograph's 1.3). No facial darks means no facial contrast; neither male nor female cues can carry.
- **Proportions:** the cranium and forehead dominate the frame while the lower face is cropped and foreshortened. "A large head, a high, jutting forehead" is the baby schema (Glocker et al. 2009, in `sex-age.md`), and the small hand beside it (G4) completes a child's proportions. Critic 2 read "young, maybe a teenager to 30", sex uncertain.
- **The grin:** a closed-mouth AU6+12 with one eye shut (AU43 on one side). Read upside down, the lit roll of the lower lid became "an open eye" (both critics), and the mouth corner turning up reads as down when inverted **[H]**. The face carried no specular, so the wet eye and lip had nothing to say "alive".

**Root cause.** Composition (inversion, crop), reference (no skin, no beard texture), process (the face blended at 60 then 40 detail px: "overblended", ep 18 and 21).

**Proposed fix.**
- An upright face, near frontal or three-quarter, from portrait distance (G4).
- Male age cues present at full size: pores, beard shadow, crow's feet as form plus line, the eye's darks (lash line, iris rim, pupil at the floor of G2).
- The expression built from AUs checked upright from two angles at thumbnail before drawing (`face.md` checks, item 3).
- At least one catchlight reserved or indented before any tone.

**Acceptance test.**
- On the redo's render and schema: face p1 ≤ 12; ≥ 2 catchlights ≥ 30 L*; skin bands as in G1.
- A fresh critic shown the schema at thumbnail names age within ±10 years of the intended age, the sex, and the expression's family (joy against longing).
- The same three checks on the drawing at checkpoint 1.

**Effort.** M (mostly from G1 and G4).

## G7. Mark strategy: no tool draws a designed fine mark

**What the tools can and can't draw** (`docs/manual/graphite.md`, `MANUAL.md`; round-19 logs):

| Mark the style needs | How hyperrealists build it [S] | Studio today | Status |
|---|---|---|---|
| Hair strand | Stroke by stroke with a 0.5 mm 4B mechanical pencil, "bold to begin with, but ended lightly"; darks between groups first; highlights lifted with a kneaded eraser pinched to an edge, "as though you're drawing white hair"; strands vary around the flow (RapidFireArt, "How to draw short hair"). Indenting for light strands (Sibley, indenting) | `strokes` with hand-written points only; `match` lays short form-following dashes, `hatch` parallel bands. Neither follows a strand from root to tip with a taper | **missing as a tool** |
| Braid crossing | Strand groups over and under, with the occlusion dark at each crossing | none | missing |
| Droplet | Shaded on the side toward the light, light on the far side; "a pure white dot" glare; a dark arc of cast shadow opposite the light (Plaid, "How to draw realistic water droplets") | `electric_eraser` dot plus hand-written arcs | missing as a unit |
| Pores | Lightly, "pores that are too dark will look like blackheads"; small circular stump marks for the base; "work on one small section at a time" (DeSerres, "How to draw realistic skin using graphite pencils") | `match` at threshold 0.02 gives speckle, not pores; no stipple-with-lift | missing |
| Eyelashes, nail edge, fine creases | Hard lead lines (2H-3H for fine lines, same source); indented whites | `strokes` with `mech_03` (1.5 px at 5 px/mm: a soft ramp; the manual says lashes "read soft") | partial, at 4× detail only |
| Specular | Reserved, indented, or lifted with a battery eraser | `electric_eraser`, `stylus`, `finish lift` | tool exists; not planned from the reference |
| Crisp edge between two darks | Hard lead drawn along the edge | missing (`graphite-hyperrealism.md` limits, item 3) | missing |
| Fabric weave | Regular hatch at the weave's period, then lift | `hatch` with `regular: true` | possible, untested |

In round 19, 1 intention in 287 on the main sheet used the stylus (the thumbnail's groove). There were 15 `strokes` intentions, mostly repairs, and 112 blends (39%). About 2,300 hand-placed stroke paths were written across all logs [M].

**Does `match` or `hatch` ever produce such marks?** No. `match` places strokes where the canvas differs from the schema by more than `threshold`, oriented by `follow`, with lengths from the felt state. Its marks are value corrections and leave dashes (calibration limits, item 4). `hatch` lays tone. Neither knows what a strand, a lash or a rim is.

**What a reference-driven fine-mark tool needs [H].** A new intention, `marks`, whose input is the reference's **structure**, not its pixels. The renderer (G1) emits these alongside the image:
- strand curves (id, width, depth, lit or shadow side);
- specular blobs (centre, size, prominence);
- droplet ellipses (axis, light direction);
- pore centres;
- crease and lash polylines;
- contour edges with their side values.

The tool turns each into studio strokes with the mark grammar above:
- **strands:** dark-to-light pressure, taper, the occlusion darks first, an optional indent pass for the light strands, a kneaded-edge lift for highlights;
- **glints:** indent or battery eraser;
- **droplets:** shadow side, rim, glint and cast shadow as one unit;
- **pores:** light stipple plus a tiny lift on the lit lip;
- **edges:** a hard lead along the contour.

The painter chooses which families, where and how many, and every mark is laid by a studio tool. This is like `transfer`, which already draws the schema's contours as pencil strokes. Whether it stays inside rule 2 is a ruling for the owner (G11).

**Acceptance test.** Three test drawings, each against a public-domain photograph patch of the same subject at equal subject scale, with `hyperreal_gaps.py` bands, speculars and edges:
1. a lock of hair 30 × 30 mm: strand bands within ±35%, orientation coherence within ±0.1;
2. a droplet field on skin: count and prominence of glints within ±30%, each droplet with a darker rim;
3. a 25 × 25 mm cheek patch: pore-band energy within ±35%, no pore darker than its surround by more than 12 L*.

**Effort.** L for the tool, XL with G1's structure outputs.

## G8. Process: the order of work, relation, and time

**Where each failure came from** (journal):

| Failure | Episode | Cause |
|---|---|---|
| The tooth filled before the darks | eps 3-15: all-over value bands, then a full-sheet blend of the sky (ep 5) and of the lower half (ep 8: "one 70 px brush over the whole lower half"), then two more (ep 11, 13) | The calibrated recipe (bands, blend, correct) applied sheet-wide; the darks came at ep 60 and "did not move" |
| The murk | ep 8 onward: "every blend lifts" | Whole-sheet blending; brush `pick-up` lifts darks (calibration) |
| The face's oval rim; the fist's paper ring and halos; the sky's rectangles and discs | eps 16-21, 24-39, 36-38, 46-54, 70-71 | Clip regions and detail rectangles as boundaries; a correction confined to a rectangle in an even field always shows (journal: "the same lesson a third time") |
| The pasted-on hand | eps 22-35 (hand at 4×), never related back to the arm and cuff | The detail was finished alone, against an invented study light (G5) |
| Lost creases | eps 18, 41, 66: blend after line | Blends larger than the feature (`brush` 60 detail px over a face) |
| Episodes lost | 9 on a fold drawn on a wrong axis plus a `paintout` (eps 45-53); 2 cancelled details; the server restarted twice | — |

**Passage by passage.** Hyperrealist practice finishes one area at a time: "Work on one small section at a time" (DeSerres, skin tutorial); the studio manager's note after critique 1 said the same. Round 19 worked layer by layer across the whole sheet in phase 1 and switched only in phase 2, when the tooth was already full.

**Relation back.** After each detail closes, its texture, value and edge statistics must sit on the same curve as the passages it touches at the same depth. The fist against the arm failed by 5-6× (G5).

**Episodes against hours.** About 8.5 h of wall clock for the whole round (first frame 15:42, last 00:15), 83 numbered episodes. The style's process reports give about 200 hours for one large drawing (My Modern Met, in the style doc). The studio is faster per mark, but the count of designed marks a face needs is 10^3-10^4 (G9), and round 19 laid about 2,300 hand-placed paths in all.

**Proposed fix** (`docs/orchestration.md`, `docs/agents/painting-quickstart.md`, the style doc's section 9):
1. Darks first, per passage, before any blend touches them.
2. Blending by part only, with a brush no larger than the part's own blur; a whole-sheet blend is not allowed in this style.
3. Finish a passage to near-final before the next. Order: the focal passage, then the face, then the passages that touch them, then the background.
4. After every detail: a relation check (G10) against its neighbours at the same depth.
5. Never confine a correction in an even field to a rectangle: correct the whole passage.

**Acceptance test.**
- On a two-passage test drawing (a hand emerging from a sleeve, both in focus): texture band energy at 0.4-1.6 sheet-mm within a factor of 1.5 between the two elements.
- The darks reach the G2 floor in the dark passages.
- No visible seam: grain and mean L* in 30 px strips on either side of every detail rectangle within 0.5 L*.

**Effort.** S (rules) plus the G10 checks.

## G9. Resolution, sheet size and detail density

**What the style needs [S, M, H].**
- **Pores:** 0.06-0.37 mm² in area (about 0.3-0.7 mm across), 10-90 per cm² (Flament 2015). On a head drawn at 2× life that is 0.6-1.4 mm on the sheet: 3-7 px at 5 px/mm, resolvable.
- **Hair:** about 0.02-0.18 mm across (Wikipedia, "Hair"; not re-fetched this session: **[H]** until checked). Drawn hair is a 0.3-0.5 mm line whatever the scale (RapidFireArt: a 0.5 mm mechanical pencil). At 5 px/mm a 0.3 mm line is 1.5 px, "a soft ramp" (manual). The detail pass at 4× gives 6 px and draws it crisp (manual, detail pass).
- **Round 19's subject scales** were 1.2× life for the face (6 px per face-mm) and 0.47× for the hand (2.3 px per hand-mm, so a 13 mm nail is 6 mm on the sheet). Neither the hand nor any hair was drawn at a scale that can hold the style's detail.
- **Mark counts:** a visible face of about 150 cm² at 10-90 pores per cm² is 1,500-13,500 pore marks before any hair. The examples' braids and hair are thousands of strands **[H]**.

**What is possible [S: calibration and manual].**
- 2400 × 3200 runs an empty episode in 1.9 s and took about 80 min for the egg test.
- 3600 × 4800 adds about 12 s per episode.
- A 4× detail of round 19's face (4400 × 3440) ran, but the reference render at that size was killed for memory.

**Proposed fix.**
- Keep the 48 × 64 cm sheet at 5 px/mm for block-in, but **scale the subject** so the head is about 2× life (crown to chin about 46 cm): 10 px per face-mm, about twice round 19's.
- Draw hair, lashes, glints, droplets and nails in **tiled 4× details** (e.g. 600 × 600 sheet-px tiles, 2400 × 2400 at 4×, with 10% overlapping margins that are blended back as one passage). Render the reference per tile at the same scale.
- Budget about 400-600 episodes for a hyperrealist head, against round 19's 83. Spread them over more phases (6-8 instead of 3), with a critic at each **[H]**.

**Acceptance test.** A timing run on one 4× tile with 2,000 strand strokes and 500 pores: wall time per tile ≤ 10 min on 2 vCPU, peak memory ≤ 6 GB, and the tile's seam check from G8 passes.

**Effort.** M (tiling the detail and the render).

## G10. Measurement: what would have caught each gap, and what is missing

**What `report` saw.** `eyes.measure` resizes every image to **512 px on the long side** (`eyes.py`, `SIZE`). On a 48 × 64 cm sheet one measured pixel is 1.25 mm, so every band finer than about 2.5 mm (pores, strands, lashes, glints, the edges of the focus) is invisible to it.

At the finish, `report` gave:
- hard-edge share 18% ("within range" of 17%) while the drawing read as fog;
- texture variation within range.

The value numbers did show the gap but only as z-scores: spread 10 against 21 (z -2.1), darks 0% against 29%. The only standing flag was "murky middle". There is no hard gate.

**What would have caught each gap:**

| Gap | Existing number (outcome) | Missing number (proposed) |
|---|---|---|
| G1 reference | none: `report` measures the canvas, not the schema | **`report ref`**: the same measures run on the schema, compared with the target before drawing |
| G2 darks | `value_dark` 0% against 29%, `value_p5` 41 against 17 (shown, not flagged) | `value_below20`, `value_p1`; a **hard flag** when the share below L* 25 is under half the target's |
| G3 composition | none | `flat_midtone_share` (target ≤ 0.15, photograph 0.02), `bare_paper_share`, `subject_area_share` |
| G4, G5 proportion | none | Projected hand-to-face ratio and face roll angle, from `scene` |
| G5, G8 relation | `element_clarity` (contrast only) | **`relation`**: texture band ratio and edge-width ratio between adjacent elements at the same depth (flag > 2×) |
| G6, G1 speculars | none | `specular_count` and `max_prominence` in the focal element at native resolution |
| G7, G9 detail | `detail_energy` at 512 px | **Native-resolution band energy per element**, in subject-mm when the scene gives the scale (this script's method) |
| Edges | `hard_edge_share` at 512 px | The 10-90% edge-width distribution at native resolution in the focal element (photograph-like: p10 ≤ 0.3 mm at the focus) |

**What `studio/targets.json` → `graphite-hyperrealism` should contain [H].** Keep the 45-photo set for the whole-sheet value keys. Add a **close-up ruler**: ≥ 10 public-domain or CC0 portrait and hand photographs at ≥ 3000 px, measured at native resolution in subject-mm. Provisional values from the one portrait measured here (n = 1, to be replaced):
- `value_below20` ≥ 0.10;
- `value_p1` ≤ 10;
- `flat_midtone_share` ≤ 0.05 (photograph 0.024);
- `skin_band_rms` {0.25: 0.38, 0.5: 0.62, 1: 1.03, 2: 1.75} L*;
- `hair_band_rms` {0.125: 0.55, 0.25: 0.98, 0.5: 1.24} L*;
- `face_specular_count` ≥ 3 at a prominence of ≥ 30 L*;
- `subject_area_share` ≥ 0.4.

The keys `focal_x`, `focal_y` and the documentary-photo composition keys don't describe this style (close-ups); leave them out of the verdicts.

**Effort.** M: `eyes.py` native-resolution measures and new flags, a `report ref` mode, the close-up ruler.

## G11. The rules: an honest way to do hyperrealism inside them

**The conflict.** A hyperrealist renders one photograph of one real person, transferred mechanically (the style doc, section 6). Rule 5 forbids a likeness of a real person. Rule 2 forbids tracing anything onto the canvas, and `docs/research/references.md` draws the line between study and tracing. Copying a found photograph of a stranger would break both.

**Options.**

| Option | What it achieves | What it doesn't | Rules |
|---|---|---|---|
| **A. A composite of several CC0 photographs, for study only** | Real irregularity: asymmetry, blemishes, hair randomness | Few modern high-resolution CC0 close-ups are reachable: museum CC0 photographs are mostly 19th-century and soft; Wikimedia was rate-limited here; public-domain government portraits are identifiable people. A blend of two or three faces can still resemble one of them. Lighting and expression can't be chosen | Rule 5 risk on any face composite: **not recommended for faces** |
| **B. A photoreal render of an invented mesh person** (procedural skin, strand hair, water) | No likeness by construction (MakeHuman CC0 base, `ancestry` and morph mix); full control of light, expression, water, lens and depth of field; it emits the structure the fine-mark tool needs (G7) | The real photograph's unplanned truth; there is a risk of the uncanny valley, and the skin's statistics are only as good as their model | Fully inside the rules |
| **C. Hybrid (recommended)**: B, with micro-detail statistics and textures taken from **anonymous** CC0 or public-domain macro photographs of skin patches, hair locks, water droplets and hands (no face), and real anatomy checked against public-domain references studied for one feature each (`find_refs.py`) | B's control and no likeness, plus measured real texture; an acceptance ruler from the same patches | Still a render at heart: expression subtleties depend on the AU rig | Inside the rules: a patch of cheek skin, a lock of hair or a droplet is not a likeness; the faces stay invented |

**Transfer and fine marks.** The style's practice is a light mechanical transfer of the outline (the style doc, section 6). The studio's `transfer` already draws the reference's contours in 2H on the tooth, from **Teodor's own invented reference**, not from someone's photograph. That keeps the spirit of rule 2: nothing is pasted, and every tone and mark is laid by a tool and checked by looking.

The fine-mark tool (G7) goes further: it plans strands, glints and pores from the render's structure. **This needs an explicit ruling from the owner.** It is the same kind of help as `transfer`, but at a far finer grain. Proposed wording for AGENTS.md rule 2: "a planner may propose mark paths from the painter's own reference structure; the painter chooses the families, the regions and the counts, and every mark is laid by a studio tool".

**A rule-hygiene note.** `docs/styles/graphite-hyperrealism.md` cites two process interviews whose URLs carry the names of living artists. Rule 3 versions styles, never authors. The citations are for working method, not for models, but the URLs could be replaced by neutral descriptions or moved to a gitignored note.

**Effort.** S for the decisions and wording; option C's build is G1 (XL).

---

## Recommended order of fixes

1. **Decisions (S, first):** G11, the reference route (option C) and the ruling on the fine-mark planner; G3 and G4, the composition conventions and the camera rule into the style doc.
2. **Measurement (M):** G10, `hyperreal_gaps.py`'s measures into `eyes.py` at native resolution, `report ref`, the hard flags; source the close-up ruler (≥ 10 public-domain or CC0 portraits, a public-domain hand, hair and droplet patches). Every later step is judged by these numbers.
3. **Darks (M-L):** G2, charcoal powder and compressed charcoal in the graphite medium, `workable` fixative cycles, the darks-first recipe; pass the patch test.
4. **The reference (XL):** G1, skin maps and specular, strand hair, droplets, depth of field, tiled rendering; pass the render-against-photograph test. Then G5's hand preset and G6's face checks on the render.
5. **Marks (L-XL):** G7, the `marks` intention; pass the hair, droplet and pore patch tests.
6. **Process and scale (S-M):** G8 rules into orchestration and the quickstart; G9 tiled 4× details; pass the hand-in-sleeve and the timing tests.
7. **A test head**, before the commission: one invented head at 2× life on white paper, drawn with the new pipeline and measured against the close-up ruler. If it fails, the redo waits.

## What the redo should look like

Teodor chooses the feeling and the picture. These are the style's conventions the redo should meet, and three directions that serve "Man and the Moon" inside them, offered as options, not as a design.

**Conventions to meet:**
- one subject, large (head at about 2× life, ≥ 40% of the sheet), on bare white paper, with no rendered sky field;
- upright, from portrait distance (85-135 mm equivalent);
- one hard light giving true darks (charcoal floor), crisp speculars and a core shadow;
- the event inside the subject, finished passage by passage;
- the moon at true optical scale for whatever surface carries it, so that it is unmistakably the Moon at close viewing distance.

**Directions:**
1. **The moon in the eye.** A man's face, tight crop, one eye in sharp focus: the moon reflected on the cornea as the catchlight. At 2× life an eye is about 60 mm across on the sheet, so the reflection can be several millimetres, with its phase and maria crisp. The face carries the feeling (in round 19, sly delight). The rejected thumbnails C and D become possible at this scale.
2. **The thumb, kept, but as a portrait.** Face and fist at the same distance from a portrait-length lens: the thumb raised close beside the clenched eye. The thumbnail's nail, with a tiny crisp moon at its edge in the same plane of focus, is the event. Hand and face are both about 2× life, the thumb an anatomical thumb (G5), the grin upright.
3. **Water and moonlight.** A face lifted from water at night, droplets with rims and glints, the moon as the single light source and repeated in every droplet's glint. This plays to the examples' strengths (droplets, darks, speculars) but is low-key, so it depends on G2's darks.

Whichever he chooses, the schema has to pass G3's and G4's acceptance tests, and a fresh critic has to read the intended feeling from the schema's thumbnail, before the first mark.
