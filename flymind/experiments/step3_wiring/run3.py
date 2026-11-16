"""Krok 3 — próby w pętli z ramieniem dla sieci zbudowanej inną regułą z danych i z dwoma rodzajami tasowań.
Niczego nie zmienia w kroku 2 ani w modułach wspólnych: importuje joint_net i W PAMIĘCI podmienia klasę sieci ramienia.

Dodatkowe opcje (reszta jak joint_net.py):
  --rule base|pre|pre2|full2     reguła wyboru neuronów (nets.py)
  --kind free|layer              rodzaj tasowania dla --arm S: free = visual_path.shuffle(equal_weight=True) (jak w kroku 2),
                                 layer = side_shuffle.shuffle_within_side z grupami receptory / interneurony / MN
Ziarna testowe kroku 3 (TEST3) tylko z STEP3_FINAL_TEST=1; ziarna testowe kroku 2 blokuje joint_net.
"""
import hashlib
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nets  # noqa: E402
import side_shuffle  # noqa: E402

JN = nets.JN
TEST3 = {21201, 21301}
CFG = dict(rule="pre", kind="free")


def pop(flag, default, choices):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        v = sys.argv[i + 1]
        del sys.argv[i:i + 2]
        if v not in choices:
            sys.exit(f"{flag}: {v!r} spoza {choices}")
        return v
    return default


class ArmNet3(JN.ArmNet):
    def __init__(self, glu, ac, shuffle_seed=None):
        spec, self.idx, rep, layer = nets.build_rule(glu, ac.J0, CFG["rule"])
        self.rep = dict(rep, shuffle_kind=None)
        if shuffle_seed is not None:
            if CFG["kind"] == "free":
                spec = JN.visual_path.shuffle(spec, shuffle_seed, equal_weight=True)
            else:
                spec = side_shuffle.shuffle_within_side(spec, np.array(layer, str), shuffle_seed)
            self.rep = dict(self.rep, shuffle_seed=shuffle_seed, shuffle_kind=CFG["kind"],
                            W_sha256_shuffled=hashlib.sha256(np.ascontiguousarray(spec.W).tobytes()).hexdigest())
        self.W, self.N, self.ac = spec.W, spec.W.shape[0], ac
        self.nsteps = int(round(10.0 / ac.dt_ms))
        self.reset()


def main():
    CFG["rule"] = pop("--rule", "pre", ("base", "pre", "pre2", "full2"))
    CFG["kind"] = pop("--kind", "free", ("free", "layer"))
    if "--seed" in sys.argv:
        s = int(sys.argv[sys.argv.index("--seed") + 1])
        if s in TEST3 and not os.environ.get("STEP3_FINAL_TEST"):
            sys.exit("ziarna testowe kroku 3 tylko w teście końcowym (STEP3_FINAL_TEST=1)")
    JN.ArmNet = ArmNet3
    JN.main()


if __name__ == "__main__":
    main()
