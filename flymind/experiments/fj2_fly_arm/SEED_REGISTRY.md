# Rejestr ziaren — FJ2 (eksploracja: ramię sterowane przez muchę)

Zarejestrowano 2026-11-03 przed pierwszym użyciem tych ziaren. Wszystkie pule są EKSPLORACYJNE. Nie są pulami potwierdzającymi:
test potwierdzający FJ2 dostanie nową pulę.

**Kontrola kolizji:** wyrażenie `\b9[ _]?21[1-9][ _]?[0-9]{3}\b` przeszukane w flymind/ i bio2/ (*.py, *.json, *.md, *.txt) dało 0 ziaren.

**Pule zakazane** (jak w rejestrach programu i FJ1): 0–39, 300–399, 8 4xx xxx – 8 7xx xxx, 910 xxxx – 912 xxxx,
9 201 xxx, 9 208 xxx, 9 209 xxx.

| Pula | Zakres | Użycie |
|---|---|---|
| tasowanie sieci sześciu nóg, Glu −1 | 9 211 001 – 9 211 010 | `visual_path.shuffle(spec, seed, equal_weight=True)` w `shuffle_six_legs.py` |
| tasowanie sieci sześciu nóg, Glu +1 | 9 211 011 – 9 211 020 | jw. |
| zapas / smoke | 9 218 001 – 9 218 099 | sprawdzenia potoku, nieanalizowane |
| red team | 9 219 001 – 9 219 999 | własne sprawdzenia agentów |

**Szum ALIF:** 0. Generator jest tworzony z seed=None i nigdy nie losuje.
