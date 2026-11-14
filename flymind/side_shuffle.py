"""flymind/side_shuffle.py — kontrola SHUF_WITHIN_SIDE (V5 v3, przygotowanie). Bez mujoco, bez bio2, nic nie zapisuje.

Wersja 2 (po Red Team `results/redteam/v5v3_control_redteam.md`): grupa neuronu = WARSTWA × STRONA.
  strona   (DATA) kolumna `somaSide` adnotacji MaleCNS v1.0: 'L' / 'R'; inne (np. 'M', puste) → 'U' (zamiany tylko w 'U').
           Nie z nazwy ani `instance`. `rootSide` jest pusty dla tej sieci — nieużywany. Strona somy ≠ strona synaps.
  warstwa  (DATA + reguła selekcji) 'in' = typ LC10a (adnotacja), 'dn' = DNa02 (adnotacja), 'mid' = pośrednie wybrane regułą
           visual_path.select (≥ 5 synaps od LC10a i ≥ 5 do DNa02).
Wersja 1 (tylko strona) odrzucona: tworzyła 78–95 bezpośrednich krawędzi LC10a → DNa02 (w danych 0) i zmieniała
architekturę warstw (RT §3).

SHUF_WITHIN_SIDE (MODEL, kontrola): podwójne zamiany krawędzi danych (a→b, c→d) → (a→d, c→b), dozwolone WYŁĄCZNIE gdy
  w(a→b) == w(c→d) (waga ze znakiem), grupa(a) == grupa(c), grupa(b) == grupa(d), a ≠ d, c ≠ b, nowe krawędzie nie istnieją.
  Zachowane z konstrukcji: liczba neuronów, krawędzi, synaps, zbiór wag, Dale, stopnie i siły we/wy, multizbiory wag we/wy
  każdego neuronu, dla każdego neuronu skład grup partnerów (liczba i suma wag ze znakiem), macierz grupa×grupa. Ponieważ
  grupy 'dn' mają po 1 neuronie, wejścia DNa02 są niezmienione (zamiana dwóch krawędzi do tego samego neuronu nic nie
  zmienia). Zmienia się: który neuron w obrębie grupy jest partnerem — przy jednakowym prądzie enkodera na stronę
  dynamicznie istotne są głównie wzorce rekurencji wewnątrz bloków (LC10a↔LC10a, pośrednie↔pośrednie).
"""
import numpy as np
import pandas as pd

from connectome import ConnectomeError
from snn_interface import SNNSpec
from visual_path import ANN


def side_labels(bodies, ann_path=ANN):
    """Strona per neuron z metadanych: 'L' / 'R' / 'U'. Zwraca (tablica, raport z liczbami)."""
    a = pd.read_feather(ann_path, columns=["bodyId", "somaSide"]).set_index("bodyId").somaSide.reindex(bodies)
    s = np.where(a.isin(["L", "R"]), a.astype(object), "U").astype(str)
    return s, dict(source="somaSide (MaleCNS v1.0)", counts=pd.Series(s).value_counts().to_dict(),
                   raw_values=a.fillna("NA").value_counts().to_dict())


def layer_side_labels(spec, idx, ann_path=ANN):
    """Grupa warstwa_strona per neuron ('in_L', 'mid_R', 'dn_L', …). Warstwa z indeksów visual_path.network."""
    side, srep = side_labels(spec.bodies, ann_path)
    layer = np.empty(len(spec.bodies), object)
    for k, v in idx.items():
        layer[v] = "in" if k.startswith("in_") else "dn" if k.startswith("DNa02") else "mid"
    if any(x is None for x in layer):
        raise ConnectomeError("neuron bez warstwy")
    g = np.array([f"{a}_{b}" for a, b in zip(layer, side)])
    return g, dict(srep, groups=pd.Series(g).value_counts().sort_index().to_dict())


def shuffle_within_side(spec, groups, seed, n_swaps_per_edge=5):
    """Kopia SNNSpec z przetasowanymi krawędziami danych wg reguły z nagłówka. W_model musi być puste.
    Raport: zamiany wykonane / docelowe (complete = osiągnięto cel), krawędzie w kluczach z ≥ 2 członkami."""
    if spec.W_model.any():
        raise ConnectomeError("shuffle_within_side: sieć ma krawędzie modelowe")
    groups = np.asarray(groups)
    if len(groups) != len(spec.bodies):
        raise ConnectomeError("groups: długość ≠ liczba neuronów")
    post, pre = np.nonzero(spec.W_data)
    w = spec.W_data[post, pre].copy()
    E = len(w)
    keys = {}
    for k in range(E):
        keys.setdefault((float(w[k]), groups[pre[k]], groups[post[k]]), []).append(k)
    keys = [np.array(g) for g in keys.values() if len(g) > 1]
    if not keys:
        raise ConnectomeError("brak par krawędzi dopuszczalnych do zamiany")
    p = np.array([len(g) for g in keys], float)
    p /= p.sum()
    rng = np.random.default_rng(seed)
    exists = set(zip(pre.tolist(), post.tolist()))
    done = tried = 0
    target = n_swaps_per_edge * E
    while done < target and tried < 3 * target:
        tried += 1
        g = keys[rng.choice(len(keys), p=p)]
        i, j = rng.choice(g, 2, replace=False)
        a, b, c, d = pre[i], post[i], pre[j], post[j]
        if b == d or a == d or c == b or (a, d) in exists or (c, b) in exists:
            continue                                   # b == d: zamiana nic nie zmienia (nie liczymy jej jako wykonanej)
        exists -= {(a, b), (c, d)}
        exists |= {(a, d), (c, b)}
        post[i], post[j] = d, b
        done += 1
    Wd = np.zeros_like(spec.W_data)
    Wd[post, pre] = w
    rep = dict(spec.report, shuffle_within_side=dict(seed=seed, swaps=done, target=target, attempts=tried, complete=done == target,
                                                     edges=E, edges_in_swappable_keys=int(sum(len(g) for g in keys))))
    return SNNSpec(spec.bodies, spec.nt, spec.sign, Wd, spec.W_model.copy(), rep)


