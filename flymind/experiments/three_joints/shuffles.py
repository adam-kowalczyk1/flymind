"""Trzy stawy na sieciach potasowanych (plan: PREREG_TASOWANIA.md). Tylko MuJoCo.
  shuffles.py --selftest
  shuffles.py --nets N,F27310001,LS27330001 --out DIR [--seeds …]     (sieć z danych budowana raz, tasowania w pamięci)"""
import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import three_joints as T  # noqa: E402

JN = T.JN
ANN = JN.visual_path.ANN
COND = {"spokoj": None, "palec1": 0, "palec2": 1}
WIN = dict(przed=(0, 300), nacisk=(300, 500), po=(500, 800))


def shuffle_edges(pre, post, w, keys, n, seed, per_edge=5, max_rounds=400):
    """Podwójne zamiany (a→b, c→d) → (a→d, c→b) tylko w obrębie klucza (waga, grupa pre, grupa post); a≠d, c≠b, b≠d, nowe krawędzie
    nie istnieją. Rundami: każda krawędź najwyżej w jednej parze na rundę; przyjęte tylko zamiany bez kolizji. → (post', raport)."""
    rng, post, E = np.random.default_rng(seed), post.copy(), len(pre)
    done, rounds, target = 0, 0, per_edge * E
    while done < target and rounds < max_rounds:
        rounds += 1
        order = np.lexsort((rng.random(E), keys))                     # losowa kolejność w obrębie klucza
        k = keys[order]
        start = np.r_[0, np.flatnonzero(k[1:] != k[:-1]) + 1]
        rank = np.arange(E) - np.repeat(start, np.diff(np.r_[start, E]))
        i = np.flatnonzero((rank % 2 == 0) & np.r_[k[1:] == k[:-1], False])
        x, y = order[i], order[i + 1]
        a, b, c, d = pre[x], post[x], pre[y], post[y]
        ok = (b != d) & (a != c) & (a != d) & (c != b)
        x, y, a, b, c, d = (v[ok] for v in (x, y, a, b, c, d))
        n1, n2 = a * n + d, c * n + b
        cur = np.sort(pre * n + post)
        inside = lambda v: cur[np.minimum(np.searchsorted(cur, v), E - 1)] == v  # noqa: E731
        allnew, cnt = np.unique(np.r_[n1, n2], return_counts=True)
        dup = allnew[cnt > 1]
        good = ~(inside(n1) | inside(n2) | np.isin(n1, dup) | np.isin(n2, dup))
        post[x[good]], post[y[good]] = d[good], b[good]
        done += int(good.sum())
    return post, dict(seed=seed, swaps=done, target=target, rounds=rounds, complete=done >= target)


def make_keys(w, pre, post, g):
    """Jedna liczba na krawędź: (waga ze znakiem, grupa pre, grupa post)."""
    _, wi = np.unique(w, return_inverse=True)
    G = int(g.max()) + 1
    return wi.astype(np.int64) * G * G + g[pre].astype(np.int64) * G + g[post]


def group_labels(net):
    """{rodzina: etykieta grupy na neuron}; tylko z adnotacji MaleCNS i zbiorów neuronów sieci."""
    inv = {i: b for b, i in net.pos.items()}
    bodies = [inv[i] for i in range(net.N)]
    a = pd.read_feather(ANN, columns=["bodyId", "superclass", "somaSide", "rootSide", "subclass", "entryNerve"]).set_index("bodyId").reindex(bodies)
    side = np.where(a.somaSide.isin(["L", "R"]), a.somaSide, np.where(a.rootSide.isin(["L", "R"]), a.rootSide, "U")).astype(str)
    sc = a.superclass.fillna("NA").to_numpy().astype(str)
    sens = np.array([x.startswith(("vnc_sensory", "sensory_")) or x == "cb_sensory" for x in sc])
    layer = np.where(sens, "S", np.where(sc == "vnc_motor", "M", "I"))
    cls = np.where(np.char.startswith(sc, "vnc_sensory") | np.char.startswith(sc, "sensory_"), "vnc_sensory", sc)
    m = net._meta
    s1, s2, fl = set(m["sens1"]), set(m["sens2"]), set(m["flb"])
    leg = np.array(["T1" if b in s1 or b in fl else "T2" if b in s2 else "-" for b in bodies])
    raw = {"F": np.zeros(net.N, int).astype(str), "L": layer, "LS": np.char.add(np.char.add(cls, "_"), side)}
    raw["LSN"] = np.char.add(np.char.add(raw["LS"], "_"), np.where((layer == "S") | (layer == "M"), leg, "-"))
    net._part = dict(rdzen=np.isin(sc, ["vnc_intrinsic", "vnc_motor"]) | (sens & (sc != "cb_sensory")), mozg=~(np.isin(sc, ["vnc_intrinsic", "vnc_motor"]) | sens),
                     receptory_A0=np.isin(np.arange(net.N), net._full[0]), receptory_A1=np.isin(np.arange(net.N), net._full[1]),
                     MN_T1L=np.array([b in fl for b in bodies]))
    return raw


def use_matrix(net, W):
    net._spec, net._Wc = JN.LB._W(W.tocsr()), W.tocsc()


def build():
    net = T.build(-1.0)
    net._meta = T.R.nets.bodies_for("pre")[1]
    net._data = net._Wc.tocoo()
    net.W = None                                                      # gęsta macierz niepotrzebna (RAM)
    net._labels = group_labels(net)
    return net


