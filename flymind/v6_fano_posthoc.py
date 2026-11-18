"""flymind/v6_fano_posthoc.py — POST-HOC (not pre-registered) LC10a population synchrony per V6 configuration: Fano factor of the
summed ipsilateral LC10a count (10 ms bins, 500–1000 ms), DATA vs SWS (all instances; mean over reps, levels, sides), in two input
ranges: 7–9 mV and DATA's own window. Run: .venv/bin/python -I -B flymind/v6_fano_posthoc.py --run flymind/results/v6 --v41 flymind/results/v5v41
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from v6 import CONFIGS, LV  # noqa: E402

LVa = np.array(LV)


def fano(counts, sel):
    """counts [Lv, 2, R, 100, 6] E1 → mean Fano of LC ipsi population count over selected levels, sides, reps."""
    c = counts[sel].astype(float)
    x = np.concatenate([c[:, 0, :, 50:100, 0], c[:, 1, :, 50:100, 1]], 1)
    m = x.mean(-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return float(np.nanmean(np.where(m > 0, x.var(-1) / m, np.nan)))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--run", required=True)
    ap.add_argument("--v41", required=True)
    a = ap.parse_args()
    A = json.load(open(os.path.join(a.run, "analysis.json")))["openloop"]
    out = {}
    for cfg in CONFIGS:
        if cfg == "D0":
            files = {os.path.basename(p)[:-4]: p for p in glob.glob(os.path.join(a.v41, "raw", "*.npz"))}

            def get(p):
                z = np.load(p)
                return z["E1_counts"][np.isin(np.round(z["E1_levels"], 4), LVa)][:, :, :4]
        else:
            files = {os.path.basename(p)[:-4]: p for p in glob.glob(os.path.join(a.run, "openloop", cfg, "*.npz"))}

            def get(p):
                return np.load(p)["E1_counts"]
        lo, hi = A[cfg]["own_window"]
        ranges = {"7-9": (LVa >= 7) & (LVa <= 9), "own": (LVa >= lo - 1e-9) & (LVa <= hi + 1e-9)}
        e = {}
        for rn, sel in ranges.items():
            d = fano(get(files["DATA"]), sel)
            s = [fano(get(p), sel) for n, p in sorted(files.items()) if n.startswith("SWS_")]
            e[rn] = dict(data=d, sws_mean=float(np.nanmean(s)), sws_min=float(np.nanmin(s)), sws_max=float(np.nanmax(s)), n_sws=len(s),
                         ratio=float(np.nanmean(s) / d) if d else None)
        e["delta_dn_own"] = A[cfg]["families"]["SWS"]["dn|own"]["delta"]
        out[cfg] = e
        print(f"{cfg:9s} Fano 7–9 DATA {e['7-9']['data']:6.1f} SWS {e['7-9']['sws_mean']:6.1f} | own DATA {e['own']['data']:6.1f} "
              f"SWS {e['own']['sws_mean']:6.1f} (ratio {e['own']['ratio'] or float('nan'):.2f}) | ΔDN own {e['delta_dn_own']:+.1f}")
    with open(os.path.join(a.run, "posthoc_lc_fano.json"), "x") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
