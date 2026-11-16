"""Krok 3 — warianty sieci ramienia zbudowane WYŁĄCZNIE z danych MaleCNS (reguły wyboru neuronów), bez zmian modułów wspólnych.
Wszystko importowane z kroku 2 (joint_net) i modułów wspólnych; ten plik tylko dobiera inne zbiory neuronów.

Reguły (parametr rule):
  base   = sieć kroku 2 (joint_net.build_net, in_rule "fl"): obwody T2 L + T1 L, MN „fl” L, IN: ≥5 syn od receptorów T1 L i ≥5 do MN
  pre    = base + WSZYSTKIE vnc_intrinsic z ≥ t synapsami do MN „fl” L (przedruchowe; bez warunku na receptory)
  pre2   = pre + vnc_intrinsic z ≥ t synapsami od receptorów T1 L / T2 L (odbiorcy czuciowi; bez warunku na MN)
  full2  = pre2 + vnc_intrinsic z ≥ t synapsami OD odbiorców czuciowych i ≥ t DO przedruchowych (ogniwo pośrednie)
"""
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

HERE = os.path.dirname(os.path.abspath(__file__))
FLY = os.path.dirname(os.path.dirname(HERE))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(FLY, "experiments", "step2_whole_arm"))
sys.path.insert(0, FLY)
import joint_net as JN  # noqa: E402
import visual_path  # noqa: E402
from connectome import load_edges  # noqa: E402
from leg_circuit import select  # noqa: E402
from snn_interface import DEFAULT_SIGN, NT_COLS, ModelParams, assign_nt, build  # noqa: E402

NAMES = {1: ("j1+ wymach", "j1- podpór"), 2: ("j2+ Ti flex", "j2- Ti ext"), 3: ("j3+ Ta lev", "j3- Ta dep"),
         4: ("j4+ Tr flex", "j4- Tr ext")}


def bodies_for(rule, t=5):
    a = pd.read_feather(visual_path.ANN, columns=["bodyId", "type", "superclass", "subclass", "somaSide"])
    t2, g2, _ = select("T2", "L")
    t1, g1, _ = select("T1", "L")
    fl = a[(a.superclass == "vnc_motor") & (a.subclass == "fl") & (a.somaSide == "L")]
    flb = sorted(fl.bodyId.astype(int))
    intr = set(a.bodyId[a.superclass == "vnc_intrinsic"].astype(int))
    W = ds.dataset(visual_path.WEIGHTS, format="ipc")
    sens1 = sorted({int(b) for v in g1["sensory"].values() for b in v})
    sens2 = sorted({int(b) for v in g2["sensory"].values() for b in v})
    q_out = lambda pre: W.to_table(filter=ds.field("body_pre").isin(sorted(pre))).to_pandas().groupby("body_post").weight.sum()  # noqa: E731
    q_in = lambda post: W.to_table(filter=ds.field("body_post").isin(sorted(post))).to_pandas().groupby("body_pre").weight.sum()  # noqa: E731
    ge = lambda s: set(int(b) for b in s[s >= t].index)  # noqa: E731
    m_out = ge(q_in(flb)) & intr                                 # przedruchowe
    s_in1 = ge(q_out(sens1)) & intr
    extra0 = sorted(s_in1 & m_out)                               # = reguła „fl” kroku 2
    base = list(dict.fromkeys([int(b) for b in list(t2) + list(t1) + flb + extra0]))
    add = []
    if rule in ("pre", "pre2", "full2"):
        add += sorted(m_out)
    if rule in ("pre2", "full2"):
        srec = (ge(q_out(sens1)) | ge(q_out(sens2))) & intr
        add += sorted(srec)
    if rule == "full2":
        mid = ge(q_out(srec)) & ge(q_in(m_out)) & intr
        add += sorted(mid)
    if rule not in ("base", "pre", "pre2", "full2"):
        raise ValueError(rule)
    bodies = list(dict.fromkeys(base + add))
    return bodies, dict(a=a, g1=g1, g2=g2, flb=flb, n_base=len(base), sens1=sens1, sens2=sens2)


def build_rule(glu, J0, rule):
    """Zwraca (spec, idx, rep) w tym samym formacie co joint_net.build_net; dla rule='base' macierz W identyczna (sprawdzane)."""
    bodies, m = bodies_for(rule)
    a, g1, g2, flb = m["a"], m["g1"], m["g2"], m["flb"]
    edges, erep = load_edges(visual_path.WEIGHTS, bodies=bodies)
    nts = pd.read_feather(visual_path.NTS)
    tab = nts.set_index("body").reindex(bodies)[list(NT_COLS)]
    ov = {b: ("unknown", "brak NT; znak 0") for b, r in tab.iterrows() if not any(isinstance(x, str) and x != "unclear" for x in r)}
    signs = {**DEFAULT_SIGN, "glutamate": glu}
    signs.update({n: 0.0 for n in set(assign_nt(bodies, nts, ov).nt) - set(signs)})
    spec = build(edges, bodies, nts, ModelParams(J0=J0, sign_map=signs), nt_overrides=ov)
    pos = {b: i for i, b in enumerate(bodies)}
    ty = a.set_index("bodyId").type
    pool = lambda names: [pos[b] for b in flb if ty[b] in names]  # noqa: E731
    half = lambda v: ([pos[b] for b in v[: len(v) // 2]], [pos[b] for b in v[len(v) // 2:]])  # noqa: E731
    sens1all = [b for v in g1["sensory"].values() for b in v]
    idx = dict(padsT2=half(g2["sensory"]["mechanosensory bristle"]), padsT1=half(g1["sensory"]["mechanosensory bristle"]),
               feco={k: [pos[b] for b in sens1all if str(ty.get(b)) == tt] for k, tt in JN.FECO_T1.items()},
               pools={j: (pool(p), pool(n)) for j, (p, n) in JN.POOLS.items()})
    sens = set(m["sens1"]) | set(m["sens2"])
    layer = np.array(["S" if b in sens else "M" if b in set(flb) or str(a.set_index("bodyId").superclass.get(b)) == "vnc_motor" else "I"
                      for b in bodies])
    rep = dict(N=len(bodies), rule=rule, n_base=m["n_base"], edges=erep["loaded"], W_sha256=spec.report["W_sha256"],
               layers={k: int((layer == k).sum()) for k in "SIM"})
    return spec, idx, rep, layer
