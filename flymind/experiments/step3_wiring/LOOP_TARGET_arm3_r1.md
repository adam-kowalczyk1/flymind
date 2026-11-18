# Krok 3 — cel i reguły testu (zapisane PRZED testem, 15 XI 2026)

## Pytania
1. **Sprawa 1 — czy sieć muszki może sterować całym ramieniem?** W kroku 2 sieć z danych odłożyła 0/135. Eksploracja bez
   robota (15 XI, `results/step3_20261115/explore_rules_v1.json`) pokazała, że pula unoszenia barku milczała, bo sieć kroku 2
   zawierała tylko część neuronów przedruchowych. Reguła „pre” (wszystkie `vnc_intrinsic` z ≥ 5 synapsami do neuronów
   ruchowych „fl” strony L — sama reguła wyboru z danych, bez zmiany wag, progów ani k) daje przy Glu +1 pulę wymachu 47,6 Hz
   wobec podporu 21,5 Hz.
2. **Sprawa 2 — czy schemat połączeń ma znaczenie?** Dotychczasowe tasowanie (swobodne, równa waga) miesza warstwy. Dodaję
   kontrolę sprawiedliwszą: tasowanie zachowujące warstwy (receptory / interneurony / neurony ruchowe).

## Co jest ustalone i NIE będzie zmieniane
- Sieć: `nets.build_rule(glu, 0.2, "pre")`, 3148 neuronów; W sha256 Glu +1 `00c17540de…`, Glu −1 `98e8084d0f…`.
  Wybór reguły „pre” (najprostszej z trzech sprawdzonych: pre / pre2 / full2) zapadł po eksploracji BEZ robota i po jednej
  iteracji treningowej (ziarno 21101: N Glu +1 29/45, K 29/45, R 18/45; N Glu −1 0/45). Żaden parametr nie był strojony.
- Konfiguracja jak w teście całego ramienia kroku 2 (`LOOP_TARGET_arm_r1.md`): stawy 1, 2, 3 + obrót z sieci w fazie
  podnoszenia, wejścia padsT2 + padsT1, limit fazy 3 s, k = 0,005 rad/s/Hz, τ 50 ms, dt 1 ms, szczęka = LegJaw T2 L,
  dojazd i harmonogram klasyczne, strażnik odstępu 5 mm. Kod: `run3.py` (podmienia w pamięci tylko klasę sieci ramienia).
- Test: `--seed 21201`, 45 przedmiotów × 3 pozy = 135 prób, **raz**. Ramiona: N (dane), K, R, K0, S1–S5 (tasowania swobodne,
  ziarna 21 210 001–005), L1–L5 (tasowania zachowujące warstwy, ziarna 21 220 001–005); oba znaki Glu.

## Kryteria (wynik główny: `placed`; analiza `analyze3.py`, zapisana przed testem)
- C1 niegorszość N wobec K: dolna granica 95 % bootstrapu par ≥ −10 pp.
- C2 N > R (McNemar, p < 0,05).
- C3S N > każde z S1–S5 (McNemar + Holm). C3L N > każde z L1–L5 (McNemar + Holm).
- C4 siła ramię↔blat ≤ 5 N i bezpiecznik ≤ 10 % taktów w każdej próbie N.
- **Sprawa 1 uznana za rozwiązaną dla danego Glu**, gdy C1, C2 i C4 są spełnione (ramię z sieci nie gorsze od klasycznego,
  lepsze od odruchu, bezpieczne). **Sprawa 2 rozwiązana**, gdy dodatkowo C3L (i osobno raportowane C3S).
- Oczekiwanie zapisane uczciwie przed testem: z eksploracji wynika, że tasowania pobudzają pule MOCNIEJ niż dane
  (wymach 60–177 Hz), więc C3S i C3L najpewniej NIE będą spełnione na wyniku `placed`.

## Hipoteza dodatkowa (wtórna, z góry): „sieć z danych steruje spokojniej”
Pochodzenie: próba dymna na 3 scenach treningowych (obrót nadgarstka N ok. 0,56 rad, S1 0,85–0,91, L1 1,54–1,66).
- H-spokój (w pętli): odchylenie obrotu nadgarstka `roll_dev` w N jest mniejsze niż w każdym S_i i każdym L_i — test znaków
  na parach (te same sceny, wszystkie 135 prób), Holm w rodzinie 10 porównań, osobno dla każdego Glu.
- H-cisza (bez robota, `quiet_test.py`): przy dotyku 1 N przez 1 s średnia częstość wszystkich neuronów ruchowych „fl” L
  w sieci z danych jest niższa niż w każdym z 20 nowych tasowań swobodnych (ziarna 21 230 001–020) i każdym z 20 nowych
  tasowań zachowujących warstwy (21 240 001–020); Glu +1 i −1 osobno. Poziom: p = 1/21 na rodzinę, gdy dane są skrajne.
Te hipotezy NIE zmieniają werdyktu C3; mówią, czym sieć z danych różni się od losowej, nie że lepiej wykonuje zadanie.

## Czego nie wolno
Zmieniać reguły, parametrów ani kryteriów po zobaczeniu testu; powtarzać testu; używać ziaren testowych drugi raz.
Każda dalsza zmiana = nowy plik celu i nowe ziarna.
