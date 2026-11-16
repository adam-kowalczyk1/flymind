# Krok 5b — nadgarstek, próg oddania dłoni 3 N (cel zapisany PRZED testem, 16 XI 2026)

## Dlaczego ta zmiana (wniosek po teście r1 — hipoteza, nie dowód)
W teście r1 (`LOOP_TARGET_wrist_r1.md`, ziarno 21701) 19/25 prób cofnięcia ruszyło nadgarstkiem (próg 20). W 6 z 10
porażek nacisk dłoni w chwili oddania był >1 N, ale spadał do 0,05–0,67 N w ciągu 0,5 s, i wtedy nadgarstek nie ruszał.
Jedyna zmiana: próg oddania F_ON 1 N → 3 N (`reflex5_f3.py`). Trening (ziarno 21411, 3 pozy, 13 ważnych prób na Glu):
nadgarstek ruszył w 13/13 prób (oba Glu), sukces ścisły 7/13 (oba Glu). Trening NIE jest dowodem — to tylko kontrola, że
zmiana nie psuje sterowania.

## Co się NIE zmienia
Sieć („pre” + 69 BM + 2 DNge078), wejścia, pady, k, dt, szczęka, strażnik, dojazd klasyczny, czas sterowania 0,5 s,
progi ruchu (≥ 0,02 rad w W; ≤ 0,01 rad w C i bark/łokieć ≤ 0,01 rad), definicje K5-A i K5-B (analyze_wrist.py,
analyze_reflex.py) — identyczne jak w LOOP_TARGET_wrist_r1.md.

## Test
`--seed 21801` (W: 21 801 000–049; C: 21 801 100–149), 6 póz, **raz**, z `STEP5B_FINAL_TEST=1`.
Sieci: N; F1–F5 (21 810 001–005); L1–L5 (21 820 001–005); oba znaki Glu. Ziarna z 21 8xx xxx; 21 9xx xxx nie są używane.

## Kryteria (bez zmian względem r1)
- K5-A: w N ≥ 80 % ważnych prób W z ruchem nadgarstka ORAZ ≥ 95 % ważnych prób C ze spoczynkiem — dla OBU Glu.
- K5-B: H-R(F), H-R(L) z analyze_reflex.py (ścisły sukces OBA; McNemar + Holm).

## Zastrzeżenia zapisane z góry
Ten test to druga próba tego samego pytania po zmianie wybranej na podstawie testu r1. Sukces tutaj byłby wynikiem
eksploracyjnym tylko częściowo, bo zmiana powstała po zobaczeniu porażek; porażka potwierdzi, że próg nie wystarcza.
Oba wyniki zapisuję jako są, z oznaczeniem „r2 po zmianie wynikającej z r1”.
