"""Measured style targets: what each current measures like, from public-domain works in The Met's
open-access collection (Open Access API, collectionapi.metmuseum.org; images and data CC0) and the
Cleveland Museum of Art's (Open Access API, openaccess-api.clevelandart.org; CC0 works only).
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
  python3 tools/measure_targets.py index-cma [style ...]        # Cleveland Museum of Art candidates (CMA_QUERIES)
  python3 tools/measure_targets.py measure [style ...] [--n 60] [--parts]
  python3 tools/measure_targets.py closeup add <photo> --id ... --source ... --licence ... (--px-per-mm | --ipd-px)
                                                   [--face/--skin/--hair x,y,w,h]   # a close-up ruler (see "close-up rulers")

Department 9 (Drawings and Prints, ~186,000 objects) is too large to sample at random for rare groups such as
pen-and-ink illustration drawings, so `index-csv` reads The Met's Open Access CSV (MetObjects.csv from
github.com/metmuseum/openaccess, CC0; downloaded once to ~/.cache/teodor/met/openaccess/), applies a coarse
pre-filter (CSV_PREFILTERS) and fetches the API records of up to --per-rule matches each into
~/.cache/teodor/met/records_dp_cands.jsonl. The RULES below then select from all cached records as before.
`--parts` writes each result to studio/targets.parts/<style>.json instead of studio/targets.json (for merging).

The Cleveland Museum of Art (CMA) Open Access API is queried with `cc0=1&has_image=1` (only works the museum
releases as CC0, with an image) and the queries in CMA_QUERIES (object type, creation-date window, and a keyword
for rare groups). `index-cma` stores each record, mapped to the Met's field names (artist nationality parsed
from the creator line "Name (German, 1880-1938)", culture, technique as medium, the "web" image), in
~/.cache/teodor/cma/records.jsonl. The same RULES then select from the Met and CMA records together; a
result lists the object ids of each museum and every work's collection URL (`_works`).
The Art Institute of Chicago is not used: its image server refuses the workspace's requests, and we don't work
around that.

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
CMA_API = "https://openaccess-api.clevelandart.org/api/artworks/"
CMA_CACHE = os.path.expanduser("~/.cache/teodor/cma")
CMA_FIELDS = ("id,accession_number,title,creation_date,creation_date_earliest,creation_date_latest,culture,technique,"
              "type,department,creators,images,share_license_status,url")
UA = "TeodorResearch/1.0 (https://github.com/robertontiu/teodor)"
CACHE = os.path.expanduser("~/.cache/teodor/met")
DEPARTMENTS = {11: "European Paintings", 6: "Asian Art", 17: "Medieval Art", 1: "The American Wing"}
FIELDS = ("objectID", "isPublicDomain", "primaryImageSmall", "department", "classification",
          "objectBeginDate", "objectEndDate", "artistNationality", "culture", "medium")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(5):
        try:
            return urllib.request.urlopen(req, timeout=90).read()
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 + 3 * attempt)


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
    """Every cached record: The Met's (records*.jsonl in CACHE) and Cleveland's (CMA_CACHE/records.jsonl)."""
    out, seen = [], set()
    files = [(CACHE, fn) for fn in (["records.jsonl"] + sorted(f for f in os.listdir(CACHE) if f.startswith("records_dp") and f.endswith(".jsonl"))
                                    if os.path.isdir(CACHE) else [])]
    files += [(CMA_CACHE, "records.jsonl")]
    byid = {}
    for d, fn in files:
        if not os.path.exists(os.path.join(d, fn)):
            continue
        for l in open(os.path.join(d, fn)):
            o = json.loads(l)
            k = o.get("objectID")
            if k in byid:      # the same object fetched twice: fill in fields the first copy lacks (e.g. dimensions)
                byid[k].update({f: v for f, v in o.items() if v not in (None, "") and byid[k].get(f) in (None, "")})
                continue
            byid[k] = o; out.append(o)
    return out


def source(o):
    return "cma" if str(o.get("objectID", "")).startswith("cma:") else "met"


def cma_record(o):
    """A CMA Open Access record mapped to the Met's field names (only the fields the rules read)."""
    cr = [c for c in (o.get("creators") or []) if c.get("description")]
    desc = cr[0]["description"] if cr else ""
    m = re.search(r"\(([^()]*?)(?:,\s*(?:active|born|died|c\.|ca\.|\d)[^()]*)?\)\s*$", desc)
    nationality = (m.group(1).split(",")[0].strip() if m else "")
    img = ((o.get("images") or {}).get("web") or {}).get("url")
    return {"objectID": f"cma:{o['id']}", "isPublicDomain": o.get("share_license_status") == "CC0", "primaryImageSmall": img,
            "department": o.get("department"), "classification": o.get("type"),
            "objectBeginDate": o.get("creation_date_earliest"), "objectEndDate": o.get("creation_date_latest"),
            "artistNationality": nationality, "culture": "; ".join(o.get("culture") or []), "medium": o.get("technique"),
            "title": o.get("title"), "artistDisplayName": desc, "objectDate": o.get("creation_date"),
            "accessionNumber": o.get("accession_number"), "objectURL": o.get("url")}


