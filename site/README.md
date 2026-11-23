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
2. Add `["r11", "Its Title"]` to the `works` list in `app/Gallery.tsx`, where you want it in the order.

The Open Graph / Twitter image is `/paintings/r9.jpg`, set in `app/layout.tsx`.
