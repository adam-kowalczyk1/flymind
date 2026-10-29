"""Testy izolowane dekodera motorycznego (spike'i syntetyczne, wyniki analityczne; bez bio2, mujoco i danych MaleCNS).
Uruchom:  .venv/bin/python -I -B flymind/test_decoder.py"""
import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decoder import (MN_CLASS, DecoderError, GripDecoder, SteerDecoder, SteerParams, channel_provenance,  # noqa: E402
                     fit_steer, size_classes)
from snn_interface import ModelEdge, build  # noqa: E402

IDX = {"DNa02_L": [0], "DNa02_R": [1], "DNa01_L": [2], "DNa01_R": [3]}
FAST = SteerParams(tau_rate_ms=1e-9)          # częstość = chwilowa (a = 0) → odczyt d̃ zależy tylko od τ kanału


def raises(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except DecoderError:
        return True
    return False


def spikes(k, n, on):
    s = np.zeros((k, n), bool)
    s[:, on] = True
    return s


def main():
    # kalibracja: dokładna prosta odzyskana; kanał płaski (DNa01 bez wejścia) odrzucony, nie liczony z zerem
    x = np.radians([-30, 0, 30])
    off, sl = fit_steer(x, np.c_[2 + 40 * x, -3 + 10 * x], min_slope=1.0)
    assert np.allclose(off, [2, -3]) and np.allclose(sl, [40, 10])
    assert raises(fit_steer, x, np.c_[2 + 40 * x, np.zeros(3)], 1.0)
    assert raises(fit_steer, [0.1, 0.1], [[1.0], [2.0]], 1.0)

    # skręt: L = R → 0; filtr kanału dokładnie 1 − exp(−T/τ); znak L > P przy slope > 0 → + (w lewo)
    dec = SteerDecoder(IDX, ("DNa02", "DNa01"), [0, 0], [1000, 1000], FAST)
    assert dec.step(spikes(10, 4, [0, 1, 2, 3]), 1.0)["omega"] == 0.0
    dec.reset()
    o = dec.step(spikes(10, 4, [0]), 1.0)
    assert math.isclose(o["angle"][0], 1 - math.exp(-0.01 / 0.10)) and o["angle"][1] == 0 and o["omega"] > 0
    assert math.isclose(o["omega"], 2.5 * o["angle"].mean())
    # nasycenie: kąt 1 rad w obu kanałach → 2,5 rad/s surowo, 1,0 po przycięciu i flaga
    for _ in range(300):
        o = dec.step(spikes(10, 4, [0, 2]), 1.0)
    assert math.isclose(o["omega_raw"], 2.5, rel_tol=1e-3) and o["omega"] == 1.0 and o["clipped"]

    # trym: start od offset → brak impulsu skrętu przy stałej różnicy równej trymowi (bio2: błąd „impuls w lewo”)
    d2 = SteerDecoder({"DNa02_L": [0], "DNa02_R": [1]}, ("DNa02",), [1000.0], [500.0], FAST)
    assert d2.step(spikes(10, 2, [0]), 1.0)["omega"] == 0.0

    # częstość: EMA τ_rate = 50 ms przy stałym 1 spike/krok → 1000·(1 − e^(−t/50))
    d3 = SteerDecoder({"DNa02_L": [0], "DNa02_R": [1]}, ("DNa02",), [0.0], [1.0])
    d3.step(spikes(100, 2, [0]), 1.0)
    assert math.isclose(d3.r[0], 1000 * (1 - math.exp(-100 / 50))) and d3.r[1] == 0

    # odmowy: pusta populacja, slope 0, zły typ spike'ów, za mało neuronów, niespójne długości
    assert raises(SteerDecoder, {"DNa02_L": [0]}, ("DNa02",), [0], [1])
    assert raises(SteerDecoder, IDX, ("DNa02",), [0], [0])
    assert raises(dec.step, spikes(10, 4, [0]).astype(float), 1.0)
    assert raises(dec.step, spikes(10, 3, [0]), 1.0)
    assert raises(SteerDecoder, IDX, ("DNa02", "DNa01"), [0], [1])

    # pochodzenie kanału: udział krawędzi modelowych w wejściu populacji
    nt = pd.DataFrame(dict(body=[1, 2, 3], ground_truth=[None] * 3, consensus_nt=["acetylcholine"] * 3,
                           celltype_predicted_nt=["unclear"] * 3))
    e = pd.DataFrame(dict(body_pre=[1], body_post=[2], weight=[3]))
    sp = build(e, [1, 2, 3], nt, model_edges=[ModelEdge(1, 3, 3.0, "test")])
    assert channel_provenance(sp, [1])["model_frac"] == 0 and channel_provenance(sp, [2])["model_frac"] == 1
    assert math.isnan(channel_provenance(sp, [0])["model_frac"])

    # klasy MN wg rangi wejścia (największe → pierwsza klasa); zła długość → błąd
    assert size_classes([10, 50, 30], ["fast", "int", "slow"]) == ["slow", "fast", "int"]
    assert raises(size_classes, [1, 2], ["fast"])

    # mięsień: cisza → 0; zamykające 1 spike/krok → k·ΣF·tanh(1000/100) w stanie ustalonym; otwierające → znak −
    g = GripDecoder([0, 1], [2], ["fast", "slow"], ["int"])
    assert g.step(spikes(10, 3, []), 1.0)["torque"] == 0.0
    for _ in range(100):
        t = g.step(spikes(10, 3, [0, 1]), 1.0)["torque"]
    assert math.isclose(t, 0.40 * (MN_CLASS["fast"][0] + MN_CLASS["slow"][0]) * math.tanh(10), rel_tol=1e-9)
    g.reset()
    for _ in range(100):
        t = g.step(spikes(10, 3, [2]), 1.0)["torque"]
    assert math.isclose(t, -0.40 * MN_CLASS["int"][0] * math.tanh(10), rel_tol=1e-9)
    assert raises(GripDecoder, [0, 1], [1], ["fast", "slow"], ["int"])
    assert raises(GripDecoder, [0], [1], ["huge"], ["int"])
    print("OK: dekoder motoryczny (23 asercje)")


if __name__ == "__main__":
    main()
