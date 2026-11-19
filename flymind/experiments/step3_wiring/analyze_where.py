"""Kryteria W1–W3 z LOOP_TARGET_where_r1.md. Uruchom: analyze_where.py where_r1.json"""
import json
import sys

import numpy as np

R = json.load(open(sys.argv[1]))
raw = lambda k, w: np.array(R[k]["raw"][str(w)])  # noqa: E731
ok1 = ok2 = ok3 = True
for g in ("-1", "+1"):
    s = R[f"N|somato|glu{g}"]
    X = np.vstack([raw(f"N|somato|glu{g}", 0), raw(f"N|somato|glu{g}", 1)])
    sd = np.maximum(X.std(0), 1.0)
    z = lambda v: np.asarray(v) / sd  # noqa: E731
    d_som = np.linalg.norm(z(raw(f"N|somato|glu{g}", 0).mean(0)) - z(raw(f"N|somato|glu{g}", 1).mean(0)))
    d_mir = np.linalg.norm(z(raw(f"N|swap|glu{g}", 0).mean(0)) - z(raw(f"N|somato|glu{g}", 1).mean(0)))
    w1 = s["acc"] >= 0.95 and s["dprime"] >= 3
    w2 = d_mir < 0.25 * d_som
    w3 = R[f"N|somato_bal|glu{g}"]["acc"] >= 0.95
    ok1, ok2, ok3 = ok1 and w1, ok2 and w2, ok3 and w3
    print(f"glu{g}: W1 acc {s['acc']:.2f} d' {s['dprime']:.1f} -> {w1} | W2 lustro {d_mir:.2f} vs 0.25*{d_som:.2f} -> {w2} | W3 bal acc {R[f'N|somato_bal|glu{g}']['acc']:.2f} -> {w3}")
print("W1", ok1, "W2", ok2, "W3", ok3)
for k, v in R.items():
    print(f"{k:28s} acc {v['acc']:.2f} d' {v['dprime']:5.1f}  A0 {v['m0']}  A1 {v['m1']}")
