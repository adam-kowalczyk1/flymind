"""Etap 5 (bio2) — testy autentyczności: czy zachowanie ramienia wynika z KONKRETNEJ struktury połączeń konektomu,
a nie z dowolnej sieci albo z inżynierii wokół niej (dekodery, kalibracje, stan „polowanie”, wejścia modelowe).

WARUNKI (VNC zawsze pełny i nietknięty; po każdej zmianie mózgu rekalibracja odczytu: calibrate_ring + calibrate_steer
z zabezpieczeniem nachylenia z ablation.LesionedBrain — nachylenie 0/nieskończone → ∞, czyli odczyt skrętu = 0):
  control      kontrola dodatnia: pełny mózg, ten sam kod; ma odtworzyć results/stage4.txt dla 292
  rewire_all   losowe przełączenie krawędzi na całej macierzy mózgu net.W (a→b, c→d ⇒ a→d, c→b; stopnie wejścia/wyjścia
               każdego neuronu zachowane; waga i znak wędrują z neuronem presynaptycznym; bez pętli własnych i duplikatów;
               liczba UDANYCH wymian ≥ 10 × liczba krawędzi)
  rewire_cx    to samo, ale tylko wśród krawędzi wewnątrz CX (EPG/PEN/Delta7/PFL3); krawędzie z/do reszty nietknięte
  shuffle_all  topologia zostaje, wartości wag permutowane losowo między istniejącymi krawędziami TEGO SAMEGO ZNAKU (cała macierz)
  shuffle_cx   to samo tylko wśród krawędzi wewnątrz CX (dodatkowy warunek, odróżnia pierścień od reszty)
  les_*        lezja WSZYSTKICH neuronów typu (obie strony): PFL3; EPG; PEN_a+PEN_b; Delta7; LC4+LPLC2; DNa02+DNa01; HS (HSN+HSE+HSS)
               Wiersze i kolumny zerowane, spike'i maskowane. Martwe neurony ZOSTAJĄ w grupach odczytu (ich częstość = 0 Hz):
               po wycięciu z grup pusta grupa DNa dawałaby NaN (mean z pustej tablicy) w odczycie skrętu i w d.ctrl[0].
Seed próby = seed losowania przetasowania = seed szumu (seedy 0–9). Zamknięta pętla: scenariusze A (pamięć), B1 (ucieczka),
B2 (chwyt) jak w stage4 (świeży mózg+VNC na każdy scenariusz). Otwarta pętla: ablation.ring_trial, 5 ziaren szumu na seed
(10 × 5 = 50 prób na warunek, jak w ablation.py).

PRZEWIDYWANIA (zapisane w results/stage5_predictions.txt PRZED jakimkolwiek pomiarem; poniższa tabela jest sprawdzana w --check
względem słownika PRED, a raport porównuje z nią wyniki). Przedział „lo..hi” = trafione, gdy wynik w nim leży (włącznie).
A<10° = liczba prób z |b| < 10° (z 10); med|b| = mediana |błędu| przy wyłonieniu [°]; B2 = sukcesy chwytu (z 10);
B1 = sukcesy ucieczki (z 10); wzgórze = % z 50 prób otwartej pętli, w których wzgórze EPG istnieje.
  control      A<10°: 4..4  med|b|: 15.8..16°  B2: 8..8  B1: 10..10  wzgórze: 96..100%
  rewire_all   A<10°: 0..1  med|b|: 20..90°  B2: 0..6  B1: 0..2  wzgórze: 0..30%
  rewire_cx    A<10°: 0..1  med|b|: 20..90°  B2: 0..6  B1: 9..10  wzgórze: 0..40%
  shuffle_all  A<10°: 0..1  med|b|: 20..90°  B2: 0..6  B1: 4..10  wzgórze: 0..30%
  shuffle_cx   A<10°: 0..1  med|b|: 20..90°  B2: 0..6  B1: 9..10  wzgórze: 0..30%
  les_PFL3     A<10°: 0..1  med|b|: 20..90°  B2: 0..6  B1: 9..10  wzgórze: 90..100%
  les_EPG      A<10°: 0..1  med|b|: 20..90°  B2: 0..6  B1: 9..10  wzgórze: 0..2%
  les_PEN      A<10°: 0..1  med|b|: 25..90°  B2: 4..9  B1: 9..10  wzgórze: 0..60%
  les_D7       A<10°: 0..1  med|b|: 20..90°  B2: 0..6  B1: 9..10  wzgórze: 0..10%
  les_LOOM     A<10°: 4..4  med|b|: 15.8..16°  B2: 7..9  B1: 0..0  wzgórze: 96..100%
  les_DNa      A<10°: 0..1  med|b|: 15..45°  B2: 4..6  B1: 9..10  wzgórze: 96..100%
  les_HS       A<10°: 2..6  med|b|: 10..25°  B2: 6..10  B1: 9..10  wzgórze: 96..100%
Dodatkowo (przewidywania „identyczne z kontrolą”, bo w macierzy nie ma krawędzi z DN/looming/HS do CX): otwarta pętla
w les_LOOM, les_DNa, les_HS identyczna z kontrolą co do próby; A w les_LOOM identyczne z kontrolą co do próby.
Uzasadnienia per warunek: PRED[...]["why"] i results/stage5_predictions.txt.

Użycie (z bio2, ../.venv/bin/python):
  authenticity.py --check          samotest (bez MuJoCo): rewire, shuffle, lezje, spójność tabeli z PRED
  authenticity.py predictions      zapisuje results/stage5_predictions.txt (raz; odmawia nadpisania)
  authenticity.py one KLUCZ SEED   jedna próba (wszystkie miary) na ekran
  authenticity.py run              wszystkie warunki × seedy 0–9, 3 procesy, wznawialne → results/stage5_raw.jsonl
  authenticity.py report           results/stage5_authenticity.{txt,png}
"""
import datetime
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

