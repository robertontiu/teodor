# Space: perspective, horizon, recession and scale

Layer 1 for `space`: how a three-dimensional scene projects onto a flat canvas, and the cues a viewer uses to read depth. It covers linear perspective (one, two and three points), horizon and eye level, the cone of vision and lens choice, ellipses and inclined planes, cast shadows in perspective, the foreshortening of a whole scene, overlap, scale cues and aerial perspective. Buildings and rooms are in `architecture.md`; light on single forms is in `light-shadow.md`; still-life objects are in `objects.md`.

## 1. What it is, structurally

### The picture plane and the eye
- Linear perspective is a central projection: every point of the scene is joined to one eye (the **station point** or viewpoint), and the picture is where those rays cross a plane in front of it (the **picture plane**). Brunelleschi demonstrated it about 1420 by painting the Florence Baptistery, piercing a hole at the vanishing point and checking the painting in a mirror against the building; Alberti codified it in *On Painting* within a couple of decades ([Smarthistory](https://smarthistory.org/linear-perspective)).
- **Sizes follow similar triangles.** With object size Z at distance X and a viewing distance x, the image size is z = Z·x/X. An object twice as far away is drawn half as tall ([handprint, central perspective](https://www.handprint.com/HP/WCL/perspect2.html)).
- **The horizon line is eye level.** It is the vanishing line of the ground plane; its height on the canvas sets the viewer's height, and anything at the viewer's eye height sits on it, at any distance ([handprint](https://www.handprint.com/HP/WCL/perspect2.html); [handprint, two-point](https://www.handprint.com/HP/WCL/perspect3.html)). A horizon above the canvas's midline means the viewer looks down; below it, up (same source).
- **Eye heights:** standing adult eye about 1.5-1.6 m (handprint's worked examples use 1.5 m; the studio's `scene.py` camera default is 1.6 m). Seated about 1.1-1.2 m, a child about 1 m, a first-floor window about 4-5 m (**judgement**).
- **Consequence on flat ground** (follows from the geometry above): the horizon cuts every standing figure of the same height at the same place, at any distance. With the eye at 1.6 m and figures 1.75 m tall, the horizon runs through every figure's eyes or brow, near and far. A child's head stays below it everywhere; a rider's rises above it everywhere.
- **Height in the field:** a point on the ground at distance D lies below the horizon by an angle of atan(h/D), where h is eye height. Near ground is low on the canvas and recedes upward toward the horizon (geometry; handprint notes that half the horizon's height below it is twice the viewing distance in depth).

### Vanishing points
- **Parallel lines share one vanishing point**; lines parallel to the picture plane have none ([handprint](https://www.handprint.com/HP/WCL/perspect2.html)). The vanishing point of any set of parallels is where a ray from the eye, parallel to them, meets the picture plane (the visual-ray method, same source).
- **Horizontal lines vanish on the horizon.** Lines on any plane vanish on that plane's own vanishing line (same source).
- **One-point (central) perspective:** a box face parallel to the picture plane; all depth lines (orthogonals) meet at the principal point straight ahead on the horizon. The two **distance points** sit on the horizon at the viewing distance left and right of it; 45° diagonals of a ground grid vanish there (same source).
- **Two-point perspective:** a box turned to the picture plane. Its two horizontal edge sets are 90° apart, so their vanishing points satisfy: if one face is turned x°, the other is 90°-x°. Each VP sits at tan(angle) × viewing distance from the centre of vision: at 45°/45° both are one viewing distance out, so the VPs are **two viewing distances apart**; at 30°/60° they are 0.58 and 1.73 viewing distances out ([handprint, two-point](https://www.handprint.com/HP/WCL/perspect3.html)). Verticals stay vertical (same source).
- **The most common two-point fault is VPs too close together**, which makes boxes bulge as in a wide-angle photograph; widely spaced VPs flatten them as in a telephoto view (same source).
- **Three-point perspective:** when the view tilts up or down, verticals converge on a third VP on the vertical line through the centre of vision: above the horizon looking up, below it looking down. A third VP close to the horizon gives violent foreshortening; rule of thumb: put it at least as far from the horizon as the two horizontal VPs are from each other ([Advanced Perspective Techniques, OUP](https://learninglink.oup.com/protected/files/content/file/1573546337378-Advanced-Perspective-Techniques.pdf)).
- **Inclined planes** (roofs, ramps, stairs, an open lid): their sloping edges vanish on an auxiliary VP on the vertical through the VP of their horizontal direction, above it for planes rising away from the viewer and below it for planes falling away. A gable roof with equal pitches has its two auxiliary VPs equally far above and below the horizon (OUP; [handprint](https://www.handprint.com/HP/WCL/perspect2.html) for stairs).
- **Dividing depth:** the diagonals of a rectangle in perspective cross at its perspective centre (halves only); a measuring line parallel to the picture plane with a measuring point on the horizon gives thirds, tenths or unequal divisions (OUP). The measure point for a VP at 90°-x from the centre of vision lies at x/2 on the opposite side ([handprint, two-point](https://www.handprint.com/HP/WCL/perspect3.html)).

### The cone of vision and viewing distance
- Undistorted vision covers about **60°**: 30° each side of the line of sight. Forms drawn outside this cone stretch and distort ([BYU-Idaho, cone of vision](https://courses.byui.edu/art110_new/art110/week02/cone_of_vision.html)). Handprint puts extreme foreground distortion outside the 60° circle and recommends composing within it ([handprint](https://www.handprint.com/HP/WCL/perspect2.html)).
- A picture is most comfortably seen at about a **25°** circle of view, a viewing distance of about 2.5 times its controlling dimension (same source).
- A perspective picture is exact from one point only. Viewed from elsewhere it reads as telescopic or wide-angle (same source). Hoogstraten's perspective box (National Gallery, London, about 1655-60) is an extreme example: a jumble of walls and tiles from the open end that resolves into a Dutch house only through the peephole ([National Gallery](https://www.nationalgallery.org.uk/paintings/samuel-van-hoogstraten-a-peepshow-with-views-of-the-interior-of-a-dutch-house)).

### Ellipses (circles in perspective)
- The minor axis of an ellipse lies along the axis of its cylinder, like an axle through a wheel; the major axis is at 90° to it ([New Masters Academy ellipse handout](https://s3.amazonaws.com/uploads.nma.art/uploads/2021/03/Ellipse-Guide_Drawing-Foudations-Handout.pdf)).
- The degree (how open the ellipse is) grows as the circle moves away from eye level: a horizontal circle at eye level is a line; the bottom of a cup below the eye is rounder than its rim (same source). The far half of a perspective circle is smaller than the near half ([BYU-Idaho, ellipses](https://courses.byui.edu/art110_new/art110/week01/ellipses.html)).
- Ends are rounded, never pointed ("football" ellipses read as creased circles) (same source).

### Shadows in perspective
- Sun rays are parallel, so they vanish too: at the sun when it is in front of the viewer, and at the antisolar point (below the horizon, centred on the viewer's own shadow) when it is behind. Shadows on the ground vanish at the point on the horizon below (or above) that light point; shadow edges run toward it or away from it ([perspective notes, shadows and reflections](https://bertverhees.github.io/perspect6.html)).
- The sun subtends about 0.5°, so a shadow's soft edge (penumbra) is about 1% of the distance from the casting edge to the shadow (same source).

### Lens and angle of view
- Angle of view = 2·atan(d/2f), with d the format dimension and f the focal length ([Wikipedia, Angle of view](https://en.wikipedia.org/wiki/Angle_of_view_(photography))). On 35 mm (36 × 24 mm):

| focal length | horizontal | vertical | diagonal |
|---|---|---|---|
| 24 mm (wide) | 73.7° | 53.1° | 84.1° |
| 35 mm | 54.4° | 37.8° | 63.4° |
| 50 mm ("normal") | 39.6° | 27.0° | 46.8° |
| 85 mm | 23.9° | 16.1° | 28.6° |
| 200 mm (tele) | 10.3° | 6.9° | 12.3° |

- **Perspective comes from where the eye stands, not from the lens.** A wide lens is used close, which makes near things large and far things small (extension); a long lens is used far away, which makes distant things similar in size and depth hard to judge (compression). Lenses of about 85-135 mm are the usual portrait choice, because they are used at a distance that does not swell the nose ([Wikipedia, Perspective distortion](https://en.wikipedia.org/wiki/Perspective_distortion)).
- **Studio mapping:** `scene.py`'s `fov` is the **vertical** angle (it scales by the canvas height). 35 mm equivalent f = 12 mm / tan(fov/2): `fov` 53 ≈ 24 mm, 40 (default) ≈ 33 mm, 27 ≈ 50 mm, 16 ≈ 85 mm, 7 ≈ 200 mm (computed from the formula above). Horizontal angle = 2·atan(aspect · tan(fov/2)); at the default 40° on a 3:2 canvas it is about 57°, just inside the 60° cone.

### Depth cues and where each works
Cutting and Vishton (1995) rank the depth sources by distance band ([Perceiving layout and knowing distances](https://scispace.com/pdf/perceiving-layout-and-knowing-distances-the-integration-1i3ri93gex.pdf)):
- **Personal space (within about 2 m):** occlusion, binocular disparity, relative size, convergence and accommodation. A painting has only occlusion and relative size here.
- **Action space (about 2-30 m):** occlusion, height in the visual field, disparity, motion perspective, relative size.
- **Vista space (beyond about 30 m):** occlusion, height in the visual field, relative size and aerial perspective.
- **Occlusion** works at every distance with a threshold of about 0.1% and does not weaken with distance; it is the strongest cue overall. **Relative size** works from about 0.5 m to 5 km. **Height in the visual field** works from about 2 m out. **Aerial perspective** grows with the logarithm of distance and only matters far away. **Texture density** is marginal (about 10% threshold) (same source).
- So a painting's depth rests on overlap, size and height on the ground plane everywhere, and on aerial perspective only for the far distance.

### Aerial (atmospheric) perspective
- Air between the eye and an object adds a veil of scattered skylight. Contrast falls, both against the background and inside the object; colours desaturate and shift toward the colour of the air: bluish in daylight, reddish near sunrise and sunset, grey in fog. Contrast drops at all scales at once, which is different from blur, which removes only fine detail ([Wikipedia, Aerial perspective](https://en.wikipedia.org/wiki/Aerial_perspective)).
- **Koschmieder's law:** apparent contrast C = C0·e^(-σd), where σ is the extinction coefficient and d the distance. Visual range (2% contrast) = 3.912/σ ([AMS Glossary, Airlight formula](https://glossary.ametsoc.org/wiki/Airlight_formula); [Wikipedia, Visibility](https://en.wikipedia.org/wiki/Visibility)). Since the veil is added light of the horizon sky's colour, **dark objects lighten and bright objects dim, both converging on the horizon sky's value and hue** (follows from the airlight formula).
- Visibility classes: fog below 1 km, mist 1-2 km, haze 2-5 km; the cleanest possible air would allow about 296 km (Wikipedia, Visibility).
- **Studio mapping:** `scene.py` fog mixes in `1 - exp(-d·density)`, the same law. `density` 0.008 (default) gives a visual range of about 490 m, which is fog; clear haze of 20 km is about 0.0002, haze of 3 km about 0.0013 (computed). Choose density from the weather, not by habit.

## 2. Seen from different viewpoints
- **Eye level (horizon in the middle third):** the calm, documentary view. Ground and sky planes both visible; standing figures key to the horizon at their eyes.
- **High viewpoint (horizon high or above the frame):** much ground visible, figures seen from above, verticals converge downward if the view tilts (three-point). Gives overview, map-like order, smallness of people.
- **Low viewpoint (horizon low or below the frame):** sky dominates, figures and buildings tower and rise above the horizon; verticals converge upward if the view tilts.
- **Level view, two-point:** keep verticals vertical when the line of sight is horizontal; most ground-level architecture needs no third VP ([handprint, two-point](https://www.handprint.com/HP/WCL/perspect3.html)). Verticals that converge are a decision to tilt the view, and then all of them must converge on one VP.
- **Near versus far viewpoint:** standing close (wide angle) exaggerates the size gap between near and far, steepens floor and road convergence, and swells objects at the edges; standing far (long lens) flattens depth into stacked layers of similar size ([Wikipedia, Perspective distortion](https://en.wikipedia.org/wiki/Perspective_distortion)).
- **Foreshortening of the whole scene:** equal steps in depth shrink fast on the canvas. A ground interval ΔD at distance D occupies about f·h·ΔD/D² vertically, so it shrinks with the square of distance: tiles one metre apart at 4 m are about four times taller on the canvas than at 8 m (geometry, from height in the field). Distant ground compresses into thin bands near the horizon.
- **Beyond about 90° of view** a flat (rectilinear) projection stretches spheres and figures at the edges grotesquely; curvilinear projections bend straight lines instead (Wikipedia, Perspective distortion). Keep important forms inside the 60° cone.

## 3. Under light
- **Light direction lives in the same perspective as the forms.** All sun shadows on flat ground converge (or diverge) toward one point on the horizon; shadows on a wall vanish on that wall's vanishing line (bertverhees perspective notes).
- **Lamp light** spreads from a point: shadows radiate from the foot of the lamp on the floor (the point directly below the source), and their length grows as objects get farther from it (**judgement**, standard geometry of point-source shadows).
- **Light describes the ground plane.** Long cast shadows across a field, a road or a floor lay out its perspective and give scale steps; sunlit patches on receding ground compress like the tiles above.
- **Aerial perspective colours light and shadow differently:** distant sunlit planes go toward the horizon-sky colour and lose saturation; distant shadow planes lighten and turn bluer; the value gap between sun and shadow shrinks with distance until a far mountain is one flat value (Koschmieder plus Wikipedia, Aerial perspective).
- **Against the light** (sun ahead), the air between viewer and subject glows and silhouettes stack in flat value layers that lighten with each step back (**judgement**, follows from added airlight being brightest toward the sun).

## 4. Variation
- **Weather:** clear air (dark distant hills still dark), haze (layers of blue-grey), fog (near forms only, everything beyond 100-200 m gone), rain (contrast lost even at mid distance) (visibility classes from Wikipedia, Visibility; examples **judgement**).
- **Time of day:** low sun stretches shadows into strong perspective lines; noon shortens them; dusk turns the airlight warm near the sun and blue away from it (Wikipedia, Aerial perspective, for warm near sunrise and sunset).
- **Scale of space:** a tabletop (personal space, only overlap and size), a room or street (action space, height on the floor plane is the main cue), a valley (vista space, aerial perspective joins in) (Cutting and Vishton).
- **Terrain:** on slopes the ground's vanishing line is no longer the horizon; a road going uphill vanishes above the horizon, downhill below it (inclined planes rule, OUP).
- **Curved and irregular space** (forest, crowds, rocks) has no ruled lines; there, depth comes from overlap, size gradients and value layering, with a horizon still governing where heads and the ground plane sit (**judgement**).

## 5. How painters observe and construct it
- **Fix the horizon and the viewer first.** Decide eye height and viewing distance, mark the horizon, the centre of vision and the 60° cone, then place VPs from the scene's orientation (handprint method; BYU cone).
- **Construct with the orthogonals.** Painters of the Dutch Golden Age often used a pin at the vanishing point and a chalked string snapped to the canvas for the orthogonals; pinholes at the vanishing point have been found in thirteen paintings by Vermeer, three visible to the naked eye ([Essential Vermeer, perspective](https://essentialvermeer.com/technique/perspective/vermeer-and-perspective.html)). Named here only as an example of practice.
- **Build depth with a ground grid.** Lay a floor or ground of squares in perspective (distance-point method or measuring points), then stand each object on it; heights are carried back from a measuring line or a known figure height ([handprint](https://www.handprint.com/HP/WCL/perspect2.html); OUP).
- **Use a figure as the scale stick.** Draw one figure at a known place, then key every other standing figure's eyes to the horizon and its feet to its spot on the ground (geometry from section 1).
- **Sight-size and sighting angles** when working from life: hold a pencil at arm's length to compare angles and sizes, and a plumb line for verticals (**judgement**: standard atelier practice; not separately sourced here).
- **Plan the planes, then the air.** Divide the picture into foreground, middle ground and distance, give each a value range, and narrow the range and lift the darks with each step back (Koschmieder; **judgement** for the three-plane device).
- **In the studio:** the 3D blockout (`scene.py`) gives exact perspective. Set camera height and `fov` on purpose (section 1 mapping), and set fog density from the weather.

## 6. Common mistakes
- **Several horizons.** Objects drawn from different eye levels (a table seen from above, a figure from level) read as a collage. Check: every horizontal edge's VP on one line.
- **VPs too close together.** Boxes bulge and corners exceed 90° in front ([handprint, two-point](https://www.handprint.com/HP/WCL/perspect3.html)). Check: the front corner of a box on the ground should open to more than 90° on the canvas.
- **Accidental three-point.** Verticals that lean a little and in different directions look careless; either all vertical or all converge on one VP.
- **Figures off the horizon.** Distant figures with heads far above or below the horizon on flat ground read as giants or dwarfs.
- **Floor rising like a wall.** Depth intervals not shrinking (equal tile rows) tilt the ground up; the 1/D² compression is missing.
- **Pointed or tilted ellipses.** Rims with pointed ends, minor axes not on the cylinder's axis, or the same ellipse degree at top and bottom of a cylinder below eye level ([NMA handout](https://s3.amazonaws.com/uploads.nma.art/uploads/2021/03/Ellipse-Guide_Drawing-Foudations-Handout.pdf)).
- **Edge distortion.** Spheres and figures near the canvas edge stretched by a too-wide angle; keep them inside the 60° cone.
- **Aerial perspective as "everything far is blue".** Hue shift without value convergence, or haze on near objects, or the same haze in clear and foggy weather. The rule is contrast loss first, colour shift second.
- **Tangents and ambiguous overlaps.** Edges that just touch kill occlusion, the strongest depth cue (Cutting and Vishton); make one form clearly pass in front.
- **Shadows in conflicting directions** under one sun.

## 7. Checks for Teodor
1. **One horizon.** Draw it on the schema; every horizontal edge set meets on it, and every standing figure's eyes on flat ground sit at the same height relative to it as the camera's eye height (e.g. on it, for a 1.6 m camera and adult figures).
2. **Cone and lens.** The blockout's `fov` is a choice: wide (≥ 50) only when the feeling needs crowding and swelling, long (≤ 20) for stacked flat layers; important forms inside the central 60°.
3. **Depth compression.** Equal ground intervals (tiles, rows, fence posts) shrink about with the square of distance; check two of them by measuring.
4. **Overlap at every depth step.** Each plane is in front of the next by a clear overlap, not a tangent.
5. **Aerial ladder.** Sample the darkest dark of foreground, middle ground and distance: the darks should lift and the contrast shrink step by step toward the horizon-sky value, by an amount that fits the stated weather (fog density chosen from visibility).
6. **Shadows agree.** All sun shadows on the ground point to one point on the horizon; penumbrae widen with distance from the casting edge.
7. **Ellipses.** Minor axis on the cylinder axis; rounder the farther from eye level; no points.

## 8. Sources
- handprint (Bruce MacEvoy), [Central (one-point) perspective](https://www.handprint.com/HP/WCL/perspect2.html) (similar triangles, horizon, circle of view, distance points, viewing distance)
- handprint, [Two-point perspective](https://www.handprint.com/HP/WCL/perspect3.html) (90° rule, VP placement by tangent, measure points, VP spacing, three-point note)
- Oxford University Press learning link, [Advanced Perspective Techniques](https://learninglink.oup.com/protected/files/content/file/1573546337378-Advanced-Perspective-Techniques.pdf) (measuring lines, three-point VP rule of thumb, inclined planes, distortion)
- BYU-Idaho Art 110, [Cone of vision](https://courses.byui.edu/art110_new/art110/week02/cone_of_vision.html) and [Ellipses](https://courses.byui.edu/art110_new/art110/week01/ellipses.html)
- New Masters Academy, [Ellipse guide handout](https://s3.amazonaws.com/uploads.nma.art/uploads/2021/03/Ellipse-Guide_Drawing-Foudations-Handout.pdf)
- [Perspective notes: shadows, reflections and atmosphere](https://bertverhees.github.io/perspect6.html) (light and shadow vanishing points, sun 0.5°, penumbra 1%) (secondary)
- Smarthistory, [Linear perspective: Brunelleschi's experiment](https://smarthistory.org/linear-perspective)
- National Gallery, London, [Samuel van Hoogstraten, A Peepshow with Views of the Interior of a Dutch House](https://www.nationalgallery.org.uk/paintings/samuel-van-hoogstraten-a-peepshow-with-views-of-the-interior-of-a-dutch-house)
- Essential Vermeer, [Vermeer and perspective](https://essentialvermeer.com/technique/perspective/vermeer-and-perspective.html) (pin-and-string, pinholes)
- Wikipedia, [Angle of view](https://en.wikipedia.org/wiki/Angle_of_view_(photography)), [Perspective distortion](https://en.wikipedia.org/wiki/Perspective_distortion), [Aerial perspective](https://en.wikipedia.org/wiki/Aerial_perspective), [Visibility](https://en.wikipedia.org/wiki/Visibility) (secondary)
- American Meteorological Society Glossary, [Airlight formula](https://glossary.ametsoc.org/wiki/Airlight_formula) (Koschmieder's law)
- Cutting, J. E. and Vishton, P. M. (1995), [Perceiving layout and knowing distances](https://scispace.com/pdf/perceiving-layout-and-knowing-distances-the-integration-1i3ri93gex.pdf), in *Perception of Space and Motion*
- Computed here from the sources' formulas: the `scene.py` fov-to-focal-length mapping, the fog densities for given visibilities, the 1/D² compression of ground intervals. Marked **judgement**: eye heights other than standing, seated sighting practice, lamp shadow geometry wording, the three-plane device, weather examples.
