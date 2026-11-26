# Light and shadow (layer 1)

Light on form as it really is: how a lit object divides into a light family and a shadow family, how shadows are shaped and edged, how the colour of the light and the colour of the shadow relate, what several lights do, and how air changes everything with distance. Researched 2026-11. Every value names its source; values marked **judgement** have no published source and are editorial choices for Teodor. Every other subject page refers here.

## 1. What it is, structurally

**Two families.** Every lit form divides at the **terminator**, "the line by which an object's light and shadow sides are separated" ([Sessions College, The anatomy of a shadow](https://www.sessions.edu/notes-on-design/looking-at-light-the-anatomy-of-a-shadow/)), into a light family and a shadow family. The rule that holds the picture together: the darkest value on the light side stays lighter than the lightest value on the shadow side, and reflected light "must be darker than the darkest value of the light side" (same source).

**The elements, with values on a 0–10 scale** (0 black, 10 white; values from [Proko, Elements of Light and Shadow](https://www.proko.com/course-lesson/elements-of-light-and-shadow/notes), for a light-coloured matte form in one strong light; they shift with local colour and lighting):

| element | what it is | value |
|---|---|---|
| highlight | mirror reflection of the source; "not present on matte materials" | 10 |
| centre light | the plane facing the light most directly | 9–10 |
| halftones | the form turning away; the lightest is the largest area | light 8–9, medium 6–7, dark 4–5 |
| terminator | the edge between light and shadow | — |
| core shadow | darkest part of the form shadow, just past the terminator | 1–2 |
| reflected light | light bounced from the surroundings into the shadow | ~4 (always below the darkest halftone: Sessions) |
| occlusion shadow | crevices and contacts where no light, direct or reflected, reaches | 0 |
| cast shadow | the shadow one form throws on another | 2–3, darker and sharper near the object, lighter and softer away |

Block the whole shadow shape first at one value (about 3 in Proko's scheme), then find the core and the reflected light; values do not change in a simple gradient: they "quickly darken at core shadows, lighten with reflected light" (Proko).

**Why the core exists.** The core shadow sits where the form has turned away from the main light but not yet toward the light bouncing back; it persists "because the main light is stronger than the reflected light", and two equally strong lights from opposite sides would remove it (Sessions).

**Light falls off with the angle of the surface.** A matte surface's brightness is proportional to the cosine of the angle between its normal and the light (Lambert's cosine law; standard optics, **not fetched**). So halftones are wide where the form turns slowly and narrow where it turns fast; a plane change shows as a value step (**judgement** for the painting consequence).

**Cast shadows** start at the terminator: "the shadows all stem from the terminator" (Sessions); a cast shadow is the projection of the terminator line onto the receiving surface (**judgement**, follows from geometry). Its edge is set by the size of the source: the sun's disc is about 0.5° across, so its rays diverge by that much and every shadow has a dark umbra and a softer penumbra ([Atmospheric Optics](https://www.atoptics.co.uk/fz317.htm)). Derived from 0.5°: the penumbra is about 1/110 of the distance from the casting edge to the receiving surface (1 cm wide at 1 m, 10 cm at 10 m) (**judgement**: arithmetic, not a quoted value). Hence a shadow is sharp at the contact point and softens with distance; larger or closer sources (a window, an overcast sky, a lampshade) give much softer shadows.

**The viewer assumes light from above.** The visual system resolves ambiguous shading by assuming light from above and slightly to the left ([Ramachandran 1988, *Nature*](https://www.nature.com/articles/331163a0.pdf); Mamassian & Goutcher 2001, *Cognition* 81, B1–B9, is the usual reference for the leftward bias, cited here via [McCourt et al. 2013](https://www.frontiersin.org/articles/10.3389/fpsyg.2013.00983/full)). Measured priors vary: one fit put the assumed direction about 3° left of vertical (tilt 93.2°, observers 89.7–97.1°), while other studies imply about 20° left (tilt ~110°) ([O'Shea, Agrawala & Banks 2010, *Journal of Vision*](https://pmc.ncbi.nlm.nih.gov/articles/PMC3066057)). Consequences: shading that only makes sense with light from below can flip bumps into hollows, and light from below reads as unusual or uneasy (**judgement** for the second point).

## 2. Seen from different viewpoints (the light's direction relative to the viewer)

(**judgement**, standard lighting vocabulary, the geometry following from section 1)
- **Front light** (behind the viewer): almost all light family, little shadow, form told by halftones and edges; shapes flatten, colour reads strongly.
- **Side light** (90°): about half light, half shadow; the terminator crosses the middle of the form; texture and form are strongest.
- **Three-quarter light** (about 45° to the side and above): most of the form lit, a clear terminator and cast shadows; the most common studio light for modelling.
- **Top light:** shadows under brows, nose, chin and in eye sockets; heads become masks unless there is fill.
- **Back light (contre-jour):** the form is mostly shadow with a rim of light on the edges; edges, silhouettes and the glow of translucent things (hair, ears, leaves, thin cloth) carry the picture.
- **Light from below:** against the viewer's prior (section 1); firelight, footlights, a lamp on a table.
- **Distance from the viewer:** with distance, values compress toward the air (section 4, atmospheric perspective) and small shadows (cores, occlusions) disappear first.

## 3. Under light: colour of light and colour of shadow

- **Light sources have colour.** Correlated colour temperatures: a 100 W incandescent bulb about 2800 K, direct noon sunlight about 4870 K, average daylight (D65) about 6500 K, overcast skylight about 6770 K ([HyperPhysics, Color temperature](https://hyperphysics.gsu.edu/hbase/phyopt/coltemp.html)). Candle flame is lower still, around 1900 K (**judgement**, commonly cited, not fetched). Low numbers are orange, high numbers blue.
- **The shadow is lit by something else.** Outdoors in sun, shadows are lit mainly by blue skylight while lit planes get sunlight plus skylight, so "in most sunny conditions, shadows really are in a complementary color range compared to the sunlit surfaces"; a white sheet in shadow photographs noticeably bluer ([Gurney, Complementary shadows](https://gurneyjourney.blogspot.com/2014/09/complementary-shadows.html?m=1)). The effect grows as the sun gets lower (same). But if warm surfaces surround the shadow and the sky is blocked, "the shadow might be very warm, too" (same). Rule: **the colour of a shadow is the colour of whatever lights it**, not a fixed complement.
- **Simultaneous contrast** pushes a neutral next to a colour toward its complement, so shadows also *look* complementary beyond what is physically there (Gurney).
- **Reflected light takes the colour of the reflector:** "every opaque and colourless body assumes the hue of the colour reflected on it" ([Leonardo, Notebooks §281](https://www.fromoldbooks.org/R.bak/section-5/item-281.html)). A face over a red shirt has a red under-chin; grass greens the underside of a white cow.
- **Translucent materials** (skin, ears, leaves, wax, thin cloth, light hair) let light scatter inside them, so the terminator softens and often becomes the most saturated band, warm and reddish on skin ([Proko community discussion](https://proko.com/community/topics/why-there-s-higher-saturation-near-the-terminator), secondary; **judgement**).
- **Saturation.** The light side carries the source's colour mixed with the local colour; halftones are usually where local colour is most saturated; the highlight takes the light's colour, not the object's (**judgement**; the highlight point follows from Proko's definition and, for hair, from Marschner, see `hair`).

## 4. Variation

- **Weather and time of day** (**judgement** unless noted): direct sun: hard cast shadows, strong value split, cool shadows (Gurney); low sun: long shadows, warm light, the colour split strongest (Gurney); overcast: one huge soft source, almost no cast shadows, form told by occlusion and gentle top-to-bottom gradation, colours saturated and cool; fog and haze: contrast collapses with distance (below); night and artificial light: small warm sources, rapid falloff.
- **Falloff with distance from a lamp:** illuminance falls with the square of the distance from a small source (inverse-square law; standard optics, **not fetched**): a figure twice as far from the candle gets a quarter of the light. Large sources (windows, sky) fall off more gently (**judgement**).
- **Several lights.** In photography the key-to-fill ratio sets the contrast: (key + fill) : fill, with 4:1 a two-stop and 8:1 a three-stop difference; a higher ratio gives higher contrast ([Wikipedia, Lighting ratio](https://en.wikipedia.org/wiki/Lighting_ratio)). For painting (**judgement**): keep one dominant light that owns the terminator and the cast shadows; a second light (sky fill, a bounce, a rim) only lifts the shadow family and colours it, without crossing into the light family; two equal lights split the form into two lit sides with a dark core line between, and each light throws its own cast shadow, darkest where they overlap.
- **Materials:** matte surfaces show broad halftones and no highlight (Proko); glossy ones show a sharp highlight in the light's colour and reflect their surroundings; metals have almost no diffuse colour and are mostly reflection; translucent ones glow (**judgement** beyond Proko).

**Atmospheric (aerial) perspective.** Air between the eye and the object adds its own light and removes the object's contrast.
- Leonardo: distant things look blue, "almost of the same hue as the atmosphere itself"; make a building five times as distant "five times bluer" ([Notebooks §295](https://www.fromoldbooks.org/Richter-NotebooksOfLeonardo/section-6/item-295.html)); and "those will look of the bluest colour which are in themselves the darkest", so bare winter mountains are not blue like summer ones ([§461](https://www.fromoldbooks.org/Richter-NotebooksOfLeonardo/section-8/item-461.html)).
- Physics: apparent contrast decays exponentially with distance (Beer–Lambert / Koschmieder), and visual range is defined where contrast falls to 2 %: x = ln(50)/b ≈ 3.912/b for an extinction coefficient b; visibility is up to about 240 km in very clean air, 2–5 km in haze, under 1 km in fog ([Wikipedia, Visibility](https://en.wikipedia.org/wiki/Visibility)). Derived rule for painting (**judgement**, arithmetic from the 2 % definition): at a distance d with visibility V, contrast is about 0.02^(d/V): 38 % of its near value at a quarter of V, 14 % at half, 2 % at V.
- In practice: darks lighten and turn toward the sky's colour fastest; lights dim and, toward a low sun, warm; edges soften; saturation drops; details go first (**judgement**, consistent with Leonardo §295 and §461 and the contrast law).

## 5. How painters observe and construct it

- **Squint** to merge everything into the two families, then check the shadow shapes as single flat shapes (**judgement**, standard atelier practice; Teodor's studio has `squint` and `notan` views for it).
- **Order of work** (after Proko): block the shadow shapes at one value; then halftones; then the core along the terminator and the reflected light, kept inside the shadow family; occlusion accents; highlights last and few.
- **Mid-tone grounds.** Renaissance drapery studies were drawn with a brush on a mid-tone ground, shading down in black and heightening up in white ([Royal Collection Trust, Leonardo drapery study](https://www.rct.uk/collection/exhibitions/leonardo-da-vinci-a-life-in-drawing/the-drapery-of-a-kneeling-figure)): the ground is the halftone, so only the two families need adding.
- **Light logic before colour:** decide the source (where, how big, what colour), the fill (what lights the shadows, what colour), and the air (how far, how hazy); then every value and colour follows (**judgement**).
- Leonardo's notebooks are an example of observation (reflections, aerial colour), not a model of manner.

## 6. Common mistakes

- **Families that overlap:** reflected light as bright as the halftones, or halftones dropped into shadow values; the form loses its light (Sessions; Proko).
- **Shadow as black or grey:** shadows made by darkening the local colour with black instead of finding what lights them (**judgement**; Gurney's skylight shadows are the counter-example).
- **One formula for every light:** warm light and violet shadow by reflex, regardless of the source; this is Teodor's "warm against cool, always the same way" habit (`docs/habits.md`). Under a cool north window the light is cool and the shadow relatively warm; under overcast sky everything is cool and soft; under a red neon the light is red (**judgement** for the examples).
- **Pillow shading:** darkening around the outline of every shape instead of from a light direction (**judgement**).
- **Floating objects:** no occlusion or contact shadow where a thing meets the ground (Sessions).
- **Uniform cast shadows:** the same hard edge and value from contact to tip, or soft shadows under a hard sun (Atmospheric Optics on the penumbra).
- **Inconsistent lights:** cast shadows and terminators that point to different sources in one picture (**judgement**).
- **Highlights on matte things,** or a highlight the colour of the object instead of the light (Proko).
- **Aerial perspective as white fog** laid evenly over everything, or blue on light distant things where Leonardo says the darkest go bluest (§461).
- **Rim light everywhere** as a decorative outline without a source behind (**judgement**).
- **The radiant burst:** light radiating from a central point as a symbol rather than a source in a space (Teodor's habit; **judgement**).

## 7. Checks for Teodor

1. Name the key light (direction, size, colour) and what fills the shadows; every terminator and cast shadow in the picture agrees with them.
2. Squint or `notan`: two clear families; nothing in shadow is as light as the darkest light-side value.
3. Each form has a core shadow along the terminator, reflected light inside the shadow, and occlusion accents at contacts.
4. Cast shadows are sharp at contact and soften with distance, more so for bigger sources.
5. Shadow colour comes from the fill source and nearby reflectors, not from a fixed complement.
6. With distance, contrast and saturation drop toward the air's colour, darks first.
7. Highlights only on glossy or wet surfaces, in the light's colour, few.

## 8. Sources

- Proko, [Elements of Light and Shadow (lesson notes)](https://www.proko.com/course-lesson/elements-of-light-and-shadow/notes).
- Sessions College, [Looking at light: the anatomy of a shadow](https://www.sessions.edu/notes-on-design/looking-at-light-the-anatomy-of-a-shadow/).
- Atmospheric Optics, [Shrinking heads and sharper sundials](https://www.atoptics.co.uk/fz317.htm) (the sun's 0.5° and the penumbra).
- V. S. Ramachandran, [Perception of shape from shading](https://www.nature.com/articles/331163a0.pdf), *Nature* 331, 1988 (not read in full).
- Mamassian & Goutcher, Prior knowledge on the illumination position, *Cognition* 81, 2001 (not read; cited via McCourt, Blakeslee & Padmanabhan, [Lighting direction and visual field modulate perceived intensity of illumination](https://www.frontiersin.org/articles/10.3389/fpsyg.2013.00983/full), *Frontiers in Psychology* 4:983, 2013).
- O'Shea, Agrawala & Banks, [The influence of shape cues on the perception of lighting direction](https://pmc.ncbi.nlm.nih.gov/articles/PMC3066057), *Journal of Vision* 10(12), 2010.
- HyperPhysics, [Color temperature](https://hyperphysics.gsu.edu/hbase/phyopt/coltemp.html).
- James Gurney, [Complementary shadows](https://gurneyjourney.blogspot.com/2014/09/complementary-shadows.html?m=1), Gurney Journey, 2014.
- Leonardo da Vinci, Notebooks (Richter ed.): [§281 reflected colour](https://www.fromoldbooks.org/R.bak/section-5/item-281.html), [§295 aerial perspective](https://www.fromoldbooks.org/Richter-NotebooksOfLeonardo/section-6/item-295.html), [§461 winter mountains](https://www.fromoldbooks.org/Richter-NotebooksOfLeonardo/section-8/item-461.html).
- Wikipedia, [Visibility](https://en.wikipedia.org/wiki/Visibility) (contrast decay, 2 % threshold, visual ranges); [Lighting ratio](https://en.wikipedia.org/wiki/Lighting_ratio).
- Royal Collection Trust, [Leonardo, The drapery of a kneeling figure](https://www.rct.uk/collection/exhibitions/leonardo-da-vinci-a-life-in-drawing/the-drapery-of-a-kneeling-figure).
- Proko community, [Why there's higher saturation near the terminator](https://proko.com/community/topics/why-there-s-higher-saturation-near-the-terminator) (forum, secondary).
- Not fetched, standard optics: Lambert's cosine law, the inverse-square law, candle colour temperature.
