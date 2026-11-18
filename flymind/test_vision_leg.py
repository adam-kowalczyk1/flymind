"""Test vision_leg: sieć buduje się z danych, a bodziec wzrokowy na LC9 jednej strony pobudza tylko DNp09 tej strony.
Bez szumu (generator losowy nieużywany), bez ziaren.  Uruchom:  .venv/bin/python -I -B flymind/test_vision_leg.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402
from vision_leg import network  # noqa: E402


def main():
    spec, idx, rep = network(0.275, -1.0)
    assert rep["sizes"]["LC9_L"] > 50 and rep["sizes"]["LC9_R"] > 50 and set(rep["sizes"]["legs"]) == {"T2L", "T2R"}
    for side, other in (("L", "R"), ("R", "L")):
        X = np.zeros(spec.W.shape[0])
        X[idx["LC9"][side]] = 12.0
        r = SparseALIF(spec, ALIFParams(), None).run(X, 300)[50:].mean(0) * 1000
        assert r[idx["DNp09"][side]] > 50 and r[idx["DNp09"][other]] == 0, (side, r[idx["DNp09"][side]], r[idx["DNp09"][other]])
    print(f"OK: wzrok → DNp09 tylko po stronie bodźca; sieć {rep['sizes']['total']} neuronów")


if __name__ == "__main__":
    main()
