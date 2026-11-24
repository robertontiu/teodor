# Handoff after PHASE 2 (round 14, theme HIGH)

## Feeling (see feeling.md)
Unfastened: the bliss of being lifted out of my own weight, and the small cold fact that my shadow stayed on the floor. Lift first (loud, bright, joyful), the shadow half a second later.

## Style
Figurative, flat and high-key, between Op art and Hockney: plumb bird's-eye view of a figure in white floating head-down over a Riley-style warped checker floor (hot pink / turquoise, lemon where it is squeezed thin along a "furrow"), its ultramarine shadow thrown clear of it into the dim upper-left corner. No brown, no black, no door, no dusk.

## Habits broken (on purpose)
1. Eye-level, middle-distance, centred -> plumb view from above, figure large, off-centre (lower right), head-down on a diagonal.
2. Warm lamp in a brown room / amber vs violet -> high-key pink, turquoise, lemon, white; the only dark is saturated ultramarine.
3. Lone figure from behind in silhouette -> figure face-up, open, lit, with a face, hands and feet; the silhouette role goes to the shadow.
4. Hushed bittersweet melancholy -> loud joy with one thin cold thread.
5. Uniform square dabs -> hard-edge masked tiles at the seam, looser soft-edged tiles at the margins, long cut planes for cloth, fan-brush plume for hair, liner for contour, face and furrow strings.
6. (phase 2) Generic mannequin -> the studio mannequin thrown away; my own lay figure posed joint by joint (pose2.py), close camera, wide lens.

## What changed in phase 2 (critique 1: "a toy dropped on a tablecloth": stiff symmetrical mannequin, dead-centre diagonal, one-value floor, one dab, shadow not matching)
- New blockout (scene_P3.json, pose_J.json, schema_P3.png = schema v9; 8 blockout versions in all). Body is a bow: one arm flung past the head, arched trunk, long trailing leg, other knee drawn up and out, other arm hooked with the open hand coming toward the eye. Camera at 4.4 m, fov 50, so the chest looms. Body lower right; shadow scaled to 0.8 and pushed up-left (painter's licence: higher = smaller).
- Floor completely relaid: every tile filled to its exact outline (ep2.crisp_tiles: strokes masked to the tile polygon). Hard and saturated along the seam, hard and quieter beside it, soft-edged and thinner at the margins. Light: violet glazes sink the upper left, lemon-white glazes bleach the lower right.
- Shadow: flat ultramarine, exact human outline, the floor pattern only just breathing inside (two blues under two glazes). Darkest thing; sits alone in the dim corner. A clean bright band of the loudest tiles lies between it and the body: that band is the lift.
- Body: shirt (warm white) over trousers (cooler, a step darker), painted as cut cloth planes with a shade plane toward the shadow and a white light plane toward lower right; shirt tail with a wavy hem and a cast shadow; violet contour toward the shadow, thick white rim toward the light. Head thrown back, throat, open collar; small face (closed eyes, nose ridge, open mouth); violet hair as one plume streaming from the crown. Hands open (near one larger), feet pointed.
- Furrow: seven fine liner strings (ultramarine, white, deep pink) along the seam, passing under shadow and body. The earlier trembling scribble was removed (it clotted in the gap).

## What each element is for
- Bright band between body and shadow = the height. Keep it clean; never let body and shadow touch.
- White body, thickest paint = weightlessness. Bowed gesture, open hands, floating hair and shirt tail = abandon; nothing hangs.
- Shadow, flat, cold, exact = the weight that stayed; the second beat.
- Hard-edge squeezed tiles + strings = the floor humming.
- Light gradient = a real light, and the shadow's corner cold.

## Open problems (for phase 3)
1. Hands read as gloves (round finger ends); feet are blunt wedges. Refine with small flat/liner: knuckle breaks, tapered fingertips, heel/arch, crisp light edges. These are the focal fine touches.
2. Face is near a cartoon of sleep. Soften the eye arcs and mouth (smaller, lower contrast, a little shadow in the eye sockets) so it is a painted head, not a sign.
3. Hair is a stiff broom of parallel fan lines. Break it: two or three broad dark masses, softer ends, fewer line-ends; a few lit strands.
4. Cloth planes are a bit like folded card; knees and elbows are angular seams. A few soft transitions (sparing blend) and two or three true fold shadows; check the pelvis/hem passage.
5. Chest highlight should be the thickest, whitest note; confirm it reads. Reflected floor colour (pink/mint) in the shade planes is still missing.
6. Margins: check that the soft far tiles do not look digital; a few broken-colour touches. Upper-right corner slightly blurred from an old blend.
7. "Dissolving" is still not in the picture; only add it if critique 2 misses it (idea: a few tile-shaped white notes leaving the trailing hand/foot). Do not clutter the gap.
8. Furrow strings are faint mid-canvas; decide whether to strengthen them or leave the tiles to do the humming.
9. Final: unifying glaze check, crisp accents at head/near hand, sign (lower corner away from the body), timelapse.

## Tools (all in /home/claude/v14f)
- pose2.py (lay figure from pose_J.json), compose2.py (schema builder: masks idea_P3_fig.npy / idea_P3_shadow.npy; fig2_poly.json, shadow2_poly.json).
- ep2.py: act(felt4, intents) (splits into fours), look(..., to=name) copies to /tmp/v14f, journal, dry; JP = projected joints in canvas px; along(), at() for strokes relative to limbs; quad(), mask_poly(), part() for cloth planes; contour_lines(); crisp_tiles(zone, ...) hard-edge tiles; tiles_in()/lay() loose tiles; floor_colour(); hand(); FIG, SH region polys.
- Head frame: centre (496,1216), axis toward crown a=(-0.85,0.53), across p=(0.53,0.85); P(u,v)=C+a*u+p*v. Mouth at u=-29, nose u=4..-14, eyes u=9 v=+-20, hairline u~26.
- Joints (px): pelvis (791,917), lumbar (733,1009), chest (658,1091), neck (583,1161), sh_l (528,1060), el_l (425,957), ha_l (265,1010) near hand, sh_r (687,1226), el_r (665,1394), ha_r (566,1506) far hand, kn_l (619,695), an_l (826,550), toe_l (903,491), kn_r (970,704), an_r (1088,501), toe_r (1128,430).
- Palette: pink #ff5aa5/#ff3d8f (deep #bf0f78), turquoise #35d3bb (deep #0a8494), lemon #ffe14d, pale #fff4d2; shirt #fbf8ee, shade #cdc7f0/#a59ee0; trousers #e6eafb, shade #b4b4ea/#8a87d6; contour violet #7a72cf; skin #f7a48c, light #ffd9c2, shade #de6f8c; hair #3a1c86/#44209a; shadow #22137c/#1c3f9c glazed #170c6e; glazes #3a1290 (upper left), #fff3c0 (lower right).
- Lessons: the floor cannot be "matched" (confetti) and must be laid tile by tile; round-brush strokes leave capsule ends (use strokes run past the ends and clipped); blend = airbrush, avoid; relaying tiles eats hair, hands and the light gradient, so restate them after.

## Plan for phase 3
Read critique 2 first. Then fine work only: hands, feet, face, hair; two or three folds and bounce colour; margin touches; accents and rim lights; unify; sign; timelapse; final.png.
