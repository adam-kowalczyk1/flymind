"""flymind/alif_dt.py — ALIF z jawnym czasem dyskretnym (Etap 0). Te same równania co alif.ALIF; alif.py nietknięty (przypięty sha256).

Zmienia wyłącznie obsługę czasu dyskretnego (protokół: program_stage0/STAGE0_PROTOCOL.md):
  refrakcja   całkowity licznik kroków n_ref zamiast `ref -= dt` (float: przy dt = 0,2 stary kod blokuje 12 kroków zamiast 11)
  opóźnienie  całkowity n_delay; spike z indeksu k podnosi g celu na początku kroku k + n_delay
  zaokrąglenie timing="exact": t/dt musi być całkowite, inaczej odmowa; timing="legacy": ceil (refrakcja) i round (opóźnienie)
              jak alif.py — tylko do odtworzenia starego modelu przy dt = 1
  szum        ALIFParams.noise = σ na krok przy dt_ref = 1 ms; σ_krok = σ·√(dt_ref/dt) → wariancja v niezależna od dt.
              noise_ref_dt=None przywraca stare znaczenie (σ na krok przy każdym dt).
Przy dt = 1, timing="legacy" wynik jest bit w bit równy alif.ALIF (test_stage0_dt.py, T1b).
"""
import math

import numpy as np

from alif import ALIF
from connectome import ConnectomeError

TOL = 1e-9


def to_steps(t_ms, dt, rule):
    """Czas fizyczny [ms] → liczba kroków. rule: 'exact' (odmowa, gdy t/dt nie jest całkowite), 'ceil', 'round'."""
    q = t_ms / dt
    n = round(q)
    if abs(q - n) <= TOL * max(1.0, abs(q)):
        return int(n)
    if rule == "exact":
        raise ConnectomeError(f"{t_ms} ms nie jest całkowitą wielokrotnością dt = {dt} ms (t/dt = {q!r})")
    if rule == "ceil":
        return int(math.ceil(q))
    if rule == "round":
        return int(round(q))
    raise ValueError(rule)


RULES = {"exact": ("exact", "exact"), "legacy": ("ceil", "round")}


class ALIFdt(ALIF):
    def __init__(self, spec, params, seed, gain=None, b_a=None, timing="exact", noise_ref_dt=1.0):
        p = params
        r_ref, r_del = RULES[timing]
        if timing == "legacy" and p.dt != 1.0:
            raise ConnectomeError("timing='legacy' tylko przy dt = 1 ms (odtworzenie starego modelu); przy innym dt użyj 'exact'")
        self.timing = timing
        self.n_ref = to_steps(p.t_ref, p.dt, r_ref)
        self.n_delay = to_steps(p.delay_ms, p.dt, r_del)
        self.sigma_step = p.noise * math.sqrt(noise_ref_dt / p.dt) if noise_ref_dt else p.noise
        if self.n_delay < 1:
            raise ConnectomeError(f"opóźnienie {p.delay_ms} ms < 1 krok dt={p.dt}")
        super().__init__(spec, p, seed, gain, b_a)

    def timing_report(self):
        p = self.p
        return dict(dt=p.dt, timing=self.timing, n_ref=self.n_ref, n_delay=self.n_delay,
                    t_ref_eff_ms=self.n_ref * p.dt, delay_eff_ms=self.n_delay * p.dt,
                    t_ref_err_ms=self.n_ref * p.dt - p.t_ref, delay_err_ms=self.n_delay * p.dt - p.delay_ms,
                    sigma_step=self.sigma_step, r_max_hz=self.r_max_hz)

    @property
    def r_max_hz(self):
        """Najkrótszy ISI = krok wykrycia + n_ref zablokowanych kroków."""
        return 1000.0 / ((self.n_ref + 1) * self.p.dt)

    def reset(self):
        super().reset()
        self.ref = np.zeros(self.N, np.int64)
        self.buf = np.zeros((self.n_delay, self.N), bool)

    def step(self, I_ext):
        p, dt = self.p, self.p.dt
        slot = self.t % self.n_delay
        self.g += self.W @ self.buf[slot] - self.g * dt / p.tau_syn
        I = I_ext + self.sigma_step * self.rng.standard_normal(self.N) if self.sigma_step else I_ext
        self.v += dt / p.tau_m * (p.v_rest - self.v + self.gain * (self.g + I) - self.a)
        self.v[self.ref > 0] = p.v_reset
        np.maximum(self.ref - 1, 0, out=self.ref)
        spk = self.v >= p.v_th
        self.v[spk] = p.v_reset
        self.ref[spk] = self.n_ref
        self.a += -self.a * dt / p.tau_a + self.b_a * spk
        self.buf[slot] = spk
        self.t += 1
        return spk


def isi_steps(D, dt, n_ref, tau_m=20.0, delta=7.0):
    """Wzór zamknięty (Euler, stały napęd D = gain·I [mV], bez szumu, g i adaptacji, V_reset = V_rest):
    ISI = n_ref + n*, n* = najmniejsze j ≥ 1 z D·(1 − (1 − h)^j) ≥ Δ, h = dt/τ_m. None, gdy D ≤ Δ (brak spike'ów)."""
    if D <= delta:
        return None
    h = dt / tau_m
    j = max(1, math.ceil(math.log(1 - delta / D) / math.log(1 - h) - 1e-12))
    while D * (1 - (1 - h) ** j) < delta:                 # strażnik zaokrąglenia logarytmu
        j += 1
    while j > 1 and D * (1 - (1 - h) ** (j - 1)) >= delta:
        j -= 1
    return n_ref + j


def isi_continuous_ms(D, t_ref=2.2, tau_m=20.0, delta=7.0):
    return t_ref + tau_m * math.log(D / (D - delta)) if D > delta else None
