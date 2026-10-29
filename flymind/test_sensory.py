"""Testy izolowane interfejsu sensorycznego (bodźce syntetyczne; bez bio2, mujoco i kamery).
Uruchom:  .venv/bin/python -I -B flymind/test_sensory.py"""
import math
import os
import sys
import tempfile
from dataclasses import replace

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sensory import Frame, SensoryError, SensoryGate, load_clip, project, replay, save_clip, spot_clip  # noqa: E402

SHAPE, FOVY, P = (96, 128), 70.0, 0.01          # jak kamera „eye” w bio2/scene2.py (128×96, fovy 70°, 100 Hz)


def gate(**kw):
    return SensoryGate(**{**dict(shape=SHAPE, period=P, max_age=0.05, reset_after=0.05), **kw})


def run(g, frames):
    return [g.push(f, f.t_receive) for f in frames]


def raises(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except SensoryError:
        return True
    return False


def main():
    # geometria: zgodna z odwrotnością bio2/vision.py (col_az = arctan(−col_x), col_x = (2u/W − 1)·tanx)
    az = np.radians([-30, -10, 0, 15, 35])
    u, v = project(az, 0.0, SHAPE, FOVY)
    tanx = math.tan(math.radians(FOVY) / 2) * SHAPE[1] / SHAPE[0]
    assert np.allclose(np.arctan(-(2 * u / SHAPE[1] - 1) * tanx), az) and np.allclose(v, SHAPE[0] / 2)
    assert project(0.2, 0.1, SHAPE, FOVY)[0] < 64 and project(0.0, 0.1, SHAPE, FOVY)[1] < 48   # + w lewo, + w górę

    # bodziec: środek ciężkości plamki = rzut prawdy (< 0,5 px); poza polem widzenia → samo tło, visible=False
    c = spot_clip(np.radians([10, 60, 120]), np.radians([-5, 0, 0]), SHAPE, FOVY)
    yy, xx = np.nonzero(c.images[0, ..., 1] == 0)
    u0, v0 = project(c.truth["az"][0], c.truth["el"][0], SHAPE, FOVY)
    assert abs(xx.mean() + 0.5 - u0) < 0.5 and abs(yy.mean() + 0.5 - v0) < 0.5
    assert c.truth["visible"].tolist() == [True, False, False] and (c.images[1:] == 120).all()
    assert spot_clip(az, 0.0, SHAPE, FOVY).sha256 == spot_clip(az, 0.0, SHAPE, FOVY).sha256       # deterministyczny

    sweep = spot_clip(np.linspace(-0.4, 0.4, 100), 0.0, SHAPE, FOVY)
    # nominalnie: wszystkie użyte, dt = okres, bez flag
    g = gate()
    out = run(g, replay(sweep, P))
    assert all(s.usable and not s.flags for s in out) and np.allclose([s.dt for s in out[1:]], P)
    assert g.stats["usable"] == 100 and g.stats["lost"] == 0

    # utrata 2 klatek: przeskok seq, faktyczne dt = 3 okresy, bez resetu; utrata 10 → reset filtrów
    s = {x.frame.seq: x for x in run(gate(), replay(sweep, P, drop={10, 11}))}
    assert s[12].lost == 2 and set(s[12].flags) == {"gap", "late"} and math.isclose(s[12].dt, 3 * P) and s[12].usable
    s = {x.frame.seq: x for x in run(gate(), replay(sweep, P, drop=range(10, 20)))}
    assert "reset" in s[20].flags and s[20].usable

    # brak obrazu: dostarczona, nieużyta, NIE liczona jako utracona; następna ma dt od ostatniego obrazu
    g = gate()
    s = {x.frame.seq: x for x in run(g, replay(sweep, P, blank={5}))}
    assert not s[5].usable and s[5].flags == ("no_image",) and s[6].lost == 0 and math.isclose(s[6].dt, 2 * P)
    assert g.stats["no_image"] == 1 and g.stats["lost"] == 0 and g.stats["usable"] == 99

    # opóźnienie: wiek > max_age → nieaktualna i nieużyta; jitter jako tablica opóźnień
    jit = np.zeros(100)
    jit[40] = 0.08
    s = {x.frame.seq: x for x in run(gate(), replay(sweep, P, delay=jit))}
    assert not s[40].usable and "stale" in s[40].flags and math.isclose(s[40].age, 0.08) and s[41].usable

    # duplikat i klatka spoza kolejności: odrzucone, stan bramki bez zmian
    g, fr = gate(), list(replay(sweep, P))
    run(g, fr[:5])
    assert run(g, [fr[4]])[0].flags == ("duplicate",) and run(g, [fr[2]])[0].flags == ("out_of_order",)
    assert g.last.seq == 4 and g.stats["usable"] == 5

    # zamrożony obraz: bajtowo identyczny przy nowym seq → flaga, decyzja u konsumenta
    out = run(gate(), replay(spot_clip(np.zeros(4), 0.0, SHAPE, FOVY), P))
    assert [("frozen" in x.flags) for x in out] == [False, True, True, True] and all(x.usable for x in out)

    # naruszenia kontraktu → błąd, nie naprawa
    f = fr[0]
    assert raises(gate().push, replace(f, image=f.image[:, :64]), 1.0)
    assert raises(gate().push, replace(f, image=f.image.astype(np.float32)), 1.0)
    assert raises(gate().push, replace(f, t_capture=math.nan), 1.0)
    assert raises(gate().push, replace(f, t_receive=f.t_capture - 0.001), 1.0)
    assert raises(gate().push, replace(f, proprio=np.array([0.0, math.inf])), 1.0)
    assert raises(gate().push, f, f.t_receive - 0.001)
    g = gate()
    g.push(fr[1], 1.0)
    assert raises(g.push, Frame(2, fr[1].t_capture, 1.0, fr[2].image), 1.0)                      # czas nie rośnie
    assert raises(SensoryGate, SHAPE, 0.01, 0.005, 0.05)                                          # max_age < period

    # zapis/odczyt klipu: wierne, wykrywa zmianę obrazów i niezgodną długość prawdy
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "sweep.npz")
        save_clip(p, sweep)
        back = load_clip(p)
        assert back.sha256 == sweep.sha256 and np.array_equal(back.truth["az"], sweep.truth["az"])
        bad = replace(sweep, images=sweep.images.copy())
        save_clip(p, bad)
        with np.load(p) as z:
            arrs = dict(z)
        arrs["images"][0, 0, 0, 0] ^= 1
        np.savez(p, **arrs)
        assert raises(load_clip, p)
        arrs = {**arrs, "images": sweep.images, "truth_az": sweep.truth["az"][:50]}
        np.savez(p, **arrs)
        assert raises(load_clip, p)
    print("OK: interfejs sensoryczny (26 asercji)")


if __name__ == "__main__":
    main()
