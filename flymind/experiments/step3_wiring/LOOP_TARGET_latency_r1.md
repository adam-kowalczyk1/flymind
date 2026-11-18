# Czysty pomiar czasu pętli (cel zapisany PRZED pomiarem, 16 XI 2026; zgoda Adama „Tak, zmierz”)

## Po co
- Benchmark kolorów (`LOOP_TARGET_colour_r1.md`) dał p99 taktu 71–95 ms, czyli K3 = FAILED.
- Wszystko liczyło się wtedy na obciążonym komputerze: 5 przebiegów naraz plus test innej sesji.
- Wynik K3 z benchmarku zostaje bez zmian. Ten pomiar to NOWY cel: czy pętla mieści się w 60 ms, gdy liczy się tylko jeden przebieg?

## Pomiar (raz)
- **Kod:** ten sam co w benchmarku (`colour_bench.py`, percepcja „chroma”); nic nie zmieniam.
- **Sceny:** `--seed 21992`, czyli sceny 21 992 000–440; szum drogi wzrokowej 39 992 000–440.
- **Przedmioty:** 9 (9 kształtów, materiał hard_grip), w kolorach zielonym i czerwonym.
- **Kolejność:** E_vis_touch zielony, E czerwony, A_cam zielony, A czerwony. Po JEDNYM procesie, kolejno; żadnych innych moich obliczeń w tym czasie.
- **Obciążenie:** zapisuję `uptime` i listę procesów przed i po.
  - Przed pomiarem (21:23) działa jeden proces innej sesji: `bridge_loom.py`, ok. 1 rdzeń z 10. Nie mogę go zatrzymać; zapisuję to uczciwie.
- **Wyniki:** `results/step3_20261115/latency/`.

## Kryterium (`analyze_latency.py`)
- **K3-clean (osobno dla A i E):** p99 czasu taktu < 50 ms w każdym przebiegu, czyli 10 ms okresu kamery + p99 obliczeń < 60 ms.
- **Opisowo:** mediana, p95, p99,9, maksimum, liczba taktów > 50 ms, sukcesy.

## Oczekiwanie
- Spełnione dla obu: p99 24–31 ms w przebiegach przy małym obciążeniu i w próbach dymnych.
- Maksimum może przekroczyć 60 ms (pojedyncze takty) — nie jest kryterium.

## Granice
- Czas zegarowy na tym laptopie, w symulacji.
- Nie obejmuje opóźnień prawdziwej kamery, USB ani serw.
- Takt fizyki (10 ms) jest stały, więc „pętla” = okres kamery + obliczenia.
