import numpy as np, sys
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import distance_transform_edt, binary_opening
base = Image.open(sys.argv[1]).convert('RGB'); out = sys.argv[2]
A = np.asarray(base).astype(float)
r,g,b = A[...,0],A[...,1],A[...,2]
body = (b > r + 40) & (b > g + 10)
body = binary_opening(body, iterations=2)
dout = distance_transform_edt(~body); din = distance_transform_edt(body)
rng = np.random.default_rng(14)
img = base.convert('RGBA')
ov = Image.new('RGBA', img.size, (0,0,0,0)); d = ImageDraw.Draw(ov)
# echo contours (aura), drawn as rings from distance field
H,W = body.shape
cols = [(255,92,150),(40,200,200),(250,240,90),(255,255,255)]
ring = np.zeros((H,W,4),float)
for k,dist in enumerate(range(44, 230, 44)):
    band = np.abs(dout - dist) < 4.5
    c = cols[k % 3]; a = 235 * (1 - dist/280)
    ring[band] = (*c, a)
ringimg = Image.fromarray(ring.astype(np.uint8), 'RGBA').filter(ImageFilter.GaussianBlur(1.2))
img = Image.alpha_composite(img, ringimg)
# kusama dots
step = int(sys.argv[3]) if len(sys.argv) > 3 else 46
for y in range(0, H, step):
    for x in range(0, W, step):
        xx = int(np.clip(x + rng.normal(0, step*0.18) + (step/2 if (y//step)%2 else 0), 0, W-1)); yy = int(np.clip(y + rng.normal(0, step*0.18), 0, H-1))
        if body[yy,xx]:
            e = din[yy,xx]
            if rng.random() > np.clip(1.15 - e/90, 0.12, 1): continue
            rad = rng.uniform(5, 11); c = (250,240,90,255) if rng.random() < .65 else (255,110,165,255)
        else:
            e = dout[yy,xx]
            rad = np.clip(15 - e/60, 4, 15) * rng.uniform(.75,1.1)
            c = (255,92,150,255) if rng.random() < .6 else ((255,255,250,255) if rng.random()<.6 else (30,60,190,255))
        d.ellipse([xx-rad,yy-rad,xx+rad,yy+rad], fill=c)
img = Image.alpha_composite(img, ov)
img.convert('RGB').save(out)
