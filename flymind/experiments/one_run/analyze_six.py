"""Zgodność z oryginałem i odczyt sześciu osi (plan: PLAN_ODCZYT_SZESCIU.md). analyze_six.py ORYGINAŁ.npz DIR_RAW DIR_WYNIK"""
import csv
import json
import sys

import numpy as np

AXES = {"podstawa": (("1 podstawa|+ promotor",), ("1 podstawa|- remotor",)),
        "bark": (("2 bark|Tr flexor", "2 bark|Acc. tr flexor"), ("2 bark|Tr extensor", "2 bark|Sternotroch.", "2 bark|Tergotr.")),
        "łokieć": (("3 łokieć|Ti flexor", "3 łokieć|Acc. ti flexor"), ("3 łokieć|Ti extensor",)),
        "nadgarstek zgięcie": (("4 nadg. zgięcie|Ta levator",), ("4 nadg. zgięcie|Ta depressor",)),
        "nadgarstek obrót": (("5 nadg. obrót|Sternal ant. rotator",), ("5 nadg. obrót|Sternal post. rotator",)),
        "szczęka T2": (("szczęka T2|zaciskanie (Ti extensor)",), ("szczęka T2|zwalnianie (Ti flexor + Acc)",))}
WIN = [("spokój", 0, 6), ("kula w poprzek i na środek", 6, 12), ("zbliżenie 1", 12, 13.2), ("oddalenie, spokój", 13.2, 20), ("A0", 20, 22), ("po A0", 22, 27), ("A1", 27, 29),
       ("po A1", 29, 36), ("zbliżenie 2 + A1", 36, 38.5), ("po", 38.5, 45), ("całość", 0, 45)]
DEG = np.degrees(1.0)


def low(x):
    """Filtr z sieci: τ_r 50 ms, krok 10 ms; x [takt] w Hz."""
    r, o = 0.0, np.zeros(len(x))
    for i, v in enumerate(x):
        r += 0.01 / 0.05 * (v - r)
        o[i] = r
    return o


def load(raw):
    z, meta = dict(np.load(raw + "/pelny_odczyt.npz")), json.load(open(raw + "/neurony.json"))
    col = {b: i for i, b in enumerate(meta["kolumny_cnt"]) if b != "(dawne)"}
    S = {g: z["cnt"][:, [col[b] for b in v]] for g, v in meta["grupy"].items()}            # impulsy [takt, neuron]
    hz = lambda s: s.mean(1) * 100.0                                                        # średnia po neuronach i 10 krokach 1 ms → Hz
    R = {}
    for a, (p, n) in AXES.items():
        R[a] = np.array([low(hz(np.hstack([S[g] for g in side]))) for side in (p, n)]).T
    R.update({g: low(hz(s)) for g, s in S.items()})
    C = {a: 0.005 * (R[a][:, 0] - R[a][:, 1]) * (1 if a == "szczęka T2" else DEG) for a in AXES}   # °/s; szczęka N·m
    return z, meta, col, S, R, C


