"""T2 — warstwa komórek zbliżania MaleCNS (LPLC2 lub LC4 + LPi + rekurencja) na napędzie z t2_drive; uczone tylko
właściwości typów (stała czasowa, spoczynek) i siły par typów — połączenia i znaki z MaleCNS bez zmian (PREREG_T2.md).
envs/flyvis: t2_model.py DRIVE.npz TARGET(LPLC2|LC4) VARIANT(full|nolpi|untrained) OUT.json"""
import json
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t1_transplant as T1  # noqa: E402

DT, STEPS, LR, RESTARTS = 0.01, 600, 0.03, (24104201, 24104202, 24104203)
torch.set_num_threads(4)


def auc(pos, neg):
    pos, neg = np.asarray(pos), np.asarray(neg)
    return float(((pos[:, None] > neg[None]).mean() + 0.5 * (pos[:, None] == neg[None]).mean()))


class Layer(torch.nn.Module):
    def __init__(self, n_types, n_lpi_types, lpi_types_of_cells, n_lpi_in, rec, lpi_edges, n_cells, n_lpi, variant):
        super().__init__()
        z = lambda *s: torch.nn.Parameter(torch.zeros(*s))  # noqa: E731
        self.g, self.tau, self.b = z(n_types), z(1), z(1)                     # cel: siły typów wejść, τ, spoczynek
        self.g_lpi, self.g_rec = z(n_lpi_types), z(1)
        self.lg, self.ltau, self.lb = z(n_lpi_in), z(n_lpi_types), z(n_lpi_types)   # LPi: siły typów wejść (wspólne), τ i spoczynek na typ LPi
        self.a, self.c = torch.nn.Parameter(torch.tensor(1.0)), torch.nn.Parameter(torch.tensor(0.0))   # próg odczytu
        self.lt = torch.tensor(lpi_types_of_cells)
        self.R = torch.sparse_coo_tensor(torch.stack(rec[:2]), rec[2], (n_cells, n_cells)).coalesce()
        self.P = [torch.sparse_coo_tensor(torch.stack(e[:2]), e[2], (n_cells, n_lpi)).coalesce() for e in lpi_edges]
        self.variant = variant

    def forward(self, D, DL):
        """D: (S, cells, typy, T), DL: (S, lpi, typy_lpi, T) → wyjście komórek relu(V): (S, cells, T)."""
        sp_ = torch.nn.functional.softplus
        g, lg = sp_(self.g + 0.5413), sp_(self.lg + 0.5413)                     # start: 1,0
        tau, ltau = 0.02 * torch.exp(self.tau), 0.02 * torch.exp(self.ltau[self.lt])
        S, C, _, T = D.shape
        I = torch.einsum("sctk,t->sck", D, g)                                # D: (bodziec, komórka, typ, czas)
        IL = torch.einsum("sltk,t->slk", DL, lg)
        V, VL, out = torch.zeros(S, C), torch.zeros(S, DL.shape[1]), []
        for k in range(T):
            r, rl = torch.relu(V), torch.relu(VL)
            inp = I[:, :, k]
            if self.variant != "nolpi":
                inp = inp + sum(sp_(self.g_lpi[j] + 0.5413) * torch.sparse.mm(self.P[j], rl.T).T for j in range(len(self.P)))
            inp = inp + sp_(self.g_rec + 0.5413) * torch.sparse.mm(self.R, r.T).T
            V = V + DT / tau * (-V + self.b + inp)
            VL = VL + DT / ltau * (-VL + self.lb[self.lt] + IL[:, :, k])
            out.append(torch.relu(V))
        return torch.stack(out, -1)

    def score(self, D, DL):
        y = self.forward(D, DL)
        return torch.logsumexp(10 * y.flatten(1), 1) / 10                       # ≈ max po komórkach i czasie


def main(drive, target, variant, out):
    Z = np.load(drive)
    M = dict(np.load(os.path.join(T1.RES, "t2_map.npz")))
    D, DL = torch.tensor(Z[f"D_{target}"].astype(np.float32)), torch.tensor(Z["D_LPi"].astype(np.float32))
    lab, split, names = Z["label"], Z["split"], Z["names"]
    tot = M[f"{target}_total_in"]
    lt_names = sorted(set(M["lpi_type"]))
    lt = np.array([lt_names.index(x) for x in M["lpi_type"]])
    L = M[f"{target}_lpi"]
    lpi_edges = []
    for j in range(len(lt_names)):
        m = lt[L[:, 1].astype(int)] == j
        lpi_edges.append((np.c_[L[m, 0], L[m, 1]].T.astype(int), L[m, 3] * L[m, 2] / tot[L[m, 0].astype(int)]))
    lpi_edges = [(torch.tensor(i), torch.tensor(w, dtype=torch.float32)) for i, w in lpi_edges]
    Rr = M[f"{target}_rec"]
    rec = (torch.tensor(Rr[:, :2].T.astype(int)), torch.tensor(Rr[:, 3] * Rr[:, 2] / tot[Rr[:, 0].astype(int)], dtype=torch.float32))
    tr, te = split == "train", split == "test"
    best = None
    for seed in RESTARTS:
        torch.manual_seed(seed)
        net = Layer(D.shape[2], len(lt_names), lt, DL.shape[2], (rec[0][0], rec[0][1], rec[1]),
                    [(e[0][0], e[0][1], e[1]) for e in lpi_edges], D.shape[1], DL.shape[1], variant)
        with torch.no_grad():
            for p in (net.g, net.lg, net.g_lpi):
                p.add_(0.3 * torch.randn_like(p))
        params = [net.a, net.c] if variant == "untrained" else list(net.parameters())
        opt = torch.optim.Adam(params, lr=LR)
        yl, w = torch.tensor(lab[tr], dtype=torch.float32), torch.tensor(np.where(lab[tr] == 1, (lab[tr] == 0).sum() / max(1, lab[tr].sum()), 1.0), dtype=torch.float32)
        for step in range(STEPS if variant != "untrained" else 300):
            y = net.score(D[tr], DL[tr])
            loss = torch.nn.functional.binary_cross_entropy_with_logits(net.a * (y - net.c), yl, weight=w)
            opt.zero_grad(); loss.backward(); opt.step()
        if best is None or loss.item() < best[0]:
            best = (loss.item(), seed, {k: v.detach().clone() for k, v in net.state_dict().items()}, net)
    loss, seed, _, net = best
    with torch.no_grad():
        y = net.score(D, DL).numpy()
    te_pos, te_neg = y[te & (lab == 1)], y[te & (lab == 0)]
    pure = np.array(["Tloom_" in n for n in names]) & te
    selfloom = np.array(["Tloomself" in n for n in names])
    res = dict(target=target, variant=variant, drive=os.path.basename(drive), train_loss=loss, seed=seed,
               auc_train=auc(y[tr & (lab == 1)], y[tr & (lab == 0)]), auc_test=auc(te_pos, te_neg),
               loomself_over_pureloom=float(y[selfloom].mean() / max(y[pure].mean(), 1e-9)),
               worst_test_neg=str(names[te & (lab == 0)][np.argmax(te_neg)]), min_test_pos=str(names[te & (lab == 1)][np.argmin(te_pos)]),
               y={str(n): float(v) for n, v in zip(names, y)},
               g={str(t): float(torch.nn.functional.softplus(net.g[i] + 0.5413)) for i, t in enumerate(Z[f"{target}_types"])},
               tau_ms=float(20 * torch.exp(net.tau)), bias=float(net.b), g_rec=float(torch.nn.functional.softplus(net.g_rec + 0.5413)))
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("y", "g")}), flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:5])
