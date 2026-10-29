"""Testy syntetyczne analizy pierścienia EPG (bez danych MaleCNS, bez bio2, SNN i mujoco; nic nie zapisują).
PRZYGOTOWANE, NIEURUCHOMIONE — wymagają osobnej zgody.  Uruchom:  .venv/bin/python -I -B flymind/test_epg_ring.py"""
import itertools
import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from connectome import ConnectomeError  # noqa: E402
from epg_ring import (_rng, angles, best_cycle, bump_metrics, bootstrap_stability, canonical, circulation, circulation_null,  # noqa: E402
                      concentration, cycle_score, glom_matrix, glomerulus_labels, label_permutation_null,
                      local_margin, neuron_matrix, sensitivity, symmetric, top2_ring)

SIZES = {"L1": 2, "L2": 3, "L3": 2, "L4": 4, "R1": 2, "R2": 3, "R3": 2, "R4": 2}
TRUE = ["L1", "R3", "L4", "R2", "L2", "R1", "L3", "R4"]      # prawdziwy cykl syntetyczny (celowo nie w kolejności nazw)


def raises(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except ConnectomeError:
        return True
    return False


def ring_data(seed=1001, noise=0.5):
    """Neurony z etykietami; sąsiedzi w TRUE: 10 synaps na parę neuronów (oba kierunki), wewnątrz glomerulusa 5,
    reszta: szum całkowity 0–noise·2. Zwraca (labels, edges)."""
    rng = np.random.default_rng(seed)
    rows, b = [], 1
    for g, m in SIZES.items():
        for _ in range(m):
            rows.append((b, g[0], int(g[1:]), g))
            b += 1
    labels = pd.DataFrame(rows, columns=["bodyId", "side", "num", "glomerulus"])
    pos = {g: k for k, g in enumerate(TRUE)}
    e = []
    for (bi, gi), (bj, gj) in itertools.product(zip(labels.bodyId, labels.glomerulus), repeat=2):
        if bi == bj:
            continue
        d = (pos[gj] - pos[gi]) % len(TRUE)
        w = 10 if d in (1, len(TRUE) - 1) else 5 if d == 0 else int(rng.integers(0, int(2 * noise) + 1))
        if w:
            e.append((bi, bj, w))
    return labels, pd.DataFrame(e, columns=["body_pre", "body_post", "weight"])


def main():
    labels, edges = ring_data()
    N = neuron_matrix(edges, labels)
    A, G = glom_matrix(N, labels, "pairs")
    S = symmetric(A)
    true_idx = [G.index(g) for g in TRUE]

    # cykl z danych = prawdziwy co do obrotu/odbicia; wynik niezależny od obrotu/odbicia zapisu
    cyc, score = best_cycle(S)
    assert canonical(cyc) == canonical(true_idx)
    rot, rev = true_idx[3:] + true_idx[:3], true_idx[::-1]
    assert canonical(rot) == canonical(rev) == canonical(true_idx) and canonical(true_idx[:2][::-1] + true_idx[2:]) != canonical(true_idx)
    assert math.isclose(cycle_score(S, true_idx), cycle_score(S, rot)) and math.isclose(cycle_score(S, true_idx), cycle_score(S, rev))
    assert math.isclose(score, cycle_score(S, cyc))

    # dokładność Held–Karp: zgodność z pełnym przeglądem dla n = 7 (360 cykli)
    R = np.random.default_rng(1002).random((7, 7))
    R = R + R.T
    np.fill_diagonal(R, 0)
    brute = max(cycle_score(R, (0,) + p) for p in itertools.permutations(range(1, 7)))
    assert math.isclose(best_cycle(R)[1], brute)

    # niezależność od etykiet: przenumerowanie glomerulusów → ten sam cykl po przeniesieniu
    pi = np.random.default_rng(1003).permutation(len(G))
    Sp = S[np.ix_(pi, pi)]
    assert canonical([pi[i] for i in best_cycle(Sp)[0]]) == canonical(cyc)

    # stabilność / wieloznaczność: czysty pierścień → margines > 0; macierz jednorodna → margines 0 (wiele cykli)
    assert local_margin(S, cyc)["margin"] > 0
    U = np.ones((6, 6)) - np.eye(6)
    assert local_margin(U, best_cycle(U)[0])["margin"] == 0
    n_mut, ring, order, tie = top2_ring(S)
    assert ring and canonical(order) == canonical(true_idx) and n_mut == len(G) and not tie
    assert top2_ring(U)[3]                                   # remis partnerów zgłoszony
    assert bootstrap_stability(N, labels, 20, 1004)[0] == 1.0

    # kierunek: pierścień skierowany → ±1, odwrócenie kolejności zmienia znak; symetryczny → 0
    D = np.zeros((5, 5))
    for k in range(5):
        D[k, (k + 1) % 5] = 1.0
    assert circulation(D, range(5)) == 1.0 and circulation(D, list(range(5))[::-1]) == -1.0
    assert circulation(D + D.T, range(5)) == 0.0
    a, b = circulation_null(D, range(5), 50, 1005), circulation_null(D, range(5), 50, 1005)
    assert np.array_equal(a, b) and raises(circulation_null, D, range(5), 5, 300) and raises(circulation_null, D, range(5), 5, 7)

    # kontrola permutacyjna: powtarzalna dla ziarna, słabsza od danych (n_mutual), zabronione ziarna odrzucone
    p1, p2 = label_permutation_null(N, labels, 30, 1006), label_permutation_null(N, labels, 30, 1006)
    assert p1.equals(p2) and p1.n_mutual.mean() < n_mut and raises(label_permutation_null, N, labels, 3, 350)

    # etykiety: dokładny typ (EPGt wykluczony i zgłoszony), brak sufiksu → błąd
    ann = pd.DataFrame(dict(bodyId=[1, 2, 3], type=["EPG", "EPG", "EPGt"], instance=["EPG(PB08)_L3", "EPG(PB08)_R10", "EPGt(PB09)_L9"]))
    lab, rep = glomerulus_labels(ann)
    assert lab.glomerulus.tolist() == ["L3", "R10"] and rep["excluded_similar_types"] == ["EPGt"]
    assert raises(glomerulus_labels, ann.assign(instance=["EPG(PB08)_L3", "EPG(PB08)", "x"]))

    # agregacja: "pairs" = suma / (m_pre · m_post)
    As, _ = glom_matrix(N, labels, "sum")
    m = labels.glomerulus.value_counts().reindex(G).to_numpy()
    assert np.allclose(A, As / np.outer(m, m)) and raises(glom_matrix, N, labels, "mean")

    # skupienie: niezdefiniowane przy zerze, błędy, C ∈ [0, 1], niezmienniczość
    th = 2 * np.pi * np.arange(8) / 8
    assert concentration(np.zeros(8), th)[0] is None and concentration(np.zeros(8), th)[2]
    assert raises(concentration, -np.ones(8), th) and raises(concentration, np.full(8, np.nan), th)
    one = np.eye(8)[2]
    assert math.isclose(concentration(one, th)[0], 1.0) and concentration(np.ones(8), th)[0] < 1e-12
    r = np.exp(2 * np.cos(th - 1.0))
    c0, ph0, _ = concentration(r, th)
    assert math.isclose(concentration(7 * r, th)[0], c0)                         # skala
    assert math.isclose(concentration(r, th + 2.3)[0], c0)                       # obrót
    c_ref, ph_ref, _ = concentration(r, -th)
    assert math.isclose(c_ref, c0) and math.isclose(ph_ref, -ph0)                # odbicie: C bez zmian, faza odbita

    # warianty kątów: A — jeden kąt na glomerulus; R — równe odstępy neuronów; nierówne liczebności →
    # równomierna aktywność daje C > 0 w A (obciążenie geometrii), ≈ 0 w R
    thA, thB, thR = (angles(labels, cyc, G, v) for v in "ABR")
    assert all(len(set(np.round(thA[labels.glomerulus == g], 12))) == 1 for g in G)
    assert len(set(np.round(thB, 12))) == len(labels) and len(set(np.round(thR, 12))) == len(labels)
    u = np.ones(len(labels))
    assert concentration(u, thA)[0] > 1e-3 and concentration(u, thR)[0] < 1e-12
    assert raises(angles, labels, cyc, G, "Z")
    tab = sensitivity(labels, cyc, G)
    assert list(tab.columns) == ["A", "B", "R"] and tab.loc["one_glomerulus", "A"] == 1.0
    # bump_metrics: jeden glomerulus aktywny → C = 1 w A, faza na bodźcu, permutacja kątów obniża C; cisza → None
    g0 = labels.glomerulus.to_numpy() == G[cyc[0]]
    bm = bump_metrics(g0.astype(float), thA, 0.0, n_perm=50, rng=_rng(1007))
    assert math.isclose(bm["C"], 1.0) and math.isclose(bm["dC"], 1.0 - concentration(u, thA)[0])
    assert bm["phase_err"] < 1e-9 and bm["C_perm"] < bm["C"]
    assert bump_metrics(np.zeros(len(labels)), thA, 0.0)["C"] is None and raises(bump_metrics, u, thA, 0.0, 5)
    print("OK: analiza pierścienia EPG (syntetyczna, 32 asercje)")


if __name__ == "__main__":
    main()