# current -> CMA API queries (cc0=1 and has_image=1 are always added); the RULES below decide what is used
CMA_QUERIES = {
    "byzantine-icon": [dict(type="Painting", created_after=1100, created_before=1850, q=w)
                       for w in ("icon", "Byzantine", "Cretan", "Greece", "Russia", "Balkan", "Bulgaria", "Serbia", "Romania")],
    "fauvism": [dict(type=t, created_after=1904, created_before=1910) for t in ("Painting", "Drawing", "Print")],
    "expressionism": [dict(type=t, created_after=a, created_before=b) for t in ("Painting", "Drawing", "Print")
                      for a, b in ((1905, 1912), (1913, 1918), (1919, 1925))],
}


def index_cma(styles):
    os.makedirs(CMA_CACHE, exist_ok=True)
    path = os.path.join(CMA_CACHE, "records.jsonl")
    have = {json.loads(l)["objectID"] for l in open(path)} if os.path.exists(path) else set()
    import urllib.parse
    with open(path, "a") as f:
        for sid in styles:
            for q in CMA_QUERIES.get(sid, []):
                skip, new = 0, 0
                while True:
                    u = CMA_API + "?" + urllib.parse.urlencode(dict(q, cc0=1, has_image=1, limit=100, skip=skip, fields=CMA_FIELDS))
                    try:
                        d = json.loads(get(u))
                    except Exception as e:
                        print(f"  {sid} {q} skip={skip}: {e}", file=sys.stderr); break
                    for o in d.get("data", []):
                        r = cma_record(o)
                        if r["objectID"] in have or not r["isPublicDomain"] or not r["primaryImageSmall"]:
                            continue
                        have.add(r["objectID"]); new += 1
                        f.write(json.dumps(r) + "\n")
                    f.flush()
                    skip += 100
                    if skip >= d.get("info", {}).get("total", 0):
                        break
                    time.sleep(0.2)
                print(f"{sid} {q}: {new} new", flush=True)


import re  # noqa: E402

