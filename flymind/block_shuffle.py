"""flymind/block_shuffle.py — V5 v4.2 single-block controls (CONTROL). No mujoco, no bio2; frozen side_shuffle untouched.

Rule = SHUF_WITHIN_SIDE v2 (side_shuffle.shuffle_within_side) restricted to ONE connectivity block: double edge swaps
(a→b, c→d) → (a→d, c→b) only between data edges with identical key (signed weight, layer×side group of pre, of post) AND whose
(layer(pre), layer(post)) is in the block. Blocks (layers: 'in' = LC10a, 'mid' = intermediates, 'dn' = DNa02):
  LCxLC   in → in      LC2MID  in → mid     MID2LC  mid → in     MIDxMID  mid → mid     ALL  every block (= SWS v2)
Edges outside the block are untouched (same pre, post, weight). Target swaps = n_swaps_per_edge × (edges of the block).
With block ALL the rng call sequence is identical to side_shuffle.shuffle_within_side → bit-identical output (test).
Preserved within the block by construction: per-neuron in/out degree and strength, per-neuron multisets of (partner group, weight),
group×group block sums, weight multiset, Dale. Not preservable in general: motifs that combine the shuffled block with an untouched
one (e.g. LC→mid shuffled alone changes LC↔mid reciprocal pairs, which also involve mid→LC edges) — measured, not assumed.
"""
import numpy as np

from connectome import ConnectomeError
from snn_interface import SNNSpec

BLOCKS = {"LCxLC": {("in", "in")}, "LC2MID": {("in", "mid")}, "MID2LC": {("mid", "in")}, "MIDxMID": {("mid", "mid")},
          "ALL": None}


def layer_of(groups):
    return np.array([g.split("_")[0] for g in groups])


def block_shuffle(spec, groups, seed, block, n_swaps_per_edge=5, max_attempt_factor=3):
    if spec.W_model.any():
        raise ConnectomeError("block_shuffle: model edges present")
    groups = np.asarray(groups)
    lay = layer_of(groups)
    allowed = BLOCKS[block]
    post, pre = np.nonzero(spec.W_data)
    w = spec.W_data[post, pre].copy()
    inb = np.ones(len(w), bool) if allowed is None else np.array([(lay[a], lay[b]) in allowed for a, b in zip(pre, post)])
    E = int(inb.sum())
    keys = {}
    for k in np.flatnonzero(inb):
        keys.setdefault((float(w[k]), groups[pre[k]], groups[post[k]]), []).append(k)
    keys = [np.array(g) for g in keys.values() if len(g) > 1]
    if not keys:
        raise ConnectomeError("no swappable edge pairs in block")
    p = np.array([len(g) for g in keys], float)
    p /= p.sum()
    rng = np.random.default_rng(seed)
    exists = set(zip(pre.tolist(), post.tolist()))
    done = tried = 0
    target = n_swaps_per_edge * E
    while done < target and tried < max_attempt_factor * target:
        tried += 1
        g = keys[rng.choice(len(keys), p=p)]
        i, j = rng.choice(g, 2, replace=False)
        a, b, c, d = pre[i], post[i], pre[j], post[j]
        if b == d or a == d or c == b or (a, d) in exists or (c, b) in exists:
            continue
        exists -= {(a, b), (c, d)}
        exists |= {(a, d), (c, b)}
        post[i], post[j] = d, b
        done += 1
    Wd = np.zeros_like(spec.W_data)
    Wd[post, pre] = w
    rep = dict(spec.report, block_shuffle=dict(block=block, seed=seed, swaps=done, target=target, attempts=tried,
                                               complete=done == target, block_edges=E,
                                               block_edges_swappable=int(sum(len(g) for g in keys))))
    return SNNSpec(spec.bodies, spec.nt, spec.sign, Wd, spec.W_model.copy(), rep)


def block_masks(groups):
    lay = layer_of(np.asarray(groups))
    return {name: (np.isin(lay, [a for a, _ in s])[None, :] & np.isin(lay, [b for _, b in s])[:, None]) if s else None
            for name, s in BLOCKS.items() if s}


