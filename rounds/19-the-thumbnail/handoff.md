# Handoff after phase 3 (FINISHED; round 19, Man and the Moon, graphite hyperrealism on vellum)

Finished: final.png (signed bottom right), main_timelapse.mp4. 83 episodes in all (phase 3: 63-83). 32 schema versions (v1-v32). Phase 3 summary and the final report are at the end of journal.md. Open problems carried out of the painting (for the experiments log): value spread 10 vs 21 and murky middle 74% (tooth filled before the darks; blends lift); hard edges not gathered at the focus (3% vs 20%); the upside-down head still reads slowly, so the grin is quiet; the arm close to the sky's value; three faint eraser lights in the face; one stray accent line in the hair.

Phase 3 lessons: region polygons must come from masks of what is drawn, never rectangles (the chest seams were the chest region's own boxes, and the arm element swallowed a patch); in graphite a long eraser stroke is a scratch, not a light; the tortillon is too slow for a face; eraser arcs to fill a disc make a target pattern, fuse with the brush.

---

# Handoff after phase 2 (round 19, Man and the Moon, graphite hyperrealism on vellum, 2400x3200)

## Where the drawing stands (62 episodes; crit_2.png)
- **Fist** (focal point 1318, 1172): drawn in a 4x detail from a tonal study (plan/m/hand_study.py, hand_study_4x.png): the knuckle arc of the curled fingers, occlusion between them, the lit thumb (L* ~80) with its nail plate (from the indented free edge), the back of the hand in half-light (~66), the little-finger side in shadow (~45-50), the wrist darkening into the cuff. Its silhouette is clean against the sky. Still soft overall: the report counts no hard edges at the focus.
- **Sky**: one even passage (L* ~43 at the top to ~60 at the horizon), corrected as a whole three times this phase. No cirrus yet.
- **Moon** (2040, 404): a small gibbous disc (73% lit, limb up-left), drawn in an 8x detail from plan/m/moon_study.py; a faint mottle for the maria; dark side lost in the sky. Its lit limb is not yet the hard edge the ledger asks for.
- **Arm/sleeve**: now follows the schema's narrower arm; lit cylinder with a shadow side and faint folds near the elbow. Still reads as a tube; masked in report (5 L* from its surround).
- **Face** (lower left): rebuilt as one passage from the face study (composited into the schema, v25-v27). Large values within 2-4 L* of the study; nose, socket and the lid roll read; the clenched eye still reads as an open eye at a glance and the grin is weak. Carbon speckle in the hair.
- **Chest** (right half): simplified into a quiet soft mass (no more "horse"). Rectangular seams remain in it: a vertical one at x ~1150 (y 2300-2420), a horizontal one at y ~2330 (x 1150-2400), another near x ~1700 (y 2120-2330).
- **Treeline and ground**: lumpy top, some texture; still a stiff diagonal band.

## What each element does for the feeling (sly delight; underneath it, the moon that does not care)
- **The fist and thumbnail**: the focus, the sighting hand. Sharpest edges, clearest form; the nail faces his eye.
- **The face**: the loud half, the grin: the near eye clenched, the cheek balled up, the mouth closed and pulled up at the corner.
- **The arm**: the diagonal from face to fist; must separate from the sky.
- **The moon**: the quiet half: small, true size, on the extension of the eye-thumb line, the brightest thing in the sky but not on the sheet, with the hardest small edge on its lit limb.
- **Sky and treeline**: room, scale, a bright afternoon.

## Expectation ledger
The drawing teaches soft photographic tone, a mid-grey filtered sky, one diagonal from lower left to upper right, blur near the lens. The one break: the moon's lit limb, the smallest, hardest-edged shape, alone in the sky. The thumbnail is the hard focal edge that rhymes with it. Not yet true on the sheet: neither edge is hard yet.

## Habits broken (unchanged)
The lone figure from behind; eye-level middle distance; the hushed dusk with one warm light; the radial burst; the open red laugh. Watch: the raised arm, the rotated figure.

## Lessons from this phase (for phase 3)
- In an even passage (sky, chest), never correct a rectangle or an ellipse of it: every local blend or match shows its boundary. Correct the whole part, clipped to its real edges.
- Every blender lifts a little. Blend once per part, at the size of that part's blur (sky 80, chest 50, arm 20, face 12, treeline 14), then stop.
- `match` with carbon or 8B over a large region leaves a field of dashes; it must be followed by that part's blend.
- Don't draw strokes from an estimated axis: derive coordinates from the masks. `paintout` in graphite lays coarse side-lead stripes: avoid it.
- The darks are stuck near L* 40 because the tooth is full; phase 3 can't get below that except with carbon in small, unblended accents.

## Open problems for phase 3 (in order)
1. **The face's expression** (the loudest cue for the feeling). Make the near eye unmistakably shut: darken the lit roll under the lash crease so it reads as a closed lid fold, not an eyeball; a dark pressed lash line in carbon; crow's feet stronger; the cheek ball lifted; the mouth's corner pulled up with a small carbon dimple. Work in a 2x detail on the eye and mouth only, from the study, with the tortillon, no large blends.
2. **Edges at the focus**: an edge pass on the fist (thumbnail free edge, the thumb's lit upper edge against the sky, the knuckle tops) with a 0.3 mm 2B cut-in from the sky side and the battery eraser on the lit side, unblended. The moon's lit limb: one precise eraser arc, the dark side left soft. Goal: hard edges at the focus > 0.
3. **The arm masked**: lift the lit side (left) toward L* 72 and darken the turning shadow side (right) toward L* 45 with 4B, unblended at the edge; a cuff hem (a turned band with a soft shadow line) and two real folds at the elbow derived from the arm mask.
4. **Seams in the chest** (listed above): blend the whole chest once more at 50 and match the boundary strips.
5. **Values**: the spread (10 vs 21): carbon accents in the hair, under the head and in the near grass, small and unblended; lift the forehead's and the thumb's lights with the battery eraser. Murky middle 75%.
6. **Cirrus**: lift three faint streaks with the kneaded eraser, long and soft, across the upper sky (once, as one passage).
7. Finishing: `finish clean`, `lift`, `accents`, optional fixative; `report finish`; sign where the picture wants it (not bottom right by habit).

## Files
- Current schema: plan/m/schema7.png (schema7_L.npy): the schema with the face study, the quiet chest and the sky as drawn.
- Studies: plan/m/hand_study.py (hand_study_4x.png, hand_study_L.npy, hand_study_mask.npy; detail 1260,1100 380x420 at 4x), plan/m/moon_study.py (moon_study_8x.png; detail 1990,355 100x100 at 8x), plan/m/face_study.py.
- Regions: plan/m/regions.json (sky, lower, sleeve, torso, ground, grass, hairr, face_work, chest, sky_round_hand), plan/m/hand_regions.json (detail px), plan/m/treeline.json, plan/m/moon_regions.json; the "raised arm" polygon in elements.json is the schema's arm, which the drawing now follows.
- Ruler: plan/m/cmpL.py (canvas L* against a study, per zone).
