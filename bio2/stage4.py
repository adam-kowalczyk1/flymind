"""Etap 4 (bio2) — ablacja w zamkniętej pętli: mózg + VNC zredukowane do 292 / 120 / 50 neuronów (ablation.py),
dwa warianty: bez kompensacji i ze skalowaniem synaptycznym; seedy 0–9 (seed próby = losowanie lezji = ziarno szumu).
Parametry sceny i agenta ZAMROŻONE (Etap 3); niczego nie strojono.
  A  pamięć przestrzenna: stage3.scenario_A(seed, "pred"), miara: błąd przy wyłonieniu [°]; odniesienie "none" (pełna sieć);
  B2 chwyt: stage3_b2.run_trial (P_FINAL, W_MAX 0,6): sukces, zgniecenie (20 ms), klasy porażek, reakcja (i);
  B1 ucieczka: stage3_b1.run_trial("pred"): sukces, opóźnienie od 0,30 m.
Poziom 292 = pełny układ (skala wag = 1, więc oba warianty są tam identyczne — liczony raz, wyniki w obu kolumnach).
Każdy scenariusz dostaje świeży mózg+VNC (ta sama lezja i ziarno, kalibracja od nowa) jak w Etapie 3.
Użycie: python stage4.py run   (3 procesy, wznawialne: results/stage4_closed.jsonl)  |  python stage4.py report
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

import agent as agent_mod
from ablation import lesioned_brain

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
RAW = os.path.join(RES, "stage4_closed.jsonl")
W0 = agent_mod.W_MAX                      # domyślne W_MAX agenta (B2 ustawia 0,6 globalnie w procesie)
SEEDS = range(10)
LEVELS = (292, 120, 50)


def _clean(x):
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items() if not isinstance(v, np.ndarray)}
    if isinstance(x, (np.floating, float)):
        return None if not np.isfinite(x) else float(x)
    if isinstance(x, (np.integer, np.bool_)):
        return x.item()
    return x


def task(args):
    """Jeden (poziom, wariant, seed): KAŻDY scenariusz dostaje świeży mózg+VNC (to samo losowanie lezji i ziarno szumu =
    seed, kalibracja od nowa) — tak jak w Etapie 3 (tam świeży Agent/Brain na próbę), więc poziom 292 odtwarza Etap 3."""
    level, comp, seed = args
    import stage3
    import stage3_b1
    import stage3_b2
    t0 = time.time()
    out = dict(level=level, comp=comp, seed=seed, t_cal=0.0)

    def run(key, f):
        agent_mod.W_MAX = W0
        t1 = time.time()
        brain, vnc = lesioned_brain(level, seed, compensate=comp)
        out["t_cal"] += time.time() - t1
        out["n_alive"] = int(brain.alive.sum() + vnc.N)
        t1 = time.time()
        try:
            out[key] = _clean(f(brain, vnc))
        except Exception as e:                       # porażka techniczna też trafia do raportu
            out[key] = dict(error=repr(e))
        out[key + "_s"] = time.time() - t1

    run("A", lambda b, v: stage3.scenario_A(seed, "pred", brain=b, vnc=v))
    if level == LEVELS[0] and not comp:
        run("A_none", lambda b, v: stage3.scenario_A(seed, "none", brain=b, vnc=v))
    run("B1", lambda b, v: stage3_b1.run_trial(("pred", seed, None, False), brain=b, vnc=v))
    run("B2", lambda b, v: stage3_b2.run_trial(seed, stage3_b2.P_FINAL, brain=b, vnc=v))
    agent_mod.W_MAX = W0
    out["t_total"] = time.time() - t0
    return out


def task_b2(args):
    """Tylko B2 dla (poziom, wariant, seed) — jak w task(): świeży mózg+VNC z tą samą lezją i ziarnem."""
    level, comp, seed = args
    import stage3_b2
    t0 = time.time()
    agent_mod.W_MAX = W0
    brain, vnc = lesioned_brain(level, seed, compensate=comp)
    try:
        r = _clean(stage3_b2.run_trial(seed, stage3_b2.P_FINAL, brain=brain, vnc=vnc))
    except Exception as e:
        r = dict(error=repr(e))
    agent_mod.W_MAX = W0
    return dict(level=level, comp=comp, seed=seed, B2=r, B2_s=time.time() - t0)


def rerun_b2(procs=3):
    """Przelicza wyłącznie wiersze B2 w stage4_closed.jsonl (nowa miara reakcji (i)); A i B1 bez zmian. Wypisuje, czy
    pozostałe pola B2 (poza t_detect/t_move/react_move_ms/t_vis) zgadzają się ze starym zapisem."""
    R = [json.loads(l) for l in open(RAW)]
    with Pool(procs, maxtasksperchild=1) as pool:
        new = {(r["level"], r["comp"], r["seed"]): r for r in pool.imap_unordered(task_b2, [(r["level"], r["comp"], r["seed"]) for r in R])}
    skip = {"t_detect", "t_move", "react_move_ms", "t_vis"}
    diff = 0
    for r in R:
        n = new[(r["level"], r["comp"], r["seed"])]
        old = r.get("B2") or {}
        diff += sum(1 for k, v in (n["B2"] or {}).items() if k not in skip and old.get(k) != v)
        r["B2"], r["B2_s"] = n["B2"], n["B2_s"]
    with open(RAW, "w") as f:
        for r in R:
            f.write(json.dumps(r) + "\n")
    print(f"B2 przeliczone dla {len(R)} prób; różnice w pozostałych polach B2: {diff}")


PARTS = os.path.join(RES, "stage4_parts.jsonl")


def task_part(args):
    """Diagnostyka rozbicia B2: ta sama lezja, ale tylko w mózgu (VNC pełny) albo tylko w VNC (mózg pełny)."""
    level, comp, seed, part = args
    import stage3_b2
    agent_mod.W_MAX = W0
    t0 = time.time()
    brain, vnc = lesioned_brain(level, seed, compensate=comp, only=part)
    try:
        r = _clean(stage3_b2.run_trial(seed, stage3_b2.P_FINAL, brain=brain, vnc=vnc))
    except Exception as e:
        r = dict(error=repr(e))
    agent_mod.W_MAX = W0
    return dict(level=level, comp=comp, seed=seed, part=part, B2=r, t=time.time() - t0)


def run_parts(procs=3):
    done = set()
    if os.path.exists(PARTS):
        done = {(r["level"], r["comp"], r["seed"], r["part"]) for r in map(json.loads, open(PARTS))}
    tasks = [(n, c, s, p) for n in LEVELS[1:] for c in (False, True) for p in ("brain", "vnc") for s in SEEDS]
    tasks = [t for t in tasks if t not in done]
    t0 = time.time()
    with Pool(procs, maxtasksperchild=1) as pool, open(PARTS, "a") as f:
        for r in pool.imap_unordered(task_part, tasks):
            f.write(json.dumps(r) + "\n")
            f.flush()
            print(f"[{time.time() - t0:5.0f} s] parts N={r['level']} comp={r['comp']} {r['part']} seed={r['seed']} {r['B2'].get('cls')}", flush=True)


def run_all(procs=3):
    done = set()
    if os.path.exists(RAW):
        for l in open(RAW):
            r = json.loads(l)
            done.add((r["level"], r["comp"], r["seed"]))
    tasks = [(292, False, s) for s in SEEDS] + [(n, c, s) for n in LEVELS[1:] for c in (False, True) for s in SEEDS]
    tasks = [t for t in tasks if t not in done]
    t0 = time.time()
    with Pool(procs, maxtasksperchild=1) as pool, open(RAW, "a") as f:
        for r in pool.imap_unordered(task, tasks):
            f.write(json.dumps(r) + "\n")
            f.flush()
            print(f"[{time.time() - t0:5.0f} s] N={r['level']} comp={r['comp']} seed={r['seed']} "
                  f"A={r.get('A', {}).get('err_reappear')} B2={r.get('B2', {}).get('cls')} B1={r.get('B1', {}).get('ok')}", flush=True)


# ------------------------------------------------------------------ raport
def load():
    R = [json.loads(l) for l in open(RAW)]
    for r in R:
        r["wall"] = r.get("t_total", 0.0)
    return R


def cond(R, level, comp):
    """Próby dla (poziom, wariant); poziom 292 = ten sam zestaw w obu wariantach."""
    return sorted([r for r in R if r["level"] == level and (r["comp"] == comp or level == 292)], key=lambda r: r["seed"])


def a_stats(rs, key="A"):
    e = np.array([np.nan if (r.get(key) or {}).get("err_reappear") is None else r[key]["err_reappear"] for r in rs], float)
    n = len(rs)
    fin = e[np.isfinite(e)]
    return dict(n=n, nfin=len(fin), e=e, ok10=int((abs(fin) < 10).sum()), ok20=int((abs(fin) < 20).sum()),
                med=float(np.median(abs(fin))) if len(fin) else np.nan, mean_abs=float(abs(fin).mean()) if len(fin) else np.nan,
                sd_abs=float(abs(fin).std()) if len(fin) else np.nan, mean=float(fin.mean()) if len(fin) else np.nan,
                esc=sum(bool((r.get(key) or {}).get("escapes")) for r in rs),
                nobump=sum((r.get(key) or {}).get("bump_reappear") == 0.0 for r in rs),     # kąt dokładnie 0 = brak spike'ów EPG (martwe wzgórze)
                ring=[(r.get(key) or {}).get("err_ring") for r in rs])


def b2_stats(rs):
    b = [r.get("B2") or {} for r in rs]
    cls = {}
    for x in b:
        cls[x.get("cls", "błąd techniczny")] = cls.get(x.get("cls", "błąd techniczny"), 0) + 1
    mv = [x["react_move_ms"] for x in b if x.get("react_move_ms") is not None]
    return dict(n=len(rs), ok=sum(bool(x.get("success")) for x in b), crush=sum(bool(x.get("crushed")) for x in b),
                crush_inst=sum((x.get("peak") or 0) > 5.0 for x in b), cls=cls, mv=mv,
                grip=[x["react_grip_ms"] for x in b if x.get("react_grip_ms") is not None],
                touched=sum(x.get("cls") != "chybienie" and "cls" in x for x in b))


def b1_stats(rs):
    b = [r.get("B1") or {} for r in rs]
    lat = [x["lat30"] for x in b if x.get("ok") and x.get("lat30") is not None]
    return dict(n=len(rs), ok=sum(bool(x.get("ok")) for x in b), pre=sum(bool(x.get("pre")) for x in b),
                esc=sum(bool(x.get("esc")) for x in b), lat=lat, err=sum("error" in x for x in b))


def ms(v, f="{:.0f}"):
    v = np.asarray(v, float)
    return "—" if not len(v) else f"{f.format(v.mean())} ± {f.format(v.std())} (n={len(v)})"


def report():
    R = load()
    L = ["Etap 4 — ablacja w ZAMKNIĘTEJ pętli (MuJoCo), seedy 0–9; parametry Etapu 3 zamrożone, nic nie strojone.",
         "Seed próby = losowanie lezji = ziarno szumu. 292 = pełny układ (oba warianty identyczne, liczone raz). Wszystkie liczby surowe (bez wykluczeń):",
         "próba, w której piłeczka nie wyszła zza przesłony lub scenariusz zgłosił błąd techniczny, liczy się jako porażka.", ""]
    none = a_stats(cond(R, 292, False), "A_none")
    full = a_stats(cond(R, 292, False))
    L += ["A. PAMIĘĆ PRZESTRZENNA (błąd azymutu przy wyłonieniu zza przesłony, [°]; sukces |błąd| < 10°)",
          f"{'N / wariant':26s}{'|b|<10°':>9s}{'|b|<20°':>9s}{'mediana|b|':>12s}{'śr.|b| ± SD':>16s}{'śr. b':>9s}{'n wyłon.':>12s}{'ucieczki':>10s}{'bez wzg.':>9s}  błędy [°]"]
    def line(name, s):
        L.append(f"{name:26s}{s['ok10']:>6d}/{s['n']:<2d}{s['ok20']:>6d}/{s['n']:<2d}{s['med']:12.1f}{s['mean_abs']:10.1f} ± {s['sd_abs']:4.1f}"
                 f"{s['mean']:9.1f}{s['nfin']:>8d}/{s['n']:<3d}{s['esc']:>7d}{s['nobump']:>9d}  {np.round(s['e']).tolist()}")
    line("pełny, bez pamięci (none)", none)
    line("pełny 292 (pred)", full)
    for n in LEVELS[1:]:
        for c, nm in ((False, "bez komp."), (True, "skalowanie")):
            line(f"{n}, {nm} (pred)", a_stats(cond(R, n, c)))
    L += ["", "B2. CHWYT (piłeczka z równi; sukces = uniesiona ≥ 3 cm i obie szczęki ≥ 1 s; zgniecenie = średnia 20 ms siły szczęki > 5 N)",
          f"{'N / wariant':26s}{'sukces':>9s}{'zgniecenie':>12s}{'(szczyt 1 ms>5N)':>18s}{'reakcja (i) wykr.→ruch do celu [ms]':>38s}  klasy porażek / sukcesu"]
    for n in LEVELS:
        for c, nm in ((False, "bez komp."), (True, "skalowanie")):
            if n == 292 and c:
                continue
            s = b2_stats(cond(R, n, c))
            lab = "pełny 292" if n == 292 else f"{n}, {nm}"
            L.append(f"{lab:26s}{s['ok']:>6d}/{s['n']:<2d}{s['crush']:>9d}/{s['n']:<2d}{s['crush_inst']:>12d}/{s['n']:<2d}{ms(s['mv']):>38s}  "
                     + ", ".join(f"{k} {v}" for k, v in sorted(s["cls"].items(), key=lambda kv: -kv[1])))
    L += ["", "B1. UCIECZKA (kula drapieżnika; sukces = spike DNp01 po starcie kuli, zanim jej środek zbliży się do kamery na ≤ 10 cm)",
          f"{'N / wariant':26s}{'sukces':>9s}{'spike przed startem':>21s}{'opóźnienie od 0,30 m [ms]':>34s}"]
    for n in LEVELS:
        for c, nm in ((False, "bez komp."), (True, "skalowanie")):
            if n == 292 and c:
                continue
            s = b1_stats(cond(R, n, c))
            lab = "pełny 292" if n == 292 else f"{n}, {nm}"
            L.append(f"{lab:26s}{s['ok']:>6d}/{s['n']:<2d}{s['pre']:>15d}/{s['n']:<2d}{ms(s['lat']):>34s}")
    errs = [(r["level"], r["comp"], r["seed"], k, r[k]["error"]) for r in R for k in ("A", "A_none", "B1", "B2") if isinstance(r.get(k), dict) and "error" in r[k]]
    L += ["", f"błędy techniczne scenariuszy: {errs if errs else 'brak'}"]
    L += ["", "CZAS OBLICZEŃ (suma po procesach, s): " + ", ".join(
        f"N={n}{'/skal.' if c else ''}: {sum(r['t_total'] for r in cond(R, n, c)):.0f} (kalibracja {sum(r['t_cal'] for r in cond(R, n, c)):.0f})"
        for n in LEVELS for c in (False, True) if not (n == 292 and c)),
        f"  w tym A {sum(r.get('A_s', 0) for r in R):.0f}, B1 {sum(r.get('B1_s', 0) for r in R):.0f}, B2 {sum(r.get('B2_s', 0) for r in R):.0f}; "
        f"razem {sum(r['t_total'] for r in R):.0f} s CPU, {len(R)} prób"]
    if os.path.exists(PARTS):
        P = [json.loads(l) for l in open(PARTS)]
        L += ["", "B2 — ROZBICIE (ta sama lezja tylko w mózgu przy pełnym VNC / tylko w VNC przy pełnym mózgu; diagnostyka, N łączne nie obowiązuje)",
              f"{'N / wariant / część':34s}{'sukces':>9s}{'zgniecenie':>12s}  klasy"]
        for n in LEVELS[1:]:
            for c, nm in ((False, "bez komp."), (True, "skalowanie")):
                for part, pn in (("brain", "lezja tylko mózg"), ("vnc", "lezja tylko VNC")):
                    rs = [dict(B2=r["B2"]) for r in P if (r["level"], r["comp"], r["part"]) == (n, c, part)]
                    if rs:
                        s_ = b2_stats(rs)
                        L.append(f"{f'{n}, {nm}, {pn}':34s}{s_['ok']:>6d}/{s_['n']:<2d}{s_['crush']:>9d}/{s_['n']:<2d}  "
                                 + ", ".join(f"{k} {v}" for k, v in sorted(s_["cls"].items(), key=lambda kv: -kv[1])))
    ol = os.path.join(RES, "stage4_openloop.json")
    if os.path.exists(ol):
        O = json.load(open(ol))
        L += ["", "OTWARTA PĘTLA (wzgórze istnieje w oknie pamięci, % prób; ablation.py): N: bez komp. / skalowanie"]
        for n in sorted({o["level"] for o in O}, reverse=True):
            f = lambda c: 100 * np.mean([o["exists"] for o in O if o["level"] == n and o["comp"] == c])
            L.append(f"  N={n}: {f(False):.0f} % / {f(True):.0f} %")
    txt = "\n".join(L)
    open(os.path.join(RES, "stage4.txt"), "w").write(txt + "\n")
    print(txt)
    plot(R, none)


def plot(R, none):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    INK, GRID, BLUE, ORG, RED = "#0b0b0b", "#e4e3df", "#2a78d6", "#eb6834", "#e34948"
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(2, 3, figsize=(16, 8.5))
    ax = ax.ravel()
    V = {False: (BLUE, "o-", -2.0, "bez kompensacji"), True: (ORG, "s--", 2.0, "skalowanie synaptyczne")}
    for a in ax:
        a.invert_xaxis(); a.set_xlabel("neuronów łącznie (mózg + VNC)"); a.grid(color=GRID); a.set_xticks(LEVELS)
    rng = np.random.default_rng(0)
    for c, (col, mk, off, lab) in V.items():
        xs = [n + off for n in LEVELS]
        S = [a_stats(cond(R, n, c)) for n in LEVELS]
        # A: błąd pamięci
        ax[0].errorbar(xs, [s["mean_abs"] for s in S], [s["sd_abs"] for s in S], fmt=mk, color=col, capsize=3, label=lab)
        for x, s in zip(xs, S):
            f = abs(s["e"][np.isfinite(s["e"])])
            ax[0].scatter(x + rng.uniform(-1.5, 1.5, len(f)), f, s=8, color=col, alpha=0.35)
        ax[1].plot(xs, [100 * s["ok20"] / s["n"] for s in S], mk, color=col, label=f"|błąd| < 20° ({lab})")
        ax[1].plot(xs, [100 * s["ok10"] / s["n"] for s in S], mk, color=col, alpha=0.45, mfc="none", label=f"|błąd| < 10°")
        B2 = [b2_stats(cond(R, n, c)) for n in LEVELS]
        ax[2].plot(xs, [100 * s["ok"] / s["n"] for s in B2], mk, color=col, label=lab)
        ax[2].plot(xs, [100 * s["crush"] / s["n"] for s in B2], mk, color=RED, alpha=0.5 + 0.0 * c, mfc="none", label="zgniecenie (20 ms)" if c else None)
        B1 = [b1_stats(cond(R, n, c)) for n in LEVELS]
        ax[3].plot(xs, [100 * s["ok"] / s["n"] for s in B1], mk, color=col, label=lab)
    ax[0].axhline(none["mean_abs"], color=INK, ls=":", lw=1.2)
    ax[0].text(LEVELS[0], none["mean_abs"], f" bez pamięci (none, pełna sieć): {none['mean_abs']:.0f}°", va="bottom", fontsize=8)
    ax[0].set_ylabel("|błąd| przy wyłonieniu [°]"); ax[0].set_title("A. Pamięć przestrzenna (śr. ± SD, punkty = próby)", color=INK)
    ax[0].legend(frameon=False)
    ax[1].axhline(100 * none["ok20"] / none["n"], color=INK, ls=":", lw=1.2)
    ax[1].text(LEVELS[0], 100 * none["ok20"] / none["n"], " none, pełna sieć (<20°)", va="bottom", fontsize=8)
    ax[1].set_ylabel("% prób"); ax[1].set_ylim(-3, 103); ax[1].set_title("A. Odsetek prób z |błędem| < 20° (pełne) i < 10° (puste)", color=INK, fontsize=9)
    ax[2].set_ylabel("% prób"); ax[2].set_ylim(-3, 103); ax[2].set_title("B2. Chwyt: sukces (zgniecenie na czerwono)", color=INK); ax[2].legend(frameon=False, fontsize=8)
    ax[3].set_ylabel("% prób"); ax[3].set_ylim(-3, 103); ax[3].set_title("B1. Ucieczka przed drapieżnikiem: sukces", color=INK); ax[3].legend(frameon=False)
    ol = os.path.join(RES, "stage4_openloop.json")
    if os.path.exists(ol):
        O = json.load(open(ol))
        for c, (col, mk, off, lab) in V.items():
            Ns = sorted({o["level"] for o in O}, reverse=True)
            ax[4].plot(Ns, [100 * np.mean([o["exists"] for o in O if o["level"] == n and o["comp"] == c]) for n in Ns], mk, color=col, label=lab)
        ax[4].set_xticks([292, 250, 210, 160, 120, 90, 50]); ax[4].set_ylim(-3, 103); ax[4].legend(frameon=False)
    ax[4].set_ylabel("% prób z wzgórzem"); ax[4].set_title("Otwarta pętla: wzgórze EPG istnieje w oknie pamięci", color=INK)
    # klasy porażek B2 — słupki skumulowane
    cats = ["sukces", "zgniecenie*", "zgniecenie", "upuszczenie", "przepchnięcie", "wytoczenie", "chybienie"]
    cols = ["#1baf7a", "#eda100", "#e34948", "#6250d6", "#eb6834", "#2a78d6", "#8a8a85"]
    conds = [(292, False, "292")] + [(n, c, f"{n}\n{'skal.' if c else 'bez'}") for n in LEVELS[1:] for c in (False, True)]
    bot = np.zeros(len(conds))
    for k, col in zip(cats, cols):
        h = np.array([b2_stats(cond(R, n, c))["cls"].get(k, 0) for n, c, _ in conds], float)
        ax[5].bar(range(len(conds)), h, bottom=bot, color=col, label=k)
        bot += h
    ax[5].set_xticks(range(len(conds)), [x[2] for x in conds]); ax[5].set_xlabel("neuronów łącznie / wariant")
    ax[5].invert_xaxis(); ax[5].set_ylabel("liczba prób (z 10)"); ax[5].set_title("B2. Klasy wyników chwytu", color=INK)
    ax[5].legend(frameon=False, fontsize=7, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.22))
    fig.suptitle("Etap 4 — ablacja konektomu: pamięć przestrzenna, chwyt, ucieczka (zamknięta pętla, seedy 0–9) i pierścień EPG (otwarta pętla)", color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "explory_connectome_results.png"), dpi=110)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run_all()
    elif len(sys.argv) > 1 and sys.argv[1] == "parts":
        run_parts()
    elif len(sys.argv) > 1 and sys.argv[1] == "rerun_b2":
        rerun_b2()
    elif len(sys.argv) > 1 and sys.argv[1] == "report":
        report()
    elif len(sys.argv) > 1 and sys.argv[1] == "one":          # szybki test: python stage4.py one N comp seed
        print(task((int(sys.argv[2]), sys.argv[3] == "1", int(sys.argv[4]))))
