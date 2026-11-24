"""Analiza tasowań wg PREREG_TASOWANIA.md (napisana przed obejrzeniem wyników). analyze_tas.py DIR_TAS DIR_RAW OUT.json OUT.csv"""
import csv
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import holm, signflip  # noqa: E402

SEEDS = range(27301001, 27301011)


def cross(X):
    """Średnia po parach różnych ziaren x(s)·x(s′) — nieobciążony kwadrat długości średniej."""
    n, s = len(X), X.sum(0)
    return float((s @ s - (X * X).sum()) / (n * (n - 1)))


def net_stats(f):
    z, rep = np.load(f), json.load(open(f.replace(".npz", ".json")))
    q = {(s, c): z[f"{s}_{c}_q"] for s in SEEDS for c in ("spokoj", "palec1", "palec2")}
    dw = lambda c, a, b: np.array([q[s, c][b - 1] - q[s, c][a - 1] for s in SEEDS])  # noqa: E731
    Q = dw("spokoj", 300, 500)
    M = {c: dw(f"palec{c}", 300, 500) - Q for c in (1, 2)}
    post = {c: dw(f"palec{c}", 500, 800) - dw("spokoj", 500, 800) for c in (1, 2)}
    d = (M[1] - M[2])[:, :2]
    A = {c: np.sqrt(max(0.0, cross(M[c][:, :2]))) for c in (1, 2)}
    S = np.sqrt(max(0.0, cross(d)))
    p = holm(np.array([signflip(d[:, k]) for k in (0, 1)]))
    med, same = np.median(d, 0), np.array([max((d[:, k] > 0).sum(), (d[:, k] < 0).sum()) for k in (0, 1)])
    disc = [bool(p[k] < 0.05 and same[k] >= 9 and abs(med[k]) >= 0.02) for k in (0, 1)]
    react = bool(max(A.values()) >= 0.005)
    m1, m2 = np.median(M[1], 0), np.median(M[2], 0)
    napad = any(abs(np.median(post[c], 0)[k]) >= max(0.02, 0.5 * abs(np.median(M[c], 0)[k])) for c in (1, 2) for k in (0, 1))
    own = float(max(np.abs(q[s, "spokoj"] - z["q0"][1:4]).max() for s in SEEDS))
    act = rep["activity"]
    a = lambda c, w, k: float(np.mean([act[f"{s}_{c}"][w][k] for s in SEEDS]))  # noqa: E731
    pool = lambda c: np.mean([z[f"{s}_{c}_r"][300:500].mean(0) for s in SEEDS], 0).round(2).tolist()  # noqa: E731
    return dict(tag=rep["tag"], changed_frac=rep.get("changed_frac", 0.0), m1=m1.tolist(), m2=m2.tolist(), D=med.tolist(), D_min=d.min(0).tolist(), D_max=d.max(0).tolist(),
                same=same.tolist(), p_holm=p.tolist(), rozroznia=disc, A1=float(A[1]), A2=float(A[2]), S=float(S), reaguje=react,
                SI=float(S / (A[1] + A[2])) if react and A[1] + A[2] > 0 else None, napad=napad, ruch_wlasny=own,
                wzor_danych=bool(abs(m2[0]) >= 0.02 and abs(m1[0]) < 0.01 and m1[1] < m2[1] <= -0.01),
                nadgarstek=[float(m1[2]), float(m2[2])],
                flagi=int(sum((z[f"{s}_{c}_flag"] > 0).sum() for s in SEEDS for c in ("spokoj", "palec1", "palec2"))),
                straznik=int(sum(z[f"{s}_{c}_guard"].sum() for s in SEEDS for c in ("spokoj", "palec1", "palec2"))),
                akt={c: dict(nacisk=a(c, "nacisk", "cala"), po=a(c, "po", "cala"), rdzen=a(c, "nacisk", "rdzen"), mozg=a(c, "nacisk", "mozg"),
                             aktywne=a(c, "nacisk", "aktywne"), aktywne_rdzen=a(c, "nacisk", "aktywne_rdzen"), MN=a(c, "nacisk", "MN_T1L"),
                             rec=max(a(c, "nacisk", "receptory_A0"), a(c, "nacisk", "receptory_A1")), pule=pool(c)) for c in ("spokoj", "palec1", "palec2")})


