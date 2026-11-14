"""flymind/test_v5v41.py — checks of the V5 v4.1 engine against frozen alif.ALIF (no mujoco). Run: .venv/bin/python -I -B flymind/test_v5v41.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alif import ALIF, ALIFParams  # noqa: E402
from decoder import SteerDecoder  # noqa: E402
import v5v41 as V  # noqa: E402

spec, idx, gr, _ = V.make_net("DATA", None)
P = ALIFParams(noise=2.0)
N = len(spec.bodies)
SEED = 8_490_050                      # smoke pool

# T1 step: counts equal to a direct alif.ALIF.run with the same current matrix and seed
cfg = dict(I=8.0, step_ms=300)
r = V.simulate(spec, idx, "L", cfg, SEED, P)
I = np.zeros((300, N)); I[:, idx["in_L"]] = 8.0
s = ALIF(spec, P, SEED).run(I, 300)
c = s.reshape(30, 10, N)
assert np.array_equal(r["counts"][:, 0], c[:, :, idx["in_L"]].sum((1, 2))), "T1 in_ipsi"
assert np.array_equal(r["counts"][:, 4], c[:, :, idx["DNa02_L"]].sum((1, 2))), "T1 dn_L"
assert np.array_equal(r["counts"][:, 3], c[:, :, idx["mid_R"]].sum((1, 2))), "T1 mid_R"
fd = np.flatnonzero(s[:, idx["DNa02_L"][0]])
assert r["first_dn"] == (fd[0] if len(fd) else -1), "T1 first spike"
# T2 decoder chain identical to SteerDecoder fed the same chunks
d = SteerDecoder({"DNa02_L": idx["DNa02_L"], "DNa02_R": idx["DNa02_R"]}, ("DNa02",), [0.0], [V.DEC_SLOPE], V.STEER)
ang = [d.step(c[b], 1.0)["angle"][0] for b in range(30)]
assert np.allclose(r["angle"], ang, atol=1e-6), "T2 decoder"
# T3 pre-drive on contra side then step: currents placed correctly
cfg = dict(I=7.0, step_ms=200, pre_ms=100, pre_side="contra", pre_mV=10.0)
r = V.simulate(spec, idx, "R", cfg, SEED, P)
I = np.zeros((300, N)); I[:100, idx["in_L"]] = 10.0; I[100:, idx["in_R"]] = 7.0
s = ALIF(spec, P, SEED).run(I, 300).reshape(30, 10, N)
assert np.array_equal(r["counts"][:, 0], s[:, :, idx["in_R"]].sum((1, 2))) and np.array_equal(r["counts"][:, 1], s[:, :, idx["in_L"]].sum((1, 2))), "T3"
assert r["pre"] == 100
# T4 bilateral fraction
cfg = dict(I=8.0, step_ms=100, contra_frac=0.5)
r = V.simulate(spec, idx, "L", cfg, SEED, P)
I = np.zeros((100, N)); I[:, idx["in_L"]] = 8.0; I[:, idx["in_R"]] = 4.0
s = ALIF(spec, P, SEED).run(I, 100).reshape(10, 10, N)
assert np.array_equal(r["counts"][:, 5], s[:, :, idx["DNa02_R"]].sum((1, 2))), "T4"
# T5 ramp profile endpoints and length
r = V.simulate(spec, idx, "L", dict(I=None, ramp=(4.0, 12.0, 100)), SEED, ALIFParams(noise=0.0))
assert r["counts"].shape == (20, 6)
# T6 steady-state window counts = spikes 500..999 ms after onset
cfg = dict(I=9.0, step_ms=1000, pre_ms=200, pre_side="ipsi", pre_mV=10.0)
r = V.simulate(spec, idx, "L", cfg, SEED, P)
I = np.zeros((1200, N)); I[:, idx["in_L"]] = 9.0; I[:200, idx["in_L"]] = 10.0
s = ALIF(spec, P, SEED).run(I, 1200)
assert np.array_equal(r["ss"], s[700:1200].sum(0)), "T6 steady window"
# T7 random initial v changes the run but is reproducible
cfg = dict(I=8.0, step_ms=200, init_v=True)
a1 = V.simulate(spec, idx, "L", cfg, SEED, P, 8_490_051)["counts"]
a2 = V.simulate(spec, idx, "L", cfg, SEED, P, 8_490_051)["counts"]
a0 = V.simulate(spec, idx, "L", dict(I=8.0, step_ms=200), SEED, P)["counts"]
assert np.array_equal(a1, a2) and not np.array_equal(a1, a0), "T7"
# T8 SWS instance reproducible from seed (same W hash twice), differs from DATA
s1 = V.make_net("SWS", 8_490_001)[0]; s2 = V.make_net("SWS", 8_490_001)[0]
assert V.w_sha(s1) == V.w_sha(s2) != V.w_sha(spec), "T8"
print("test_v5v41: 8 tests OK")
