"""Etap 4 (bio2) — ablacja: mózg + VNC zredukowane do N neuronów łącznie (pełny = 292 = 220 mózg + 72 VNC).

LEZJA, nie kompensacja. Usunięty neuron jest martwy na stałe: jego wiersz i kolumna w macierzy wag są zerami
(nie dostaje i nie wysyła synaps), nie dostaje prądu zewnętrznego (jest wycięty z grup, więc `inputs()` go nie
dotyka) i jego spike'i są maskowane. Wagi pozostałych NIE są skalowane (żadnej homeostazy, reinerwacji, ani
przestrojenia stałych). W VNC użyto istniejącej maski `keep` klasy FlyController (usunięcie wiersza/kolumny =
to samo co wyzerowanie), z `compensate=False`.
JEDYNE co robimy po lezji, to ponowna KALIBRACJA ODCZYTU — `Brain.calibrate_ring` (odwrócona krzywa
prędkość wzgórza → komenda u) i `Brain.calibrate_steer` (trym i nachylenie DNa02/DNa01). To kalibracja
dekodera (jak strojenie przyrządu pomiarowego), nie sieci: bez niej każdy wynik „obrót wzgórza ≠ zadany”
mierzyłby rozjazd skali, nie utratę funkcji. Kalibracja nie dodaje żadnych synaps ani nie zmienia wag.

REGUŁA WYBORU (losowanie warstwowe, `allocation`):
  1. Warstwa (typ funkcjonalny × strona): mózg = (typ komórki, strona L/R) — 30 warstw (EPG, PEN_a, PEN_b,
     Delta7, PFL3, DNa01/02, DNp01, DNp09, MDN, HSN/HSE/HSS, LC4, LPLC2, każdy L i R); VNC = populacje
     z `vnc.make_groups` bez neuronów pościgu (SENS_fixed/moving/palm, IN_ACh/GABA/Glu, RR_assist/resist/hold/and,
     MN_flex/ext/ltm, HP) oraz RR_gate rozbity na szczękę stałą i ruchomą (to dwa osobne kanały wejścia
     bramki AND) — 16 warstw. Razem 46 warstw; VNC jest jednostronny (noga T1-L), więc „strona” to tam jedna.
  2. Podłoga: każda warstwa dostaje ≥ 1 neuron (wymaga N ≥ 46).
  3. Reszta rozdzielona proporcjonalnie do rozmiaru warstwy (water-filling: warstwy z udziałem < 1 dostają 1,
     udział reszty przeliczany od nowa; zaokrąglenie metodą największych reszt, remisy: kolejność warstw).
     Przydział (ile z warstwy zostaje) jest DETERMINISTYCZNY; seed wybiera tylko KTÓRE neurony (rng.choice
     bez zwracania w warstwie). Warstwy 1-neuronowe (DNa01/02, DNp01/09, HSN/HSE/HSS, HP, RR_gate×2) nigdy
     nie są lezjonowane, więc przy N = 50 ablacja dotyczy głównie pierścienia, interneuronów i CX.
  Tabelę „ile zostaje z każdego typu” przy 292/120/50 wypisuje `allocation_table()` (jest w results/).
Kalibracja czytnika ≠ synapsy: nie wolno jej mylić z kompensacją homeostatyczną (której tu NIE ma).

Interfejs zamkniętej pętli: `lesioned_brain(n_total, seed) -> (Brain, vnc_controller)`.
Pomiar otwartej pętli (bez MuJoCo): `python ablation.py` → results/stage4_openloop.txt/.png (3 procesy).
"""
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

from brain import Brain
from vnc import FlyController, full_circuit, make_groups

HERE = os.path.dirname(os.path.abspath(__file__))
LEVELS = (292, 120, 50)          # poziomy docelowe: pełny, 120, 50
N_FULL = 292


# ------------------------------------------------------------------ warstwy i przydział
def strata(brain_neurons, vnc_neurons):
    """Lista warstw (nazwa, krotka indeksów, 'b'|'v'); indeksy w pełnej liście mózgu / pełnej liście VNC."""
    S = {}
    for i, n in enumerate(brain_neurons):
        S.setdefault((f"{n['type']}_{n['side']}", "b"), []).append(i)
    g = make_groups(vnc_neurons)
    for k, ids in g.items():
        if len(ids) == 0 or k.endswith(("_L", "_R")):          # puste = neurony pościgu (nie w bio2)
            continue
        if k == "RR_gate":                                      # [0] = szczęka stała, [1] = ruchoma (jak w vnc.py)
            S[("RR_gate_fixed", "v")], S[("RR_gate_moving", "v")] = [ids[0]], [ids[1]]
        else:
            S[(k, "v")] = list(ids)
    return [(k[0], tuple(v), k[1]) for k, v in S.items()]


