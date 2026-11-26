# episode of block impressions by colour: python3 epc.py NAME felt_json colour...
import json, sys
seeds = json.load(open("/home/claude/teodor-work/18/plan/seeds3.json"))
name, felt = sys.argv[1], json.loads(sys.argv[2])
do = [{"type": "strokes", "brush": "block", "carve": "region", "role": "body", "focus_scale": False, "role_scale": False,
       "strokes": [{k: v for k, v in s.items() if k != "name"} for s in seeds[c]]} for c in sys.argv[3:]]
json.dump({"felt": felt, "do": do}, open(f"/home/claude/teodor-work/18/ep_{name}.json", "w"))
