# Experiment log

Each round: what changed in the setup, the hidden emotion, the human's guess, and what we learned.
Rounds were run in one long session (Nov 22–23, 2026) between Robert Ontiu (the human) and Claude (orchestrator), with painter agents spawned as sub-agents.

The test protocol, from round 1 on:
1. The orchestrator draws one emotion at random (Python `random.SystemRandom`) and writes it to a hidden `.secret` file.
2. A painter agent reads it, paints, keeps a journal, and is told never to write the emotion or obvious synonyms anywhere.
3. The human sees only the painting and its title and guesses from 8 options.
4. Then the answer, the journal, and the process artifacts are revealed.

Basic emotions (rounds 1–3): grief, joy, longing, anxiety, serenity, anger, wonder, tenderness.
Complex emotions (rounds 4+): bittersweet nostalgia, relief mixed with guilt, pride tinged with loss, envy, quiet resignation, awe mixed with dread, hope after grief, ambivalence.

---

## Round 0: "A warmth that doesn't know where it came from" (Claude, by hand)
- **Setup:** no agent. Claude painted directly: one gesture at a time with `studio/v0-by-hand/paint.py` (cairo bristle brush), looking at the rendered PNG after every gesture and deciding the next one. 37 strokes.
- **Why it exists:** the human asked whether earlier "feel each stroke" demos were scripted loops. They were. This was the honest version: no loop, decisions made by looking.
- **Learned:** mistakes (a rope-like smoke stroke, ruled ripples) had to be painted over, not undone; accidents (a dry-brush trail) were kept; imagery (distant lights on water) emerged unplanned.

## Round 1: *Updraft, Late Morning* (Elias Varga)
- **Setup:** first sub-agent, persona "Elias Varga". Same cairo brush (`studio/v1-elias/paint.py`), abstract only, ≤3 strokes per gesture, look after every gesture.
- **Emotion:** joy. **Guess:** "joy or wonder… joy." ✅
- **Learned:** the journal showed the agent steering *away* from cousin feelings (sunset/sleepy → serenity). Joy is an easy target (warm, bright, upward).

## Round 2: *Vent* (Teodor, v2)
- **Setup:** `studio/v2`: numpy wet-paint engine (pigment-like mixing, impasto lighting, brush types flat/round/fan/knife/smudge/glaze), a "hand" that turns one intention into many varied marks (mind/hand split), stages (sketchbook → block-in → develop → refine), views (thumb, gray, crop). Abstract only.
- **Emotion:** anger. **Guess:** anger ✅
- **Learned:** structure carried the feeling more than color (a black lid pressing down, red forced through a throat). The title was a giveaway.

## Round 3: *After the Supper Plates* (Teodor, v3)
- **Setup:** `studio/v3`: v2 plus `clip` (marks stay inside a region, so silhouettes hold). The brief now *requires* human symbolism (figures, objects, places) and targets museum visitors with a "three-second test".
- **Emotion:** anger (random repeat). **Guess:** anger ✅
- **Learned:** huge jump in legibility. A man seen from behind with fists, a knocked-over chair, broken plates. Journal highlight: adding the corner of the room so "he is home, which is worse".

## Round 4: *The Marks on the Doorpost* (Teodor, v4)
- **Setup:** `studio/v3` engine, brief switched to complex (mixed) emotions and told to hold both halves.
- **Emotion:** pride tinged with loss. **Guess:** "1 or 7" (bittersweet nostalgia / hope after grief) ❌
- **Learned:** the loss half landed (dark room, the one who stays, a waving hand); the pride half lived only in small clues (height marks on the doorpost, a child-sized chair) and the golden road read as memory or hope. Lesson fed forward: *each half must live in the paint, not only in a clue.*

## Round 5: *The Fork at Evening, the Sail at Morning* (Teodor, v5 "levels")
- **Setup:** `studio/v5-levels`: inspired by Next-Concept Modeling (NCM, coarse-to-fine parallel generation). The canvas is painted in 7 levels (1×1, 2×2, 4×3, 6×4, 8×6, 12×8, accents). Within a level, every cell is decided in one decision and all marks are painted interleaved "in parallel"; each level is conditioned only on the cumulative canvas and cannot be redone. Every level's cumulative and isolated layer is saved (`layers/`, contact sheets).
- **Emotion:** *withheld: the human has not guessed yet.* (Answer to be added here after the guess.)
- **Learned:** 7 decisions instead of ~50 produced a coherent image in ~4 minutes; the big emotional decision (warm half vs. cool half) happened at level 2. The human noted it resembled Claude's very first inline sketch (two lights, something between), although the agent never saw it.

## Round 6: *The Morning After, Number Eleven* (Teodor, v6)
- **Setup:** `studio/v6`: see `docs/research.md` for the reasoning and `docs/prompts/v6-painter-brief.md` for the exact brief.
  - Kubelka–Munk-style pigment mixing, blend brush (sfumato), edge control (hard/soft/lost), glazing, 1200×1600.
  - A **schema** (SVG drawing the painter designs and may revise) + a **making-and-matching** hand that places strokes where canvas and schema differ most, following form.
  - A **felt state** (arousal, tension, valence, care) per episode that drives the hand's kinematics (minimum-jerk speed profile, pressure, width, tremor, angularity, dry-brush at speed, landing hesitation).
  - Many short episodes (≤4 intentions) with a look between each; global/local views; stages from Mace & Ward; time-lapse recording.
