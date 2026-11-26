# Plans face strokes in head-local coordinates (the schema's head group), transformed to canvas.
import json, math, sys
C, S = math.cos(math.radians(16)), math.sin(math.radians(16))
def T(p, ox=375, oy=895):
    x, y = p; return [round(ox + x*C - y*S, 1), round(oy + x*S + y*C, 1)]
def strokes(lst):
    return [{"pts": [T(p) for p in s[0]], "size": s[1], "color": s[2], "pressure": s[3] if len(s) > 3 else 0.7} for s in lst]
