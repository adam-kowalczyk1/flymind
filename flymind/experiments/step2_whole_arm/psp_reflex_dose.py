import sys, json, os; sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np
from alif import ALIFParams; from alif_sparse import SparseALIF; from leg_circuit import network; from snn_interface import DEFAULT_SIGN
class S:
    def __init__(s, W): s.W = W
res = {}
for glu in (-1.0, 1.0):
    spec, idx, _ = network(0.2, "T2", "L", sign_map={**DEFAULT_SIGN, "glutamate": glu})
    br = idx["sensory"]["mechanosensory bristle"]; pr = idx["MN"]["Ti extensor MN"]; rl = idx["MN"]["Ti flexor MN"] + idx["MN"]["Acc. ti flexor MN"]
    row = {}
    for mv in (2.5, 5, 7.5, 10, 15, 20, 30, 40):
        X = np.zeros(spec.W.shape[0]); X[br[:len(br)//2]] = mv   # jeden pad (połowa szczecinek), jak FlyJaw
        s = SparseALIF(S(spec.W), ALIFParams(), None).run(X, 500)[250:].mean(0) * 1000
        row[mv] = dict(press=round(float(s[pr].mean()),1), release=round(float(s[rl].mean()),1), torque=round(0.005*float(s[pr].mean()-s[rl].mean()),3))
    res[f"glu{glu:+.0f}"] = row
out = "/Users/admin/so101_fly_project/flymind/results/step2_whole_arm_20261113/psp_reflex_dose_v1.json"
open(out, "x").write(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
