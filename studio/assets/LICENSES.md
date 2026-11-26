# Asset licences and provenance

Every third-party asset the studio uses, where it comes from and under what licence. Large asset files are not versioned: `tools/fetch_human.py` fetches them from GitHub into `~/.cache/teodor/` (raw checkouts in `~/.cache/teodor/src/`, the compiled file the studio reads in `~/.cache/teodor/human/mh_hm08.npz`, about 6 MB).

## The human mesh (`studio/v8/human.py`)

### MakeHuman 1.x assets: CC0 1.0

- **Source:** [github.com/makehumancommunity/makehuman](https://github.com/makehumancommunity/makehuman), commit `a8bc2d54ff0ac92e78ff71431b1023eda42bf482` (2024-06-26), fetched sparsely and shallowly over anonymous git.
- **Files used:**
  - `makehuman/data/3dobjs/base.obj`: the hm08 base mesh (13 380 body vertices, with helper geometry for the eyes, teeth and tongue; the eyelash, hair, skirt, tights and genital helpers and the joint cubes are not drawn).
  - `makehuman/data/targets/macrodetails/*.target`: the macro targets (sex x age x ancestry; sex x age x muscle x weight), 132 files.
  - `makehuman/data/targets/expression/units/*/*.target`: the 32 expression unit targets for each of the three ancestries.
  - `makehuman/data/targets/breast/nipple-point-decr.target`, `nipple-size-decr.target`, `breast-point-decr.target`: used under clothing.
  - `makehuman/data/rigs/default.mhskel` and `default_weights.mhw`: the 163-bone default skeleton and its skin weights.
- **Licence:** CC0 1.0 Universal. The repository's `LICENSE.md`, section C: "The assets are defined as any data contributing to the graphical output of MakeHuman. This includes: The base mesh and proxies, Targets and modifiers, Textures, Clothes (any MHCLO-based asset), Poses and expressions. These assets have been released under CC0 1.0 Universal." Section D: no claim is made over output such as renders. The full legal text is the repository's `LICENSE.ASSETS.md`; each file's header repeats "This asset was explicitly released as CC0 in september 2020". The project's FAQ ([What changed regarding the license in 2020?](https://static.makehumancommunity.org/oldsite/faq/what_changed_regarding_the_license_in_2020.html)): "Targets, proxies and the base mesh are considered graphical assets, covered by CC0".
- **Copyright holders at the time of release** (from the file headers): Data Collection AB, Joel Palmius, Jonas Hauquier; the targets' original copyright Manuel Bastioni (2014), transferred to the team in 2016. CC0 asks for no attribution; it is given here anyway.
- **The code is not used.** MakeHuman's program code is AGPL 3 (`LICENSE.CODE.md`). The studio reads the asset files with its own code (`tools/fetch_human.py`, `studio/v8/human.py`); the way macro targets are mixed (each macro variable split between its neighbouring target levels) is re-implemented from the documented behaviour, not copied.

### MPFB2 region masks: CC0 1.0

- **Source:** [github.com/makehumancommunity/mpfb2](https://github.com/makehumancommunity/mpfb2), commit `650c5c53bd6989a8ac264f31fa1d11d4a0c7bd8a` (2026-11-22).
- **Files used:** `src/mpfb/data/textures/mpfb_lips.jpg`, `mpfb_face.jpg`, `mpfb_eyelids.jpg`, `mpfb_fingernails.jpg`, `mpfb_inside-mouth.jpg`: greyscale masks in the base mesh's UV layout, sampled at each vertex (lips, the face element, nails, the inside of the mouth).
- **Licence:** CC0 1.0 (the repository's `LICENSE.ASSETS.md` is the CC0 1.0 Universal text; `LICENSE.md` separates the GPL code from the CC0 assets). The code is not used.

### Not reachable, so not used

- **MakeHuman's asset library** (hair, eyebrows, eyelashes, clothes, the high-poly eyes: `github.com/makehumancommunity/makehuman-assets`, also CC0) refuses anonymous git reads here, and the project's download site is not on GitHub; it was not worked around. Hair and clothes stay the studio's own simulated masses (`figure.hair_part`, `dress_part`, `shawl_part`), now resting on the mesh.

### Considered and excluded

- **SMPL, SMPL-X, MANO** (Max Planck Institute for Intelligent Systems): the model licences allow "non-commercial scientific research" only, forbid redistribution and require registration on the institute's own site ([SMPL model licence](https://smpl.is.tue.mpg.de/modellicense.html), [SMPL-X model licence](https://smpl-x.is.tue.mpg.de/modellicense.html)). SMPL-Body is CC BY 4.0 ([licence](https://smpl.is.tue.mpg.de/license.html)) but is only the template body, served from the same registration site, not from GitHub.
- **MB-Lab** (the successor of ManuelbastioniLAB): its base models are AGPL 3 and characters made from them stay AGPL 3 ([MB-Lab licence](https://mb-lab-docs.readthedocs.io/en/latest/license.html)); not an open licence in the sense this repository needs (MIT code, CC0-clean assets).