if __name__ == "__main__":
    orig, raw, out = sys.argv[1:4]
    o = dict(np.load(orig))
    z, meta, col, S, R, C = load(raw)
    res = dict(zgodnosc={k: bool(np.array_equal(o[k], z[k][:, :5] if k == "cnt" else z[k])) for k in o}, zgodnosc_wszystko=None)
    res["zgodnosc_wszystko"] = all(res["zgodnosc"].values()) and set(o) == set(z)
    res["maks_roznica_katow_rad"] = float(np.abs(o["q_all"] - z["q_all"]).max())
    chk = {}
    for j, pn in meta["obecne_pule"].items():
        cols = [np.hstack([z["cnt"][:, [col[b]]] for b in pn[s]]) if all(b in col for b in pn[s]) else None for s in "+-"]
        chk[j] = [float(np.abs(low(c.mean(1) * 100.0) - z["r"][:, int(j) - 1, k]).max()) if c is not None else "brak" for k, c in enumerate(cols)]
    res["sprawdzian_odczytu_maks_roznica_Hz"] = chk
    res["lokiec_nadgarstek_nowa_mapa_rowna_zapisanej_komendzie_maks_stopnie_s"] = [float(np.abs(sg * C[a] / DEG * 0.01 - z["dq"][:, k]).max() * DEG * 100) for a, k, sg in (("łokieć", 1, 1), ("nadgarstek zgięcie", 2, -1))]
    res["obecne_dq_maks_stopnie_s"] = (np.degrees(np.abs(z["dq"])).max(0) * 100).round(2).tolist()
    sl = lambda a, b: slice(int(round(a * 100)), int(round(b * 100)))
    res["grupy_impulsy"] = {g: {n: int(s[sl(a, b)].sum()) for n, a, b in WIN} for g, s in S.items()}
    res["grupy_aktywne_neurony"] = {g: f"{int((s.sum(0) > 0).sum())}/{s.shape[1]}" for g, s in S.items()}
    res["grupy_srednia_Hz"] = {g: {n: round(float(s[sl(a, b)].mean() * 100), 3) for n, a, b in WIN} for g, s in S.items()}
    res["neurony_impulsy"] = {str(b): int(z["cnt"][:, c].sum()) for b, c in col.items()}
    res["komenda_calka_stopnie"] = {a: {n: round(float(C[a][sl(u, v)].sum() * 0.01), 3) for n, u, v in WIN} for a in AXES if a != "szczęka T2"}
    res["komenda_min_maks_stopnie_s"] = {a: {n: [round(float(C[a][sl(u, v)].min()), 2), round(float(C[a][sl(u, v)].max()), 2)] for n, u, v in WIN} for a in AXES if a != "szczęka T2"}
    res["obecny_bark_calka_stopnie"] = {n: round(float(np.degrees(z["dq"][sl(u, v), 0].sum())), 3) for n, u, v in WIN}
    res["szczeka_T2_moment_Nm"] = {n: dict(srednia=round(float(C["szczęka T2"][sl(u, v)].mean()), 4), min=round(float(C["szczęka T2"][sl(u, v)].min()), 3), maks=round(float(C["szczęka T2"][sl(u, v)].max()), 3)) for n, u, v in WIN}
    # obrót a podstawa
    B, Ro = C["podstawa"], C["nadgarstek obrót"]
    sb = sum(S[g].sum(1) for side in AXES["podstawa"] for g in side)
    sr = sum(S[g].sum(1) for side in AXES["nadgarstek obrót"] for g in side)
    cmp = {}
    for n, u, v in WIN:
        w = sl(u, v)
        b1, r1 = [(x[w][: len(x[w]) // 10 * 10].reshape(-1, 10).sum(1) > 0) for x in (sb, sr)]
        b, r = B[w], Ro[w]
        opp = lambda th: (np.abs(b) > th) & (np.abs(r) > th) & (b * r < 0)                  # noqa: E731
        same = lambda th: (np.abs(b) > th) & (np.abs(r) > th) & (b * r > 0)                 # noqa: E731
        m = len(b) // 50 * 50
        bb, rr, ib, ir = [x[w][:m].reshape(-1, 50).sum(1) for x in (B * .01, Ro * .01, sb, sr)]
        both = (np.abs(b) > .05) | (np.abs(r) > .05)
        cmp[n] = dict(kubelki_100ms=dict(tylko_podstawa=int((b1 & ~r1).sum()), tylko_rotatory=int((r1 & ~b1).sum()), oba=int((b1 & r1).sum()), nic=int((~b1 & ~r1).sum())),
                      takty_podstawa_gdy_obrot_cichy=int(((np.abs(b) > .57) & (np.abs(r) < .05)).sum()), takty_obrot_gdy_podstawa_cicha=int(((np.abs(r) > .57) & (np.abs(b) < .05)).sum()),
                      takty_przeciwny=[int(opp(.05).sum()), int(opp(.57).sum())], takty_zgodny=[int(same(.05).sum()), int(same(.57).sum())],
                      polsekundy=dict(przeciwny=int(((np.abs(bb) > .05) & (np.abs(rr) > .05) & (bb * rr < 0)).sum()), zgodny=int(((np.abs(bb) > .05) & (np.abs(rr) > .05) & (bb * rr > 0)).sum()),
                                      tylko_podstawa=int(((np.abs(bb) > .05) & (ir == 0)).sum()), tylko_rotatory=int(((np.abs(rr) > .05) & (ib == 0)).sum())),
                      suma_stopnie=[round(float(b.sum() * .01), 3), round(float(r.sum() * .01), 3)],
                      korelacja=round(float(np.corrcoef(b[both], r[both])[0, 1]), 3) if both.sum() > 20 and b[both].std() and r[both].std() else None)
    res["obrot_a_podstawa"] = cmp
    json.dump(res, open(out + "/analysis.json", "x"), indent=1, ensure_ascii=False)
    with open(out + "/neurony.csv", "x", newline="") as f:
        w = csv.writer(f)
        w.writerow(["grupa", "bodyId"] + [f"impulsy {n} {a}-{b} s" for n, a, b in WIN])
        for g, ids in meta["grupy"].items():
            for k, b in enumerate(ids):
                w.writerow([g, b] + [int(S[g][sl(u, v), k].sum()) for _, u, v in WIN])
    np.savez_compressed(out + "/aktywnosc_w_czasie.npz", t=z["t"], **{"impulsy " + g.replace("|", " – "): s.astype(np.int8) for g, s in S.items()},
                        **{"Hz50ms " + g.replace("|", " – "): R[g] for g in S}, **{"komenda " + a: C[a] for a in AXES})
    for k, v in res.items():
        if isinstance(v, dict) and k not in ("neurony_impulsy",):
            print(k)
            [print("   ", a, b) for a, b in v.items()]
        elif k != "neurony_impulsy":
            print(k, v)
