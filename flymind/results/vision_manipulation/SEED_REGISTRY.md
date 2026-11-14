# Rejestr ziaren — etap „wzrok w pętli” (2026-11-10)

Zarejestrowano przed pierwszym pełnym przebiegiem (run_arms.sh v1).

| Pula | Zakres | Użycie |
|---|---|---|
| położenia przedmiotów — benchmark | 100 000 – 100 442 | `seed·1000 + indeks·10 + poza`; TE SAME przedmioty i położenia co baza klasyczna i ramiona etapu dotyku |
| położenia przedmiotów — prace rozwojowe | 101 000 – 101 442 | strojenie pomiaru z kamery, próby dymne, testy `test_vision_manipulation.py`; nie do wyników |
| szum drogi wzrokowej (2 mV) | 18 000 000 + ziarno sceny → 18 100 000 – 18 100 442 (benchmark), 18 101 000 – 18 101 442 (rozwój) | `np.random.default_rng` w `VisJaw.reset` |
| kalibracja dekodera skrętu | 18 190 000 – 18 190 006 | `vision_manipulation.calibrate` (7 azymutów) |
| testy śledzenia | 102 000 – 102 999 (+ szum 18 102 xxx) | `tracking.py` |

Kontrola kolizji: `grep -rlE "18[ _]?[01][0-9]{2}[ _]?[0-9]{3}"` w flymind/ (*.py, *.md) poza plikami tego etapu — 0 trafień.
Co było dobierane na puli rozwojowej (przed benchmarkiem): poza patrzenia, oświetlenie rozproszone, segmentacja po odcieniu,
kierunek drugiego widoku, kryterium ustalenia obrotu (średnia ω z 0,3 s), szum drogi wzrokowej 2 mV (wartość z V5).
