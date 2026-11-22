"""CMA-ES „nie dać się dotknąć” (22 XI 2026, plan: PREREG_CMAES.md). Stroimy POKRĘTŁA, połączenia z MaleCNS bez zmian.
Sieć: brainleg.BrainNet („pre” + 69 BM + 2 DNge078 + 2 DNg15, 3 221 neuronów). Zadanie i miara: step3_wiring/avoid.trial
(ręka = kula 4 cm, 0,3 m/s, w dłoń; dotyk hw2p: A0 szczęka stała → szczecinki nogi „udo”, P dłoń → BM; bez wzroku; szum 2 mV).
Pokrętła (log-skala, wzmocnienie = exp(x), x ∈ [−3, 3], start 0 = sieć jak dotąd):
  2  wejścia: A0, dłoń;   6  wyjścia: pule POS/NEG stawów 1–3;   ≤25 bloki połączeń grupa_pre → grupa_post
  (S czucie nogi, BM, DN, I interneurony, M motoneurony; tylko bloki z synapsami);   1  siła wszystkich synaps hamujących.
„Bez muchy”: 2 wejścia + 6 wyjść + 12 wag czujnik → pula (prosto do stawów, bez sieci).
Uruchom:  cma_avoid.py train --net N|L|D [--shuffle-seed S] --cma-seed C --seeds a,b --gens G --lam 12 --out DIR
          cma_avoid.py test  --net N|L|D [--shuffle-seed S] --params best.json|zero --seeds ... --conds full,numb,lesion --out P.json
          cma_avoid.py selftest   (sam CMA-ES na funkcji kwadratowej, bez symulacji)"""
import argparse
import json
import os
import pickle
import sys
import time

import numpy as np
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "step3_wiring"))
TEST_SEEDS = set(range(26120001, 26120006))
DIRS = ("left", "right", "front")
GROUPS = ("S", "BM", "DN", "I", "M")
LO, HI, SIGMA0 = -3.0, 3.0, 0.5


class CMA:
    """Najprostszy CMA-ES (Hansen, „purecma”): rank-1 + rank-μ, ścieżka σ. ponytail: pełna macierz C, dla wymiaru ≤40 wystarcza."""
    def __init__(self, x0, sigma, lam, seed):
        n = len(x0)
        self.n, self.lam, self.mu = n, lam, lam // 2
        w = np.log(self.mu + 0.5) - np.log(np.arange(1, self.mu + 1))
        self.w = w / w.sum()
        self.mueff = 1 / (self.w ** 2).sum()
        self.cc = (4 + self.mueff / n) / (n + 4 + 2 * self.mueff / n)
        self.cs = (self.mueff + 2) / (n + self.mueff + 5)
        self.c1 = 2 / ((n + 1.3) ** 2 + self.mueff)
        self.cmu = min(1 - self.c1, 2 * (self.mueff - 2 + 1 / self.mueff) / ((n + 2) ** 2 + self.mueff))
        self.ds = 1 + 2 * max(0, np.sqrt((self.mueff - 1) / (n + 1)) - 1) + self.cs
        self.chi = np.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n * n))
        self.m, self.sigma = np.array(x0, float), sigma
        self.pc, self.ps, self.C = np.zeros(n), np.zeros(n), np.eye(n)
        self.rng, self.gen = np.random.default_rng(seed), 0

    def ask(self):
        self.D2, self.B = np.linalg.eigh(self.C)
        self.D = np.sqrt(np.maximum(self.D2, 1e-20))
        self.Z = self.rng.standard_normal((self.lam, self.n))
        self.Y = self.Z * self.D @ self.B.T
        return self.m + self.sigma * self.Y

    def tell(self, f):
        i = np.argsort(f)[: self.mu]
        y = self.w @ self.Y[i]
        self.m = self.m + self.sigma * y
        zw = self.B @ (self.w @ self.Z[i])                       # = C^(−1/2)·y
        self.ps = (1 - self.cs) * self.ps + np.sqrt(self.cs * (2 - self.cs) * self.mueff) * zw
        hs = np.linalg.norm(self.ps) / np.sqrt(1 - (1 - self.cs) ** (2 * (self.gen + 1))) < (1.4 + 2 / (self.n + 1)) * self.chi
        self.pc = (1 - self.cc) * self.pc + hs * np.sqrt(self.cc * (2 - self.cc) * self.mueff) * y
        Yi = self.Y[i]
        self.C = ((1 - self.c1 - self.cmu) * self.C + self.c1 * (np.outer(self.pc, self.pc) + (1 - hs) * self.cc * (2 - self.cc) * self.C)
                  + self.cmu * (Yi.T * self.w) @ Yi)
        self.C = (self.C + self.C.T) / 2
        self.sigma *= np.exp(self.cs / self.ds * (np.linalg.norm(self.ps) / self.chi - 1))
        self.gen += 1


