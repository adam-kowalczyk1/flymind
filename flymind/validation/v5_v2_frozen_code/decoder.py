"""flymind/decoder.py — dekoder motoryczny (krok 7): spike'i DN/MN → komendy fizyczne. Bez bio2, bez mujoco.

Wyjścia (konwencje jak bio2; przeliczenie na ctrl serw to krok 9, ograniczenia bezpieczeństwa to krok 8):
  omega   [rad/s] prędkość obrotu bazy, + = w lewo       — z różnic L−P częstości DNa02 (szybko) i DNa01 (wolno)
  torque  [N·m]   moment szczęki, + = zamykanie           — z MN_flex + MN_ltm (zamykają) − MN_ext (otwiera)

Przepisane z bio2 (tylko odczyt: brain.py step10/calibrate_steer, agent.py step, vnc.py muscle):
  częstość  r ← a·r + (1−a)·s/dt,  a = exp(−dt/τ_rate)            (bio2: τ_rate 50 ms, dt 1 ms)
  skręt     d_c = mean r[c_L] − mean r[c_R];  d̃_c ← filtr τ_c;  kąt_c = (d̃_c − offset_c)/slope_c;
            omega = gain · mean_c kąt_c, przycięte do ±w_max       (bio2: τ 0,10/0,40 s, gain 2,5 1/s, w_max 1 rad/s)
  mięsień   twitch ← filtr τ_klasy; F = force_klasy · tanh(twitch/sat_hz); torque = k·(ΣF_zamyk − ΣF_otw)
Wszystkie stałe to parametry modelu (wybory bio2), nie pomiary. Kalibracja offset/slope jest dopasowaniem do
odpowiedzi tej konkretnej sieci — kanał bez zależności od kąta jest odrzucany (fit_steer), a nie liczony z zerem.
NIE ma tu bramek zachowania z bio2 (hunting, LOCK, kontakt, ucieczka, podnoszenie) — to klasyczna logika sterowania,
nie dekodowanie; jeśli wróci, to jako osobna, jawnie nazwana warstwa.
"""
from dataclasses import dataclass

import numpy as np


class DecoderError(ValueError):
    pass


def _ema_step(state, x, dt, tau):
    a = np.exp(-dt / tau)
    return a * state + (1 - a) * x


def _take(spikes, idx):
    """Kolumny idx z bool [k, N]; zły typ/kształt albo za mało neuronów → błąd."""
    spikes = np.asarray(spikes)
    if spikes.dtype != bool or spikes.ndim != 2 or spikes.shape[1] <= idx.max():
        raise DecoderError(f"spike'i {spikes.dtype} {spikes.shape}, oczekiwano bool [k, N > {idx.max()}]")
    return spikes[:, idx]


def channel_provenance(spec, idx):
    """Skąd pochodzi wejście populacji idx w SNNSpec: |W_data| i |W_model| (suma wierszy) i udział modelu.
    Pozwala sprawdzić, czy kanał dekodera jest napędzany danymi, czy krawędziami dodanymi przez modelarza."""
    d, m = float(np.abs(spec.W_data[idx]).sum()), float(np.abs(spec.W_model[idx]).sum())
    return dict(data=d, model=m, model_frac=m / (d + m) if d + m else float("nan"))


def fit_steer(x, diffs, min_slope):
    """Kalibracja liniowa per kanał: diffs[:, c] ≈ offset_c + slope_c·x.  x: [n] kąt [rad] (lub inna znana zmienna
    sterująca), diffs: [n, C] różnice L−P [Hz]. |slope| < min_slope [Hz/rad] → odmowa (kanał nie koduje kąta)."""
    x, diffs = np.asarray(x, float), np.atleast_2d(np.asarray(diffs, float).T).T
    if len(x) < 2 or np.ptp(x) == 0 or len(diffs) != len(x) or not np.isfinite(diffs).all():
        raise DecoderError("kalibracja wymaga ≥ 2 różnych x i skończonych różnic tej samej długości")
    (off, slope), *_ = np.linalg.lstsq(np.c_[np.ones_like(x), x], diffs, rcond=None)
    dead = np.flatnonzero(np.abs(slope) < min_slope)
    if dead.size:
        raise DecoderError(f"kanały {dead.tolist()}: |slope| {np.abs(slope[dead]).round(3).tolist()} < {min_slope} Hz/rad")
    return off, slope


@dataclass(frozen=True)
class SteerParams:
    tau_rate_ms: float = 50.0          # bio2 brain.py tau_rate
    tau_s: tuple = (0.10, 0.40)        # filtr odczytu per kanał [s]: DNa02 szybki, DNa01 wolny (bio2 agent.py)
    gain: float = 2.5                  # 1/s, G_TURN (mucha: 2–3,3 (°/s)/°)
    w_max: float = 1.0                 # rad/s


