"""Fetch and compile the human mesh assets for the studio's people (studio/v8/human.py).

  python3 tools/fetch_human.py            fetch (if needed) and compile into ~/.cache/teodor/human/
  python3 tools/fetch_human.py --force    fetch and compile again

What it takes (all CC0 1.0; provenance and licence in studio/assets/LICENSES.md):
- the MakeHuman 1.x base mesh hm08 (makehuman/data/3dobjs/base.obj), its macro targets (sex, age, muscle,
  weight, ancestry: makehuman/data/targets/macrodetails, without the height and proportion subfolders),
  the expression unit targets (targets/expression/units), three breast targets for clothed figures
  (targets/breast/nipple-point-decr, nipple-size-decr, breast-point-decr) and the default skeleton with its skin weights
  (rigs/default.mhskel, rigs/default_weights.mhw), from github.com/makehumancommunity/makehuman at a
  pinned commit;
- five region masks in the base mesh's UV layout (lips, face, eyelids, fingernails, inside of the mouth) from MPFB2
  (github.com/makehumancommunity/mpfb2, src/mpfb/data/textures), at a pinned commit.

Only GitHub is used (anonymous git reads, sparse and shallow, so about 110 MB of targets come down and
nothing else). The raw checkout stays in ~/.cache/teodor/src/ and is never committed; the compiled
file (~/.cache/teodor/human/mh_hm08.npz, about 20 MB) is what the studio reads. Large asset files stay
out of git (AGENTS.md rule 8).
"""
import glob, json, os, subprocess, sys
import numpy as np

CACHE = os.path.expanduser("~/.cache/teodor")
SRC = os.path.join(CACHE, "src")
OUT = os.path.join(CACHE, "human", "mh_hm08.npz")
MH = dict(url="https://github.com/makehumancommunity/makehuman", commit="a8bc2d54ff0ac92e78ff71431b1023eda42bf482",
          dir="makehuman", paths=["/LICENSE.md", "/LICENSE.ASSETS.md", "/makehuman/data/3dobjs/base.obj",
                                  "/makehuman/data/targets/macrodetails/*.target", "/makehuman/data/targets/expression/units/",
                                  "/makehuman/data/targets/breast/nipple-point-decr.target", "/makehuman/data/targets/breast/nipple-size-decr.target",
                                  "/makehuman/data/targets/breast/breast-point-decr.target",
                                  "/makehuman/data/rigs/default.mhskel", "/makehuman/data/rigs/default_weights.mhw"])
MPFB = dict(url="https://github.com/makehumancommunity/mpfb2", commit="650c5c53bd6989a8ac264f31fa1d11d4a0c7bd8a",
            dir="mpfb2", paths=["/LICENSE.md", "/LICENSE.ASSETS.md", "/src/mpfb/data/textures/mpfb_lips.jpg",
                                "/src/mpfb/data/textures/mpfb_face.jpg", "/src/mpfb/data/textures/mpfb_eyelids.jpg",
                                "/src/mpfb/data/textures/mpfb_fingernails.jpg", "/src/mpfb/data/textures/mpfb_inside-mouth.jpg"])
UNIT = 0.1            # MakeHuman units are decimeters


def git(*a, cwd=None):
    env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1", GIT_TERMINAL_PROMPT="0")
    subprocess.run(["git", *a], cwd=cwd, check=True, env=env)


def fetch(repo, force=False):
    d = os.path.join(SRC, repo["dir"] + "-" + repo["commit"][:10])
    stamp = os.path.join(d, ".teodor_ok")
    if os.path.exists(stamp) and not force:
        return d
    os.makedirs(d, exist_ok=True)
    if not os.path.isdir(os.path.join(d, ".git")):
        git("init", "-q", cwd=d)
        git("remote", "add", "origin", repo["url"], cwd=d)
    git("config", "core.sparseCheckout", "true", cwd=d)
    with open(os.path.join(d, ".git", "info", "sparse-checkout"), "w") as f:
        f.write("\n".join(repo["paths"]) + "\n")
    git("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", repo["commit"], cwd=d)
    git("checkout", "-q", repo["commit"], cwd=d)
    open(stamp, "w").write(repo["commit"])
    return d


def read_target(path):
    idx, dl = [], []
    for line in open(path):
        if not line.strip() or line.startswith("#"):
            continue
        a = line.split()
        idx.append(int(a[0])); dl.append([float(a[1]), float(a[2]), float(a[3])])
    return np.asarray(idx, np.int32), np.asarray(dl, np.float32).reshape(-1, 3) * UNIT


