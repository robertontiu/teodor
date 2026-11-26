"""Measured style targets: what each current measures like, from public-domain works in The Met's
open-access collection (Open Access API, collectionapi.metmuseum.org; images and data CC0).
Spectre does the same for music (tools/refcurve.py: era target curves from catalogue data).

How it works:
  1. `index`: list the object ids of a few departments and fetch each record once (cached in
     ~/.cache/teodor/met/, never committed). The Met has no movement labels, so
  2. each current is selected by a RULE on the records (date range, artist nationality or culture,
     classification, medium keywords), written below and stored with the result as provenance.
  3. `measure`: up to N matching public-domain works per current are downloaded (the Met's
     "web-large" image), measured with studio/v8/eyes.py and deleted. The mean and standard deviation
     of every measure go to studio/targets.json with the rule, n and the Met object ids.
     Only statistics are versioned, never images.

  python3 tools/measure_targets.py index [--limit 4000]
  python3 tools/measure_targets.py index-csv [--per-rule 250]   # Drawings and Prints candidates via MetObjects.csv
  python3 tools/measure_targets.py measure [style ...] [--n 60] [--parts]

Department 9 (Drawings and Prints, ~186,000 objects) is too large to sample at random for rare groups such as
pen-and-ink illustration drawings, so `index-csv` reads The Met's Open Access CSV (MetObjects.csv from
github.com/metmuseum/openaccess, CC0; downloaded once to ~/.cache/teodor/met/openaccess/), applies a coarse
pre-filter (CSV_PREFILTERS) and fetches the API records of up to --per-rule matches each into
~/.cache/teodor/met/records_dp_cands.jsonl. The RULES below then select from all cached records as before.
`--parts` writes each result to studio/targets.parts/<style>.json instead of studio/targets.json (for merging).

A rule is a proxy for a movement, not a curator's label: "Dutch paintings 1600-1690" is mostly but
not only the Dutch Golden Age. Currents still in copyright (surrealism, abstract-expressionism)
have no public-domain sample and stay unmeasured. (The Art Institute of Chicago labels works by
style, but its image server refused the workspace's requests; the Met's search endpoint is retired,
so this tool reads department listings and object records instead.)
"""
import io, json, os, random, sys, time, urllib.request
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "studio", "v8"))
import eyes  # noqa: E402

API = "https://collectionapi.metmuseum.org/public/collection/v1/"
UA = "TeodorResearch/1.0 (https://github.com/robertontiu/teodor)"
CACHE = os.path.expanduser("~/.cache/teodor/met")
DEPARTMENTS = {11: "European Paintings", 6: "Asian Art", 17: "Medieval Art", 1: "The American Wing"}
FIELDS = ("objectID", "isPublicDomain", "primaryImageSmall", "department", "classification",
          "objectBeginDate", "objectEndDate", "artistNationality", "culture", "medium")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            return urllib.request.urlopen(req, timeout=60).read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1 + 2 * attempt)


def index(limit):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "records.jsonl")
    seen = os.path.join(CACHE, "seen.txt")
    have = set(open(seen).read().split()) if os.path.exists(seen) else set()
    with open(path, "a") as f, open(seen, "a") as fs:
        for dep, name in DEPARTMENTS.items():
            ids = json.loads(get(API + f"objects?departmentIds={dep}"))["objectIDs"] or []
            random.Random(dep).shuffle(ids)
            ids = [i for i in ids[:limit] if str(i) not in have]
            print(f"{name}: fetching {len(ids)} records", flush=True)
            for k, i in enumerate(ids):
                try:
                    o = json.loads(get(API + f"objects/{i}"))
                except Exception:
                    continue
                fs.write(f"{i}\n")
                if o.get("isPublicDomain") and o.get("primaryImageSmall"):
                    f.write(json.dumps({k2: o.get(k2) for k2 in FIELDS}) + "\n")
                if k % 200 == 0:
                    f.flush(); fs.flush(); print(f"  {k}", flush=True)
                time.sleep(0.03)


def records():
    out, seen = [], set()
    for fn in ["records.jsonl"] + sorted(f for f in os.listdir(CACHE) if f.startswith("records_dp") and f.endswith(".jsonl")) if os.path.isdir(CACHE) else []:
        for l in open(os.path.join(CACHE, fn)):
            o = json.loads(l)
            if o.get("objectID") in seen:
                continue
            seen.add(o.get("objectID")); out.append(o)
    return out


import re  # noqa: E402

# coarse pre-filters on MetObjects.csv rows (index-csv); the RULES decide
CSV_PREFILTERS = {
    "pen-and-ink-illustration": lambda o, m, b: o["Classification"] == "Drawings" and 1875 <= b <= 1920 and "pen" in m and "ink" in m,
    "etching-engraving-engraving": lambda o, m, b: o["Department"] == "Drawings and Prints" and o["Classification"] == "Prints" and 1480 <= b <= 1900 and m.startswith("engraving"),
    "etching-engraving-etching": lambda o, m, b: o["Department"] == "Drawings and Prints" and o["Classification"] == "Prints" and 1500 <= b <= 1925 and m.startswith("etching"),
}


