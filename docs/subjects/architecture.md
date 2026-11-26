# Architecture: buildings, interiors, streets, doors and windows

Layer 1 for `architecture`: how buildings and rooms are built, how they sit in perspective, what their materials look like, and how light gets into them. The perspective machinery itself (horizon, vanishing points, cone of vision, inclined planes) is in `space.md`; material optics in general (glass, stone, wood) is in `objects.md`.

## 1. What it is, structurally

### Buildings obey gravity and the human body
- A building is a stack of horizontal floors carried down to the ground by walls or columns; openings are spanned by lintels or arches, so **openings stack above openings** and walls get thicker or heavier toward the base in masonry (**judgement**: general structural logic; not separately sourced here).
- Almost every dimension is keyed to the body, so architecture is the painter's best scale stick: a door tells the size of a figure, and the reverse.

### Key dimensions (metric)
| element | value | source |
|---|---|---|
| Interior door leaf, metric standard (common in mainland Europe) | 2040 mm high; 526-926 mm wide (826 mm typical) | [Howarth Timber, UK door sizes](https://www.howarth-timber.co.uk/help-advice/uk-door-sizes) |
| Interior door leaf, UK imperial | 1981 × 762 mm (most typical in England and Wales) | same |
| Front door opening | about 2.1 m × 0.97 m | same (converted) |
| Garage door | about 2.4 m wide × 2.1 m high | same |
| Minimum floor-to-ceiling height in a dwelling | 2.3 m (UK standard, over 75% of floor area) | [UK nationally described space standard](https://www.gov.uk/government/publications/technical-housing-standards-nationally-described-space-standard/technical-housing-standards-nationally-described-space-standard) |
| Typical residential ceiling | 2.4-2.7 m; floor-to-floor about 2.8-3.2 m | **judgement** (typical modern practice) |
| Older town houses, public buildings | ceilings 3-4.5 m; floor-to-floor 3.5-5 m | **judgement** |
| Single bedroom width (minimum) | 2.15 m; double 2.55-2.75 m | UK space standard |
| Stairs | 2 risers + 1 tread = 63-65 cm (Blondel); comfortable 18 cm riser, 28 cm tread; steep 21/21; outdoor 13/39 | [ArchDaily, staircase calculations](https://www.archdaily.com/892647/how-to-make-calculations-for-staircase-designs) |
| Stair headroom | at least 2.0-2.15 m | same (Neufert 2.0 m) |
| Window sill | about 0.8-0.9 m above floor; window heads usually line up with door heads at about 2.0-2.1 m | **judgement** |
| Table, chair seat, counter | about 0.75 m, 0.45 m, 0.9 m | **judgement** |
| Brick, UK | 215 × 102.5 × 65 mm, 10 mm joints: a 75 mm course, about 13 courses per metre | [Wikipedia, Brick](https://en.wikipedia.org/wiki/Brick) |
| Brick, Denmark | 228 × 108 × 54 mm (about 66 mm courses with a 12 mm joint, **judgement** for the joint); Germany 240 × 115 × 71; US modular 194 × 92 × 57 | same |
| Brick proportion | length ≈ 2 widths + 1 joint, so bricks bond across corners | same |

- **Courses as a ruler:** a wall's courses are a ready-made height scale. A UK door is about 27 courses high; a Danish one about 31 (computed from the table).

### Classical orders (for columns and porticoes)
- Column height in lower diameters: Tuscan about 7, Doric 7-8, Ionic 8-9, Corinthian 9-10, Composite about 10; real buildings vary a lot. Vignola's module is half a diameter ([Wikipedia, Classical order](https://en.wikipedia.org/wiki/Classical_order)).
- **Entasis:** the shaft swells slightly and thins toward the top, from about a third of the way up (same source). A column drawn as a straight tube reads as a pipe.
- The entablature has three bands (architrave, frieze, cornice); the Doric frieze alternates triglyphs and metopes (same source).

### Parts that carry the look
- **Wall thickness** shows at every opening as a reveal: an old masonry wall is 0.4-0.8 m thick, a modern insulated wall about 0.3-0.5 m, a timber frame wall 0.15-0.25 m (**judgement**). The reveal catches light on one side and shadow on the other and is what makes a window sit *in* a wall.
- **Roofs:** pitch, overhang (eaves) and the shadow under the eaves define a house's silhouette. Steep pitches (35-50°) where snow and rain are heavy, low pitches (15-25°) in dry warm climates (**judgement**). Draw pitched roofs with auxiliary vanishing points (`space.md`).
- **Repetition with variation:** windows in a façade repeat on a grid (bays and storeys); a street repeats house widths of roughly 5-10 m in old towns (**judgement**). The grid is what perspective acts on, so it should be constructed, not improvised.

## 2. Seen from different viewpoints
- **Street, one-point:** looking down a straight street, the façades on both sides are orthogonals to a single VP at eye level; cornice lines slope down to it, pavements slope up to it. Windows and doors foreshorten into narrow slivers near the VP ([handprint, central perspective](https://www.handprint.com/HP/WCL/perspect2.html)).
- **Corner, two-point:** a building seen on its corner. Keep VPs far apart (at 45°/45° they are two viewing distances apart) or the corner bulges toward the viewer ([handprint, two-point](https://www.handprint.com/HP/WCL/perspect3.html)). With a level gaze, verticals stay vertical; distortion of vertical proportions is minor for ground-level architecture (same source).
- **Tall building from the street, three-point:** tilt the view up and the verticals converge to a VP high above; put that VP at least as far from the horizon as the two horizontal VPs are apart ([OUP, Advanced Perspective Techniques](https://learninglink.oup.com/protected/files/content/file/1573546337378-Advanced-Perspective-Techniques.pdf)). Window rows still converge on the horizon's VPs; floors get visibly shorter upward.
- **Bird's-eye:** roofs dominate, streets become canyons, verticals converge downward.
- **Interior:** a room is a box seen from inside. From a standing eye at 1.6 m in a 2.5 m room, the horizon sits about two-thirds of the way up the walls, so you see much floor and a strip of ceiling; tables and seats are seen from above, door handles (about 1 m) below eye level (geometry; heights **judgement**).
- **Rooms are wider than the cone of vision.** Showing two side walls of a 4 m room from inside it needs more than 60°; edge distortion follows. Painters back the viewpoint off (as if through the wall) or show one wall and a corner (**judgement**; cone of vision from [BYU-Idaho](https://courses.byui.edu/art110_new/art110/week02/cone_of_vision.html)).
- **Doors and windows in perspective:** an open door's leaf swings on a vertical hinge; its top and bottom edges vanish to a VP on the horizon that moves along it as the door opens. Window panes and shutters follow the same rule (two-point rule applied to a rotated plane, handprint).
- **Distance:** near, every brick, joint and frame profile shows; at mid distance, courses become a texture gradient and windows become dark rectangles with a light sill and a shadowed head; far, a building is a few planes of value and a silhouette (**judgement**, consistent with relative-size and texture cues in `space.md`).

## 3. Under light

### Exterior
- **Each plane has one value per light.** A box building in sun has a sunlit face, a skylit shadow face and a roof lit by sun and sky; keep each face near one value and modulate within it only a little (**judgement**, standard plane logic; see `light-shadow.md`).
- **Shadow faces are lit by sky and by bounce from the ground:** bluer than the sunlit face under a clear sky, warmer near the bottom where sunlit pavement bounces into them (**judgement**, consistent with skylight being blue; [Wikipedia, Aerial perspective](https://en.wikipedia.org/wiki/Aerial_perspective)).
- **Cast shadows describe relief:** eaves, cornices, sills, balconies and reveals throw shadows whose length shows how far each one projects. Sun shadows converge to one point on the horizon (see `space.md`; [perspective notes](https://bertverhees.github.io/perspect6.html)).
- **Windows from outside in daylight read dark,** because the interior is much dimmer than the outdoors (daylight factor below), except where the glass reflects bright sky. Reflection rises sharply toward grazing angles (Fresnel; see `objects.md`), so windows seen obliquely, and upper windows that catch sky, are lighter and more mirror-like than windows seen straight on (physics from [Wikipedia, Fresnel equations](https://en.wikipedia.org/wiki/Fresnel_equations); application **judgement**).
- **At dusk and night** the relationship flips: lit windows are the brightest, warmest shapes and throw light patches onto pavement and sills.
- **Streets as canyons:** the lower floors and pavement of a narrow street see less sky and are darker; upper floors and cornices catch more light (**judgement**).

### How light enters a room
- **Sunlight through a window** arrives as parallel rays and projects the window's shape onto floor and walls as a skewed copy (a parallelogram on the floor for a rectangular window), with glazing bars as dark bars inside it. Its edges are sharp near the sill and soften with distance, the penumbra being about 1% of the distance from the window edge to the patch, since the sun spans about 0.5° ([perspective notes](https://bertverhees.github.io/perspect6.html)). All sun patches in one room are cast in one direction.
- **Daylight falls off with depth.** Usable daylight reaches about 1.5-2 times the window head height into a room (up to about 2.5 times without blinds) ([MIT 4.401 daylighting lecture](https://www.ocw.mit.edu/courses/4-401-environmental-technologies-in-buildings-fall-2018/be2f4e041e1683f5615ec47f6208d8d9_MIT4_401F18_lec8.pdf)). Beyond that zone the room goes dim quickly.
- **The range is enormous.** Direct sun gives 32,000-100,000 lux and open daylight 10,000-25,000 lux, against 320-500 lux for office lighting and about 50 lux for a living room lamp ([Wikipedia, Lux](https://en.wikipedia.org/wiki/Lux)). The daylight factor (indoor/outdoor light) is under 2% in an inadequately lit spot and over 5% in a well-lit one ([Wikipedia, Daylight factor](https://en.wikipedia.org/wiki/Daylight_factor)). So the view through a window is often 20 to 100 times brighter than the back wall; paint cannot hold that range, and the painter has to choose what to keep (**judgement** for the conclusion).
- **Reflectance shapes the room's light.** The ceiling's reflectance and the ground outside are among the most important surfaces for how deep daylight reaches; high reflectances make a room look larger, and a window next to a bright wall or ceiling makes the room look wider or higher (MIT lecture).
- **The window wall is the darkest wall** seen from inside: it gets no direct light from its own window, so it reads as a dark frame around a bright opening, while the side walls grade from bright near the window to dim away from it (**judgement**, follows from the falloff above).
- **Bounce:** a sun patch on the floor is a secondary light source: it lights the ceiling and the undersides of nearby objects and tints them with the floor's colour (**judgement**, consistent with the internally reflected component of the daylight factor).
- **Colour:** skylight from a north window is cool and even; direct sun is warm; lamplight is warmer still. A room lit by both shows warm patches and cool fill (**judgement**; see `light-shadow.md`).
- **Window reveals** are bright on the side facing the light and graded on the others; deep reveals and splays spread light into the room (**judgement**).

## 4. Variation
- **Type and region:** timber, brick, stone, render or concrete; pitched or flat roofs; small deep windows in thick old walls or large shallow glazing in modern frames. Read the brief and pick a type before drawing; don't mix systems by accident (**judgement**).
- **Age and weathering:** streaks of dirt run down from sills and cornices, ledges darken, mortar recedes, timber greys, roofs sag a little along the ridge, damp and moss sit at the foot of walls and on north faces, paint flakes at edges first (**judgement**, common observation).
- **Weather:** wet pavements and walls darken and gain reflections of lit windows and sky; snow outlines every horizontal ledge and roof; fog removes the far end of a street in value steps (see `space.md`).
- **Time of day:** low sun rakes façades and shows texture (every brick course casts a tiny shadow); noon flattens walls and deepens shadows under eaves; overcast light shows the building's own colours and joints evenly (**judgement**).
- **Interiors:** a lived-in room has slightly irregular placement, worn floor paths, things on surfaces; a constructed room has exactly parallel furniture (**judgement**).

## 5. How painters observe and construct it
- **Plan, elevation, perspective.** Work out the building's footprint and front elevation in plain dimensions first (door 2.04-2.1 m, storeys about 3 m), then project them; that keeps windows aligned and storeys consistent (**judgement**; method of the perspective manuals above).
- **Box first, openings second.** Mass the building or room as one or a few boxes on the ground plane with a fixed horizon, then cut doors and windows on the façade grid, then add thickness (reveals, sills, eaves), then texture.
- **Construct repeats.** Divide façades and floors with diagonals or a measuring line instead of guessing ([OUP](https://learninglink.oup.com/protected/files/content/file/1573546337378-Advanced-Perspective-Techniques.pdf)); floor tiles, beams and window bays are grids that make depth measurable.
- **Pin and string.** Dutch painters of interiors set a pin at the vanishing point and snapped a chalked string for the orthogonals; pinholes have been found at the vanishing point of thirteen interiors by Vermeer ([Essential Vermeer](https://essentialvermeer.com/technique/perspective/vermeer-and-perspective.html)). Hoogstraten's perspective box shows the same culture of exact interior construction ([National Gallery](https://www.nationalgallery.org.uk/paintings/samuel-van-hoogstraten-a-peepshow-with-views-of-the-interior-of-a-dutch-house)). Named here only as examples of practice.
- **Brunelleschi's test** (comparing a perspective painting with a building through a hole and a mirror) is the original architecture check ([Smarthistory](https://smarthistory.org/linear-perspective)).
- **Simplify by distance.** Near: profiles, joints and frames. Middle: windows as dark shapes with a lit sill and a shadow under the head; courses as a soft texture. Far: planes and silhouettes (**judgement**).
- **In the studio:** `scene.py` has a `house` object (walls, door default 2.1 × 1.0 m, windows, gable roof) and boxes for rooms. Build the room or street in the blockout with real metres so the perspective, sun patches and shadows come out right, then paint over it.

## 6. Common mistakes
- **Wrong scale against figures:** doors at shoulder height or twice a figure's height. A 2.04-2.1 m door is about 1.2 times a standing adult.
- **Windows floating on the façade:** no reveal, no sill shadow, no alignment of heads and sills across a storey.
- **Storeys that change height** up a façade, or window rows that do not converge on the same VP as the cornice.
- **Accidental leaning verticals** or verticals converging in a level view; or converging verticals without any upward tilt elsewhere in the picture.
- **Corners bulging** from VPs too close together.
- **Flat-lit rooms:** the same brightness at the back of the room as by the window; sun patches with the wrong shape or with no relation to the window; the window wall painted as light as the others.
- **Daylight windows painted light blue from outside** when seen straight on; dark-interior windows are usually darker than the wall.
- **Uniform texture:** every brick drawn at every distance (looks like wallpaper) instead of a texture gradient.
- **Columns as tubes:** no entasis, no capital and base proportion, wrong height-to-diameter ratio.
- **Pristine surfaces** in a scene that should be old or weathered, and the reverse.

## 7. Checks for Teodor
1. **Scale stick:** door height ÷ standing figure height ≈ 1.15-1.2; storey ≈ 1.6-1.8 figures; steps ≈ 0.1 figure each.
2. **Grid alignment:** window heads and sills align across each storey and stack between storeys; they meet the same VPs as the cornice and the ground line.
3. **Verticals:** all vertical, or all converging on one third VP set far enough away.
4. **Thickness:** every opening shows a reveal with a lit side and a shaded side, and a sill with a cast shadow.
5. **Room light:** brightness falls off with distance from the window (daylit zone ≈ 1.5-2 × window head height); the window wall frames the opening in dark; sun patches share one direction and have the window's skewed shape.
6. **Windows from outside:** darker than the wall in daylight unless they reflect sky at a grazing angle; lit and warm at night.
7. **Texture gradient:** individual bricks or stones only in the foreground; courses as tone in the middle ground.

## 8. Sources
- Howarth Timber, [UK door sizes](https://www.howarth-timber.co.uk/help-advice/uk-door-sizes) (metric and imperial door leaves, front and garage door openings)
- UK Government, [Technical housing standards: nationally described space standard](https://www.gov.uk/government/publications/technical-housing-standards-nationally-described-space-standard/technical-housing-standards-nationally-described-space-standard)
- ArchDaily, [How to calculate staircase dimensions](https://www.archdaily.com/892647/how-to-make-calculations-for-staircase-designs) (Blondel, headroom, citing Neufert)
- Wikipedia, [Brick](https://en.wikipedia.org/wiki/Brick), [Classical order](https://en.wikipedia.org/wiki/Classical_order), [Lux](https://en.wikipedia.org/wiki/Lux), [Daylight factor](https://en.wikipedia.org/wiki/Daylight_factor), [Fresnel equations](https://en.wikipedia.org/wiki/Fresnel_equations), [Aerial perspective](https://en.wikipedia.org/wiki/Aerial_perspective) (secondary)
- MIT OpenCourseWare 4.401, [Daylighting lecture](https://www.ocw.mit.edu/courses/4-401-environmental-technologies-in-buildings-fall-2018/be2f4e041e1683f5615ec47f6208d8d9_MIT4_401F18_lec8.pdf) (daylit depth 1.5-2.5 × window head height, citing Reinhart 2005; reflectances)
- handprint, [Central perspective](https://www.handprint.com/HP/WCL/perspect2.html) and [Two-point perspective](https://www.handprint.com/HP/WCL/perspect3.html)
- Oxford University Press, [Advanced Perspective Techniques](https://learninglink.oup.com/protected/files/content/file/1573546337378-Advanced-Perspective-Techniques.pdf)
- BYU-Idaho, [Cone of vision](https://courses.byui.edu/art110_new/art110/week02/cone_of_vision.html)
- [Perspective notes: shadows, reflections and atmosphere](https://bertverhees.github.io/perspect6.html) (secondary)
- Essential Vermeer, [Vermeer and perspective](https://essentialvermeer.com/technique/perspective/vermeer-and-perspective.html); National Gallery, London, [Hoogstraten's peepshow](https://www.nationalgallery.org.uk/paintings/samuel-van-hoogstraten-a-peepshow-with-views-of-the-interior-of-a-dutch-house); Smarthistory, [Linear perspective](https://smarthistory.org/linear-perspective)
- Not reached: designingbuildings.co.uk door-size page (fetch blocked); Neufert, *Architects' Data* (cited only through ArchDaily). Marked **judgement**: typical ceiling and storey heights, sills, furniture heights, wall thicknesses, roof pitches, street widths, weathering, and the qualitative rules on window walls, bounce, canyons and windows seen from outside.
