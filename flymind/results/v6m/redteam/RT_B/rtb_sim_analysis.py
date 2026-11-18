"""Analyse sim_interaction.npz (crossed bootstrap, RNG 8_498_105)."""
import numpy as np
z = np.load("flymind/results/v6m/redteam/RT_B/sim_interaction.npz")
D, B, cs = z["data"], z["b1"], list(z["conds"])            # D [C,L,S,R], B [K,C,L,S,R]
rng = np.random.default_rng(8_498_105); NB = 10000
def stat(D, B, sel=(slice(None),)*2):
    xd = D[(slice(None),) + sel].reshape(len(cs), -1, D.shape[-1]).mean(1)       # [C,R]
    xb = B[(slice(None), slice(None)) + sel].reshape(B.shape[0], len(cs), -1, B.shape[-1]).mean(2)  # [K,C,R]
    return xd, xb
def show(lab, sel=(slice(None),)*2):
    xd, xb = stat(D, B, sel)
    pt_g = xb.mean((0, 2)) - xd.mean(1); pt_d = xd.mean(1)
    gb = np.empty((NB, len(cs))); db = np.empty((NB, len(cs)))
    for i in range(NB):
        k = rng.integers(10, size=10); r = rng.integers(8, size=8)
        gb[i] = xb[k][:, :, r].mean((0, 2)) - xd[:, r].mean(1); db[i] = xd[:, r].mean(1)
    q = lambda x: np.percentile(x, [2.5, 97.5])
    print(f"== {lab}")
    for c in cs:
        j = cs.index(c)
        print(f"  {c:5s} DATA {pt_d[j]:6.1f}  gap {pt_g[j]:+6.1f} {np.round(q(gb[:,j]),1).tolist()}  rel {pt_g[j]/pt_d[j]:+.3f} {np.round(q(gb[:,j]/db[:,j]),3).tolist()}")
    M0, MC, T0, MCT0 = (cs.index(c) for c in cs)
    for nm, a, b in (("timing F at REF  (MC vs M0)", MC, M0), ("timing F at t0 (MCT0 vs T0)", MCT0, T0), ("t0 F, timing intact (T0 vs M0)", T0, M0),
                     ("t0 F, timing destroyed (MCT0 vs MC)", MCT0, MC)):
        Fa = 1 - pt_g[a] / pt_g[b]; Fr = 1 - (pt_g[a] / pt_d[a]) / (pt_g[b] / pt_d[b])
        print(f"  {nm:38s} F_abs {Fa:+.2f} {np.round(q(1-gb[:,a]/gb[:,b]),2).tolist()}   F_rel {Fr:+.2f} {np.round(q(1-(gb[:,a]/db[:,a])/(gb[:,b]/db[:,b])),2).tolist()}")
    ia = (pt_g[MC] - pt_g[M0]) - (pt_g[MCT0] - pt_g[T0])
    iab = (gb[:, MC] - gb[:, M0]) - (gb[:, MCT0] - gb[:, T0])
    print(f"  interaction (timing effect at REF minus at t0), abs Hz {ia:+.2f} {np.round(q(iab),2).tolist()}")
show("pooled 7/8/9 mV, L+R")
for li, lv in enumerate((7, 8, 9)):
    show(f"{lv} mV", (li, slice(None)))
