import sys, glob, numpy as np
sys.path.insert(0, "flymind")
import v6m3 as M3, v5v42 as V2
data, idx, N, lc, mid, dn = M3.setup()
W = np.asarray(data.W, float)
print("N", N, "lc", len(lc), "mid", len(mid), "dn", dn, {k: len(v) for k, v in idx.items()})
for side in "LR":
    mi = idx[f"mid_{side}"]; d = idx[f"DNa02_{side}"][0]
    w = W[d, mid]
    print(side, "mids with W[dn]>0:", (w > 0).sum(), "<0:", (w < 0).sum(), "sum+", w[w>0].sum().round(1), "sum-", w[w<0].sum().round(1))
# sign of each mid's outgoing weights
out = W[:, mid]
inh = (out < 0).sum(0) > (out > 0).sum(0)
print("inhibitory-like mids:", inh.sum(), "of", len(mid))
print("mid->mid weights: nonzero", (W[np.ix_(mid, mid)] != 0).sum(), "neg", (W[np.ix_(mid, mid)] < 0).sum(), "sum neg", W[np.ix_(mid, mid)][W[np.ix_(mid, mid)]<0].sum().round(1), "sum pos", W[np.ix_(mid, mid)][W[np.ix_(mid, mid)]>0].sum().round(1))
print("dn->mid", (W[np.ix_(mid, dn)] != 0).sum(), "mid->lc", (W[np.ix_(lc, mid)] != 0).sum(), "dn->dn", W[np.ix_(dn, dn)])
other = np.setdiff1d(np.arange(N), np.r_[lc, mid, dn]); print("other neurons", len(other))
b1 = V2.make_block_net("LCxLC", 8_499_001)[0]
Wb = np.asarray(b1.W, float)
diff = Wb != W
r, c = np.nonzero(diff)
print("B1 vs DATA differing entries", diff.sum(), "all within LCxLC:", np.isin(r, lc).all() and np.isin(c, lc).all())
