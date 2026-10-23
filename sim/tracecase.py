"""Przebieg jednej próby wokół szczytu siły (diagnostyka zgnieceń):  python tracecase.py ziarno szum"""
import sys

import numpy as np

from circuit import FlyController
from stage3 import run_trial

seed, d = int(sys.argv[1]), int(sys.argv[2])
fc = FlyController(seed=seed + 100 * d)
r = run_trial(seed, fc, record=True)
L, g, S = r["log"], fc.groups, r["log"]["spikes"]
F = r["F"]
F20 = np.array([np.convolve(F[:, i], np.ones(20) / 20, "same") for i in range(2)]).T
i = int(np.argmax(F20.max(1)))
print(f"ziarno {seed} szum {d}: szczyt20 {F20[i].round(2)} (stała, ruchoma) w t={i / 1000:.3f} s, kontakt {r['contact']}, "
      f"unoszenie {r['t_lift']}, celowanie {r['az_err_deg']:.1f}°")
cls = lambda c: [j for j, cc in fc.mn_class.items() if cc == c]
for k in range(max(0, i // 10 - 10), min(len(L["t"]), i // 10 + 4), 2):
    sp = S[max(0, k - 2):k + 1].reshape(-1, fc.N)
    rr = lambda ids: sp[:, ids].mean() * 1000
    print(f"  t={L['t'][k]:.2f} q={L['q_grip'][k]:.3f} τ={L['torque'][k]:.2f} F={np.round(L['force'][k], 2)} "
          f"dotyk={np.round(L['touch'][k], 1)} τ_baza={L['tau_pan'][k]:+.2f} kulka_z={L['ball'][k][2]:.3f} "
          f"assist={rr(g['RR_assist']):.0f} resist={rr(g['RR_resist']):.0f} hold={rr(g['RR_hold']):.0f} "
          f"MN s/i/f={rr(cls('slow')):.0f}/{rr(cls('int')):.0f}/{rr(cls('fast')):.0f}")
