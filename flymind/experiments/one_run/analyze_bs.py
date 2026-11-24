"""Prognoza / komendy / kąty i porównanie reakcji (plan: PLAN_PODSTAWA_BARK.md). analyze_bs.py DIR_WYNIK"""
import json
import sys

import numpy as np
from analyze_six import WIN, load

D = sys.argv[1]
OLD = dict(np.load(D + "/../one_run_20261124/raw/pelny.npz"))
Z = {k: dict(np.load(f"{D}/raw/{k}.npz")) for k in ("nowa", "zablokowane", "mikro")}
_, _, _, _, _, C = load(D + "/../six_readout_20261124/raw")
J, deg = ("podstawa", "bark", "łokieć", "nadgarstek"), np.degrees
PROG = np.vstack([C["podstawa"], -C["bark"], C["łokieć"], -C["nadgarstek zgięcie"]]).T * 0.01          # ° na takt, znaki serw z planu
W = [(n, int(round(a * 100)), int(round(b * 100))) for n, a, b in WIN]
res, n = {}, Z["nowa"]
ang = lambda z: deg(np.vstack([z["q0"], z["q_all"]])[:, :4])  # noqa: E731
res["koniec_stopnie"] = {j: dict(prognoza=round(float(PROG[:, k].sum()), 3), komendy_nowa=round(float(deg(n["dq_net"][:, k].sum())), 3), wyslane_cele=round(float(deg(n["qc"][-1, k] - n["qc"][0, k] + n["dq_sent"][0, k])), 3),
                                kat=round(float((ang(n)[-1] - ang(n)[0])[k]), 3), stary_bark_kat=round(float((deg(OLD["q_all"][-1] - OLD["q0"]))[k]), 3), zablokowane_komendy=round(float(deg(Z["zablokowane"]["dq_net"][:, k].sum())), 3),
                                zablokowane_kat=round(float((ang(Z["zablokowane"])[-1] - ang(Z["zablokowane"])[0])[k]), 3)) for k, j in enumerate(J)}
res["okna"] = {w: {j: dict(prognoza=round(float(PROG[a:b, k].sum()), 3), komendy=round(float(deg(n["dq_net"][a:b, k].sum())), 3), kat=round(float(ang(n)[b, k] - ang(n)[a, k]), 3), zablokowane_komendy=round(float(deg(Z["zablokowane"]["dq_net"][a:b, k].sum())), 3),
                          mikro_komendy=round(float(deg(Z["mikro"]["dq_net"][a:b, k].sum())), 3)) for k, j in enumerate(J)} for w, a, b in W}
d = ang(n)[1:] - ang(n)[0]
err = d - deg(np.cumsum(n["dq_net"][:, :4], 0))
res["blad_kata_wobec_sumy_komend_stopnie"] = np.abs(err).max(0).round(4).tolist()
res["maks_wychylenie_stopnie"] = np.abs(d).max(0).round(3).tolist()
res["zakres_katow_w_probie_stopnie"] = [[round(float(x), 2) for x in (d[:, k].min(), d[:, k].max())] for k in range(4)]
res["maks_predkosc_komendy_stopnie_s"] = (deg(np.abs(n["dq_net"][:, :4])).max(0) * 100).round(2).tolist()
res["maks_wyprzedzenie_celu_wobec_kata_rad_(limit_0.02_podstawa_0.3_reszta)"] = np.abs(n["qt"][:, :4] - n["q_all"][:, :4]).max(0).round(4).tolist()
res["flagi_straznik"] = {k: [z["flag"].any().item(), int(z["guard"].sum())] for k, z in Z.items()}
res["kontakty"] = {k: int(z["ncon"].max()) for k, z in Z.items()}
res["obrot_szczeka_maks_ruch_stopnie_wzgledem_taktu_0"] = {k: deg(np.abs(z["q_all"][:, 4:6] - z["q_all"][0, 4:6])).max(0).round(4).tolist() for k, z in {**Z, "oryginal": OLD}.items()}
move = np.abs(d[:, :2]).max(1) > 0.05
res["pierwszy_ruch_podstawy_lub_barku_0_05_stopnia_s"] = float(n["t"][move.argmax()])
first = lambda x, y: (float(Z["nowa"]["t"][np.flatnonzero(x != y)[0]]) if (x != y).any() else None)  # noqa: E731
any1 = lambda a, b: (a != b).reshape(len(a), -1).any(1)  # noqa: E731
res["pierwszy_takt_roznicy_s"] = {}
for nm, ref in (("nowa vs zablokowane", "zablokowane"), ("mikro vs zablokowane", "zablokowane")):
    z1, z0 = Z[nm.split(" ")[0]], Z[ref]
    res["pierwszy_takt_roznicy_s"][nm] = {k: (float(z1["t"][x.argmax()]) if (x := any1(z1[k], z0[k])).any() else None) for k in ("felt", "feco", "fcrc", "raw", "loom", "cnt", "dq_net", "q_all")}
