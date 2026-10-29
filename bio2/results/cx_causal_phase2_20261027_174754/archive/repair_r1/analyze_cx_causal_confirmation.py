#!/usr/bin/env python3
"""
bio2/analyze_cx_causal_confirmation.py — analiza potwierdzająca Exp A2 wg confirmatory_protocol_v4.md (wiążący).

Tryby:
  --mode stage1   zaślepiony etap 1 (ziarna 300–323): TYLKO liczności, warunki E1–E3 (PASS/FAIL), SD/SD_UB, N_req, N_final.
                  Bez średnich, efektów i testów. Zapis stage1_decision.json.
  --mode final    jednorazowa analiza końcowa (ziarna 300 … 299+N_final z stage1_decision.json).
  --mode dev      dane rozwojowe (200–299): bez weryfikacji pochodzenia, ramiona opcjonalne, wynik oznaczony DEV,
                  BEZ werdyktów.
  --selftest      testy syntetyczne (zakres ziaren 1300+, bez symulacji).
Reguły V1–V10, E1–E4, rodziny F1/F2/F3/F1s i werdykty: patrz protokół §2–§5. Skrypt nie imputuje i nie usuwa po cichu.
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time

import numpy as np
import scipy.stats as st

ANALYSIS_VERSION = "1.0.0"
PROTOCOL_VERSION = "v4"
REQUIRED_ARMS = ("Freeze", "Scalar", "SelfOnly", "CX-Bump", "CX-Bump-NoSelf", "CX-DN", "CX-Sham", "CX-Pulse+30",
                 "CX-Pulse-30", "CX-DN-Sham", "CX-DN-Pulse+30", "CX-DN-Pulse-30", "CX-Reset", "CX-Shuffle20",
                 "Scalar-Shift+30", "Scalar-Shift-30")
INTACT_CX_ARMS = ("CX-Bump", "CX-Bump-NoSelf", "CX-DN", "CX-Sham", "CX-Pulse+30", "CX-Pulse-30", "CX-DN-Sham",
                  "CX-DN-Pulse+30", "CX-DN-Pulse-30", "CX-Reset")
DELTAS = (-20.0, 0.0, 20.0)
STAGE1_SEEDS = tuple(range(300, 324))
CONFIRM_RANGE = range(300, 400)
DEV_RANGE = range(200, 300)
N_FLOOR, N_CAP = 40, 100
ALPHA = 0.025                      # jednostronne, po Holmie w rodzinie
SIZING = dict(alpha2=0.0125, power=0.90)
BOOT = dict(n=10_000, seed=20261027)
ONSET_TOL, PASSIVE_LO, PASSIVE_HI, PASSIVE0_TOL = 1e-3, 16.85, 17.85, 0.5
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FROZEN = os.path.join(HERE, "results", "cx_causal_phase2_20261027_174754", "frozen_manifest_v4.json")


class Refused(RuntimeError):
    pass


wrap = lambda x: ((x + 180.0) % 360.0) - 180.0


# ----------------------------------------------------------------------------- statystyka
def tstats(d):
    d = np.asarray(d, float); n = len(d); m = float(d.mean())
    sd = float(d.std(ddof=1)) if n > 1 else float("nan")
    se = sd / math.sqrt(n) if n > 1 else float("nan")
    return n, m, sd, se


def t_ci(d, level=0.95):
    n, m, sd, se = tstats(d)
    if n < 2:
        return float("nan"), float("nan")
    if sd == 0:
        return m, m
    h = st.t.ppf(0.5 + level / 2, n - 1) * se
    return m - h, m + h


def p_less(d, mu0):
    """H0: mu >= mu0 vs H1: mu < mu0 (jednostronny t)."""
    n, m, sd, se = tstats(d)
    if n < 2:
        return float("nan")
    if sd == 0:
        return 0.0 if m < mu0 else 1.0
    return float(st.t.cdf((m - mu0) / se, n - 1))


def p_greater(d, mu0):
    n, m, sd, se = tstats(d)
    if n < 2:
        return float("nan")
    if sd == 0:
        return 0.0 if m > mu0 else 1.0
    return float(1 - st.t.cdf((m - mu0) / se, n - 1))


def holm(ps):
    ps = np.asarray(ps, float); m = len(ps); order = np.argsort(ps); adj = np.empty(m); run = 0.0
    for i, j in enumerate(order):
        run = max(run, (m - i) * ps[j]); adj[j] = min(1.0, run)
    return adj.tolist()


def bca_ci(d, level=0.95):
    d = np.asarray(d, float)
    if len(d) < 3:
        return float("nan"), float("nan")
    if np.ptp(d) <= 1e-9 * max(1.0, abs(float(d.mean()))):        # stałe (z dokładnością do zaokrągleń)
        return float(d.mean()), float(d.mean())
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = st.bootstrap((d,), np.mean, confidence_level=level, n_resamples=BOOT["n"], method="BCa",
                             random_state=np.random.default_rng(BOOT["seed"]))
    return float(r.confidence_interval.low), float(r.confidence_interval.high)


def bca_ok(*arrays, level=0.95):
    return all(np.all(np.isfinite(bca_ci(a, level))) for a in arrays)


def wilcoxon_p(d, mu0=0.0):
    x = np.asarray(d, float) - mu0
    if len(x) < 2 or np.all(x == 0):
        return float("nan")
    return float(st.wilcoxon(x).pvalue)


def sd_upper(sd, n, conf=0.80):
    return sd * math.sqrt((n - 1) / st.chi2.ppf(1 - conf, n - 1))


def n_required(sd, delta, alpha2=SIZING["alpha2"], power=SIZING["power"]):
    """Najmniejsze n, przy którym sparowany t dwustronny (alpha2) ma moc >= power dla różnicy delta (dokładnie, nct)."""
    if not np.isfinite(sd) or sd <= 0:
        return N_FLOOR
    for n in range(2, 100_000):
        df = n - 1; nc = delta * math.sqrt(n) / sd; tc = st.t.ppf(1 - alpha2 / 2, df)
        pw = 1 - st.nct.cdf(tc, df, nc) + st.nct.cdf(-tc, df, nc)
        if pw >= power:
            return n
    return 100_000


# ----------------------------------------------------------------------------- walidacja
def load_jsonl(path):
    raw = open(path, "rb").read()
    if raw and not raw.endswith(b"\n"):
        raise Refused(f"V1: niepełny ostatni rekord w {path}")
    recs = []
    for n, ln in enumerate(raw.split(b"\n")[:-1], 1):
        try:
            recs.append(json.loads(ln))
        except ValueError:
            raise Refused(f"V1: uszkodzony rekord w linii {n}")
    return recs


def validate_dataset(recs, manifest, frozen, planned_seeds, mode):
    """V1/V2 — odmowa przy jakiejkolwiek niezgodności z zamrożonym protokołem. Zwraca słownik (arm, seed, delta) -> rec."""
    if mode != "dev":
        if manifest is None:
            raise Refused("V1: brak manifestu zbioru")
        for k in ("protocol_version", "runner_sha256", "cfg_sha256"):
            if manifest.get(k) != frozen.get(k):
                raise Refused(f"V1: manifest {k}={manifest.get(k)!r} ≠ zamrożone {frozen.get(k)!r}")
        if manifest.get("jump") is not True or manifest.get("moving") is not False:
            raise Refused("V1: manifest nie jest Exp A2 (jump=True, moving=False)")
        if sorted(manifest.get("arms", [])) != sorted(REQUIRED_ARMS):
            raise Refused(f"V1: ramiona manifestu ≠ 16 wymaganych: {manifest.get('arms')}")
        if sorted(manifest.get("passive", [])) != sorted(DELTAS):
            raise Refused(f"V1: Δ manifestu ≠ {DELTAS}")
        if manifest.get("no_log"):
            raise Refused("V1: zbiór bez przebiegów czasowych (no_log) — kontrola trwałości niewykonalna")
    E = {}
    for r in recs:
        if mode != "dev":
            for k in ("dataset_id", "protocol_version", "runner_sha256", "cfg_sha256"):
                if r.get(k) != manifest.get(k):
                    raise Refused(f"V1: rekord {r.get('arm')}/{r.get('seed')}: {k} niezgodne z manifestem")
            if r.get("jump") is not True or r.get("ball_stop") is not True:
                raise Refused(f"V1: rekord {r.get('arm')}/{r.get('seed')}/{r.get('passive_deg')} nie jest A2")
        a, s, dl = r.get("arm"), r.get("seed"), r.get("passive_deg")
        if a not in REQUIRED_ARMS:
            raise Refused(f"V1: nieznane ramię {a!r}")
        if dl not in DELTAS:
            raise Refused(f"V1: niedozwolone Δ {dl!r}")
        if s not in planned_seeds:
            raise Refused(f"V1: ziarno {s} poza planem")
        if (a, s, dl) in E:
            raise Refused(f"V1: duplikat {(a, s, dl)}")
        E[(a, s, dl)] = r
    if mode != "dev":
        missing = [(a, s, dl) for a in REQUIRED_ARMS for s in planned_seeds for dl in DELTAS if (a, s, dl) not in E]
        if missing:
            raise Refused(f"V2: brak {len(missing)} zaplanowanych rekordów, np. {missing[:3]}")
    return E


def trial_valid(E, key):
    """V3–V5 dla jednej próby (V9: cichy bump NIE unieważnia)."""
    r = E.get(key)
    if r is None or r.get("status") != "OK":
        return False
    a, s, dl = key
    on = r["snaps"].get("onset", {}).get("true_rel_deg")
    ref_r = E.get(("Freeze", s, dl))
    if ref_r is not None and ref_r.get("status") == "OK":
        ref = ref_r["snaps"]["onset"]["true_rel_deg"]
    else:
        vals = [x["snaps"]["onset"]["true_rel_deg"] for (aa, ss, dd), x in E.items()
                if ss == s and dd == dl and x.get("status") == "OK" and "onset" in x.get("snaps", {})]
        ref = float(np.median(vals)) if vals else None
    if on is None or ref is None or abs(on - ref) > ONSET_TOL:
        return False
    pr = r.get("passive_realised_deg")
    if pr is None:
        return False
    if dl == 0.0:
        return abs(pr) <= PASSIVE0_TOL
    return np.sign(pr) == np.sign(dl) and PASSIVE_LO <= abs(pr) <= PASSIVE_HI


def seed_status(E, s, arms):
    rs = [E[(a, s, dl)] for a in arms for dl in DELTAS if (a, s, dl) in E]
    nc = [r.get("status") == "NOT_CONVERGED" for r in rs]
    if rs and all(nc):
        return "NOT_CONVERGED"
    if any(nc):
        return "TECHNICAL_FAILURE"                                     # V7
    for a in INTACT_CX_ARMS:
        for dl in DELTAS:
            r = E.get((a, s, dl))
            sc = (r or {}).get("steer_calib")
            if sc and (min(sc["slope_mem"]) < 7 or max(abs(x) for x in sc["offset_mem"]) > 10):
                return "TECHNICAL_FAILURE"                             # V8
    if any(not trial_valid(E, (a, s, dl)) for a in arms for dl in DELTAS if (a, s, dl) in E):
        return "TECHNICAL_FAILURE"                                     # ≥1 nieważna próba (V3–V5)
    return "OK"


# ----------------------------------------------------------------------------- statystyki ziarna
def e(E, a, s, dl):
    return E[(a, s, dl)]["e_end_deg"]


CONTRASTS = {
    # nazwa: (potrzebne (ramię, Δ), funkcja wartości ziarna)
    "S_DN": ([("CX-DN-Pulse-30", d) for d in DELTAS] + [("CX-DN-Pulse+30", d) for d in DELTAS],
             lambda E, s: np.mean([(e(E, "CX-DN-Pulse-30", s, d) - e(E, "CX-DN-Pulse+30", s, d)) / 2 for d in DELTAS])),
    "P2a": ([("CX-Bump", 0.0), ("Freeze", 0.0)],
            lambda E, s: abs(e(E, "CX-Bump", s, 0.0)) - abs(e(E, "Freeze", s, 0.0))),
    "P2b": ([(a, d) for a in ("CX-Bump", "SelfOnly") for d in (-20.0, 20.0)],
            lambda E, s: np.mean([abs(e(E, "CX-Bump", s, d)) for d in (-20.0, 20.0)])
            - np.mean([abs(e(E, "SelfOnly", s, d)) for d in (-20.0, 20.0)])),
    "P3": ([(a, d) for a in ("CX-Bump", "Scalar") for d in DELTAS],
           lambda E, s: np.mean([abs(e(E, "CX-Bump", s, d)) for d in DELTAS])
           - np.mean([abs(e(E, "Scalar", s, d)) for d in DELTAS])),
    "S_scalar": ([("Scalar-Shift-30", d) for d in DELTAS] + [("Scalar-Shift+30", d) for d in DELTAS],
                 lambda E, s: np.mean([(e(E, "Scalar-Shift-30", s, d) - e(E, "Scalar-Shift+30", s, d)) / 2 for d in DELTAS])),
    "g": ([("CX-Bump", d) for d in (-20.0, 20.0)],
          lambda E, s: np.mean([-wrap(E[("CX-Bump", s, d)]["snaps"]["post_passive"]["bump_deg"]
                                      - E[("CX-Bump", s, d)]["snaps"]["onset"]["bump_deg"]) / E[("CX-Bump", s, d)]["passive_realised_deg"]
                                for d in (-20.0, 20.0)])),
    "DN+30_vs_sham": ([(a, d) for a in ("CX-DN-Pulse+30", "CX-DN-Sham") for d in DELTAS],
                      lambda E, s: np.mean([e(E, "CX-DN-Pulse+30", s, d) - e(E, "CX-DN-Sham", s, d) for d in DELTAS])),
    "DN-30_vs_sham": ([(a, d) for a in ("CX-DN-Pulse-30", "CX-DN-Sham") for d in DELTAS],
                      lambda E, s: np.mean([e(E, "CX-DN-Pulse-30", s, d) - e(E, "CX-DN-Sham", s, d) for d in DELTAS])),
    "S_bump": ([("CX-Pulse-30", d) for d in DELTAS] + [("CX-Pulse+30", d) for d in DELTAS],
               lambda E, s: np.mean([(e(E, "CX-Pulse-30", s, d) - e(E, "CX-Pulse+30", s, d)) / 2 for d in DELTAS])),
    "Q4_bump_vs_noself": ([(a, d) for a in ("CX-Bump", "CX-Bump-NoSelf") for d in DELTAS],
                          lambda E, s: np.mean([abs(e(E, "CX-Bump", s, d)) - abs(e(E, "CX-Bump-NoSelf", s, d)) for d in DELTAS])),
    "Q4_noself_vs_freeze": ([(a, d) for a in ("CX-Bump-NoSelf", "Freeze") for d in DELTAS],
                            lambda E, s: np.mean([abs(e(E, "CX-Bump-NoSelf", s, d)) - abs(e(E, "Freeze", s, d)) for d in DELTAS])),
    "DN_vs_freeze": ([(a, d) for a in ("CX-DN", "Freeze") for d in DELTAS],
                     lambda E, s: np.mean([abs(e(E, "CX-DN", s, d)) - abs(e(E, "Freeze", s, d)) for d in DELTAS])),
    "memerr_CXBump": ([("CX-Bump", d) for d in DELTAS],
                      lambda E, s: np.mean([abs(E[("CX-Bump", s, d)]["mem_err_end_deg"]) if E[("CX-Bump", s, d)].get("mem_err_end_deg")
                                            is not None else float("nan") for d in DELTAS])),
}


def contrast_values(E, name, seeds, seed_ok, valid):
    need, f = CONTRASTS[name]
    vals, used, excl = [], [], []
    for s in seeds:
        if seed_ok.get(s) == "NOT_CONVERGED" or not all((a, s, d) in valid for a, d in need):
            excl.append(s); continue
        if seed_ok.get(s) == "TECHNICAL_FAILURE" and any(a in INTACT_CX_ARMS for a, _ in need) and seed_calib_bad(E, s):
            excl.append(s); continue
        v = float(f(E, s))
        if not np.isfinite(v):                                        # np. brak estymaty pamięci (cichy bump) — jawnie
            excl.append(s); continue
        vals.append(v); used.append(s)
    return np.array(vals), used, excl


_CALIB_BAD = {}


def seed_calib_bad(E, s):
    if s not in _CALIB_BAD:
        bad = False
        for a in INTACT_CX_ARMS:
            for d in DELTAS:
                sc = (E.get((a, s, d)) or {}).get("steer_calib")
                if sc and (min(sc["slope_mem"]) < 7 or max(abs(x) for x in sc["offset_mem"]) > 10):
                    bad = True
        _CALIB_BAD[s] = bad
    return _CALIB_BAD[s]


def summarize(d):
    n, m, sd, se = tstats(d) if len(d) else (0, float("nan"), float("nan"), float("nan"))
    lo, hi = t_ci(d) if n >= 2 else (float("nan"), float("nan"))
    blo, bhi = bca_ci(d) if n >= 3 else (float("nan"), float("nan"))
    return dict(n=n, mean=m, sd=sd, t_ci95=[lo, hi], bca_ci95=[blo, bhi], wilcoxon_p=wilcoxon_p(d) if n >= 2 else float("nan"),
                frac_positive=float(np.mean(np.asarray(d) > 0)) if n else float("nan"))


def manipulation_check(E, valid):
    sh = {"+30": [], "-30": [], "sham": []}; dcoh = []
    for arm, k in (("CX-DN-Pulse+30", "+30"), ("CX-DN-Pulse-30", "-30"), ("CX-DN-Sham", "sham")):
        for key in valid:
            if key[0] != arm:
                continue
            sn = E[key]["snaps"]
            if "post_int" not in sn or "bump_pre_int" not in sn:
                continue
            sh[k].append(wrap(sn["post_int"]["bump_deg"] - sn["bump_pre_int"]))
            dcoh.append(sn["post_int"]["coh"] - sn["pre_int"]["coh"])
    med = {k: (float(np.median(v)) if v else float("nan")) for k, v in sh.items()}
    ok = (med["+30"] >= 15 and med["-30"] <= -15 and abs(med["sham"]) <= 5 and dcoh and abs(float(np.median(dcoh))) <= 0.1)
    return bool(ok), dict(median_shift=med, median_coh_change=float(np.median(dcoh)) if dcoh else float("nan"))


def persistence_check(E, valid):
    n_ok, n_all, n_eval = 0, 0, 0
    for key in valid:
        if key[0] != "CX-Bump":
            continue
        n_all += 1
        log = E[key].get("log")
        if not log:
            continue
        c = [x[4] for x in log if x[0] >= 0.6 and x[4] is not None]
        if not c:
            continue
        n_eval += 1
        n_ok += (np.mean(c) >= 0.6 and np.min(c) >= 0.4)
    if n_eval < n_all or n_all == 0:
        return None, dict(evaluable=n_eval, trials=n_all)
    return bool(n_ok / n_all >= 0.9), dict(fraction_ok=n_ok / n_all, trials=n_all)


def memory_content(E, valid, arm, seeds):
    xs, ys = [], []
    for d in DELTAS:
        x = [E[(arm, s, d)]["snaps"]["post_passive"]["true_rel_deg"] for s in seeds if (arm, s, d) in valid]
        y = [E[(arm, s, d)]["e_end_deg"] - E[(arm, s, d)]["snaps"]["post_passive"]["true_rel_deg"] for s in seeds if (arm, s, d) in valid]
        if len(x) >= 2:
            xs.append(np.array(x) - np.mean(x)); ys.append(np.array(y) - np.mean(y))
    if not xs:
        return None
    x, y = np.concatenate(xs), np.concatenate(ys)
    if np.std(x) == 0 or np.std(y) == 0:
        return dict(slope=0.0, r=0.0, pass_=False, n=len(x))
    l = st.linregress(x, y); h = st.t.ppf(0.975, len(x) - 2) * l.stderr
    return dict(slope=float(l.slope), ci=[float(l.slope - h), float(l.slope + h)], r=float(l.rvalue), n=len(x),
                pass_=bool(l.slope <= -0.5 and l.slope + h < 0 and l.rvalue <= -0.5))


# ----------------------------------------------------------------------------- werdykty
def verdict_q1(d, manip_ok, ci_fn):
    if not manip_ok:
        return "INCONCLUSIVE (no manipulation)"
    lo, hi = ci_fn(d); fp = float(np.mean(d > 0))
    if lo > 5 and fp >= 0.8:
        return "SUPPORTED"
    if hi < 5 or fp < 0.6:
        return "NEGATIVE"
    return "INCONCLUSIVE"


def verdict_q2(da, db, gate_ok, use_bca=False):
    res = {}
    if use_bca:      # zachowawczy odpowiednik Holma: Bonferroni, dwustronne 97,5 %
        ca, cb = bca_ci(da, 0.975), bca_ci(db, 0.975)
        benefit = [ca[1] < 0, cb[1] < 0]
        nomeaning = [ca[0] > -3, cb[0] > -3]
    else:
        pb = holm([p_less(da, 0.0), p_less(db, 0.0)]); pn = holm([p_greater(da, -3.0), p_greater(db, -3.0)])
        res.update(holm_p_benefit=pb, holm_p_no_meaningful_benefit=pn)
        benefit = [p < ALPHA for p in pb]; nomeaning = [p < ALPHA for p in pn]
    if not gate_ok:
        benefit[1] = False; nomeaning[1] = False            # P2b nieinformatywne przy nieudanej bramce
    if nomeaning[0] or nomeaning[1]:
        v = "NEGATIVE"
    elif all(benefit) and da.mean() <= -3 and db.mean() <= -3 and gate_ok:
        v = "SUPPORTED"
    else:
        v = "INCONCLUSIVE" + ("" if gate_ok else " (P2b miscalibrated)")
    return v, res


def verdict_q3(d, gate_ok, ci_fn):
    if not gate_ok:
        return "INCONCLUSIVE (miscalibrated)"
    lo, hi = ci_fn(d)
    if hi < 5:
        return "SUPPORTED"
    if lo > 5:
        return "NEGATIVE"
    return "INCONCLUSIVE"


def robust(v_t, v_b):
    return v_t if v_t == v_b else f"INCONCLUSIVE (fragile: t→{v_t}, BCa→{v_b})"


# ----------------------------------------------------------------------------- przebieg
def analyse(recs, manifest, frozen, mode, planned_seeds, stage1_decision=None):
    _CALIB_BAD.clear()
    E = validate_dataset(recs, manifest, frozen, set(planned_seeds), mode)
    seeds = sorted(planned_seeds) if mode != "dev" else sorted({s for (_, s, _) in E})
    arms = REQUIRED_ARMS if mode != "dev" else tuple(a for a in REQUIRED_ARMS if any(k[0] == a for k in E))
    seed_ok = {s: seed_status(E, s, arms) for s in seeds}
    valid = {k for k in E if trial_valid(E, k)}
    N = len(seeds)
    n_tf = sum(v == "TECHNICAL_FAILURE" for v in seed_ok.values())
    n_nc = sum(v == "NOT_CONVERGED" for v in seed_ok.values())
    out = dict(analysis_version=ANALYSIS_VERSION, protocol_version=PROTOCOL_VERSION, mode=mode, planned_seeds=N,
               dataset_id=(manifest or {}).get("dataset_id"), n_records=len(recs),
               seed_status_counts=dict(OK=N - n_tf - n_nc, TECHNICAL_FAILURE=n_tf, NOT_CONVERGED=n_nc),
               invalid_trials=sorted([list(k) for k in E if k not in valid]),
               silent_bump_trials=sum(1 for k in valid if k[0] == "CX-Bump" and E[k].get("log")
                                      and any(x[4] is not None and x[4] < 0.2 for x in E[k]["log"])))
    E1 = n_tf > 0.10 * N
    E2 = n_nc > 0.20 * N
    sc, _, _ = contrast_values(E, "S_scalar", seeds, seed_ok, valid) if all(a in arms for a in ("Scalar-Shift+30", "Scalar-Shift-30")) else (np.array([]), [], [])
    E3 = (len(sc) == 0) or (float(sc.mean()) < 20.0)
    min_valid = max(20, math.ceil(0.85 * N))
    vals = {}
    for name in CONTRASTS:
        need, _ = CONTRASTS[name]
        if not all(a in arms for a, _ in need):
            continue
        v, used, excl = contrast_values(E, name, seeds, seed_ok, valid)
        vals[name] = dict(values=v, used=used, excluded=excl)

    if mode == "stage1":
        rows = {}
        for name, key in (("S_DN", "Q1"), ("P2a", "Q2a"), ("P2b", "Q2b"), ("P3", "Q3")):
            v = vals[name]["values"]; n = len(v)
            sd = float(v.std(ddof=1)) if n > 1 else float("nan")
            ub = sd_upper(sd, n) if n > 1 else float("nan")
            delta = 10.0 if name == "S_DN" else 5.0
            rows[key] = dict(n_valid=n, sd=sd, sd_ub80=ub, delta=delta, n_required=n_required(ub, delta))
        n_final = min(N_CAP, max(N_FLOOR, *[r["n_required"] for r in rows.values()]))
        out.update(stage1=rows, n_final=int(n_final), final_seeds=[300, 299 + int(n_final)],
                   E1_technical_failure_rate="FAIL" if E1 else "PASS", E2_not_converged_rate="FAIL" if E2 else "PASS",
                   E3_positive_control="FAIL" if E3 else "PASS",
                   decision=("STOP — EXPERIMENT TECHNICAL_FAILURE" if (E1 or E3) else
                             "STOP — NOT_CONVERGED > 20 %" if E2 else f"CONTINUE to seeds 324–{299 + int(n_final)}"))
        return out                                                     # zaślepione: brak średnich/testów

    res = {name: summarize(x["values"]) | dict(excluded_seeds=x["excluded"]) for name, x in vals.items()}
    manip_ok, manip = manipulation_check(E, valid) if "S_DN" in vals else (False, {})
    g = res.get("g")
    gate_ok = bool(g and g["n"] >= 2 and 0.75 <= g["mean"] <= 1.25 and 0.6 <= g["t_ci95"][0] and g["t_ci95"][1] <= 1.5)
    pers_ok, pers = persistence_check(E, valid)
    out.update(results=res, manipulation_check=dict(passed=manip_ok, **manip), self_motion_gate=dict(passed=gate_ok),
               persistence_check=dict(passed=pers_ok, **pers),
               memory_content={a: memory_content(E, valid, a, seeds) for a in ("CX-Bump", "CX-DN", "Scalar") if a in arms},
               positive_control=(dict(S_scalar_mean=float(sc.mean()), passed=not E3) if len(sc) else None),
               E1=E1, E2=E2, E3=E3, min_valid_seeds=min_valid)
    # F1s (wtórna, Holm m=3)
    if all(k in vals for k in ("DN+30_vs_sham", "DN-30_vs_sham", "S_bump")):
        ps = [st.ttest_1samp(vals["DN+30_vs_sham"]["values"], 0).pvalue, st.ttest_1samp(vals["DN-30_vs_sham"]["values"], 0).pvalue,
              p_greater(vals["S_bump"]["values"], 5.0)]
        out["F1s_holm_p"] = dict(zip(("DN+30_vs_sham", "DN-30_vs_sham", "S_bump>5"), holm([float(x) for x in ps])))
    if mode == "dev":
        out["verdicts"] = "DEV — NOT CONFIRMATORY (no verdicts from development seeds)"
        return out
    # werdykty
    if E1 or E3:
        out["verdicts"] = dict(EXPERIMENT="TECHNICAL_FAILURE", reason=("E1 TF seeds > 10 %" if E1 else "") + (" E3 positive control" if E3 else ""))
        return out
    V = {}
    small = lambda name: len(vals[name]["values"]) < min_valid
    t95 = lambda d: t_ci(d, 0.95)
    b95 = lambda d: bca_ci(d, 0.95)
    if E2:
        V = dict(Q1="INCONCLUSIVE (E2)", Q2="INCONCLUSIVE (E2)", Q3="INCONCLUSIVE (E2)")
    else:
        d1 = vals["S_DN"]["values"]
        V["Q1"] = ("INCONCLUSIVE (E4)" if small("S_DN") else "INCONCLUSIVE (BCa not computable)" if not bca_ok(d1)
                   else robust(verdict_q1(d1, manip_ok, t95), verdict_q1(d1, manip_ok, b95)))
        da, db = vals["P2a"]["values"], vals["P2b"]["values"]
        if small("P2a") or small("P2b"):
            V["Q2"] = "INCONCLUSIVE (E4)"
        elif not bca_ok(da, db, level=0.975):
            V["Q2"] = "INCONCLUSIVE (BCa not computable)"
        else:
            vt, extra = verdict_q2(da, db, gate_ok); vb, _ = verdict_q2(da, db, gate_ok, use_bca=True)
            V["Q2"] = robust(vt, vb); out["Q2_tests"] = extra
            if pers_ok is False:
                V["Q2"] += " [persistence check failed]"
        d3 = vals["P3"]["values"]
        V["Q3"] = ("INCONCLUSIVE (E4)" if small("P3") else "INCONCLUSIVE (BCa not computable)" if not bca_ok(d3)
                   else robust(verdict_q3(d3, gate_ok, t95), verdict_q3(d3, gate_ok, b95)))
    me = res.get("memerr_CXBump")
    out["causal_memory_composite_descriptive"] = dict(
        q1_supported=V.get("Q1") == "SUPPORTED", self_motion_gate=gate_ok,
        memerr_upper_below_17_3=bool(me and me["t_ci95"][1] < 17.3))
    out["verdicts"] = V
    return out


def jdefault(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, np.bool_):
        return bool(o)
    raise TypeError(type(o))


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--mode", choices=("stage1", "final", "dev"))
    ap.add_argument("--data", help="JSONL zbioru (manifest: <data>.manifest.json)")
    ap.add_argument("--dev-files", nargs="*", help="(dev) pliki JSONL rozwojowe")
    ap.add_argument("--frozen", default=DEFAULT_FROZEN, help="frozen_manifest_v4.json")
    ap.add_argument("--stage1-decision", help="(final) stage1_decision.json")
    ap.add_argument("--out", required=False, help="plik wyniku JSON")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        import importlib.util
        spec = importlib.util.spec_from_file_location("acc_selftest", os.path.join(HERE, "test_analyze_cx_causal_confirmation.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        sys.exit(0 if m.run_all() else 1)
    try:
        if a.mode == "dev":
            recs = [r for f in a.dev_files for r in load_jsonl(f)]
            seeds = sorted({r["seed"] for r in recs})
            if any(s not in DEV_RANGE for s in seeds):
                raise Refused("dev: tylko ziarna 200–299")
            out = analyse(recs, None, {}, "dev", seeds)
        else:
            frozen = json.load(open(a.frozen))
            man_path = a.data + ".manifest.json"
            manifest = json.load(open(man_path)) if os.path.exists(man_path) else None
            recs = load_jsonl(a.data)
            if a.mode == "stage1":
                planned = STAGE1_SEEDS
            else:
                dec = json.load(open(a.stage1_decision))
                if dec.get("dataset_id") != (manifest or {}).get("dataset_id") or dec.get("analysis_version") != ANALYSIS_VERSION:
                    raise Refused("final: stage1_decision niezgodny ze zbiorem lub wersją analizy")
                planned = tuple(range(300, 300 + int(dec["n_final"])))
            if any(s not in CONFIRM_RANGE for s in planned):
                raise Refused("plan poza 300–399")
            out = analyse(recs, manifest, frozen, a.mode, planned)
            out.update(data_sha256=sha256(a.data), manifest_sha256=sha256(man_path), analysis_sha256=sha256(__file__),
                       created_at=time.strftime("%Y-%m-%dT%H:%M:%S"))
    except Refused as exc:
        out = dict(analysis_version=ANALYSIS_VERSION, mode=a.mode, verdicts="REFUSED", reason=str(exc))
        print(json.dumps(out, ensure_ascii=False, indent=1))
        if a.out:
            json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1)
        sys.exit(2)
    txt = json.dumps(out, default=jdefault, ensure_ascii=False, indent=1)
    if a.out:
        open(a.out, "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
