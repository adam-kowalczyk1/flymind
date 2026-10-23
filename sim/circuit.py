"""Obwód sterownika: neurony i synapsy z MaleCNS v1.0 (sim/circuit_malecns.json) + 16 neuronów
modelowych odwrócenia odruchu (nie z konektomu) + kodery wejść i dekodery wyjść.

Moduł odruchu (model, liczby synaps nasze):
  RR_assist (6, ACh):  dotyk (czułe aferenty dłoni i szczęk) → zginacz + ltm; aktywny tylko w stanie „polowanie”
                       (wspomaganie = odwrócony odruch, Bässler; stan aktywny/pasywny);
                       samopobudzenie bez adaptacji = zatrzask: krótki dotyk → trwałe zamykanie.
  RR_resist (6, GABA): nacisk ruchomej szczęki i prędkość zamykania → mocno wyłącza szybkie i pośrednie MN,
                       słabiej wolne (odruch oporu / ogranicznik siły) oraz DNa02 (dotyk wstrzymuje
                       skręt); w stanie pasywnym czulszy.
  RR_hold (4, ACh):    zatrzask „trzymam”: koincydencja nacisku OBU szczęk (ujemny prąd stanu, jeden
                       kanał nie wystarcza) → trwałe pobudzenie RR_resist,
                       więc po uderzeniu trzymają już tylko wolne MN (zasada wielkości).

Wejścia:  azymut celu → LC10a (pola recepcyjne);  siły w szczękach → neurony czuciowe nogi.
Wyjścia:  DNa02 L−R → prędkość obrotu bazy;  MN zginacza/ltm − MN prostownika → moment szczęki.
"""
import json
import os

import numpy as np

from snn import ConnectomeSNN

HERE = os.path.dirname(os.path.abspath(__file__))

# Zasada wielkości (Azevedo i in. 2020, eLife): rezystancja wejściowa wolny/pośredni/szybki
# ~700/300/150 MΩ → wzmocnienie wejścia 1 : 0,43 : 0,21; siła na spike <0,1 / ~1 / ~10 µN.
SIZE_CLASS = {"slow": (1.0, 0.1), "int": (0.43, 1.0), "fast": (0.21, 10.0)}

N_RR = 6           # neuronów w grupach RR_assist i RR_resist (nasza liczba)
N_HOLD = 4         # neuronów RR_hold

# --- nasze stałe (strojone w symulacji, nie z literatury) ---
P = dict(
    J0=1.6,            # mV na ln(1+N_syn)
    noise=3.0,         # σ szumu prądu [mV]
    vis_amp=28.0,      # prąd LC10a w środku pola recepcyjnego [mV]
    vis_sigma=np.radians(15),
    bias_aotu=7.5, bias_dna02=7.0, bias_ext=8.5, bias_slow=6.0,
    bias_in=4.0,       # tło interneuronów nogi (niezmodelowane wejścia premotoryczne)
    sens_gain=26.0,    # mV / N siły (× współczynnik progu neuronu)
    state_bias=4.0,    # prąd stanu „aktywny/pasywny” na neurony odwrócenia odruchu
    k_yaw=0.04,        # rad/s na (spike/s) DNa02 L−R → wzmocnienie pościgu ~2,7 (°/s)/° (mucha: 2–3,3)
    resist_kmax=5.0,   # aferenty szczęk o czułości < resist_kmax zasilają opór
    syn_resist_dn=1000, syn_resist_assist=0,
    calibrate=True,    # auto-trym DNa02 przy tworzeniu (patrz calibrate)
    vel_gain=205.0,     # mV na rad/s prędkości zamykania szczęki → RR_resist (tłumienie)
    syn_palm_assist=10, syn_jaw_resist=1000, syn_assist_mn=1000, syn_resist_mn=1000, syn_latch=1000,
    gain_dna02=2.5, gain_lc10a=0.5,    # wzmocnienie wejścia DNa02 (kompensuje kompresję ln jednej silnej synapsy)
    tau_rate=100.0,    # ms, filtr częstości DN
    tau_twitch=dict(fast=10.0, int=20.0, slow=60.0),   # ms, skurcz: szybkie włókna krótko, wolne długo
    syn_resist_slow=10, syn_moving_hold=30, hold_offset=19.5, syn_hold_resist=1000,
    k_muscle=0.48,      # N·m na jednostkę siły MN (pośredni MN przy 50 Hz ≈ 0,37 N·m)
)


