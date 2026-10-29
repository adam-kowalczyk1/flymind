"""flymind/epg_ring.py — struktura cykliczna EPG i wrażliwość miary skupienia (V3.1). Analiza offline: bez bio2,
bez SNN, bez mujoco, nic nie zapisuje; NIE jest częścią pętli sterowania SO-101.

Warstwy (osobno, żeby było widać, co jest danymi, a co założeniem):
  1. etykiety      glomerulus EPG = sufiks `_<L|R><n>` pola `instance` adnotacji (DANE; interpretacja sufiksu jako
                   glomerulusa PB to konwencja nazewnictwa — litera w 46/46 pokrywa się też z somaSide, więc z tego
                   pliku nie da się odróżnić strony glomerulusa od strony somy)
  2. macierz       A[g_pre, g_post] z krawędzi EPG→EPG (DANE → przekształcenie deterministyczne, wybór agregacji jawny)
  3. cykl          kolejność cykliczna maksymalizująca Σ S[c_k, c_k+1], S = A + Aᵀ bez przekątnej (Held–Karp, dokładnie)
                   — wyznaczona Z DANYCH, ale tylko z dokładnością do obrotu i odbicia (grupa dwuścienna, 2n postaci)
  4. kąty          ZAŁOŻENIA: równe odstępy glomerulusów, punkt zero i kierunek umowne; wariant A/B/R niżej
  5. skupienie     C = |Σ rᵢ e^{iθᵢ}| / Σ rᵢ — niezmiennicze względem obrotu i odbicia, ZALEŻNE od wariantu kątów

Kierunek krawędzi: cykl wyznaczany z S (symetrycznej); kierunek analizowany osobno (circulation): czy przepływ
wzdłuż cyklu w jedną stronę przeważa — tylko to mogłoby z danych wybrać orientację (nadal nie punkt zero).
Połączenia wewnątrz glomerulusa (przekątna A) nie mówią nic o sąsiedztwie → wyłączone z celu, raportowane osobno.
"""
import re

import numpy as np
import pandas as pd

from connectome import ConnectomeError, load_edges, provenance

LABEL_RE = re.compile(r"_([LR])(\d+)$")
FORBIDDEN_SEEDS = set(range(0, 40)) | set(range(300, 400))
MAX_HK = 18                            # Held–Karp: pamięć 2^n · n — powyżej odmowa zamiast przeciążenia maszyny


def _rng(seed):
    if seed in FORBIDDEN_SEEDS:
        raise ConnectomeError(f"ziarno {seed} zabronione (0–39, 300–399)")
    return np.random.default_rng(seed)


# ---------------------------------------------------------------- 1. etykiety

def glomerulus_labels(ann, type_="EPG"):
    """Ciała typu `type_` (dokładnie) z etykietą glomerulusa z sufiksu instance. Brak sufiksu → błąd (nie pomijane).
    Zwraca (DataFrame bodyId, side, num, glomerulus — posortowane po bodyId, raport)."""
    t = ann[ann["type"] == type_][["bodyId", "instance"]].copy()
    if t.empty or not t.bodyId.is_unique:
        raise ConnectomeError(f"typ {type_!r}: brak ciał albo powtórzone bodyId")
    m = t.instance.astype(str).str.extract(LABEL_RE)
    bad = t.bodyId[m[0].isna()].tolist()
    if bad:
        raise ConnectomeError(f"{len(bad)} ciał {type_} bez sufiksu _<L|R><n>: {bad[:10]}")
    t["side"], t["num"] = m[0].to_numpy(), m[1].astype(int).to_numpy()
    t["glomerulus"] = t.side + t.num.astype(str)
    t = t.sort_values("bodyId").reset_index(drop=True)
    types = ann["type"].dropna()
    near = sorted(set(types[types.str.contains(type_, regex=False)]) - {type_})
    return t[["bodyId", "side", "num", "glomerulus"]], dict(
        type_filter=f"type == {type_!r} (dokładnie)", excluded_similar_types=near, regex=LABEL_RE.pattern,
        neurons=len(t), per_glomerulus=t.glomerulus.value_counts().sort_index().to_dict(),
        caveat="interpretacja sufiksu jako glomerulusa PB to konwencja nazewnictwa (porównanie z somaSide w load())")


def glom_order(labels):
    """Stała, nieanatomiczna kolejność etykiet (L przed R, rosnąco numerem) — tylko do indeksowania macierzy."""
    return sorted(labels.glomerulus.unique(), key=lambda g: (g[0], int(g[1:])))


