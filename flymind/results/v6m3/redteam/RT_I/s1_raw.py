import glob, json, numpy as np
R = "flymind/results/v6m3"
an = json.load(open(f"{R}/analysis.json"))
for S in ("MAIN", "REP"):
    B = [np.load(p) for p in sorted(glob.glob(f"{R}/raw/{S}_B1_*.npz"))]
    X = np.stack([b["B"] for b in B])       # k, dyn, cell, lv, side, rep
    print(S, X.shape, "nan", np.isnan(X).sum())
    dd = X[:, :, 0]
    print("  DD identical across k (per dyn):", [bool(np.all(dd[:, i] == dd[0:1, i])) for i in range(3)])
    bb = X[:, 0, 3]; print("  BB REF sd across k / sd across reps (rep means):", bb.mean((1, 2)).std(0).mean().round(2), bb.mean((0, 1, 2)).std().round(2))
    for c in range(4):
        print("  REF cell", "DD DB BD BB".split()[c], "sd across k of k-mean", X[:, 0, c].mean((1, 2, 3)).std().round(3),
              "sd across rep of rep-mean", X[:, 0, c].mean((0, 1, 2)).std().round(3))
    m = X.mean((0, 3, 4, 5))
    print("  means", m.round(2))
    st = an[S]["partB"]["stats"]
    for key in ("C|REF", "T|REF", "Cshare|REF", "inter|REF", "gap|REF", "Csharelog|REF", "T|T0", "T|T0G", "C|T0", "C|T0G", "inter|T0", "inter|T0G"):
        v = st[key]; print(f"  {key:14s} est {v['est']:+.3f} pct [{v['ci_pct'][0]:+.3f};{v['ci_pct'][1]:+.3f}] jt [{v['ci_jackt'][0]:+.3f};{v['ci_jackt'][1]:+.3f}]")
    ad = np.stack([b["added"] for b in B])  # k, 2, lv, side, rep
    print("  added frac DB/BD", ad[:, 0].mean().round(4), ad[:, 1].mean().round(4), "per level BD", ad[:, 1].mean((0, 2, 3)).round(4), "per side BD", ad[:, 1].mean((0, 1, 3)).round(4),
          "per level DB", ad[:, 0].mean((0, 2, 3)).round(4), "per side DB", ad[:, 0].mean((0, 1, 3)).round(4))
