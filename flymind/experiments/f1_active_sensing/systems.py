"""F1 systems: pixel noise → frozen encoder → (SNN | P | TH | LIN) decision variables + neural measures. No file writes.
Stage 0 EXPERIMENTAL readouts; decoder.SteerDecoder is not used. Labels: MODEL (ALIF/network), ENGINEERING (encoder, P), CONTROL (TH, LIN,
B1, SWS)."""
import math
import os
import sys

import numpy as np
from scipy.ndimage import uniform_filter

FLY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, FLY)
import loop as L  # noqa: E402
from alif import ALIF  # noqa: E402
from block_shuffle import block_shuffle  # noqa: E402
from encoder import TargetEncoder  # noqa: E402
from side_shuffle import layer_side_labels, shuffle_within_side  # noqa: E402
from visual_path import network  # noqa: E402

SHAPE = (96, 128)
STEPS = 10                                            # SNN steps (1 ms) per 10 ms frame
ENC = TargetEncoder(SHAPE, L.ENC)


def pixel_noise(unit, sigma, T=300):
    """Rounded Gaussian pixel noise for one unit, int16 [T, H, W, 3]; rint(img + n) == img + rint(n) for integer img."""
    return np.rint(np.random.default_rng([unit, 1]).standard_normal((T, *SHAPE, 3)) * sigma).astype(np.int16)


def encode(imgs, noise):
    """Noisy frames → g [T, 2] (frozen encoder, per frame) and LIN [T] (blurred contrast, no c_min, no saturation)."""
    x = np.clip(imgs.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    g = np.array([ENC.encode(f)["g"] for f in x])
    lin = np.empty(len(x))
    w = ENC.S[0] - ENC.S[1]
    for k, f in enumerate(x):                         # same blur and contrast as encoder.encode, without threshold
        y = uniform_filter(f.astype(np.float32), size=(L.ENC.blur_px, L.ENC.blur_px, 1), mode="nearest")
        c = (y[..., 1] - (y[..., 0] + y[..., 2]) / 2) / float(y.mean())
        lin[k] = float(c.sum(0) @ w)
    return g, lin


W = slice(100, 300)                                  # analysis window frames (1–3 s)


def ema(x, a):
    """y[k] = a·y[k−1] + (1 − a)·x[k], y[−1] = 0, along axis 0."""
    y, out = np.zeros(x.shape[1:]), np.empty_like(x, dtype=float)
    for k in range(len(x)):
        y = a * y + (1 - a) * x[k]
        out[k] = y
    return out


def lowpass_drive(g, i_max, tau_ms, frame_ms=10.0):
    """First-order low-pass of the held drive i_max·g sampled at frame ends: x ← I + (x − I)·exp(−frame/τ), x0 = 0."""
    return ema(i_max * np.asarray(g, float), math.exp(-frame_ms / tau_ms))


def thresh_D(drive, th):
    """Window mean of max(0, drive_L − th) − max(0, drive_R − th); drive [..., T, 2]; th scalar or [K] → [..., K]."""
    th = np.atleast_1d(th)
    r = np.maximum(0, drive[..., W, :, None] - th)
    return (r[..., 0, :] - r[..., 1, :]).mean(-2)


def controls(g, lin, th_mV, th_lp_mV, tau_s, tau_lp_ms, i_max):
    """Decision variables of the non-SNN systems over the window (PROTOCOL §4), computed from the stored g / LIN streams."""
    g = np.asarray(g, float)
    P = ema(g @ [1.0, -1.0], math.exp(-0.01 / tau_s))                # loop.py classical_p filter
    return dict(P=float(P[W].mean()), TH=float(thresh_D(i_max * g, th_mV)[0]),
                TH_LP=float(thresh_D(lowpass_drive(g, i_max, tau_lp_ms), th_lp_mV)[0]), LIN=float(np.asarray(lin)[W].mean()))


class Networks:
    def __init__(self, b1_seeds, sws_seeds, first_unit):
        self.first = first_unit
        self.spec, self.idx, self.rep = network(L.J0)
        groups, _ = layer_side_labels(self.spec, self.idx)
        self.nets = {"DATA": [self.spec],
                     "B1": [block_shuffle(self.spec, groups, s, "LCxLC") for s in b1_seeds],
                     "SWS": [shuffle_within_side(self.spec, groups, s) for s in sws_seeds]}

    def pick(self, name, unit):
        fam = self.nets[name]
        return fam[(unit - self.first) % len(fam)]


def paircorr(x, b=5):
    X = x.reshape(-1, b, x.shape[1]).sum(1)
    act = X.var(0) > 0
    if act.sum() < 2:
        return np.nan
    cc = np.corrcoef(X[:, act].T)
    return float(np.nanmean(cc[np.triu_indices_from(cc, 1)]))


def fourier(x, f, dt=0.001):
    t = np.arange(len(x)) * dt
    return complex((2 / len(x)) * (x * np.exp(-2j * math.pi * f * t)).sum())


def run_snn(spec, idx, g, unit, i_max, f=None, theta=None):
    """One SNN trial. Returns decision variable D and neural measures (window 1–3 s unless stated)."""
    N = len(spec.bodies)
    I = np.zeros((len(g), N))
    I[:, idx["in_L"]] = i_max * g[:, :1]
    I[:, idx["in_R"]] = i_max * g[:, 1:]
    s = ALIF(spec, L.P, unit).run(np.repeat(I, STEPS, 0), len(g) * STEPS)
    W = slice(1000, 3000)
    w = s[W]
    pops = {k: idx[k] for k in ("in_L", "in_R", "mid", "DNa02_L", "DNa02_R")}
    cnt = {k: int(w[:, v].sum()) for k, v in pops.items()}
    out = dict(D=cnt["DNa02_L"] - cnt["DNa02_R"], **{f"n_{k}": v for k, v in cnt.items()})
    for k in ("in_L", "in_R", "mid"):
        out[f"sync_{k}"] = paircorr(w[:, pops[k]])
    for k in ("in_L", "in_R", "DNa02_L", "DNa02_R"):
        t = np.flatnonzero(s[:, pops[k]].any(1))
        out[f"lat_{k}_ms"] = float(t[0]) if t.size else np.nan
    if out["D"]:                                       # decision latency: first spike on the reported side after window start
        t = np.flatnonzero(w[:, pops["DNa02_L" if out["D"] > 0 else "DNa02_R"]].any(1))
        out["lat_decision_ms"] = float(t[0])
    else:
        out["lat_decision_ms"] = np.nan
    if f:
        th = np.repeat(theta, STEPS)[W]
        ref = fourier(th, f)
        for k, x in (("in_L", w[:, pops["in_L"]].mean(1)), ("in_R", w[:, pops["in_R"]].mean(1)),
                     ("dn", w[:, pops["DNa02_L"]].sum(1) - w[:, pops["DNa02_R"]].sum(1).astype(float))):
            z = fourier(x.astype(float) * 1000, f)
            out[f"F_{k}_amp_hz"], out[f"F_{k}_phase"] = abs(z), float(np.angle(z / ref)) if abs(ref) else np.nan
    return out
