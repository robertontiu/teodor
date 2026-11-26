# Objects: still-life objects and their materials

Layer 1 for `objects`: how still-life objects are built and, above all, how each material reflects, transmits and scatters light so that the painter can make it read as glass, metal, ceramic, wood, stone, fabric, paper or food. Perspective of the table and the ellipses of rims are in `space.md`; light on form in general (form shadow, cast shadow, halftones) is in `light-shadow.md`; flowers and fruit as arranged subjects are in `flowers.md`; cloth folds are in `drapery.md`.

## 1. What it is, structurally

### Objects: simple solids with a resting surface
- Most still-life objects are turned or built from simple solids: cylinders (glasses, jugs, bottles), spheres (fruit), cones, boxes (books), and their combinations. Draw the solid and its axis first; rims and bases are ellipses whose minor axis lies on the object's axis and which open as they move away from eye level ([NMA ellipse handout](https://s3.amazonaws.com/uploads.nma.art/uploads/2021/03/Ellipse-Guide_Drawing-Foudations-Handout.pdf)).
- Objects **rest**: each has a contact line or point with the table, a contact shadow there (the darkest dark of the cast shadow) and a cast shadow on the table (**judgement**, standard observation; see `light-shadow.md`).
- Sizes for scale (**judgement**): wine glass 15-22 cm high, tumbler 9-12 cm, wine bottle 30 cm × 7.5 cm diameter, dinner plate 26-28 cm, cup 8-9 cm high, apple 7-8 cm, lemon 7-9 cm long, grape 1.5-2.5 cm, A4 sheet 21 × 29.7 cm, hardback book about 16 × 24 cm, a hand span about 20 cm.

