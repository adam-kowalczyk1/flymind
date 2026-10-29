#!/usr/bin/env python3
"""Testy syntetyczne analizy potwierdzającej (bez symulacji; ziarna syntetyczne 1300+, nigdy 300–399 ani 0–39)."""
import copy
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_cx_causal_confirmation as A

SEEDS = tuple(range(1300, 1324))
FROZEN = dict(protocol_version="v4", runner_sha256="R" * 64, cfg_sha256="C" * 64)
MAN = dict(FROZEN, dataset_id="synthetic", jump=True, moving=False, arms=list(A.REQUIRED_ARMS),
           passive=list(A.DELTAS), no_log=False)


def make(S_DN=20.0, S_bump=22.0, effA=-8.0, effB=-8.0, noise=1.0, g=1.0, dn_shift=(28.0, -27.0, 1.0),
         scalar_shift=27.0, seeds=SEEDS, rng_seed=7, base_shift=0.0):
    rng = np.random.default_rng(rng_seed); n = lambda: float(rng.normal(0, noise)); recs = []
    for s in seeds:
        for dl in A.DELTAS:
            pr = 0.0 if dl == 0 else math.copysign(17.35, dl)
            base = dict(Freeze=10 + base_shift + n(), SelfOnly=8 + base_shift + n(), Scalar=2 + n())
            cx = (base["Freeze"] + effA if dl == 0 else base["SelfOnly"] + effB) + n()
            vals = dict(base, **{"CX-Bump": cx, "CX-Bump-NoSelf": cx + 5, "CX-DN": cx, "CX-Sham": cx, "CX-DN-Sham": cx,
                                 "CX-Pulse+30": cx - S_bump, "CX-Pulse-30": cx + S_bump,
                                 "CX-DN-Pulse+30": cx - S_DN + n(), "CX-DN-Pulse-30": cx + S_DN + n(),
                                 "CX-Reset": base["Freeze"], "CX-Shuffle20": base["Freeze"],
                                 "Scalar-Shift+30": base["Scalar"] - scalar_shift, "Scalar-Shift-30": base["Scalar"] + scalar_shift})
            for arm in A.REQUIRED_ARMS:
                snaps = dict(onset=dict(true_rel_deg=0.5 * (s % 7), bump_deg=0.0, coh=0.8),
                             post_passive=dict(true_rel_deg=-pr, bump_deg=-g * pr, coh=0.8),
                             pre_int=dict(coh=0.8, bump_deg=0.0), post_int=dict(coh=0.8, bump_deg=0.0))
                if arm in ("CX-DN-Pulse+30", "CX-DN-Pulse-30", "CX-DN-Sham", "CX-Pulse+30", "CX-Pulse-30", "CX-Sham"):
                    sh = {"+30": dn_shift[0], "-30": dn_shift[1]}.get(arm[-3:], dn_shift[2])
                    snaps["bump_pre_int"] = 0.0; snaps["post_int"]["bump_deg"] = sh
                rec = dict(MAN, arm=arm, seed=s, passive_deg=dl, ball_stop=True, jump=True, status="OK",
                           e_end_deg=vals[arm], snaps=snaps, passive_realised_deg=pr, mem_err_end_deg=10.0,
                           log=[(round(0.1 * k, 1), 0.0, 0.0, 0.0, 0.8) for k in range(21)],
                           steer_calib=(dict(slope_mem=[14.0, 14.0], offset_mem=[-3.0, -3.0]) if arm in A.INTACT_CX_ARMS else None))
                for k in ("arms", "passive", "no_log", "moving"):
                    rec.pop(k)
                recs.append(rec)
    return recs


def run(recs, mode="final", man=MAN, seeds=SEEDS):
    return A.analyse(recs, man, FROZEN, mode, seeds)


def refused(fn):
    try:
        fn()
    except A.Refused:
        return True
    return False


def walk_keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from walk_keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk_keys(v)


