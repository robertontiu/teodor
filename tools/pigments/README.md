# How studio/pigments.json and studio/calibration_refs.json were built

Scripts written during the real-data research (2026-11-25; docs/media-data.md describes the sources and method).

- `build_pigments.py` builds `studio/pigments.json` from three sources, downloaded into `$TEODOR_PIGMENT_DATA` (default `~/.cache/teodor/pigment-data/`, never committed):
  - `revigo/repo/`: a clone of github.com/fligt/revigo-spectra (Geldof et al. 2018, Heritage Science, doi:10.1186/s40494-018-0181-6; CC0): 16 hand-ground 19th-century oil paints over black and white, with tints. Two-constant Kubelka-Munk K and S are fitted from these.
  - `chsos/zip/`: the Pigments Checker FORS spectra (Cosentino 2014, chsopensource.org; no licence stated, so only derived colours are kept, and they are hue-only because the reflectance scale is uncalibrated).
  - `handprint/`: watercolour pigment ratings parsed from handprint.com (B. MacEvoy) by `parse_handprint.py` (transparency, staining, granulation, value range, hue): factual ratings, kept with attribution.
- `met_candidates.py`, `met_refs.py` built `studio/calibration_refs.json`: public-domain Met works per medium for measuring real marks (`tools/calibrate_media.py`).
The scripts expect those downloads in place; re-download them to rebuild.
