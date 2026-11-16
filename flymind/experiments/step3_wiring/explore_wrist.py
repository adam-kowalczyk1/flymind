"""Krok 5, eksploracja bez robota (szum 0): czy naturalne czucie — dotyk, czujniki kąta „kolana” (FeCO: SNpp50/51/39/41),
płytki włosków (SNpp45, SNpp52) — pojedynczo i w parach pobudza pule stępu (nadgarstek) w sieci „pre” + receptory dodatkowe.
Każdy bodziec 40 mV, 1 s; częstości z ostatnich 0,5 s. Uruchom: explore_wrist.py OUT.json"""
import itertools
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nets  # noqa: E402
import nets2  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402

JN = nets.JN


def main(out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    ex = nets2.extra_sensory()
    res = {}
    for glu in (1.0, -1.0):
        spec, idx, rep, layer, pos, m = nets2.build_ext(glu, list(ex))
        ty = m["a"].set_index("bodyId").type
        sens1 = [b for v in m["g1"]["sensory"].values() for b in v]
        chan = {"dotyk": [i for n in ("padsT2", "padsT1") for h in idx[n] for i in h],
                "FeCO_claw_flex(SNpp50)": idx["feco"]["claw_flex"], "FeCO_claw_ext(SNpp51)": idx["feco"]["claw_ext"],
                "FeCO_hook_flex(SNpp41)": idx["feco"]["hook_flex"], "FeCO_hook_ext(SNpp39)": idx["feco"]["hook_ext"],
                "plytki_SNpp45": [pos[b] for b, v in ex.items() if v[2] == "SNpp45"],
                "plytki_SNpp52": [pos[b] for b, v in ex.items() if v[2] == "SNpp52"],
                "szczecinki_SNta33": [pos[b] for b, v in ex.items() if v[2] == "SNta33"]}
        for t in sorted({str(ty.get(b)) for b in sens1 if str(ty.get(b)).startswith("SNpp")} - {"SNpp50", "SNpp51", "SNpp41", "SNpp39", "SNppxx"}):
            chan[f"inne_{t}"] = [pos[b] for b in sens1 if str(ty.get(b)) == t]
        sizes = {k: len(v) for k, v in chan.items()}
        rows = {}
        combos = [(k,) for k in chan] + [c for c in itertools.combinations(chan, 2)]
        for c in combos:
            net = SparseALIF(JN.LB._W(spec.W), ALIFParams(), None)
            X = np.zeros(spec.W.shape[0])
            for k in c:
                X[chan[k]] = 40.0
            S = np.concatenate([net.run(X, 10) for _ in range(100)])[500:]
            r = {nets.NAMES[j][q]: round(float(S[:, ix].mean() * 1000), 1) for j, pq in idx["pools"].items() for q, ix in enumerate(pq)}
            rows[" + ".join(c)] = r
            if r["j3+ Ta lev"] >= 1 or r["j3- Ta dep"] >= 1:
                print(f"Glu {glu:+.0f} {' + '.join(c):52s} Ta lev {r['j3+ Ta lev']:6.1f}  Ta dep {r['j3- Ta dep']:6.1f} | bark {r['j1+ wymach']:.0f}/{r['j1- podpór']:.0f} łokieć {r['j2+ Ti flex']:.0f}/{r['j2- Ti ext']:.0f}", flush=True)
        res[f"glu{glu:+.0f}"] = dict(rep=rep, channel_sizes=sizes, rows=rows)
        print(f"Glu {glu:+.0f}: kanały {sizes}; kombinacji {len(combos)}; z odpowiedzią stępu ≥ 1 Hz: {sum(1 for r in rows.values() if r['j3+ Ta lev'] >= 1 or r['j3- Ta dep'] >= 1)}", flush=True)
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1])
