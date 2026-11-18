import glob, numpy as np, json
raw = "flymind/results/v6m3/raw"
cal = json.load(open("flymind/results/v6m3/calibration.json"))
print("cal", {k: cal[k] for k in ("ref_mid","mid_gain","mid_bias","dn_gain")})
cv = cal["curves"]; gg = np.array(cv["gain_grid"]); bg = np.array(cv["bias_grid"])
mg = np.array(cv["mid_gain"]); mb = np.array(cv["mid_bias"])
print("gain curve near pick", [(g, round(m,2)) for g, m in zip(gg, mg) if 0.65 <= g <= 0.8])
print("bias curve near pick", [(b, round(m,2)) for b, m in zip(bg, mb) if -8.5 <= b <= -5.5])
conds = ["REF","MT0","MT0G","MT0B","LCIRC"]
for S in ("MAIN","REP"):
    D = np.load(f"{raw}/{S}_DATA.npz")["A"]
    Bs = np.stack([np.load(f)["A"] for f in sorted(glob.glob(f"{raw}/{S}_B1_*.npz"))])
    nmid_ipsi = None
    print("=====", S, "A shape", D.shape, Bs.shape)
    # mid ipsi count per level, per side, by cond; field 1
    for li, lv in enumerate((8, 9)):
        for si, sd in enumerate("LR"):
            row = []
            for ci, c in enumerate(conds):
                d = D[ci, li, si, :, 1].mean(); b = Bs[:, ci, li, si, :, 1].mean()
                dx = D[ci, li, si, :, 2].mean(); bx = Bs[:, ci, li, si, :, 2].mean()
                row.append(f"{c}: midD {d:6.1f} midB {b:6.1f} Drel {bx/dx-1:+.3f}")
            print(lv, sd, " | ".join(row))
    # lc counts
    print("LC count D vs B1 (REF):", D[0, ..., 5].mean(), Bs[:, 0, ..., 5].mean(), "LCIRC:", D[4, ..., 5].mean(), Bs[:, 4, ..., 5].mean())
    # per-level rate match relative to REF DATA
    for li in (0, 1):
        r = D[0, li, :, :, 1].mean()
        print("level", li, "DATA mid REF", round(r,1), "MT0G", round(D[2, li, :, :, 1].mean(),1), "MT0B", round(D[3, li, :, :, 1].mean(),1),
              "| B1 REF", round(Bs[:,0,li,:,:,1].mean(),1), "MT0G", round(Bs[:,2,li,:,:,1].mean(),1), "MT0B", round(Bs[:,3,li,:,:,1].mean(),1))
    # Dinh
    print("Dinh D/B REF", D[0,...,3].mean(), Bs[:,0,...,3].mean(), "MT0B", D[3,...,3].mean(), Bs[:,3,...,3].mean())
    # B1 instance spread of Drel REF
    dr = Bs[:, 0, ..., 2].mean((1,2,3)) / D[0, ..., 2].mean() - 1
    print("Drel REF per B1 instance", np.round(dr, 3))
    # per-rep Drel REF (paired by seed)
    print("Drel REF per rep", np.round(Bs[:,0,...,2].mean((0,1,2))/D[0,...,2].mean((0,1)) - 1, 3))
    print("Drel MT0B per rep", np.round(Bs[:,3,...,2].mean((0,1,2))/D[3,...,2].mean((0,1)) - 1, 3))
