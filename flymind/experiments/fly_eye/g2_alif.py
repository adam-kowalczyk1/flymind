"""G2-ALIF: czy T4/T5 z MaleCNS rozróżniają kierunek ruchu przy JEDNAKOWYCH parametrach ALIF (silnik projektu)?

Cel i kryteria: LOOP_TARGET_G2_ALIF.md. Jedyna zmiana względem bramki r1 (v1_camera_input, model stopniowany M-G):
model neuronu = SparseALIF z flymind (ALIFParams() bez zmian, impulsowy). Wszystko inne pożyczone bez zmian:
wycinek (optic_slice.build), bodźce i fotoreceptor (eye_gate.stimulus + te same filtry), tasowanie C1
(eye_gate.shuffle_typed), znaki (eye_gate.SIGN), format wyniku i analiza (eye_gate_analysis.py, progi G1–G3).

Wejście tylko do L1/L2/L3 wszystkich kolumn wycinka, jedną regułą. Żaden T4/T5/LC/LPLC nie dostaje prądu z bodźca.
[MODEL] stały prąd I_BIAS i szum SIGMA dostaje KAŻDY neuron jednakowo (odpowiednik V_rest > 0 z r1: sieć ma spoczynkową
aktywność, więc światło może ją zmniejszać i zwiększać).

Uruchomienie: g2_alif.py data OUT.npz | shuffle SEED OUT.npz | smoke. Zapis tylko w trybie „x”.
"""
import os
import sys
import time
from types import SimpleNamespace

import numpy as np
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
FM = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path[:0] = [FM, os.path.join(FM, "experiments", "v1_camera_input")]
import eye_gate as G  # noqa: E402
import optic_slice as OS  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402

P = ALIFParams()                 # parametry projektu, bez zmian, jednakowe dla wszystkich typów
J0 = 0.2                         # mV/synapsę, jak FlyJawCfg.J0 i visual_path; połowione tylko regułą pick_j0
I_BIAS, SIGMA = 10.0, 3.0        # [MODEL] mV, jednakowo dla wszystkich neuronów
K_MV = 20.0                      # [MODEL] mV na jednostkę log-kontrastu fotoreceptora → L1/L2/L3 (znak −, jak r1)
TAU_R = 20.0                     # ms, wygładzanie impulsów do częstości
WARM = 1000                      # ms stałego obrazu przed t = 0 (adaptacja τ_a = 300 ms dochodzi do równowagi)
KEEP = ["L1", "L2", "Mi1", "Tm3", "Tm1"] + [f"T4{s}" for s in "abcd"] + [f"T5{s}" for s in "abcd"]
POOLS = {"smoke": range(23501001, 23501100), "data": range(23502001, 23502011), "shuffle": range(23503001, 23503041)}


def weights(S, j0):
    sign = np.array([0.0 if t is None else G.SIGN.get(t, 0.0) for t in S["nt"]])   # Glu −1, histamina −1 (jak r1)
    N = len(S["bodies"])
    return sp.csr_matrix((sign[S["pre"]] * j0 * S["n"], (S["post"], S["pre"])), shape=(N, N))


def batched_net(W, M):
    """SparseALIF z flymind z (N × M) stanem: M niezależnych przebiegów naraz. Równania klasy bez zmian."""
    N = W.shape[0]
    net = SparseALIF(SimpleNamespace(W=W), P, None, gain=np.ones((N, 1)), b_a=np.full((N, 1), P.b_a))
    net.v = np.full((N, M), P.v_rest); net.g = np.zeros((N, M)); net.a = np.zeros((N, M)); net.ref = np.zeros((N, M))
    net.buf = np.zeros((P.delay_steps, N, M), bool)
    return net


