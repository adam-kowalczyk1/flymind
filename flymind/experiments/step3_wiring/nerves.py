"""„Nerwy” — model prawdziwego czucia i prawdziwych serw MIĘDZY mózgiem muchy a ramieniem (18 XI, cel: LOOP_TARGET_nerves_r1.md).
Mózg muchy (BrainNet etapu 1) bez zmian; zmienia się tylko to, co do niego dochodzi i co od niego wychodzi.

Nerw czuciowy (2 × FSR402 + Arduino, dzielnik z 10 kΩ, 5 V, ADC 10 bit):
  - tylko 2 czujniki: dłoń (touch[2]) i JEDEN pad szczęki stałej (touch[0]); jego odczyt idzie do obu połówek receptorów
    padów (podział na połówki był wyborem modelu, nie sprzętu); pad ruchomy (touch[1]) nie ma czujnika;
  - siła na czujniku = siła · g, g losowe na próbę i czujnik (montaż: część siły omija pole czujnika, rozrzut sztuk);
  - opór FSR z tabeli Adafruit (krzywa producenta): 0,2 N → 30 kΩ, 1 N → 6 kΩ, 10 N → 1 kΩ, 100 N → 250 Ω (log-log),
    poniżej 0,2 N obwód otwarty (0 zliczeń); szum ADC σ zliczeń; komputer przelicza zliczenia → N tą samą krzywą
    nominalną (nie zna g); opóźnienie odczytu (Arduino → USB) d_s taktów po 10 ms.
Nerw ruchowy (STS3215 przez magistralę):
  - cele stawów wysyłane co m_every taktów, z opóźnieniem d_m taktów, kwantowane do 4096 kroków/obrót;
  - moment szczęki = tryb PWM (jak w modelu so101.py: 3,35 N·m = 100 %), kwant 1/1000, te same takt i opóźnienie.
Poziomy: ideal (brak nerwów), typ (typowe), pess (pesymistyczne). Losowość tylko z ziarna sceny → pary między sieciami.
Uruchom jak touch_natural.py, plus --nerves ideal|typ|pess."""
import os
import sys
from collections import deque

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LEVELS = {
    "ideal": None,
    "typ": dict(g=(0.7, 1.1), adc_sd=1.5, d_s=1, m_every=1, d_m=1),
    "pess": dict(g=(0.4, 1.2), adc_sd=4.0, d_s=3, m_every=3, d_m=2),
}
F_TAB = np.log([0.2, 1.0, 10.0, 100.0])           # N
R_TAB = np.log([30e3, 6e3, 1e3, 250.0])          # Ω (Adafruit FSR 402, tabela z krzywej producenta)
R_FIX, ADC = 10e3, 1023
Q_STEP = 2 * np.pi / 4096                        # rad, enkoder STS3215
TAU_FULL, TAU_STEPS = 3.35, 1000                 # N·m przy 100 % PWM, rozdzielczość PWM


def fsr_counts(f):
    """Siła [N] → zliczenia ADC (bez szumu)."""
    if f < 0.2:
        return 0.0
    r = np.exp(np.interp(np.log(min(f, 100.0)), F_TAB, R_TAB))
    return ADC * R_FIX / (R_FIX + r)


def counts_to_force(c):
    """Zliczenia → siła [N] krzywą nominalną (to, co zrobi program na komputerze)."""
    c0 = fsr_counts(0.2)
    if c < c0 * 0.5:                              # poniżej progu zadziałania = brak dotyku
        return 0.0
    c = min(c, ADC - 1)
    r = R_FIX * (ADC - c) / c
    return float(np.exp(np.interp(np.log(r), R_TAB[::-1], F_TAB[::-1])))


class Nerves:
    def __init__(self, level, seed):
        self.p = LEVELS[level]
        if self.p is None:
            return
        self.rng = np.random.default_rng([int(seed), 18112026])
        self.g = self.rng.uniform(*self.p["g"], size=2)                    # [dłoń, pad]
        self.sense = deque([np.zeros(3)] * (self.p["d_s"] + 1), maxlen=self.p["d_s"] + 1)
        self.k = 0
        self.wish = None                                                   # cel, którego „chce” sieć (suma jej dq)
        self.sent = None                                                   # cel, który ma serwo
        self.pipe = deque()
        self.tau_sent = 0.0

    def feel(self, touch):
        """Prawdziwa siła ze świata → to, co czuje sieć (te same jednostki co touch)."""
        if self.p is None:
            return touch
        out = np.zeros(3)
        for f, gi, dst in ((touch[2], self.g[0], (2,)), (touch[0], self.g[1], (0, 1))):
            c = fsr_counts(float(f) * gi) + self.rng.normal(0, self.p["adc_sd"])
            v = counts_to_force(round(min(max(c, 0.0), ADC)))
            for d in dst:
                out[d] = v
        self.sense.append(out)
        return self.sense[0]

    def move(self, dq, tau):
        """Życzenie sieci (przyrost celów stawów, moment szczęki) → to, co serwa dostają w tym takcie."""
        if self.p is None:
            return dq, tau
        if self.wish is None:
            self.wish, self.sent = np.zeros(len(dq)), np.zeros(len(dq))
        self.wish = self.wish + dq
        if self.k % self.p["m_every"] == 0:
            q = np.round(self.wish / Q_STEP) * Q_STEP
            t = np.sign(tau) * min(np.round(abs(tau) / TAU_FULL * TAU_STEPS), TAU_STEPS) * TAU_FULL / TAU_STEPS
            self.pipe.append((self.k + self.p["d_m"], q, t))
        self.k += 1
        out = np.zeros(len(dq))
        while self.pipe and self.pipe[0][0] < self.k:
            _, q, t = self.pipe.popleft()
            out += q - self.sent
            self.sent, self.tau_sent = q, t
        return out, self.tau_sent


def wrap(NetCls, level):
    """Podklasa sieci: mózg bez zmian, tylko nerwy na wejściu i wyjściu. Ziarno nerwów ustawia trial (ziarno sceny)."""
    class NerveNet(NetCls):
        nerve_seed = 0

        def reset(self):
            super().reset()
            self.nv = Nerves(level, self.nerve_seed)
            self.tau_raw = 0.0

        def step(self, touch, q, qd, dt=0.01, **kw):
            dq = super().step(self.nv.feel(np.asarray(touch, float)), q, qd, dt, **kw)
            self.tau_raw = self.tau
            dq, self.tau = self.nv.move(np.asarray(dq, float), self.tau_raw)
            return dq

    NerveNet.__name__ = f"Nerve{NetCls.__name__}_{level}"
    return NerveNet


def _check():
    assert fsr_counts(0.1) == 0 and counts_to_force(0) == 0.0
    for f in (0.3, 1.0, 3.0, 10.0):
        assert abs(counts_to_force(fsr_counts(f)) - f) / f < 0.02, f
    n = Nerves("typ", 1)
    n.g[:] = 1.0
    n.p = dict(n.p, adc_sd=0.0)
    seen = [n.feel(np.array([2.0, 0.0, 3.0]))[2] for _ in range(3)]
    assert seen[0] == 0.0 and abs(seen[1] - 3.0) < 0.1, seen                # 1 takt opóźnienia
    out = [n.move(np.full(5, 0.01), 0.1)[0][0] for _ in range(4)]
    assert out[0] == 0.0 and abs(sum(out) - 0.03) < 2 * Q_STEP, out         # opóźnienie 1 takt, suma = życzenie
    assert Nerves("ideal", 1).feel(np.ones(3)) is not None
    print("nerves _check OK")


if __name__ == "__main__":
    _check()
