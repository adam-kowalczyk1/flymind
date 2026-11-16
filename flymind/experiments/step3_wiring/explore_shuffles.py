"""Krok 3, etap 0b (eksploracja, bez robota): sieć „pre” — dane kontra tasowania swobodne (visual_path.shuffle, równa waga)
i tasowania zachowujące warstwy (side_shuffle.shuffle_within_side z grupami: receptory T2, receptory T1, interneurony, MN).
Bodziec: dotyk 1 N na oba pady, 1 s. Wynik: częstości 8 pul. Ziarna tasowań: 21 100 001–010 (rejestr).
Uruchom: .venv/bin/python -I -B .../explore_shuffles.py OUT.json"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import explore_rules as ER  # noqa: E402
import nets  # noqa: E402
import side_shuffle  # noqa: E402

RULE = "pre"


def groups_for(spec, idx, layer):
    g = layer.astype(object).copy()
    t2 = set(i for h in idx["padsT2"] for i in h)
    for i in np.flatnonzero(layer == "S"):
        g[i] = "S"                                    # receptory: jedna grupa (pady T2/T1 to podzbiory szczecinek)
    return np.array(g, str)


def main(out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res = {}
    for glu in (-1.0, 1.0):
        spec, idx, rep, layer = nets.build_rule(glu, 0.2, RULE)
        g = groups_for(spec, idx, layer)
        rows = {"N": ER.respond(spec.W, idx)[0]}
        for i in range(1, 6):
            sh = nets.visual_path.shuffle(spec, 21_100_000 + i, equal_weight=True)
            rows[f"S{i}"] = ER.respond(sh.W, idx)[0]
        for i in range(6, 11):
            sh = side_shuffle.shuffle_within_side(spec, g, 21_100_000 + i)
            rows[f"L{i - 5}"] = ER.respond(sh.W, idx)[0]
            rows[f"L{i - 5}_rep"] = {k: v for k, v in sh.report.items() if k in ("shuffle", "swaps", "complete")} if hasattr(sh, "report") else None
        res[f"glu{glu:+.0f}"] = dict(rep=rep, rows=rows)
        for k, v in rows.items():
            if not k.endswith("_rep"):
                print(glu, k.ljust(3), " ".join(f"{x:6.1f}" for x in v.values()), flush=True)
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False, default=str)


if __name__ == "__main__":
    print("pule:", " | ".join(n for j in nets.NAMES for n in nets.NAMES[j]))
    main(sys.argv[1])
