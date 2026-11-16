"""Krok 5 — rozszerzenie sieci „pre” o dodatkowe neurony z danych, bez zmiany nets.py (podmiana listy neuronów w pamięci).
  extra_sensory("T1acc")  receptory nogi przedniej L wchodzące nerwami dodatkowymi: VProN (płytki włosków SNpp45),
                           DProN (płytki włosków SNpp52, szczecinki SNta33, inne), ProAN — razem 28 neuronów"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nets  # noqa: E402

ACC_NERVES = ("VProN", "DProN", "ProAN")
SENS = ("vnc_sensory", "vnc_sensory_tbc", "sensory_ascending", "sensory_ascending_tbc", "sensory_descending")


def extra_sensory(kind="T1acc"):
    a = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "type", "superclass", "subclass", "rootSide", "entryNerve"])
    s = a[a.superclass.isin(SENS) & (a.rootSide == "L") & a.entryNerve.isin(ACC_NERVES)]
    return {int(b): (str(n), str(sc), str(t)) for b, n, sc, t in zip(s.bodyId, s.entryNerve, s.subclass, s.type)}


def build_ext(glu, extra, J0=0.2):
    """Sieć „pre” + neurony `extra` (lista bodyId). Zwraca (spec, idx, rep, layer, pos)."""
    orig = nets.bodies_for

    def bf(rule, t=5):
        b, m = orig("pre", t)
        return list(dict.fromkeys(b + [int(x) for x in extra])), m
    nets.bodies_for = bf
    try:
        spec, idx, rep, layer = nets.build_rule(glu, J0, "pre")
        bodies, m = bf("pre")
    finally:
        nets.bodies_for = orig
    pos = {b: i for i, b in enumerate(bodies)}
    layer = np.array(layer, object)
    for b in extra:
        layer[pos[int(b)]] = "S"
    rep = dict(rep, rule="pre+extra", n_extra=len(extra), layers={k: int((layer == k).sum()) for k in "SIM"})
    return spec, idx, rep, layer, pos, m
