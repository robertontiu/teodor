# Romanticism: light and shadow (layer 2)

How Romantic painting (c. 1790–1850) handles light on form and on the land, as a departure from the layer-1 baseline in [`docs/subjects/light-shadow.md`](../../subjects/light-shadow.md). Read the style doc [`docs/styles/romanticism.md`](../romanticism.md) first. Researched 2026-11-26 for the case of one low, raking, cold-white light under a storm's edge, everything else in the storm's shadow, and translucent wet linen. **[J]** marks a judgement call; **[M]** marks a value measured on the public-domain images in section 2.

## 1. The twist in one paragraph
Layer 1 lights a form. Romantic painting lights a *place in the land*: a break in the cloud lets one beam fall on a minority of the ground, while the sky holds the main light and the rest of the land sits in the cloud's shadow. Constable called this the "chiar'oscuro of nature" and believed the contrast of light and dark "was a principle of nature" [3]. Burke gives the feeling: "A quick transition from light to darkness, or from darkness to light, has yet a greater effect", and "darkness is more productive of sublime ideas than light" [4]. So the picture is mostly dark ground under a lighter sky, with one bounded patch of light. Form modelling inside that patch follows layer 1. Everything outside it is simplified into large dark masses.

## 2. Works examined and how they were measured
Fourteen paintings and watercolours, eight artists, public domain at the Met and the Cleveland Museum of Art (CMA): Cole, *The Oxbow* (Met 08.228) [5]; Constable, *Branch Hill Pond, Hampstead* (CMA 1972.48) [6] and *Hampstead Heath, Looking Toward Harrow* (CMA 1916.1027) [7] and *A Mill Near Colchester* (watercolour, Met 2007.41) [8]; Georges Michel, *Landscape Near Paris* (CMA 1975.78) [9]; J. C. Dahl, *View over Hallingdal* (Met 2012.447) [10] and *Feige Waterfall* (CMA 2019.76) [11]; Isabey, *A Storm off the Normandy Coast* (Met 2007.164.5) [12]; Turner, *Flüelen* (watercolour, CMA 1954.129) [13], *The Burning of the Houses of Lords and Commons* (CMA 1942.647) [14] and *Whalers* (Met 96.29) [15]; William Turner of Oxford, *A View from Moel Cynwich* (watercolour, CMA 2010.147) [16]; Flers, *Cottage by the River with Washerwomen* (CMA 1980.259) [17]; Cole, *View of Schroon Mountain … After a Storm* (CMA 1917.1335) [18].

**Method [M]:** the museums' open-access web images, frames cropped, sRGB converted to CIE L* (0 black, 100 white), horizon read by eye on a 10 % grid, "lit" pixels = the top 15 % of L* in the picture, or the ground's top 10 %. These are photographs of varnished pictures. Yellowed varnish warms the colours, so hue figures are only relative; value relations are the reliable part. The measuring scripts were scratch work and are not versioned; the numbers are all given here.

