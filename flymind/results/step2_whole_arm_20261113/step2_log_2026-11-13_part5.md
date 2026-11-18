# Krok 2 — log sesji „FlyMind autonomiczny plan ramienia” (część 5 i dalej) — 2026-11-13

Ciąg dalszy wpisów z `step2_log_2026-11-13.md` („Część 5”, punkty 5.1–5.3.4). Od 18:35 ta sesja pisze tylko tutaj (prośba
drugiej sesji, która prowadzi staw (b) i pisze „Część 4” w logu wspólnym). Oznaczenia dowodów jak w logu wspólnym.

## 5.4 Pliki zapisane przed przebiegami

| Plik | sha256 | Kiedy / po co |
|---|---|---|
| `experiments/step2_whole_arm/LOOP_TARGET_arm_r1.md` | `e4d6d4b3f423881fdf14bd3f4ee10ddc0d4eb7a5f00f31ec85a8dd6cf01fc432` | 18:24, cel kroku 5 (całe ramię), przed jakimkolwiek przebiegiem kroku 5 |
| `experiments/step2_whole_arm/CONFLICT_TARGET_r1.md` | `e1746e72db2b19ec44d93e59b31b76ee6613efaf6056e81d540312b920bfdfd1` | ok. 18:30, plan kroku 7 po 2 pilotach bodźca (pilot = tylko obraz; ziarno 20961) |
| `experiments/step2_whole_arm/conflict_test.py` | `69dccfba…d592` (stan przy spisaniu planu) | program kroku 7 |
| `experiments/step2_whole_arm/lift_b_pin.py` | `2e6e0698…ef2c` | przypięta kopia `lift_b.py` (stan 18:16:34, zmiana drugiej sesji addytywna); od iteracji 2 stawów c–e importowana zamiast `lift_b.py` |

## 5.5 Krok 7 — piloty bodźca (ziarno 20961, 3 przedmioty, N, Glu −1)

| # | Co i dlaczego | Plik | Wynik |
|---|---|---|---|
| 5.5.1 | Pilot 1: bodziec = zielona kula przy zielonych przedmiotach (konwencja etapu wzroku) | `conflict_7/pilot/pilot1_*` | Enkoder nasycony przez trzymany przedmiot: g ≈ (1,00; 1,00) „on”, (0,86–0,99; 1,00) „sham” — bodziec prawie nie zmienia wejścia. **Projekt bodźca FAILED** |
| 5.5.2 | Pilot 2: przedmioty w kolorach materiałów (`--colors native`) | `conflict_7/pilot/pilot2_*` | cube_S/hard_grip: g (1,00; 0,78) vs (0,51; 0,28), DNa02 L/R 164/124 vs 12/0 Hz; long/heavy podobnie; sphere/light (żółty materiał pobudza enkoder) mała różnica — bodziec dociera do sieci. Przyjęte, offset bez zmian. Czas ~23 s/próbę przy obciążonym CPU |

## 5.6 Staw (c) elbow_flex — pętla (cel `LOOP_TARGET_c_r1.md`)

### Iteracja 1 — wejścia padsT2 + padsT1, IN reguła fl (z góry). `elbow_c/it1/`, analiza `elbow_c/it1_analysis_g±1.json`
Odciski przed podniesieniem identyczne z K: 45/45 we wszystkich seriach, oba Glu — VERIFIED. Siła maks. 0,0 N wszędzie, bezpiecznik 0.

| Glu | N lift | K | R | S1 | S2 | N placed | N vs K (CI95) | N vs R McNemar | średnie pule w fazie (Ti flex / Ti ext) |
|---|---|---|---|---|---|---|---|---|---|
| −1 | **0**/45 | 31 | 24 | 5 | 32 | 0 | −0,69 [−0,82; −0,56] | p = 1 | 0,0 / 4,0 Hz |
| +1 | **34**/45 | 34 | 26 | 36 | 0 | 0 | 0,00 [−0,09; +0,09] | **p = 0,019**, CI [+0,04; +0,31] | 2,7 / 17,7 Hz |

