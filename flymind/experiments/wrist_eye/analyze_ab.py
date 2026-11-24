"""Analiza pilotażu A/B wg PREREG_PILOT_AB.md (napisana przed obejrzeniem wyników). analyze_ab.py DIR_RAW OUT.json"""
import json
import os
import sys

import numpy as np

W = {"W1": (100, 300), "W2": (427, 627)}
G, J = ("oko", "mozg", "DN", "rdzen", "MN_stawy"), ("bark", "lokiec", "nadgarstek")


def first(m):
    m = np.asarray(m)
    return int(np.argmax(m)) if m.any() else None


def q_at(z, i):
    return z["q"][i - 1] if i else z["q0"][1:4]


def main(d, out):
    seeds = sorted({int(f.split("_")[1]) for f in os.listdir(d)})
    res = dict(seeds=seeds)
    md = lambda v: [round(float(x), 5) for x in np.percentile(v, [0, 50, 100])]  # noqa: E731
    for g in (-1, 1):
        Z = {(s, c): dict(np.load(os.path.join(d, f"g{g:+.0f}_{s}_{c}.npz"))) for s in seeds for c in ("A", "B", "B1", "C")}
        r, chain, ok = {}, [], []
        for s in seeds:
            a, b = Z[s, "A"], Z[s, "B"]
            mv = first(np.abs(a["q"] - a["q0"][1:4]).max(1) > 1e-6)
            c = dict(komenda=first(np.abs(a["dq"]).max(1) > 0), ruch=mv, inna_klatka=first(a["fcrc"] != b["fcrc"]), inny_sygnal_oka=first((a["loom"] != b["loom"]).any(1)))
            for k, n in enumerate(G):
                c["inne_impulsy_" + n] = first(a["crc"][:, k] != b["crc"][:, k])
            c["inna_komenda"] = first((a["dq"] != b["dq"]).any(1))
            c["inny_kat"] = first((a["q"] != b["q"]).any(1))
            chain.append(c)
            f = c["inna_klatka"] if c["inna_klatka"] is not None else 700
            ok.append(bool((a["loom"][:f] == b["loom"][:f]).all() and (a["dq"][:f] == b["dq"][:f]).all() and (a["q"][:f] == b["q"][:f]).all() and (mv is None or f > mv)))
        r["A_i_B_identyczne_do_pierwszej_innej_klatki"] = int(sum(ok))
        r["lancuch_czas_s"] = {k: dict(ile_par=sum(c[k] is not None for c in chain), min_med_maks=md([c[k] * 0.01 for c in chain if c[k] is not None]) if any(c[k] is not None for c in chain) else None) for k in chain[0]}
        r["komendy_roznia_sie"] = int(sum(c["inna_komenda"] is not None for c in chain))
        r["opoznienie_klatka_do_komendy_ms"] = md([(c["inna_komenda"] - c["inna_klatka"]) * 10 for c in chain if c["inna_komenda"] is not None and c["inna_klatka"] is not None]) if r["komendy_roznia_sie"] else None
        for w, (i0, i1) in W.items():
            cmd = {c: np.array([Z[s, c]["dq"][i0:i1].sum(0) for s in seeds]) for c in ("A", "B", "B1", "C")}
            ang = {c: np.array([q_at(Z[s, c], i1) - q_at(Z[s, c], i0) for s in seeds]) for c in cmd}
            loom = {c: np.array([Z[s, c]["loom"][i0:i1].sum(0) * 0.01 for s in seeds]) for c in cmd}
            cnt = {c: np.array([Z[s, c]["cnt"][i0:i1].sum(0) for s in seeds]) for c in cmd}
            o = dict(zmiana_kata_stopnie={c: {n: md(np.degrees(ang[c][:, k])) for k, n in enumerate(J)} for c in ang},
                     suma_komend_stopnie={c: {n: md(np.degrees(cmd[c][:, k])) for k, n in enumerate(J)} for c in cmd},
                     calka_oka_mVs={c: md(loom[c].sum(1)) for c in loom}, szczyt_oka_mV={c: md([Z[s, c]["loom"][i0:i1].max() for s in seeds]) for c in loom},
                     szczyt_oka_nieobciety={c: md([Z[s, c]["raw"][i0:i1].max() for s in seeds]) for c in loom},
                     impulsy={c: {n: md(cnt[c][:, k]) for k, n in enumerate(G)} for c in cnt},
                     obrot_kamery_maks={c: md([Z[s, c]["rot"][i0:i1].max() for s in seeds]) for c in loom}, zmiana_klatki_sr={c: md([Z[s, c]["fdiff"][i0:i1].mean() for s in seeds]) for c in ("A", "B1")})
            # wielkość różnicy A−B na każdym etapie: suma |A−B| po taktach / suma B (w %), oraz to samo dla B1−B
            stage = {}
            for c in ("A", "B1"):
                e = {}
                e["oko_sygnal"] = [100 * np.abs(Z[s, c]["loom"][i0:i1] - Z[s, "B"]["loom"][i0:i1]).sum() / max(Z[s, "B"]["loom"][i0:i1].sum(), 1e-9) for s in seeds]
                for k, n in enumerate(G):
                    e["impulsy_" + n] = [100 * np.abs(Z[s, c]["cnt"][i0:i1, k].astype(float) - Z[s, "B"]["cnt"][i0:i1, k]).sum() / max(Z[s, "B"]["cnt"][i0:i1, k].sum(), 1) for s in seeds]
                e["komendy"] = [100 * np.abs(Z[s, c]["dq"][i0:i1] - Z[s, "B"]["dq"][i0:i1]).sum() / max(np.abs(Z[s, "B"]["dq"][i0:i1]).sum(), 1e-9) for s in seeds]
                stage[c] = {k: [round(float(x), 2) for x in np.percentile(v, [0, 50, 100])] for k, v in e.items()}
            o["roznica_etapami_proc_B"] = stage
            o["ruch"] = {}
            for k, n in enumerate(J):
                dif, ref = ang["A"][:, k] - ang["B"][:, k], np.abs(ang["B1"][:, k] - ang["B"][:, k])
                p95, m, same = float(np.percentile(ref, 95)), float(np.median(dif)), int(max((dif > 0).sum(), (dif < 0).sum()))
                o["ruch"][n] = dict(A_minus_B_stopnie=md(np.degrees(dif)), abs_mediana_stopnie=float(np.degrees(np.median(np.abs(dif)))), ten_sam_znak=same, B1_minus_B_p95_stopnie=float(np.degrees(p95)),
                                    B1_abs_mediana_stopnie=float(np.degrees(np.median(ref))), zauwazalnie=bool(abs(m) >= 0.005 and same >= 9 and abs(m) > p95), par_z_ruchem_A=int((np.abs(ang["A"][:, k]) >= 0.005).sum()), par_z_ruchem_B=int((np.abs(ang["B"][:, k]) >= 0.005).sum()))
            r[w] = o
        r["flagi"] = {c: int(sum((Z[s, c]["flag"] > 0).sum() for s in seeds)) for c in ("A", "B", "B1", "C")}
        r["straznik"] = {c: int(sum(Z[s, c]["guard"].sum() for s in seeds)) for c in ("A", "B", "B1", "C")}
        r["kontakty"] = {c: int(max(Z[s, c]["ncon"].max() for s in seeds)) for c in ("A", "B", "B1", "C")}
        r["komenda_rozna_od_celu"] = {c: float(max(np.abs(Z[s, c]["qc"] - Z[s, c]["qt"]).max() for s in seeds)) for c in ("A", "B")}
        r["C_bez_zblizania_maks_komenda"] = float(max(np.abs(Z[s, "C"]["dq"]).max() for s in seeds))
        r["przed_zblizeniem_maks_komenda_A"] = float(max(np.abs(Z[s, "A"]["dq"][:100]).max() for s in seeds))
        r["koniec_7s_kat_A_stopnie"] = {n: md([np.degrees(Z[s, "A"]["q"][-1, k] - Z[s, "A"]["q0"][1 + k]) for s in seeds]) for k, n in enumerate(J)}
        res[f"glu{g:+d}"] = r
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=None, ensure_ascii=False, separators=(",", ":")).replace('"W', '\n"W').replace('"glu', '\n\n"glu').replace('"roznica', '\n  "roznica').replace('"ruch":', '\n  "ruch":').replace('"impulsy":', '\n  "impulsy":').replace('"lancuch', '\n"lancuch').replace('"flagi', '\n"flagi'))


if __name__ == "__main__":
    main(*sys.argv[1:3])
