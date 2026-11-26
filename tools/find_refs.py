"""Find openly licensed reference images for a painting, the way a painter gathers studies and photographs.

  python3 tools/find_refs.py <workdir> "portrait photograph woman laughing" --type photo --feature "laughing cheek"
  python3 tools/find_refs.py <workdir> "hand study" "study of hands" --type study --feature "hand gripping cloth" --dry
  python3 tools/find_refs.py <workdir> --take met:339909 cma:162888 --feature "hand gripping cloth" --why "knuckles over a fold"
  python3 tools/find_refs.py <workdir> --sheet            (rebuild refs/sheet.jpg from refs/refs.json)

Searches two open-access museum APIs and keeps only images their museum releases as public domain / CC0:
  - The Met: /public/collection/v1.1/search (offset + limit paging), then /public/collection/v1/objects/<id>;
    kept only when isPublicDomain is true and there is an image. Requests are paced (the Met answers fast
    requests with a 403; on a 403 the tool stops asking the Met instead of retrying around it).
  - The Cleveland Museum of Art: /api/artworks/ with the bare `cc0` flag; kept only when share_license_status is CC0.
Both get a plain User-Agent. No other site is used, and nothing works around any site's protection (AGENTS.md rule 10).

--type picks the kind of image: photo (a photograph), study (a drawing: studies, académies, sketches),
print (prints), painting, sculpture (casts, antique and academic sculpture), or any of these. Every reference is recorded in <workdir>/refs/refs.json with its title,
artist, date, museum, object URL, image URL, licence and the evidence for it, the query, the FEATURE it is
studied for and the reason it was chosen; refs/sheet.jpg is a contact sheet grouped by feature
(`studio.py look refs` shows it beside the canvas).

The rules this tool helps keep (docs/research/references.md):
  - A reference is studied for one FEATURE (a laughing cheek, a hand gripping cloth, wet hair in wind),
    at least three per feature, from different sources; never one person's face as the subject.
  - Titles naming a sitter (a portrait of a named person) are skipped by default; --allow-named keeps
    them for features that are not a face (a hand, drapery), and they are marked "named_sitter" in refs.json.
  - At most --per-artist (default 2) references by one artist per feature: a current, never one author's manner.
"""
import argparse, json, os, re, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone

UA = "TeodorRefs/1.0 (open-access reference finder for a painting experiment; python urllib)"
MET = "https://collectionapi.metmuseum.org/public/collection"
CMA = "https://openaccess-api.clevelandart.org/api/artworks/"
MET_PACE = 0.6          # seconds between Met requests (judgement: well under its documented 80 req/s, since it 403s bursts)

# type -> (Met departments, Met classification test, Cleveland types)
TYPES = {
    "photo":    ([19], lambda c, n: "photo" in (c + n).lower(), ["Photograph"]),
    "study":    ([9], lambda c, n: "drawing" in (c + n).lower(), ["Drawing"]),
    "print":    ([9], lambda c, n: "print" in (c + n).lower(), ["Print"]),
    "painting": ([11, 1, 15], lambda c, n: "painting" in (c + n).lower(), ["Painting"]),
    "sculpture": ([12, 13], lambda c, n: "sculpture" in (c + n).lower(), ["Sculpture"]),     # casts and antique figures
    "any":      ([None], lambda c, n: any(k in (c + n).lower() for k in ("photo", "drawing", "print", "painting", "sculpture")),
                 ["Photograph", "Drawing", "Print", "Painting", "Sculpture"]),
}
# Titles that name a sitter. A judgement heuristic: it errs toward skipping; the orchestrator still checks every reference.
HONORIFIC = re.compile(r"\b(?:Mrs?\.|Mme\.?|Mlle\.?|Madame|Monsieur|Miss|Lady|Lord|Sir|Duke|Duchess|King|Queen|Prince|Princess|"
                       r"Count|Countess|General|President|Emperor|Empress|Dr\.)\s+[A-Z]|\bprobably [A-Z]")
