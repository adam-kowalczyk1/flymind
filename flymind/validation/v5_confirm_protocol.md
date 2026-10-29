# V5 — protokół potwierdzający pętli zamkniętej (zamrożony 2026-10-28, przed przebiegiem)

Status: POTWIERDZAJĄCY, jednorazowy. Wszystkie parametry ustalone na ziarnach rozwojowych 1001–1030
(`results/v5/v5_dev1_*`, `v5_dev2_delays_*`); po odsłonięciu wyników bez zmian — zmiana = nowa wersja protokołu.
Hashe kodu i pliku kalibracji: `v5_confirm_manifest.json` (ten katalog).

## Pytanie
Czy pętla obraz → enkoder (model) → LC10a → sieć z danych MaleCNS → DNa02 L/R → dekoder → warstwa bezpieczeństwa →
SO-101 (MuJoCo) orientuje bazę na piłeczkę, i czy zależy to od okablowania z danych?

## Układ (kod `flymind/loop.py`, analiza `flymind/analyze_v5.py`)
- Sieć: `visual_path.network(0.2)` — 424 neurony, 13 510 krawędzi z danych, brak krawędzi modelowych; ALIF noise 2 mV,
  b_a 0,5. J0 = 0,2 z reguły V4 v2 (część A), nie strojone na pętli.
- Enkoder: `EncoderParams(blur_px=3)` (V4 v2). Dekoder: `SteerDecoder`, kanał DNa02, offset 0, slope z
  `results/v4/v4_partB_v2_*.json` (495,6 Hz/rad); znak ustalony z góry (L−P > 0 ⇒ w lewo); gain 2,5 1/s, w_max 1 rad/s.
- Zadanie: `loop.trial_spec(seed)` — |az0| ~ U[10°, 30°], znak losowy, ρ ~ U[0,16; 0,24] m; 3 s; takt 10 ms.
- Ziarna: 2011–2050 (n = 40), sparowane między warunkami. Tasowanie: ziarno próby + 100 000.

## Warunki
`snn`, `snn_shuffle`, `snn_swap`, `no_vision`, `classical_p` (opóźnienie 0) oraz `snn` z opóźnieniem klatek 50 ms
(5 taktów; tylko opis).

## Miary (prawda symulatora, wyłącznie do oceny)
Sukces: |e| < 5° we wszystkich taktach 2,5–3,0 s. Dodatkowo: średnie |e| w 2,5–3,0 s, czas pierwszego |e| < 5°,
liczba prób z wejściem < 5° w ≤ 2 s, przeregulowanie, takty z flagą warstwy bezpieczeństwa.

## Hipotezy (α = 0,05, Bonferroni na H2–H4 → 0,0167; testy sparowane McNemara, dokładne, jednostronne)
- H1: odsetek sukcesów `snn` ≥ 0,8 i dolna granica 95 % CI Wilsona > 0,6 (kryterium projektu, nie standard).
- H2: `snn` > `snn_shuffle` (udział topologii z danych przy tych samych wagach, stopniach i dekoderze).
- H3: `snn` > `snn_swap`; H3b: w ≥ 80 % prób `snn_swap` błąd końcowy większy niż początkowy (odwraca się od celu).
- H4: `snn` > `no_vision` (sukces nie wynika z ustawienia początkowego).
- Opis (bez hipotezy przewagi): różnica |e| końcowego `classical_p` − `snn` (bootstrap sparowany, 95 % CI);
  przewidywanie z dev: regulator P dokładniejszy. Opóźnienie 50 ms: opis (dev: 8/20).

## Interpretacja ustalona przed przebiegiem
- H1–H4 spełnione → „sieć z danych przenosi znak i rozróżnia stronę celu wystarczająco do orientacji w pętli
  zamkniętej; tasowanie okablowania niszczy zachowanie”. NIE: „SNN steruje lepiej niż klasyczny regulator”,
  NIE: „biologiczny model widzenia muchy”, NIE: „pamięć/CX” (droga LC10a nie zawiera pierścienia).
- Enkoder i dekoder (kalibracja, gain) są elementami modelu; udział SNN = ZNAK i ROZRÓŻNIENIE STRON, a skalę
  ustala kalibracja.
- Niepowodzenie którejkolwiek hipotezy raportowane jako wynik; brak powtórnego przebiegu na tych ziarnach.

## Wykluczenia
Brak. Próba przerwana błędem symulatora (SimError) liczy się jako porażka i jest raportowana osobno.
