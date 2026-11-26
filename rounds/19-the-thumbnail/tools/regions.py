"""Masks -> polygon regions for the studio (holes joined to the outline by thin slits)."""
import numpy as np, cv2, json, sys
def mask_to_poly(mask, eps=3.0, min_area=400):
    m = mask.astype(np.uint8)
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is None: return []
    hier = hier[0]; polys = []
    for i, c in enumerate(cs):
        if hier[i][3] != -1 or cv2.contourArea(c) < min_area: continue
        outer = cv2.approxPolyDP(c, eps, True)[:, 0, :].tolist()
        j = hier[i][2]
        while j != -1:
            h = cs[j]
            if cv2.contourArea(h) >= 30:
                hp = cv2.approxPolyDP(h, eps * 0.5, True)[:, 0, :].tolist()
                # slit: from the outer point nearest the hole's first point, around the hole, and back
                o = np.array(outer); k = int(np.argmin(((o - np.array(hp[0])) ** 2).sum(1)))
                outer = outer[:k + 1] + hp + [hp[0], outer[k]] + outer[k + 1:]
            j = hier[j][0]
        polys.append(outer)
    return polys
def region(mask, eps=3.0):
    ps = mask_to_poly(mask, eps)
    ps.sort(key=lambda p: -cv2.contourArea(np.array(p, np.int32)))
    return [{"type": "poly", "pts": p} for p in ps]
