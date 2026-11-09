"""Testy Etapu 1 (pick_place.py) w MuJoCo, headless, wartości nominalne (seed None, bez losowości).
T1 profil trapezowy (bez fizyki), T2 scena, T3 jeden cykl A→B faza po fazie, T4 ciągłość 6 cykli bez resetu,
T5 kostka przesunięta o 6 mm → nowy plan chwytu i sukces, T6–T8 wstrzyknięte (kostka niewidoczna dla szczęk, śliska, obrócona) awarie muszą być wykryte, nie zaliczone.
Uruchom:  .venv/bin/python -I -B flymind/test_pick_place.py"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grip import GripCfg  # noqa: E402
from pick_place import PHASES, Cell, Fail, PPCfg, cube_pose, profile  # noqa: E402


def expect_fail(cell, reasons):
    try:
        cell.cycle()
    except Fail as e:
        assert e.reason in reasons, f"oczekiwano {reasons}, jest {e.reason}: {e.detail}"
        rec = cell.recover()
        assert rec is True, rec
        assert np.abs(cell.obs.q[:5] - cell.home[:5]).max() < 0.05, "po recover ramię nie w domu"
        return e.reason
    raise AssertionError(f"awaria {reasons} nie wykryta — cykl zaliczony")


def main():
    cfg = PPCfg()
    # T1: profil — start/koniec, |Δ| ≤ v·dt, |Δ²| ≤ a·dt² (odcinek prosty)
    q0, q1 = np.zeros(5), np.array([1.0, -0.5, 0.2, 0.0, 0.0])
    tg = profile([q1], q0, 1.0, 4.0, 0.01)
    d = np.diff(np.vstack([q0, tg]), axis=0)
    assert np.allclose(tg[-1], q1) and np.abs(d).max() <= 0.01 + 1e-9, "profil: koniec / prędkość"
    assert np.abs(np.diff(d, axis=0)).max() <= 4.0 * 1e-4 + 1e-9, "profil: przyspieszenie"
    assert profile([q0], q0, 1.0, 4.0, 0.01) == []

    # T2: scena — kostka i znaczniki; znaczniki bez kontaktu
    cell = Cell(cfg)
    m = cell.sim.m
    assert abs(m.geom("cube").size[0] - cfg.cube / 2) < 1e-9 and abs(m.body("cube").mass[0] - cfg.cube_mass) < 1e-9
    assert all(m.geom(f"mark{i}").contype == 0 and m.geom(f"mark{i}").conaffinity == 0 for i in (0, 1))
    assert cell.where() == "A"

    # T3: jeden cykl, warunki każdej fazy (kontrole wewnątrz cycle() + pomiary)
    r = cell.cycle()
    assert (r["src"], r["dst"]) == ("A", "B")
    assert set(r["t_sim"]) == set(PHASES) and all(v > 0 for v in r["t_sim"].values())
    assert r["lift_mm"] > 40, r["lift_mm"]
    assert r["place_err_mm"] < cfg.zone * 1e3 and abs(r["tilt_deg"]) < cfg.tilt_tol
    assert r["home_err_rad"] < cfg.settle_tol
    assert cell.obs.q[5] > cfg.q_clear and max(cell.obs.touch[:2]) < GripCfg().f_contact, "szczęka nie zwolniona"
    assert cell.where() == "B" and not cell.stats["flags"], cell.stats["flags"]

    # T4: ciągłość — 6 kolejnych cykli bez resetu, kierunek się przełącza, brak dryfu
    seq = [cell.cycle() for _ in range(6)]
    assert [x["src"] for x in seq] == ["B", "A"] * 3
    assert max(x["home_err_rad"] for x in seq) < cfg.settle_tol
    assert max(x["place_err_mm"] for x in seq) < 3.0, [round(x["place_err_mm"], 2) for x in seq]

    # T5: kostka 6 mm od A (w strefie) → nowy plan chwytu, sukces, odłożenie nadal w B
    c5 = Cell(cfg)
    n = c5.stats["replans"]
    c5.sim.reset(c5.home, cube_pose=(cfg.A[0] + 0.006, cfg.A[1], c5.yaw_nom["A"]))
    c5.obs = c5.sim.observe()
    r = c5.cycle()
    assert c5.stats["replans"] == n + 1 and r["place_err_mm"] < 3.0, r["place_err_mm"]

    # T6: kostka „duch” dla chwytaka (koliduje tylko ze stołem) → no_contact, nie sukces
    c6 = Cell(cfg)
    m = c6.sim.m
    m.geom_conaffinity[m.geom("table").id] = 3
    m.geom_contype[m.geom("cube").id] = m.geom_conaffinity[m.geom("cube").id] = 2
    expect_fail(c6, {"no_contact"})

    # T7: śliska kostka (tarcie 0,05 zamiast 0,8, pady też 0,05) → chwyt nie utrzyma: lift_failed / slip / weak_grip
    c7 = Cell(cfg)
    m = c7.sim.m
    for g in ("cube", "jaw_fixed", "jaw_moving", "palm"):
        m.geom_friction[m.geom(g).id, 0] = 0.05
    expect_fail(c7, {"lift_failed", "slip", "weak_grip"})

    # T8: kostka obrócona o 30° (poza yaw_tol) lub poza A/B → object_lost bez ruchu ramienia
    c8 = Cell(cfg)
    c8.sim.reset(c8.home, cube_pose=(cfg.A[0], cfg.A[1], c8.yaw_nom["A"] + math.radians(30)))
    c8.obs = c8.sim.observe()
    expect_fail(c8, {"object_lost"})
    p, yaw, tilt = cube_pose(c8.sim)
    assert np.linalg.norm(p[:2] - cfg.A) < 1e-3, "object_lost nie może ruszać kostki"
    print(f"OK: pick-and-place (T1–T8; cykl A→B {sum(seq[0]['t_sim'].values()):.2f} s sym., "
          f"błąd odłożenia ≤ {max(x['place_err_mm'] for x in seq):.2f} mm w 6 cyklach ciągłych)")


if __name__ == "__main__":
    main()
