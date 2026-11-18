"""Etap 0 (bramka) z DESIGN.md: wycinek S-core, model stopniowany M-G, wejście E2 (−u fotoreceptora do L1/L2/L3), F-IDEAL.
Bodźce: S0 (błysk pełnego pola ON/OFF, kontrast 50 %) i S1 (krawędź ON/OFF, 6 kierunków siatki, 60/120/240 °/s).
Ustalone PRZED pierwszym uruchomieniem (projekt nie podaje): g = 1, połowione aż sieć stabilna (reguła `pick_g`);
k = 1; σ szumu = 0,05; 10 jednostek danych, 4 jednostki na tasowanie; R: S0 = średnie f(V) w oknie − spoczynek; S1 = szczyt f(V) − spoczynek (zmiana po teście e, przed danymi)."""
import json
import os
import sys
import zlib

import numpy as np
import scipy.sparse as sp
from scipy.special import ndtr

import optic_slice as OS

SIGN = {"acetylcholine": 1.0, "gaba": -1.0, "glutamate": -1.0, "histamine": -1.0}
TAU, DT, VREST, K_IN, SIGMA = 50.0, 1.0, 1.0, 1.0, 0.05
DEG_COL, FWHM = 5.1, 5.0
SPEEDS, DIRS = (60.0, 120.0, 240.0), np.arange(6) * 60.0
PRE_MS, POST_MS, EDGE_START = 300, 300, 50.0           # krawędź startuje 50° od środka (krążek ma ~41°)
POOLS = {"data": range(15502001, 15502041), "shuffle": list(range(15503001, 15503051)) + list(range(15511001, 15511200)), "smoke": range(15501001, 15501100)}


def weights(S, n, glu=-1.0, g=1.0):
    sign = np.array([0.0 if t is None else (glu if t == "glutamate" else SIGN.get(t, 0.0)) for t in S["nt"]])
    tot = np.bincount(S["post"], weights=n, minlength=len(S["bodies"]))
    w = sign[S["pre"]] * g * n / tot[S["post"]]
    return sp.csr_matrix((w, (S["post"], S["pre"])), shape=(len(S["bodies"]),) * 2)


def shuffle_typed(S, seed, swaps_per_edge=5):
    """C1: zamiany końców krawędzi tylko w bloku (typ pre, typ post); zachowane stopnie i skład typów; bez duplikatów i pętli."""
    rng = np.random.default_rng(seed)
    pre, post, n = S["pre"].copy(), S["post"].copy(), S["n"].copy()
    ty = S["type"]
    blocks = {}
    for k, (a, b) in enumerate(zip(ty[pre], ty[post])):
        blocks.setdefault((a, b), []).append(k)
    exists = set(zip(pre.tolist(), post.tolist()))
    done = 0
    for ks in blocks.values():
        if len(ks) < 2:
            continue
        ks = np.array(ks)
        for _ in range(swaps_per_edge * len(ks)):
            i, j = rng.choice(ks, 2, replace=False)
            a, b, c, d = pre[i], post[i], pre[j], post[j]
            if a == d or c == b or (a, d) in exists or (c, b) in exists:
                continue
            exists -= {(a, b), (c, d)}
            exists |= {(a, d), (c, b)}
            post[i], post[j] = d, b
            done += 1
    T = dict(S, pre=pre, post=post, n=n)
    return T, done


def col_xy(S):
    return OS.xy(S["hexq"], S["hexr"]) * DEG_COL


def stimulus(S, kind, speed=None, dirs=DIRS, pols=(1, -1)):
    """Zwraca (T_ms, fun(t) → luminancja [kolumny × B]) dla B = len(dirs)·len(pols). Kolumny = komórki wejściowe L1/L2/L3."""
    inp = np.where(np.isin(S["type"], ["L1", "L2", "L3"]) & ~np.isnan(S["hexq"]))[0]
    P = col_xy(S)[inp]
    sig = FWHM / 2.355
    combos = [(d, p) for d in dirs for p in pols]
    if kind == "S0":
        T = PRE_MS + 600

        def lum(t):
            return np.tile([1.0 + 0.5 * p if t >= PRE_MS else 1.0 for _, p in combos], (len(inp), 1))
        return inp, T, lum, combos
    proj = np.stack([P @ [np.cos(np.radians(d)), np.sin(np.radians(d))] for d, _ in combos], 1)
    pol = np.array([p for _, p in combos])
    T = PRE_MS + int(2 * EDGE_START / speed * 1000) + POST_MS

    def lum(t):
        s = -EDGE_START + speed * max(t - PRE_MS, 0) / 1000.0
        behind = ndtr((s - proj) / sig)                     # 1 = krawędź już przeszła
        return 1.0 + 0.5 * pol * (2 * behind - 1)            # ON: ciemno 0,5 → jasno 1,5; OFF odwrotnie
    return inp, T, lum, combos