class SteerDecoder:
    def __init__(self, idx, channels, offset, slope, params=SteerParams()):
        """idx: {'<kanał>_L'/'<kanał>_R': indeksy neuronów}; channels np. ('DNa02', 'DNa01') albo ('DNa02',) —
        ablacja kanału modelowego. offset/slope z fit_steer, w kolejności channels."""
        p = params
        if len(p.tau_s) < len(channels) or len(offset) != len(channels) or len(slope) != len(channels):
            raise DecoderError("liczba kanałów ≠ długość tau_s/offset/slope")
        if not np.all(np.abs(slope) > 0) or not np.isfinite(np.r_[offset, slope]).all():
            raise DecoderError("slope = 0 lub nieskończona kalibracja")
        self.LR = []
        for c in channels:
            L, R = (np.asarray(idx.get(f"{c}_{s}", []), int) for s in "LR")
            if not (L.size and R.size):
                raise DecoderError(f"kanał {c}: pusta populacja L lub R")
            self.LR.append((L, R))
        self.used = np.unique(np.concatenate([np.r_[L, R] for L, R in self.LR]))
        self.LR = [(np.searchsorted(self.used, L), np.searchsorted(self.used, R)) for L, R in self.LR]
        self.channels, self.p = tuple(channels), p
        self.offset, self.slope = np.asarray(offset, float), np.asarray(slope, float)
        self.tau = np.asarray(p.tau_s[:len(channels)], float)
        self.reset()

    def reset(self):
        self.r = np.zeros(len(self.used))   # częstość [Hz] neuronów self.used
        self.d_f = self.offset.copy()  # jak bio2: odczyt startuje od trymu (kąt 0), nie od 0 Hz

    def step(self, spikes, dt_ms):
        """spikes: bool [k, N] z jednego okresu sterowania (k kroków po dt_ms). Zwraca dict omega i diagnostykę."""
        for s in _take(spikes, self.used):
            self.r = _ema_step(self.r, s * 1000.0 / dt_ms, dt_ms, self.p.tau_rate_ms)
        diff = np.array([self.r[L].mean() - self.r[R].mean() for L, R in self.LR])
        self.d_f = _ema_step(self.d_f, diff, len(spikes) * dt_ms / 1000.0, self.tau)
        angle = (self.d_f - self.offset) / self.slope
        raw = self.p.gain * float(angle.mean())
        return dict(omega=float(np.clip(raw, -self.p.w_max, self.p.w_max)), omega_raw=raw,
                    clipped=abs(raw) > self.p.w_max, diff_hz=diff, angle=angle)


# ---------------- mięsień szczęki (MN) ----------------

# (siła na jednostkę, τ skurczu [ms]) per klasa — bio2 vnc.py SIZE_CLASS/tau_twitch (model, nie pomiar)
MN_CLASS = {"slow": (0.1, 60.0), "int": (1.0, 20.0), "fast": (10.0, 10.0)}


def size_classes(input_synapses, classes):
    """Przypisanie klas MN wg rangi liczby synaps wejściowych (największa → classes[0]). Reguła modelu bio2."""
    if len(input_synapses) != len(classes):
        raise DecoderError(f"{len(input_synapses)} MN, {len(classes)} klas")
    out = [None] * len(classes)
    for rank, j in enumerate(np.argsort(-np.asarray(input_synapses), kind="stable")):
        out[j] = classes[rank]
    return out


class GripDecoder:
    def __init__(self, close, open_, classes_close, classes_open, k_muscle=0.40, sat_hz=100.0):
        """close: indeksy MN zamykających (MN_flex + MN_ltm), open_: otwierających (MN_ext); klasy z MN_CLASS."""
        close, open_ = np.asarray(close, int), np.asarray(open_, int)
        if not (close.size and open_.size) or np.intersect1d(close, open_).size:
            raise DecoderError("MN zamykające i otwierające: niepuste i rozłączne")
        cls = list(classes_close) + list(classes_open)
        if len(cls) != close.size + open_.size or not set(cls) <= set(MN_CLASS):
            raise DecoderError(f"klasy MN muszą być z {sorted(MN_CLASS)}, po jednej na neuron")
        self.idx = np.r_[close, open_]
        self.sign = np.r_[np.ones(close.size), -np.ones(open_.size)]
        self.force = np.array([MN_CLASS[c][0] for c in cls])
        self.tau = np.array([MN_CLASS[c][1] for c in cls])
        self.k, self.sat = k_muscle, sat_hz
        self.reset()

    def reset(self):
        self.twitch = np.zeros(self.idx.size)

    def step(self, spikes, dt_ms):
        """spikes: bool [k, N]. Zwraca dict torque [N·m, + zamykanie] i składowe."""
        for s in _take(spikes, self.idx):
            self.twitch = _ema_step(self.twitch, s * 1000.0 / dt_ms, dt_ms, self.tau)
        F = self.force * np.tanh(self.twitch / self.sat)
        return dict(torque=float(self.k * (self.sign * F).sum()), close=float(self.k * F[self.sign > 0].sum()),
                    open=float(self.k * F[self.sign < 0].sum()))