## 3. What it stretches and simplifies
- **The light is a patch, not the whole scene.** Ground brighter than its own median by more than 15 L* covers 4–26 % of the land area, median about 13 % [M, 14 works]. The rest of the land is one connected shadow family.
- **The sky holds the light.** In 13 of 14 works, 71–100 % of the brightest 15 % of pixels lie above the horizon, 89 % or more in nine [M]. The sky's mean L* is 11–46 above the land's, median about 20: Oxbow 52/32, Branch Hill 45/21, Michel 56/23, Hampstead 46/28, Hallingdal 40/19, Flers 71/25 [M]. The exception is Isabey's night storm, where the light is a sunset slot in the sea and on breaking foam (32 % in the sky, sky 4 L* darker than the sea). Constable: the sky is "the keynote, the standard of scale, and the chief organ of sentiment" (letter to Fisher, 23 Oct 1821) [2][3].
- **The lit land stays below the sky.** The brightest tenth of the ground averages below the brightest tenth of the sky in 13 of 14 works [M]. In the oils under storm cloud (Oxbow, Branch Hill, Michel, Hampstead, Hallingdal, Feige, Schroon) the gap is 11–43 L*, median 25: for example Michel 46 vs 83, Schroon 38 vs 81, Branch Hill 51 vs 67. In Turner's luminous pictures and the watercolours, where paper or a high-key ground serves both, it shrinks to 2–8 (Constable's *Mill* 74 vs 76). Isabey's night sea is the exception again.
- **Storm cloud is dark but never black.** The darkest 30 % of storm sky sits at about L* 28–32 in five works (Oxbow 29, Branch Hill 29, Michel 32, Hampstead 30, Hallingdal 28) [M]. The land's darks go lower, L* 5–18 [M]. **The land in shadow is darker than the darkest cloud.**
- **The light often lands in the middle distance, and the foreground is dark.** In Branch Hill, Hampstead and Flers the value range of the band just below the horizon (44–57 L*) is larger than the foreground's (24–31) [M]. This inverts layer 1's "contrast falls with distance": aerial perspective is still kept in the *darks*, which lift toward the horizon (Oxbow 8 → 11 → 20, Branch Hill 2 → 7 → 14, Hampstead 15 → 16 → 20, near → mid → far) [M]. The distance can also be a *dark* band under cloud shadow, with the middle ground lit (Michel, Hallingdal) [M].
- **Form shadow is simplified to masses.** Outside the lit patch, trees, hills and figures merge into a few dark shapes with lost edges. Core shadows, reflected light and occlusion (layer 1) appear only inside or at the edge of the light **[J]** from the corpus.

## 4. Conventions
- **Storm edge, light beyond.** A dark storm mass on one side, the light falling on the other: "tempestuous storm clouds" beside "sunlight [that] falls on the farmland beyond" (Oxbow) [5]. Also Hampstead, Michel, Moel Cynwich and Hallingdal [M].
- **Visible shafts.** Rays of light or sheets of rain slanting down from the cloud break (Hampstead, Moel Cynwich, the Oxbow rain curtain) [M].
- **The light's colour.** Two families. A cool silver-white (Michel's lit sky about RGB 207/208/198, Moel Cynwich 217/213/200) [M], and a warm gold at sunset or near fire (Hallingdal, Flers, Turner). A cold-white storm light is fully within the current.
- **Shadow colour under a storm is warm, dark earth, not blue.** Measured ground darks are brown-olive in every work (for example Oxbow RGB 41/36/12, Branch Hill 27/22/14, Michel 37/33/28) [M; varnish warms them]. That follows layer 1's rule that a shadow takes the colour of what lights it: under a cloud there is no blue sky to fill the shadow, only grey cloud and bounce from the brown land **[J]** for the reading.
- **Abrupt transition.** The boundary of the lit patch is the strongest value step in the picture [4]. On the ground it stays soft-edged, as a cloud's shadow is (a kilometre-scale caster; layer 1 penumbra rule), while the lit rims of clouds are crisper **[J]**.
- **Bright small things in the light.** White cloth, sails, a white horse or a whitewashed wall placed in or at the edge of the light are the land's brightest accents [M: Branch Hill's white horse, Flers's laundry and cottage, Whalers' sails, Oxbow umbrella].

## 5. Colour, edge and mark
- **Values:** plan three families, not two: sky (light), lit land patch (middle to light, below the sky), shadowed land (dark, darker than the darkest cloud). Squint must show the patch as one shape **[J]** from the measurements.
- **Edges:** lost edges inside the shadow family; the patch boundary soft; the crispest edges at the light's focus, on the lit object against dark (style doc §8).
- **Marks:** broad dark scumbles for the shadowed land; thicker, lighter paint in the lit patch and sky lights (Constable's "thickly applied highlights" [3]; style doc's selective impasto). Light flecks on the lit ground **[J]** from Branch Hill.

## 6. What stays true to life
- One dominant light; cast shadows and terminators agree with its direction (layer 1). A low light gives long shadows across the ground, raking texture and a warm or cool cast throughout the lit patch.
- The light-family/shadow-family rule (layer 1 §1) holds inside the patch: modelled forms still have a terminator, a core and reflected light there.
- Aerial perspective in the darks (above).
- Translucent materials glow when lit from behind and soften their terminator (layer 1 §3). The sample has no Romantic convention for translucent wet linen, so layer 1 governs it **[J]**.

