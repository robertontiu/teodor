import json, sys, random
random.seed(int(sys.argv[3]) if len(sys.argv)>3 else 1)
d=json.load(open('/home/claude/tools/dots.json'))
keys=sys.argv[1].split(','); color=sys.argv[2]
cs=color.split(',')
st=[]
for k in keys:
    for x,y,r in d[k]:
        a=random.uniform(0,3.14); import math
        dx,dy=math.cos(a)*r*0.25, math.sin(a)*r*0.25
        st.append({"pts":[[x-dx,y-dy],[x+dx,y+dy]],"size":r*1.9,"color":random.choice(cs)})
print(json.dumps(st))
