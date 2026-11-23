# Research basis for v6

Before v6, we asked: does our loop resemble how humans actually paint? This is the summary of what we found and how each finding changed the studio.

| Finding | Source | What v6 does with it |
|---|---|---|
| **Making and matching.** Painters don't copy an "innocent eye". They start from a *schema* (a loose first category of the form) and tighten it by placing marks, comparing, and correcting. "Making precedes matching." | E. H. Gombrich, *Art and Illusion* (1960) | The painter draws a **schema** (SVG). The `match` intention compares canvas to schema at the current brush scale and paints where they differ most. The schema can be revised. |
| **Short eye–hand cycles.** A professional portrait painter alternated gaze between model and canvas 12×/min (5-hour portrait) to 22×/min (2-minute sketch), working detail by detail in short episodes; the hand often keeps drawing "blind" while the eye is elsewhere. | Miall & Tchalenko (2001), *Leonardo* 34(1); Tchalenko & Miall (2009), *Cortex*; Tchalenko et al. (2014), *Psychol. Aesthetics, Creativity & the Arts* | Many short **episodes** (≤4 intentions), with a look between every episode; within an episode the hand runs on its own. |
| **Global first, flexible switching.** Artists have superior local *and* global processing, prefer drawing globally first, and switch fluidly between levels; more global saccades while drawing. | Drake, Riccio, Chamberlain & Kozbelt; Chamberlain & Wagemans (2015), *Acta Psychologica*; Park, Williams & Chamberlain (2021) | Views to step back (`thumb`, `gray`) and lean in (`crop`); coarse-to-fine as a rhythm, but free to return to big brushes (unlike v5's fixed levels). |
| **Problem finding.** Art students who spent time *finding and formulating* the visual problem made more original, more compelling work, and were more successful years later. Art-making is a continuous cycle of problem-finding and problem-solving. | Getzels & Csikszentmihalyi, *The Creative Vision* (1976); Mace & Ward (2002) | A conception stage with 2–3 idea sketches; schema revisions are allowed and versioned. |
| **Stages of professional art-making:** conception → development → realization → finalization. | Mace & Ward (2002), grounded-theory model; Botella, Zenasni & Lubart (2018) | The brief's stages. |
| **Feeling travels through gesture.** Viewers covertly simulate the movements implied by brushstrokes (motor cortex activity even for abstract works). The speed of implied motion affects arousal; lines with natural human movement dynamics (varying thickness) are preferred. | Freedberg & Gallese (2007), *Trends Cogn. Sci.*; Sbriscia-Fioretti et al. (2013); Goldsmiths drawing-kinematics studies | A **felt state** per episode drives the hand: minimum-jerk speed profile, speed→thinner and lighter strokes with dry-brush breaks, tension→tremor and jagged corners, valence→smooth vs. angular paths, care→steadier and hesitant landing. |

## Known gaps (not yet modeled)
- Real time pressure and fatigue; the painter's physiological arousal changing over a session (studies measured skin conductance, heart rate while making art).
- Peripheral vision and true viewing distance.
- A learned motor vocabulary (years of practice → automatized strokes). Our hand is parametric, not learned.
- Bimanual and whole-body movement (scale of gesture).
