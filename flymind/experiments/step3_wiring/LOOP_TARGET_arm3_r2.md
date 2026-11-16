# Krok 3 — cel r2: limit fazy podnoszenia 10 s (zapisany PRZED testem, 15 XI 2026)

Powód: w teście r1 (limit 3 s) sieć z danych przy Glu −1 uniosła przedmiot w 102/135 prób, ale odłożyła 0 — za wolno
(napęd tylko z łokcia). To zmiana po zobaczeniu wyniku r1, dlatego: nowy plik celu, nowe sceny testowe, osobny werdykt.
Wynik r1 pozostaje bez zmian.

- Jedyna różnica względem `LOOP_TARGET_arm3_r1.md`: `--lift-max 10` (dla wszystkich ramion). Sieć, wejścia, k, dt, szczęka,
  strażnik — identyczne. Eksploracja: jedna iteracja treningowa (ziarno 21101, `train/it1_lm10_*.json`): N Glu +1 29/45,
  N Glu −1 30/45, K 29/45, R 19/45; czas dojścia do wysokości transportu: mediana 1,95 s (Glu +1) i 5,5 s (Glu −1).
- Test: `--seed 21301`, 135 prób, **raz**. Ramiona: N, K, R (oba Glu) i K0. Tasowań w r2 NIE ma — pytanie o tasowania
  rozstrzygnął r1 (C3S, C3L niespełnione) i r2 go nie zmienia.
- Kryteria (analiza `analyze3.py`, bez zmian): C1 niegorszość wobec K (≥ −10 pp), C2 N > R (McNemar p < 0,05),
  C4 siła ≤ 5 N i bezpiecznik ≤ 10 %. **Sprawa 1 uznana za rozwiązaną niezależnie od znaku glutaminianu**, gdy C1, C2, C4
  spełnione dla OBU Glu.
- Uczciwie: limit 10 s to łagodniejsze zadanie niż 3 s; raport musi podawać oba wyniki obok siebie.
