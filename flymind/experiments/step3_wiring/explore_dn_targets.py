import sys, numpy as np
sys.path.insert(0, '/Users/admin/so101_fly_project/flymind/experiments/step3_wiring')
import brainleg as B
bm, d78, d15 = B.route_ids()
for kind, ss in (("N", None), ("B", 21100006), ("B", 21100007), ("L", 21100006)):
    n = B.BrainNet(1.0, kind, ss)
    import nets2
    _, idx, _, _, pos, _ = nets2.build_ext(1.0, bm + d78 + d15) if kind == "N" else (None, None, None, None, POS, None)
    if kind == "N":
        POS = pos
    W = n.W.toarray() if hasattr(n.W, "toarray") else np.asarray(n.W)
    row = []
    for name, ids in (("DNge078", d78), ("DNg15", d15)):
        cols = [POS[b] for b in ids]
        for j, lab in ((2, "łokieć"), (3, "nadgarstek")):
            p, q = n.pools[j]
            row.append(f"{name}→{lab} +{W[np.ix_(p, cols)].sum():.0f}/-{W[np.ix_(q, cols)].sum():.0f}")
    bmc = [POS[b] for b in bm]
    row.append(f"BM→DN78 {W[np.ix_([POS[b] for b in d78], bmc)].sum():.0f} BM→DN15 {W[np.ix_([POS[b] for b in d15], bmc)].sum():.0f}")
    print(kind, ss, " | ".join(row), flush=True)
