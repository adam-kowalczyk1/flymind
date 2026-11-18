"""flymind/audit_v5v4_independent.py — NIEZALEŻNA reanaliza V5 v4 (inna implementacja niż v5v4.analyze: pandas, CI t i bootstrap z innym
ziarnem RNG (9501), własny Holm i własne kategorie wg protokołu §1/§6). Nie zmienia wyników.
Uruchom: .venv/bin/python -I -B flymind/audit_v5v4_independent.py raw_A.jsonl raw_B.jsonl"""
import json, sys
import numpy as np, pandas as pd
from scipy import stats
rows = []
for f in sys.argv[1:]:
    for line in open(f):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        for c, v in r["conds"].items():
            rows.append(dict(seed=r["seed"], stratum=r["stratum"], rho=r["rho"], az=abs(r["az0_deg"]), cond=c, err=v["final_abs_err"],
                             succ=v["success"], error=v.get("error")))
df = pd.DataFrame(rows)
print("ziarna:", df.seed.nunique(), "| warunki:", sorted(df.cond.unique()), "| błędy prób:", int(df.error.notna().sum()))
bad = set(df[df.error.notna()].seed)
W = df[~df.seed.isin(bad)].pivot(index="seed", columns="cond", values="err")
meta = df.drop_duplicates("seed").set_index("seed").loc[W.index]
rng = np.random.default_rng(9501)
def ci(d):
    se = d.std(ddof=1) / np.sqrt(len(d)); h = stats.t.ppf(0.975, len(d) - 1) * se
    bs = d[rng.integers(len(d), size=(20000, len(d)))].mean(1)
    return (d.mean() - h, d.mean() + h), tuple(np.percentile(bs, [2.5, 97.5]))
def perm(d):
    s = np.abs((rng.choice([-1.0, 1.0], size=(200000, len(d))) * d).mean(1))
    return (1 + (s >= abs(d.mean()) - 1e-12).sum()) / 200001
res = {}
for st in ("S1", "S2"):
    d = (W["DATA"] - W["SWS"])[meta.stratum == st].to_numpy()
    tci, bci = ci(d); res[st] = dict(n=len(d), mean=d.mean(), tci=tci, bci=bci, p=perm(d))
ps = sorted(res, key=lambda k: res[k]["p"]); res[ps[0]]["ph"] = min(1, 2 * res[ps[0]]["p"]); res[ps[1]]["ph"] = max(res[ps[0]]["ph"], res[ps[1]]["p"])
for st, o in res.items():
    eq = all(-0.5 < a and b < 0.5 for a, b in (o["tci"], o["bci"]))
    lo, hi = o["bci"]
    size = "≥ SESOI" if abs(o["mean"]) >= 0.5 else ("< SESOI (pomijalny)" if eq else "wielkość nieustalona")
    cat = (f"DATA lepsza, {size}" if o["ph"] < 0.05 and hi < 0 else f"kontrola lepsza, {size}" if o["ph"] < 0.05 and lo > 0
           else "równoważne ±0,5°" if eq else "nie wykazano ani różnicy, ani równoważności")
    print(f"H1 {st}: n {o['n']} śr {o['mean']:+.3f}° CI95 t [{o['tci'][0]:+.3f}; {o['tci'][1]:+.3f}] boot [{o['bci'][0]:+.3f}; {o['bci'][1]:+.3f}] p {o['p']:.4g} p_Holm {o['ph']:.4g} → {cat}")
h2 = {k: (W[a] - W[b]).to_numpy() for k, (a, b) in dict(H2a=("DATA", "STR_OWN"), H2b=("STR_SHARED", "STR_OWN")).items()}
p2 = {k: perm(v) for k, v in h2.items()}; o = sorted(p2, key=p2.get); ph = {o[0]: min(1, 2 * p2[o[0]])}; ph[o[1]] = max(ph[o[0]], p2[o[1]])
for k, v in h2.items():
    tci, bci = ci(v); print(f"{k}: śr {v.mean():+.3f}° CI95 t [{tci[0]:+.3f}; {tci[1]:+.3f}] boot [{bci[0]:+.3f}; {bci[1]:+.3f}] p {p2[k]:.4g} p_Holm {ph[k]:.4g}")
for k, (a, b) in dict(D_TOY=("DATA", "TOY"), D_P=("DATA", "P")).items():
    v = (W[a] - W[b]).to_numpy(); tci, _ = ci(v); print(f"{k}: śr {v.mean():+.3f}° CI95 t [{tci[0]:+.3f}; {tci[1]:+.3f}]")
