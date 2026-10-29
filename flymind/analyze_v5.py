"""flymind/analyze_v5.py — analiza przebiegu V5 (pętla zamknięta) wg validation/v5_confirm_protocol.md.
Czysty odczyt JSON z loop.py; nic nie symuluje. Uruchom: python -I -B flymind/analyze_v5.py WYNIK.json"""
import json
import sys

import numpy as np
from scipy.stats import binomtest


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(float(c - h), 3), round(float(c + h), 3)]


def mcnemar_greater(a, b):
    """Para prób (te same ziarna): a sukces ∧ ¬b vs ¬a ∧ b; dokładny jednostronny test dwumianowy (a > b)."""
    n10 = int(np.sum(a & ~b))
    n01 = int(np.sum(~a & b))
    return dict(a_only=n10, b_only=n01, p=float(binomtest(n10, n10 + n01, 0.5, "greater").pvalue) if n10 + n01 else 1.0)


def boot_diff(x, y, seed=2201, n=10000):
    """Sparowany bootstrap różnicy średnich x − y (po ziarnach)."""
    d = np.asarray(x) - np.asarray(y)
    rng = np.random.default_rng(seed)
    m = d[rng.integers(len(d), size=(n, len(d)))].mean(1)
    return dict(mean=round(float(d.mean()), 3), ci95=[round(float(v), 3) for v in np.percentile(m, [2.5, 97.5])])


def analyze(res, alpha=0.05 / 3):
    runs = res["runs"]
    by = {}
    for r in runs:
        by.setdefault((r["cond"], r["delay_k"]), {})[r["seed"]] = r
    seeds = sorted(by[("snn", 0)])
    S = lambda c, k=0: np.array([by[(c, k)][s]["success"] for s in seeds])
    F = lambda c, k=0: np.array([by[(c, k)][s]["final_abs_err"] for s in seeds])
    out = dict(n=len(seeds), conds={})
    for (c, k), d in sorted(by.items()):
        x = np.array([d[s]["success"] for s in seeds])
        t = [d[s]["t_first_within"] for s in seeds if d[s]["t_first_within"] is not None]
        out["conds"][f"{c}|delay{k * 10}ms"] = dict(
            success=int(x.sum()), rate=round(float(x.mean()), 3), wilson95=wilson(int(x.sum()), len(x)),
            final_abs_err_median=round(float(np.median([d[s]["final_abs_err"] for s in seeds])), 2),
            t_first_within_median=round(float(np.median(t)), 2) if t else None,
            t_within_2s=int(sum(1 for s in seeds if d[s]["t_first_within"] is not None and d[s]["t_first_within"] <= 2.0)),
            overshoot_median=round(float(np.median([d[s]["overshoot_deg"] for s in seeds])), 2),
            safety_flagged_ticks_total=int(sum(d[s]["safety_ticks_flagged"] for s in seeds)),
            signed_final_e_mean=round(float(np.mean([np.mean(d[s]["e_deg"][-50:]) * np.sign(d[s]["az0_deg"]) for s in seeds])), 2))
    snn = S("snn")
    out["H1_snn_rate_ge_0.8_lowerCI_gt_0.6"] = bool(snn.mean() >= 0.8 and wilson(int(snn.sum()), len(snn))[0] > 0.6)
    out["H2_snn_vs_shuffle"] = mcnemar_greater(snn, S("snn_shuffle"))
    out["H3_snn_vs_swap"] = mcnemar_greater(snn, S("snn_swap"))
    out["H4_snn_vs_no_vision"] = mcnemar_greater(snn, S("no_vision"))
    for h in ("H2_snn_vs_shuffle", "H3_snn_vs_swap", "H4_snn_vs_no_vision"):
        out[h]["pass"] = out[h]["p"] < alpha
    sw = [np.mean(by[("snn_swap", 0)][s]["e_deg"][-50:]) * np.sign(by[("snn_swap", 0)][s]["az0_deg"]) for s in seeds]
    away = np.array(sw) > np.abs([by[("snn_swap", 0)][s]["az0_deg"] for s in seeds])   # błąd urósł w stronę startu
    out["H3b_swap_turns_away"] = dict(frac_away=round(float(away.mean()), 3), pass_=bool(away.mean() >= 0.8))
    out["desc_classical_minus_snn_final_abs_err"] = boot_diff(F("classical_p"), F("snn"))
    return out


if __name__ == "__main__":
    print(json.dumps(analyze(json.load(open(sys.argv[1]))), indent=1, ensure_ascii=False))
