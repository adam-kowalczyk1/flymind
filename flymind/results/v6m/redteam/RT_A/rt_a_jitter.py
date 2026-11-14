"""RT-A: jitter/CIRC loss fractions and refractory violations created in clamped intermediate trains. Seeds: noise 8 498 001-002
(DATA source, REF replay = free run, 8 mV, L/R); manipulation rng 8 498 060 + 10*variant + rep."""
import sys
import numpy as np
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import v5v41 as V, v5v43 as R  # noqa: E401,E402
from alif import ALIF, ALIFParams  # noqa: E402
data, idx, _, _ = V.make_net("DATA", None)
P = ALIFParams(noise=2.0)
mid = np.r_[idx["mid_L"], idx["mid_R"]]
def short_isi(x):
    return sum(int((np.diff(np.flatnonzero(x[:, j])) < 4).sum()) for j in range(x.shape[1]))
for side in "LR":
    for r, sd in enumerate((8_498_001, 8_498_002)):
        s = ALIF(data, P, sd).run(R.current(idx, side, 8.0, len(data.bodies)), 1000)
        m = s[:, mid]
        n_win = int(m[300:1000].sum())
        row = [f"{side} {sd}: mid spikes 300-1000 {n_win}, ISI<4 in REF {short_isi(m)}"]
        for vi, var in enumerate(("CIRC", "J2", "J5", "J20", "POIS")):
            x, lost = R.manipulate(m, var, np.random.default_rng(8_498_060 + 10 * vi + r))
            row.append(f"{var}: lost {lost} ({100 * lost / n_win:.2f}%), ISI<4 {short_isi(x)}, ss-count change {int(x[500:].sum()) - int(m[500:].sum()):+d}")
        print(" | ".join(row))