def index_csv(per_rule):
    import csv
    csv.field_size_limit(10 ** 8)
    path = os.path.join(CACHE, "openaccess", "MetObjects.csv")
    if not os.path.exists(path):
        sys.exit(f"Download https://media.githubusercontent.com/media/metmuseum/openaccess/master/MetObjects.csv to {path} first.")
    pools = {k: [] for k in CSV_PREFILTERS}
    for o in csv.DictReader(open(path, encoding="utf-8-sig")):
        if o["Is Public Domain"] != "True":
            continue
        try:
            b = int(o["Object Begin Date"])
        except ValueError:
            continue
        m = o["Medium"].lower()
        for k, f in CSV_PREFILTERS.items():
            if f(o, m, b):
                pools[k].append(o["Object ID"])
    have = {str(o["objectID"]) for o in records()}
    out = open(os.path.join(CACHE, "records_dp_cands.jsonl"), "a")
    for k, ids in pools.items():
        random.Random(k).shuffle(ids)
        ids = [i for i in ids[:per_rule] if i not in have]
        print(f"{k}: {len(pools[k])} in the CSV, fetching {len(ids)}", flush=True)
        for i in ids:
            try:
                o = json.loads(get(API + f"objects/{i}"))
            except Exception:
                continue
            if o.get("isPublicDomain") and o.get("primaryImageSmall"):
                out.write(json.dumps({k2: o.get(k2) for k2 in FIELDS + ("primaryImage", "artistDisplayName", "dimensions", "title", "objectDate")}) + "\n")
            time.sleep(0.03)


def has(text, *words):
    t = (text or "").lower()
    return any(w in t for w in words)


def date_in(o, a, b):
    return o.get("objectBeginDate") is not None and a <= o["objectBeginDate"] <= b


def painting(o):
    return has(o.get("classification"), "painting") or has(o.get("medium"), "oil on", "tempera on", "on canvas", "on wood", "on panel")


def eu(o):
    return o.get("department") == "European Paintings"


# current -> (description of the rule, predicate)
RULES = {
    "byzantine-icon": ("Medieval Art and European Paintings: Byzantine, Greek, Cretan or Russian painted works (tempera, icons), 1200-1800",
                       lambda o: has(o.get("culture"), "byzantine", "greek", "cretan", "russian") and painting(o) and date_in(o, 1200, 1800)),
    "renaissance": ("European Paintings 1400-1560 by Italian, Netherlandish, Flemish or German artists",
                    lambda o: eu(o) and date_in(o, 1400, 1560) and has(o.get("artistNationality"), "italian", "netherlandish", "flemish", "german")),
    "baroque": ("European Paintings 1600-1700 by Italian, Spanish, Flemish or French artists",
                lambda o: eu(o) and date_in(o, 1600, 1700) and has(o.get("artistNationality"), "italian", "spanish", "flemish", "french")),
    "dutch-golden-age": ("European Paintings 1600-1690 by Dutch artists",
                         lambda o: eu(o) and date_in(o, 1600, 1690) and has(o.get("artistNationality"), "dutch")),
    "romanticism": ("European and American paintings 1790-1850 by British, German, French or American artists",
                    lambda o: painting(o) and date_in(o, 1790, 1850) and has(o.get("artistNationality"), "british", "english", "german", "french", "american")),
    "realism": ("European Paintings 1840-1880 by French artists (Realism and the Barbizon generation)",
                lambda o: eu(o) and date_in(o, 1840, 1880) and has(o.get("artistNationality"), "french")),
    "impressionism": ("European Paintings 1865-1895 by French artists, oil",
                      lambda o: eu(o) and date_in(o, 1865, 1895) and has(o.get("artistNationality"), "french") and has(o.get("medium"), "oil")),
    "post-impressionism": ("European Paintings 1885-1905 by French or Dutch artists",
                           lambda o: eu(o) and date_in(o, 1885, 1905) and has(o.get("artistNationality"), "french", "dutch")),
    "fauvism": ("European Paintings 1904-1910 by French artists (few public-domain works; weak)",
                lambda o: eu(o) and date_in(o, 1904, 1910) and has(o.get("artistNationality"), "french")),
    "expressionism": ("Paintings 1905-1925 by German or Austrian artists (few public-domain works; weak)",
                      lambda o: painting(o) and date_in(o, 1905, 1925) and has(o.get("artistNationality"), "german", "austrian")),
    "ukiyo-e": ("Asian Art: Japanese woodblock prints, 1700-1868",
                lambda o: o.get("department") == "Asian Art" and has(o.get("culture"), "japan") and has(o.get("classification"), "print") and date_in(o, 1700, 1868)),
    "pen-and-ink-illustration": ("Drawings in pen and ink without wash, colour, chalk or charcoal, 1875-1920 (any department but Modern and "
                                 "Contemporary Art; trade designs titled 'Design for' or numbered '#' excluded): the illustrators' originals",
                                 lambda o: has(o.get("classification"), "drawing") and date_in(o, 1875, 1920) and has(o.get("medium"), "pen")
                                 and has(o.get("medium"), "ink") and not has(o.get("medium"), "watercolo", "gouache", "wash", "chalk", "pastel", "crayon", "charcoal", "oil")
                                 and o.get("department") != "Modern and Contemporary Art" and not re.search(r"^design for|#\s?\d", (o.get("title") or "").lower())),
    "etching-engraving": ("Drawings and Prints: intaglio prints whose medium begins 'Engraving' (1480-1900) or 'Etching' (1500-1925), "
                          "black and white (no wood engraving, stipple, mezzotint, aquatint, crayon manner, roulette, soft-ground, colour or hand colouring)",
                          lambda o: has(o.get("classification"), "print") and o.get("department") == "Drawings and Prints"
                          and ((o.get("medium") or "").lower().startswith("engraving") and date_in(o, 1480, 1900)
                               or (o.get("medium") or "").lower().startswith("etching") and date_in(o, 1500, 1925))
                          and not has(o.get("medium"), "wood", "stipple", "mezzotint", "aquatint", "crayon", "roulette", "soft", "color", "colour", "hand", "letterpress", "photo")),
    "east-asian-ink": ("Asian Art: Chinese and Japanese paintings in ink, 1300-1900",
                       lambda o: o.get("department") == "Asian Art" and has(o.get("culture"), "china", "japan") and has(o.get("classification"), "painting")
                       and has(o.get("medium"), "ink") and date_in(o, 1300, 1900)),
}


