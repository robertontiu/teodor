import numpy as np, json, sys
from PIL import Image
from scipy.ndimage import label, find_objects
ov=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int)
cols={'pink':(255,92,150),'white':(255,255,250),'blue':(30,60,190),'lemon':(250,240,90),'pink2':(255,110,165)}
res={}
for k,c in cols.items():
    m=(np.abs(ov-np.array(c)).sum(-1)<12)
    lab,n=label(m)
    out=[]
    for i,sl in enumerate(find_objects(lab)):
        h=sl[0].stop-sl[0].start; w=sl[1].stop-sl[1].start
        if h<6 or w<6 or h>40 or w>40: continue
        out.append([(sl[1].start+sl[1].stop)/2,(sl[0].start+sl[0].stop)/2,max(h,w)/2])
    res[k]=out
    print(k,len(out),file=sys.stderr)
json.dump(res,open(sys.argv[2],'w'))
