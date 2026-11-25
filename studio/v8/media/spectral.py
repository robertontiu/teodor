"""Spectral paint mixing (studio v8): a measured two-constant Kubelka-Munk model with an RGB interface.

Colours stay RGB at the interface (sRGB-encoded 0..1, like hx() and cv.col), but mixing happens in
pigment space, the way Mixbox does it (Sochorova and Jamriska 2021): a colour is turned into
concentrations of a palette of real, measured pigments plus a small RGB residual (the part the palette
cannot explain), concentrations and residuals mix linearly, and the forward model turns the mixture back
into RGB. A round trip is exact (mix(a, a, t) == a, mix(a, b, 0) == a); what changes is how colours mix:
each pigment keeps its own tinting strength and hue shift, so 6% Prussian blue in white is still a strong
mid blue (measured), where per-channel RGB Kubelka-Munk (base.kmix) gives a near white.

The model (docs/media-data.md, "Pigments"; docs/calibration/colour.md):
- Palette: the Revigo oil paints (Geldof et al. 2018, CC0) with the spectral K and S per 100 um film that
  tools/pigments/build_pigments.py fitted into studio/pigments.json (31 bands, 400-700 nm), plus zinc white
  and bone black. Mixing follows Duncan's rule: K and S of a mixture are the concentration-weighted sums.
- Forward: R_inf = 1 + K/S - sqrt((K/S)^2 + 2 K/S) per band (internal reflectance), the Saunderson
  surface (k1 = 0.04, k2 = 0.49, Geldof et al.) with the specular part excluded, CIE 1931 2-degree observer,
  D65, sRGB.
- Unmixing: a lookup table over the RGB cube (49^3 nodes, built in about 2 s and cached in ~/.cache/teodor/).
  Each node holds the sparsest palette mixture whose colour is nearest (CIELAB), chosen among sampled
  mixtures (any two paints; one or two chromatic paints with white and black); a paint costs PENALTY dE in
  the choice (white and black less), so a colour one paint matches is that paint, and a grey is white and
  black. Per pixel the table is interpolated trilinearly and the residual makes the round trip exact.
  The engine evaluates 16 bands (20 nm); the validation's spectral reference uses all 31.
- Films: film_over / glaze lay a pigment film over a substrate (the Kubelka-Munk layer equations per
  band, in internal reflectance, the surface counted once on top); thickness in units of the 100 um film.
  glaze(..., ref=x) reads the colour as the glaze's look over white at thickness x (glaze_paint: transparent
  paints thinned with clear oil for dark and saturated colours, white for light ones).
- Canvases: mix_window keeps the pigment state of a canvas (CanvasLatent) while a command runs; paint mixes
  into wet paint and lies as a film over dry paint (WET_MIX, BODY_FILM).

Functions: mix(a, b, t) (same shape semantics as base.kmix), glaze(R0, color, thickness, ref=None),
mix_window(cv, sl, t, b, ...), latent(rgb), from_latent(c, res), forward(c).
`python3 -m media.spectral validate` (from studio/v8) checks the model against the measured Revigo tints and
mixtures (the held-out refits need the raw Revigo spectra: TEODOR_PIGMENT_DATA, as tools/pigments uses).
"""
import os, sys, json, hashlib
import numpy as np

# ---------------------------------------------------------------- colorimetry (400-700 nm, 10 nm)
WL = np.arange(400, 701, 10)
_CMF = np.array([[0.01431, 0.000396, 0.06785], [0.04351, 0.00121, 0.2074], [0.13438, 0.004, 0.6456], [0.2839, 0.0116, 1.3856],
                 [0.34828, 0.023, 1.74706], [0.3362, 0.038, 1.77211], [0.2908, 0.06, 1.6692], [0.19536, 0.09098, 1.28764],
                 [0.09564, 0.13902, 0.81295], [0.03201, 0.20802, 0.46518], [0.0049, 0.323, 0.272], [0.0093, 0.503, 0.1582],
                 [0.06327, 0.71, 0.07825], [0.1655, 0.862, 0.04216], [0.2904, 0.954, 0.0203], [0.43345, 0.99495, 0.00875],
                 [0.5945, 0.995, 0.0039], [0.7621, 0.952, 0.0021], [0.9163, 0.87, 0.00165], [1.0263, 0.757, 0.0011],
                 [1.0622, 0.631, 0.0008], [1.0026, 0.503, 0.00034], [0.85445, 0.381, 0.00019], [0.6424, 0.265, 5e-05],
                 [0.4479, 0.175, 2e-05], [0.2835, 0.107, 0.0], [0.1649, 0.061, 0.0], [0.0874, 0.032, 0.0], [0.04677, 0.017, 0.0],
                 [0.0227, 0.00821, 0.0], [0.011359, 0.004102, 0.0]])
_D65 = np.array([82.7549, 91.486, 93.4318, 86.6823, 104.865, 117.008, 117.812, 114.861, 115.923, 108.811, 109.354, 107.802,
                 104.79, 107.689, 104.405, 104.046, 100.0, 96.3342, 95.788, 88.6856, 90.0062, 89.5991, 87.6987, 83.2886,
                 83.6992, 80.0268, 80.2146, 82.2778, 78.2842, 69.7213, 71.6091])
_XYZ2RGB = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.204, 1.057]])
WHITE = np.array([0.95046, 1.0, 1.08906])                      # D65 white point (CIE 1931 2 deg), for CIELAB
_SPEC2XYZ = (_CMF * _D65[:, None]) / np.sum(_D65 * _CMF[:, 1])   # (31, 3): reflectance spectrum -> XYZ (Y of 1 = white)
_SPEC2LIN = (_SPEC2XYZ @ _XYZ2RGB.T).astype(np.float32)          # (31, 3): reflectance spectrum -> linear sRGB
_YW = (_SPEC2XYZ[:, 1] / _SPEC2XYZ[:, 1].sum()).astype(np.float32)  # luminance weight per band
# The engine evaluates every other band (16 bands, 20 nm), with the colour-matching weights rescaled to keep the
# white point: against all 31 bands the colours of random palette mixtures differ by dE2000 0.18 (median), 0.85
# (95th percentile) (docs/calibration/colour.md). The validation's spectral reference uses all 31.
BANDS = np.arange(0, 31, 2)
_E2XYZ = _SPEC2XYZ[BANDS] * (_SPEC2XYZ.sum(0) / _SPEC2XYZ[BANDS].sum(0))
_E2LIN = (_E2XYZ @ _XYZ2RGB.T).astype(np.float32)
_EYW = (_E2XYZ[:, 1] / _E2XYZ[:, 1].sum()).astype(np.float32)
K1, K2 = 0.04, 0.49                                                 # Saunderson constants (Geldof et al. 2018, SCI data)


def encode(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * np.power(lin, 1 / 2.4) - 0.055)


def decode(enc):
    enc = np.clip(enc, 0, 1)
    return np.where(enc <= 0.04045, enc / 12.92, np.power((enc + 0.055) / 1.055, 2.4))


def rgb_to_lab(rgb):
    """sRGB-encoded (..., 3) -> CIELAB (D65)."""
    X = decode(np.asarray(rgb, np.float64)) @ np.linalg.inv(_XYZ2RGB).T
    return xyz_to_lab(X)


