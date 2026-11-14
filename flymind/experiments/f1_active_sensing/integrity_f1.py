"""F1 integrity: compare flymind/ (excluding flymind/experiments/), bio2/, data/, assets/ with integrity_pre_snapshot.json taken before any
F1 file existed (2026-11-01 12:55). Read-only. Exit 1 on any changed, added or removed file.
Run: .venv/bin/python -I -B flymind/experiments/f1_active_sensing/integrity_f1.py"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
snap = json.load(open(os.path.join(HERE, "integrity_pre_snapshot.json")))["files"]
now = {}
for top in ("flymind", "bio2", "data", "assets"):
    for d, dirs, fs in os.walk(os.path.join(ROOT, top)):
        rel = os.path.relpath(d, ROOT)
        dirs[:] = sorted(x for x in dirs if x != "__pycache__" and os.path.join(rel, x) != os.path.join("flymind", "experiments"))
        for f in sorted(fs):
            p = os.path.join(d, f)
            now[os.path.relpath(p, ROOT)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
changed = sorted(k for k in snap if k in now and snap[k] != now[k])
added, removed = sorted(set(now) - set(snap)), sorted(set(snap) - set(now))
ok = not (changed or added or removed)
print(f"F1 integrity: {len(now)} files; changed {changed[:5]} added {added[:5]} removed {removed[:5]} → {'OK' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
