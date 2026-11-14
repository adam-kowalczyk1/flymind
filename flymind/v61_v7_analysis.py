"""flymind/v61_v7_analysis.py — pre-specified analyses of V6.1 (V61_PROTOCOL.md §4) and V7 (V7_PROTOCOL.md §2). Written before any
V6.1 / V7 trial result was opened. d = err(DATA) − err(ctrl) (positive = control has lower error).
Run: .venv/bin/python -I -B flymind/v61_v7_analysis.py --v61 flymind/results/v61 --v6 flymind/results/v6
     .venv/bin/python -I -B flymind/v61_v7_analysis.py --v7 flymind/results/v7 --v6 flymind/results/v6 --drive flymind/results/v61/drive_index.json
V7 "corresponding drive regime" (protocol §2, operationalised here before the run): G4 (ρ < 0.16, stronger drive than S1) and the
ρ < 0.22 half of G2/G3 → V5 v4 S1 sign (d > 0); G1 (ρ ≥ 0.28) and the ρ ≥ 0.22 half of G2/G3 → S2 sign (d < 0).
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from v5v41_e6_analysis import per_net as e6_net  # noqa: E402

V61_RNG, V7_RNG = 8_419_030, 8_419_040


def load(path):
    recs = []
    for line in open(path):
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return recs


def cluster_ci(d, cl, rng, n=10_000):
    u = np.unique(cl)
    idx = {c: np.flatnonzero(cl == c) for c in u}
    bs = [d[np.concatenate([idx[c] for c in rng.choice(u, len(u))])].mean() for _ in range(n)]
    return [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def paired(recs, cfg, fam, ref="DATA", sel=lambda r: True):
    by = {(r["config"], r["family"] if r.get("cond") != "classical_p" else "P", r["seed"]): r for r in recs if not r.get("error")}
    rows = []
    for (c, f, s), r in by.items():
        if c == cfg and f == fam and sel(r) and (c, ref, s) in by:
            d = by[(c, ref, s)]
            rows.append(dict(d=d["final_abs_err"] - r["final_abs_err"], k=r["k"] if r["k"] is not None else s, seed=s, rho=r["rho"],
                             az=r["az0_deg"], ref_moved=d["moved"], moved=r["moved"], ref_err=d["final_abs_err"], err=r["final_abs_err"],
                             ref_succ=d["success"], succ=r["success"], ov=d["overshoot_deg"] - r["overshoot_deg"]))
    return rows


def summarise(rows, rng):
    if not rows:
        return None
    d = np.array([x["d"] for x in rows])
    cl = np.array([x["k"] for x in rows])
    return dict(n=len(d), mean_d=float(d.mean()), ci95_cluster=cluster_ci(d, cl, rng), median_d=float(np.median(d)), zeros=int((d == 0).sum()),
                only_ref_moved=sum(1 for x in rows if x["ref_moved"] and not x["moved"]),
                only_ctrl_moved=sum(1 for x in rows if x["moved"] and not x["ref_moved"]),
                ref_mean_err=float(np.mean([x["ref_err"] for x in rows])), ctrl_mean_err=float(np.mean([x["err"] for x in rows])),
                ref_median_err=float(np.median([x["ref_err"] for x in rows])), ctrl_median_err=float(np.median([x["err"] for x in rows])),
                ref_success=float(np.mean([x["ref_succ"] for x in rows])), ctrl_success=float(np.mean([x["succ"] for x in rows])),
                ref_moved=float(np.mean([x["ref_moved"] for x in rows])), ctrl_moved=float(np.mean([x["moved"] for x in rows])),
                overshoot_diff_mean=float(np.mean([x["ov"] for x in rows])))


def toy(run):
    p = os.path.join(run, "toy", "toy.npz")
    if not os.path.exists(p):
        return None
    z = np.load(p)
    c = z["E1_counts"].astype(float)[..., 50:100, :].mean(-2) * 100.0
    dn = ((c[:, 0, :, 4] + c[:, 1, :, 5]) / 2).mean(-1)
    G = e6_net(dict(counts=z["E6_counts"], deltas=z["deltas"], n_pop=z["n_pop"]))["G_small"].mean(-1)
    return dict(levels=z["E1_levels"].tolist(), dn_ipsi=dn.tolist(), I0=z["I0"].tolist(), G_small=G.tolist())


def v61(run, v6run):
    rng = np.random.default_rng(V61_RNG)
    recs = load(os.path.join(run, "v61.jsonl"))
    d0 = [dict(r, config="I12", i_max=12.0) for r in load(os.path.join(v6run, "closedloop.jsonl")) if r["config"] == "D0"]
    recs_all = recs + d0
    drive = {r["seed"]: r for r in json.load(open(os.path.join(run, "drive_index.json"))) if "block" not in r}
    out = dict(n_records=len(recs), errors=sum(1 for r in recs if r.get("error")), per_imax={}, toy=toy(run))
    fams = sorted({r["family"] for r in recs_all if r["family"] != "DATA"})
    for im in (8, 10, 12, 14, 16):
        cfg = f"I{im}"
        for fam in fams:
            for st in ("S1", "S2", "ALL"):
                s = summarise(paired(recs_all, cfg, fam, sel=lambda r: st == "ALL" or r["stratum"] == st), rng)
                if s:
                    out["per_imax"][f"{cfg}|{fam}|{st}"] = s
    # descriptive model d ~ drive_index + ρ pooled over I_max (OLS, cluster bootstrap over control instances)
    out["drive_model"] = {}
    for fam in fams:
        rows = []
        for im in (8, 10, 12, 14, 16):
            for x in paired(recs_all, f"I{im}", fam):
                g = drive[x["seed"]]
                rows.append((x["d"], max(g["gL"], g["gR"]) * im, x["rho"], x["k"]))
        if not rows:
            continue
        a = np.array([r[:3] for r in rows], float)
        cl = np.array([r[3] for r in rows])
        X = np.c_[np.ones(len(a)), a[:, 1], a[:, 2]]
        beta = np.linalg.lstsq(X, a[:, 0], rcond=None)[0]
        u = np.unique(cl)
        idx = {c: np.flatnonzero(cl == c) for c in u}
        bs = []
        for _ in range(5000):
            i = np.concatenate([idx[c] for c in rng.choice(u, len(u))])
            bs.append(np.linalg.lstsq(X[i], a[i, 0], rcond=None)[0])
        bs = np.array(bs)
        out["drive_model"][fam] = dict(n=len(a), beta=dict(zip(("intercept", "drive_mV", "rho_m"), beta.tolist())),
                                       ci95={k: [float(np.percentile(bs[:, j], 2.5)), float(np.percentile(bs[:, j], 97.5))]
                                             for j, k in enumerate(("intercept", "drive_mV", "rho_m"))},
                                       drive_range=[float(a[:, 1].min()), float(a[:, 1].max())])
    with open(os.path.join(run, "analysis.json"), "x") as f:
        json.dump(out, f, indent=1)
    for k, v in out["per_imax"].items():
        print(f"{k:16s} n {v['n']:3d} d {v['mean_d']:+.3f} [{v['ci95_cluster'][0]:+.3f};{v['ci95_cluster'][1]:+.3f}] med {v['median_d']:+.3f} "
              f"zeros {v['zeros']:3d} err DATA {v['ref_mean_err']:.2f} ctrl {v['ctrl_mean_err']:.2f} moved {v['ref_moved']:.2f}/{v['ctrl_moved']:.2f}")
    for k, v in out["drive_model"].items():
        print("drive model", k, {a: round(b, 4) for a, b in v["beta"].items()}, {a: np.round(b, 4).tolist() for a, b in v["ci95"].items()})


def v7(run, drive_path):
    rng = np.random.default_rng(V7_RNG)
    recs = load(os.path.join(run, "v7.jsonl"))
    drive = {r["seed"]: r for r in json.load(open(drive_path)) if "block" in r}
    out = dict(n_records=len(recs), errors=sum(1 for r in recs if r.get("error")), per_block={})
    halves = {"near": lambda r: r["rho"] < 0.22, "far": lambda r: r["rho"] >= 0.22}
    for b in ("G1", "G2", "G3", "G4"):
        e = {}
        subsets = {"ALL": lambda r: True, **(halves if b in ("G2", "G3") else {})}
        for sn, sel in subsets.items():
            e[f"SWS|{sn}"] = summarise(paired(recs, b, "SWS", sel=sel), rng)
            e[f"P|{sn}"] = summarise(paired(recs, b, "P", sel=sel), rng)        # d = err(DATA) − err(P)
        expect = {"G1": [("ALL", -1)], "G4": [("ALL", +1)], "G2": [("near", +1), ("far", -1)], "G3": [("near", +1), ("far", -1)]}[b]
        e["pattern"] = {sn: ("pattern holds" if e[f"SWS|{sn}"] and sign * e[f"SWS|{sn}"]["ci95_cluster"][0 if sign > 0 else 1] > 0
                             else "not shown") for sn, sign in expect}
        e["drive_max_mV_median"] = float(np.median([max(drive[s]["gL"], drive[s]["gR"]) * 12.0 for s in {r["seed"] for r in recs if r["config"] == b}]))
        e["n_px_zero"] = int(sum(1 for s in {r["seed"] for r in recs if r["config"] == b} if drive[s]["n_px"] == 0))
        out["per_block"][b] = e
    with open(os.path.join(run, "analysis.json"), "x") as f:
        json.dump(out, f, indent=1)
    for b, e in out["per_block"].items():
        for k, v in e.items():
            if isinstance(v, dict) and "mean_d" in v:
                print(f"{b} {k:9s} n {v['n']:3d} d {v['mean_d']:+.3f} [{v['ci95_cluster'][0]:+.3f};{v['ci95_cluster'][1]:+.3f}] med {v['median_d']:+.3f} "
                      f"err DATA {v['ref_mean_err']:.2f} ctrl {v['ctrl_mean_err']:.2f} succ {v['ref_success']:.2f}/{v['ctrl_success']:.2f} "
                      f"moved {v['ref_moved']:.2f}/{v['ctrl_moved']:.2f}")
        print(b, "pattern", e["pattern"], "drive median", round(e["drive_max_mV_median"], 2), "no-pixel scenes", e["n_px_zero"])


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--v61")
    ap.add_argument("--v7")
    ap.add_argument("--v6", required=True)
    ap.add_argument("--drive")
    a = ap.parse_args()
    if a.v61:
        v61(a.v61, a.v6)
    if a.v7:
        v7(a.v7, a.drive)


if __name__ == "__main__":
    main()
