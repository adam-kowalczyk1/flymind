"""flymind/audit_v5v2_independent.py — NIEZALEŻNA reanaliza V5 v2 (topologia), inną implementacją niż v5v2_topology.analyze.
Sprawdza: zgodność manifestu i kopii zamrożonej, parowanie scen, średnie/CI (bootstrap innym ziarnem + CI t), wrażliwość p
na obsługę zer (exact bez zer / approx / Pratt / test znaków) z korektą Holma, oraz indeks lateralizacji jawnym wyliczeniem
ścieżek. Nic nie symuluje w pętli; nie zmienia wyników archiwalnych. Uruchom: .venv/bin/python -I -B flymind/audit_v5v2_independent.py"""
import json, glob, hashlib, math, os
import numpy as np
from scipy import stats
R = os.path.dirname(os.path.abspath(__file__)) + "/"
m = json.load(open(R + "validation/v5v2_topology_manifest.json"))
bad = [f for f, h in m["code_sha256"].items() if hashlib.sha256(open(R + f, "rb").read()).hexdigest() != h]
print("manifest V5 v2 vs bieżący kod — niezgodne:", bad or "brak")
frozen = [f for f in m["code_sha256"] if f.endswith(".py") and hashlib.sha256(open(R + "validation/v5v2_topology_frozen_code/" + f, "rb").read()).hexdigest() != m["code_sha256"][f]]
print("kopia zamrożona vs manifest — niezgodne:", frozen or "brak")
res = json.load(open(sorted(glob.glob(R + "results/v5v2_topology/v5v2_topology_*.json"))[-1]))
rep = json.load(open(R + "results/v5v2_topology/analysis.json"))
runs = res["runs"]
conds = sorted({r["cond"] for r in runs}); seeds = sorted({r["seed"] for r in runs})
print("warunki", len(conds), "ziarna", seeds[0], "–", seeds[-1], "n", len(seeds), "próby", len(runs))
# parowanie: identyczne sceny
scene = {}
mism = 0
for r in runs:
    k = (round(r["az0_deg"], 9), round(r["rho"], 9))
    if r["seed"] in scene and scene[r["seed"]] != k: mism += 1
    scene.setdefault(r["seed"], k)
print("niezgodne sceny w parach:", mism, "| duplikaty (cond, seed):", len(runs) - len({(r['cond'], r['seed']) for r in runs}))
E = {(r["cond"], r["seed"]): r["final_abs_err"] for r in runs}
base = np.array([E[("DATA", s)] for s in seeds])
rows, ps = [], []
for c in [x for x in ["SHUF_DEG","SHUF_STR","CUT_LC10a_AOTU","ABL_AOTU019","TOY_RELAY","P_CTRL","NO_VISION","SWAP"]]:
    d = np.array([E[(c, s)] for s in seeds]) - base
    p = stats.wilcoxon(d, zero_method="wilcox").pvalue
    # bootstrap percentile z innym ziarnem i t-CI
    bm = np.random.default_rng(777).choice(d, size=(20000, len(d))).mean(1)
    t = stats.t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / math.sqrt(len(d))
    rows.append((c, d.mean(), np.percentile(bm, [2.5, 97.5]), (d.mean() - t, d.mean() + t), p)); ps.append(p)
# Holm niezależnie
order = np.argsort(ps); k = len(ps); holm = [None] * k; prev = 0
for i, j in enumerate(order):
    prev = max(prev, min(1, (k - i) * ps[j])); holm[j] = prev
for (c, mean, bci, tci, p), h in zip(rows, holm):
    r = rep["comparisons"][c]
    print(f"{c:15s} mean {mean:+.3f} (rap {r['mean_diff_deg']:+.3f}) boot {bci.round(2)} (rap {r['ci95']}) tCI {np.round(tci,2)} p {p:.3g} (rap {r['wilcoxon_p']:.3g}) holm {h:.3g} (rap {r['wilcoxon_p_holm']:.3g})")
# --- wrażliwość na obsługę zer (Holm na 8 porównaniach) ---
C = ["SHUF_DEG","SHUF_STR","CUT_LC10a_AOTU","ABL_AOTU019","TOY_RELAY","P_CTRL","NO_VISION","SWAP"]
D = {c: np.array([E[(c, s)] - E[("DATA", s)] for s in seeds]) for c in C}
def holm2(p):
    o = np.argsort(p); h = np.empty(len(p)); m = 0
    for i, j in enumerate(o): m = max(m, min(1, (len(p) - i) * p[j])); h[j] = m
    return h
for name, f in (("bez zer, exact", lambda d: stats.wilcoxon(d[d != 0]).pvalue), ("bez zer, approx", lambda d: stats.wilcoxon(d[d != 0], method="approx").pvalue),
                ("Pratt", lambda d: stats.wilcoxon(d, zero_method="pratt").pvalue), ("test znaków", lambda d: stats.binomtest(int((d > 0).sum()), int((d != 0).sum())).pvalue)):
    print(f"Holm [{name:15s}]", " ".join(f"{c}:{x:.3g}" for c, x in zip(C, holm2(np.array([f(D[c]) for c in C])))))
print("pary z d = 0 (SHUF_STR):", int((D["SHUF_STR"] == 0).sum()), "/", len(seeds))
# --- indeks lateralizacji: jawne wyliczenie ścieżek vs zapisane wartości ---
import sys; sys.path.insert(0, R)
import v5v2_topology as T
from visual_path import network, shuffle
spec, idx, _ = network(0.2); W = spec.W_data
def li_paths(W):
    tot = 0.0
    for s, o in (("L", "R"), ("R", "L")):
        for lc in idx[f"in_{s}"]:
            outs = np.flatnonzero(W[:, lc])
            for dn, sg in ((idx[f"DNa02_{s}"][0], 1), (idx[f"DNa02_{o}"][0], -1)):
                tot += sg * (W[dn, lc] + sum(W[dn, m] * W[m, lc] for m in outs))
    return tot
a = li_paths(W)
print("LI DATA jawne == macierzowe:", np.isclose(a, T.lateralization(W, idx)))
Lr = {(r["cond"], r["seed"]): r["lateralization_rel"] for r in runs}
for c, off, st in (("SHUF_STR", 200_000, True), ("SHUF_DEG", 100_000, False)):
    for s in (seeds[0], seeds[len(seeds) // 2]):
        print(c, s, "LI zapisane", round(Lr[(c, s)], 4), "jawne", round(li_paths(shuffle(spec, s + off, equal_weight=st).W_data) / a, 4))
