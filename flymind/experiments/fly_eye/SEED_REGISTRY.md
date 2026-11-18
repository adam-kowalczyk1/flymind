# Rejestr ziaren — fly_eye (G2 w wersji ALIF)

Zarejestrowano 2026-11-16 ok. 19:12, PRZED pierwszym użyciem.
Kontrola kolizji: wyrażenie `\b23[ _]?5[0-9]{2}[ _]?[0-9]{3}\b` w flymind/, bio2/, reports/ → 0 trafień.
Przejrzane rejestry (11 plików `SEED_REGISTRY.md` w flymind/): używane prefiksy 15, 17–21, 39, 91, 92, 8 4xx–8 7xx, 9 2xx xxx — 23 5xx xxx wolne.

| Ziarna | Użycie | Status |
|---|---|---|
| 23 501 001 – 23 501 099 | próby dymne i `test_g2_alif.py` (nieanalizowane) | zarezerwowane |
| 23 502 001 – 23 502 010 | G2-ALIF: jednostki danych (szum sieci); połowa A = 001–005, B = 006–010; 001–004 także szum tasowań (pary, jak r1) | zarezerwowane — RAZ |
| 23 503 001 – 23 503 040 | G2-ALIF: instancje tasowania C1 (`eye_gate.shuffle_typed`) | zarezerwowane — RAZ |
| 23 501 001 – 23 501 002, 23 501 099 (zużyte) | próba dymna `g2_alif.py smoke` i `test_g2_alif.py`, 16 XI ok. 19:13 | ZUŻYTE |
| 23 502 001 – 23 502 010, 23 503 001 – 23 503 040 (zużyte) | G2-ALIF wykonany RAZ 16 XI 19:16–20:45 — wynik FAILED, `reports/fly_eye_g2_alif_20261116.md` | ZUŻYTE |
| 23 504 001 | W0: ziarno świata `object_handling.World` w `w0_render.py` (przedmiot stawiany ręcznie, generator nieużywany) | w użyciu (deterministyczne, wielokrotne) |
| 23 505 001 – 23 505 023 | W2 (17 XI): 23 losowe permutacje etykiet typów w odczycie LC4 (`w2_run.perms`); kolizji brak (wyrażenie `23[ _]?505` → 0 trafień przed wpisem) | w użyciu (deterministyczne, wielokrotne; użyte też w próbie dymnej na modelu 040) |
| 23 506 001 – 23 506 003 | D (17 XI wieczór): 3 losowe tekstury „własnego ruchu” (`d_ideal.texture`); kolizji brak (`23[ _]?506` → 0 trafień przed wpisem) | w użyciu (deterministyczne, wielokrotne) |
