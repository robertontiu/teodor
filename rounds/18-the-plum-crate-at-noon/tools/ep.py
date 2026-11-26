# Writes an episode file of block impressions from the seed list: python3 ep.py NN felt_json colour [colour...]
import json, sys
seeds = json.load(open("/home/claude/teodor-work/18/plan/seeds.json"))
n, felt = sys.argv[1], json.loads(sys.argv[2])
do = []
for c in sys.argv[3:]:
    st = [{k: v for k, v in s.items() if k != "name"} for s in seeds[c]]
    do.append({"type": "strokes", "brush": "block", "carve": "region", "role": "body", "focus_scale": False, "role_scale": False, "strokes": st})
json.dump({"felt": felt, "do": do}, open(f"/home/claude/teodor-work/18/ep_{n}.json", "w"))
print(f"ep_{n}.json", [len(d["strokes"]) for d in do])
