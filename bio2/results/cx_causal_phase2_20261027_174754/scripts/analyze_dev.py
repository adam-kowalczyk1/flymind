"""Development-set analysis (EXPLORATORY; used only to set provisional thresholds). Usage: analyze_dev.py OUT.txt FILE.jsonl..."""
import json, sys, numpy as np
out, files = sys.argv[1], sys.argv[2:]
R = [json.loads(l) for f in files for l in open(f)]
A = [r for r in R if r.get("ball_stop", True)]
B = [r for r in R if not r.get("ball_stop", True)]
L = []
p = L.append
by = {(r["arm"], r["seed"], r["passive_deg"]): r for r in A}
seeds = sorted({r["seed"] for r in A}); pas = sorted({r["passive_deg"] for r in A}); arms = list(dict.fromkeys(r["arm"] for r in A))
p(f"EXP A dev: {len(A)} records, seeds {seeds}, passive {pas}; statuses: " + str({s: sum(r['status'] == s for r in A) for s in set(r['status'] for r in A)}))
ok = [r for r in A if r["status"] == "OK"]
on = {(r["seed"], r["passive_deg"]): r for r in ok if r["arm"] == "Freeze"}
x = np.array([[r["t_on"], r["snaps"]["onset"]["true_rel_deg"], r["snaps"]["onset"]["w_base"], r["passive_realised_deg"]] for r in on.values()])
p(f"onset (shared visible phase): t_on mean {x[:,0].mean():.2f} [{x[:,0].min():.2f},{x[:,0].max():.2f}] s; e_onset mean|.| {np.abs(x[:,1]).mean():.2f} SD {x[:,1].std(ddof=1):.2f}; "
  f"w_base at onset mean|.| {np.abs(x[:,2]).mean():.3f} rad/s; realised passive |.| mean {np.abs(x[:,3]).mean():.2f} SD {np.abs(x[:,3]).std(ddof=1):.2f} deg")
ident = all(r["snaps"]["onset"]["true_rel_deg"] == on[(r["seed"], r["passive_deg"])]["snaps"]["onset"]["true_rel_deg"] for r in ok if (r["seed"], r["passive_deg"]) in on)
p(f"onset state identical across arms within (seed, passive): {ident}")
p("\nper arm: n | |e_end| mean SD median | signed mean | |mem_err_end| mean (estimate vs truth at reappearance) | n coh<0.2 at end")
E = {}
for a in arms:
    rs = [r for r in ok if r["arm"] == a]
    e = np.array([r["e_end_deg"] for r in rs]); E[a] = {(r["seed"], r["passive_deg"]): r["e_end_deg"] for r in rs}
    me = np.array([r["mem_err_end_deg"] for r in rs if r.get("mem_err_end_deg") is not None])
    lowc = sum(1 for r in rs if r["log"] and r["log"][-1][4] is not None and r["log"][-1][4] < 0.2)
    p(f"  {a:16s} {len(rs):3d} | {np.abs(e).mean():6.2f} {np.abs(e).std(ddof=1):6.2f} {np.median(np.abs(e)):6.2f} | {e.mean():+6.2f} | "
      f"{(np.abs(me).mean() if len(me) else float('nan')):6.2f} (n={len(me)}) | {lowc}")
def paired(a, b, f=abs):
    k = sorted(set(E[a]) & set(E[b])); d = np.array([f(E[a][i]) - f(E[b][i]) for i in k]); n = len(d)
    se = d.std(ddof=1) / np.sqrt(n); from scipy.stats import t
    return n, d.mean(), d.std(ddof=1), d.mean() - t.ppf(.975, n - 1) * se, d.mean() + t.ppf(.975, n - 1) * se
p("\npaired D = |e_A| - |e_B| (deg): n, mean, SD, 95% t-CI")
for a, b in [("CX-Bump", "Scalar"), ("CX-Bump", "Freeze"), ("Scalar", "Freeze"), ("CX-DN", "Freeze"), ("CX-DN", "Scalar"),
             ("CX-Bump", "CX-Bump-NoSelf"), ("CX-Bump", "CX-Reset"), ("CX-Bump", "CX-Shuffle20"), ("CX-Shuffle20", "Freeze"), ("CX-Reset", "Freeze")]:
    if a in E and b in E:
        n, m, s, lo, hi = paired(a, b); p(f"  {a:14s} - {b:14s} n={n:2d} {m:+6.2f} SD {s:5.2f} [{lo:+6.2f}, {hi:+6.2f}]")
