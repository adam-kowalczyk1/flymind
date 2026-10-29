"""dev4 analysis (v2 design, EXPLORATORY dev seeds). Seed-level unit; t 95% CI. Usage: analyze_dev4.py OUT.txt FILES..."""
import json, sys, numpy as np, scipy.stats as st
out, files = sys.argv[1], sys.argv[2:]
R = [json.loads(l) for f in files for l in open(f)]
L = []; p = L.append
ok = [r for r in R if r["status"] == "OK"]
p(f"dev4: {len(R)} records; statuses {dict((s, sum(r['status'] == s for r in R)) for s in set(r['status'] for r in R))}; jump flags {set(r['jump'] for r in R)}")
E = {(r["arm"], r["seed"], r["passive_deg"]): r for r in ok}
seeds = sorted({r["seed"] for r in ok})
fz = [E[("Freeze", s, 0.0)] for s in seeds]
p("e_onset (Δ=0, shared): " + ", ".join(f"{r['snaps']['onset']['true_rel_deg']:+.1f}" for r in fz) + f"; jump_deg: " + ", ".join(f"{r['jump_deg']:+.1f}" for r in fz))
ident = all(E[(a, s, d)]["snaps"]["onset"]["true_rel_deg"] == E[("Freeze", s, d)]["snaps"]["onset"]["true_rel_deg"] for (a, s, d) in E)
p(f"onset state identical across arms within (seed, Δ): {ident}")
def seed_val(arm, deltas, f=abs):
    return np.array([np.mean([f(E[(arm, s, d)]["e_end_deg"]) for d in deltas]) for s in seeds])
def ci(x):
    n = len(x); h = st.t.ppf(.975, n - 1) * x.std(ddof=1) / np.sqrt(n); return f"{x.mean():+6.2f} [{x.mean()-h:+6.2f}, {x.mean()+h:+6.2f}] (SD {x.std(ddof=1):.2f}, n={n})"
arms = list(dict.fromkeys(r["arm"] for r in ok))
for lab, ds in (("Δ = 0 (pure target memory)", (0.0,)), ("Δ = ±20 (seed mean)", (-20.0, 20.0))):
    p(f"\n{lab}: seed-level |e_end| mean (SD)")
    for a in arms:
        v = seed_val(a, ds); p(f"  {a:16s} {v.mean():6.2f} ({v.std(ddof=1):5.2f})")
    p("  paired d = |e_A| - |e_B|:")
    for a, b in (("CX-Bump", "Freeze"), ("CX-Bump", "Scalar"), ("CX-Bump", "SelfOnly"), ("Scalar", "Freeze"), ("Scalar", "SelfOnly"),
                 ("CX-DN", "Freeze"), ("CX-Bump", "CX-Bump-NoSelf")):
        p(f"    {a:14s} - {b:14s} {ci(seed_val(a, ds) - seed_val(b, ds))}")
p("\nmemory-content test: regression of the memory-phase correction (true_rel change after passive window, i.e. e_end − e_post_passive)")
p("on the target bearing at the end of the passive window (ideal memory: slope −1 → full correction; freeze 0)")
for a in ("Scalar", "SelfOnly", "CX-Bump", "CX-DN", "Freeze"):
    x = np.array([E[(a, s, d)]["snaps"]["post_passive"]["true_rel_deg"] for s in seeds for d in (-20.0, 0.0, 20.0)])
    y = np.array([E[(a, s, d)]["e_end_deg"] for s in seeds for d in (-20.0, 0.0, 20.0)]) - x
    sl = st.linregress(x, y); p(f"  {a:9s} slope {sl.slope:+.2f} ± {sl.stderr:.2f}  r {sl.rvalue:+.2f}  (n={len(x)})")
p("\nperturbation (signed, seed mean over Δ ∈ {−20, 0, 20}): S = (e(−30) − e(+30))/2, predicted > 0")
for pre in ("CX", "CX-DN"):
    S = seed_val(f"{pre}-Pulse-30", (-20.0, 0.0, 20.0), f=lambda v: v) / 2 - seed_val(f"{pre}-Pulse+30", (-20.0, 0.0, 20.0), f=lambda v: v) / 2
    p(f"  {pre:6s} S {ci(S)}  positive {int((S > 0).sum())}/{len(S)}")
    sham = f"{pre}-Sham"
    for pl in ("+30", "-30"):
        d = seed_val(f"{pre}-Pulse{pl}", (-20.0, 0.0, 20.0), f=lambda v: v) - seed_val(sham, (-20.0, 0.0, 20.0), f=lambda v: v)
        p(f"    {pre}-Pulse{pl} − Sham {ci(d)}")
    sh = {k: [] for k in ("+30", "-30", "Sham")}
    for k, arm in (("+30", f"{pre}-Pulse+30"), ("-30", f"{pre}-Pulse-30"), ("Sham", sham)):
        for s in seeds:
            for d in (-20.0, 0.0, 20.0):
                r = E[(arm, s, d)]; sn = r["snaps"]
                sh[k].append(((sn["post_int"]["bump_deg"] - sn["bump_pre_int"] + 180) % 360) - 180)
    p(f"    manipulation check (median bump shift): +30 {np.median(sh['+30']):+.1f}, −30 {np.median(sh['-30']):+.1f}, sham {np.median(sh['Sham']):+.1f}")
open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))
