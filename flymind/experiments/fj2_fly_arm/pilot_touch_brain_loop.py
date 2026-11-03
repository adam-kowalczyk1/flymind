"""Pilot (eksploracja, bez ziaren, szum 0): czy pętla dotyk → AN → mózg → DN → VNC → MN zmienia odpowiedź nogi T2 L na
dotyk (wymach vs podpór) względem samego obwodu nogi? Wybór DN/AN WYŁĄCZNIE wg siły wejścia z dotyku (nie wg wyjścia),
żeby nie wybierać pod wynik. Wejście: tylko prąd do receptorów szczecinkowych (dotyk). J0 = 0,275 (Shiu 2024).
Uruchom:  .venv/bin/python -I -B flymind/experiments/fj2_fly_arm/pilot_touch_brain_loop.py [n_dn]"""
import os
from types import SimpleNamespace
import sys

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

T, N_AN = 5, 100
N_DN = int(sys.argv[1]) if len(sys.argv) > 1 else 100
SWING = ("Sternal anterior rotator MN", "Tr flexor MN")
STANCE = ("Pleural remotor/abductor MN", "Sternal posterior rotator MN", "Tr extensor MN", "Sternotrochanter MN", "Tergotr. MN")
a = pd.read_feather(ANN, columns=["bodyId", "superclass"]).set_index("bodyId").superclass
W = ds.dataset(WEIGHTS, format="ipc")
q = lambda col, ids: W.to_table(filter=ds.field(col).isin([int(x) for x in ids])).to_pandas()  # noqa: E731
leg, g, _ = select("T2", "L")
br = g["sensory"]["mechanosensory bristle"]
e = q("body_pre", leg); e = e[(e.weight >= T) & (a.reindex(e.body_post).values == "ascending_neuron")]
AN = e.groupby("body_post").weight.sum().sort_values(ascending=False).head(N_AN).index      # AN z najsilniejszym wejściem z obwodu nogi
e = q("body_pre", AN); e = e[e.weight >= T]
dn_direct = e[a.reindex(e.body_post).values == "descending_neuron"].groupby("body_post").weight.sum()
brain = e[pd.Series(a.reindex(e.body_post).values).isin(["cb_intrinsic", "visual_projection", "ol_intrinsic"]).values | pd.isna(a.reindex(e.body_post).values)]
e2 = q("body_pre", brain.body_post.unique()); e2 = e2[(e2.weight >= T) & (a.reindex(e2.body_post).values == "descending_neuron")]
dn_score = dn_direct.add(e2.groupby("body_post").weight.sum(), fill_value=0)
DN = dn_score.sort_values(ascending=False).head(N_DN).index                                # DN wg wejścia (nie wyjścia)
mids = sorted(set(brain.body_post) & set(e2[e2.body_post.isin(DN)].body_pre))
e3 = q("body_pre", DN); e3 = e3[(e3.weight >= T) & (a.reindex(e3.body_post).values == "vnc_intrinsic")]
e4 = q("body_pre", e3.body_post.unique()); e4 = e4[(e4.weight >= T) & e4.body_post.isin(set(leg))]
relay = sorted(set(e4.body_pre) - set(leg))
B = list(dict.fromkeys([int(x) for x in leg] + [int(x) for x in AN] + [int(x) for x in mids] + [int(x) for x in DN] + [int(x) for x in relay]))
print(f"leg {len(leg)}, AN {len(AN)}, brain mids {len(mids)}, DN {len(DN)}, VNC relays {len(relay)}, total {len(B)}")
edges, _ = load_edges(WEIGHTS, bodies=B)
nts = pd.read_feather(NTS); tab = nts.set_index("body").reindex(B)[list(NT_COLS)]
ov = {b: ("unknown", "brak NT; znak 0") for b, r in tab.iterrows() if not any(isinstance(x, str) and x != "unclear" for x in r)}
pos = {b: k for k, b in enumerate(B)}
pool = lambda names: [pos[b] for n in names for b in g["MN"].get(n, [])]  # noqa: E731
sw, st = pool(SWING), pool(STANCE)
for glu in (-1.0, 1.0):
    s = {**DEFAULT_SIGN, "glutamate": glu}; s.update({n: 0.0 for n in set(assign_nt(B, nts, ov).nt) - set(s)})
    spec = build(edges, B, nts, ModelParams(J0=0.275, sign_map=s), nt_overrides=ov)
    for label, cut in (("pełna pętla", False), ("bez pętli (DN wyciszone przez odcięcie wyjść)", True)):
        sp = spec
        if cut:                                       # kontrola: te same neurony, ale DN nie wysyłają sygnału
            Wm = spec.W.copy(); Wm[:, [pos[b] for b in DN]] = 0.0
            sp = SimpleNamespace(W=Wm)
        X = np.zeros(len(B)); X[[pos[b] for b in br]] = 40.0
        r = SparseALIF(sp, ALIFParams(), None).run(X, 600)[100:].mean(0) * 1000
        print(f"Glu {glu:+.0f} {label:45s}: wymach {r[sw].mean():6.1f} Hz, podpór {r[st].mean():6.1f} Hz, "
              f"DN aktywne {int((r[[pos[b] for b in DN]] > 0).sum())}/{len(DN)}, AN aktywne {int((r[[pos[b] for b in AN]] > 0).sum())}/{len(AN)}")
