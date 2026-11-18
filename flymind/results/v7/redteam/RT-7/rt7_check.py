"""RT-7 (second reviewer instance) independent re-analysis of V7. No trials. RNG 8_498_411 (cluster bootstrap), 8_498_412 (scene bootstrap)."""
import json
from collections import Counter
import numpy as np
F = "/Users/admin/so101_fly_project/flymind/"
recs = [json.loads(l) for l in open(F + "results/v7/v7.jsonl")]
DI = json.load(open(F + "results/v61/drive_index.json"))
drv = {r["seed"]: r for r in DI if "block" in r}
v6d = {r["seed"]: r for r in DI if "block" not in r}
cal = json.load(open(F + "results/v6/calibration.json"))
AJ = json.load(open(F + "results/v7/analysis.json"))
print("n", len(recs), "err", sum(bool(r.get("error")) for r in recs), "uniq", len({r["name"] for r in recs}))
print(Counter((r["config"], r["cond"], r["family"], round(r["slope"], 2), json.dumps(r["alif"])) for r in recs))
print("cal SG6", round(cal["SG6"]["slope"], 2), "D0", round(cal["D0"]["slope"], 2))
T = {(r["config"], "P" if r["cond"] == "classical_p" else r["family"], r["seed"]): r for r in recs}
# scene regeneration
BL = {"G1": ((0.28, 0.40), "u"), "G2": ((0.16, 0.28), "w"), "G3": ((0.16, 0.28), "u"), "G4": ((0.12, 0.16), "u")}
mis = 0
for (b, c, s), r in T.items():
    g = np.random.default_rng(s)
    if BL[b][1] == "w":
        a = float(g.uniform(30, 40) * g.choice([-1, 1])); rho = float(g.uniform(*BL[b][0]))
    else:
        a = float(g.uniform(-30, 30)); rho = float(g.uniform(*BL[b][0]))
    mis += (a != r["az0_deg"]) or (rho != r["rho"]) or drv[s]["block"] != b or drv[s]["rho"] != rho
print("scene/drive-index mismatches", mis)
sws_ok = all(T[(b, "SWS", s)]["k"] == 8_410_001 + (i % 50) for b, (lo, _) in [(k, v) for k, v in BL.items()]
             for i, s in enumerate(sorted(x for (bb, c, x) in T if bb == b and c == "DATA")))
print("SWS instance mapping ((i-1) mod 50)+1 ok", sws_ok)

def ci_cluster(d, cl, rng, n=10_000):
    u = np.unique(cl); idx = {c: np.flatnonzero(cl == c) for c in u}
    bs = [d[np.concatenate([idx[c] for c in rng.choice(u, len(u))])].mean() for _ in range(n)]
    return np.percentile(bs, [2.5, 97.5])

R1, R2 = np.random.default_rng(8_498_411), np.random.default_rng(8_498_412)
def cell(b, sel, ctrl="SWS"):
    ss = sorted(s for (bb, c, s) in T if bb == b and c == "DATA" and sel(T[(bb, c, s)]))
    D = np.array([T[(b, "DATA", s)]["final_abs_err"] for s in ss]); X = np.array([T[(b, ctrl, s)]["final_abs_err"] for s in ss])
    d = D - X
    cl = np.array([T[(b, ctrl, s)]["k"] or s for s in ss])
    c1 = ci_cluster(d, cl, R1); c2 = ci_cluster(d, np.array(ss), R2, 5000)
    dr = np.array([max(drv[s]["gL"], drv[s]["gR"]) * 12 for s in ss])
    return ss, d, c1, c2, dr

def stats(b, ss, key, cond):
    return np.array([float(T[(b, cond, s)][key]) for s in ss])

