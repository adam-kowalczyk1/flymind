"""flymind/visual_path.py — droga wzrokowa LC10a → pośrednie → DNa02 z danych MaleCNS v1.0 (V4/V5). Bez bio2, bez mujoco.

Wybór populacji (decyzje zapisane PRZED symulacjami dynamiki i zachowania, 2026-10-28; ekran danych w VALIDATION_PLAN V4):
  wejście    typ dokładnie 'LC10a' (275 neuronów, strona = somaSide). Uzasadnienie: (a) literatura — LC10a to detektory
             małych ruchomych obiektów, ich aktywacja jednostronna wywołuje skręt ipsilateralny (Ribeiro i in. 2018);
             (b) ekran 8 typów wzrokowych w danych: znakowany wpływ 2-skokowy LC10a → DNa02 jest push-pull (ipsi +, kontra −)
             i symetryczny. Wybór LC10a nastąpił PO tym ekranie — to wybór eksploracyjny, nie test hipotezy.
  pośrednie  neurony z ≥ s_min synapsami od całej populacji LC10a ORAZ ≥ s_min synapsami do DNa02 (L+R); s_min = 5.
  wyjście    DNa02 L (523769), DNa02 R (10360) — instance/somaSide z adnotacji.
  krawędzie  podgraf indukowany (wszystkie krawędzie z danych między wybranymi neuronami), bez krawędzi modelowych.
Czego brak (jawnie): ~88 % wejścia DNa02 pochodzi spoza podgrafu (nie modelowane — tło = szum ALIF); przedziały EB/PB/LAL
nie są rozróżnione (wagi zsumowane po regionach); LC10a dostają prąd z enkodera, nie z rdzenia wzrokowego.

Kontrole:
  shuffle(spec, seed)   podwójne zamiany krawędzi (a→b, c→d) → (a→d, c→b): zachowane stopnie wejścia/wyjścia, siła
                        wyjściowa i znak każdego neuronu presynaptycznego; niszczy KTO z KIM.
  zamiana stron wejścia i ablacje robi pętla (indeksy wejścia), nie sieć.
"""
import os

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

from connectome import ConnectomeError, load_edges
from snn_interface import ModelParams, SNNSpec, build

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "malecns")
ANN = os.path.join(DATA, "body-annotations-male-cns-v1.0-minconf-0.5.feather")
NTS = os.path.join(DATA, "body-neurotransmitters-male-cns-v1.0.feather")
WEIGHTS = os.path.join(DATA, "connectome-weights-male-cns-v1.0-minconf-0.5.feather")
INPUT_TYPE, S_MIN = "LC10a", 5
DNA02 = {"L": 523769, "R": 10360}


def select(s_min=S_MIN, input_type=INPUT_TYPE):
    """Zwraca (bodies, groups, raport). groups: in_L, in_R, mid, DNa02_L, DNa02_R (bodyId)."""
    ann = pd.read_feather(ANN, columns=["bodyId", "type", "instance", "somaSide"])
    inp = ann[ann.type == input_type]
    if inp.empty or not inp.somaSide.isin(["L", "R"]).all():
        raise ConnectomeError(f"{input_type}: brak neuronów albo strona spoza L/R")
    dn = ann.set_index("bodyId").reindex(list(DNA02.values()))
    if not (dn.type == "DNa02").all() or list(dn.somaSide) != list(DNA02):
        raise ConnectomeError(f"DNa02: adnotacje niezgodne z {DNA02}")
    lc = inp.bodyId.astype(int).tolist()
    W = ds.dataset(WEIGHTS, format="ipc")
    out = W.to_table(filter=ds.field("body_pre").isin(lc)).to_pandas().groupby("body_post").weight.sum()
    inn = W.to_table(filter=ds.field("body_post").isin(list(DNA02.values()))).to_pandas().groupby("body_pre").weight.sum()
    mid = sorted(set(out[out >= s_min].index) & set(inn[inn >= s_min].index) - set(lc) - set(DNA02.values()))
    groups = dict(in_L=sorted(inp.bodyId[inp.somaSide == "L"].astype(int)), in_R=sorted(inp.bodyId[inp.somaSide == "R"].astype(int)),
                  mid=[int(b) for b in mid], DNa02_L=[DNA02["L"]], DNa02_R=[DNA02["R"]])
    bodies = groups["in_L"] + groups["in_R"] + groups["mid"] + groups["DNa02_L"] + groups["DNa02_R"]
    rep = dict(input_type=input_type, s_min=s_min, sizes={k: len(v) for k, v in groups.items()},
               dna02_input_total=int(inn.sum()), dna02_input_from_mid=int(inn.reindex(mid).sum()),
               mid_types=ann.set_index("bodyId").reindex(mid).type.value_counts().to_dict())
    return bodies, groups, rep


def network(J0, s_min=S_MIN, transform="linear"):
    """SNNSpec tylko z danych + indeksy grup w macierzy. Brak przekaźnika → błąd (assign_nt), nie domysł."""
    bodies, groups, rep = select(s_min)
    edges, erep = load_edges(WEIGHTS, bodies=bodies)
    spec = build(edges, bodies, pd.read_feather(NTS), ModelParams(J0=J0, transform=transform))
    pos = {b: i for i, b in enumerate(bodies)}
    idx = {k: np.array([pos[b] for b in v]) for k, v in groups.items()}
    rep.update(edges=erep["loaded"], build=spec.report)
    return spec, idx, rep


def shuffle(spec, seed, n_swaps_per_edge=10, equal_weight=False):
    """Kopia SNNSpec z przetasowanymi krawędziami danych (podwójne zamiany). W_model musi być puste.
    equal_weight=True: zamiany tylko między krawędziami o identycznej wadze ze znakiem → zachowana także siła WEJŚCIOWA
    każdego neuronu (kontrola ostrzejsza; dodana po Red Team V4/V5)."""
    if spec.W_model.any():
        raise ConnectomeError("shuffle: sieć ma krawędzie modelowe — tasowanie dotyczy tylko danych")
    post, pre = np.nonzero(spec.W_data)
    w = spec.W_data[post, pre].copy()
    E = len(w)
    rng = np.random.default_rng(seed)
    exists = set(zip(pre.tolist(), post.tolist()))
    done = 0
    groups = {}
    for k, x in enumerate(w):
        groups.setdefault(float(x) if equal_weight else 0.0, []).append(k)
    groups = [np.array(g) for g in groups.values() if len(g) > 1]
    p = np.array([len(g) for g in groups], float)
    for _ in range(n_swaps_per_edge * E * 3):
        if done >= n_swaps_per_edge * E:
            break
        i, j = rng.choice(groups[rng.choice(len(groups), p=p / p.sum())], 2) if equal_weight else rng.integers(E, size=2)
        a, b, c, d = pre[i], post[i], pre[j], post[j]
        if i == j or a == d or c == b or (a, d) in exists or (c, b) in exists:
            continue
        exists -= {(a, b), (c, d)}
        exists |= {(a, d), (c, b)}
        post[i], post[j] = d, b
        done += 1
    Wd = np.zeros_like(spec.W_data)
    Wd[post, pre] = w
    rep = dict(spec.report, shuffle=dict(seed=seed, swaps=done, edges=E, equal_weight=equal_weight))
    return SNNSpec(spec.bodies, spec.nt, spec.sign, Wd, spec.W_model.copy(), rep)
