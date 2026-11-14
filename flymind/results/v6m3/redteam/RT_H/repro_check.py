"""Re-execute rep 0 of kept r1 job(s) with the r2 code; compare to the stored npz (no new seeds spent: identical inputs)."""
import json, os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "../../../.."))
import v6m3 as M3
cal = json.load(open(os.path.join(HERE, "../../calibration.json")))
for name, fam, k, S in (("REP_B1_8421016", "B1", 8421016, "REP"), ("MAIN_B1_8421003", "B1", 8421003, "MAIN")):
    r = M3.job_run(dict(set=S, family=fam, k=k, cal=cal, out=os.path.join(HERE, "repro"), n_reps=1, name=name))
    new = np.load(os.path.join(HERE, "repro", name + ".npz")); old = np.load(os.path.join(HERE, "../../raw", name + ".npz"))
    print(name, r["checks"], "A eq", np.array_equal(new["A"][..., 0, :], old["A"][..., 0, :], equal_nan=True),
          "B eq", np.array_equal(new["B"][..., 0], old["B"][..., 0], equal_nan=True), "added eq", np.array_equal(new["added"][..., 0], old["added"][..., 0]))
