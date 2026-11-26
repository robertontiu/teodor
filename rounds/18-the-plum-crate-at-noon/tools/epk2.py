# Key-line episode: python3 epk.py NAME felt_json part:width_mm[:articulation] ...
import json, sys
keys = json.load(open("/home/claude/teodor-work/18/plan/keys2.json"))
name, felt = sys.argv[1], json.loads(sys.argv[2])
do = []
for spec in sys.argv[3:]:
    bits = spec.split(":")
    parts, w = bits[0].split("+"), float(bits[1])
    art = bits[2] if len(bits) > 2 else "auto"
    st = []
    for p in parts:
        for k in keys.get(p, []):
            st.append({"pts": k["pts"], "color": k["color"]})
    do.append({"type": "strokes", "brush": "key", "width_mm": w, "role": "contour", "articulation": art,
               "focus_scale": False, "role_scale": False, "strokes": st})
json.dump({"felt": felt, "do": do}, open(f"/home/claude/teodor-work/18/ep_{name}.json", "w"))
print(name, [len(d["strokes"]) for d in do])