half = {"ALL": lambda r: True, "near": lambda r: r["rho"] < 0.22, "far": lambda r: r["rho"] >= 0.22}
expect = {("G1", "ALL"): -1, ("G4", "ALL"): +1, ("G2", "near"): +1, ("G2", "far"): -1, ("G3", "near"): +1, ("G3", "far"): -1}
print("\nblock half n | err mean/med DATA SWS P | succ D/S/P | moved D/S | d_SWS [cl CI] [scene CI] med zeros | d_P [cl] | drive med [IQR] | ovsh D-S | rule(code) mine")
for b in ("G1", "G2", "G3", "G4"):
    for h in (("ALL", "near", "far") if b in ("G2", "G3") else ("ALL",)):
        ss, d, c1, c2, dr = cell(b, half[h])
        _, dp, cp, _, _ = cell(b, half[h], "P")
        E = {c: stats(b, ss, "final_abs_err", c) for c in ("DATA", "SWS", "P")}
        S = {c: stats(b, ss, "success", c).mean() for c in ("DATA", "SWS", "P")}
        M = {c: stats(b, ss, "moved", c).mean() for c in ("DATA", "SWS")}
        ov = (stats(b, ss, "overshoot_deg", "DATA") - stats(b, ss, "overshoot_deg", "SWS")).mean()
        sg = expect.get((b, h))
        rule = "" if sg is None else ("holds" if (c1[0] > 0 if sg > 0 else c1[1] < 0) else "not shown")
        code = AJ["per_block"][b]["pattern"].get(h, "")
        aj = AJ["per_block"][b][f"SWS|{h}"]
        assert abs(aj["mean_d"] - d.mean()) < 1e-9 and aj["n"] == len(d)
        print(f"{b} {h:4s} {len(ss):3d} | {E['DATA'].mean():.2f}/{np.median(E['DATA']):.2f} {E['SWS'].mean():.2f}/{np.median(E['SWS']):.2f} {E['P'].mean():.2f}/{np.median(E['P']):.2f} "
              f"| {S['DATA']:.2f}/{S['SWS']:.2f}/{S['P']:.2f} | {M['DATA']:.2f}/{M['SWS']:.2f} | {d.mean():+.3f} [{c1[0]:+.3f};{c1[1]:+.3f}] [{c2[0]:+.3f};{c2[1]:+.3f}] "
              f"{np.median(d):+.3f} {(d == 0).sum():3d} | {dp.mean():+.2f} [{cp[0]:+.2f};{cp[1]:+.2f}] | {np.median(dr):.2f} [{np.percentile(dr,25):.2f};{np.percentile(dr,75):.2f}] "
              f"| {ov:+.2f} | {code} / {rule}  (analysis.json CI {aj['ci95_cluster'][0]:+.3f};{aj['ci95_cluster'][1]:+.3f})")

# G1 movers
ss, d, *_ = cell("G1", half["ALL"])
mD = stats("G1", ss, "moved", "DATA").astype(bool); mS = stats("G1", ss, "moved", "SWS").astype(bool)
print("\nG1 moved D only", (mD & ~mS).sum(), "S only", (mS & ~mD).sum(), "both", (mD & mS).sum(), "neither", (~mD & ~mS).sum(), "zeros", (d == 0).sum())
for nm, m in (("both", mD & mS), ("D only", mD & ~mS), ("S only", mS & ~mD)):
    print(f"  G1 d over {nm}: sum {d[m].sum():+.2f} mean {d[m].mean() if m.any() else float('nan'):+.3f}")
print("  G1 P err mean", stats("G1", ss, "final_abs_err", "P").mean().round(3), "DATA err | moved", stats("G1", ss, "final_abs_err", "DATA")[mD].mean().round(2))

# G4 anatomy: success failures, oscillation, signed error
ss, d, *_ = cell("G4", half["ALL"])
for c in ("DATA", "SWS", "P"):
    sd = stats("G4", ss, "e_sd_last1s", c); se = stats("G4", ss, "final_signed_err", c); a0 = np.array([T[("G4", c, s)]["az0_deg"] for s in ss])
    tr = np.array([T[("G4", c, s)]["e_deg_ds"] for s in ss])
    late_max = np.abs(tr[:, -5:]).max(1)
    print(f"G4 {c}: e_sd_last1s med {np.median(sd):.3f} | signed final err * sign(az0) mean {np.mean(se*np.sign(a0)):+.2f} | late |e| max med {np.median(late_max):.2f} | frac final |e|>=5 {np.mean(np.abs(tr[:,-1])>=5):.2f} | succ {stats('G4', ss, 'success', c).mean():.2f}")
