"""flymind/alif.py — sieć ALIF na SNNSpec i walidacja dynamiki (krok 5). Bez bio2, bez mujoco, nic nie zapisuje.

Równania przepisane z bio2/snn.py (równoważności nie testowano — wymagałoby importu bio2):
  g ← g + W·s(t − d) − g·dt/τ_syn                    prąd synaptyczny [mV]; skok o W[post, pre] na spike
  v ← v + dt/τ_m · (V_rest − v + gain·(g + I_ext + σ·ξ) − a)
  w refrakcji v ← V_reset; spike gdy v ≥ V_th → v ← V_reset, ref ← T_ref
  a ← a − a·dt/τ_a + b_a·s                           adaptacja [mV]
Różnica wobec bio2: tam opóźnienie to stałe 2 kroki niezależnie od dt; tu delay_ms jest przeliczane na kroki.
Skutek kwantyzacji (też w bio2): refrakcja 2,2 ms trwa faktycznie ceil(T_ref/dt) = 3 kroki → r_max = 250 Hz.
"""
from dataclasses import dataclass

import numpy as np

from connectome import ConnectomeError


@dataclass(frozen=True)
class ALIFParams:
    # błona: Shiu i in. 2024 (Nature), jak bio2/snn.py — parametry modelu, nie pomiar tych neuronów
    v_rest: float = -52.0
    v_reset: float = -52.0
    v_th: float = -45.0
    tau_m: float = 20.0
    tau_syn: float = 5.0
    t_ref: float = 2.2
    delay_ms: float = 1.8
    # adaptacja: wybór projektu bio2 (Betkiewicz i in. 2020 jako inspiracja, brak danych dla tych neuronów)
    tau_a: float = 300.0
    b_a: float = 0.5
    noise: float = 0.0          # σ szumu prądu [mV]
    dt: float = 1.0             # ms
    max_dt_tau: float = 0.5     # Euler: dt/τ powyżej tego → odmowa (błąd zaniku > ~10 % na krok)

    @property
    def delay_steps(self):
        return int(round(self.delay_ms / self.dt))

    @property
    def r_max(self):
        """Maksymalna częstość [Hz] przy kwantyzacji refrakcji (spike + ceil(T_ref/dt) kroków zablokowanych)."""
        return 1000.0 / (self.dt * (np.ceil(self.t_ref / self.dt - 1e-9) + 1))


class ALIF:
    def __init__(self, spec, params, seed, gain=None, b_a=None):
        """seed obowiązkowy (reprodukowalność); gain, b_a: per neuron, domyślnie 1 i params.b_a."""
        p = params
        ratio = p.dt / min(p.tau_m, p.tau_syn, p.tau_a)
        if ratio > p.max_dt_tau:
            raise ConnectomeError(f"dt/τ = {ratio:.2f} > {p.max_dt_tau} — całkowanie Eulera niestabilne/niedokładne")
        if p.delay_steps < 1:
            raise ConnectomeError(f"opóźnienie {p.delay_ms} ms < 1 krok dt={p.dt}")
        self.p, self.W = p, np.asarray(spec.W, float)
        self.N = self.W.shape[0]
        self.gain = np.ones(self.N) if gain is None else np.asarray(gain, float)
        self.b_a = np.full(self.N, p.b_a) if b_a is None else np.asarray(b_a, float)
        self.rng = np.random.default_rng(seed)
        self.reset()

    def reset(self):
        p = self.p
        self.v = np.full(self.N, p.v_rest)
        self.g = np.zeros(self.N)
        self.a = np.zeros(self.N)
        self.ref = np.zeros(self.N)
        self.buf = np.zeros((p.delay_steps, self.N), bool)
        self.t = 0

    def step(self, I_ext):
        p, dt = self.p, self.p.dt
        slot = self.t % p.delay_steps
        self.g += self.W @ self.buf[slot] - self.g * dt / p.tau_syn
        I = I_ext + p.noise * self.rng.standard_normal(self.N) if p.noise else I_ext
        self.v += dt / p.tau_m * (p.v_rest - self.v + self.gain * (self.g + I) - self.a)
        self.v[self.ref > 0] = p.v_reset
        self.ref -= dt
        spk = self.v >= p.v_th
        self.v[spk] = p.v_reset
        self.ref[spk] = p.t_ref
        self.a += -self.a * dt / p.tau_a + self.b_a * spk
        self.buf[slot] = spk
        self.t += 1
        return spk

    def run(self, I_ext, steps):
        """I_ext: (N,) stałe albo [steps, N]. Zwraca spike'i [steps, N]. Błąd przy NaN/inf w wejściu lub stanie."""
        I_ext = np.broadcast_to(np.asarray(I_ext, float), (steps, self.N))
        if not np.isfinite(I_ext).all():
            raise ConnectomeError("wejście zawiera NaN/inf")
        out = np.zeros((steps, self.N), bool)
        for k in range(steps):
            out[k] = self.step(I_ext[k])
        if not (np.isfinite(self.v).all() and np.isfinite(self.g).all() and np.isfinite(self.a).all()):
            raise ConnectomeError(f"stan sieci nieskończony/NaN po {steps} krokach")
        return out