def measure_style(sid, n, recs):
    desc, rule = RULES[sid]
    pool = [o for o in recs if rule(o)]
    random.Random(sid).shuffle(pool)
    ms, ids = [], []
    for o in pool:
        if len(ms) >= n:
            break
        try:
            img = Image.open(io.BytesIO(get(o["primaryImageSmall"])))
            if min(img.size) < 200:
                continue
            ms.append(eyes.measure(img))
            ids.append(o["objectID"])
        except Exception as e:
            print(f"  skip {o['objectID']}: {e}", file=sys.stderr)
        time.sleep(0.1)
    if len(ms) < 5:
        return None, len(pool)
    t = {"_n": len(ms), "_pool": len(pool), "_source": "The Met Open Access (CC0), public-domain works",
         "_rule": desc, "_met_object_ids": ids, "_measured": time.strftime("%Y-%m-%d")}
    for k in ms[0]:
        v = np.array([m[k] for m in ms], float)
        v = v[np.isfinite(v)]
        t[k] = {"mean": round(float(v.mean()), 4), "sd": round(float(v.std()), 4)}
    return t, len(pool)


if __name__ == "__main__":
    argv = sys.argv[1:]

    def opt(name, default):
        if name in argv:
            i = argv.index(name); v = argv[i + 1]; del argv[i:i + 2]; return int(v)
        return default
    if not argv or argv[0] not in ("index", "index-csv", "measure"):
        sys.exit(__doc__)
    if argv[0] == "index":
        index(opt("--limit", 4000)); sys.exit()
    if argv[0] == "index-csv":
        index_csv(opt("--per-rule", 250)); sys.exit()
    parts = "--parts" in argv
    if parts:
        argv.remove("--parts")
    n = opt("--n", 60)
    recs = records()
    if not recs:
        sys.exit("No records cached yet: run `index` first.")
    out = os.path.join(ROOT, "studio", "targets.json")
    targets = json.load(open(out)) if os.path.exists(out) else {}
    targets["_about"] = "Measured style targets (statistics only) from public-domain works in The Met's Open Access collection; see tools/measure_targets.py and docs/MANUAL.md, 'Report'."
    for sid in (argv[1:] or list(RULES)):
        print(f"{sid} ...", flush=True)
        t, pool = measure_style(sid, n, recs)
        if t is None:
            print(f"  only {pool} matching works: left unmeasured")
            continue
        if parts:
            pd = os.path.join(ROOT, "studio", "targets.parts")
            os.makedirs(pd, exist_ok=True)
            pp = os.path.join(pd, f"{sid}.json")
            json.dump({sid: t}, open(pp + ".tmp", "w"), indent=1)
            os.replace(pp + ".tmp", pp)
            print(f"  {t['_n']} of {pool} -> {pp}", flush=True)
            continue
        targets[sid] = t
        print(f"  {t['_n']} of {pool}: key {t['value_mean']['mean']:.0f}, spread {t['value_spread']['mean']:.0f}, chroma {t['chroma_mean']['mean']:.0f}, "
              f"edges {t['edge_density']['mean']:.2f}, hard {t['hard_edge_share']['mean']:.2f}, slope {t['spectral_slope']['mean']:.2f}", flush=True)
        tmp = out + ".tmp"
        json.dump(targets, open(tmp, "w"), indent=1)
        os.replace(tmp, out)
    if not parts:
        print(out)
