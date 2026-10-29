"""Supplementary analyses requested by the red team: BCa CIs, Holm-adjusted p-values (descriptive), onset-adjusted
contrasts (ANCOVA-style D ~ onset-difference), and the POST HOC ball-motion-free endpoint |dAim - e_onset|."""
import glob, json, numpy as np, scipy.stats as st
P = {}
for f in sorted(glob.glob("raw/pilot_*.jsonl")):
    for l in open(f):
        r = json.loads(l); P[(r["variant"], r["seed"])] = r
S = range(100, 130)
g = lambda v, k: np.array([P[(v, s)][k] for s in S], float)
ae = lambda v: np.abs(g(v, "e_reappear_deg"))
fams = {"NI": [("BIO-Static", "LastObs-PD"), ("BIO-Hybrid", "Kalman-PD")],
        "mechanism": [("BIO-Static", "BIO-NoSelf"), ("BIO-Hybrid", "BIO-Static")],
        "freeze": [("BIO-Static", "BIO-Static-Freeze-Diag"), ("LastObs-PD", "LastObs-Freeze-Diag")]}
def holm(p):
    o = np.argsort(p); adj = np.empty(len(p)); run = 0
    for i, j in enumerate(o):
        run = max(run, (len(p) - i) * p[j]); adj[j] = min(1, run)
    return adj
print("D = |e_A| - |e_B| (deg). BCa 95% CI (scipy.stats.bootstrap, 10000, seed 20261027); paired-t p (two-sided) Holm within family; descriptive only")
for fam, pairs in fams.items():
    ps, rows = [], []
    for A, B in pairs:
        d = ae(A) - ae(B)
        bca = st.bootstrap((d,), np.mean, n_resamples=10000, method="BCa", random_state=np.random.default_rng(20261027)).confidence_interval
        p = st.ttest_1samp(d, 0).pvalue; ps.append(p)
        on = g(A, "e_onset_deg") - g(B, "e_onset_deg")
        c = np.polyfit(on, d, 1) if np.std(on) > 1e-9 else (0.0, d.mean())
        rows.append((A, B, d.mean(), bca.low, bca.high, p, c[1], c[0]))
    for (A, B, m, lo, hi, p, ic, sl), pa in zip(rows, holm(np.array(ps))):
        print(f"[{fam}] {A} - {B}: mean {m:+.2f} BCa [{lo:+.2f}, {hi:+.2f}] p={p:.2g} Holm={pa:.2g} | onset-adjusted D at equal e_onset {ic:+.2f} (slope {sl:+.2f})")
print("\nPOST HOC (not prespecified) ball-motion-free endpoint r = dAim - e_onset (0 = arm executed exactly the correction")
print("a perfect static memory would make); |r| mean, SD; paired vs LastObs-PD:")
r = {v: np.abs((g(v, "aim_reappear_deg") - g(v, "aim_onset_deg")) - g(v, "e_onset_deg")) for v in ("BIO-Static", "BIO-NoSelf", "LastObs-PD", "BIO-Static-Freeze-Diag", "LastObs-Freeze-Diag")}
for v, x in r.items():
    d = x - r["LastObs-PD"]
    print(f"  {v:24s} |r| {x.mean():5.2f} (SD {x.std(ddof=1):4.2f})  vs LastObs: {d.mean():+5.2f} [{d.mean()-2.045*d.std(ddof=1)/np.sqrt(30):+.2f}, {d.mean()+2.045*d.std(ddof=1)/np.sqrt(30):+.2f}]")
d = r["BIO-Static"] - r["BIO-NoSelf"]
print(f"  BIO-Static - BIO-NoSelf on |r|: {d.mean():+.2f} [{d.mean()-2.045*d.std(ddof=1)/np.sqrt(30):+.2f}, {d.mean()+2.045*d.std(ddof=1)/np.sqrt(30):+.2f}]")
enc = np.abs(g("BIO-Static", "bump_onset_deg") - g("BIO-Static", "e_onset_deg"))
print(f"\nBIO-Static encoding error at onset |bump_onset - e_onset|: mean {enc.mean():.2f} SD {enc.std(ddof=1):.2f} deg (part of the 14 deg 'memory fidelity' figure)")
