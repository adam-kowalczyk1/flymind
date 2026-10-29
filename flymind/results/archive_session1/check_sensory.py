import sys, time
import numpy as np
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
from sensory import SensoryGate, replay, spot_clip
rng = np.random.default_rng(1001)
T = 3000
clip = spot_clip(np.sin(np.linspace(0, 6 * np.pi, T)) * 0.5, 0.0, (96, 128), 70.0)
drop = set(np.flatnonzero(rng.random(T) < 0.02)); blank = set(np.flatnonzero(rng.random(T) < 0.01)) - drop
jit = rng.exponential(0.004, T)
g = SensoryGate((96, 128), 0.01, 0.02, 0.05)
t = time.perf_counter(); out = [g.push(f, f.t_receive) for f in replay(clip, 0.01, delay=jit, drop=drop, blank=blank)]
el = time.perf_counter() - t
print(g.stats, f"drop={len(drop)} blank={len(blank)} stale_expected={(jit[[i for i in range(T) if i not in drop and i not in blank]] > 0.02).sum()}")
print(f"gate: {el / len(out) * 1e6:.1f} us/klatka (128x96, sha256 incl.)")
