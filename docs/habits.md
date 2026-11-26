# Teodor's habits

A running list of what Teodor's paintings keep doing. Every new painting starts by reading this file and looking at the contact sheet of past work (`studio/contact_sheet.py`), and then deliberately breaking at least three of these habits. After each painting, the orchestrator updates this list (add new habits, note which ones were broken).

Last updated after round 16.

## Recurring habits

- **A lone figure seen from behind, in silhouette.** Rounds 3, 4, 5, 6, 7, 8, 9 and 12: one small person, back to us or faceless, standing in the middle distance. We never see a face, and rarely a hand doing something.
- **A rectangle of light in a dark wall.** A doorway, window, gate or frame glowing in a dark room: rounds 4, 7, 8, 9 and 12 (and the lit window of round 10). The threshold has become a signature.
- **One warm light in a dark brown room.** Umber and gold interiors lit by a single soft source (a lamp, a door, a window, footlights): rounds 8, 9, 12. Outdoors it becomes dusk or golden hour: rounds 5, 6, 7, 11.
- **Warm against cool, always the same way.** Amber or orange light against violet, blue or grey shadow. Few other color ideas.
- **Eye-level, middle-distance, centered.** The camera stands where a polite visitor would. Nothing too close, nothing from above or below, rarely a hard crop.
- **A hushed, melancholy mood.** Even rage (round 9) and satire (round 12) came out quiet and elegiac. Critics keep saying "quiet", "solemn", "melancholy".
- **The same kind of feeling.** Almost every chosen feeling is something bittersweet: X held together with grief or loss (pride and loss, relief and guilt, hope and dread, pride and grief, bittersweet joy).
- **Uniform marks.** The same square dab everywhere, soft edges, little difference between a hard focal edge and a lost one; critics call it "a filter".
- **A radiant burst at the centre.** Light exploding from one central point: rounds 3, 11 and 13 (the black noon sun ringed by white).
- **Generic mannequin people.** Faces are blobs or masks, near-identical, with no individual age, character or expression; hands are tubes. Critics notice it in every figure painting.
- **Red and black as the code for drama.** Rounds 2, 3, 12 and 13.
- **One figure in a field, pulled toward a centre.** Even after palette and mood changed in round 14, both versions kept a single central figure with a radial or tunnel pull around it. Critics called it "the same staging formula".
- **A dark double or silhouette.** Shadows and silhouettes stand in for people: rounds 3, 7, 8, 12, 14b.
- **Frontal, stiff bodies.** Even two people side by side (round 15) face front and don't lean toward each other; the feeling ends up only in the hands or faces.
- **A big empty block.** A large field of one color with nothing in it (the quilt in round 15, the audience band in round 12).
- **Old beside young as the shorthand for life.** Rounds 4, 6, 15 and 16: age and youth (or an old couple) stand for the life cycle. Find another carrier.
- **Faces between expression and grimace.** An open mouth and shut eyes, painted as a mask, can read as a laugh or a scream (rounds 13, 15, 16). An expression needs the whole face (cheeks, crow's feet, light) and the body to agree.
- **The signature in the same corner.** Bottom right every time; place it where the painting wants it.
- **Portrait 3:4 every time.** (The canvas format is fixed by the studio; work against it with composition: a crop, a horizon, a figure too big for the frame.)

## Broken so far

- Round 1 (*Updraft*) and round 2 (*Vent*): pure abstraction, bright full-field color, no figure. Nothing since has been that loud.
- Round 11: abstract again, but it fell back into a sunset.
- Round 13 (*Black Noon*): broke the lone figure from behind (a crowd facing us), the dark warm room (glaring noon outdoors), eye level (worm's-eye, cropped hard), amber against violet, and the hushed mood (confronting). A first start that repeated the old pattern was thrown away.
- Round 15: two people instead of one, a high-key pale interior, and a feeling that was not bittersweet. Kept: frontal figures, disc faces, round-dab stamping.
- Round 16 (*Cold Water at the Landing Stage*): broke the lone figure from behind (two faces turned to us, really interacting), eye level (a high view from a jetty, hard crop), the warm dark room (daylight water), amber against violet (vermilion flesh against teal and ultramarine), the hushed mood (loud) and the radial burst (the spray travels sideways). Kept: old beside young, mask-like faces, uniform dab texture, a dark block in the lower third.
- Round 14 (both models): broke the dark room, the amber palette and the hushed mood completely (high-key acid color, open daylight, rapture). Kept: one central figure, a radial pull, mannequin drawing.

## Craft notes from the painters

- Faces and hands work best from a drawn tonal study (an SVG study set as the reference), matched with small brushes. Flesh built from hand-placed strokes comes out as tubes.
- Painting inside a clipped region leaves a hard, pasted-looking edge; break it with loose strokes across the boundary.
- `match` and `free` left alone fall back into square dabs and blob faces.
- Plan face strokes in the head's own coordinates (round 16's `tools/face.py`), then paint the features as planes; lines drawn over the paint read as cartoon.
- A pale veil over a face kills its lights and softens every edge around it; lift lights with opaque paint instead.
- When two critics read the same wrong feeling, change the schema (where the feeling has a form), not only the surface.