p("\nperturbation: signed D = e_end(arm) - e_end(sham/base), same (seed, passive); prediction: +30 -> negative, -30 -> positive")
for a, b in [("CX-Pulse+30", "CX-Sham"), ("CX-Pulse-30", "CX-Sham"), ("CX-Sham", "CX-Bump"), ("Scalar-Shift+30", "Scalar"), ("Scalar-Shift-30", "Scalar")]:
    if a in E and b in E:
        n, m, s, lo, hi = paired(a, b, f=lambda v: v); p(f"  {a:16s} - {b:9s} n={n:2d} {m:+6.2f} SD {s:5.2f} [{lo:+6.2f}, {hi:+6.2f}]")
if "CX-Pulse+30" in E and "CX-Pulse-30" in E:
    k = sorted(set(E["CX-Pulse+30"]) & set(E["CX-Pulse-30"])); d = np.array([(E["CX-Pulse-30"][i] - E["CX-Pulse+30"][i]) / 2 for i in k])
    p(f"  symmetric pulse effect (e(-30) - e(+30))/2: n={len(d)} mean {d.mean():+.2f} SD {d.std(ddof=1):.2f}; fraction of seeds with predicted sign {np.mean(d > 0):.2f}")
p("\nintervention verification (CX arms): bump shift pre_int -> post_int (deg), coherence, EPG Hz")
for a in ("CX-Pulse+30", "CX-Pulse-30", "CX-Sham"):
    rs = [r for r in ok if r["arm"] == a and "post_int" in r["snaps"]]
    if rs:
        sh = np.array([((r["snaps"]["post_int"]["bump_deg"] - r["bump_pre_int"] + 180) % 360) - 180 if "bump_pre_int" in r else np.nan for r in rs])
        sh = np.array([((r["snaps"]["post_int"]["bump_deg"] - r["snaps"]["bump_pre_int"] + 180) % 360) - 180 for r in rs])
        p(f"  {a:12s} n={len(rs)} shift {sh.mean():+6.2f} SD {sh.std(ddof=1):5.2f} | coh pre {np.mean([r['snaps']['pre_int']['coh'] for r in rs]):.2f} post {np.mean([r['snaps']['post_int']['coh'] for r in rs]):.2f} | EPG pre {np.mean([r['snaps']['pre_int']['epg_hz'] for r in rs]):.1f} post {np.mean([r['snaps']['post_int']['epg_hz'] for r in rs]):.1f}")
p("\nclosed-loop self-motion integration during passive window (CX-Bump vs CX-Bump-NoSelf): g = -(bump change)/(realised rotation)")
for a in ("CX-Bump", "CX-Bump-NoSelf"):
    rs = [r for r in ok if r["arm"] == a]
    gg = np.array([-(((r["snaps"]["post_passive"]["bump_deg"] - r["snaps"]["onset"]["bump_deg"] + 180) % 360) - 180) / r["passive_realised_deg"] for r in rs])
    enc = np.array([r["snaps"]["onset"]["bump_deg"] - r["snaps"]["onset"]["true_rel_deg"] for r in rs])
    p(f"  {a:15s} g mean {gg.mean():+.2f} SD {gg.std(ddof=1):.2f} (n={len(gg)}); onset encoding error bump-true mean {enc.mean():+.2f} SD {enc.std(ddof=1):.2f}")
sc = [r for r in ok if r["arm"] == "Scalar"]
if sc:
    gg = np.array([-(r["snaps"]["post_passive"]["th_hat_deg"] - r["snaps"]["onset"]["th_hat_deg"]) / r["passive_realised_deg"] for r in sc])
    p(f"  Scalar          g mean {gg.mean():+.2f} SD {gg.std(ddof=1):.3f}")
if B:
    p(f"\nEXP B dev (moving target, passive 0): {len(B)} records")
    for a in dict.fromkeys(r["arm"] for r in B):
        e = np.array([r["e_end_deg"] for r in B if r["arm"] == a and r["status"] == "OK"])
        p(f"  {a:10s} n={len(e)} |e_end| mean {np.abs(e).mean():6.2f} SD {np.abs(e).std(ddof=1):5.2f}")
open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))