from ablation import EXIST_RATE, EXIST_SKUP, LesionedBrain, ring_trial
from brain import Brain
from vnc import FlyController, full_circuit

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
RAW = os.path.join(RES, "stage5_raw.jsonl")
PREDF = os.path.join(RES, "stage5_predictions.txt")
SEEDS = range(10)
K_NOISE = 5                      # ziaren szumu na seed w otwartej pętli (jak w ablation.py)
PROCS = 3
SWAP_MULT = 10                   # liczba udanych wymian ≥ SWAP_MULT × liczba krawędzi
B2_LOCKED = 5                    # B2 z zablokowaną bazą (results/stage3_b2.txt, kontrola: 5/10)

CX_GROUPS = ["EPG", "PEN_a_L", "PEN_a_R", "PEN_b_L", "PEN_b_R", "Delta7", "PFL3_L", "PFL3_R"]
PEN = ("PEN_a(PEN1)", "PEN_b(PEN2)")
# klucz: (etykieta, rodzaj, argument)
COND = {
    "control": ("kontrola (pełny mózg)", "control", None),
    "rewire_all": ("REWIRE cały mózg", "rewire", "all"),
    "rewire_cx": ("REWIRE tylko CX", "rewire", "cx"),
    "shuffle_all": ("WEIGHT-SHUFFLE cały mózg", "shuffle", "all"),
    "shuffle_cx": ("WEIGHT-SHUFFLE tylko CX", "shuffle", "cx"),
    "les_PFL3": ("lezja PFL3", "lesion", ("PFL3",)),
    "les_EPG": ("lezja EPG", "lesion", ("EPG",)),
    "les_PEN": ("lezja PEN_a+PEN_b", "lesion", PEN),
    "les_D7": ("lezja Delta7", "lesion", ("Delta7",)),
    "les_LOOM": ("lezja LC4+LPLC2", "lesion", ("LC4", "LPLC2")),
    "les_DNa": ("lezja DNa02+DNa01", "lesion", ("DNa02", "DNa01")),
    "les_HS": ("lezja HS (HSN+HSE+HSS)", "lesion", ("HSN", "HSE", "HSS")),
}

