import re, html, json, statistics, sys
D = "" + os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data")) + "/handprint/"
pages = ["waterc", "waterr", "watero", "watere", "watery", "waterg", "waterb", "waterv", "waterw"]
row = re.compile(r"(P[A-Z][a-z]?[A-Z]?\d+(?::\d+)?(?:\+P[A-Z][a-z]?[A-Z]?\d+(?::\d+)?)*) (.{2,200}?) (\d) (\d) (\d{1,3}) (\d) (\d) (\d) (\d{1,3}) ([+-]?\d{1,3}) (\d,\d)")
camr = re.compile(r"average CIECAM J,a,b values for ([^()]{2,60}?) \((P[A-Z][a-z]?[A-Z]?\d+(?::\d+)?)\) (?:were|are):? (-?\d+), (-?\d+), (-?\d+)")
dry = re.compile(r"\((P[A-Z][a-z]?[A-Z]?\d+(?::\d+)?)\)[^.]{0,200}?drying shift[^.]{0,120}?(lighten|darken)ing by (\d+)%")
out = {}
for p in pages:
    t = open(D + p + ".html", encoding="latin-1").read()
    t = html.unescape(re.sub(r"<[^>]+>", " ", t)); t = re.sub(r"\s+", " ", t)
    for m in row.finditer(t):
        code = m.group(1)
        r = out.setdefault(code, {"page": p, "paints": []})
        r["paints"].append(dict(name=m.group(2)[-80:], Tr=int(m.group(3)), St=int(m.group(4)), VR=int(m.group(5)),
                                Gr=int(m.group(6)), Bl=int(m.group(7)), Df=int(m.group(8)), HA=int(m.group(9)), HS=int(m.group(10))))
    for m in camr.finditer(t):
        out.setdefault(m.group(2), {"page": p, "paints": []})["ciecam_Jab"] = [int(m.group(i)) for i in (3, 4, 5)]
        out[m.group(2)]["common_name"] = m.group(1).strip()
    for m in re.finditer(r"\((P[A-Z][a-z]?[A-Z]?\d+(?::\d+)?)\)", t):
        pass
    for m in re.finditer(r"drying shift[^.]{0,60}?(lighten|darken)ing (?:by )?(\d+)%", t):
        # attribute to the nearest preceding pigment code mention
        prev = list(re.finditer(r"\b(P[A-Z][a-z]?[A-Z]?\d+(?::\d+)?)\b", t[max(0, m.start()-400):m.start()]))
        if prev:
            out.setdefault(prev[-1].group(1), {"page": p, "paints": []})["drying_shift_pct"] = (1 if m.group(1) == "lighten" else -1) * int(m.group(2))
for k, r in out.items():
    ps = r["paints"]
    if ps:
        r["n_paints"] = len(ps)
        for a in ("Tr", "St", "VR", "Gr", "Bl", "Df", "HA"):
            r[a + "_median"] = statistics.median(x[a] for x in ps)
json.dump(out, open("" + os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data")) + "/handprint/handprint_ratings.json", "w"), indent=1)
print(len(out), sum(1 for r in out.values() if r.get("paints")), sum("ciecam_Jab" in r for r in out.values()), sum("drying_shift_pct" in r for r in out.values()))
for k in ["PB29", "PB28", "PB27", "PR101", "PBr7", "PG17", "PY43", "PB15:3", "PR122", "PBk9", "PW6"]:
    r = out.get(k, {}); print(k, r.get("common_name"), r.get("n_paints"), {a: r.get(a + "_median") for a in ("Tr", "St", "VR", "Gr", "Bl", "Df")}, r.get("ciecam_Jab"), r.get("drying_shift_pct"))
