"""Pilot (eksploracja, bez ziaren, szum 0): dotyk lewej środkowej nogi (T2 L) → czy INNE nogi dostają sygnał wymachu?
Sieć z danych: obwody 6 nóg (leg_circuit) + MN nóg wg podklasy fl/ml/hl (T1 ma biodro na ProAN/VProN/DProN) + przekaźniki
vnc_intrinsic (≥ T od obwodu T2 L i ≥ T do obwodów innych nóg). Wejście: tylko dotyk T2 L (40 mV na szczecinki).
Kontrola: te same neurony, odcięte połączenia z obwodu T2 L do reszty (czy efekt idzie od dotkniętej nogi).
Uruchom:  .venv/bin/python -I -B flymind/experiments/fj2_fly_arm/pilot_touch_other_legs.py"""
import os
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402
from connectome import load_edges  # noqa: E402
from leg_circuit import select  # noqa: E402
from snn_interface import DEFAULT_SIGN, NT_COLS, ModelParams, assign_nt, build  # noqa: E402
from visual_path import ANN, NTS, WEIGHTS  # noqa: E402

T = 5
SWING = ("Sternal anterior rotator MN", "Tr flexor MN", "Tergopleural/Pleural promotor MN")
STANCE = ("Pleural remotor/abductor MN", "Sternal posterior rotator MN", "Tr extensor MN", "Sternotrochanter MN", "Tergotr. MN")
SUB = {"T1": "fl", "T2": "ml", "T3": "hl"}
a = pd.read_feather(ANN, columns=["bodyId", "type", "superclass", "subclass", "somaSide"])
A = a.set_index("bodyId")
W = ds.dataset(WEIGHTS, format="ipc")
q = lambda col, ids: W.to_table(filter=ds.field(col).isin([int(x) for x in ids])).to_pandas()  # noqa: E731
legs, mns = {}, {}
for seg in ("T1", "T2", "T3"):
    for side in ("L", "R"):
        b, g, _ = select(seg, side)
        m = a[(a.superclass == "vnc_motor") & (a.subclass == SUB[seg]) & (a.somaSide == side)]
        legs[seg + side] = (set(b), g)
        mns[seg + side] = {t: sorted(v.bodyId.astype(int)) for t, v in m.groupby(m.type.fillna("NA"))}
touched = legs["T2L"][0]
others = set().union(*[v[0] for k, v in legs.items() if k != "T2L"]) | {b for k, d in mns.items() for v in d.values() for b in v}
e = q("body_pre", touched); e = e[(e.weight >= T) & (A.superclass.reindex(e.body_post).values == "vnc_intrinsic")]
cand = set(e.body_post) - touched - others
e2 = q("body_pre", cand); e2 = e2[(e2.weight >= T) & e2.body_post.isin(others)]
relay = sorted(set(e2.body_pre))
B = list(dict.fromkeys([int(x) for x in sorted(touched)] + [int(x) for x in sorted(others)] + [int(x) for x in relay]))
print(f"sieć: {len(B)} neuronów (T2 L {len(touched)}, inne nogi + MN {len(others)}, przekaźniki {len(relay)})")
edges, _ = load_edges(WEIGHTS, bodies=B)
nts = pd.read_feather(NTS); tab = nts.set_index("body").reindex(B)[list(NT_COLS)]
ov = {b: ("unknown", "brak NT; znak 0") for b, r in tab.iterrows() if not any(isinstance(x, str) and x != "unclear" for x in r)}
pos = {b: k for k, b in enumerate(B)}
br = [pos[b] for b in legs["T2L"][1]["sensory"]["mechanosensory bristle"]]
src = [pos[b] for b in touched]
for glu in (-1.0, 1.0):
    s = {**DEFAULT_SIGN, "glutamate": glu}; s.update({n: 0.0 for n in set(assign_nt(B, nts, ov).nt) - set(s)})
    spec = build(edges, B, nts, ModelParams(J0=0.275, sign_map=s), nt_overrides=ov)
    Wc = spec.W.copy(); mask = np.ones(len(B), bool); mask[src] = False
    Wc[np.ix_(mask, src)] = 0.0                                     # kontrola: obwód T2 L nie wysyła do reszty
    X = np.zeros(len(B)); X[br] = 40.0
    res = {lab: SparseALIF(sp, ALIFParams(), None).run(X, 600)[100:].mean(0) * 1000
           for lab, sp in (("pełna", spec), ("odcięta", SimpleNamespace(W=Wc)))}
    print(f"\nGlu {glu:+.0f}: noga  wymach / podpór (Hz)  [pełna sieć | odcięte wyjście T2 L]")
    for leg, d in mns.items():
        sw = [pos[b] for t in SWING for b in d.get(t, [])]; st = [pos[b] for t in STANCE for b in d.get(t, [])]
        f = lambda r, ix: r[ix].mean() if ix else float("nan")  # noqa: E731
        print(f"   {leg}: {f(res['pełna'], sw):6.1f} / {f(res['pełna'], st):6.1f}   |  {f(res['odcięta'], sw):6.1f} / {f(res['odcięta'], st):6.1f}"
              f"   (MN wymachu {len(sw)}, podporu {len(st)})")