def simulate(W, S, kind, units, speed=None):
    """Zwraca R [N × B × 2 połowy jednostek]: S0 = średnia zmiana częstości w oknie; S1 = szczyt (częstość − spoczynek).
    Częstość uśredniana po jednostkach połowy PRZED wzięciem szczytu (impulsy są szumne)."""
    inp, T, lum, combos = G.stimulus(S, kind, speed)
    N, B, U = W.shape[0], len(combos), len(units)
    h = U // 2
    rngs = [np.random.default_rng([u, 0]) for u in units]
    net = batched_net(W, B * U)
    a = np.tile(np.log(lum(0)), (1, U)); y1 = np.zeros_like(a); y2 = np.zeros_like(a)   # fotoreceptor jak eye_gate.simulate
    r = np.zeros((N, B * U))
    rest = np.zeros((N, B, 2)); resp = np.zeros((N, B, 2)); peak = np.full((N, B, 2), -np.inf)
    for t in range(-WARM, T):
        lg = np.tile(np.log(lum(max(t, 0))), (1, U))
        a += P.dt / 1000.0 * (lg - a)
        y1 += P.dt / 12.0 * ((lg - a) - y1); y2 += P.dt / 12.0 * (y1 - y2)
        I = I_BIAS + SIGMA * np.hstack([g.standard_normal((N, B)) for g in rngs])
        I[inp] -= K_MV * y2
        spk = net.step(I)
        r += P.dt / TAU_R * (spk * (1000.0 / P.dt) - r)
        if t < G.PRE_MS - 200:
            continue
        x = r.reshape(N, U, B)
        rh = np.stack([x[:, :h].mean(1), x[:, h:].mean(1)], -1)
        if t < G.PRE_MS:
            rest += rh / 200
        else:
            resp += rh
            np.maximum(peak, rh - rest, out=peak)
    if not (np.isfinite(net.v).all() and np.isfinite(net.g).all()):
        raise FloatingPointError("stan sieci NaN/inf")
    return (resp / (T - G.PRE_MS) - rest) if kind == "S0" else peak, rest


def pick_j0(S, units):
    """Reguła (przed danymi): J0 = 0,2, połowić aż w spoczynku S0: średnia < 50 Hz i < 5 % neuronów ≥ 0,9·r_max."""
    j0 = J0
    while j0 > 1e-3:
        W = weights(S, j0)
        _, rest = simulate(W, S, "S0", units)
        if rest.mean() < 50 and (rest.mean((1, 2)) >= 0.9 * P.r_max).mean() < 0.05:
            return j0, W
        j0 /= 2
    raise RuntimeError("brak stabilnego J0")


def run(S, units):
    j0, W = pick_j0(S, units[:2])
    out = [simulate(W, S, "S0", units)[0]] + [simulate(W, S, "S1", units, speed=v)[0] for v in G.SPEEDS]
    return j0, np.stack(out, 1)                                   # [N × 4 × 12 × 2]


def main():
    mode = sys.argv[1]
    S = OS.build()
    if mode == "smoke":
        units = [23501001, 23501002]
        t0 = time.time(); j0, W = pick_j0(S, units)
        _, rest = simulate(W, S, "S0", units)
        print("J0", j0, "spoczynek śr. Hz", round(rest.mean(), 1), "czas S0+pick", round(time.time() - t0, 1), "s")
        for ty in ("L1", "Mi1", "Tm3", "T4a", "T5a", "LPLC2"):
            k = S["type"] == ty
            print(f"  {ty:6s} n={k.sum():4d} spoczynek {rest[k].mean():6.1f} Hz")
        t0 = time.time(); R, _ = simulate(W, S, "S1", units, speed=240.0); print("S1 240 °/s", round(time.time() - t0, 1), "s", R.shape)
        return
    out = sys.argv[-1]
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    data_units = list(POOLS["data"])
    if mode == "data":
        units, shuf, done = data_units, None, 0
    else:
        shuf = int(sys.argv[2])
        assert shuf in POOLS["shuffle"], "ziarno spoza puli tasowań"
        units = data_units[:4]                                     # pary szumu z danymi, jak r1
        S, done = G.shuffle_typed(S, shuf)
    j0, R = run(S, units)
    sel = np.where(np.isin(S["type"], KEEP))[0]
    np.savez_compressed(open(out, "xb"), R=R[sel].astype(np.float32), types=S["type"][sel], bodies=S["bodies"][sel], g=j0,
                        glu=-1.0, units=np.array(units), shuffle_seed=-1 if shuf is None else shuf, swaps=done)
    print("zapisano", out, R[sel].shape, "J0", j0)


if __name__ == "__main__":
    main()
