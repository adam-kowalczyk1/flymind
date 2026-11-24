"""Analiza trzech stawów wg PREREG_THREE_JOINTS.md (napisana przed obejrzeniem wyników testowych). analyze.py DIR_RAW OUT.json"""
import itertools
import json
import os
import sys

import numpy as np

I0, I1, DT = 300, 500, 0.01
NAMES = ("bark", "łokieć", "nadgarstek")
MAIN = ("spokoj", "palec1", "palec2")


def load(d, g, s, c):
    return dict(np.load(os.path.join(d, f"g{g:+.0f}_{s}_{c}.npz")))


def q_at(z, i):                                                        # kąt po i taktach (0 = przed pierwszym)
    return z["q"][i - 1] if i else z["q0"][1:4]


def signflip(x):
    x = np.asarray(x, float)
    if not x.any():
        return 1.0
    m = abs(x.mean())
    S = np.array(list(itertools.product((1, -1), repeat=len(x))))
    return float((np.abs((S * x).mean(1)) >= m - 1e-15).mean())


def holm(p):
    o, out, run = np.argsort(p), np.zeros(len(p)), 0.0
    for k, i in enumerate(o):
        run = max(run, min(1.0, (len(p) - k) * p[i]))
        out[i] = run
    return out


def windows(z):
    n = len(z["q"])
    Q = np.vstack([z["q0"][1:4], z["q"]])
    path = lambda a, b: np.abs(np.diff(Q[a:b + 1], axis=0)).sum(0)  # noqa: E731
    return dict(pre=q_at(z, I0) - q_at(z, 0), press=q_at(z, I1) - q_at(z, I0), post=q_at(z, n) - q_at(z, I1),
                path_pre=path(0, I0), path_press=path(I0, I1))


def still(z, a, b):
    """Dlaczego staw stoi w oknie [a,b): wg planu. None = staw się ruszył."""
    out, mv = [], q_at(z, b) - q_at(z, a)
    for k in range(3):
        if abs(mv[k]) >= 0.005:
            out.append("ruszył")
        elif abs(z["dq"][a:b, k].sum()) < 0.005:
            out.append("sieć nie wysłała")
        elif z["flag"][a:b, k].any() or z["guard"][a:b].any():
            out.append("zatrzymało ograniczenie")
        else:
            out.append("komenda przeszła, staw nie ruszył")
    return out


def loo(X, y, seed):
    ok = 0
    for s in np.unique(seed):
        tr = seed != s
        sd = X[tr].std(0)
        keep = sd > 1e-9
        Z = X[:, keep] / sd[keep]
        cen = [Z[tr & (y == c)].mean(0) for c in range(3)]
        ok += sum(int(np.argmin([np.linalg.norm(Z[i] - c) for c in cen]) == y[i]) for i in np.flatnonzero(~tr))
    return ok / len(y)


