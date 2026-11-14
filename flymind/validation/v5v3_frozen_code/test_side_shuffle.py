"""Testy SHUF_WITHIN_SIDE (side_shuffle.py, wersja 2: grupy warstwa × strona): syntetyczne + przypadki Red Team (A, B, C)
+ sieć z danych MaleCNS (bez symulacji). Ziarna 1001–1003 (synt.), 1401–1403 (tasowania sieci z danych).
Uruchom: .venv/bin/python -I -B flymind/test_side_shuffle.py"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from connectome import ConnectomeError  # noqa: E402
from side_shuffle import KEYS, group_block, layer_side_labels, properties, shuffle_within_side  # noqa: E402
from snn_interface import ModelEdge, SNNSpec, build  # noqa: E402
from v5v2_topology import lateralization  # noqa: E402
from visual_path import ANN, NTS, WEIGHTS, network  # noqa: E402

n = 0
rng = np.random.default_rng(1001)
B = np.arange(1, 61)
e = pd.DataFrame([(a, b, int(rng.integers(1, 6))) for a in B for b in B if a != b and rng.random() < 0.2],
                 columns=["body_pre", "body_post", "weight"])
nt = pd.DataFrame(dict(body=B, ground_truth=[None] * 60, consensus_nt=(["acetylcholine"] * 20 + ["gaba"] * 5) * 2 + ["acetylcholine"] * 10,
                       celltype_predicted_nt=["unclear"] * 60))
s = build(e, B, nt)
g = np.array(["x_L"] * 25 + ["x_R"] * 25 + ["x_U"] * 10)
W_before = s.W_data.copy()
t = shuffle_within_side(s, g, 1001)
p = properties(s, t, g)
assert all(p[k] for k in KEYS), {k: p[k] for k in KEYS if not p[k]}; n += 1                # wszystkie własności
assert t.report["shuffle_within_side"]["complete"]; n += 1                                    # cel zamian osiągnięty
assert np.array_equal(s.W_data, W_before); n += 1                                             # źródło nietknięte
assert np.array_equal(shuffle_within_side(s, g, 1001).W_data, t.W_data); n += 1             # deterministyczne
assert not np.array_equal(shuffle_within_side(s, g, 1002).W_data, t.W_data); n += 1         # inne ziarno → inna sieć
bs, bt = group_block(s.W_data, g), group_block(t.W_data, g)
assert all(bs[k] == bt[k] for k in bs if "x_U" in k) and set(bs) == set(bt); n += 1         # grupa U tylko wewnątrz U

mk = lambda W: SNNSpec(s.bodies, s.nt, s.sign, W, s.W_model.copy(), {})
# (A) permutacja wag na tym samym zbiorze krawędzi (w obrębie kolumn tego samego znaku) — topologia ta sama, wagi nie
WA = s.W_data.copy()
for j in range(WA.shape[1]):
    nz = np.flatnonzero(WA[:, j])
    WA[nz, j] = WA[rng.permutation(nz), j]
WA[:, 0] = WA[:, 0][::-1] if WA[:, 0].any() else WA[:, 0]
pa = properties(s, mk(WA), g)
assert not all(pa[k] for k in KEYS), "A niewykryte"; n += 1
# (B) tożsamość — nie jest tasowaniem
assert not properties(s, mk(s.W_data.copy()), g)["nontrivial"]; n += 1
# (C) zamiana etykiet grup pre E/I między stronami: przenieś wyjścia neuronu hamującego L na hamujący R
WC = s.W_data.copy()
WC[:, [20, 45]] = WC[:, [45, 20]]                                                             # 20: gaba L, 45: gaba R
pc = properties(s, mk(WC), g)
assert not (pc["post_group_composition"] and pc["group_block"]), "C niewykryte"; n += 1
# (P2, RT runda 2) dwa neurony post z jednej grupy wymieniają wzorce wag między grupami pre przy zachowanych sumach,
# licznikach i całkowitych multizbiorach: b: A{1,3} B{2,2}, d: A{2,2} B{1,3}  →  b: A{2,2} B{1,3}, d: A{1,3} B{2,2}
gp = np.array(["A"] * 4 + ["B"] * 4 + ["P"] * 2)
W2 = np.zeros((10, 10))
for col, (wb, wd) in zip(range(8), [(1, 2), (3, 2), (0, 0), (0, 0), (2, 1), (2, 3), (0, 0), (0, 0)]):
    W2[8, col], W2[9, col] = wb, wd
W3 = W2.copy()
W3[8, [0, 1, 4, 5]], W3[9, [0, 1, 4, 5]] = [2, 2, 1, 3], [1, 3, 2, 2]
ten = np.arange(1, 11)
sp2 = SNNSpec(ten, None, np.ones(10), W2, np.zeros((10, 10)), {})
p2 = properties(sp2, SNNSpec(ten, None, np.ones(10), W3, np.zeros((10, 10)), {}), gp)
assert p2["in_strength"] and p2["pre_group_composition"] and not p2["in_group_weight_multisets"]; n += 1
for args in ((build(e, B, nt, model_edges=[ModelEdge(2, 1, 1.0, "x")] if not ((e.body_pre == 2) & (e.body_post == 1)).any()
                    else [ModelEdge(1, 2, 1.0, "x")]), g), (s, g[:-1])):
    try:
        shuffle_within_side(*args, 1)
        raise AssertionError("brak odmowy")
    except ConnectomeError:
        n += 1

# ---- sieć z danych ----
stat = {f: os.stat(f)[6:9] for f in (ANN, NTS, WEIGHTS)}
spec, idx, _ = network(0.2)
gr, grep_ = layer_side_labels(spec, idx)
assert grep_["counts"] == {"R": 230, "L": 194}; n += 1                                      # strony z metadanych, brak 'U'
assert grep_["groups"] == {"dn_L": 1, "dn_R": 1, "in_L": 135, "in_R": 140, "mid_L": 58, "mid_R": 89}; n += 1
W0 = spec.W_data.copy()
li0 = lateralization(spec.W_data, idx)
dn = np.r_[idx["DNa02_L"], idx["DNa02_R"]]
lc = np.r_[idx["in_L"], idx["in_R"]]
for seed in (1401, 1402, 1403):
    sh = shuffle_within_side(spec, gr, seed)
    p = properties(spec, sh, gr)
    assert all(p[k] for k in KEYS), (seed, {k: p[k] for k in KEYS if not p[k]}); n += 1
    assert sh.report["shuffle_within_side"]["complete"] and p["changed_frac"] > 0.3; n += 1
    assert np.array_equal(sh.W_data[dn], W0[dn]); n += 1                                      # wejścia DNa02 niezmienione
    assert not sh.W_data[np.ix_(dn, lc)].any(); n += 1                                        # brak krawędzi LC10a → DNa02
    rec = lambda W: int(((W[np.ix_(lc, lc)] != 0) & (W[np.ix_(lc, lc)].T != 0)).sum() // 2)
    print(f"ziarno {seed}: zmienione krawędzie {p['changed_frac']:.3f}, Jaccard {p['jaccard_edges']:.3f}, "
          f"lateralizacja ścieżek ≤ 2 = {lateralization(sh.W_data, idx) / li0:.4f} × DATA, "
          f"wzajemne pary LC–LC {rec(sh.W_data)} (DATA {rec(W0)})")
assert np.array_equal(spec.W_data, W0); n += 1                                                # sieć źródłowa nietknięta
assert {f: os.stat(f)[6:9] for f in stat} == stat; n += 1                                     # pliki danych nietknięte
print(f"OK: side_shuffle v2 ({n} asercji)")
