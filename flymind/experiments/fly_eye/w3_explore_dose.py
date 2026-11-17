"""W3 — EKSPLORACJA (argument: typ detektora, np. LPLC2; domyślnie LC4) struktury (bez robota, bez oka): czy droga LC4 R → neurony zstępujące → sieć nogi „pre” w ogóle porusza pule mięśni.
Sieć = „pre” + 55 LC4 R + neurony zstępujące z ≥ 100 synapsami od LC4 R (reguła z danych). Do LC4 podawany jest równy prąd próbny
(to diagnostyka połączeń, NIE bodziec zachowania — w teście wejściem będzie wyłącznie oko). .venv: w3_explore_dose.py"""
import os
import sys

import numpy as np
import pandas as pd

S3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "step3_wiring")
sys.path.insert(0, S3)
import nets  # noqa: E402
import nets2  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402

JN = nets.JN


VPN = sys.argv[1] if len(sys.argv) > 1 else "LC4"          # typ detektora (prawa strona); domyślnie LC4 jak 17 XI rano


def route():
    a = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "type", "superclass", "somaSide"])
    lc4 = sorted(int(b) for b in a.bodyId[(a.type == VPN) & (a.somaSide == "R")])
    w = pd.read_feather(nets.visual_path.WEIGHTS)
    e = w[w.body_pre.isin(lc4)]
    sc = a.set_index("bodyId").superclass
    dn = e[e.body_post.map(sc) == "descending_neuron"].groupby("body_post").weight.sum()
    dn = [int(b) for b in dn[dn >= 100].index]
    return lc4, dn, a.set_index("bodyId").type


if __name__ == "__main__":
    lc4, dn, ty = route()
    for glu in (1.0, -1.0):
        spec, idx, rep, layer, pos, m = nets2.build_ext(glu, lc4 + dn)
        W = JN.LB._W(spec.W)
        li = [pos[b] for b in lc4]; di = [pos[b] for b in dn]
        print(f"{VPN} | Glu {glu:+.0f}: N = {spec.W.shape[0]}, {VPN} {len(li)}, DN {len(di)}: {[str(ty[b]) for b in dn]}")
        for mv in (0.0, 10.0, 20.0, 40.0):
            net = SparseALIF(W, ALIFParams(), None)
            X = np.zeros(spec.W.shape[0]); X[li] = mv
            s = np.concatenate([net.run(X, 10) for _ in range(100)])[200:]          # 1 s, pomijam pierwsze 0,2 s
            hz = lambda ix: float(s[:, ix].mean() * 1000.0) if len(ix) else 0.0      # noqa: E731
            pools = {nets.NAMES[j][k]: round(hz(idx["pools"][j][k]), 1) for j in (1, 2, 3) for k in (0, 1)}
            print(f"  {VPN} {mv:4.0f} mV → {VPN} {hz(li):6.1f} Hz, DN {[round(hz([i]), 0) for i in di]}, pule: {pools}")
        # dokąd w ogóle dochodzi aktywność (LC4 40 mV): warstwy i neurony ruchowe wg typu
        act = s.mean(0) * 1000.0
        bodies = [None] * len(pos)
        for b, i in pos.items():
            bodies[i] = b
        lay = np.array(layer, object); lay[li] = "LC4"; lay[di] = "DN"
        print("  aktywne (> 1 Hz) przy 40 mV:", {k: f"{int((act[lay == k] > 1).sum())}/{int((lay == k).sum())}" for k in ("LC4", "DN", "S", "I", "M")}, "(LC4 = komórki detektora)")
        mn = [(str(ty.get(bodies[i])), round(float(act[i]), 1)) for i in np.where(lay == "M")[0] if act[i] > 1]
        print("  neurony ruchowe > 1 Hz:", mn if mn else "żaden")
        mn2 = m["g2"]["MN"]                                                          # noga środkowa T2 L = szczęka chwytaka (jak reflex.TwoNet)
        press = [pos[int(b)] for b in mn2.get("Ti extensor MN", [])]
        release = [pos[int(b)] for k in ("Ti flexor MN", "Acc. ti flexor MN") for b in mn2.get(k, [])]
        t2all = {pos[int(b)] for v in mn2.values() for b in v}
        print(f"  noga środkowa T2 L: pula zaciskania {hz(press):.1f} Hz ({len(press)} MN), pula puszczania {hz(release):.1f} Hz ({len(release)} MN);"
              f" aktywne MN należące do T2: {sum(1 for i in np.where(lay == 'M')[0] if act[i] > 1 and i in t2all)} z {int((act[lay == 'M'] > 1).sum())}")
