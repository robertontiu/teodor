# References: how painters use studies, casts and photographs, and Teodor's rules for them

Written 2026-11-26. Why: Teodor builds faces, hands and figures from a 3D blockout alone, and in rounds 13 to 17 the faces came out as masks or caricatures. `docs/research/process.md` (2.1) names the cause: categorical schemas, the painter drawing the *category* face or hand instead of observed shapes of light and dark. Human painters break that schema by looking at real structure: the model, casts, studies, photographs. This doc says how they do it, where studying ends and copying begins, and the rules Teodor follows. The tool is `tools/find_refs.py`; the view is `studio.py look refs` (docs/MANUAL.md, "References").

Labels as in `process.md`: **[S]** a named source, **[T]** studio practice or a secondary account, **[M]** measured here, **[H]** a judgement of this document.

---

## 1. How painters use references

**The academy: copies, casts, then life.** Academic training put the living model last. At the Royal Academy, life drawing was "the ultimate stage", reached after copying prints and drawings and drawing antique statues or their plaster casts, so that students knew the "approved body types, poses and expressions of antique sculpture" and could correct the imperfections of real bodies (Wickham 2018) [S]. Bargue and Gérôme's *Cours de dessin* (Goupil, 1868-1873, 197 lithographs) codified the sequence: plates after casts, then after master drawings, then after the living model, each copied exactly as an exercise [S]. Note the direction [H]: the academy used casts to give students an *ideal* schema to correct nature with. Teodor has the opposite problem: his schema (the blockout's plane head) is already too ideal and generic, and he needs the specific irregularities of real faces and hands to correct *it*.

**Photographic académies for painters.** From the 1850s photographers made nude and costumed figure studies for artists. Eugène Durieu made such studies in 1853-54; Delacroix helped him pose the figures and later praised them, and Delacroix and other artists sketched from them. They were sold as "photographic académies", an alternative to the live model, often posed after classical statuary or old masters (The Met, Durieu, *[Nude Study]*, 2005.100.569) [S]. Both museums Teodor uses still hold many of these (section 4).

**Eakins: study versus tracing.** The Met's essay on Thomas Eakins says he "did not generally use photographs as a preparatory aid to painting"; he saw the camera as part of "knowing the figure", alongside dissection and preparatory wax and plaster sculpture, and introduced it to the American studio (The Met, Department of Photographs, 2004) [S]. The 2001 Philadelphia retrospective then showed newly surfaced photographs beside paintings with nearly identical figures, evidence that he had also projected and traced photographs; the tracing "was furtive" and "was frowned on at the time" (Yale Daily News, 2001, reporting the exhibition; the technical study by the museum's conservators is given from that report, not re-read) [S]. That is the line this doc draws: the camera as a way of knowing the figure is study; projecting and tracing it is copying, and even then painters hid it.

**Degas: several views, one painting.** Degas photographed a dancer from several angles, and two of these images inform the poses of the dancers in *Four Dancers* (c. 1899); photographs also suggested ways to frame a picture (National Gallery of Art, teacher handout on painting and photography, 2014, citing the literature) [S]. Degas's photographs are a separate practice closely tied to his posing and staging (Daniel et al., *Edgar Degas, Photographer*, The Met, 1998; from the publication's description) [S].

**Mucha: an archive of variants, synthesised.** Mucha photographed models in improvised poses, building "an archive of variants" to select from for later commissions, and for the *Slav Epic* staged costumed models, then "selected appropriate images and synthesised them" into each scene (Mucha Foundation, "Studio, Models and Staged Photography") [S]. A drawn study then simplifies or exaggerates what the camera recorded; a photograph helps with the body's structure but "cannot supply that entire design" (a secondary account, thehistoryofart.org) [T].

**Illustrators.** Rockwell's covers were staged with models and props and photographed by Gene Pelham ("Rockwell's Right-hand Man", *The Saturday Evening Post*, 2013, after Ron Schick's *Norman Rockwell: Behind the Camera*, 2009) [S]. The standard illustrator's advice, given in `process.md` 2.5 from Gurney (2010) and Schmid (1998), is to *correct* the camera: regroup its values (shadows go black, lights burn out), choose edges, select detail, and fix lens distortion [T]. (Gurney's blog post "Using photo reference", 2009, could not be fetched for this doc; its argument is given from the books.)

