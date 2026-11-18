# Rejestr ziaren — FJ1 (szczęka sterowana obwodem nogi muchy)

Zarejestrowano 2026-11-03, PRZED jakimkolwiek uruchomieniem FJ1 (także przed smoke).

**Kontrola kolizji (2026-11-03):** wyrażenie `\b9[ _]?2[0-9]{2}[ _]?[0-9]{3}\b` na flymind/ i bio2/ (*.py, *.json, *.md, *.txt) dało 4 trafienia. Wszystkie to liczby dziesiętne w plikach wyników (np. 0.9244375), żadne nie jest ziarnem.

**Pule zakazane** (jak w programme registry): 0–39, 300–399 i wszystkie pule zużyte wcześniej (8 4xx xxx – 8 7xx xxx, 910 xxxx – 912 xxxx).

| Pula | Zakres | Użycie |
|---|---|---|
| tasowanie C, Glu −1 | 9 201 001 – 9 201 010 | `visual_path.shuffle(spec, seed, equal_weight=True)`: 10 instancji, test potwierdzający |
| tasowanie C, Glu +1 | 9 201 011 – 9 201 020 | jw. |
| smoke | 9 208 001 – 9 208 099 | tylko sprawdzenie potoku, nigdy nie analizowane (001: Glu −1, 002: Glu +1) |
| red team | 9 209 001 – 9 209 999 | własne sprawdzenia agentów red teamu (każdy zapisuje, czego użył) |

**Szum ALIF:** 0 we wszystkich ramionach. Generator ALIF jest tworzony z seed=None i nigdy nie losuje, więc ziaren szumu nie ma.