# ---------------------------------------------------------------- 2. macierz

def neuron_matrix(edges, labels):
    """N[pre, post] = synapsy między ciałami z `labels` (kolejność labels.bodyId). Krawędzie spoza zbioru pomijane."""
    ids = labels.bodyId.to_numpy()
    pos = {int(b): i for i, b in enumerate(ids)}
    e = edges[edges.body_pre.isin(pos) & edges.body_post.isin(pos)]
    N = np.zeros((len(ids), len(ids)))
    N[e.body_pre.map(pos).to_numpy(), e.body_post.map(pos).to_numpy()] = e.weight.to_numpy()
    return N


def glom_matrix(N, labels, normalize="pairs", w=None):
    """A[g_pre, g_post] z macierzy neuronów. normalize: "sum" (suma synaps) albo "pairs" (suma / liczba par
    neuronów pre×post — usuwa przewagę glomerulusów z 4 EPG nad tymi z 2). w: krotności neuronów (bootstrap).
    Zwraca (A skierowana, nazwy glomerulusów)."""
    G = glom_order(labels)
    P = (labels.glomerulus.to_numpy()[:, None] == np.array(G)[None, :]).astype(float)   # [neuron, glomerulus]
    w = np.ones(len(labels)) if w is None else np.asarray(w, float)
    A = P.T @ (w[:, None] * N * w[None, :]) @ P
    if normalize == "pairs":
        m = P.T @ w
        A = A / np.outer(m, m)
    elif normalize != "sum":
        raise ConnectomeError(f"normalize: 'sum' albo 'pairs', nie {normalize!r}")
    return A, G


def symmetric(A):
    """S = A + Aᵀ bez przekątnej — sąsiedztwo nieskierowane do wyznaczania cyklu."""
    S = A + A.T
    np.fill_diagonal(S, 0.0)
    return S


# ---------------------------------------------------------------- 3. cykl

def cycle_score(S, order):
    o = list(order)
    return float(sum(S[o[k], o[(k + 1) % len(o)]] for k in range(len(o))))


def canonical(order):
    """Postać kanoniczna cyklu względem obrotu i odbicia: start od najmniejszego, kierunek z mniejszym drugim."""
    o = list(order)
    k = o.index(min(o))
    o = o[k:] + o[:k]
    rev = [o[0]] + o[1:][::-1]
    return tuple(min(o, rev))


def best_cycle(S):
    """Dokładny cykl Hamiltona o maksymalnej wadze (Held–Karp, start w węźle 0 — obrót ustalony umownie).
    Remisy rozstrzyga argmax (pierwszy indeks) — patrz local_margin, czy są równorzędne alternatywy."""
    S = np.asarray(S, float)
    n = len(S)
    if n < 3 or n > MAX_HK or S.shape != (n, n) or not np.isfinite(S).all():
        raise ConnectomeError(f"best_cycle: macierz skończona [n, n], 3 ≤ n ≤ {MAX_HK}")
    full = 1 << n
    dp = np.full((full, n), -np.inf)
    par = np.full((full, n), -1, np.int16)
    dp[1, 0] = 0.0
    bits = 1 << np.arange(n)
    for mask in range(1, full, 2):                       # tylko maski zawierające węzeł 0
        row = dp[mask]
        if not np.isfinite(row).any():
            continue
        cand = row[:, None] + S                          # [skąd i, dokąd j]
        bi, bv = cand.argmax(0), cand.max(0)
        js = np.flatnonzero((mask & bits) == 0)
        nm = mask | bits[js]
        upd = bv[js] > dp[nm, js]
        dp[nm[upd], js[upd]] = bv[js][upd]
        par[nm[upd], js[upd]] = bi[js][upd]
    last = full - 1
    end = int(np.argmax(dp[last] + S[:, 0]))
    order, mask, j = [], last, end
    while j != -1:
        order.append(j)
        i = int(par[mask, j])
        mask ^= 1 << j
        j = i if mask else -1
    order = order[::-1]
    return order, float(dp[last, end] + S[end, 0])


