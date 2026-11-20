"""Why r1 (TARGET_why_r1.md): dotyk czubka vs dłoni → pule ruchowe nogi T1 (ramię). Opisowe, nic nie stroi."""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../step3_wiring"))
import live_avoid as LA  # noqa: E402
import reflex as R  # noqa: E402

SEEDS = range(2011230, 2011235)
F = 3.3


def trial(net, q, seed, touch, mute):
    net.net = R.SparseALIF(net._spec, R.ALIFParams(noise=2.0), seed)
    net.net.step = LA.fast_step(net.net, net.net.W.tocsc())
    net.r, net.rj, net.tau = np.zeros((5, 2)), np.zeros(2), 0.0
    run0, last = net.net.run, {}

    def run(X, n):
        X = X.copy()
        if mute:
            X[net._grp["MDN"]] = -200.0
        last["s"] = run0(X, n)
        return last["s"]
    net.net.run = run
    rates, dq = np.zeros((3, 2)), np.zeros(3)
    for _ in range(100):
        dq += net.step(np.array(touch), q, np.zeros(5), 0.01)[1:4]
        s = last["s"] * 1000.0
        rates += [[s[:, p].mean(), s[:, n].mean()] for p, n in (net.pools[j] for j in (1, 2, 3))]
    return rates / 100, np.degrees(dq), float((last["s"][:, net._grp["MDN"]]).mean() * 1000)


def main():
    net = LA.build(glu=-1, brake="hub", layout="czubek")      # pads = (A0, czubek); kanał 3 = dłoń → BM
    q = net._world.sim.d.qpos[net._world.sim.qadr][:5].copy()
    conds = {"nic": ([0, 0, 0], 0), "czubek": ([0, F, 0], 0), "A0": ([F, 0, 0], 0), "dlon": ([0, 0, F], 0),
             "czubek_bezMDN": ([0, F, 0], 1), "dlon_bezMDN": ([0, 0, F], 1)}
    out = {}
    for k, (t, m) in conds.items():
        r = [trial(net, q, s, t, m) for s in SEEDS]
        out[k] = dict(rates=np.mean([x[0] for x in r], 0).tolist(), dq_deg=np.mean([x[1] for x in r], 0).tolist(),
                      dq_deg_seeds=[x[1].tolist() for x in r])
        print(k, "pule POS/NEG [Hz]", np.round(out[k]["rates"], 2).tolist(), "ramię Δ° 1 s", np.round(out[k]["dq_deg"], 2).tolist(), flush=True)
    Z = np.array(out["nic"]["rates"])
    d = {k: np.array(out[k]["rates"]) - Z for k in out}
    S = lambda k: float(np.abs(d[k]).sum())                         # noqa: E731
    K = lambda k: float(np.abs(d[k][:, 0] - d[k][:, 1]).sum())      # noqa: E731
    s, kk = S("czubek") / S("dlon"), K("czubek") / K("dlon")
    verdict = "nie dochodzi" if s < 0.2 else "znosi się" if kk < 0.2 else "dochodzi z kierunkiem"
    # D3: budowa — wagi bezpośrednie i dwuetapowe (W[post, pre])
    W = np.asarray(net.W)                                   # gęsta W[post, pre] tej samej sieci
    tip, bm, mdn = net.pads[1], net.palm, net._grp["MDN"]
    d3 = {}
    for j in (1, 2, 3):
        for lab, pool in zip(("POS", "NEG"), net.pools[j]):
            row = W[pool, :]
            for g, ix in (("czubek", tip), ("dlon", bm)):
                two = row @ W[:, ix]
                via = row[:, mdn] @ W[np.ix_(mdn, ix)]
                d3[f"j{j}_{lab}_{g}"] = dict(direct=float(W[np.ix_(pool, ix)].sum()), two_hop=float(two.sum()), via_MDN=float(via.sum()))
    res = dict(F=F, seeds=list(SEEDS), conditions=out, S_ratio=s, K_ratio=kk, verdict=verdict,
               K_mute=dict(czubek=K("czubek_bezMDN"), dlon=K("dlon_bezMDN"), czubek0=K("czubek"), dlon0=K("dlon")), D3=d3,
               n=dict(tip=len(tip), bm=len(bm), mdn=len(mdn), pools={j: [len(p), len(n)] for j, (p, n) in net.pools.items()}))
    json.dump(res, open(os.path.join(HERE, "results/why_r1.json"), "w"), indent=1)
    print(f"D1: S czubek/dłoń = {s:.3f}, K czubek/dłoń = {kk:.3f} → „{verdict}”")
    print("D2: K czubek", round(K("czubek"), 2), "→ bez MDN", round(K("czubek_bezMDN"), 2), "| K dłoń", round(K("dlon"), 2), "→ bez MDN", round(K("dlon_bezMDN"), 2))
    for k, v in d3.items():
        print("D3", k, {a: round(b, 2) for a, b in v.items()})


if __name__ == "__main__":
    main()
