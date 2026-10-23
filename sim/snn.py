"""ConnectomeSNN — sieć neuronów ALIF (Adaptive Leaky Integrate-and-Fire) w NumPy.

Krok dt = 1 ms, 10 kroków na cykl sterowania 100 Hz.
Wagi: W_ij = sign(nt_j) · J0 · ln(1 + N_syn,ij), gdzie nt_j to neuroprzekaźnik neuronu
presynaptycznego j: ACh → +1, GABA → −1, Glu → −1 (w OUN owadów glutaminian hamuje przez
kanały GluCl — Liu & Wilson 2013, PNAS). N_syn,ij to liczba synaps j → i z konektomu.
Uwaga: Shiu i in. 2024 używają wagi liniowej (0,275 mV × N_syn); ln(1+N) to wybór projektu
(kompresuje rozpiętość 1…7600 synaps), patrz RESULTS.md.
"""
import numpy as np

NT_SIGN = {"ACh": 1.0, "GABA": -1.0, "Glu": -1.0}


class ConnectomeSNN:
    # Błona jak w modelu całego mózgu Shiu i in. 2024 (Nature), mV / ms.
    V_REST = -52.0
    V_RESET = -52.0
    V_TH = -45.0
    TAU_M = 20.0
    TAU_SYN = 5.0
    T_REF = 2.2
    DELAY = 2          # opóźnienie synaptyczne 1,8 ms → 2 kroki po 1 ms
    # Adaptacja (ALIF): τ_a z zakresu 200–400 ms, przyrost 0,5 mV/spike (wyprowadzone
    # z Betkiewicz i in. 2020, eNeuro — u owadów brak gotowych parametrów; nasze stałe).
    TAU_A = 300.0
    B_A = 0.5

    def __init__(self, nt, gain=None, J0=1.0, noise=0.0, dt=1.0, seed=0):
        """nt: lista neuroprzekaźników (po jednym na neuron); gain: wzmocnienie wejścia
        (rezystancja wejściowa — zasada wielkości); noise: σ szumu prądu [mV]."""
        self.N = len(nt)
        self.sign = np.array([NT_SIGN[n] for n in nt])
        self.gain = np.ones(self.N) if gain is None else np.asarray(gain, float)
        self.J0, self.noise, self.dt = J0, noise, dt
        self.b_a = np.full(self.N, self.B_A)      # adaptacja per neuron (0 = bez adaptacji)
        self.rng = np.random.default_rng(seed)
        self.nsyn = np.zeros((self.N, self.N))   # nsyn[post, pre]
        self.reset()

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
        I = I_ext + self.noise * self.rng.standard_normal(self.N) if self.noise else I_ext
        drive = self.gain * (self.g + I) - self.a
        self.v += dt / self.TAU_M * (self.V_REST - self.v + drive)
        self.v[self.ref > 0] = self.V_RESET
        self.ref -= dt
        spk = self.v >= self.V_TH
        self.v[spk] = self.V_RESET
        self.ref[spk] = self.T_REF
        self.a += -self.a * dt / self.TAU_A + self.b_a * spk
        self.buf[self.t % self.DELAY] = spk
        self.t += 1
        return spk
