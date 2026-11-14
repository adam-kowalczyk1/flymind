"""flymind/v6_analysis.py — pre-specified analysis of V6 (program_v5v41/V6_PROTOCOL.md §5).
Open loop: per configuration Δ (control − DATA) with hierarchical bootstrap; closed loop: d = err(DATA) − err(ctrl) per stratum with
cluster bootstrap over control instances. D0 open-loop data = first 4 reps / 33-level subset of V5 v4.1 (identical seeds, schedules).
Run: .venv/bin/python -I -B flymind/v6_analysis.py --run flymind/results/v6 --v41 flymind/results/v5v41
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from v5v41_analysis import compare, range_avg, thresholds  # noqa: E402
from v5v41_e6_analysis import per_net as e6_net  # noqa: E402
from v6 import CL_CONFIGS, CONFIGS, LV, REPS  # noqa: E402

BOOT, CLB = 8_419_020, 8_419_021


def dn_ss(counts, n_pop):
    """E1 counts [Lv, 2, R, 100, 6] → side-averaged rep-level steady states [Lv, R] for DN ipsi, LC ipsi, mid ipsi."""
    c = counts.astype(float)[..., 50:100, :].mean(-2) * 100.0          # Hz per population sum (10 ms bins)
    dn = (c[:, 0, :, 4] + c[:, 1, :, 5]) / 2
    lc = (c[:, 0, :, 0] / n_pop[0] + c[:, 1, :, 0] / n_pop[1]) / 2
    mid = (c[:, 0, :, 2] / n_pop[2] + c[:, 1, :, 3] / n_pop[3]) / 2
    return dict(dn=dn, lc=lc, mid=mid)


def load_cfg(run, v41, cfg):
    out = {}
    if cfg == "D0":
        sel = np.isin(np.round(np.load(os.path.join(v41, "raw", "DATA.npz"))["E1_levels"], 4), LV)
        for p in glob.glob(os.path.join(v41, "raw", "*.npz")):
            n = os.path.basename(p)[:-4]
            z = np.load(p)
            e6 = np.load(os.path.join(v41, "E6", "raw", f"{n}.npz"))
            out[n] = dict(E1=z["E1_counts"][sel][:, :, :REPS], E6=e6["counts"][:, :, :REPS], deltas=e6["deltas"], n_pop=z["n_pop"])
    else:
        for p in glob.glob(os.path.join(run, "openloop", cfg, "*.npz")):
            z = np.load(p)
            out[os.path.basename(p)[:-4]] = dict(E1=z["E1_counts"], E6=z["E6_counts"], deltas=z["E6_deltas"], n_pop=z["n_pop"],
                                                 spont=int(z["spont_spikes_300ms"]))
    return out


def openloop(run, v41, rng):
    res = {}
    for cfg in CONFIGS:
        nets = load_cfg(run, v41, cfg)
        if "DATA" not in nets:
            continue
        S = {n: dn_ss(z["E1"], z["n_pop"]) for n, z in nets.items()}
        G = {n: e6_net(dict(counts=z["E6"], deltas=z["deltas"], n_pop=z["n_pop"]))["G_small"] for n, z in nets.items()}
        D = S["DATA"]
        th10 = thresholds(LV, D["dn"].mean(-1), 10)
        own = (th10, th10 + 3.0) if np.isfinite(th10) else (6.0, 9.0)
        own = (max(own[0], LV[0]), min(own[1], LV[-1]))
        r = dict(data_I_th10=th10, own_window=own, families={})
        for fam in sorted({n.split("_")[0] for n in nets if n != "DATA"}):
            names = sorted(n for n in nets if n.startswith(fam + "_"))
            e = {}
            for m in ("dn", "lc", "mid"):
                xK = np.stack([S[n][m] for n in names])
                for rn, (lo, hi) in {"6-9": (6, 9), "9-12": (9, 12), "own": own}.items():
                    e[f"{m}|{rn}"] = compare(range_avg(LV, D[m], lo, hi), np.stack([range_avg(LV, x, lo, hi) for x in xK]), rng)
            for t, th in (("I_th10", 10), ("I_th30", 30)):
                tD = thresholds(LV, D["dn"].mean(-1), th)
                tK = np.array([thresholds(LV, S[n]["dn"].mean(-1), th) for n in names])
                e[t] = dict(data=tD, ctrl_mean=float(np.nanmean(tK)), delta=float(np.nanmean(tK) - tD),
                            ctrl_q=[float(np.nanpercentile(tK, q)) for q in (2.5, 50, 97.5)], never=int(np.isnan(tK).sum()))
            I0 = np.array([4, 5, 6, 7, 8, 9, 10, 11.0])
            gK = np.stack([G[n] for n in names])
            e["G_small"] = {str(x): compare(G["DATA"][i], gK[:, i], rng) for i, x in enumerate(I0)}
            for i, x in enumerate(I0):
                g = e["G_small"][str(x)]
                if g.get("delta") is not None and g["data"]:
                    g["rel_delta"] = g["delta"] / g["data"]
            dn_own, gg = e["dn|own"], [e["G_small"][str(x)] for x in (6.0, 7.0, 8.0)]
            e["equivalent_Q6"] = bool(dn_own.get("delta") is not None and -5 < dn_own["ci95"][0] and dn_own["ci95"][1] < 5 and
                                      all(g.get("data") and abs(g["ci95"][0]) < 0.1 * abs(g["data"]) and abs(g["ci95"][1]) < 0.1 * abs(g["data"]) for g in gg))
            r["families"][fam] = e
        r["spont_spikes_300ms_max"] = max([z.get("spont", 0) for z in nets.values()])
        r["dn_curve_data"] = D["dn"].mean(-1).tolist()
        r["dn_curve_sws_mean"] = np.mean([S[n]["dn"].mean(-1) for n in nets if n.startswith("SWS_")], 0).tolist()
        res[cfg] = r
    # interaction contrasts (2×2) on Δ dn|own and Δ dn|6-9 (family SWS), bootstrap over instances
    def delta_inst(cfg, key):
        nets = load_cfg(run, v41, cfg)
        S = {n: dn_ss(z["E1"], z["n_pop"]) for n, z in nets.items()}
        lo, hi = res[cfg]["own_window"] if key == "own" else (6, 9)
        d = range_avg(LV, S["DATA"]["dn"].mean(-1), lo, hi)
        return np.array([range_avg(LV, S[n]["dn"].mean(-1), lo, hi) - d for n in sorted(S) if n.startswith("SWS_")])
    inter = {}
    for name, (a1b1, a0b1, a1b0, a0b0) in {"b_a×v_th(gap6)": ("TH6", "BA0xTH6", "D0", "BA0"), "b_a×v_th(gap8)": ("TH8", "BA0xTH8", "D0", "BA0"),
                                           "b_a×J0(0.15)": ("J015", "BA0xJ015", "D0", "BA0"), "b_a×J0(0.25)": ("J025", "BA0xJ025", "D0", "BA0")}.items():
        if all(c in res for c in (a1b1, a0b1, a1b0, a0b0)):
            for key in ("6-9", "own"):
                v = [delta_inst(c, key) for c in (a1b1, a0b1, a1b0, a0b0)]
                ic = (v[0].mean() - v[1].mean()) - (v[2].mean() - v[3].mean())
                bs = []
                for _ in range(5000):
                    i = rng.integers(len(v[0]), size=len(v[0]))      # same instances across configs (paired)
                    bs.append((v[0][i].mean() - v[1][i].mean()) - (v[2][i].mean() - v[3][i].mean()))
                inter[f"{name}|{key}"] = dict(contrast=float(ic), ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
    return res, inter


def closedloop(run, rng):
    path = os.path.join(run, "closedloop.jsonl")
    if not os.path.exists(path):
        return None
    recs = [json.loads(l) for l in open(path) if l.strip()]
    by = {r["name"]: r for r in recs}
    out = dict(n_records=len(recs), errors=sum(1 for r in recs if r.get("error")), per_config={})
    P = {r["seed"]: r for r in recs if r["config"] == "P"}
    for cfg in CL_CONFIGS:
        fams = sorted({r["family"] for r in recs if r["config"] == cfg and r["family"] != "DATA"})
        e = {}
        for fam in fams:
            for st in ("S1", "S2", "ALL"):
                rows = []
                for r in recs:
                    if r["config"] == cfg and r["family"] == fam and (st == "ALL" or r["stratum"] == st):
                        d = by.get(f"{cfg}|DATA|{r['seed']}")
                        if d and not d.get("error") and not r.get("error"):
                            rows.append((d["final_abs_err"] - r["final_abs_err"], r["k"], d["moved"], r["moved"], d["overshoot_deg"] - r["overshoot_deg"]))
                if not rows:
                    continue
                dd = np.array([x[0] for x in rows])
                cl = np.array([x[1] for x in rows])
                u = np.unique(cl)
                bs = []
                for _ in range(10_000):
                    pick = rng.choice(u, len(u))
                    bs.append(np.concatenate([dd[cl == c] for c in pick]).mean())
                e[f"{fam}|{st}"] = dict(n=len(dd), mean_d=float(dd.mean()), ci95_cluster=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                                        median_d=float(np.median(dd)), zeros=int((dd == 0).sum()),
                                        only_data_moved=int(sum(1 for x in rows if x[2] and not x[3])),
                                        only_ctrl_moved=int(sum(1 for x in rows if x[3] and not x[2])),
                                        overshoot_diff_mean=float(np.mean([x[4] for x in rows])),
                                        data_mean_err=float(np.mean([by[f"{cfg}|DATA|{s}"]["final_abs_err"] for s in {r['seed'] for r in recs if r['config'] == cfg and (st == 'ALL' or r['stratum'] == st)}])))
        out["per_config"][cfg] = e
    if P:
        out["P_mean_err"] = {st: float(np.mean([r["final_abs_err"] for r in P.values() if st == "ALL" or r["stratum"] == st])) for st in ("S1", "S2", "ALL")}
    return out


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--run", required=True)
    ap.add_argument("--v41", required=True)
    ap.add_argument("--name", default="analysis.json")
    a = ap.parse_args()
    rng = np.random.default_rng(BOOT)
    ol, inter = openloop(a.run, a.v41, rng)
    cl = closedloop(a.run, np.random.default_rng(CLB))
    q8 = None
    if cl:
        q8 = {}
        for st in ("S1", "S2"):
            xs = [ol[c]["families"]["SWS"]["dn|own"]["delta"] for c in CL_CONFIGS if c in ol and f"SWS|{st}" in cl["per_config"].get(c, {})]
            ys = [cl["per_config"][c][f"SWS|{st}"]["mean_d"] for c in CL_CONFIGS if c in ol and f"SWS|{st}" in cl["per_config"].get(c, {})]
            if len(xs) >= 4:
                rr = stats.spearmanr(xs, ys)
                q8[st] = dict(n=len(xs), spearman=float(rr[0]), p=float(rr[1]), x_openloop_delta_dn_own=xs, y_closedloop_d=ys)
    out = dict(openloop=ol, interactions=inter, closedloop=cl, Q8=q8)
    with open(os.path.join(a.run, a.name), "x") as f:
        json.dump(out, f, indent=1, default=float)
    for c, r in ol.items():
        e = r["families"]["SWS"]
        print(f"{c:9s} th10 DATA {r['data_I_th10']:.2f} | ΔDN 6–9 {e['dn|6-9']['delta']:+6.2f} [{e['dn|6-9']['ci95'][0]:+.2f};{e['dn|6-9']['ci95'][1]:+.2f}]"
              f" 9–12 {e['dn|9-12']['delta']:+6.2f} [{e['dn|9-12']['ci95'][0]:+.2f};{e['dn|9-12']['ci95'][1]:+.2f}] own {e['dn|own']['delta']:+6.2f}"
              f" | ΔLC 6–9 {e['lc|6-9']['delta']:+.3f} | Δth30 {e['I_th30']['delta']:+.3f} | ΔG7 {e['G_small']['7.0'].get('delta', float('nan')):+.2f} | eq {e['equivalent_Q6']}")
    for k, v in inter.items():
        print("interaction", k, round(v["contrast"], 2), np.round(v["ci95"], 2))
    if cl:
        for c, e in cl["per_config"].items():
            print(c, {k: (round(v["mean_d"], 3), np.round(v["ci95_cluster"], 3).tolist()) for k, v in e.items()})
        print("P", cl.get("P_mean_err"), "Q8", q8)


if __name__ == "__main__":
    main()
