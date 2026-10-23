"""ConnectomeSNN — sieć neuronów ALIF (Adaptive Leaky Integrate-and-Fire) w NumPy.

Krok dt = 1 ms, 10 kroków na cykl sterowania 100 Hz.
Wagi: W_ij = sign(nt_i) · J0 · ln(1 + N_syn,ij), gdzie nt_i to neuroprzekaźnik neuronu
presynaptycznego: ACh → +1, GABA → −1, Glu → −1 (w OUN owadów glutaminian hamuje przez
kanały GluCl). N_syn to liczba synaps między parą neuronów.
"""
import numpy as np

NT_SIGN = {"ACh": 1.0, "GABA": -1.0, "Glu": -1.0}


class ConnectomeSNN:
    # Parametry błony jak w modelu całego mózgu Shiu i in. 2024 (Nature), mV / ms.
    V_REST = -52.0
    V_RESET = -52.0
    V_TH = -45.0
    TAU_M = 20.0
    TAU_SYN = 5.0
    T_REF = 2.2
    DELAY = 2          # opóźnienie synaptyczne w krokach (1,8 ms u Shiu → 2 ms)
    # Adaptacja (ALIF) — nasze stałe, typowe dla adaptacji częstotliwości wyładowań.
    TAU_A = 200.0
    B_A = 1.5          # przyrost prądu adaptacji po każdym spike'u [mV]

    def __init__(self, sizes, nt, gain=None, dt=1.0, J0=1.0, seed=0):
        """sizes: {populacja: liczba neuronów}; nt: {populacja: 'ACh'|'GABA'|'Glu'};
        gain: {populacja: wzmocnienie wejścia} — rezystancja wejściowa (zasada wielkości)."""
        self.dt, self.J0 = dt, J0
        self.rng = np.random.default_rng(seed)
        self.idx, start = {}, 0
        for p, n in sizes.items():
            self.idx[p] = np.arange(start, start + n)
            start += n
        self.N = start
        self.sign = np.zeros(self.N)
        self.gain = np.ones(self.N)
        for p, ids in self.idx.items():
            self.sign[ids] = NT_SIGN[nt[p]]
            if gain and p in gain:
                self.gain[ids] = gain[p]
        self.nsyn = np.zeros((self.N, self.N))   # nsyn[post, pre]
        self.reset()

    def connect(self, pre, post, n_syn, p=1.0, exclude_self=True):
        """Połącz populacje. n_syn: średnia liczba synaps na połączoną parę (Poisson, ≥1);
        p: prawdopodobieństwo połączenia pary. Może być tablicą [len(post), len(pre)]."""
        i, j = self.idx[post], self.idx[pre]
        mask = self.rng.random((len(i), len(j))) < p
        n = np.maximum(1, self.rng.poisson(np.broadcast_to(n_syn, mask.shape)))
        block = np.where(mask, n, 0)
        if exclude_self and pre == post:
            np.fill_diagonal(block, 0)
        self.nsyn[np.ix_(i, j)] += block

    def build(self):
        self.W = self.sign[None, :] * self.J0 * np.log1p(self.nsyn)
        return self

    def reset(self):
        self.v = np.full(self.N, self.V_REST)
        self.g = np.zeros(self.N)
        self.a = np.zeros(self.N)
        self.ref = np.zeros(self.N)
        self.buf = np.zeros((self.DELAY, self.N), dtype=bool)
        self.t = 0

    def step(self, I_ext):
        """Jeden krok 1 ms. I_ext: prąd zewnętrzny [mV] (N,). Zwraca wektor spike'ów (bool)."""
        dt = self.dt
        arriving = self.buf[self.t % self.DELAY]
        self.g += self.W @ arriving - self.g * dt / self.TAU_SYN
        drive = self.gain * (self.g + I_ext) - self.a
        self.v += dt / self.TAU_M * (self.V_REST - self.v + drive)
        self.v[self.ref > 0] = self.V_RESET
        self.ref -= dt
        spk = self.v >= self.V_TH
        self.v[spk] = self.V_RESET
        self.ref[spk] = self.T_REF
        self.a += -self.a * dt / self.TAU_A + self.B_A * spk
        self.buf[self.t % self.DELAY] = spk
        self.t += 1
        return spk

    def run(self, I_ext, steps):
        """steps kroków ze stałym (lub zależnym od kroku: callable k → I) wejściem.
        Zwraca macierz spike'ów [steps, N]."""
        out = np.zeros((steps, self.N), dtype=bool)
        for k in range(steps):
            out[k] = self.step(I_ext(k) if callable(I_ext) else I_ext)
        return out