def graph_metrics(W, groups):
    """Graph statistics of the data-edge graph (A[post, pre]). Whole network + per block. Pure numpy/scipy."""
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components
    groups = np.asarray(groups)
    lay = layer_of(groups)
    A = W != 0
    absw = np.abs(W)
    out = {}
    U = (A | A.T)
    Uf = U.astype(float)
    deg = U.sum(1)
    tri_node = np.einsum("ij,jk,ki->i", Uf, Uf, Uf) / 2
    clust = np.where(deg > 1, tri_node / np.maximum(deg * (deg - 1) / 2, 1), 0.0)
    indeg, outdeg = A.sum(1), A.sum(0)
    post, pre = np.nonzero(A)
    def r(x, y):
        return float(np.corrcoef(x, y)[0, 1]) if np.std(x) > 0 and np.std(y) > 0 else None
    out["all"] = dict(edges=int(A.sum()), abs_w=float(absw.sum()), reciprocal_pairs=int((A & A.T).sum() // 2),
                      triangles=int(np.trace(Uf @ Uf @ Uf) // 6), avg_clustering=float(clust.mean()),
                      assort_out_in=r(outdeg[pre], indeg[post]), assort_in_in=r(indeg[pre], indeg[post]),
                      assort_out_out=r(outdeg[pre], outdeg[post]),
                      n_strong_cc=int(connected_components(csr_matrix(A.T), directed=True, connection="strong")[0]),
                      largest_strong_cc=int(np.bincount(connected_components(csr_matrix(A.T), directed=True, connection="strong")[1]).max()),
                      n_weak_cc=int(connected_components(csr_matrix(A.T), directed=True, connection="weak")[0]))
    # LC×LC sub-block and LC↔mid cross motifs
    inn, mid = lay == "in", lay == "mid"
    B = A[np.ix_(inn, inn)]
    Bu = (B | B.T).astype(float)
    dB = Bu.sum(1)
    tB = np.einsum("ij,jk,ki->i", Bu, Bu, Bu) / 2
    out["LCxLC"] = dict(edges=int(B.sum()), abs_w=float(absw[np.ix_(inn, inn)].sum()), reciprocal_pairs=int((B & B.T).sum() // 2),
                        triangles=int(np.trace(Bu @ Bu @ Bu) // 6),
                        avg_clustering=float(np.where(dB > 1, tB / np.maximum(dB * (dB - 1) / 2, 1), 0).mean()))
    M = A[np.ix_(mid, mid)]
    Mu = (M | M.T).astype(float)
    out["MIDxMID"] = dict(edges=int(M.sum()), abs_w=float(absw[np.ix_(mid, mid)].sum()), reciprocal_pairs=int((M & M.T).sum() // 2),
                          triangles=int(np.trace(Mu @ Mu @ Mu) // 6))
    lc2mid = A[np.ix_(mid, inn)]                            # post mid, pre in
    mid2lc = A[np.ix_(inn, mid)]
    out["LC_MID"] = dict(lc2mid_edges=int(lc2mid.sum()), mid2lc_edges=int(mid2lc.sum()),
                         lc_mid_reciprocal_pairs=int((lc2mid & mid2lc.T).sum()),
                         abs_w_lc2mid=float(absw[np.ix_(mid, inn)].sum()), abs_w_mid2lc=float(absw[np.ix_(inn, mid)].sum()))
    return out


def strongest_preserved(W0, W1, q=(0.99, 0.95)):
    """Fraction of DATA's strongest edges (top 1 %, 5 % by |w|) present at the same (pre, post) with the same weight."""
    post, pre = np.nonzero(W0)
    w = np.abs(W0[post, pre])
    out = {}
    for qq in q:
        m = w >= np.quantile(w, qq)
        out[f"top{round((1 - qq) * 100)}pct"] = float((W1[post[m], pre[m]] == W0[post[m], pre[m]]).mean())
    return out