res["feco_roznica_rad_nowa_vs_zablokowane_w_s"] = {str(s): float(np.abs(n["feco"][:int(s * 100), 0] - Z["zablokowane"]["feco"][:int(s * 100), 0]).max()) for s in (12, 20, 22, 27, 36, 45)}
res["loom_roznica_mV_nowa_vs_zablokowane_maks_w_oknie"] = {w: [round(float(np.abs(n["loom"][a:b] - Z["zablokowane"]["loom"][a:b]).max()), 3), round(float(np.abs(n["raw"][a:b] - Z["zablokowane"]["raw"][a:b]).max()), 3)] for w, a, b in W}
res["impulsy_76_neuronow_nowa_mikro_minus_zablokowane"] = {w: dict(nowa=int(np.abs(n["cnt"][a:b, 5:] - Z["zablokowane"]["cnt"][a:b, 5:]).sum()), mikro=int(np.abs(Z["mikro"]["cnt"][a:b, 5:] - Z["zablokowane"]["cnt"][a:b, 5:]).sum()), razem_zablokowane=int(Z["zablokowane"]["cnt"][a:b, 5:].sum())) for w, a, b in W}
res["impulsy_5_grup_(oko, mozg, DN, rdzen, MN)"] = {w: {k: Z[k]["cnt"][a:b, :5].sum(0).astype(int).tolist() for k in Z} for w, a, b in W}
res["roznica_komend_nowa_i_mikro_vs_zablokowane_stopnie"] = {w: {j: [round(float(deg(Z["nowa"]["dq_net"][a:b, k].sum() - Z["zablokowane"]["dq_net"][a:b, k].sum())), 3), round(float(deg(Z["mikro"]["dq_net"][a:b, k].sum() - Z["zablokowane"]["dq_net"][a:b, k].sum())), 3)] for k, j in enumerate(J)} for w, a, b in W}
res["kula_kamera_mm"] = {w: round(float(n["gap"][a:b].min() * 1e3), 1) for w, a, b in W}
res["takty_przerwa_ponizej_5_mm_s"] = [float(n["t"][i]) for i in np.flatnonzero(n["gap"] < 0.005)][:1] + [float(n["t"][i]) for i in np.flatnonzero(n["gap"] < 0.005)][-1:]
res["przerwa_ponizej_0_mm_takty"] = int((n["gap"] < 0).sum())
res["kamera_przesuniecie_mm_i_obrot_stopnie"] = {str(s): [(1e3 * (n["cam"][int(s * 100)] - n["cam"][0])).round(1).tolist(), round(float(n["rot"][int(s * 100)]), 2)] for s in (12.5, 20, 22.5, 29.5, 36, 44.9)}
res["wspolczynnik_pelny_zapis"] = {"prefiks_oryginalu_0_12s_te_same_liczby_impulsow": bool((n["cnt"][:1200, :5] == OLD["cnt"][:1200]).all()), "pierwszy_takt_roznicy_nowa_vs_oryginal_impulsy_s": first(n["cnt"][:, :5].sum(1), OLD["cnt"].sum(1))}
json.dump(res, open(D + "/analysis.json", "x"), indent=1, ensure_ascii=False)
for k, v in res.items():
    if isinstance(v, dict):
        print(k)
        [print("   ", a, b) for a, b in v.items()]
    else:
        print(k, v)
