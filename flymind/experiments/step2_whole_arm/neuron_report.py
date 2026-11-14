"""Krok 2(a): raport pojedynczego neuronu ALIF (flymind/alif.py, bez zmian) — f–I, adaptacja, PSP, porównanie z Shiu 2024.

Tylko odczyt modułów wspólnych; wynik do nowego pliku JSON (tryb "x"). Uruchom z katalogu tymczasowego:
  .venv/bin/python -I -B flymind/experiments/step2_whole_arm/neuron_report.py OUT.json
Ziarna (tylko część z szumem): 20 000 001–20 000 005 (SEED_REGISTRY.md w tym katalogu).
"""
import json
import math
import os
import sys

import numpy as np

FLY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, FLY)
from alif import ALIF, ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402

SEEDS = range(20_000_001, 20_000_006)
I_GRID = np.round(np.arange(0.0, 60.01, 0.5), 2)


class Spec:
    def __init__(self, W):
        self.W = np.asarray(W, float)


def one(params, b_a=None, seed=0):
    return ALIF(Spec([[0.0]]), params, seed, b_a=None if b_a is None else [b_a])


def run_const(params, I, ms, b_a=None, seed=0):
    net = one(params, b_a, seed)
    return net.run(np.array([I]), int(round(ms / params.dt)))[:, 0]


def rates(spk, dt):
    t = np.flatnonzero(spk) * dt
    first = 1000.0 / (t[1] - t[0]) if len(t) > 1 else 0.0
    n = len(spk)
    return dict(first_isi_hz=round(first, 2),
                first_100ms_hz=round(spk[:int(100 / dt)].sum() * 10.0, 2),
                steady_last_1s_hz=round(spk[n - int(1000 / dt):].sum() * 1.0, 2))


def lif_theory(I, p):
    """Ciągły LIF bez adaptacji: f = 1/(t_ref + τ_m ln(I/(I − (V_th − V_rest)))) [Hz]."""
    d = p.v_th - p.v_rest
    return 0.0 if I <= d else 1000.0 / (p.t_ref + p.tau_m * math.log(I / (I - d)))


def psp(p, w, ms=60):
    """Odpowiedź błony na jeden impuls presynaptyczny o wadze w [mV] (skok g o w), bez adaptacji. Zwraca szczyt [mV]."""
    net = one(p, 0.0)
    net.g[:] = w
    v, spk = [], False
    for _ in range(int(ms / p.dt)):
        spk |= bool(net.step(np.zeros(1))[0])
        v.append(float(net.v[0]))
    return max(v) - p.v_rest, spk


def main(out):
    P1, P01 = ALIFParams(), ALIFParams(dt=0.1)
    rep = dict(params=P1.__dict__, r_max_dt1=P1.r_max, r_max_dt01=P01.r_max)

    # 1. f–I: bez szumu, 2 s stałego prądu; adaptacja projektu (b_a 0,5) i bez adaptacji (jak Shiu); dt 1 i 0,1 ms
    fi = []
    for I in I_GRID:
        row = dict(I_mV=float(I), lif_theory_hz=round(lif_theory(I, P1), 2))
        for tag, p, b in (("dt1_ba05", P1, None), ("dt1_ba0", P1, 0.0), ("dt01_ba05", P01, None), ("dt01_ba0", P01, 0.0)):
            row[tag] = rates(run_const(p, I, 2000, b), p.dt)
        fi.append(row)
    rep["fI"] = fi
    rep["rheobase_mV"] = {tag: next((r["I_mV"] for r in fi if r[tag]["steady_last_1s_hz"] > 0), None)
                          for tag in ("dt1_ba05", "dt1_ba0", "dt01_ba05", "dt01_ba0")}

    # 2. adaptacja (v2): skok prądu przez 2 s przy dt 0,1 ms; częstość chwilowa 1/ISI; dopasowanie
    #    r(t) = r_ss + (r0 − r_ss)·exp(−t/τ) — siatka τ 1…3000 ms, r_ss i r0 metodą najmniejszych kwadratów.
    #    (v1 liczyła z okien 50 ms przy dt 1 ms: rozdzielczość 20 Hz → τ niewiarygodne, wynik v1 = FAILED.)
    for I in (10.0, 20.0, 40.0):
        s = run_const(P01, I, 2000)
        t = np.flatnonzero(s) * P01.dt
        tm, r = (t[1:] + t[:-1]) / 2, 1000.0 / np.diff(t)
        best = None
        for tau in np.arange(1.0, 3000.0, 1.0):
            X = np.c_[np.ones_like(tm), np.exp(-tm / tau)]
            coef, res, *_ = np.linalg.lstsq(X, r, rcond=None)
            sse = float(((X @ coef - r) ** 2).sum())
            if best is None or sse < best[0]:
                best = (sse, tau, coef)
        sse, tau, (r_ss, amp) = best
        rep.setdefault("adaptation", {})[f"I{int(I)}"] = dict(
            first_isi_hz=round(float(r[0]), 1), last_isi_hz=round(float(r[-1]), 1), fit_tau_ms=float(tau),
            fit_r_ss_hz=round(float(r_ss), 1), fit_r0_hz=round(float(r_ss + amp), 1),
            ratio_last_to_first=round(float(r[-1] / r[0]), 3), n_isi=int(len(r)),
            rms_fit_hz=round(math.sqrt(sse / len(r)), 2), a_ss_mV_theory=round(0.5 * float(r_ss) * 0.3, 2))

    # 3. PSP: szczyt dla wagi jednej synapsy (projekt J0 0,2 / 0,275 mV; Shiu 0,275 mV) i ile synchronicznych synaps do spike'a
    rep["psp_peak_mV"] = {str(w): round(psp(P1, w)[0], 4) for w in (0.2, 0.275)}
    lo, hi = 0.0, 200.0
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if psp(P1, mid)[1] else (mid, hi)
    rep["w_for_spike_from_rest_mV"] = round(hi, 3)
    rep["synapses_for_spike"] = {str(J0): round(hi / J0, 1) for J0 in (0.2, 0.275)}

    # 4. szum σ = 2 mV (jak droga wzrokowa V5): f–I uśrednione po 5 ziarnach
    rep["fI_noise2"] = [dict(I_mV=float(I), steady_hz=[rates(run_const(ALIFParams(noise=2.0), I, 2000, None, s), 1.0)
                                                       ["steady_last_1s_hz"] for s in SEEDS]) for I in I_GRID[::4]]
    rep["seeds_noise"] = [SEEDS[0], SEEDS[-1]]

    # 5. SparseALIF (używany w obwodach nóg) = ALIF co do impulsu?
    a = run_const(P1, 20.0, 1000)
    sn = SparseALIF(Spec([[0.0]]), P1, 0)
    rep["sparse_equal"] = bool((sn.run(np.array([20.0]), 1000)[:, 0] == a).all())

    with open(out, "x") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k not in ("fI", "fI_noise2", "adaptation")}, indent=1))
    for r in fi[::8]:
        print(r["I_mV"], r["lif_theory_hz"], *(r[t]["first_isi_hz"] for t in ("dt1_ba0", "dt01_ba0")),
              *(r[t]["steady_last_1s_hz"] for t in ("dt1_ba05", "dt1_ba0", "dt01_ba05")))
    for k, v in rep["adaptation"].items():
        print(k, v)
    for r in rep["fI_noise2"]:
        print("noise2", r["I_mV"], r["steady_hz"])


if __name__ == "__main__":
    main(sys.argv[1])
