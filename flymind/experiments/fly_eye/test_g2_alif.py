"""Sprawdzenie: batched_net (M przebiegów naraz) daje te same impulsy co zwykły SparseALIF dla każdej kolumny osobno."""
import os
import sys
from types import SimpleNamespace

import numpy as np
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g2_alif as A  # noqa: E402

rng = np.random.default_rng(23501099)
N, M, T = 60, 3, 400
W = sp.random(N, N, density=0.1, random_state=1, data_rvs=lambda k: rng.normal(0, 3, k)).tocsr()
I = A.I_BIAS + 4 * rng.standard_normal((T, N, M))
net = A.batched_net(W, M)
batch = np.stack([net.step(I[t]) for t in range(T)])
assert batch.any() and not batch.all()
for m in range(M):
    single = A.SparseALIF(SimpleNamespace(W=W), A.P, None).run(I[:, :, m], T)
    assert (single == batch[:, :, m]).all(), m
print("OK: batched == SparseALIF dla", M, "kolumn,", int(batch.sum()), "impulsów")
