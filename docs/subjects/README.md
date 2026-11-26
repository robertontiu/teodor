# Subjects: what things look like, and how each style changes them

Teodor's knowledge of subjects is layered, like his styles.

**Layer 1, the subject as it really is** (`docs/subjects/<subject>.md`): how the thing is built and how painters observe and draw it from life. Proportions and structure, how it looks from different angles and distances, how light falls on it, how it moves or changes, its range of variation (age, species, material, weather), and the drawing and painting methods that get it right. It is the realistic baseline, written for a painter, with sources.

**Layer 2, the subject in a style** (`docs/styles/subjects/<style>--<subject>.md`, plus `studio/subjects.json` → `styles.<style>.<subject>`): how the current departs from the baseline. Which proportions it stretches or flattens, what it simplifies or idealises, what it leaves out, which conventions it uses (the almond eye of an icon, the ukiyo-e hairline, the Fauvist green shadow, Cubist faceting), and what stays true to life. Each entry describes a twist from layer 1, never an artist's personal manner: styles, never authors.

A painter reads layer 1 for every subject in the schema, then layer 2 for the chosen style, and paints the subject through both.

## Subjects

| id | layer 1 covers |
|---|---|
| `face` | the head and face: proportions, planes, orientation and foreshortening, age and sex, features, expressions (facial action units) |
| `figure` | the human body: proportion canons, gesture and line of action, anatomy that shows, weight and balance, foreshortening, poses |
| `hands-feet` | hands and feet: proportions, construction, gestures and grips |
| `hair` | hair as masses and locks, wet and dry, in wind, by type and age |
| `drapery` | cloth and clothing: fold types, gravity, wind, material, how cloth reveals the body |
| `crowd` | groups and crowds: overlap, rhythm, scale, individuality within a mass |
| `animals` | mammals, birds, fish and insects: skeletal structure, gesture, fur, feathers and scales, movement |
| `trees-plants` | trees, foliage, grass and vegetation: growth structure, masses, seasons |
| `flowers` | flowers and fruit as subjects: structure, petals, still-life arrangement |
| `landscape` | terrain, rock, mountains, fields, paths: structure, planes, recession |
| `water` | still and moving water, waves, spray, reflections, transparency, rain |
| `sky` | sky, clouds, weather, atmosphere, sun and moon, times of day |
| `fire-smoke` | fire, smoke, steam, candlelight as subjects |
| `light-shadow` | light on form: form and cast shadow, reflected light, halftones, light sources, atmospheric perspective |
| `space` | perspective and space: linear, aerial, overlap, scale, horizon and viewpoint, foreshortening of the scene |
| `architecture` | buildings, interiors, streets, doors and windows: structure, perspective, materials |
| `objects` | still-life objects and materials: glass, metal, ceramic, wood, fabric, paper, food; texture and reflection |

## Layer 1 file template (`docs/subjects/<id>.md`)
1. **What it is, structurally**, with proportions and landmarks as numbers where the literature gives them.
2. **Seen from different viewpoints** (orientation, foreshortening, distance).
3. **Under light** (planes, form shadow, cast shadow, reflected light, colour of light and shadow).
4. **Variation** (age, type, material, season, weather, motion).
5. **How painters observe and construct it** (methods, order of work, common simplifications).
6. **Common mistakes**: what makes it read as wrong, stiff, cartoonish or "a mannequin", and how to check for it.
7. **Checks for Teodor**: three to seven concrete things to verify on the canvas.
8. **Sources**, with links; values without a source are marked as judgement calls.

`studio/subjects.json` holds the machine-readable short form: `subjects.<id>` (key proportions, checks) and `styles.<style>.<subject>` (the twist: a short list of rules, each citing its source, with judgement calls marked). Research batches write to `studio/subjects.parts/*.json`, which are merged into it.
