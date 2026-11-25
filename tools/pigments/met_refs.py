import json, re, os, sys, time, io, urllib.request, concurrent.futures as cf
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
API = "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
UA = "TeodorResearch/1.0 (https://github.com/robertontiu/teodor)"
IMG = "" + os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data")) + "/img"; os.makedirs(IMG, exist_ok=True)
F = ("objectID","isPublicDomain","primaryImage","department","classification","title","artistDisplayName","objectDate","culture","medium","dimensions","objectURL")
SEL = {
 "oil": [436535, 436532, 436528, 437980, 437127, 437399, 437305, 437680, 437433, 435881, 436140, 436016, 436596, 436523, 436098],
 "tempera_gold": [438423, 438754, 437007, 436908, 436053, 437611, 438020, 436506],
 "watercolour": [819278, 420544, 390390, 363700, 364366, 383837, 437693, 437695, 356060],
 "gouache": [437315, 436134, 710360, 355542, 386569, 378505, 379126],
 "ink_brush": [737736, 916565, 48903, 902217, 36084, 48967, 45620, 51415, 36145, 57262, 57261],
 "charcoal": [399579, 436166, 365663, 337802, 335745, 436127, 436151, 337511],
 "graphite": [409002, 355649, 384261, 365595, 812726, 345512, 344278, 386741],
 "pastel": [436173, 437379, 438544, 438615, 436163, 437584, 436124, 436159],
 "ukiyoe": [37224, 56188, 57052, 55740, 56212, 55020, 57062, 45301],
}
def get(u, binary=False):
    for a in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=180).read()
        except Exception as e:
            err = e; time.sleep(2 + 3 * a)
    raise err
def dims_cm(s):
    m = re.search(r"\(([\d.]+)\s*[x×]\s*([\d.]+)\s*(cm|mm)", s or "")
    if not m: return None
    f = 10 if m.group(3) == "cm" else 1
    return float(m.group(1)) * f, float(m.group(2)) * f
def crop_for(a, medium, win):
    """Window (full-res px) where marks are most legible: high local detail energy, away from the margins."""
    g = a.mean(-1)
    h, w = g.shape
    s = max(1, int(round(min(h, w) / 1200)))         # analyse on a reduced grid
    gs = g[::s, ::s]
    from scipy.ndimage import gaussian_filter, uniform_filter
    hp = np.abs(gs - gaussian_filter(gs, 3))
    k = max(8, win // s)
    e = uniform_filter(hp, k)
    lum = uniform_filter(gs, k)
    # avoid the margins (frames, mounts, paper edges) and near-blank areas
    H, W = e.shape; my, mx = int(0.12 * H) + k // 2, int(0.12 * W) + k // 2
    m = np.zeros_like(e, bool); m[my:H - my, mx:W - mx] = True
    score = np.where(m, e * (0.35 + np.clip(1 - np.abs(lum - 128) / 128, 0, 1)), -1)
    y, x = np.unravel_index(np.argmax(score), score.shape)
    x0 = int(np.clip(x * s - win // 2, 0, w - win)); y0 = int(np.clip(y * s - win // 2, 0, h - win))
    return [x0, y0, win, win]
def one(args):
    med, oid = args
    try:
        o = json.loads(get(API + str(oid)))
    except Exception as e:
        return dict(objectID=oid, medium_group=med, ok=False, error=f"record: {e}")
    r = {k: o.get(k) for k in F}
    r["medium_group"] = med
    if not (o.get("isPublicDomain") and o.get("primaryImage")):
        r.update(ok=False, error="not public domain or no image"); return r
    path = f"{IMG}/{oid}.jpg"
    try:
        if not os.path.exists(path):
            b = get(o["primaryImage"]); open(path, "wb").write(b)
        im = Image.open(path).convert("RGB")
    except Exception as e:
        r.update(ok=False, error=f"image: {e}"); return r
    w, h = im.size
    a = np.asarray(im, np.float32)
    r.update(ok=True, image_px=[w, h], bytes=os.path.getsize(path))
    d = dims_cm(o.get("dimensions"))
    if d:
        r["size_mm_hw"] = [round(d[0]), round(d[1])]
        ph, pw = h / d[0], w / d[1]
        r["px_per_mm"] = round((ph + pw) / 2, 2)
        r["px_per_mm_note"] = "consistent" if abs(ph - pw) / max(ph, pw) < 0.12 else f"inconsistent (h {ph:.1f}, w {pw:.1f}): image may include frame/mount or dims are of the sheet"
    win = int(min(1024, 0.3 * min(w, h)))
    r["crop_xywh"] = crop_for(a, med, win)
    return r
jobs = [(m, i) for m, ids in SEL.items() for i in ids]
with cf.ThreadPoolExecutor(5) as ex:
    res = list(ex.map(one, jobs))
json.dump(res, open("" + os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data")) + "/met/refs_raw.json", "w"), indent=1)
for r in res:
    print(r["medium_group"], r["objectID"], r.get("ok"), r.get("error", ""), (r.get("artistDisplayName") or "")[:20], "|", (r.get("medium") or "")[:45], r.get("image_px"), r.get("px_per_mm"), r.get("crop_xywh"))
