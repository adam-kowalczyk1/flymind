# Analiza punktowa epg_ring na danych MaleCNS (bez losowania) + czas jednego Held–Karp
import sys, time, json
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np, pandas as pd
from epg_ring import load, analyze, neuron_matrix, glom_matrix, symmetric, best_cycle
D = "/Users/admin/so101_fly_project/data/malecns/"
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
