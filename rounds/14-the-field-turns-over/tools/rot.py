# rotate the overhead render so the body lies upside-down and diagonal; save rotated render + masks
import numpy as np, sys
from PIL import Image
src=Image.open(sys.argv[1]).convert('RGB').resize((1200,1600),Image.LANCZOS)
ang=float(sys.argv[2]); sc=float(sys.argv[3]); cx,cy=float(sys.argv[4]),float(sys.argv[5]); tx,ty=float(sys.argv[6]),float(sys.argv[7])
# affine: output pixel (u,v) -> source
import math
a=math.radians(ang); ca,sa=math.cos(a),math.sin(a)
# inverse mapping: src = c + R(-a)*(out - t)/sc
coeffs=(ca/sc, sa/sc, cx - (ca*tx+sa*ty)/sc, -sa/sc, ca/sc, cy - (-sa*tx+ca*ty)/sc)
out=src.transform((1200,1600),Image.AFFINE,coeffs,resample=Image.BICUBIC,fillcolor=(162,188,64))
out.save(sys.argv[8])