### Materials: where light goes when it meets a surface
At a surface, light splits into a **specular** part, reflected mirror-like at the surface, and a part that enters. Entering light is absorbed, scattered back out (**diffuse**), passed through (**transmission**), or scattered sideways under the surface before it leaves (**subsurface scattering**). Energy is conserved: whatever is reflected specularly is not available for diffuse ([LearnOpenGL, PBR theory](https://learnopengl.com/PBR/Theory)).

- **Fresnel:** every surface reflects more as the view grows more oblique, approaching total reflection at grazing angles ([LearnOpenGL](https://learnopengl.com/PBR/Theory); [Wikipedia, Fresnel equations](https://en.wikipedia.org/wiki/Fresnel_equations)). Head-on reflectance for a non-metal is R0 = ((n-1)/(n+1))²: about 4% for glass (n ≈ 1.5), 8% for both faces of a pane; Brewster's angle about 56°; total internal reflection inside glass beyond about 42° (Wikipedia, Fresnel equations).
- **Head-on (F0) specular reflectance** ([LearnOpenGL](https://learnopengl.com/PBR/Theory)):

| material | F0 (R, G, B) | reads as |
|---|---|---|
| water | 0.02 | faint, colourless reflections head-on, mirror at grazing |
| glass, plastic | 0.03-0.05 | same, a little stronger |
| high-index glass, ruby | 0.08 | |
| diamond | 0.17 | the brightest non-metal |
| iron | 0.56, 0.57, 0.58 | dark grey mirror |
| aluminium | 0.91, 0.92, 0.92 | bright neutral mirror |
| silver | 0.95, 0.93, 0.88 | bright, faintly warm mirror |
| copper | 0.95, 0.64, 0.54 | reflections tinted orange-pink |
| gold | 1.00, 0.71, 0.29 | reflections tinted yellow |

- **Non-metals (dielectrics)** have a colourless (white) highlight on top of a coloured diffuse body; **metals** have no diffuse colour at all: everything you see is reflection, tinted by the metal for gold and copper (LearnOpenGL).
- **Roughness:** a surface is modelled as tiny mirror facets; the rougher it is, the wider and dimmer the highlight; the smoother, the smaller, sharper and brighter (LearnOpenGL).
- **Diffuse reflectance (albedo)** for value planning: fresh asphalt 0.04, bare soil 0.17, green grass 0.25, desert sand 0.40, new concrete 0.55, fresh snow 0.80 ([Wikipedia, Albedo](https://en.wikipedia.org/wiki/Albedo)). White paper and plaster sit near snow (about 0.7-0.85), black velvet and charcoal near 0.02-0.05 (**judgement**).
- **Transmission and absorption:** in a coloured transparent material, transmitted light falls exponentially with path length (Beer-Lambert) ([Wikipedia](https://en.wikipedia.org/wiki/Beer%E2%80%93Lambert_law)): thick parts of coloured glass, wine or tea are darker and more saturated than thin parts.
- **Subsurface scattering:** in milk, marble, skin, wax and leaves, light enters, scatters and leaves at another point. It bleeds colour inside the material and softens the boundary of the form shadow; without it these materials look like plastic or metal ([Jensen et al. 2001](https://www.cs.cornell.edu/~srm/publications/SG01-subsurf-abstract.html); [Wikipedia, Subsurface scattering](https://en.wikipedia.org/wiki/Subsurface_scattering)). In skin, red scatters furthest, then green, blue least (Wikipedia), which is why shadow edges on such materials go warm.
- **Caustics:** curved glass or water focuses light into bright curves and patches on the table, often inside or beside the object's shadow; a glass in parallel light makes a nephroid-shaped bright patch ([Wikipedia, Caustic](https://en.wikipedia.org/wiki/Caustic_(optics))).

### How viewers read materials (perception research)
- **Highlights must agree with the form.** Highlights that follow the shading and are elongated along the direction of least curvature read as gloss; moved or rotated, the same highlights read as stray light or spots of white paint (Beck and Prazdny, reported in [Todd, Norman and Mingolla 2004](https://www.asc.ohio-state.edu/todd.44/date/Todd,%20Norman%20&%20Mingolla%202004.pdf)).
- **Contrast and sharpness carry gloss.** In seventeenth-century painted grapes, highlight contrast and blurriness explained 69% of perceived gloss; highlight coverage had no effect ([Di Cicco, Wijntjes and Pont 2019](https://repository.tudelft.nl/record/uuid:550c3a32-0e7e-4b0c-a9ed-367a98335cc5)). Sharper and higher-contrast highlights, and distinct reflections of the surroundings, signal higher gloss ([Hansmann-Roth, Pont and Mamassian 2017](https://pure.tudelft.nl/ws/portalfiles/portal/12907234/i1534_7362_17_2_17.pdf)).
- **Dark surfaces look glossier** than light ones with the same coating, and a light glossy area next to a dark one looks less glossy (Hansmann-Roth et al. 2017). A positively skewed value histogram (mostly dark with a few bright peaks) looks darker and glossier ([Motoyoshi et al. 2007, Nature](https://www.nature.com/articles/nature05724)).
- **Fabrics:** in painted cloth, perceived shininess rises with mean luminance and highlight coverage; satin reads shiny through many bright highlights; velvet reads soft, warm and heavy ([Di Cicco et al. 2021](https://repository.tudelft.nl/record/uuid:ed8025d9-0fdf-4ec1-815c-fef09dee61b8)).
- **Thick transparent objects** are judged by how they distort what is behind them ([Fleming, Jäkel and Maloney 2011](https://www.psychologicalscience.org/journals/psychological-science/0956797611408734/)); small specular reflections (a few percent, like real glass at about 4%) make them read thick and solid, while stronger distortion alone makes them look thinner ([Ohara, Kim and Koida 2022](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.766056/pdf)).

### Material by material
- **Glass (clear).** It has almost no colour of its own: it is the background, refracted (shifted, flipped or compressed inside curved walls), plus faint reflections of windows and lights, plus bright mirror-like rims where the walls are seen at grazing angles (Fresnel). Edges usually read as a pair of lines: a dark line where the wall refracts something dark or hides the background, and a light line of reflection beside it (**judgement**, follows from Fresnel and refraction). Liquid inside a glass has its own surface ellipse and a meniscus; the part of the background seen through liquid shifts again. Thick bases and stems are dark and full of compressed reflections. Coloured glass darkens and saturates where it is thick (Beer-Lambert). A green glass in a Dutch still life (Heda) carries more than nine separate window images, upright and inverted, from its curved inner and outer faces ([Atmospheric Optics, Heda](https://atoptics.co.uk/fza35.htm)).
- **Metal (polished).** A distorted mirror of the room: the dark of the room lies in it as dark shapes, windows and the light source as sharp bright shapes, and neighbouring objects as coloured, curved reflections. No diffuse "local colour" (LearnOpenGL): a silver jug's "colour" is the room's values, slightly warm; a brass or gold one tints every reflection yellow; copper tints them pink-orange. Value range is the widest of any material: near black to the brightest highlight in the picture (**judgement**, follows from F0 0.9 plus no diffuse). Reflections follow the curvature: stretched along a cylinder's length, compressed around its sides. **Brushed or worn metal** blurs the reflections and stretches highlights across the brushing direction; **tarnished** metal loses contrast and gains a dull diffuse layer (**judgement**).
- **Ceramic.** Glazed: a coloured diffuse body under a clear glass-like coat, so a white, sharp highlight and reflected window shapes sit on top of colour that keeps its own form shading; Fresnel makes the rims and the side turned away from the viewer slightly more reflective. Porcelain is faintly translucent at thin rims when backlit. Unglazed earthenware and terracotta are matte: soft, wide halftones, no highlight, a slightly lighter edge of grazing scatter (**judgement**, two-layer dielectric logic from LearnOpenGL).
- **Wood.** Grain is a directional texture following the growth of the tree and the cut (straight on planks, curved figure on turned bowls). Finished wood shows a subsurface highlight from the fibres under the finish that lies on a cone around the fibre direction and shifts as the view changes, the reason figured woods shimmer, on top of the finish's own white surface highlight ([Marschner et al. 2005](https://www.cs.cornell.edu/~srm/publications/SG05-wood.html)). Raw wood is matte; oiled and varnished wood deepens and warms in colour and gains a sharp highlight (**judgement** for the latter).
- **Stone.** Marble: translucent, with soft form shadows and colour bleeding near the shadow edge (Jensen et al. 2001); polished marble adds sharp reflections. Granite and sandstone: opaque, matte, speckled or grainy; the texture shows best in raking light (**judgement**).
- **Fabric.** See `drapery.md` for folds. Optical types: matte (linen, cotton, wool: wide soft halftones, little highlight; wool has a fuzzy edge); **satin and silk** (sharp, high-coverage, bright highlights running along the folds, value range like metal) (Di Cicco et al. 2021); **velvet** (bright edges at the silhouette and at the edge of the form shadow, from light scattered by the pile at grazing angles, and darker, richer colour where the surface faces you: the reverse of a matte cloth) ([Koenderink and Pont 2003](https://unpaywall.org/10.1007%2Fs00138-002-0089-7)). The same grazing scatter makes peaches and soft skin look velvety (same source).
- **Paper.** Diffuse and very light (near 0.8, **judgement**), thin, so it is translucent against light: backlit, a sheet glows warm and shows what is printed on the other side. Its edges are lines of thickness; it curls, folds and casts sharp thin shadows; stacked pages show as a striped edge (**judgement**).
- **Food.** Grapes need three cues in balance: gloss (sharp highlights), translucency (light along the edges, glow) and bloom (a whitish waxy film). The 1692 manual by Willem Beurs builds them in layers: body colour in light and shadow, internal edge reflections, a thin uneven scumble of bloom once dry, a soft white highlight only where there is no bloom, glazes in the shadows and reflections, seeds last; in tests of a reconstruction, highlights correlated with perceived gloss at r = 0.94 and the bloom layer with perceived bloom at r = 0.92 ([Di Cicco et al. 2020](https://repository.tudelft.nl/record/uuid:4854c5e2-cc70-44fc-a6c4-deb24ba50d15)). Other fruit: waxy skins (apples, plums) have broad soft highlights; citrus has a dimpled, pitted highlight; cut fruit shows wet, translucent flesh (**judgement**). Milk and cheese scatter light under the surface (Jensen et al. 2001); bread crust is matte and rough, the crumb porous; meat and fish are glossy and translucent at their edges (**judgement**).

## 2. Seen from different viewpoints
- **Highlights move with the viewer; shading does not.** Diffuse shading depends only on the light; a specular highlight sits where the surface's mirror angle joins light and eye, so moving the eye moves it (physics of specular reflection; **judgement** for wording). Paint each highlight for the one viewpoint of the picture.
- **Eye level and ellipses:** a still life seen from a standing eye looks down into cups and bowls (open ellipses); from table height the rims flatten into lines and the objects overlap more (`space.md`).
- **Grazing views** make every material more reflective (Fresnel): a table top seen at a low angle reflects the objects standing on it, and a matte cloth shows a sheen toward the far edge.
- **Through glass:** what is behind a glass is shifted, compressed or flipped depending on the glass's curvature and on how far the background is (Fleming et al. 2011); moving the viewpoint changes it entirely, so construct it for one viewpoint.
- **Distance:** at arm's length texture and micro-highlights (pits in a lemon, grain in wood) carry the material; from a few metres, the material is carried by its value range and the sharpness of its highlights alone (**judgement**, consistent with the contrast and blur findings above).

## 3. Under light
- **One window or one lamp, from the side and a little above**, is the classic still-life light: it gives each object a light side, a form shadow, a reflected light from the table, a contact shadow and a cast shadow, and it puts one readable reflection of the light source in every glossy surface (**judgement**, studio convention).
- **The highlight is an image of the light source.** A window appears in a sphere as a small curved rectangle with its glazing bars, a lamp as a point; on a cylinder it is stretched along the axis (Todd et al. 2004 on elongation along minimum curvature). Its size grows with roughness and with the light's size.
- **Value structure per material** (**judgement**, follows from sections 1 and the perception research):
  - matte (paper, unglazed clay, cotton): full form shading, small value range in the light, no highlight;
  - glossy dielectric (glaze, varnish, fruit skin, satin): form shading plus a small, sharp, near-white highlight and faint reflections;
  - metal: no form shading as such, only reflections; darkest darks and brightest lights together;
  - glass: the background's values, edge lines, a few sharp highlights, caustics in the shadow;
  - translucent (marble, wax, milk, grapes, paper against light, leaves): soft and coloured shadow edges, glow on the side away from the light when backlit, low contrast inside the form.
- **Reflected colour:** glossy and metallic objects pick up the colours of their neighbours as reflections; matte objects pick them up only as a faint coloured bounce in the shadow side (**judgement**).
- **Backlight** reveals translucency (fruit, paper, wine, porcelain rims glow), and rim highlights from the Fresnel rise outline glossy objects (**judgement**).
- **Caustics** from glass and water sit in or near the cast shadow, on the side away from the light, often warmer or coloured by the liquid ([Wikipedia, Caustic](https://en.wikipedia.org/wiki/Caustic_(optics)); placement **judgement**).

## 4. Variation
- **Wear and age:** metal tarnishes and loses contrast; glazes craze; wood darkens and dents, and its finish wears to matte where hands touch it; paper yellows and softens at the edges; fruit wrinkles, browns and loses gloss; bread dries and cracks (**judgement**).
- **Wet and dry:** a wet surface darkens (less diffuse scatter) and becomes glossy; dust makes any surface matte and lighter (**judgement**).
- **Fill level:** a glass of water, wine or milk changes completely: the liquid's surface ellipse, its colour by thickness, its meniscus, and its own reflections.
- **Lighting conditions:** the same silver jug under an overcast window is soft and grey with long pale reflections; in sun it has tiny, blinding highlights and black reflections (**judgement**, follows from highlight = image of the source).
- **Light source colour** tints every highlight; on dielectrics the highlight takes the light's colour, not the object's (LearnOpenGL: only metals tint their reflection).

## 5. How painters observe and construct it
- **Construct, then describe material.** Draw each object as a solid on its axis on the table plane, with ellipses keyed to eye level, before any material effect (`space.md`).
- **Paint in the order light reaches the eye.** Beurs's recipe for grapes is the clearest documented order: body colour and three-dimensional shading, then internal reflections, then the bloom scumble, then the highlight, then glazes ([Di Cicco et al. 2020](https://repository.tudelft.nl/record/uuid:4854c5e2-cc70-44fc-a6c4-deb24ba50d15)). In general: local colour and form shadow first, reflections and translucent glow next, highlights last and sparingly (**judgement**, generalising the recipe).
- **Glass and metal are painted as what they show, not as what they are.** Paint the background through and around the glass, then the edge lines and reflections; paint metal as a mosaic of distorted reflected shapes (**judgement**, follows from F0 values and the distortion research).
- **Squint for the material's value range:** matte objects have a compressed range in the light, metal the full range; gloss reads through few sharp, high-contrast highlights, not many (Di Cicco et al. 2019; Hansmann-Roth et al. 2017).
- **Lose the highlight on purpose:** a highlight placed where the form does not call for it reads as a white spot (Todd et al. 2004). Check every highlight against the light direction and the surface normal.
- **Examples of observation** (not rules): the breakfast and banquet still lifes of Pieter Claesz and Willem Claesz Heda, with glasses and pewter on wooden tables in a near-monochrome palette, and the display (pronk) still lifes of Willem Kalf and Abraham van Beyeren, with porcelain, Venetian glass and silver-gilt in glistening light ([Met, Still-Life Painting in Northern Europe](https://www.metmuseum.org/essays/still-life-painting-in-northern-europe-1600-1800)).
- **In the studio:** the blockout's `gloss` adds a white Blinn-Phong highlight (exponent 40) without Fresnel, transmission or subsurface scattering, so it shows form and cast shadows correctly but glass reads as solid, metal as glossy plastic, and marble or fruit as hard. Paint those material effects from this page over the blockout; for glass, render the background without the glass and paint the glass over it.

## 6. Common mistakes
- **Same highlight everywhere:** one white dot of one size on every object, regardless of material and roughness; materials stop reading.
- **Misaligned highlights:** spots of white that do not agree with the light direction and the form; they read as paint on the surface (Todd et al. 2004).
- **Coloured highlights on non-metals** (a red highlight on a red apple) or white highlights on gold.
- **Metal with a local colour:** a silver jug painted grey with a light side and a dark side, like a matte object; it should be reflections.
- **Glass outlined and filled:** a glass drawn as a contour with a pale tint inside; no refraction, no edge pairs, no reflections, no caustics.
- **Too many highlights on glass,** or a uniform glassy sheen: real glass reflects only a few percent head-on and becomes mirror-like at the rims.
- **Translucent things painted opaque:** marble, wax, grapes, milk with hard grey shadows and no glow.
- **Velvet painted like satin** (highlights in the middle of the forms) instead of bright edges and dark fronts.
- **Uniform texture:** grain, weave or pitting painted at the same strength on the lit side, the shadow side and the edges; texture shows most in the halftone and raking light and vanishes in deep shadow and the highlight (**judgement**).
- **Floating objects:** no contact shadow, cast shadows inconsistent with the light, ellipses from a different eye level than the table.

## 7. Checks for Teodor
1. **One light, one highlight logic:** every highlight sits where its surface faces halfway between the light and the eye, and has the light's shape (window or point) and colour.
2. **Material ladder:** sharp, high-contrast highlights only on glossy things; matte things none; metal shows the darkest darks and brightest lights of its area.
3. **Glass:** background visible and shifted through it, a dark and a light edge line, two to five reflections at most, a caustic or a light patch in or near its cast shadow, its contact with the table drawn.
4. **Metals:** no local colour shading; reflections of the neighbouring objects and the window, tinted for gold, brass and copper only.
5. **Translucency:** marble, wax, fruit, milk and paper against light have warm, soft shadow edges and some glow; grapes show gloss, edge light and bloom together.
6. **Fabric type:** satin with many bright highlights along the folds; velvet with bright edges and dark fronts; linen and wool matte.
7. **Grounding:** each object has a contact shadow and a cast shadow pointing away from the one light, and ellipses consistent with one eye level.

## 8. Sources
- LearnOpenGL, [PBR theory](https://learnopengl.com/PBR/Theory) (F0 table, metals versus dielectrics, Fresnel at grazing angles, energy conservation, microfacet roughness) (secondary)
- Wikipedia, [Fresnel equations](https://en.wikipedia.org/wiki/Fresnel_equations), [Beer-Lambert law](https://en.wikipedia.org/wiki/Beer%E2%80%93Lambert_law), [Subsurface scattering](https://en.wikipedia.org/wiki/Subsurface_scattering), [Caustic (optics)](https://en.wikipedia.org/wiki/Caustic_(optics)), [Albedo](https://en.wikipedia.org/wiki/Albedo) (secondary)
- Jensen, Marschner, Levoy and Hanrahan (2001), [A practical model for subsurface light transport](https://www.cs.cornell.edu/~srm/publications/SG01-subsurf-abstract.html), SIGGRAPH
- Marschner, Westin, Arbree and Moon (2005), [Measuring and modeling the appearance of finished wood](https://www.cs.cornell.edu/~srm/publications/SG05-wood.html), SIGGRAPH
- Koenderink and Pont (2003), [The secret of velvety skin](https://unpaywall.org/10.1007%2Fs00138-002-0089-7), *Machine Vision and Applications*
- Todd, Norman and Mingolla (2004), [Lightness constancy in the presence of specular highlights](https://www.asc.ohio-state.edu/todd.44/date/Todd,%20Norman%20&%20Mingolla%202004.pdf) (reports Beck and Prazdny 1981)
- Motoyoshi, Nishida, Sharan and Adelson (2007), [Image statistics and the perception of surface qualities](https://www.nature.com/articles/nature05724), *Nature*
- Hansmann-Roth, Pont and Mamassian (2017), [Contextual effects on real bicolored glossy surfaces](https://pure.tudelft.nl/ws/portalfiles/portal/12907234/i1534_7362_17_2_17.pdf), *Journal of Vision*
- Di Cicco, Wijntjes and Pont (2019), [Understanding gloss perception through the lens of art](https://repository.tudelft.nl/record/uuid:550c3a32-0e7e-4b0c-a9ed-367a98335cc5), *Journal of Vision*
- Di Cicco, Wiersma, Wijntjes and Pont (2020), [Material properties and image cues for convincing grapes: the know-how of the 17th-century pictorial recipe by Willem Beurs](https://repository.tudelft.nl/record/uuid:4854c5e2-cc70-44fc-a6c4-deb24ba50d15), *Art and Perception*
- Di Cicco, van Zuijlen, Wijntjes and Pont (2021), [Soft like velvet and shiny like satin](https://repository.tudelft.nl/record/uuid:ed8025d9-0fdf-4ec1-815c-fef09dee61b8), *Journal of Vision*
- Fleming, Jäkel and Maloney (2011), [Visual perception of thick transparent materials](https://www.psychologicalscience.org/journals/psychological-science/0956797611408734/), *Psychological Science*
- Ohara, Kim and Koida (2022), [The role of specular reflections and illumination in the perception of thickness in solid transparent objects](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.766056/pdf), *Frontiers in Psychology*
- Atmospheric Optics, [Dutch still life reflections, Willem Claesz. Heda](https://atoptics.co.uk/fza35.htm)
- Met, Heilbrunn Timeline, [Still-Life Painting in Northern Europe, 1600-1800](https://www.metmuseum.org/essays/still-life-painting-in-northern-europe-1600-1800)
- New Masters Academy, [Ellipse guide handout](https://s3.amazonaws.com/uploads.nma.art/uploads/2021/03/Ellipse-Guide_Drawing-Foudations-Handout.pdf)
- Not reached: the translucency perception review on PubMed Central (PMC8340651) and the velvet/satin paper's full text there (browser check). Marked **judgement**: object sizes, albedos of paper and velvet, glass edge pairs, metal value range, brushed and tarnished metal, ceramic, raw and varnished wood, granite, paper, foods other than grapes, texture visibility, wear, and the studio lighting convention.
