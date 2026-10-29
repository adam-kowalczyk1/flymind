"""Testy izolowane warstwy bezpieczeństwa (zakresy syntetyczne + zastępczy serwo-model kinematyczny, nie fizyka;
bez bio2, mujoco i sprzętu). Uruchom:  .venv/bin/python -I -B flymind/test_safety.py"""
import math
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safety import Command, Limits, SafetyError, SafetyLayer, ranges_from_mjcf  # noqa: E402

R = np.array([[-1.9, 1.9], [-1.7, 1.7], [-1.69, 1.69], [-1.66, 1.66], [-2.7, 2.8], [-0.17, 1.75]])
Q0 = np.zeros(6)
L = Limits(R)
SNN = {0: "snn:DNa02", "jaw": "snn:MN"}


def raises(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except SafetyError:
        return True
    return False


def cmd(t, pan=None, jaw=None, src=SNN, **more):
    q = {} if pan is None else {0: pan}
    q.update(more.get("q", {}))
    return Command(t, q, jaw, src)


def follow(q, target, v=4.7, dt=0.01):
    """Zastępczy serwo: pozycja dąży do celu z prędkością ≤ v (STS3215 wg bio2). Nie jest modelem fizyki."""
    q = q.copy()
    q[:5] += np.clip(target - q[:5], -v * dt, v * dt)
    return q


def main():
    # MJCF: zakresy czytane z XML bez mujoco; brak stawu → błąd
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "a.xml")
        names = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper")
        open(p, "w").write("<mujoco>" + "".join(f'<joint name="{n}" range="{a} {b}"/>' for n, (a, b) in zip(names, R))
                           + "</mujoco>")
        assert np.allclose(ranges_from_mjcf(p), R)
        open(p, "w").write('<mujoco><joint name="shoulder_pan" range="-1 1"/></mujoco>')
        assert raises(ranges_from_mjcf, p)

    # start bez skoku: pierwszy cel = pomiar; komenda w zakresie i wolna → bez zmian
    s = SafetyLayer(L)
    out, tau, flags, per = s.step(cmd(0.0, pan=0.01, jaw=0.5), Q0, 0.0, 0.0)
    assert out[0] == 0.01 and (out[1:] == 0).all() and tau == 0.5 and not flags and not per

    # prędkość: skok celu o 1 rad → |Δ| = v_max·dt na takt; wyprzedzenie: cel ≤ q + max_lead (zablokowane serwo)
    s = SafetyLayer(L)
    out, _, _, per = s.step(cmd(0.0, q={1: 1.0}, src={1: "script:lift"}), Q0, 0.0, 0.0)
    assert math.isclose(out[1], 0.015) and per[1] == ("rate",)
    for k in range(50):
        out, _, _, per = s.step(cmd(k * 0.01, q={1: 1.0}, src={1: "script:lift"}), Q0, k * 0.01, 0.0)
    assert math.isclose(out[1], 0.3) and "lead" in per[1]

    # zakres: ciągłe omega w lewo całkowane do celu — z serwem cel zatrzymuje się na krańcu − margines
    s, q, tgt = SafetyLayer(L), Q0.copy(), 0.0
    for k in range(400):
        tgt += 1.0 * 0.01
        out, _, _, per = s.step(cmd(k * 0.01, pan=tgt), q, k * 0.01, 0.0)
        q = follow(q, out)
        tgt = out[0]                              # integrator czyta wysłany cel (jak bio2: ctrl[0] − ω·dt)
    assert math.isclose(out[0], 1.9 - 0.05) and q[0] <= 1.85 + 1e-9

    # widzenie nieaktualne → baza hold, inne stawy dalej sterowane
    s = SafetyLayer(L)
    s.step(cmd(0.0, pan=0.01), Q0, 0.0, 0.0)
    out, _, _, per = s.step(cmd(0.01, pan=0.02, q={2: 0.01}, src={0: "snn:DNa02", 2: "script:x"}), Q0, 0.01, 0.2)
    assert out[0] == 0.01 and per[0] == ("vision_stale",) and out[2] == 0.01

    # watchdog, NaN w komendzie, nieznany staw → hold (cel poprzedni, szczęka 0), bez zatrzaśnięcia
    s = SafetyLayer(L)
    s.step(cmd(0.0, pan=0.01, jaw=0.5), Q0, 0.0, 0.0)
    assert s.step(cmd(0.0, pan=0.02, jaw=0.5), Q0, 0.2, 0.0)[1:3] == (0.0, ("cmd_timeout",))
    out, tau, flags, _ = s.step(cmd(0.3, pan=math.nan, jaw=0.5), Q0, 0.3, 0.0)
    assert flags == ("bad_command",) and out[0] == 0.01 and tau == 0.0
    assert s.step(cmd(0.4, q={7: 0.0}, src={7: "snn:x"}), Q0, 0.4, 0.0)[2] == ("bad_command",)
    assert s.step(cmd(0.5, pan=0.02), Q0, 0.5, 0.0)[0][0] == 0.02 and s.fault is None

    # estop i błąd czujnika: zatrzaśnięte do clear(); pomiar NaN na starcie → brak bezpiecznego celu
    s = SafetyLayer(L)
    s.step(cmd(0.0, pan=0.01), Q0, 0.0, 0.0)
    s.estop("operator")
    assert s.step(cmd(0.01, pan=0.02), Q0, 0.01, 0.0)[2] == ("fault",)
    s.clear("test")
    assert s.step(cmd(0.02, pan=0.02), Q0, 0.02, 0.0)[0][0] == 0.02
    bad = Q0.copy()
    bad[3] = 2.5
    s.step(cmd(0.03, pan=0.03), bad, 0.03, 0.0)
    assert s.fault.startswith("state") and s.step(cmd(0.04, pan=0.03), Q0, 0.04, 0.0)[2] == ("fault",)
    assert raises(SafetyLayer(L).step, cmd(0.0, pan=0.0), np.full(6, np.nan), 0.0, 0.0)

    # szczęka: limit momentu; kraniec zamknięcia → 0 przy zamykaniu, otwieranie dozwolone
    s = SafetyLayer(L)
    assert s.step(cmd(0.0, jaw=3.0), Q0, 0.0, 0.0)[1] == 1.0
    closed = Q0.copy()
    closed[5] = -0.16
    assert s.step(cmd(0.01, jaw=0.5), closed, 0.01, 0.0)[1] == 0.0
    assert s.step(cmd(0.02, jaw=-0.5), closed, 0.02, 0.0)[1] == -0.5

    # etykiety źródeł obowiązkowe; statystyki interwencji per źródło
    assert raises(SafetyLayer(L).step, Command(0.0, {0: 0.0}, None, {0: "DNa02"}), Q0, 0.0, 0.0)
    assert s.stats["per_source"]["snn:MN"] == {"ticks": 3, "torque": 1, "jaw_end": 1}
    assert raises(SafetyLayer, Limits(R[:5]))
    print("OK: warstwa bezpieczeństwa (21 asercji)")


if __name__ == "__main__":
    main()
