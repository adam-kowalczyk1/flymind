"""flymind/audit_v5v3_independent.py — NIEZALEŻNA reanaliza wyniku V5 v3 (inna implementacja niż v5v3.analyze: pandas,
inne ziarna RNG, więcej permutacji, CI t obok bootstrapu, własny Holm, własna reguła decyzji z protokołu r3 §5).
Nie zmienia wyników. Uruchom: .venv/bin/python -I -B flymind/audit_v5v3_independent.py [plik.json]"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
path = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(os.path.join(HERE, "results", "v5v3", "v5v3_*.json")))[-1]
res = json.load(open(path))
df = pd.DataFrame(res["runs"])
print("plik:", os.path.basename(path), "| próby:", len(df), "| warunki:", df.cond.nunique(), "| ziarna:", df.seed.min(), "–", df.seed.max())
assert not df.duplicated(["cond", "seed"]).any()
scenes = df.groupby("seed")[["az0_deg", "rho"]].nunique()
print("sceny identyczne w parach:", bool((scenes == 1).all().all()))
bad = sorted(df[df.error.notna()].seed.unique())
print("ziarna z błędem symulatora:", bad, "| błędy per warunek:", df[df.error.notna()].groupby("cond").size().to_dict())
E = df[~df.seed.isin(bad)].pivot(index="seed", columns="cond", values="final_abs_err")
rho = df[df.cond == "DATA"].set_index("seed").rho.reindex(E.index)
pairs = dict(H1=("DATA", "SHUF_WITHIN_SIDE"), H2=("DATA", "SHUF_STR"), H3=("SHUF_WITHIN_SIDE", "SHUF_STR"),
             D1=("DATA", "TOY_RELAY"), D2=("DATA", "P_CTRL"))
rng = np.random.default_rng(7001)
out = {}
for h, (a, b) in pairs.items():
    d = (E[a] - E[b]).to_numpy()
    flips = rng.choice([-1.0, 1.0], size=(200_000, len(d)))
    p = (1 + (np.abs((flips * d).mean(1)) >= abs(d.mean()) - 1e-12).sum()) / 200_001
    bs = d[np.random.default_rng(7002).integers(len(d), size=(20_000, len(d)))].mean(1)
    se = d.std(ddof=1) / np.sqrt(len(d))
    out[h] = dict(mean=d.mean(), ci95_boot=np.percentile(bs, [2.5, 97.5]), ci90_boot=np.percentile(bs, [5, 95]),
                  ci95_t=d.mean() + np.array([-1, 1]) * stats.t.ppf(0.975, len(d) - 1) * se, p=p,
                  dz=d.mean() / d.std(ddof=1), zeros=int((d == 0).sum()), sign=(int((d < 0).sum()), int((d > 0).sum())),
                  strata={f"{lo}-{hi}": round(float(d[(rho >= lo) & (rho < hi)].mean()), 3) for lo, hi in ((0.16, 0.24), (0.24, 0.30), (0.30, 0.36))})
ph = sorted([("H2", out["H2"]["p"]), ("H3", out["H3"]["p"])], key=lambda x: x[1])
adj = {ph[0][0]: min(1, 2 * ph[0][1])}
adj[ph[1][0]] = max(adj[ph[0][0]], min(1, ph[1][1]))
adj["H1"] = out["H1"]["p"]


def rule(o, p):
    if p < 0.05 and o["ci95_boot"][1] < 0:
        return "pierwszy lepszy " + ("≥ SESOI" if o["mean"] <= -1.0 else "< SESOI")
    if p < 0.05 and o["ci95_boot"][0] > 0:
        return "drugi lepszy"
    if -1.0 < o["ci90_boot"][0] and o["ci90_boot"][1] < 1.0:
        return "równoważne w granicach SESOI"
    return "nierozstrzygnięte"


for h, o in out.items():
    dec = rule(o, adj[h]) if h in adj else "opis"
    print(f"{h} ({pairs[h][0]} − {pairs[h][1]}): śr {o['mean']:+.3f}° CI95 boot [{o['ci95_boot'][0]:+.3f}; {o['ci95_boot'][1]:+.3f}] "
          f"CI95 t [{o['ci95_t'][0]:+.3f}; {o['ci95_t'][1]:+.3f}] CI90 [{o['ci90_boot'][0]:+.3f}; {o['ci90_boot'][1]:+.3f}] "
          f"p {o['p']:.4g} p_dec {adj.get(h, float('nan')):.4g} d_z {o['dz']:+.3f} zera {o['zeros']} (−/+) {o['sign']} "
          f"warstwy {o['strata']} → {dec}")
rep = res["analysis"]["tests"]
print("zgodność z v5v3.analyze (średnie):", all(abs(rep[h]["mean_d"] - out[h]["mean"]) < 1e-9 for h in out),
      "| decyzje raportu:", {h: rep[h]["decision"] for h in rep})