# --- PRZEWIDYWANIA: (lo, hi) włącznie. A_ok = próby z |b|<10° (z 10), A_med [°], B2 i B1 = sukcesy (z 10), EX = % z 50 ---
_NOSTEER = dict(A_ok=(0, 1), A_med=(20, 90), B2=(0, 6), B1=(9, 10), EX=(0, 30))
PRED = {
    "control": dict(A_ok=(4, 4), A_med=(15.8, 16.0), B2=(8, 8), B1=(10, 10), EX=(96, 100),
                    why="Ten sam kod co stage4 dla 292 (seedy, kolejność RNG, VNC) → odtworzenie wyniku co do próby: A 4/10, mediana 15,9°, B2 8/10, B1 10/10."),
    "rewire_all": dict(_NOSTEER, B1=(0, 2), EX=(0, 30),
                       why="Wagi pierścienia (profile kątowe) lądują na losowych celach, więc brak wzgórza. DNp01 ma ~54 krawędzie wejściowe, a neurony LC4/LPLC2 "
                           "to ~3 % krawędzi wychodzących, więc po przełączeniu dostaje ~1–2 wejścia z looming → ucieczka znika (B1 ≤ 2/10). "
                           "Odczyt skrętu nie ma sygnału kierunku (nachylenie ≈ szum), więc bez celowania: B2 ≈ zablokowana baza lub gorzej."),
    "rewire_cx": dict(_NOSTEER, EX=(0, 40),
                      why="CX jest GĘSTY (69 % par, EPG→EPG 2070/2070), więc przełączenie przy stałych stopniach jest ograniczone i może być słabsze niż się zdaje "
                          "(stąd szeroki EX 0..40 %). Zmienia się jednak przypisanie wag do celów → profil kątowy zaniknie. Szlak looming nietknięty: B1 10/10."),
    "shuffle_all": dict(_NOSTEER, B1=(4, 10), EX=(0, 30),
                        why="Profile kątowe zniszczone → brak wzgórza i celowania. Wagi LC4/LPLC2→DNp01 (średnio ~20 mV) zastąpione losowymi z puli dodatnich "
                            "(średnia ~1,3 mV, ogon do 51): looming słabszy, ale 24 wejścia na DNp01 mogą wystarczyć → B1 niepewne (4..10, spike później)."),
    "shuffle_cx": dict(_NOSTEER, EX=(0, 30),
                       why="Topologia CX (gęsta) zostaje, ginie profil kątowy wag → brak wzgórza; szlak looming nietknięty: B1 10/10."),
    "les_PFL3": dict(_NOSTEER, EX=(90, 100),
                     why="PFL3 to jedyna droga EPG→DNa02/DNa01 (bezpośrednich krawędzi EPG→DN: 0). Pierścień działa (PFL3→EPG sumarycznie ≈ 0 mV), ale DNa02 widzą tylko szum: "
                         "nachylenie dekodera jest skończone, choć losowe (strażnik łapie tylko dokładne 0), więc baza może się wić losowo (nie stać) → B2 ≤ zablokowana baza (≤ 6/10), "
                         "A z dużym błędem."),
    "les_EPG": dict(_NOSTEER, EX=(0, 2),
                    why="Bez EPG nie ma wzgórza ani sygnału do PFL3 → jak PFL3: odczyt skrętu to szum. Wzgórze nie istnieje (0 %)."),
    "les_PEN": dict(A_ok=(0, 1), A_med=(25, 90), B2=(4, 9), B1=(9, 10), EX=(0, 60),
                    why="PEN→EPG jest największym szlakiem dodatnim w CX (3357 mV) — bez PEN wzgórze w pamięci może zaniknąć (EX niepewne). W B2 cel jest stale widoczny i napędza EPG "
                        "wprost, więc B2 ≈ kontrola. W A wzgórze (jeśli trwa) nie jest przesuwane przez −prędkość bazy ani przez przewidywanie celu: ramię skręca dalej do zamrożonego "
                        "kierunku (przestrzał, |b| ≥ 50°) albo, gdy wzgórze gaśnie, jak bez pamięci (~30°). Oba warianty: |b| ≥ 25°, brak sukcesów."),
    "les_D7": dict(_NOSTEER, EX=(0, 10),
                   why="Delta7 to całe hamowanie pierścienia (−4787 na EPG, −8017 na PEN): bez niego EPG/PEN się nasycają, wzgórze rozlane (skupienie < 0,5). PFL3 też traci "
                       "hamowanie → odczyt skrętu bez sygnału kierunku."),
    "les_LOOM": dict(A_ok=(4, 4), A_med=(15.8, 16.0), B2=(7, 9), B1=(0, 0), EX=(96, 100),
                     why="Z LC4/LPLC2 nie wychodzą krawędzie poza looming/DNp01, a do CX żadna. DNp01 dostaje tylko tło 2 mV + szum: brak ucieczki (B1 0/10). "
                         "Reszta bez zmian: otwarta pętla i A identyczne z kontrolą co do próby; B2 ≈ kontrola (±1, bo kontrola mogła mieć fałszywe ucieczki — B2 ich nie raportuje)."),
    "les_DNa": dict(A_ok=(0, 1), A_med=(15, 45), B2=(4, 6), B1=(9, 10), EX=(96, 100),
                    why="Martwe DNa → różnica L−P ≡ 0 → nachylenie 0 → ∞ → odczyt skrętu = 0 dokładnie (jak zablokowana baza, tylko miękka). B2 ≈ 5/10 (zablokowana baza, seedy 1,2,3,6,8), "
                        "A: baza stoi od startu, błąd = azymut piłeczki przy wyłonieniu względem pozy startowej (nie znam pozy, stąd szerokie 15..45°). Pierścień nietknięty."),
    "les_HS": dict(A_ok=(2, 6), A_med=(10, 25), B2=(6, 10), B1=(9, 10), EX=(96, 100),
                   why="HS→DNa02: 6 krawędzi, suma wag 41 mV; HS wygaszone przy własnym obrocie. Niewielki wpływ na tło DNa02, więc wyniki w granicach szumu kontroli."),
}
SHORT = dict(control="kontrola", rewire_all="REWIRE\ncały", rewire_cx="REWIRE\nCX", shuffle_all="SHUFFLE\ncały", shuffle_cx="SHUFFLE\nCX", les_PFL3="PFL3", les_EPG="EPG",
             les_PEN="PEN", les_D7="Delta7", les_LOOM="LC4+\nLPLC2", les_DNa="DNa", les_HS="HS")      # etykiety osi wykresu
SAME = {"les_LOOM": ("ring", "A"), "les_DNa": ("ring",), "les_HS": ("ring",)}     # „identyczne z kontrolą co do próby”
QN = [("A_ok", "A <10° [z 10]"), ("A_med", "med|b| A [°]"), ("B2", "B2 sukces [z 10]"), ("B1", "B1 sukces [z 10]"), ("EX", "wzgórze [% z 50]")]

FACTS = """Fakty o macierzy mózgu (odczyt Brain(seed=0).net.W, bez symulacji), na których oparto przewidywania:
 - 16 823 niezerowych krawędzi w całej macierzy (10 813 dodatnich, 6 010 ujemnych) → 10 × = 168 230 wymian w rewire_all.
 - CX (154 neurony): 16 169 krawędzi z 23 562 możliwych par (69 %), EPG→EPG 2070 z 2070 → topologia CX niesie mało informacji, informację niosą WARTOŚCI wag (profile kątowe z danych).
 - Brak krawędzi z DN, looming i HS do CX; brak bezpośrednich krawędzi EPG→DNa02/DNa01 (jedyna droga: PFL3→DNa02, 24 krawędzie, suma wag 221; DNa01 to modelowa kopia).
 - DNp01 dostaje 24 krawędzie z LC4 (suma 476) i 24 z LPLC2 (355) + 3 inne (DNp01, MDN).
 - Strażnik nachylenia (ablation.LesionedBrain.calibrate_steer) łapie tylko nachylenie DOKŁADNIE 0 (|s| < 1e-9) albo nieskończone; szumowe nachylenie skończone przechodzi i
   daje losowe sterowanie (±W_MAX) zamiast braku skrętu.
 - Ocena „trafione” = wynik w przedziale lo..hi (włącznie); B2 ma 10 prób, więc B2 z zablokowaną bazą (5/10; 24–76 %) i kontrola (8/10; 49–94 %) nie są statystycznie rozdzielne."""


def pred_line(k):
    p = PRED[k]
    return (f"  {k:12s} A<10°: {p['A_ok'][0]}..{p['A_ok'][1]}  med|b|: {p['A_med'][0]:g}..{p['A_med'][1]:g}°  "
            f"B2: {p['B2'][0]}..{p['B2'][1]}  B1: {p['B1'][0]}..{p['B1'][1]}  wzgórze: {p['EX'][0]}..{p['EX'][1]}%")


