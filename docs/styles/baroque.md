# Baroque chiaroscuro and tenebrism

Researched 2026-11-25. Citations in brackets refer to the numbered sources at the end. **[J]** marks a judgement call; **[L]** marks a claim resting on a source located but not read in this session (a fetch limit), to be checked.

## 1. In one paragraph
The dramatic light-dark painting that began with Caravaggio in Rome around 1600 and spread, through his followers, into "an international movement" and one of the foundations of Baroque painting: Manfredi in Italy, the Utrecht painters (ter Brugghen, Honthorst), Valentin in France, Ribera in Naples and Spain [1]. Chiaroscuro means light-dark, "the balance and pattern of light and shade in a painting" [2]; tenebrism (from *tenebroso*, dark) is its extreme form, where most of the picture falls into darkness and a strong focused light picks out the figures **[J]** (standard definition; not in a read source). It wanted immediacy: real models, figures pushed up to the picture plane, a past event unfolding in front of the viewer [1]. Later Baroque painters, Rembrandt among them, carried the dark ground and the built-up light into a more inward key [4].

## 2. How it carries feeling
- **Light as event and judgement:** "a focused light source from high up, without reflections", with very light and very dark areas side by side, gives figures "enormous three-dimensionality" [1]. Light falls on someone: revelation, guilt, grace, violence **[J]**.
- **Confrontation:** figures close to the picture plane seem to confront the viewer; the scene happens now [1].
- **Darkness as space and silence:** large areas of near-black ground carry weight, threat or intimacy; what is left out matters **[J]**.
- **Bodies and real faces:** posed live models instead of idealised forms close the gap between painting and everyday life [1][3]: dirty feet, wrinkled hands, plain faces carry pathos **[J]**.
- **Avoided:** even, diffuse daylight; decorative colour; distance and calm **[J]**. Emotion research: `docs/research/emotion.md` once written (for now `docs/research.md`).

## 3. Media, supports and grounds
- **Historical:** oil on canvas. Caravaggio's early works have a warm, transparent ground that serves as a mid-tone for flesh and hair; *Salome* has a darker priming [3]; one ground analysed was mostly calcite, earth pigments and a little lead white [3]. Egg tempera was found in some of his white paint, walnut oil elsewhere [3]. Rembrandt's canvases moved from grey-over-red double grounds (1630s) to drab grey-brown quartz-clay grounds and other dark grounds later [4].
- **The ground's role:** the darker ground is a "readymade midtone" [4]; over a dark ground "thick, high-impasto applications" are needed to reach brightness [4]. Over the career, Caravaggio moved toward broader handling and "a greater use of the ground or ground colour to increase the drama of the tenebristic effects" [3].
- **Default for Teodor:** oil on `canvas`, warm mid-dark brown ground `#5a4532` **[J]** (between the warm transparent and the darker priming in [3]).

## 4. Palette
- **Principle:** a limited, earth-based palette with few saturated accents (a vermilion or red-lake drapery, a white sleeve) against brown-black; colour lives only in the light **[J]**.
- **Pigments** (hex values approximate **[J]**; the list is standard Baroque practice **[J]** except ground earths and lead white [3]):
  - lead white `#efe8d8`, yellow ochre `#c08f45`, lead-tin yellow `#ddc25a`
  - vermilion `#c13a24`, red lake `#8f2032`, red ochre `#93452c`
  - raw umber `#5c4a36`, burnt umber `#4a3424`, bone black `#1a1714`
  - green earth `#6f7556`, azurite/smalt blue `#3a5276` (used sparingly)
  - the ground itself `#5a4532`
- **Avoid:** high-key pastel colour; cool blue shadows from atmosphere; mixing white into shadows (it greys them) **[J]**.

## 5. Light and value
One strong, focused source, high and to one side, with no reflected light [1]; low-key overall with a narrow band of high lights; abrupt transitions from light to shadow at the terminator, shadows merging into the dark background (lost edges in the dark) **[J]**. A candle or hidden flame inside the picture is a variant (Utrecht Caravaggisti, Georges de La Tour) **[J]**.

## 6. Drawing and form
Caravaggio worked from posed live models and did not idealise [1]; he used incised lines in the priming and broad brushstrokes to indicate forms (abbozzo) instead of a full drawing [3]. Form is carved by the light: the lit plane is modelled, the shadow side is mostly ground or near-ground **[J]** following [3][4].

## 7. Composition
Figures at half or three-quarter length, close to the picture plane [1]; shallow stage, a plain dark wall behind; diagonals of light and gesture; tight cropping that crowds the frame; a moment of action or recognition **[J]**.

