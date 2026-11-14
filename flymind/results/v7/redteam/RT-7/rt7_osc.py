"""RT-7: oscillation / success comparison across V7 blocks and V6.1 S1 cells (no RNG)."""
import json
import numpy as np
F = "/Users/admin/so101_fly_project/flymind/results/"
def L(p): return [json.loads(l) for l in open(p) if l.strip()]
v7 = L(F + "v7/v7.jsonl"); v61 = L(F + "v61/v61.jsonl")
v6 = [r for r in L(F + "v6/closedloop.jsonl") if r.get("config") == "D0"]
def show(tag, rs):
    rs = [r for r in rs if not r.get("error")]
    if not rs: return
    print(f"{tag:22s} n {len(rs):3d} err {np.mean([r['final_abs_err'] for r in rs]):.2f} succ {np.mean([r['success'] for r in rs]):.2f} "
          f"e_sd_last1s med {np.median([r.get('e_sd_last1s', np.nan) for r in rs]):.3f}")
for b in ("G1", "G2", "G3", "G4"):
    for f in ("DATA", "SWS"):
        show(f"V7 {b} {f}", [r for r in v7 if r["config"] == b and r["family"] == f and r["cond"] == "snn"])
for im in ("I8", "I10", "I14", "I16"):
    for f in ("DATA", "SWS"):
        show(f"V6.1 {im} S1 {f}", [r for r in v61 if r["config"] == im and r["family"] == f and r["seed"] <= 8_600_040])
for f in ("DATA", "SWS"):
    show(f"V6 D0(I12) S1 {f}", [r for r in v6 if r["family"] == f and r["seed"] <= 8_600_040])
