# build an episode: ep.py felt_json out.json  intention_json_with_@STROKES@ [strokes_file]
import sys,json
felt=json.loads(sys.argv[1]); its=[]
for a in sys.argv[2:]:
    it=json.loads(a) if not a.startswith('@') else None
    if it is None:
        spec,fn=a[1:].split('=',1); it=json.loads(spec); it['strokes']=json.load(open(fn))
    its.append(it)
json.dump({"felt":felt,"do":its},open('/tmp/ep.json','w'))
