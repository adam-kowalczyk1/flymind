"""FJ1 — analiza według reguł z PROTOCOL.md (spisana przed uruchomieniem --run; poprawki po red teamie r1 nie zmieniają
progów H1/H2). Czyta results/fj1_trials.jsonl, drukuje werdykty H1/H2, raport H3 i kontroli zerowej oraz tabelę
instancji C (wtórna). Nic nie losuje.  Uruchom:  .venv/bin/python -I -B flymind/experiments/fj1_fly_jaw/analyze_fj1.py"""
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = {"A": "snn:legT2L", "C": "snn:legT2L", "D": "classical:reflex", "N": "classical:null"}


def check(rows):
    """Integralność: każda próba ok, 12 prób na ramię/instancję, brak duplikatów, oczekiwane źródła komend."""
    bad = [r for r in rows if r["status"] != "ok"]
    if bad:
        raise SystemExit(f"{len(bad)} prób przerwanych — brak werdyktu: {[(r['arm'], r['seed'], r['pos'], r['status']) for r in bad][:5]}")
    keys = Counter((r["arm"], r["seed"], tuple(r["pos"])) for r in rows)
    if any(v > 1 for v in keys.values()):
        raise SystemExit("duplikaty prób")
    per = Counter((r["arm"], r["seed"]) for r in rows)
    if any(v != 12 for v in per.values()) or len([k for k in per if k[0].startswith("C_")]) != 20:
        raise SystemExit(f"niekompletne: {dict(per)}")
    for r in rows:
        if r["sources"] != sorted({"classical:reach", "classical:open", SRC[r["arm"][0]]}):
            raise SystemExit(f"nieoczekiwane źródła {r['sources']} w {r['arm']}")


def verdicts(rows):
    A = {g: sum(r["success"] for r in rows if r["arm"] == f"A_glu{g:+.0f}") for g in (-1.0, 1.0)}
    C = {g: defaultdict(int) for g in (-1.0, 1.0)}
    for r in rows:
        if r["arm"].startswith("C_"):
            C[r["glu"]][r["seed"]] += r["success"]
    out = {}
    for g in (-1.0, 1.0):
        cs = [C[g][s] for s in sorted(C[g])]
        mc = sum(cs) / len(cs)
        h1 = "POTWIERDZONA" if A[g] >= 10 else "ODRZUCONA" if A[g] <= 7 else "NIEROZSTRZYGNIĘTA"
        h2 = ("POTWIERDZONA" if all(A[g] > c for c in cs) and mc <= A[g] - 4 else
              "ODRZUCONA" if mc >= A[g] - 1 else "NIEROZSTRZYGNIĘTA")
        out[g] = dict(A=A[g], C=cs, C_seeds=sorted(C[g]), C_mean=round(mc, 2), H1=h1, H2=h2,
                      C_ge_A=sum(c >= A[g] for c in cs))
    return out


def main():
    path = os.path.join(HERE, "results", sys.argv[1] if len(sys.argv) > 1 else "fj1_trials.jsonl")
    rows = [json.loads(x) for x in open(path)]
    check(rows)
    v = verdicts(rows)
    D = sum(r["success"] for r in rows if r["arm"] == "D_reflex")
    N = sum(r["success"] for r in rows if r["arm"] == "N_zero")
    for g, x in v.items():
        print(f"Glu {g:+.0f}: A {x['A']}/12 → H1 {x['H1']};  C średnia {x['C_mean']}/12 → H2 {x['H2']}")
        print(f"   [wtórne] instancje C (ziarno: sukcesy/12): " + ", ".join(f"{s}: {c}" for s, c in zip(x["C_seeds"], x["C"]))
              + f"; instancji C ≥ A: {x['C_ge_A']}/10")
        print(f"   H3: odruch D {D}/12 vs A {x['A']}/12 → " + ("brak przewagi obwodu nad trywialnym odruchem" if D >= x["A"]
                                                           else "obwód osiąga więcej sukcesów niż odruch D"))
    print(f"Kontrola zerowa N (moment 0 po dotyku): {N}/12")
    for arm in ("A_glu-1", "A_glu+1", "D_reflex", "N_zero"):
        rr = [r for r in rows if r["arm"] == arm]
        print(f"  {arm:9s} uniesienie {min(r['lift_mm'] for r in rr):.1f}–{max(r['lift_mm'] for r in rr):.1f} mm, "
              f"częstości prostownik/zginacz {sorted({tuple(r['rates']) for r in rr})[:3]}, "
              f"przycięcia momentu {sorted({json.dumps(r['jaw_clips']) for r in rr})}")
    fails = [(r["arm"], r["pos"], r["lift_mm"], r["end_touch"], r["table_hits"]) for r in rows
             if r["arm"].startswith(("A_", "D_")) and not r["success"]]
    print("Porażki A/D:", fails or "brak")


if __name__ == "__main__":
    main()
