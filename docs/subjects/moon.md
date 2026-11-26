# Moon (layer 1: the subject as it really is)

The Moon as seen from Earth, by day and by night: its true size in the sky and on a lens's image, its phases and which limb is lit, the maria and craters at naked-eye and telephoto scale, the terminator, earthshine, how bright it is against a day sky and a night sky, the low-moon illusion, and how it comes out in a black-and-white photograph. Researched 2026-11. Every value names its source; **judgement** marks values with no published source; **derived** marks arithmetic from sourced values. The sky around the Moon (gradients, clouds, twilight) is in `sky.md`, which already gives the 0.5° size and the lit-side rule in one line each; this page is the full treatment, kept as its own id so it can be researched per style.

## 1. What it is, structurally

**Size in the sky.** Angular diameter 29.3′ to 34.1′ (about 0.49° to 0.57°), varying "by up to 14%" over the elliptical orbit ([Wikipedia, Moon](https://en.wikipedia.org/wiki/Moon)). "Your fingernail and the Moon are about the same size" at arm's length ([NASA, moon illusion](https://science.nasa.gov/science-news/science-at-nasa/2007/27jun_moonillusion)); about half the width of the little finger held at arm's length, which covers about 1° (**judgement**, the rule of thumb in `sky.md`).

**Size on a lens's image.** The Moon's image is about the focal length divided by 110 (f/110, in mm, on any sensor size) ([UniquePhoto Q&A, Sun and Moon on the sensor](https://www.uniquephoto.com/community/qa/how-large-do-the-sun-and-moon-appear-on-the-sensor-at-a-given-focal-length)); the exact factor is f/101 to f/117 over the orbit (**derived**: 2·tan of half the angular diameter). On a 36 × 24 mm frame, and scaled to Teodor's default 48 × 64 cm sheet (the frame's 24 mm side across the 480 mm width, 20×, at 5 px/mm):

| focal length | Moon on the sensor | share of the 36 mm side | on a 48 cm-wide sheet |
|---|---|---|---|
| 24 mm (wide) | 0.22 mm | 0.6% | 4.3 mm (22 px) |
| 35 mm | 0.32 mm | 0.9% | 6.3 mm (32 px) |
| 50 mm ("normal") | 0.45 mm | 1.3% | 9.0 mm (45 px) |
| 100 mm | 0.90 mm | 2.5% | 18 mm (90 px) |
| 200 mm | 1.8 mm | 5.0% | 36 mm (181 px) |
| 400 mm | 3.6 mm | 10% | 72 mm (362 px) |
| 800 mm | 7.2 mm | 20% | 145 mm (724 px) |

(**derived** from f/110.) Filling the 24 mm height of a full frame takes about 2640 mm (same Q&A). So in any picture taken with an ordinary lens, the Moon is a dot: about 0.5° divided by the picture's angle of view (`space.md` has the angles). A large moon over a landscape means a long lens from far away, which also makes the landscape distant and compressed (`space.md`, perspective comes from where the camera stands).

**Phases and the lit limb.**
- The Moon's lit side always faces the Sun. In the Northern Hemisphere the right side is the waxing side; in the Southern Hemisphere the view is rotated 180° and the left side waxes ([Wikipedia, Lunar phase](https://en.wikipedia.org/wiki/Lunar_phase)).
- When the Sun is above the Moon the crescent opens downward; when the Moon is above the Sun it opens upward; near the equator the terminator looks horizontal in the morning and evening (same source).
- More exactly, the lit limb points along the great circle through the Moon and the Sun, which across a wide sky curves; so it often seems to point above the Sun, the "moon tilt illusion" ([Trefethen, *The moon tilt illusion*](https://people.maths.ox.ac.uk/~trefethen/moontilt.pdf), discussing the effect; **judgement** for the great-circle wording, the geometry of illumination).
- **Lit shape (derived geometry):** the lit fraction is k = (1 + cos φ)/2 for phase angle φ; the lit limb is always a semicircle, the terminator a half-ellipse whose semi-minor axis is R·|2k − 1|. At first quarter (k 0.5) the terminator is a straight diameter; at a waxing gibbous of k 0.75 it bows out half a radius into the dark half; the lit width along the Sun line is k × the diameter.

**When each phase is up** (average times, [Wikipedia, Lunar phase](https://en.wikipedia.org/wiki/Lunar_phase)):

| phase | rises | highest | sets | seen |
|---|---|---|---|---|
| waxing crescent | 09:00 | 15:00 | 21:00 | late morning to after dusk |
| first quarter | 12:00 | 18:00 | 00:00 | afternoon and early night |
| waxing gibbous | 15:00 | 21:00 | 03:00 | late afternoon and most of the night |
| full | 18:00 | 00:00 | 06:00 | sunset to sunrise |
| waning gibbous | 21:00 | 03:00 | 09:00 | most of the night and early morning |
| last quarter | 00:00 | 06:00 | 12:00 | late night and morning |

The waxing gibbous is seen "ascending in the east as the sun is descending in the west," and is "easy to see in the daytime" ([EarthSky, waxing gibbous](https://earthsky.org/moon-phases/waxing-gibbous)). The first and last quarters share the sky with the Sun longest, five to six hours a day ([Live Science, daytime moon](https://www.livescience.com/why-moon-visible-daytime)). A full Moon is never in a day sky (it rises at sunset); a new Moon is never seen.

**Surface.** Albedo about 0.12, "comparable to worn asphalt" ([Wikipedia, Moon](https://en.wikipedia.org/wiki/Moon)). Two terrains: "darker basaltic plains (maria) and lighter feldspar-rich highlands"; almost all maria are on the near side, where they cover 31% of the surface (same). True colour, outside the atmosphere, "a muted brownish-gray" (same). Young craters with ray systems (Tycho, Copernicus) stay bright and readily visible (same).

## 2. Seen from different viewpoints (scale and position)

- **Naked eye.** The maria read as a few dark grey patches on a lighter disc (the "face" or "rabbit" patterns of folklore); individual craters are not seen. **Judgement:** the eye resolves about 1′, so the disc is only about 30 resolvable elements across: draw maria as soft-edged patches, not craters.
- **Short telephoto (100–300 mm).** The maria shapes sharpen and the largest craters and the bright rays show; "a 250 mm telephoto" is a basic lunar setup; "at least 500 to 600 mm" for detail ([Royal Museums Greenwich, photographing the Moon](https://www.rmg.co.uk/stories/space-astronomy/how-photograph-moon)).
- **Along the terminator** long shadows make craters and plains "stand out in sharp, clear relief"; at full there are "no visible shadows at all" and the Moon "appears flat and one-dimensional" ([Space.com, when the moon looks best](https://www.space.com/stargazing/dont-wait-for-the-full-moon-heres-when-the-moon-looks-best-through-a-telescope)).
- **Near the horizon.** The Moon is no bigger: photographs at different heights show the same diameter ([NASA, photographing the moon illusion](https://science.nasa.gov/resource/photographing-the-moon-illusion)); it is in fact about 1.5% farther away at the horizon, while it is usually perceived about 50% larger ([Wikipedia, Moon illusion](https://en.wikipedia.org/wiki/Moon_illusion)). Refraction lifts its lower edge more than its upper: about 35′ at the horizon against 29′ half a degree up, so a disc on the horizon is flattened by about 5′, a sixth of its height ([Wikipedia, Atmospheric refraction](https://en.wikipedia.org/wiki/Atmospheric_refraction)); its lower limb may "flatten out or shrink into a pedestal" ([EarthSky, refraction](https://earthsky.org/astronomy-essentials/refraction-distortion-moon-sun-near-horizon/)). A low Moon is yellow to orange, for the same reason as a low Sun (the long path through air, `sky.md`).
- **Where in the frame.** In a rectilinear wide-angle picture, a disc near the corner is stretched radially by about 1/cos of its angle off-axis (1.2× at 35°, 1.35× at 42°) (**derived**, projection geometry, see `space.md`), so even the Moon becomes an oval at the corner of a 24 mm frame.

## 3. Under light

**The disc.**
- The lit limb is sharp: there is no atmosphere to soften it (**judgement**). The disc shows little darkening toward the limb at full, hence the "flat" look (Space.com above).
- Toward the terminator the surface darkens as the Sun gets lower on the Moon, broken by crater shadows (Space.com above). **Measured** on a NASA rendering of a waxing gibbous from LRO elevation and albedo data ([NASA SVS image, GSFC_20171208_Archive_e001862](https://images.nasa.gov/details/GSFC_20171208_Archive_e001862), public domain; a display rendering, so treat as approximate): maria about L* 50 against highlands about L* 80 in the well-lit half, and the lit side fading over roughly the last third of its width before the terminator.
- The dark part of the disc: at night it is black or, near new, lit by earthshine; in the day it is exactly the colour and value of the sky, because the sky is in front of it (**judgement**, follows from the sky being scattered light in our own air). No outline of the full circle shows in daylight.

**Brightness by phase.** The first-quarter Moon is "only 1/11th as bright as full," and reaches half of full's brightness only about 2.4 days before full (Space.com above); the regolith makes the Moon "much brighter at full moon than at quarter phases" (Wikipedia, Moon). So a quarter Moon's lit half has about a fifth of the full Moon's surface brightness (**derived**: half the area, 1/11 the light).

**Against a night sky versus a day sky** (luminances from [Wikipedia, Orders of magnitude (luminance)](https://en.wikipedia.org/wiki/Orders_of_magnitude_(luminance)): Moon surface 2.5 kcd/m², average clear sky 7 kcd/m², average cloudy sky 2 kcd/m², night sky 1 mcd/m²; a full Moon near perigee measured 4.9–5.4 kcd/m², a typical full Moon about 25% dimmer ([Luminance and brightness data for the full Moon](https://spaceweather.com/swpod2009/13jan09/Perigee_moon_2009_01_11_corr.pdf))):
- **Night:** the Moon is about a million times brighter than the sky around it (**derived**). Any exposure that shows the land turns the Moon into a featureless white disc. **Measured** in a NASA photograph of a full Moon over a lit building ([NHQ201611140005](https://images.nasa.gov/details/NHQ201611140005), public domain): the disc is clipped at L* 99.4 ± 1.0 with no maria visible, ringed by a glow that falls from L* 30 just outside the limb to L* 18 at twice the radius, against a sky median of L* 6. Photographers warn to "underexpose slightly to prevent bright details burning out" (RMG above).
- **Day:** the Moon is seen through the sky's own light, so it adds only its surface brightness to the sky's. With a gibbous Moon's lit surface about 0.75–2.5 kcd/m² and the clear sky 3.5–7 kcd/m² (darker away from the Sun: `sky.md`), the Moon is only 1.1 to 1.7 times as bright as the sky beside it, under one stop (**derived**). Hence "pale and ghostly" ([BBC Sky at Night, why we see the Moon by day](https://skyatnightmagazine.com/advice/why-can-see-moon-during-day)): a low-contrast, bluish-white disc with faint maria, never a white hole in the sky.
- **Against things on the ground in daylight:** the Moon's surface gets the same sunlight as the Earth's, and reflects less of it, which is why the "Looney 11" exposure for the Moon is one stop more than the "sunny 16" exposure for a sunlit scene ([Wikipedia, Looney 11 rule](https://en.wikipedia.org/wiki/Looney_11_rule)). So the daytime Moon is about as bright as sunlit worn asphalt (albedo comparison: Wikipedia, Moon), darker than sunlit skin, paper, white cloth or a lit cloud (white illuminated cloud 10 kcd/m²: luminance table above) (**derived**).

**In black-and-white photographs** (`sky.md` for the sky itself):
- Unfiltered panchromatic film renders a blue sky light, so the day Moon is only a few L* above it (**judgement**, from the ratio above: about 5–10 L* at a sky of L* 65–75).
- A yellow filter "darkens the sky slightly", an orange one records blue skies "in very dark tones", a red one records them "as black" ([Ilford, colour filters](https://ilfordphoto.com/colour-filters)); a red filter "will turn a blue sky almost black" ([Photography Mad, coloured filters](https://photographymad.com/pages/view/using-coloured-filters-in-black-and-white-photography)). The Moon is brownish grey, so the filter barely touches it: the filtered sky drops away and the Moon stands out as a light disc on a dark-grey sky (**judgement**, from the filters' action and the Moon's colour). Even then it stays about the value of a sunlit grey stone, not of paper white (**derived**, above).
- A daytime waxing gibbous photographed in the afternoon: Ansel Adams's *Moon and Half Dome* was made "at 4:14 the afternoon of December 28, 1960" with a 250 mm lens ([Ansel Adams Gallery, about this image](https://www.anseladams.com/pages/about-this-image)). Named only as an example of observation: a long lens, a darkened sky, the Moon a small light disc with visible maria above a sunlit cliff.

**Earthshine.** Sunlight reflected by the Earth (mostly its clouds) dimly lights the Moon's dark part; it is best seen in twilight or at night, a few days either side of new, on a thin crescent: "the old Moon in the new Moon's arms" ([Wikipedia, Earthshine](https://en.wikipedia.org/wiki/Earthshine)); earthlight on the Moon is roughly 0.01% of direct sunlight (same). It is invisible in a day sky, and on a gibbous Moon (**judgement**, follows from both).

## 4. Variation
- **Phase:** crescent (horns away from the Sun, earthshine at dusk), quarter (straight terminator, maximum relief along it), gibbous (terminator a bowed half-ellipse, relief on one side only), full (flat, no shadows, bright rays) (sources above).
- **Hemisphere and latitude:** which side waxes, and how far the disc is tilted at a given hour (Wikipedia, Lunar phase).
- **Height in the sky:** low: flattened by a sixth, yellow to orange, dimmed; high: white, round (sources above).
- **Distance:** up to 14% larger at perigee than at apogee (Wikipedia, Moon); not something the eye sees without comparison (**judgement**).
- **Sky:** day (low contrast, bluish), twilight (the Moon brightens against a darkening sky), night (blown out in any exposure with a landscape), through thin cloud (a soft corona or a 22° halo in cirrostratus: `sky.md`).

## 5. How painters observe and construct it
1. **Decide the date and hour before drawing.** Phase, height and the Sun's direction follow from them (the phase table); a waxing Moon in the afternoon is in the east with the Sun in the west.
2. **Point the lit limb at the Sun** along the great circle, and check the scene's cast shadows agree (`light-shadow.md`).
3. **Size it from the lens:** 0.5° on the picture's field of view (the focal-length table); a big Moon needs a long lens and a far viewpoint.
4. **Value from the sky, not from memory:** in daylight a few steps above the sky around it; at night either a white disc (scene exposed) or a detailed grey disc on black (Moon exposed), never both (**judgement**, from the luminance ratios).
5. **Maria first, then the terminator:** the maria pattern places the disc's orientation (it always shows the same face); at naked-eye size two or three soft dark patches are enough (**judgement**).
6. Sketch it the way NASA and RMG advise photographing it: use the terminator for focus and relief, underexpose rather than burn the lights (RMG above).

## 6. Common mistakes
- **A giant Moon** beside a near landscape seen with a normal lens (`sky.md`), or a big crisp Moon beside a sharp foreground at a few metres.
- **Lit side not facing the Sun**, or a crescent at an hour or position it can't have (a crescent rising at midnight; a waxing Moon in the west in the afternoon).
- **The full circle outlined** behind a crescent or gibbous in daylight; earthshine on a daytime or gibbous Moon.
- **A day Moon as bright as paper white** with the maria sharp and dark, or a day Moon whiter than a sunlit cloud.
- **Craters all over a full Moon** with shadows; or a quarter Moon with no relief along the terminator.
- **A night landscape with a detailed Moon** in the same exposure (the moon would be blown out).
- **The low Moon drawn larger,** or round and white on the horizon.

## 7. Checks for Teodor
1. The Moon's diameter on the canvas is about 0.5° of the picture's field of view (the focal-length table); larger only as a stated long-lens view from far away.
2. The lit limb faces the Sun's direction, consistent with every cast shadow; the phase fits the hour (the phase table).
3. The terminator is a half-ellipse of the right width for the phase (k × diameter lit), soft and broken at telephoto scale, the limb opposite it crisp.
4. In daylight the dark part of the disc equals the sky; the lit part sits a few steps above the sky (more if the sky is filter-darkened), at about a sunlit grey stone's value, below sunlit cloud and skin.
5. At night: either a clipped white disc with a faint glow and a visible landscape, or a detailed Moon on a black sky; not both.
6. Maria as a few soft patches at naked-eye size, matching the near side's real pattern.
7. A horizon Moon is flattened (about a sixth) and warm; not enlarged.

## 8. Sources
- Wikipedia: [Moon](https://en.wikipedia.org/wiki/Moon) (angular size, albedo, maria share, colour, rays); [Lunar phase](https://en.wikipedia.org/wiki/Lunar_phase) (which side waxes, rise and set times, crescent orientation); [Moon illusion](https://en.wikipedia.org/wiki/Moon_illusion); [Atmospheric refraction](https://en.wikipedia.org/wiki/Atmospheric_refraction); [Earthshine](https://en.wikipedia.org/wiki/Earthshine); [Orders of magnitude (luminance)](https://en.wikipedia.org/wiki/Orders_of_magnitude_(luminance)); [Looney 11 rule](https://en.wikipedia.org/wiki/Looney_11_rule) (secondary)
- NASA: [The moon illusion](https://science.nasa.gov/science-news/science-at-nasa/2007/27jun_moonillusion); [Photographing the moon illusion](https://science.nasa.gov/resource/photographing-the-moon-illusion); [Moon photography guide](https://science.nasa.gov/moon/photography-guide/); images [GSFC_20171208_Archive_e001862](https://images.nasa.gov/details/GSFC_20171208_Archive_e001862) and [NHQ201611140005](https://images.nasa.gov/details/NHQ201611140005) (public domain, measured here)
- Royal Museums Greenwich, [Photographing the Moon: the basics](https://www.rmg.co.uk/stories/space-astronomy/how-photograph-moon)
- Space.com, [When the moon looks best through a telescope](https://www.space.com/stargazing/dont-wait-for-the-full-moon-heres-when-the-moon-looks-best-through-a-telescope)
- EarthSky, [Waxing gibbous](https://earthsky.org/moon-phases/waxing-gibbous); [Refraction distorts the Moon and Sun near the horizon](https://earthsky.org/astronomy-essentials/refraction-distortion-moon-sun-near-horizon/)
- Live Science, [Why can we see the moon in daylight?](https://www.livescience.com/why-moon-visible-daytime); BBC Sky at Night, [Why can we see the Moon during the day?](https://skyatnightmagazine.com/advice/why-can-see-moon-during-day)
- [Luminance and brightness data for the full Moon](https://spaceweather.com/swpod2009/13jan09/Perigee_moon_2009_01_11_corr.pdf) (perigee Moon, 2009)
- UniquePhoto community Q&A, [How large do the Sun and Moon appear on the sensor](https://www.uniquephoto.com/community/qa/how-large-do-the-sun-and-moon-appear-on-the-sensor-at-a-given-focal-length) (the f/110 rule; secondary)
- Trefethen, L. N., [The moon tilt illusion](https://people.maths.ox.ac.uk/~trefethen/moontilt.pdf) (note)
- Ilford Photo, [Using colour filters for black and white photography](https://ilfordphoto.com/colour-filters); Photography Mad, [Using coloured filters in black and white photography](https://photographymad.com/pages/view/using-coloured-filters-in-black-and-white-photography)
- Ansel Adams Gallery, [About this image (Moon and Half Dome)](https://www.anseladams.com/pages/about-this-image) (example of observation only; not measured, in copyright)
- **Derived** here: the focal-length table, lit-fraction and terminator geometry, corner stretch, quarter-Moon surface brightness, the day and night Moon/sky ratios, the Moon's value against sunlit ground. **Judgement:** finger-width rule, naked-eye resolution and maria as patches, the crisp limb, the dark part equal to the sky by day, unfiltered and filtered Moon/sky values, earthshine invisible by day, order of work.
- Not reached: Minnaert, *Light and Colour in the Outdoors*; a photometric (not rendered) measurement of maria against highlands; a public-domain black-and-white photograph of a daytime Moon to measure (the Library of Congress and NASA searches found none in the time available; Wikimedia Commons refused automated access, and was not retried).
