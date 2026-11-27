"""Check a reference render (a `scene` image) against the close-up ruler, the way a hyperrealist's photograph would
be judged: the cheek patch at 0.25-4 face-mm, the face's darks and speculars, the hair's strands, the sharpest edges.

  python3 tools/analysis/reference_check.py <image.png> --stem <dir>/<canvas> [--style graphite-hyperrealism]
          [--json out.json]

<stem>_elements.json / .npz and <stem>_structure.json come from `scene` (masks, the face's px per face-mm, the
pupils). The cheek patch is placed as on the ruler's photographs (docs/research/hyperrealism-gaps.md, "The close-up
ruler"): 25 face-mm square, its centre 7 mm toward the nose from the lit pupil and 41 mm below it. Bounds are the
ruler's p10-p90 (`studio/targets.json` -> `<style>-closeup`). Prints one row per check and the count passed."""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "studio", "v8"))
import eyes  # noqa: E402


def load(stem):
    idx = json.load(open(stem + "_elements.json"))
    npz = np.load(stem + "_elements.npz")
    st = json.load(open(stem + "_structure.json")) if os.path.exists(stem + "_structure.json") else {}
    return idx, npz, st


def cheek_box(L, pupils, ppm, face_mask):
    """(x0, y0, x1, y1) of the cheek patch under the lit eye: the pupil whose surround is brighter."""
    best = None
    for p in pupils:
        x, y = p["x"], p["y"]
        r = int(6 * ppm)
        y0, y1, x0, x1 = int(y + 20 * ppm), int(y + 55 * ppm), int(x - r), int(x + r)
        sub = L[max(0, y0):y1, max(0, x0):x1]
        v = float(sub.mean()) if sub.size else -1
        if best is None or v > best[0]:
            best = (v, p)
    if best is None:
        return None
    p = best[1]
    others = [q for q in pupils if q is not p]
    toward_nose = np.sign(others[0]["x"] - p["x"]) if others else 0
    cx, cy = p["x"] + toward_nose * 7 * ppm, p["y"] + 41 * ppm
    h = 12.5 * ppm
    box = [int(cx - h), int(cy - h), int(cx + h), int(cy + h)]
    return box, p["side"]


def check(image, stem, style="graphite-hyperrealism", ruler_path=None):
    rgb = np.asarray(Image.open(image).convert("RGB"), np.float32) / 255
    L, f = eyes.lightness(rgb)
    assert f == 1, "image over 16 MP: crop it"
    H, W = L.shape
    idx, npz, st = load(stem)
    tp = ruler_path or os.path.join(HERE, "..", "..", "studio", "targets.json")
    T = json.load(open(tp))[style + "-closeup"]
    k_ = W / idx["size"][0]
    face = next(e for e in idx["elements"] if e["element"] == "face")
    hair = next((e for e in idx["elements"] if e["element"] == "hair"), None)
    rs = lambda m: np.asarray(Image.fromarray(m.astype(np.uint8) * 255).resize((W, H), Image.NEAREST)) > 127
    fm = rs(npz[face["key"]])
    ppm = face["px_per_subject_mm"] * k_
    rows = []

    def add(name, v, lo=None, hi=None):
        ok = (lo is None or v >= lo) and (hi is None or v <= hi)
        rows.append(dict(check=name, value=round(float(v), 3), lo=lo, hi=hi, ok=bool(ok)))
    pupils = [dict(p, x=p["x"] * k_, y=p["y"] * k_) for p in st.get("pupils", [])]
    cb = cheek_box(L, pupils, ppm, fm) if pupils else None
    if cb:
        (x0, y0, x1, y1), side = cb
        patch = L[y0:y1, x0:x1]
        be = eyes.band_energy(patch, ppm)
        for s in ("0.125", "0.25", "0.5", "1.0", "2.0", "4.0"):
            b = T["skin_band_rms"][s]
            v = be[float(s)]
            if v is not None:
                add(f"cheek texture {s} face-mm (RMS L*)", v, b["p10"], b["p90"])
    fe = eyes.measure_fine(rgb, ppm, mask=fm, edges=False)
    add("face p1 (L*)", fe["value_p1"], None, T["face_value_p1"]["p90"])
    add("face share below L* 20", fe["value_below20"], T["face_value_below20"]["p10"], None)
    add("face speculars >= 30 L*", fe["specular_count_30"], T["face_specular_count_30"]["p10"], None)
    for s, b in T["face_band_rms"].items():
        v = fe["band_rms"].get(s)
        if v is not None:
            add(f"face texture {s} face-mm", v, b["p10"], b["p90"])
    if hair and hair["key"] in npz.files:
        hm = rs(npz[hair["key"]])
        if hm.sum() > 400:
            hp = (hair.get("px_per_subject_mm") or face["px_per_subject_mm"]) * k_
            he = eyes.measure_fine(rgb, hp, mask=hm, edges=False)
            for s in ("0.125", "0.25", "0.5"):
                v = he["band_rms"].get(s)
                if v is not None:
                    add(f"hair texture {s} mm", v, T["hair_band_rms"][s]["p10"], None)
            add("hair strand coherence", eyes.coherence(L, hp, hm), T["hair_coherence"]["p10"], None)
    # the sharpest edges at the sheet's 5 px/mm, as the ruler measured them (the whole frame)
    sheet_ppm = W / 480.0
    e = eyes.edge_widths(L, sheet_ppm, mask=None)
    if e.get("edge_n"):
        add("sharpest edges, p10 of the 10-90% rise (mm, sheet)", e["edge_p10_mm"], None, T["edge_p10_mm"].get("p90"))
    return rows, (cb[0] if cb else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--stem", required=True)
    ap.add_argument("--style", default="graphite-hyperrealism")
    ap.add_argument("--json")
    a = ap.parse_args()
    rows, box = check(a.image, a.stem, a.style)
    for r in rows:
        b = (f">= {r['lo']:.3g}" if r["hi"] is None else (f"<= {r['hi']:.3g}" if r["lo"] is None else f"{r['lo']:.3g}-{r['hi']:.3g}"))
        print(f"  {'pass' if r['ok'] else 'FAIL'}  {r['check']}: {r['value']}  (ruler {b})")
    print(f"{sum(r['ok'] for r in rows)} of {len(rows)} within the close-up ruler; cheek patch {box}")
    if a.json:
        json.dump(dict(rows=rows, cheek_box=box), open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
