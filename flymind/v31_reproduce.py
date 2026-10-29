"""V3.1 — odtworzenie liczb z VALIDATION_PLAN (analiza punktowa + permutacje/bootstrap/kierunek). Przeniesione ze
scratchpadu sesji 1 (epg_point.py + epg_null.py), ścieżki względne. Uruchom: .venv/bin/python -I -B flymind/v31_reproduce.py"""
import json, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from epg_ring import (analyze, best_cycle, bootstrap_stability, circulation, circulation_null, glom_matrix,  # noqa: E402
                      label_permutation_null, load, neuron_matrix, symmetric, top2_ring)
D = os.path.join(os.path.dirname(HERE), "data", "malecns") + os.sep
labels, edges, prov = load(D + "body-annotations-male-cns-v1.0-minconf-0.5.feather",
                           D + "connectome-weights-male-cns-v1.0-minconf-0.5.feather")
print("PROV labels:", json.dumps(prov["labels"], ensure_ascii=False))
print("PROV edges:", prov["edges"]["loaded"], "| ann mtime/bytes:", prov["annotations"]["bytes"], "| minconf:", prov["weights"].get("minconf"))
N = neuron_matrix(edges, labels)
print("EPG→EPG: krawędzi", int((N > 0).sum()), "synaps", int(N.sum()), "autapsy", int(np.trace(N)))
for norm in ("pairs", "sum"):
    r = analyze(labels, edges, norm)
    print(f"\n=== normalize={norm}")
    print("cykl (kanoniczny):", "–".join(r["cycle_canonical"]))
    print(f"score {r['cycle_score']:.2f}; frakcja wagi S na cyklu {r['cycle_frac']:.3f}; przekątna {r['diagonal_total']:.1f}; poza {r['offdiag_total']:.1f}")
    lm = r["local"]; print(f"margines lokalny {lm['margin']:.2f} ({100*lm['margin']/lm['score']:.1f}% score); alternatywa {[r['glomeruli'][i] for i in lm['alternative']]}")
    print("top2:", r["top2"], "| circulation:", round(r["circulation"], 4))
    print("wrażliwość C:\n", r["sensitivity"].round(4).to_string())
S_ = symmetric(glom_matrix(N, labels, "pairs")[0]); t = time.perf_counter(); best_cycle(S_); print(f"\nHeld–Karp n=16: {time.perf_counter()-t:.2f} s")
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
