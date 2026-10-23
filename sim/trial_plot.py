"""Wykres przebiegu jednej próby Etapu 3:  python trial_plot.py [seed] [plik.png]"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from circuit import FlyController
from stage3 import run_trial, F_CRUSH, F_SECURE

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
out = sys.argv[2] if len(sys.argv) > 2 else f"../results/trial_{seed}.png"
fc = FlyController(seed=seed)
r = run_trial(seed, fc, record=True)
L = r["log"]
t = L["t"]
fig, ax = plt.subplots(6, 1, figsize=(11, 13), sharex=True)
ax[0].plot(t, np.degrees(L["theta"]), label="azymut kulki")
ax[0].set_ylabel("azymut [°]")
ax0b = ax[0].twinx()
ax0b.plot(t, L["yaw"], "C1", label="obrót bazy")
ax0b.set_ylabel("ω bazy [rad/s]", color="C1")
ax[1].plot(t, L["ball"][:, 0], label="x")
ax[1].plot(t, L["ball"][:, 1], label="y")
ax[1].plot(t, L["ball"][:, 2], label="z")
ax[1].legend(fontsize=8)
ax[1].set_ylabel("kulka [m]")
tm = np.arange(len(r["F"])) / 1000
ax[2].plot(tm, r["F"][:, 0], label="szczęka stała")
ax[2].plot(tm, r["F"][:, 1], label="szczęka ruchoma")
ax[2].axhline(F_CRUSH, color="r", ls="--", lw=0.8, label="zgniecenie")
ax[2].axhline(F_SECURE, color="g", ls="--", lw=0.8)
ax[2].set_ylabel("siła kontaktu [N]")
ax[2].legend(fontsize=8)
ax[3].plot(t, L["touch"], lw=0.8)
ax[3].set_ylabel("czujniki touch [N]")
ax[3].legend(["stała", "ruchoma", "dłoń"], fontsize=8)
ax[4].plot(t, L["torque"], "C3")
ax[4].set_ylabel("moment SNN [N·m]")
ax[5].plot(t, L["q_grip"], "k", label="kąt szczęki [rad]")
ax[5].plot(t, L["tau_pan"], "C4", label="moment serwa bazy [N·m]")
ax[5].legend(fontsize=8)
ax[5].set_xlabel("czas [s]")
fig.suptitle(f"próba {seed}: sukces={r['success']} szczyt={r['peak_force']:.2f} N reakcja={r['reaction_ms']}")
fig.tight_layout()
fig.savefig(out, dpi=110)
print(out, {k: v for k, v in r.items() if k not in ("log", "F")})