- Glu +1: **C1 spełnione, C2 spełnione, C3 NIE** (S1 36 ≥ N 34), C4 spełnione → cel nieosiągnięty (FAILED). Sieć prostuje łokieć
  po dotyku i unosi przedmiot ≥ 2 cm (kryterium `lift`), ale za wolno, by w 3 s dojść do wysokości transportu (36× no_lift) →
  `placed` 0 — VERIFIED (liczby). Glu −1: Ti extensor 4 Hz → ruch za wolny, 0/45 — FAILED.
- Wniosek [INFERRED]: przy Glu +1 sieć z danych realizuje odruch „dotyk → prostowanie”, który podnosi tak samo dobrze jak klasyczne
  IK i lepiej niż stałe unoszenie R, ale jedna z dwóch przetasowanych sieci robi to samo — nie ma dowodu, że liczy się układ
  połączeń z danych.

### Iteracja 2 — hipoteza: propriocepcja łokcia przez receptory FeCO T1 L (`fecoT1`: kąt → claw, prędkość → hook; [MODEL])
Uzasadnienie: jedyna dozwolona klasa zmian, która może dać zachowanie zależne od połączeń z danych (droga FeCO → MN goleni jest
specyficzna, w screenie SNpp51 → Ti flexor). Przewidywanie z góry [HYPOTHESIS]: odruch oporu (spowolni prostowanie), więc lift
raczej spadnie; może jednak różnicować N od tasowań. Zmiana dotyczy N, S1, S2; R i K bez zmian (biorę z it1, ten sam kod ramion).
Uruchomione 18:43 (`elbow_c/it2/`). Kod: `joint_net.py` od tej iteracji importuje `lift_b_pin.py` (sha `ad332dce…8b46`).

## 5.7 Staw (d) wrist_flex — pętla (cel `LOOP_TARGET_d_r1.md`)

### Iteracja 1 — wejścia padsT2 + padsT1, IN fl. `wrist_d/it1/`, analiza `wrist_d/it1_analysis_g±1.json`
| Glu | N lift | K | R | S1 | S2 | R placed | pule Ta lev / Ta dep w fazie |
|---|---|---|---|---|---|---|---|
| −1 | **0**/45 | 30 | 35 | 0 | 0 | 1 | 0,0 / 0,0 Hz |
| +1 | **0**/45 | 33 | 35 | 0 | 0 | 1 | 0,0 / 0,0 Hz |
Odciski przed podniesieniem 45/45 identyczne; siła 0 N. **FAILED** (C1–C3). Sieć z danych (i oba tasowania) nie porusza stawu 3 —
zgodnie z przewidywaniem zapisanym w celu. Odruch R podnosi nadgarstkiem (35/45 lift), ale przechyla przedmiot: placed 1/45.

### Koniec pętli (d) po iteracji 1 — brak hipotezy w dozwolonych klasach zmian (nie jest to STOP planu)
- nowe wejścia receptorowe: `receptor_screen_v1.json` / `receptor_screen_groups_v1.json` — ŻADEN typ ani klasa receptorów T1 L/T2 L
  (także wszystkie naraz, 10–40 mV, oba Glu) nie daje > 0 Hz w pulach Ta levator/depressor — VERIFIED;
- rusztowanie fazy: nie może pobudzić milczących pul;
- kalibracja (k, znaki, τ_r): przy r = 0 dowolne k daje 0; zmiana przypisania pul na pule aktywne byłaby wyborem pul pod zachowanie
  (strojenie), a nie hipotezą biologiczną — odrzucone.
Najlepsza wersja (reguła z góry: remis → wcześniejsza) = it1 dla obu Glu. Test końcowy uruchomiony 18:44.

## 5.8 Krok 6 — interfejs na żywo (wykonał agent Sonnet; sprawdzone przeze mnie)

