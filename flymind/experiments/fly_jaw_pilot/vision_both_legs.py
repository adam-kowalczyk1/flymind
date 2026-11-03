"""Pilot (exploratory, no seeds, noise 0): LC9 L / R / both -> MN pools of left and right middle legs."""
import sys, time
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np
from alif import ALIFParams
from alif_sparse import SparseALIF
from vision_leg import network

POOLS = ("Ti flexor MN", "Ti extensor MN", "Tr flexor MN", "Tr extensor MN", "Fe reductor MN", "Sternal anterior rotator MN",
         "Sternal posterior rotator MN", "Pleural remotor/abductor MN", "Sternotrochanter MN")
for glu in (-1.0, 1.0):
    t0 = time.time(); spec, idx, rep = network(float(sys.argv[1]) if len(sys.argv) > 1 else 0.2, glu); tb = time.time() - t0
    print(f"\nGlu {glu:+.0f}: N {spec.W.shape[0]} {rep['sizes']} build {tb:.0f}s, no_nt {rep['unsigned']['no_nt']}")
    res = {}
    for name, grp in (("LC9-L", idx["LC9"]["L"]), ("LC9-R", idx["LC9"]["R"]), ("both", idx["LC9"]["L"] + idx["LC9"]["R"])):
        X = np.zeros(spec.W.shape[0]); X[grp] = 12.0
        t0 = time.time(); s = SparseALIF(spec, ALIFParams(), None).run(X, 600); dt = (time.time() - t0) / 600 * 1000
        res[name] = s[100:].mean(0) * 1000
    print(f"  ms/step {dt:.2f}; DNp09 L/R:", {k: (round(r[idx['DNp09']['L']]), round(r[idx['DNp09']['R']])) for k, r in res.items()})
    for p in POOLS:
        row = []
        for k in ("LC9-L", "LC9-R", "both"):
            row.append("/".join(f"{res[k][idx['legs'][leg]['MN'][p]].mean():5.1f}" if p in idx['legs'][leg]['MN'] else "  -  " for leg in ("T2L", "T2R")))
        print(f"  {p:28s} L-stim {row[0]}   R-stim {row[1]}   both {row[2]}  (left leg / right leg Hz)")