def rates(spikes, dt):
    """Częstość per neuron [Hz] z okna spike'ów [T, N]."""
    return spikes.mean(0) * 1000.0 / dt


def validate(spec, params, seed, I_on, on_ms=300, off_ms=700, pops=None, other_seed=None, **net_kw):
    """Protokół: cisza (szum 0, wejście 0) → bodziec I_on przez on_ms → brak bodźca przez off_ms.
    Raport: numeryka, punkt stały ciszy, deterministyczność, częstości per populacja, nasycenie, trwałość/eksplozja."""
    p = params
    on, off = int(on_ms / p.dt), int(off_ms / p.dt)
    rep = dict(numerics=dict(dt_tau_m=p.dt / p.tau_m, dt_tau_syn=p.dt / p.tau_syn, delay_steps=p.delay_steps,
                             delay_quantization_ms=p.delay_steps * p.dt - p.delay_ms, r_max_hz=p.r_max))

    quiet = ALIF(spec, ALIFParams(**{**p.__dict__, "noise": 0.0}), seed, **net_kw)
    s0 = quiet.run(0.0, int(200 / p.dt))
    rep["silent_fixed_point"] = bool(not s0.any() and (quiet.v == p.v_rest).all() and not quiet.g.any())

    I = np.zeros((on + off, len(spec.bodies)))
    I[:on] = I_on

    def protocol(sd):
        return ALIF(spec, p, sd, **net_kw).run(I, on + off)

    s = protocol(seed)
    rep["deterministic"] = bool((protocol(seed) == s).all())
    if p.noise and other_seed is not None:
        rep["seed_changes_noise"] = bool((protocol(other_seed) != s).any())

    r_on, r_off = rates(s[:on], p.dt), rates(s[on + off // 2:], p.dt)      # druga połowa okna „off”
    rep["saturated_frac"] = float((r_on >= 0.9 * p.r_max).mean())
    rep["active_frac_on"] = float((r_on > 0).mean())
    rep["mean_rate_on_hz"], rep["mean_rate_late_off_hz"] = float(r_on.mean()), float(r_off.mean())
    rep["extinct_after_off"] = bool(r_off.max() == 0)
    rep["runaway"] = bool(r_off.mean() > r_on.mean())                       # aktywność rośnie po zdjęciu bodźca
    if pops:
        pos = {int(b): i for i, b in enumerate(spec.bodies)}
        rep["pops_hz"] = {k: (round(float(r_on[[pos[b] for b in v if b in pos]].mean()), 2),
                              round(float(r_off[[pos[b] for b in v if b in pos]].mean()), 2))
                          for k, v in pops.items() if any(b in pos for b in v)}
    return rep