# G4 err vs |az0|
a0 = np.abs(np.array([T[("G4", "DATA", s)]["az0_deg"] for s in ss]))
for lo, hi in ((0, 10), (10, 20), (20, 30)):
    m = (a0 >= lo) & (a0 < hi)
    print(f"  G4 |az0| {lo}-{hi}: n {m.sum()} DATA err {stats('G4', ss, 'final_abs_err', 'DATA')[m].mean():.2f} P err {stats('G4', ss, 'final_abs_err', 'P')[m].mean():.2f} d {d[m].mean():+.3f}")

# Drive comparison with V6 / V6.1 strata (drive = max(g)*I_max)
print("\nV6 scene drive (max g * I_max) medians by stratum:")
for im in (8, 10, 12, 14, 16):
    for st, lo, hi in (("S1", 8_600_001, 8_600_040), ("S2", 8_600_041, 8_600_120)):
        dr = [max(v6d[s]["gL"], v6d[s]["gR"]) * im for s in range(lo, hi + 1)]
        print(f"  I{im} {st}: median {np.median(dr):.2f} IQR [{np.percentile(dr,25):.2f};{np.percentile(dr,75):.2f}]")
# drive-matched check: G4 vs G2 near vs V6 S1 at I12 overlap
for b, h in (("G2", "near"), ("G2", "far"), ("G3", "near"), ("G3", "far"), ("G4", "ALL"), ("G1", "ALL")):
    ss, d, c1, _, dr = cell(b, half[h])
    for lo, hi in ((0, 6), (6, 10), (10, 12), (12, 30)):
        m = (dr >= lo) & (dr < hi)
        if m.sum() >= 8:
            print(f"  {b} {h:4s} drive [{lo},{hi}) n {m.sum():3d} d {d[m].mean():+.3f}")
# drive-based split of G2/G3 instead of rho split
v6s1 = np.median([max(v6d[s]["gL"], v6d[s]["gR"]) * 12 for s in range(8_600_001, 8_600_041)])
v6s2 = np.median([max(v6d[s]["gL"], v6d[s]["gR"]) * 12 for s in range(8_600_041, 8_600_121)])
cut = 0.5 * (v6s1 + v6s2)
print(f"\nDrive-split sensitivity (cut {cut:.2f} mV = midpoint of V6 S1/S2 medians at I12):")
for b in ("G2", "G3"):
    for nm, f in (("hi-drive", lambda r: max(drv[r["seed"]]["gL"], drv[r["seed"]]["gR"]) * 12 >= cut),
                  ("lo-drive", lambda r: max(drv[r["seed"]]["gL"], drv[r["seed"]]["gR"]) * 12 < cut)):
        ss, d, c1, _, _ = cell(b, f)
        print(f"  {b} {nm}: n {len(d)} d {d.mean():+.3f} [{c1[0]:+.3f};{c1[1]:+.3f}]")
for cutr in (0.20, 0.21, 0.23, 0.24):
    for b in ("G2",):
        a = cell(b, lambda r: r["rho"] < cutr); z = cell(b, lambda r: r["rho"] >= cutr)
        print(f"  G2 rho split {cutr}: near d {a[1].mean():+.3f} [{a[2][0]:+.3f};{a[2][1]:+.3f}] n {len(a[1])} | far d {z[1].mean():+.3f} [{z[2][0]:+.3f};{z[2][1]:+.3f}] n {len(z[1])}")
# P-vs-DATA range claim
print("\nP err range across blocks:", [round(stats(b, cell(b, half['ALL'])[0], 'final_abs_err', 'P').mean(), 3) for b in ("G1", "G2", "G3", "G4")])
