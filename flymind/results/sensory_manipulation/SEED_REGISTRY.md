# Rejestr ziaren — etap „czucie i manipulacja” (2026-11-10)

Zarejestrowano przed pierwszym pełnym przebiegiem ramion. Szum ALIF = 0 (generator tworzony z seed=None, nie losuje).

| Pula | Zakres | Użycie |
|---|---|---|
| położenia przedmiotów | 100 000 – 100 442 | `seed·1000 + indeks·10 + poza`, te same co `object_handling` B_base (identyczne przedmioty i pozy we wszystkich ramionach) |
| tasowanie S (Glu −1) | 17 100 001 – 17 100 003 | `visual_path.shuffle(spec, seed, equal_weight=True)`, 3 instancje |
| smoke | 9 208 001 (pula smoke FJ1) i poza 3 | tylko sprawdzenie potoku na cube_M/mid i sphere/mid, nieanalizowane |

Kontrola kolizji: `grep` wzorca `17[ _]?100[ _]?00[0-9]` w flymind/ (*.py, *.md, *.json) poza tym katalogiem — 0 trafień.
Przedmioty użyte przy pracy nad kodem (nie są niezależnym testem): cube_M/mid, sphere/mid.
