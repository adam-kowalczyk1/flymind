"""flymind/v7_encoder_distance.py — Etap 7 (ENGINEERING, eksploracja): wyjście enkodera g = (gL, gR) w funkcji odległości ρ
i namiaru celu w renderach MuJoCo (bez SNN, bez sterowania). Sprawdza wyjaśnienie martwej strefy: prąd LC10a = 12 mV·g,
próg ALIF ≈ 7 mV ponad spoczynkiem → LC10a milczą, gdy g < ~0,58 (bez szumu). Uruchom:
.venv/bin/python -I -B flymind/v7_encoder_distance.py"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import loop as L  # noqa: E402
from encoder import TargetEncoder  # noqa: E402
from so101 import SO101Sim  # noqa: E402
sim = SO101Sim()
enc = TargetEncoder(sim.cfg.cam_shape, L.ENC)
print("ρ [m]  az [°]   n_px   gL     gR     max(g)·12 mV")
for rho in (0.16, 0.20, 0.24, 0.28, 0.32, 0.35, 0.40):
    for az in (0.0, 15.0):
        sim.reset(L.Q_POSE, ball_pos=L.place_ball(sim, math.radians(az), rho))
        o = enc.encode(sim.observe().frame.image)
        print(f"{rho:5.2f} {az:6.1f} {o['n_px']:6d} {o['g'][0]:6.3f} {o['g'][1]:6.3f} {12 * o['g'].max():8.2f}")
sim.close()
