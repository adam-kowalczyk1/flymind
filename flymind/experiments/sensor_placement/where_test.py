"""„Mucha wie, gdzie czuje” (cel TARGET_where_r1.md): czubek vs A0 w tym samym mózgu co na żywo, mapa Elabbady (bristle_map_r1.json)."""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../step3_wiring"))
import live_avoid as LA  # noqa: E402
import reflex as R  # noqa: E402

SEEDS = range(2011210, 2011215)
KEYS = ("esc", "MDN", "DNg15", "DNge078", "j1", "j2", "j3", "tau")


def fresh(net, seed):
    net.net = R.SparseALIF(net._spec, R.ALIFParams(noise=2.0), seed)
    net.net.step = LA.fast_step(net.net, net.net.W.tocsc())
    net.r, net.rj, net.tau = np.zeros((5, 2)), np.zeros(2), 0.0
    run0, last = net.net.run, {}

    def run(X, n):
        last["s"] = run0(X, n)
        return last["s"]
    net.net.run = run
    return last


def trial(net, q, pads, seed, f_tip, f_a0, ticks=100):
    net.pads = pads
    last = fresh(net, seed)
    acc = np.zeros(len(KEYS))
    for _ in range(ticks):
        net.step(np.array([f_tip, f_a0, 0.0]), q, np.zeros(5), 0.01)
        s = last["s"] * 1000.0
        acc += np.r_[[s[:, ix].mean() for ix in (net._grp[k] for k in KEYS[:4])], net.r[1:4, 0] - net.r[1:4, 1], net.tau]
    return acc / ticks


def main():
    bm = json.load(open(os.path.join(HERE, "results/bristle_map_r1.json")))
    net = LA.build(glu=-1, brake="hub")
    q = net._world.sim.d.qpos[net._world.sim.qadr][:5].copy()
    tip, a0 = [net.pos[b] for b in bm["tip"]], [net.pos[b] for b in bm["A0"]]
    out = {}
    for name, (ft, fa) in {"nic": (0, 0), "czubek": (1, 0), "A0": (0, 1), "oba": (1, 1)}.items():
        out[name] = [trial(net, q, (tip, a0), s, ft, fa).tolist() for s in SEEDS]
        print(name, np.round(np.mean(out[name], 0), 2), flush=True)
    T, A, Z = np.array(out["czubek"]), np.array(out["A0"]), np.array(out["nic"])
    ok_none = bool((Z[:, :4] < 1.0).all())
    w1 = int((T[:, 1] > A[:, 1]).sum())
    # W2: najbliższy środek, zostaw jedno ziarno (wektor znormalizowany odchyleniem z wszystkich prób)
    X = np.r_[T, A]
    sd = X.std(0) + 1e-9
    acc = []
    for i in range(len(SEEDS)):
        mt, ma = np.delete(T, i, 0).mean(0), np.delete(A, i, 0).mean(0)
        for v, lab in ((T[i], 0), (A[i], 1)):
            acc.append(int(np.argmin([np.linalg.norm((v - mt) / sd), np.linalg.norm((v - ma) / sd)]) == lab))
    w2 = float(np.mean(acc))
    # W3: losowe podziały 310 szczecinek na 84/93
    allb = [net.pos[b] for b in json.load(open(os.path.join(HERE, "../step3_wiring/touch_map.json")))["femur"] +
            json.load(open(os.path.join(HERE, "../step3_wiring/touch_map.json")))["tibia_tarsus"]]
    rng = np.random.default_rng(2011215)
    real = np.linalg.norm((T.mean(0) - A.mean(0)) / sd)
    rnd = []
    for _ in range(100):
        p = rng.permutation(allb)
        g1, g2 = list(p[:len(tip)]), list(p[len(tip):len(tip) + len(a0)])
        r1 = np.mean([trial(net, q, (g1, g2), s, 1, 0) for s in list(SEEDS)[:2]], 0)
        r2 = np.mean([trial(net, q, (g1, g2), s, 0, 1) for s in list(SEEDS)[:2]], 0)
        rnd.append(float(np.linalg.norm((r1 - r2) / sd)))
    pct = float((np.array(rnd) < real).mean())
    res = dict(keys=KEYS, conditions=out, ok_none=ok_none, W1_seeds=w1, W1=w1 >= 4, W2_acc=w2, W2=w2 >= 0.9,
               W3_real=float(real), W3_random=rnd, W3_percentile=pct, n_tip=len(tip), n_A0=len(a0))
    json.dump(res, open(os.path.join(HERE, "results/where_r1.json"), "w"), indent=1)
    print(f"nic<1Hz: {ok_none} | W1 MDN czubek>A0 w {w1}/5 → {'ZDANE' if w1 >= 4 else 'NIE ZDANE'} | "
          f"W2 trafność {w2:.2f} → {'ZDANE' if w2 >= 0.9 else 'NIE ZDANE'} | W3 percentyl wśród losowych podziałów {pct:.2f}")


if __name__ == "__main__":
    main()
