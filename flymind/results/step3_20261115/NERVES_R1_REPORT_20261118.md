# Etap 3a — „nerwy” w symulacji (18 XI 2026)

Cel zapisany przed testem: `flymind/experiments/step3_wiring/LOOP_TARGET_nerves_r1.md`. Kod: `nerves.py` (model FSR402 + Arduino
i serw STS3215), `nerves_run.py`, `analyze_nerves.py`. Wyniki: `nerves_test/`, `analysis_nerves_r1.json`, hasze PRE/POST.
Sceny 21941–21943 × 6 póz → 80 par (dotyk dłoni + chwyt) i 90 chwytów na każdy wariant. Uruchomiony raz (pierwszy start zatrzymał się
na argumentach przed jakąkolwiek symulacją — zepsuta lista w zsh; opis w audit_log, logi w `nerves_test/failed_start_zsh/`).

## Wynik

| Glu | Nerwy | Wycofanie po dotyku dłoni | Z wycięciem DNg15+DNge078 | Spokój przy chwycie | Chwyt | Ponowny dotyk (próby) | Kryteria |
|---|---|---|---|---|---|---|---|
| +1 | brak (idealne) | 80/80 | — | 80/80 | 63/90 | 0 | — |
| +1 | **typowe** | **80/80** | **0/80** | **80/80** | **82/90** | 1 | **PASS** |
| +1 | pesymistyczne | 80/80 | 0/80 | 79/80 | 90/90 | 28 | PASS |
| −1 | brak (idealne) | 56/80 | — | 80/80 | 74/90 | 0 | — |
| −1 | **typowe** | **66/80 (83 %)** | **0/80** | **80/80** | **90/90** | 17 | **PASS** |
| −1 | pesymistyczne | 75/80 | 0/80 | 80/80 | 90/90 | 29 | PASS |

Mediana czasu do puszczenia dłoni: Glu +1 0,04 s (idealne) → 0,06 s (typowe) → 0,09 s (pesymistyczne).

## Co to znaczy
- **Mózg muchy działa z nerwami jak w prawdziwym ramieniu** (2 czujniki, szum, opóźnienia, kwantowanie serw): przy Glu +1 wszystko
  jak w etapie 1; wycięcie dwóch neuronów zstępujących dalej znosi odruch całkowicie (0/80).
- **Przewidywanie dla Glu −1 było błędne**: z nerwami wycofanie przekroczyło próg 80 % (bez nerwów 70 %, jak w etapie 1).
  Możliwe wyjaśnienie (niesprawdzone): opóźnienie sprawia, że ruch trwa dłużej i odsuwa dłoń dalej.
- Przy wolnych nerwach (pesymistyczne) ramię często „odbija”: puszcza, wraca i dotyka ponownie (28–29 z 80 prób), choć na końcu dłoń jest wolna.
  Na prawdziwym ramieniu to może wyglądać jak drganie — wtedy trzeba skrócić opóźnienia, nie zmieniać mózgu.
- Chwyt z nerwami wychodzi CZĘŚCIEJ niż bez nich — prawdopodobnie dlatego, że jeden czujnik padu pobudza obie połówki receptorów padów
  (wybór sprzętowy zapisany przed testem). To nie jest „lepszy mózg”, tylko silniejsze wejście.

## Zastrzeżenia
Model nerwów ≠ sprzęt (brak luzów, innej sztywności serw, przesunięcia czujnika). Moment szczęki jako PWM STS3215 — NIEZNANE, czy da się
tak sterować na prawdziwym serwie. Bez tasowań (pytanie o odporność, nie wybiórczość). Symulacja, dłoń = szczecinki głowy (BM), palce = noga T2 L.
