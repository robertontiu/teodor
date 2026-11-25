"""Build studio/pigments.json from downloaded, cached data (see provenance in the file)."""
import csv, json, re, html, sys, os
import numpy as np
from scipy.optimize import least_squares
import colour

sys.path.insert(0, "/home/claude/teodor/studio/v8")
from media.base import pigment as engine_pigment, kmix as engine_kmix

WL = np.arange(400, 701, 10)
CMF = colour.MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]
D65 = colour.SDS_ILLUMINANTS["D65"]
cmf = np.array([CMF[w] for w in WL]); ill = np.array([D65[w] for w in WL])
kY = 100 / np.sum(ill * cmf[:, 1])


def spec_to_xyz(R):
    return kY * np.sum((ill * R)[:, None] * cmf, 0)


def xyz_to_srgb(X):
    lin = colour.XYZ_to_RGB(X / 100, colour.RGB_COLOURSPACES["sRGB"], apply_cctf_encoding=False)
    lin = np.clip(lin, 0, 1)
    enc = colour.cctf_encoding(lin, function="sRGB")
    return lin, enc


def lab(X):
    return colour.XYZ_to_Lab(X / 100, colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"])


M_XYZ2RGB = np.array(colour.RGB_COLOURSPACES["sRGB"].matrix_XYZ_to_RGB)
# channel weights per wavelength: the sRGB primaries' response to each wavelength under D65 (negative lobes clipped)
_W = np.clip((M_XYZ2RGB @ (cmf * ill[:, None]).T), 0, None)   # (3, n)
W_RGB = _W / _W.sum(1, keepdims=True)


def band(v):
    """Spectral K or S -> 3 channel values (R, G, B) for an RGB two-constant Kubelka-Munk engine."""
    return W_RGB @ v


def r3(a, n=4):
    return [round(float(v), n) for v in np.ravel(a)]


# ---------------------------------------------------------------- Revigo (Geldof et al. 2018), CC0
K1, K2 = 0.04, 0.49          # Saunderson constants used by Geldof et al. 2018 (SCI data)


def unsaunderson(Rm):
    return np.clip((Rm - K1) / (1 - K1 - K2 + K2 * Rm), 1e-4, 0.9999)


def saunderson(Ri):
    return K1 + (1 - K1) * (1 - K2) * Ri / (1 - K2 * Ri)


def seen(Ri):
    """Specular excluded (SCE): the colour away from glare, i.e. without the 4% first-surface reflection."""
    return (1 - K1) * (1 - K2) * Ri / (1 - K2 * Ri)


def km_film(K, S, Rg, x=1.0):
    S = np.maximum(S, 1e-6)
    a = 1 + K / S
    b = np.sqrt(a * a - 1)
    cth = 1 / np.tanh(np.minimum(b * S * x, 50))
    return (1 - Rg * (a - b * cth)) / (a - Rg + b * cth)


def fit_ks(Rob, Row, Rgb, Rgw):
    """Per wavelength (K, S) for one film (x = 1) from its internal reflectance over two backgrounds."""
    K, S = [], []
    for i in range(len(Rob)):
        def res(p):
            k, s = np.exp(p)
            return [km_film(k, s, Rgb[i]) - Rob[i], km_film(k, s, Rgw[i]) - Row[i]]
        best = None
        for s0 in (0.1, 1, 10, 50):
            for k0 in (0.01, 0.3, 3):
                r = least_squares(res, np.log([k0, s0]), bounds=(np.log([1e-5, 1e-4]), np.log([1e3, 1e3])))
                if best is None or r.cost < best.cost:
                    best = r
        k, s = np.exp(best.x); K.append(k); S.append(s)
    return np.array(K), np.array(S)


def fit_joint(films, Kw, Sw):
    """films: list of (c, Rob_i, Row_i, Rgb_i, Rgw_i) with c the pigment weight fraction (rest zinc white, K Kw S Sw).
    Fits the pigment's K, S per wavelength so that Duncan mixtures reproduce every film over both backgrounds."""
    n = len(films[0][1]); K, S, rms = [], [], []
    for i in range(n):
        def res(p):
            k, s_ = np.exp(p); r = []
            for c, ob, ow, gb, gw in films:
                km, sm = c * k + (1 - c) * Kw[i], c * s_ + (1 - c) * Sw[i]
                w = 1.0 if c > 0.95 else 0.7
                r += [w * (km_film(km, sm, gb[i]) - ob[i]), w * (km_film(km, sm, gw[i]) - ow[i])]
            return r
        best = None
        for s0 in (0.1, 1, 10, 50):
            for k0 in (0.01, 0.3, 3, 30):
                r = least_squares(res, np.log([k0, s0]), bounds=(np.log([1e-5, 1e-4]), np.log([1e4, 1e3])))
                if best is None or r.cost < best.cost:
                    best = r
        k, s_ = np.exp(best.x); K.append(k); S.append(s_); rms.append(np.sqrt(np.mean(np.square(best.fun))))
    return np.array(K), np.array(S), float(np.mean(rms))


def load_revigo():
    d = "" + os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data")) + "/revigo/repo/data/"
    rows = list(csv.reader(open(d + "revigo-aggregated-palette-spectral-data.txt"), delimiter="\t"))
    spec = {r[0]: np.array([float(v) for v in r[1:]]) / 100 for r in rows[1:]}
    mix = {}
    for line in open(d + "revigo-mixture-specifications.txt"):
        k, v = line.strip().split("\t")
        names, frac = v.split("|")
        mix[k] = (names.split("-"), [float(f) for f in frac.split("-")])
    return spec, mix


REVIGO_CI = {"Eosin1Wax": ("eosine (geranium) lake, 1.5% wax", "PR90"), "Eosin": ("eosine (geranium) lake", "PR90"),
             "Eosin2PbWax": ("eosine lake on lead, with wax", "PR90"), "Cochineal": ("cochineal (carmine) lake", "NR4"),
             "Minium": ("red lead (minium)", "PR105"), "Vermillion": ("vermilion", "PR106"),
             "ZincWhite": ("zinc white", "PW4"), "ZincWhiteLinseed": ("zinc white (linseed oil)", "PW4"),
             "LeadWhite": ("lead white", "PW1"), "ViridianGreen": ("viridian", "PG18"),
             "EmeraldGreen": ("emerald green", "PG21"), "UltramarineBlue": ("synthetic ultramarine", "PB29"),
             "CobaltBlue": ("cobalt blue", "PB28"), "PrussianBlue": ("Prussian blue", "PB27"),
             "ChromeYellow": ("chrome yellow (lead chromate)", "PY34"), "ChromeYellowPoppyseed": ("chrome yellow, poppy oil", "PY34"),
             "ChromeYellowOtero": ("lemon chrome yellow (W&N process)", "PY34"),
             "BariumSulphate": ("barium sulphate (extender)", "PW21"), "CalciumCarbonate": ("chalk (extender)", "PW18"),
             "BoneBlack": ("bone black", "PBk9")}


def revigo_entries():
    spec, mix = load_revigo()
    out, tints = [], []
    I = lambda code: [unsaunderson(spec[f"{code}_{s}"]) for s in ("ob", "ow", "b", "w")]
    zob, zow, zb, zw_ = I("07A")
    Kw, Sw = fit_ks(zob, zow, zb, zw_)
    todo = [(c, n, f) for c, (n, f) in mix.items() if len(f) and f[0] == 100]
    todo.append(("07CDEF", ["BoneBlack"], [100]))
    for code, names, frac in todo:
        if code == "07CDEF":
            films = [(mix[c][1][1] / 100, *I(c)) for c in ("07C", "07D", "07E", "07F")]
            K, S, rms = fit_joint(films, Kw, Sw)
            Rb, Rob, Row, Rw = (spec[f"07E_{s}"] for s in ("b", "ob", "ow", "w"))
        else:
            Rb, Rob, Row, Rw = (spec[f"{code}_{s}"] for s in ("b", "ob", "ow", "w"))
            ib, iob, iow, iw = map(unsaunderson, (Rb, Rob, Row, Rw))
            tcodes = [c for c, (n, f) in mix.items() if c[:2] == code[:2] and c != code and len(n) > 1 and n[1] == "ZincWhite"
                      and n[0] == names[0] and f[0] not in (0, 100) and (len(f) < 3 or f[2] == 0)]
            if names[0] == "ZincWhite":
                K, S = Kw, Sw; rms = 0.0
            elif tcodes:
                films = [(1.0, iob, iow, ib, iw)] + [(mix[c][1][0] / 100, *I(c)) for c in tcodes]
                K, S, rms = fit_joint(films, Kw, Sw)
            else:
                K, S = fit_ks(iob, iow, ib, iw); rms = None
        hiding = float(np.max(np.abs(Row - Rob))) < 0.02
        Rinf_i = 1 + K / S - np.sqrt((K / S) ** 2 + 2 * K / S)
        Rinf = seen(Rinf_i)
        # what the engine needs: the film (x = 1, the 100 um drawdown) over ideal white and ideal black, as seen (SCI)
        ow_ideal = seen(km_film(K, S, np.full_like(K, 0.999)))
        ob_ideal = seen(km_film(K, S, np.zeros_like(K)))
        gw = seen(km_film(K, S, np.full_like(K, 0.999), 0.1))     # a glaze: a tenth of the drawdown (~10 um wet)
        gb = seen(km_film(K, S, np.zeros_like(K), 0.1))
        cols = {}
        for nm, R in (("masstone", Rinf), ("measured_over_white", np.clip(Row - K1, 0, 1)), ("measured_over_black", np.clip(Rob - K1, 0, 1)),
                      ("film_over_white", ow_ideal), ("film_over_black", ob_ideal),
                      ("glaze_over_white", gw), ("glaze_over_black", gb)):
            X = spec_to_xyz(R); lin, enc = xyz_to_srgb(X)
            cols[nm] = dict(srgb=r3(enc, 3), linear=r3(lin, 4), lab=r3(lab(X), 1))
        Ke, Se = engine_pigment(np.array(cols["glaze_over_white"]["srgb"]), np.array(cols["glaze_over_black"]["srgb"]))
        name, ci = REVIGO_CI.get(names[0], (names[0], None))
        e = dict(id="oil_" + re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_"), name=name, ci=ci, medium="oil",
                 binder=("poppyseed oil" if names[0] in ("ZincWhite", "LeadWhite", "UltramarineBlue", "PrussianBlue", "CobaltBlue", "ChromeYellowPoppyseed") else "linseed oil"),
                 sample=("Revigo 07C-07F (bone black in zinc white)" if code == "07CDEF" else f"Revigo {code}"), hiding_at_film=hiding,
                 colours=cols,
                 engine=dict(thickness="glaze: 0.1 of the 100 um drawdown (K_rgb, S_rgb are per unit of that glaze)",
                             over_white=cols["glaze_over_white"]["srgb"], over_black=cols["glaze_over_black"]["srgb"],
                             K_rgb=r3(Ke), S_rgb=r3(Se), K_rgb_linear_band=r3(band(K)), S_rgb_linear_band=r3(band(S)),
                             note="sRGB-encoded 0..1 (the engine's hx convention), specular excluded (colour away from glare); feed over_white/over_black to media.base.pigment()"),
                 spectral=dict(wavelengths_nm=[400, 700, 10], K_per_film=r3(K, 4), S_per_film=r3(S, 4),
                               R_inf=r3(Rinf, 4), unit="per film of the 100 um drawdown (wet applicator gap); Saunderson k1=0.04, k2=0.49 removed before fitting"),
                 opacity=round(float(1 - np.mean(np.abs(Row - Rob)) / max(1e-3, np.mean(Rw - Rb))), 3),
                 fit=dict(films=("masstone + zinc-white tints (Duncan, weight fractions)" if rms not in (None, 0.0) else "masstone film only"),
                          rms_internal_reflectance=(None if rms is None else round(rms, 4))),
                 source="revigo")
        out.append(e)
        if names[0] == "ZincWhite":
            zw = Rinf
    # tints with zinc white: the measured colour vs the engine's kmix and a spectral two-constant KM (Duncan) prediction
    base = {e["sample"].split()[1]: e for e in out}
    for code, (names, frac) in mix.items():
        if len(names) < 2 or names[1] != "ZincWhite" or frac[0] in (100, 0) or (len(frac) > 2 and frac[2] != 0):
            continue
        mcode = code[:2] + "A"
        if mcode not in base:
            continue
        m = base[mcode]
        X = spec_to_xyz(np.clip(spec[f"{code}_ow"] - K1, 0, 1)); lin, enc = xyz_to_srgb(X)
        t_white = frac[1] / 100
        pred = engine_kmix(np.array(m["colours"]["masstone"]["srgb"], np.float32), np.array(base["07A"]["colours"]["masstone"]["srgb"], np.float32), t_white)
        Km, Sm = np.array(m["spectral"]["K_per_film"]), np.array(m["spectral"]["S_per_film"])
        Kw, Sw = np.array(base["07A"]["spectral"]["K_per_film"]), np.array(base["07A"]["spectral"]["S_per_film"])
        c = 1 - t_white
        Km_, Sm_ = c * Km + (1 - c) * Kw, c * Sm + (1 - c) * Sw
        Rd = seen(1 + Km_ / Sm_ - np.sqrt((Km_ / Sm_) ** 2 + 2 * Km_ / Sm_))
        Xd = spec_to_xyz(Rd)
        plab = colour.XYZ_to_Lab(colour.RGB_to_XYZ(colour.cctf_decoding(np.clip(pred, 0, 1)), colour.RGB_COLOURSPACES["sRGB"]),
                                 colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"])
        # 3-channel two-constant KM (what an RGB engine with per-pigment K and S would do)
        Kb = c * band(Km) + (1 - c) * band(Kw); Sb = c * band(Sm) + (1 - c) * band(Sw)
        Rl = seen(1 + Kb / Sb - np.sqrt((Kb / Sb) ** 2 + 2 * Kb / Sb))
        enc3 = colour.cctf_encoding(np.clip(Rl, 0, 1), function="sRGB")
        lab3 = colour.XYZ_to_Lab(colour.RGB_to_XYZ(Rl, colour.RGB_COLOURSPACES["sRGB"]), colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"])
        tints.append(dict(sample=f"Revigo {code}", pigment=m["name"], pigment_fraction_by_weight=frac[0] / 100,
                          rgb3_km_srgb=r3(enc3, 3), rgb3_km_dE2000=round(float(colour.delta_E(lab(X), lab3, method="CIE 2000")), 1),
                          measured_srgb=r3(enc, 3), measured_lab=r3(lab(X), 1),
                          engine_kmix_srgb=r3(pred, 3), engine_kmix_dE2000=round(float(colour.delta_E(lab(X), plab, method="CIE 2000")), 1),
                          spectral_km_duncan_lab=r3(lab(Xd), 1), spectral_km_dE2000=round(float(colour.delta_E(lab(X), lab(Xd), method="CIE 2000")), 1)))
    return out, tints


# ---------------------------------------------------------------- Pigments Checker FORS (Cosentino 2014)
FORS_CI = {"burntumber": ("burnt umber", "PBr7"), "rawumber": ("raw umber", "PBr7"), "vandykebrown": ("Van Dyke brown", "NBr8"),
           "burntsienna": ("burnt sienna", "PBr7"), "rawsienna": ("raw sienna", "PBr7"), "redochre": ("red ochre", "PR102"),
           "redlead": ("red lead", "PR105"), "cadmiumred": ("cadmium red", "PR108"), "alizarin": ("alizarin crimson", "PR83"),
           "madderlake": ("madder lake", "NR9"), "lacdye": ("lac dye", "NR25"), "carminelake": ("carmine lake", "NR4"),
           "vermilion": ("vermilion", "PR106"), "realgar": ("realgar", None), "yellowlakeresed": ("reseda (weld) lake", "NY2"),
           "massicot": ("massicot", None), "yellowochre": ("yellow ochre", "PY43"), "gamboge": ("gamboge", "NY24"),
           "naplesyellow": ("Naples yellow", "PY41"), "leadtinyellowII": ("lead-tin yellow II", None), "leadtinyellowI": ("lead-tin yellow I", None),
           "saffron": ("saffron", "NY6"), "orpiment": ("orpiment", "PY39"), "cobaltyellow": ("cobalt yellow (aureolin)", "PY40"),
           "cadmiumyellow": ("cadmium yellow", "PY35"), "chromegreen": ("chrome green", None), "cobaltgreen": ("cobalt green", "PG19"),
           "cadmiumgreen": ("cadmium green", None), "greenearth": ("green earth", "PG23"), "viridian": ("viridian", "PG18"),
           "phthalogreen": ("phthalo green", "PG7"), "verdigris": ("verdigris", "PG20"), "malachite": ("malachite", "PG39"),
           "bluebice": ("blue bice (verditer)", "PB30"), "cobaltblue": ("cobalt blue", "PB28"), "azurite": ("azurite", "PB30"),
           "egyptianblue": ("Egyptian blue", "PB31"), "ultramarine": ("ultramarine", "PB29"), "phthaloblue": ("phthalo blue", "PB15"),
           "smalt": ("smalt", "PB32"), "indigo": ("indigo", "NB1"), "mayablue": ("Maya blue", None), "prussianblue": ("Prussian blue", "PB27"),
           "cobaltviolet": ("cobalt violet", "PV14"), "ivoryblack": ("ivory black", "PBk9"), "vineblack": ("vine black", "PBk8"),
           "boneblack": ("bone black", "PBk9"), "lampblack": ("lamp black", "PBk6"), "gypsum": ("gypsum", "PW25"), "chalk": ("chalk", "PW18"),
           "leadwhite": ("lead white", "PW1"), "zincwhite": ("zinc white", "PW4"), "titaniumwhite": ("titanium white", "PW6"), "lithopone": ("lithopone", "PW5")}
ORDER = list(FORS_CI)


def fors():
    d = "" + os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data")) + "/chsos/zip/CSV/"
    res = {}
    for f, binder in (("gum Arabic", "gum arabic"), ("egg tempera", "egg tempera"), ("linseed oil", "linseed oil"), ("fresco", "fresco")):
        rows = list(csv.reader(open(d + f + ".csv", encoding="latin-1")))
        a = np.array([[float(x) if x else np.nan for x in r] for r in rows[1:]])
        wl = a[:, 0]
        for j, key in enumerate(ORDER):     # the columns are in the same order in every file (headers are spelled differently)
            col = a[:, j + 1]
            if np.nanmax(np.abs(col - wl)) < 1:   # a column that repeats the wavelength (linseed oil, Van Dyke brown)
                continue
            # 400-700 nm at 10 nm: mean over +-5 nm
            R = np.array([np.nanmean(col[(wl >= w - 5) & (wl < w + 5)]) for w in WL]) / 100
            res.setdefault(key, {})[binder] = R
    out = {}
    # the files' scale is relative (whites read above 100%, carbon blacks about 10%): normalise each binder per
    # wavelength so its lamp black reads 0.03 and its titanium white 0.90 (an assumption; see the source note)
    for binder in ("gum arabic", "egg tempera", "linseed oil", "fresco"):
        tw = res.get("titaniumwhite", {}).get(binder); lb = res.get("lampblack", {}).get(binder)
        for key in ORDER:
            R = res.get(key, {}).get(binder)
            if R is None or tw is None or lb is None:
                continue
            Rn = 0.03 + (R - lb) * (0.90 - 0.03) / np.maximum(tw - lb, 1e-3)
            X = spec_to_xyz(np.clip(Rn, 0.005, 1)); lin, enc = xyz_to_srgb(X)
            out.setdefault(key, {})[binder] = dict(srgb=r3(enc, 3), lab=r3(lab(X), 1))
    return out


# ---------------------------------------------------------------- handprint (MacEvoy) watercolour ratings
def handprint():
    hp = json.load(open("" + os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data")) + "/handprint/handprint_ratings.json"))
    # first-use dates from the pigment rows ("chemical name (date)")
    dates = {}
    for p in ["waterc", "waterr", "watero", "watere", "watery", "waterg", "waterb", "waterv", "waterw"]:
        t = open(f"" + os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data")) + f"/handprint/{p}.html", encoding="latin-1").read()
        t = html.unescape(re.sub(r"<[^>]+>", " ", t)); t = re.sub(r"\s+", " ", t)
        for m in re.finditer(r"\b(P[A-Z][a-z]?[A-Z]?\d+(?::\d+)?) ([a-z][^()]{2,90}?) \(((?:[^()]*\d{4}[^()]*)|antiquity[^()]*)\)", t):
            dates.setdefault(m.group(1), dict(chemical=m.group(2).strip(), date=m.group(3).strip()))
    return hp, dates


def main():
    rev, tints = revigo_entries()
    fo = fors()
    hp, dates = handprint()
    # pigment library keyed by CI name (one entry per pigment), media blocks inside
    lib = {}

    GROUP = {"PBr7": "natural iron oxide earths (raw/burnt sienna, raw/burnt umber)", "PBk9": "bone / ivory black",
             "PB30": "azurite / blue verditer (basic copper carbonate)"}

    def entry(ci, name):
        name = GROUP.get(ci, name)
        k = ci or name
        e = lib.setdefault(k, dict(ci=ci, name=name, media={}, provenance=[]))
        if ci in dates and "chemical" not in e:
            e["chemical"] = dates[ci]["chemical"]; e["first_use"] = dates[ci]["date"]; e["provenance"].append("first_use: handprint")
        return e

    for r in rev:
        e = entry(r["ci"], r["name"])
        blk = {k: r[k] for k in ("binder", "sample", "hiding_at_film", "opacity", "fit", "colours", "engine", "spectral")}
        e["media"].setdefault("oil", []).append(dict(name=r["name"], **blk))
        if "revigo" not in e["provenance"]:
            e["provenance"].append("revigo")
    for key, by in fo.items():
        name, ci = FORS_CI[key]
        e = entry(ci, name)
        e.setdefault("masstone_by_binder", {})[name] = by
        if "fors" not in e["provenance"]:
            e["provenance"].append("fors")
    for ci, r in hp.items():
        if not r.get("paints"):
            continue
        if "+" in ci:
            continue
        nm = r.get("common_name") or (dates.get(ci, {}).get("chemical")) or ci
        e = entry(ci, nm)
        wc = dict(n_paints=r["n_paints"], transparency_0_4=r["Tr_median"], staining_0_4=r["St_median"],
                  value_range=r["VR_median"], granulation_0_4=r["Gr_median"], blossom_0_4=r["Bl_median"],
                  diffusion_0_4=r["Df_median"], hue_angle_cielab=r["HA_median"])
        if "ciecam_Jab" in r:
            wc["ciecam_Jab_masstone"] = r["ciecam_Jab"]
        if "drying_shift_pct" in r:
            wc["drying_shift_lightness_pct"] = r["drying_shift_pct"]
        wc["engine"] = dict(granulation=round(r["Gr_median"] / 4, 3), staining=round(r["St_median"] / 4, 3),
                            opacity=round(1 - r["Tr_median"] / 4, 3), darkest_L=round(max(0.0, 94 - r["VR_median"]), 1),
                            note="granulation, staining = rating/4; opacity = 1 - transparency/4; darkest_L ~ paper value (~94) minus value range")
        if ci == "PBr7":   # natural iron oxides: split by marketing name
            sub = {}
            for p in r["paints"]:
                n = p["name"].lower()
                for k in ("burnt sienna", "raw sienna", "burnt umber", "raw umber"):
                    if k in n:
                        sub.setdefault(k, []).append(p)
            wc["by_name"] = {k: dict(n=len(v), **{a: float(np.median([x[a] for x in v])) for a in ("Tr", "St", "VR", "Gr", "Bl", "Df")}) for k, v in sub.items()}
        e["media"]["watercolour"] = wc
        if "handprint" not in e["provenance"]:
            e["provenance"].append("handprint")

    curtis = [("Quinacridone Rose", [0.22, 1.47, 0.57], [0.05, 0.003, 0.03], 0.02, 5.5, 0.81),
              ("Indian Red", [0.46, 1.07, 1.50], [1.28, 0.38, 0.21], 0.05, 7.0, 0.40),
              ("Cadmium Yellow", [0.10, 0.36, 3.45], [0.97, 0.65, 0.007], 0.05, 3.4, 0.81),
              ("Hookers Green", [1.62, 0.61, 1.64], [0.01, 0.012, 0.003], 0.09, 1.0, 0.41),
              ("Cerulean Blue", [1.52, 0.32, 0.25], [0.06, 0.26, 0.40], 0.01, 1.0, 0.31),
              ("Burnt Umber", [0.74, 1.54, 2.10], [0.09, 0.09, 0.004], 0.09, 9.3, 0.90),
              ("Cadmium Red", [0.14, 1.08, 1.68], [0.77, 0.015, 0.018], 0.02, 1.0, 0.63),
              ("Brilliant Orange", [0.13, 0.81, 3.45], [0.005, 0.009, 0.007], 0.01, 1.0, 0.14),
              ("Hansa Yellow", [0.06, 0.21, 1.78], [0.50, 0.88, 0.009], 0.06, 1.0, 0.08),
              ("Phthalo Green", [1.55, 0.47, 0.63], [0.01, 0.05, 0.035], 0.02, 1.0, 0.12),
              ("French Ultramarine", [0.86, 0.86, 0.06], [0.005, 0.005, 0.09], 0.01, 3.1, 0.91),
              ("Interference Lilac", [0.08, 0.11, 0.07], [1.25, 0.42, 1.43], 0.06, 1.0, 0.08)]

    doc = {
        "about": ("Pigment library for the studio's media, from measured data. Every number has a source in `sources`; "
                  "derived values (sRGB, engine K/S) are computed by tools from the measurements with CIE 1931 2-degree observer, "
                  "D65, 400-700 nm at 10 nm. 'engine.over_white/over_black' are the inputs of studio/v8/media/base.py pigment(); "
                  "they are sRGB-encoded 0..1 like the engine's hx() colours. Built 2026-11-25 (see docs/media-data.md)."),
        "sources": {
            "revigo": dict(cite="M. Geldof, A. Proano Gaibor, F. Ligterink, E. Hendriks, E. Kirchner, 'Reconstructing Van Gogh's palette to determine the optical characteristics of his paints', Heritage Science 6:17 (2018)",
                           doi="10.1186/s40494-018-0181-6", data="https://github.com/fligt/revigo-spectra (data/revigo-aggregated-palette-spectral-data.txt), CC0 1.0",
                           method="hand-ground oil paints (19th-c. recipes and Kremer pigments), drawn down 'relatively uniform layer of 100 um thickness' on a BYK-Gardner black-and-white chart, Konica Minolta CM-2600d d/8 SCI, 400-700 nm / 10 nm. Suffixes: _b black chart, _ob paint over black, _ow paint over white, _w white chart. K and S per wavelength fitted here by two-constant Kubelka-Munk (x = 1 film) after removing a Saunderson correction with the paper's k1 = 0.04, k2 = 0.49.",
                           status="measured; K/S fit computed for this file (the repo's own K/S notebook is empty)"),
            "fors": dict(cite="A. Cosentino, 'FORS spectral database of historical pigments in different binders', e-conservation Journal 2 (2014) 57-68",
                         data="https://chsopensource.org/new-free-pigments-fors-spectroscopy-database (zip of CSV: gum arabic, egg tempera, linseed oil, fresco, powder; 360-1000 nm)",
                         method="54 historical pigments (Pigments Checker swatches) measured with a fibre-optic reflectance spectrometer and integrating sphere. The CSV scale is relative (whites read 100-135%, carbon blacks ~10%); here each binder set is normalised per wavelength so lamp black = 0.03 and titanium white = 0.90 (assumed values), so absolute values are approximate. Use for hue and for ranking pigments by value within a binder; the Revigo oil data and handprint values are the calibrated ones.",
                         status="measured spectra; absolute scale not verified; licence not stated (data offered for free download)"),
            "handprint": dict(cite="B. MacEvoy, handprint.com 'guide to watercolor pigments' (rev. 2015), ratings of 750+ commercial watercolour paints",
                              data="https://www.handprint.com/HP/WCL/waterfs.html (pages waterc/r/o/e/y/g/b/v/w)",
                              method="per paint: Tr transparency 0 (very opaque)-4, St staining 0-4, VR value range (paper value minus masstone value, 100-step scale), Gr granulation 0 (liquid)-4, Bl blossom 0-4, Df diffusion wet-in-wet 0 (inert)-4, HA CIELAB hue angle (GretagMacbeth spectrophotometer). Medians over the brands tested, per Colour Index name. CIECAM J,a,b masstone and drying shift parsed from the notes where given.",
                              status="one experienced tester's standardised swatch tests: ratings are ordinal judgements, colour values are instrument measurements; not peer reviewed"),
            "curtis1997": dict(cite="C. J. Curtis et al., 'Computer-Generated Watercolor', SIGGRAPH 1997, Fig. 5", doi="10.1145/258734.258896",
                               status="NOT measured: K and S were derived from colours the authors chose by eye over white and black; density, staining power and granularity are the authors' simulation settings. Kept as the graphics baseline the studio's watercolour follows.")},
        "kmix_check_tints": tints,
        "pigments": sorted(lib.values(), key=lambda e: (e["ci"] or "Z" + e["name"])),
        "curtis1997_watercolour": [dict(name=n, K=k, S=s, density=d, staining=w, granularity=g) for n, k, s, d, w, g in curtis],
    }
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/teodor/studio/pigments.json"
    with open(out + ".tmp", "w") as f:
        json.dump(doc, f, indent=1)
    os.replace(out + ".tmp", out)
    print("pigments", len(lib), "oil(revigo)", len(rev), "tints", len(tints))
    for key in ("engine_kmix_dE2000", "rgb3_km_dE2000", "spectral_km_dE2000"):
        v = [t[key] for t in tints]; print(key, "median", np.median(v), "max", max(v))
    for t in tints:
        print(f"  {t['sample']:12s} {t['pigment'][:28]:28s} p={t['pigment_fraction_by_weight']:.2f} engine dE={t['engine_kmix_dE2000']:5.1f} rgb3KM dE={t['rgb3_km_dE2000']:5.1f} spectralKM dE={t['spectral_km_dE2000']:5.1f}")


if __name__ == "__main__":
    main()
