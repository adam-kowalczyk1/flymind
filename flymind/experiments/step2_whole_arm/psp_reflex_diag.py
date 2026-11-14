"""Propozycja 7 (diagnostyka, eksploracja): czy obwód nogi T2 L działa jak odruch monosynaptyczny?

Obwód z leg_circuit.network (J0 0,2, szum 0), dotyk 40 mV na wszystkie szczecinki „mechanosensory bristle” (jak oba pady naraz),
500 ms. Mierzę dla pul szczęki (zaciskanie = Ti extensor, puszczanie = Ti flexor + Acc. ti flexor):
  1. średni wkład do g [mV] od receptorów, interneuronów i MN: Σ_pre W[mn, pre] · r_pre · τ_syn (stan ustalony filtra g);
  2. częstość pul w sieci pełnej, bez krawędzi IN→MN (sama droga bezpośrednia receptor→MN) i bez krawędzi receptor→MN
     (sama droga przez IN). Oba znaki Glu. Bez szumu — ziarna nieużywane.
  .venv/bin/python -I -B flymind/experiments/step2_whole_arm/psp_reflex_diag.py OUT.json
"""
import json
import os
import sys

import numpy as np

FLY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, FLY)
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402
from leg_circuit import network  # noqa: E402
from snn_interface import DEFAULT_SIGN  # noqa: E402

PRESS, RELEASE = ("Ti extensor MN",), ("Ti flexor MN", "Acc. ti flexor MN")


class _S:
    def __init__(self, W):
        self.W = W


def run(W, N, br, ms=500):
    X = np.zeros(N)
    X[br] = 40.0
    s = SparseALIF(_S(W), ALIFParams(), None).run(X, ms)
    return s[ms // 2:].mean(0) * 1000.0           # częstość [Hz] z drugiej połowy (po adaptacji wstępnej)


def main(out):
    p, res = ALIFParams(), {}
    for glu in (-1.0, 1.0):
        spec, idx, rep = network(0.2, "T2", "L", sign_map={**DEFAULT_SIGN, "glutamate": glu})
        W, N = spec.W, spec.W.shape[0]
        sens = np.array(sorted(i for v in idx["sensory"].values() for i in v))
        IN, MN = np.array(idx["IN"]), np.array(sorted(i for v in idx["MN"].values() for i in v))
        br = idx["sensory"]["mechanosensory bristle"]
        pools = {"press": [i for t in PRESS for i in idx["MN"][t]], "release": [i for t in RELEASE for i in idx["MN"][t]]}
        W_direct = W.copy()
        W_direct[np.ix_(MN, IN)] = 0.0                # bez IN → MN
        W_via_in = W.copy()
        W_via_in[np.ix_(MN, sens)] = 0.0              # bez receptor → MN
        r = {k: run(w, N, br) for k, w in (("full", W), ("direct_only", W_direct), ("via_IN_only", W_via_in))}
        out_g = {}
        for name, pool in pools.items():
            contrib = {c: float((W[np.ix_(pool, grp)] @ r["full"][grp]).mean() * p.tau_syn / 1000.0)
                       for c, grp in (("receptors", sens), ("IN", IN), ("MN", MN))}
            out_g[name] = dict(n=len(pool), g_contrib_mV=dict((k, round(v, 2)) for k, v in contrib.items()),
                               syn_from_receptors=int(round(np.abs(W[np.ix_(pool, sens)]).sum() / 0.2)),
                               syn_from_IN=int(round(np.abs(W[np.ix_(pool, IN)]).sum() / 0.2)),
                               rate_hz={k: round(float(v[pool].mean()), 1) for k, v in r.items()})
        res[f"glu{glu:+.0f}"] = dict(pools=out_g, mean_rate_hz={k: dict(receptors=round(float(v[sens].mean()), 1),
                                                                          IN=round(float(v[IN].mean()), 1),
                                                                          MN=round(float(v[MN].mean()), 1))
                                                                   for k, v in r.items()},
                                     torque_Nm={k: round(0.005 * float(v[pools["press"]].mean() - v[pools["release"]].mean()), 3)
                                                for k, v in r.items()})
    with open(out, "x") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
