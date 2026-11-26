import numpy as np, json
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
S=np.asarray(Image.open('plan/m/schema11.png').convert('L')).astype(float)
C=np.asarray(Image.open('main_full.png').convert('L')).astype(float)
H,W=S.shape
e=json.load(open('elements.json'))
pts=[x for x in e['elements'] if x['name']=='raised arm'][0]['region']['pts']
am=Image.new('L',(W,H),0); ImageDraw.Draw(am).polygon([tuple(p) for p in pts],fill=255)
r=json.load(open('plan/m/regions.json'))
fm=Image.new('L',(W,H),0); ImageDraw.Draw(fm).polygon([tuple(p) for p in r['face_work']],fill=255)
m=(np.asarray(am)>0)&~(np.asarray(fm)>0)
yy,xx=np.mgrid[0:H,0:W]
m&=yy>1482
m=ndi.binary_erosion(m,iterations=3)
# per row: position across the arm 0 (left) .. 1 (right)
t=np.zeros((H,W))
for y in range(H):
    xs=np.where(m[y])[0]
    if len(xs)>4:
        t[y,xs]=(xs-xs.min())/(xs.max()-xs.min())
# cylinder lit from the left: light at t~0.25, turning to shadow at the right, reflected light at the very edge
shade=np.where(t<0.3, 12*(1-np.abs(t-0.22)/0.3), 12-38*(t-0.3)/0.6)
shade=np.where(t>0.9,shade+8*(t-0.9)/0.1,shade)
base=ndi.gaussian_filter(C*m,12)/np.maximum(ndi.gaussian_filter(m.astype(float),12),1e-4)
O=np.where(m,np.clip(base+shade*1.2,0,255),S)
f=np.clip(ndi.distance_transform_edt(m)/6,0,1)
O=O*f+S*(1-f)
Image.fromarray(O.astype(np.uint8)).convert('RGB').save('plan/m/schema12.png')
from skimage import measure
c=max(measure.find_contours(np.pad(m,1).astype(float),0.5),key=len)-1
c=measure.approximate_polygon(c,1.5)
json.dump({'type':'poly','pts':[[float(p[1]),float(p[0])] for p in c]},open('p3/arm.json','w'))
Image.fromarray(O.astype(np.uint8)).resize((600,800)).save('p3/s12.png')