def local_margin(S, order):
    """Najlepsza alternatywa w sąsiedztwie 2-opt (odwrócenie odcinka) i zamiany dwóch węzłów, różna od `order`
    co do obrotu/odbicia. margin = score(order) − score(alternatywy); ≈ 0 → kilka porównywalnych cykli."""
    o, base, best = list(order), cycle_score(S, order), (-np.inf, None)
    ref, n = canonical(o), len(o)
    for i in range(n):
        for j in range(i + 1, n):
            for alt in (o[:i] + o[i:j + 1][::-1] + o[j + 1:], o[:i] + [o[j]] + o[i + 1:j] + [o[i]] + o[j + 1:]):
                if canonical(alt) != ref:
                    s = cycle_score(S, alt)
                    if s > best[0]:
                        best = (s, alt)
    return dict(score=base, best_alternative=best[0], margin=base - best[0], alternative=best[1])


def top2_ring(S):
    """Szybka statystyka: krawędzie wzajemnych 2 najsilniejszych partnerów. Pierścień, jeśli każdy węzeł ma stopień
    2 i graf jest jednym cyklem długości n. Zwraca (n_mutual, is_ring, order|None, tie) — tie: 2. i 3. partner równi."""
    n = len(S)
    S = np.array(S, float)
    np.fill_diagonal(S, -np.inf)                          # węzeł nie jest własnym partnerem
    top = np.argsort(-S, axis=1, kind="stable")[:, :3]
    tie = bool(any(S[i, top[i, 1]] == S[i, top[i, 2]] for i in range(n))) if n > 3 else False
    t2 = [set(top[i, :2]) for i in range(n)]
    adj = {i: {j for j in t2[i] if i in t2[j]} for i in range(n)}
    n_mut = sum(len(v) for v in adj.values()) // 2
    if any(len(v) != 2 for v in adj.values()):
        return n_mut, False, None, tie
    order, prev, cur = [0], None, 0
    while True:
        nxt = next(j for j in sorted(adj[cur]) if j != prev)
        if nxt == 0:
            break
        order.append(nxt)
        prev, cur = cur, nxt
    return n_mut, len(order) == n, order if len(order) == n else None, tie


def circulation(A, order):
    """Kierunek: (Σ A[k→k+1] − Σ A[k+1→k]) / suma po krawędziach cyklu. ±1: cały przepływ w jedną stronę; ≈ 0:
    brak informacji o orientacji. Odwrócenie `order` zmienia znak."""
    o = list(order)
    fw = sum(A[o[k], o[(k + 1) % len(o)]] for k in range(len(o)))
    bw = sum(A[o[(k + 1) % len(o)], o[k]] for k in range(len(o)))
    return float((fw - bw) / (fw + bw)) if fw + bw else float("nan")


def circulation_null(A, order, n, seed):
    """Kontrola kierunku: losowa zamiana kierunku każdej pary sąsiadów cyklu (asymetria bez spójnej orientacji).
    Zwraca rozkład statystyki circulation pod H0."""
    rng, o = _rng(seed), list(order)
    pairs = [(A[o[k], o[(k + 1) % len(o)]], A[o[(k + 1) % len(o)], o[k]]) for k in range(len(o))]
    f, b = np.array(pairs).T
    out = np.empty(n)
    for t in range(n):
        s = rng.random(len(f)) < 0.5
        fw, bw = np.where(s, b, f).sum(), np.where(s, f, b).sum()
        out[t] = (fw - bw) / (fw + bw) if fw + bw else np.nan
    return out


def label_permutation_null(N, labels, n, seed, normalize="pairs", exact_every=0):
    """Kontrola permutacyjna zachowująca CAŁY graf neuronów i liczebności glomerulusów: losowa permutacja etykiet
    glomerulusów między neuronami EPG. Testuje związek etykiet z połączeniami. Statystyki: n_mutual (top2_ring)
    zawsze; dokładny cykl (frakcja wagi S na cyklu) co `exact_every` permutacji (0 = nigdy; Held–Karp ~ sekundy)."""
    rng = _rng(seed)
    out = []
    for t in range(n):
        lab = labels.assign(glomerulus=rng.permutation(labels.glomerulus.to_numpy()))
        S = symmetric(glom_matrix(N, lab, normalize)[0])
        rec = dict(n_mutual=top2_ring(S)[0])
        if exact_every and t % exact_every == 0:
            rec["cycle_frac"] = best_cycle(S)[1] / (S.sum() / 2)
        out.append(rec)
    return pd.DataFrame(out)


