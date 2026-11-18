# Cel pętli dla stawu (d) wrist_flex — wersja r1 (spisana 2026-11-13, PRZED pierwszą iteracją stawu d; hash w logu)

Procedura, reguły zmian, STOP, statystyka i ramiona jak `LOOP_TARGET_b_r2.md` i `LOOP_TARGET_c_r1.md` — tu tylko różnice.
Kalibracja (`CALIBRATION_k_SIGNS.md`, bez zmian): staw 3: POS = Ta levator MN (2, T1 L), NEG = Ta depressor MN (5, T1 L), s₃ = −1;
**[ANALOGIA] budowy** (ostatni zawias przed końcówką); funkcja pul Ta levator/depressor w literaturze NOT FOUND (tylko nazwy — INFERRED).
Kod: `joint_net.py --joints 3`. Analiza: `analyze_joint.py DIR GLU --outcome lift`.

## 1. Zadanie
Faza „podniesienie” jak (b)/(c), ruch wykonuje **staw 3 (wrist_flex)**: `cel₃ += −1 · 0,005 · 0,01 · (r_levator − r_depressor)`;
stawy 0, 1, 2, 4 trzymają pozę chwytu. Kinematyka (VERIFIED statycznie): +q₃ opuszcza koniec chwytaka (−6,5 mm / +0,05 rad
w Q_POSE), więc „levator” → −q₃ → w górę. Uwaga z góry: sam nadgarstek obraca chwytak wraz z przedmiotem; 5,5 cm wymaga
~0,4 rad — przedmiot może się wysunąć. Ten sam koniec fazy, bezpiecznik, pomiar siły, wynik główny `lift`/135.

## 2. Wejścia iteracji 1 (ustalone z góry) — te same co (c) it1
`padsT2` + `padsT1`, interneurony regułą `fl`. Przewidywanie z góry [HYPOTHESIS, z `receptor_screen_v1.json` i
`receptor_screen_groups_v1.json`]: pule Ta levator i Ta depressor mają 0,0 Hz przy KAŻDYM badanym bodźcu receptorowym (pojedyncze
typy, klasy, wszystkie receptory T1 L, 10–40 mV, Glu ±1) — sieć z danych **nie poruszy stawu 3**; spodziewany wynik N ≈ 0/45
(„no_lift”). Tasowania mogą się ruszać (inne połączenia).

## 3. Ramiona
N (sieć), S1–S5 (tasowania), **R = `cel₃ −= 0,5 rad/s · 0,01 s` w każdym takcie fazy (stałe unoszenie nadgarstkiem, zdefiniowane
TERAZ)**, K (klasyczne IK `P["lift"]`), K0. Szczęka: samodzielny LegJaw T2 L (poza K0).

## 4. Odniesienia (VERIFIED, pliki)
K (trening b, seed 20101): lift 32/45 (Glu −1), 33/45 (Glu +1); K seed 100: 97/101 z 135; K0 99/135.

## 5. Cel — jak r2 §4 (C1 niegorszość wobec K −10 pp; C2 McNemar N > R; C3 N > S1–S5 z Holmem; C4 ≤ 5 N i bezpiecznik ≤ 10 %).

## 6. Ziarna (SEED_REGISTRY.md): trening `--seed 20501` × 45, tasowania 20 510 001–002; test `--seed 20601` × 135,
tasowania 20 610 001–005 (bootstrap: stałe ziarno `analyze_b.py`, jak dla wszystkich stawów).

## 7. Iteracje i koniec pętli — jak (c) r1 §7. Jeśli żadna dozwolona zmiana nie daje hipotezy, jak pobudzić pule Ta (wejścia
tylko przez receptory), pętla kończy się wcześniej z uzasadnieniem w logu.
