"""flymind/v5v41_analysis.py — pre-specified analysis of V5 v4.1 (program_v5v41/V5v41_PROTOCOL.md §4–5). Descriptive / estimation.
Reads <run>/raw/*.npz + instances.json; writes <run>/analysis.json and <run>/figures/*.png (new files only).
Reusable: per-run metrics (`run_metrics`) and the hierarchical-bootstrap comparison (`compare`) are imported by later stages.

Unit of between-network inference = network instance. DATA is one network: its noise-repetition uncertainty is resampled once per
bootstrap iteration (common to all comparisons); each resampled control instance has its repetitions resampled independently.
Run: .venv/bin/python -I -B flymind/v5v41_analysis.py --run flymind/results/v5v41
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
BIN, SLOPE, RMAX = 10, 492.11874242900916, 250.0
PRE = {"E3": 500, "E3c": 500}
B_BOOT, BOOT_SEED, CORR_SEED = 10_000, 8_419_001, 8_419_002
RANGES = {"6-10": (6.0, 10.0), "6-8": (6.0, 8.0), "8-10": (8.0, 10.0), "4-12": (4.0, 12.0), "6-9": (6.0, 9.0)}


def load(run):
    nets = {}
    for p in sorted(glob.glob(os.path.join(run, "raw", "*.npz"))):
        nets[os.path.basename(p)[:-4]] = dict(np.load(p))
    return nets


def run_metrics(z, exp):
    """Per (level, side, rep) metrics for a step experiment. Side 0 = L driven, 1 = R driven (ipsi = driven side)."""
    c = z[f"{exp}_counts"].astype(float)                    # [Lv, 2, R, nb, 6]
    n = z["n_pop"].astype(float)
    pre = PRE.get(exp, 0) // BIN
    nin = np.array([[n[0], n[1]], [n[1], n[0]]])           # [side] → (ipsi n, contra n)
    nmid = np.array([[n[2], n[3]], [n[3], n[2]]])
    rate = np.empty(c.shape[:4] + (6,))
    for s in (0, 1):
        x = c[:, s] * 1000.0 / BIN
        dn_i, dn_c = (4, 5) if s == 0 else (5, 4)
        mid_i, mid_c = (2, 3) if s == 0 else (3, 2)
        rate[:, s, ..., 0] = x[..., 0] / nin[s, 0]          # LC10a ipsi
        rate[:, s, ..., 1] = x[..., 1] / nin[s, 1]          # LC10a contra
        rate[:, s, ..., 2] = x[..., mid_i] / nmid[s, 0]     # mid ipsi (somaSide = driven side)
        rate[:, s, ..., 3] = x[..., mid_c] / nmid[s, 1]
        rate[:, s, ..., 4] = x[..., dn_i]                   # DNa02 ipsi
        rate[:, s, ..., 5] = x[..., dn_c]
    ssw = slice(pre + 50, pre + 100)
    ss = rate[..., ssw, :].mean(-2)                          # [Lv, 2, R, 6]
    sgn = np.array([1.0, -1.0])[None, :, None]
    ang = z[f"{exp}_angle"]                                  # rad, + = left
    out = dict(lc_ipsi=ss[..., 0], lc_contra=ss[..., 1], mid_ipsi=ss[..., 2], mid_contra=ss[..., 3], dn_ipsi=ss[..., 4],
               dn_contra=ss[..., 5], D_ipsi=ss[..., 4] - ss[..., 5],
               angle_ss_deg=np.degrees((ss[..., 4] - ss[..., 5]) / SLOPE),
               angle_dec_final_deg=np.degrees(ang[..., -1] * sgn), angle_dec_mean_ss_deg=np.degrees(ang[..., ssw].mean(-1) * sgn))
    dn = rate[..., 4]
    tr = dn[..., pre:pre + 16]
    tr20 = (tr[..., 0:-1:2] + tr[..., 1::2]) / 2
    out["dn_peak_0_150"] = tr20[..., :8].max(-1)
    out["dn_peak_over_ss"] = np.where(out["dn_ipsi"] > 1, out["dn_peak_0_150"] / np.maximum(out["dn_ipsi"], 1e-9), np.nan)
    fd = z[f"{exp}_first_dn"].astype(float)
    out["latency_ms"] = np.where(fd < 0, np.nan, fd)
    out["latency_censored"] = (fd < 0).astype(float)
    a = np.exp(-BIN / 50.0)
    f = np.zeros(dn.shape[:-1])
    th = np.full(dn.shape[:-1], np.nan)
    half = 0.5 * out["dn_ipsi"]
    for b in range(pre, dn.shape[-1]):
        f = a * f + (1 - a) * dn[..., b]
        hit = np.isnan(th) & (f >= half) & (half > 1)
        th[hit] = (b - pre + 1) * BIN
    out["t_half_ms"] = th
    ad = z[f"{exp}_adapt"]
    out["adapt_lc_end"], out["adapt_mid_end"], out["adapt_dn_end"] = ad[..., -1, 0], ad[..., -1, 1], ad[..., -1, 2]
    return out


def neuron_sat(z, exp, R):
    """Fraction of neurons with steady-state rate ≥ 0.9 r_max (rep-summed spikes over 500 ms) per level and side."""
    r = z[f"{exp}_ss"] / (R * 0.5)
    return (r >= 0.9 * RMAX).mean(-1)


def thresholds(levels, curve, th):
    """Smallest interpolated level where curve (rep-mean, levels ascending) reaches th; nan if never, levels[0] if already."""
    k = np.flatnonzero(curve >= th)
    if not len(k):
        return np.nan
    i = k[0]
    if i == 0:
        return float(levels[0])
    return float(levels[i - 1] + (th - curve[i - 1]) / (curve[i] - curve[i - 1]) * (levels[i] - levels[i - 1]))


def compare(xD, xK, rng, B=B_BOOT):
    """xD [R], xK [K, R] (nan allowed). Δ = mean_k mean_r xK − mean_r xD with hierarchical bootstrap CI95."""
    mD, mK = np.nanmean(xD), np.nanmean(xK, 1)
    ok = np.isfinite(mK)
    if not np.isfinite(mD) or ok.sum() < 3:
        return dict(delta=None, n_inst=int(ok.sum()))
    xK, mK = xK[ok], mK[ok]
    K, R = xK.shape
    ki = rng.integers(K, size=(B, K))
    ri = rng.integers(R, size=(B, K, R))
    bK = np.nanmean(np.take_along_axis(xK[ki], ri, 2), 2)
    bD = np.nanmean(xD[rng.integers(len(xD), size=(B, len(xD)))], 1)
    bd = np.nanmean(bK, 1) - bD
    sdb = float(np.std(mK, ddof=1))
    return dict(delta=float(mK.mean() - mD), ci95=[float(np.nanpercentile(bd, 2.5)), float(np.nanpercentile(bd, 97.5))],
                data=float(mD), ctrl_mean=float(mK.mean()), sd_between=sdb, sd_within_ctrl=float(np.nanmean(np.nanstd(xK, 1, ddof=1))),
                sd_within_data=float(np.nanstd(xD, ddof=1)), frac_ctrl_ge_data=float((mK >= mD).mean()),
                std_delta=float((mK.mean() - mD) / sdb) if sdb > 0 else None, n_inst=int(K),
                ctrl_q=[float(np.percentile(mK, q)) for q in (2.5, 25, 50, 75, 97.5)])


def range_avg(levels, x, lo, hi):
    """Trapezoid average over levels in [lo, hi] along axis 0 of x."""
    m = (levels >= lo - 1e-9) & (levels <= hi + 1e-9)
    L = levels[m]
    return np.trapezoid(x[m], L, axis=0) / (L[-1] - L[0])


def hysteresis(z, R):
    """E4 ramp 4→12→4 mV over 2×4000 ms. Per side and rep: DNa02 ipsi rate binned by current (0.25 mV), up vs down."""
    c = z["E4_counts"][0].astype(float) * 1000.0 / BIN       # [2, R, 800, 6]
    nb = c.shape[2]
    half = nb // 2
    t = (np.arange(nb) * BIN + BIN / 2)
    I = np.where(np.arange(nb) < half, 4 + 8 * t / 4000, 12 - 8 * (t - 4000) / 4000)
    edges = np.arange(4.0, 12.0001, 0.25)
    up_m = np.arange(nb) < half
    res = {}
    for s in (0, 1):
        dn = c[s, :, :, 4 if s == 0 else 5]
        lc = c[s, :, :, 0] / z["n_pop"][s]
        U = np.full((dn.shape[0], len(edges) - 1), np.nan)
        D = U.copy()
        UL, DL = U.copy(), U.copy()
        for i in range(len(edges) - 1):
            m = (I >= edges[i]) & (I < edges[i + 1])
            U[:, i], D[:, i] = dn[:, m & up_m].mean(1), dn[:, m & ~up_m].mean(1)
            UL[:, i], DL[:, i] = lc[:, m & up_m].mean(1), lc[:, m & ~up_m].mean(1)
        res[s] = dict(up=U, down=D, up_lc=UL, down_lc=DL)
    centers = (edges[:-1] + edges[1:]) / 2
    return centers, res


def spearman_ci(x, y, rng, B=B_BOOT):
    x, y = np.asarray(x, float), np.asarray(y, float)
    r0 = stats.spearmanr(x, y)
    bs = []
    for _ in range(2000):
        i = rng.integers(len(x), size=len(x))
        bs.append(stats.spearmanr(x[i], y[i])[0])
    return dict(rho=float(r0[0]), p=float(r0[1]), ci95=[float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))], n=len(x))


STEP_EXPS = ("E1", "E1n0", "E2", "E3", "E3c", "E5")
MAIN_METRICS = ("dn_ipsi", "dn_contra", "lc_ipsi", "lc_contra", "mid_ipsi", "mid_contra", "D_ipsi", "angle_ss_deg",
                "angle_dec_final_deg", "dn_peak_0_150", "latency_ms", "t_half_ms", "adapt_lc_end", "adapt_mid_end", "adapt_dn_end")


def analyze(run, ctrl_prefix="SWS_", data_name="DATA", figures=True):
    nets = load(run)
    D = nets[data_name]
    names = sorted(k for k in nets if k.startswith(ctrl_prefix))
    rng = np.random.default_rng(BOOT_SEED)
    out = dict(n_ctrl=len(names), ctrl_names=names, experiments={})
    curves = {}
    for exp in STEP_EXPS:
        if f"{exp}_counts" not in D:
            continue
        lv = D[f"{exp}_levels"]
        mD = run_metrics(D, exp)
        mK = [run_metrics(nets[k], exp) for k in names]
        R = mD["dn_ipsi"].shape[2]
        e = dict(levels=lv.tolist(), per_level={}, ranges={}, thresholds={}, saturation={})
        for m in MAIN_METRICS:
            # pool sides as repetitions? No: report side-averaged (mean of L and R) per rep, and per side separately.
            xD = np.nanmean(mD[m], 1)                         # [Lv, R] side-averaged
            xK = np.stack([np.nanmean(q[m], 1) for q in mK])  # [K, Lv, R]
            e["per_level"][m] = [compare(xD[i], xK[:, i], rng) for i in range(len(lv))]
            for side in (0, 1):
                e["per_level"][f"{m}_side{'LR'[side]}"] = [compare(mD[m][i, side], np.stack([q[m][i, side] for q in mK]), rng)
                                                          for i in range(len(lv))] if m in ("dn_ipsi", "lc_ipsi", "angle_ss_deg") else None
            for rn, (lo, hi) in RANGES.items():
                if lv.min() <= lo + 1e-9 and lv.max() >= hi - 1e-9 and (m not in ("latency_ms", "t_half_ms", "dn_peak_over_ss")):
                    aD = range_avg(lv, xD, lo, hi)
                    aK = np.stack([range_avg(lv, xK[k], lo, hi) for k in range(len(names))])
                    e["ranges"][f"{m}|{rn}"] = compare(aD, aK, rng)
            curves[(exp, m)] = (lv, np.nanmean(xD, -1), np.nanmean(xK, -1))
        for th_name, (met, th) in {"I_th10_dn": ("dn_ipsi", 10), "I_th30_dn": ("dn_ipsi", 30), "I_lc1": ("lc_ipsi", 1)}.items():
            tD = np.array([thresholds(lv, np.nanmean(mD[met][:, s], -1), th) for s in (0, 1)])
            tK = np.array([[thresholds(lv, np.nanmean(q[met][:, s], -1), th) for s in (0, 1)] for q in mK])
            e["thresholds"][th_name] = dict(data_LR=tD.tolist(), data_mean=float(np.nanmean(tD)),
                                            ctrl_mean=float(np.nanmean(tK)), ctrl_q=[float(np.nanpercentile(np.nanmean(tK, 1), q)) for q in (2.5, 50, 97.5)],
                                            delta=float(np.nanmean(tK) - np.nanmean(tD)),
                                            frac_ctrl_gt_data=float((np.nanmean(tK, 1) > np.nanmean(tD)).mean()),
                                            ctrl_never=int(np.isnan(tK).any(1).sum()), per_ctrl=np.nanmean(tK, 1).tolist())
        sD = neuron_sat(D, exp, R).mean(1)
        sK = np.stack([neuron_sat(nets[k], exp, R).mean(1) for k in names])
        e["saturation"] = dict(data=sD.tolist(), ctrl_mean=sK.mean(0).tolist(), ctrl_max=sK.max(0).tolist(),
                               dn_ipsi_over_rmax_data=(np.nanmean(mD["dn_ipsi"], (1, 2)) / RMAX).tolist())
        # local slope of steady-state DN ipsi (Hz/mV), side-averaged rep-mean curves
        gD = np.gradient(np.nanmean(mD["dn_ipsi"], (1, 2)), lv)
        gK = np.stack([np.gradient(np.nanmean(q["dn_ipsi"], (1, 2)), lv) for q in mK])
        e["slope_dn_hz_per_mV"] = dict(data=gD.tolist(), ctrl_mean=gK.mean(0).tolist(), ctrl_q025=np.percentile(gK, 2.5, 0).tolist(),
                                       ctrl_q975=np.percentile(gK, 97.5, 0).tolist(), data_max=float(gD.max()), data_argmax=float(lv[gD.argmax()]),
                                       ctrl_max_median=float(np.median(gK.max(1))), ctrl_argmax_median=float(np.median(lv[gK.argmax(1)])))
        out["experiments"][exp] = e
    # ---- hysteresis ----
    if "E4_counts" in D:
        R = D["E4_counts"].shape[2]
        cen, hD = hysteresis(D, R)
        hK = [hysteresis(nets[k], R)[1] for k in names]
        def hmet(h):
            up = np.nanmean([h[s]["up"].mean(0) for s in (0, 1)], 0)
            dn = np.nanmean([h[s]["down"].mean(0) for s in (0, 1)], 0)
            m610 = (cen >= 6) & (cen <= 10)
            return dict(mean_abs_610=float(np.nanmean(np.abs(up - dn)[m610])), max_abs=float(np.nanmax(np.abs(up - dn))),
                        th10_up=thresholds(cen, up, 10), th10_down=_down_th(cen, dn, 10),
                        up=up.tolist(), down=dn.tolist())
        HD, HK = hmet(hD), [hmet(h) for h in hK]
        out["hysteresis_E4"] = dict(centers=cen.tolist(), data=HD,
                                    ctrl=dict(mean_abs_610=[h["mean_abs_610"] for h in HK], th10_up=[h["th10_up"] for h in HK],
                                              th10_down=[h["th10_down"] for h in HK]),
                                    ctrl_up_mean=np.nanmean([h["up"] for h in HK], 0).tolist(),
                                    ctrl_down_mean=np.nanmean([h["down"] for h in HK], 0).tolist())
    # ---- mechanism correlations across instances ----
    inst = os.path.join(run, "instances.json")
    if os.path.exists(inst) and "E1_counts" in D:
        rows = {f"{ctrl_prefix}{r['seed']}": r for r in json.load(open(inst))["rows"]}
        lv = D["E1_levels"]
        mD = run_metrics(D, "E1")
        dDN, dLC, rec, tri = [], [], [], []
        for k in names:
            q = run_metrics(nets[k], "E1")
            dDN.append(range_avg(lv, np.nanmean(q["dn_ipsi"], (1, 2)) - np.nanmean(mD["dn_ipsi"], (1, 2)), 6, 9))
            dLC.append(range_avg(lv, np.nanmean(q["lc_ipsi"], (1, 2)) - np.nanmean(mD["lc_ipsi"], (1, 2)), 6, 9))
            rec.append(rows[k]["lc_reciprocal_pairs"])
            tri.append(rows[k]["lc_triangles_undirected"])
        r2 = np.random.default_rng(CORR_SEED)
        out["mechanism_E1_6_9"] = dict(dDN_vs_dLC=spearman_ci(dLC, dDN, r2), dDN_vs_lc_reciprocity=spearman_ci(rec, dDN, r2),
                                       dDN_vs_lc_triangles=spearman_ci(tri, dDN, r2), dLC_vs_lc_reciprocity=spearman_ci(rec, dLC, r2),
                                       per_inst=dict(dDN=list(map(float, dDN)), dLC=list(map(float, dLC)), recip=rec, tri=tri))
    if figures:
        make_figures(run, out, curves, nets, names, D)
    return out


def _down_th(cen, dn, th):
    """On the descending ramp: the current at which the response falls below th (searching from high to low current)."""
    order = np.argsort(cen)
    c, d = cen[order], dn[order]
    return thresholds(c, d, th)


def make_figures(run, out, curves, nets, names, D):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fd = os.path.join(run, "figures")
    os.makedirs(fd, exist_ok=True)
    # F1 individual curves
    fig, ax = plt.subplots(2, 3, figsize=(15, 8))
    for a, m in zip(ax.flat, ("dn_ipsi", "lc_ipsi", "mid_ipsi", "dn_contra", "angle_ss_deg", "adapt_lc_end")):
        if ("E1", m) not in curves:
            continue
        lv, cD, cK = curves[("E1", m)]
        for y in cK:
            a.plot(lv, y, color="0.6", lw=0.5, alpha=0.6)
        a.plot(lv, cK.mean(0), color="tab:blue", lw=2, label=f"control mean (n={len(cK)})")
        a.plot(lv, cD, color="tab:red", lw=2, label="DATA")
        a.axvspan(6, 10, color="y", alpha=0.08)
        a.set_title(f"E1 steady state: {m}")
        a.set_xlabel("LC10a ipsi current [mV]")
    ax[0, 0].legend()
    fig.tight_layout()
    fig.savefig(os.path.join(fd, "F1_E1_individual_curves.png"), dpi=110)
    plt.close(fig)
    # F2 Δ with CI per experiment
    fig, ax = plt.subplots(2, 3, figsize=(15, 8))
    for a, m in zip(ax.flat, ("dn_ipsi", "lc_ipsi", "mid_ipsi", "angle_ss_deg", "dn_peak_0_150", "latency_ms")):
        for exp, col in zip(STEP_EXPS, ("k", "0.5", "tab:green", "tab:orange", "tab:purple", "tab:brown")):
            if exp not in out["experiments"]:
                continue
            e = out["experiments"][exp]
            pl = e["per_level"][m]
            lv = np.array(e["levels"])
            d = np.array([p["delta"] if p.get("delta") is not None else np.nan for p in pl])
            lo = np.array([p["ci95"][0] if p.get("delta") is not None else np.nan for p in pl])
            hi = np.array([p["ci95"][1] if p.get("delta") is not None else np.nan for p in pl])
            a.plot(lv, d, color=col, label=exp)
            a.fill_between(lv, lo, hi, color=col, alpha=0.12)
        a.axhline(0, color="k", lw=0.5)
        if m == "angle_ss_deg":
            a.axhline(0.5, ls=":", color="r"); a.axhline(-0.5, ls=":", color="r")
        a.set_title(f"Δ = control − DATA: {m}")
        a.set_xlabel("LC10a ipsi current [mV]")
    ax[0, 0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(fd, "F2_delta_CI_by_experiment.png"), dpi=110)
    plt.close(fig)
    # F3 thresholds distribution
    fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    for a, t in zip(ax, ("I_lc1", "I_th10_dn", "I_th30_dn")):
        th = out["experiments"]["E1"]["thresholds"][t]
        a.hist(th["per_ctrl"], bins=20, color="0.6")
        a.axvline(th["data_mean"], color="tab:red", lw=2, label="DATA")
        a.set_title(f"E1 {t} [mV] (control instances)")
        a.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(fd, "F3_threshold_distributions.png"), dpi=110)
    plt.close(fig)
    # F4 hysteresis
    if "hysteresis_E4" in out:
        h = out["hysteresis_E4"]
        fig, ax = plt.subplots(1, 2, figsize=(12, 4))
        c = np.array(h["centers"])
        ax[0].plot(c, h["data"]["up"], "r-", label="DATA up")
        ax[0].plot(c, h["data"]["down"], "r--", label="DATA down")
        ax[0].plot(c, h["ctrl_up_mean"], "b-", label="control mean up")
        ax[0].plot(c, h["ctrl_down_mean"], "b--", label="control mean down")
        ax[0].set_xlabel("LC10a ipsi current [mV]"); ax[0].set_ylabel("DNa02 ipsi [Hz]"); ax[0].legend()
        ax[1].hist(h["ctrl"]["mean_abs_610"], bins=20, color="0.6")
        ax[1].axvline(h["data"]["mean_abs_610"], color="r")
        ax[1].set_title("E4 mean |up − down| 6–10 mV [Hz]")
        fig.tight_layout()
        fig.savefig(os.path.join(fd, "F4_hysteresis.png"), dpi=110)
        plt.close(fig)
    # F5 mechanism scatter
    if "mechanism_E1_6_9" in out:
        mm = out["mechanism_E1_6_9"]["per_inst"]
        fig, ax = plt.subplots(1, 3, figsize=(14, 4))
        ax[0].scatter(mm["dLC"], mm["dDN"], s=10); ax[0].set_xlabel("Δ LC10a ipsi [Hz] (6–9 mV)"); ax[0].set_ylabel("Δ DNa02 ipsi [Hz]")
        ax[1].scatter(mm["recip"], mm["dDN"], s=10); ax[1].set_xlabel("LC×LC reciprocal pairs")
        ax[2].scatter(mm["tri"], mm["dDN"], s=10); ax[2].set_xlabel("LC×LC triangles")
        for a in ax:
            a.axhline(0, color="k", lw=0.5)
        fig.tight_layout()
        fig.savefig(os.path.join(fd, "F5_mechanism_scatter.png"), dpi=110)
        plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--run", required=True)
    ap.add_argument("--ctrl-prefix", default="SWS_")
    ap.add_argument("--name", default="analysis.json")
    a = ap.parse_args()
    res = analyze(a.run, a.ctrl_prefix)
    with open(os.path.join(a.run, a.name), "x") as f:
        json.dump(res, f, indent=1, default=float)
    e = res["experiments"]["E1"]
    for k in ("dn_ipsi|6-10", "lc_ipsi|6-10", "mid_ipsi|6-10", "angle_ss_deg|6-10", "dn_ipsi|8-10", "dn_ipsi|6-8"):
        r = e["ranges"].get(k)
        if r and r.get("delta") is not None:
            print(f"E1 {k}: Δ {r['delta']:+.3f} CI [{r['ci95'][0]:+.3f}; {r['ci95'][1]:+.3f}] DATA {r['data']:.2f} ctrl≥DATA {r['frac_ctrl_ge_data']:.2f}")
    for t, v in e["thresholds"].items():
        print(f"E1 {t}: DATA {v['data_mean']:.3f} ctrl {v['ctrl_mean']:.3f} Δ {v['delta']:+.3f} ctrl q {np.round(v['ctrl_q'], 3)}")