OF_WHOM = re.compile(r"\b(?:portrait|bust|head|likeness|study|profile|photograph) of ([A-Z][\w'\-]+)", re.I)
GENERIC = set("""a an the two three four several young old elderly woman women man men girl girls boy boys child children
hand hands foot feet arm arms leg legs head heads figure figures nude nudes model models bather bathers dancer dancers lady
gentleman youth peasant peasants monk nun christ virgin st saint apostle angel angels satyr nymph study studies drapery seated
standing reclining kneeling female male back untitled unidentified unknown sculpture cast woman's man's girl's boy's
mother father brother sister husband wife family self laughing smiling weeping sleeping running seated dancing""".split())
PARTICLES = ("de", "van", "von", "da", "di", "del", "la", "le", "and")


def _is_name(words):
    words = [w.strip("[]\"',.") for w in words if w.strip("[]\"',.")]
    caps = [w for w in words if w not in PARTICLES]
    return 1 <= len(caps) <= 4 and all(w[0].isupper() for w in caps) and not any(w.lower().rstrip("'s") in GENERIC for w in caps)


def named_sitter(title):
    """True when the title names a real sitter, so the image is a likeness. A judgement heuristic that errs toward
    skipping; single-word titles ("Christabel", "Harry") pass it, so the orchestrator still checks every reference."""
    t = (title or "").strip()
    if HONORIFIC.search(t):
        return True
    for m in OF_WHOM.finditer(t):
        w = m.group(1)
        if w[0].isupper() and w.lower() not in GENERIC:
            return True
    head = re.split(r",| and |;|\(", t.strip("[]"))[0].split()
    if len(head) >= 2 and _is_name(head):                       # "Julia Jackson", "Lola Montez", "[Carlotta Cortudino]"
        return True
    m = re.match(r"^\[?((?:[A-Z][\w.'\-]*\s+){1,3})(?:in|as|at|with|on)\s", t)    # "Nijinsky in ...", "Clara L. White as a Child"
    return bool(m and _is_name(m.group(1).split()))


# rule 5: no gore; post-mortem and medical-wound photographs are not references for Teodor
GORE = re.compile(r"post-?mortem|\bdead\b|corpse|cadaver|autopsy|wound|execution|dissection|surgical|slaying|beheading|severed|strangl|"
                  r"head of (?:goliath|holofernes|cyrus|st\.? john|saint john|medusa)", re.I)
# people photographed without being able to consent (asylum patients, prisoners): not references for Teodor (a judgement)
CONSENT = re.compile(r"\b(?:asylum|lunatic|insane|prisoner|convict|mugshot)\b", re.I)


