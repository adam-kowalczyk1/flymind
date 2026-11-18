"""Bramka r2 (opcja 1, po porażce r1): typy-specyficzna dynamika z literatury, reszta jak eye_gate.py.
Klasy (Borst, Haag, Mauss 2020, J Comp Physiol A, PMC7069908): dolnoprzepustowe Mi4, Mi9, Tm9; pasmowe Mi1, Tm3, Tm1, Tm2, Tm4.
Liczby (Borst 2018, PLoS Comput Biol, PMC6016951, model oparty na pomiarach Arenz 2017): dolnoprzepustowy τ = 50 ms;
wejście pasmowe = górnoprzepustowy τ = 250 ms + 10 % składowej stałej. Szybka błona typów pasmowych τ_m = 10 ms
(Borst nie filtruje ich dolnoprzepustowo; 10 ms = wybór, ustalony przed uruchomieniem). Pozostałe typy: τ = 50 ms jak r1.
Wyjście typu pasmowego: f(V_rest + HP(V − V_rest) + 0,1·(V − V_rest))."""
import numpy as np

import eye_gate as G

LOWPASS = {"Mi4": 50.0, "Mi9": 50.0, "Tm9": 50.0}
BANDPASS = ("Mi1", "Tm3", "Tm1", "Tm2", "Tm4")
TAU_FAST, TAU_HP, DC = 10.0, 250.0, 0.1


def simulate(W, S, kind, units, speed=None, record=None):
    inp, T, lum, combos = G.stimulus(S, kind, speed)
    N, B, U = W.shape[0], len(combos), len(units)
    tau = np.array([LOWPASS.get(t, TAU_FAST if t in BANDPASS else G.TAU) for t in S["type"]])[:, None]
    bp = np.isin(S["type"], BANDPASS)
    rngs = [np.random.default_rng([u, 0]) for u in units]
    V = np.full((N, B * U), G.VREST)
    a_hp = np.zeros((int(bp.sum()), B * U))                 # wolna składowa odchylenia (do filtru górnoprzepustowego)
    a = np.tile(np.log(lum(0)), (1, U)); y1 = np.zeros_like(a); y2 = np.zeros_like(a)
    rest = np.zeros((N, B * U)); resp = np.zeros((N, B * U)); peak = np.full((N, B * U), -np.inf)
    for t in range(T):
        lg = np.tile(np.log(lum(t)), (1, U))
        a += G.DT / 1000.0 * (lg - a)
        y1 += G.DT / 12.0 * ((lg - a) - y1); y2 += G.DT / 12.0 * (y1 - y2)
        I = np.zeros((N, B * U)); I[inp] = -G.K_IN * y2
        d = V[bp] - G.VREST
        a_hp += G.DT / TAU_HP * (d - a_hp)
        Y = V.copy(); Y[bp] = G.VREST + (d - a_hp) + DC * d
        F = np.maximum(Y, 0.0)
        noise = np.hstack([r.standard_normal((N, B)) for r in rngs])
        V += G.DT / tau * (G.VREST - V + W @ F + I) + G.SIGMA * np.sqrt(G.DT / tau) * noise
        if not np.isfinite(V).all() or np.abs(V).max() > 1e3:
            raise FloatingPointError(f"sieć niestabilna w t={t}")
        if G.PRE_MS - 200 <= t < G.PRE_MS:
            rest += F
        elif t >= G.PRE_MS:
            if t == G.PRE_MS:
                rest /= 200
            resp += F
            np.maximum(peak, F - rest, out=peak)
    resp = resp / (T - G.PRE_MS) - rest
    out = resp if kind == "S0" else peak
    return out.reshape(N, U, B).transpose(0, 2, 1), rest.reshape(N, U, B).transpose(0, 2, 1), combos


def install():
    G.simulate = simulate
