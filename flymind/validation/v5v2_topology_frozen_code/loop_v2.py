"""flymind/loop_v2.py — V5 wersja 2: czy w pętli orientacji liczy się topologia z danych PONAD lateralizację?
Protokół: validation/v5_v2_protocol.md (zamrożony przed przebiegiem; hashe w v5_v2_manifest.json). Pętla, enkoder,
dekoder, warstwa bezpieczeństwa i symulator — z loop.py (run_trial); tu tylko warianty sieci, zadanie v2 i analiza.

Warianty sieci (ten sam enkoder, ten sam takt; dekoder: patrz `slope`):
  snn             sieć z danych (visual_path, J0 0,2), dekoder V4 v2 (slope 495,6 Hz/rad)
  snn_eqshuffle   visual_path.shuffle(equal_weight=True), ziarno próby + 100 000 — zachowana siła wejścia i wyjścia
                  każdego neuronu, znak (Dale), stopnie; dekoder sieci z danych
  snn_dnperm      wejścia DNa02 L/R przypisane losowym neuronom presynaptycznym tego samego znaku (bez DNa02),
                  ziarno próby + 200 000 — zachowana siła wejścia DNa02, zniszczona lateralizacja; dekoder sieci z danych
  toy_relay       tylko krawędzie modelowe: każdy LC10a → DNa02 tej samej strony, n_syn = (suma pobudzających synaps
                  do DNa02 tej strony w sieci z danych) / liczba LC10a tej strony; własna kalibracja procedurą V4 v2
  classical_p     regulator P na gL − gR (jak V5 v1)
  no_vision       klatki bez obrazu (poziom przypadku: |az0| < 5° wygrywa bez ruchu)
  snn_distr, p_distr  jak snn / classical_p, plus mniejsza zielona kula (r 1,25 cm) po przeciwnej stronie
Uruchom: .venv/bin/python -I -B flymind/loop_v2.py --seeds 2051-2100 --out flymind/results/v5   (analiza: --analyze PLIK)
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import binomtest

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("uruchom z python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import loop as L  # noqa: E402
import v4_open_loop as V4  # noqa: E402
from snn_interface import ModelEdge, ModelParams, SNNSpec, build  # noqa: E402
from so101 import SceneCfg, SimError  # noqa: E402
from visual_path import NTS, network, shuffle  # noqa: E402

CONDS = ("snn", "snn_eqshuffle", "snn_dnperm", "toy_relay", "classical_p", "no_vision", "snn_distr", "p_distr")
DISTR_R, TOL = 0.0125, 5.0
RHO_BINS = (0.16, 0.24, 0.30, 0.35)


def trial_spec_v2(seed):
    rng = np.random.default_rng(seed)
    az0, rho = rng.uniform(-30, 30), rng.uniform(0.16, 0.35)
    daz, drho = -math.copysign(1, az0) * rng.uniform(15, 30), rng.uniform(0.16, 0.35)
    return dict(seed=seed, az0_deg=float(az0), rho=float(rho), distr_az_deg=float(daz), distr_rho=float(drho))


def dn_permute(spec, idx, seed):
    """Wiersze DNa02: każda waga przeniesiona na losowy neuron presynaptyczny tego samego znaku (bez DNa02)."""
    rng = np.random.default_rng(seed)
    Wd = spec.W_data.copy()
    dn = np.r_[idx["DNa02_L"], idx["DNa02_R"]]
    pool = {s: np.setdiff1d(np.flatnonzero(spec.sign == s), dn) for s in (1.0, -1.0)}
    for i in dn:
        row = spec.W_data[i]
        new = np.zeros_like(row)
        for s in (1.0, -1.0):
            j = np.flatnonzero(np.sign(row) == s)
            new[rng.choice(pool[s], len(j), replace=False)] = row[j]
        Wd[i] = new
    return SNNSpec(spec.bodies, spec.nt, spec.sign, Wd, spec.W_model.copy(), dict(spec.report, dn_permute=seed))


def toy_relay(spec, idx):
    """Przekaźnik ipsilateralny z krawędzi modelowych (reguła rozmiaru w nagłówku). Zwraca (spec, idx, raport)."""
    bodies = spec.bodies
    lc = {s: [int(bodies[i]) for i in idx[f"in_{s}"]] for s in "LR"}
    dn = {s: int(bodies[idx[f"DNa02_{s}"][0]]) for s in "LR"}
    me, nsyn = [], {}
    for s in "LR":
        row = spec.W_data[idx[f"DNa02_{s}"][0]]
        nsyn[s] = float(row[row > 0].sum() / L.J0 / len(lc[s]))
        me += [ModelEdge(b, dn[s], nsyn[s], "V5 v2 toy relay: LC10a → ipsilateralny DNa02 (kontrola modelowa)") for b in lc[s]]
    tb = lc["L"] + lc["R"] + [dn["L"], dn["R"]]
    empty = pd.DataFrame(dict(body_pre=pd.Series([], dtype="int64"), body_post=pd.Series([], dtype="int64"),
                              weight=pd.Series([], dtype="int64")))
    t = build(empty, tb, pd.read_feather(NTS), ModelParams(J0=L.J0), model_edges=me)
    pos = {b: i for i, b in enumerate(tb)}
    tidx = {"in_L": np.array([pos[b] for b in lc["L"]]), "in_R": np.array([pos[b] for b in lc["R"]]),
            "DNa02_L": np.array([pos[dn["L"]]]), "DNa02_R": np.array([pos[dn["R"]]])}
    return t, tidx, dict(n_syn_per_edge=nsyn, edges=len(me))


def calibrate_v4v2(spec, idx):
    """Procedura kalibracji V4 v2: offset = L−P przy pustym obrazie, slope MNK przez ten punkt; ≤ 2 Hz/rad → odmowa."""
    V4.V.update(V4.VERSION[2])
    X = np.repeat(np.radians(V4.CAL_AZ), len(V4.CAL_SEEDS))
    Y = np.array([V4.static_diff(spec, idx, s, V4.spot(a)) for a in V4.CAL_AZ for s in V4.CAL_SEEDS])
    blank = np.full((*V4.SHAPE, 3), V4.BG, np.uint8)
    off = float(np.mean([V4.static_diff(spec, idx, s, blank) for s in V4.CAL_SEEDS]))
    slope = float(((Y - off) * X).sum() / (X * X).sum())
    return dict(offset=off, slope=slope, refused=bool(slope <= V4.MIN_SLOPE))


def run(seeds, out, calib_file):
    pre = L.stage1_hashes()
    if pre["mismatched"]:
        sys.exit(f"Stage 1 niezgodny PRZED: {pre['mismatched']}")
    v4 = json.load(open(calib_file))
    if v4.get("version") != 2 or v4["J0"] != L.J0 or not v4["calib"]["slope_hz_per_rad"] > 0:
        sys.exit("--calib: oczekiwano V4 v2, J0 0,2, slope > 0")
    t0 = time.perf_counter()
    spec, idx, rep = network(L.J0)
    toy, tidx, toyrep = toy_relay(spec, idx)
    cal = dict(slope_snn=v4["calib"]["slope_hz_per_rad"], slope_p=L.calibrate_p(SceneCfg().cam_shape),
               toy=calibrate_v4v2(toy, tidx), data_recheck=calibrate_v4v2(spec, idx))
    print("kalibracja:", json.dumps(cal), flush=True)
    dcfg = SceneCfg(distractor_r=DISTR_R)
    runs = []
    for c in CONDS:
        for s in seeds:
            tr = trial_spec_v2(s)
            kw = dict(tr={k: tr[k] for k in ("seed", "az0_deg", "rho")})
            base = (spec, idx)
            cond = {"snn_eqshuffle": "snn", "snn_dnperm": "snn", "toy_relay": "snn", "snn_distr": "snn",
                    "p_distr": "classical_p"}.get(c, c)
            if c == "snn_eqshuffle":
                base = (shuffle(spec, s + 100_000, equal_weight=True), idx)
            elif c == "snn_dnperm":
                base = (dn_permute(spec, idx, s + 200_000), idx)
            elif c == "toy_relay":
                base, kw["slope"] = (toy, tidx), cal["toy"]["slope"]
            if c in ("snn_distr", "p_distr"):
                probe = L.SO101Sim(dcfg, render=False)
                d = L.place_ball(probe, math.radians(tr["distr_az_deg"]), tr["distr_rho"])
                kw.update(cfg=dcfg, distractor=(d[0], d[1], DISTR_R))
            try:
                if c == "toy_relay" and cal["toy"]["refused"]:
                    raise SimError("kalibracja toy_relay odrzucona — próba = porażka")
                r = L.run_trial(cond, s, base, cal, **kw)
                r.update(L.metrics(r, TOL))
            except SimError as err:
                r = dict(error=str(err), success=False, final_abs_err=float("nan"), t_first_within=None,
                         overshoot_deg=float("nan"), safety_ticks_flagged=0, safety_flags={}, e_deg=[float("nan")])
            r.update(cond=c, **tr)
            runs.append(r)
            print(f"{c:13s} {s}: az0 {tr['az0_deg']:+6.1f}° ρ {tr['rho']:.2f} → |e| {r['final_abs_err']:5.2f}° "
                  f"success {r['success']}", flush=True)
    post = L.stage1_hashes()
    res = dict(protocol="V5 v2", seeds=[seeds[0], seeds[-1]], calib=cal, toy=toyrep, network=rep, runs=runs,
               stage1_pre=pre, stage1_post=post, wall_s=time.perf_counter() - t0, argv=sys.argv,
               code_sha256={f: hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest()
                            for f in ("loop_v2.py", "loop.py", "v4_open_loop.py", "visual_path.py", "so101.py", "encoder.py",
                                      "alif.py", "decoder.py", "safety.py", "snn_interface.py")})
    path = os.path.join(out, f"v5v2_{time.strftime('%Y%m%dT%H%M%S')}.json")
    with open(path, "x") as f:
        json.dump(res, f, ensure_ascii=False, default=str)
    print("zapisano:", path, "| Stage 1 po:", "OK" if not post["mismatched"] else post["mismatched"])
    return path


def analyze(res, alpha=0.025, margin=0.15):
    by = {}
    for r in res["runs"]:
        by.setdefault(r["cond"], {})[r["seed"]] = r
    seeds = sorted(by["snn"])
    S = lambda c: np.array([bool(by[c][s]["success"]) for s in seeds])
    F = lambda c: np.array([by[c][s]["final_abs_err"] for s in seeds], float)
    rho = np.array([by["snn"][s]["rho"] for s in seeds])
    w = lambda k, n: [round(float(x), 3) for x in L_wilson(k, n)]
    out = dict(n=len(seeds), conds={})
    for c in by:
        x = S(c)
        bins = {f"{lo:.2f}-{hi:.2f}": f"{int(x[(rho >= lo) & (rho < hi + (hi == RHO_BINS[-1]))].sum())}/"
                f"{int(((rho >= lo) & (rho < hi + (hi == RHO_BINS[-1]))).sum())}" for lo, hi in zip(RHO_BINS, RHO_BINS[1:])}
        out["conds"][c] = dict(success=int(x.sum()), rate=round(float(x.mean()), 3), wilson95=w(int(x.sum()), len(x)),
                               final_abs_err_median=round(float(np.nanmedian(F(c))), 2), by_rho=bins,
                               errors=int(sum("error" in by[c][s] for s in seeds)))

    def mcnemar(a, b, alt):
        n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
        p = float(binomtest(n10, n10 + n01, 0.5, alt).pvalue) if n10 + n01 else 1.0
        return dict(a_only=n10, b_only=n01, p=p)

    def boot(a, b, seed=2202, n=10000):
        d = a.astype(float) - b.astype(float)
        m = d[np.random.default_rng(seed).integers(len(d), size=(n, len(d)))].mean(1)
        return dict(diff=round(float(d.mean()), 3), ci95=[round(float(v), 3) for v in np.percentile(m, [2.5, 97.5])])

    h1 = mcnemar(S("snn"), S("snn_dnperm"), "greater")
    out["H1_lateralization_snn_gt_dnperm"] = dict(h1, pass_=h1["p"] < alpha)
    h2, b2 = mcnemar(S("snn"), S("snn_eqshuffle"), "two-sided"), boot(S("snn"), S("snn_eqshuffle"))
    out["H2_topology_snn_vs_eqshuffle"] = dict(h2, **b2, equivalent=bool(-margin <= b2["ci95"][0] and b2["ci95"][1] <= margin),
                                               topology_matters=bool(h2["p"] < alpha and b2["diff"] > 0))
    for c in ("toy_relay", "classical_p", "no_vision", "snn_distr"):
        out[f"desc_{c}_minus_snn_success"] = boot(S(c), S("snn"))
    out["desc_p_distr_minus_snn_distr_success"] = boot(S("p_distr"), S("snn_distr"))
    return out


def L_wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, c - h), min(1.0, c + h)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--seeds")
    ap.add_argument("--out")
    ap.add_argument("--calib", default=os.path.join(HERE, "results", "v4", "v4_partB_v2_20261028T214641.json"))
    ap.add_argument("--analyze")
    a = ap.parse_args()
    if a.analyze:
        print(json.dumps(analyze(json.load(open(a.analyze))), indent=1, ensure_ascii=False))
        sys.exit()
    lo, hi = map(int, a.seeds.split("-"))
    seeds = list(range(lo, hi + 1))
    if set(seeds) & L.FORBIDDEN or not a.out or not L._allowed(a.out):
        sys.exit("odmowa: zabronione ziarna albo --out poza flymind/ i $TMPDIR")
    run(seeds, a.out, a.calib)