| # | Co | Plik / komenda | Wynik |
|---|---|---|---|
| 6.1 | Nowy pokaz (demo.py bez zmian): okno MuJoCo + panel: raster WSZYSTKICH neuronów sieci sterujących (ArmNet + LegJaw), pule POS/NEG na staw z częstościami, Δcel na takt, moment szczęki, źródło komendy każdego stawu, faza, linia „dane / model / inżynieria” | `flymind/demo/demo_arm.py` (sha `4312db6a…1744`) | — |
| 6.2 | Test zgodności z eksperymentem | `.venv/bin/python -I -B flymind/demo/test_demo_arm.py` (uruchomiony przeze mnie 19:1x; ziarno 20951, cube_S/hard_grip) | **WSZYSTKIE TESTY OK** — T1: 23 pola wyniku identyczne z `joint_net.run_trial`; T2: sha całej trajektorii z przechwytywaniem impulsów = bez (`50b22ed1…`); T3: częstości z impulsów = `ArmNet.r`; T4: źródła komend ⊂ statystyki SafetyLayer; T5: ziarno testowe odrzucane — **VERIFIED** |
| 6.3 | Nagranie i zrzuty (bez okna) | `--media flymind/demo/media_arm_20261113/` (MP4 1600×900, 447 klatek; 3 PNG) | Zrzut „lift” obejrzany przeze mnie: panel i scena poprawne — VERIFIED |
| 6.4 | Liczba neuronów na rastrze | z sieci, nie wpisana | **4100 = ArmNet 2593 + LegJaw 1507** (nie 2916: 2916 to sieć T2 L + T1 L + wzrok z `tick_cost`; tu sterują dwie sieci: ramię i osobna szczęka, obwód T2 L występuje w obu). Wzroku w tym pokazie nie ma |
| 6.5 | Wydajność (agent, obciążenie ~200, więc pesymistycznie) | `--bench` | 53 takty/s bez panelu (0,53× czasu rzeczywistego), 47 takty/s z panelem 20 kl./s (0,47×) — REPORTED (nie powtórzone na wolnej maszynie) |
| 6.6 | Okno interaktywne | `.venv/bin/mjpython flymind/demo/demo_arm.py --seed 20951` | Uruchomione przez agenta do czystego wyjścia; **samego okna nikt nie widział — NOT VERIFIED** |

## 5.9 Staw (e) wrist_roll — pętla (cel `LOOP_TARGET_e_r1.md`; słaba analogia, znak arbitralny)

### Iteracja 1 — padsT2 + padsT1, IN fl. `roll_e/it1/`, analiza `roll_e/it1_analysis_g±1.json` (wynik główny `placed`, C2 nie dotyczy)
| Glu | N placed | K | R (trzymanie) | S1 | S2 | maks. |q₄ − q₄(chwyt)| N / S1 / S2 | pule Tr flex / Tr ext w fazie (N) |
|---|---|---|---|---|---|---|---|
| −1 | 29/45 | 29 | 29 | 28 | 28 | 0,000 / 0,231 / 0,265 rad | 0,0 / 0,0 Hz |
| +1 | 29/45 | 29 | 29 | 28 | 29 | 0,008 / 0,641 / 0,804 rad | 0,20 / 0,54 Hz |
Odciski przed podniesieniem identyczne (45/45), siła 0 N, bezpiecznik 0. C1 spełnione **trywialnie** (sieć z danych praktycznie
nie rusza stawu: |Δq₄| ≤ 0,008 rad, czyli robi to samo co R = trzymanie), C3 NIE (tasowania obracają nadgarstek do 0,8 rad i nie
psują odkładania: 28–29/45). **FAILED** jako dowód sterowania; zgodnie z przewidywaniem w celu. Komendy stawu 4 pochodzą formalnie
z sieci (`snn:legT1L`: 8 734 / 8 955 taktów), ale ich wartość ≈ 0 — nie należy tego przedstawiać jako „mucha obraca nadgarstek”.

### Koniec pętli (e) po iteracji 1 — brak hipotezy w dozwolonych klasach
Screen receptorów: żaden bodziec receptorowy T1 L/T2 L nie daje pulom krętarza więcej niż 4 Hz (wszystkie receptory T1 L naraz,
40 mV, Glu +1) — VERIFIED; przy k = 0,005 to ≤ 0,02 rad/s. Zmiana k/pul = strojenie pod zachowanie — odrzucone. Najlepsza wersja = it1.

