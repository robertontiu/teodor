"""Measured style targets: what each current measures like, from public-domain works in the Art
Institute of Chicago's open-access collection (https://api.artic.edu; images CC0 via its IIIF server).
Spectre does the same for music (tools/refcurve.py: era target curves from catalogue data).

For every current in studio/styles.json that has a query below, the tool downloads up to N images
(843 px wide), measures each with studio/v8/eyes.py, deletes the image, and writes the mean and
standard deviation of every measure to studio/targets.json, with provenance: the query, the number of
works and their AIC ids. No images are kept; only statistics are versioned.

  python3 tools/measure_targets.py [style ...] [--n 60]

Queries use the AIC's own style labels where it has them, and otherwise place, date and classification
as a proxy (marked "proxy" in the provenance). Currents whose works are still in copyright
(surrealism, abstract-expressionism) have no public-domain sample and are left unmeasured.
"""
import io, json, os, sys, time, urllib.request
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "studio", "v8"))
import eyes  # noqa: E402

API = "https://api.artic.edu/api/v1/artworks/search"
IIIF = "https://www.artic.edu/iiif/2/{}/full/843,/0/default.jpg"
UA = "Mozilla/5.0 (compatible; TeodorResearch/1.0; +https://github.com/robertontiu/teodor)"

PAINT = {"terms": {"classification_title.keyword": ["painting", "oil on canvas"]}}


def rng(a, b):
    return {"range": {"date_start": {"gte": a, "lte": b}}}


def place(*p):
    return {"terms": {"place_of_origin.keyword": list(p)}}


def style(*s):
    return {"terms": {"style_title.keyword": list(s)}}


def cls(*c):
    return {"terms": {"classification_title.keyword": list(c)}}


QUERIES = {
    "byzantine-icon": {"must": [style("byzantine"), cls("painting", "icon")], "kind": "label"},
    "renaissance": {"must": [style("Renaissance", "15th century", "sixteenth century", "16th Century"), PAINT, rng(1400, 1560)], "kind": "label+date"},
    "baroque": {"must": [PAINT, rng(1600, 1700), place("Italy", "Spain", "Flanders", "France")], "kind": "proxy: Italian, Spanish, Flemish, French paintings 1600-1700"},
    "dutch-golden-age": {"must": [PAINT, rng(1600, 1690), place("Netherlands", "Holland", "Haarlem", "Amsterdam", "Utrecht", "Leiden", "Delft")], "kind": "proxy: Dutch paintings 1600-1690"},
    "romanticism": {"must": [PAINT, rng(1790, 1850), place("England", "Germany", "France", "United States")], "kind": "proxy: English, German, French, American paintings 1790-1850"},
    "realism": {"must": [style("Realism"), PAINT], "kind": "label"},
    "impressionism": {"must": [style("Impressionism"), PAINT], "kind": "label"},
    "post-impressionism": {"must": [style("Post-Impressionism"), PAINT], "kind": "label"},
    "fauvism": {"must": [PAINT, rng(1904, 1910), place("France")], "kind": "proxy: French paintings 1904-1910"},
    "expressionism": {"must": [PAINT, rng(1905, 1925), place("Germany", "Austria")], "kind": "proxy: German and Austrian paintings 1905-1925"},
    "cubism": {"must": [PAINT, rng(1908, 1920), place("France", "Spain")], "kind": "proxy: French and Spanish paintings 1908-1920 (few public-domain works; weak)"},
    "ukiyo-e": {"must": [cls("print", "woodblock print", "color woodblock print"), place("Japan"), rng(1700, 1868)], "kind": "proxy: Japanese prints 1700-1868"},
    "east-asian-ink": {"must": [cls("painting", "hanging scroll", "handscroll", "album leaf"), place("China", "Japan"), rng(1300, 1900)], "kind": "proxy: Chinese and Japanese paintings 1300-1900"},
}


def fetch(url, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            return urllib.request.urlopen(req, timeout=60).read()
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(2 + 3 * attempt)


def find(q, n):
    body = {"query": {"bool": {"must": [{"term": {"is_public_domain": True}}, {"exists": {"field": "image_id"}}] + q["must"]}},
            "fields": ["id", "image_id", "date_start", "classification_title", "style_title"], "limit": min(100, n * 2)}
    d = json.loads(fetch(API, json.dumps(body).encode()))
    return [x for x in d["data"] if x.get("image_id")][:n]


def measure_style(sid, n):
    q = QUERIES[sid]
    works = find(q, n)
    ms, ids = [], []
    for w in works:
        try:
            img = Image.open(io.BytesIO(fetch(IIIF.format(w["image_id"]))))
            ms.append(eyes.measure(img))
            ids.append(w["id"])
        except Exception as e:
            print(f"  skip {w['id']}: {e}", file=sys.stderr)
        time.sleep(0.3)
    if len(ms) < 5:
        return None
    t = {"_n": len(ms), "_source": "Art Institute of Chicago open access (api.artic.edu), public-domain works",
         "_query": q["kind"], "_aic_ids": ids, "_measured": time.strftime("%Y-%m-%d")}
    for k in ms[0]:
        v = np.array([m[k] for m in ms], float)
        v = v[np.isfinite(v)]
        t[k] = {"mean": round(float(v.mean()), 4), "sd": round(float(v.std()), 4)}
    return t


if __name__ == "__main__":
    argv = sys.argv[1:]
    n = 60
    if "--n" in argv:
        i = argv.index("--n"); n = int(argv[i + 1]); del argv[i:i + 2]
    args = argv
    out = os.path.join(ROOT, "studio", "targets.json")
    targets = json.load(open(out)) if os.path.exists(out) else {"_about": __doc__.strip().split("\n\n")[0]}
    for sid in (args or list(QUERIES)):
        print(f"{sid} ...", flush=True)
        t = measure_style(sid, n)
        if t is None:
            print(f"  too few works, left unmeasured")
            continue
        targets[sid] = t
        print(f"  {t['_n']} works: key {t['value_mean']['mean']:.0f}±{t['value_spread']['mean']:.0f}, chroma {t['chroma_mean']['mean']:.0f}, "
              f"edges {t['edge_density']['mean']:.2f}, slope {t['spectral_slope']['mean']:.2f}")
        tmp = out + ".tmp"
        json.dump(targets, open(tmp, "w"), indent=1)
        os.replace(tmp, out)
    print(out)
