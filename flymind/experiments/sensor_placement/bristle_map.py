"""Mapa koniec nogi / nasada dla szczecinek T2 L z szkieletów SWC (reguła Elabbady 2026; cel TARGET_bristle_map_r1.md)."""
import json, os, sys
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
SKEL = os.path.join(ROOT, "data/malecns/skeletons_T2L_bristle")
OUT = os.path.join(os.path.dirname(__file__), "results")

def leaves(path):
    a = np.loadtxt(path, comments="#")
    par = a[:, 6].astype(int)
    leaf = ~np.isin(a[:, 0].astype(int), par) & (par != -1)
    return a[leaf, 2:5]

def eta2(r, g):
    m = r.mean(); ssb = sum(len(r[g == k]) * (r[g == k].mean() - m) ** 2 for k in np.unique(g))
    return ssb / ((r - m) ** 2).sum()

def main():
    mp = json.load(open(os.path.join(ROOT, "flymind/experiments/step3_wiring/touch_map.json")))
    ann = pd.read_feather(os.path.join(ROOT, "data/malecns/body-annotations-male-cns-v1.0-minconf-0.5.feather"), columns=["bodyId", "type"])
    typ = dict(zip(ann.bodyId, ann.type))
    rows = []
    for grp in ("femur", "tibia_tarsus"):
        for b in mp[grp]:
            p = os.path.join(SKEL, f"{b}.swc")
            if not os.path.exists(p):
                continue
            L = leaves(p)
            if len(L) < 3:
                continue
            rows.append(dict(bodyId=b, grp=grp, type=typ.get(b), n_leaf=len(L), c_mean=L.mean(0), c_med=np.median(L, 0)))
    df = pd.DataFrame(rows)
    out = dict(n=len(df))
    for key in ("c_mean", "c_med"):                                 # c_mean = cel; c_med = sprawdzian odporności
        C = np.median(np.stack(df[key]), 0)
        r = np.linalg.norm(np.stack(df[key]) - C, axis=1)
        df["r_" + key] = r
        big = df.type.map(df.type.value_counts()) >= 3
        rr, gg = r[big.values], df.type[big].values
        e = eta2(rr, gg)
        rng = np.random.default_rng(2011203)
        perm = np.array([eta2(rr, rng.permutation(gg)) for _ in range(1000)])
        mw = mannwhitneyu(r[df.grp == "femur"], r[df.grp == "tibia_tarsus"])
        out[key] = dict(eta2=float(e), perm_p=float((perm >= e).mean()), perm_mean=float(perm.mean()),
                        n_types=int(len(np.unique(gg))), n_in_types=int(big.sum()),
                        r_femur_med=float(np.median(r[df.grp == "femur"])), r_tibia_med=float(np.median(r[df.grp == "tibia_tarsus"])),
                        mw_p=float(mw.pvalue))
    use = out["c_mean"]["eta2"] >= 0.5 and out["c_mean"]["perm_p"] < 0.01
    out["usable"] = bool(use)
    u = df.r_c_mean.rank(pct=True).values - 0.5 / len(df)
    df["u"] = u
    out["by_type"] = (df.groupby("type").agg(n=("u", "size"), u_med=("u", "median"), r_med=("r_c_mean", "median"))
                      .sort_values("u_med").round(3).reset_index().to_dict("records"))
    if use:
        out["tip"] = df.bodyId[np.abs(u - 0.12) <= 0.15].astype(int).tolist()
        out["A0"] = df.bodyId[np.abs(u - 0.46) <= 0.15].astype(int).tolist()
    json.dump(out, open(os.path.join(OUT, "bristle_map_r1.json"), "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k not in ("by_type", "tip", "A0")}, indent=1))
    print("UŻYTECZNA" if use else "NIEUŻYTECZNA (zostaje hipoteza)", "| tip", len(out.get("tip", [])), "A0", len(out.get("A0", [])))
    for t in out["by_type"]:
        print(t)

if __name__ == "__main__":
    main()
