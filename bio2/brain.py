"""Mózg bio2: kompleks centralny (pierścień EPG), neurony zstępujące, looming, HS — ConnectomeSNN (ALIF, dt 1 ms).
Neurony z MaleCNS v1.0 (bio2/circuit_bio2.json, moduły cx/dn/loom/hs). Rdzeń brzuszny (chwyt) jest osobno: vnc.py.

Kompleks centralny (EPG 46, PEN_a 20, PEN_b 22, Delta7 42, PFL3 24):
  * Surowa macierz konektomu daje tylko 2 stabilne położenia wzgórza (zmierzone: ~75° i ~210°), bo kliny
    mają 2–4 EPG, a liczby synaps różnią się między glomerulusami. Dlatego wagi wewnątrz CX pochodzą z
    PROFILI zmierzonych w danych: średnia liczba synaps między parą grup (typ × strona dla PEN) w funkcji
    różnicy kątów w pierścieniu (16 koszyków), a neurony każdej grupy stoją w równych odstępach wzdłuż
    pierścienia w kolejności swoich zmierzonych kątów (EPG: numer klina z danych; reszta: środek
    ciężkości połączeń z EPG). Profile z danych: EPG→EPG ±1 klin, PEN_a/b L→EPG +½ klina, R→EPG −½,
    Delta7→EPG szczyt po przeciwnej stronie (180°).
  * Wagi liniowe (J0 mV na synapsę, jak Shiu 2024) — ln(1+N) spłaszczał kontrast profili i wzgórze nie
    powstawało. Hamowanie Delta7→EPG/PEN ×G_INH, Delta7→Delta7 ×G_DD, bez adaptacji w CX (nasze stałe).
  * Obrót: PEN_L += k·u, PEN_R −= k·u. Zależność prędkości wzgórza od u jest monotoniczna, ale z dryfem
    (asymetria L/P danych) — kalibracja odwraca zmierzoną krzywą (calibrate_ring).
  * Cel dla PFL3 (FC2 w ciele wachlarzowatym — nie ma ich w podzbiorze): prąd ~cos(θ − cel ± 45°) dla PFL3
    L/P — wejście MODELOWE (Westeinde i in. 2024). PFL3_L→DNa02_R i PFL3_R→DNa02_L z danych (380/356 syn.).
Pozostałe moduły: surowe liczby synaps z danych, wagi liniowe J0_RAW. Wejścia modelowe: looming → LC4/LPLC2,
bliskość → MDN, stop → DNp09, ruch obrazu → HS, cel → PFL3, bodziec wzrokowy celu → EPG.
"""
import json
import os

import numpy as np

from snn import ConnectomeSNN

HERE = os.path.dirname(os.path.abspath(__file__))
B = 16

# --- nasze stałe (strojone w symulacji pierścienia, 2026-10-24) ---
P = dict(J0_CX=0.14, G_INH=8.0, G_DD=0.3, J0_RAW=0.15, noise=2.0, rot_gain=2.0, cue_amp=12.0, cue_sigma=0.4,
         goal_amp=6.0, goal_phase=np.radians(45), loom_gain=30.0, mdn_gain=20.0, stop_gain=20.0, hs_gain=10.0,
         bias_dn=5.0, tau_rate=50.0, dna01_frac=0.3)


def _binof(d):
    return np.round(np.angle(np.exp(1j * d)) / (2 * np.pi / B)).astype(int) % B


