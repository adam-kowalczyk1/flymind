"""Testy izolowane dynamiki ALIF (sieci syntetyczne, wyniki analityczne; bez bio2, mujoco i danych MaleCNS).
Ziarna RNG 1001–1002 (poza zakresami protokołu Stage 1). Uruchom:  .venv/bin/python -I -B flymind/test_alif.py"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alif import ALIF, ALIFParams, rates, validate  # noqa: E402
from connectome import ConnectomeError  # noqa: E402
from snn_interface import build  # noqa: E402

NT = pd.DataFrame(dict(body=[1, 2, 3], ground_truth=[None] * 3, consensus_nt=["acetylcholine", "acetylcholine", "gaba"],
                       celltype_predicted_nt=["unclear"] * 3))
NOP = ALIFParams(b_a=0.0)


def spec(edges, bodies=(1, 2, 3)):
    e = pd.DataFrame(edges or [(8, 9, 1)], columns=["body_pre", "body_post", "weight"])
    return build(e, list(bodies), NT)


def raises(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except ConnectomeError:
        return True
    return False


def main():
    one = spec(None, [1])
    # cisza: brak bodźca i szumu → punkt stały V_rest, zero spike'ów
    assert validate(spec([(1, 2, 20)]), NOP, 1001, I_on=0.0)["silent_fixed_point"]

    # analitycznie (Euler, dt/τ_m = 0,05): I = 20 mV → v_n = −32 − 20·0,95^n ≥ −45 przy n = 9;
    # pierwszy spike w kroku 8, potem 3 kroki refrakcji + 9 kroków całkowania = okres 12 kroków
    t = np.flatnonzero(ALIF(one, NOP, 1001).run(20.0, 1200)[:, 0])
    assert t[0] == 8 and (np.diff(t) == 12).all()
    # górna granica: okres 4 kroki → 250 Hz = r_max (refrakcja 2,2 ms skwantowana do 3 kroków)
    assert rates(ALIF(one, NOP, 1001).run(1e4, 1000), 1.0)[0] == NOP.r_max == 250.0

    # opóźnienie: spike 1 w kroku k → prąd w 2 pojawia się w kroku k + delay_steps
    for delay_ms, d in ((1.8, 2), (3.0, 3)):
        net, first_spk, first_g = ALIF(spec([(1, 2, 3)]), ALIFParams(b_a=0.0, delay_ms=delay_ms), 1001), None, None
        for k in range(30):
            s = net.step(np.array([50.0, 0, 0]))
            first_spk = k if first_spk is None and s[0] else first_spk
            first_g = k if first_g is None and net.g[1] > 0 else first_g
        assert first_g - first_spk == d

    # znak: hamujący 3(GABA) → 2 obniża częstość 2 przy tym samym prądzie własnym
    inh = spec([(3, 2, 10)])
    r_free = rates(ALIF(inh, NOP, 1001).run([0, 10.0, 0], 1000), 1.0)[1]
    r_inh = rates(ALIF(inh, NOP, 1001).run([0, 10.0, 30.0], 1000), 1.0)[1]
    assert r_free > 0 and r_inh < r_free and inh.W[1, 2] < 0

    # adaptacja: b_a > 0 → częstość spada w czasie; b_a = 0 → stała
    s = ALIF(one, ALIFParams(), 1001).run(20.0, 1000)
    assert rates(s[:100], 1.0)[0] > rates(s[-100:], 1.0)[0]

    # deterministyczność: to samo ziarno → identycznie; szum + inne ziarno → inaczej; bez szumu ziarno bez znaczenia
    noisy = ALIFParams(noise=2.0)
    rep = validate(spec([(1, 2, 20)]), noisy, 1001, I_on=[10.0, 0, 0], other_seed=1002)
    assert rep["deterministic"] and rep["seed_changes_noise"]
    assert (ALIF(one, NOP, 1001).run(15.0, 300) == ALIF(one, NOP, 1002).run(15.0, 300)).all()

    # stabilność: sieć jednokierunkowa wygasa; pętla pobudzająca trwa po bodźcu; nasycenie wykrywane
    ff = validate(spec([(1, 2, 20)]), NOP, 1001, I_on=[20.0, 0, 0])
    assert ff["extinct_after_off"] and not ff["runaway"] and ff["saturated_frac"] == 0
    loop = validate(spec([(1, 2, 50), (2, 1, 50)]), NOP, 1001, I_on=[20.0, 0, 0], on_ms=50)
    assert not loop["extinct_after_off"] and loop["runaway"]
    assert validate(spec([(1, 2, 20)]), NOP, 1001, I_on=1e4)["saturated_frac"] == 1.0

    # odmowy: zbyt duży dt, opóźnienie < 1 krok, NaN w wejściu
    assert raises(ALIF, one, ALIFParams(dt=5.0), 1001)
    assert raises(ALIF, one, ALIFParams(delay_ms=0.2), 1001)
    assert raises(ALIF(one, NOP, 1001).run, np.nan, 10)
    print("OK: dynamika ALIF (14 asercji)")


if __name__ == "__main__":
    main()