# ---------- sieć i pokrętła ----------
def build(kind, shuffle_seed=None, glu=-1.0):
    import alive
    import avoid as A
    import brainleg as B
    import live_avoid as LA
    import nets
    import pandas as pd
    import touch_map as TM
    R = A.R
    if not getattr(R, "_fast", False):                     # te same spiki co alif.ALIF.step (sprawdzane w live_avoid --check), szybciej
        class Fast(R.SparseALIF):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                self.step = LA.fast_step(self, self.W.tocsc())
        R.SparseALIF, R._fast = Fast, True
    if kind == "D":                                          # bez muchy: brak sieci
        net = type("Direct", (), {})()
        net.W, net.N, net.kind, net._eyes, net._feco = sp.csr_matrix((1, 1)), 1, "D", {"L": [], "R": []}, None
        net.names = ["in_A0", "in_palm"] + [f"out_j{j}{s}" for j in (1, 2, 3) for s in "+-"] + \
                    [f"w_{c}_j{j}{s}" for c in ("A0", "palm") for j in (1, 2, 3) for s in "+-"]
        return net
    net = B.BrainNet(glu, kind, shuffle_seed)
    net.pads = TM.pads_for(net, "somato")                     # ustawia też net.pos; A0 → pads[0]
    order = sorted(net.pos, key=net.pos.get)
    sc = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "superclass"]).set_index("bodyId").superclass.reindex(order).astype(str)
    g = np.array(["BM" if s == "cb_sensory" else "DN" if s == "descending_neuron" else "M" if s == "vnc_motor"
                  else "S" if "sensory" in s else "I" for s in sc])
    net.grp = np.array([GROUPS.index(x) for x in g])
    net.W0 = sp.csr_matrix(net.W, dtype=float)
    coo = net.W0.tocoo()                                      # W[post, pre]
    blk = net.grp[coo.row] * len(GROUPS) + net.grp[coo.col]
    net.blocks = sorted(set(blk.tolist()))
    net._blk, net._neg = blk, coo.data < 0
    net._coo = coo
    net.names = ["in_A0", "in_palm"] + [f"out_j{j}{s}" for j in (1, 2, 3) for s in "+-"] + \
                [f"blk_{GROUPS[b // 5]}->{GROUPS[b % 5]}" for b in net.blocks] + ["inh_all"]
    net.kind, net._eyes, net._feco = kind, {"L": [], "R": []}, alive.feco_idx(glu)
    net.dn = [net.pos[b] for b in B.route_ids()[1] + B.route_ids()[2]]
    net.rep.update(groups={k: int((g == k).sum()) for k in GROUPS}, n_knobs=len(net.names))
    return net


def set_knobs(net, x, lesion=False):
    x = np.clip(np.asarray(x, float), LO, HI)
    assert len(x) == len(net.names)
    e = np.exp(x)
    net._gin, net._gout = e[:2], e[2:8].reshape(3, 2)
    if net.kind == "D":
        net._wd = e[8:20].reshape(2, 6)
    else:
        c = net._coo
        bg = dict(zip(net.blocks, e[8:8 + len(net.blocks)]))
        d = c.data * np.array([bg[b] for b in net._blk]) * np.where(net._neg, e[-1], 1.0)
        W = sp.csr_matrix((d, (c.row, c.col)), shape=c.shape)
        if lesion:                                           # wycięcie DNg15 + DNge078: zerowane ich wyjścia (kolumny)
            m = np.ones(W.shape[0])
            m[net.dn] = 0.0
            W = sp.csr_matrix(W.multiply(m[None, :]))
        net.W = W
    import types
    net.step = types.MethodType(step_direct if net.kind == "D" else step_fly, net)
    net.r, net.rj, net.tau = np.zeros((5, 2)), np.zeros(2), 0.0


def _x(touch, gin):                                          # jak reflex.TwoNet.step: 40 mV/N, sufit 40 mV; potem wzmocnienie
    return np.array([gin[0] * min(40.0, 40.0 * max(0.0, float(touch[0]))), gin[1] * min(40.0, 40.0 * max(0.0, float(touch[2])))])


def _out(net, now, dt, tau_r=0.05):
    import nets
    dq = np.zeros(5)
    for j in (1, 2, 3):
        net.r[j] += dt / tau_r * (now[j - 1] * net._gout[j - 1] - net.r[j])
        dq[j] = nets.JN.SIGN[j] * 0.005 * dt * float(net.r[j, 0] - net.r[j, 1])
    return dq


def step_fly(net, touch, q, qd, dt=0.01):                     # hw2p: touch = [A0, 0, dłoń]
    X = np.zeros(net.N)
    xa, xp = _x(touch, net._gin)
    X[net.pads[0]] = xa
    X[net.palm] = xp
    s = net.net.run(X, 10)
    now = np.array([[s[:, p].mean(), s[:, n].mean()] for p, n in (net.pools[1], net.pools[2], net.pools[3])]) * 1000.0
    return _out(net, now, dt)


def step_direct(net, touch, q, qd, dt=0.01):                  # bez muchy: 2,5 Hz/mV · waga, prosto do pul stawów
    now = (2.5 * _x(touch, net._gin) @ net._wd).reshape(3, 2)
    return _out(net, now, dt)


