"""Diagnoza (19 XI, rozwój, NIE test): dlaczego wzrok osłabia cofnięcie po dotyku dłoni (avoid r1: bez wzroku 14/15, ze wzrokiem 9/15).
Pary prób z tym samym ziarnem szumu: full (wzrok + dotyk) i blind (sam dotyk), układ hw2p (A0 szczęka stała + P dłoń), Glu −1.
Zapis: wynik próby (JSON) + liczba spików KAŻDEGO neuronu w każdym takcie 10 ms (npz, uint8).
Uruchom: diag_vision.py --out DIR --seeds 21950001,... [--conds full,blind] [--dirs left,right,front] [--silence plik.json]
--silence: lista indeksów neuronów, którym zerujemy wyjścia (jak wycięcie DNg15+DNge078 w avoid.py) — do sprawdzania przyczyn."""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import avoid as A  # noqa: E402
import head  # noqa: E402
import touch_map as TM  # noqa: E402


def build(glu=-1.0):
    net = head.HeadLife(glu, "N", None, eyes=True)
    net.pads = TM.pads_for(net, "somato")
    net._eyes = A.eye_idx(net)
    return net


def silence(net, idx):
    import scipy.sparse as sp
    mask = np.ones(net.N)
    mask[list(idx)] = 0.0
    net.W = sp.csr_matrix(net.W.multiply(mask[None, :])) if sp.issparse(net.W) else net.W * mask[None, :]


def run(net, d, seed, cond, glu=-1.0):
    spikes, base = [], A.R.SparseALIF

    class Rec(base):
        def run(self, X, n):
            s = super().run(X, n)
            spikes.append(np.minimum(np.asarray(s).sum(0), 255).astype(np.uint8))
            return s
    A.R.SparseALIF = Rec
    try:
        feel = TM.Feel(r_fix=5100.0, level="typ", seed=seed)
        feel.discs = ("A0", "P")
        res, log = A.trial(net, d, 2.0, seed, blind=cond == "blind", frozen=cond == "frozen", numb=cond == "numb",
                           feco=A.alive.feco_idx(glu), aim="palm", feel=feel)
    finally:
        A.R.SparseALIF = base
    return res, log, np.array(spikes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--conds", default="full,blind")
    ap.add_argument("--dirs", default="left,right,front")
    ap.add_argument("--silence")
    ap.add_argument("--tag", default="N")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    net = build()
    meta = os.path.join(a.out, "net_meta.npz")
    if not os.path.exists(meta):                    # obszary (jak podgląd mózgu) + macierz połączeń do analizy bez budowania sieci
        import scipy.sparse as sp
        import brain_view as BV
        net.glu = -1.0
        reg, ty = BV.regions(net)
        body = np.zeros(net.N, np.int64)
        for b, i in net.pos.items():
            body[i] = b
        np.savez_compressed(meta, reg=reg.astype(str), type=ty.astype(str), body=body, palm=np.array(net.palm))
        sp.save_npz(os.path.join(a.out, "net_W.npz"), sp.csr_matrix(net.W))
    if a.silence:
        silence(net, json.load(open(a.silence)))
    for d in a.dirs.split(","):
        for s in map(int, a.seeds.split(",")):
            for c in a.conds.split(","):
                out = os.path.join(a.out, f"{a.tag}_{c}_{d}_{s}")
                if os.path.exists(out + ".json"):
                    continue
                res, log, sp = run(net, d, s, c)
                np.savez_compressed(out + ".npz", spikes=sp, **{k: np.array(v) for k, v in log.items()})
                with open(out + ".json", "x") as f:
                    json.dump(dict(res, dir=d, seed=s, cond=c, tag=a.tag), f)
                print(c, d, s, json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
