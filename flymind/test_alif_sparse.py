"""Test SparseALIF: identyczne spike'i i stan jak ALIF (gęsty) na prawdziwych sieciach z MaleCNS, plus pomiar czasu.
Bez szumu (noise = 0), więc generator losowy nie jest używany: seed=None, żadne ziarno nie jest zużywane.
Sieci: ścieżka wzrokowa LC10a → DNa02 (visual_path, J0 = 0,2 jak loop.py) i obwód lewej środkowej nogi (leg_circuit T2 L).
Uruchom:  .venv/bin/python -I -B flymind/test_alif_sparse.py"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alif import ALIF, ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402
import leg_circuit  # noqa: E402
import visual_path  # noqa: E402

P = ALIFParams()                               # parametry zamrożone, bez zmian
STEPS = 600


def compare(spec, inputs, label):
    I = np.zeros((STEPS, spec.W.shape[0]))
    I[:300, inputs] = 20.0                    # mV przez 300 ms, potem cisza (protokół jak alif.validate)
    out, dt = {}, {}
    for name, cls in (("dense", ALIF), ("sparse", SparseALIF)):
        net = cls(spec, P, None)
        t0 = time.perf_counter()
        s = net.run(I, STEPS)
        dt[name] = (time.perf_counter() - t0) / STEPS * 1000
        out[name] = (s, net.v.copy(), net.g.copy(), net.a.copy())
    (sd, vd, gd, ad), (ss, vs, gs, as_) = out["dense"], out["sparse"]
    assert sd.any(), f"{label}: sieć milczy — test nic nie sprawdza"
    assert (sd == ss).all(), f"{label}: spike'i różnią się w {int((sd != ss).sum())} miejscach"
    for x, y in ((vd, vs), (gd, gs), (ad, as_)):
        assert np.allclose(x, y, atol=1e-9), f"{label}: stan różny o {np.abs(x - y).max()}"
    print(f"  {label}: N = {spec.W.shape[0]}, spike'ów {int(sd.sum())}, gęsta {dt['dense']:.3f} ms/krok, "
          f"rzadka {dt['sparse']:.3f} ms/krok")
    return dt


def main():
    spec, idx, _ = visual_path.network(0.2)
    compare(spec, np.r_[idx["in_L"], idx["in_R"]], "LC10a→DNa02")
    spec, idx, rep = leg_circuit.network(0.2, "T2", "L")
    bristle = idx["sensory"]["mechanosensory bristle"]
    dt = compare(spec, bristle, f"noga T2 L (bez NT: {rep['unsigned']['no_nt']} ciał, znak 0)")
    assert dt["sparse"] * 10 < 10.0, f"takt 10 ms (10 kroków) trwa {dt['sparse'] * 10:.1f} ms"
    print(f"OK: SparseALIF = ALIF (identyczne spike'i i stan); takt 10 ms obwodu nogi liczy się {dt['sparse'] * 10:.1f} ms")


if __name__ == "__main__":
    main()
