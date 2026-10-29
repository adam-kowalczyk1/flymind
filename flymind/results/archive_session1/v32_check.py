# Zgodność v1 ↔ v2 per próba (J0 0,10 i 0,14 przy b_a 0,5) + kryteria dopuszczalności v2
import sys, json, glob
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np, pandas as pd
import v32_bump as vb
r1, d1 = vb.run(1)
r2, d2 = vb.run(2)
key = ["J0", "glomerulus", "seed", "variant", "window"]
a = d1[d1.J0.isin([0.1, 0.14])].set_index(key).sort_index()[["C", "dC", "phase_err"]]
b = d2[(d2.b_a == 0.5) & d2.J0.isin([0.1, 0.14])].set_index(key).sort_index()[["C", "dC", "phase_err"]]
same = a.index.equals(b.index) and all(np.array_equal(a[c].to_numpy(dtype=float), b[c].to_numpy(dtype=float), equal_nan=True) for c in a)
print(f"v1 ↔ v2 (b_a 0,5; J0 0,10 i 0,14): {len(a)} wierszy, C/dC/faza identyczne co do bitu: {same}")
for k, v in r2["admissibility"].items():
    print(k, {x: (round(y, 3) if isinstance(y, float) else y) for x, y in v.items()})
