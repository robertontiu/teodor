import json,sys
sc=json.load(open(sys.argv[1]))
sc["camera"]={"pos":[0.5,2.0,3.2],"look_at":[0.05,1.75,-0.9],"fov":30}
sc["objects"]=[o for o in sc["objects"] if not (o["type"] in ("box","ellipsoid","capsule") and o.get("pos",o.get("a",[0,0,0]))[2]>1.5)]
json.dump(sc,open(sys.argv[2],"w"))