def group_block(W, groups):
    """Macierz blokowa [grupa_pre][grupa_post] → (liczba krawędzi, suma wag ze znakiem)."""
    post, pre = np.nonzero(W)
    out = {}
    for gp, go, x in zip(groups[pre], groups[post], W[post, pre]):
        n, s = out.get((gp, go), (0, 0.0))
        out[(gp, go)] = (n + 1, s + x)
    return {f"{k[0]}->{k[1]}": (v[0], round(v[1], 6)) for k, v in sorted(out.items())}


def properties(spec, sh, groups):
    """Deklarowane własności kontroli (True = zachowana) + liczby zmian. Sprawdzenia per neuron używają wag ZE ZNAKIEM
    rozdzielonych na dodatnie i ujemne, multizbiorów wag oraz wszystkich etykiet grup (nie stałej listy)."""
    W0, W1 = spec.W_data, sh.W_data
    A, B = W0 != 0, W1 != 0
    G = np.unique(groups)

    def comp(W, M, along_pre):
        """Per neuron i grupa: (liczba, suma dodatnich, suma ujemnych) partnerów z grupy."""
        out = []
        for g in G:
            m = groups == g
            sub, msk = (W[:, m], M[:, m]) if along_pre else (W[m, :].T, M[m, :].T)
            out.append(np.stack([msk.sum(1), np.clip(sub, 0, None).sum(1), np.clip(sub, None, 0).sum(1)]))
        return np.stack(out)

    def multisets(W, M, axis):
        """Per neuron: posortowane pary (grupa partnera, waga) — silniejsze niż sam multizbiór wag (RT runda 2, P2)."""
        if axis == 1:
            return [tuple(sorted(zip(groups[M[i]], W[i][M[i]]))) for i in range(W.shape[0])]
        return [tuple(sorted(zip(groups[M[:, j]], W[:, j][M[:, j]]))) for j in range(W.shape[1])]

    return dict(
        neurons=len(sh.bodies) == len(spec.bodies) and np.array_equal(sh.bodies, spec.bodies),
        edges=int(A.sum()) == int(B.sum()), synapses=bool(np.isclose(np.abs(W0).sum(), np.abs(W1).sum())),
        weight_multiset=bool(np.array_equal(np.sort(W0[A]), np.sort(W1[B]))),
        dale=bool(((W1 * spec.sign[None, :]) >= 0).all()), no_autapse=bool(not np.diag(W1).any()),
        in_degree=bool((A.sum(1) == B.sum(1)).all()), out_degree=bool((A.sum(0) == B.sum(0)).all()),
        in_strength=bool(np.allclose(W0.sum(1), W1.sum(1))), out_strength=bool(np.allclose(W0.sum(0), W1.sum(0))),
        in_group_weight_multisets=multisets(W0, A, 1) == multisets(W1, B, 1),
        out_group_weight_multisets=multisets(W0, A, 0) == multisets(W1, B, 0),
        pre_group_composition=bool(np.allclose(comp(W0, A, True), comp(W1, B, True))),
        post_group_composition=bool(np.allclose(comp(W0, A, False), comp(W1, B, False))),
        group_block=group_block(W0, groups) == group_block(W1, groups),
        model_edges_untouched=bool(np.array_equal(spec.W_model, sh.W_model)),
        nontrivial=bool((A & ~B).any()),
        changed_edges=int((A & ~B).sum()), changed_frac=round(float((A & ~B).sum() / A.sum()), 4),
        jaccard_edges=round(float((A & B).sum() / (A | B).sum()), 4))


KEYS = ("neurons", "edges", "synapses", "weight_multiset", "dale", "no_autapse", "in_degree", "out_degree", "in_strength",
        "out_strength", "in_group_weight_multisets", "out_group_weight_multisets", "pre_group_composition", "post_group_composition",
        "group_block", "model_edges_untouched", "nontrivial")