### (c) Iteracja 2 — wynik (`elbow_c/it2/`, R i K dowiązane z it1 — ten sam kod ramion, `*_linked.json`; analiza `elbow_c/it2_analysis_g±1.json`)
| Glu | N lift | K | R | S1 | S2 | N placed | kryteria |
|---|---|---|---|---|---|---|---|
| −1 | 0/45 | 31 | 24 | 2 | 33 | 0 | C1–C3 nie, C4 tak — FAILED |
| +1 | 34/45 | 34 | 26 | 38 | 0 | 0 | C1 tak, C2 tak (p = 0,019), **C3 nie** (S1 38), C4 tak — FAILED |
FeCO prawie nie zmienia sieci z danych (Ti ext 17,7 Hz jak w it1; wynik N identyczny co do liczby). Przewidywanie „odruch oporu
spowolni” — nie potwierdzone (brak efektu) [VERIFIED liczby].

### Koniec pętli (c) po iteracji 2 (19:27; ~1 h 10 min pętli) — uzasadnienie
Wiążącym warunkiem jest C3 (sieć z danych lepsza od tasowań): przy Glu +1 jedno tasowanie podnosi tyle samo lub więcej (36, 38).
Pozostałe dozwolone zmiany (dłuższy limit fazy, większe k — nowy plik kalibracji) przyspieszają tak samo N i tasowania, więc nie
testują hipotezy o roli połączeń z danych; byłyby strojeniem pod wynik `placed`. Najlepsza wersja (reguła: najwyższe lift(N),
remis → wcześniejsza) = **it1** dla obu Glu. Test końcowy `--seed 20401 --poses 3`, S1–S5 20 410 001–005, uruchomiony 19:27.

## 5.10 Staw (d) i (c) — testy końcowe uruchomione
(d) 18:44: `wrist_d/test/` (`--seed 20601 --poses 3`, N/S1–S5/R/K × Glu ±1 + K0). (c) 19:27: `elbow_c/test/` (`--seed 20401`).

## 5.11 Krok 5 — całe ramię, iteracja 0 (`whole_arm_5/it0/`, ziarno 20951, 3 przedmioty; cel `LOOP_TARGET_arm_r1.md`)
Konfiguracja: jedna sieć (2593 neurony: T2 L + T1 L + MN „fl” + 104 IN reguły fl), wejścia padsT2 + padsT1, stawy 1–3 w fazie
podniesienia + staw 4 od zaciśnięcia do zwolnienia.
| # | Co | Wynik |
|---|---|---|
| 0.1 | Odciski trajektorii do podniesienia: N, S1, R, K | identyczne 3/3 w każdym ramieniu, oba Glu — VERIFIED |
| 0.2 | Siła ramię↔blat | 0,0 N we wszystkich ramionach |
| 0.3 | Zachowanie (bez wniosków, n = 3) | N Glu −1: 0/3 lift (dz ≈ 5 mm); N Glu +1: lift 2/3, placed 0 (dz 19–27 mm w 3 s); R: 2/3 i 3/3 placed; S1 Glu −1 3/3 placed, Glu +1 0/3 (bezpiecznik 53 takty) |
| 0.4 | Błąd proceduralny | Pierwsze uruchomienie S1 użyło ziarna tasowania 20 910 001 z puli TESTOWEJ kroku 5; przerwane po kilku s przed zapisem (logi `whole_arm_5/it0_killed_testshuffleseed/`), powtórzone z 20 952 001 (rezerwa, wpisane w SEED_REGISTRY). Sieć S1 testu nie została użyta do żadnej decyzji |
| 0.5 | Czas | 150 s (K, R) – 510 s (S1) na 3 próby przy obciążeniu maszyny ~250 (dwie sesje równolegle) |
Test kroku 5 czeka na najlepszą wersję stawu (b) od drugiej sesji (reguła §2 celu: wejścia = suma wejść najlepszych wersji).

