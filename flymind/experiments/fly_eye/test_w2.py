"""Samosprawdzenie odczytu W2 (envs/flyvis): macierz układu prawdziwego i permutacji, znak, prostowanie."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from w2_run import NCOL, perms, readout_mats

M = dict(post=np.array([7, 9]), in_post=np.array([0, 0, 1]), in_type=np.array(["A", "B", "B"]), in_u=np.array([0, 0, 1]),
         in_v=np.array([0, 0, 0]), in_inside=np.array([True, True, True]), in_w=np.array([2.0, 3.0, 5.0]), in_sign=np.array([1.0, -1.0, -1.0]))
types, mats = readout_mats(M, {(0, 0): 0, (1, 0): 1})
assert types == ["A", "B"] and len(mats) == 24
rel = np.zeros(2 * NCOL); rel[0] = 1.0; rel[NCOL] = 10.0; rel[NCOL + 1] = 1.0      # A kol.0 = 1; B kol.0 = 10, kol.1 = 1
d = mats[0] @ rel
assert np.allclose(d, [2 * 1 - 3 * 10, -5 * 1]), d                                  # pobudzenie A, hamowanie B
swapped = [m @ rel for p, m in zip(perms(2), mats) if list(p) == [1, 0]]
assert swapped and np.allclose(swapped[0], [-2 * 10 + 3 * 1, 5 * 0]), swapped[:1]   # etykiety zamienione, znak idzie za źródłem
print("test_w2 OK")
