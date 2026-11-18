# Etap 0 (bramka G1–G3) — uzupełnienie DESIGN.md, zapisane PRZED uruchomieniem na danych (16 XI 2026)

Decyzja Adama 16 XI („Działaj, póki nie skończysz”) po raporcie `flymind/reports/fly_eye_research_20261116.md`:
robię Etap 0 w wariancie głównym DESIGN.md §4.4 — **D1 (model M-G), D2 (V_rest > 0), D3 (wejście E2) przyjęte według rekomendacji
projektu, bez osobnej odpowiedzi właściciela na każdą z nich** (jawnie). D5 (pobranie parametrów Lappalainen) — NIE.
Tylko wejście F-IDEAL (bez emulatorów kamer; Etap 1 nie jest częścią tego zadania).

## Szczegóły, których DESIGN.md nie ustalał (ustalone teraz, przed danymi)
- g: reguła `pick_g` — g = 1, połowione, aż S0 przebiega stabilnie i max f(V) w spoczynku < 20 (na ziarnach jednostek 1–2).
  Próba dymna (ziarna 15 501 001–002): g = 1.
- k (wejście do L1/L2/L3) = 1; fotoreceptor: log-jasność − adaptacja (τ 1 s) → 2 × filtr 1. rzędu τ 12 ms.
- σ szumu sieci = 0,05 (Euler–Maruyama), τ = 50 ms, V_rest = 1, dt = 1 ms.
- Bodźce S1: krawędź ON i OFF, kontrast 50 % (0,5 ↔ 1,5), 6 kierunków siatki (0°, 60°, …, 300° w osadzeniu §1), prędkości
  60, 120, 240 °/s (jak P1), start 50° od środka, 300 ms przed i po. Optyka: Gauss FWHM 5°, odstęp kolumn 5,1°.
- **Miara odpowiedzi na krawędź = SZCZYT f(V) − spoczynek** (nie średnia z okna). Zmiana po teście (e) z DESIGN §11
  (DSI bez sieci = 0,195 dla średniej — zależność od położenia komórki; dla szczytu −0,002). Zmiana przed jakimkolwiek
  przebiegiem na danych. S0: średnia zmiana w oknie 600 ms − spoczynek.
- Jednostki: dane 10 (ziarna 15 502 001–010; połowa A = 001–005, B = 006–010); tasowania C1: 40 instancji
  (15 503 001–040), każda z 4 jednostkami o ziarnach szumu 15 502 001–004 (pary z danymi; świadome powtórne użycie ziaren
  szumu, nie ziaren testu).
- DSI: kierunek pref = argmax średniej (3 prędkości) w połowie A; DSI = (R_pref − R_null)/(R_pref + R_null) w połowie B,
  R obcięte do ≥ 0; brak gdy suma < 0,001. T4 na krawędziach ON, T5 na OFF. Mediana po komórkach z określonym DSI.
- G1, G2, G3 dokładnie jak DESIGN §8 (G1 ≥ 6/7 typów; G2 ≥ 3/4 podtypów T4: mediana DSI ≥ 0,20 i > 95. percentyl z 40 tasowań;
  G3 ≥ 3/4 podtypów T4: mediana różnicy osi ≤ 30°). T5 opisowo. Glu +1: opisowo.
- Nie robię: C1b, C3–C5, M-A, S-ext (zapisane jako nie wykonane).
- **Bramka nie przejdzie → STOP**, raport, decyzja Adama (dopasowanie parametrów / flyvis).

Kod: `optic_slice.py`, `eye_gate.py`, `eye_gate_run.py`, `eye_gate_analysis.py`, `test_eye_gate.py` (test OK przed danymi).
Wyniki: `flymind/results/v1_camera/gate/`.