## 5.12 Sprawdzenie dt 0,1 ms — zasada (spisana 20:37, przed pierwszym przebiegiem dt 0,1 dla c–e)
Tylko N, oba Glu, najlepsza wersja stawu, sieć ramienia przy `ALIFParams(dt=0.1)` (100 kroków/takt; szczęka LegJaw bez zmian,
dt 1 ms, bo to moduł wspólny). Ziarna: **te same sceny testowe, ale tylko pierwsza poza każdej sceny (`--poses 1`, 45 prób)** —
ograniczenie czasu (przy dt 1 ms seria N (d) trwała ~1 h 50 min przy obciążeniu maszyny 250–600; dt 0,1 ms ≈ 10× droższa sieć).
Porównanie sparowane z tymi samymi 45 próbami serii dt 1 ms (McNemar dwustronny, różnica liczby lift/placed). Nic nie jest potem
zmieniane — to tylko sprawdzenie wrażliwości wyniku na krok całkowania.

## 5.13 (d) wrist_flex — TEST KOŃCOWY (`wrist_d/test/`, `--seed 20601 --poses 3`, 135 prób; analiza `wrist_d/test_analysis_g±1.json`)
| Glu | N lift [Wilson 95 %] | K | R | K0 | S1–S5 | N placed | K / R / K0 placed | siła maks. | bezpiecznik N |
|---|---|---|---|---|---|---|---|---|---|
| −1 | **0/135** [0; 2,8 %] | 95 | 98 | 98 | 0,0,0,0,0 | 0 | 87 / 6 / 96 | 0,0 N (wszystkie) | 0 / 76 276 taktów |
| +1 | **0/135** [0; 2,8 %] | 101 | 106 | 98 | 0,0,0,0,0 | 0 | 92 / 7 / 96 | 0,0 N | 0 / 76 713 |
N vs K: −0,70 [−0,78; −0,63] (Glu −1), −0,75 [−0,82; −0,67] (Glu +1); McNemar N > R p = 1; N vs Sᵢ różnica 0 (p = 1, Holm: żadne).
**Wynik (d): FAILED — C1, C2, C3 niespełnione; C4 spełnione.** Sieć z danych (i każde tasowanie) nie porusza nadgarstka; przyczyna:
pule Ta levator/depressor nie dostają żadnego pobudzenia z receptorów (5.2.3). Udział komend `snn:legT1L` 8,8 % wszystkich
taktów stawów (staw 3 w fazie podniesienia), ale ich wartość = 0. Odruch R podnosi (98–106/135), lecz przechyla przedmiot (placed 6–7).

## 5.14 (c) elbow_flex — TEST KOŃCOWY (`elbow_c/test/`, `--seed 20401 --poses 3`, 135 prób; wersja it1; analiza `elbow_c/test_analysis_g±1.json`)
| Glu | N lift [Wilson 95 %] | K | R | K0 | S1 | S2 | S3 | S4 | S5 | N placed | K / R / K0 placed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| −1 | **0/135** [0; 2,8 %] | 96 | 75 | 99 | 0 | 0 | 76 | 35 | 114 | 0 | 88 / 64 / 96 |
| +1 | **107/135** [71,7; 85,2 %] | 100 | 87 | 99 | 111 | 115 | 113 | 105 | 115 | **0** | 90 / 74 / 96 |
Glu +1: N − K = +0,05 [−0,01; +0,12] → **C1 spełnione** (niegorszość; punktowo lepiej, McNemar N > K p = 0,095 — nieistotne);
N vs R: +0,15 [+0,07; +0,23], McNemar p = 0,0008 → **C2 spełnione**; N vs S1–S5: −0,03 / −0,06 / −0,04 / +0,01 / −0,06, McNemar
p 0,41–0,999, Holm: żadne → **C3 NIE**; siła 0 N, bezpiecznik 0/40 354 taktów → C4 tak. **Cel (c) przy Glu +1: NIEOSIĄGNIĘTY
(FAILED na C3).** Glu −1: FAILED (C1–C3). Wszystkie przypadki „lift” sieci N to uniesienie ≥ 2 cm bez osiągnięcia wysokości
transportu w 3 s (110× no_lift, 28× snn_released) → `placed` 0/135; tasowania prostują łokieć szybciej i odkładają 89–98/135.
Wniosek [INFERRED]: łokieć z sieci muchy (Glu +1) podnosi przedmiot równie często jak klasyczne IK i częściej niż stały odruch, ale
to samo (szybciej) robią sieci z przetasowanymi połączeniami — **wynik nie świadczy, że liczą się połączenia z danych**.
Udział komend sieci (`snn:legT1L`): 7,2 % taktów wszystkich stawów (Glu +1), 8,7 % (Glu −1). Siła na stół: 0,0 N we wszystkich ramionach.
Uwaga: wstrzymałem (SIGSTOP) 8 serii testu (e) na prośbę drugiej sesji (obciążenie 300–390); wpływa tylko na czas zegarowy (T_wall).

