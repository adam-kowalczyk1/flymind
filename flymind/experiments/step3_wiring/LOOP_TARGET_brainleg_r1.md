# Krok 6 — dotyk głowy porusza łokciem i nadgarstkiem przez dwa szlaki z danych (cel zapisany PRZED testem, 16 XI 2026)

## Pytanie
Czy sieć z danych MaleCNS („pre” + 69 neuronów szczecinek głowy BM + 2 DNge078 + 2 DNg15; 3221 neuronów, `brainleg.py`)
po dotyku „dłoni” (wejście do BM, próg oddania F_ON 3 N) porusza **łokciem** (szlak BM→DNg15→prostownik goleni) **i
nadgarstkiem** (szlak BM→DNge078→dźwigacz stopy), a bez dotyku (próba C) stoi — i czy robi to lepiej niż te same sieci
z przetasowanymi połączeniami?

## Co wiadomo z treningu (ziarno 21421, 3 pozy; 9 ważnych par na Glu) — NIE dowód
- Glu −1: łokieć 7/9, nadgarstek 7/9, oba 7/9, chwyt bez dotyku stoi 9/9; odpowiedź wybiórcza 7/9.
- Glu +1: łokieć 8/9, nadgarstek 0/9 (mediana 0,012 rad < próg 0,02), oba 0/9.
- Tasowania F1 (21 100 001) i L6 (21 100 006): ruszają ramieniem także BEZ dotyku (C stoi 0/15) — dlatego główną
  miarą porównania jest **odpowiedź wybiórcza** (oba stawy ruszyły w W **i** para C stała). Ta zmiana miary powstała
  po obejrzeniu treningu i jest zapisana tu jawnie, przed testem.
- 6 z 15 prób W na Glu jest nieważnych (poza nieosiągalna dla walca 60 mm) — tak samo w każdej sieci.

## Przewidywanie z treningu (zapisane, żeby było widać, czy test je potwierdzi)
Glu −1: BL_A/BL_B/BL_C na granicy progu (trening 78 %); Glu +1: BL_A tak, BL_B i BL_C **nie** (nadgarstek za słaby).

## Test
`brainleg.py --seed 21831 --poses 6`, z `STEP6_FINAL_TEST=1`, **raz**. Sieci: N; F1–F5 (21 840 001–005, tasowanie
swobodne, równe wagi); L1–L5 (21 850 001–005, tasowanie w obrębie strony/warstwy); oba Glu. 22 przebiegi.
Bez zmian względem treningu: sieć, wejścia, k, dt, czas sterowania 0,5 s, F_ON 3 N, progi ruchu.

## Kryteria (analyze_brainleg.py, liczone osobno dla Glu +1 i Glu −1, na ważnych parach W/C)
- BL_A: łokieć |dq2| ≥ 0,01 rad w ≥ 80 % par.
- BL_B: nadgarstek dq3 ≥ 0,02 rad w ≥ 80 % par.
- BL_C: oba stawy w ≥ 70 % par.
- BL_D: próba C stoi (|dq2| ≤ 0,01 i |dq3| ≤ 0,01) w ≥ 95 % par.
- H(F), H(L): odpowiedź wybiórcza N lepsza niż każde z 5 tasowań (McNemar dokładny, Holm w rodzinie 5, p < 0,05).
Cel „dotyk głowy steruje łokciem i nadgarstkiem” = BL_A–BL_D dla danego Glu. Dowód schematu = H(F) i H(L).
Wyniki zapisuję osobno dla każdego Glu; nie wybieram znaku po fakcie.

## Zastrzeżenia z góry
Szlaki wybrałem z danych sam (przeszukanie: `brain_leg_search.py`, `explore_dng15.py`) — to test, czy wybrane szlaki
działają w pętli z robotem, a nie odkrycie, że mucha tak robi. Oba szlaki są acetylocholinowe (konsensus), więc znak Glu
działa tylko przez resztę sieci „pre”. Symulacja MuJoCo, bez prawdziwego robota.
