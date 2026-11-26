# Hands and feet (layer 1)

Hands and feet as they really are: a palm block with fingers built of three stacked cylinders on a curved row of knuckles, a thumb that moves from low on the wrist, and a foot that is a wedge with an arch. Researched 2026-11. Every value names its source; values marked **judgement** have no published source and are editorial choices for Teodor. Read with `figure` (where they hang and how big they are) and `face` (a hand is as long as the face). The studio's hands (`scene` people and `hand` objects, `docs/MANUAL.md`) follow this page.

## 1. What they are, structurally

**Size.** "Hands are as long as the face" ([Body proportions, Wikipedia](https://en.wikipedia.org/wiki/Body_proportions)); in the canon about three-quarters of a head, and the fingertips of a hanging arm reach mid-thigh (see `figure`). Hand length predicts stature: height (cm) = 80.4 + 5.122 × hand length (cm) − 0.195 × age + 6.383 for men ([PubMed 24169457](https://pubmed.ncbi.nlm.nih.gov/24169457/)). Measured digit lengths: thumb about 7.0 cm in men, 6.4 cm in women; index 7.5 and 7.0 cm ([Greiner 1992, US Army hand anthropometry](https://www.ece.uvic.ca/~bctill/papers/mocap/Greiner_1992.pdf)).

**The palm.** A flat block, "very much like a steak", roundish, squarish or trapezoidal with rounded corners; the fingers attach to it afterwards ([Tuts+, how to draw hands](https://design.tutsplus.com/tutorials/human-anatomy-fundamentals-how-to-draw-hands--cms-21440)). Palm and fingers are roughly equal in length, the palm a little longer (**judgement**; the studio uses palm 0.53 and middle finger 0.44 of the hand length). On the palm side, the ball of the thumb (thenar) and the pad below the little finger (hypothenar) make the palm a shallow cup (**judgement**).

**The fingers.** Each is a stack of three cylinders; "the fold lines of a bent finger correspond to the bases of these cylinders"; "the joints of the fingers are not aligned on straight lines, but fall onto concentric arches", and the true base of a finger "is much lower than the apparent base formed by flaps of skin" (Tuts+). The middle finger is longest, the ring finger next, the index a little shorter, the little finger ends near the last joint of the ring finger (**judgement**, common teaching; the studio's lengths 0.40/0.44/0.415/0.335 of the hand). The phalanges shorten toward the tip, roughly 0.46/0.30/0.24 of the finger (**judgement**).

**The thumb.** "Its real base, and centre of movement, is very low on the hand, where it meets the wrist"; relaxed, it leaves a visible space from the rest of the hand; the maximum spread between thumb and little finger is about 90° from the thumb's base; with the index finger's length as the unit, the widest openings are about 1.5 between thumb and index and 1 between neighbouring fingers (Tuts+). The thumb's pad faces across the palm toward the fingers, so it bends across the palm, not toward it (**judgement**, anatomy; this fixed the studio's stick-like thumbs).

**The foot.** A wedge: high at the ankle and instep, low at the toes; the inner side arched, the outer side flat on the ground; the ankle bone higher on the inside than the outside; about one head long in the adult canon (**judgement**, common drawing teaching; not fetched from a measured source this round).

## 2. Seen from different viewpoints

- **Back of the hand:** the knuckle arc and the tendons fan from the wrist; the fingers look shorter than from the palm side because the webs hide their bases (Tuts+).
- **Palm:** the creases mark the joints; the fingers look longer (Tuts+).
- **Side (thumb side):** the hand is a thin wedge, thick at the base of the thumb; curled fingers show their stacked cylinders (**judgement**).
- **Foreshortened toward the eye:** the fingers overlap and shorten to their tips and nails; draw the palm block first, in perspective, then the cylinders (Tuts+ "stacks of three cylinders ... easier to draw them at any angle").
- **Feet from above:** the instep's wedge and the toes' row, which follows an arc from big toe to little toe; from below: the sole's pads and the arch's shadow (**judgement**).

## 3. Under light

The palm block takes one light and one shadow plane; each finger is a small cylinder with its own core shadow; curled fingers cast shadows into the palm; the gaps between fingers are the darkest accents (**judgement**; see `light-shadow`). Fingertips, knuckles and the heel of the hand are redder than the back of the hand (**judgement**).

## 4. Variation and gesture

- **Age:** a child's hand is plump, short-fingered, the knuckles dimpled; an old hand is bony, with visible tendons, large knuckles and loose skin (**judgement**, observation).
- **Sex and build:** men's hands are larger and broader; the knuckles squarer (Greiner's means show men's digits about 8-10% longer).
- **Gestures the studio has as presets:** open, spread (palms to the wind), relaxed (each finger a little more curled than the one before, from index to little finger), resting on a surface, holding (fingers wrapped round a cylinder, thumb opposed), gripping (a fist with the thumb across), pushing hair back (fingers spread and curved, the wrist bent back), throwing (fingers extending at release, the wrist snapping forward), pointing. These are observational (**judgement**); the angles are in `studio/v8/figure.py`, `HANDS`.

## 5. How painters observe and construct it

1. The mitten: palm block and the fingers as one mass, the thumb as its own wedge, in perspective (the "steak" of Tuts+).
2. The knuckle arc and the finger directions, as lines of action for each finger.
3. The three cylinders of each finger, joints on the concentric arcs.
4. Light on the block first, then the cylinders; the dark gaps last.

## 6. Common mistakes

- **Tubes, mitts, paddles** (habit, every figure round): fingers as one sausage bundle, or no fingers at all; the thumb a stick from the wrist. Check: is there a palm block, a knuckle arc, and a thumb that starts at the wrist and bends across the palm?
- **All fingers the same:** in a relaxed hand each finger curls a little more than its neighbour.
- **Hands too small:** measure against the face.
- **Hands that don't touch:** a hand "on" an object must press, wrap or rest: show the contact shadow and the fingers bending to the surface.
- **Feet as blobs:** no instep, no arch, toes in a straight row.

## 7. Checks for Teodor

1. Is each hand about a face long?
2. Can you see the palm block, then the fingers, then the thumb as a separate wedge from the wrist?
3. Do the knuckles lie on an arc, not a straight line?
4. Does a resting or holding hand make contact (cast shadow, fingers following the surface)?
5. Is the gesture of the hand the same feeling as the face and the body?

## Sources

- [Body proportions, Wikipedia](https://en.wikipedia.org/wiki/Body_proportions)
- [Tuts+, human anatomy fundamentals: how to draw hands](https://design.tutsplus.com/tutorials/human-anatomy-fundamentals-how-to-draw-hands--cms-21440)
- [Greiner 1992, hand anthropometry of US Army personnel](https://www.ece.uvic.ca/~bctill/papers/mocap/Greiner_1992.pdf)
- [PubMed 24169457, hand length as an alternative measurement of height](https://pubmed.ncbi.nlm.nih.gov/24169457/)
