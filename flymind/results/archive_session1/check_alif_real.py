import json, sys, time
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np, pandas as pd
from connectome import load_edges
from snn_interface import build, ModelEdge, ModelParams
from alif import ALIF, ALIFParams, rates, validate
D = "/Users/admin/so101_fly_project/data/malecns/"
c = json.load(open("/Users/admin/so101_fly_project/bio2/circuit_bio2.json"))
N = [n for n in c["neurons"] if n["module"] in ("cx", "dn", "loom", "hs")]
ids = [n["bodyId"] for n in N]
nt = pd.read_feather(D + "body-neurotransmitters-male-cns-v1.0.feather")
e, _ = load_edges(D + "connectome-weights-male-cns-v1.0-minconf-0.5.feather", bodies=ids)
key = lambda n: f"{n['type'].split('(')[0]}_{n['side']}" if n["module"] == "dn" else n["type"].split("(")[0]
pops = {}
for n in N: pops.setdefault(key(n), []).append(n["bodyId"])
pick = lambda t, s: [n["bodyId"] for n in N if n["type"] == t and n["side"] == s]
me = [ModelEdge(p, pick("DNa01", so)[0], float(w), "bio2 brain.py:111 kopia PFL3→DNa02")
      for sp, so in (("L", "R"), ("R", "L")) for p in pick("PFL3", sp)
      for w in [e.weight[(e.body_pre == p) & (e.body_post == pick("DNa02", so)[0])].sum()] if w]
mp = ModelParams(J0=0.3)                         # = bio2 J0_RAW (poza CX); CX w bio2 ma inne, profilowe wagi
full, data = build(e, ids, nt, mp, model_edges=me), build(e, ids, nt, mp, model_edges=me, include_model=False)
P = ALIFParams(noise=2.0)                        # = bio2 noise; b_a 0,5 wszędzie (bio2 zeruje b_a w CX)
idx = {b: i for i, b in enumerate(ids)}
def stim(groups, amp):
    I = np.zeros(len(ids)); I[[idx[b] for g in groups for b in pops[g]]] = amp; return I
for name, I in (("spontan (szum 2 mV, brak bodźca)", np.zeros(len(ids))), ("EPG 12 mV", stim(["EPG"], 12.0))):
    t0 = time.perf_counter()
    r = validate(data, P, 1001, I_on=I, other_seed=1002, pops=pops)
    print(f"## {name} [{time.perf_counter()-t0:.1f} s / 4 przebiegi po 1 s]")
    print(json.dumps({k: v for k, v in r.items() if k != "pops_hz"}, ensure_ascii=False))
    print("  pops (on, late-off) Hz:", r["pops_hz"])
print("## ablacja DNa01: PFL3 10 mV przez 1 s, szum 2 mV, ziarna 1001–1005, średnia [Hz]")
I = stim(["PFL3"], 10.0)
for lab, sp in (("dane+model", full), ("tylko dane", data)):
    rr = np.mean([rates(ALIF(sp, P, s).run(I, 1000), 1.0) for s in range(1001, 1006)], axis=0)
    print(f"  {lab:11s}", {g: round(float(rr[[idx[b] for b in pops[g]]].mean()), 1) for g in ("PFL3", "DNa02_L", "DNa02_R", "DNa01_L", "DNa01_R")})
net = ALIF(data, P, 1001); t0 = time.perf_counter(); net.run(np.zeros(len(ids)), 5000)
print(f"## koszt: {len(ids)} neuronów, 5000 kroków po 1 ms: {time.perf_counter()-t0:.2f} s ściany (jedna maszyna, jeden pomiar)")
