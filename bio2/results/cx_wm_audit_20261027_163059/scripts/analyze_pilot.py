"""Pilot analysis per stats_plan.md §7 + §9. Usage: analyze_pilot.py RAW.jsonl [RAW2.jsonl ...] OUTDIR
Writes summary_by_condition.csv, paired_contrasts.csv, reconciliation.json, analysis.md."""
import csv, json, os, sys
import numpy as np
import scipy.stats as st

PRIMARY = ["BIO-Static", "BIO-Hybrid", "BIO-NoSelf", "BIO-Shuffle", "LastObs-PD", "Kalman-PD"]
DIAG = ["LastObs-Freeze-Diag", "BIO-Static-Freeze-Diag"]
SEEDS = list(range(100, 130))
CONTRASTS = [  # (role, A, B): D = |e_A| - |e_B|
    ("NI-1", "BIO-Static", "LastObs-PD"), ("NI-2", "BIO-Hybrid", "Kalman-PD"),
    ("mech-self", "BIO-Static", "BIO-NoSelf"), ("mech-velocity", "BIO-Hybrid", "BIO-Static"),
    ("freeze-BIO", "BIO-Static", "BIO-Static-Freeze-Diag"), ("freeze-LastObs", "LastObs-PD", "LastObs-Freeze-Diag"),
    ("freeze-vs-BIOHybrid", "BIO-Hybrid", "BIO-Static-Freeze-Diag"),
    ("context", "Kalman-PD", "LastObs-PD"), ("shuffle-descriptive", "BIO-Static", "BIO-Shuffle"),
]
VALID_FOR_ENDPOINT = ("SUCCESS", "CONTROL_FAILURE")   # e defined & controller functional
rng = np.random.default_rng(20261027)


def boot_ci(x, stat=np.mean, n=10000):
    idx = rng.integers(0, len(x), (n, len(x)))
    b = np.array([stat(x[i]) for i in idx])
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def hl(x):
    w = [(x[i] + x[j]) / 2 for i in range(len(x)) for j in range(i, len(x))]
    return float(np.median(w))