def allocation(sizes, n_total):
    """Ile neuronów zostaje w każdej warstwie przy sumie n_total (reguła w docstringu modułu)."""
    sizes = np.asarray(sizes, float)
    assert len(sizes) <= n_total <= sizes.sum(), f"N musi być w [{len(sizes)}, {int(sizes.sum())}]"
    n = np.zeros(len(sizes), int)
    fixed = np.zeros(len(sizes), bool)
    while True:
        f = (n_total - n[fixed].sum()) / sizes[~fixed].sum()
        q = sizes * f
        new = ~fixed & ((q < 1) | (q > sizes))
        if not new.any():
            break
        n[new] = np.where(q[new] < 1, 1, sizes[new]).astype(int)
        fixed |= new
    free = np.where(~fixed)[0]
    base = np.floor(q[free]).astype(int)
    rest = n_total - n[fixed].sum() - base.sum()
    order = np.argsort(-(q[free] - base), kind="stable")        # największe reszty; remis → kolejność warstw
    base[order[:rest]] += 1
    n[free] = base
    assert n.sum() == n_total and (n >= 1).all() and (n <= sizes).all()
    return n


def _setup(brain_neurons):
    vn, _ = full_circuit()
    st = strata(brain_neurons, vn)
    return vn, st


def allocation_table(levels=LEVELS):
    b = Brain(seed=0)
    _, st = _setup(b.neurons)
    sizes = [len(s[1]) for s in st]
    cols = {n: allocation(sizes, n) for n in levels}
    lines = [f"{'warstwa (typ_strona)':24s}" + "".join(f"{n:>6d}" for n in levels) + "   (mózg/VNC)"]
    for i, (name, ids, kind) in enumerate(st):
        lines.append(f"{name:24s}" + "".join(f"{cols[n][i]:>6d}" for n in levels)
                     + f"   z {len(ids)} ({'mózg' if kind == 'b' else 'VNC'})")
    lines.append(f"{'RAZEM':24s}" + "".join(f"{cols[n].sum():>6d}" for n in levels))
    return "\n".join(lines), st, cols


def draw_alive(n_total, seed, brain_neurons=None):
    """Maski żywych neuronów (alive_mózg [220], alive_vnc [pełna lista VNC, 72 bez pościgu + track]) i przydział."""
    if brain_neurons is None:
        brain_neurons = Brain(seed=0).neurons
    vn, st = _setup(brain_neurons)
    n = allocation([len(s[1]) for s in st], n_total)
    rng = np.random.default_rng(seed)
    ab, av = np.zeros(len(brain_neurons), bool), np.array([x["circuit"] != "track" for x in vn])
    for (name, ids, kind), k in zip(st, n):
        keep = rng.choice(np.array(ids), size=k, replace=False)
        if kind == "b":
            ab[keep] = True
        else:
            av[list(ids)] = False
            av[keep] = True
    return ab, av, st, n


