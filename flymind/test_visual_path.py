"""Testy visual_path: tasowanie (syntetyczne) i wybór sieci z danych MaleCNS. Uruchom: .venv/bin/python -I -B flymind/test_visual_path.py"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snn_interface import ModelEdge, build  # noqa: E402
from visual_path import network, shuffle  # noqa: E402

n = 0
rng = np.random.default_rng(1001)
B = np.arange(1, 41)
e = pd.DataFrame([(a, b, int(rng.integers(1, 20))) for a in B for b in B if a != b and rng.random() < 0.15],
                 columns=["body_pre", "body_post", "weight"])
nt = pd.DataFrame(dict(body=B, ground_truth=[None] * 40, consensus_nt=["acetylcholine"] * 30 + ["gaba"] * 10,
                       celltype_predicted_nt=["unclear"] * 40))
s = build(e, B, nt)
t = shuffle(s, 1001)
A, Bm = s.W_data != 0, t.W_data != 0
assert (A.sum(0) == Bm.sum(0)).all() and (A.sum(1) == Bm.sum(1)).all(); n += 1          # stopnie wyjścia/wejścia
assert np.allclose(s.W_data.sum(0), t.W_data.sum(0)); n += 1                           # siła wyjściowa i znak pre
assert (A != Bm).sum() > A.sum(); n += 1                                                # faktycznie przetasowane
assert not np.diag(t.W_data).any(); n += 1                                              # bez autapsów
assert (shuffle(s, 1001).W_data == t.W_data).all() and (shuffle(s, 1002).W_data != t.W_data).any(); n += 1
try:
    shuffle(build(e, B, nt, model_edges=[ModelEdge(1, 2, 1.0, "x")] if not ((e.body_pre == 1) & (e.body_post == 2)).any()
                  else [ModelEdge(2, 1, 1.0, "x")]), 1); raise AssertionError
except ValueError:
    n += 1
u = shuffle(s, 1003, equal_weight=True)
assert np.allclose(u.W_data.sum(1), s.W_data.sum(1)) and np.allclose(u.W_data.sum(0), s.W_data.sum(0)); n += 1   # siła wej./wyj.
assert ((u.W_data != 0) != A).sum() > 0; n += 1
spec, idx, rep = network(0.2)                                                          # dane MaleCNS
assert rep["sizes"] == dict(in_L=135, in_R=140, mid=147, DNa02_L=1, DNa02_R=1); n += 1
assert rep["edges"]["edges"] == 13510 and not spec.W_model.any(); n += 1
assert sum(len(v) for v in idx.values()) == len(spec.bodies) == 424; n += 1
print(f"OK: visual_path ({n} asercji)")