- **Run:** 3 conception ideas, 5 distinct schema drawings (6 versions), 59 episodes, ~16 minutes. Two houses the morning after a fire: one spared and lit with a family in the doorway, its identical twin a black shell with a woman kneeling before it; a man at the fence between, head sunk, his shadow across their ash.
- **Emotion:** relief mixed with guilt. **Guess:** "5 or 7" (quiet resignation / hope after grief) ❌
- **Learned:** by far the most professional-looking result (real drawing underneath, form-following strokes, light and space). But the guilt half read as grief (sunk head, hand on post = mourning posture) and the relief half as returning hope (warm light beside dark). The painter predicted "plain grief" as the risk himself. Feelings defined by a *relationship* (my luck, their cost) need the viewer to feel the causal link, e.g. one fire, one wind, one fence with heat on only one side, or the man's gesture directed at the other house rather than inward.

## Round 7: *Gate, Evening* (Teodor, v7; theme: war)
- **Setup:** `studio/v7` = v6 + `scene.py`, a numpy SDF renderer for 3D blockouts (camera, sun, sky, fog/atmospheric perspective, soft shadows, AO, point lights, houses with openings and ruins, fences, trees, and a posable 7.5-head mannequin with presets and joint overrides), plus an SVG overlay. Matching strokes adapt their size to the schema's local detail, sample color from the sharp schema and stop at its edges; a `liner` brush for fine tapered lines. Brief: `docs/prompts/v7-painter-brief.md`.
- **Protocol change:** the human gave a theme ("war"); the painter chose his own feeling and wrote it to `.secret` before painting; the human guessed freely, without options.
- **Run:** 3 conception blockouts, 7 scene versions (one revision mid-painting: lower camera, figure's head against the last light), 76 episodes, ~29 minutes.
- **Feeling:** waiting, meaning hope that will not let go held together with dread. **Robert:** "loss" (close: the dread half). **Blind critic:** "dread while waiting… a vigil for a person who may not come back… a small bit of warmth at the edge" ✅ (nearly exact).
- **Learned:** the in-painting critic failed (the sub-agent had no Agent tool); run critics from the orchestrator instead. Craft gaps per the critic: the figure has no gesture or weight, edges are uniformly blurred with no hierarchy, and the middle values are murky. Next: posture and crisp focal edges.

## Round 8: *The Threshold Light* (Teodor, v7; theme: Emergence: the rise of machines)
- **Setup:** v7 studio; the painter chose a complex feeling; two blind critiques mid-painting (the painter stopped at checkpoints, and the orchestrator ran fresh critics and passed the readings back). The painter session could not be resumed after checkpoint 2, so a fresh session finished from the journal and the canvas state. That led to the phase-based protocol in `docs/orchestration.md`.
- **Run:** 3 idea blockouts, 15 scene versions, 95 episodes.
- **Feeling:** tender pride and grief at being outgrown (machines as our children walking out into the light). **Robert:** "anxiety" ❌. **Critics:** dread/unease each time; the final critic adds "tender welcome".
- **Learned:** direction of travel is decisive. Figures framed in a doorway read as *arriving* even when drawn from behind; arriving plus a dark room reads as dread, so pride never had a chance. Left to choose, the painter returned to the same feeling family as round 4 (parents and children leaving). Craft: the strongest light so far; weaknesses are the anatomy of the key gesture (an arm with no elbow), generic mannequin robots, and a muddy floor.

## Round 9: *The Cross in the Window* (Teodor, v7; theme: Exploding rage)
- **Setup:** the first fully **phase-based** round (`docs/orchestration.md`): three fresh painter sessions with `handoff.md` between them, and blind critiques run by the orchestrator after phases 1 and 2 (`critiques/`). No stuck sessions.
- **Run:** 17 scene versions, 84 episodes.
- **Feeling:** 🔒 withheld until the human guesses.
- **Robert:** "This one is the best one so far."
- **Critics:** all three read held-in, cooling anger and dread rather than an explosion. Their shared craft notes: boxy square strokes look like a digital filter, the figure dissolves into brown, and the umber palette damps the heat. Strongest: the cold window against the warm dark room, with the cracks radiating from the fist.

## Round 11: *The Long Gold Hour* (Teodor, v7; theme: Happiness, abstract)
- **Setup:** the first abstract commission. The brief swapped human motifs for pure color, value, rhythm and gesture, and the schema became an SVG composition instead of a 3D blockout (`docs/prompts/painter-brief.md`, abstract variant). Phase 2 was interrupted at episode 46 and recovered with a fresh session that continued from episode 47, the first test of phase recovery. This is also the first painting made after the guessing game was retired, so the feeling is published with it.
- **Run:** 8 schema versions, 92 episodes.
- **Feeling:** bittersweet joy, happiness that knows it will not last: "the golden hour with my children laughing in the garden, a warmth so full it aches, because some part of me already feels the cool evening coming and loves the light more for it."
- **Critics:** all three read the rising half: elation, a burst of light, with a little vertigo. None read the coming evening as the ache inside the joy. In phase 3 Teodor let the dusk in from three sides, deepened the tide and put one near-black needle at the brightest place; the visitor still read exhilaration and release. Shared craft notes: one big diagonal with no counter-movement, so it can read as a tilted sunset; strokes uniform in width, pressure and direction, like a brush preset; few deliberate hard edges; the upper-right plum corner stamped and unresolved.
- **Learned:** in abstraction the "bitter" half needs its own form, not just darker color at the edges: a counter-movement, a real interval of rest, or a cooling that visibly takes space from the light. A `color_shift` value multiplies the color rather than shifting it (it turned a corner black). The mark vocabulary is still too uniform for abstract work, where the marks are the whole picture: the next studio work is varied pressure, width and direction within a stroke.

## Round 12: *The Footlights* (Teodor, v7; theme: The Orange Buffoon, political satire)
- **Setup:** the first satire, on the vanity of power. Robert's theme pointed at a real politician; the brief made the ruler Teodor's own invented archetype instead (no likeness, no orange skin or yellow hair, no flags or slogans) and put the orange and gold in the world around him: gilt, brass, spotlights. The brief named the tradition: Goya, Daumier, Ensor, Grosz.
- **Run:** 18 scene versions, 78 episodes. The workspace restarted during phase 1; the phase had already finished.
- **Feeling:** "the laugh that catches in the throat: mockery, with a cold draught of fear under it, and a thread of pity."
- **Image:** a small, pot-bellied ruler in a crimson robe and toy crown stands inside a huge empty gilt frame, posing as his own portrait with a fist in the air; the footlights throw a giant, near-black, crowned shadow of him up the wall; a house of cardboard cutouts on struts claps in the dark.
- **Critics:** critic 1 felt solemn expectation, not mockery (a tiny unreadable figure, the frame read as a gallows), which drove a full rebuild in phase 2. Critic 2 got the gag but felt it "more pathetic than biting" and asked for the shadow to become the star. The visitor read "a small man and his huge ego", warm, mild amusement, without much bite. Two of three critics asked for the figure to be painted orange, which the brief ruled out; the studio manager's notes redirected that to the robe, the sash and the glare.
- **Learned:** satire needs a face or a gesture the viewer can read close up; a figure seen from behind keeps the joke at arm's length. The idea (the shadow bigger than the man) carried the painting, but the cold half arrived late and mild. The square-dab texture again flattened the frame, wall and floor. Watch for silhouettes that echo existing symbols: a crowned figure with a raised arm can recall the Statue of Liberty.

## Round 13: *Black Noon* (Teodor, v7; theme: Death)
- **Setup:** Robert asked for it to shock (no gore) and to break the pattern of the earlier work. A first start fell straight back into the pattern (a hushed bedroom, a grieving old man, warm window light) and was discarded after 13 episodes. That led to a lasting change: `docs/habits.md`, a contact sheet of past work (`studio/contact_sheet.py`), and research plus a "break at least three habits" step in the brief. The restarted phase 1 got both.
- **Run:** 25 schema/scene versions, 85 episodes. The painter wrote his own stroke helpers (`tools/`, including `p3/facegen.py` for shaded heads).
- **Feeling:** "noon terror, and the hands of strangers": the panic of dying on hot pavement in glaring daylight in front of everyone, held against the tenderness of strangers who reach for you without knowing your name. Research: Kollwitz's *Death Seizes a Woman*, for the hand that might be helping or seizing.
- **Image:** the viewer is the one on the pavement, looking straight up into a ring of six strangers around a white noon sky with a sun burned black; a woman in red gasps and reaches an open hand at us, a man in black brings two fingers to our throat for a pulse, someone films with the flash on.
- **Habits broken (by the painter's account):** a crowd facing us instead of a lone figure from behind; glaring noon instead of one warm light in a dark room; a worm's-eye view with hard crops; red, black and white instead of amber against violet; a confronting mood.
- **Critics:** critic 1 was puzzled ("an odd group portrait") and suggested dimming the sky to a fading violet, which the studio manager's note refused as the old habit. Critic 2 felt dread first and named the phone filming the death as the strongest idea. The visitor was startled and claustrophobic, then it slid toward comedy, "a fisheye group selfie". Their notes: near-identical faces, rubbery hands, a flat white top half, six heads of equal weight. On the contact sheet: "the viewpoint is a real departure", but it repeats the radiant central light burst, the red-and-black palette and generic mannequin figures.
- **Learned:** the habit list works; the first idea was the old one, and naming the habits got a genuinely different picture. The next limits are craft, not ideas: individual faces with expression, and hands with joints. A wide-angle ring of faces risks reading as a selfie; fewer, more specific witnesses would carry more.