# ---------- próby i ocena ----------
def scene(net, d, seed, cond="full"):
    import avoid as A
    import touch_map as TM
    f = TM.Feel(level="typ", seed=seed)                      # ziarno nerwów = ziarno szumu (jak avoid r1)
    f.discs = ("A0", "P")
    res, log = A.trial(net, d, 2.0, seed, blind=True, numb=cond == "numb", frozen=cond == "frozen", feco=net._feco, feel=f)
    T, Q = np.array(log["touch"]).max(axis=1), np.array(log["q"])
    k = int(np.argmax(T > 0.2)) if (T > 0.2).any() else len(T)
    res["premove"] = round(float(np.abs(Q[:max(k, 1)] - Q[0]).max(axis=0).sum()), 4)
    res["J"] = round(res["touched_s"] - 0.02 * min(10.0, max(0.0, res["end_gap_cm"])) + 2.0 * res["premove"], 4)
    return res


def fitness(net, x, seeds):
    set_knobs(net, x)
    return float(np.mean([scene(net, d, s)["J"] for d in DIRS for s in seeds]))


def train(a):
    if set(a.seeds) & TEST_SEEDS:
        sys.exit("ziarna testowe nie do uczenia")
    os.makedirs(a.out, exist_ok=True)
    net = build(a.net, a.shuffle_seed)
    n = len(net.names)
    st = os.path.join(a.out, "cma_state.pkl")
    es = pickle.load(open(st, "rb")) if os.path.exists(st) else CMA(np.zeros(n), SIGMA0, a.lam, a.cma_seed)
    logf = open(os.path.join(a.out, "progress.jsonl"), "a")
    while es.gen < a.gens:
        t0 = time.time()
        X = es.ask()
        f = [fitness(net, x, a.seeds) for x in X]
        i = int(np.argmin(f))
        es.tell(np.array(f))
        rec = dict(gen=es.gen, best=f[i], median=float(np.median(f)), sigma=es.sigma, wall_s=round(time.time() - t0, 1),
                   x_best=np.clip(X[i], LO, HI).round(4).tolist(), x_mean=np.clip(es.m, LO, HI).round(4).tolist())
        logf.write(json.dumps(rec) + "\n")
        logf.flush()
        print(json.dumps({k: rec[k] for k in ("gen", "best", "median", "sigma", "wall_s")}), flush=True)
        pickle.dump(es, open(st + ".tmp", "wb"))
        os.replace(st + ".tmp", st)
    # wynik = średnia rozkładu po ostatnim pokoleniu (mniej przeuczona niż najlepszy pojedynczy punkt; ustalone w planie)
    out = dict(net=a.net, shuffle_seed=a.shuffle_seed, cma_seed=a.cma_seed, seeds=a.seeds, gens=es.gen, lam=a.lam,
               names=net.names, x=np.clip(es.m, LO, HI).round(5).tolist(), rep=getattr(net, "rep", {}),
               J_train_final=fitness(net, es.m, a.seeds))
    json.dump(out, open(os.path.join(a.out, "best.json"), "w"), indent=1, default=float)


def test(a):
    if set(a.seeds) & TEST_SEEDS and not os.environ.get("CMA_FINAL_TEST"):
        sys.exit("ziarna testowe tylko w teście końcowym (CMA_FINAL_TEST=1)")
    if os.path.exists(a.out):
        sys.exit(f"istnieje {a.out}")
    net = build(a.net, a.shuffle_seed)
    x = np.zeros(len(net.names)) if a.params == "zero" else np.array(json.load(open(a.params))["x"])
    rows = []
    for cond in a.conds.split(","):
        set_knobs(net, x, lesion=cond == "lesion")
        for d in DIRS:
            for s in a.seeds:
                r = scene(net, d, s, "full" if cond == "lesion" else cond)
                rows.append(dict(cond=cond, dir=d, seed=s, **r))
                print(cond, d, s, r["touched_s"], r["J"], flush=True)
    json.dump(dict(vars(a), names=net.names, x=x.tolist(), rows=rows), open(a.out, "x"), indent=1, default=float)


def selftest():
    es = CMA(np.full(20, 2.0), 0.5, 12, 1)
    f = lambda x: float(((x - 0.7) ** 2).sum())  # noqa: E731
    while es.gen < 250:
        X = es.ask()
        es.tell(np.array([f(x) for x in X]))
    assert f(es.m) < 1e-6, f(es.m)
    print("selftest OK", f(es.m))


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"]:
        selftest()
        sys.exit(0)
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("train", "test"))
    ap.add_argument("--net", required=True, choices=("N", "L", "D"))
    ap.add_argument("--shuffle-seed", type=int)
    ap.add_argument("--cma-seed", type=int)
    ap.add_argument("--seeds", required=True, type=lambda s: [int(v) for v in s.split(",")])
    ap.add_argument("--gens", type=int, default=40)
    ap.add_argument("--lam", type=int, default=12)
    ap.add_argument("--params", default="zero")
    ap.add_argument("--conds", default="full")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if (a.net == "L") != (a.shuffle_seed is not None):
        sys.exit("--shuffle-seed wymagane dokładnie dla --net L")
    train(a) if a.mode == "train" else test(a)
