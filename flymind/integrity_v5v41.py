"""flymind/integrity_v5v41.py — integrity snapshot for the V5 v4.1+ research programme (2026-10-30). Read-only except --out.

Checks (CONTROL / ENGINEERING, no science):
  stage1    sha256 of the 28 Stage 1 files listed in bio2/results/cx_causal_phase2_20261027_174754/frozen_manifest_v4.json
  manifests code hashes of validation/v5v3_manifest.json and v5v4_manifest.json vs current files (frozen code must not change)
  protected sha256 of every file under bio2/, assets/, data/, flymind/validation/, flymind/results/v5v3/, flymind/results/v5v4/,
            plus loop.py, loop_v2.py, V5v4_FINAL_REPORT.md (tree hash + per-file hashes)
  pycache   bio2/__pycache__ mtime (a write would mean someone imported bio2 without -B)
Usage:
  .venv/bin/python -I -B flymind/integrity_v5v41.py --snapshot flymind/results/v5v41/integrity_baseline.json
  .venv/bin/python -I -B flymind/integrity_v5v41.py --compare flymind/results/v5v41/integrity_baseline.json --label after_X
"""
import argparse
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STAGE1 = os.path.join(ROOT, "bio2", "results", "cx_causal_phase2_20261027_174754", "frozen_manifest_v4.json")
TREES = ["bio2", "assets", "data", "flymind/validation", "flymind/results/v5v3", "flymind/results/v5v4"]
FILES = ["flymind/loop.py", "flymind/loop_v2.py", "flymind/V5v4_FINAL_REPORT.md", "flymind/V5v4_STAGE_A_AUDIT.md"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def stage1():
    m = json.load(open(STAGE1))
    files = dict(m["deps_sha256"], **{m[k]: m[k + "_sha256"] for k in ("runner", "analysis", "analysis_selftest", "runner_safety_test")})
    bad = [p for p, h in files.items() if sha(os.path.join(ROOT, p)) != h]
    return dict(n=len(files), ok=len(files) - len(bad), mismatched=bad, manifest_sha256=sha(STAGE1))


def manifests():
    out = {}
    for name in ("v5v3_manifest.json", "v5v4_manifest.json"):
        m = json.load(open(os.path.join(HERE, "validation", name)))
        bad = [f for f, h in m["code_sha256"].items() if sha(os.path.join(HERE, f)) != h]
        out[name] = dict(n=len(m["code_sha256"]), mismatched=bad)
    return out


def protected():
    per = {}
    for t in TREES:
        for d, dirs, fs in os.walk(os.path.join(ROOT, t)):
            dirs[:] = sorted(x for x in dirs if x != "__pycache__")
            for f in sorted(fs):
                p = os.path.join(d, f)
                per[os.path.relpath(p, ROOT)] = sha(p)
    for f in FILES:
        per[f] = sha(os.path.join(ROOT, f))
    tree = hashlib.sha256("".join(f"{k}{v}" for k, v in sorted(per.items())).encode()).hexdigest()
    return tree, per


def snapshot():
    tree, per = protected()
    pc = os.path.join(ROOT, "bio2", "__pycache__")
    return dict(time=time.strftime("%Y-%m-%dT%H:%M:%S"), stage1=stage1(), manifests=manifests(), protected_tree_sha256=tree,
                protected_n=len(per), protected=per, bio2_pycache_mtime=os.path.getmtime(pc) if os.path.exists(pc) else None)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--snapshot")
    ap.add_argument("--compare")
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    s = snapshot()
    line = (f"{s['time']} [{a.label}] Stage 1 {s['stage1']['ok']}/{s['stage1']['n']}; manifests "
            + ", ".join(f"{k} {v['n'] - len(v['mismatched'])}/{v['n']}" for k, v in s["manifests"].items())
            + f"; protected files {s['protected_n']} tree {s['protected_tree_sha256'][:16]}")
    if a.snapshot:
        with open(a.snapshot, "x") as f:
            json.dump(s, f, indent=1)
        print(line, "| baseline written")
    if a.compare:
        b = json.load(open(a.compare))
        changed = sorted(k for k in set(b["protected"]) | set(s["protected"]) if b["protected"].get(k) != s["protected"].get(k))
        ok = (not changed and s["stage1"]["ok"] == s["stage1"]["n"] == 28
              and not any(v["mismatched"] for v in s["manifests"].values()) and s["bio2_pycache_mtime"] == b["bio2_pycache_mtime"])
        print(line, f"| vs baseline: changed {len(changed)} {changed[:10]} pycache {'same' if s['bio2_pycache_mtime'] == b['bio2_pycache_mtime'] else 'CHANGED'}"
              f" | {'INTEGRITY OK' if ok else 'INTEGRITY FAIL'}")
        sys.exit(0 if ok else 1)
