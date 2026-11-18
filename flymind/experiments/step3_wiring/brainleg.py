"""Krok 6 — dwa szlaki z głowy do nogi na robocie (cel: LOOP_TARGET_brainleg_r1.md). Sieć: „pre” + BM (69) + DNge078 (2) + DNg15 (2).
Trial W (dotyk dłoni przy głowie, jak w reflex5/krok 5b; F_ON 3 N) mierzy ruch łokcia (dq2) i nadgarstka (dq3) — trial5 zapisuje oba.
Kryteria liczy analyze_brainleg.py. Bez zmian w reflex5/trial5 — tylko inna sieć (podmiana HeadNet w pamięci).
Uruchom: brainleg.py --net N|F|L --glu ±1 --seed S --poses P --tag T --out DIR (ziarno testowe 21831 tylko z STEP6_FINAL_TEST=1)"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nets  # noqa: E402
import nets2  # noqa: E402
import reflex as R  # noqa: E402
import reflex5 as R5  # noqa: E402

TEST6 = {21831}


def route_ids():
    a = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "type", "superclass"])
    bm = [int(b) for b in a.bodyId[(a.type == "BM") & (a.superclass == "cb_sensory")]]
    d78 = [int(b) for b in a.bodyId[a.type == "DNge078"]]
    d15 = [int(b) for b in a.bodyId[a.type == "DNg15"]]
    return bm, d78, d15


class BrainNet(R5.HeadNet):
    def __init__(self, glu, kind="N", shuffle_seed=None, rule="pre"):
        bm, d78, d15 = route_ids()
        import hashlib
        spec, idx, rep, layer, pos, m = nets2.build_ext(glu, bm + d78 + d15)
        from alif import ALIFParams  # noqa: F401
        bodies = [None] * len(pos)
        for b, i in pos.items():
            bodies[i] = b
        import explore_specificity as ES
        t2, t1 = ES.mn_sets(bodies, m)
        layer = np.array(layer, object)
        for b in d78 + d15:
            layer[pos[b]] = "I"
        self.rep = dict(rep, kind=kind, shuffle_seed=shuffle_seed, n_BM=len(bm), n_DNge078=len(d78), n_DNg15=len(d15))
        if kind != "N":
            import side_shuffle
            g = layer.copy()
            if kind == "B":
                for b in bm:
                    g[pos[b]] = "S_BM"
                for b in d78 + d15:
                    g[pos[b]] = "I_DN"
            spec = JN_v().shuffle(spec, shuffle_seed, equal_weight=True) if kind == "F" else \
                side_shuffle.shuffle_within_side(spec, np.array(g, str), shuffle_seed)
            self.rep["W_sha256_shuffled"] = hashlib.sha256(np.ascontiguousarray(spec.W).tobytes()).hexdigest()
        mn2 = m["g2"]["MN"]
        self.press = [pos[int(b)] for b in mn2.get("Ti extensor MN", [])]
        self.release = [pos[int(b)] for k in ("Ti flexor MN", "Acc. ti flexor MN") for b in mn2.get(k, [])]
        self.pads, self.palm = idx["padsT2"], [pos[b] for b in bm]
        self.pools = {j: idx["pools"][j] for j in (1, 2, 3)}
        self.W, self.N = spec.W, spec.W.shape[0]
        self.rep.update(press_MN=len(self.press), release_MN=len(self.release), palm_receptors=len(self.palm),
                        pad_receptors=[len(x) for x in self.pads])
        self.reset()


def JN_v():
    return nets.visual_path


if __name__ == "__main__":
    if "--seed" in sys.argv and int(sys.argv[sys.argv.index("--seed") + 1]) in TEST6 and not os.environ.get("STEP6_FINAL_TEST"):
        sys.exit("ziarna testowe kroku 6 tylko w teście końcowym (STEP6_FINAL_TEST=1)")
    R.F_ON = 3.0
    R.TwoNet = BrainNet
    R.trial = R5.trial5
    R.main()
