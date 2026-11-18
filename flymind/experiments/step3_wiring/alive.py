"""„Ożywienie” (eksploracja, 18 XI): mózg muchy (BrainNet etapu 1) bez zadania i bez dotyku, tylko spontaniczna aktywność =
szum prądu σ mV w KAŻDYM neuronie jednakowo (ALIFParams.noise, jak brainleg_noise.py), żadnego celowego pobudzania.
Bez robota: liczy, co sieć „kazałaby” ramieniu przez T s (suma dq stawów 1–3 i moment szczęki z tych samych pul co w kroku 4).
Uruchom: alive.py --glu ±1 --net N|F|L [--shuffle-seed S] --noise σ --noise-seed K --T 30 --out PLIK.json"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brainleg as B  # noqa: E402
import reflex as R  # noqa: E402


def run(net, sigma, seed, T, dt=0.01):
    net.net = R.SparseALIF(R.JN.LB._W(net.W), R.ALIFParams(noise=sigma), seed)
    net.r, net.rj, net.tau = np.zeros((5, 2)), np.zeros(2), 0.0
    q, Q, TAU, rate = np.zeros(5), [], [], []
    for _ in range(int(round(T / dt))):
        q = q + net.step(np.zeros(3), q, np.zeros(5), dt)
        Q.append(q[1:4].copy())
        TAU.append(net.tau)
        rate.append(net.r[1:4].copy())
    return np.array(Q), np.array(TAU), np.array(rate)


def describe(Q, TAU, dt=0.01):
    v = np.diff(Q, axis=0) / dt
    out = dict(range_rad=np.ptp(Q, axis=0).round(4).tolist(), end_rad=Q[-1].round(4).tolist(),
               moving_frac=(np.abs(v) > 0.01).mean(axis=0).round(3).tolist(),            # takty z ruchem > 0,01 rad/s
               jaw_close_frac=round(float((TAU > 0.05).mean()), 3), tau_mean=round(float(TAU.mean()), 4))
    peaks = []
    for j in range(3):                                                                    # rytm: najsilniejsza częstotliwość ruchu
        x = v[:, j] - v[:, j].mean()
        if x.std() < 1e-6:
            peaks.append(None)
            continue
        f = np.fft.rfftfreq(len(x), dt)
        p = np.abs(np.fft.rfft(x)) ** 2
        k = 1 + int(np.argmax(p[1:]))
        peaks.append(dict(hz=round(float(f[k]), 2), share=round(float(p[k] / p[1:].sum()), 3)))
    out["rhythm"] = peaks
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--glu", type=float, required=True)
    ap.add_argument("--net", default="N")
    ap.add_argument("--shuffle-seed", type=int)
    ap.add_argument("--noise", type=float, required=True)
    ap.add_argument("--noise-seed", type=int, required=True)
    ap.add_argument("--T", type=float, default=30.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"istnieje {a.out}")
    net = B.BrainNet(a.glu, a.net, a.shuffle_seed)
    Q, TAU, rate = run(net, a.noise, a.noise_seed, a.T)
    res = dict(vars(a), **describe(Q, TAU), mean_pool_rates=rate.mean(axis=0).round(2).tolist())
    np.savez_compressed(a.out.replace(".json", ".npz"), Q=Q.astype(np.float32), TAU=TAU.astype(np.float32))
    with open(a.out, "x") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res))
