"""Porównanie serii historycznych (kod z f0b6927) z powtórzonymi poprawionym kodem (<tag>_<sufiks>.json).
Tylko czyta JSON-y. Porównuje WSZYSTKIE pola symulacyjne każdego cyklu co do bitu (czasy zegarowe pomija — zależą od
obciążenia komputera) i wypisuje metryki stare / nowe / różnica bez zaokrąglania różnic. Kod wyjścia 0 = brak różnic.

Uruchom:  .venv/bin/python -I -B flymind/results/pick_place/validation/compare_postfix.py [sufiks=postfix_v1]"""
import json
import os
import statistics as st
import sys

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TAGS = ("S0_baseline", "S1_v1.45", "S2_v1.45_jaw0.65", "S3_v1.45_jaw0.65_homemid", "S4_v1.0_jaw0.65_homemid",
        "S3_long500_seed6")
WALL = ("cycle_wall", "t_wall")                       # pola zegarowe: nieporównywalne między przebiegami
NEW_FIELDS = ("auto_resets", "continuous", "complete", "stopped_by", "recovered")   # dodane po audytach


def metrics(j):
    runs = j["runs"]
    cyc = [c for r in runs for c in r["cycles"]]
    ok = [c for c in cyc if c["ok"]]
    cs = [c["cycle_sim"] for c in ok]
    T = sum(r["T_sim"] for r in runs)
    pe = [c["place_err_mm"] for c in ok]
    return {"próby": len(cyc), "sukcesy": len(ok), "porażki": len(cyc) - len(ok),
            "resety": sum(r["resets"] for r in runs),
            "przerwania (serie niekompletne)": sum(not r.get("complete", True) for r in runs),
            "T_sim [s]": T, "mediana cyklu [s]": st.median(cs), "3600/mediana [op/h]": 3600 / st.median(cs),
            "ok/T_sim×3600 [op/h]": len(ok) / T * 3600, "max prędkość [rad/s]": max(r["stats"]["max_qd"] for r in runs),
            "max przyspieszenie [rad/s²]": max(r["stats"]["max_qdd"] for r in runs),
            "błąd odłożenia mediana [mm]": st.median(pe), "błąd odłożenia max [mm]": max(pe),
            "suma czasów faz [s]": sum(sum(c["t_sim"].values()) for c in ok),
            "takty symulacji (z warstwy bezp.)": sum(r["safety_stats"]["classical:pick_place"]["ticks"] for r in runs) // 6}


def main():
    suffix = sys.argv[1] if len(sys.argv) > 1 else "postfix_v1"
    total = 0
    for tag in TAGS:
        old = json.load(open(os.path.join(D, f"{tag}.json")))
        new = json.load(open(os.path.join(D, f"{tag}_{suffix}.json")))
        print(f"\n== {tag}  vs  {tag}_{suffix}")
        print(f"   kod stary: {old['git']['sha256_16']}\n   kod nowy:  {new['git']['sha256_16']}")
        diffs = []
        if old["cfg"] != new["cfg"]:
            diffs.append("cfg")
        if old["argv"][1:-1] != new["argv"][1:-1]:
            diffs.append("argv (poza tagiem)")
        for ro, rn in zip(old["runs"], new["runs"]):
            for k in ro:                              # każde pole serii ze starego pliku, poza zegarowymi
                if k in ("T_wall", "plan_wall", "per_h_wall", "cycles"):
                    continue
                if ro[k] != rn[k]:
                    diffs.append(f"seed {ro['seed']}: {k}: {ro[k]} → {rn[k]}")
            if len(ro["cycles"]) != len(rn["cycles"]):
                diffs.append(f"seed {ro['seed']}: liczba cykli")
            for co, cn in zip(ro["cycles"], rn["cycles"]):
                for k in co:
                    if k not in WALL and co[k] != cn.get(k):
                        diffs.append(f"seed {ro['seed']} cykl {co['i']}: {k}: {co[k]} → {cn.get(k)}")
                extra = set(cn) - set(co)
                if extra:
                    diffs.append(f"seed {ro['seed']} cykl {co['i']}: nowe pola {sorted(extra)}")
            extra = set(rn) - set(ro) - set(NEW_FIELDS)
            if extra:
                diffs.append(f"seed {ro['seed']}: nieoczekiwane nowe pola serii {sorted(extra)}")
        if len(old["runs"]) != len(new["runs"]):
            diffs.append("liczba serii")
        mo, mn = metrics(old), metrics(new)
        print(f"   {'metryka':38s} {'stare':>22s} {'nowe':>22s} {'różnica':>12s}")
        for k in mo:
            print(f"   {k:38s} {mo[k]!r:>22} {mn[k]!r:>22} {mn[k] - mo[k]!r:>12}")
            if mo[k] != mn[k]:
                diffs.append(f"metryka {k}")
        new_flags = {k: [r.get(k) for r in new["runs"]] for k in ("auto_resets", "continuous", "complete", "stopped_by")}
        print(f"   nowe pola serii: {new_flags}; plik complete={new.get('complete')}")
        if not new.get("complete") or any(r["auto_resets"] or not r["continuous"] for r in new["runs"]):
            diffs.append("nowa seria niekompletna / z resetem")
        print(f"   pola symulacyjne porównane co do bitu: {sum(len(r['cycles']) for r in old['runs'])} cykli; "
              f"RÓŻNICE: {len(diffs)}")
        for x in diffs[:20]:
            print("     -", x)
        total += len(diffs)
    print(f"\nŁĄCZNIE różnic w polach symulacyjnych: {total}")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
