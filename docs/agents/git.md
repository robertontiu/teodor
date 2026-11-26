# Git and publishing conventions

Back to the router: [AGENTS.md](../../AGENTS.md).

- **Author:** Robert Ontiu <robertontiu@users.noreply.github.com>. Push straight to `main`.
- **Commit by path:** `git commit -m "..." -- <paths>`. Several agents can share one working tree, so never `git add -A` while others are working. Check `git status` and `git log origin/main..HEAD` before pushing: a push publishes every local commit.
- **Commit messages** end with the attribution lines the session gives you, when it gives them.
- **Commit as you go**, after every finished piece of work, so an interrupted session loses at most the piece in progress.
- **Never commit:** canvas state (`*.npy`, `*.npz`, `*_frames/`), work dirs, `__pycache__`, `~/.cache/teodor/`, raw downloaded data (pigment spectra, museum images), or `studio/styles.local/`.
- **The site deploys** about 5 minutes after the last push that touches `site/` (a GitHub Action calls a Vercel Deploy Hook; [site.md](site.md)). Batch site changes into as few pushes as you can: Vercel's plan allows 100 deployments a day.
