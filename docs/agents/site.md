# The site

Back to the router: [AGENTS.md](../../AGENTS.md).

- **Live:** https://teodor.robertontiu.com, built from `site/` (Next.js).
- **Deploys:** `.github/workflows/deploy-site.yml` runs when a push touches `site/`, waits 5 minutes (a burst of pushes makes one deployment) and calls a Vercel Deploy Hook (secret `VERCEL_DEPLOY_HOOK`). Git-triggered deploys are off (`site/vercel.json`), because Vercel's Hobby plan allows 100 deployments a day and skipped builds count too. Run "Deploy site" from GitHub's Actions tab to deploy at once.
- **Adding a painting:** `site/public/paintings/rNN.jpg` (900×1200 JPEG) and an entry in `site/app/works.ts` (`model` set if the painter wasn't Opus 5.5). That gives it a page at `/rNN/`, a share preview and a sitemap entry. The site lists the newest first.
- **Public text** is plain and non-technical, with the research cited.
- **Building without network access:** the build fetches Google Fonts. In a sandbox without it, mock the font: put `module.exports = new Proxy({}, { get: (_, url) => typeof url === "string" ? "@font-face { font-family: 'Cormorant Garamond'; font-style: normal; font-weight: 500; src: local('Georgia'); }" : undefined, has: () => true });` in `/tmp/fontmock.cjs`, then run `NEXT_FONT_GOOGLE_MOCKED_RESPONSES=/tmp/fontmock.cjs npx next build --webpack` in `site/` (Turbopack ignores the mock). Delete `node_modules`, `.next` and `out` afterwards.
