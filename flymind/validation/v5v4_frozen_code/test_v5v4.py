"""Testy techniczne V5 v4 r2 (bez pętli zamkniętej): sceny, reguły decyzji, analiza na danych syntetycznych, wznowienie, odmowy.
Syntetyczne RNG: ziarno 7101 (poza pulami eksperymentów). Uruchom: .venv/bin/python -I -B flymind/test_v5v4.py"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v5v4 import CONDS, CONFIRM, FORBIDDEN, STRATA, analyze, append_record, h1_category, holm, load_done, perm_test, read_records, trial_spec_v4  # noqa: E402

n = 0
specs = [trial_spec_v4(s) for s in CONFIRM]
assert sum(t["stratum"] == "S1" for t in specs) == 150 and sum(t["stratum"] == "S2" for t in specs) == 300; n += 1
assert all(STRATA[t["stratum"]][0] <= t["rho"] < STRATA[t["stratum"]][1] and -30 <= t["az0_deg"] <= 30 for t in specs); n += 1
assert trial_spec_v4(4001) == trial_spec_v4(4001) and trial_spec_v4(4001) != trial_spec_v4(4002); n += 1
assert not (set(CONFIRM) & FORBIDDEN) and {0, 39, 300, 399, 1500, 2050, 3075} <= FORBIDDEN; n += 1
assert np.allclose(holm([0.01, 0.04]), [0.02, 0.04]) and perm_test(np.zeros(20)) == 1.0 and perm_test(-np.ones(30)) < 1e-4; n += 1
c = lambda lo, hi, m, p, tlo=None, thi=None: h1_category(dict(ci95=[lo, hi], ci95_t=[lo if tlo is None else tlo, hi if thi is None else thi], mean_d=m), p)
assert c(-0.3, 0.2, -0.05, 0.5) == "równoważne w granicach ±SESOI"; n += 1
assert c(-0.3, 0.2, -0.05, 0.5, tlo=-0.55) == "nie wykazano ani różnicy, ani równoważności"; n += 1      # oba CI muszą być w ±SESOI
assert c(-1.6, -0.6, -1.1, 0.001) == "DATA lepsza, efekt ≥ SESOI"; n += 1
assert c(-0.45, -0.05, -0.25, 0.01) == "DATA lepsza, efekt < SESOI (praktycznie pomijalny)"; n += 1
assert c(-0.8, -0.1, -0.4, 0.01) == "DATA lepsza, wielkość względem SESOI nieustalona"; n += 1
assert c(0.6, 1.4, 1.0, 0.01) == "kontrola lepsza, efekt ≥ SESOI"; n += 1
assert c(-0.9, 0.3, -0.3, 0.3) == "nie wykazano ani różnicy, ani równoważności"; n += 1
rng = np.random.default_rng(7101)
recs = []
for t in specs:
    base = rng.uniform(1, 8)
    off = dict(DATA=0.0, SWS=(1.0 if t["stratum"] == "S2" else 0.0) + rng.normal(0, 0.05), STR_OWN=1.5, STR_SHARED=3.0, TOY=0.8, P=-3.0)
    conds = {k: dict(final_abs_err=max(0.0, base + v), success=bool(rng.random() < 0.5), error=None, slope=490.0, t_first_within=0.3,
                     overshoot_deg=1.0) for k, v in off.items()}
    if t["seed"] == 4010:
        conds["STR_OWN"]["error"] = "SimError"
    if t["seed"] == 4011:
        conds["STR_OWN"]["calibration_refused"] = True
    recs.append(dict(t, conds=conds))
a = analyze(recs, list(CONFIRM))
assert a["excluded_seeds"] == [4010] and a["n_analyzed"] == 449; n += 1
assert a["H1"]["per_stratum"]["S2"]["category"] == "DATA lepsza, efekt ≥ SESOI" and a["H1"]["per_stratum"]["S1"]["category"].startswith("równoważne"); n += 1
assert a["H2"]["H2a"]["significant"] and a["H2"]["H2b"]["mean_d"] > 1.4 and a["H2"]["interpretable"]; n += 1
assert a["H2"]["sensitivity_without_refused"]["seeds"] == [4011] and set(a["sensitivity_H1_excluded"]) == {"S1"}; n += 1
assert set(a["H1"]["subbands_descriptive"]) == {"S2a", "S2b"} and set(a["H1"]["regression_descriptive"]) == {"const", "rho_m", "abs_az_deg"}; n += 1
assert set(a["conds"]) == set(CONDS) and "DATA-SWS" in a["aux"]["success_mcnemar"]; n += 1
for bad_input in (recs + [recs[0]], recs[:-1]):                       # duplikat ziarna; brakujące ziarno
    try:
        analyze(bad_input, list(CONFIRM))
        raise AssertionError("brak STOP analizy")
    except ValueError:
        n += 1
with tempfile.TemporaryDirectory() as d:                              # wznowienie: linia uszkodzona → ziarno do powtórki
    p = os.path.join(d, "raw.jsonl")
    with open(p, "w") as f:
        f.write(json.dumps(dict(seed=4001)) + "\n" + json.dumps(dict(seed=4002)) + "\n" + '{"seed": 4003, "conds": {"DA')
    assert load_done(p) == {4001, 4002}; n += 1
    append_record(p, dict(seed=4003, conds={}))                      # RT r2 N7: domknięcie uciętej linii
    recs2, nbad = read_records(p)
    assert [r["seed"] for r in recs2] == [4001, 4002, 4003] and nbad == 1; n += 1
r = subprocess.run([sys.executable, "-I", "-B", os.path.join(os.path.dirname(os.path.abspath(__file__)), "v5v4.py"), "--seeds", "1001-1002",
                    "--out", "/tmp", "--shard", "x", "--approved-protocol-sha256", "x"], capture_output=True, text=True)
assert r.returncode != 0 and "odmowa" in (r.stdout + r.stderr); n += 1
r = subprocess.run([sys.executable, "-I", "-B", os.path.join(os.path.dirname(os.path.abspath(__file__)), "v5v4.py"), "--seeds", "6001-6002",
                    "--out", "/tmp", "--approved-protocol-sha256", "x"], capture_output=True, text=True)
assert r.returncode != 0 and "odmowa" in (r.stdout + r.stderr); n += 1                    # RT r2 N9: brak --shard / protokołu
print(f"OK: V5 v4 r2 testy techniczne ({n} asercji)")
