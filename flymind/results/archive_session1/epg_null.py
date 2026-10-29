# Kontrola permutacyjna, bootstrap i kierunek dla agregacji "pairs" (ziarna 1001–1003)
import sys, time
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np
from epg_ring import (load, neuron_matrix, glom_matrix, symmetric, best_cycle, top2_ring, circulation,
                      circulation_null, label_permutation_null, bootstrap_stability)
D = "/Users/admin/so101_fly_project/data/malecns/"
labels, edges, _ = load(D + "body-annotations-male-cns-v1.0-minconf-0.5.feather", D + "connectome-weights-male-cns-v1.0-minconf-0.5.feather")
N = neuron_matrix(edges, labels)
A, G = glom_matrix(N, labels, "pairs"); S = symmetric(A)
cyc, score = best_cycle(S); frac = score / (S.sum() / 2); nm = top2_ring(S)[0]; circ = circulation(A, cyc)
pv = lambda null, obs, two=False: (1 + int(((np.abs(null) >= abs(obs)) if two else (null >= obs)).sum())) / (1 + len(null))
t = time.perf_counter()
P = label_permutation_null(N, labels, 10000, 1001, exact_every=50)
print(f"permutacja etykiet (n=10000, ziarno 1001, {time.perf_counter()-t:.0f} s):")
print(f"  n_mutual: obs {nm}; null mediana {P.n_mutual.median():.0f}, max {P.n_mutual.max()}, p = {pv(P.n_mutual.to_numpy(), nm):.5f}")
cf = P.cycle_frac.dropna().to_numpy()
print(f"  frakcja wagi na cyklu (dokładny cykl, n={len(cf)}): obs {frac:.3f}; null mediana {np.median(cf):.3f}, max {cf.max():.3f}, p = {pv(cf, frac):.4f}")
t = time.perf_counter()
st, forms = bootstrap_stability(N, labels, 500, 1002)
print(f"bootstrap neuronów w glomerulusach (n=500, ziarno 1002, {time.perf_counter()-t:.0f} s): identyczny cykl w {100*st:.1f}% prób; różnych postaci: {len(forms)}")
for f, k in list(forms.items())[:4]:
    print(f"  {k:4d} × {'–'.join(G[i] for i in f)}")
cn = circulation_null(A, cyc, 10000, 1003)
print(f"kierunek: circulation obs {circ:+.4f}; null (losowe odwrócenie par, n=10000, ziarno 1003) 95% [{np.percentile(cn,2.5):+.4f}, {np.percentile(cn,97.5):+.4f}], p dwustronne = {pv(cn, circ, True):.4f}")
