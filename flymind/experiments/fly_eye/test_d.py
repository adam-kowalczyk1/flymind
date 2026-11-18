"""Sprawdzenie bodźców d_ideal przed testem (envs/flyvis): tekstura ~50 % jasna, ruch przesuwa wzór, obrót o 0 = brak zmiany."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v1_camera_input"))
import d_ideal as D  # noqa: E402

g = np.mgrid[-15:16, -15:16].reshape(2, -1).T.astype(float)
f = D.texture(D.SEEDS[0], g)
assert 0.3 < f(g).mean() < 0.7
assert np.array_equal(f(g - [1.0, 0]), f(g + [-1.0, 0]))
sm = D.self_motion(g, D.SEEDS[0], 5, 2, 1)
assert set(sm) == {f"{m}_s{D.SEEDS[0]}" for m in D.MOVES} and all(v.shape == (8, len(g)) for v in sm.values())
r = sm[f"roll+_s{D.SEEDS[0]}"]; assert np.array_equal(r[0], r[2]) and not np.array_equal(r[2], r[-1])   # klatka ruchu 0 = θ 0
t = sm[f"tr0_s{D.SEEDS[0]}"]; assert np.array_equal(t[2], f(g + [8.0, 0]))                             # start: wzór przesunięty o −8
print("test_d OK")
