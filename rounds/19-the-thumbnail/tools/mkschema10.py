import numpy as np, json
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
S=np.asarray(Image.open('plan/m/schema9.png').convert('L')).astype(float)
C=np.asarray(Image.open('main_full.png').convert('L')).astype(float)
H,W=S.shape
r=json.load(open('plan/m/regions.json'))
fm=Image.new('L',(W,H),0); ImageDraw.Draw(fm).polygon([tuple(p) for p in r['face_work']],fill=255)
face=np.asarray(fm)>0
e=json.load(open('elements.json'))
am=Image.new('L',(W,H),0)
for x in e['elements']:
    if x['name']=='raised arm': ImageDraw.Draw(am).polygon([tuple(p) for p in x['region']['pts']],fill=255)
arm=np.asarray(am)>0
yy,xx=np.mgrid[0:H,0:W]
box=(xx>=860)&(xx<=1480)&(yy>=2170)&(yy<=2470)
m=box&~face&~(arm&(yy<2290))
mf=m.astype(float)
b=ndi.gaussian_filter(C*mf,22)/np.maximum(ndi.gaussian_filter(mf,22),1e-4)
f=np.clip(ndi.distance_transform_edt(m)/10,0,1)
O=S*(1-f)+b*f
Image.fromarray(O.astype(np.uint8)).convert('RGB').save('plan/m/schema10.png')
pts=[[860,2170],[1480,2170],[1480,2470],[860,2470]]
np.save('p3/base_mask.npy',m)
from skimage import measure
c=max(measure.find_contours(np.pad(m,1).astype(float),0.5),key=len)-1
c=measure.approximate_polygon(c,2.0)
json.dump({'type':'poly','pts':[[float(p[1]),float(p[0])] for p in c]},open('p3/base.json','w'))
Image.fromarray(O.astype(np.uint8)).crop((800,2100,1550,2550)).save('p3/s10crop.png')
