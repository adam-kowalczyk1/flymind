"""Test „placebo” odruchów dotyku (PREREG_PLACEBO.md). Nakładka na reflex.py/loud.py — tamtych plików nie zmienia.
Uruchom: placebo.py CALIB.json|none M <argumenty reflex.py>   (wzmocnienie = g z kalibracji (tasowania) lub 1 (dane) razy M)"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loud as L  # noqa: E402
import reflex as R  # noqa: E402

calib, m = sys.argv[1], float(sys.argv[2])
del sys.argv[1:3]
g = 1.0
if calib != "none":
    s = int(sys.argv[sys.argv.index("--shuffle-seed") + 1])
    g = json.load(open(calib))["nets"][str(s)]["gain"]
R.TwoNet = lambda glu, kind, seed, rule="pre": L.GainNet(glu, kind, seed, rule, gain=g * m)
R.main()
