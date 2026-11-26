import json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import measure
W,H=2400,3200
r=json.load(open('plan/m/regions.json'))
def polys(v):
    if isinstance(v,dict): return [v]
    if v and isinstance(v[0],dict): return v
    return [{'type':'poly','pts':v}]
def mask(name):
    m=Image.new('L',(W,H),0); d=ImageDraw.Draw(m)
    for x in polys(r[name]):
        if x['type']=='poly': d.polygon([tuple(p) for p in x['pts']],fill=255)
        else: d.ellipse([x['cx']-x['rx'],x['cy']-x['ry'],x['cx']+x['rx'],x['cy']+x['ry']],fill=255)
    return np.asarray(m)>0
def armmask():
    e=json.load(open('elements.json'))
    m=Image.new('L',(W,H),0); d=ImageDraw.Draw(m)
    for x in e['elements']:
        if 'arm' in x['name'] or 'fist' in x['name']: d.polygon([tuple(p) for p in x['region']['pts']],fill=255)
    return ndi.binary_dilation(np.asarray(m)>0,iterations=6)
excl=mask('sky')|mask('ground')|armmask()|mask('face_work')|mask('hairr')
yy,xx=np.mgrid[0:H,0:W]
patch=(xx>=950)&(xx<=1720)&(yy<=2340)&(yy> 2100+(1700-xx)*0.2)
excl=excl&~(patch&~armmask()&~mask('face_work')&~mask('hairr'))
m=(~excl)&(xx>=900)&(yy>=1900)
m=ndi.binary_opening(m,iterations=3)
lab,n=ndi.label(m); sizes=ndi.sum(m,lab,range(1,n+1)); big=np.argmax(sizes)+1; m=lab==big
m=ndi.binary_fill_holes(m)
np.save('p3/chest2_mask.npy',m)
c=measure.find_contours(np.pad(m,1).astype(float),0.5)
c=max(c,key=len)-1
c=measure.approximate_polygon(c,2.0)
pts=[[float(np.clip(p[1],0,W-1)),float(np.clip(p[0],0,H-1))] for p in c]
json.dump({'type':'poly','pts':pts},open('p3/chest2.json','w'))
print(len(pts), m.sum())
im=Image.open('main_full.png').convert('RGB'); d=ImageDraw.Draw(im)
d.line([tuple(p) for p in pts],fill='red',width=8); im.resize((600,800)).save('p3/chest2.png')
