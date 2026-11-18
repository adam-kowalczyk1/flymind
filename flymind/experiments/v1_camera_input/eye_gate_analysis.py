"""Analiza bramki G1–G3 (DESIGN.md §7–8 + PREREG_GATE.md). eye_gate_analysis.py DIR OUT.json"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eye_gate as G  # noqa: E402
import optic_slice as OS  # noqa: E402

EPS = 1e-3
T4 = [f"T4{s}" for s in "abcd"]; T5 = [f"T5{s}" for s in "abcd"]


def dsi(R, types, pol):
    """R [n × 4 × 12 × 2]; bodźce w kolejności (kierunek, pol) z pol ∈ (1, −1). Kierunek pref z połowy A, DSI z połowy B; średnia z 3 prędkości."""
    pidx = 0 if pol == 1 else 1
    m = R[:, 1:, pidx::2, :].mean(1)                  # [n × 6 kier. × 2 połowy]
    pref = m[:, :, 0].argmax(1)
    null = (pref + 3) % 6
    rp = np.maximum(m[np.arange(len(m)), pref, 1], 0); rn = np.maximum(m[np.arange(len(m)), null, 1], 0)
    d = np.where(rp + rn > EPS, (rp - rn) / np.maximum(rp + rn, EPS), np.nan)
    full = m.mean(2)
    return d, full.argmax(1) * 60.0


def polarity(R, types):
    on = np.maximum(R[:, 0, 0::2, :].mean((1, 2)), 0); off = np.maximum(R[:, 0, 1::2, :].mean((1, 2)), 0)
    out = {}
    for t, grp in (("L1", ["L1"]), ("L2", ["L2"]), ("Mi1", ["Mi1"]), ("Tm3", ["Tm3"]), ("Tm1", ["Tm1"]), ("T4", T4), ("T5", T5)):
        k = np.isin(types, grp)
        a, b = on[k].mean(), off[k].mean()
        out[t] = float((a - b) / (a + b)) if a + b > EPS else None
    return out


def mi_axis(bodies):
    """Oś anatomiczna T4: wektor od środka wejść Mi9 do środka wejść Mi4 (kąt w stopniach, osadzenie §1)."""
    S = OS.build()
    idx = {b: i for i, b in enumerate(S["bodies"])}
    P = OS.xy(S["hexq"], S["hexr"])
    ang = {}
    e = pd.DataFrame(dict(pre=S["pre"], post=S["post"], n=S["n"]))
    e["pt"] = S["type"][e.pre]
    for b in bodies:
        i = idx[b]
        x = e[e.post == i]
        c = {}
        for t in ("Mi9", "Mi4"):
            y = x[x.pt == t]
            if y.n.sum() == 0:
                break
            c[t] = (P[y.pre.values] * y.n.values[:, None]).sum(0) / y.n.sum()
        if len(c) == 2:
            v = c["Mi4"] - c["Mi9"]
            ang[b] = float(np.degrees(np.arctan2(v[1], v[0])))
    return ang


def main(d, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    D = np.load(os.path.join(d, "data_glu-1.npz"), allow_pickle=True)
    types, bodies = D["types"], D["bodies"]
    shuf = sorted(glob.glob(os.path.join(d, "shuf_*.npz")))
    res = dict(n_shuffles=len(shuf), G1=polarity(D["R"], types))
    exp = {"L1": -1, "L2": -1, "Mi1": 1, "Tm3": 1, "T4": 1, "Tm1": -1, "T5": -1}
    res["G1_ok_types"] = sum(1 for t, s in exp.items() if res["G1"][t] is not None and np.sign(res["G1"][t]) == s)
    res["G1"] = dict(res["G1"], ok=res["G1_ok_types"] >= 6)
    dsT4, prefT4 = dsi(D["R"], types, 1); dsT5, _ = dsi(D["R"], types, -1)
    sh = {t: [] for t in T4 + T5}
    for f in shuf:
        X = np.load(f, allow_pickle=True)
        a, _ = dsi(X["R"], X["types"], 1); b, _ = dsi(X["R"], X["types"], -1)
        for t in T4:
            sh[t].append(float(np.nanmedian(a[X["types"] == t])))
        for t in T5:
            sh[t].append(float(np.nanmedian(b[X["types"] == t])))
    ang = mi_axis([b for b, t in zip(bodies, types) if t in T4])
    rows = {}
    for t in T4 + T5:
        k = types == t
        dd = (dsT4 if t in T4 else dsT5)[k]
        med = float(np.nanmedian(dd)); p95 = float(np.percentile(sh[t], 95)) if sh[t] else None
        r = dict(n=int(k.sum()), n_defined=int(np.isfinite(dd).sum()), median_DSI=med, shuffle_p95=p95,
                 shuffle_median=float(np.median(sh[t])) if sh[t] else None, G2=bool(med >= 0.20 and p95 is not None and med > p95))
        if t in T4:
            diffs = []
            for b, pdeg in zip(bodies[k], prefT4[k]):
                if b in ang:
                    x = abs((pdeg - ang[b] + 180) % 360 - 180)
                    diffs.append(min(x, 180 - x))
            r.update(axis_diff_median=float(np.median(diffs)) if diffs else None, G3=bool(diffs and np.median(diffs) <= 30))
        rows[t] = r
    res["cells"] = rows
    res["G2_ok"] = sum(rows[t]["G2"] for t in T4) >= 3
    res["G3_ok"] = sum(rows[t]["G3"] for t in T4) >= 3
    res["GATE"] = bool(res["G1"]["ok"] and res["G2_ok"] and res["G3_ok"])
    p = os.path.join(d, "data_glu1.npz")
    if os.path.exists(p):
        X = np.load(p, allow_pickle=True); a, _ = dsi(X["R"], X["types"], 1)
        res["sensitivity_glu+1_T4_median_DSI"] = {t: float(np.nanmedian(a[X["types"] == t])) for t in T4}
    json.dump(res, open(out, "x"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
