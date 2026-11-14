"""flymind/v5v3.py — V5 v3: izolacja topologii od lateralizacji. PRZYGOTOWANE, NIEURUCHOMIONE (czeka na zatwierdzenie
protokołu validation/v5v3_protocol_DRAFT.md). Pętla, enkoder, dekoder, bezpieczeństwo — loop.run_trial (bez zmian);
sceny — loop_v2.trial_spec_v2 (jak V5 v2), sieć — visual_path.network(0,2), kontrole — side_shuffle / visual_path.

Warunki (5): DATA; SHUF_WITHIN_SIDE v2 — grupy warstwa × strona, 5 zamian/krawędź (ziarno próby + 400 000); SHUF_STR (+ 200 000); TOY_RELAY; P_CTRL.
Znak metryki głównej: d = błąd(DATA) − błąd(kontrola) [°]; d < 0 ⇔ DATA lepsza.
Uruchom (po zatwierdzeniu): .venv/bin/python -I -B flymind/v5v3.py --seeds 3051-3100 --out flymind/results/v5v3
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
from scipy.stats import wilcoxon

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("uruchom z python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CONDS = ("DATA", "SHUF_WITHIN_SIDE", "SHUF_STR", "TOY_RELAY", "P_CTRL")   # protokół: validation/v5v3_protocol_DRAFT.md r3
COMPARISONS = (("H1", "DATA", "SHUF_WITHIN_SIDE"), ("H2", "DATA", "SHUF_STR"), ("H3", "SHUF_WITHIN_SIDE", "SHUF_STR"),
               ("D1", "DATA", "TOY_RELAY"), ("D2", "DATA", "P_CTRL"))
SESOI, ALPHA, N_PERM, N_BOOT, PERM_SEED, BOOT_SEED = 1.0, 0.05, 100_000, 10_000, 3401, 3402
MAX_SIM_ERROR_FRAC = 0.05


# ---------------- statystyka (czysta numpy/scipy; testowana syntetycznie w test_v5v3_analysis.py) ----------------
def perm_test(d, n=N_PERM, seed=PERM_SEED):
    """Test permutacyjny losowych zmian znaku dla średniej różnic w parach, dwustronny; zera zostają w danych."""
    d = np.asarray(d, float)
    rng = np.random.default_rng(seed)
    obs = abs(d.mean())
    sims = np.abs((rng.choice([-1.0, 1.0], size=(n, len(d))) * d).mean(1))
    return float((1 + (sims >= obs - 1e-12).sum()) / (n + 1))


def boot_ci(d, level, n=N_BOOT, seed=BOOT_SEED):
    d = np.asarray(d, float)
    m = d[np.random.default_rng(seed).integers(len(d), size=(n, len(d)))].mean(1)
    a = (1 - level) / 2
    return [float(np.percentile(m, 100 * a)), float(np.percentile(m, 100 * (1 - a)))]


def holm(p):
    p = np.asarray(p, float)
    out, run = np.empty(len(p)), 0.0
    for rank, i in enumerate(np.argsort(p)):
        run = max(run, min(1.0, (len(p) - rank) * p[i]))
        out[i] = run
    return out


def decide(mean, ci95, ci90, p_holm, sesoi=SESOI, alpha=ALPHA):
    """Reguła decyzji ustalona w protokole (d < 0 ⇔ pierwszy warunek lepszy)."""
    if p_holm < alpha and ci95[1] < 0:
        return "pierwszy lepszy, efekt ≥ SESOI" if mean <= -sesoi else "pierwszy lepszy, efekt < SESOI"
    if p_holm < alpha and ci95[0] > 0:
        return "drugi lepszy"
    if -sesoi < ci90[0] and ci90[1] < sesoi:
        return "równoważne w granicach SESOI"
    return "nierozstrzygnięte"


RHO_STRATA = ((0.16, 0.24), (0.24, 0.30), (0.30, 0.3500001))


def analyze(runs):
    """Protokół r3: H1 jedyna główna (α 0,05, bez korekty); H2, H3 — Holm z dwóch; D1, D2 — opis bez korekty i decyzji;
    warstwy ρ (opis); wrażliwość na wykluczenia (d = +max|d| dla wykluczonych ziaren, najgorzej dla pierwszego warunku)."""
    by = {}
    for r in runs:
        by.setdefault(r["cond"], {})[r["seed"]] = r
    seeds = sorted(by["DATA"])
    err_seeds = sorted({r["seed"] for r in runs if r.get("error")})
    ok = [s for s in seeds if s not in err_seeds]                 # wykluczenie sparowane (protokół §6)
    out = dict(n_seeds=len(seeds), excluded_seeds=err_seeds, n_analyzed=len(ok), conds={}, tests={})
    for c in CONDS:
        x = np.array([by[c][s]["final_abs_err"] for s in ok])
        out["conds"][c] = dict(median=round(float(np.median(x)), 3), mean=round(float(x.mean()), 3),
                               success=int(sum(bool(by[c][s]["success"]) for s in seeds)),
                               sim_errors=int(sum(by[c][s].get("error") is not None for s in seeds)))
    rho = np.array([by["DATA"][s]["rho"] for s in ok])
    for h, a, b in COMPARISONS:
        d = np.array([by[a][s]["final_abs_err"] - by[b][s]["final_abs_err"] for s in ok])
        sd = d.std(ddof=1)
        t = dict(first=a, second=b, mean_d=float(d.mean()), median_d=float(np.median(d)), ci95=boot_ci(d, 0.95),
                 ci90=boot_ci(d, 0.90), dz=float(d.mean() / sd) if sd else None, zeros=int((d == 0).sum()),
                 worse_by_gt1=int((d > 1).sum()), better_by_gt1=int((d < -1).sum()), p_perm=perm_test(d),
                 p_wilcoxon_pratt=float(wilcoxon(d, zero_method="pratt").pvalue) if np.any(d) else 1.0,
                 strata={f"{lo:.2f}-{min(hi, 0.35):.2f}": dict(n=int(m.sum()), mean_d=float(d[m].mean()) if m.any() else None,
                                                               ci95=boot_ci(d[m], 0.95) if m.sum() > 1 else None)
                         for lo, hi in RHO_STRATA for m in [(rho >= lo) & (rho < hi)]})
        if err_seeds and h == "H1":
            worst = np.r_[d, np.full(len(err_seeds), np.abs(d).max())]
            t["sensitivity_excluded_as_worst"] = dict(mean_d=float(worst.mean()), ci95=boot_ci(worst, 0.95), p_perm=perm_test(worst))
        out["tests"][h] = t
    out["tests"]["H1"]["p_decision"] = out["tests"]["H1"]["p_perm"]
    for h, ph in zip(("H2", "H3"), holm([out["tests"]["H2"]["p_perm"], out["tests"]["H3"]["p_perm"]])):
        out["tests"][h]["p_decision"] = float(ph)
    for h in ("H1", "H2", "H3"):
        t = out["tests"][h]
        t["decision"] = decide(t["mean_d"], t["ci95"], t["ci90"], t["p_decision"])
    for h in ("D1", "D2"):
        out["tests"][h]["decision"] = "opis (bez decyzji)"
    out["H1_verdict_text"] = ("Hipoteza nie została potwierdzona." if not out["tests"]["H1"]["decision"].startswith("pierwszy lepszy")
                              else "DATA lepsza: " + out["tests"]["H1"]["decision"])
    return out


# ---------------- przebieg (po zatwierdzeniu) ----------------
def run(seeds, out_dir):
    import loop as L
    import loop_v2 as L2
    from side_shuffle import KEYS, layer_side_labels, properties, shuffle_within_side
    from v5v2_topology import check_shuffle, lateralization
    from visual_path import network, shuffle
    pre = L.stage1_hashes()
    if pre["mismatched"]:
        sys.exit(f"PRZERWANIE: Stage 1 niezgodny przed przebiegiem: {pre['mismatched']}")
    t0 = time.perf_counter()
    spec, idx, _ = network(L.J0)
    gr, srep = layer_side_labels(spec, idx)
    li0 = lateralization(spec.W_data, idx)
    toy, tidx, _ = L2.toy_relay(spec, idx)
    cal = dict(slope_snn=json.load(open(os.path.join(HERE, "results", "v4", "v4_partB_v2_20261028T214641.json")))["calib"]["slope_hz_per_rad"],
               slope_p=L.calibrate_p((96, 128)), toy=L2.calibrate_v4v2(toy, tidx))
    runs = []
    for c in CONDS:
        for s in seeds:
            tr = {k: v for k, v in L2.trial_spec_v2(s).items() if k in ("seed", "az0_deg", "rho")}
            kw, cond, base, extra = dict(tr=tr), "snn", (spec, idx), {}
            if c == "SHUF_WITHIN_SIDE":
                sh = shuffle_within_side(spec, gr, s + 400_000)
                p = properties(spec, sh, gr)
                if not all(p[k] for k in KEYS) or not sh.report["shuffle_within_side"]["complete"]:
                    sys.exit(f"PRZERWANIE: SHUF_WITHIN_SIDE ziarno {s}: naruszone {[k for k in KEYS if not p[k]]}")
                base, extra = (sh, idx), dict(li_rel=lateralization(sh.W_data, idx) / li0, changed_frac=p["changed_frac"])
            elif c == "SHUF_STR":
                sh = shuffle(spec, s + 200_000, equal_weight=True)
                check_shuffle(spec, sh, True)
                base, extra = (sh, idx), dict(li_rel=lateralization(sh.W_data, idx) / li0)
            elif c == "TOY_RELAY":
                base, kw["slope"] = (toy, tidx), cal["toy"]["slope"]
            elif c == "P_CTRL":
                cond = "classical_p"
            try:
                r = L.run_trial(cond, s, base, cal, **kw)
                r.update(L.metrics(r))
                err = None
            except L.SimError as e:
                r, err = dict(success=False, final_abs_err=float("nan"), t_first_within=None), str(e)
            runs.append(dict(cond=c, **tr, **extra, success=r["success"], final_abs_err=r["final_abs_err"],
                             t_first_within=r.get("t_first_within"), error=err))
            print(f"{c:17s} {s}: |e| {r['final_abs_err']:6.2f} {r['success']}", flush=True)
            if sum(x["error"] is not None for x in runs) > MAX_SIM_ERROR_FRAC * len(CONDS) * len(seeds) or \
                    sum(x["error"] is not None for x in runs if x["cond"] == c) > 2:
                sys.exit("PRZERWANIE: > 2 błędy symulatora w jednym warunku lub > 5 % wszystkich prób")
    post = L.stage1_hashes()
    res = dict(protocol="V5 v3", seeds=[seeds[0], seeds[-1]], groups=srep, runs=runs, analysis=analyze(runs), stage1_pre=pre,
               stage1_post=post, wall_s=time.perf_counter() - t0, argv=sys.argv,
               code_sha256={f: hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest()
                            for f in ("v5v3.py", "side_shuffle.py", "v5v2_topology.py", "loop.py", "loop_v2.py", "visual_path.py")})
    path = os.path.join(out_dir, f"v5v3_{time.strftime('%Y%m%dT%H%M%S')}.json")
    with open(path, "x") as f:
        json.dump(res, f, ensure_ascii=False, default=str)
    print("zapisano:", path, "| Stage 1 po:", "OK" if not post["mismatched"] else post["mismatched"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--approved-protocol-sha256", required=True,
                    help="sha256 zatwierdzonego protokołu — bez zgodności przebieg odmawia")
    a = ap.parse_args()
    proto = os.path.join(HERE, "validation", "v5v3_protocol.md")
    if not os.path.exists(proto) or hashlib.sha256(open(proto, "rb").read()).hexdigest() != a.approved_protocol_sha256:
        sys.exit("odmowa: brak zatwierdzonego validation/v5v3_protocol.md albo niezgodny sha256")
    lo, hi = map(int, a.seeds.split("-"))
    seeds = list(range(lo, hi + 1))
    import loop as _L
    if set(seeds) & _L.FORBIDDEN or not _L._allowed(a.out):
        sys.exit("odmowa: zabronione ziarna albo --out poza flymind/ i $TMPDIR")
    run(seeds, a.out)
