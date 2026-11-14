"""flymind/v5v4_post_sws_slopes.py — opis wymagany protokołem V5 v4 §9 (N3), PO przebiegu: nachylenia kalibracji (procedura v5v4.calibrate,
pula 5001–5003) 10 pierwszych instancji SWS (ziarna 4001–4010 → +400 000) względem dekodera DATA. Bez prób zachowania.
Uruchom: .venv/bin/python -I -B flymind/v5v4_post_sws_slopes.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from side_shuffle import layer_side_labels, shuffle_within_side  # noqa: E402
from v5v4 import calibrate  # noqa: E402
from visual_path import network  # noqa: E402
spec, idx, _ = network(0.2)
gr, _ = layer_side_labels(spec, idx)
d = calibrate(spec, idx)["slope"]
print(f"DATA {d:.1f} Hz/rad")
for s in range(4001, 4011):
    x = calibrate(shuffle_within_side(spec, gr, s + 400_000), idx)["slope"]
    print(f"SWS ziarno {s}: {x:.1f} Hz/rad ({x / d:.3f} × DATA)", flush=True)
