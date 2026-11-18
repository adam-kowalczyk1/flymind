"""Etap 2 — analiza testu z wyrównaną aktywnością (reguły LOOP_TARGET_loud_r1.md): analyze_reflex2.py bez zmian, inne ziarna scen.
Uruchom: analyze_loud.py KATALOG OUT.json   (pliki x{SEED}_{N|F1..F5|L1..L5}_g{Glu}.json)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_reflex2 as A  # noqa: E402

A.SEEDS = (21874, 21875, 21876)

if __name__ == "__main__":
    A.main(*sys.argv[1:3])
