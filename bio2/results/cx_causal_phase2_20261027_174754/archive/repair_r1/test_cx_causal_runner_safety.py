#!/usr/bin/env python3
"""Testy bezpieczeństwa i regresji runnera test_cx_causal_memory.py (ziarno DEV 233; katalogi tymczasowe; bez 300–399/0–39).
Użycie: test_cx_causal_runner_safety.py DEV4_JSONL_DIR"""
import glob
import hashlib
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_cx_causal_memory as R

H = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
OK = True


def check(name, cond, info=""):
    global OK
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  -> {info}"))
    OK &= bool(cond)


def run(argv):
    """Uruchom main(); zwróć (kod/komunikat SystemExit lub None)."""
    saved = dict(R.CFG)
    try:
        R.main(argv)
        return None
    except SystemExit as e:
        return e.code
    finally:
        R.CFG.clear(); R.CFG.update(saved)


def recs(p):
    return [json.loads(l) for l in open(p)]


def main(dev_dir):
    dev4 = {(r["arm"], r["seed"], r["passive_deg"]): r for f in glob.glob(os.path.join(dev_dir, "expA2_dev4_*.jsonl")) for r in recs(f)}
    tmp = tempfile.mkdtemp(prefix="runner_safety_")
    out = os.path.join(tmp, "new_dir", "sub", "ds.jsonl")             # katalogi nie istnieją
    base = ["--run", "--seeds", "233", "--passive=0", "--jump", "--no-log", "--out", out, "--dataset-id", "SAFETY-TEST"]
    A1 = ["--arms", "Scalar,CX-DN-Pulse+30"]

    code = run(base + A1)
    check("C-dir: missing output directories are created", code is None and os.path.exists(out), code)
    rs = recs(out)
    same = all(r["e_end_deg"] == dev4[(r["arm"], 233, 0.0)]["e_end_deg"] and r["snaps"] == dev4[(r["arm"], 233, 0.0)]["snaps"]
               for r in rs)
    check("D-regression: hardened runner reproduces dev4 trials bit-identically (e_end + snaps)", same and len(rs) == 2,
          [(r["arm"], r["e_end_deg"]) for r in rs])
    man = json.load(open(out + ".manifest.json"))
    check("C-manifest: dataset_id, protocol v4, runner/cfg hash, arms, Δ, jump stored",
          man["dataset_id"] == "SAFETY-TEST" and man["protocol_version"] == "v4" and man["runner_sha256"] == R.runner_sha256()
          and man["cfg_sha256"] == R.cfg_sha256(R.CFG) and man["jump"] is True and man["arms"] == ["Scalar", "CX-DN-Pulse+30"])
    check("C-provenance: every record carries dataset_id/protocol/runner/cfg hash",
          all(r["dataset_id"] == "SAFETY-TEST" and r["protocol_version"] == "v4" and r["runner_sha256"] == man["runner_sha256"]
              and r["cfg_sha256"] == man["cfg_sha256"] for r in rs))
    check("C-lock: lock file removed after normal run", not os.path.exists(out + ".lock"))
    h0 = H(out)

    code = run(base + A1)
    check("C-resume: identical command adds no trials (no duplicates)", code is None and H(out) == h0 and len(recs(out)) == 2, code)
    code = run(base + A1 + ["--lambda-cx", "0.5"])
    check("C-mismatch: changed parameter (--lambda-cx) refused, file unchanged", isinstance(code, str) and "manifest" in code and H(out) == h0, code)
    code = run([x for x in base if x != "--jump"] + A1)
    check("C-mismatch: missing --jump refused, file unchanged", isinstance(code, str) and "jump" in code and H(out) == h0, code)
    code = run(base + ["--arms", "Scalar"])
    check("C-mismatch: different arm list refused", isinstance(code, str) and "arms" in code and H(out) == h0, code)
    code = run([("OTHER-ID" if x == "SAFETY-TEST" else x) for x in base] + A1)
    check("C-mismatch: different dataset_id refused", isinstance(code, str) and "dataset_id" in code and H(out) == h0, code)

    open(out + ".lock", "w").write("pid=0\n")
    code = run(base + A1)
    check("C-lock: existing lock -> refused (single writer)", isinstance(code, str) and "zablokowany" in code and H(out) == h0, code)
    os.remove(out + ".lock")

    orphan = os.path.join(tmp, "orphan.jsonl"); shutil.copy(out, orphan)
    code = run([orphan if x == out else x for x in base] + A1)
    check("C-manifest: data file without manifest refused", isinstance(code, str) and "bez manifestu" in code, code)

    bad = os.path.join(tmp, "badhash.jsonl"); shutil.copy(out, bad); shutil.copy(out + ".manifest.json", bad + ".manifest.json")
    rr = recs(bad); rr[0]["runner_sha256"] = "0" * 64
    open(bad, "w").write("".join(json.dumps(x) + "\n" for x in rr))
    code = run([bad if x == out else x for x in base] + A1)
    check("C-provenance: record with foreign runner hash refused", isinstance(code, str) and "runner_sha256" in code, code)

    dup = os.path.join(tmp, "dup.jsonl"); shutil.copy(out + ".manifest.json", dup + ".manifest.json")
    open(dup, "w").write(open(out).read() + open(out).read().splitlines(True)[0])
    code = run([dup if x == out else x for x in base] + A1)
    check("C-duplicate: duplicated record in file refused", isinstance(code, str) and "zduplikowany" in code, code)

    tr = os.path.join(tmp, "trunc.jsonl"); shutil.copy(out + ".manifest.json", tr + ".manifest.json")
    open(tr, "w").write(open(out).read() + '{"arm": "Freeze", "seed": 23')
    ht = H(tr)
    code = run([tr if x == out else x for x in base] + ["--arms", "Scalar,CX-DN-Pulse+30"])
    check("C-truncated: incomplete last record -> refused, file unchanged", isinstance(code, str) and "niepełny" in code and H(tr) == ht, code)
    code = run([tr if x == out else x for x in base] + A1 + ["--repair-truncated"])
    origs = glob.glob(tr + ".orig-*"); reps = glob.glob(tr + ".repair-*.json")
    check("C-truncated: --repair-truncated keeps original copy + report, keeps all complete records",
          code is None and len(origs) == 1 and H(origs[0]) == ht and len(reps) == 1 and len(recs(tr)) == 2
          and json.load(open(reps[0]))["removed_bytes"] == len('{"arm": "Freeze", "seed": 23'), (code, origs, reps))

    mid = os.path.join(tmp, "mid.jsonl"); shutil.copy(out + ".manifest.json", mid + ".manifest.json")
    L = open(out).read().splitlines(True); open(mid, "w").write("{broken\n" + "".join(L))
    hm = H(mid)
    code = run([mid if x == out else x for x in base] + A1 + ["--repair-truncated"])
    check("C-corrupt: corrupted non-final line refused even with --repair-truncated, file unchanged",
          isinstance(code, str) and "uszkodzony" in code and H(mid) == hm, code)

    # trwały zapis błędu kalibracji
    calout = os.path.join(tmp, "calib", "ds.jsonl")
    real = R.calibrated_brain
    R.calibrated_brain = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthetic calibration failure"))
    try:
        code = run(["--run", "--seeds", "233", "--passive=0", "--jump", "--no-log", "--out", calout, "--dataset-id", "CAL",
                    "--arms", "CX-Bump,Freeze,CX-DN"])
    finally:
        R.calibrated_brain = real
    cr = {r["arm"]: r for r in recs(calout)}
    check("C-calibration: failure persisted as TECHNICAL_FAILURE for every CX arm, run continues for Freeze",
          code is None and cr["CX-Bump"]["status"] == "TECHNICAL_FAILURE" and "kalibracja" in cr["CX-Bump"]["reason"]
          and cr["CX-DN"]["status"] == "TECHNICAL_FAILURE" and cr["Freeze"]["status"] == "OK"
          and all(r["dataset_id"] == "CAL" for r in cr.values()), {a: (r["status"], r.get("reason", "")[:40]) for a, r in cr.items()})

    code = run(["--run", "--seeds", "5", "--out", os.path.join(tmp, "h.jsonl"), "--dataset-id", "H", "--arms", "Freeze"])
    check("C-guard: held-out seed refused", isinstance(code, str) and "held-out" in code, code)
    code = run(["--run", "--seeds", "233", "--out", os.path.join(tmp, "n.jsonl"), "--arms", "Freeze"])
    check("C-guard: --dataset-id required", isinstance(code, str) and "dataset-id" in code, code)
    code = run(["--run", "--seeds", "233", "--out", os.path.join(tmp, "u.jsonl"), "--dataset-id", "U", "--arms", "Freeze,Bogus"])
    check("C-guard: unknown arm refused", isinstance(code, str) and "ramiona" in code, code)
    ds = R.Dataset(os.path.join(tmp, "x", "y.jsonl"), dict(dataset_id="X", protocol_version="v4", runner_sha256="r", cfg_sha256="c",
                                                         jump=True, moving=False, arms=["Freeze"], passive=[0.0], no_log=True)).__enter__()
    ds.append(dict(arm="Freeze", seed=233, passive_deg=0.0))
    try:
        ds.append(dict(arm="Freeze", seed=233, passive_deg=0.0)); dup_ok = False
    except R.DatasetError:
        dup_ok = True
    ds.__exit__(None, None, None)
    check("C-duplicate: in-run duplicate append refused", dup_ok)
    print(f"temp dir: {tmp}")
    print("RUNNER SAFETY " + ("PASS" if OK else "FAIL"))
    return OK


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1]) else 1)