## 8. Marks and edges
Broad bristle brushes for the abbozzo and darks; lights laid thickly and directly, increasingly broad [3][4]; impasto in the brightest passages over dark grounds [4]. Edge hierarchy: hard edges where light meets dark against the ground, lost edges where shadow meets background **[J]**.

## 9. Process (the order of work)
After [3] (Caravaggio) and [4] (Rembrandt, dark-ground works):
1. Prepare a warm or dark coloured ground.
2. Pose the model and the light; mark key contours by incising into the still soft priming [3].
3. Abbozzo: broad brushstrokes indicating forms [3] (Rembrandt: a compositional sketch in light paint, then thin dark brown sketching [4]).
4. Lay in the lights, building lead-white-rich passages thickly where light falls; let underlayers dry [4].
5. Final paint in one or two layers; the ground kept as a mid-tone between lights and darks [3][4].
6. Late brown "ground-coloured" paint added near the end to sharpen darks, e.g. between fingers and in eye sockets [3].
7. Shadow glazes feathered out onto the lights [3].

Teodor's phases **[J]**: phase 1 = model/light blockout (`scene` with one lamp) and incised-style `transfer`; phase 2 = abbozzo and lights; phase 3 = final layer, darks reclaimed, glazes, accents.

## 10. Finishing
Degree of finish varies: high finish and surface effect in some commissions, broader handling later [3]. The last acts are the strongest highlights and the dark accents reclaiming edges, then varnish **[J]**. Oil grows more transparent with age, so grounds now read darker than intended [3]: Teodor should not exaggerate the ground for a "museum" look **[J]**.

## 11. Pitfalls for Teodor
- **Pastiche:** black background plus spotlight on a face; candle-in-the-dark kitsch; brown sauce everywhere; faked craquelure.
- **Nearest wrong feelings:** horror-film menace, cheap theatricality, gloom without event; and Teodor's habit of a lit doorway in a dark warm room (`docs/habits.md`) is close to this current, so the light must strike a figure or event, not a hushed interior **[J]**.
- **Value collapse:** without a narrow high-value band the picture goes muddy; check `look gray` and `look notan 2`.
- **Engine:** v8 oil can build impasto but there is no incising tool.

## 12. Engine mapping (studio v8)
- **Medium:** `oil --support canvas` (exists).
- **Schema:** `scene` blockout with one strong high side light gives the cast-light structure.
- **Tools:** `flat` and `round` bristle brushes for abbozzo and lights; `knife` sparingly for thick lights; `liner` for incised-like contour marks; `smudge` and `blend` for merging shadows into ground; `glaze` intention for shadow glazes.
- **Intentions:** `transfer` (with a dark colour); `match` broad on the lights only (clip to the lit region), leaving ground in shadows; high `impasto` and `load` in lights; `glaze` at the end.
- **Felt state:** higher arousal and tension than the Renaissance; care moderate-high.
- **Views:** `look notan 2` (the picture must read as light shapes on dark); `look squint`.
- **Gaps:** no incising into a wet priming; no true transparency of the ground (exposed ground is just unpainted canvas colour); no varnish finishing op yet; no paint-ageing (refractive-index) model, which is fine.

## 13. Sources
1. The Metropolitan Museum of Art, "Caravaggio (Michelangelo Merisi) (1571-1610) and His Followers" (Heilbrunn Timeline): https://www.metmuseum.org/essays/caravaggio-michelangelo-merisi-1571-1610-and-his-followers (read)
2. Tate, Art term "Chiaroscuro": https://www.tate.org.uk/art/art-terms/c/chiaroscuro (read)
3. L. Keith (1998), "Three Paintings by Caravaggio", *National Gallery Technical Bulletin* 19, 37-51: https://www.nationalgallery.org.uk/research/research-resources/technical-bulletin/three-paintings-by-caravaggio ; text https://www.nationalgallery.org.uk/media/15906/keith1998b.rtf (read)
4. P. Noble (2025), "The Role of the Colored Ground in Rembrandt's Painting Practice", *JHNA* 17:2: https://jhna.org/articles/the-role-of-the-colored-ground-in-rembrandts-painting-practice/ (read, first part)
5. E. Kolfin (2025), "Why Colored Grounds Matter", *JHNA* 17:2 (Utrecht Caravaggisti grounds influencing overall tone, after A. Roy): https://jhna.org/articles/why-colored-grounds-matter-evolving-research-colored-grounds-in-dutch-paintings-1580-1720/ (read, first part)
