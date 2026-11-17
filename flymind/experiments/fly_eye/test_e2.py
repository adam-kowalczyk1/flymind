"""Sprawdzenie e2_lpi.readout_lpi przed testem (envs/flyvis lub .venv z torch): bez krawędzi LPi = w5_and.readout; silne LPi gasi AND."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_lpi as E  # noqa: E402
import w5_and as W  # noqa: E402

assert E.out_layers("LPi43") == [3] and E.out_layers("LPi3412") == [1, 2] and E.out_layers("LPi2c") == [2] and E.out_layers("LPi14") == [4]
rng = np.random.default_rng(0)
# 2 komórki: 0 = LPLC2, 1 = LPi34 (wyjście warstwa 4 → ramię d)
M = dict(post=np.arange(2), post_type=np.array(["LPLC2", "LPi34"]), in_post=np.array([0, 0, 0, 0, 1, 1]), in_sub=np.array([0, 1, 2, 3, 2, 6]),
         in_w=np.array([5., 5, 5, 5, 3, 1]), vv_pre=np.array([1]), vv_post=np.array([0]), vv_w=np.array([1e6]), vv_sign=np.array([-1.]))
A = rng.random((7, 8, 3)); ci = np.zeros(6, int); ok = np.ones(6, bool)
none = (np.zeros(0, int), np.zeros(0, int), np.zeros(0))
assert np.allclose(E.readout_lpi(A, M, ci, ok, none), W.readout(A, M, ci, ok)[0], atol=1e-5)
ea, ek, ew = E.inhibition_edges(M)
assert ea.tolist() == [1] and ek.tolist() == [3] and ew.tolist() == [1e6]
pk = E.readout_lpi(A, M, ci, ok, (ea, ek, ew))
assert np.allclose(pk[1, :, 0], 0) and (pk[0, 0, 0] < W.readout(A, M, ci, ok)[0][0, 0, 0])
print("test_e2 OK")