# ------------------------------------------------------------------ mózg z lezją
class LesionedBrain(Brain):
    """Brain z trwale martwymi neuronami (maska `alive`). Domyślnie nic nie kompensuje; kalibruje odczyt (calibrate=True).
    compensate=True: skalowanie synaptyczne (wariant 2) — patrz `COMP_CAP` i `_scale_layers`."""

    def __init__(self, alive, seed=0, params=None, calibrate=True, compensate=False):
        super().__init__(seed=seed, params=params)
        self.alive = np.asarray(alive, bool)
        dead = ~self.alive
        self.net.W[dead, :] = 0.0                              # nie dostaje synaps
        self.net.W[:, dead] = 0.0                              # nie wysyła synaps
        self.comp_scale = {}                                   # warstwa → zastosowana skala (tylko compensate=True)
        if compensate:
            self._scale_layers()
        keep = lambda ids: ids[self.alive[ids]]
        self.groups = {k: keep(v) for k, v in self.groups.items()}   # inputs()/odczyty nie widzą martwych
        self.penL, self.penR = keep(self.penL), keep(self.penR)
        step = self.net.step
        self.net.step = lambda I: step(I * self.alive) & self.alive   # brak prądu zewn. i brak spike'ów
        if calibrate:
            self.calibrate_ring()
            self.calibrate_steer()

    def calibrate_steer(self, *a, **kw):
        """Jak Brain.calibrate_steer; jedyna zmiana: nachylenie dekodera DNa (slope, slope_mem) równe 0/nie-skończone
        (martwe wzgórze → regresja L−P na stały kąt) zamieniam na ∞, czyli odczyt skrętu = 0 (dekoder nie niesie informacji).
        Bez tego Agent dzieli przez 0 → NaN w d.ctrl[0], a MuJoCo zeruje wszystkie komendy (ramię skacze do q = 0) — artefakt
        numeryczny, nie skutek lezji. Nie dotyka kalibracji o skończonym (choćby złym) nachyleniu."""
        st = super().calibrate_steer(*a, **kw)
        for k in ("slope", "slope_mem"):
            bad = ~np.isfinite(st[k]) | (np.abs(st[k]) < 1e-9)
            st[k] = np.where(bad, np.inf, st[k])
        return st


    def _scale_layers(self):
        """Skalowanie synaptyczne: wagi WEJŚCIOWE każdego żywego neuronu postsynaptycznego od warstwy presynaptycznej
        (typ × strona) × n_pełne/n_żywe tej warstwy (czyli wagi wychodzące ocalałych z warstwy rosną), by średnie pole
        od warstwy zostało. Limit COMP_CAP. Bez zmian wejść zewnętrznych i parametrów neuronów."""
        lay = {}
        for i, n in enumerate(self.neurons):
            lay.setdefault((n["type"], n["side"]), []).append(i)
        for key, ids in lay.items():
            ids = np.array(ids)
            f = min(len(ids) / self.alive[ids].sum(), COMP_CAP)   # ponytail: limit 10× — jeden ocalały z 23 dałby 23×, co już jest wzmocnieniem, nie homeostazą; tuning limitu gdy trzeba
            self.net.W[:, ids] *= f
            self.comp_scale[key] = (float(f), bool(len(ids) / self.alive[ids].sum() > COMP_CAP))


COMP_CAP = 10.0


def lesioned_brain(n_total, seed=0, calibrate=True, compensate=False, only=None):
    """(Brain, vnc_controller) z n_total neuronami łącznie (292 = pełny), gotowe do Agent(brain=...).
    Brain jest już skalibrowany (calib, steer) → Agent nie wywoła własnych kalibracji. VNC: patrz diff dla agent.py
    w raporcie (Agent musi przyjąć `vnc=`). `seed` = losowanie lezji = ziarno szumu mózgu.
    only="brain"|"vnc": diagnostyka (lezja tylko w jednej części, druga pełna; N łączne wtedy nie obowiązuje).
    compensate=True: mózg — skalowanie warstw (n_pełne/n_żywe, limit COMP_CAP); VNC — istniejące `compensate=True`
    FlyController: wagi wyjściowe ocalałych z populacji × n_pełne/n_żywe (BEZ limitu) oraz siła skurczu ocalałych MN
    × to samo (reinerwacja kolateralna)."""
    ab, av, _, _ = draw_alive(n_total, seed)
    if only == "brain":                         # diagnostyka: lezja tylko w mózgu, VNC pełny
        av = np.array([x["circuit"] != "track" for x in full_circuit()[0]])
    elif only == "vnc":                         # diagnostyka: lezja tylko w VNC, mózg pełny
        ab = np.ones_like(ab)
    brain = LesionedBrain(ab, seed=seed, calibrate=calibrate, compensate=compensate and only != "vnc")
    vnc = FlyController(seed=seed, params=dict(calibrate=False), keep=av, compensate=compensate and only != "brain")
    return brain, vnc


# ------------------------------------------------------------------ pomiar otwartej pętli (protokół stage2_test, B)
PROFILE = [(0.3, None), (1.5, 0.0), (1.0, 45.0), (0.5, 0.0), (1.0, -30.0)]     # cue → pamięć → +45 → spoczynek → −30
C0 = np.radians(60.0)


