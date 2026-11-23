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

## Round 2: *Vent* (Teodor Lisk, v2)
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