def bootstrap_stability(N, labels, n, seed, normalize="pairs"):
    """Stabilność: losowanie neuronów ze zwracaniem w obrębie glomerulusów (liczebności zachowane) → dokładny cykl.
    Zwraca (odsetek prób z cyklem identycznym co do obrotu/odbicia z punktowym, liczność postaci kanonicznych)."""
    rng = _rng(seed)
    ref = canonical(best_cycle(symmetric(glom_matrix(N, labels, normalize)[0]))[0])
    groups = [np.flatnonzero(labels.glomerulus.to_numpy() == g) for g in glom_order(labels)]
    found = []
    for _ in range(n):
        w = np.zeros(len(labels))
        for idx in groups:
            np.add.at(w, rng.choice(idx, len(idx), replace=True), 1.0)
        found.append(canonical(best_cycle(symmetric(glom_matrix(N, labels, normalize, w=w)[0]))[0]))
    return float(np.mean([f == ref for f in found])), pd.Series(found).value_counts().to_dict()


# ---------------------------------------------------------------- 4. kąty (ZAŁOŻENIA)

VARIANTS = {
    "A": "wszystkie EPG glomerulusa k mają kąt 2πk/n (równe odstępy glomerulusów)",
    "B": "EPG glomerulusa k równo w jego klinie [2π(k−½)/n, 2π(k+½)/n) wg rosnącego bodyId (bodyId nie jest anatomią)",
    "R": "wszystkie EPG równo co 2π/N wg rangi (pozycja glomerulusa, bodyId) — reguła opisana w bio2/brain.py "
         "(„idealna geometria”), odtworzona z opisu, nie importowana",
}


def angles(labels, cycle, G, variant):
    """θ [rad] per neuron (kolejność labels). cycle: indeksy G w kolejności cyklu. Punkt zero = cycle[0], kierunek
    = kolejność `cycle` — oba umowne (dane nie wyznaczają ani obrotu, ani odbicia)."""
    pos = {G[c]: k for k, c in enumerate(cycle)}
    n, k = len(cycle), labels.glomerulus.map(pos).to_numpy()
    if np.isnan(k.astype(float)).any():
        raise ConnectomeError("glomerulus spoza cyklu")
    if variant == "A":
        return 2 * np.pi * k / n
    order = np.lexsort((labels.bodyId.to_numpy(), k))                 # po pozycji, potem bodyId
    if variant == "R":
        th = np.empty(len(labels))
        th[order] = 2 * np.pi * np.arange(len(labels)) / len(labels)
        return th
    if variant == "B":
        th = np.empty(len(labels))
        for g in range(n):
            ids = [i for i in order if k[i] == g]
            th[ids] = 2 * np.pi * (g + (np.arange(len(ids)) + 0.5) / len(ids) - 0.5) / n
        return th
    raise ConnectomeError(f"wariant {variant!r}: dostępne {sorted(VARIANTS)}")


# ---------------------------------------------------------------- 5. skupienie

def concentration(r, theta):
    """C = |Σ rᵢ e^{iθᵢ}| / Σ rᵢ i faza. r: aktywność ≥ 0 (dowolna skala — C jej nie zależy; nieaktywne rᵢ = 0
    nie wnoszą nic do licznika ani mianownika). Σ r = 0 → (None, None, powód) — C niezdefiniowane, nie 0.
    Ujemne lub nieskończone r → błąd. Faza ma sens tylko w umownym układzie `angles` (obrót/odbicie dowolne)."""
    r, theta = np.asarray(r, float), np.asarray(theta, float)
    if r.shape != theta.shape or not (np.isfinite(r).all() and np.isfinite(theta).all()):
        raise ConnectomeError("r i θ: ten sam kształt, wartości skończone")
    if (r < 0).any():
        raise ConnectomeError("r < 0 — skupienie zdefiniowane dla aktywności nieujemnej")
    tot = r.sum()
    if tot == 0:
        return None, None, "Σr = 0 (brak aktywności) — C niezdefiniowane"
    z = (r * np.exp(1j * theta)).sum()
    return float(abs(z) / tot), float(np.angle(z)), None


