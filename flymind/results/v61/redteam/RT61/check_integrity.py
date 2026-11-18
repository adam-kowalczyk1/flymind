import json, collections, sys
import numpy as np
R = "/Users/admin/so101_fly_project/flymind/results/"
lines = open(R+"v61/v61.jsonl").read().split("\n")
print("lines", len(lines), "last empty", lines[-1] == "")
recs, bad = [], 0
for l in lines:
    if not l: continue
    try: recs.append(json.loads(l))
    except Exception: bad += 1
print("parsed", len(recs), "bad", bad)
names = collections.Counter(r["name"] for r in recs)
print("unique names", len(names), "dups", [n for n,c in names.items() if c>1][:5])
exp = {f"I{im:g}|{f}|{s}" for im in (8,10,14,16) for f in ("DATA","SWS","B1") for s in range(8600001,8600121)}
print("missing", len(exp-set(names)), "extra", len(set(names)-exp))
print("errors", sum(1 for r in recs if r.get("error")))
cal = json.load(open(R+"v6/calibration.json"))
print("slopes", collections.Counter(r["slope"] for r in recs), "D0", cal["D0"]["slope"])
print("enc", collections.Counter((r["config"], json.dumps(r["enc"]), r["i_max"]) for r in recs))
print("alif/J0/cond", collections.Counter((json.dumps(r["alif"]), r["J0"], r["cond"]) for r in recs))
v6 = [json.loads(l) for l in open(R+"v6/closedloop.jsonl") if l.strip()]
print("v6 configs", collections.Counter((r["config"], r["family"]) for r in v6))
d0 = {(r["family"], r["seed"]): r for r in v6 if r["config"] == "D0"}
print("v6 D0 n", len(d0), "errors", sum(1 for r in d0.values() if r.get("error")), "slopes", collections.Counter(r["slope"] for r in d0.values()), "enc", collections.Counter(json.dumps(r.get("enc")) for r in d0.values()), collections.Counter((json.dumps(r["alif"]),r["J0"]) for r in d0.values()))
# scene identity and pairing
mism = 0
for r in recs:
    o = d0.get((r["family"], r["seed"]))
    if o is None: mism += 1; print("no D0", r["name"]); continue
    for k in ("az0_deg","rho","stratum","k"):
        if o[k] != r[k]: mism += 1; print("mism", r["name"], k, o[k], r[k])
print("scene/k mismatches vs V6 D0:", mism)
# k pattern
import importlib; sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
for f in ("SWS","B1"):
    ks = {}
    for r in recs+list(d0.values()):
        if r["family"]==f: ks.setdefault(r["seed"], set()).add(r["k"])
    print(f, "seeds with >1 k across Imax+D0:", sum(len(v)>1 for v in ks.values()), "n clusters", len({next(iter(v)) for v in ks.values()}))
# wall_s timing/ordering at restart
t = [r["wall_s"] for r in recs]
print("first 88 names imax", collections.Counter(r["config"] for r in recs[:88]), "wall mean first88 %.1f rest %.1f" % (np.mean(t[:88]), np.mean(t[88:])))
# DATA determinism: does I12-equivalent ? check DATA moved / err identical across families? n/a
# encoder consistency: drive index file
di = json.load(open(R+"v61/drive_index.json"))
dv6 = [x for x in di if "block" not in x]
print("drive rows v6", len(dv6), "seeds", len({x["seed"] for x in dv6}))
sc = {r["seed"]:(r["az0_deg"],r["rho"]) for r in recs}
print("drive scene mismatches", sum(1 for x in dv6 if (x["az0_deg"],x["rho"]) != sc[x["seed"]]))
print("n_px zero", sum(1 for x in dv6 if x["n_px"]==0))
