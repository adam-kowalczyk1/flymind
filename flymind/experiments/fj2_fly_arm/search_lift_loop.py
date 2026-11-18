"""Przeszukanie danych (tylko odczyt, bez symulacji): pętla dotyk nogi T2 L → neurony wstępujące (AN) → mózg → neurony
zstępujące (DN) → pule wymachu vs podporu tej nogi. Miara: iloczyny liczby synaps po ścieżkach (strukturalna, bez znaku).
Uruchom:  .venv/bin/python -I -B flymind/experiments/fj2_fly_arm/search_lift_loop.py"""
import os
import sys

import pandas as pd
import pyarrow.dataset as ds

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from leg_circuit import select  # noqa: E402
from visual_path import ANN, WEIGHTS  # noqa: E402

T = 5
SWING = ("Sternal anterior rotator MN", "Tr flexor MN")
STANCE = ("Pleural remotor/abductor MN", "Sternal posterior rotator MN", "Tr extensor MN", "Sternotrochanter MN", "Tergotr. MN")
a = pd.read_feather(ANN, columns=["bodyId", "type", "superclass", "somaSide"]).set_index("bodyId")
W = ds.dataset(WEIGHTS, format="ipc")
q = lambda col, ids: W.to_table(filter=ds.field(col).isin([int(x) for x in ids])).to_pandas()  # noqa: E731
sup = lambda b: a.superclass.reindex(b).values  # noqa: E731

bodies, g, _ = select("T2", "L")
br = g["sensory"]["mechanosensory bristle"]
INs = set(g["IN"])
# 1) dotyk → AN: bezpośrednio albo przez IN obwodu (≥T na krawędź)
e1 = q("body_pre", br); e1 = e1[e1.weight >= T]
an_direct = e1[sup(e1.body_post.values) == "ascending_neuron"].groupby("body_post").weight.sum()
mid = e1[e1.body_post.isin(INs)]
e2 = q("body_pre", mid.body_post.unique()); e2 = e2[(e2.weight >= T) & (sup(e2.body_post.values) == "ascending_neuron")]
p = mid.merge(e2, left_on="body_post", right_on="body_pre", suffixes=("1", "2"))
an_via = (p.weight1 * p.weight2).groupby(p.body_post2).sum()
AN = pd.concat([an_direct.rename("direct"), an_via.rename("via_IN")], axis=1).fillna(0)
AN["touch_score"] = AN.direct * 20 + AN.via_IN                  # ponytail: skala heurystyczna (bezp. ≈ 20× ścieżki 2-skok.)
print(f"AN z wejściem dotykowym T2 L: {len(AN)} (bezpośrednio {int((AN.direct > 0).sum())})")
# 2) AN → DN: bezpośrednio albo przez 1 neuron mózgu
e3 = q("body_pre", AN.index); e3 = e3[e3.weight >= T]
dn_d = e3[sup(e3.body_post.values) == "descending_neuron"]
brain = e3[~pd.Series(sup(e3.body_post.values)).str.startswith(("vnc", "ascending_neuron", "descending_neuron", "sensory"), na=False).values]
e4 = q("body_pre", brain.body_post.unique()); e4 = e4[(e4.weight >= T) & (sup(e4.body_post.values) == "descending_neuron")]
pp = brain.merge(e4, left_on="body_post", right_on="body_pre", suffixes=("1", "2"))
s_touch = AN.touch_score
dn_score = (dn_d.weight * s_touch.reindex(dn_d.body_pre).values).groupby(dn_d.body_post).sum().rename("direct")
dn_score2 = (pp.weight1 * pp.weight2 * s_touch.reindex(pp.body_pre1).values).groupby(pp.body_post2).sum().rename("via_brain")
DN = pd.concat([dn_score, dn_score2], axis=1).fillna(0)
DN["touch_in"] = DN.direct * 20 + DN.via_brain
print(f"DN osiągalne z dotyku przez AN: {len(DN)} (bezpośrednio AN→DN {int((DN.direct > 0).sum())})")
# 3) DN → pule wymachu / podporu T2 L (bezpośrednio albo przez 1 neuron VNC)
mn = {k: set(v) for k, v in g["MN"].items()}
sw, st = set().union(*[mn.get(x, set()) for x in SWING]), set().union(*[mn.get(x, set()) for x in STANCE])
cand = DN.sort_values("touch_in", ascending=False).head(300).index
e5 = q("body_pre", cand); e5 = e5[e5.weight >= T]
e6 = q("body_pre", e5.body_post.unique()); e6 = e6[(e6.weight >= T) & e6.body_post.isin(sw | st)]
path = e5.merge(e6, left_on="body_post", right_on="body_pre", suffixes=("1", "2"))
path["pp"] = path.weight1 * path.weight2
direct = e5[e5.body_post.isin(sw | st)]
out = pd.DataFrame(index=cand)
for name, S in (("swing", sw), ("stance", st)):
    out[name] = (path[path.body_post2.isin(S)].groupby("body_pre1").pp.sum().reindex(cand).fillna(0)
                 + 20 * direct[direct.body_post.isin(S)].groupby("body_pre").weight.sum().reindex(cand).fillna(0))
out["touch_in"] = DN.touch_in.reindex(cand)
out["swing_bias"] = (out.swing - out.stance) / (out.swing + out.stance).clip(lower=1)
out["type"], out["side"] = a.type.reindex(cand).values, a.somaSide.reindex(cand).values
top = out[(out.swing + out.stance) > 0].assign(score=lambda d: d.touch_in.rank(pct=True) * d.swing.rank(pct=True))
print("\nDN: wejście z dotyku T2 L (przez AN) i wyjście na pule wymachu vs podporu T2 L — 15 najlepszych wg dotyk × wymach:")
print(top.sort_values("score", ascending=False).head(15)[["type", "side", "touch_in", "swing", "stance", "swing_bias"]].round(2).to_string())
print("\nNajsilniej wymachowe (swing_bias > 0.3, wymach > 0):")
print(top[(top.swing_bias > 0.3)].sort_values("swing", ascending=False).head(10)[["type", "side", "touch_in", "swing", "stance", "swing_bias"]].round(2).to_string())
print("\nAN najsilniej z dotykiem:", AN.sort_values("touch_score", ascending=False).head(8).assign(type=lambda d: a.type.reindex(d.index).values)[["type", "direct", "via_IN"]].to_string())
