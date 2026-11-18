# Etap 0 — bramka „czy płat wzrokowy z danych liczy kierunek ruchu” — wynik (16 XI 2026)

Cel zapisany przed uruchomieniem: `experiments/v1_camera_input/DESIGN.md` §8 + `PREREG_GATE.md`; hashe: `PRE_GATE_HASHES.txt` (14:27:52).
Uruchomione raz, 14:28–14:48: dane Glu −1 (główne), Glu +1 (wrażliwość), 40 tasowań C1; 42/42 plików, bez błędów.
Wycinek: prawe oko, 5120 neuronów (odtworzony co do neuronu). Model M-G (stopniowany), jednolite parametry, g = 1.

| Kryterium | Wynik | Werdykt |
|---|---|---|
| **G1** polaryzacja ON/OFF (≥ 6/7 typów) | L1 −1, L2 −1, Mi1 +0,91, Tm3 +1, Tm1 −1, T4 +0,98, T5 −0,95 → **7/7** | **PASS** — rozdział ON/OFF wynika z samych połączeń i znaków |
| **G2** kierunek (≥ 3/4 podtypów T4: mediana DSI ≥ 0,20 i > 95. percentyl tasowań) | mediany DSI T4a–d: 0,003 / 0,008 / 0,006 / 0,001 (tasowania p95: 0,007–0,012); T5a–d 0,001–0,004 | **FAILED** — brak kierunkowości (DSI ~0, jak w tasowaniach) |
| **G3** oś Mi9–Mi4 (≤ 30°) | mediany różnicy 34°, 39°, 41°, 46° (losowo ≈ 45°) | **FAILED** |
| Glu +1 (opisowo) | T4 mediana DSI 0,067–0,072 | poniżej progu 0,20 |
| **BRAMKA** | | **FAILED → STOP** (zgodnie z DESIGN §8 i planem z 12 XI) |

## Co to znaczy
- Połączenia z danych **same** dają prawidłowy podział na „jaśniej” (Mi1, Tm3, T4) i „ciemniej” (L1, L2, Tm1, T5) — VERIFIED (model).
- Połączenia z danych przy **jednakowych** stałych czasowych neuronów **nie** dają czujników kierunku ruchu — VERIFIED (model).
  Zgodne z literaturą: kierunkowość T4/T5 wymaga różnych opóźnień wejść (Mi1/Tm3 szybkie, Mi4/Mi9 wolniejsze; Haag i in. 2016,
  2017), a Lappalainen i in. 2024 musieli dopasować 734 parametry. Konektom mówi „kto z kim”, nie „jak szybko”.
- Zgodnie z planem nie podłączam oka do ramienia. Decyzja dla Adama: (a) stałe czasowe per typ z literatury
  (pomiary, nie dopasowanie do wyniku), (b) pobranie flyvis (gotowe, dopasowane parametry; inny konektom), (c) wstrzymać oko.

## Zmiany względem projektu (jawnie)
Miara odpowiedzi na krawędź = szczyt zamiast średniej (po teście e, przed danymi). Nie wykonane: C1b, C3–C5, M-A, S-ext, Etap 1.
Pliki: `data_glu-1.npz`, `data_glu1.npz`, `shuf_01–40.npz`, `gate_result.json`, logi.
