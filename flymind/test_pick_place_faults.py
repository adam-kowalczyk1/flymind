"""Testy naprawcze Etapu 1 po audytach: pomiar czasu przy resetach (P1), ścieżki błędów cyklu (P5), prawdziwe
odzyskanie bez resetu (R), zatrzaskiwanie i potwierdzanie błędów bezpieczeństwa (S), zapis wyników (W). MuJoCo, headless.

Awarie są wywoływane w symulacji: złą ścieżką lub kalibracją, uszkodzonym stanem fizyki, podmienionym odczytem albo
zmianą progu / planera (opis przy każdym teście — to nie zawsze zdarzenie fizyczne). Sprawdzana jest reakcja kodu:
przyczyna, brak zaliczenia jako sukces, `outcome` (recovered / reset / halted), stan PO błędzie i rozliczenie czasu.
To NIE jest benchmark: każda seria ma 1–4 cykli. Niezależna miara czasu: liczba taktów sim.step × n_sub × timestep.
Wszystkie kontrole czytają stan symulatora (poza kostki, kontakty, dotyk) — na sprzęcie tych danych nie ma.

Uruchom (z katalogu repo):  .venv/bin/python -I -B flymind/test_pick_place_faults.py
Test sam przechodzi do katalogu tymczasowego, bo MuJoCo dopisuje ostrzeżenia o niestabilności do ./MUJOCO_LOG.TXT."""
import contextlib
import io
import json
import os
import sys
import tempfile
from dataclasses import replace

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pick_place as PP  # noqa: E402
from grip import ClassicGrip  # noqa: E402
from pick_place import OUT, Cell, Fail, PPCfg, cube_pose, series, summarize  # noqa: E402
from reach import plan  # noqa: E402
from so101 import SimError  # noqa: E402

CFG = PPCfg()
TICK = None   # s na takt sterowania, ustawiane z pierwszej sceny


def steps(cell):
    return cell.sim.stats["steps"]


def check_time(run, cell, steps0):
    """Rozliczenie czasu serii: brak ujemnych, suma cykli = T_sim, T_sim = wykonane takty × TICK (bez podwójnego
    liczenia i bez utraty czasu przy resetach)."""
    cs = [c["cycle_sim"] for c in run["cycles"]]
    assert min(cs) >= 0 and all(c["cycle_sim"] > 0 for c in run["cycles"] if c["ok"]), f"czas cyklu < 0 (lub 0 w udanym): {cs}"
    assert abs(sum(cs) - run["T_sim"]) < 1e-9, (sum(cs), run["T_sim"])
    exp = (steps(cell) - steps0) * TICK
    assert abs(run["T_sim"] - exp) < 1e-6, f"T_sim {run['T_sim']} ≠ takty × dt {exp}"
    for c in run["cycles"]:
        if c["ok"]:
            assert abs(sum(c["t_sim"].values()) - c["cycle_sim"]) < 1e-9, "fazy nie sumują się do cyklu"
        elif c["reason"] != "exception":
            assert 0 <= c["t_to_fail_sim"] <= c["cycle_sim"] + 1e-12, c


def inject(cell, at, fault):
    """Uszkodzenie stanu fizyki tuż przed `at`-tym wywołaniem sim.step (liczone od teraz)."""
    orig, n = cell.sim.step, [0]

    def step():
        n[0] += 1
        if n[0] == at:
            fault(cell.sim)
        return orig()
    cell.sim.step = step
    return lambda: setattr(cell.sim, "step", orig)


def nan_cube_vel(sim):        # → MuJoCo: BADQVEL + samoczynny mj_resetData
    sim.d.qvel[sim.m.joint("cube").dofadr[0]] = np.nan


def huge_cube_force(sim):     # → MuJoCo: BADQACC + samoczynny mj_resetData
    sim.d.qfrc_applied[sim.m.joint("cube").dofadr[0]] = 1e300


def ready(cell, tol=None):
    """Stan gotowości czytany wprost z symulatora (nie z wartości zwracanej przez recover): ramię w domu, szczęka
    otwarta, pady bez nacisku, brak kontaktu ramię–stół i ramię–kostka, kostka w A/B, brak błędów."""
    o = cell.sim.observe()
    assert np.abs(o.q[:5] - cell.home[:5]).max() < (tol or cell.cfg.settle_tol), o.q
    assert o.q[5] >= cell.cfg.q_clear and max(o.touch) <= 0.2, (o.q[5], o.touch)
    assert not cell.table_contacts() and not cell.cube_contacts() and cell.where() in ("A", "B")
    assert cell.safety.fault is None and cell.sim.stopped is None and cell.not_ready() is None


