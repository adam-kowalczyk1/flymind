"""Buduje touch_map.json: podział 322 szczecinek T2 L na 'udo' (szczęka stała) i 'goleń+stopa' (szczęka ruchoma).
Literatura (Marin 2024, Takemura 2024, VFB, Tsubouchi 2017, Elabbady 2025) NIE podaje tabeli typ SNta → segment nogi (sprawdzone 19 XI),
więc: HIPOTEZA oparta na danych — 2 klastry typów wg profilu połączeń wyjściowych (kosinus, k-means).
Który klaster jest 'udem' — arbitralne (brak zasady); dlatego test używa też mapowania 'swap'."""
import json
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from scipy.cluster.hierarchy import fcluster, linkage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nets  # noqa: E402

VP = nets.visual_path
a = pd.read_feather(VP.ANN, columns=["bodyId", "type", "subclass", "rootSide", "entryNerve"])
s = a[(a.subclass == "mechanosensory bristle") & a.entryNerve.astype(str).str.contains("MesoLN") & (a.rootSide == "L")]
ids = sorted(int(b) for b in s.bodyId)
ty = s.set_index("bodyId").type.astype(str)
W = ds.dataset(VP.WEIGHTS, format="ipc").to_table(filter=ds.field("body_pre").isin(ids)).to_pandas()
W["t"] = W.body_pre.map(ty)
M = W.pivot_table(index="t", columns="body_post", values="weight", aggfunc="sum", fill_value=0)
M = M.div(M.sum(1), axis=0)
from scipy.cluster.vq import kmeans2
w = np.array([(ty == t).sum() for t in M.index])
X = M.values / np.linalg.norm(M.values, axis=1, keepdims=True)
U, S, _ = np.linalg.svd(X - np.average(X, axis=0, weights=w), full_matrices=False)
best = None
for seed in range(50):                                                   # k-means k=2 na 4 pierwszych składowych, wybór najbardziej zrównoważonego z najlepszą inercją
    c, lab = kmeans2(U[:, :4] * S[:4], 2, seed=seed, minit="++")
    if len(set(lab)) < 2:
        continue
    cost = sum(((U[lab == k, :4] * S[:4] - c[k]) ** 2).sum() for k in (0, 1))
    if best is None or cost < best[0] - 1e-9:
        best = (cost, lab)
cl = best[1] + 1
# ponytail: k-means zamiast drzewa — drzewo (k-means) wydzielało tylko 34 komórki (SNta21, SNta38)
n = {c: int(sum((ty == t).sum() for t in M.index[cl == c])) for c in (1, 2)}
print("klastry (komórki):", n)
# kolejność: klaster A = ten z mniejszym numerem fcluster (arbitralnie 'femur')
per, fem, tt = {}, [], []
for t, c in zip(M.index, cl):
    seg = "femur" if c == 1 else "tibia_tarsus"
    per[t] = dict(segment=seg, source="HIPOTEZA: klaster profilu wyjść (k-means, 4 składowe SVD), przypisanie klastra do segmentu arbitralne", cluster=int(c))
    (fem if c == 1 else tt).extend(int(b) for b in ty.index[ty == t])
out = dict(femur=sorted(fem), tibia_tarsus=sorted(tt), unassigned=[], per_type=per, status="hypothesis",
           method="2 klastry typów SNta T2 L (MesoLN, L) wg znormalizowanego profilu połączeń wyjściowych; literatura nie daje mapy typ→segment; "
                  "który klaster = udo jest arbitralne (nieobronione) — mapowanie 'swap' jest równorzędne")
json.dump(out, open(os.path.join(HERE, "touch_map.json"), "w"), indent=1)
for c in (1, 2):
    print(c, list(M.index[cl == c]))
print(len(fem), len(tt))