**Many faces, no one's face.** Averaging photographs of many faces gives a composite rated more attractive than almost all the individual faces in it, and more so as faces are added (Langlois & Roggman 1990) [S]. Galton's composite portraits (1878) were the first such averages [T]. For Teodor [H]: a face invented from several references drifts toward the typical and away from any one person's likeness, which is what the likeness rule wants; but it also drifts toward the bland, so the references are for *structure* (how a laugh folds a cheek), and the character of the face comes from the painting's feeling and the current.

**Where copying begins.** In *Rogers v. Koons* (2d Cir. 1992) a sculptor who reproduced the core of a photograph nearly entirely in a sculpture had no fair-use defence (U.S. Copyright Office fair-use summary) [S]. Teodor uses only public-domain images, so copyright is not the issue; the case is cited for the line itself [H]: reproducing an image's composition, pose and arrangement wholesale is copying, whatever the medium; studying how a feature is built and painting a new one is not.

**Summary [H].** Across these accounts painters use references in four ways: to *know* a structure (Eakins, the academy), to *gather variants* and choose (Degas, Mucha), to *synthesise* several into one invented figure (Mucha, illustrators), and, the frowned-on case, to *transfer* one image by projection or tracing (Eakins in secret). Teodor does the first three and never the fourth.

---

## 2. Teodor's rules for references

1. **Study, translate, never transfer (rule 2).** A reference is for structure and light: where the planes turn, how a form overlaps another, what the light does on it. It is studied beside the canvas (`look refs`), drawn from in a tonal study (*étude*), and translated through the current and the hand. It is never set as the schema (`ref`), traced, projected, composited or pasted, and no script samples colours or contours from it onto the canvas.
2. **No likeness of real people (rule 5).** A photograph shows a real person, and most old drawings and portraits do too. So:
   - never take one person's face as the subject: study **several references for one feature** (the cheek in a laugh, an eye in shadow, the mouth in a scream) and **invent the face**;
   - **at least three references per feature, from different sources** (different makers, and where possible different kinds: a photograph, a drawn study, a cast);
   - **no photographs of identifiable public figures at all** (performers, named sitters, famous models), even for a hand; a work whose title names its sitter is never used for a face (`find_refs.py` skips named titles by default; the orchestrator checks the rest, since many titles don't name the sitter: Nadar's *Pierrot Laughing* is the mime Deburau);
   - no images of people who could not consent (asylum patients, prisoners) and no post-mortem photographs [H].
3. **Only openly licensed images (rule 10).** CC0 or public domain, from a museum's open-access API, with provenance recorded per image in `refs/refs.json`: title, artist, date, museum, object URL, image URL, licence and the evidence for it (the Met's `isPublicDomain: true`; Cleveland's `share_license_status: CC0`). Nothing from a site with bot protection, and nothing worked around.
4. **Styles, never authors (rule 3).** A reference may be a public-domain work of the painting's current, but Teodor studies how the *current* handles a feature across several works and makers, never one artist's manner: at most two works by one artist per feature (`--per-artist`), and never an artist named as a model in the journal.
5. **No gore (rule 5).** No wound, execution, dissection or post-mortem images (filtered by title; the orchestrator checks).
6. **Name what you study.** Each reference carries a `feature` and a `reason` written by the painter ("the fold under the eye pushes the lower lid up"), not the tool's default. A reference with no reason is not used.
7. **Beware the comic type.** Prints of laughing "types" (genre heads, grimaces, caricatures of the passions) are the easiest laughing faces to find in the collections (section 4), and they teach caricature, the very failure of rounds 13-17. For a face feature, at least one reference should be a photograph or a study from life [H].
8. **When the museums hold nothing, say so.** Some subjects have no usable open-access references (section 4). Then the painter says so in the journal and works from the subject pages and the blockout; no reference from an unlicensed source.

---

## 3. Where it sits in the process

- **Planning (phase 1, after `subjects.json`):** the painter gathers references for the hard subjects (faces, hands, expressions, unusual poses), at least three per feature, with `tools/find_refs.py`, and writes each reason (`docs/prompts/painter-brief.md`).
- **Orchestrator check (before phase 1 continues):** licence, likeness, gore, one-author and reason checks; failing references are removed and the sheet rebuilt (`docs/orchestration.md`, "Subjects before drawing").
- **Études (phase 1 continued and later):** each face, hand and expression study is built from the blockout and its references side by side (`look refs <feature>`); the journal says what was taken from them.
- **Publishing:** `refs/refs.json` is copied into the round folder as `references.json` (provenance only; the images stay in the work dir and are never committed).

---

## 4. What the museums hold (measured 2026-11-26) [M]

