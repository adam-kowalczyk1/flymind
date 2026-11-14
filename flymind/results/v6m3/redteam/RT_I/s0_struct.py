import sys, numpy as np
sys.path.insert(0, "flymind")
import v6m3 as M3
data, idx, N, lc, mid, dn = M3.setup()
W = np.asarray(data.W, float)
print("N", N, "lc", len(lc), "mid", len(mid), "dn", len(dn), "other", N-len(lc)-len(mid)-len(dn))
print({k: len(v) for k, v in idx.items()})
for side in "LR":
    d = idx[f"DNa02_{side}"][0]
    print(side, "W[d,lc] nonzero", np.count_nonzero(W[d, lc]), "sum", W[d, lc].sum(), "| W[d,mid] +", W[d, mid][W[d, mid] > 0].sum(), "-", W[d, mid][W[d, mid] < 0].sum(),
          "n+", (W[d, mid] > 0).sum(), "n-", (W[d, mid] < 0).sum(), "| W[d,dn]", W[d, dn], "| other", np.count_nonzero(np.delete(W[d], np.r_[lc, mid, dn])))
    mi = idx[f"mid_{side}"]
    print("  ipsi mid count", len(mi), "W[d, mid_ipsi] nonzero", np.count_nonzero(W[d, mi]), "contra nonzero", np.count_nonzero(W[d, np.setdiff1d(mid, mi)]))
print("T W0 W1 SS", M3.T, M3.W0, M3.W1, M3.SS)
