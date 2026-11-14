"""flymind/test_block_shuffle.py — run: .venv/bin/python -I -B flymind/test_block_shuffle.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from block_shuffle import BLOCKS, block_masks, block_shuffle, graph_metrics, layer_of, strongest_preserved  # noqa: E402
from side_shuffle import KEYS, layer_side_labels, properties, shuffle_within_side  # noqa: E402
from visual_path import network  # noqa: E402

spec, idx, _ = network(0.2)
gr, _ = layer_side_labels(spec, idx)
lay = layer_of(gr)
S = 8_490_010                                               # smoke pool
# T1 ALL == frozen SWS v2 bit-exactly
a, b = block_shuffle(spec, gr, S, "ALL"), shuffle_within_side(spec, gr, S)
assert np.array_equal(a.W_data, b.W_data), "T1 ALL != SWS"
masks = block_masks(gr)
for name in ("LCxLC", "LC2MID", "MID2LC", "MIDxMID"):
    sh = block_shuffle(spec, gr, S, name, max_attempt_factor=10)
    rep = sh.report["block_shuffle"]
    m = masks[name]
    # T2 only the block changes; T3 SWS invariants hold; T4 nontrivial and complete
    assert np.array_equal(sh.W_data[~m], spec.W_data[~m]), f"T2 {name}: edges outside block changed"
    p = properties(spec, sh, gr)
    assert all(p[k] for k in KEYS), f"T3 {name}: {[k for k in KEYS if not p[k]]}"
    assert rep["complete"] and ((sh.W_data != 0) & (spec.W_data == 0))[m].any(), f"T4 {name}"
    # T5 block edge count matches mask
    assert rep["block_edges"] == int((spec.W_data[m] != 0).sum()), f"T5 {name}"
    print(name, rep, "| changed frac in block", round(float(((sh.W_data != 0) & (spec.W_data == 0))[m].sum() / (spec.W_data[m] != 0).sum()), 3))
# T6 blocks partition the swappable edges of SWS (dn-involving keys cannot change)
union = np.zeros_like(masks["LCxLC"])
for k in ("LCxLC", "LC2MID", "MID2LC", "MIDxMID"):
    union |= masks[k]
rest = (spec.W_data != 0) & ~union
assert np.all(np.isin(lay[np.nonzero(rest)[0]], ["dn"]) | np.isin(lay[np.nonzero(rest)[1]], ["dn"])), "T6 edges outside blocks must touch DNa02"
assert np.array_equal(b.W_data[rest], spec.W_data[rest]), "T6 SWS changed a DNa02 edge"
# T7 graph metrics deterministic and DATA LC×LC reciprocity = 2450 (known value)
g0 = graph_metrics(spec.W_data, gr)
assert g0["LCxLC"]["reciprocal_pairs"] == 2450 and g0 == graph_metrics(spec.W_data, gr), "T7"
assert strongest_preserved(spec.W_data, spec.W_data) == {"top1pct": 1.0, "top5pct": 1.0}
print("test_block_shuffle: 7 tests OK")
