# Bramka r2 (opcja 1: dynamika typów z literatury) — wynik (16 XI 2026, 14:58–15:35)

Cel: `experiments/v1_camera_input/PREREG_GATE_r2.md`, hashe `PRE_GATE_HASHES.txt` (14:57:50). 42/42 plików, bez błędów
(nieudany był tylko mój jednorazowy skrót wypisujący wynik; `gate_result.json` zapisany poprawnie).

| Kryterium | r1 (jednakowe τ) | r2 (τ z literatury) | Werdykt r2 |
|---|---|---|---|
| G1 polaryzacja | 7/7 | 7/7 (Mi1 +0,36, Tm3 +0,79, T4 +0,66, Tm1 −0,78, T5 −0,98, L1/L2 −1) | PASS |
| G2 mediana DSI T4a–d | 0,001–0,008 | **0,025 / 0,030 / 0,027 / 0,026** (tasowania p95: 0,023 / 0,016 / 0,022 / 0,021) | **FAILED** — powyżej tasowań we wszystkich 4 podtypach, ale ~8× poniżej progu 0,20 |
| G3 oś Mi9–Mi4 | 34–46° | 33°, 34°, 34°, 43° | FAILED |
| T5a–d | 0,001–0,004 | 0,020–0,032 (poniżej tasowań) | — |
| Glu +1 (opisowo) | 0,07 | brak (NaN — brak określonych DSI) | — |

Wniosek: dynamika z literatury daje **słaby, ale niezerowy** ślad kierunkowości w T4 ponad tasowaniami (INFERRED: test 95.
percentyla dla 4/4 podtypów; sam ten warunek nie był kryterium bramki). Do działającego czujnika kierunku daleko.
Zgodnie z decyzją Adama: przechodzę do opcji 2 (flyvis). Ziarna 15 502 011–020, 15 511 001–040 zużyte.
