#!/usr/bin/env python3
"""Merge studio/subjects.parts/*.json into studio/subjects.json (later parts win per key)."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
out = REPO / "studio" / "subjects.json"
lib = json.loads(out.read_text()) if out.exists() else {}
lib.setdefault("_about", "Teodor's subject library, short form. Layer 1: subjects.<id>; layer 2: styles.<style>.<id>. Docs: docs/subjects/README.md.")
lib.setdefault("subjects", {}); lib.setdefault("styles", {})
for f in sorted((REPO / "studio" / "subjects.parts").glob("*.json")):
    d = json.loads(f.read_text())
    lib["subjects"].update(d.get("subjects", {}))
    for st, subs in d.get("styles", {}).items():
        lib["styles"].setdefault(st, {}).update(subs)
out.write_text(json.dumps(lib, indent=1, ensure_ascii=False) + "\n")
print(f"{len(lib['subjects'])} subjects, {sum(len(v) for v in lib['styles'].values())} style rules -> {out}")
