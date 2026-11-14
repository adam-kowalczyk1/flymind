"""RT-A: realized event participation and boundary ISI of v6m.synth. Seeds: free run noise 8 498 001 (DATA, 8 mV, L and R);
synth rng 8 498 040 + grid index (side L) / 8 498 070 + grid index (side R). Run from /Users/admin/so101_fly_project with .venv python -I -B."""
import sys
import numpy as np
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import v5v41 as V, v5v43 as R, v6m as M  # noqa: E401,E402
from alif import ALIF, ALIFParams  # noqa: E402
data, idx, _, _ = V.make_net("DATA", None)
P = ALIFParams(noise=2.0)
L = M.W1 - M.W0
for side, base in (("L", 8_498_040), ("R", 8_498_070)):
    s = ALIF(data, P, 8_498_001).run(R.current(idx, side, 8.0, len(data.bodies)), M.T)
    tr = s[:, idx[f"in_{side}"]]
    n = tr[M.W0:M.W1].sum(0)
    print(f"side {side}: LC ipsi per-neuron spikes in 300-1000: mean {n.mean():.1f} (rate {n.mean()/0.7:.1f} Hz), max {n.max()}")
    for g, (ev_rate, p) in enumerate(M.P_SYNC):
        r0 = np.random.default_rng(base + g)
        n_ev = r0.poisson(ev_rate * L / 1000.0)
        ev = r0.integers(0, L, n_ev)                      # synth's first two draws = the events
        x = M.synth(tr, p, np.random.default_rng(base + g), ev_rate)
        seg = x[M.W0:M.W1]
        near = np.zeros(L, bool)
        for e in ev:
            near[max(e - 1, 0):e + 2] = True
        t, j = np.nonzero(seg)
        part = near[t].mean()
        chance = near.mean()
        # ISI across the W0 boundary (pre-window spikes are not checked by synth)
        viol = 0
        for k in range(x.shape[1]):
            ts = np.flatnonzero(x[:, k])
            viol += int((np.diff(ts) < 4).sum())
        print(f"  ev {ev_rate:4.0f} Hz p {p:.2f}: n_ev {n_ev:2d}  spikes within +-1 ms of an event {part:.3f} (chance {chance:.3f}; "
              f"nominal p {p:.2f})  ISI<4 incl. W0 boundary: {viol}  Fano10 {M.sync_metrics(x)[2]:.1f}")
