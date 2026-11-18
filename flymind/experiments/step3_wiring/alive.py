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


Q_LIM = 1.69   # rad: zakres łokcia SO-101; ponytail: ten sam dla stawów 1–3 (kinematyka bez MuJoCo), MuJoCo gdy trzeba ciała


def feco_idx(glu):
    import nets2
    bm, d78, d15 = B.route_ids()
    return nets2.build_ext(glu, bm + d78 + d15)[1]["feco"]   # pozycje „pre” nie zależą od tasowania ani od --head


def run(net, sigma, seed, T, dt=0.01, feco=None, q2=0.0):
    """feco: indeksy FeCO T1 L → czucie własnego łokcia (kodowanie jak step2 joint_net: claw = kąt, hook = prędkość, 40 mV)."""
    net.net = R.SparseALIF(R.JN.LB._W(net.W), R.ALIFParams(noise=sigma), seed)
    net.r, net.rj, net.tau = np.zeros((5, 2)), np.zeros(2), 0.0
    q, qd, Q, TAU, rate = np.zeros(5), np.zeros(5), [], [], []
    q[2] = q2                                                   # spoczynkowe zgięcie łokcia (noga nie stoi w środku zakresu)
    if feco:
        run0 = net.net.run

        def run_feco(X, n):
            X, e, v = X.copy(), q[2] / Q_LIM, qd[2] / 1.0
            for k, x in (("claw_flex", e), ("claw_ext", -e), ("hook_flex", v), ("hook_ext", -v)):
                X[feco[k]] = 40.0 * min(1.0, max(0.0, x))
            return run0(X, n)
        net.net.run = run_feco
    cnt, run1 = np.zeros(net.N), net.net.run

    def run_count(X, n):                                        # liczy kolce każdego neuronu (aktywność głowy i nogi)
        sp = run1(X, n)
        cnt[:] += sp.sum(axis=0)
        return sp
    net.net.run = run_count
    for _ in range(int(round(T / dt))):
        q1 = np.clip(q + net.step(np.zeros(3), q, qd, dt), -Q_LIM, Q_LIM)
        qd, q = (q1 - q) / dt, q1
        Q.append(q[1:4].copy())
        TAU.append(net.tau)
        rate.append(net.r[1:4].copy())
    run.hz = cnt / T                                            # Hz na neuron
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
    # serie ruchu: |v| ramienia > 0,05 rad/s; CV odstępów między startami: ~0 rytm, ~1 przypadek (Poisson), >1 seriami jak zwierzę
    mv = np.abs(v).max(axis=1) > 0.05
    on = np.flatnonzero(mv[1:] & ~mv[:-1])
    iv = np.diff(on) * dt
    out["bouts"] = dict(n=int(len(on)), cv_interval=round(float(iv.std() / iv.mean()), 2) if len(iv) > 2 else None,
                        mean_bout_s=round(float(mv.sum() * dt / max(1, len(on))), 3))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--glu", type=float, required=True)
    ap.add_argument("--net", default="N")
    ap.add_argument("--shuffle-seed", type=int)
    ap.add_argument("--noise", type=float, required=True)
    ap.add_argument("--noise-seed", type=int, required=True)
    ap.add_argument("--T", type=float, default=30.0)
    ap.add_argument("--feco", action="store_true")
    ap.add_argument("--q2", type=float, default=0.0)
    ap.add_argument("--head", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"istnieje {a.out}")
    if a.head:
        import head
        net = head.HeadLife(a.glu, a.net, a.shuffle_seed)
    else:
        net = B.BrainNet(a.glu, a.net, a.shuffle_seed)
    Q, TAU, rate = run(net, a.noise, a.noise_seed, a.T, feco=feco_idx(a.glu) if a.feco else None, q2=a.q2)
    hz, n0 = run.hz, (net.N - net.rep.get("n_head", 0))
    act = dict(leg_mean_hz=round(float(hz[:n0].mean()), 3), leg_active_frac=round(float((hz[:n0] > 0).mean()), 4))
    if a.head:
        act.update(head_mean_hz=round(float(hz[n0:].mean()), 3), head_active_frac=round(float((hz[n0:] > 0).mean()), 4))
    res = dict(vars(a), **describe(Q, TAU), **act, mean_pool_rates=rate.mean(axis=0).round(2).tolist())
    np.savez_compressed(a.out.replace(".json", ".npz"), Q=Q.astype(np.float32), TAU=TAU.astype(np.float32))
    with open(a.out, "x") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res))