def main(d, out):
    seeds = sorted({int(f.split("_")[1]) for f in os.listdir(d)})
    res = dict(seeds=seeds)
    for g in (-1.0, 1.0):
        Z = {(s, c): load(d, g, s, c) for s in seeds for c in MAIN + ("palec1_92",)}
        W = {k: windows(z) for k, z in Z.items()}
        r = dict(identyczne_przed_naciskiem=all((Z[s, c]["q_all"][:I0] == Z[s, "spokoj"]["q_all"][:I0]).all() and
                                                (Z[s, c]["r"][:I0] == Z[s, "spokoj"]["r"][:I0]).all() for s in seeds for c in MAIN[1:] + ("palec1_92",)))
        M = {c: np.array([W[s, c]["press"] for s in seeds]) for c in MAIN + ("palec1_92",)}
        pre = np.array([W[s, "spokoj"]["pre"] for s in seeds])
        cmd_pre = np.array([(np.abs(Z[s, "spokoj"]["dq"][:I0]) / DT > 0.01).mean(0) for s in seeds])
        r["przed_dotykiem"] = dict(przesuniecie_mediana=np.median(pre, 0).tolist(), min=pre.min(0).tolist(), max=pre.max(0).tolist(),
                                   droga_mediana=np.median([W[s, "spokoj"]["path_pre"] for s in seeds], 0).tolist(),
                                   udzial_taktow_z_komenda=cmd_pre.mean(0).tolist(), ziarna_z_ruchem=(np.abs(pre) >= 0.005).sum(0).tolist(),
                                   pule_Hz=np.mean([Z[s, "spokoj"]["r"][:I0].mean(0) for s in seeds], 0).round(3).tolist())
        r["spokoj_8s_maks_ruch"] = [float(max(np.abs(Z[s, "spokoj"]["q"][:, k] - Z[s, "spokoj"]["q0"][1 + k]).max() for s in seeds)) for k in range(3)]
        for c in M:
            r["okno_nacisku_" + c] = dict(mediana=np.median(M[c], 0).tolist(), min=M[c].min(0).tolist(), max=M[c].max(0).tolist(),
                                          ziarna_z_ruchem=(np.abs(M[c]) >= 0.005).sum(0).tolist(),
                                          po_nacisku_mediana=np.median([W[s, c]["post"] for s in seeds], 0).tolist(),
                                          pule_Hz=np.mean([Z[s, c]["r"][I0:I1].mean(0) for s in seeds], 0).round(2).tolist())
            st = [still(Z[s, c], I0, I1) for s in seeds]
            r["czemu_stoi_" + c] = {NAMES[k]: {x: [t[k] for t in st].count(x) for x in sorted({t[k] for t in st})} for k in range(3)}
            r["komendy_" + c] = dict(suma_dq_mediana=np.median([Z[s, c]["dq"][I0:I1].sum(0) for s in seeds], 0).tolist(),
                                     maks_dq=np.max([np.abs(Z[s, c]["dq"]).max(0) for s in seeds], 0).tolist(),
                                     flagi=int(sum((Z[s, c]["flag"] > 0).sum() for s in seeds)), straznik=int(sum(Z[s, c]["guard"].sum() for s in seeds)),
                                     roznica_qc_qt=float(max(np.abs(Z[s, c]["qc"] - Z[s, c]["qt"]).max() for s in seeds)),
                                     kontakty=int(max(Z[s, c]["ncon"].max() for s in seeds)), dotyk_sceny_N=float(max(Z[s, c]["real_touch"].max() for s in seeds)),
                                     blad_nadazania=float(max(np.abs(Z[s, c]["q"] - Z[s, c]["qt"]).max() for s in seeds)))
        ct = [("palec1", "spokoj"), ("palec2", "spokoj"), ("palec1", "palec2")]
        D = [(a, b, k, M[a][:, k] - M[b][:, k]) for a, b in ct for k in range(3)]
        ph = holm(np.array([signflip(x[3]) for x in D]))
        r["porownania"] = [dict(co=f"{a} − {b}", staw=NAMES[k], mediana=float(np.median(x)), min=float(x.min()), max=float(x.max()), p_holm=float(p),
                                ten_sam_znak=int(max((x > 0).sum(), (x < 0).sum())), tak=bool(p < 0.05 and abs(np.median(x)) >= 0.02))
                           for (a, b, k, x), p in zip(D, ph)]
        X = np.array([np.r_[W[s, c]["press"], W[s, c]["post"], W[s, c]["path_press"]] for s in seeds for c in MAIN])
        y, sd = np.array([i for _ in seeds for i in range(3)]), np.repeat(seeds, 3)
        acc, rng = loo(X, y, sd), np.random.default_rng(1)
        pr = []
        for _ in range(5000):
            yp = np.concatenate([rng.permutation(3) for _ in seeds])
            pr.append(loo(X, yp, sd))
        r["rozpoznanie"] = dict(trafnosc=acc, los=1 / 3, p=float((1 + sum(x >= acc for x in pr)) / 5001))
        # kolejność: pierwszy takt po nacisku, gdy komenda > 0,01 rad/s i gdy kąt odszedł o 0,005 rad
        for c in MAIN[1:]:
            t_c, t_q = [], []
            for s in seeds:
                z = Z[s, c]
                f = lambda m: [float(np.argmax(m[:, k])) * DT * 1e3 + 10 if m[:, k].any() else None for k in range(3)]  # noqa: E731
                t_c.append(f(np.abs(z["dq"][I0:I1]) / DT > 0.01))
                t_q.append(f(np.abs(z["q"][I0:I1] - q_at(z, I0)) >= 0.005))
            med = lambda t: [(None if not (v := [x[k] for x in t if x[k] is not None]) else [round(float(np.median(v))), len(v)]) for k in range(3)]  # noqa: E731
            r["start_ms_" + c] = dict(komenda=med(t_c), ruch_5mrad=med(t_q))
        a3 = {c: np.array([(np.abs(Z[s, c]["dq"][I0:I1]) / DT > 0.01).all(1).mean() for s in seeds]) for c in M}
        r["udzial_taktow_3_stawy_naraz"] = {c: float(v.mean()) for c, v in a3.items()}
        r["dokladne_p1_vs_p1_92_mediana"] = np.median(M["palec1"] - M["palec1_92"], 0).tolist()
        res[f"glu{g:+.0f}"] = r
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:3])