def get(url, tries=1):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, image/*"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


def getj(url):
    return json.loads(get(url).decode("utf-8"))


class MetBlocked(Exception):
    pass


_last = [0.0]


def met(path):
    wait = MET_PACE - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()
    try:
        return getj(MET + path)
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise MetBlocked("the Met answered 403 (rate limit); stopping Met requests for this run")
        if e.code == 404:
            return None
        raise


def search_met(q, kind, want, scan):
    depts, ok_class, _ = TYPES[kind]
    out, seen = [], 0
    try:
        for dep in depts:
            offset = 0
            while len(out) < want and seen < scan:
                p = {"q": q, "hasImages": "true", "limit": 40, "offset": offset}
                if dep:
                    p["departmentId"] = dep
                r = met("/v1.1/search?" + urllib.parse.urlencode(p)) or {}
                ids = r.get("objectIDs") or []
                if not ids:
                    break
                for oid in ids:
                    if len(out) >= want or seen >= scan:
                        break
                    seen += 1
                    o = met(f"/v1/objects/{oid}")
                    if not o or not o.get("isPublicDomain") or not (o.get("primaryImageSmall") or o.get("primaryImage")):
                        continue
                    if not ok_class(o.get("classification", ""), o.get("objectName", "")):
                        continue
                    out.append({
                        "museum": "The Metropolitan Museum of Art", "key": f"met:{oid}", "object_id": oid,
                        "title": o.get("title", ""), "artist": o.get("artistDisplayName") or "unknown",
                        "date": o.get("objectDate", ""), "medium": o.get("medium", ""),
                        "kind": o.get("classification") or o.get("objectName", ""),
                        "object_url": o.get("objectURL", ""), "image_url": o.get("primaryImageSmall") or o.get("primaryImage"),
                        "licence": "CC0 (The Met Open Access, public domain)",
                        "licence_evidence": "Met API isPublicDomain: true", "credit": o.get("creditLine", ""),
                        "hits": r.get("total", 0)})
                offset += 40
    except MetBlocked as e:
        print(f"  [met] {e}", file=sys.stderr)
    return out


def search_cma(q, kind, want):
    out = []
    for t in TYPES[kind][2]:
        p = {"q": q, "has_image": 1, "limit": max(want * 2, 10)}
        if t:
            p["type"] = t
        url = CMA + "?" + urllib.parse.urlencode(p) + "&cc0"     # the bare cc0 flag
        try:
            r = getj(url)
        except urllib.error.HTTPError as e:
            print(f"  [cma] HTTP {e.code}; skipping", file=sys.stderr)
            continue
        for a in r.get("data", []):
            if a.get("share_license_status") != "CC0":
                continue
            img = ((a.get("images") or {}).get("web") or {}).get("url")
            if not img:
                continue
            cr = "; ".join(c.get("description", "") for c in (a.get("creators") or [])) or "unknown (" + ", ".join(a.get("culture") or ["no maker recorded"]) + ")"
            out.append({
                "museum": "The Cleveland Museum of Art", "key": f"cma:{a['id']}", "object_id": a["id"],
                "title": a.get("title", ""), "artist": cr, "date": a.get("creation_date", ""),
                "medium": a.get("technique", "") or "", "kind": a.get("type", ""),
                "object_url": a.get("url", ""), "image_url": img,
                "licence": "CC0 (Cleveland Museum of Art Open Access)",
                "licence_evidence": "CMA API share_license_status: CC0", "credit": a.get("creditline", "") or "",
                "hits": (r.get("info") or {}).get("total", 0)})
            if len(out) >= want:
                break
    return out


def take(key):
    mus, oid = key.split(":", 1)
    if mus == "met":
        o = met(f"/v1/objects/{oid}")
        if not o or not o.get("isPublicDomain") or not (o.get("primaryImageSmall") or o.get("primaryImage")):
            print(f"  {key}: not public domain or no image at the Met; not taken", file=sys.stderr)
            return None
        return {"museum": "The Metropolitan Museum of Art", "key": key, "object_id": int(oid), "title": o.get("title", ""),
                "artist": o.get("artistDisplayName") or "unknown", "date": o.get("objectDate", ""), "medium": o.get("medium", ""),
                "kind": o.get("classification") or o.get("objectName", ""), "object_url": o.get("objectURL", ""),
                "image_url": o.get("primaryImageSmall") or o.get("primaryImage"),
                "licence": "CC0 (The Met Open Access, public domain)", "licence_evidence": "Met API isPublicDomain: true",
                "credit": o.get("creditLine", "")}
    if mus == "cma":
        a = getj(CMA + urllib.parse.quote(oid)).get("data", {})
        img = ((a.get("images") or {}).get("web") or {}).get("url")
        if a.get("share_license_status") != "CC0" or not img:
            print(f"  {key}: not CC0 or no image at Cleveland; not taken", file=sys.stderr)
            return None
        cr = "; ".join(c.get("description", "") for c in (a.get("creators") or [])) or "unknown"
        return {"museum": "The Cleveland Museum of Art", "key": key, "object_id": a.get("id"), "title": a.get("title", ""),
                "artist": cr, "date": a.get("creation_date", ""), "medium": a.get("technique", "") or "", "kind": a.get("type", ""),
                "object_url": a.get("url", ""), "image_url": img, "licence": "CC0 (Cleveland Museum of Art Open Access)",
                "licence_evidence": "CMA API share_license_status: CC0", "credit": a.get("creditline", "") or ""}
    sys.exit(f"unknown museum in {key} (use met:<id> or cma:<id>)")


def load(path):
    if os.path.exists(path):
        return json.load(open(path))
    return {"format": "teodor-refs/1", "rules": "docs/research/references.md", "refs": []}


def save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def download(ref, rdir):
    from PIL import Image
    name = re.sub(r"[^a-z0-9]+", "-", ref["key"].lower()) + ".jpg"
    dst = os.path.join(rdir, name)
    if not os.path.exists(dst):
        data = get(ref["image_url"])
        tmp = dst + ".part"
        open(tmp, "wb").write(data)
        try:
            im = Image.open(tmp)
            im.load()
            im = im.convert("RGB")
            if max(im.size) > 1400:
                im.thumbnail((1400, 1400))
            im.save(dst, quality=90)
        finally:
            os.remove(tmp)
    return name


def artist_key(a):
    """One key per maker however a museum spells the name ("Duchenne de Boulogne" / "Duchenne (de Boulogne)")."""
    a = (a or "").lower()
    if not a or a.startswith(("unknown", "anonymous", "unidentified")):
        return ""
    return " ".join(re.sub(r"[^a-zà-ÿ]+", " ", a.split("(")[0].split(",")[0]).split()[:3])


def ascii_label(t):
    """PIL's default bitmap font has no accents or dashes."""
    import unicodedata
    t = (t or "").replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'")
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()


def sheet(rdir, data, out=None, only=None):
    """A contact sheet of the references, one row block per feature, each tile numbered as in refs.json."""
    from PIL import Image, ImageDraw
    refs = [(i, r) for i, r in enumerate(data["refs"], 1) if not only or only.lower() in (r.get("feature") or "").lower()]
    if not refs:
        return None
    feats = []
    for _, r in refs:
        if r.get("feature", "") not in feats:
            feats.append(r.get("feature", ""))
    T, cols, pad, head = 220, 5, 8, 22
    rows = []
    for f in feats:
        items = [(i, r) for i, r in refs if r.get("feature", "") == f]
        rows.append((f, [items[k:k + cols] for k in range(0, len(items), cols)]))
    H = sum(head + len(chunks) * (T + 16 + pad) for _, chunks in rows) + pad
    W = cols * (T + pad) + pad
    S = Image.new("RGB", (W, H), (28, 27, 25))
    d = ImageDraw.Draw(S)
    y = pad
    for f, chunks in rows:
        d.text((pad, y + 4), ascii_label(f"FEATURE: {f or '(none given)'}"), fill=(235, 225, 200))
        y += head
        for chunk in chunks:
            for c, (i, r) in enumerate(chunk):
                x = pad + c * (T + pad)
                try:
                    im = Image.open(os.path.join(rdir, r["file"])).convert("RGB")
                    im.thumbnail((T, T))
                    S.paste(im, (x + (T - im.width) // 2, y + (T - im.height) // 2))
                except Exception:
                    d.rectangle((x, y, x + T, y + T), outline=(120, 60, 60))
                lab = ascii_label(f"{i}. {(r.get('artist') or '').split('(')[0].strip()[:24]}, {(r.get('date') or '')[:12]}")
                d.text((x, y + T + 2), lab, fill=(200, 195, 185))
            y += T + 16 + pad
    out = out or os.path.join(rdir, "sheet.jpg")
    S.save(out, quality=88)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir")
    ap.add_argument("terms", nargs="*", help="search terms (each a separate query)")
    ap.add_argument("--type", default="any", choices=list(TYPES))
    ap.add_argument("--feature", default="", help='what the references are studied for, e.g. "laughing cheek"')
    ap.add_argument("--why", default="", help="the reason they were chosen (recorded for each)")
    ap.add_argument("--n", type=int, default=4, help="references to keep per query and museum (default 4)")
    ap.add_argument("--scan", type=int, default=60, help="Met objects to inspect per query at most (default 60)")
    ap.add_argument("--museum", default="met,cma", help="met, cma or both (default)")
    ap.add_argument("--per-artist", type=int, default=2, help="at most this many by one artist per feature (default 2)")
    ap.add_argument("--allow-named", action="store_true", help="keep works whose title names a sitter (never for a face)")
    ap.add_argument("--dry", action="store_true", help="list candidates with their keys; download nothing")
    ap.add_argument("--take", nargs="*", default=[], help="download these candidates: met:<id> cma:<id>")
    ap.add_argument("--sheet", action="store_true", help="only rebuild refs/sheet.jpg")
    a = ap.parse_args()

    rdir = os.path.join(os.path.abspath(a.workdir), "refs")
    os.makedirs(rdir, exist_ok=True)
    jpath = os.path.join(rdir, "refs.json")
    data = load(jpath)
    if a.sheet:
        print(sheet(rdir, data) or "no references yet")
        return
    if (a.terms or a.take) and not a.feature:
        sys.exit("say what you study these references for: --feature \"laughing cheek\" (docs/research/references.md)")
    if a.feature and re.search(r"\b(face|portrait|head)\b", a.feature, re.I) and a.allow_named:
        sys.exit("--allow-named is never for a face: a named sitter's face is a likeness (AGENTS.md rule 5)")

    have = {(r["key"], r.get("feature", "")) for r in data["refs"]}
    per_artist = {}
    for r in data["refs"]:
        if r.get("feature") == a.feature and artist_key(r.get("artist")):
            per_artist[artist_key(r["artist"])] = per_artist.get(artist_key(r["artist"]), 0) + 1

    cands = []
    if a.take:
        for k in a.take:
            c = take(k)
            if c:
                c["query"] = "(taken by key)"
                cands.append(c)
    mus = a.museum.split(",")
    for q in a.terms:
        found = []
        if "met" in mus:
            found += search_met(q, a.type, a.n, a.scan)
        if "cma" in mus:
            found += search_cma(q, a.type, a.n)
        for c in found:
            c["query"] = q
        print(f"'{q}' ({a.type}): {len(found)} usable", file=sys.stderr)
        cands += found

    kept = []
    for c in cands:
        if GORE.search(c["title"] + " " + c.get("medium", "")):
            print(f"  skip {c['key']} '{c['title'][:60]}': gore, violence or death (rule 5)", file=sys.stderr)
            continue
        if CONSENT.search(c["title"]):
            print(f"  skip {c['key']} '{c['title'][:60]}': a person who could not consent (asylum, prison)", file=sys.stderr)
            continue
        c["named_sitter"] = named_sitter(c["title"])
        if c["named_sitter"] and not a.allow_named:
            print(f"  skip {c['key']} '{c['title'][:60]}': names a sitter (likeness rule)", file=sys.stderr)
            continue
        ak = artist_key(c["artist"])
        if ak and per_artist.get(ak, 0) >= a.per_artist:
            print(f"  skip {c['key']}: already {a.per_artist} by {c['artist'][:40]} for this feature (styles, never authors)", file=sys.stderr)
            continue
        if (c["key"], a.feature) in have:
            continue
        if ak:
            per_artist[ak] = per_artist.get(ak, 0) + 1
        have.add((c["key"], a.feature))
        kept.append(c)

    if a.dry:
        for c in kept:
            print(f"{c['key']:<14} {c['kind'][:14]:<14} {c['date'][:16]:<16} {c['artist'][:30]:<30} {c['title'][:70]}")
            print(f"{'':14} {c['object_url']}")
        print(f"{len(kept)} candidates (nothing downloaded; --take KEY ... to keep some)")
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for c in kept:
        try:
            c["file"] = download(c, rdir)
        except Exception as e:
            print(f"  {c['key']}: download failed ({e}); not recorded", file=sys.stderr)
            continue
        c.pop("hits", None)
        c.update({"feature": a.feature, "type": a.type if c["query"] != "(taken by key)" else c.get("kind", ""), "fetched": now,
                  "reason": a.why or f"matched '{c['query']}' ({a.type}); study it for: {a.feature}. Replace with what you see in it."})
        data["refs"].append(c)
        print(f"{len(data['refs'])}. {c['key']} {c['artist'][:30]}, {c['date']}: {c['title'][:60]}")
    save(jpath, data)
    feats = {}
    for r in data["refs"]:
        feats.setdefault(r.get("feature", ""), set()).add(r["museum"])
    n = sum(1 for r in data["refs"] if r.get("feature") == a.feature)
    srcs = len({artist_key(r["artist"]) or r["key"] for r in data["refs"] if r.get("feature") == a.feature})
    print(f"feature '{a.feature}': {n} references from {srcs} sources" + ("" if n >= 3 and srcs >= 3 else "  (fewer than 3 from different sources: find more)"))
    print(sheet(rdir, data) or "")


if __name__ == "__main__":
    main()