## 7. For the storm-edge case
- Sky about L* 30 (storm) to about 80 (the break); the lit patch at about 45–65; the shadowed land at about 8–20 **[J]**, scaled from section 3.
- The raking cold-white light falls on a minority of the ground, about 10–25 %, with the figure and the sheets inside it or on its edge [M range].
- **Wet linen:** where the sheets are between the eye and the light, they transmit it. The lit sheet becomes the brightest shape on land, still kept below the sky break. Where a sheet faces away, it is a mid-grey plane, with the sheet behind showing as a darker shape through it **[J]** from layer 1 transmission plus the sky-above-land rule.
- Shadows: warm grey-brown on the land; the cold light makes the lit planes cooler than the shadows. This is the reverse of the usual warm-light/cool-shadow polarity, and it is correct for a cold source with brown bounce **[J]**.

## 8. Avoid
- Even daylight with the land as bright as the sky.
- Black storm clouds (the darkest cloud stays around L* 30).
- A spotlight with a hard edge on the ground.
- Several competing light patches.
- Blue shadows under a storm sky.
- Modelling every form in the shadow.
- A generic orange sunset vortex (style doc pitfall).

## 9. Sources
1. Teodor style doc [`docs/styles/romanticism.md`](../romanticism.md); layer 1 [`docs/subjects/light-shadow.md`](../../subjects/light-shadow.md).
2. Constable to John Fisher, 23 October 1821, transcribed at https://lacrank.blogspot.com/2025/08/john-constable-letter-about-clouds.html (secondary transcription; read).
3. The Met, "John Constable (1776–1837)" (Heilbrunn Timeline): https://www.metmuseum.org/essays/john-constable-1776-1837 (read; "chief organ of sentiment", "Chiar'Oscuro of Nature", "thickly applied highlights")
4. E. Burke, *Philosophical Enquiry* (1757), Part II §15 "Light": https://viscomi.sites.oasis.unc.edu/viscomi/Burke/sublime/II.15.htm (read)
5. The Met, Cole, *The Oxbow*, 08.228: https://www.metmuseum.org/art/collection/search/10497 (image measured; page read)
6. CMA, Constable, *Branch Hill Pond, Hampstead*, 1972.48: https://www.clevelandart.org/art/1972.48 (measured; description read)
7. CMA, Constable, *Hampstead Heath, Looking Toward Harrow*, 1916.1027: https://www.clevelandart.org/art/1916.1027 (measured)
8. The Met, Constable, *A Mill Near Colchester*, 2007.41: https://www.metmuseum.org/art/collection/search/375834 (measured)
9. CMA, Georges Michel, *Landscape Near Paris*, 1975.78: https://www.clevelandart.org/art/1975.78 (measured; description read)
10. The Met, J. C. Dahl, *View over Hallingdal*, 2012.447: https://www.metmuseum.org/art/collection/search/441967 (measured)
11. CMA, J. C. Dahl, *Feige Waterfall*, 2019.76: https://www.clevelandart.org/art/2019.76 (measured)
12. The Met, Isabey, *A Storm off the Normandy Coast*, 2007.164.5: https://www.metmuseum.org/art/collection/search/438950 (measured)
13. CMA, J. M. W. Turner, *Flüelen, from the Lake of Lucerne*, 1954.129: https://www.clevelandart.org/art/1954.129 (measured; description read)
14. CMA, J. M. W. Turner, *The Burning of the Houses of Lords and Commons*, 1942.647: https://www.clevelandart.org/art/1942.647 (measured; description read)
15. The Met, J. M. W. Turner, *Whalers*, 96.29: https://www.metmuseum.org/art/collection/search/437854 (measured)
16. CMA, William Turner of Oxford, *A View from Moel Cynwich*, 2010.147: https://www.clevelandart.org/art/2010.147 (measured; description read)
17. CMA, Camille Flers, *Cottage by the River with Washerwomen*, 1980.259: https://www.clevelandart.org/art/1980.259 (measured)
18. CMA, Thomas Cole, *View of Schroon Mountain, Essex County, New York, After a Storm*, 1917.1335: https://www.clevelandart.org/art/1917.1335 (measured; description read)