def bump_metrics(r, theta, stim_angle, n_perm=0, rng=None):
    """Skupienie aktywności r przy kątach θ względem bodźca w kierunku stim_angle (ten sam umowny układ):
    C, dC = C − C_uniform (C dla aktywności równomiernej przy tej samej geometrii — obciążenie geometrii),
    phase_err = |faza − stim_angle| [rad], C_perm = mediana C po losowych permutacjach θ między neuronami
    (ta sama aktywność, zniszczony związek z pierścieniem). Σr = 0 → wartości None z powodem."""
    c_u = concentration(np.ones(len(theta)), theta)[0]
    C, ph, why = concentration(r, theta)
    if C is None:
        return dict(C=None, dC=None, phase_err=None, C_perm=None, C_uniform=c_u, reason=why)
    perm = None
    if n_perm:
        if rng is None:
            raise ConnectomeError("n_perm > 0 wymaga rng (ziarno ≥ 1001)")
        perm = float(np.median([concentration(r, rng.permutation(theta))[0] for _ in range(n_perm)]))
    return dict(C=C, dC=C - c_u, phase_err=float(abs(np.angle(np.exp(1j * (ph - stim_angle))))), C_perm=perm,
                C_uniform=c_u, reason=None)


def sensitivity(labels, cycle, G, variants=("A", "B", "R"), kappas=(0.5, 2.0, 8.0)):
    """C dla wzorców syntetycznych na pierścieniu glomerulusów, w każdym wariancie kątów. Wzorce: równomierny
    (C ≠ 0 tu = obciążenie geometrii, np. z nierównych liczebności), jeden glomerulus, von Mises o κ.
    Aktywność przypisana per glomerulus (wszystkie jego EPG równo) — więc różnice między wariantami pochodzą
    wyłącznie z geometrii, nie z aktywności."""
    n = len(cycle)
    pos = labels.glomerulus.map({G[c]: k for k, c in enumerate(cycle)}).to_numpy()
    phi = 2 * np.pi * pos / n
    pats = {"uniform": np.ones(len(labels)), "one_glomerulus": (pos == 0).astype(float)}
    pats.update({f"vonmises_k{k}": np.exp(k * np.cos(phi)) for k in kappas})
    rows = []
    for v in variants:
        th = angles(labels, cycle, G, v)
        for name, r in pats.items():
            rows.append(dict(variant=v, pattern=name, C=concentration(r, th)[0]))
    return pd.DataFrame(rows).pivot(index="pattern", columns="variant", values="C")


# ---------------------------------------------------------------- dane i raport pochodzenia

def load(ann_path, weights_path, type_="EPG"):
    """Etykiety z adnotacji, krawędzie EPG→EPG z wag (connectome.load_edges, podgraf indukowany)."""
    ann = pd.read_feather(ann_path, columns=["bodyId", "type", "instance", "somaSide"])
    labels, lrep = glomerulus_labels(ann, type_)
    soma = ann.set_index("bodyId").somaSide.reindex(labels.bodyId).to_numpy()
    lrep["side_equals_somaSide"] = f"{int((labels.side.to_numpy() == soma).sum())}/{len(labels)}"
    edges, erep = load_edges(weights_path, bodies=labels.bodyId.tolist())
    return labels, edges, dict(annotations=provenance(ann_path), weights=provenance(weights_path), labels=lrep,
                               edges=erep)


def analyze(labels, edges, normalize="pairs"):
    """Analiza punktowa (bez losowania): macierz, cykl dokładny, margines, top-2, kierunek, wrażliwość C."""
    N = neuron_matrix(edges, labels)
    A, G = glom_matrix(N, labels, normalize)
    S = symmetric(A)
    cyc, score = best_cycle(S)
    n_mut, is_ring, ring, tie = top2_ring(S)
    return dict(
        glomeruli=G, normalize=normalize, diagonal_total=float(np.trace(A)), offdiag_total=float(S.sum() / 2),
        cycle=[G[i] for i in cyc], cycle_canonical=[G[i] for i in canonical(cyc)], cycle_score=score,
        cycle_frac=score / (S.sum() / 2), local=local_margin(S, cyc),
        top2=dict(n_mutual=n_mut, is_ring=is_ring, same_as_cycle=bool(ring) and canonical(ring) == canonical(cyc),
                  tie=tie),
        circulation=circulation(A, cyc), sensitivity=sensitivity(labels, cyc, G),
        assumptions=["cykl tylko z dokładnością do obrotu i odbicia", "równe odstępy glomerulusów (A, B, R)",
                     "kąty wewnątrz glomerulusa (B, R) — reguła modelowa", "punkt zero i kierunek umowne",
                     "sufiks instance = glomerulus PB (konwencja; litera = somaSide)",
                     "brak danych o położeniu w EB — C nie dowodzi lokalizacji anatomicznej"])
