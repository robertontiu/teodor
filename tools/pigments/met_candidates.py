import json, re, sys, time, urllib.request, concurrent.futures as cf
API = "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
UA = "TeodorResearch/1.0 (https://github.com/robertontiu/teodor)"
F = ("objectID","isPublicDomain","primaryImage","department","classification","title","artistDisplayName","objectDate","culture","medium","dimensions","objectURL")
def get(i):
    for a in range(4):
        try:
            o = json.loads(urllib.request.urlopen(urllib.request.Request(API + str(i), headers={"User-Agent": UA}), timeout=60).read())
            return {k: o.get(k) for k in F}
        except Exception as e:
            time.sleep(2 + 2 * a)
    return None
recs = []
for f in ["" + os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data")) + "/met/dep9.jsonl", "" + os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data")) + "/met/dep16.jsonl", "/root/.cache/teodor/met/records.jsonl"]:
    try: recs += [json.loads(l) for l in open(f)]
    except FileNotFoundError: pass
pat = {
 "oil": r"^oil on (canvas|wood|panel)$",
 "tempera_gold": r"^tempera (and gold )?on wood, gold ground$|^tempera and gold on wood$",
 "watercolour": r"^watercolou?r(,? over graphite| on (white |wove )?paper|$)",
 "gouache": r"^gouache|watercolor and gouache|opaque watercolor",
 "ink_brush_asian": r"^ink on (paper|silk)$|^ink and (light )?color on (paper|silk)$",
 "charcoal": r"charcoal",
 "graphite": r"^graphite( on .*)?$",
 "pastel": r"^pastel",
 "ukiyoe": r"^(polychrome )?woodblock print; ink and color on paper$",
}
extra = [int(x) for x in sys.argv[1:]]
want = {}
for k, p in pat.items():
    m = [r["objectID"] for r in recs if re.search(p, (r.get("medium") or "").strip().lower())]
    want[k] = m[:60]
ids = sorted(set(i for v in want.values() for i in v) | set(extra))
print(len(ids), {k: len(v) for k, v in want.items()}, flush=True)
with cf.ThreadPoolExecutor(6) as ex:
    full = {i: r for i, r in zip(ids, ex.map(get, ids)) if r}
json.dump({"want": want, "records": full}, open("" + os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data")) + "/met/candidates.json", "w"))
for k, v in want.items():
    print("==", k)
    for i in v[:60]:
        r = full.get(i)
        if r and r["primaryImage"]:
            print(f"  {i} | {(r['artistDisplayName'] or '')[:28]} | {r['title'][:40]} | {r['objectDate']} | {r['medium'][:50]} | {r['dimensions'][:40]}")