## 5.15 (e) wrist_roll — TEST KOŃCOWY (`roll_e/test/`, `--seed 20801 --poses 3`; wersja it1; analiza `roll_e/test_analysis_full_g±1.json`)
Uwaga proceduralna: pierwszy zapis analizy powstał, gdy gotowych było 13 z 17 serii — zachowany jako
`test_analysis_PARTIAL_13of17files_g±1.json` (NIE używać); pełna analiza w `test_analysis_full_*`.
| Glu | N placed [Wilson 95 %] | K | R (trzymanie) | K0 | S1–S5 | N lift | maks. obrót N / S1–S5 [rad] |
|---|---|---|---|---|---|---|---|
| −1 | **83/135** [53,1; 69,3 %] | 85 | 83 | 98 | 83, 83, 82, 82, 83 | 93 | 0,000 / 0,06–0,20 |
| +1 | **91/135** [59,1; 74,7 %] | 92 | 91 | 98 | 87, 86, 86, 86, 86 | 102 | 0,008 / 0,30–1,14 |
N − K: −0,015 [−0,037; 0,000] (Glu −1), −0,007 [−0,022; 0,000] (Glu +1) → **C1 spełnione**; C2 nie dotyczy; N vs S (Glu +1): +0,03–0,04,
McNemar p 0,06–0,13, Holm: żadne → **C3 NIE**; siła 0 N, bezpiecznik 0 → C4 tak. **FAILED (C3).** N jest identyczna z R (trzymanie)
w każdej próbie (0 różnic) — sieć z danych praktycznie nie obraca nadgarstka; tasowania obracają go do 1,14 rad i tracą 4–6
odłożeń (różnica nieistotna). Udział komend `snn:legT1L`: 5,1–5,6 % taktów stawów (wartości ≈ 0).

## 5.16 Zmiana środowiska uruchomień (23:15): 1 wątek bibliotek numerycznych
Obciążenie 500–760 przy 10 rdzeniach: każdy proces Pythona miał 20–23 wątki (`ps -M`). Sprawdzenie: `OMP_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1` — próba całego ramienia (ziarno 20951, cube_S/hard_grip, N Glu +1)
identyczna z wersją wielowątkową w 8 polach (prelift_sha, truth, lift_log, T_sim, safety_stats, roll_dev, częstości, fmax) —
VERIFIED (scratchpad `thr1/`). Od 23:15 nowe serie tej sesji startują z tymi zmiennymi; przekazane drugiej sesji.

## 5.17 Krok 7 — test N zakończony (01:33, 14 XI); szczegóły w osobnym logu `step7_conflict_log_2026-11-13.md`
Kontrola manipulacji spełniona (DNa02 L +134–138 Hz), moment szczęki bez efektu wg reguły z góry w obu Glu. Tasowania S czekają.
Logi kroków 6–7 jako osobne pliki: `step6_interface_log_2026-11-13.md` (kopia §5.8) i `step7_conflict_log_2026-11-13.md`.

## 5.18 Krok 5 — konfiguracja testu całego ramienia (spisana 14 XI ok. 01:55, PRZED testem; reguła `LOOP_TARGET_arm_r1.md` §2)
Najlepsze wersje: (b) it3 = `lift_b --net it2 --lift-max 30` (wybór drugiej sesji, Część 4); (c) it1; (d) it1; (e) it1
(c, d, e: `--inputs padsT2,padsT1 --in-rule fl`, limit fazy 3 s).
- Sieć: `--net it2` (b) = `--in-rule fl` (c–e) — **ta sama sieć**: W sha256 identyczne w `lift_b/it3/it3_N_g±1.json` i
  `elbow_c/test/c_test_N_g±1.json` (Glu +1 `2dfbb84e…`, Glu −1 `a85285c6…`, N = 2593) — VERIFIED.
