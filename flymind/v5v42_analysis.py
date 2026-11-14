"""flymind/v5v42_analysis.py — pre-specified analysis of V5 v4.2 (program_v5v41/V5v42_PROTOCOL.md §5).
DATA and SWS come from V5 v4.1 (results/v5v41/raw and results/v5v41/E6/raw; same networks, seeds and schedules).
Run: .venv/bin/python -I -B flymind/v5v42_analysis.py --run flymind/results/v5v42 --v41 flymind/results/v5v41
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
from v5v41_analysis import compare, range_avg, run_metrics, spearman_ci, thresholds  # noqa: E402
from v5v41_e6_analysis import per_net as e6_net  # noqa: E402

FAMS = ("SWS", "B1", "B2", "B3", "B4", "B5")
LABEL = {"SWS": "SWS v2 (all blocks)", "B1": "LC×LC", "B2": "LC→mid", "B3": "mid→LC", "B4": "mid×mid", "B5": "ALL re-impl."}
BOOT, CORR = 8_419_010, 8_419_011


def load_all(run, v41):
    nets = {}
    for p in glob.glob(os.path.join(v41, "raw", "*.npz")):
        nets[os.path.basename(p)[:-4]] = dict(np.load(p))
    for p in glob.glob(os.path.join(v41, "E6", "raw", "*.npz")):
        z = np.load(p)
        nets[os.path.basename(p)[:-4]].update(E6_counts=z["counts"], E6_I0=z["I0"], E6_deltas=z["deltas"])
    for p in glob.glob(os.path.join(run, "raw", "*.npz")):
        nets[os.path.basename(p)[:-4]] = dict(np.load(p))
    fam = {f: sorted(k for k in nets if k.startswith(f + "_")) for f in FAMS}
    return nets, fam


def e6z(z):
    return dict(counts=z["E6_counts"], deltas=z["E6_deltas"], I0=z["E6_I0"], n_pop=z["n_pop"])


def summary_vec(z):
    """Per-network vectors used for the family comparisons: E1 side-averaged steady states [Lv, R] and E6 gain [I0, R]."""
    m = run_metrics(z, "E1")
    m0 = run_metrics(z, "E1n0")
    g = e6_net(e6z(z))
    lv = z["E1_levels"]
    out = {k: np.nanmean(m[k], 1) for k in ("dn_ipsi", "lc_ipsi", "mid_ipsi", "angle_ss_deg")}
    out["dn_ipsi_n0"] = np.nanmean(m0["dn_ipsi"], 1)
    out["G_small"] = g["G_small"]
    out["th"] = {t: float(np.nanmean([thresholds(lv, np.nanmean(m[met][:, s], -1), th) for s in (0, 1)]))
                 for t, (met, th) in {"I_th10_dn": ("dn_ipsi", 10), "I_th30_dn": ("dn_ipsi", 30), "I_lc1": ("lc_ipsi", 1)}.items()}
    out["levels"], out["I0"] = lv, z["E6_I0"]
    out.update(mediators(z))
    return out


def mediators(z):
    """Amendment A2: population synchrony at 7–9 mV (E1 / E1n0 steady window 500–1000 ms, 10 ms bins)."""
    res = {}
    for exp in ("E1", "E1n0"):
        lv = np.round(z[f"{exp}_levels"], 3)
        c = z[f"{exp}_counts"].astype(float)[(lv >= 7) & (lv <= 9)][..., 50:100, :]   # [l, side, R, 50, 6]
        lc = c[..., 0]
        mid = np.stack([c[:, 0, ..., 2], c[:, 1, ..., 3]], 1)                          # ipsi mid
        fano = lambda x: float(np.nanmean(x.var(-1) / np.where(x.mean(-1) > 0, x.mean(-1), np.nan)))
        f = np.fft.rfftfreq(50, 0.01)
        P = np.abs(np.fft.rfft(lc - lc.mean(-1, keepdims=True), axis=-1)) ** 2
        band = (f >= 6) & (f <= 14)
        res[f"lc_fano_{exp}"] = fano(lc)
        res[f"mid_fano_{exp}"] = fano(mid)
        res[f"lc_pow614_{exp}"] = float(np.nanmean(P[..., band].sum(-1) / np.maximum(P[..., 1:].sum(-1), 1e-12)))
    return res


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--run", required=True)
    ap.add_argument("--v41", required=True)
    a = ap.parse_args()
    nets, fam = load_all(a.run, a.v41)
    S = {k: summary_vec(nets[k]) for k in ["DATA"] + [x for f in FAMS for x in fam[f]]}
    D = S["DATA"]
    lv, I0 = D["levels"], D["I0"]
    rng = np.random.default_rng(BOOT)
    out = dict(n=dict((f, len(fam[f])) for f in FAMS), levels=lv.tolist(), I0=I0.tolist(), families={})
    for f in FAMS:
        K = [S[k] for k in fam[f]]
        if not K:
            continue
        e = dict(label=LABEL[f], ranges={}, per_level={}, thresholds={}, E6={})
        for m in ("dn_ipsi", "lc_ipsi", "mid_ipsi", "angle_ss_deg", "dn_ipsi_n0"):
            xK = np.stack([k[m] for k in K])
            e["per_level"][m] = [compare(D[m][i], xK[:, i], rng) for i in range(len(lv))]
            for rn, (lo, hi) in {"6-10": (6, 10), "6-8": (6, 8), "8-10": (8, 10), "6-9": (6, 9)}.items():
                e["ranges"][f"{m}|{rn}"] = compare(range_avg(lv, D[m], lo, hi), np.stack([range_avg(lv, x, lo, hi) for x in xK]), rng)
        for t in D["th"]:
            v = np.array([k["th"][t] for k in K])
            e["thresholds"][t] = dict(data=D["th"][t], ctrl_mean=float(np.nanmean(v)), delta=float(np.nanmean(v) - D["th"][t]),
                                      ctrl_q=[float(np.nanpercentile(v, q)) for q in (2.5, 50, 97.5)], frac_gt_data=float((v > D["th"][t]).mean()))
        for m in ("lc_fano_E1", "mid_fano_E1", "lc_pow614_E1", "lc_fano_E1n0", "mid_fano_E1n0"):
            v = np.array([k[m] for k in K])
            e.setdefault("mediators", {})[m] = dict(data=D[m], ctrl_mean=float(v.mean()), ctrl_q=[float(np.percentile(v, q)) for q in (2.5, 50, 97.5)],
                                                    frac_gt_data=float((v > D[m]).mean()))
        for m in ("dn_ipsi", "lc_ipsi", "mid_ipsi"):
            m6 = (lv >= 6) & (lv <= 9)
            e["ranges"][f"{m}|6-9|plainmean"] = float(np.mean([k[m][m6].mean() for k in K]) - D[m][m6].mean())
        xK = np.stack([k["G_small"] for k in K])
        e["E6"]["G_small"] = {str(float(x)): compare(D["G_small"][i], xK[:, i], rng) for i, x in enumerate(I0)}
        out["families"][f] = e
    # ---- additivity: Σ Δ_B1..B4 vs Δ_SWS and Δ_B5 (per level, rep-mean family means) ----
    def fam_delta(f, m):
        return np.mean([S[k][m].mean(-1) for k in fam[f]], 0) - D[m].mean(-1)
    add = {}
    for m in ("dn_ipsi", "lc_ipsi", "mid_ipsi"):
        s = sum(fam_delta(f, m) for f in ("B1", "B2", "B3", "B4"))
        add[m] = dict(sum_blocks=s.tolist(), sws=fam_delta("SWS", m).tolist(), b5=fam_delta("B5", m).tolist(),
                      sum_blocks_6_9=float(range_avg(lv, s, 6, 9)), sws_6_9=float(range_avg(lv, fam_delta("SWS", m), 6, 9)),
                      b5_6_9=float(range_avg(lv, fam_delta("B5", m), 6, 9)),
                      per_block_6_9={f: float(range_avg(lv, fam_delta(f, m), 6, 9)) for f in ("B1", "B2", "B3", "B4")})
    out["additivity"] = add
    # ---- family vs SWS (difference of family means, bootstrap over instances of both) ----
    vs = {}
    for f in ("B1", "B2", "B3", "B4", "B5"):
        a6 = np.array([range_avg(lv, S[k]["dn_ipsi"].mean(-1), 6, 9) for k in fam[f]])
        s6 = np.array([range_avg(lv, S[k]["dn_ipsi"].mean(-1), 6, 9) for k in fam["SWS"]])
        bs = [rng.choice(a6, len(a6)).mean() - rng.choice(s6, len(s6)).mean() for _ in range(10_000)]
        vs[f] = dict(diff_dn_6_9=float(a6.mean() - s6.mean()), ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                     mannwhitney_p=float(stats.mannwhitneyu(a6, s6).pvalue))
    out["family_vs_SWS"] = vs
    # ---- structure–function across block-family instances ----
    st = {(r["family"], r["seed"]): r for r in json.load(open(os.path.join(a.run, "structure.json")))["rows"]}
    xs = dict(lc_recip=[], lc_tri=[], lcmid_recip=[], mid_tri=[], all_clust=[], dDN=[], fam=[])
    for f in ("SWS", "B1", "B2", "B3", "B4", "B5"):
        for k in fam[f]:
            r = st[(f, int(k.split("_")[1]))]
            xs["lc_recip"].append(r["graph"]["LCxLC"]["reciprocal_pairs"])
            xs["lc_tri"].append(r["graph"]["LCxLC"]["triangles"])
            xs["lcmid_recip"].append(r["graph"]["LC_MID"]["lc_mid_reciprocal_pairs"])
            xs["mid_tri"].append(r["graph"]["MIDxMID"]["triangles"])
            xs["all_clust"].append(r["graph"]["all"]["avg_clustering"])
            xs["dDN"].append(float(range_avg(lv, S[k]["dn_ipsi"].mean(-1) - D["dn_ipsi"].mean(-1), 6, 9)))
            xs["fam"].append(f)
    r2 = np.random.default_rng(CORR)
    out["structure_function"] = {k: spearman_ci(xs[k], xs["dDN"], r2) for k in ("lc_recip", "lc_tri", "lcmid_recip", "mid_tri", "all_clust")}
    out["structure_function"]["within_family"] = {f: {k: spearman_ci(np.array(xs[k])[np.array(xs["fam"]) == f], np.array(xs["dDN"])[np.array(xs["fam"]) == f], r2)
                                                      for k in ("lc_recip", "lc_tri", "lcmid_recip")} for f in ("SWS", "B1", "B2")}
    out["structure_function"]["per_inst"] = xs
    with open(os.path.join(a.run, "analysis.json"), "x") as fh:
        json.dump(out, fh, indent=1, default=float)
    make_figures(a.run, out, S, fam, D)
    for f, e in out["families"].items():
        r = e["ranges"]["dn_ipsi|6-9"]
        r2_ = e["ranges"]["lc_ipsi|6-9"]
        g = e["E6"]["G_small"]["7.0"]
        print(f"{f:4s} {LABEL[f]:22s} ΔDN(6–9) {r['delta']:+6.2f} [{r['ci95'][0]:+.2f};{r['ci95'][1]:+.2f}]  ΔLC(6–9) {r2_['delta']:+6.3f} "
              f"[{r2_['ci95'][0]:+.3f};{r2_['ci95'][1]:+.3f}]  ΔG(I0=7) {g['delta']:+6.2f} [{g['ci95'][0]:+.2f};{g['ci95'][1]:+.2f}]  "
              f"Δth30 {e['thresholds']['I_th30_dn']['delta']:+.3f} | LC Fano {e['mediators']['lc_fano_E1']['ctrl_mean']:.1f} (DATA {e['mediators']['lc_fano_E1']['data']:.1f})"
              f" mid Fano {e['mediators']['mid_fano_E1']['ctrl_mean']:.1f} (DATA {e['mediators']['mid_fano_E1']['data']:.1f})")
    print("additivity dn 6–9:", {k: round(v, 3) for k, v in add["dn_ipsi"].items() if k.endswith("6_9") and not isinstance(v, dict)}, add["dn_ipsi"]["per_block_6_9"])


def make_figures(run, out, S, fam, D):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(os.path.join(run, "figures"), exist_ok=True)
    lv = D["levels"]
    fig, ax = plt.subplots(2, 3, figsize=(16, 8), sharex=True)
    for a, f in zip(ax.flat, FAMS):
        for k in fam[f]:
            a.plot(lv, S[k]["dn_ipsi"].mean(-1) - D["dn_ipsi"].mean(-1), color="0.6", lw=0.5)
        if fam[f]:
            a.plot(lv, np.mean([S[k]["dn_ipsi"].mean(-1) for k in fam[f]], 0) - D["dn_ipsi"].mean(-1), "b", lw=2)
        a.axhline(0, color="k", lw=0.5)
        a.axvspan(6, 9, color="y", alpha=0.08)
        a.set_title(f"{f} {LABEL[f]}: Δ DNa02 ipsi (control − DATA) [Hz]")
        a.set_xlabel("LC10a ipsi current [mV]")
    fig.tight_layout()
    fig.savefig(os.path.join(run, "figures", "G1_block_delta_dn.png"), dpi=110)
    plt.close(fig)
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    xs = out["structure_function"]["per_inst"]
    col = {"SWS": "k", "B1": "tab:red", "B2": "tab:blue", "B3": "tab:green", "B4": "tab:orange", "B5": "0.5"}
    for a, k in zip(ax, ("lc_recip", "lcmid_recip", "mid_tri")):
        for f in FAMS:
            m = np.array(xs["fam"]) == f
            a.scatter(np.array(xs[k])[m], np.array(xs["dDN"])[m], s=8, color=col[f], label=f)
        a.set_xlabel(k); a.set_ylabel("Δ DNa02 ipsi 6–9 mV [Hz]"); a.axhline(0, color="k", lw=0.5)
    ax[0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(run, "figures", "G2_structure_function.png"), dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    main()
