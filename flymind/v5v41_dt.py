"""flymind/v5v41_dt.py — harness otwartej pętli V5 v4.1 w czasie fizycznym (Etap 0). v5v41.py nietknięty (przypięty sha256).

simulate_dt = v5v41.simulate z rozdzielonym czasem [ms] i licznikami kroków:
  harmonogram (pre_ms, step_ms, ramp half) w ms → kroki przez to_steps(..., 'exact')
  BIN_MS = 10 ms fizycznie → k_bin = 10/dt kroków; okno ustalone [pre+500, pre+1000) ms jak dotąd
  dekoder: dec.step(chunk, dt) zamiast dec.step(chunk, 1.0)
  first_dn [ms] = (indeks − pre_n)·dt (znacznik k·dt, przekroczenie w (k·dt, (k+1)·dt]); first_dn_step = indeks w krokach
Przy dt = 1 i timing="legacy" wyniki są bit w bit równe v5v41.simulate (test_stage0_dt.py, T1a/T1c).
Kształty wyjść (biny 10 ms) nie zależą od dt, więc analizy V6 (×100 Hz, biny [50:100]) zachowują znaczenie.
"""
import numpy as np

from alif_dt import ALIFdt, to_steps
from decoder import SteerDecoder
from v5v41 import DEC_OFFSET, DEC_SLOPE, STEER

BIN_MS = 10


def simulate_dt(spec, idx, side, cfg, seed, P, initv_seed=None, timing="exact", make=ALIFdt):
    """Jeden przebieg. Prąd tylko na LC10a; początek skoku w t = pre_ms. make: fabryka sieci (testy podstawiają raster)."""
    dt = P.dt
    o = "R" if side == "L" else "L"
    net = make(spec, P, seed, timing=timing)
    if cfg.get("init_v"):
        net.v = np.random.default_rng(initv_seed).uniform(P.v_rest, P.v_th, net.N)
    N = net.N
    k_bin = to_steps(BIN_MS, dt, "exact")
    iI, iC = idx[f"in_{side}"], idx[f"in_{o}"]
    if "ramp" in cfg and cfg["ramp"]:
        lo, hi, half_ms = cfg["ramp"]
        half = to_steps(half_ms, dt, "exact")
        prof = np.r_[np.linspace(lo, hi, half, endpoint=False), np.linspace(hi, lo, half, endpoint=False)]
        pre_ms, pre, T = 0, 0, 2 * half
        ipsi_t, contra_t = prof, np.zeros(T)
    else:
        pre_ms = cfg.get("pre_ms", 0)
        pre = to_steps(pre_ms, dt, "exact")
        T = pre + to_steps(cfg["step_ms"], dt, "exact")
        ipsi_t = np.full(T, cfg["I"])
        contra_t = np.full(T, cfg["I"] * cfg.get("contra_frac", 0.0))
        if pre:
            ipsi_t[:pre] = cfg["pre_mV"] if cfg["pre_side"] == "ipsi" else 0.0
            contra_t[:pre] = cfg["pre_mV"] if cfg["pre_side"] == "contra" else 0.0
    if T % k_bin:
        raise ValueError(f"czas przebiegu {T * dt} ms nie jest wielokrotnością binu {BIN_MS} ms")
    dec = SteerDecoder({"DNa02_L": idx["DNa02_L"], "DNa02_R": idx["DNa02_R"]}, ("DNa02",), [DEC_OFFSET], [DEC_SLOPE], STEER)
    nb = T // k_bin
    counts = np.zeros((nb, 6), np.int16)
    adapt = np.zeros((nb, 3), np.float32)
    angle = np.zeros(nb, np.float32)
    ss = np.zeros(N, np.int32)                          # spike'i per neuron w oknie [pre+500, pre+1000) ms
    first_dn = -1
    dn_i = idx[f"DNa02_{side}"][0]
    mL, mR = idx["mid_L"], idx["mid_R"]
    I = np.zeros(N)
    chunk = np.zeros((k_bin, N), bool)
    for b in range(nb):
        for j in range(k_bin):
            t = b * k_bin + j
            I[iI] = ipsi_t[t]
            I[iC] = contra_t[t]
            s = net.step(I)
            chunk[j] = s
            if first_dn < 0 and t >= pre and s[dn_i]:
                first_dn = t - pre
        counts[b] = (chunk[:, iI].sum(), chunk[:, iC].sum(), chunk[:, mL].sum(), chunk[:, mR].sum(),
                     chunk[:, idx["DNa02_L"]].sum(), chunk[:, idx["DNa02_R"]].sum())
        if pre_ms + 500 <= b * BIN_MS < pre_ms + 1000 and "ramp" not in cfg:
            ss += chunk.sum(0)
        adapt[b] = (net.a[iI].mean(), net.a[np.r_[mL, mR]].mean(), net.a[dn_i])
        angle[b] = dec.step(chunk, dt)["angle"][0]
    if not (np.isfinite(net.v).all() and np.isfinite(net.g).all() and np.isfinite(net.a).all()):
        raise FloatingPointError("non-finite ALIF state")
    return dict(counts=counts, adapt=adapt, angle=angle, ss=ss, first_dn=first_dn * dt if first_dn >= 0 else -1,
                first_dn_step=first_dn, pre=pre_ms, dt=dt, k_bin=k_bin, steps=T, T_ms=T * dt,
                timing=net.timing_report() if hasattr(net, "timing_report") else None)


def fano(counts):
    """Fano czynnik po osi binów (oś 0): var/mean, ddof = 0; NaN przy średniej 0."""
    c = np.asarray(counts, float)
    m = c.mean(0)
    return np.where(m > 0, c.var(0) / np.where(m > 0, m, 1), np.nan)
