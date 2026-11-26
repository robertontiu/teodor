"""Named region masks from the schema layers, traced to polygons for the studio's regions.
usage: python3 regions.py NAME [x y w h] -> prints JSON list of polys (largest first)"""
import sys, json, numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, label
from skimage import measure
W,H=1200,1600
D='/home/claude/teodor-work/17/schema/'
def a(p): return np.asarray(Image.open(D+p).convert('RGBA'))[...,3]>40
def masks():
    m=np.load(D+'../blk_elements.npz')
    r=np.asarray(Image.open(D+'../blk_scene_v1.png').convert('RGB')).astype(float)/255
    mx=r.max(-1)+1e-6; warm=(r[...,0]-r[...,2])/mx>0.25
    cloth=m['she.drapery']|m['she.torso']|m['she.legs']
    yy,xx=np.mgrid[0:H,0:W]
    skin=m['she.arms']|m['she.hands']|m['she.neck']
    far=binary_dilation(cloth&~warm&(xx>650+(yy-500)*0.05),iterations=4)&~skin
    crest=a('crest_1.png'); sheet=a('sheet_2.png')&~(skin|cloth); face=a('face_3.png')
    cl=a('cloth_1.png')
    dress=((cloth&warm)&~far)|cl; shawl=(cloth&~warm)&~far
    fig=(skin|dress|shawl|face)&~crest
    occ=np.load(D+'occ.npy')
    M={'sky':~occ&(yy<1168),'sea':~occ&(yy>=1166),'crest':crest,'sheet':sheet&~crest,'skin':skin&~crest&~face,
       'dress':dress&~crest&~face,'shawl':shawl&~crest&~face,'face':face,'figure':fig,'arms':skin&~face}
    return M
def polys(mask, rect=None, minpx=400, tol=2.5):
    if rect:
        x,y,w,h=rect; r=np.zeros_like(mask); r[max(0,y):y+h, max(0,x):x+w]=True; mask=mask&r
    lab,n=label(mask); out=[]
    for i in range(1,n+1):
        mm=lab==i
        if mm.sum()<minpx: continue
        cs=measure.find_contours(np.pad(mm,1).astype(float),0.5); c=max(cs,key=len)
        c=measure.approximate_polygon(c,tolerance=tol)
        out.append((int(mm.sum()),[[round(float(p[1]-1)),round(float(p[0]-1))] for p in c]))
    out.sort(key=lambda t:-t[0]); return [p for _,p in out]
if __name__=='__main__':
    M=dict(np.load(D+'masks.npz')); name=sys.argv[1]; rect=[int(v) for v in sys.argv[2:6]] if len(sys.argv)>5 else None
    print(json.dumps(polys(M[name],rect)))
