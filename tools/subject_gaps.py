#!/usr/bin/env python3
"""Which subjects of a planned painting still need research.

Usage: python3 tools/subject_gaps.py <workdir> [--style ID]

Reads <workdir>/subjects.json, written by the painter at the end of planning:
  {"style": "romanticism", "subjects": [{"id": "face", "note": "laughing, three-quarter, from below"},
                                         {"id": "seabirds", "note": "gulls in a gale"}]}
Ids should be the library's ids (docs/subjects/README.md) where one fits; a new id is fine for
a subject the library doesn't have yet (kebab-case, broad enough to reuse: "seabirds" -> "animals"
if animals covers it).

Prints, per subject, whether layer 1 (docs/subjects/<id>.md) and layer 2 (the style's rules in
studio/subjects.json -> styles.<style>.<id>) exist, and writes <workdir>/subject_gaps.json with the
missing ones. Exit code 0 when nothing is missing, 1 otherwise.
"""
import json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def load_library():
    lib = {"subjects": {}, "styles": {}}
    main = REPO / "studio" / "subjects.json"
    files = [main] if main.exists() else []
    files += sorted((REPO / "studio" / "subjects.parts").glob("*.json"))
    for f in files:
        d = json.loads(f.read_text())
        lib["subjects"].update(d.get("subjects", {}))
        for st, subs in d.get("styles", {}).items():
            lib["styles"].setdefault(st, {}).update(subs)
    return lib


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    wd = Path(sys.argv[1])
    plan = json.loads((wd / "subjects.json").read_text())
    style = sys.argv[sys.argv.index("--style") + 1] if "--style" in sys.argv else plan.get("style")
    lib = load_library()
    gaps = []
    for s in plan["subjects"]:
        sid = s["id"]
        l1 = (REPO / "docs" / "subjects" / f"{sid}.md").exists()
        l2 = bool(style) and sid in lib["styles"].get(style, {})
        print(f"{sid:16s} layer 1: {'yes' if l1 else 'MISSING'}   layer 2 ({style or 'no style'}): {'yes' if l2 or not style else 'MISSING'}")
        if not l1:
            gaps.append({"layer": 1, "subject": sid, "note": s.get("note", "")})
        if style and not l2:
            gaps.append({"layer": 2, "subject": sid, "style": style, "note": s.get("note", "")})
    (wd / "subject_gaps.json").write_text(json.dumps(gaps, indent=1))
    print(f"{len(gaps)} gap(s); written to {wd / 'subject_gaps.json'}")
    sys.exit(1 if gaps else 0)


if __name__ == "__main__":
    main()