def set_net(net, tag):
    """tag: N albo rodzina + ziarno (np. LS27330001). Zwraca raport."""
    c = net._data
    post, pre, w = c.row.astype(np.int64), c.col.astype(np.int64), c.data
    if tag == "N":
        use_matrix(net, c)
        return dict(tag=tag, edges=len(w))
    fam, seed = tag.rstrip("0123456789"), int(tag[len(tag.rstrip("0123456789")):])
    lab, g = np.unique(net._labels[fam], return_inverse=True)
    p2, rep = shuffle_edges(pre, post, w, make_keys(w, pre, post, g), net.N, seed)
    W = sp.coo_matrix((w, (p2, pre)), shape=(net.N, net.N))
    same = np.isin(pre * net.N + p2, pre * net.N + post).mean()
    bc = lambda p, x: np.bincount(p, weights=x, minlength=net.N)  # noqa: E731
    assert len(np.unique(pre * net.N + p2)) == len(w), "zdublowane krawędzie"
    assert (np.bincount(post, minlength=net.N) == np.bincount(p2, minlength=net.N)).all() and np.allclose(bc(post, w), bc(p2, w))
    assert (g[post] == g[p2]).all(), "zmieniona grupa odbiorcy"
    assert rep["complete"], rep
    use_matrix(net, W)
    return dict(rep, tag=tag, edges=len(w), groups=len(lab), changed_frac=round(1 - float(same), 4))


class Drv(T.Drv):
    """Jak T.Drv + liczenie impulsów na neuron w oknach (nie wpływa na sieć)."""
    def __init__(self, net, feco, seed):
        super().__init__(net, feco, seed)
        self.i, self.cnt, run1 = 0, {k: np.zeros(net.N, np.int64) for k in WIN}, net.net.run

        def run(X, n):
            s = run1(X, n)
            for k, (a, b) in WIN.items():
                if a <= self.i < b:
                    self.cnt[k] += s.sum(0)
            self.i += 1
            return s
        net.net.run = run


def activity(net, drv):
    out = {}
    for k, (a, b) in WIN.items():
        hz = drv.cnt[k] / ((b - a) * T.DT)
        out[k] = dict(cala=float(hz.mean()), aktywne=float((hz > 0).mean()), **{p: float(hz[m].mean()) for p, m in net._part.items()},
                      aktywne_rdzen=float((hz[net._part["rdzen"]] > 0).mean()), aktywne_mozg=float((hz[net._part["mozg"]] > 0).mean()))
    return out


def run(net, feco, tag, seeds, out):
    path = os.path.join(out, tag + ".npz")
    if os.path.exists(path):
        print("jest", tag, flush=True)
        return
    t0 = time.time()
    rep, i0, i1 = set_net(net, tag), 300, 500
    data, act = {}, {}
    for s in seeds:
        for c, k in COND.items():
            net.pads = net._full
            feel, drv = T.TM.Feel(level="ideal", seed=s), Drv(net, feco, s)

            def felt(i):
                f = np.zeros(2)
                if k is not None and i0 <= i < i1:
                    f[k] = T.F_N
                return feel.step(f)
            g = T.simulate(drv, felt, 800)
            act[f"{s}_{c}"] = activity(net, drv)
            for x in ("q", "dq", "r", "flag", "guard", "ncon"):
                data[f"{s}_{c}_{x}"] = g[x] if x == "q" else g[x].astype(np.float32)
            data["q0"] = g["q0"]
    rep.update(wall_s=round(time.time() - t0, 1), activity=act)
    np.savez_compressed(path, **data)
    with open(path.replace(".npz", ".json"), "x") as f:
        json.dump(rep, f)
    print(tag, {k: v for k, v in rep.items() if k != "activity"}, flush=True)


def selftest():
    import side_shuffle as SS
    from snn_interface import SNNSpec
    rng = np.random.default_rng(3)
    n, sign = 300, np.where(np.arange(300) % 3, 1.0, -1.0)
    W = (rng.random((n, n)) < 0.15) * rng.integers(1, 4, (n, n)) * 0.2 * sign[None, :]
    np.fill_diagonal(W, 0)
    spec = SNNSpec(np.arange(1, n + 1), None, sign, W, np.zeros((n, n)), {})
    for g in (np.zeros(n, int), rng.integers(0, 6, n)):
        po, pr = np.nonzero(W)
        w = W[po, pr]
        p2, rep = shuffle_edges(pr, po, w, make_keys(w, pr, po, g), n, 1)
        W2 = np.zeros((n, n))
        W2[p2, pr] = w
        props = SS.properties(spec, SNNSpec(spec.bodies, None, sign, W2, np.zeros((n, n)), {}), g.astype(str))
        assert all(props[k] for k in SS.KEYS), {k: props[k] for k in SS.KEYS if not props[k]}
        old = SS.shuffle_within_side(spec, g.astype(str), 1)
        print("grup", len(set(g)), rep, "| zmienione krawędzie: nowa", props["changed_frac"], "stara", SS.properties(spec, old, g.astype(str))["changed_frac"])
    print("selftest OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--nets")
    ap.add_argument("--seeds", default=",".join(str(27301000 + i) for i in range(1, 11)))
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        sys.exit(0)
    os.makedirs(a.out, exist_ok=True)
    net, feco = build(), T.alive.feco_idx(-1.0)
    print({k: len(set(v)) for k, v in net._labels.items()}, {k: int(v.sum()) for k, v in net._part.items()}, flush=True)
    for tag in a.nets.split(","):
        run(net, feco, tag, [int(s) for s in a.seeds.split(",")], a.out)