def full_circuit():
    """Pełna lista neuronów (MaleCNS + modelowe) i krawędzie z pliku. Kolejność = indeks „pełny”."""
    c = json.load(open(os.path.join(HERE, "circuit_malecns.json")))
    neurons = c["neurons"]
    # neurony modelowe odwrócenia odruchu (nie z konektomu)
    for name, nt in [("RR_assist", "ACh")] * N_RR + [("RR_resist", "GABA")] * N_RR + [("RR_hold", "ACh")] * N_HOLD:
        neurons.append(dict(bodyId=-len(neurons), type=name, side="L", circuit="model", nt=nt))
    # czujniki szczęk → neurony czuciowe: przydział po kolei na pełnej liście (nasz wybór); zapisany
    # w neuronie, żeby ablacja nie przetasowała kanałów
    sens = [n for n in neurons if n["circuit"] == "grip" and n.get("subclass") in ("campaniform sensilla", "leg")]
    for ch, part in zip(("fixed", "moving", "palm"), np.array_split(np.arange(len(sens)), 3)):
        for j in part:
            sens[j]["sens_ch"] = ch
    return neurons, c["edges"]


def make_groups(neurons):
    g = {k: [] for k in POPULATIONS}
    for i, n in enumerate(neurons):
        t = n["type"]
        if n["circuit"] == "track":
            key = f"{t}_{n['side']}"
        elif t == "Ti flexor MN":
            key = "MN_flex"
        elif t == "Ti extensor MN":
            key = "MN_ext"
        elif t == "ltm MN":
            key = "MN_ltm"
        elif n["circuit"] == "model":
            key = t
        elif "sens_ch" in n:
            key = "SENS_" + n["sens_ch"]
        else:
            key = "IN_" + n["nt"]
        g[key].append(i)
    return {k: np.array(v, dtype=int) for k, v in g.items()}


POPULATIONS = ["LC10a_L", "LC10a_R", "AOTU019_L", "AOTU019_R", "AOTU025_L", "AOTU025_R", "DNa02_L", "DNa02_R",
               "SENS_fixed", "SENS_moving", "SENS_palm", "IN_ACh", "IN_GABA", "IN_Glu",
               "RR_assist", "RR_resist", "RR_hold", "MN_ext", "MN_flex", "MN_ltm"]


