"""Samosprawdzenie: (a) konwencja hex z danych (L1→Mi1), (b) wycinek = 5120, (d) C1 zachowuje bloki i stopnie, (e) DSI bez sieci ≈ 0."""
import collections
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eye_gate as G  # noqa: E402
import eye_gate_analysis as A  # noqa: E402
import optic_slice as OS  # noqa: E402

S = OS.build()
assert len(S["bodies"]) == 5120 and len(S["n"]) == 124134 and int(S["n"].sum()) == 799229          # (b)
t = S["type"]
m = (t[S["pre"]] == "L1") & (t[S["post"]] == "Mi1") & (S["n"] >= 5)
off = collections.Counter(zip((S["hexq"][S["post"]] - S["hexq"][S["pre"]])[m].astype(int), (S["hexr"][S["post"]] - S["hexr"][S["pre"]])[m].astype(int)))
assert off[(0, 0)] > 10 * max(v for k, v in off.items() if k != (0, 0)), off                     # (a) ta sama kolumna dominuje
assert off[(1, -1)] + off[(-1, 1)] <= off[(1, 1)] + off[(-1, -1)] + 2, off                       # (a) sąsiedzi to (1,1)/(−1,−1), nie (1,−1)
T, done = G.shuffle_typed(S, 15501050, swaps_per_edge=1)
assert done > 0.3 * len(S["n"])
for arr in ("pre", "post"):
    assert (np.bincount(S[arr], minlength=5120) == np.bincount(T[arr], minlength=5120)).all()     # (d) stopnie
assert collections.Counter(zip(t[S["pre"]], t[S["post"]])) == collections.Counter(zip(t[T["pre"]], t[T["post"]]))  # (d) bloki
# (e) „sieć” bez połączeń: L1 odpowiada na krawędź tak samo w każdym kierunku → DSI ≈ 0 (przez szum)
import scipy.sparse as sp
W0 = sp.csr_matrix((5120, 5120))
R, _, combos = G.simulate(W0, S, "S1", [15501051, 15501052, 15501053, 15501054], speed=240.0)
k = t == "L1"
X = np.stack([R[k][:, :, :2].mean(2), R[k][:, :, 2:].mean(2)], -1)[:, None].repeat(4, 1)
d, _ = A.dsi(X, t[k], -1)
assert abs(np.nanmedian(d)) < 0.1, np.nanmedian(d)
print("test_eye_gate OK; offsety L1→Mi1:", dict(off.most_common(7)), "| zamian C1:", done, "| DSI bez sieci:", round(float(np.nanmedian(d)), 3))