def ring_trial(b):
    """Jeden przebieg stage2 'ring_run' na gotowym mózgu. Zwraca słownik miar (kąty w stopniach)."""
    b.reset()
    epg = b.groups["EPG"]
    true, est, skup, nspk = [], [], [], []
    ang = C0
    for dur, om in PROFILE:
        for _ in range(int(dur * 100)):
            if om is None:
                s = b.step10(cue=C0)
            else:
                ang += np.radians(om) * 0.01
                s = b.step10(u=b.u_for(np.radians(om)))
            a, sk, _ = b.bump(s)
            true.append(ang); est.append(a); skup.append(sk); nspk.append(s[:, epg].sum())
    est, true, skup, nspk = np.unwrap(est), np.array(true), np.array(skup), np.array(nspk)
    est += np.round((true[29] - est[29]) / (2 * np.pi)) * 2 * np.pi
    err = np.degrees(np.angle(np.exp(1j * (est - true))))
    mem, end = slice(30, 180), slice(150, 180)
    rate = nspk[mem].sum() / (1.5 * len(epg))                  # Hz na neuron EPG w oknie pamięci
    return dict(err_mem=abs(err[179]), skup=skup[mem].mean(), skup_end=skup[end].mean(), rate=rate,
                shift_pos=np.degrees(est[279] - est[179]), shift_neg=np.degrees(est[-1] - est[329]),
                err_end=abs(err[-1]), n_epg=len(epg))


EXIST_SKUP, EXIST_RATE = 0.5, 5.0       # „wzgórze istnieje”: skupienie w pamięci > 0,5 (kryterium stage2) i EPG ≥ 5 Hz


def worker(args):
    n_total, draw, k_noise, comp = args
    seed = 100 * n_total + draw                   # to samo losowanie lezji dla obu wariantów (para)
    ab, av, _, _ = draw_alive(n_total, seed)
    b = LesionedBrain(ab, seed=seed, compensate=comp)
    out = []
    for k in range(k_noise):
        b.net.rng = np.random.default_rng(10_000 + 97 * seed + k)
        r = ring_trial(b)
        r.update(level=n_total, comp=comp, draw=draw, noise=k, n_alive=int(ab.sum() + av.sum()),
                 n_pen=len(b.penL) + len(b.penR), n_d7=len(b.groups["Delta7"]))
        r["exists"] = bool(r["skup"] > EXIST_SKUP and r["rate"] >= EXIST_RATE)
        r["exists_end"] = bool(r["skup_end"] > EXIST_SKUP and r["rate"] >= EXIST_RATE)
        out.append(r)
    return out


def ms(x):
    x = np.asarray(x, float)
    return f"{x.mean():6.1f} ± {x.std():5.1f}" if len(x) else "   —  "


