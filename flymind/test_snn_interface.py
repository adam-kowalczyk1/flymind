"""Testy izolowane interfejsu connectom → SNN (dane syntetyczne; bez bio2, mujoco i plików MaleCNS).
Uruchom:  .venv/bin/python -I -B flymind/test_snn_interface.py"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from connectome import ConnectomeError  # noqa: E402
from snn_interface import ModelEdge, ModelParams, assign_nt, build  # noqa: E402

E = pd.DataFrame(dict(body_pre=[1, 2, 3, 9], body_post=[2, 3, 1, 1], weight=[5, 7, 2, 4]))
NT = pd.DataFrame(dict(body=[1, 2, 3, 4],
                       ground_truth=[None, "gaba", None, None],
                       consensus_nt=["acetylcholine", "acetylcholine", "unclear", "unclear"],
                       celltype_predicted_nt=["acetylcholine", "acetylcholine", "glutamate", "unclear"]))


def raises(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except ConnectomeError:
        return True
    return False


def main():
    # przekaźnik: ground_truth > consensus > celltype; 'unclear' = brak; braki tylko przez override z uzasadnieniem
    nt = assign_nt([1, 2, 3], NT)
    assert nt.nt.tolist() == ["acetylcholine", "gaba", "glutamate"]
    assert nt.nt_source.tolist() == ["consensus_nt", "ground_truth", "celltype_predicted_nt"]
    assert raises(assign_nt, [4], NT)
    assert raises(assign_nt, [4], NT, {4: ("acetylcholine", "")})
    assert assign_nt([4], NT, {4: ("acetylcholine", "test")}).nt_source[0] == "override: test"

    # orientacja [post, pre], znak presynaptyczny, krawędź 9→1 spoza sieci policzona
    s = build(E, [1, 2, 3], NT)
    assert s.W_data[1, 0] == 5 and s.W_data[0, 1] == 0        # 1(ACh)→2: +5 w wierszu post=2
    assert s.W_data[2, 1] == -7                               # 2(GABA)→3: −7
    assert s.W_data[0, 2] == -2                               # 3(Glu)→1: −2 (założenie GluCl)
    assert s.report["data"] == dict(edges=3, synapses=14, self_loops=0, dropped_outside=1)

    # parametry modelu oddzielone od danych
    s2 = build(E, [1, 2, 3], NT, ModelParams(J0=0.5, transform="log1p"))
    assert np.isclose(s2.W_data[1, 0], 0.5 * np.log1p(5)) and (np.sign(s2.W_data) == np.sign(s.W_data)).all()
    assert raises(build, E, [1, 2, 3], NT, ModelParams(transform="sqrt"))
    assert raises(build, E, [1, 2, 3], NT, ModelParams(sign_map={"acetylcholine": 1.0}))

    # krawędzie modelowe: osobna macierz, wyłączalne, nie nadpisują danych
    me = [ModelEdge(1, 3, 4.0, "test: brak w danych")]
    s3 = build(E, [1, 2, 3], NT, model_edges=me)
    assert s3.W_model[2, 0] == 4 and (s3.W_data == s.W_data).all() and np.count_nonzero(s3.W_model) == 1
    assert s3.report["model"]["edges"] == 1 and s3.report["W_sha256"] != s.report["W_sha256"]
    s4 = build(E, [1, 2, 3], NT, model_edges=me, include_model=False)
    assert not s4.W_model.any() and s4.report["W_sha256"] == s.report["W_sha256"]
    assert raises(build, E, [1, 2, 3], NT, model_edges=[ModelEdge(1, 3, 4.0, "")])
    assert raises(build, E, [1, 2, 3], NT, model_edges=[ModelEdge(1, 2, 4.0, "x")])     # istnieje w danych
    assert raises(build, E, [1, 2, 3], NT, model_edges=[ModelEdge(1, 9, 4.0, "x")])     # spoza sieci
    assert raises(build, E, [1, 1, 2], NT)

    # deterministyczność
    assert build(E, [1, 2, 3], NT).report["W_sha256"] == s.report["W_sha256"]
    print("OK: 20 sprawdzeń interfejsu connectom → SNN")


if __name__ == "__main__":
    main()
