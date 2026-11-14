"""RT-C analysis: v6m_analysis.gaps (unchanged, paired hierarchical bootstrap) per configuration. Bootstrap RNG 8 498 230.
Run: .venv/bin/python -I -B flymind/results/v6m/redteam/RT_C/rtc_analysis.py"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
import v6m_analysis as A  # noqa: E402

CONDS = ["REF", "LCIRC", "E1_DN_t0", "E1c_DN_t0", "E3_M0", "E3_MCIRC", "E1b_MID_t0", "E2a_DN_b00"]
res = {}
for cfg in ("D0", "TH8", "BA1", "J025"):
    D = dict(np.load(os.path.join(HERE, "raw", f"{cfg}_DATA.npz")))
    Bs = [dict(np.load(os.path.join(HERE, "raw", f"{cfg}_B1_{k}.npz"))) for k in (8_421_001, 8_421_002, 8_421_003)]
    g = A.gaps(D, Bs, CONDS, np.random.default_rng(8_498_230))
    for c in CONDS:
        for n in ("dn_isi_le4_frac", "mid"):
            g[c][n] = [float(np.nanmean(A.per_rep(D, c, n))), float(np.mean([np.nanmean(A.per_rep(b, c, n)) for b in Bs]))]
        j = list(D["conds"]).index(c)
        g[c]["mid_fano10"] = [float(np.nanmean(D["midsync"][j][..., 2])), float(np.mean([np.nanmean(b["midsync"][j][..., 2]) for b in Bs]))]
        # per-level gap (levels not averaged) for the operating-point check
        dn = list(D["sum_names"]).index("dn")
        g[c]["gap_by_level"] = [float(np.mean([b["summ"][j, li, ..., dn].mean() for b in Bs]) - D["summ"][j, li, ..., dn].mean())
                                for li in range(D["summ"].shape[1])]
    g["_lc_fano10_REF"] = [float(np.nanmean(D["lcsync"][0][..., 2])), float(np.mean([np.nanmean(b["lcsync"][0][..., 2]) for b in Bs]))]
    g["_levels"] = D["levels"].tolist()
    res[cfg] = g
    print(f"== {cfg} levels {g['_levels']}  LC Fano10 REF DATA/B1 {g['_lc_fano10_REF'][0]:.1f}/{g['_lc_fano10_REF'][1]:.1f}")
    for c in CONDS:
        e = g[c]
        Fs = f"F {e['F']:+.2f} ({e['F_ci95'][0]:+.2f};{e['F_ci95'][1]:+.2f}) {e['label']}" if "F" in e else ""
        print(f"  {c:11s} DN {e['dn_data']:6.1f}/{e['dn_b1']:6.1f} gap {e['gap']:+6.1f} ({e['gap_ci95'][0]:+.1f};{e['gap_ci95'][1]:+.1f}) "
              f"rel {e['rel_gap']:+.2f} byLv {[round(x, 1) for x in e['gap_by_level']]} inst {[round(x, 1) for x in e['gap_inst']]} "
              f"isi<=4 {e['dn_isi_le4_frac'][0]:.2f}/{e['dn_isi_le4_frac'][1]:.2f} mid {e['mid'][0]:.1f}/{e['mid'][1]:.1f} "
              f"midF10 {e['mid_fano10'][0]:.1f}/{e['mid_fano10'][1]:.1f}  {Fs}")
with open(os.path.join(HERE, "rtc_analysis.json"), "x") as f:
    json.dump(res, f, indent=1)