def report(R, table_txt, n_draw, k_noise, comp=False):
    L = [f"Etap 4, pomiar otwartej pętli (bez MuJoCo). {n_draw} losowań lezji × {k_noise} ziaren szumu na poziom; "
         "protokół stage2_test B: cue 0,3 s (60°) → ciemność 1,5 s → +45°/s 1 s → 0,5 s → −30°/s 1 s.",
         ("WARIANT 2: lezja + skalowanie synaptyczne warstw (× n_pełne/n_żywe, limit 10×)" if comp else
          "WARIANT 1: lezja trwała, BEZ kompensacji") + "; po lezji ponownie calibrate_ring + calibrate_steer (kalibracja dekodera).",
         f"„Wzgórze istnieje” = skupienie (średnia z okien 10 ms, jak stage2) > {EXIST_SKUP} ORAZ EPG ≥ {EXIST_RATE:.0f} Hz "
         "w oknie pamięci. Błąd = |kąt wzgórza − całka prawdy| [°]; przy braku wzgórza kąt jest niezdefiniowany, więc "
         "podaję błąd (a) tylko dla prób, gdzie wzgórze istnieje i (b) „efektywny” = 90° (poziom losowy) dla pozostałych.",
         "Średnia ± SD po wszystkich próbach (losowania × ziarna); w nawiasie liczba prób.", "",
         *(["Ile neuronów zostaje z każdej warstwy:", table_txt, ""] if table_txt else [])]
    hdr = f"{'miara':58s}" + "".join(f"{('pełny' if n == 292 else n):>20}" for n in LEVELS)
    rows = {n: [r for r in R if r["level"] == n] for n in LEVELS}
    ex = {n: [r for r in rows[n] if r["exists"]] for n in LEVELS}
    L.append(hdr)
    def line(name, f):
        L.append(f"{name:58s}" + "".join(f"{f(n):>20s}" for n in LEVELS))
    line("neuronów łącznie (mózg+VNC)", lambda n: str(rows[n][0]["n_alive"]))
    line("EPG / PEN / Delta7 (żywe, średnio)",
         lambda n: f"{np.mean([r['n_epg'] for r in rows[n]]):.0f}/{np.mean([r['n_pen'] for r in rows[n]]):.0f}/{np.mean([r['n_d7'] for r in rows[n]]):.0f}")
    line("wzgórze istnieje w pamięci [% prób]", lambda n: f"{100 * np.mean([r['exists'] for r in rows[n]]):.0f} ({len(ex[n])}/{len(rows[n])})")
    line("wzgórze istnieje jeszcze w ostatnich 0,3 s [% prób]", lambda n: f"{100 * np.mean([r['exists_end'] for r in rows[n]]):.0f}")
    line("skupienie wzgórza w pamięci (wszystkie próby)", lambda n: ms([r["skup"] for r in rows[n]]))
    line("EPG w pamięci [Hz/neuron] (wszystkie próby)", lambda n: ms([r["rate"] for r in rows[n]]))
    line("błąd pamięci 1,5 s [°], próby z wzgórzem", lambda n: ms([r["err_mem"] for r in ex[n]]) + f" ({len(ex[n])})")
    line("błąd pamięci 1,5 s [°], efektywny (brak = 90°)",
         lambda n: ms([r["err_mem"] if r["exists"] else 90.0 for r in rows[n]]))
    line("przesunięcie przy +45°/s × 1 s [°] (cel +45), z wzgórzem", lambda n: ms([r["shift_pos"] for r in ex[n]]))
    line("przesunięcie przy −30°/s × 1 s [°] (cel −30), z wzgórzem", lambda n: ms([r["shift_neg"] for r in ex[n]]))
    line("|błąd| całkowania obrotu: |przesunięcie − cel| (+45) [°]", lambda n: ms([abs(r["shift_pos"] - 45) for r in ex[n]]))
    line("|błąd| całkowania obrotu: |przesunięcie − cel| (−30) [°]", lambda n: ms([abs(r["shift_neg"] + 30) for r in ex[n]]))
    line("poprawny znak obrotu (+45 → >0 i −30 → <0) [% prób z wzgórzem]",
         lambda n: f"{100 * np.mean([(r['shift_pos'] > 0) and (r['shift_neg'] < 0) for r in ex[n]]) if ex[n] else float('nan'):.0f}")
    line("|błąd| na końcu (po całym protokole) [°], z wzgórzem", lambda n: ms([r["err_end"] for r in ex[n]]))
    L += ["", "Rozrzut między losowaniami lezji (SD średnich z losowań; w losowaniach, gdzie wzgórze istnieje wszędzie obliczone z prób z wzgórzem):"]
    for n in LEVELS:
        per = [np.mean([r["err_mem"] for r in rows[n] if r["draw"] == d and r["exists"]]) for d in range(n_draw)
               if any(r["draw"] == d and r["exists"] for r in rows[n])]
        pe = [np.mean([r["exists"] for r in rows[n] if r["draw"] == d]) for d in range(n_draw)]
        L.append(f"  N={n}: błąd pamięci — średnie z losowań {ms(per)} (losowań z wzgórzem: {len(per)}/{n_draw}); "
                 f"odsetek istnienia na losowanie {ms(100 * np.array(pe))} %")
    return "\n".join(L)


SWEEP = (270, 250, 230, 210, 190, 160, 90, 70)       # poziomy pośrednie: gdzie pierścień się załamuje