class FlyController:
    def __init__(self, seed=0, params=None, keep=None, compensate=False):
        """keep: maska (bool) na pełnej liście neuronów — ablacja. Usunięte neurony znikają z sieci
        (mniejsza macierz W, więc i mniejszy koszt CPU); pozostałe zachowują cechy z pełnego obwodu
        (klasa MN, pole recepcyjne, próg czucia).
        compensate: kompensacja homeostatyczna — ocalałe neurony populacji przejmują jej synapsy
        (wagi wyjściowe × n_pełne/n_zostało; skalowanie synaptyczne), a ocalałe MN przejmują włókna
        mięśniowe usuniętych z tej samej puli (reinerwacja kolateralna)."""
        self.p = dict(P, **(params or {}))
        neurons, edges = full_circuit()
        N = len(neurons)
        idx = {n["bodyId"]: i for i, n in enumerate(neurons)}
        g = make_groups(neurons)

        # --- cechy per neuron, liczone na PEŁNYM obwodzie ---
        gain = np.ones(N)
        force = np.zeros(N)
        mn_class = np.array([None] * N, dtype=object)
        for key in ("flex", "ext", "ltm"):
            ids = g["MN_" + key]
            size = np.array([neurons[i]["input_synapses"] for i in ids])
            order = np.argsort(-size)       # największy → szybki
            classes = {"flex": ["fast", "int", "int", "slow", "slow"], "ext": ["fast", "slow"],
                       "ltm": ["int", "int", "slow", "slow"]}[key]
            for rank, j in enumerate(order):
                i = ids[j]
                mn_class[i] = classes[rank]
                gain[i], force[i] = SIZE_CLASS[classes[rank]]
        gain[g["DNa02_L"]] = gain[g["DNa02_R"]] = self.p["gain_dna02"]
        # LC10a: rekurencja LC10a→LC10a (~13 tys. synaps/stronę) przy wzmocnieniu 1 dawała salwy
        # (σ skrętu 2 rad/s); niższa rezystancja wejściowa + silniejszy bodziec wzrokowy
        gain[g["LC10a_L"]] = gain[g["LC10a_R"]] = self.p["gain_lc10a"]
        # pola recepcyjne LC10a: równomierna mapa retinotopowa w polu −15°…165° po swojej stronie
        # (Ribeiro 2018). Losowe położenia dawały stały przechył L/R zależny od ziarna (~5°).
        pref = np.zeros(N)
        pref[g["LC10a_L"]] = np.radians(np.linspace(-15, 165, len(g["LC10a_L"])))
        pref[g["LC10a_R"]] = -np.radians(np.linspace(-15, 165, len(g["LC10a_R"])))
        # czucie: frakcjonowanie zakresu — różne progi (współczynnik 0,5…4, log)
        sens_k = np.zeros(N)
        for ch in ("fixed", "moving", "palm"):
            sens_k[g["SENS_" + ch]] = np.geomspace(0.5, 4, len(g["SENS_" + ch]))

        nsyn = np.zeros((N, N))         # nsyn[post, pre]
        for pre, post, w in edges:
            nsyn[idx[post], idx[pre]] = w
        # połączenia modelowe odwrócenia odruchu (liczby synaps nasze)
        # frakcjonowanie zakresu: czułe aferenty (niski próg) → wspomaganie
        sens = np.concatenate([g["SENS_fixed"], g["SENS_moving"], g["SENS_palm"]])
        nsyn[np.ix_(g["RR_assist"], sens[sens_k[sens] >= 1.4])] = self.p["syn_palm_assist"]
        # opór tylko z czucia ruchomej szczęki: przypadkowe uderzenie kulki w stałą szczękę nie
        # może gasić uderzenia (w prawdziwym chwycie siły na obu szczękach i tak są równe)
        mov = g["SENS_moving"]
        nsyn[np.ix_(g["RR_resist"], mov[sens_k[mov] < self.p["resist_kmax"]])] = self.p["syn_jaw_resist"]
        close = np.concatenate([g["MN_flex"], g["MN_ltm"]])
        nsyn[np.ix_(close, g["RR_assist"])] = self.p["syn_assist_mn"]
        # opór: mocno wyłącza szybkie i pośrednie MN (przejście uderzenie → trzymanie), słabiej
        # i stopniowo hamuje wolne MN (łagodna regulacja siły trzymania, wzmocnienie pętli ~1)
        for i in close:
            nsyn[i, g["RR_resist"]] = self.p["syn_resist_slow" if mn_class[i] == "slow" else "syn_resist_mn"]
        nsyn[np.ix_(g["RR_assist"], g["RR_assist"])] = self.p["syn_latch"]   # zatrzask chwytu
        # dotyk szczęk wstrzymuje skręt (jak u samca po dotknięciu samicy) — inaczej szum pościgu
        # dociskał serwem bazy szczękę do kulki (~15 N) i opór blokował zamykanie
        for k in ("DNa02_L", "DNa02_R"):
            nsyn[np.ix_(g[k], g["RR_resist"])] = self.p["syn_resist_dn"]
        nsyn[np.ix_(g["RR_assist"], g["RR_resist"])] = self.p["syn_resist_assist"]
        # stan „trzymam”: koincydencja nacisku obu szczęk zatrzaskuje RR_hold → RR_resist
        nsyn[np.ix_(g["RR_hold"], g["SENS_moving"])] = self.p["syn_moving_hold"]
        nsyn[np.ix_(g["RR_hold"], g["SENS_fixed"])] = self.p["syn_moving_hold"]
        nsyn[np.ix_(g["RR_hold"], g["RR_hold"])] = self.p["syn_latch"]
        nsyn[np.ix_(g["RR_resist"], g["RR_hold"])] = self.p["syn_hold_resist"]
        np.fill_diagonal(nsyn, 0)
        b_a = np.full(N, ConnectomeSNN.B_A)
        b_a[g["RR_assist"]] = b_a[g["RR_hold"]] = 0.0   # zatrzaski: bez adaptacji (trwała aktywność)

        bias = np.zeros(N)
        for k in ("AOTU019_L", "AOTU019_R", "AOTU025_L", "AOTU025_R"):
            bias[g[k]] = self.p["bias_aotu"]
        bias[g["DNa02_L"]] = bias[g["DNa02_R"]] = self.p["bias_dna02"]
        for k in ("IN_ACh", "IN_GABA", "IN_Glu"):
            bias[g[k]] = self.p["bias_in"]
        bias[mn_class == "slow"] = self.p["bias_slow"]
        # filtr skurczu per neuron (MN wg klasy; reszta 20 ms — nie wpływa na moment)
        tau = np.array([self.p["tau_twitch"][c] if c else 20.0 for c in mn_class])

        # --- ablacja: zostaw tylko neurony z maski ---
        keep = np.ones(N, bool) if keep is None else np.asarray(keep, bool)
        k = np.where(keep)[0]
        self.neurons = [neurons[i] for i in k]
        self.N = len(k)
        self.groups = make_groups(self.neurons)
        self.mn_class = {j: mn_class[i] for j, i in enumerate(k) if mn_class[i]}
        self.force_per_spike, self.pref, self.sens_k = force[k], pref[k], sens_k[k]
        self.bias, self.a_twitch = bias[k], np.exp(-1.0 / tau[k])
        net = ConnectomeSNN([neurons[i]["nt"] for i in k], gain[k], J0=self.p["J0"], noise=self.p["noise"], seed=seed)
        net.nsyn = nsyn[np.ix_(k, k)]
        net.b_a = b_a[k]
        self.net = net.build()
        if compensate:
            full_g = g
            for pop, ids in self.groups.items():
                if len(ids):
                    f = len(full_g[pop]) / len(ids)
                    self.net.W[:, ids] *= f
                    if pop.startswith("MN_"):
                        self.force_per_spike[ids] *= f
        self.trim = 0.0
        self.reset()
        if self.p["calibrate"]:
            self.calibrate()

    def calibrate(self, iters=6, steps=80):
        """Trym DNa02: cel na wprost (0°) → różnica częstości L−R ≈ 0. Kompensuje asymetrię L/P
        konektomu (np. LC10a_R→AOTU019_R 7595 vs L 6615 synaps), która dawała stały przechył ~7°.
        Gałka kalibracyjna, jak trym w prawdziwym robocie."""
        g = self.groups
        for _ in range(iters):
            self.reset()
            diff = []
            for k in range(steps):
                self.control_step(0.0, (0, 0, 0), True)
                if k >= 30:
                    diff.append(self.rate[g["DNa02_L"]].sum() - self.rate[g["DNa02_R"]].sum())
            self.trim -= 0.08 * np.mean(diff)          # mV na Hz różnicy
            self.bias[g["DNa02_L"]] = self.p["bias_dna02"] + self.trim / 2
            self.bias[g["DNa02_R"]] = self.p["bias_dna02"] - self.trim / 2
        self.reset()

    def reset(self):
        self.net.reset()
        self.rate = np.zeros(self.N)      # spike/s, filtr wykładniczy
        self.twitch = np.zeros(self.N)

    def inputs(self, theta, forces, active, jaw_vel=0.0):
        """theta: azymut celu [rad], + = w lewo (None = brak celu); forces: (stała, ruchoma, dłoń) [N];
        active: stan „polowanie” (True) / „spoczynek” (False); jaw_vel: prędkość szczęki [rad/s],
        − = zamykanie (odpowiednik aferentów prędkości narządu strunowego FeCO → tłumienie)."""
        g, p = self.groups, self.p
        I = self.bias.copy()
        if theta is not None:
            d = np.angle(np.exp(1j * (theta - self.pref)))
            lc = np.concatenate([g["LC10a_L"], g["LC10a_R"]])
            I[lc] += p["vis_amp"] * np.exp(-0.5 * (d[lc] / p["vis_sigma"]) ** 2)
        for ch, f in zip(("fixed", "moving", "palm"), forces):
            ids = g["SENS_" + ch]
            I[ids] += p["sens_gain"] * self.sens_k[ids] * max(f, 0.0)
        I[g["RR_assist"]] += p["state_bias"] if active else -20.0
        I[g["RR_hold"]] += p["state_bias"] - p["hold_offset"] if active else -20.0
        I[g["RR_resist"]] += (0.0 if active else p["state_bias"]) + p["vel_gain"] * max(-jaw_vel, 0.0)
        I[g["MN_ext"]] += p["bias_ext"]               # toniczne napięcie prostownika
        return I

    def control_step(self, theta, forces, active=True, n=10, jaw_vel=0.0):
        """10 kroków SNN po 1 ms. Zwraca (prędkość obrotu bazy [rad/s, + = w lewo],
        moment szczęki [N·m, + = zamykanie], spike'i [n, N])."""
        I = self.inputs(theta, forces, active, jaw_vel)
        spikes = np.zeros((n, self.N), bool)
        a_r = np.exp(-1.0 / self.p["tau_rate"])
        a_t = self.a_twitch
        for k in range(n):
            s = self.net.step(I)
            spikes[k] = s
            self.rate = a_r * self.rate + (1 - a_r) * 1000.0 * s
            self.twitch = a_t * self.twitch + (1 - a_t) * 1000.0 * s
        g = self.groups
        yaw = self.p["k_yaw"] * (self.rate[g["DNa02_L"]].sum() - self.rate[g["DNa02_R"]].sum())
        return yaw, self.muscle(), spikes

    def muscle(self):
        """Moment szczęki [N·m, + = zamykanie] = k_muscle · (Σ siła_klasy · nasycenie(częstość)
        zginaczy i ltm − to samo dla prostowników). Serwo i tak tnie do ±3,35 N·m."""
        g = self.groups
        f = self.force_per_spike * np.tanh(self.twitch / 100.0)   # nasycenie skurczu ~100 spike/s
        close = np.concatenate([g["MN_flex"], g["MN_ltm"]])
        return float(self.p["k_muscle"] * (f[close].sum() - f[g["MN_ext"]].sum()))