def main():
    *raws, out = sys.argv[1:]
    recs = [json.loads(l) for r in raws for l in open(r)]
    by = {}
    dup = []
    for r in recs:
        key = (r["variant"], r["seed"])
        if key in by:
            dup.append(key)
        by[key] = r
    planned = [(v, s) for v in PRIMARY + DIAG for s in SEEDS]
    missing = [k for k in planned if k not in by]
    recon = dict(n_records=len(recs), n_planned_primary=len(PRIMARY) * len(SEEDS), n_planned_diag=len(DIAG) * len(SEEDS),
                 missing=missing, duplicates=dup,
                 status_counts={v: {s: sum(1 for k in SEEDS if (v, k) in by and by[(v, k)]["status"] == s)
                                    for s in ("SUCCESS", "CONTROL_FAILURE", "DEGENERATE_CALIBRATION", "TECHNICAL_FAILURE")}
                                for v in PRIMARY + DIAG})
    json.dump(recon, open(os.path.join(out, "reconciliation.json"), "w"), indent=1)

    def e_abs(v, s, strict=True):
        r = by.get((v, s))
        if r is None or r.get("e_reappear_deg") is None:
            return np.nan
        if strict and r["status"] not in VALID_FOR_ENDPOINT:
            return np.nan
        return abs(r["e_reappear_deg"])

    rows = []
    for v in PRIMARY + DIAG:
        rs = [by[(v, s)] for s in SEEDS if (v, s) in by]
        a = np.array([e_abs(v, s) for s in SEEDS]); a = a[np.isfinite(a)]
        raw = np.array([abs(r["e_reappear_deg"]) for r in rs if r.get("e_reappear_deg") is not None])
        sg = np.array([r["e_reappear_deg"] for r in rs if r["status"] in VALID_FOR_ENDPOINT])
        tre = [r["t_reacquire"] for r in rs if r["status"] in VALID_FOR_ENDPOINT]
        j = np.array([r["j_ctrl"] for r in rs if r["status"] in VALID_FOR_ENDPOINT])
        ring = np.array([abs(r["e_ring_lastocc_deg"]) for r in rs if r.get("e_ring_lastocc_deg") is not None
                         and (r.get("coh_reappear") or 0) >= 0.2 and r["status"] in VALID_FOR_ENDPOINT])
        onset = np.array([abs(r["e_onset_deg"]) for r in rs if r.get("e_onset_deg") is not None])
        dball = np.array([r["ball_reappear_deg"] - r["ball_onset_deg"] for r in rs if r.get("ball_reappear_deg") is not None])
        daim = np.array([r["aim_reappear_deg"] - r["aim_onset_deg"] for r in rs if r.get("aim_reappear_deg") is not None])
        f = lambda x, fn: (float(fn(x)) if len(x) else None)
        rows.append(dict(
            variant=v, completed=len(rs), n_valid_endpoint=len(a),
            **{k: recon["status_counts"][v][k] for k in recon["status_counts"][v]},
            abs_e_mean=f(a, np.mean), abs_e_sd=f(a, lambda x: np.std(x, ddof=1) if len(x) > 1 else np.nan),
            abs_e_median=f(a, np.median), abs_e_q25=f(a, lambda x: np.percentile(x, 25)), abs_e_q75=f(a, lambda x: np.percentile(x, 75)),
            abs_e_mean_all_records=f(raw, np.mean), signed_e_mean=f(sg, np.mean),
            abs_e_onset_mean=f(onset, np.mean), delta_ball_mean=f(dball, np.mean), delta_aim_mean=f(daim, np.mean),
            t_reacq_n_defined=sum(t is not None for t in tre), t_reacq_median=(float(np.median([t for t in tre if t is not None])) if any(t is not None for t in tre) else None),
            j_ctrl_mean=f(j, np.mean), j_ctrl_n_zero=int((j == 0).sum()) if len(j) else 0,
            abs_e_ring_mean=f(ring, np.mean), n_ring_valid=len(ring),
            n_fallback=sum(bool(r.get("fallback_used")) for r in rs)))
    with open(os.path.join(out, "summary_by_condition.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    crow = []
    for role, A, Bv in CONTRASTS:
        strict = role != "shuffle-descriptive"
        d = np.array([e_abs(A, s) - e_abs(Bv, s, strict) for s in SEEDS]); d = d[np.isfinite(d)]
        n = len(d)
        if n < 3:
            crow.append(dict(role=role, A=A, B=Bv, n_pairs=n)); continue
        m, sd = float(d.mean()), float(d.std(ddof=1)); se = sd / np.sqrt(n)
        tc = st.t.ppf(0.975, n - 1)
        bl, bh = boot_ci(d)
        h = hl(d)
        hb = boot_ci(d, hl, n=2000)
        wil = st.wilcoxon(d) if np.any(d != 0) else None
        crow.append(dict(role=role, A=A, B=Bv, n_pairs=n, mean_D=m, sd_D=sd, t_ci95_lo=m - tc * se, t_ci95_hi=m + tc * se,
                         t_upper95_onesided=m + st.t.ppf(0.95, n - 1) * se, boot_ci95_lo=bl, boot_ci95_hi=bh,
                         hl=h, hl_boot_lo=hb[0], hl_boot_hi=hb[1], wilcoxon_p=(float(wil.pvalue) if wil else None),
                         frac_D_below_3=float((d < 3).mean()), frac_A_better=float((d < 0).mean())))
    keys = sorted({k for r in crow for k in r}, key=lambda k: list(crow[0]).index(k) if k in crow[0] else 99)
    with open(os.path.join(out, "paired_contrasts.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(crow)

    fmt = lambda x: "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else (f"{x:.2f}" if isinstance(x, float) else str(x))
    with open(os.path.join(out, "analysis.md"), "w") as fh:
        fh.write("# Pilot analysis (exploratory; seeds 100–129, t_occ = 1.0 s)\n\n## Reconciliation\n\n")
        fh.write(f"records {len(recs)}; planned primary {recon['n_planned_primary']} + diagnostic {recon['n_planned_diag']}; "
                 f"missing {len(missing)}; duplicates {len(dup)}\n\n## Per condition\n\n")
        cols = ["variant", "completed", "SUCCESS", "CONTROL_FAILURE", "DEGENERATE_CALIBRATION", "TECHNICAL_FAILURE", "n_valid_endpoint",
                "abs_e_mean", "abs_e_sd", "abs_e_median", "abs_e_q25", "abs_e_q75", "signed_e_mean", "abs_e_mean_all_records", "abs_e_onset_mean",
                "delta_ball_mean", "delta_aim_mean", "t_reacq_n_defined", "j_ctrl_mean", "j_ctrl_n_zero", "abs_e_ring_mean", "n_ring_valid"]
        fh.write("| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
        for r in rows:
            fh.write("| " + " | ".join(fmt(r[c]) for c in cols) + " |\n")
        fh.write("\n## Paired contrasts D = |e_A| − |e_B| (deg; negative = A better)\n\n")
        cols = ["role", "A", "B", "n_pairs", "mean_D", "sd_D", "t_ci95_lo", "t_ci95_hi", "t_upper95_onesided", "boot_ci95_lo", "boot_ci95_hi",
                "hl", "hl_boot_lo", "hl_boot_hi", "wilcoxon_p", "frac_A_better"]
        fh.write("| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
        for r in crow:
            fh.write("| " + " | ".join(fmt(r.get(c)) for c in cols) + " |\n")
    print(open(os.path.join(out, "analysis.md")).read())


if __name__ == "__main__":
    main()