def xyz_to_lab(X):
    f = X / WHITE
    f = np.where(f > (6 / 29) ** 3, np.cbrt(np.maximum(f, 0)), f / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def spectrum_to_rgb(R):
    """Reflectance spectrum (..., 31) -> sRGB-encoded colour (all bands)."""
    return encode(np.asarray(R, np.float64) @ _SPEC2LIN)


def spectrum_to_lab(R):
    return xyz_to_lab(np.asarray(R, np.float64) @ _SPEC2XYZ)


def de2000(lab1, lab2):
    """CIEDE2000 colour difference (Sharma, Wu and Dalal 2005)."""
    L1, a1, b1 = np.moveaxis(np.asarray(lab1, np.float64), -1, 0)
    L2, a2, b2 = np.moveaxis(np.asarray(lab2, np.float64), -1, 0)
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = a1 * (1 + G), a2 * (1 + G)
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    dh = np.where(C1p * C2p == 0, 0, np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh)))
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lmp, Cmp = (L1 + L2) / 2, (C1p + C2p) / 2
    hs = h1p + h2p
    hmp = np.where(C1p * C2p == 0, hs, np.where(np.abs(h1p - h2p) <= 180, hs / 2, np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2)))
    T = 1 - 0.17 * np.cos(np.radians(hmp - 30)) + 0.24 * np.cos(np.radians(2 * hmp)) + 0.32 * np.cos(np.radians(3 * hmp + 6)) - 0.20 * np.cos(np.radians(4 * hmp - 63))
    dth = 30 * np.exp(-(((hmp - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cmp ** 7 / (Cmp ** 7 + 25 ** 7))
    SL = 1 + 0.015 * (Lmp - 50) ** 2 / np.sqrt(20 + (Lmp - 50) ** 2)
    SC, SH = 1 + 0.045 * Cmp, 1 + 0.015 * Cmp * T
    RT = -np.sin(np.radians(2 * dth)) * Rc
    return np.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2 + RT * (dCp / SC) * (dHp / SH))


# ---------------------------------------------------------------- Kubelka-Munk per band
def rinf(K, S):
    """Internal reflectance of an opaque layer; the rationalised form 1/(1 + q + sqrt(q^2 + 2q)) is stable
    for the very large K/S of transparent lakes (S ~ 1e-4)."""
    q = K / np.maximum(S, 1e-7)
    return 1.0 / (1.0 + q + np.sqrt(q * q + 2 * q))


def seen(Ri):
    """Saunderson surface, specular excluded (the colour away from glare), as in pigments.json."""
    return (1 - K1) * (1 - K2) * Ri / (1 - K2 * Ri)


def unseen(Rs):
    """Inverse of seen(): internal reflectance from a specular-excluded reflectance."""
    return Rs / ((1 - K1) * (1 - K2) + K2 * Rs)


def film(K, S, x):
    """Reflectance R and transmittance T (internal, per band) of a film of thickness x (units of the 100 um
    drawdown) with constants K, S: the hyperbolic Kubelka-Munk solution, written with B = bS = sqrt(K(K + 2S))
    and E = exp(-Bx) so it stays finite for clear films (S -> 0) and thick ones."""
    B = np.sqrt(K * (K + 2 * S))
    E = np.exp(-np.minimum(B * x, 40))
    E2 = E * E
    sh = 1 - E2
    den = (S + K) * sh + B * (1 + E2) + 1e-30
    return S * sh / den, 2 * B * E / den


def km_over(K, S, x, Rg):
    """A film over a substrate of internal reflectance Rg: R + T^2 Rg / (1 - R Rg)."""
    R, T = film(K, S, x)
    return R + T * T * Rg / (1 - R * Rg), T


# ---------------------------------------------------------------- the palette (measured)
# (sample code in pigments.json, short name); white first, black second
PALETTE_SAMPLES = [("Revigo 07A", "zinc white"), ("Revigo 07C-07F (bone black in zinc white)", "bone black"),
                   ("Revigo 05A", "red lead"), ("Revigo 06A", "vermilion"), ("Revigo 02A", "eosine lake"),
                   ("Revigo 04A", "cochineal lake"), ("Revigo 14A", "chrome yellow"), ("Revigo 15A", "lemon chrome yellow"),
                   ("Revigo 10A", "emerald green"), ("Revigo 09A", "viridian"), ("Revigo 13A", "Prussian blue"),
                   ("Revigo 12A", "cobalt blue"), ("Revigo 11A", "synthetic ultramarine")]
# The palette's spectral K and S per 100 um film, 400-700 nm / 10 nm, copied from studio/pigments.json (built
# 2026-11-25 by tools/pigments/build_pigments.py from the Revigo data), so the module works in a work dir without
# it. Palette() reads pigments.json when it can find it and uses this copy otherwise.
_EMBEDDED = {
    'Revigo 07A': ([1.3476, 0.1968, 0.1128, 0.0781, 0.0549, 0.0436, 0.034, 0.0305, 0.0252, 0.023, 0.0217, 0.0199, 0.0195, 0.0194, 0.0185, 0.0186, 0.0184, 0.0179, 0.0182, 0.0174, 0.0175, 0.0159, 0.0156, 0.015, 0.0137, 0.0135, 0.0129, 0.0135, 0.0131, 0.0127, 0.0127],
        [60.468, 15.6731, 13.418, 13.0839, 12.0039, 11.3084, 10.5331, 10.1569, 9.451, 9.1173, 8.7782, 8.2944, 8.0008, 7.6324, 7.4628, 7.2596, 7.0106, 6.7379, 6.5641, 6.3666, 6.1468, 6.0835, 5.8985, 5.7224, 5.5847, 5.3869, 5.2873, 5.0795, 4.998, 4.8532, 4.7565]),
    'Revigo 07C-07F (bone black in zinc white)': ([222.6969, 63.1672, 58.9691, 61.1865, 59.6358, 59.1847, 57.5262, 57.7225, 55.9088, 55.556, 55.2351, 53.9348, 53.5608, 52.6361, 52.4585, 52.1596, 51.6092, 50.8257, 50.4052, 49.7347, 49.1995, 48.2683, 47.7141, 47.0999, 46.6405, 45.8866, 45.6275, 44.9952, 44.6103, 44.1659, 43.8371],
        [0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001]),
    'Revigo 05A': ([65.0441, 18.9224, 18.0994, 19.1908, 18.9658, 19.1865, 18.9342, 19.4817, 19.1173, 19.2873, 19.4943, 19.2053, 18.9963, 18.2411, 16.4594, 11.5067, 5.1935, 1.7351, 0.5648, 0.288, 0.1988, 0.1534, 0.1267, 0.1092, 0.0942, 0.0838, 0.0727, 0.0652, 0.058, 0.0518, 0.0462],
        [2.9528, 0.9253, 0.7593, 0.8149, 0.8697, 0.8791, 0.877, 0.8711, 0.859, 0.8727, 0.8881, 0.8388, 0.928, 1.0195, 1.2494, 1.9912, 3.2679, 3.8447, 3.9383, 5.0227, 6.0148, 6.7946, 6.9987, 7.1751, 7.2648, 7.313, 7.3112, 7.2696, 7.2996, 7.2823, 7.2589]),
    'Revigo 06A': ([120.754, 34.6613, 32.7849, 34.5293, 33.8317, 33.9453, 33.3763, 33.9146, 33.1273, 33.1105, 32.8511, 31.6254, 30.7839, 29.3976, 28.459, 26.9883, 23.9997, 19.2169, 12.8528, 6.4797, 2.6287, 1.094, 0.6335, 0.4931, 0.4354, 0.402, 0.3877, 0.3767, 0.3654, 0.3588, 0.353],
        [15.3676, 4.4564, 3.883, 4.0238, 3.9518, 3.9031, 3.8122, 3.7838, 3.6733, 3.7092, 3.7822, 3.7157, 3.8336, 3.9186, 4.1136, 4.3316, 4.8423, 5.505, 6.5799, 7.2761, 6.9138, 6.1755, 5.7516, 5.748, 5.8225, 5.8026, 5.8757, 5.8606, 5.8764, 5.9094, 5.938]),
    'Revigo 02A': ([35.9832, 9.093, 7.6551, 7.3484, 6.9635, 7.2561, 7.7677, 9.0888, 10.9349, 12.748, 13.6699, 14.7105, 16.4516, 15.6965, 11.664, 6.5764, 2.7505, 0.3337, 0.1347, 0.0699, 0.0474, 0.0382, 0.0333, 0.0302, 0.0278, 0.0254, 0.024, 0.0228, 0.0219, 0.0208, 0.0201],
        [1.5729, 0.6052, 0.5898, 0.6141, 0.5155, 0.3401, 0.1644, 0.012, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.165, 0.7897, 0.0291, 0.0157, 0.0112, 0.0076, 0.0073, 0.0043, 0.0026, 0.0016, 0.0002, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001]),
    'Revigo 04A': ([407.1363, 113.465, 106.7492, 115.5189, 114.1731, 118.5187, 126.1303, 146.6395, 167.6957, 186.2352, 203.4068, 225.3126, 245.5059, 229.2512, 210.0751, 220.272, 238.2746, 200.1662, 116.7547, 57.948, 30.3456, 17.8554, 11.8183, 8.3626, 6.1866, 4.7149, 3.7637, 3.0592, 2.5715, 2.1874, 1.8433],
        [1.3809, 0.2169, 0.0001, 0.0001, 0.0001, 0.0001, 0.0385, 0.1591, 0.3773, 0.5481, 0.6607, 0.808, 1.1802, 1.2471, 1.0153, 0.909, 1.3069, 1.6563, 1.3373, 1.007, 1.1922, 1.6572, 2.0632, 2.3179, 2.4509, 2.4269, 2.3774, 2.268, 2.2273, 2.1607, 2.0584]),
    'Revigo 14A': ([838.7626, 243.3916, 230.201, 236.892, 221.8346, 211.6754, 200.4829, 193.5958, 182.3977, 175.7751, 146.2293, 86.2745, 31.6961, 9.7669, 2.9607, 1.0552, 0.5705, 0.4435, 0.3891, 0.3572, 0.3345, 0.3088, 0.294, 0.2805, 0.2674, 0.259, 0.2476, 0.2409, 0.2309, 0.2265, 0.2199],
        [28.5583, 8.1077, 5.1989, 4.1344, 3.7834, 3.1974, 3.3404, 3.1236, 4.4005, 5.6535, 8.2879, 12.754, 15.8844, 12.8653, 8.5539, 5.262, 4.0073, 3.8405, 3.8652, 3.987, 4.0987, 4.3306, 4.5066, 4.6812, 4.9043, 5.1071, 5.2619, 5.4091, 5.5255, 5.6438, 5.706]),
    'Revigo 15A': ([946.8229, 264.5837, 233.3189, 222.4697, 192.6299, 170.1605, 139.8862, 112.1864, 72.9203, 41.4169, 16.3522, 5.2597, 1.4925, 0.3966, 0.226, 0.1766, 0.1601, 0.1563, 0.1556, 0.1552, 0.1582, 0.1541, 0.1564, 0.1553, 0.156, 0.1568, 0.1597, 0.1604, 0.1624, 0.1652, 0.1667],
        [32.6119, 11.3477, 10.6406, 12.4999, 14.7216, 16.0708, 18.1437, 20.0343, 21.3298, 21.1787, 19.6683, 16.3495, 12.8891, 7.9668, 8.4994, 9.2421, 9.4333, 9.4025, 9.2576, 9.0955, 9.0014, 8.8478, 8.7303, 8.4608, 8.2857, 8.1163, 7.9556, 7.6655, 7.5865, 7.4174, 7.2631]),
    'Revigo 10A': ([95.6065, 22.1936, 16.0356, 12.2698, 8.2, 5.3927, 3.3525, 2.2406, 1.4316, 0.7513, 0.4648, 0.372, 0.347, 0.3666, 0.445, 0.6104, 0.9659, 1.5239, 2.1951, 2.9615, 3.8851, 4.8432, 5.9359, 7.0398, 8.0629, 8.9556, 9.8328, 10.4707, 11.1445, 11.5011, 11.8072],
        [2.7027, 0.691, 0.6629, 0.8661, 1.0996, 1.3859, 1.6366, 1.9137, 1.98, 1.3648, 1.0262, 0.9491, 0.9062, 0.8667, 0.8424, 0.8377, 0.9287, 0.9826, 0.894, 0.7642, 0.6403, 0.5445, 0.469, 0.3987, 0.3439, 0.2969, 0.2797, 0.2448, 0.2353, 0.2078, 0.2041]),
    'Revigo 09A': ([48.7697, 18.0099, 20.4016, 23.0254, 21.4226, 17.8347, 13.5115, 10.5467, 7.7694, 5.8256, 4.2777, 3.7014, 4.35, 5.8495, 8.3902, 11.9269, 16.3483, 20.9421, 25.799, 30.0102, 33.1895, 34.7802, 35.7113, 35.2897, 33.3966, 29.5702, 26.4745, 23.1364, 18.2287, 14.3792, 12.3899],
        [5.8742, 1.6039, 1.4337, 1.4082, 1.3328, 1.265, 1.2043, 1.149, 1.0861, 1.0528, 1.0123, 0.9458, 0.8912, 0.8087, 0.7198, 0.6211, 0.5146, 0.3837, 0.2865, 0.1951, 0.1242, 0.1192, 0.103, 0.092, 0.1305, 0.1583, 0.1787, 0.2177, 0.2985, 0.3379, 0.3552]),
    'Revigo 13A': ([319.1844, 79.614, 63.8066, 57.9258, 51.0631, 48.8562, 49.8113, 56.216, 64.8096, 77.5642, 95.3795, 113.2766, 138.1961, 163.6988, 196.2325, 233.226, 274.4289, 318.499, 368.8642, 421.3288, 475.6128, 534.2935, 590.6103, 644.4786, 694.9809, 734.1422, 769.0161, 792.0955, 815.7022, 824.961, 832.7366],
        [4.8207, 1.0584, 0.7483, 0.6119, 0.4374, 0.3034, 0.1923, 0.0788, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.4247, 1.835, 3.695, 7.0752, 10.425, 13.7871, 17.0996, 20.2792, 22.6122, 24.0525, 25.739, 25.4461, 25.524]),
    'Revigo 12A': ([13.459, 2.9717, 2.0049, 1.7526, 1.5917, 1.6523, 1.6873, 2.2013, 2.3885, 2.0774, 2.9067, 5.903, 13.0495, 24.7184, 40.1901, 49.4801, 57.1295, 69.7335, 79.1292, 79.8417, 75.2428, 70.2196, 71.2359, 67.2496, 50.2837, 28.0235, 12.0382, 4.5633, 1.6506, 0.2429, 0.1012],
        [13.126, 3.7911, 3.4517, 3.6784, 3.6678, 3.8215, 3.8344, 3.9312, 3.7542, 3.6994, 3.5604, 3.1636, 2.6998, 2.2541, 2.0027, 1.8106, 1.7154, 1.5263, 1.4953, 1.6729, 1.7627, 2.0127, 2.0976, 2.3227, 2.867, 3.3063, 3.4607, 3.4479, 3.5604, 1.1019, 1.0706]),
    'Revigo 11A': ([11.8785, 2.7773, 1.9065, 0.723, 0.5671, 0.5254, 0.6145, 1.8161, 3.289, 5.3853, 8.9612, 13.6808, 19.6998, 25.5298, 31.2732, 36.4827, 40.4548, 43.1633, 45.7759, 47.0558, 47.6367, 46.9183, 45.8285, 44.099, 41.3794, 37.5849, 33.1413, 27.7526, 22.1581, 16.5792, 11.6943],
        [3.5234, 1.1142, 1.0007, 0.3212, 0.2721, 0.2553, 0.2591, 0.8787, 0.775, 0.4591, 0.0831, 0.0952, 0.1291, 0.1325, 0.1162, 0.102, 0.0853, 0.0697, 0.0612, 0.0653, 0.0609, 0.0883, 0.0955, 0.1006, 0.1098, 0.1264, 0.1467, 0.1648, 0.1736, 0.1611, 0.1297]),
}
LUT_N = 49                    # nodes per axis of the unmixing table
PENALTY = {"white": 0.5, "black": 1.0, "chromatic": 2.5}   # dE2000-like cost per pigment used (tuned by eye: sparsity prior)
_VERSION = "spectral-2"


def _pigments_path():
    here = os.path.dirname(os.path.abspath(__file__))
    for c in (os.path.join(here, "..", "pigments.json"), os.path.join(here, "..", "..", "pigments.json")):
        if os.path.exists(c):
            return c
    raise FileNotFoundError("studio/pigments.json not found (the spectral palette needs it)")


def oil_entries():
    """Every Revigo oil entry with spectral K and S in pigments.json: {sample: entry}."""
    out = {}
    for p in json.load(open(_pigments_path()))["pigments"]:
        for e in p.get("media", {}).get("oil", []):
            if "spectral" in e:
                out[e["sample"]] = dict(e, ci=p.get("ci"))
    return out


def _palette_ks(samples):
    try:
        ent = oil_entries()
        return [(np.array(ent[s]["spectral"]["K_per_film"]), np.array(ent[s]["spectral"]["S_per_film"])) for s in samples]
    except (OSError, KeyError):
        return [(np.array(_EMBEDDED[s][0]), np.array(_EMBEDDED[s][1])) for s in samples]


class Palette:
    def __init__(self, samples=PALETTE_SAMPLES, ks=None):
        self.names = [n for _, n in samples]
        self.samples = [s for s, _ in samples]
        if ks is None:
            ks = _palette_ks(self.samples)
        self.K = np.array([k for k, _ in ks], np.float64)
        self.S = np.maximum(np.array([s for _, s in ks], np.float64), 1e-6)
        self.K32, self.S32 = self.K[:, BANDS].astype(np.float32), self.S[:, BANDS].astype(np.float32)   # engine bands
        self.P = len(self.names)
        self.lut = None

    # ---- forward
    def spectrum(self, c):
        """Concentrations (..., P) -> reflectance spectrum as seen (..., 31) of the opaque mixture (R_inf), all bands."""
        c = np.asarray(c, np.float64)
        return seen(rinf(c @ self.K, c @ self.S))

    def forward(self, c, chunk=1 << 16):
        """Concentrations (..., P) -> sRGB-encoded colour (..., 3) (engine bands)."""
        c = np.asarray(c, np.float32)
        sh = c.shape[:-1]
        c = c.reshape(-1, self.P)
        out = np.empty((len(c), 3), np.float32)
        for i in range(0, len(c), chunk):
            cc = c[i:i + chunk]
            out[i:i + chunk] = encode(seen(rinf(cc @ self.K32, cc @ self.S32)) @ _E2LIN)
        return out.reshape(sh + (3,))

    # ---- unmixing table
    def _key(self):
        h = hashlib.sha1((_VERSION + json.dumps(PENALTY) + str(LUT_N)).encode())
        h.update(self.K.round(5).tobytes()); h.update(self.S.round(5).tobytes())
        return h.hexdigest()[:16]

    def build_lut(self, verbose=False):
        """Sample sparse mixtures, then give every node of the RGB cube the cheapest one (dE + penalty)."""
        from scipy.spatial import cKDTree
        P = self.P
        chrom = list(range(2, P))
        u = np.linspace(-7.5, 7.5, 31)
        fr = np.concatenate([[0.0], 1 / (1 + np.exp(-u)), [1.0]])            # logit-spaced: tinting strengths span 1000x
        fw = np.concatenate([[0.0], 1 / (1 + np.exp(-np.linspace(-6, 6, 13))), [1.0]])
        rows = []                                                            # (c dense, cost of pigments)

        def add(idx, W):
            C = np.zeros((len(W), P), np.float32)
            for j, i in enumerate(idx):
                C[:, i] += W[:, j]
            rows.append(C)
        # pairs of any two palette paints
        for i in range(P):
            for j in range(i + 1, P):
                add((i, j), np.stack([1 - fr, fr], 1))
        # one or two chromatic paints with white and black: s = chromatic share, v = white's part of the rest
        fs = np.concatenate([[0.0], 1 / (1 + np.exp(-np.linspace(-8, 8, 41))), [1.0]])
        fv = np.concatenate([[0.0], 1 / (1 + np.exp(-np.linspace(-7, 7, 29))), [1.0]])
        sv = np.array(np.meshgrid(fs, fv, indexing="ij")).reshape(2, -1).T
        for i in chrom:
            add((i, 0, 1), np.stack([sv[:, 0], (1 - sv[:, 0]) * sv[:, 1], (1 - sv[:, 0]) * (1 - sv[:, 1])], 1))
        g = np.array(np.meshgrid(fw, fw, fw, indexing="ij")).reshape(3, -1).T    # (chromatic share, white part of the rest, 2nd chromatic part)
        for i in chrom:
            for j in chrom:
                if j <= i:
                    continue
                s_, v_, h_ = g[:, 0], g[:, 1], g[:, 2]
                add((i, j, 0, 1), np.stack([s_ * (1 - h_), s_ * h_, (1 - s_) * v_, (1 - s_) * (1 - v_)], 1))
        C = np.unique(np.concatenate(rows).round(6), axis=0).astype(np.float32)
        C /= C.sum(1, keepdims=True)
        rgb = self.forward(C)
        lab = rgb_to_lab(rgb)
        used = C > 1e-6
        pen = used[:, 0] * PENALTY["white"] + used[:, 1] * PENALTY["black"] + used[:, 2:].sum(1) * PENALTY["chromatic"]
        tree = cKDTree(lab)
        n = LUT_N
        ax = np.linspace(0, 1, n)
        nodes = np.array(np.meshgrid(ax, ax, ax, indexing="ij")).reshape(3, -1).T
        nlab = rgb_to_lab(nodes)
        d, ix = tree.query(nlab, k=64)
        cost = d + pen[ix]
        best = ix[np.arange(len(ix)), np.argmin(cost, 1)]
        self.lut = C[best].reshape(n, n, n, P).astype(np.float32)
        self._flat = None
        if verbose:
            print(f"[spectral] {len(C)} sampled mixtures; median node distance {np.median(d[:, 0]):.2f} (CIELAB)")
        return self.lut

    def ensure_lut(self):
        if self.lut is not None:
            return self.lut
        path = os.path.join(os.path.expanduser("~/.cache/teodor"), f"spectral_lut_{self._key()}.npy")
        try:
            self.lut = np.load(path)
            self._flat = None
            return self.lut
        except Exception:
            pass
        self.build_lut()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + f".{os.getpid()}.tmp.npy"
            np.save(tmp, self.lut)
            os.replace(tmp, path)
        except OSError:
            pass
        return self.lut

    # ---- RGB <-> latent
    def concentrations(self, rgb):
        """sRGB (..., 3) -> concentrations (..., P), trilinear in the unmixing table."""
        lut = self.ensure_lut()
        n = lut.shape[0]
        if getattr(self, "_flat", None) is None or self._flat.shape[0] != n ** 3:
            self._flat = np.ascontiguousarray(lut.reshape(-1, self.P))
            self._corner = np.array([(dz * n + dy) * n + dx for dz in (0, 1) for dy in (0, 1) for dx in (0, 1)], np.int64)
        rgb = np.asarray(rgb, np.float32)
        sh = rgb.shape[:-1]
        p = np.clip(rgb.reshape(-1, 3), 0, 1) * (n - 1)
        i0 = np.minimum(p.astype(np.int32), n - 2)
        f = p - i0
        g = 1 - f
        w = np.empty((len(p), 8), np.float32)
        k = 0
        for wz in (g[:, 0], f[:, 0]):
            for wy in (g[:, 1], f[:, 1]):
                wzy = wz * wy
                w[:, k] = wzy * g[:, 2]; w[:, k + 1] = wzy * f[:, 2]; k += 2
        base = (i0[:, 0].astype(np.int64) * n + i0[:, 1]) * n + i0[:, 2]
        rows = np.take(self._flat, base[:, None] + self._corner[None, :], axis=0)   # (N, 8, P)
        out = np.matmul(w[:, None, :], rows)[:, 0]
        return out.reshape(sh + (self.P,))

    def latent(self, rgb):
        rgb = np.asarray(rgb, np.float32)
        c = self.concentrations(rgb)
        return c, rgb - self.forward(c)


_PAL = None


def palette():
    global _PAL
    if _PAL is None:
        _PAL = Palette()
    return _PAL


# ---------------------------------------------------------------- the interface
def latent(rgb):
    """sRGB colour(s) (..., 3) -> (concentrations (..., P), residual (..., 3))."""
    return palette().latent(rgb)


def from_latent(c, res):
    return np.clip(palette().forward(c) + res, 0, 1).astype(np.float32)


def forward(c):
    return palette().forward(c)


def mix(a, b, t):
    """Mix paint colour a with b, a fraction t of b (by weight), in pigment space. Same shape semantics as
    base.kmix: a (..., 3), b broadcastable to it, t a scalar or (..., 1)."""
    a = np.asarray(a, np.float32)
    b = np.asarray(b, np.float32)
    t = np.asarray(t, np.float32)
    shape = np.broadcast_shapes(a.shape, b.shape, t.shape[:-1] + (3,) if t.ndim else ())
    ca, ra = latent(a)
    cb, rb = latent(b)
    tt = t if t.ndim else t.reshape(1)
    tt = np.clip(tt, 0, 1)
    c = ca * (1 - tt) + cb * tt
    r = ra * (1 - tt) + rb * tt
    out = np.clip(palette().forward(c) + r, 0, 1).astype(np.float32)
    return np.broadcast_to(out, shape).copy() if out.shape != shape else out


class CanvasLatent:
    """The pigment state of a canvas colour array, kept in step with it, so that paint laid with mix_window
    keeps its pigments (a pixel mixed from white and 2% Prussian blue stays that mixture, rather than being
    unmixed again from its RGB). The cache is checked against the colour array pixel by pixel: wherever
    anything else changed the colour (a blender, a glaze, a reload), the pixel is unmixed again from RGB."""

    def __init__(self, H, W):
        self.W = W
        self.rgb = np.full((H * W, 3), -1.0, np.float32)
        self.c = np.zeros((H * W, palette().P), np.float32)
        self.r = np.zeros((H * W, 3), np.float32)

    def index(self, sl, m):
        yy, xx = np.nonzero(m)
        return (yy + (sl[0].start or 0)) * self.W + (xx + (sl[1].start or 0))

    def get(self, col, idx):
        """Colour, concentrations (n, P) and residual (n, 3) of the canvas pixels idx (flat)."""
        a = col.reshape(-1, 3)[idx]
        c, r = self.c[idx], self.r[idx]
        bad = ~np.all(self.rgb[idx] == a, axis=1)
        if bad.any():
            c[bad], r[bad] = latent(a[bad])
        return a, c, r

    def put(self, col, idx, out, c, r):
        col.reshape(-1, 3)[idx] = out
        self.rgb[idx] = out
        self.c[idx] = c
        self.r[idx] = r


def latent_cache(cv):
    """The CanvasLatent of a canvas (made on first use; not saved with the canvas)."""
    lc = getattr(cv, "_spectral_latent", None)
    if lc is None or lc.W != cv.col.shape[1] or len(lc.rgb) != cv.col.shape[0] * cv.col.shape[1]:
        lc = cv._spectral_latent = CanvasLatent(cv.col.shape[0], cv.col.shape[1])
    return lc


def film_over(ca, ra, Kf, Sf, x, rb=None):
    """A paint film (constants Kf, Sf per engine band; (n, B) or (1, B)) of thickness x (n, 1) over substrates
    given as latents (ca (n, P), ra (n, 3)). Returns (sRGB (n, 3), luminance transmittance T^2 (n, 1)). The
    substrate's residual passes through the film (T^2); the film paint's own residual rb, if given, shows as
    the film covers (1 - T^2)."""
    pal = palette()
    Rg = rinf(ca @ pal.K32, ca @ pal.S32)
    Rt, T = km_over(Kf, Sf, x, Rg)
    T2 = ((T * T) @ _EYW)[:, None]
    out = encode(seen(Rt) @ _E2LIN) + ra * T2
    if rb is not None:
        out = out + rb * (1 - T2)
    return np.clip(out, 0, 1).astype(np.float32), T2


BODY_FILM = 0.5     # film thickness (units of the 100 um drawdown) that a full deposit (t = 1) lays over dry paint:
                    # 50 um, within the measured 10-80 um of single paint layers (docs/media-data.md [O1]); a judgement


WET_MIX = 0.15      # paint wetter than this takes new paint in by mixing; drier paint is covered by it (oil's touch-dry
                    # threshold, media/oil.py _dry)


def mix_window(cv, sl, t, b, index=None, thr=1e-3, wet=None):
    """In place: paint b laid into cv.col[sl] with amount t, wherever t > thr, keeping the canvas's pigment
    state. t: window shape (h, w) or (h, w, 1). b: an RGB colour (3,), an RGB window (h, w, 3), or a latent
    pair (c (k, P), r (k, 3)) with `index` (h, w) choosing a row per pixel (e.g. per bristle clump).
    wet (h, w) 0..1, optional (default: all wet): how wet the paint beneath is. Into wet paint (wet >= WET_MIX)
    the new paint mixes (pigment space, a fraction t of b); over dry paint it lies on top as a film of
    thickness t * BODY_FILM (spectral Kubelka-Munk), so opaque paint covers and transparent paint stains. The
    pixel's pigment state is then the new paint, with what shows through it in the residual."""
    t = np.asarray(t, np.float32)
    if t.ndim == 3:
        t = t[..., 0]
    m = t > thr
    if not m.any():
        return
    if not (cv.col.flags.c_contiguous and cv.col.dtype == np.float32):
        cv.col = np.ascontiguousarray(cv.col, np.float32)
    pal = palette()
    lc = latent_cache(cv)
    idx = lc.index(sl, m)
    a, ca, ra = lc.get(cv.col, idx)
    if isinstance(b, tuple):
        cb, rb = b
        ix = index[m]
        fb = pal.forward(cb)[ix]
        cb, rb = cb[ix], rb[ix]
    else:
        b = np.asarray(b, np.float32)
        cb, rb = latent(b if b.ndim == 1 else b[m])
        fb = (b if b.ndim == 1 else b[m]) - rb
        if b.ndim == 1:
            cb, rb, fb = (np.broadcast_to(v, (len(a),) + v.shape) for v in (cb, rb, fb))
    tt = np.clip(t[m], 0, 1)[:, None]
    dry = None if wet is None else np.asarray(wet, np.float32)[m] < WET_MIX
    if dry is None or not dry.any():
        c = ca + (cb - ca) * tt
        f = pal.forward(c)
        out = np.clip(f + ra + (rb - ra) * tt, 0, 1).astype(np.float32)
    else:
        out = np.empty_like(a)
        c = np.array(cb, np.float32)
        f = np.array(fb, np.float32)
        w_ = ~dry
        if w_.any():
            c[w_] = ca[w_] + (cb[w_] - ca[w_]) * tt[w_]
            f[w_] = pal.forward(c[w_])
            out[w_] = np.clip(f[w_] + ra[w_] + (rb[w_] - ra[w_]) * tt[w_], 0, 1)
        cbd = cb[dry]
        out[dry] = film_over(ca[dry], ra[dry], cbd @ pal.K32, cbd @ pal.S32, tt[dry] * BODY_FILM, rb[dry])[0]
    lc.put(cv.col, idx, out, c, out - f)


GLAZE_VEIL_L = 70.0           # glaze colours lighter than this L* are veils (paint with white, no extra medium): a judgement
GLAZE_WHITE = 4.0             # extra cost (dE) of white in a darker glaze, so transparent paints are preferred: a judgement


def _film_over_white(pal, C, ref):
    """Colour (sRGB) of films of concentrations C (n, P, summing to the pigment share; the rest is clear oil)
    and thickness ref over a zinc-white ground (the measured zinc white masstone)."""
    Rg = rinf(pal.K32[0], pal.S32[0])
    out = np.empty((len(C), 3), np.float32)
    for i in range(0, len(C), 1 << 15):
        cc = C[i:i + (1 << 15)]
        Rt, _ = km_over(cc @ pal.K32, cc @ pal.S32, ref, Rg)
        out[i:i + (1 << 15)] = encode(seen(Rt) @ _E2LIN)
    return out


def glaze_samples(ref):
    """Sampled glaze paints for a film thickness ref: (C (n, P) pigment concentrations, medium share (n,),
    CIELAB of the film over white (n, 3), penalty (n,)). Clear oil medium dilutes the pigments (K = S = 0)."""
    pal = palette()
    key = round(float(ref), 6)
    cache = pal.__dict__.setdefault("_glaze_samples", {})
    if key in cache:
        return cache[key]
    P = pal.P
    u = 1 / (1 + np.exp(-np.linspace(-9, 9, 37)))
    rows = []

    def add(idx, W):
        C = np.zeros((len(W), P + 1), np.float32)
        for j, i in enumerate(idx):
            C[:, i] += W[:, j]
        rows.append(C)
    M = P                                                     # the medium's column
    g = np.array(np.meshgrid(u, u, indexing="ij")).reshape(2, -1).T     # (paint share, split)
    for i in range(P):
        add((i,), np.ones((1, 1)))
        add((i, M), np.stack([u, 1 - u], 1))
        for j in range(i + 1, P):
            add((i, j, M), np.stack([g[:, 0] * g[:, 1], g[:, 0] * (1 - g[:, 1]), 1 - g[:, 0]], 1))
            add((i, j), np.stack([u, 1 - u], 1))
    for i in range(2, P):                                     # a chromatic paint with white and black, undiluted
        sv = g
        add((i, 0, 1), np.stack([sv[:, 0], (1 - sv[:, 0]) * sv[:, 1], (1 - sv[:, 0]) * (1 - sv[:, 1])], 1))
    C = np.unique(np.concatenate(rows).round(6), axis=0)
    C /= C.sum(1, keepdims=True)
    med = C[:, M].copy()
    C = C[:, :M].astype(np.float32)
    lab = rgb_to_lab(_film_over_white(pal, C, ref))
    used = C > 1e-6
    pen = used[:, 0] * PENALTY["white"] + used[:, 1] * PENALTY["black"] + used[:, 2:].sum(1) * PENALTY["chromatic"]
    cache[key] = (C, med, lab, pen)
    return cache[key]


def glaze_paint(color, ref):
    """The glaze paint whose film of thickness ref looks like `color` over a white ground: (pigment
    concentrations (P,), medium share). Dark and saturated colours come out as transparent pigments diluted
    in oil; colours lighter than GLAZE_VEIL_L carry white instead (a veil, velatura)."""
    pal = palette()
    key = (tuple(np.round(np.asarray(color, np.float64), 4)), round(float(ref), 6))
    memo = pal.__dict__.setdefault("_glaze_memo", {})
    if key not in memo:
        C, med, lab, pen = glaze_samples(ref)
        tl = rgb_to_lab(np.asarray(color, np.float64))
        cost = np.sqrt(((lab - tl) ** 2).sum(1)) + pen
        if tl[0] > GLAZE_VEIL_L:
            cost = cost + 100 * (med > 1e-6)
        else:                                                 # a glaze proper: transparent paint preferred to white
            cost = cost + GLAZE_WHITE * (C[:, 0] > 1e-6)
        k = int(np.argmin(cost))
        memo[key] = (C[k].copy(), float(med[k]))
    return memo[key]


def glaze(R0, color, thickness, ref=None, chunk=1 << 15):
    """A pigment film over a substrate of colour R0 (..., 3): per band the film's own reflectance plus the
    substrate seen through it twice (the Kubelka-Munk layer equation in internal reflectance; the surface
    counted once, on top). thickness: scalar or R0's shape without the channel axis, in units of the measured
    100 um film (a 10 um film is 0.1).
    color (sRGB (3,)): with ref=None, the paint itself (its masstone; the film is undiluted paint); with a
    ref thickness, the colour the glaze shows over white at that thickness (glaze_paint: transparent pigments
    in oil for dark and saturated colours, white for light ones).
    The substrate's residual (what the palette does not explain) passes through the film's luminance
    transmittance, so a zero thickness returns R0 exactly."""
    pal = palette()
    R0 = np.asarray(R0, np.float32)
    sh = R0.shape[:-1]
    x = np.broadcast_to(np.asarray(thickness, np.float32), sh).reshape(-1)
    col = np.asarray(color, np.float32)
    if ref is None:
        cf = pal.concentrations(col)
    else:
        cf, _ = glaze_paint(col, ref)
    Kf, Sf = (cf @ pal.K32)[None], (cf @ pal.S32)[None]
    flat0 = R0.reshape(-1, 3)
    out = flat0.copy()
    idx = np.nonzero(x > 1e-5)[0]
    for i in range(0, len(idx), chunk):
        j = idx[i:i + chunk]
        c0, res = latent(flat0[j])
        out[j] = film_over(c0, res, Kf, Sf, x[j][:, None])[0]
    return out.reshape(sh + (3,)).astype(np.float32)


# ---------------------------------------------------------------- validation against the measured Revigo data
def _old_kmix(a, b, t):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from media.base import kmix
    return kmix(np.asarray(a, np.float32), np.asarray(b, np.float32), t)


def _raw_revigo():
    import csv
    d = os.path.join(os.environ.get("TEODOR_PIGMENT_DATA", os.path.expanduser("~/.cache/teodor/pigment-data")), "revigo/repo/data/")
    rows = list(csv.reader(open(d + "revigo-aggregated-palette-spectral-data.txt"), delimiter="\t"))
    spec = {r[0]: np.array([float(v) for v in r[1:]]) / 100 for r in rows[1:]}
    mix_ = {}
    for line in open(d + "revigo-mixture-specifications.txt"):
        k, v = line.strip().split("\t")
        names, frac = v.split("|")
        mix_[k] = (names.split("-"), [float(f) for f in frac.split("-")])
    return spec, mix_


def _unsaund(Rm):
    return np.clip((Rm - K1) / (1 - K1 - K2 + K2 * Rm), 1e-4, 0.9999)


def _fit(films, comps):
    """Per band K, S of one unknown paint from films [(c_unknown, {known index: c}, Rob, Row, Rgb, Rgw)] (Duncan,
    internal reflectance, x = 1 film), as tools/pigments/build_pigments.py fit_joint does."""
    from scipy.optimize import least_squares
    n = len(WL); K, S = np.zeros(n), np.zeros(n)
    for i in range(n):
        def res(p):
            k, s = np.exp(p); r = []
            for cu, kn, ob, ow, gb, gw in films:
                km = cu * k + sum(cc * comps[q][0][i] for q, cc in kn.items())
                sm = cu * s + sum(cc * comps[q][1][i] for q, cc in kn.items())
                w = 1.0 if cu > 0.95 else 0.7
                r += [w * (km_over(km, sm, 1.0, gb[i])[0] - ob[i]), w * (km_over(km, sm, 1.0, gw[i])[0] - ow[i])]
            return r
        best = None
        for s0 in (0.1, 1, 10, 50):
            for k0 in (0.01, 0.3, 3, 30):
                r = least_squares(res, np.log([k0, s0]), bounds=(np.log([1e-5, 1e-4]), np.log([1e4, 1e3])))
                if best is None or r.cost < best.cost:
                    best = r
        K[i], S[i] = np.exp(best.x)
    return K, S


def validate(heldout=True):
    """Prints the model's errors (dE2000) against measured Revigo colours; returns a dict of results."""
    pal = palette()
    pal.ensure_lut()
    d = json.load(open(_pigments_path()))
    ent = oil_entries()
    by_code = {s.split()[1]: e for s, e in ent.items()}
    zw = by_code["07A"]
    Kw, Sw = np.array(zw["spectral"]["K_per_film"]), np.array(zw["spectral"]["S_per_film"])
    white_rgb = np.array(zw["colours"]["masstone"]["srgb"], np.float32)
    out = {"tints": []}
    for t in d["kmix_check_tints"]:
        code = t["sample"].split()[1]
        m = by_code[code[:2] + "A"]
        c = t["pigment_fraction_by_weight"]
        meas = np.array(t["measured_lab"])
        Km, Sm = np.array(m["spectral"]["K_per_film"]), np.array(m["spectral"]["S_per_film"])
        spec_lab = spectrum_to_lab(seen(rinf(c * Km + (1 - c) * Kw, c * Sm + (1 - c) * Sw)))
        mrgb = np.array(m["colours"]["masstone"]["srgb"], np.float32)
        new = mix(mrgb, white_rgb, 1 - c)
        old = _old_kmix(mrgb, white_rgb, 1 - c)
        out["tints"].append(dict(sample=t["sample"], pigment=t["pigment"], c=round(c, 3),
                                 measured_srgb=t["measured_srgb"], kmix_srgb=[round(float(v), 3) for v in old],
                                 spectral_srgb=[round(float(v), 3) for v in new],
                                 dE_kmix=float(de2000(meas, rgb_to_lab(old))), dE_spectral_insample=float(de2000(meas, spec_lab)),
                                 dE_engine=float(de2000(meas, rgb_to_lab(new))), in_palette=(m["sample"] in pal.samples)))
    T = out["tints"]
    med = lambda k, L=T: float(np.median([r[k] for r in L])) if L else float("nan")
    mx = lambda k, L=T: float(np.max([r[k] for r in L])) if L else float("nan")
    print(f"tints with zinc white (n={len(T)}), dE2000 median / max:")
    for k, lab_ in (("dE_kmix", "old kmix (RGB)"), ("dE_spectral_insample", "spectral KM, constants fitted on these tints"),
                    ("dE_engine", "spectral.mix through the RGB interface (LUT)")):
        print(f"  {lab_:52s} {med(k):5.2f} / {mx(k):5.2f}")
    if not heldout:
        return out
    try:
        spec, mixes = _raw_revigo()
    except OSError as e:
        print(f"held-out checks skipped: raw Revigo spectra not found ({e}); set TEODOR_PIGMENT_DATA")
        return out
    I = lambda code: [_unsaund(spec[f"{code}_{s}"]) for s in ("ob", "ow", "b", "w")]
    target = lambda code: spectrum_to_lab(np.clip(spec[f"{code}_ow"] - K1, 0, 1))
    # (1) leave one tint out: refit the pigment from its masstone film and the other tints, predict the one left out
    comps = {"w": (Kw, Sw)}
    ho = []
    for t in d["kmix_check_tints"]:
        code = t["sample"].split()[1]
        mcode = code[:2] + "A"
        others = [c for c, (n, f) in mixes.items() if c[:2] == code[:2] and c not in (code, mcode) and len(n) > 1 and n[1] == "ZincWhite"
                  and f[0] not in (0, 100) and (len(f) < 3 or f[2] == 0) and f"{c}_ow" in spec]
        films = [(1.0, {}, *I(mcode))] + [(mixes[c][1][0] / 100, {"w": mixes[c][1][1] / 100}, *I(c)) for c in others]
        K, S = _fit(films, comps)
        cu = mixes[code][1][0] / 100
        R = seen(rinf(cu * K + (1 - cu) * Kw, cu * S + (1 - cu) * Sw))
        ho.append(dict(sample=t["sample"], c=cu, n_tints_fitted=len(others), dE=float(de2000(target(code), spectrum_to_lab(R)))))
    out["leave_one_tint_out"] = ho
    print(f"held out, spectral, leave one tint out (refit from masstone + the other tints; n={len(ho)}): median {med('dE', ho):.2f}, max {mx('dE', ho):.2f}")
    # (1b) the whole engine path held out: refit every palette pigment without the light (c < 0.3) or without the
    #      strong (c >= 0.3) tints, rebuild the unmixing table, predict the held-out tints through mix()
    fold = []
    for name, held in (("light tints held out", lambda c: c < 0.3), ("strong tints held out", lambda c: c >= 0.3)):
        ks = []
        for smp in pal.samples:
            code = smp.split()[1]
            if code in ("07A", "07C-07F"):
                e = by_code[code]; ks.append((np.array(e["spectral"]["K_per_film"]), np.array(e["spectral"]["S_per_film"]))); continue
            keep = [c for c, (n, f) in mixes.items() if c[:2] == code[:2] and c != code and len(n) > 1 and n[1] == "ZincWhite"
                    and f[0] not in (0, 100) and (len(f) < 3 or f[2] == 0) and f"{c}_ow" in spec and not held(f[0] / 100)]
            films = [(1.0, {}, *I(code))] + [(mixes[c][1][0] / 100, {"w": mixes[c][1][1] / 100}, *I(c)) for c in keep]
            ks.append(_fit(films, comps))
        fp = Palette(ks=ks); fp.build_lut()
        for t in d["kmix_check_tints"]:
            if not held(t["pigment_fraction_by_weight"]):
                continue
            code = t["sample"].split()[1]; mcode = code[:2] + "A"; c = t["pigment_fraction_by_weight"]
            if f"Revigo {mcode}" in fp.samples:
                j = fp.samples.index(f"Revigo {mcode}"); e1 = np.zeros(fp.P, np.float32); e1[j] = 1
                mrgb = fp.forward(e1)
            else:
                mrgb = np.array(by_code[mcode]["colours"]["masstone"]["srgb"], np.float32)
            wrgb = fp.forward(np.eye(fp.P, dtype=np.float32)[0])
            ca, ra = fp.latent(mrgb); cb, rb = fp.latent(wrgb)
            pred = np.clip(fp.forward(ca * c + cb * (1 - c)) + ra * c + rb * (1 - c), 0, 1)
            fold.append(dict(sample=t["sample"], fold=name, c=c, in_palette=f"Revigo {mcode}" in fp.samples,
                             dE_engine=float(de2000(np.array(t["measured_lab"]), rgb_to_lab(pred)))))
    out["engine_heldout_folds"] = fold
    ip = [f for f in fold if f["in_palette"]]
    print(f"held out, engine path (refit without the held-out tints, table rebuilt; n={len(fold)}): median {med('dE_engine', fold):.2f}, max {mx('dE_engine', fold):.2f}"
          f"; pigments in the palette (n={len(ip)}): median {med('dE_engine', ip):.2f}, max {mx('dE_engine', ip):.2f}")
    # (2) mixtures with bone black: never used in any fit (black was fitted on its mixtures with zinc white)
    bk = by_code["07C-07F"]
    Kb, Sb = np.array(bk["spectral"]["K_per_film"]), np.array(bk["spectral"]["S_per_film"])
    black_rgb = np.array(bk["colours"]["masstone"]["srgb"], np.float32)
    blk = []
    for code, (names, f) in mixes.items():
        if len(f) == 3 and f[1] == 0 and f[2] not in (0, 100) and f"{code}_ow" in spec and code[:2] + "A" in by_code:
            m = by_code[code[:2] + "A"]
            cu, cb = f[0] / 100, f[2] / 100
            Km, Sm = np.array(m["spectral"]["K_per_film"]), np.array(m["spectral"]["S_per_film"])
            K_, S_ = cu * Km + cb * Kb, cu * Sm + cb * Sb
            ob, ow, gb, gw = I(code)
            Rf = seen(km_over(K_, S_, 1.0, gw)[0])
            mrgb = np.array(m["colours"]["masstone"]["srgb"], np.float32)
            tl = target(code)
            ok_, ek_ = _old_kmix(mrgb, black_rgb, cb), mix(mrgb, black_rgb, cb)
            blk.append(dict(sample=f"Revigo {code}", pigment=m["name"], black=cb, dE_kmix=float(de2000(tl, rgb_to_lab(ok_))),
                            dE_spectral=float(de2000(tl, spectrum_to_lab(Rf))), dE_engine=float(de2000(tl, rgb_to_lab(ek_))),
                            L_measured=float(tl[0]), kmix_rgb=[float(v) for v in ok_], engine_rgb=[float(v) for v in ek_],
                            measured_rgb=[float(v) for v in spectrum_to_rgb(np.clip(spec[f"{code}_ow"] - K1, 0, 1))]))
    out["black_mixtures"] = blk
    print(f"held out, pigment + bone black (n={len(blk)}), dE2000 median / max: kmix {med('dE_kmix', blk):.2f} / {mx('dE_kmix', blk):.2f}, "
          f"spectral {med('dE_spectral', blk):.2f} / {mx('dE_spectral', blk):.2f}, engine {med('dE_engine', blk):.2f} / {mx('dE_engine', blk):.2f}")
    # (3) lead white tints: lead white fitted from its own film and its mixtures with bone black only; the
    #     pigments from their zinc-white tints; the tints with lead white are predicted
    comps2 = {"k": (Kb, Sb)}
    films = [(1.0, {}, *I("08A"))] + [(mixes[c][1][0] / 100, {"k": mixes[c][1][1] / 100}, *I(c)) for c in ("08B", "08C")]
    Klw, Slw = _fit(films, comps2)
    lw_rgb = encode(seen(rinf(Klw, Slw)) @ _SPEC2LIN).astype(np.float32)
    code_of = {"Cochineal": "04A", "ViridianGreen": "09A", "CobaltBlue": "12A", "ChromeYellow": "14A"}
    lw = []
    for code in ("08D", "08E", "08F", "08G"):
        names, f = mixes[code]
        j = int(np.argmax(f[2:])) + 2
        m = by_code[code_of[names[j]]]
        cu = f[j] / 100
        Km, Sm = np.array(m["spectral"]["K_per_film"]), np.array(m["spectral"]["S_per_film"])
        R = seen(rinf(cu * Km + (1 - cu) * Klw, cu * Sm + (1 - cu) * Slw))
        mrgb = np.array(m["colours"]["masstone"]["srgb"], np.float32)
        tl = target(code)
        ok_, ek_ = _old_kmix(mrgb, lw_rgb, 1 - cu), mix(mrgb, lw_rgb, 1 - cu)
        lw.append(dict(sample=f"Revigo {code}", pigment=m["name"], c=cu, dE_kmix=float(de2000(tl, rgb_to_lab(ok_))),
                       dE_spectral=float(de2000(tl, spectrum_to_lab(R))), dE_engine=float(de2000(tl, rgb_to_lab(ek_))),
                       kmix_rgb=[float(v) for v in ok_], engine_rgb=[float(v) for v in ek_],
                       measured_rgb=[float(v) for v in spectrum_to_rgb(np.clip(spec[f"{code}_ow"] - K1, 0, 1))]))
    out["lead_white_tints"] = lw
    print(f"held out, ~10% pigment in lead white (n={len(lw)}), dE2000 median / max: kmix {med('dE_kmix', lw):.2f} / {mx('dE_kmix', lw):.2f}, "
          f"spectral {med('dE_spectral', lw):.2f} / {mx('dE_spectral', lw):.2f}, engine {med('dE_engine', lw):.2f} / {mx('dE_engine', lw):.2f}")
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        r = validate("--no-heldout" not in sys.argv)
        if "--json" in sys.argv:
            json.dump(r, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
    elif len(sys.argv) > 1 and sys.argv[1] == "build":
        palette().build_lut(verbose=True)
