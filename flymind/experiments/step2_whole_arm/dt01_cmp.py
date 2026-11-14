"""Porównanie sparowane dt 0,1 ms vs dt 1 ms (te same sceny: test, poza 0). Użycie: dt01_cmp.py JOINTDIR PREFIX OUTCOME GLU"""
import json, sys, glob
import numpy as np
from scipy.stats import binomtest
d, pre, oc, g = sys.argv[1:5]
f01 = json.load(open(f"{d}/dt01/{pre}_dt01_N_g{g}.json"))
f1 = json.load(open(glob.glob(f"{d}/test/{pre}_test_N_g{g}.json")[0]))
val = (lambda r: bool(r["truth"]["lift"])) if oc == "lift" else (lambda r: bool(r["success"]))
A = {(r["item"], r["seed"]): r for r in f01["runs"]}
B = {(r["item"], r["seed"]): r for r in f1["runs"] if (r["item"], r["seed"]) in A}
ks = sorted(A)
assert len(B) == len(ks) == 45, (len(B), len(ks))
a = np.array([val(A[k]) for k in ks]); b = np.array([val(B[k]) for k in ks])
n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
p = binomtest(n10, n10 + n01).pvalue if n10 + n01 else 1.0
same_prelift = sum(A[k].get("prelift_sha") == B[k].get("prelift_sha") for k in ks)
fm = max(r["fmax"] for r in A.values())
print(json.dumps(dict(joint=d, glu=g, outcome=oc, n=len(ks), dt01=int(a.sum()), dt1=int(b.sum()), dt01_only=n10, dt1_only=n01,
                      mcnemar2_p=round(float(p), 4), prelift_identical=same_prelift, fmax_dt01=fm, wall_s=f01.get("wall_s"))))
