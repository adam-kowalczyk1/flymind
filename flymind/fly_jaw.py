"""flymind/fly_jaw.py — szczęka SO-101 sterowana obwodem dotykowym nogi muchy (MaleCNS, T2 L). Bez bio2, bez mujoco.

Zasada projektu: o ruchu szczęki decyduje obwód z konektomu, nie algorytm. Klasyczny grip.ClassicGrip jest tylko
punktem odniesienia. Źródło komend: "snn:legT2L".

Pętla na takt 10 ms (10 kroków ALIF po 1 ms):
  dotyk padów [N] → prąd do receptorów szczecinkowych nogi [mV]   [MODEL] stała gain_mV_per_N, połowa receptorów na pad
  → SparseALIF obwodu nogi (receptory, interneurony, MN; połączenia i liczby synaps z danych)   [DATA] + znaki [MODEL]
  → częstości puli MN (filtr wykładniczy τ = rate_tau)
  → moment szczęki = k · (prostownik − zginacz)   [MODEL / ANALOGIA]

Mapowanie wyjścia jest analogią i decyzją projektową: mucha nie ma chwytaka. Wybrano je po pilocie (2026-11-03), który
pokazał, że dotyk szczecinek pobudza głównie prostowniki goleni. Prostownik → zaciskanie oznacza „dociśnij to, czego
dotykasz”. To nie jest biologia chwytu. Znak glutaminianu jest parametrem, bo dane go nie rozstrzygają (raport D1).
"""
from dataclasses import dataclass

import numpy as np

from alif import ALIFParams
from alif_sparse import SparseALIF
from leg_circuit import network
from snn_interface import DEFAULT_SIGN

PRESS = ("Ti extensor MN",)                          # → zaciskanie
RELEASE = ("Ti flexor MN", "Acc. ti flexor MN")      # → otwieranie


@dataclass(frozen=True)
class FlyJawCfg:
    leg: str = "T2"
    side: str = "L"
    J0: float = 0.2              # mV/synapsę, jak visual_path w loop.py (nie strojone tutaj)
    glu_sign: float = -1.0       # założenie o glutaminianie: −1 hamuje, +1 pobudza
    gain_mV_per_N: float = 40.0  # [MODEL] dotyk → prąd receptora; 10 było za mało (0,5 N → brak spike’ów, pilot 2026-11-03)
    max_mV: float = 40.0
    rate_tau: float = 0.05       # s
    k: float = 0.005             # N·m na Hz różnicy pul (100 Hz → 0,5 N·m)
    steps: int = 10              # kroków ALIF na takt sterowania


class FlyJaw:
    def __init__(self, cfg=FlyJawCfg(), spec=None):
        """spec: gotowa sieć o tych samych ciałach i kolejności (np. przetasowana kontrola); None = z danych."""
        self.cfg = cfg
        base, idx, self.rep = network(cfg.J0, cfg.leg, cfg.side, sign_map={**DEFAULT_SIGN, "glutamate": cfg.glu_sign})
        if spec is None:
            spec = base
        elif list(spec.bodies) != list(base.bodies):
            raise ValueError("spec: inne ciała lub kolejność niż obwód z danych")
        br = idx["sensory"]["mechanosensory bristle"]
        self.pad_in = (br[: len(br) // 2], br[len(br) // 2:])      # [MODEL] stały pad, ruchomy pad
        self.press = [i for p in PRESS for i in idx["MN"].get(p, [])]
        self.release = [i for p in RELEASE for i in idx["MN"].get(p, [])]
        if not self.press or not self.release:
            raise ValueError("brak puli MN prostownika lub zginacza w obwodzie")
        self.net = SparseALIF(spec, ALIFParams(), None)             # szum 0: generator losowy nieużywany
        self.N = spec.W.shape[0]
        self.r_press = self.r_release = 0.0

    def step(self, touch, dt=0.01):
        """touch[3] [N] (cs_fixed, cs_moving, cs_palm) → moment szczęki [N·m], + = zamykanie."""
        c = self.cfg
        X = np.zeros(self.N)
        for ix, f in zip(self.pad_in, touch[:2]):
            X[ix] = min(c.max_mV, c.gain_mV_per_N * max(0.0, float(f)))
        s = self.net.run(X, c.steps)
        a = dt / c.rate_tau
        self.r_press += a * (s[:, self.press].mean() * 1000 - self.r_press)
        self.r_release += a * (s[:, self.release].mean() * 1000 - self.r_release)
        return c.k * (self.r_press - self.r_release)
