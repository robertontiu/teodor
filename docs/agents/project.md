# The project

Moved from AGENTS.md. Back to the router: [AGENTS.md](../../AGENTS.md).

An experiment in whether an AI can **paint the way a human painter does**. A painter agent, Teodor, paints a feeling in a simulated studio, in a human-like perceive → feel → act loop. He researches, makes thumbnails and colour studies, and builds a drawing (a schema or a 3D blockout). Then he paints over it in many short look-and-correct episodes, and gets a fresh critic's reading between phases. The aim is a process as close as possible to how human painters work ([docs/research.md](../research.md), [docs/research/process.md](../research/process.md)), and output as close to professional quality as possible.

## Roles
- **Person (Robert, the owner):** asks for a painting with a theme or a feeling, and optionally a style.
- **Orchestrator agent:** sets up the studio, writes the painter's brief, runs the painter's phases and the critics, researches what's missing, shows the result and publishes it.
- **Painter agent:** Teodor, the persona that paints. He never talks to the person directly.
- **Critics:** fresh agents that see only the canvas and the commission.

## Decisions the owner has made
- The painter is called "Teodor" everywhere (first name only). Until round 10 he was "Teodor Lisk" and signed "T. Lisk"; the name was shortened on request and every painting was re-signed. Persona names stay fictional: an earlier name, "Elias Varga", collided with a real painter.
- Every painting is signed. Feelings are published openly with each painting.
- Public text (README, site) is plain and non-technical, with the research cited.
- The code is MIT; Teodor's paintings are CC BY 4.0 (credit the repo); paintings other people make with the project are theirs and their responsibility.
- Styles never authors; it must be a painting; utensils rest on research and real data; it's an experiment (the always-on rules in AGENTS.md).

## The signature
Every painting is signed "Teodor" (`studio/signature.py`): a handwritten mark with an underline flourish, laid as tapered brush strokes and coloured from the paint under it. In the studio it is the painter's last act (`studio.py sign`). To sign any image: `python3 studio/signature.py in.png out.png` (start from an unsigned image to re-sign).

## Keep it fresh
Teodor drifts into one look: a lone figure from behind, a lit doorway in a dark warm room, a hushed bittersweet mood. Every painting should be a departure. [docs/habits.md](../habits.md) lists the habits; the brief makes him study his past work and break at least three habits on purpose. The orchestrator checks the first checkpoint against the contact sheet and updates the habits after every painting. A style or mood the person asks for wins over any habit.

## Conventions
- Titles are a painter's titles, not labels for the feeling.
- Critics see only the canvas and the commission, never the feeling, journal or handoff.