def sweep_report(R):
    L = ["", "Poziomy pośrednie i krzywa degradacji (10 losowań × 3 ziarna; 292/120/50: × 5 ziaren)", f"{'N':>5s}{'istnieje %':>12s}{'skupienie':>12s}"
         f"{'EPG Hz':>10s}{'EPG żywych':>12s}{'błąd pamięci [°] (z wzgórzem)':>34s}"]
    for n in sorted({r["level"] for r in R}, reverse=True):
        rs = [r for r in R if r["level"] == n]
        ex = [r["err_mem"] for r in rs if r["exists"]]
        L.append(f"{n:5d}{100 * np.mean([r['exists'] for r in rs]):12.0f}{np.mean([r['skup'] for r in rs]):12.2f}"
                 f"{np.mean([r['rate'] for r in rs]):10.1f}{np.mean([r['n_epg'] for r in rs]):12.0f}{ms(ex):>30s} ({len(ex)})")
    return "\n".join(L)


def plot(R, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    INK, GRID = "#0b0b0b", "#e4e3df"
    VAR = {False: ("#2a78d6", "o-", "bez kompensacji"), True: ("#eb6834", "s--", "skalowanie synaptyczne (limit 10×)")}
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(1, 4, figsize=(17, 4.4))
    for a in ax[:3]:
        a.set_xlabel("neuronów łącznie (mózg + VNC)"); a.grid(color=GRID); a.invert_xaxis()
        for n in LEVELS:
            a.axvline(n, color="#52514e", lw=0.6, ls=":")
    for comp, (c, mk, lab) in VAR.items():
        Rc = [r for r in R if r["comp"] == comp]
        Ns = sorted({r["level"] for r in Rc}, reverse=True)
        rows = {n: [r for r in Rc if r["level"] == n] for n in Ns}
        off = 1.5 if comp else -1.5
        ax[0].plot(Ns, [100 * np.mean([r["exists"] for r in rows[n]]) for n in Ns], mk, color=c, label=lab)
        for a, key in ((ax[1], "err_mem"), (ax[2], "shift_pos")):
            xs = [n for n in Ns if any(r["exists"] for r in rows[n])]
            if xs:
                a.errorbar(np.array(xs) + off, [np.mean([r[key] for r in rows[n] if r["exists"]]) for n in xs],
                           [np.std([r[key] for r in rows[n] if r["exists"]]) for n in xs], fmt=mk, color=c, capsize=3, label=lab)
        ax[3].scatter([r["n_epg"] + (0.15 if comp else -0.15) for r in Rc], [r["skup"] for r in Rc], s=10, alpha=0.4, color=c, label=lab)
    ax[0].set_ylabel("% prób z wzgórzem"); ax[0].set_title("Wzgórze istnieje (okno pamięci)", color=INK); ax[0].legend(frameon=False)
    ax[1].axhline(90, color="#e34948", ls="--", lw=1); ax[1].text(ax[1].get_xlim()[0], 91, "poziom losowy 90°", color="#e34948", fontsize=8)
    ax[1].set_ylim(0, 100); ax[1].set_title("Błąd pamięci 1,5 s [°] (próby z wzgórzem)", color=INK, fontsize=9)
    ax[2].axhline(45, color="#e34948", ls="--", lw=1); ax[2].set_title("Przesunięcie przy +45°/s × 1 s [°] (z wzgórzem)", color=INK, fontsize=9)
    ax[3].axhline(EXIST_SKUP, color="#52514e", ls=":", lw=1)
    ax[3].set_xlabel("żywych EPG"); ax[3].set_ylabel("skupienie w pamięci"); ax[3].legend(frameon=False, fontsize=8)
    ax[3].set_title("Skupienie wzgórza a liczba żywych EPG", color=INK)
    fig.suptitle("Etap 4 — ablacja (otwarta pętla): lezja trwała, bez i z kompensacją synaptyczną; kalibracja odczytu po lezji", color=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=110)


def selfcheck():
    b0 = Brain(seed=0)
    v0, _ = full_circuit()
    # pełny: tyle neuronów, co Brain i pełny VNC
    br, vn = lesioned_brain(N_FULL, 0, calibrate=False)
    assert br.N == b0.N == 220 and br.alive.all() and vn.N == 72 and br.N + vn.N == N_FULL
    # N = 50 (i 120): dokładnie tyle aktywnych, każdy typ ≥ 1, martwi niemi
    for n in (50, 120):
        ab, av, st, al = draw_alive(n, 3)
        br, vn = lesioned_brain(n, 3, calibrate=False)
        assert int(br.alive.sum()) + vn.N == n == ab.sum() + av.sum()
        assert all(len(v) for v in br.groups.values())
        assert all(len(v) for k, v in vn.groups.items() if not k.endswith(("_L", "_R")))     # (_L/_R = pościg, puste w bio2)
        assert (al >= 1).all() and al.sum() == n
        for name, ids, kind in st:                                  # każdy typ ma ≥1 żywy neuron
            assert (ab[list(ids)] if kind == "b" else av[list(ids)]).sum() >= 1, name
        dead = ~br.alive
        assert not br.net.W[dead].any() and not br.net.W[:, dead].any()
        spk = np.concatenate([br.step10(cue=0.0, u=0.3) for _ in range(30)])
        assert not spk[:, dead].any(), "martwy neuron odpalił"
    # ta sama liczność niezależnie od seeda, wybór zależny od seeda
    a1, a2 = draw_alive(50, 1)[0], draw_alive(50, 2)[0]
    assert (a1 != a2).any() and a1.sum() == a2.sum()
    # compensate=True: skala = min(n_pełne/n_żywe, 10) dokładnie; średnie pole zachowane w populacji
    ab = draw_alive(120, 3)[0]
    bl, bc = LesionedBrain(ab, 3, calibrate=False), LesionedBrain(ab, 3, calibrate=False, compensate=True)
    lay = {}
    for i, x in enumerate(bc.neurons):
        lay.setdefault((x["type"], x["side"]), []).append(i)
    epg = [i for i in lay[("EPG", "L")] + lay[("EPG", "R")] if ab[i]]
    for key, ids in lay.items():
        f = min(len(ids) / ab[ids].sum(), COMP_CAP)
        assert np.allclose(bc.net.W[np.ix_(epg, ids)], bl.net.W[np.ix_(epg, ids)] * f), key
        assert bc.comp_scale[key][0] == f
    # Pojedynczy neuron NIE odtwarza pełnej sumy (zależy, które presynaptyczne przeżyły: mediana |odch.| ~40 % przy 120),
    # ale suma po WSZYSTKICH żywych EPG od warstwy EPG_L (nie przyciętej) wraca do pełnej w < 2 % (średnie pole).
    Wf, ids = Brain(0).net.W, lay[("EPG", "L")]
    assert not bc.comp_scale[("EPG", "L")][1]
    dev = bc.net.W[np.ix_(epg, ids)].sum() / Wf[np.ix_(epg, ids)].sum() - 1
    assert abs(dev) < 0.02, dev
    # N=50: limit skali zadziałał tam, gdzie n_pełne/n_żywe > 10
    b5 = LesionedBrain(draw_alive(50, 3)[0], 3, calibrate=False, compensate=True)
    assert max(v[0] for v in b5.comp_scale.values()) <= COMP_CAP and any(v[1] for v in b5.comp_scale.values())
    assert lesioned_brain(50, 3, calibrate=False, compensate=True)[1].N == lesioned_brain(50, 3, calibrate=False)[1].N
    print("self-check OK")


def main():
    k_noise, n_draw = 5, 10
    table, _, _ = allocation_table()
    R = []
    for comp in (False, True):                  # kolejno, każdy wariant na 3 procesach
        tasks = [(n, d, k_noise, comp) for n in LEVELS for d in range(n_draw)] + \
                [(n, d, 3, comp) for n in SWEEP for d in range(n_draw)]
        with Pool(int(os.environ.get("ABL_PROCS", 3))) as pool:
            R += [r for out in pool.imap_unordered(worker, tasks) for r in out]
    txt = []
    for comp in (False, True):
        Rc = [r for r in R if r["comp"] == comp]
        txt += [report([r for r in Rc if r["level"] in LEVELS], table if not comp else "", n_draw, k_noise, comp),
                sweep_report(Rc), "", "=" * 100, ""]
    txt = "\n".join(txt)
    print(txt)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "stage4_openloop.txt"), "w").write(txt + "\n")
    json.dump([{k: (v.item() if hasattr(v, "item") else v) for k, v in r.items()} for r in R],
              open(os.path.join(HERE, "results", "stage4_openloop.json"), "w"))
    plot(R, os.path.join(HERE, "results", "stage4_openloop.png"))
    return 0


if __name__ == "__main__":
    selfcheck()
    if "--check" not in sys.argv:
        sys.exit(main())
