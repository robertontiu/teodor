import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage.color import rgb2lab
S=np.asarray(Image.open('plan/m/schema8.png').convert('L')).astype(float)
H,W=S.shape
yy,xx=np.mgrid[0:H,0:W]
def line_mask(pts,w,blur):
    m=Image.new('L',(W,H),0); ImageDraw.Draw(m).line(pts,fill=255,width=w,joint='curve')
    return ndi.gaussian_filter(np.asarray(m).astype(float)/255,blur)
def ell(cx,cy,rx,ry,blur,rot=0):
    m=(((xx-cx)/rx)**2+((yy-cy)/ry)**2<=1).astype(float); return ndi.gaussian_filter(m,blur)
def toward(S,mask,val): return S*(1-mask)+val*mask
O=S.copy()
# socket band left of the lid: lift so no dark ring
O=O+ell(705,2790,28,150,18)*22
# upper lid: quieter, not an eyeball
O=O-ell(770,2775,45,95,14)*16
# cheek ball pushed up against the shut lid
O=O+ell(912,2800,50,120,22)*26
O=O-line_mask([(965,2690),(985,2790),(970,2890),(930,2960)],18,14)*20
# lid fold
O=toward(O,line_mask([(792,2690),(808,2730),(816,2785),(808,2835),(790,2875)],5,2.5)*0.5,95)
crease=[(815,2672),(838,2705),(852,2745),(860,2790),(852,2830),(834,2865),(810,2895),(782,2918)]
O=toward(O,line_mask(crease,9,2.5),55)
feet=[[(780,2922),(745,2950),(708,2978)],[(784,2925),(762,2965),(740,3002)],[(790,2926),(782,2968),(772,3008)],[(796,2924),(806,2962),(812,2995)]]
for f in feet:
    O=toward(O,line_mask(f,5,1.8)*0.8,95)
for f in [[(760,2940),(725,2975)],[(772,2948),(752,2990)],[(787,2950),(778,2995)]]:
    O=O+line_mask(f,7,3)*25
lip=[(1075,2650),(1090,2720),(1100,2770),(1125,2840),(1160,2910),(1190,2945)]
O=toward(O,line_mask(lip,7,2.5)*0.9,60)
O=toward(O,line_mask([(1190,2945),(1186,2964),(1170,2978),(1150,2984)],8,3),50)
O=O+ell(1120,3005,55,30,14)*20
O=np.clip(O,0,255)
np.save('plan/m/schema9_L.npy',O)
Image.fromarray(O.astype(np.uint8)).convert('RGB').save('plan/m/schema9.png')
Image.fromarray(O.astype(np.uint8)).crop((620,2500,1380,3100)).save('p3/s9crop.png')
