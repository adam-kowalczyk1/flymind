"""T2 — oko (flyvis, liczby wg T1) na bodźcach t2_stim → napęd synaptyczny MaleCNS do LPLC2, LC4, LPi (PREREG_T2.md).
envs/flyvis: t2_drive.py COUNTS(malecns|orig) WIRING(real|shuffle) MODEL OUT.npz
Napęd[komórka, typ pre, t] = Σ_j znak_j · n_ij · relu(V_typ(kolumna_j)(t)) / całe wejście komórki (MaleCNS). shuffle = kontrola:
kolumny wejść losowo przetasowane między krawędziami tego samego typu pre (skład typów i liczby synaps zostają; ziarno 24 104 300 + model)."""
import os
import sys

import numpy as np
import scipy.sparse as sp
import torch
from flyvis import NetworkView

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t1_transplant as T1  # noqa: E402
import t2_stim  # noqa: E402
from bridge_loom import DT, flyxy  # noqa: E402

torch.set_num_threads(4)


def drives(edges, types, n_post, act, node, total, rng=None):
    ut = sorted(set(types))
    D = np.zeros((n_post, len(ut), act.shape[0]), np.float32)
    miss = 0.0
    E = edges.copy()
    if rng is not None:
        for t in ut:
            ix = np.where(types == t)[0]
            E[ix, 1:3] = E[rng.permutation(ix), 1:3]
    for k, t in enumerate(ut):
        ix = np.where(types == t)[0]
        cols = np.array([node.get((t, int(u), int(v)), -1) for u, v in E[ix, 1:3]])
        ok = cols >= 0
        miss += E[ix[~ok], 3].sum()
        S = sp.csr_matrix((E[ix[ok], 4] * E[ix[ok], 3] / total[E[ix[ok], 0].astype(int)], (E[ix[ok], 0].astype(int), cols[ok])),
                          shape=(n_post, act.shape[1]))
        D[:, k, :] = (S @ act.T).astype(np.float32)
    return D, ut, miss / edges[:, 3].sum()


def main(counts, wiring, model, out):
    model = int(model)
    M = dict(np.load(os.path.join(T1.RES, "t2_map.npz")))
    net = NetworkView(f"flow/0000/{model:03d}").init_network()
    n, _ = T1.counts(counts, model)
    with torch.no_grad():
        net.edges_syn_count.data = torch.tensor(np.log(np.maximum(n, 1e-6)), dtype=net.edges_syn_count.dtype)
    nd = net.connectome.nodes
    t = np.array([x.decode() if isinstance(x, bytes) else x for x in nd.type[:]]); u = np.array(nd.u[:]); v = np.array(nd.v[:])
    node = {(a, int(b), int(c)): i for i, (a, b, c) in enumerate(zip(t, u, v))}
    r1 = t == "R1"
    S = t2_stim.stimuli(flyxy(u[r1], v[r1]))
    rng = (lambda: np.random.default_rng(24104300 + model)) if wiring == "shuffle" else (lambda: None)
    tot = {k: M[f"{k}_total_in"] for k in ("LPLC2", "LC4")}
    lpi_tot = np.bincount(M["lpi_in"][:, 0].astype(int), weights=M["lpi_in"][:, 3], minlength=len(M["lpi_cells"]))
    res = dict(names=np.array(list(S)), label=np.array([S[k][1] for k in S]), split=np.array([S[k][2] for k in S]))
    acc = {k: [] for k in ("LPLC2", "LC4", "LPi")}
    for name, (mv, _, _) in S.items():
        with torch.no_grad():
            V = net.simulate(torch.tensor(mv)[None, :, None, :], DT).numpy()[0]
        act = np.maximum(V, 0)
        for k in ("LPLC2", "LC4"):
            D, ut, miss = drives(M[f"{k}_in"], M[f"{k}_in_type"], len(M[f"{k}_cells"]), act, node, tot[k], rng())
            acc[k].append(D); res[f"{k}_types"], res[f"{k}_miss"] = np.array(ut), miss
        D, ut, miss = drives(M["lpi_in"], M["lpi_in_type"], len(M["lpi_cells"]), act, node, np.maximum(lpi_tot, 1), rng())
        acc["LPi"].append(D); res["LPi_types"], res["LPi_miss"] = np.array(ut), miss
        print(name, flush=True)
    for k, L in acc.items():
        T = max(x.shape[-1] for x in L)
        res[f"D_{k}"] = np.stack([np.pad(x, ((0, 0), (0, 0), (0, T - x.shape[-1])), mode="edge") for x in L]).astype(np.float16)
    np.savez_compressed(out, **res)


if __name__ == "__main__":
    main(*sys.argv[1:5])
