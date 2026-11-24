# Teodor site

The gallery at https://teodor.robertontiu.com: one painting per screen, swipe or use the arrow keys, F for fullscreen.

Next.js (App Router), exported as a static site.

## Run

```sh
npm install
npm run dev     # http://localhost:3000
npm run build   # static export in out/
```

The build fetches Cormorant Garamond from Google Fonts (via `next/font/google`), so it needs network access.

## Deploy

On Vercel: import the repo and set **Root Directory** to `site`. The framework preset (Next.js) and defaults are right as they are.
Any static host works too: upload the contents of `out/` after `npm run build`.

## Paintings

They live in `public/paintings/` (900x1200 jpg). To add one:

1. Drop the jpg into `public/paintings/`, e.g. `r11.jpg`.
2. Add `{ id: "r11", title: "Its Title" }` at the end of the list in `app/works.ts` (add `model: "Fable 5.2"` or similar if it was not painted by Opus 5.5) (the list is in the order painted; the gallery shows the newest first).

The Open Graph / Twitter image is `/paintings/r9.jpg`, set in `app/layout.tsx`.

## Builds only when the site changes

`vercel.json` sets an ignored build step: `git diff --quiet HEAD^ HEAD -- .` runs from this `site/` folder (the project's Root Directory), so Vercel builds only when something under `site/` changed in the pushed commit: the site code, or a new painting in `public/paintings/` with its entry in the works list. Commits that only touch rounds, docs or the studio are skipped. (If the previous commit can't be found, for example on the very first deploy, the command fails and Vercel builds anyway.)

## Pages and sharing

- `/` is the gallery; `/r0/` … `/r10/` are the same gallery opened at one painting, each with its own title, description and Open Graph / Twitter preview image (the painting itself). The Share button shares these links; old `#r9` links still work.
- `robots.txt` allows everything and points to `sitemap.xml`, which lists every painting page with its image.
- The favicon and home-screen icon are Teodor's badge (`app/icon.png`, `app/apple-icon.png`; source in `/assets/badge.png`).
