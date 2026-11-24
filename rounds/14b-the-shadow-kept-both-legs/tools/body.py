import sys, math; sys.path.insert(0,"/home/claude/v14f")
import numpy as np
LIT = np.array([0.87, 0.5])
def limb(pts, w, base, light, shade, k=0.27):
    """three parallel strokes along a limb: shade side, base, lit side"""
    pts = np.array(pts, float)
    out = []
    for col, off, sz in ((base, 0, w*0.95), (shade, -1, w*0.5), (light, +1, w*0.5)):
        q = []
        for i, p in enumerate(pts):
            t = pts[min(i+1, len(pts)-1)] - pts[max(i-1, 0)]; t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]]); n = n if n @ LIT > 0 else -n
            q.append((p + n * off * w * k).round(1).tolist())
        out.append({"pts": q, "size": round(sz, 1), "color": col})
    return out
