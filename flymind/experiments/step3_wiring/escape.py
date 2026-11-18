"""Tryb „ucieczka przed ręką” (18 XI, prośba Adama). Sieć: noga + głowa (head.HeadLife, 15 254 n.).
Scena (kinematyka SO-101 z MuJoCo, bez fizyki): „dłoń” = kula r 4 cm leci prosto do POCZĄTKOWEGO położenia chwytaka z kierunku
left (+y) / right (−y) / front (+x, z góry), 0,3 m/s, staje 8 cm od niego (bez kontaktu).
Oko (MODEL, klasyczny kod): z punktu gripperframe kąt widzenia dłoni θ = 2·asin(r/d); zbliżanie L = max(0, dθ/dt).
Pobudzane TYLKO detektory zbliżania z danych: LPLC2 i LC4, oko lewe/prawe wg somaSide, waga strony w = (1 ± sin az)/2,
X = 40 mV · min(1, L / 2 rad/s) · w. Wszystko dalej (które DN, który staw, w którą stronę) = sieć muchy.
Ciało: jak cały krok 3/4 — pule stawów 1–3 → przyrost celu (dq), szczęka pominięta.
Uruchom: escape.py --glu ±1 --net N|F|L [--shuffle-seed S] --dir left|right|front|none --noise σ --noise-seed K --out PLIK.json"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import head  # noqa: E402
import nets  # noqa: E402
import reflex as R  # noqa: E402

JN = nets.JN
R_HAND, V_HAND, D0, D_STOP = 0.04, 0.30, 0.45, 0.08
L_FULL, MV = 2.0, 40.0
DIRS = {"left": (0, 1, 0), "right": (0, -1, 0), "front": (0.7, 0, 0.7), "none": (0, 1, 0)}
T_PRE, T_POST, DT = 0.5, 1.5, 0.01


def loom_idx(net):
    import pandas as pd
    a = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "type", "somaSide"])
    a = a[a.type.isin(["LPLC2", "LC4"]) & a.bodyId.isin(list(net.pos))]
    return {s: [net.pos[int(b)] for b in a.bodyId[a.somaSide == s]] for s in ("L", "R")}


def trial(net, direction, sigma, seed):
    w = JN.ForceWorld([("cyl", JN.oh.BASE_MATS[0])], 1)
    sim = w.sim
    q6 = sim.d.qpos[sim.qadr].copy()
    grip = lambda q: JN._kin(sim, q).site("gripperframe").xpos.copy()  # noqa: E731
    g0 = grip(q6)
    u = np.array(DIRS[direction], float)
    u /= np.linalg.norm(u)
    t_move = (D0 - D_STOP) / V_HAND
    eyes = loom_idx(net)
    net.net = R.SparseALIF(R.JN.LB._W(net.W), R.ALIFParams(noise=sigma), seed)
    net.r, net.rj, net.tau = np.zeros((5, 2)), np.zeros(2), 0.0
    loom = {"L": 0.0}
    run0 = net.net.run

    def run_eye(X, n):
        X = X.copy()
        for s, ix in eyes.items():
            X[ix] = loom[s]
        return run0(X, n)
    net.net.run = run_eye
    hz_t, n_leg = [], net.N - net.rep["n_head"]
    import pandas as pd
    a = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "type"])
    esc = [net.pos[int(b)] for b in a.bodyId[a.type.isin(["DNp01", "DNp02", "DNp04", "DNp11"])] if int(b) in net.pos]

    def run_count(X, k):                                           # aktywność: noga / głowa / detektory zbliżania
        sp = run_eye(X, k)
        m = sp.sum(axis=0) / (k * 1e-3)
        hz_t.append((m[:n_leg].mean(), m[n_leg:].mean(), (m[n_leg:] > 0).mean(), m[esc].mean()))
        return sp
    net.net.run = run_count
    th_prev, log = None, dict(t=[], d=[], loom=[], q=[], g=[])
    n = int(round((T_PRE + t_move + T_POST) / DT))
    for i in range(n):
        t = i * DT
        h = g0 + u * (D0 - V_HAND * min(max(0.0, t - T_PRE), t_move))
        g = grip(q6)
        v = h - g
        d = float(np.linalg.norm(v))
        th = 2 * np.arcsin(min(1.0, R_HAND / d))
        L = 0.0 if th_prev is None else max(0.0, (th - th_prev) / DT)
        th_prev = th
        sa = float(v[1] / np.linalg.norm(v[:2])) if np.linalg.norm(v[:2]) > 1e-6 else 0.0   # sin azymutu: + = lewo
        drive = 0.0 if direction == "none" else MV * min(1.0, L / L_FULL)
        loom["L"], loom["R"] = drive * (1 + sa) / 2, drive * (1 - sa) / 2
        dq = net.step(np.zeros(3), q6[:5], np.zeros(5), DT)
        q6[1:4] = np.clip(q6[1:4] + dq[1:4], sim.m.jnt_range[1:4, 0], sim.m.jnt_range[1:4, 1])
        for k, x in (("t", t), ("d", d), ("loom", L), ("q", q6[1:4].tolist()), ("g", g.tolist())):
            log[k].append(x)
    D, G = np.array(log["d"]), np.array(log["g"])
    # odniesienie: ramię nieruchome → odległość, jaką miałaby dłoń od chwytaka
    d_frozen = np.array([np.linalg.norm(g0 + u * (D0 - V_HAND * min(max(0.0, t - T_PRE), t_move)) - g0) for t in log["t"]])
    away = float(-(G[-1] - g0) @ u)                                     # przesunięcie chwytaka od dłoni (m)
    return dict(min_d=round(float(D.min()), 4), min_d_frozen=round(float(d_frozen.min()), 4),
                gain_cm=round(100 * float(D.min() - d_frozen.min()), 2), away_cm=round(100 * away, 2),
                move_cm=round(100 * float(np.linalg.norm(G[-1] - g0)), 2),
                dq_end=np.round(np.array(log["q"][-1]) - np.array(log["q"][0]), 3).tolist(),
                t_first_move=next((round(t, 2) for t, a, b in zip(log["t"][1:], log["q"][1:], log["q"]) if
                                   np.abs(np.array(a) - b).max() > 1e-4), None),
                n_eye=[len(eyes["L"]), len(eyes["R"])],
                hz_last1s=np.round(np.mean(hz_t[-100:], axis=0), 3).tolist(),            # noga Hz, głowa Hz, głowa % aktywnych, DN ucieczki Hz
                hz_peak=np.round(np.max(hz_t, axis=0), 3).tolist()), log


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--glu", type=float, required=True)
    ap.add_argument("--net", default="N")
    ap.add_argument("--shuffle-seed", type=int)
    ap.add_argument("--dir", required=True, choices=list(DIRS))
    ap.add_argument("--noise", type=float, default=2.0)
    ap.add_argument("--noise-seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"istnieje {a.out}")
    net = head.HeadLife(a.glu, a.net, a.shuffle_seed)
    res, log = trial(net, a.dir, a.noise, a.noise_seed)
    res = dict(vars(a), **res)
    np.savez_compressed(a.out.replace(".json", ".npz"), **{k: np.array(v) for k, v in log.items()})
    with open(a.out, "x") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res))
