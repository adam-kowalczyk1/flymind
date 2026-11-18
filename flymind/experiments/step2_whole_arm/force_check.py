# Kontrola pozytywna miernika siły ForceWorld: ramię celowo dociskane do blatu (bez warstwy bezpieczeństwa, sam symulator).
import sys; sys.path.insert(0, "/Users/admin/so101_fly_project/flymind/experiments/step2_whole_arm")
import numpy as np, lift_b as lb
from reach import clearance
w = lb.ForceWorld([("cube_M", "mid")], 1)
q = np.array(w.obs.q[:5]); w.phase = "test"
out = []
for k in range(400):
    q[1] = min(q[1] + 0.003, w.sim.jrange[1, 1] - 0.05)       # +q stawu 1 = w dół
    w.step(q, 0.0)
    if k % 40 == 0: out.append((k, round(clearance(w.sim, w.obs.q), 4), w.fmax.get("test", 0.0)))
print(out); print("fmax", w.fmax)