def pred_text():
    L = ["PRZEWIDYWANIA Etapu 5 (testy autentyczności), przed jakimkolwiek pomiarem.",
         "Skala: A<10° = próby z |b|<10° (z 10); med|b| = mediana |błędu| przy wyłonieniu [°]; B2, B1 = sukcesy (z 10); wzgórze = % z 50 prób otwartej pętli.",
         "Odniesienia z Etapu 3/4: pełny mózg A 4/10 (med 15,9°), none: 0/10 (med 30,5°), B2 8/10, zablokowana baza B2 5/10, B1 10/10.", ""]
    L += [pred_line(k) for k in COND]
    L += ["", "Przewidywania „identyczne z kontrolą co do próby”: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in SAME.items()), "", "UZASADNIENIA"]
    L += [f"  {k}: {PRED[k]['why']}" for k in COND]
    L += ["", FACTS]
    return "\n".join(L)


def write_predictions():
    if os.path.exists(PREDF):
        print("odmowa: results/stage5_predictions.txt już istnieje (przewidywania zapisuje się raz)")
        return
    os.makedirs(RES, exist_ok=True)
    ts = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    open(PREDF, "w").write(f"Zapisano: {ts} (przed jakimkolwiek pomiarem Etapu 5)\n\n" + pred_text() + "\n")
    print("zapisano", PREDF, ts)


# ------------------------------------------------------------------ operacje na macierzy wag (W[post, pre])
def rewire(W, idx, rng, mult=SWAP_MULT, cap=400):
    """Losowe przełączenie krawędzi (degree-preserving) wśród krawędzi W[idx][:, idx]: a→b, c→d ⇒ a→d, c→b.
    Waga (i znak) zostaje przy neuronie presynaptycznym, więc stopnie wejścia/wyjścia i suma wag na neuron presynaptyczny
    są zachowane. Odrzucam wymiany tworzące pętlę własną lub duplikat. Kończy po `mult` × E UDANYCH wymianach."""
    idx = np.asarray(idx)
    n = len(idx)
    sub = W[np.ix_(idx, idx)]
    post, pre = (a.tolist() for a in np.nonzero(sub))
    w = sub[np.nonzero(sub)]
    E = len(w)
    occ0 = {a * n + b for a, b in zip(pre, post)}
    occ = set(occ0)
    target, done, tries = mult * E, 0, 0
    rng_ = np.random.default_rng(rng.integers(2**63))
    while done < target:
        assert tries < cap * E, "rewire: za mało dopuszczalnych wymian"
        for i, j in rng_.integers(0, E, size=(200_000, 2)).tolist():
            tries += 1
            a, b, c, d = pre[i], post[i], pre[j], post[j]
            if a == c or b == d or a == d or c == b:
                continue
            k1, k2 = a * n + d, c * n + b
            if k1 in occ or k2 in occ:
                continue
            occ.difference_update((a * n + b, c * n + d))
            occ.update((k1, k2))
            post[i], post[j] = d, b
            done += 1
            if done >= target:
                break
    out = W.copy()
    out[np.ix_(idx, idx)] = 0.0
    out[idx[np.array(post)], idx[np.array(pre)]] = w
    return out, dict(edges=E, swaps=done, tries=tries, moved=len(occ - occ0) / E)


def shuffle_weights(W, idx, rng):
    """Topologia zostaje; wartości niezerowych wag wśród krawędzi W[idx][:, idx] permutowane losowo osobno wśród dodatnich i ujemnych."""
    idx = np.asarray(idx)
    sub = W[np.ix_(idx, idx)].copy()
    E = int((sub != 0).sum())
    for s in (1.0, -1.0):
        m = s * sub > 0
        sub[m] = rng.permutation(sub[m])
    out = W.copy()
    out[np.ix_(idx, idx)] = sub
    return out, dict(edges=E, moved=float((out != W).sum()) / E)


class AuthBrain(LesionedBrain):
    """Mózg z modyfikacją strukturalną (control/rewire/shuffle/les_*), potem ta sama rekalibracja co w LesionedBrain.
    Dziedziczy calibrate_steer ze strażnikiem nachylenia. Nie woła LesionedBrain.__init__: tamten wycina martwe neurony z grup,
    a pusta grupa DNa daje NaN w odczycie skrętu; tu martwe zostają w grupach (0 Hz), maska spike'ów jak w LesionedBrain."""

    def __init__(self, key, seed=0, calibrate=True):
        Brain.__init__(self, seed=seed)
        _, kind, arg = COND[key]
        g = self.groups
        W = self.net.W
        self.info = {}
        if kind in ("rewire", "shuffle"):
            idx = np.arange(self.N) if arg == "all" else np.sort(np.concatenate([g[k] for k in CX_GROUPS]))
            self.net.W, self.info = (rewire if kind == "rewire" else shuffle_weights)(W, idx, np.random.default_rng(seed))
        dead = np.isin(np.array([n["type"] for n in self.neurons]), arg) if kind == "lesion" else np.zeros(self.N, bool)
        self.alive = ~dead
        self.net.W[dead, :] = 0.0
        self.net.W[:, dead] = 0.0
        self.comp_scale = {}
        step = self.net.step
        self.net.step = lambda I: step(I * self.alive) & self.alive
        if calibrate:
            self.calibrate_ring()
            self.calibrate_steer()


_AV = None


def build(key, seed):
    """(mózg, VNC) — VNC pełny jak w ablation.lesioned_brain(292, seed)."""
    global _AV
    if _AV is None:
        _AV = np.array([x["circuit"] != "track" for x in full_circuit()[0]])
    return AuthBrain(key, seed), FlyController(seed=seed, params=dict(calibrate=False), keep=_AV, compensate=False)


# ------------------------------------------------------------------ samotest
def selfcheck():
    b0 = Brain(seed=0)
    W0 = b0.net.W
    N = b0.N
    cx = np.sort(np.concatenate([b0.groups[k] for k in CX_GROUPS]))
    for line in (pred_line(k) for k in COND):                       # tabela w docstringu = PRED
        assert line.strip() in __doc__, line
    # REWIRE: stopnie wejścia/wyjścia, suma wag na neuron presynaptyczny, brak pętli własnych, liczba udanych wymian
    for name, idx in (("all", np.arange(N)), ("cx", cx)):
        W1, info = rewire(W0, idx, np.random.default_rng(1))
        sub0, sub1 = W0[np.ix_(idx, idx)], W1[np.ix_(idx, idx)]
        assert ((sub0 != 0).sum(1) == (sub1 != 0).sum(1)).all(), "stopnie wejścia"
        assert ((sub0 != 0).sum(0) == (sub1 != 0).sum(0)).all(), "stopnie wyjścia"
        assert np.allclose(sub0.sum(0), sub1.sum(0)), "suma wag na neuron presynaptyczny"
        assert np.allclose(np.sort(np.abs(sub0), 0), np.sort(np.abs(sub1), 0)), "multizbiór wag każdego presynaptycznego"
        assert (np.sign(sub0).sum(0) == np.sign(sub1).sum(0)).all() and not np.diag(W1).any(), "znak / pętle własne"
        assert info["swaps"] >= SWAP_MULT * info["edges"] and (W1 != 0).sum() == (W0 != 0).sum()
        if name == "cx":                                             # poza CX×CX nic się nie zmienia
            m = np.ones((N, N), bool)
            m[np.ix_(idx, idx)] = False
            assert (W0[m] == W1[m]).all()
        print(f"  rewire_{name}: krawędzi {info['edges']}, udanych wymian {info['swaps']} (prób {info['tries']}), "
              f"krawędzi w nowym miejscu {100 * info['moved']:.0f} %")
    # WEIGHT-SHUFFLE: ta sama topologia i multizbiór wag (osobno dodatnich i ujemnych)
    for name, idx in (("all", np.arange(N)), ("cx", cx)):
        W2, info = shuffle_weights(W0, idx, np.random.default_rng(1))
        sub0, sub1 = W0[np.ix_(idx, idx)], W2[np.ix_(idx, idx)]
        assert ((sub0 != 0) == (sub1 != 0)).all(), "topologia"
        assert (np.sign(sub0) == np.sign(sub1)).all(), "znaki krawędzi"
        assert np.array_equal(np.sort(sub0[sub0 != 0]), np.sort(sub1[sub1 != 0])), "multizbiór wag"
        assert info["moved"] > 0.5
        if name == "cx":
            m = np.ones((N, N), bool)
            m[np.ix_(idx, idx)] = False
            assert (W0[m] == W2[m]).all()
        print(f"  shuffle_{name}: krawędzi {info['edges']}, zmienionych wag {100 * info['moved']:.0f} %")
    # kontrola = Brain bez zmian; lezje zerują wiersze i kolumny, grupy odczytu zostają pełne
    bc = AuthBrain("control", 0, calibrate=False)
    assert np.array_equal(bc.net.W, W0) and bc.alive.all()
    n_exp = dict(les_PFL3=24, les_EPG=46, les_PEN=42, les_D7=42, les_LOOM=48, les_DNa=4, les_HS=6)
    for k, ne in n_exp.items():
        b = AuthBrain(k, 0, calibrate=False)
        dead = ~b.alive
        assert dead.sum() == ne, (k, dead.sum())
        assert not b.net.W[dead].any() and not b.net.W[:, dead].any()
        assert {a: len(v) for a, v in b.groups.items()} == {a: len(v) for a, v in b0.groups.items()}
        spk = np.concatenate([b.step10(cue=0.0, u=0.3, loom=(1.0, 1.0)) for _ in range(30)])
        assert not spk[:, dead].any(), "martwy neuron odpalił"
        assert (W0[np.ix_(~dead, ~dead)] == b.net.W[np.ix_(~dead, ~dead)]).all(), "żywe krawędzie zmienione"
    # lezja DNa: odczyt skrętu bez NaN (nachylenie → ∞, przesunięcie skończone)
    b = AuthBrain("les_DNa", 0, calibrate=False)
    st = b.calibrate_steer(angles=(-30.0, 0.0, 30.0), seconds=0.5)
    assert np.isfinite(st["offset"]).all() and np.isinf(st["slope"]).all(), st
    print("self-check OK")


# ------------------------------------------------------------------ pomiar
def task(args):
    """Jeden (warunek, seed): otwarta pętla (5 ziaren szumu) + A (+ A_none dla kontroli) + B1 + B2, każde ze świeżym mózgiem i VNC."""
    key, seed = args
    import agent as agent_mod
    import stage3
    import stage3_b1
    import stage3_b2
    from stage4 import W0, _clean
    t0 = time.time()
    out = dict(cond=key, seed=seed, t_cal=0.0)
    t1 = time.time()
    b = AuthBrain(key, seed)
    out["t_cal"] += time.time() - t1
    out["info"] = _clean(b.info)
    out["n_dead"] = int((~b.alive).sum())
    ring = []
    for k in range(K_NOISE):
        b.net.rng = np.random.default_rng(10_000 + 97 * seed + k)          # jak ablation.worker
        r = _clean(ring_trial(b))
        r["exists"] = bool(r["skup"] > EXIST_SKUP and r["rate"] >= EXIST_RATE)
        ring.append(r)
    out["ring"] = ring

    def run(name, f):
        agent_mod.W_MAX = W0
        t1 = time.time()
        brain, vnc = build(key, seed)
        out["t_cal"] += time.time() - t1
        t1 = time.time()
        try:
            out[name] = _clean(f(brain, vnc))
        except Exception as e:                      # porażka techniczna też trafia do raportu
            out[name] = dict(error=repr(e))
        out[name + "_s"] = time.time() - t1

    run("A", lambda b_, v: stage3.scenario_A(seed, "pred", brain=b_, vnc=v))
    if key == "control":
        run("A_none", lambda b_, v: stage3.scenario_A(seed, "none", brain=b_, vnc=v))
    run("B1", lambda b_, v: stage3_b1.run_trial(("pred", seed, None, False), brain=b_, vnc=v))
    run("B2", lambda b_, v: stage3_b2.run_trial(seed, stage3_b2.P_FINAL, brain=b_, vnc=v))
    agent_mod.W_MAX = W0
    out["t_total"] = time.time() - t0
    return out


def run_all():
    done = set()
    if os.path.exists(RAW):
        done = {(r["cond"], r["seed"]) for r in map(json.loads, open(RAW))}
    tasks = [(k, s) for k in COND for s in SEEDS if (k, s) not in done]
    t0 = time.time()
    with Pool(PROCS, maxtasksperchild=1) as pool, open(RAW, "a") as f:
        for r in pool.imap_unordered(task, tasks):
            f.write(json.dumps(r) + "\n")
            f.flush()
            print(f"[{time.time() - t0:5.0f} s] {r['cond']:12s} seed={r['seed']} A={(r.get('A') or {}).get('err_reappear')} "
                  f"B2={(r.get('B2') or {}).get('cls')} B1={(r.get('B1') or {}).get('ok')} "
                  f"wzgórze={sum(x['exists'] for x in r['ring'])}/{len(r['ring'])}", flush=True)


# ------------------------------------------------------------------ raport
def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (c - h, c + h)


def collect():
    from stage4 import a_stats, b1_stats, b2_stats
    R = [json.loads(l) for l in open(RAW)]
    M = {}
    for k in COND:
        rs = sorted([r for r in R if r["cond"] == k], key=lambda r: r["seed"])
        if not rs:
            continue
        ring = [x for r in rs for x in r["ring"]]
        ex = [x for x in ring if x["exists"]]
        a = a_stats(rs)
        M[k] = dict(rs=rs, n=len(rs), A=a, B2=b2_stats(rs), B1=b1_stats(rs), ring=ring, ex=ex,
                    EX=100 * len(ex) / len(ring), A_ok=a["ok10"], A_med=a["med"], B2n=b2_stats(rs)["ok"], B1n=b1_stats(rs)["ok"],
                    info=[r.get("info") or {} for r in rs])
    return M


def ms(v, f="{:.1f}"):
    v = np.asarray(v, float)
    return "—" if not len(v) else f"{f.format(v.mean())} ± {f.format(v.std())}"


def same_as_control(M, k, what):
    c, x = M["control"], M[k]
    if what == "ring":
        return all(np.allclose([t[q] for t in c["ring"]], [t[q] for t in x["ring"]], rtol=1e-9, atol=1e-9, equal_nan=True)
                   for q in ("skup", "rate", "err_mem", "shift_pos", "shift_neg"))
    if what == "A":
        return np.allclose(c["A"]["e"], x["A"]["e"], atol=1e-6, equal_nan=True)


def report():
    M = collect()
    assert "control" in M, "brak wyników kontroli"
    fresh = open(PREDF).read().split("\n\n", 1)[1].rstrip("\n") == pred_text()
    L = ["Etap 5 — testy autentyczności (struktura konektomu vs dowolna sieć). Seedy 0–9; seed próby = seed przetasowania = seed szumu; VNC pełny.",
         "Po każdej zmianie mózgu: calibrate_ring + calibrate_steer (ze strażnikiem nachylenia). Wszystkie liczby surowe, bez wykluczeń.",
         f"Przewidywania: results/stage5_predictions.txt ({open(PREDF).readline().strip()}); treść zgodna z PRED w kodzie: {'TAK' if fresh else 'NIE (PRZEWIDYWANIA ZMIENIONE PO ZAPISIE!)'}",
         f"Wzgórze istnieje = skupienie > {EXIST_SKUP} i EPG ≥ {EXIST_RATE:.0f} Hz w oknie pamięci (ablation.py). n prób: A/B1/B2 10 na warunek, otwarta pętla 50.", ""]
    L += ["MODYFIKACJE STRUKTURY (średnio po seedach)"]
    for k in COND:
        if k in M and COND[k][1] in ("rewire", "shuffle"):
            i = M[k]["info"]
            L.append(f"  {k:12s} krawędzi {np.mean([x['edges'] for x in i]):.0f}; " + (f"udanych wymian {np.mean([x['swaps'] for x in i]):.0f}; " if "swaps" in i[0] else "")
                     + f"{'krawędzi w nowym miejscu' if 'tries' in i[0] else 'wag zmienionych'} {100 * np.mean([x['moved'] for x in i]):.0f} %")
    A_none = None
    if "A_none" in M["control"]["rs"][0]:
        from stage4 import a_stats
        A_none = a_stats(M["control"]["rs"], "A_none")
    # --- tabela pomiarów ---
    L += ["", "POMIARY (przedział Wilsona 95 % dla A, B2, B1 w nawiasach)",
          f"{'warunek':26s}{'n':>3s}{'A<10°':>8s}{'A<20°':>8s}{'med|b|':>8s}{'śr. b':>8s} {'B2':>6s}{'(95%)':>10s}{'klasy B2':>34s} {'B1':>5s}{'lat0,3m [ms]':>14s}{'wzgórze':>9s}{'err_pam [°]':>13s}{'shift+45':>10s}"]
    for k in COND:
        if k not in M:
            continue
        m = M[k]
        a, b2, b1 = m["A"], m["B2"], m["B1"]
        lo, hi = wilson(b2["ok"], b2["n"])
        cls = ", ".join(f"{c} {v}" for c, v in sorted(b2["cls"].items(), key=lambda kv: -kv[1]))
        L.append(f"{COND[k][0]:26s}{m['n']:>3d}{a['ok10']:>5d}/{a['n']:<2d}{a['ok20']:>5d}/{a['n']:<2d}{a['med']:8.1f}{a['mean']:8.1f} {b2['ok']:>3d}/{b2['n']:<2d}{100 * lo:>4.0f}-{100 * hi:<3.0f}%{cls:>34s} "
                 f"{b1['ok']:>2d}/{b1['n']:<2d}{(f'{np.mean(b1['lat']):.0f}' if b1['lat'] else '—'):>12s}{m['EX']:>8.0f}%{ms([x['err_mem'] for x in m['ex']]):>13s}{ms([x['shift_pos'] for x in m['ex']]):>10s}")
    if A_none:
        L.append(f"{'odniesienie: A none (pełny)':26s}{A_none['n']:>3d}{A_none['ok10']:>5d}/{A_none['n']:<2d}{A_none['ok20']:>5d}/{A_none['n']:<2d}{A_none['med']:8.1f}{A_none['mean']:8.1f}")
    L.append(f"{'odniesienie: B2 zabl. baza':26s}{'':>3s}{'':>32s}{B2_LOCKED:>3d}/10 (results/stage3_b2.txt)")
    # --- przewidywanie vs wynik ---
    L += ["", "PRZEWIDYWANIE vs WYNIK (TRAFIONE = wynik w przedziale lo..hi)"]
    L.append(f"{'warunek':14s}" + "".join(f"{q[1]:>34s}" for q in QN))
    hits = tot = 0
    for k in COND:
        if k not in M:
            continue
        cells = []
        for q, _ in QN:
            lo, hi = PRED[k][q]
            v = M[k][{'B2': 'B2n', 'B1': 'B1n'}.get(q, q)]
            h = bool(np.isfinite(v) and lo <= v <= hi)
            hits += h
            tot += 1
            cells.append(f"{lo:g}..{hi:g} -> {v:.1f}".replace(".0 ", " ") + (" TRAFIONE" if h else " NIETRAFIONE"))
        L.append(f"{k:14s}" + "".join(f"{c:>34s}" for c in cells))
    L.append(f"przedziałowe: trafionych {hits}/{tot}")
    L.append("Przewidywania „identyczne z kontrolą co do próby”:")
    for k, ws in SAME.items():
        for w in ws:
            ok = k in M and same_as_control(M, k, w)
            hits += ok
            tot += 1
            L.append(f"  {k:10s} {w:5s}: {'TRAFIONE (identyczne)' if ok else 'NIETRAFIONE (różne)'}")
    L.append(f"RAZEM trafionych {hits}/{tot}")
    # --- szczegóły ---
    L += ["", "SZCZEGÓŁY — błędy A przy wyłonieniu [°] (seedy 0…9; NaN = brak wyłonienia), uwagi"]
    for k in COND:
        if k in M:
            a = M[k]["A"]
            L.append(f"  {k:12s} {np.round(a['e']).tolist()}  bez wzgórza (bump=0): {a['nobump']}, ucieczki: {a['esc']}, śr.|b| {a['mean_abs']:.1f} ± {a['sd_abs']:.1f}")
    if A_none:
        L.append(f"  {'A none':12s} {np.round(A_none['e']).tolist()}")
    L += ["", "SZCZEGÓŁY — B1 i B2 po seedach"]
    for k in COND:
        if k in M:
            L.append(f"  {k:12s} B1 ok: {''.join('1' if (r.get('B1') or {}).get('ok') else '0' for r in M[k]['rs'])} (spike przed startem: {M[k]['B1']['pre']}, brak spike'a: "
                     f"{sum(not (r.get('B1') or {}).get('esc') and not (r.get('B1') or {}).get('pre') for r in M[k]['rs'])})   "
                     f"B2 ok: {''.join('1' if (r.get('B2') or {}).get('success') else '0' for r in M[k]['rs'])}  zgniecenia {M[k]['B2']['crush']}")
    L += ["", "SZCZEGÓŁY — otwarta pętla (50 prób): skupienie, EPG Hz, błąd pamięci, przesunięcia, poprawny znak obrotu (z wzgórzem)"]
    for k in COND:
        if k in M:
            m = M[k]
            sg = np.mean([(x['shift_pos'] > 0) and (x['shift_neg'] < 0) for x in m['ex']]) * 100 if m['ex'] else float('nan')
            L.append(f"  {k:12s} skupienie {ms([x['skup'] for x in m['ring']], '{:.2f}')}, EPG {ms([x['rate'] for x in m['ring']])} Hz, pamięć {ms([x['err_mem'] for x in m['ex']])}° (n={len(m['ex'])}), "
                     f"+45°/s: {ms([x['shift_pos'] for x in m['ex']])}°, −30°/s: {ms([x['shift_neg'] for x in m['ex']])}°, znak OK {sg:.0f} %")
    errs = [(r["cond"], r["seed"], n, r[n]["error"]) for k in M for r in M[k]["rs"] for n in ("A", "A_none", "B1", "B2") if isinstance(r.get(n), dict) and "error" in r[n]]
    tt = sum(r["t_total"] for k in M for r in M[k]["rs"])
    tc = sum(r["t_cal"] for k in M for r in M[k]["rs"])
    L += ["", f"błędy techniczne scenariuszy: {errs if errs else 'brak'}",
          f"CZAS OBLICZEŃ: {tt:.0f} s CPU (w tym kalibracje {tc:.0f} s), {sum(M[k]['n'] for k in M)} zadań (warunek × seed), {PROCS} procesy"]
    txt = "\n".join(L)
    open(os.path.join(RES, "stage5_authenticity.txt"), "w").write(txt + "\n")
    print(txt)
    plot(M, A_none)


def plot(M, A_none):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
    GC = {"control": "#0b0b0b", "rewire": "#eb6834", "shuffle": "#6250d6", "lesion": "#2a78d6"}
    keys = [k for k in COND if k in M]
    x = np.arange(len(keys))
    col = [GC[COND[k][1]] for k in keys]
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURF, "axes.facecolor": SURF})
    fig, ax = plt.subplots(2, 2, figsize=(15, 9.2))
    ax = ax.ravel()
    ctrl = M["control"]

    def prop(a, key, kn, ref, ref_lab, ylab, title):
        for i, k in enumerate(keys):
            n = M[k]["n"] if kn != "EX" else len(M[k]["ring"])
            kk = M[k][key] if kn != "EX" else len(M[k]["ex"])
            lo, hi = wilson(kk, n)
            a.plot([i, i], [100 * lo, 100 * hi], color=col[i], lw=2.0, solid_capstyle="round")
            a.plot(i, 100 * kk / n, "o", color=col[i], ms=8, mec=SURF, mew=2)
        for v, lab, c, ls in ref:
            a.axhline(v, color=c, ls=ls, lw=1.2)
            a.text(len(keys) - 0.4, v, " " + lab, va="center", ha="left", fontsize=8, color=INK2)
        a.set_ylim(-3, 103); a.set_ylabel(ylab); a.set_title(title, loc="left", color=INK)

    # A: mediana |b| z punktami prób
    a = ax[0]
    for i, k in enumerate(keys):
        e = abs(M[k]["A"]["e"][np.isfinite(M[k]["A"]["e"])])
        a.scatter(i + np.random.default_rng(i).uniform(-0.18, 0.18, len(e)), e, s=14, color=col[i], alpha=0.35, edgecolor="none")
        a.plot(i, M[k]["A"]["med"], "o", color=col[i], ms=8, mec=SURF, mew=2)
    a.axhline(ctrl["A"]["med"], color=INK, ls="--", lw=1.2)
    a.text(len(keys) - 0.4, ctrl["A"]["med"], f" pełny mózg {ctrl['A']['med']:.1f}°", va="center", fontsize=8, color=INK2)
    if A_none:
        a.axhline(A_none["med"], color="#e34948", ls=":", lw=1.4)
        a.text(len(keys) - 0.4, A_none["med"], f" none {A_none['med']:.1f}°", va="center", fontsize=8, color=INK2)
    a.axhline(10, color=INK2, ls=":", lw=0.8)
    a.set_ylabel("|błąd| przy wyłonieniu [°] (punkt = mediana, kropki = próby)"); a.set_title("A. Pamięć przestrzenna: mediana |b|", loc="left", color=INK)
    prop(ax[1], "B2n", "B2", [(100 * ctrl["B2"]["ok"] / ctrl["B2"]["n"], "pełny mózg", INK, "--"), (10 * B2_LOCKED, "zablokowana baza 5/10", "#e34948", ":")],
         "", "% prób (z 10), przedział Wilsona 95 %", "B2. Chwyt: sukces")
    prop(ax[2], "B1n", "B1", [(100 * ctrl["B1"]["ok"] / ctrl["B1"]["n"], "pełny mózg", INK, "--")], "", "% prób (z 10), przedział Wilsona 95 %", "B1. Ucieczka: sukces (spike DNp01 przed 0,10 m)")
    prop(ax[3], "EX", "EX", [(ctrl["EX"], "pełny mózg", INK, "--")], "", "% prób (z 50), przedział Wilsona 95 %", "Otwarta pętla: wzgórze EPG istnieje w pamięci")
    for a in ax:
        a.set_xticks(x, [SHORT[k] for k in keys], fontsize=8)
        a.grid(axis="y", color=GRID); a.set_axisbelow(True); a.set_xlim(-0.6, len(keys) - 0.4)
    for g, c in GC.items():
        ax[0].plot([], [], "o", color=c, label={"control": "kontrola", "rewire": "REWIRE", "shuffle": "WEIGHT-SHUFFLE", "lesion": "lezja typu"}[g])
    ax[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Etap 5 — autentyczność: przełączenie krawędzi, permutacja wag i lezje pojedynczych typów (seedy 0–9, VNC pełny, rekalibracja odczytu)", color=INK)
    fig.tight_layout(rect=(0, 0, 0.93, 0.97))
    fig.savefig(os.path.join(RES, "stage5_authenticity.png"), dpi=110)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--check" in a:
        selfcheck()
    elif a[:1] == ["predictions"]:
        write_predictions()
    elif a[:1] == ["one"]:
        print(task((a[1], int(a[2]))))
    elif a[:1] == ["run"]:
        run_all()
    elif a[:1] == ["report"]:
        report()
    else:
        print(__doc__)
