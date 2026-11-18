"""flymind/v5v3_post_slopes.py — opis wymagany protokołem V5 v3 r3 §5 (po przebiegu): nachylenie kalibracji V4 v2 (pętla otwarta,
spot_clip, ziarna ALIF 1001–1003) dla 5 pierwszych instancji każdej kontroli (ziarna prób 3051–3055 → instancje +400 000 / +200 000).
Tylko struktura sieci i odpowiedź otwarta; bez prób zachowania. Uruchom: .venv/bin/python -I -B flymind/v5v3_post_slopes.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loop_v2 as L2  # noqa: E402
from side_shuffle import layer_side_labels, shuffle_within_side  # noqa: E402
from visual_path import network, shuffle  # noqa: E402

spec, idx, _ = network(0.2)
gr, _ = layer_side_labels(spec, idx)
print("DATA", round(L2.calibrate_v4v2(spec, idx)["slope"], 1))
for s in range(3051, 3056):
    a = L2.calibrate_v4v2(shuffle_within_side(spec, gr, s + 400_000), idx)["slope"]
    b = L2.calibrate_v4v2(shuffle(spec, s + 200_000, equal_weight=True), idx)["slope"]
    print(f"ziarno {s}: SHUF_WITHIN_SIDE {a:6.1f}  SHUF_STR {b:6.1f}  [Hz/rad]", flush=True)
