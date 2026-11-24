"""Zdarzenia ruchu i przypisanie przyczyn. analyze_one.py DIR_RAW OUT.json"""
import json, sys
import numpy as np
import one_run as R
d, out = sys.argv[1:3]
Z = {k: dict(np.load(f"{d}/{k}.npz")) for k in R.RUNS}
z, J, t = Z["pelny"], ("bark", "lokiec", "nadgarstek"), Z["pelny"]["t"]
q = lambda r: np.vstack([r["q0"][1:4], r["q_all"][:, 1:4]])
res = dict(sprawdzian_ruch_rowny_komendom_rad=float(np.abs((q(z)[1:] - q(z)[0]) - np.cumsum(z["dq"], 0)).max()),
           siec_odcieta_maks_ruch_stopnie=np.degrees(np.abs(q(Z["siec_odcieta"]) - q(Z["siec_odcieta"])[0]).max(0)).round(5).tolist(),
           stawy_klasyczne_maks_ruch_stopnie=np.degrees(np.abs(z["q_all"][:, [0, 4, 5]] - z["q0"][[0, 4, 5]]).max(0)).round(4).tolist(),
           flagi={k: int((v["flag"] > 0).sum()) for k, v in Z.items()}, straznik={k: int(v["guard"].sum()) for k, v in Z.items()}, kontakty={k: int(v["ncon"].max()) for k, v in Z.items()},
           cel_po_bezpieczniku_rowny_komendzie=float(np.abs(z["qc"] - z["qt"]).max()), zmiana_koncowa_stopnie={k: np.degrees(q(v)[-1] - q(v)[0]).round(3).tolist() for k, v in Z.items()},
           takty_bez_komendy_proc=float(100 * (np.abs(z["dq"]).max(1) == 0).mean()), takty_bezruchu_0_05_stopnia_na_s_proc=float(100 * (np.degrees(np.abs(z["dq"])).max(1) / .01 < .05).mean()),
           takty_dwoch_stawow_naraz=int(((np.degrees(np.abs(z["dq"])) / .01 > .57).sum(1) == 2).sum()), takty_trzech_stawow_naraz=int(((np.degrees(np.abs(z["dq"])) / .01 > .57).sum(1) == 3).sum()),
           oko_szczyty_mV={f"{a}-{b}": z["loom"][int(a * 100):int(b * 100)].max(0).round(2).tolist() for a, b in ((0, 6), (6, 8.6), (10, 11.3), (12, 13.2), (13.2, 14), (14.5, 16), (20, 22), (27, 29), (34, 35.3), (36, 38.4), (38.5, 45))},
           pula_nadgarstka_maks_Hz=z["r"][:, 2].max(0).tolist(), MN_impulsy=int(z["cnt"][:, 4].sum()))
ev = []
for k in range(3):
    on = np.flatnonzero(np.degrees(np.abs(z["dq"][:, k])) / .01 > 0.05)      # plan mówił „> 0”: ogon filtra nigdy nie jest zerem (zmiana po fakcie)
    for g in (np.split(on, np.flatnonzero(np.diff(on) > 30) + 1) if len(on) else []):
        a, b = int(g[0]), min(len(t) - 1, int(g[-1]) + 1)
        s = {n: float(np.degrees(v["dq"][a:b, k].sum())) for n, v in Z.items()}
        ev.append(dict(staw=J[k], od_s=round(float(t[a]), 2), do_s=round(float(t[b]), 2), ruch_stopnie=round(float(np.degrees(q(z)[b][k] - q(z)[a][k])), 3), komenda_stopnie=round(s["pelny"], 3), bez_wzroku=round(s["bez_wzroku"], 3), bez_dotyku=round(s["bez_dotyku"], 3),
                       bez_obu=round(s["bez_obu"], 3), maks_predkosc_stopnie_s=round(float(np.degrees(np.abs(z["dq"][a:b, k]).max()) / .01), 2)))
ev = [e for e in sorted(ev, key=lambda e: e["od_s"])]
res["zdarzenia"] = ev
WIN = [("spokój 0–6", 0, 6), ("kula w poprzek 6–10", 6, 10), ("kula na środek 10–12", 10, 12), ("zbliżenie 12–13,2", 12, 13.2), ("oddalenie i wyjazd 13,2–20", 13.2, 20), ("A0 20–22", 20, 22), ("po A0 22–27", 22, 27), ("A1 27–29", 27, 29),
       ("po A1 29–34", 29, 34), ("kula na środek 34–36", 34, 36), ("zbliżenie + A1 36–38", 36, 38), ("po 38–45", 38, 45)]
res["okna_stopnie"] = {n: {k: np.degrees(q(v)[int(b * 100)] - q(v)[int(a * 100)]).round(3).tolist() for k, v in Z.items()} for n, a, b in WIN}
json.dump(res, open(out, "x"), indent=1, ensure_ascii=False)
for k, v in res.items():
    if k in ("zdarzenia",):
        [print("  ", e) for e in v]
    elif k == "okna_stopnie":
        for n, w in v.items(): print(f"  {n:28s}", {a: b for a, b in w.items()})
    else: print(k, v)