# coarse pre-filters on MetObjects.csv rows (index-csv); the RULES decide
CSV_PREFILTERS = {
    "pen-and-ink-illustration": lambda o, m, b: o["Classification"] == "Drawings" and 1875 <= b <= 1920 and "pen" in m and "ink" in m,
    "etching-engraving-engraving": lambda o, m, b: o["Department"] == "Drawings and Prints" and o["Classification"] == "Prints" and 1480 <= b <= 1900 and m.startswith("engraving"),
    "etching-engraving-etching": lambda o, m, b: o["Department"] == "Drawings and Prints" and o["Classification"] == "Prints" and 1500 <= b <= 1925 and m.startswith("etching"),
    "byzantine-icon": lambda o, m, b: 1100 <= b <= 1850 and "tempera" in m and has(o["Culture"] + " " + o["Artist Nationality"], *ORTHODOX),
    "expressionism": lambda o, m, b: 1905 <= b <= 1925 and nat({"artistNationality": o["Artist Nationality"]}) in ("german", "austrian")
                                     and o["Classification"] in ("Paintings", "Drawings", "Prints"),
    "fauvism": lambda o, m, b: 1904 <= b <= 1910 and nat({"artistNationality": o["Artist Nationality"]}) == "french"
                               and o["Classification"] in ("Paintings", "Drawings", "Prints"),
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


def nat(o):
    """The artist's first-named nationality, lower case ("German|American" -> "german"; Cleveland's
    "American, born Germany" -> "american")."""
    return re.split(r"[|,;]", (o.get("artistNationality") or "").strip().lower() + "|")[0].strip()


ORTHODOX = ("byzant", "greek", "greece", "cret", "russia", "balkan", "bulgaria", "serbia", "romania", "macedonia", "cyprus", "novgorod",
            "moscow", "pskov", "yaroslavl")
COLOUR_MEDIA = ("oil", "tempera", "watercolo", "gouache", "pastel", "color", "colour", "red chalk", "colored", "coloured")


def small_sheet(o, cm=16):
    """True when the record's dimensions give a sheet or image under `cm` both ways (postcard format, 14 x 9 cm)."""
    m = re.search(r"\(([\d.]+)\s*[x×]\s*([\d.]+)\s*cm\)", o.get("dimensions") or "")
    return bool(m) and max(float(m.group(1)), float(m.group(2))) < cm


# current -> (description of the rule, predicate)
RULES = {
    "byzantine-icon": ("Paintings (Met: any department; Cleveland: type Painting) in tempera (egg tempera, tempera and gold) on wood, panel or "
                       "linen, begun 1100-1850, whose culture or artist nationality is Byzantine, Greek/Cretan, Russian or Balkan Orthodox "
                       "(Byzant-, Greek, Greece, Cret-, Russia-, Balkan, Bulgaria, Serbia, Romania, Macedonia, Cyprus, Novgorod, Moscow, Pskov, "
                       "Yaroslavl); oil paintings (e.g. El Greco's Spanish work), mosaics, metalwork, textiles and manuscripts on parchment excluded",
                       lambda o: has((o.get("culture") or "") + " " + (o.get("artistNationality") or ""), *ORTHODOX) and painting(o)
                       and date_in(o, 1100, 1850) and has(o.get("medium"), "tempera") and has(o.get("medium"), "wood", "panel", "linen")
                       and not has(o.get("medium"), "oil", "mosaic", "parchment", "vellum", "silver", "enamel")),
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
    "fauvism": ("Paintings, drawings and prints in colour begun 1904-1910 by French artists (Met and Cleveland). No public-domain "
                "work by a member of the 1905 Salon d'Automne group is released by either museum, so this proxy measures their "
                "contemporaries, not the Fauves: do not use it as a Fauvist target",
                lambda o: date_in(o, 1904, 1910) and nat(o) == "french" and has(o.get("classification"), "painting", "drawing", "print")
                and has(o.get("medium"), *COLOUR_MEDIA) and not small_sheet(o)),
    "expressionism": ("Paintings, drawings and prints in colour (oil, tempera, watercolour, gouache, pastel, coloured chalk or crayon, "
                      "colour prints) begun 1905-1925 by artists whose first-named nationality is German or Austrian (Met and "
                      "Cleveland; postcards and other sheets under 16 cm, Met prints without a catalogued size, ornament and design "
                      "drawings excluded, which removes the Wiener Werkstaette postcards); black-and-white prints and drawings (black chalk, crayon, charcoal, woodcut) are "
                      "excluded because they would set the colour measures, not the current",
                      lambda o: date_in(o, 1905, 1925) and nat(o) in ("german", "austrian")
                      and has(o.get("classification"), "painting", "drawing", "print")
                      and not has(o.get("classification"), "ornament", "postcard", "design")
                      and not re.search(r"^design for|postcard", (o.get("title") or "").lower())
                      and has(o.get("medium"), *COLOUR_MEDIA) and not small_sheet(o)
                      and not (source(o) == "met" and has(o.get("classification"), "print") and not o.get("dimensions"))),
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


def greyscale(img):
    """True for a black-and-white photograph (a greyscale image, or RGB with no pixel more than 2/255 off grey).
    Many older museum photographs of paintings are black and white; measuring them would put zero chroma into a
    current's colour targets. (Added 2026-11-26; targets measured before then did not apply this check.)"""
    if img.mode in ("1", "L", "LA", "I", "I;16", "F"):
        return True
    a = np.asarray(img.convert("RGB").resize((128, 128)), np.int16)
    return int((a.max(2) - a.min(2)).max()) <= 2


def measure_style(sid, n, recs):
    desc, rule = RULES[sid]
    # Cleveland's cache holds only what CMA_QUERIES fetched for the currents listed there; for any other current a
    # Cleveland record matching the rule is an accident of those queries, not a sample of Cleveland's holdings
    # (2026-11-26: 34 Cleveland drawings, 31 of them one artist's 1914 brush-and-ink series, had entered the
    # pen-and-ink pool through the Expressionism and Fauvism queries). So Cleveland records count only there.
    pool = [o for o in recs if rule(o) and (source(o) == "met" or sid in CMA_QUERIES)]
    random.Random(sid).shuffle(pool)
    ms, used, grey = [], [], []
    for o in pool:
        if len(ms) >= n:
            break
        try:
            img = Image.open(io.BytesIO(get(o["primaryImageSmall"])))
            if min(img.size) < 200:
                continue
            if greyscale(img):      # a black-and-white photograph of the work: its colour measures would be the camera's
                grey.append(o["objectID"])
                continue
            ms.append(eyes.measure(img))
            used.append(o)
        except Exception as e:
            print(f"  skip {o['objectID']}: {e}", file=sys.stderr)
        time.sleep(0.1)
    if len(ms) < 5:
        return None, len(pool)
    met = [o["objectID"] for o in used if source(o) == "met"]
    cma = [o for o in used if source(o) == "cma"]
    src = []
    if met:
        src.append("The Met Open Access (CC0), public-domain works")
    if cma:
        src.append("Cleveland Museum of Art Open Access (CC0 works)")
    t = {"_n": len(ms), "_pool": len(pool), "_source": "; ".join(src), "_rule": desc, "_met_object_ids": met,
         "_measured": time.strftime("%Y-%m-%d")}
    if grey:
        t["_skipped_greyscale_photographs"] = grey
    if cma:
        t["_cma_object_ids"] = [int(o["objectID"][4:]) for o in cma]
        t["_pool_by_source"] = {"met": sum(source(o) == "met" for o in pool), "cma": sum(source(o) == "cma" for o in pool)}
        t["_works"] = [{"source": source(o), "id": o["objectID"] if source(o) == "met" else int(o["objectID"][4:]),
                        "accession": o.get("accessionNumber"), "date": o.get("objectBeginDate"), "medium": o.get("medium"),
                        "url": (o.get("objectURL") or f"https://www.metmuseum.org/art/collection/search/{o['objectID']}"),
                        "image": o.get("primaryImageSmall")} for o in used]
    for k in ms[0]:
        v = np.array([m[k] for m in ms], float)
        v = v[np.isfinite(v)]
        t[k] = {"mean": round(float(v.mean()), 4), "sd": round(float(v.std()), 4)}
    return t, len(pool)


# ---------------------------------------------------------------- close-up rulers (fine measures, subject-mm)
# A hyperrealist draws from one high-resolution close-up, so a close-up style needs a second ruler measured at the
# photograph's own resolution and in millimetres of the subject (docs/research/hyperrealism-gaps.md, G10):
#   python3 tools/measure_targets.py closeup add <photo> --style graphite-hyperrealism --id <id> --source <url>
#       --licence "<licence and its evidence>" (--px-per-mm P | --ipd-px D [--ipd-mm 64])
#       [--face x,y,w,h] [--skin x,y,w,h] [--hair x,y,w,h] [--sheet-px-per-mm 5] [--note "..."]
#   python3 tools/measure_targets.py closeup list|drop <id> [--style ...]
# Only openly licensed photographs (public domain or CC0), and never a photograph's pixels: each `add` measures the
# photograph (eyes.measure_fine), stores the statistics with its provenance in
# studio/targets.parts/<style>-closeup.json, rebuilds the bounds from every photograph stored, and merges the entry
# into studio/targets.json. Delete the photograph afterwards. A photograph of a real person is measured, never shown,
# published or used as a reference (AGENTS.md rule 5).
# Whole-frame keys are measured as if the photograph were printed at --sheet-px-per-mm (the studio's 5 px/mm sheet):
# that is the drawing that copies it. Subject keys (face, skin, hair) use the subject's own px per mm: give it, or
# the pupil distance in px (adult mean interpupillary distance about 64 mm: Dodgson 2004, "Variation and extrema of
# human interpupillary distance", 61.7-64.0 mm means by sex).
# Bounds from the photographs' mean (BOUND_RULES): judgements from the gaps doc's acceptance tests, the same rule
# however many photographs there are; sd and n are stored beside them so the rule can be revisited at n >= 10.
BOUND_RULES = {
    "value_below20": ("min", lambda m: 0.6 * m),
    "value_below30": ("min", lambda m: 0.6 * m),
    "value_p1": ("max", lambda m: m + 10.0),
    "value_p5": ("max", lambda m: m + 12.0),
    "value_p95": ("min", lambda m: m - 10.0),
    "flat_midtone_share": ("max", lambda m: max(0.05, 2.0 * m)),
    "edge_p10_mm": ("max", lambda m: max(0.3, 1.5 * m)),
    "face_specular_count_30": ("min", lambda m: max(1, math.ceil(0.75 * m))),
    "face_value_p1": ("max", lambda m: m + 10.0),
    "face_value_below20": ("min", lambda m: 0.3 * m),
    "hair_coherence": ("min", lambda m: min(0.5, m - 0.05)),
}
BAND_RULES = {"face_band_rms": (0.65, 1.35), "skin_band_rms": (0.65, 1.35), "hair_band_rms": (0.7, None)}
import math  # noqa: E402


def _box(s):
    return tuple(int(v) for v in s.split(",")) if s else None


def closeup_measure(path, ppm_subject, sheet_ppm=5.0, face=None, skin=None, hair=None):
    L, f = eyes.lightness(path)
    if f != 1:
        sys.exit("closeup: the photograph is larger than eyes.FINE_MAX_PX; crop it to the subject first")
    m = {}
    whole = eyes.measure_fine(L, sheet_ppm)
    for k in ("value_below20", "value_below30", "value_p1", "value_p5", "value_p95", "flat_midtone_share", "edge_p10_mm"):
        m[k] = whole.get(k)
    m["sheet_band_rms"] = whole["band_rms"]

    def crop(b):
        x, y, w, h = b
        return L[y:y + h, x:x + w]
    if face:
        fm = eyes.measure_fine(crop(face), ppm_subject)
        m["face_band_rms"] = fm["band_rms"]
        m["face_specular_count_30"] = fm["specular_count_30"]
        m["face_specular_max"] = fm["specular_max_prominence"]
        m["face_value_p1"] = fm["value_p1"]
        m["face_value_below20"] = fm["value_below20"]
    if skin:
        m["skin_band_rms"] = eyes.band_energy(crop(skin), ppm_subject)
        m["skin_band_rms"] = {str(k): (round(v, 3) if v is not None else None) for k, v in m["skin_band_rms"].items()}
    if hair:
        hb = eyes.band_energy(crop(hair), ppm_subject)
        m["hair_band_rms"] = {str(k): (round(v, 3) if v is not None else None) for k, v in hb.items()}
        m["hair_coherence"] = round(eyes.coherence(crop(hair), ppm_subject, sigma_mm=0.5), 4)
    return m


def closeup_build(photos):
    """The ruler from every stored photograph: mean, sd, n and the bound per key."""
    t = {}
    for k, (kind, rule) in BOUND_RULES.items():
        v = np.array([p["measures"][k] for p in photos if p["measures"].get(k) is not None], float)
        if len(v):
            t[k] = {"mean": round(float(v.mean()), 4), "sd": round(float(v.std()), 4), "n": int(len(v)), kind: round(float(rule(v.mean())), 4)}
    for k, (lo, hi) in BAND_RULES.items():
        rows = [p["measures"][k] for p in photos if p["measures"].get(k)]
        if not rows:
            continue
        t[k] = {}
        for s in rows[0]:
            v = np.array([r[s] for r in rows if r.get(s) is not None], float)
            if not len(v):
                continue
            mu = float(v.mean())
            e = {"mean": round(mu, 4), "sd": round(float(v.std()), 4), "n": int(len(v)), "min": round(lo * mu, 4)}
            if hi:
                e["max"] = round(hi * mu, 4)
            t[k][s] = e
    return t


def closeup(argv):
    def opt(name, default=None):
        if name in argv:
            i = argv.index(name); v = argv[i + 1]; del argv[i:i + 2]; return v
        return default
    style = opt("--style", "graphite-hyperrealism")
    key = f"{style}-closeup"
    pp = os.path.join(ROOT, "studio", "targets.parts", f"{key}.json")
    cur = json.load(open(pp))[key] if os.path.exists(pp) else {"_photos": []}
    sub = argv[0] if argv else "list"
    if sub == "list":
        for p in cur["_photos"]:
            print(p["id"], p["source"], p.get("px_per_subject_mm"))
        return
    if sub == "drop":
        cur["_photos"] = [p for p in cur["_photos"] if p["id"] != argv[1]]
    elif sub == "add":
        path = argv[1]
        pid, src, lic = opt("--id"), opt("--source"), opt("--licence")
        if not (pid and src and lic):
            sys.exit("closeup add needs --id, --source and --licence (public domain or CC0 only, with its evidence)")
        ppm = opt("--px-per-mm")
        ipd = opt("--ipd-px")
        if ppm is None and ipd is None:
            sys.exit("closeup add needs the subject's scale: --px-per-mm or --ipd-px")
        ppm = float(ppm) if ppm else float(ipd) / float(opt("--ipd-mm", "64"))
        boxes = {k: _box(opt("--" + k)) for k in ("face", "skin", "hair")}
        meas = closeup_measure(path, ppm, float(opt("--sheet-px-per-mm", "5")), **boxes)
        cur["_photos"] = [p for p in cur["_photos"] if p["id"] != pid]
        cur["_photos"].append({"id": pid, "source": src, "licence": lic, "px_per_subject_mm": round(ppm, 3),
                               "boxes": {k: v for k, v in boxes.items() if v}, "note": opt("--note", ""),
                               "measured": time.strftime("%Y-%m-%d"), "measures": meas})
    else:
        sys.exit("closeup add|list|drop")
    n = len(cur["_photos"])
    entry = {"_n": n, "_provisional": n < 10,
             "_about": (f"Close-up ruler for {style}: fine measures (eyes.measure_fine) of openly licensed close-up photographs at "
                        "their own resolution, in subject-mm (face, skin, hair) and at the sheet's 5 px/mm (whole frame). "
                        "PROVISIONAL until at least 10 photographs: bounds come from BOUND_RULES in tools/measure_targets.py "
                        "(judgements from docs/research/hyperrealism-gaps.md), applied to the photographs' mean."),
             "_measured": time.strftime("%Y-%m-%d"), "_photos": cur["_photos"]}
    entry.update(closeup_build(cur["_photos"]))
    os.makedirs(os.path.dirname(pp), exist_ok=True)
    json.dump({key: entry}, open(pp + ".tmp", "w"), indent=1)
    os.replace(pp + ".tmp", pp)
    out = os.path.join(ROOT, "studio", "targets.json")
    targets = json.load(open(out)) if os.path.exists(out) else {}
    targets[key] = entry
    json.dump(targets, open(out + ".tmp", "w"), indent=1)
    os.replace(out + ".tmp", out)
    print(json.dumps({k: v for k, v in entry.items() if k != "_photos"}, indent=1))


if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv and argv[0] == "closeup":
        closeup(argv[1:]); sys.exit()

    def opt(name, default):
        if name in argv:
            i = argv.index(name); v = argv[i + 1]; del argv[i:i + 2]; return int(v)
        return default
    if not argv or argv[0] not in ("index", "index-csv", "index-cma", "measure"):
        sys.exit(__doc__)
    if argv[0] == "index-cma":
        index_cma(argv[1:] or list(CMA_QUERIES)); sys.exit()
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
    targets["_about"] = ("Measured style targets (statistics only) from public-domain works in The Met's and the Cleveland Museum of Art's "
                         "Open Access collections; see tools/measure_targets.py and docs/MANUAL.md, 'Report'.")
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
