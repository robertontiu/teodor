"""Set up a work dir for one painting and write the painter's brief into it.

  python3 tools/make_brief.py <workdir> --commission "a public exhibition on a THEME. The theme is: ..." \\
      (--theme | --feeling "the feeling in the person's words") [--style ID|free] [--medium M] [--support S]

It copies the current studio (studio/v8 with its media) into the work dir, plus habits.md, a fresh
past_work.jpg (studio/contact_sheet.py), styles.json and targets.json, and writes brief.md from
docs/prompts/painter-brief.md with every placeholder filled. With --style free (the default) Teodor
chooses the current himself in phase 1 from the researched ones and declares it in feeling.md.
Artist-specific configurations (temporary, never committed) can be put in studio/styles.local/<id>.json
and are found by id like any other style.
"""
import argparse, glob, json, os, shutil, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
STUDIO = os.path.join(ROOT, "studio", "v8")

THEME = ("you choose it yourself. Sit with the commission and find the feeling that you, Teodor, most need to say about it: "
         "what it is like from the inside, what sits underneath it or right beside it. A complex feeling (two or at most three held "
         "at once and pulling against each other) can give a painting more life, but a single overwhelming feeling is allowed too; "
         "it need not be bittersweet. Avoid the easiest poster version if you find something truer.")


def styles():
    s = json.load(open(os.path.join(ROOT, "studio", "styles.json")))
    for f in glob.glob(os.path.join(ROOT, "studio", "styles.local", "*.json")):
        s.update(json.load(open(f)))
    return {k: v for k, v in s.items() if not k.startswith("_")}


def lst(v):
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    if isinstance(v, dict):
        return "; ".join(f"{k}: {lst(x)}" for k, x in v.items())
    return str(v)


def style_block(sid, st, targets):
    if sid == "free":
        rows = "\n".join(f"  - {k}: {v.get('name', k)} ({v.get('period', '')}); media {', '.join(v.get('media', []))}" for k, v in st.items())
        return ("The current is YOUR CHOICE. Choose the one that carries your feeling best, not the one you are used to, from the researched currents:\n"
                f"{rows}\n"
                "Read the docs of the two or three you consider ({REPO}/docs/styles/<id>.md), choose, and write the current, the medium and the support "
                "you chose, and why, at the top of feeling.md. Use that current's doc as your style doc from then on, and its id in `new --style`. "
                "If you need a current that is not listed, say so in your reply instead of inventing one: it gets researched first.")
    s = st[sid]
    out = [f"Current: {s.get('name', sid)} ({s.get('period', '')}). Read its doc in full: {{REPO}}/{s.get('doc', 'docs/styles/' + sid + '.md')}."]
    for key, label in (("technique", "Technique"), ("palette", "Palette"), ("light", "Light"), ("value_key", "Value key"),
                       ("composition", "Composition"), ("drawing", "Drawing and form"), ("edges", "Edges"), ("marks", "Marks"),
                       ("process", "Order of work"), ("finishing", "Finishing"), ("pitfalls", "Pitfalls")):
        if s.get(key):
            out.append(f"- {label}: {lst(s[key])}")
    if s.get("modes"):
        out.append(f"- Modes (choose one and say which in feeling.md): {', '.join(s['modes'])}")
    t = targets.get(sid)
    out.append(f"- Measured target: {t['_n']} public-domain works ({t['_rule']}); `report` compares your canvas with it."
               if t else "- Measured target: none yet for this current (`report` still gives the numbers and flags).")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("--commission", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--theme", action="store_true")
    g.add_argument("--feeling")
    ap.add_argument("--style", default="free")
    ap.add_argument("--medium")
    ap.add_argument("--support")
    a = ap.parse_args()
    st = styles()
    if a.style != "free" and a.style not in st:
        sys.exit(f"No researched style '{a.style}'. Research it first (docs/styles/README.md). Known: {', '.join(st)}")
    sys.path.insert(0, STUDIO)
    from media import MEDIA
    medium = a.medium or (st[a.style]["media"][0] if a.style != "free" else "your choice")
    if a.style != "free" and medium not in MEDIA:
        sys.exit(f"The current's medium '{medium}' isn't in the studio yet (have: {', '.join(MEDIA)}); pass --medium.")
    support = a.support or ((st[a.style].get("support") or {}).get(medium) if a.style != "free" else None) or \
        (list(MEDIA[medium].supports)[0] if medium in MEDIA else "your choice")
    if medium in MEDIA and MEDIA[medium].supports and support not in MEDIA[medium].supports:
        support = list(MEDIA[medium].supports)[0]

    w = os.path.abspath(a.workdir)
    os.makedirs(w, exist_ok=True)
    for f in glob.glob(os.path.join(STUDIO, "*.py")):
        if not f.endswith("test_v8.py"):
            shutil.copy(f, w)
    shutil.copytree(os.path.join(STUDIO, "media"), os.path.join(w, "media"), dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", ".*"))
    shutil.copy(os.path.join(ROOT, "docs", "habits.md"), os.path.join(w, "habits.md"))
    for f in ("styles.json", "targets.json"):
        p = os.path.join(ROOT, "studio", f)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(w, f))
    subprocess.run([sys.executable, os.path.join(ROOT, "studio", "contact_sheet.py"), os.path.join(ROOT, "rounds"),
                    os.path.join(w, "past_work.jpg")], check=True, capture_output=True)
    targets = json.load(open(os.path.join(ROOT, "studio", "targets.json"))) if os.path.exists(os.path.join(ROOT, "studio", "targets.json")) else {}
    manual = os.path.join(ROOT, "docs", "manual", f"{medium}.md")
    tpl = open(os.path.join(ROOT, "docs", "prompts", "painter-brief.md")).read()
    tpl = tpl[tpl.index("-->") + 3:].lstrip("\n")
    feeling = THEME if a.theme else (f"it is given: {a.feeling}. Make it yours: find what it is like from the inside and which human moment carries it.")
    rep = {"{STYLE}": style_block(a.style, st, targets), "{COMMISSION}": a.commission, "{FEELING}": feeling,
           "{MEDIUM}": medium, "{SUPPORT}": support, "{STYLE_ID}": a.style if a.style != "free" else "<your chosen id>",
           "{MANUAL}": manual if os.path.exists(manual) else os.path.join(ROOT, "docs", "manual", "<medium>.md"),
           "{WORKDIR}": w, "{REPO}": ROOT}
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    tpl = tpl.replace("{REPO}", ROOT)
    open(os.path.join(w, "brief.md"), "w").write(tpl)
    left = [x for x in ("{WORKDIR}", "{STYLE}", "{MEDIUM}", "{FEELING}") if x in tpl]
    print(os.path.join(w, "brief.md"), "(unfilled: " + ", ".join(left) + ")" if left else "")


if __name__ == "__main__":
    main()
