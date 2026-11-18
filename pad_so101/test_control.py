"""Testy pad_so101: .venv/bin/python pad_so101/test_control.py  (bez pada; symulacja headless)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

from control import Controller, PadState, shape

Z = np.zeros(5)


def press(c, *names, n=1, **axes):
    """n taktów z wciśniętymi przyciskami, potem puszczenie (zbocze = jedno wciśnięcie)."""
    for _ in range(n):
        c.tick(PadState(buttons=frozenset(names), **axes), c.target, 0.01)
    c.tick(PadState(), c.target, 0.01)


def test_logic():
    assert shape(0.1) == 0 and shape(1) == 1 and shape(-1) == -1 and 0 < shape(0.5) < 0.5
    c = Controller(Z.copy(), 0.5)
    press(c, n=100, lx=1.0)
    assert c.target[0] > 0.7, c.target                  # 1 s pełnego wychyłu, bieg 2 = 0,8 rad/s
    press(c, "BACK")
    t = c.target.copy()
    press(c, n=50, lx=1.0)
    assert c.stopped and np.allclose(c.target, t)       # STOP: gałki nic nie robią
    press(c, "START")
    assert not c.stopped
    press(c, "B")                                       # zapis slotu 1
    press(c, n=50, ry=1.0, rt=1.0)
    assert c.g < 0.5
    press(c, "A")
    for _ in range(300):
        c.tick(PadState(), c.target, 0.01)
    assert np.allclose(c.target, c.slots[1][0], atol=1e-3) and abs(c.g - 0.5) < 1e-3
    press(c, "Y")
    press(c, n=5, lx=1.0)
    assert c.goto is None                               # gałka przerywa automatyczny ruch
    press(c, "RIGHTSTICK")
    press(c, n=40, ly=1.0)
    press(c, "RIGHTSTICK")
    rec = [r[0] for r in c.last_rec]
    press(c, "START")
    seen = []
    for _ in range(600):
        seen.append(c.tick(PadState(), c.target, 0.01)[0].copy())
    assert any(np.allclose(s, rec[-1]) for s in seen) and np.allclose(c.target, rec[-1])
    press(c, "X")
    assert c.mode == "STAWY"                            # bez jakobianu brak trybu KART (prawdziwe ramię)
    press(c, "DPAD_UP", "DPAD_LEFT")
    assert c.gear == 2 and c.slot == 4


def test_sim_directions():
    """Kierunki pada w symulacji przez tę samą ścieżkę co run.py (Controller → SafetyLayer → SO101Sim)."""
    import pygame
    pygame.init()
    import run
    arm = run.SimArm()

    def go(n=80, mode="STAWY", **pad):
        arm.reset()
        q5, g, _ = arm.read()
        c, s = Controller(q5, g, jac=arm.jac), run.make_safety(arm)
        c.mode = mode
        f0 = arm.sim.fk(arm.read()[2])
        for _ in range(n):
            run.control_tick(arm, c, s, PadState(**pad))
        for _ in range(30):
            run.control_tick(arm, c, s, PadState())
        f1 = arm.sim.fk(arm.read()[2])
        return f1["gripperframe"] - f0["gripperframe"], f1["eye_forward"][2] - f0["eye_forward"][2], f0, f1

    def radial(f):
        return np.hypot(*f["gripperframe"][:2])

    d, *_ = go(lx=1.0)
    assert d[1] < -0.02, d                              # gałka w prawo → chwytak w prawo (−y; kamera za ramieniem)
    d, *_ = go(ly=1.0)
    assert d[2] < -0.02, d                              # lewa ↑ (STAWY) → bark w przód, chwytak w dół
    d, *_ = go(ry=1.0)
    assert d[2] > 0.02, d                               # prawa ↑ → chwytak w górę
    _, dp, *_ = go(buttons=frozenset({"RB"}))
    assert dp > 0.05, dp                                # RB → nos w górę
    d, dp, f0, f1 = go(mode="KART", ly=1.0)
    assert radial(f1) - radial(f0) > 0.02 and abs(d[2]) < 0.01 and abs(dp) < 0.03, (d, dp)   # dalej, ta sama wysokość i kąt
    d, dp, f0, f1 = go(mode="KART", ry=1.0)
    assert d[2] > 0.02 and abs(radial(f1) - radial(f0)) < 0.01 and abs(dp) < 0.03, (d, dp)    # w górę, pionowo
    arm.reset()
    q5, g, _ = arm.read()
    c, s = Controller(q5, g, jac=arm.jac), run.make_safety(arm)
    for _ in range(100):
        run.control_tick(arm, c, s, PadState(rt=1.0))
    assert arm.read()[1] < g - 0.2, (g, arm.read()[1])  # RT zamyka chwytak
    arm.close()


if __name__ == "__main__":
    test_logic()
    print("logika OK")
    test_sim_directions()
    print("kierunki w symulacji OK")