`find_refs.py --dry` runs against both APIs, about 25-60 Met objects inspected per query and up to 8 kept per museum; judged by reading the titles, and for the laughing cheek and hands by looking at the images. Both searches are full text, so many hits are irrelevant (a "wet" photo search returns wet nurses and wet-collodion views; "eye study" returns landscapes).

| Subject | Photographs (1840s-1910s) | Drawn studies, prints, casts | Verdict |
|---|---|---|---|
| **Laugh / smile** | Very few. Duchenne de Boulogne's plates (1854-56; Met and Cleveland): *Natural laughter* (Fig. 32) and the electrically induced expressions, all of very few sitters; a handful of daguerreotypes with a faint smile. Long exposures made laughter rare in early photographs [T]. | Mostly comic types: Ostade's *Laughing Peasant*, Valckert's *Laughing Fool*, Hogarth's *Laughing Audience*, Boilly's *Grimaces* (1823), Rowlandson's *Le Brun Travested* (caricatures of the passions) | **Thin and risky.** Usable for the cheek and eye-corner structure only with care: at most two Duchenne plates (one sitter), plus types studied for structure, not character. |
| **Weeping / sorrow** | Duchenne's weeping plates; little else | Some drawings: Backer's *Weeping Woman Kneeling, Seen from Behind*, Goya's young woman weeping and covering her face, an 18th-c. French seated woman weeping | **Some**, mostly posture rather than the face. |
| **Scream / fear** | Duchenne's fear plate; H. P. Robinson's staged *Fear* (c. 1860) | Benjamin West's *Head of a Screaming Man* (1792, two sheets, Cleveland) | **Thin.** One draughtsman and one photographer. |
| **Hands** | Very few (hands in daguerreotype portraits, *Brother and sister clasping hands*) | **Rich:** studies of hands by Natoire, Greuze, Ingres, Caliari, Lenfant, de Wit, Delacroix, Piazzetta (hands playing instruments), an anonymous 19th-c. French study | **Good** for hands at rest, holding, gesturing; no hand gripping cloth as such, but drapery-holding hands appear in figure studies. |
| **Feet** | Almost none | Some, inside figure studies (the query is noisy) | **Thin**; search figure studies instead. |
| **Heads (any age), eyes** | Unidentified portrait daguerreotypes and tintypes (Southworth and Hawes, anonymous studios); Cameron's sitters are often identifiable [H] | **Rich:** heads of women and old women (Sebastiano del Piombo, Holbein, Greuze's *Head of an Old Woman Looking Up*, Piva, Procaccini, Legros); no eye-only studies found | **Good** for the structure of a head, light on a face and old age; "eye" searches don't work, use head studies. |
| **Figure / académies / back views** | **Rich:** Durieu, Vallou de Villeneuve, Belloc, Le Gray, Chauvassaignes, Eakins's figure photographs, a male nude at Cleveland | **Rich:** académies and back views (Lehmann, Sacchi, Annibale Carracci, Laemlein, a 17th-c. Dutch standing man from the back) | **Good.** Casts and antique figures too (`--type sculpture`). |
| **Motion (running, dancing)** | Chronophotography: Muybridge (Cleveland), Marey and Demeny (the Met); otherwise nothing moves in early photographs | Running figures (Callot, Lanfranco, Testa, Micco Spadaro); many Degas dancers (capped at two per feature) | **Good** in drawings; Muybridge for the mechanics. Dance photographs are mostly named performers (Nijinsky): not usable. |
| **Drapery** | Few | **Rich:** drapery studies (Albert Moore, Rethel, Lancrenon, an anonymous Florentine sheet) | **Good.** |
| **Hair** | Hairstyles in daguerreotypes; Cameron's long-haired sitters (identifiable) | A woman combing her hair (Devéria), a few heads | **Thin.** |
| **Hair in wind, wet hair** | Cameron's *The South West Wind* (1864) only | Nothing usable found | **None usable.** Work from the subject pages (`hair`) and the blockout's simulated hair. |
| **Children** | Unidentified children (Cameron, Penabert, anonymous studios); several named children and one post-mortem photograph (filtered) | Mostly Madonna and Child | **Some**, photographs of unidentified children only. |

What this means [H]: the collections are strong where academic training was (hands, heads, figures, drapery, casts) and weak where early photography could not go (fleeting expressions, motion other than chronophotography, wind and water on hair). The expressions Teodor most needs (a laugh, a scream) are exactly the weakest, and what exists leans to one 19th-century scientist's sitters and to comic types. For those, references help with anatomy (which muscles bunch where) more than with the look of a living face; the subject pages (`docs/subjects/face.md`, its FACS table) stay the main source.

