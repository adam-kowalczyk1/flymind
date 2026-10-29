"""Testy izolowane modułu A (syntetyczne pliki w katalogu tymczasowym; bez bio2, bez mujoco, bez danych MaleCNS).
Uruchom:  .venv/bin/python -B flymind/test_connectome.py"""
import os
import sys
import tempfile

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from connectome import ConnectomeError, direction, load_edges, map_populations, validate_edges  # noqa: E402

GOOD = pd.DataFrame(dict(body_pre=[1, 1, 2, 3, 4], body_post=[2, 3, 3, 1, 4], weight=[5, 1, 7, 2, 3]))


def raises(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except ConnectomeError:
        return True
    return False


def main():
    with tempfile.TemporaryDirectory() as tmp:
        def write(df, name="w-minconf-0.5.feather"):
            p = os.path.join(tmp, name)
            df.reset_index(drop=True).to_feather(p)
            return p

        df, rep = load_edges(write(GOOD))
        assert rep["rows_in_file"] == 5 and rep["loaded"] == dict(edges=5, synapses=18, self_loops=1, bodies=4)
        assert rep["provenance"]["minconf"] == 0.5 and "sha256" in load_edges(write(GOOD), sha256=True)[1]["provenance"]

        # confidence: inny próg niż zaszyty w pliku albo brak progu w nazwie → odmowa
        assert raises(load_edges, write(GOOD), minconf=0.7)
        assert raises(load_edges, write(GOOD, "weights.feather"))

        # schemat i wartości
        assert raises(load_edges, write(GOOD.drop(columns="weight")))
        assert raises(validate_edges, GOOD.assign(weight=GOOD.weight.astype(float)))
        assert raises(validate_edges, GOOD.assign(body_pre=GOOD.body_pre.astype(str)))
        assert raises(load_edges, write(GOOD.iloc[:0]))
        assert raises(validate_edges, GOOD.assign(weight=pd.array([5, None, 7, 2, 3], "Int64")))
        assert raises(validate_edges, GOOD.assign(body_pre=[0, 1, 2, 3, 4]))
        assert raises(validate_edges, GOOD.assign(weight=[5, 0, 7, 2, 3]))
        assert raises(load_edges, write(pd.concat([GOOD, GOOD.iloc[:1]])))

        # podgraf indukowany + ciała bez krawędzi
        sub, rep = load_edges(write(GOOD), bodies=[1, 2, 99])
        assert sub[["body_pre", "body_post"]].values.tolist() == [[1, 2]] and rep["bodies_without_edges"] == [99]

        # jawny próg liczby synaps
        _, rep = load_edges(write(GOOD), min_weight=3)
        assert rep["loaded"]["edges"] == 5 and rep["after_min_weight"] == dict(edges=3, synapses=15)

    # kierunek: 1→2 ma 5 synaps, 2→1 nie istnieje
    assert direction(GOOD, [1], [2]) == (5, 0)

    # populacje
    ann = pd.DataFrame(dict(bodyId=[1, 2, 3, 4], type=["DNa02", "DNa02", "PFL3", "X"], somaSide=["L", "R", "L", "L"]))
    pops, rep = map_populations(ann, {"DNa02_L": dict(type="DNa02", somaSide="L"), "PFL3": dict(type="PFL3")})
    assert pops["DNa02_L"].tolist() == [1] and rep["sizes"] == {"DNa02_L": 1, "PFL3": 1}
    assert raises(map_populations, ann, {"DNa01": dict(type="DNa01")})
    assert map_populations(ann, {"DNa01": dict(type="DNa01")}, strict=False)[1]["empty"] == ["DNa01"]
    assert raises(map_populations, ann, {"a": dict(type="DNa02"), "b": dict(somaSide="R")})
    assert raises(map_populations, ann, {"a": dict(cell_class="DN")})
    print("OK: 20 sprawdzeń modułu A")


if __name__ == "__main__":
    main()