def frozen(cell, fn):
    """fn() nie może ruszyć robota: żadnego taktu fizyki, żadnej zmiany komend (ctrl) ani czasu. Zwraca wynik fn."""
    d, s0, t0 = cell.sim.d, steps(cell), cell.sim.sim_time
    ctrl = d.ctrl.copy()
    try:
        out = fn()
    except Fail as e:
        out = e
    assert steps(cell) == s0 and cell.sim.sim_time == t0 and np.array_equal(d.ctrl, ctrl), "ruch mimo blokady"
    return out


def one_fail(cell, reason, label, outcome):
    """Seria 1 cyklu na przygotowanym stanowisku: oczekiwana porażka i jej skutek (recovered = bez resetu, reset =
    teleport sceny), raport, rozliczenie czasu, stan po błędzie gotowy do następnego cyklu."""
    s0, r0 = steps(cell), cell.sim.stats["resets"]
    run = series(cell.cfg, None, 1, cell=cell)
    c = run["cycles"][0]
    assert not c["ok"] and c["reason"] == reason, f"{label}: oczekiwano {reason}, jest {c['reason']}: {c.get('detail')}"
    assert c["outcome"] == outcome, f"{label}: outcome {c['outcome']} (recover={c['recover']}), oczekiwano {outcome}"
    assert (c["recover"] is True) == (outcome == "recovered") and c.get("reset", False) == (outcome == "reset")
    assert run["resets"] == cell.sim.stats["resets"] - r0 == (outcome == "reset") and run["complete"]
    summ = summarize([run])
    assert summ["ok"] == 0 and summ["fail_reasons"] == {reason: 1} and summ["recovered"] == (outcome == "recovered")
    check_time(run, cell, s0)
    ready(cell)
    print(f"  {label}: {reason} ({c['detail'][:70]}); recover={c['recover']}; outcome={outcome}; "
          f"t_do_błędu {c['t_to_fail_sim']:.2f} s, cykl {c['cycle_sim']:.2f} s sym.")
    return run, c


class StuckJaw(ClassicGrip):
    """Awaria serwa szczęki: brak momentu otwierającego (after_hold: dopiero po pierwszym chwycie)."""
    def __init__(self, cfg, after_hold):
        super().__init__(cfg)
        self.stuck = not after_hold

    def step(self, q_jaw, touch):
        tau = super().step(q_jaw, touch)
        self.stuck |= self.mode == "hold"
        return 0.0 if self.stuck and self.mode == "open" else tau


def glitch(cell, at):
    """Jednorazowy błędny odczyt enkodera (+3 rad na shoulder_lift) w `at`-tej obserwacji od teraz."""
    orig, n = cell.sim.observe, [0]

    def observe():
        n[0] += 1
        o = orig()
        if n[0] == at:
            q = o.q.copy()
            q[1] += 3.0
            o = replace(o, q=q)
        return o
    cell.sim.observe = observe


