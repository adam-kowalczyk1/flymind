"""flymind/audit_shared_decoder.py — czy wspólny dekoder (slope sieci DATA, 495,6 Hz/rad) zmienia efektywne wzmocnienie kontroli?
Nachylenie kalibracji procedurą V4 v2 (spot_clip, az −30…30°, ziarna ALIF 1001–1003) dla instancji tasowań. Pętla otwarta,
bez nowych prób zachowania. Uruchom: .venv/bin/python -I -B flymind/audit_shared_decoder.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loop_v2 as L2  # noqa: E402
from side_shuffle import layer_side_labels, shuffle_within_side  # noqa: E402
from visual_path import network, shuffle  # noqa: E402
spec, idx, _ = network(0.2)
gr, _ = layer_side_labels(spec, idx)
print("DATA", L2.calibrate_v4v2(spec, idx))
for s in (3001, 3002, 3003):                                  # instancje SHUF_STR z V5 v2 (ziarno + 200 000)
    print("SHUF_STR (V5 v2)", s, L2.calibrate_v4v2(shuffle(spec, s + 200_000, equal_weight=True), idx))
for s in (1401, 1402):
    print("SHUF_WITHIN_SIDE v2 (dev)", s, L2.calibrate_v4v2(shuffle_within_side(spec, gr, s), idx))