def run_all():
    ok = True

    def check(name, cond, info=""):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  -> {info}"))
        ok &= bool(cond)

    # --- znane wartości statystyczne
    lo, hi = A.t_ci([1, 2, 3, 4, 5])
    check("t-CI [1..5] = 3 ± 2.776·0.7071", abs(lo - 1.0368) < 1e-3 and abs(hi - 4.9632) < 1e-3, (lo, hi))
    check("Holm [0.01,0.04,0.03] -> [0.03,0.06,0.06]", np.allclose(A.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06]), A.holm([0.01, 0.04, 0.03]))
    nr = A.n_required(10.0, 10.0, alpha2=0.05, power=0.80)
    check("n_required(d=1, α .05, 80 %) = 10 (paired t)", nr == 10, nr)
    check("SD_UB > SD", A.sd_upper(5.0, 24) > 5.0)
    d = np.random.default_rng(1).normal(3, 1, 30); b = A.bca_ci(d)
    check("BCa CI contains sample mean", b[0] < d.mean() < b[1], b)
    check("p_less/p_greater complementary", abs(A.p_less(d, 3) + A.p_greater(d, 3) - 1) < 1e-12)
    check("robust(): disagreement -> INCONCLUSIVE (fragile)", A.robust("SUPPORTED", "INCONCLUSIVE").startswith("INCONCLUSIVE (fragile"))

    # --- werdykty
    r = run(make())
    check("T1 useful: Q1 SUPPORTED", r["verdicts"]["Q1"] == "SUPPORTED", r["verdicts"])
    check("T1 useful: Q2 SUPPORTED", r["verdicts"]["Q2"] == "SUPPORTED", r["verdicts"])
    check("T1 useful: Q3 SUPPORTED (non-inferior)", r["verdicts"]["Q3"] == "SUPPORTED", r["verdicts"])
    r = run(make(effA=10.0, effB=10.0))
    check("T2 harm: Q2 NEGATIVE", r["verdicts"]["Q2"] == "NEGATIVE", r["verdicts"])
    check("T2 harm: Q3 NEGATIVE (inferior)", r["verdicts"]["Q3"] == "NEGATIVE", r["verdicts"])
    # T3: imprecise estimate. Base errors shifted to ~40° so |e| does not fold; true effect −3°, noise 10° (SE ≈ 2–3°).
    # History: earlier versions (noise > base |e|; then effect −2°, noise 3°) correctly returned NEGATIVE — the test
    # expectation was wrong, not the analysis. The precondition (each 95 % t-CI spans both 0 and −3) is now asserted.
    r = run(make(effA=-3.0, effB=-3.0, noise=10.0, rng_seed=3, base_shift=30.0))
    pre = all(r["results"][k]["t_ci95"][0] < -3 and r["results"][k]["t_ci95"][1] > 0 for k in ("P2a", "P2b"))
    check("T3 precondition: CIs span 0 and −3", pre, [r["results"][k]["t_ci95"] for k in ("P2a", "P2b")])
    check("T3 imprecise: Q2 INCONCLUSIVE", r["verdicts"]["Q2"].startswith("INCONCLUSIVE"), r["verdicts"])
    r = run(make(effA=0.0, effB=0.0, noise=3.0, base_shift=30.0))
    check("T3b precise null (benefit ≥3° excluded): Q2 NEGATIVE", r["verdicts"]["Q2"] == "NEGATIVE", r["verdicts"])
    r = run(make(S_DN=1.0))
    check("T4 small S_DN: Q1 NEGATIVE", r["verdicts"]["Q1"] == "NEGATIVE", r["verdicts"])
    r = run(make(dn_shift=(5.0, -5.0, 0.0)))
    check("T5 manipulation fails: Q1 INCONCLUSIVE (no manipulation)", "no manipulation" in r["verdicts"]["Q1"], r["verdicts"])
    r = run(make(g=1.6))
    check("T6 gate fails: Q2 not SUPPORTED", r["verdicts"]["Q2"].startswith("INCONCLUSIVE") and "miscalibrated" in r["verdicts"]["Q2"], r["verdicts"])
    check("T6 gate fails: Q3 INCONCLUSIVE (miscalibrated)", "miscalibrated" in r["verdicts"]["Q3"], r["verdicts"])
    r = run(make(g=1.6, effA=10.0))
    check("T6b gate fails but P2a harm: Q2 NEGATIVE", r["verdicts"]["Q2"] == "NEGATIVE", r["verdicts"])

    # --- odmowy (V1/V2)
    R = make()
    check("V1 duplicate -> REFUSED", refused(lambda: run(R + [copy.deepcopy(R[0])])))
    check("V2 missing record -> REFUSED", refused(lambda: run(R[1:])))
    bad = copy.deepcopy(R); bad[5]["runner_sha256"] = "X" * 64
    check("V1 record runner hash mismatch -> REFUSED", refused(lambda: run(bad)))
    check("V1 manifest hash mismatch -> REFUSED", refused(lambda: run(R, man=dict(MAN, cfg_sha256="Z" * 64))))
    check("V1 manifest without 16 arms -> REFUSED", refused(lambda: run(R, man=dict(MAN, arms=list(A.REQUIRED_ARMS[:14])))))
    check("V1 manifest no_log -> REFUSED", refused(lambda: run(R, man=dict(MAN, no_log=True))))
    check("V1 missing manifest -> REFUSED", refused(lambda: run(R, man=None)))
    bad = copy.deepcopy(R); bad[0]["arm"] = "CV"
    check("V1 unknown arm -> REFUSED", refused(lambda: run(bad)))
    bad = copy.deepcopy(R); bad[0]["jump"] = False
    check("V1 non-A2 record -> REFUSED", refused(lambda: run(bad)))
    check("V1 seed outside plan -> REFUSED", refused(lambda: run(R, seeds=SEEDS[:-1])))

    # --- E1/E2/E3, V4/V5/V7/V8/V9
    def set_status(recs, seeds, status, arm=None):
        out = copy.deepcopy(recs)
        for x in out:
            if x["seed"] in seeds and (arm is None or x["arm"] == arm):
                x["status"] = status
                if status != "OK":
                    x["snaps"] = {}
        return out
    r = run(set_status(R, SEEDS[:2], "TECHNICAL_FAILURE", arm="Scalar"))
    check("E1 2/24 TF seeds (8 %): no experiment failure", r["verdicts"].get("EXPERIMENT") is None and r["seed_status_counts"]["TECHNICAL_FAILURE"] == 2, r["verdicts"])
    check("E1 TF seeds excluded only where needed (P3 n=22, P2a n=24)",
          r["results"]["P3"]["n"] == 22 and r["results"]["P2a"]["n"] == 24, (r["results"]["P3"]["n"], r["results"]["P2a"]["n"]))
    r = run(set_status(R, SEEDS[:3], "TECHNICAL_FAILURE", arm="Scalar"))
    check("E1 3/24 TF seeds (12.5 %) -> EXPERIMENT TECHNICAL_FAILURE", r["verdicts"].get("EXPERIMENT") == "TECHNICAL_FAILURE", r["verdicts"])
    r = run(make(scalar_shift=10.0))
    check("E3 positive control < 20 -> EXPERIMENT TECHNICAL_FAILURE", r["verdicts"].get("EXPERIMENT") == "TECHNICAL_FAILURE", r["verdicts"])
    r = run(set_status(R, SEEDS[:6], "NOT_CONVERGED"))
    check("E2 6/24 NOT_CONVERGED (25 %) -> all INCONCLUSIVE (E2)", all("E2" in v for v in r["verdicts"].values()), r["verdicts"])
    r = run(set_status(R, SEEDS[:3], "NOT_CONVERGED"))
    check("E2 3/24 NOT_CONVERGED: excluded, counted, E4 not triggered (21 ≥ 21)",
          r["seed_status_counts"]["NOT_CONVERGED"] == 3 and r["results"]["P2a"]["n"] == 21 and "E4" not in r["verdicts"]["Q2"], (r["seed_status_counts"], r["verdicts"]))
    r = run(set_status(R, SEEDS[:4], "NOT_CONVERGED"))
    check("E4 20 valid seeds < 21 -> INCONCLUSIVE (E4)", all("E4" in v for v in r["verdicts"].values()), r["verdicts"])
    mix = set_status(R, SEEDS[:1], "NOT_CONVERGED", arm="Freeze")
    r = run(mix)
    check("V7 mixed NOT_CONVERGED -> seed TECHNICAL_FAILURE", r["seed_status_counts"]["TECHNICAL_FAILURE"] == 1, r["seed_status_counts"])
    r = run(R)
    check("C8 Δ=0 with realised 0° is valid (no exclusion)", r["invalid_trials"] == [] and r["results"]["P2a"]["n"] == 24, r["invalid_trials"][:3])
    bad = copy.deepcopy(R)
    for x in bad:
        if x["seed"] == SEEDS[0] and x["passive_deg"] == 0.0 and x["arm"] == "Freeze":
            x["passive_realised_deg"] = 0.7
    r = run(bad)
    check("V5 Δ=0 realised 0.7° -> trial invalid, seed TF", [ "Freeze", SEEDS[0], 0.0] in r["invalid_trials"] and r["results"]["P2a"]["n"] == 23, r["invalid_trials"])
    bad = copy.deepcopy(R)
    for x in bad:
        if x["seed"] == SEEDS[1] and x["arm"] == "Scalar" and x["passive_deg"] == 20.0:
            x["snaps"]["onset"]["true_rel_deg"] += 0.01
    r = run(bad)
    check("V4 onset mismatch 0.01° -> trial invalid", ["Scalar", SEEDS[1], 20.0] in r["invalid_trials"], r["invalid_trials"])
    bad = copy.deepcopy(R)
    for x in bad:
        if x["seed"] == SEEDS[2] and x["arm"] in A.INTACT_CX_ARMS:
            x["steer_calib"]["slope_mem"] = [3.0, 14.0]
    r = run(bad)
    check("V8 degenerate calibration -> seed excluded from CX contrasts only",
          r["results"]["P2a"]["n"] == 23 and r["results"]["S_scalar"]["n"] == 24 and r["seed_status_counts"]["TECHNICAL_FAILURE"] == 1,
          (r["results"]["P2a"]["n"], r["results"]["S_scalar"]["n"]))
    bad = copy.deepcopy(R)
    for x in bad:
        if x["arm"] == "CX-Bump" and x["seed"] in SEEDS[:2]:
            x["log"] = [(rr, a, b, c, 0.1) for rr, a, b, c, _ in x["log"]]
    r = run(bad)
    check("V9 silent bump counted, not excluded", r["silent_bump_trials"] == 6 and r["results"]["P2a"]["n"] == 24, (r["silent_bump_trials"], r["results"]["P2a"]["n"]))
    check("persistence check fails when 6/72 trials silent? (8 % < 10 %: passes)", r["persistence_check"]["passed"] is True, r["persistence_check"])

    # --- R2: zależności, NaN e_end
    check("V1 manifest deps mismatch -> REFUSED", refused(lambda: A.analyse(R, dict(MAN, deps_sha256={"bio2/brain.py": "x"}),
                                                                      dict(FROZEN, deps_sha256={"bio2/brain.py": "y"}), "final", SEEDS)))
    bad = copy.deepcopy(R)
    for x in bad:
        if x["seed"] == SEEDS[3] and x["arm"] == "Freeze" and x["passive_deg"] == 0.0:
            x["e_end_deg"] = float("nan")
    r = run(bad)
    check("V3 OK record with NaN e_end -> trial invalid, seed counted TF",
          ["Freeze", SEEDS[3], 0.0] in r["invalid_trials"] and r["seed_status_counts"]["TECHNICAL_FAILURE"] == 1, r["seed_status_counts"])

    # --- R2: CLI etap 1 -> końcowa, z wykryciem ręcznej edycji (stałe ziaren podmienione na zakres syntetyczny 1300+)
    import json as _j, tempfile
    tmp = tempfile.mkdtemp(prefix="acc_cli_")
    sv = (A.STAGE1_SEEDS, A.CONFIRM_RANGE)
    A.STAGE1_SEEDS, A.CONFIRM_RANGE = tuple(range(1300, 1324)), range(1300, 1400)
    try:
        data, frz = os.path.join(tmp, "ds.jsonl"), os.path.join(tmp, "frozen.json")
        _j.dump(FROZEN, open(frz, "w")); _j.dump(MAN, open(data + ".manifest.json", "w"))
        allrecs = make(seeds=tuple(range(1300, 1340)))
        open(data, "w").write("".join(_j.dumps(x) + "\n" for x in allrecs if x["seed"] < 1324))
        def cli(*args):
            try:
                A.main(list(args)); return 0
            except SystemExit as e:
                return e.code
        dec = os.path.join(tmp, "stage1.json")
        c1 = cli("--mode", "stage1", "--data", data, "--frozen", frz, "--out", dec)
        d1 = _j.load(open(dec))
        check("CLI stage1 writes decision with n_final and stage1_records_sha256", c1 in (None, 0) and "stage1_records_sha256" in d1 and d1["n_final"] == 40, (c1, d1.get("n_final")))
        open(data, "w").write("".join(_j.dumps(x) + "\n" for x in allrecs))
        fin = os.path.join(tmp, "final.json")
        c2 = cli("--mode", "final", "--data", data, "--frozen", frz, "--stage1-decision", dec, "--out", fin)
        check("CLI final runs on stage-1 + continuation seeds and gives verdicts", c2 in (None, 0) and isinstance(_j.load(open(fin))["verdicts"], dict), c2)
        t = dict(d1, n_final=24); tp = os.path.join(tmp, "tampered.json"); _j.dump(t, open(tp, "w"))
        c3 = cli("--mode", "final", "--data", data, "--frozen", frz, "--stage1-decision", tp, "--out", os.path.join(tmp, "f3.json"))
        check("CLI final refuses hand-edited n_final", c3 == 2 and "przeliczonemu" in _j.load(open(os.path.join(tmp, "f3.json")))["reason"], c3)
        mod = [dict(x) for x in allrecs]; mod[0]["e_end_deg"] += 1.0
        open(data, "w").write("".join(_j.dumps(x) + "\n" for x in mod))
        c4 = cli("--mode", "final", "--data", data, "--frozen", frz, "--stage1-decision", dec, "--out", os.path.join(tmp, "f4.json"))
        check("CLI final refuses modified stage-1 records", c4 == 2, c4)
    finally:
        A.STAGE1_SEEDS, A.CONFIRM_RANGE = sv

    # --- etap 1: zaślepienie
    r = run(make(), mode="stage1")
    keys = set(walk_keys(r))
    forbidden = {"mean", "t_ci95", "bca_ci95", "verdicts", "results", "wilcoxon_p", "S_scalar_mean", "holm_p_benefit"}
    check("stage1 output contains no means/tests/verdicts", not (keys & forbidden), keys & forbidden)
    check("stage1 N_final within [40, 100]", 40 <= r["n_final"] <= 100, r.get("n_final"))
    check("stage1 E1/E2/E3 reported as PASS/FAIL only", r["E3_positive_control"] in ("PASS", "FAIL"))
    r = run(make(noise=12.0), mode="stage1")
    check("stage1 large SD -> N_final capped at 100", r["n_final"] == 100, r["n_final"])
    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
