"""Test „GDZIE” r1 (cel: LOOP_TARGET_where_r1.md, zapisany przed uruchomieniem). Bez ramienia. Uruchom: where_test.py OUT.json (raz)."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brainleg as B  # noqa: E402
import fsr_live as FL  # noqa: E402
import reflex as R  # noqa: E402

SEED0, F_N, SIGMA = 21947000, 2.0, 2.0
FEAT = ["j1", "j2", "j3", "DNg15", "DNge078", "press", "release"]


def trial(net, live, which, seed):
    net.net = R.SparseALIF(R.JN.LB._W(net.W), R.ALIFParams(noise=SIGMA), seed)
    net.r, net.rj, net.tau = np.zeros((5, 2)), np.zeros(2), 0.0
    run0 = net.net.run                                         # zbieraczka spadów od nowa dla nowej SparseALIF

    def run(X, n):
        live.last = run0(X, n)
        return live.last
    net.net.run = run
    rows = []
    for i in range(130):
        f = [0.0, 0.0]
        if 50 <= i < 100:
            f[which] = F_N
        r = live.tick(f)
        if 50 <= i < 100:
            rows.append([r[k] for k in FEAT])
    return np.mean(rows, axis=0)


def stats(X0, X1):
    X = np.vstack([X0, X1])
    y = np.r_[np.zeros(len(X0)), np.ones(len(X1))]
    sd = np.maximum(X.std(0), 1.0)
    keep = X.std(0) > 0
    Z = X[:, keep] / sd[keep]
    ok = 0
    for i in range(len(Z)):
        m = np.ones(len(Z), bool)
        m[i] = False
        c0, c1 = Z[m & (y == 0)].mean(0), Z[m & (y == 1)].mean(0)
        ok += int((np.linalg.norm(Z[i] - c1) < np.linalg.norm(Z[i] - c0)) == (y[i] == 1))
    w = Z[y == 1].mean(0) - Z[y == 0].mean(0)
    p = Z @ (w / (np.linalg.norm(w) + 1e-12))
    sp = np.sqrt((p[y == 0].var(ddof=1) + p[y == 1].var(ddof=1)) / 2)
    return dict(acc=ok / len(Z), dprime=float((p[y == 1].mean() - p[y == 0].mean()) / max(sp, 1e-9)), dist=float(np.linalg.norm(w)),
                m0=X0.mean(0).round(2).tolist(), m1=X1.mean(0).round(2).tolist()), sd, keep


def main(out):
    assert not os.path.exists(out), out
    res, k = {}, 0
    for glu in (-1.0, 1.0):
        nets = [("N", None)] + [("F", s) for s in (21947901, 21947902, 21947903)]
        for kind, ss in nets:
            net = B.BrainNet(glu, kind, ss)
            live = FL.Live(net, "somato")
            maps = ["somato", "swap", "halves", "somato_bal"] if kind == "N" else ["somato"]
            for mp in maps:
                if mp == "somato_bal":
                    f, t = FL.TM.pads_for(net, "somato")
                    f = sorted(np.random.default_rng(21947800).choice(f, len(t), replace=False).tolist())
                    net.pads = (f, t)
                else:
                    net.pads = FL.TM.pads_for(net, mp)
                live.grp.update(udo=net.pads[0], golen=net.pads[1])
                X = {0: [], 1: []}
                for which in (0, 1):
                    for _ in range(10):
                        X[which].append(trial(net, live, which, SEED0 + k))
                        k += 1
                s, _, _ = stats(np.array(X[0]), np.array(X[1]))
                s["raw"] = {str(w): np.array(X[w]).round(2).tolist() for w in (0, 1)}
                res[f"{kind}{ss or ''}|{mp}|glu{int(glu):+d}"] = s
                print(f"{kind}{ss or ''} {mp} glu{int(glu):+d} ACC={s['acc']:.2f} D'={s['dprime']:.1f} dist={s['dist']:.2f}", flush=True)
            del net, live
    json.dump(res, open(out, "w"))


if __name__ == "__main__":
    main(sys.argv[1])
