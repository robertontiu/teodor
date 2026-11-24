# Handoff after phase 2

## Where the painting stands
Phase 2 ran E20-E51 (32 episodes). After critique 1 (read as "a party", a standing figure, a cross, nothing glowing) I turned the world over rather than touching up. Scene L (scene_L.json, render main_scene_v11.png) was rendered with the main cobalt figure plus two ghost figures in red and magenta that only mark where the arms swept; tools/rot.py rotated the render 152 degrees and enlarged it, and tools/compose.py built schema_L.png (live reference, schema version 15): value gradient, pale pressed fans, contact shadow, rings of dots.
The canvas now: seen from above, a flat Matisse-blue body lies UPSIDE DOWN and diagonal, feet out of the top-left corner, head low right of centre (~740,1080), one arm flung out off the right edge (~y 880-960), the other down to the bottom edge (~x 520-680). The grass is laid in curved strokes wheeling around the head: a slow vortex, hot acid lemon at its eye and along the left of the body, cooling to viridian in the upper-right and lower-right corners. Two pale cream fans of pressed grass (impasto) where the arms swept: one above the right arm (upper right), one beside the lower arm (lower left). Rose and white dots laid on rings centred on the head, like ripples in water; the legs come apart into dots (cobalt dots spill out into the grass, green, lemon and rose dots eat into the legs). The head is one dark ultramarine mass of hair with the hardest edge in the painting, against the hottest lemon. Collarbones catch a soft glimmer.
Helper scripts (all in /home/claude/v14/tools/): actf.py runs an act from a JSON file (long stroke lists exceed the shell's argument limit); ep.py builds /tmp/ep.json from intentions ('@{intention}=strokes.json' inserts a stroke list); fillmask.py fills a mask with form-following strokes; swirl.py lays strokes around a centre outside a mask; masks body_mask.npy, body_in.npy, notpale.npy, notcore.npy, body_or_pale.npy; schemas body_sch.png (darkened body), grass_sch.png (dot-free field), warm_sch.png / warm2_sch.png (hot lemon near head / body), light_sch.png (fans). Dot-ring strokes: regenerate with the ring code (centre 740,1080, radii 150-1000 step 50).

## What each element is for (feeling: boundless rapture, with the vertigo of coming undone)
- Upside down and diagonal: the world turned over. It kills the cross and the standing man, and it is the vertigo: the body tips into the ground the way the ground pours into you.
- The vortex of grass strokes: time and space turning around the head; the vertigo made by the hand, not by a symbol.
- Flung arms and the pale fans: abandon, the lift; the fans are where the arms have just been (time smearing, Balla) and they hold the lightest light, so the glow comes from where the body was, not from a burst behind a head.
- Hot lemon at the eye of the vortex and along the body; cool viridian at the rim: the rush is hot at its centre.
- The dots: Kusama's self-obliteration. Ripples spreading from the head; the far end of the body (the feet) dissolving into the same pattern, matter exchanged across the edge. This is the "coming undone".
- The dark head with the crisp edge: the one solid, still thing at the centre of the turning, the self that is being undone.
- Upper-right corner (cool, quieter, darker): the rest for the eye.

## Open problems for phase 3
1. Uniform marks: the grass is one even square dab everywhere, my old "filter" habit. Break it: a few long, loaded, varied strokes (some knife, some fan) in the field, bigger and quieter in the dark corners, smaller and sharper near the head; let some strokes cross the ring rows.
2. The liner tick marks in the lower-left fan read as rain or hatching. Either remove them (relay the cream) or make two or three long continuous sweep curves instead of many ticks.
3. Rapture is quieter than vertigo. The chest/collarbone light should sing: a few thick cream-lemon highlights on the chest and the top of the outflung arm, crisp, the brightest notes on the body. Perhaps the open hand at the right edge catches light.
4. The body interior is stamped and even in places (round dabs); a few longer strokes along the torso and arms, temperature shifts (a violet-ultramarine in the deepest turn, cerulean-green reflected from the grass on the underside).
5. Edge hierarchy: hard at the head and the arm root / shoulder only; lose the right hand into the edge, lose the lower hand at the bottom; keep the legs dissolving. Check that the body's lit rim does not read as an outline again.
6. Value check in gray: keep the three groups (dark legs/corners/head, mid body and right field, light fans and hot left field). Do not let glazes cool the whole field again (E44): glaze only small, feathered, away from the fans.
7. Danger signs to keep away from: any ring or halo around the head; radiant spikes; confetti of many colours; the cross.

## Plan for phase 3
Read critique_2.md first and test it against the feeling: if the critic reads falling or drowning without joy, push the rapture (light on the chest, the open hands, warmer and higher key near the body); if they read only pattern, firm up the body. Then: mark variety in the field (problem 1), the fans (2), the chest light (3), the body's interior (4), edges and fine touches (5), a final gray check, sign, timelapse, final.png.


# Final note after phase 3 (E52-E74, 23 episodes)
Critique 2 answered: the blob head became a head rolled to the side toward the sun, a lit cheek and profile against the hottest lemon, eyelid closed (tools/p3/head2.py, face3.py); the chest and shoulder lit as soft round planes (bodylight.py); the outflung arm repainted in one pass with an open palm leaving the frame (arm.py); the dots sunk back into the paint with distance from the head and taken off the torso, thinning toward the heart; both fans relaid with the fan brush in arcs swung round the shoulders and glazed down at their far ends; broad long strokes in the far field; lost edges at the feet. Signed and finished. Title: The Field Turns Over.
