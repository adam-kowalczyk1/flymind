"""Testy enkodera obraz → napęd LC10a (syntetyczne, bez mujoco). Uruchom: .venv/bin/python -I -B flymind/test_encoder.py"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from encoder import EncoderParams, TargetEncoder, column_azimuth  # noqa: E402
from sensory import project, spot_clip  # noqa: E402

SH, FG, BG = (96, 128), (40, 180, 50), (120, 120, 120)
spot = lambda az, fg=FG, bg=BG: spot_clip(np.radians([az]), [0.0], SH, 70.0, 9, fg, bg).images[0]
n = 0
for blur in (0, 3):
    enc = TargetEncoder(SH, EncoderParams(blur_px=blur))
    g = lambda im: enc.encode(im)["g"]
    assert (g(np.full((*SH, 3), BG, np.uint8)) == 0).all() and (g(None) == 0).all(); n += 1          # brak bodźca
    assert (g(np.zeros((*SH, 3), np.uint8)) == 0).all(); n += 1                                       # czarny obraz
    L, R, C = g(spot(20)), g(spot(-20)), g(spot(0))
    assert L[0] > 2 * L[1] and R[1] > 2 * R[0]; n += 1                                                # strona
    assert abs(C[0] - C[1]) < 0.05 * C.sum(); n += 1                                                  # środek ≈ symetria
    assert np.allclose(g(spot(20)), g(spot(-20))[::-1], atol=0.02); n += 1                            # lustro
    assert (g(spot(20, (200, 40, 40))) == 0).all(); n += 1                                            # czerwony ignorowany
    assert np.allclose(g(spot(15, (20, 90, 25), (60, 60, 60))), g(spot(15)), atol=0.02); n += 1       # Weber: oświetlenie ×0,5
    assert (g(spot(60)) == 0).all(); n += 1                                                           # poza polem widzenia
az = column_azimuth(128, 96, 70.0)
u, _ = project(az, np.zeros_like(az), SH, 70.0)
assert np.allclose(u, np.arange(128) + 0.5); n += 1                                                   # odwrotność project
assert az[0] > 0 > az[-1] and abs(math.degrees(az[0])) < 44; n += 1                                   # + w lewo, FOV ±43°
try:
    TargetEncoder(SH).encode(np.zeros((10, 10, 3), np.uint8)); raise AssertionError
except ValueError:
    n += 1
print(f"OK: enkoder ({n} asercji)")
