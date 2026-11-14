# Cel pętli dla stawu (c) elbow_flex — wersja r1 (spisana 2026-11-13 ok. 18:20, PRZED pierwszą iteracją stawu c)

Procedura, reguły zmian, STOP, statystyka i ramiona jak `LOOP_TARGET_b_r2.md` (zatwierdzony) — poniżej tylko to, co dla (c) inne.
Obowiązują: `CALIBRATION_k_SIGNS.md` (k 0,005 rad/s/Hz, τ_r 50 ms, staw 2: POS = Ti flexor + Acc. ti flexor (T1 L), NEG = Ti
extensor (T1 L), s₂ = +1), tabela C r1, dt 1 ms w pętli (0,1 ms raz na końcu: tylko N, oba Glu).
Kod: `joint_net.py --joints 2` (nowy plik; `lift_b.py` bez zmian). Analiza: `analyze_joint.py DIR GLU --outcome lift`.

## 1. Zadanie
To samo zadanie co (b) — faza „podniesienie” benchmarku etapu czucia (45 przedmiotów, `trigger="search"`, percept-wyrocznia),
ale **ruch wykonuje staw 2 (łokieć)**: `cel₂ += +1 · 0,005 · 0,01 · (r_zgięcie − r_prostowanie)`; stawy 0, 1, 3, 4 trzymają pozę
chwytu (`script:hold_grasp_pose`). Kinematyka (CALIBRATION sekcja 3, VERIFIED statycznie): +q₂ = zgięcie = chwytak w dół, więc
**prostowanie goleni (Ti extensor) → łokieć prostuje się → chwytak w górę**. Koniec fazy, bezpiecznik stołu (clearance < 5 mm →
cel bez zmian, liczone), pomiar siły, wynik główny `lift`/135 — bez zmian względem r2 §1.

## 2. Wejścia iteracji 1 (ustalone z góry)
- dotyk padów → szczecinki T2 L (jak (b) i szczęka) **oraz** ten sam dotyk → szczecinki stopy T1 L (`padsT1`, klasa
  „mechanosensory bristle” T1 L, 150 neuronów, połowa na pad) — **[MODEL]**: pady chwytaka traktowane jak stopa przedniej nogi.
- interneurony T1 wybrane regułą `fl` (poprawka D3 z logu: ≥ 5 synaps z receptorów T1 L i ≥ 5 do dowolnego MN „fl” L; +104 IN).
- Uzasadnienie (dane, nie zadanie): `receptor_screen_groups_v1.json` (sieć bez robota) — receptory T2 L nie docierają do pul T1 L
  (0 Hz przy każdym bodźcu), a szczecinki stopy T1 L pobudzają Ti extensor (1–14 Hz przy 20–40 mV, Glu −1; 11–51 Hz przy Glu +1)
  — VERIFIED. Pule zginaczy goleni prawie milczą (≤ 0,8 Hz).
- Przewidywanie z góry [HYPOTHESIS]: przy dotyku sieć prostuje łokieć → chwytak w górę → podniesienia możliwe; prędkość
  ~0,05–0,25 rad/s (k · 10–51 Hz). Odruch R robi to samo stałą prędkością, więc **warunek C2 (lepiej niż odruch) uważam za mało
  prawdopodobny**.

## 3. Ramiona (każdy Glu osobno, te same ziarna, ta sama szczęka LegJaw T2 L)
| Ramię | Staw 2 w fazie podniesienia |
|---|---|
| N | sieć z danych jak wyżej (`snn:legT1L`) |
| S1–S5 | ta sama sieć po `visual_path.shuffle(equal_weight=True)`, te same wejścia, pule, k, znak |
| R — trywialny odruch (zdefiniowany TERAZ) | `cel₂ −= 0,5 rad/s · 0,01 s` w każdym takcie fazy (stałe prostowanie = w górę), ten sam koniec i bezpiecznik |
| K | klasyczne IK `P["lift"]` (wszystkie stawy) — to samo ramię co K w (b) |
| K0 | `object_handling.Controller` (odniesienie, bez progu) |

## 4. Odniesienia z plików (VERIFIED, odczyt 2026-11-13)
- K na ziarnach treningowych (b), seed 20101, 45 prób: lift **32/45** (Glu −1), **33/45** (Glu +1) — `lift_b/it1/it1_K_g±1.json`
  (inne ziarna niż trening (c); tylko skala).
- K na ziarnie 100 (B_fly_search, szczęka = sieć): lift 97/135 (Glu −1), 101/135 (Glu +1); K0: 99/135.
- Odruch R stawu 1 na treningu (b): 26/45 (Glu −1), 29/45 (Glu +1) — `lift_b/it1/it1_R_g±1.json`.

## 5. Cel (na ziarnach testowych, raz) — osobno dla Glu −1 i Glu +1
Identyczny jak r2 §4: C1 niegorszość wobec K (dolna granica 95 % bootstrapu różnicy lift(N) − lift(K) ≥ −0,10); C2 McNemar
N > R jednostronnie p < 0,05 i 95 % CI > 0; C3 McNemar N > Sᵢ z Holmem (5 porównań); C4 siła ramię↔blat ≤ 5 N w każdej
próbie N i przejęcia bezpiecznika ≤ 10 % taktów fazy. Próg względny wobec K na tych samych ziarnach (np. przy K ≈ 72 % → N ≥ ~62 %).

## 6. Ziarna (SEED_REGISTRY.md, wpisane 18:15 przed startem)
Trening `--seed 20301` × 45 (1 poza), tasowania 20 310 001–002. Test `--seed 20401` × 135 (3 pozy), tasowania 20 410 001–005,
bootstrap 20 499 999 (analiza używa stałego ziarna bootstrapu z `analyze_b.py`, 20 299 999 — ta sama procedura dla wszystkich
stawów; zapisane jawnie).

## 7. Iteracje, „najlepsza wersja”, koniec pętli
Reguły r2 §7–8 bez zmian (≤ 10 iteracji / 3 h; zmiany dozwolone / z nowym plikiem kalibracji / zabronione; każda zmiana na N i S1–S2,
R i K przeliczane tylko gdy zmiana ich dotyczy). Najlepsza wersja = spełnia cel na treningu; jeśli żadna — iteracja o najwyższym
lift(N) osobno dla Glu −1 i Glu +1; przy remisie — wcześniejsza iteracja. Pętla może się skończyć przed limitem, jeśli nie zostaje
żadna hipoteza w dozwolonych klasach zmian — wtedy wpis w logu z uzasadnieniem (to nie jest STOP planu).
