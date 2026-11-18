"""Testy etapu „czucie i manipulacja”: czy o szczęce naprawdę decyduje sieć i czy dostaje wyłącznie sygnały czuciowe.

Uruchom z katalogu tymczasowego:  .venv/bin/python -I -B flymind/test_sensory_manipulation.py
"""
import inspect
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import object_handling as oh  # noqa: E402
import sensory_manipulation as sm  # noqa: E402

FC = sm.FlyCfg(trigger="search")
IT = ("cube_M", "mid")


def trial(arm, **kw):
    d = sm.make_driver(arm, FC, **kw)
    return d, sm.run_trial(IT, 3, d, sm.ARMS[arm][0], FC)


def test_N1_network_inputs_are_sensory_only():
    d = sm.make_driver("C_fly_feco", FC)
    sensory = set(i for p in d.pad_in for i in p) | set(i for v in d.feco.values() for i in v)
    motor = set(d.press) | set(d.release)
    assert not sensory & motor
    seen = []
    d.net.run = lambda X, n: seen.append(X.copy()) or np.zeros((n, d.N))      # podgląd prądu wejściowego
    for touch, q, qd in (([3.0, 2.0, 0.0], 0.2, -0.5), ([0.0, 0.0, 9.0], 1.5, 0.7), ([0.0, 0.0, 0.0], 0.8, 0.0)):
        d.step(np.array(touch), q, qd)
    for X in seen:
        assert set(np.nonzero(X)[0]) <= sensory                                # nic poza receptorami
    assert not set(np.nonzero(seen[1])[0]) & set(i for p in d.pad_in for i in p)   # dłoń (cs_palm) nie jest podłączona
    assert not np.nonzero(seen[2])[0].size                                     # środek zakresu, bez ruchu i dotyku: cisza
    b = sm.make_driver("B_fly", FC)
    b.net.run = lambda X, n: seen.append(X.copy()) or np.zeros((n, b.N))
    b.step(np.array([3.0, 2.0, 0.0]), 0.2, -0.5)
    assert set(np.nonzero(seen[-1])[0]) <= set(i for p in b.pad_in for i in p)  # B: wyłącznie dotyk
    assert "xipos" not in inspect.getsource(sm.LegJaw) and "contact" not in inspect.getsource(sm.LegJaw)


def test_N2_fly_jaw_decides_grasp_and_carry():
    _, r = trial("B_fly")
    o, st = r["objects"][0], r["safety_stats"]
    assert o["success"] and o["final"] == "box", o["truth"]
    assert st["snn:legT2L"]["ticks"] > 200, st                                  # chwyt + podniesienie + transport pod siecią
    assert set(st) == {"classical:reach", "classical:open", "classical:search", "snn:legT2L"}, set(st)
    a = o["attempt_log"][0]
    assert a["tau_engage"] >= FC.tau_engage and a["tau_carry"] >= FC.tau_engage


def test_N3_without_network_output_nothing_is_carried():
    for arm in ("N_null", "C_no_touch"):                                       # moment 0 / sieć bez dotyku
        _, r = trial(arm)
        o = r["objects"][0]
        assert not o["success"] and not o["truth"]["lift"] and o["final"] == "zone", (arm, o["truth"])
        assert [a["reason"] for a in o["attempt_log"]] == ["no_engage", "no_engage"], arm


def test_N4_shuffle_is_a_different_network_same_strengths():
    d, s = sm.make_driver("B_fly", FC), sm.make_driver("S_shuffle", FC, shuffle_seed=9208001)
    A, B = d.spec.toarray(), s.spec.toarray()
    assert (A != B).any() and np.allclose(A.sum(1), B.sum(1)) and np.allclose(np.sort(A[A != 0]), np.sort(B[B != 0]))


def test_N5_same_objects_and_poses_as_classical_baseline():
    items = oh.SETS["base"]
    _, r = trial("D_reflex")
    c = oh.run([IT], 3)
    assert r["objects"][0]["spawn"] == c["objects"][0]["spawn"]                 # ta sama poza startowa co w bazie
    assert sm.OUT.endswith(os.path.join("results", "sensory_manipulation")) and len(items) == 45


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"{name}: OK", flush=True)
    print("WSZYSTKIE TESTY OK")
