"""Pilot (exploratory, no seeds, noise 0): current into T2 L bristle receptors -> MN pool rates, Glu sign -1 vs +1."""
import sys
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np
from alif import ALIFParams
from alif_sparse import SparseALIF
from leg_circuit import network
from snn_interface import DEFAULT_SIGN

P = ALIFParams()
POOLS = ("Ti flexor MN", "Acc. ti flexor MN", "Ti extensor MN", "ltm MN", "ltm1-tibia MN", "ltm2-femur MN",
         "Tr flexor MN", "Tr extensor MN", "Fe reductor MN", "Sternal anterior rotator MN", "Sternal posterior rotator MN")
for glu in (-1.0, 1.0):
    spec, idx, rep = network(0.2, "T2", "L", sign_map={**DEFAULT_SIGN, "glutamate": glu})
    br = idx["sensory"]["mechanosensory bristle"]
    row = {}
    for I in (0.0, 10.0, 20.0, 40.0):
        net = SparseALIF(spec, P, None)
        X = np.zeros(spec.W.shape[0]); X[br] = I
        s = net.run(X, 500)[100:]
        r = s.mean(0) * 1000
        row[I] = {p: round(float(r[idx["MN"][p]].mean()), 1) for p in POOLS if p in idx["MN"]}
        row[I]["IN mean"] = round(float(r[idx["IN"]].mean()), 1)
        row[I]["bristle"] = round(float(r[br].mean()), 1)
    print(f"\nGlu = {glu:+.0f}")
    for p in list(row[0.0]):
        print(f"  {p:30s}", "  ".join(f"{row[I][p]:6.1f}" for I in row), " Hz  (I = 0/10/20/40 mV)")