def read_obj(path):
    V, VT, F, FT, G = [], [], [], [], []
    groups, g = [], -1
    for line in open(path):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("vt "):
            VT.append([float(x) for x in line.split()[1:3]])
        elif line.startswith("g "):
            groups.append(line.split(None, 1)[1].strip()); g = len(groups) - 1
        elif line.startswith("f "):
            a = [t.split("/") for t in line.split()[1:]]
            F.append([int(t[0]) - 1 for t in a]); FT.append([int(t[1]) - 1 for t in a]); G.append(g)
    return (np.asarray(V, np.float32) * UNIT, np.asarray(VT, np.float32), np.asarray(F, np.int32), np.asarray(FT, np.int32),
            np.asarray(G, np.int16), groups)


def compile_assets(mh, mp):
    from PIL import Image
    data = os.path.join(mh, "makehuman", "data")
    V, VT, F, FT, G, groups = read_obj(os.path.join(data, "3dobjs", "base.obj"))
    out = dict(verts=V, faces=F, face_group=G, groups=np.array(groups))
    # one UV per vertex (the first face corner that uses it; seams do not matter for region masks)
    uv = np.zeros((len(V), 2), np.float32)
    uv[F.ravel()[::-1]] = VT[FT.ravel()[::-1]]
    out["uv"] = uv
    # targets: concatenated sparse deltas
    names, offs, I, D = [], [0], [], []
    tdirs = sorted(glob.glob(os.path.join(data, "targets", "macrodetails", "*.target"))) + \
        sorted(glob.glob(os.path.join(data, "targets", "expression", "units", "*", "*.target"))) + \
        sorted(glob.glob(os.path.join(data, "targets", "breast", "*.target")))
    for p in tdirs:
        i, d = read_target(p)
        rel = os.path.relpath(p, os.path.join(data, "targets"))[:-7]
        names.append(rel); I.append(i); D.append(d); offs.append(offs[-1] + len(i))
    out.update(t_names=np.array(names), t_off=np.asarray(offs, np.int64), t_idx=np.concatenate(I), t_d=np.concatenate(D).astype(np.float16))
    # skeleton: bones in parent-first order, joints as vertex lists
    sk = json.load(open(os.path.join(data, "rigs", "default.mhskel")))
    bones = sk["bones"]
    order, seen = [], set()

    def visit(b):
        if b in seen:
            return
        p = bones[b]["parent"]
        if p:
            visit(p)
        seen.add(b); order.append(b)
    for b in bones:
        visit(b)
    out["bones"] = np.array(order)
    out["bone_parent"] = np.array([order.index(bones[b]["parent"]) if bones[b]["parent"] else -1 for b in order], np.int32)
    jn = sorted(sk["joints"])
    out["joint_names"] = np.array(jn)
    jo = [0]
    JI = []
    for j in jn:
        JI += sk["joints"][j]; jo.append(len(JI))
    out["joint_off"], out["joint_idx"] = np.asarray(jo, np.int32), np.asarray(JI, np.int32)
    out["bone_head"] = np.array([jn.index(bones[b]["head"]) for b in order], np.int32)
    out["bone_tail"] = np.array([jn.index(bones[b]["tail"]) for b in order], np.int32)
    w = json.load(open(os.path.join(data, "rigs", "default_weights.mhw")))["weights"]
    WB, WV, WW = [], [], []
    for b, lst in w.items():
        bi = order.index(b)
        for v, ww in lst:
            WB.append(bi); WV.append(v); WW.append(ww)
    out.update(w_bone=np.asarray(WB, np.int16), w_vert=np.asarray(WV, np.int32), w_w=np.asarray(WW, np.float32))
    # region masks from MPFB2, sampled at each vertex's UV (v up)
    tex = os.path.join(mp, "src", "mpfb", "data", "textures")
    for k in ("lips", "face", "eyelids", "fingernails", "inside-mouth"):
        im = np.asarray(Image.open(os.path.join(tex, f"mpfb_{k}.jpg")).convert("L"), np.float32) / 255
        h, w_ = im.shape
        x = np.clip((uv[:, 0] * (w_ - 1)).round().astype(int), 0, w_ - 1)
        y = np.clip(((1 - uv[:, 1]) * (h - 1)).round().astype(int), 0, h - 1)
        out["mask_" + k.replace("-", "_")] = im[y, x].astype(np.float16)
    out["provenance"] = np.array(json.dumps({"makehuman": MH["url"] + "@" + MH["commit"], "mpfb2": MPFB["url"] + "@" + MPFB["commit"],
                                             "licence": "CC0 1.0 (LICENSE.ASSETS.md in both repositories)"}))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp.npz"
    np.savez_compressed(tmp, **out)
    os.replace(tmp, OUT)
    return OUT


def main():
    force = "--force" in sys.argv
    if os.path.exists(OUT) and not force:
        print(OUT, "(already there; --force to rebuild)")
        return
    mh, mp = fetch(MH, force), fetch(MPFB, force)
    print(compile_assets(mh, mp), f"{os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
