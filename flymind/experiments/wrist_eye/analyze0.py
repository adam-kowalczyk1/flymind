"""Analiza kroku 0 wg PREREG_KROK0.md (napisana przed obejrzeniem wyników). analyze0.py sygnaly.npz OUT.json"""
import json
import sys

import numpy as np

W1, W2, NT = slice(137, 211), slice(110, 251), 15     # 1,367–2,1 s; 1,1–2,5 s


def main(p, out):
    z = {k.replace("__", "/"): v for k, v in np.load(p).items()}
    res = {}
    for v in ("v2", "v3"):
        S, K = z[f"S/{v}"], z[f"K/{v}"]
        r = dict(S_maks_mV=float(S[:, :2].max()), K_szczyt_mV=float(K[W1, :2].max()), K_szczyt_LP=K[W1, :2].max(0).round(3).tolist(), K_szczyt_nieobciety=float(K[W1, 2:].max()),
                 K_szczyt_cala_proba=float(K[:, :2].max()), K_czas_szczytu_s=float((137 + K[W1, :2].max(1).argmax()) * 0.01),
                 K_czas_powyzej_7mV_s=float((K[:, :2].max(1) >= 7).sum() * 0.01), K_calka_mVs=(K[:, :2].sum(0) * 0.01).round(4).tolist())
        for sc in (1, 5, 20):
            kr = [z[f"KR_{sc}_{k:02d}/{v}"] for k in range(NT)]
            ro = [z[f"R_{sc}_{k:02d}/{v}"] for k in range(NT)]
            d = np.array([np.abs(x[W2, :2] - K[W2, :2]).max() for x in kr])
            draw = np.array([np.abs(x[W2, 2:] - K[W2, 2:]).max() for x in kr])
            pk = np.array([x[W2, :2].max() for x in kr])
            q = lambda a: [round(float(x), 3) for x in np.percentile(a, [0, 50, 100])]  # noqa: E731
            r[f"x{sc}"] = dict(obrot_kamery_maks_stopnie=q([z[f"R_{sc}_{k:02d}/rot"].max() for k in range(NT)]), delta_maks_mV=q(d), delta_nieobciety=q(draw), szczyt_KR=q(pk),
                               szczyt_R=q([x[:, :2].max() for x in ro]), delta_wszystkie=d.round(3).tolist(), falszywy_alarm_R_7mV=int(sum(x[:, :2].max() >= 7 for x in ro)),
                               calka_KR_minus_K_mVs=q([float((x[:, :2] - K[:, :2]).sum() * 0.01) for x in kr]), obciete_40mV=int(sum((x[:, :2] >= 40 - 1e-9).any() for x in kr)),
                               odstep_kuli_min_cm=q([100 * z[f"KR_{sc}_{k:02d}/gap"].min() for k in range(NT)]))
            if v == "v2":
                r[f"x{sc}"]["_d"] = d
        res[v] = r
    Kn, Sn = z["K/v2_szum"], z["S/v2_szum"]                                      # [pole, N, 4]
    pk, ps = Kn[:, W1, :2].max((1, 2)), Sn[:, :, :2].max((1, 2))
    r = res["v2"]
    ok = (pk >= 20) & (pk >= 4 * ps)
    weak = (pk >= 7) & (pk >= 4 * ps)
    r["szum"] = dict(K_szczyty=pk.round(2).tolist(), S_szczyty=ps.round(3).tolist(), S_szczyt_okno=Sn[:, W1, :2].max((1, 2)).round(3).tolist(), spelnia=int(ok.sum()), slabo=int(weak.sum()))
    r["P1"] = "wykrywa" if ok.sum() >= 9 else "słabo" if weak.sum() >= 9 else "nie wykrywa"
    pair = [np.abs(Kn[i, W2, :2] - Kn[j, W2, :2]).max() for i in range(10) for j in range(i)]
    floor, kpk = float(np.percentile(pair, 95)), r["K_szczyt_mV"]
    d = r["x1"]["_d"]
    crit = np.c_[d >= 2, d >= 0.1 * kpk, d > floor]
    r["P2_prog"] = dict(podloga_szumu_p95_mV=floor, podloga_mediana_mV=float(np.median(pair)), prog_10proc_mV=0.1 * kpk, spelnia_kazdy_warunek=crit.sum(0).tolist(), trajektorii_zauwazalnych=int(crit.all(1).sum()))
    n = int(crit.all(1).sum())
    r["P2"] = "TAK" if n >= 12 else "CZĘŚCIOWO" if n >= 4 else "NIE"
    for sc in (5, 20):
        ds = r[f"x{sc}"]["_d"]
        r[f"x{sc}"]["zauwazalnych_z_15"] = int(((ds >= 2) & (ds >= 0.1 * kpk) & (ds > floor)).sum())
    dn = np.array([np.abs(z[f"KR_1_{k:02d}/v2_szum"][:, W2, :2] - Kn[:, W2, :2]).max((1, 2)) for k in range(NT)])     # to samo pole szumu
    r["x1"]["delta_to_samo_pole_szumu_mediana"] = [round(float(x), 3) for x in np.percentile(np.median(dn, 1), [0, 50, 100])]
    r["x1"]["R_szum_szczyt_maks"] = float(max(z[f"R_1_{k:02d}/v2_szum"][..., :2].max() for k in range(NT)))
    for sc in (1, 5, 20):
        r[f"x{sc}"].pop("_d")
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:3])