---

## 5. The tool, briefly

`tools/find_refs.py <workdir> "<terms>" ... --type photo|study|print|painting|sculpture|any --feature "<feature>" [--why "..."] [--dry] [--take met:ID cma:ID] [--n 4] [--per-artist 2] [--allow-named] [--sheet]`. It searches The Met (`/public/collection/v1.1/search` with offset paging and a department per type, then `/v1/objects/<id>`, kept only when `isPublicDomain` is true; paced at 0.6 s, and it stops asking the Met for the run on a 403) and the Cleveland Museum of Art (`/api/artworks/` with the bare `cc0` flag and a type filter, kept only when `share_license_status` is CC0), with a plain User-Agent. It skips named sitters, gore, asylum and prison photographs, and more than two works per artist per feature; downloads web-size images into `<workdir>/refs/`; records each in `refs/refs.json`; and draws `refs/sheet.jpg` grouped by feature. The skips are heuristics on titles [H]: they err toward skipping and still miss single-word titles and unnamed famous sitters, so the orchestrator's check is the real one.

---

## Sources

- Bargue, C., with J.-L. Gérôme (1868-1873). *Cours de dessin*. Goupil & Cie. Summary: https://en.wikipedia.org/wiki/Charles_Bargue (modern edition: G. M. Ackerman, *Charles Bargue and Jean-Léon Gérôme: Drawing Course*, ACR Edition, 2003).
- Daniel, M., with E. Parry and T. Reff (1998). *Edgar Degas, Photographer*. The Metropolitan Museum of Art. https://www.metmuseum.org/art/metpublications/Edgar_Degas_Photographer (from the publication page).
- Galton, F. (1878). Composite portraits. *Journal of the Anthropological Institute* 8, 132-144. (Not re-read.)
- Langlois, J. H., & Roggman, L. A. (1990). Attractive faces are only average. *Psychological Science* 1(2), 115-121. https://digitalcommons.usu.edu/fchd_facpub/237 (abstract).
- The Metropolitan Museum of Art. Eugène Durieu, *[Nude Study]*, 1853-54, 2005.100.569. https://metmuseum.org/art/collection/search/286255
- The Metropolitan Museum of Art, Department of Photographs (2004). Thomas Eakins (1844-1916): Photography, 1880s-90s. *Heilbrunn Timeline of Art History*. https://www.metmuseum.org/essays/thomas-eakins-1844-1916-photography-1880s-1890s
- The Metropolitan Museum of Art. Open Access (CC0). https://www.metmuseum.org/openaccess
- Mucha Foundation. Studio, Models and Staged Photography. https://muchafoundation.org/gallery/themes/theme/studio-models-and-staged-photography
- National Gallery of Art (2014). Painting and photography, teacher institute handout. https://www.nga.gov/content/dam/ngaweb/Education/teachers/teacher-institute-2014/painting-photography-handout.pdf
- *Rogers v. Koons*, 960 F.2d 301 (2d Cir. 1992). U.S. Copyright Office fair-use summary: https://www.copyright.gov/fair-use/summaries/rogers-koons-2dcir1992.pdf
- *The Saturday Evening Post* (2013). Classic Art: Rockwell's Right-hand Man. https://www.saturdayeveningpost.com/sep-keyword/gene-pelham/ ; Schick, R. (2009). *Norman Rockwell: Behind the Camera*. Little, Brown.
- thehistoryofart.org. Alphonse Mucha's Photography and Working Methods. https://www.thehistoryofart.org/alphonse-mucha/photography-and-working-methods/ (secondary).
- Wickham, A. (2018, 6 February). Strike a pose: 250 years of life drawing at the RA. Royal Academy of Arts. https://royalacademy.org.uk/article/from-life-history-of-life-drawing-annette-wickham
- Yale Daily News (2001, 12 December). Painter Eakins used projected images in work. https://yaledailynews.com/blog/2001/12/12/painter-eakins-used-projected-images-in-work/
- Gurney, J. (2010). *Color and Light*; Schmid, R. (1998). *Alla Prima*: as cited in `process.md` 2.5.

Not reached during this research (permission timed out): Gurney's post "Using photo reference" (gurneyjourney.blogspot.com, 2009) and the Cleveland Museum of Art's API documentation page (openaccess-api.clevelandart.org); the API's behaviour above was checked directly against the API instead.
