"""Krok 6 r3 — wycięcie jednego szlaku na teście z sondą (brainleg_probe.py bez zmian): `--lesion d15` zeruje wyjścia
2 neuronów DNg15, `--lesion d78` — 2 neuronów DNge078 (neurony zostają, nie wysyłają nic). Przewidywanie: bez DNg15 stoi
łokieć, bez DNge078 stoi nadgarstek (podwójna dysocjacja). Cel: LOOP_TARGET_brainleg_r3.md.
Uruchom: brainleg_lesion.py --lesion d15|d78 --net N --glu ±1 --seed S --poses P --tag T --out DIR (ziarno testowe tylko z STEP6C_FINAL_TEST=1)"""
import os
import sys

import numpy as np
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brainleg as B  # noqa: E402
import brainleg_probe as P  # noqa: E402
import reflex as R  # noqa: E402

TEST6C = {21891}

if __name__ == "__main__":
    i = sys.argv.index("--lesion")
    lesion = sys.argv[i + 1]
    del sys.argv[i:i + 2]
    assert lesion in ("d15", "d78") and sys.argv[sys.argv.index("--net") + 1] == "N"
    s = int(sys.argv[sys.argv.index("--seed") + 1])
    if s in P.TEST6B | B.TEST6:
        sys.exit("ziarna testów r1/r2 są zużyte")
    if s in TEST6C and not os.environ.get("STEP6C_FINAL_TEST"):
        sys.exit("ziarna testowe kroku 6 r3 tylko w teście końcowym (STEP6C_FINAL_TEST=1)")
    P.install()
    _init = B.BrainNet.__init__

    def init(self, glu, kind="N", shuffle_seed=None, rule="pre"):
        _init(self, glu, kind, shuffle_seed, rule)
        bm, d78, d15 = B.route_ids()
        _, _, _, _, pos, _ = B.nets2.build_ext(glu, bm + d78 + d15)
        cut = [pos[b] for b in (d15 if lesion == "d15" else d78)]
        mask = np.ones(self.N)
        mask[cut] = 0.0
        self.W = sp.csr_matrix(self.W.multiply(mask[None, :])) if sp.issparse(self.W) else self.W * mask[None, :]
        self.rep.update(lesion=lesion, lesion_idx=cut, lesion_out_nnz_left=int((abs(self.W[:, cut]) > 0).sum()))
        self.reset()

    B.BrainNet.__init__ = init
    R.main()