def main():
    global TICK
    os.chdir(tempfile.mkdtemp(prefix="pp_faults_"))
    base = Cell(CFG)
    TICK = base.sim.cfg.n_sub * base.sim.cfg.timestep

    # ---------------- P1: pomiar czasu ----------------
    # P1.1 SO101Sim: sim_time ciągły przez reset() i przez samoczynny reset MuJoCo; d.time się zeruje
    sim = Cell(CFG).sim
    for _ in range(20):
        sim.step()
    t1 = sim.sim_time
    sim.reset(CFG.home)
    assert sim.d.time == 0.0 and sim.sim_time == t1, (sim.d.time, sim.sim_time, t1)
    for _ in range(5):
        sim.step()
    assert abs(sim.sim_time - 25 * TICK) < 1e-9
    nan_cube_vel(sim)
    try:
        sim.step()
        raise AssertionError("BADQVEL / samoczynny reset MuJoCo nie wykryty")
    except SimError:
        pass
    assert sim.stats["auto_resets"] == 1 and sim.d.time < 2 * TICK, (sim.stats, sim.d.time)
    assert abs(sim.sim_time - 26 * TICK) < 1e-9, sim.sim_time       # ani utraty, ani dodanego czasu
    print("P1.1 OK: sim_time ciągły przez reset() i auto-reset MuJoCo (BADQVEL wykryty jako SimError)")

    # P1.5 samoczynny reset w 1. i w 2. kroku fizyki po reset() — d.time nie cofa się wtedy poniżej wartości sprzed
    # kroku (0 → 0,001 oraz 0,001 → 0,001); wykrycie przez licznik ostrzeżeń / brak przyrostu czasu.
    for k in (1, 2):
        sim = Cell(CFG).sim
        for _ in range(7):
            sim.step()
        sim.reset(CFG.home)
        t0, a0 = sim.sim_time, sim.stats["auto_resets"]
        for _ in range(k - 1):
            sim.mj.mj_step(sim.m, sim.d)                 # k−1 zwykłych kroków fizyki po 1 ms
        nan_cube_vel(sim)
        try:
            sim.step()                                   # 10 kroków; pierwszy z nich trafia na NaN
            raise AssertionError(f"auto-reset w kroku {k} po resecie nie wykryty")
        except SimError:
            pass
        assert sim.stats["auto_resets"] - a0 == 1, (k, sim.stats)
        exp = t0 + (k - 1 + sim.cfg.n_sub) * sim.cfg.timestep
        assert abs(sim.sim_time - exp) < 1e-12, (k, sim.sim_time, exp)   # ani utraty 1 ms, ani podwójnego liczenia
    print("P1.5 OK: auto-reset MuJoCo w 1. i 2. kroku po reset(): wykryty, auto_resets = 1, czas co do kroku")

    # P1.2 zwykłe cykle bez resetu = dotychczasowe wyniki bit w bit (S0, seed 1, cykle 0–1 z zapisanego JSON)
    old = json.load(open(os.path.join(OUT, "S0_baseline.json")))["runs"][0]
    assert old["seed"] == 1
    cell = Cell(CFG, 1)
    s0 = steps(cell)
    run = series(CFG, 1, 2, cell=cell)
    for new, ref in zip(run["cycles"], old["cycles"][:2]):
        assert new["ok"] and new["cycle_sim"] == ref["cycle_sim"], (new["cycle_sim"], ref["cycle_sim"])
        assert new["t_sim"] == ref["t_sim"], (new["t_sim"], ref["t_sim"])
    assert run["continuous"] and run["resets"] == 0 and run["auto_resets"] == 0
    check_time(run, cell, s0)
    print(f"P1.2 OK: 2 cykle bez resetu identyczne z S0_baseline.json (seed 1): "
          f"{[c['cycle_sim'] for c in run['cycles']]} s")

    # P1.3 reset w ścieżce błędu, 3 resety z rzędu (strefa B przesunięta o 15 mm → place_out_of_zone → kostka poza
    # A/B → reset). Stary kod: cycle_sim = d.time − s0 < 0 po resecie.
    cell = Cell(CFG)
    cell.cfg = replace(CFG, B=(CFG.B[0], CFG.B[1] - 0.015))
    s0 = steps(cell)
    run = series(cell.cfg, None, 3, cell=cell)
    assert [c["reason"] for c in run["cycles"]] == ["place_out_of_zone"] * 3 and run["ok"] == 0
    assert run["resets"] == 3 and all(c["reset"] for c in run["cycles"]) and not run["continuous"]
    assert cell.sim.d.time < cell.sim.sim_time       # d.time zresetowany, licznik serii nie
    check_time(run, cell, s0)
    print(f"P1.3 OK: 3 resety w ścieżce błędu, czasy cykli {[round(c['cycle_sim'], 2) for c in run['cycles']]} s, "
          f"T_sim {run['T_sim']:.2f} s = takty × dt")

    # P1.4 samoczynny reset MuJoCo w trakcie cyklu (NaN prędkości kostki w takcie 300 cyklu 0 i siła 1e300 w takcie
    # 300 cyklu 2) → sim_error, reset serii, cykle 1 i 3 udane; czas do błędu < czas cyklu (recover + reset)
    cell = Cell(CFG)
    orig_cycle, k, undo = cell.cycle, [0], [None]

    def cycle():
        if undo[0]:
            undo[0]()
            undo[0] = None
        if k[0] in (0, 2):
            undo[0] = inject(cell, 300, nan_cube_vel if k[0] == 0 else huge_cube_force)
        k[0] += 1
        return orig_cycle()
    cell.cycle = cycle
    s0 = steps(cell)
    run = series(CFG, None, 4, cell=cell)
    rs = [(c["ok"], c["reason"]) for c in run["cycles"]]
    assert rs == [(False, "sim_error"), (True, None), (False, "sim_error"), (True, None)], rs
    assert run["auto_resets"] == 2 and run["resets"] == 2 and not run["continuous"], run
    f0 = run["cycles"][0]
    assert abs(f0["t_to_fail_sim"] - 300 * TICK) < 1e-6, f0["t_to_fail_sim"]   # błąd w takcie 300 → 3,00 s
    assert f0["auto_resets"] == 1 and "BADQVEL" in f0["detail"] and "BADQACC" in run["cycles"][2]["detail"]
    assert f0["outcome"] == "reset" and str(f0["recover"]).startswith("no_motion") and f0["cycle_sim"] == f0["t_to_fail_sim"]
    check_time(run, cell, s0)
    summ = summarize([run])
    assert summ["auto_resets"] == 2 and summ["continuous"] is False and summ["ok"] == 2
    print(f"P1.4 OK: 2 auto-resety MuJoCo (BADQVEL, BADQACC) → sim_error, czas do błędu {f0['t_to_fail_sim']:.2f} s, "
          f"cykl do resetu {f0['cycle_sim']:.2f} s (recover nie rusza ramienia), po RESECIE kolejne cykle udane")

    # ---------------- P5: ścieżki błędów ----------------
    print("P5:")
    loose = replace(base.rcfg, z_min=-0.05)   # planer bez kontroli odstępu: celowo zła ścieżka

    # table_collision: zejście zaplanowane 10 mm za nisko (błąd kalibracji wysokości stołu) → pad uderza w stół.
    # recover nie zejdzie ze stołu (każdy takt znów wykrywa kontakt) → seria robi jawny reset zamiast jechać dalej.
    c = Cell(CFG)
    P, g = c.plans[("A", "B")], c.pad_target(c.place("A"), CFG.gap)
    P["approach_descend"] = plan(c.sim, P["approach_move"][-1], g - [0, 0, 0.010], point="cs_fixed",
                                 jaw_open=CFG.home[5], cfg=loose)
    run, f = one_fail(c, "table_collision", "table_collision", "reset")
    assert str(f["recover"]).startswith("no_motion") and f["cycle_sim"] == f["t_to_fail_sim"]   # zero ruchu po kolizji
    assert not c._qd_prev.any(), "po resecie _qd_prev ma być prędkością po teleportacji (0), nie sprzed resetu"

    # cube_hit_table: transport zaplanowany w dół do stołu przy B
    c = Cell(CFG)
    P, gp = c.plans[("A", "B")], c.pad_target(c.place("B"), 0.0, lift=CFG.place_drop)
    P["transport"] = plan(c.sim, P["lift"][-1], gp + [0, 0, -0.004], point="cs_fixed", cfg=loose)
    one_fail(c, "cube_hit_table", "cube_hit_table", "reset")          # recover otwiera szczękę: kostka spada poza A/B

    # release_failed (gałąź „dotyk po otwarciu”): próg zwolnienia q_clear 0,2 rad < kąt kontaktu z kostką (~0,3 rad)
    # → sterownik „widzi” otwartą szczękę, a kostka nadal ściśnięta
    run, f = one_fail(Cell(replace(CFG, q_clear=0.2)), "release_failed", "release_failed", "recovered")
    assert "touch po otwarciu" in f["detail"]

    # place_out_of_zone: znacznik B 15 mm od miejsca, w które celuje plan (błąd kalibracji miejsca)
    c = Cell(CFG)
    c.cfg = replace(CFG, B=(CFG.B[0], CFG.B[1] - 0.015))
    one_fail(c, "place_out_of_zone", "place_out_of_zone", "reset")

    # place_no_contact: zejście przy odkładaniu kończy się 15 mm za wysoko
    c = Cell(CFG)
    P, gp = c.plans[("A", "B")], c.pad_target(c.place("B"), 0.0, lift=CFG.place_drop)
    P["place_descend"] = plan(c.sim, P["transport"][-1], gp + [0, 0, 0.015], point="cs_fixed", cfg=c.rcfg)
    one_fail(c, "place_no_contact", "place_no_contact", "recovered")  # kostka upuszczona z 15 mm, ląduje w strefie B

    # cube_pushed: stała szczęka schodzi 4 mm „w ścianę” kostki (gap −4 mm) i spycha ją
    one_fail(Cell(replace(CFG, gap=-0.004)), "cube_pushed", "cube_pushed", "recovered")

    # unreachable: kostka 6 mm od A (wymaga nowego planu chwytu), planer z odstępem od stołu 20 mm odrzuca plan.
    # Porażka przed jakimkolwiek ruchem: czas do błędu = 0.
    c = Cell(CFG)
    c.sim.reset(c.home, cube_pose=(CFG.A[0] + 0.006, CFG.A[1], c.yaw_nom["A"]))
    c.obs = c.sim.observe()
    c.rcfg = replace(c.rcfg, z_min=0.02)
    run, f = one_fail(c, "unreachable", "unreachable", "recovered")
    assert f["t_to_fail_sim"] == 0.0 and "za blisko stołu" in f["detail"]

    # sim_error + reset w serii: pokryte w P1.4 (2 resety MuJoCo + 2 resety serii)

    # jaw_not_open (odłożenie): serwo szczęki po chwycie nie daje momentu otwierającego → kostka zostaje w szczękach;
    # recover nie potwierdza stanu (szczęka zamknięta) → reset, nie „odzyskanie”
    c = Cell(CFG)
    c.grip = StuckJaw(c.grip.cfg, after_hold=True)
    run, f = one_fail(c, "jaw_not_open", "jaw_not_open (odłożenie)", "reset")
    assert str(f["recover"]).startswith("jaw_not_open"), f["recover"]
    # jaw_not_open (podejście): szczęka startuje przymknięta (0,2 rad) i nie otwiera się → porażka przed zejściem
    c = Cell(CFG)
    c.grip = StuckJaw(c.grip.cfg, after_hold=False)
    c.sim.reset(np.r_[c.home[:5], 0.2], cube_pose=(*CFG.A, c.yaw_nom["A"]))
    c.obs = c.sim.observe()
    p0 = cube_pose(c.sim)[0]
    run, f = one_fail(c, "jaw_not_open", "jaw_not_open (podejście)", "reset")
    assert "0.55" in f["detail"] and np.linalg.norm(p0 - [*CFG.A, CFG.cube / 2]) < 1e-3

    # ---------------- R: prawdziwe odzyskanie bez resetu ----------------
    # Błąd przejściowy: JEDEN błędny plan podejścia (stała szczęka 4 mm „w ścianę” kostki, jak po jednorazowym złym
    # odczycie położenia) → cube_pushed. Potem nic nie jest ustawiane ręcznie: recover() wraca do domu, kostka zostaje
    # tam, gdzie ją zepchnięto, a kolejne cykle planują chwyt z jej faktycznej pozycji.
    c = Cell(CFG)
    good = dict(c.plans[("A", "B")])
    c.cfg = replace(CFG, gap=-0.004)
    c.plans[("A", "B")].update(c.plan_pick(c.place("A")))
    c.cfg = CFG
    s0, r0 = steps(c), c.sim.stats["resets"]
    run = series(CFG, None, 4, cell=c)
    c.plans[("A", "B")] = good                           # (po serii; w serii plan z cache nie był już użyty)
    f, rest = run["cycles"][0], run["cycles"][1:]
    assert (f["ok"], f["reason"], f["outcome"], f["recover"]) == (False, "cube_pushed", "recovered", True), f
    assert [(x["ok"], x["src"], x["dst"]) for x in rest] == [(True, "A", "B"), (True, "B", "A"), (True, "A", "B")]
    assert run["resets"] == 0 and run["auto_resets"] == 0 and run["continuous"] and run["complete"]
    assert c.sim.stats["resets"] == r0 and c.sim.t_offset == 0.0, "reset / teleportacja w trakcie odzyskiwania"
    assert rest[0]["start_drift_rad"] < CFG.settle_tol and rest[0]["start_jaw"] >= CFG.q_clear   # stan PO recover
    assert 3.0 < rest[0]["src_dev_mm"] < 10.0, rest[0]["src_dev_mm"]   # kostka naprawdę została zepchnięta i tam leży
    assert max(x["place_err_mm"] for x in rest) < 3.5 and c.stats["replans"] >= 1
    check_time(run, c, s0)
    ready(c)
    print(f"R1 OK: cube_pushed → recover() bez resetu (dom {rest[0]['start_drift_rad']:.4f} rad, szczęka "
          f"{rest[0]['start_jaw']:.2f} rad, kostka {rest[0]['src_dev_mm']:.1f} mm od A) → 3 kolejne cykle udane, "
          f"resets 0, błąd odłożenia ≤ {max(x['place_err_mm'] for x in rest):.2f} mm")

    # ---------------- S: błędy bezpieczeństwa — zatrzaśnięcie, brak ruchu, jawne potwierdzenie ----------------
    # S1 jednorazowy zły odczyt enkodera w podejściu → SafetyLayer zatrzaskuje błąd → safety_fault → seria STAJE
    c = Cell(CFG)
    glitch(c, 30)
    s0, r0 = steps(c), c.sim.stats["resets"]
    run = series(CFG, None, 3, cell=c)
    f = run["cycles"][0]
    assert len(run["cycles"]) == 1 and (f["reason"], f["outcome"]) == ("safety_fault", "halted"), run["cycles"]
    assert str(f["recover"]).startswith("safety_latched") and f["cycle_sim"] == f["t_to_fail_sim"]   # recover bez ruchu
    assert run["complete"] is False and run["stopped_by"].startswith("safety_latched") and run["resets"] == 0
    assert summarize([run])["complete"] is False and c.sim.stats["resets"] == r0
    assert c.safety.fault.startswith("state") and "cleared" not in c.safety.stats, "błąd skasowany bez potwierdzenia"
    check_time(run, c, s0)
    # próby ruchu przy zatrzaśniętym błędzie: recover, nowy cykl, pojedynczy takt, kolejna seria — zero taktów, zero komend
    assert str(frozen(c, c.recover)).startswith("safety_latched")
    assert frozen(c, c.cycle).reason == "safety_fault"
    assert frozen(c, lambda: c.tick(c.home[:5], "open")).reason == "safety_fault"
    again = frozen(c, lambda: series(CFG, None, 2, cell=c))
    assert len(again["cycles"]) == 1 and again["cycles"][0]["outcome"] == "halted" and not again["complete"]
    assert c.safety.fault.startswith("state")
    # dozwolona ścieżka: jawne SafetyLayer.clear(powód) → recover() potwierdza stan → następny cykl udany, bez resetu
    c.safety.clear("test: operator potwierdził po sprawdzeniu enkodera")
    assert c.safety.stats["cleared"][-1][1].startswith("test: operator") and c.recover() is True
    ready(c)
    run = series(CFG, None, 2, cell=c)
    assert run["ok"] == 2 and run["resets"] == 0 and run["complete"] and c.sim.stats["resets"] == r0
    print("S1 OK: zły odczyt enkodera → safety_fault zatrzaśnięty, seria zatrzymana; recover / cycle / tick / series "
          "bez żadnego taktu i komendy; po jawnym clear(): recover potwierdzony, 2 cykle udane, 0 resetów")

    # S2 estop (zatrzask PROGRAMOWY w SafetyLayer — sprzętowego e-stopu w projekcie nie ma): nic nie rusza, a reset
    # symulatora NIE jest potwierdzeniem bezpieczeństwa
    c = Cell(CFG)
    c.safety.estop("test")
    run = frozen(c, lambda: series(CFG, None, 3, cell=c))
    f = run["cycles"][0]
    assert len(run["cycles"]) == 1 and (f["reason"], f["outcome"], f["t_to_fail_sim"]) == ("safety_fault", "halted", 0.0)
    assert not run["complete"] and run["resets"] == 0 and run["T_sim"] == 0.0 and run["per_h_sim"] == 0.0
    assert str(frozen(c, c.recover)).startswith("safety_latched") and c.safety.fault == "estop: test"
    c.reset_scene()                                      # reset symulatora: zatrzask zostaje
    assert c.safety.fault == "estop: test" and frozen(c, c.cycle).reason == "safety_fault"
    assert frozen(c, lambda: series(CFG, None, 1, cell=c))["cycles"][0]["outcome"] == "halted"
    c.safety.clear("test: operator zwolnił estop")
    run = series(CFG, None, 1, cell=c)
    assert run["ok"] == 1 and run["complete"]
    print("S2 OK: estop → seria zatrzymana bez ruchu; recover i reset symulatora go nie kasują; po clear() cykl udany")

    # S3 błąd krytyczny symulatora (niestabilna fizyka): bez resetu nie ma wznowienia — recover i nowy cykl bez ruchu
    c = Cell(CFG)
    undo = inject(c, 50, nan_cube_vel)
    try:
        c.cycle()
        raise AssertionError("sim_error nie zgłoszony")
    except Fail as e:
        assert e.reason == "sim_error", e
    undo()
    assert c.sim.stopped and str(frozen(c, lambda: c.recover("sim_error"))).startswith("no_motion")
    assert frozen(c, c.recover).startswith("no_motion") and frozen(c, c.cycle).reason == "sim_error"
    assert c.not_ready().startswith("sim_stopped")
    print("S3 OK: sim_error → symulator zatrzymany; recover (z przyczyną i bez) oraz nowy cykl nie wykonują taktu")

    # S4 komenda łamiąca kontrakt symulatora (cel poza ctrlrange — tu podmieniony wynik warstwy bezpieczeństwa) →
    # bad_command (nie sim_error): ctrl bez zmian, bez kroku, recover bez ruchu, reset sceny
    c = Cell(CFG)
    orig = c.safety.step

    def bad_once(*a):
        c.safety.step = orig
        q, tau, flags, per = orig(*a)
        q[0] = 99.0
        return q, tau, flags, per
    c.safety.step = bad_once
    ctrl = c.sim.d.ctrl.copy()
    run, f = one_fail(c, "bad_command", "bad_command", "reset")
    assert f["t_to_fail_sim"] == 0.0 and f["cycle_sim"] == 0.0 and c.sim.stats["rejected"] == 1 and "ctrlrange" in f["detail"]
    assert np.array_equal(c.sim.d.ctrl[c.sim.aid[:5]], ctrl[c.sim.aid[:5]])   # po resecie cele = dom, jak przed

    # ---------------- W: zapis wyników ----------------
    # W1 nieoczekiwany wyjątek w cyklu → seria przerwana i oznaczona jako niekompletna (nie udana)
    c = Cell(CFG)
    orig_cycle, k = c.cycle, [0]

    def cycle():
        k[0] += 1
        if k[0] == 2:
            raise RuntimeError("test: błąd programu")
        return orig_cycle()
    c.cycle = cycle
    run = series(CFG, None, 4, cell=c)
    assert [x["ok"] for x in run["cycles"]] == [True, False] and run["cycles"][1]["reason"] == "exception"
    assert run["complete"] is False and run["stopped_by"].startswith("exception: RuntimeError") and run["ok"] == 1
    summ = summarize([run])
    assert summ["complete"] is False and summ["attempts"] == 2 and summ["fail_reasons"] == {"exception": 1}
    # W2 main(): istniejącego wyniku nie nadpisuje; seria przerwana trafia do <tag>.INCOMPLETE.json z complete=false
    PP.OUT, argv = os.getcwd(), sys.argv

    def run_main(tag, cycles):
        sys.argv = ["pick_place.py", "--seeds", "1", "2", "--cycles", str(cycles), "--tag", tag]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                PP.main()
        except SystemExit as e:
            return e.code
    assert run_main("w2", 1) == 0
    first = open("w2.json", "rb").read()
    assert json.loads(first)["complete"] is True and len(json.loads(first)["runs"]) == 2
    code = run_main("w2", 2)
    assert isinstance(code, str) and "istnieje" in code and open("w2.json", "rb").read() == first, code
    orig_series = PP.series
    PP.series = lambda cfg, seed, n: orig_series(cfg, seed, n, cell=c)   # stanowisko z W1: wyjątek w kolejnym cyklu
    k[0] = 1
    assert run_main("w3", 3) == 1 and not os.path.exists("w3.json")
    bad = json.load(open("w3.INCOMPLETE.json"))
    assert bad["complete"] is False and bad["summary"]["complete"] is False and len(bad["runs"]) == 1
    assert bad["runs"][0]["stopped_by"].startswith("exception") and isinstance(run_main("w3", 1), str)
    PP.series, PP.OUT, sys.argv = orig_series, OUT, argv
    print("W OK: wyjątek → complete=False i plik *.INCOMPLETE.json (kod wyjścia 1); istniejący tag nie jest nadpisywany")

    print("OK: test_pick_place_faults (P1.1–P1.5, P5: 9 ścieżek + bad_command, R1, S1–S4, W)")


if __name__ == "__main__":
    main()
