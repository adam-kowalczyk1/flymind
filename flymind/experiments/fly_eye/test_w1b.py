"""Samosprawdzenie W1b (envs/flyvis lub .venv): podtyp odpowiadający tylko w swoją stronę ma DI = +1, w przeciwną −1."""
import json, os, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w1b
d = tempfile.mkdtemp(); R = {}
for mat in w1b.MATS:
    for k in "RLUD":
        v = np.zeros(8)
        for j, s in enumerate(w1b.SUB):
            pref, null = w1b.PREF[s[-1]]
            v[j] = (k == pref) if s.startswith("T4") else (k == null)        # T4 poprawnie, T5 odwrotnie
        R[f"m7_{mat}_{k}"] = v
np.savez(os.path.join(d, "r.npz"), **R)
sys.stdout = open(os.devnull, "w"); w1b.evaluate(os.path.join(d, "r.npz"), os.path.join(d, "o.json")); sys.stdout = sys.__stdout__
o = json.load(open(os.path.join(d, "o.json")))
assert all(abs(o["DI"]["7"][s] - (1 if s.startswith("T4") else -1)) < 1e-6 for s in w1b.SUB), o["DI"]
assert o["K2b_horizontal"]["frac"] == 0.5 and not o["W1b_pass"]
print("test_w1b OK")