- Wejścia (suma): padsT2 (b–e) ∪ padsT1 (c–e) = `padsT2,padsT1`.
- **Sprzeczność:** limit fazy podniesienia 30 s (b) vs 3 s (c, d). Reguła §2: wygrywa staw z wyższym wynikiem treningowym
  względem K. Glu +1: (c) 34 − 34 = 0 > (b) 11 − 33 = −22 > (d) 0 − 33 → (c), 3 s. Glu −1: (d) 0 − 30 = −30 > (c) 0 − 31 > (b)
  0 − 32 → (d), 3 s. **Limit 3 s dla obu Glu.** Skutek dla (b): sieć unosiła ~1,3 mm/s, więc przy 3 s sama nie podniesie
  przedmiotu — staw (b) wchodzi w najlepszej wersji sieci, ale z limitem stawu (c); oznaczone jako wynik negatywny (b).
- Komenda: `launch_test.sh` (scratchpad) z `--joints 1,2,3 --roll --inputs padsT2,padsT1 --in-rule fl`, `--seed 20901 --poses 3`,
  tasowania 20 910 001–005, ramiona N, S1–S5, R (wszystkie odruchy), K, K0; `STEP2_FINAL_TEST=1`; 1 wątek bibliotek.
- Analiza: `analyze_joint.py … --outcome placed` (główny) i `--outcome lift`.
- **Uruchomienie (01:38, 14 XI)** po zgodzie drugiej sesji (wiadomość 01:4x: „uruchom … z nice 10”; tasowania konfliktu
  zostają wstrzymane do końca testu (b), który według niej skończy się ok. 6:00–8:00). 17 procesów (`whole_arm_5/test/`), priorytet
  nice 15 (powłoka już miała 5), 1 wątek bibliotek; `joint_net.py` sha `ad332dce…8b46`. Test raz.

## 5.19 Krok 5 — całe ramię — TEST KOŃCOWY (`whole_arm_5/test/`, `--seed 20901 --poses 3`, 135 prób; koniec 03:55, 14 XI)
Analizy: `whole_arm_5/test_analysis_placed_g±1.json` (główny; sha −1 `b3169895…`, +1 `7d476558…`) i `…_lift_g±1.json`
(−1 `727b1393…`, +1 `67d313d6…`). Czas serii N: 2,1–2,2 h zegarowo przy nice 15.

| Glu | wynik | **N** [Wilson 95 %] | K | R (wszystkie odruchy) | K0 | S1, S2, S3, S4, S5 |
|---|---|---|---|---|---|---|
| −1 | **placed** | **0/135** [0; 2,8 %] | 81 | 53 | 96 | 96, 89, 0, 0, 33 |
| −1 | lift | 0/135 | 93 | 62 | 99 | 110, 107, 0, 102, 109 |
| +1 | **placed** | **0/135** [0; 2,8 %] | 89 | 55 | 96 | 75, 89, 0, 91, 71 |
| +1 | lift | 83/135 [53,1; 69,3 %] | 101 | 65 | 99 | 112, 104, 108, 105, 84 |

- C1 (niegorszość wobec K): NIE (placed: N − K −0,60 / −0,66). C2 (N > R): NIE na placed; na `lift` Glu +1 tak (+0,13
  [0,04; 0,23], McNemar p = 0,004). C3 (N > S1–S5, Holm): NIE — kilka tasowań odkłada 75–96/135, sieć z danych 0. C4: siła
  0,0 N we wszystkich ramionach i próbach, bezpiecznik w N 0 taktów (S3 Glu −1: 13 769 / 75 263 = 18 %, S1 Glu +1: 1,4 %).
  **Wynik kroku 5: FAILED (C1–C3), C4 spełnione.** VERIFIED.
