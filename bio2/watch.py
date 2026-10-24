"""Podgląd na żywo scenariusza A (pamięć obiektu) w przeglądarce MuJoCo.

    ../.venv/bin/mjpython watch.py [seed] [pred|static|none]

Na macOS przeglądarka pasywna wymaga mjpython. Najpierw ok. 30 s kalibracji mózgu, potem pętla 100 Hz
(wolniej niż czas rzeczywisty — siatkówka + sieć impulsowa). Przesłona zasłania piłeczkę; obserwuj, czy ramię
obraca się tam, gdzie piłeczka się wyłoni. Spacja w przeglądarce = pauza.
"""
import sys
import time

import mujoco
import mujoco.viewer

from agent import Agent
from stage3 import setup_A

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 100
memory = sys.argv[2] if len(sys.argv) > 2 else "pred"
m, d, q = setup_A(seed)
print("kalibracja mózgu…")
ag = Agent(m, d, seed=seed, memory=memory, q_catch=q)
with mujoco.viewer.launch_passive(m, d) as v:
    while v.is_running() and d.time < 8.0:
        t0 = time.time()
        with v.lock():
            ag.step()
            for _ in range(10):
                mujoco.mj_step(m, d)
        v.sync()
        time.sleep(max(0.0, 0.01 - (time.time() - t0)))
    print(f"koniec próby (t = {d.time:.1f} s)")
    while v.is_running():
        time.sleep(0.1)
