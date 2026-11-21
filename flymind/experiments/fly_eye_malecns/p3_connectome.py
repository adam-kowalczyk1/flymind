"""P3 (21 XI): plik połączeń MaleCNS w formacie flyvis (ConnectomeFromAvgFilters) do uczenia oka od zera.
.venv: p3_connectome.py → results/fly_eye_malecns_20261120/malecns_flyvis.json + p3_connectome.json (raport)
Zasady (spisane przed uczeniem, PREREG_P3.md):
- typy, pary typów, znaki i lambda_mult = flyvis (zmieniamy TYLKO liczby i miejsca synaps);
- liczby MaleCNS BEZWARUNKOWE: suma synaps w rdzeniu / liczba komórek celu w rdzeniu (T1 użył średniej tylko po komórkach
  z połączeniem → 2–3× za dużo → eksplozja);
- układ współrzędnych: komórki bez assignedOlHex (np. T4/T5) mają pozycję ze środka wejść → stałe przesunięcie a_t typu;
  a_t = ważona mediana różnic środków ciężkości przesunięć MaleCNS − flyvis po parach od typów z heksem (nie zmienia
  względnego układu wejść, tylko zgrywa ramkę z krawędziami „hybrydowymi” R*, CT1, Am, które zostają z flyvis);
- miejsca pary: najmniejszy zbiór przesunięć niosący 95 % synaps pary; para bez synaps w MaleCNS — usunięta (raport)."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t0_counts as T0  # noqa: E402

SRC = "/Users/admin/so101_fly_project/envs/flyvis/lib/python3.12/site-packages/flyvis/connectome/fib25-fib19_v2.2.json"
HYB = ("R", "CT1", "Am")
MASS = float(os.environ.get("P3_MASS", 0.8))     # 80 %: start stabilny i ~0,33 s/krok (95 %: 0,54 s)
SHAPE = os.environ.get("P3_SHAPE", "1") == "1"   # suma pary = suma flyvis (siłę pary flyvis i tak uczy: edges_syn_strength na parę)


def wmedian(x, w):
    o = np.argsort(x)
    c = np.cumsum(w[o])
    return float(x[o][np.searchsorted(c, c[-1] / 2)])


def build(J, M, shift):
    out = dict(J, edges=[])
    dropped, kept = [], 0
    for e in J["edges"]:
        if e["src"].startswith(HYB) or e["tar"].startswith(HYB):
            out["edges"].append(e)
            continue
        m = M[(M.source_type == e["src"]) & (M.target_type == e["tar"])].sort_values("n", ascending=False)
        if m.n.sum() <= 0:
            dropped.append(f'{e["src"]}→{e["tar"]}')
            continue
        m = m[np.cumsum(m.n.values) - m.n.values < MASS * m.n.sum()]
        st, ss = shift.get(e["tar"], (0, 0)), shift.get(e["src"], (0, 0))
        k = sum(o[1] for o in e["offsets"]) / m.n.sum() if SHAPE else 1.0
        offs = [[[int(round(u - st[0] + ss[0])), int(round(v - st[1] + ss[1]))], float(n * k)] for u, v, n in zip(m.du, m.dv, m.n)]
        out["edges"].append(dict(e, offsets=offs))
        kept += 1
    return out, dropped, kept


def main():
    K, w, ncol, ncore, U, V = T0.load()
    s = w[w.core].groupby(["pt", "qt", "du", "dv"]).weight.sum().reset_index()
    s["n"] = s.weight / s.qt.map(ncore)
    M = s.rename(columns={"pt": "source_type", "qt": "target_type"})[["source_type", "target_type", "du", "dv", "n"]]
    J = json.load(open(SRC))
    fv = [(e["src"], e["tar"], np.array([o[0] for o in e["offsets"]], float), np.array([o[1] for o in e["offsets"]], float)) for e in J["edges"]]
    # typy z pozycją z heksu (≥ 90 % komórek ma assignedOlHex) — przesunięcie 0
    a = T0.pd.read_feather(os.path.join(T0.D, "body-annotations-male-cns-v1.0-minconf-0.5.feather"), columns=["bodyId", "type", "somaSide", "assignedOlHex1"])
    a = a[(a.somaSide == "R") & a.type.notna()]
    a["ft"] = a.type.map(lambda t: T0.ALIAS.get(t, t))
    hexok = set(a.groupby("ft").assignedOlHex1.apply(lambda x: x.notna().mean()).loc[lambda x: x >= 0.9].index)
    shift, rows = {}, []
    for tar in sorted({e[1] for e in fv}):
        d, wt = [], []
        for src, t, off, n in fv:
            if t != tar or src not in hexok or src.startswith(HYB):
                continue
            m = M[(M.source_type == src) & (M.target_type == tar)]
            if m.n.sum() < 1:
                continue
            cm = np.array([np.average(m.du, weights=m.n), np.average(m.dv, weights=m.n)])
            cf = np.average(off, axis=0, weights=n)
            d.append(cm - cf)
            wt.append(min(m.n.sum(), n.sum()))
        if d and tar not in hexok:
            d, wt = np.array(d), np.array(wt)
            shift[tar] = (int(round(wmedian(d[:, 0], wt))), int(round(wmedian(d[:, 1], wt))))
            rows.append((tar, shift[tar], len(d)))
    out, dropped, kept = build(J, M, shift)
    dst = os.path.join(T0.RES, os.environ.get("P3_OUT", "malecns_flyvis.json"))
    json.dump(out, open(dst, "w"))
    # raport: suma synaps pary MaleCNS / flyvis (po pominięciu hybryd), przesunięcia, usunięte pary
    tot = {(e["src"], e["tar"]): sum(o[1] for o in e["offsets"]) for e in out["edges"]}
    tot0 = {(e["src"], e["tar"]): sum(o[1] for o in e["offsets"]) for e in J["edges"]}
    ratio = [tot[k] / tot0[k] for k in tot if not (k[0].startswith(HYB) or k[1].startswith(HYB)) and tot0[k] > 0]
    rep = dict(file=dst, pairs_total=len(J["edges"]), pairs_malecns=kept, pairs_hybrid=len(J["edges"]) - kept - len(dropped),
               pairs_dropped=dropped, offsets_flyvis=sum(len(e["offsets"]) for e in J["edges"]),
               offsets_new=sum(len(e["offsets"]) for e in out["edges"]),
               sum_ratio_malecns_over_flyvis_median=float(np.median(ratio)), sum_ratio_q10_q90=np.quantile(ratio, [0.1, 0.9]).tolist(),
               type_shift={t: s for t, s, _ in rows}, type_shift_npairs={t: n for t, _, n in rows},
               T4a=[(e["src"], e["offsets"][:4]) for e in out["edges"] if e["tar"] == "T4a"],
               T5a=[(e["src"], e["offsets"][:4]) for e in out["edges"] if e["tar"] == "T5a"])
    json.dump(rep, open(dst.replace(".json", "_raport.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in rep.items() if k not in ("T4a", "T5a")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