- Dlaczego 0 odłożeń (VERIFIED z `lift_log`): w fazie podniesienia N unosi przedmiot maksymalnie o 29,7 mm (Glu +1, mediana
  23,1 mm) albo 6,3 mm (Glu −1) w 3 s, a do transportu potrzeba 55 mm → w każdej próbie „no_lift” (113 / 120) albo utrata
  chwytu (26 / 19). Ten sam wzór co w teście (c) (lift 107, placed 0). Częstości pul (próba 1, Glu +1, POS/NEG Hz): staw 1
  2,2/5,4; staw 2 2,5/18,5; staw 3 0/0; staw 4 0,25/0,54 — unosi głównie łokieć (c); bark (b) i nadgarstek (d) prawie nic.
- Udział komend sieci we wszystkich kanałach: N 19–22 % taktów (najwyższy w całym kroku 2). Obrót nadgarstka N ≤ 0,008 rad.
- Interpretacja [INFERRED]: tasowania z tą samą liczbą i wagą połączeń dają silniejszy, mniej zrównoważony napęd pul i często
  podnoszą wysoko; sieć z danych ma pule wymachu i Ta prawie ciche (zgodnie z przesiewem receptorów, §5.x), więc sama nie
  dociąga ramienia do wysokości transportu w 3 s. Limit 3 s wynikał z reguły §5.18 (spisanej przed testem).

## 5.20 Sprawdzenie dt 0,1 ms (zasada §5.12) — wyniki d, e, c Glu +1
Program porównania: `experiments/step2_whole_arm/dt01_cmp.py` (nowy; para = ta sama scena testowa, poza 0, dt 0,1 vs dt 1 ms;
McNemar dwustronny). Ten sam wynik co w teście (d, c: `lift`; e: `placed`). Odciski trajektorii przed fazą stawu identyczne
w 45/45 parach we wszystkich porównaniach; siła 0 N.

| Staw | Glu | dt 0,1 ms | dt 1 ms (te same 45 scen) | tylko dt 0,1 / tylko dt 1 | p |
|---|---|---|---|---|---|
| (d) lift | −1 | 0/45 | 0/45 | 0 / 0 | 1,0 |
| (d) lift | +1 | 0/45 | 0/45 | 0 / 0 | 1,0 |
| (e) placed | −1 | 28/45 | 28/45 | 0 / 0 | 1,0 |
| (e) placed | +1 | 32/45 | 32/45 | 0 / 0 | 1,0 |
| (c) lift | +1 | 32/45 | 35/45 | 0 / 3 | 0,25 |
| (c) lift | −1 | 0/45 | 0/45 | 0 / 0 | 1,0 |

Wniosek: krok całkowania nie zmienia wniosków dla (d) i (e); dla (c) Glu +1 przy dt 0,1 ms o 3 podniesienia mniej (różnica
nieistotna, ale w jednym kierunku) — VERIFIED liczby, „wnioski bez zmian” INFERRED. Czas: 3,6–4,9 h zegarowo na serię 45 prób.

## 5.21 Wyniki (b) od drugiej sesji (04:23) i wznowienie tasowań konfliktu
- Wiadomość drugiej sesji: test (b) zakończony; raport `REPORT_b_2026-11-14.md`. Liczby sprawdzone przeze mnie w
  `lift_b/test/analysis_g±1.json` i `lift_b/test_dt01/compare_g±1.json` — zgodne (VERIFIED): N lift 0 / 27 na 135, placed 0 / 0,
  C1–C3 nie, C4 tak; dt 0,1 ms Glu +1 23/45 vs 7/45 (16:0, p = 3·10⁻⁵).
- 04:24: wznowione (SIGCONT) 8 serii S1–S2 konfliktu; 04:25 uruchomione S3–S5 (12 serii, `launch_conflict.sh S3|S4|S5 1`,
  1 wątek). Ziarna z rejestru (20 980 003–005).
- Szkic raportu końcowego: `flymind/reports/step2_final_report_20261114.md` (czeka na tasowania konfliktu).
- 05:12: tasowania konfliktu gotowe; wynik w `step7_conflict_log_2026-11-13.md` §7.5–7.6 (brak efektu, brak swoistości).