def simulate(W, S, kind, units, speed=None, record=None):
    """Zwraca średnie f(V) [N × B × U] w oknie bodźca i w spoczynku (ostatnie 200 ms przed bodźcem)."""
    inp, T, lum, combos = stimulus(S, kind, speed)
    N, B, U = W.shape[0], len(combos), len(units)
    rngs = [np.random.default_rng([u, 0]) for u in units]
    V = np.full((N, B * U), VREST)
    L0 = lum(0)
    a = np.tile(np.log(L0), (1, U))                        # adaptacja (τ 1 s) startuje w stanie ustalonym
    y1 = np.zeros_like(a); y2 = np.zeros_like(a)           # filtr 2. rzędu, czas do szczytu 12 ms
    rest = np.zeros((N, B * U)); resp = np.zeros((N, B * U)); peak = np.full((N, B * U), -np.inf)
    for t in range(T):
        lg = np.tile(np.log(lum(t)), (1, U))
        a += DT / 1000.0 * (lg - a)
        y1 += DT / 12.0 * ((lg - a) - y1); y2 += DT / 12.0 * (y1 - y2)
        I = np.zeros((N, B * U)); I[inp] = -K_IN * y2
        F = np.maximum(V, 0.0)
        noise = np.hstack([r.standard_normal((N, B)) for r in rngs])
        V += DT / TAU * (VREST - V + W @ F + I) + SIGMA * np.sqrt(DT / TAU) * noise
        if not np.isfinite(V).all() or np.abs(V).max() > 1e3:
            raise FloatingPointError(f"sieć niestabilna w t={t}")
        if PRE_MS - 200 <= t < PRE_MS:
            rest += F
        elif t >= PRE_MS:
            if t == PRE_MS:
                rest /= 200
            resp += F
            np.maximum(peak, F - rest, out=peak)
    resp = resp / (T - PRE_MS) - rest
    # S0 (pełne pole): średnia zmiana; S1 (krawędź): szczyt ponad spoczynek — średnia z okna zależy od położenia komórki (test e)
    out = resp if kind == "S0" else peak
    return out.reshape(N, U, B).transpose(0, 2, 1), rest.reshape(N, U, B).transpose(0, 2, 1), combos


def pick_g(S, units):
    """Reguła (ustalona przed uruchomieniem): g = 1, połowić aż S0 przebiegnie bez niestabilności i max f(V) w spoczynku < 20."""
    g = 1.0
    while g > 1e-3:
        W = weights(S, S["n"], g=g)
        try:
            R, rest, _ = simulate(W, S, "S0", units)
            if rest.max() < 20:
                return g, W
        except FloatingPointError:
            pass
        g /= 2
    raise RuntimeError("brak stabilnego g")


def run_network(S, W, units):
    out = {"S0": simulate(W, S, "S0", units)[0]}
    for v in SPEEDS:
        out[v] = simulate(W, S, "S1", units, speed=v)[0]
    return out


def check_pool(units, pool):
    assert all(u in POOLS[pool] for u in units), f"ziarna spoza puli {pool}"


if __name__ == "__main__":
    # tryb: smoke | data GLU OUT | shuffle FIRST LAST OUT
    mode = sys.argv[1]
    S = OS.build()
    if mode == "smoke":
        import time
        units = [15501001, 15501002]
        t0 = time.time(); g, W = pick_g(S, units); print("g", g, "czas S0", round(time.time() - t0, 1))
        t0 = time.time(); R, _, c = simulate(W, S, "S1", units, speed=240.0); print("S1 240 °/s:", round(time.time() - t0, 1), "s", R.shape)
        sys.exit()
    raise SystemExit("tryby data/shuffle: eye_gate_run.py")
