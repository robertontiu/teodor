#!/usr/bin/env python3
"""Refresh a work dir's copy of the studio (code, media, styles, targets, pigments) without touching
the painter's files (brief, journal, canvas, schemas). Use it before a painter draws when the engine
changed after the work dir was made, e.g. after planning.

Usage: python3 tools/refresh_studio.py <workdir>
"""
import glob, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDIO = os.path.join(ROOT, "studio", "v8")
w = os.path.abspath(sys.argv[1])
assert os.path.exists(os.path.join(w, "brief.md")), "not a work dir (no brief.md)"
for f in glob.glob(os.path.join(STUDIO, "*.py")):
    if not f.endswith("test_v8.py"):
        shutil.copy(f, w)
shutil.copytree(os.path.join(STUDIO, "media"), os.path.join(w, "media"), dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", ".*"))
for f in ("styles.json", "targets.json", "pigments.json", "subjects.json"):
    p = os.path.join(ROOT, "studio", f)
    if os.path.exists(p):
        shutil.copy(p, os.path.join(w, f))
print("studio refreshed in", w)