class Brain:
    def __init__(self, seed=0, params=None):
        self.p = dict(P, **(params or {}))
        c = json.load(open(os.path.join(HERE, "circuit_bio2.json")))
        N = [n for n in c["neurons"] if n["module"] in ("cx", "dn", "loom", "hs")]
        self.neurons, self.N = N, len(N)
        idx = {n["bodyId"]: i for i, n in enumerate(N)}
        NS = np.zeros((self.N, self.N))
        for a, b, w in c["edges"]:
            if a in idx and b in idx:
                NS[idx[b], idx[a]] = w
        np.fill_diagonal(NS, 0)
        ty = np.array([n["type"] for n in N])
        side = np.array([n["side"] for n in N])
        sel = lambda t, s=None: np.where((ty == t) & ((side == s) if s else True))[0]
        g = {"EPG": sel("EPG"), "PEN_a_L": sel("PEN_a(PEN1)", "L"), "PEN_a_R": sel("PEN_a(PEN1)", "R"),
             "PEN_b_L": sel("PEN_b(PEN2)", "L"), "PEN_b_R": sel("PEN_b(PEN2)", "R"), "Delta7": sel("Delta7"),
             "PFL3_L": sel("PFL3", "L"), "PFL3_R": sel("PFL3", "R")}
        for t in ("DNa02", "DNa01", "DNp01", "DNp09", "MDN", "LC4", "LPLC2"):
            for s in "LR":
                g[f"{t}_{s}"] = sel(t, s)
        g["HS_L"] = np.concatenate([sel(t, "L") for t in ("HSN", "HSE", "HSS")])
        g["HS_R"] = np.concatenate([sel(t, "R") for t in ("HSN", "HSE", "HSS")])
        self.groups = g
        cx_groups = ["EPG", "PEN_a_L", "PEN_a_R", "PEN_b_L", "PEN_b_R", "Delta7", "PFL3_L", "PFL3_R"]
        cx = np.concatenate([g[k] for k in cx_groups])

        # kąty w pierścieniu: EPG z klina (dane), pozostałe = środek ciężkości połączeń z EPG
        theta = np.full(self.N, np.nan)
        epg = g["EPG"]
        theta[epg] = np.array([N[i]["wedge"] for i in epg]) * 2 * np.pi / B
        z = (NS[:, epg] + NS[epg, :].T) @ np.exp(1j * theta[epg])
        rest = np.setdiff1d(cx, epg)
        theta[rest] = np.angle(z[rest])
        # profile z danych per para grup
        prof = {}
        for ga in cx_groups:
            for gb in cx_groups:
                pre, post = g[ga], g[gb]
                D = _binof(theta[post][:, None] - theta[pre][None, :])
                M = NS[np.ix_(post, pre)]
                prof[(ga, gb)] = np.array([M[D == k].mean() if (D == k).any() else 0.0 for k in range(B)])
        self.profiles = prof
        # idealna geometria: równe odstępy w kolejności zmierzonych kątów
        th = np.zeros(self.N)
        for k in cx_groups:
            ids = g[k]
            a = np.angle(np.exp(1j * theta[ids]))
            order = ids[np.argsort(a)]
            th[order] = np.angle(np.exp(1j * (a.min() + 2 * np.pi * np.arange(len(ids)) / len(ids))))
        self.theta = th
        W = np.zeros((self.N, self.N))
        for ga in cx_groups:
            for gb in cx_groups:
                pre, post = g[ga], g[gb]
                d = np.angle(np.exp(1j * (th[post][:, None] - th[pre][None, :]))) / (2 * np.pi / B)
                p_, k0 = prof[(ga, gb)], np.floor(d).astype(int)
                f = d - k0
                W[np.ix_(post, pre)] = ((1 - f) * p_[k0 % B] + f * p_[(k0 + 1) % B]) * self.p["J0_CX"]
        np.fill_diagonal(W, 0)
        raw = np.ones((self.N, self.N), bool)
        raw[np.ix_(cx, cx)] = False                       # poza CX: surowe liczby synaps
        W[raw] = NS[raw] * self.p["J0_RAW"]
        net = ConnectomeSNN([n["nt"] for n in N], J0=1.0, noise=self.p["noise"], seed=seed)
        W *= net.sign[None, :]
        ring = np.concatenate([g[k] for k in ("EPG", "PEN_a_L", "PEN_a_R", "PEN_b_L", "PEN_b_R")])
        W[np.ix_(ring, g["Delta7"])] *= self.p["G_INH"]
        W[np.ix_(g["Delta7"], g["Delta7"])] *= self.p["G_DD"]
        # DNa01 (wolne dokręcenie): w danych brak połączeń z tym podzbiorem → MODELOWA kopia ścieżki PFL3→DNa02
        # (krzyżowo, ułamek DNA01_FRAC liczby synaps), odczyt z dłuższym filtrem (tau_rate_dna01)
        for s_pre, s_post in (("L", "R"), ("R", "L")):
            pre, post = g["PFL3_" + s_pre], g["DNa01_" + s_post]
            W[np.ix_(post, pre)] = W[np.ix_(g["DNa02_" + s_post], pre)] * self.p["dna01_frac"]
        net.W = W
        net.b_a[cx] = 0.0
        self.net = net
        self.penL = np.concatenate([g["PEN_a_L"], g["PEN_b_L"]])
        self.penR = np.concatenate([g["PEN_a_R"], g["PEN_b_R"]])
        self.calib = None
        self.reset()

    # ---------------------------------------------------------------- dynamika
    def reset(self):
        self.net.reset()
        self.rate = np.zeros(self.N)

    def inputs(self, cue=None, u=0.0, goal=0.0, loom=(0.0, 0.0), near=0.0, stop=0.0, flow=0.0):
        """cue: kąt celu widzianego [rad] (None = niewidoczny); u: komenda obrotu wzgórza (PEN, przed
        kalibracją); goal: cel PFL3 [rad]; loom: (L, P) siła loomingu z siatkówki; near: bliskość obiektu
        (MDN); stop: zamrożenie (DNp09); flow: ruch obrazu w poziomie [rad/s], + w lewo (HS)."""
        g, p = self.groups, self.p
        I = np.zeros(self.N)
        epg = g["EPG"]
        if cue is not None:
            d = np.angle(np.exp(1j * (self.theta[epg] - cue)))
            I[epg] += p["cue_amp"] * np.exp(-0.5 * (d / p["cue_sigma"]) ** 2)
        I[self.penL] += p["rot_gain"] * u
        I[self.penR] -= p["rot_gain"] * u
        for s, ph in (("L", p["goal_phase"]), ("R", -p["goal_phase"])):
            ids = g["PFL3_" + s]
            I[ids] += p["goal_amp"] * (1 + np.cos(self.theta[ids] - goal + ph))
        for t in ("DNa02", "DNa01", "DNp01", "DNp09", "MDN"):
            I[g[t + "_L"]] += p["bias_dn"]
            I[g[t + "_R"]] += p["bias_dn"]
        for s, lv in zip("LR", loom):
            I[g["LC4_" + s]] += p["loom_gain"] * lv
            I[g["LPLC2_" + s]] += p["loom_gain"] * lv
        I[np.concatenate([g["MDN_L"], g["MDN_R"]])] += p["mdn_gain"] * near
        I[np.concatenate([g["DNp09_L"], g["DNp09_R"]])] += p["stop_gain"] * stop
        I[g["HS_L"]] += p["hs_gain"] * max(flow, 0.0)        # HS: preferencja ruchu w swoją stronę
        I[g["HS_R"]] += p["hs_gain"] * max(-flow, 0.0)
        return I

    def step10(self, **kw):
        """10 kroków po 1 ms ze stałym wejściem. Zwraca spike'i [10, N]."""
        I = self.inputs(**kw)
        a = np.exp(-1.0 / self.p["tau_rate"])
        out = np.zeros((10, self.N), bool)
        for k in range(10):
            s = self.net.step(I)
            out[k] = s
            self.rate = a * self.rate + (1 - a) * 1000.0 * s
        return out

    # ---------------------------------------------------------------- odczyty
    def bump(self, spikes):
        """(kąt [rad], skupienie 0–1, średnia EPG [Hz]) z okna spike'ów [T, N]."""
        epg = self.groups["EPG"]
        r = spikes[:, epg].mean(0)
        z = (r * np.exp(1j * self.theta[epg])).sum()
        return float(np.angle(z)), float(abs(z) / max(r.sum(), 1e-9)), float(r.mean() * 1000)

    def wedges(self, spikes):
        """Aktywność 16 klinów [Hz] (EPG przypisane do najbliższego klina idealnej geometrii)."""
        epg = self.groups["EPG"]
        k = _binof(self.theta[epg])
        r = spikes[:, epg].mean(0) * 1000
        return np.array([r[k == q].mean() if (k == q).any() else 0.0 for q in range(B)])

    def dn_rates(self):
        g = self.groups
        return {k: float(self.rate[g[k]].mean()) for k in g if k.startswith(("DN", "MDN"))}

    # ---------------------------------------------------------------- kalibracja całkowania obrotu
    def calibrate_ring(self, us=(-1.0, -0.75, -0.5, -0.35, -0.25, -0.1, 0.0, 0.25, 0.5, 1.0), seconds=1.5, reps=4):
        """Zmierz prędkość wzgórza [rad/s] dla komend u i zapisz odwrotność (prędkość → u). Odpowiednik
        kalibracji wzmocnienia całkowania ścieżki u muchy. Protokół jak w użyciu: bodziec 0,3 s, zaraz potem
        obrót przez `seconds` (prędkość zależy od siły wzgórza, która słabnie po zniknięciu bodźca).
        Kąty startowe 0°, 90°, 180°, 270°. Po kalibracji reset."""
        v = []
        for u in us:
            vr = []
            for r in range(reps):
                self.reset()
                for _ in range(30):
                    self.step10(cue=2 * np.pi * r / reps)
                a = [self.bump(self.step10())[0]]
                for _ in range(int(seconds * 100)):
                    a.append(self.bump(self.step10(u=u))[0])
                vr.append((np.unwrap(a)[-1] - a[0]) / seconds)
            v.append(np.mean(vr))
        v = np.array(v)
        order = np.argsort(v)
        self.calib = (v[order], np.array(us)[order])
        self.reset()
        return np.array(us), v

    def u_for(self, omega):
        """Komenda u dająca prędkość wzgórza omega [rad/s] (interpolacja kalibracji)."""
        vs, us = self.calib
        return float(np.interp(omega, vs, us))
