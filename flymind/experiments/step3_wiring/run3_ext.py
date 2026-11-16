"""Krok 6 — integracja (eksploracja): zadanie całego ramienia z kroku 3 (run3.py bez zmian), ale sieć „pre” + 69 BM +
DNge078 + DNg15 (sieć kroku 6). BM nie dostają tu wejścia (w zadaniu podnoszenia czujnik dłoni nie jest podłączony).
Pytanie: czy dołożone drogi z głowy psują podnoszenie. Podmienia w pamięci nets.bodies_for dla reguły „pre”.
Uruchom jak run3.py (ziarna testowe kroku 3 blokuje run3.py)."""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brainleg as B  # noqa: E402
import nets  # noqa: E402

extra = [b for ids in B.route_ids() for b in ids]
_orig = nets.bodies_for


def bodies_for(rule, t=5):
    b, m = _orig(rule, t)
    return (list(dict.fromkeys(b + extra)), m) if rule == "pre" else (b, m)


nets.bodies_for = bodies_for
runpy.run_path(os.path.join(HERE, "run3.py"), run_name="__main__")