def main(d_tas, d_raw, out, out_csv):
    nets = {}
    for f in sorted(glob.glob(os.path.join(d_tas, "*.npz"))):
        r = net_stats(f)
        nets[r["tag"]] = r
    z = np.load(os.path.join(d_tas, "N.npz"))
    same = all((np.load(f"{d_raw}/g-1_{s}_{c}.npz")["q"] == z[f"{s}_{c}_q"]).all() for s in SEEDS for c in ("spokoj", "palec1", "palec2"))
    N, fam = nets["N"], {}
    for t, r in nets.items():
        if t != "N":
            fam.setdefault(t.rstrip("0123456789"), []).append(r)
    res = dict(N_identyczne_z_pierwsza_proba=bool(same), rodziny={})
    for k, R in sorted(fam.items()):
        rx = [r for r in R if r["reaguje"]]
        si, s = np.array([r["SI"] for r in rx], float), np.array([r["S"] for r in R])
        med = lambda v: [round(float(x), 4) for x in np.percentile(v, [0, 50, 100])] if len(v) else None  # noqa: E731
        res["rodziny"][k] = dict(n=len(R), reaguje=len(rx), rozroznia_bark=sum(r["rozroznia"][0] for r in R), rozroznia_lokiec=sum(r["rozroznia"][1] for r in R),
                                 rozroznia_ktorykolwiek=sum(any(r["rozroznia"]) for r in R), rozroznia_oba=sum(all(r["rozroznia"]) for r in R), wzor_danych=sum(r["wzor_danych"] for r in R),
                                 napad=sum(r["napad"] for r in R), ruch_wlasny=sum(r["ruch_wlasny"] >= 0.005 for r in R),
                                 SI_min_med_max=med(si), S_stopnie_min_med_max=[round(float(np.degrees(x)), 2) for x in np.percentile(s, [0, 50, 100])],
                                 p_SI_wszystkie=(1 + int((si >= N["SI"]).sum())) / (1 + len(R)), p_SI_reagujace=(1 + int((si >= N["SI"]).sum())) / (1 + len(rx)),
                                 p_S=(1 + int((s >= N["S"]).sum())) / (1 + len(R)),
                                 hz_palec1=med([r["akt"]["palec1"]["nacisk"] for r in R]), hz_palec2=med([r["akt"]["palec2"]["nacisk"] for r in R]))
    ls = res["rodziny"].get("LS")
    if ls:
        res["decyzja_LS"] = ("nierozstrzygnięte: kontrola milczy" if ls["reaguje"] < 15 else
                             "dane wyróżniają się" if ls["p_SI_wszystkie"] <= 0.05 else "dane NIE wyróżniają się")
    res["siec_z_danych"] = N
    res["sieci"] = nets
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    deg = lambda v: f"{np.degrees(v):.2f}"  # noqa: E731
    with open(out_csv, "x", newline="") as f:
        w = csv.writer(f)
        w.writerow(["siec", "bark_p1_deg", "lokiec_p1_deg", "bark_p2_deg", "lokiec_p2_deg", "D_bark_deg", "D_lokiec_deg", "znak_bark/10", "znak_lokiec/10", "rozroznia_bark", "rozroznia_lokiec",
                    "S_deg", "SI", "reaguje", "napad", "wzor_danych", "nadg_p1_deg", "nadg_p2_deg", "Hz_spokoj", "Hz_p1", "Hz_p2", "Hz_po_p1", "Hz_po_p2", "aktywne_p1", "aktywne_p2", "MN_Hz_p1", "MN_Hz_p2", "flagi", "straznik"])
        for t, r in nets.items():
            k = r["akt"]
            w.writerow([t, deg(r["m1"][0]), deg(r["m1"][1]), deg(r["m2"][0]), deg(r["m2"][1]), deg(r["D"][0]), deg(r["D"][1]), *r["same"], *map(int, r["rozroznia"]), deg(r["S"]),
                        "" if r["SI"] is None else f"{r['SI']:.2f}", int(r["reaguje"]), int(r["napad"]), int(r["wzor_danych"]), *map(deg, r["nadgarstek"]), f"{k['spokoj']['nacisk']:.3f}",
                        *(f"{k[c][w_]:.2f}" for w_ in ("nacisk", "po") for c in ("palec1", "palec2")), *(f"{k[c]['aktywne']:.3f}" for c in ("palec1", "palec2")),
                        *(f"{k[c]['MN']:.2f}" for c in ("palec1", "palec2")), r["flagi"], r["straznik"]])
    print(json.dumps({k: v for k, v in res.items() if k not in ("sieci", "siec_z_danych")}, indent=1, ensure_ascii=False))
    print(open(out_csv).read())


if __name__ == "__main__":
    main(*sys.argv[1:5])
