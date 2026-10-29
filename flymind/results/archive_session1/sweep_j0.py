import json, sys
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np, pandas as pd
from connectome import load_edges
from snn_interface import build, ModelParams
from alif import ALIFParams, validate
D = "/Users/admin/so101_fly_project/data/malecns/"
c = json.load(open("/Users/admin/so101_fly_project/bio2/circuit_bio2.json"))
N = [n for n in c["neurons"] if n["module"] in ("cx", "dn", "loom", "hs")]
ids = [n["bodyId"] for n in N]
nt = pd.read_feather(D + "body-neurotransmitters-male-cns-v1.0.feather")
e, _ = load_edges(D + "connectome-weights-male-cns-v1.0-minconf-0.5.feather", bodies=ids)
I = np.array([12.0 if n["type"] == "EPG" else 0.0 for n in N])
epg = np.array([n["type"] == "EPG" for n in N])
for tr in ("linear", "log1p"):
    for j0 in (0.02, 0.05, 0.1, 0.14, 0.2, 0.3, 1.0):
        r = validate(build(e, ids, nt, ModelParams(J0=j0, transform=tr)), ALIFParams(noise=2.0), 1001, I_on=I, pops={"EPG": [b for b, x in zip(ids, epg) if x]})
        print(f"{tr:6s} J0={j0:<5} on={r['mean_rate_on_hz']:6.1f} late_off={r['mean_rate_late_off_hz']:6.1f} Hz sat={r['saturated_frac']:.2f} runaway={r['runaway']} extinct={r['extinct_after_off']} EPG(on,off)={r['pops_hz']['EPG']}")
