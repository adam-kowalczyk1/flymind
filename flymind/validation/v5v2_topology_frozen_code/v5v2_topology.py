"""flymind/v5v2_topology.py — V5 v2 (topologia): czy szczegółowa topologia connectomu daje powtarzalną korzyść w sterowaniu
SO-101 ponad lateralizację, prosty przekaźnik i regulator P? Protokół: validation/v5v2_topology_protocol.md (zamrożony
przed przebiegiem). Pętla, enkoder, dekoder, bezpieczeństwo, symulator — loop.run_trial (bez zmian).

Warunki (dokładnie 9; etykiety: DATA = z connectomu, MODEL = założenie obliczeniowe, ENGINEERING = robot/symulator):
  DATA            sieć z danych (visual_path, J0 0,2)                                         DATA + MODEL(J0, ALIF, znak Glu)
  SHUF_DEG        shuffle(equal_weight=False): stopnie we/wy, siła WYJŚCIOWA, znak zachowane    MODEL (kontrola)
  SHUF_STR        shuffle(equal_weight=True): jw. + siła WEJŚCIOWA każdego neuronu zachowana   MODEL (kontrola)
  CUT_LC10a_AOTU  wyzerowane krawędzie LC10a → neurony typu AOTU* (w tym AOTU019); bez renormalizacji  MODEL (ablacja)
  ABL_AOTU019     2 neurony AOTU019 usunięte (wiersze i kolumny = 0); bez renormalizacji     MODEL (ablacja)
  TOY_RELAY       loop_v2.toy_relay: LC10a → DNa02 ipsilateralnie, krawędzie modelowe, własna kalibracja V4 v2   MODEL
  P_CTRL          regulator P na gL − gR (omija SNN)                                           ENGINEERING
  NO_VISION       klatki bez obrazu                                                            ENGINEERING (kontrola)
  SWAP            sieć z danych, napęd LC10a stron zamieniony                                  MODEL (kontrola)
Dekoder: dla wszystkich wariantów SNN poza TOY_RELAY — dekoder sieci z danych (slope V4 v2), „zmieniamy sieć, nie odczyt”.
Zadanie: loop_v2.trial_spec_v2 (az0 ~ U(−30°, 30°), ρ ~ U[0,16; 0,35]), bez dystraktora. Ziarna tasowań: SHUF_DEG ziarno
próby + 100 000, SHUF_STR + 200 000.
Uruchom: .venv/bin/python -I -B flymind/v5v2_topology.py --seeds 3001-3050 --out flymind/results/v5v2_topology
         analiza: --analyze WYNIK.json ;  sama weryfikacja kontroli: --verify-only
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import binomtest, wilcoxon

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("uruchom z python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import loop as L  # noqa: E402
import loop_v2 as L2  # noqa: E402
from snn_interface import SNNSpec  # noqa: E402
from visual_path import ANN, network, shuffle  # noqa: E402

CONDS = ("DATA", "SHUF_DEG", "SHUF_STR", "CUT_LC10a_AOTU", "ABL_AOTU019", "TOY_RELAY", "P_CTRL", "NO_VISION", "SWAP")
CALIB = os.path.join(HERE, "results", "v4", "v4_partB_v2_20261028T214641.json")


def types(spec):
    return pd.read_feather(ANN, columns=["bodyId", "type"]).set_index("bodyId").type.reindex(spec.bodies).astype(str).to_numpy()


def cut_lc_aotu(spec, idx):
    t = types(spec)
    aotu = np.flatnonzero(np.char.startswith(t.astype(str), "AOTU"))
    lc = np.r_[idx["in_L"], idx["in_R"]]
    W = spec.W_data.copy()
    W[np.ix_(aotu, lc)] = 0.0
    return SNNSpec(spec.bodies, spec.nt, spec.sign, W, spec.W_model.copy(), {}), aotu, lc


def abl_aotu019(spec):
    t = types(spec)
    k = np.flatnonzero(t == "AOTU019")
    W = spec.W_data.copy()
    W[k, :] = 0.0
    W[:, k] = 0.0
    return SNNSpec(spec.bodies, spec.nt, spec.sign, W, spec.W_model.copy(), {}), k


def lateralization(W, idx):
    """Znakowany napęd LC10a → DNa02 (ścieżki 1- i 2-skokowe, W[post, pre]): Σ_s [ipsi − kontra] [mV²/spike²].
    Miara opisowa (weryfikacja kontroli), nie hipoteza."""
    E = W @ W + W
    li = 0.0
    for s, o in (("L", "R"), ("R", "L")):
        lc = idx[f"in_{s}"]
        li += E[np.ix_(idx[f"DNa02_{s}"], lc)].sum() - E[np.ix_(idx[f"DNa02_{o}"], lc)].sum()
    return float(li)


def check_shuffle(spec, sh, strength):
    """Asercje własności tasowania; zwraca liczby. Błąd = przerwanie (kontrola nie testowałaby hipotezy)."""
    A, B = spec.W_data != 0, sh.W_data != 0
    r = dict(edges=int(A.sum()), edges_after=int(B.sum()), changed_edges=int((A & ~B).sum()),
             in_deg=bool((A.sum(1) == B.sum(1)).all()), out_deg=bool((A.sum(0) == B.sum(0)).all()),
             out_strength=bool(np.allclose(spec.W_data.sum(0), sh.W_data.sum(0))),
             in_strength=bool(np.allclose(spec.W_data.sum(1), sh.W_data.sum(1))),
             dale=bool(((sh.W_data * spec.sign[None, :]) >= 0).all()), no_autapse=bool(not np.diag(sh.W_data).any()),
             weight_multiset=bool(np.array_equal(np.sort(spec.W_data[A]), np.sort(sh.W_data[B]))))
    need = ["in_deg", "out_deg", "out_strength", "dale", "no_autapse", "weight_multiset"] + (["in_strength"] if strength else [])
    bad = [k for k in need if not r[k]]
    if bad or r["edges"] != r["edges_after"] or r["changed_edges"] == 0:
        raise AssertionError(f"tasowanie ({'siła' if strength else 'stopnie'}) łamie {bad or 'liczbę krawędzi/brak zmian'}")
    return r


def verify():
    """Zadanie 1–2: weryfikacja wszystkich kontroli i ablacji z liczbami (deterministyczna)."""
    spec, idx, rep = network(L.J0)
    out = dict(network=dict(neurons=len(spec.bodies), edges=int((spec.W_data != 0).sum()), synapses=rep["build"]["data"]["synapses"],
                            W_model_edges=int((spec.W_model != 0).sum()), groups={k: len(v) for k, v in idx.items()}))
    v4 = json.load(open(CALIB))
    out["decoder"] = dict(slope_file=v4["calib"]["slope_hz_per_rad"], recalibrated=L2.calibrate_v4v2(spec, idx))
    assert abs(out["decoder"]["recalibrated"]["slope"] - out["decoder"]["slope_file"]) < 1e-9, "kalibracja nie odtwarza się"
    li0 = lateralization(spec.W_data, idx)
    out["network"]["lateralization_index"] = round(li0, 1)
    for name, st, off in (("SHUF_DEG", False, 100_000), ("SHUF_STR", True, 200_000)):
        out[name] = []
        for s in (3001, 3002, 3003):
            sh = shuffle(spec, s + off, equal_weight=st)
            out[name].append(dict(check_shuffle(spec, sh, st), lateralization_rel=round(lateralization(sh.W_data, idx) / li0, 3)))
    c, aotu, lc = cut_lc_aotu(spec, idx)
    diff = spec.W_data != c.W_data
    blk = np.zeros_like(diff)
    blk[np.ix_(aotu, lc)] = True
    out["CUT_LC10a_AOTU"] = dict(aotu_neurons=len(aotu), aotu_types=pd.Series(types(spec)[aotu]).value_counts().to_dict(),
                                 edges_removed=int(diff.sum()), synapses_removed=int(round(np.abs(spec.W_data[diff]).sum() / L.J0)),
                                 lc_out_edges_before=int((spec.W_data[:, lc] != 0).sum()),
                                 changes_only_in_block=bool(not (diff & ~blk).any()),
                                 remaining_edges=int((c.W_data != 0).sum()), renormalized=False)
    assert out["CUT_LC10a_AOTU"]["changes_only_in_block"] and out["CUT_LC10a_AOTU"]["edges_removed"] > 0
    a, k = abl_aotu019(spec)
    d2 = spec.W_data != a.W_data
    rows_cols = np.zeros_like(d2)
    rows_cols[k, :] = rows_cols[:, k] = True
    out["ABL_AOTU019"] = dict(neurons=k.tolist(), bodyIds=[int(spec.bodies[i]) for i in k], edges_removed=int(d2.sum()),
                              in_edges=int((spec.W_data[k, :] != 0).sum()), out_edges=int((spec.W_data[:, k] != 0).sum()),
                              changes_only_in_rows_cols=bool(not (d2 & ~rows_cols).any()), remaining_edges=int((a.W_data != 0).sum()),
                              renormalized=False)
    assert len(k) == 2 and out["ABL_AOTU019"]["changes_only_in_rows_cols"]
    assert out["ABL_AOTU019"]["remaining_edges"] == out["network"]["edges"] - out["ABL_AOTU019"]["edges_removed"]
    toy, tidx, trep = L2.toy_relay(spec, idx)
    out["TOY_RELAY"] = dict(trep, neurons=len(toy.bodies), W_data_edges=int((toy.W_data != 0).sum()),
                            W_model_edges=int((toy.W_model != 0).sum()), calib=L2.calibrate_v4v2(toy, tidx))
    assert out["TOY_RELAY"]["W_data_edges"] == 0 and out["TOY_RELAY"]["W_model_edges"] == 275 and not out["TOY_RELAY"]["calib"]["refused"]
    out["SWAP"] = dict(in_L=len(idx["in_L"]), in_R=len(idx["in_R"]), note="loop.run_trial: cond 'snn_swap' zamienia indeksy prądu, sieć bez zmian")
    return out, (spec, idx, toy, tidx)


def run(seeds, out_dir):
    pre = L.stage1_hashes()
    if pre["mismatched"]:
        sys.exit(f"Stage 1 niezgodny PRZED: {pre['mismatched']}")
    t0 = time.perf_counter()
    ver, (spec, idx, toy, tidx) = verify()
    print("weryfikacja OK:", json.dumps({k: ver[k] for k in ("CUT_LC10a_AOTU", "ABL_AOTU019")}, default=str), flush=True)
    cal = dict(slope_snn=ver["decoder"]["slope_file"], slope_p=L.calibrate_p((96, 128)))
    cut = cut_lc_aotu(spec, idx)[0]
    abl = abl_aotu019(spec)[0]
    runs = []
    for c in CONDS:
        for s in seeds:
            tr = {k: v for k, v in L2.trial_spec_v2(s).items() if k in ("seed", "az0_deg", "rho")}
            kw, cond, base, li = dict(tr=tr), "snn", (spec, idx), None
            if c == "SHUF_DEG":
                sh = shuffle(spec, s + 100_000)
                check_shuffle(spec, sh, False)
                base, li = (sh, idx), lateralization(sh.W_data, idx) / lateralization(spec.W_data, idx)
            elif c == "SHUF_STR":
                sh = shuffle(spec, s + 200_000, equal_weight=True)
                check_shuffle(spec, sh, True)
                base, li = (sh, idx), lateralization(sh.W_data, idx) / lateralization(spec.W_data, idx)
            elif c == "CUT_LC10a_AOTU":
                base = (cut, idx)
            elif c == "ABL_AOTU019":
                base = (abl, idx)
            elif c == "TOY_RELAY":
                base, kw["slope"] = (toy, tidx), ver["TOY_RELAY"]["calib"]["slope"]
            elif c == "P_CTRL":
                cond = "classical_p"
            elif c == "NO_VISION":
                cond = "no_vision"
            elif c == "SWAP":
                cond = "snn_swap"
            try:
                r = L.run_trial(cond, s, base, cal, **kw)
                r.update(L.metrics(r))
                e = np.array(r["e_deg"])
                r["osc_half_amp"] = float((e[-100:].max() - e[-100:].min()) / 2)
            except L.SimError as err:
                r = dict(error=str(err), success=False, final_abs_err=float("nan"), t_first_within=None, overshoot_deg=float("nan"),
                         osc_half_amp=float("nan"), safety_ticks_flagged=0)
            runs.append(dict(cond=c, **tr, lateralization_rel=li, **{k: r.get(k) for k in ("success", "final_abs_err", "t_first_within", "overshoot_deg",
                                                                     "osc_half_amp", "safety_ticks_flagged", "error")}))
            print(f"{c:15s} {s}: az0 {tr['az0_deg']:+6.1f} ρ {tr['rho']:.3f} → |e| {r['final_abs_err']:6.2f} {r['success']}", flush=True)
    post = L.stage1_hashes()
    res = dict(protocol="V5 v2 topology", seeds=[seeds[0], seeds[-1]], verification=ver, runs=runs, stage1_pre=pre, stage1_post=post,
               wall_s=time.perf_counter() - t0, argv=sys.argv,
               code_sha256={f: hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest()
                            for f in ("v5v2_topology.py", "loop.py", "loop_v2.py", "v4_open_loop.py", "visual_path.py", "so101.py",
                                      "encoder.py", "alif.py", "decoder.py", "safety.py", "snn_interface.py", "sensory.py")})
    path = os.path.join(out_dir, f"v5v2_topology_{time.strftime('%Y%m%dT%H%M%S')}.json")
    with open(path, "x") as f:
        json.dump(res, f, ensure_ascii=False, default=str)
    print("zapisano:", path, "| Stage 1 po:", "OK" if not post["mismatched"] else post["mismatched"])
    return path


def holm(p):
    """Holm–Bonferroni: skorygowane p (monotoniczne), kolejność wejścia zachowana."""
    order = np.argsort(p)
    adj, run = np.empty(len(p)), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(p) - rank) * p[i]))
        adj[i] = run
    return adj


def analyze(res, n_boot=10000, seed=3301):
    by = {}
    for r in res["runs"]:
        by.setdefault(r["cond"], {})[r["seed"]] = r
    seeds = sorted(by["DATA"])
    col = lambda c, k: np.array([np.nan if by[c][s][k] is None else by[c][s][k] for s in seeds], float)
    base = col("DATA", "final_abs_err")
    B = np.random.default_rng(seed).integers(len(seeds), size=(n_boot, len(seeds)))
    out = dict(n=len(seeds), conds={}, comparisons={})
    for c in CONDS:
        x, sc = col(c, "final_abs_err"), col(c, "success").astype(bool)
        t = col(c, "t_first_within")
        k = int(sc.sum())
        lo, hi = L2.L_wilson(k, len(sc))
        out["conds"][c] = dict(final_err_median=round(float(np.nanmedian(x)), 2), final_err_mean=round(float(np.nanmean(x)), 2),
                               success=f"{k}/{len(sc)}", success_wilson95=[round(lo, 3), round(hi, 3)],
                               t_within_median=round(float(np.nanmedian(t)), 2) if np.isfinite(t).any() else None,
                               osc_half_amp_median=round(float(np.nanmedian(col(c, "osc_half_amp"))), 2),
                               safety_flagged_ticks=int(np.nansum(col(c, "safety_ticks_flagged"))),
                               errors=int(sum(by[c][s].get("error") is not None for s in seeds)))
    comps = [c for c in CONDS if c != "DATA"]
    ps = []
    for c in comps:
        d = col(c, "final_abs_err") - base
        nz = d[d != 0]
        p = float(wilcoxon(d[d != 0]).pvalue) if len(nz) else 1.0
        ps.append(p)
        rk = pd.Series(np.abs(nz)).rank().to_numpy()
        rbc = float((rk[nz > 0].sum() - rk[nz < 0].sum()) / rk.sum()) if len(nz) else 0.0
        bm = d[B].mean(1)
        a, b = col(c, "success").astype(bool), col("DATA", "success").astype(bool)
        n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
        out["comparisons"][c] = dict(mean_diff_deg=round(float(d.mean()), 3), ci95=[round(float(v), 3) for v in np.percentile(bm, [2.5, 97.5])],
                                     median_diff_deg=round(float(np.median(d)), 3), cohen_dz=round(float(d.mean() / d.std(ddof=1)), 3) if d.std(ddof=1) else None,
                                     rank_biserial=round(rbc, 3), wilcoxon_p=p,
                                     success_pairs_variant_only_vs_data_only=[n10, n01],
                                     success_mcnemar_p_uncorrected=float(binomtest(n10, n10 + n01, 0.5).pvalue) if n10 + n01 else 1.0)
    for c, pa in zip(comps, holm(np.array(ps))):
        out["comparisons"][c]["wilcoxon_p_holm"] = float(pa)
    h1 = out["comparisons"]["SHUF_STR"]
    out["H1_confirmed"] = bool(h1["wilcoxon_p_holm"] < 0.05 and h1["mean_diff_deg"] > 0 and h1["ci95"][0] > 0)
    from scipy.stats import spearmanr
    li = col("SHUF_STR", "lateralization_rel")
    rho_, p_ = spearmanr(li, col("SHUF_STR", "final_abs_err"))
    out["aux_SHUF_STR_lateralization_vs_error"] = dict(spearman_rho=round(float(rho_), 3), p=float(p_),
                                                       li_range=[round(float(np.nanmin(li)), 3), round(float(np.nanmax(li)), 3)])
    dc, ds = col("CUT_LC10a_AOTU", "final_abs_err") - base, col("SHUF_STR", "final_abs_err") - base
    ratio = dc[B].mean(1) / ds[B].mean(1)
    out["mechanism"] = dict(cut_deficit_deg=round(float(dc.mean()), 3), shuffle_str_deficit_deg=round(float(ds.mean()), 3),
                            share_explained=round(float(dc.mean() / ds.mean()), 3) if ds.mean() else None,
                            share_ci95=[round(float(v), 3) for v in np.nanpercentile(ratio, [2.5, 97.5])],
                            unexplained=round(float(1 - dc.mean() / ds.mean()), 3) if ds.mean() else None)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--seeds")
    ap.add_argument("--out")
    ap.add_argument("--analyze")
    ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args()
    if a.analyze:
        print(json.dumps(analyze(json.load(open(a.analyze))), indent=1, ensure_ascii=False))
    elif a.verify_only:
        print(json.dumps(verify()[0], indent=1, ensure_ascii=False, default=str))
    else:
        lo, hi = map(int, a.seeds.split("-"))
        seeds = list(range(lo, hi + 1))
        if set(seeds) & L.FORBIDDEN or not a.out or not L._allowed(a.out):
            sys.exit("odmowa: zabronione ziarna albo --out poza flymind/ i $TMPDIR")
        run(seeds, a.out)
