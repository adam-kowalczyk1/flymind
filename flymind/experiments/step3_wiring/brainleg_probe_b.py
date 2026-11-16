"""Krok 6 r3 — rodzina B na teście z sondą: tasowanie w obrębie strony i warstwy, przy czym BM (69) i DNge078+DNg15 (4) są
osobnymi grupami (zachowują liczbę i wagi synaps do każdej warstwy, ale nie to, do KTÓRYCH neuronów). Pytanie: czy liczy się,
do których motoneuronów idą dwa szlaki. Bez zmian w brainleg_probe.py; `--net B` przekazywane do reflex.main jako „G”.
Uruchom: brainleg_probe_b.py --net N|B --glu ±1 --seed S --poses P --tag T --out DIR (ziarno testowe tylko z STEP6C_FINAL_TEST=1)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brainleg as B  # noqa: E402
import brainleg_probe as P  # noqa: E402
import reflex as R  # noqa: E402

TEST6C = {21891}

if __name__ == "__main__":
    s = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else None
    if s in TEST6C | P.TEST6B | B.TEST6 and not os.environ.get("STEP6C_FINAL_TEST"):
        sys.exit("ziarna testowe kroku 6 r3 tylko w teście końcowym (STEP6C_FINAL_TEST=1)")
    if s in P.TEST6B | B.TEST6:
        sys.exit("ziarna testów r1/r2 są zużyte")
    for i, x in enumerate(sys.argv):
        if x == "--net" and sys.argv[i + 1] in ("F", "L", "G"):
            sys.exit("ten skrypt: tylko N albo B")
        if x == "--net" and sys.argv[i + 1] == "B":
            sys.argv[i + 1] = "G"
    P.install()
    _init = B.BrainNet.__init__
    B.BrainNet.__init__ = lambda self, glu, kind="N", shuffle_seed=None, rule="pre": _init(self, glu, "B" if kind == "G" else kind, shuffle_seed, rule)
    R.main()
