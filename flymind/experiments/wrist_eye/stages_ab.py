"""Po fakcie (nie w planie): kierunek różnicy A−B i B1−B na kolejnych etapach. stages_ab.py DIR_RAW"""
import sys
import numpy as np
d = sys.argv[1]
G = ("oko", "mozg", "DN", "rdzen", "MN_stawy")
for g in (-1, 1):
    for w, (i0, i1) in (("W1 po 1. ruchu", (150, 300)), ("W2", (427, 627))):
        print(f"\nGlu {g:+d} {w}: mediana sumy B | A−B mediana %, ile par >0 | B1−B mediana %, ile par >0")
        Z = {(s, c): np.load(f"{d}/g{g:+.0f}_{s}_{c}.npz") for s in range(27501001, 27501011) for c in ("A", "B", "B1")}
        rows = [("sygnał oka [mV·s]", lambda z: z["loom"][i0:i1].sum() * .01)] + [("impulsy " + n, (lambda k: lambda z: float(z["cnt"][i0:i1, k].sum()))(k)) for k, n in enumerate(G)]
        rows += [("komenda " + n + " [°]", (lambda k: lambda z: float(np.degrees(z["dq"][i0:i1, k].sum())))(k)) for k, n in enumerate(("bark", "łokieć", "nadg"))]
        rows += [("|komenda| razem [°]", lambda z: float(np.degrees(np.abs(z["dq"][i0:i1]).sum())))]
        for n, f in rows:
            v = {c: np.array([f(Z[s, c]) for s in range(27501001, 27501011)]) for c in ("A", "B", "B1")}
            da, db = v["A"] - v["B"], v["B1"] - v["B"]
            base = np.median(np.abs(v["B"])) or 1
            print(f"{n:22s} B {np.median(v['B']):10.3f} | A−B {np.median(da):+9.3f} ({100 * np.median(da) / base:+6.1f} %) >0: {(da > 0).sum()} <0: {(da < 0).sum()} |A−B| med {np.median(abs(da)):.3f} | B1−B {np.median(db):+9.3f} ({100 * np.median(db) / base:+6.1f} %) >0: {(db > 0).sum()} <0: {(db < 0).sum()} |B1−B| med {np.median(abs(db)):.3f}")
    a = [np.load(f"{d}/g{g:+.0f}_{s}_A.npz") for s in range(27501001, 27501011)]
    b = [np.load(f"{d}/g{g:+.0f}_{s}_B.npz") for s in range(27501001, 27501011)]
    print("obrót kamery A przy starcie 2. zbliżenia [°]", np.round(np.percentile([z["rot"][427] for z in a], [0, 50, 100]), 2), "| maks prędkość komendy °/s", np.degrees(max(np.abs(z["dq"]).max() for z in a) / .01).round(1), "| impulsy MN w W2 na staw (A, mediana):", np.median([z["r"][427:627].mean(0).ravel() for z in a], 0).round(2))
    t = [np.argmax(z["loom"][427:].max(1) >= 7) + 427 if (z["loom"][427:].max(1) >= 7).any() else None for z in a]
    tb = np.argmax(b[0]["loom"][427:].max(1) >= 7) + 427
    print("przejście 7 mV w 2. zbliżeniu: B", tb * .01, "A", sorted({x * .01 if x else None for x in t}, key=lambda v: (v is None, v)))
    if g == 1:
        print("A: ostatni takt z sygnałem oka > 0,5 mV:", sorted(round(float(np.flatnonzero(z["loom"].max(1) > .5).max()) * .01, 2) for z in a))
