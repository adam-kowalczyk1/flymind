# Krok 3 — większa sieć z danych i sprawiedliwsze kontrole — log kroków (15 XI 2026)

Cel: dwie sprawy z przeglądu stanu — (1) „mucha nie steruje całym ramieniem”, (2) „brak dowodu, że liczy się schemat połączeń”.
Zasady: tylko symulacja; żaden moduł wspólny ani plik kroku 2 nie został zmieniony (nowy kod w `experiments/step3_wiring/`
importuje krok 2 i podmienia klasę sieci tylko w pamięci); cele i analiza zapisane przed testami (hashe i czas w
`PRE_TEST_HASHES.txt`); nowe ziarna 21 xxx xxx wpisane do `experiments/step3_wiring/SEED_REGISTRY.md` przed użyciem; nic nie
strojone (wagi, progi, k, limit 3 s — jak w kroku 2); bez robota fizycznego; bez commitów i push; bez kodu Artificial Brains.
Oznaczenia: VERIFIED / PARTIALLY VERIFIED / REPORTED / INFERRED / HYPOTHESIS / NOT VERIFIED / FAILED / NOT IMPLEMENTED.

| # | Co i dlaczego | Komenda / plik | Wynik |
|---|---|---|---|
| 1 | Rozpoznanie na wynikach kroku 2 (tylko odczyt): czym tasowania różnią się od danych | skrypt w linii na `results/step2_whole_arm_20261113/*/test/*.json` (`mean_rates_active`, `guard`, `placed`) | Tasowania pobudzają pule antagonistyczne naraz (bark 42–99 Hz w obu kierunkach) i są bimodalne (0 albo ~90 odłożonych); dane: czysty, słaby wzór (prostownik goleni). Tasowanie swobodne miesza warstwy (receptory dostają bezpośrednie wyjścia na MN) — kontrola niesprawiedliwa |
| 2 | Sprawa 1: czy cisza barku to za mały wycinek sieci (errata E6) | `experiments/step3_wiring/nets.py`, `explore_rules.py` → `explore_rules_v1.json` (bez robota, szum 0) | Reguła `base` = sieć kroku 2 (W sha identyczny — asercja). Reguła **`pre`** (dodane wszystkie `vnc_intrinsic` z ≥ 5 synapsami do MN „fl” L; 3148 neuronów): Glu +1 pula wymachu 47,6 Hz, podpór 21,5; Glu −1 bark 0, prostownik goleni 17,8. `pre2` (4216) i `full2` (8364): ten sam obraz. Pule stępu 0 we wszystkich. VERIFIED (eksploracja) |
| 3 | Skąd pule dostają wejście (tylko dane) | `who_drives.py` → `who_drives_v1.json` | Sieć `pre` obejmuje 74–82 % synaps wejściowych pul (krok 2: 36–55 %); 74–81 % od `vnc_intrinsic`, 7–12 % od neuronów zstępujących, 3–8 % wstępujących. VERIFIED |
| 4 | Czy nadgarstek da się pobudzić naturalnym czuciem | `explore_receptors.py` → `explore_receptors_v1.json` (każdy typ receptora osobno, 40 mV, 0,5 s) | Żaden typ receptora T1 L / T2 L nie daje > 1 Hz w pulach stępu (oba Glu). Nadgarstek pozostaje bez sygnału. VERIFIED (model) |
| 5 | Tasowania na sieci `pre` bez robota (ziarna eksploracyjne 21 100 001–010) | `explore_shuffles.py` → `explore_shuffles_v1.json` | Tasowania swobodne i zachowujące warstwy pobudzają pule mocniej niż dane (Glu +1 wymach 60–177 Hz wobec 47,6) i więcej pul naraz. Oczekiwanie zapisane w pliku celu: C3 raczej niespełnione |
| 6 | Uruchamianie w pętli | `run3.py` (podmiana `joint_net.ArmNet` w pamięci; `--rule`, `--kind free\|layer`), `launch3.sh` | — |
| 7 | Iteracja treningowa (ziarno 21101, 45 scen, konfiguracja całego ramienia kroku 2, limit 3 s) | `results/step3_20261115/train/it0_*.json` | N Glu +1 **29/45**, K 29/45, R 18/45; N Glu −1 0/45 (unosi 35). Siła 0 N, bezpiecznik 0. Bark 47,7 / 17,8 Hz, dojście do 55 mm mediana 1,88 s |
| 8 | Próba dymna tasowań w pętli (3 sceny treningowe) + sprawdzenie blokady ziaren testowych | `train/smoke_S1_g1.json`, `smoke_L1_g1.json`, `smoke_guard.log` | oba rodzaje tasowań działają; blokada: „ziarna testowe kroku 3 tylko w teście końcowym”. Obrót nadgarstka: N ok. 0,56 rad, S1 0,85–0,91, L1 1,54–1,66 → źródło hipotezy H-spokój. (Pierwsza komenda dymna nie ruszyła: powłoka zsh nie rozdzieliła opcji — nic nie policzono) |
| 9 | Cel i analiza PRZED testem | `LOOP_TARGET_arm3_r1.md`, `analyze3.py`, `quiet_test.py`; `PRE_TEST_HASHES.txt` (15:19:53) | kryteria C1, C2, C3S, C3L, C4; hipotezy wtórne H-spokój (w pętli) i H-cisza (bez robota) |
| 10 | Test końcowy — pierwsze uruchomienie | `test3.sh` (wersja z `xargs -I`) | **nie uruchomiło żadnej serii** („command line cannot be assembled, too long”), katalog `test/` pusty → ziarna testowe nieużyte. Poprawiony sposób uruchamiania (`one3.sh`, `test3_jobs.txt`) |
| 11 | **Test końcowy** (`--seed 21201`, 135 prób × 27 serii, raz) | `test3.sh` → `results/step3_20261115/test/arm3_test_*.json` | 27/27 plików. W trakcie testu na komputerze uruchomiono grę (Minecraft); system zwolnił procesy tła ok. 10× na ok. 40 min — wpływa tylko na czas zegarowy (jeden wątek, wynik deterministyczny) |
| 12 | Analiza (hash `analyze3.py` = hash sprzed testu `547d0602…`) | `analyze3.py test arm3_test` → `test/analysis_arm3_test.json` | tabela niżej |
| 13 | H-cisza (bez robota, 20 + 20 nowych tasowań na Glu) | `quiet_test.py` → `quiet/*.json` | **FAILED i odwrócona:** średnia częstość MN w danych 42,4 Hz (Glu +1) / 8,5 Hz (Glu −1) jest WYŻSZA niż w każdym policzonym tasowaniu (swobodne Glu +1: 16,7–29,1; warstwowe: 19,9–41,7; warstwowe Glu −1: 3,1–5,9). Sieć z danych nie jest „cichsza” |
| 14 | Sprawa 2, inny kierunek: wybiórczość noga → noga (eksploracja, ziarna 21 100 001–010) | `explore_specificity.py` → `explore_specificity_g{1,-1}_v1.json` | dane W = 0,868 (Glu +1), 0,913 (Glu −1); 10 tasowań: −0,31…+0,24. Dotyk T2 → MN T2 81,5 Hz, MN T1 3,5 Hz (Glu +1) |
| 15 | Czy da się to przenieść na „dotyk nie rusza ramieniem” (eksploracja) | `explore_leak.py` → `explore_leak_g{1,-1}_v1.json` | **Nie:** w danych (Glu +1) dotyk samej nogi T2 pobudza pulę wymachu nogi T1 (39 Hz → 0,17 rad/s w barku) — prawdziwe połączenie między nogami. Test „przesłuchu” byłby źle postawiony; zaniechany przed zapisaniem celu |
| 16 | Cel potwierdzenia wybiórczości PRZED uruchomieniem | `LOOP_TARGET_spec_r1.md`, `spec_test.py`; dopisane do `PRE_TEST_HASHES.txt` (18:06:07) | trzy rodziny po 20 nowych tasowań: F (swobodne), L (warstwy), G (warstwy + przynależność receptorów i MN do nóg) |
| 17 | Próba dymna rodziny G (1 tasowanie, ziarno eksploracyjne 21 100 010) | skrypt w linii | grupy: I 1837, MN T1 68, MN T2 58, receptory T1 508, T2 677; W = 0,82 (nie liczy się do testu) |

## Wynik testu końcowego (krok 12) — `placed` na 135 prób

| Glu | N (dane) | K | R | K0 | S1–S5 (swobodne) | L1–L5 (warstwy) |
|---|---|---|---|---|---|---|
| +1 | **88** [56,8; 72,7 %] | 90 | 55 | 100 | 92, 85, 92, 91, 92 | 91, 82, 73, 75, 85 |
| −1 | **0** [0; 2,8 %] (unosi 102) | 85 | 53 | 100 | 0, 94, 95, 0, 90 | 89, 0, 94, 94, 91 |

| Kryterium | Glu +1 | Glu −1 |
|---|---|---|
| C1 niegorszość wobec K | **tak** (−1,5 pp, 95 % [−8,1; +5,2]) | nie (−63 pp) |
| C2 lepsza od odruchu | **tak** (36 : 3, p = 3,6·10⁻⁸) | nie (0 : 53) |
| C3S lepsza od każdego tasowania swobodnego | nie (od żadnego) | nie (gorsza od 3) |
| C3L lepsza od każdego tasowania z warstwami | nie (tylko od L3: 22 : 7, p_Holm 0,041) | nie (gorsza od 4) |
| C4 siła ≤ 5 N, bezpiecznik ≤ 10 % | **tak** (0 N, 0 %) | tak (0 N, 0 %) |
| H-spokój (obrót nadgarstka mniejszy niż w każdym tasowaniu) | nie — 9 z 10 (wyjątek L5: mediana 0,47 wobec 0,56 rad) | nie — 9 z 10 (wyjątek L2) |

Werdykt wg reguł zapisanych przed testem: **sprawa 1 rozwiązana dla Glu +1** (C1, C2, C4), nierozwiązana dla Glu −1;
**sprawa 2 na tym zadaniu nierozwiązana** (C3S, C3L niespełnione). H-spokój i H-cisza: niepotwierdzone.
Zastrzeżenia: pracują bark i łokieć — nadgarstek bez sygnału, obrót nadgarstka jest skutkiem ubocznym (0,56 rad), nie
sterowaniem; przypisanie pul do stawów jak w kroku 2 ([BIOLOGIA] bark, łokieć; [ANALOGIA] obrót); znak Glu nieznany
z danych; wszystko w MuJoCo; dojazd, harmonogram i strażnik odstępu klasyczne.

## Ciąg dalszy (15 XI, po teście r1)

| # | Co i dlaczego | Komenda / plik | Wynik |
|---|---|---|---|
| 18 | **Potwierdzenie wybiórczości noga → noga** (bez robota; cel `LOOP_TARGET_spec_r1.md`; 3 rodziny × 20 nowych tasowań × 2 Glu) | `spec_test.py` (26 zadań, `spec_jobs.txt`) → `spec/*.json`, `spec/analysis_spec.json` | Dane: W = 0,868 (Glu +1; dotyk T2 → MN T2 81,5 Hz, MN T1 3,5 Hz) i 0,913 (Glu −1). **H-W(F) potwierdzona** dla obu Glu (tasowania swobodne: −0,40…+0,12 i −0,57…+0,12; 0/20 ≥ dane). **H-W(L) potwierdzona** dla obu Glu (warstwowe: −0,25…−0,004 i −0,57…+0,07; 0/20). **H-W(G)**: Glu +1 potwierdzona (0,02…0,815; 0/20, o włos), Glu −1 **nie** (0,65…1,00; 16/20 ≥ dane). Wniosek wg reguły zapisanej z góry: schemat połączeń ma znaczenie dla tego, które mięśnie odpowiadają na dotyk — VERIFIED (model); poziom: głównie „która noga z którą” |
| 19 | H-cisza — komplet (20 + 20 tasowań × 2 Glu) | `quiet/*.json` | FAILED, odwrócona: dane 42,4 Hz (Glu +1) i 8,5 Hz (Glu −1) > każde z 80 tasowań (16,7–41,7 Hz; 3,1–7,6 Hz) |
| 20 | Sprawa 1, Glu −1: czy problemem jest tylko limit 3 s (trening, ziarno 21101, limit 10 s) | `train/it1_lm10_*.json` | N Glu +1 29/45, N Glu −1 30/45, K 29/45, R 19/45; czas dojścia 1,95 s i 5,5 s |
| 21 | Cel r2 PRZED testem (limit 10 s; nowe sceny; bez tasowań) | `LOOP_TARGET_arm3_r2.md`; `PRE_TEST_HASHES.txt` | — |
| 22 | **Test r2** (`--seed 21301`, 135 prób × 7 serii, raz) | `one3r2.sh`, `test3r2_jobs.txt` → `test_r2/*.json`; `analyze3.py` → `test_r2/analysis_arm3r2_test.json` | tabela niżej |
| 23 | Jak sieć z danych reaguje na dotyk każdej nogi osobno (eksploracja bez robota) | skrypt w linii (sieć `pre`, pule T1 i pule szczęki T2) | Dotyk T1 („dłoń”): szczęka 0 Hz → moment 0; Glu +1 bark 28,5/11,0 Hz i prostownik goleni 30 Hz (cofnięcie w górę), Glu −1 słabo (6,5 Hz). Dotyk T2 („palce”): moment szczęki +0,90 (Glu +1) / +0,62 N·m (Glu −1); przy 10 mV +0,30 / +0,095 |
| 24 | Krok 4 — próba „dwa czucia, dwa odruchy” na robocie: kod i uruchamianie | `reflex.py` (podklasa `joint_net.ArmGrip`; jedna sieć steruje szczęką i stawami 1–3), `one_reflex.sh` | Pierwsza wersja: dłoń nie dotknęła walca 50 mm (dłoń jest 51 mm nad końcem padów) → próba W na walcu 60 mm (`cyl_thin`, jedyny dość wysoki kształt katalogu). Po zmianie: N Glu +1 W 4/4 (nacisk 1,1–2,5 N → cofnięcie 3 mm, moment szczęki 0) |
| 25 | Trening kroku 4 (ziarno 21401, 3 pozy; tasowania eksploracyjne) | `reflex_train/it0_*.json` | 13 ważnych par. OBA: N Glu +1 8 (W 13, C 8); N Glu −1 2 (W 2, C 11). Glu +1: F 0, 0; L 0, 3; G 2, 8. Glu −1: F 0, 0; L 4, 0; G 6 |
| 26 | Cel kroku 4 PRZED testem | `LOOP_TARGET_reflex_r1.md`, `analyze_reflex.py`; `PRE_TEST_HASHES.txt` | kryteria H-R(F), H-R(L), H-R(G); oczekiwania zapisane (Glu −1 raczej nie) |

## Wynik testu r2 (krok 22) — limit fazy podnoszenia 10 s, `placed` na 135

| Glu | N (dane) | K | R | K0 | C1 niegorszość | C2 lepsza od odruchu | C4 | Czas dojścia N |
|---|---|---|---|---|---|---|---|---|
| +1 | **94** [61,4; 76,8 %] | 93 | 59 | 101 | tak (+0,7 pp [−6,7; +8,1]) | tak (41 : 6, p = 1,8·10⁻⁷) | tak (0 N, 0 %) | mediana 1,94 s |
| −1 | **86** [55,3; 71,3 %] | 86 | 58 | 101 | tak (0,0 pp [−7,4; +7,4]) | tak (34 : 6, p = 8,4·10⁻⁶) | tak (0 N, 0 %) | mediana 5,52 s |

Werdykt wg `LOOP_TARGET_arm3_r2.md`: **sprawa 1 rozwiązana niezależnie od znaku glutaminianu** (C1, C2, C4 dla obu Glu), przy
limicie 10 s. Obok obowiązuje wynik r1 (limit 3 s): Glu +1 tak (88 / 90 / 55), Glu −1 nie (0 / 85 / 53).
Zastrzeżenia bez zmian: napęd z barku i łokcia (Glu +1) albo samego łokcia (Glu −1); nadgarstek bez sygnału; symulacja.
| 27 | **Test kroku 4** (`--seed 21501`, 6 póz, 32 sieci, raz; `STEP4_FINAL_TEST=1`) | `one_reflex.sh`, `reflex_test_jobs.txt` → `reflex_test/rt_*.json` | 32/32 plików, brak błędów w logach; 24 ważne pary (6 par odpadło: podjazd nieosiągalny — jednakowo dla wszystkich sieci) |
| 28 | Analiza kroku 4 (hashe `analyze_reflex.py` 34bb3236…, `reflex.py` 65fc342f… = sprzed testu) | `analyze_reflex.py reflex_test rt` → `reflex_test/analysis_reflex.json` | tabela niżej |

## Wynik testu kroku 4 (krok 28) — pary scen z OBOMA odruchami udanymi, na 24 (w nawiasie: W cofnięcie / C chwyt)

| Glu | N (dane) | F1–F5 swobodne | L1–L5 warstwy | G1–G5 warstwy + nogi |
|---|---|---|---|---|
| +1 | **15** (23 / 16) | 0 (0/3), 0 (0/19), 0 (0/13), 0 (0/6), 0 (0/17) | 5 (5/22), 9 (15/16), 16 (16/22), 3 (8/13), 2 (3/12) | 13 (20/15), 4 (14/5), 9 (9/21), 15 (20/17), 8 (9/21) |
| −1 | **5** (5 / 18) | 0 (0/12), 0 (0/9), 0 (0/14), 0 (0/16), 0 (0/17) | 0 (0/13), 0 (1/8), 0 (0/15), 0 (7/0), 0 (6/4) | 8 (9/23), 0 (1/16), 2 (4/17), 0 (0/8), 1 (2/22) |

| Hipoteza (McNemar + Holm) | Glu +1 | Glu −1 |
|---|---|---|
| H-R(F): N lepsza od każdego tasowania swobodnego | **POTWIERDZONA** (5 × 15 : 0, p_Holm = 0,0003) | nie (5 : 0, p_Holm = 0,31) |
| H-R(L): N lepsza od każdego tasowania z warstwami | nie — lepsza od L1 (p 0,039), L4 (0,007), L5 (0,001); nie od L2 (9 : 3, p 0,29) ani L3 (5 : 6) | nie (5 : 0, p 0,31) |
| H-R(G) | nie (lepsza tylko od G2) | nie |

Werdykt wg `LOOP_TARGET_reflex_r1.md`: „schemat połączeń ma znaczenie w zadaniu dla robota” wymagało H-R(F) **i** H-R(L) —
**niespełnione** (Glu +1: tylko H-R(F); Glu −1: żadna). Co wolno powiedzieć: przy Glu +1 sieć z danych wykonuje oba odruchy
w 15 z 24 par, a żadna z pięciu sieci o swobodnie przetasowanych połączeniach (te same neurony, te same stopnie i wagi) ani razu;
tasowania swobodne nigdy nie cofają ramienia po dotyku dłoni (W 0/24 w każdym z 10 przebiegów). Wobec tasowań zachowujących
warstwy przewaga jest częściowa (3 z 5), a gdy zachować też podział na nogi — znika.

## Podsumowanie poziomów dowodu (krok 3 i 4)

| Twierdzenie | Poziom |
|---|---|
| Cisza barku w kroku 2 wynikała z za małego wycinka sieci; reguła „pre” obejmuje 74–82 % wejścia pul | VERIFIED (dane + model) |
| Sieć z danych steruje podnoszeniem i odkłada przedmioty na poziomie klasycznego sterownika — Glu +1, limit 3 s (88 / 90 / 55) | VERIFIED (test z góry zapisany, 135 prób) |
| To samo niezależnie od znaku Glu — limit 10 s (94 / 93 / 59 i 86 / 86 / 58) | VERIFIED (test r2) |
| To samo przy Glu −1 i limicie 3 s | FAILED (0 / 85 / 53) |
| Nadgarstek sterowany siecią | NOT IMPLEMENTED — pule stępu bez sygnału z receptorów nogi (VERIFIED model) |
| Sieć z danych lepsza od przetasowanych w liczbie odłożonych przedmiotów | FAILED (C3S, C3L) |
| Sieć z danych „cichsza” / „spokojniejsza” od przetasowanych | FAILED (H-cisza odwrócona; H-spokój 9 z 10) |
| Schemat połączeń decyduje, które mięśnie odpowiadają na dotyk (wybiórczość noga → noga), oba Glu, 80 tasowań | VERIFIED (model, test z góry zapisany) |
| …także ponad podział na nogi (dobór konkretnych interneuronów) | PARTIALLY VERIFIED (Glu +1 tak, o włos; Glu −1 nie) |
| Na robocie, zadanie dwóch odruchów: dane lepsze od każdego tasowania swobodnego (Glu +1) | VERIFIED (15 : 0 ×5) |
| …od każdego tasowania zachowującego warstwy | FAILED jako całość (3 z 5) |
| …przy Glu −1 | FAILED |
| Cokolwiek z powyższych na prawdziwym ramieniu | NOT IMPLEMENTED |

Ziarna zużyte w kroku 3/4: 21 100 001–010, 21 101 xxx, 21 201 xxx, 21 210 001–005, 21 220 001–005, 21 230 001–020,
21 240 001–020, 21 250 001–020, 21 260 001–020, 21 270 001–020, 21 301 xxx, 21 401 xxx, 21 501 000–149, 21 510/520/530 001–005.
Pomyłki uruchomieniowe (żadna nie zużyła ziaren testowych): 2 × błąd składni komendy w powłoce, 1 × `xargs -I` za długa komenda.
Nic nie zacommitowano; żaden moduł wspólny ani plik kroku 2 nie został zmieniony (`git status`: tylko nowe katalogi
`experiments/step3_wiring/`, `results/step3_20261115/` oraz wcześniejszy `panel/`).

## Krok 5 — nadgarstek (16 XI 2026)

| # | Co | Komenda / plik | Wynik |
|---|---|---|---|
| 29 | Droga w danych do dźwigacza stępu (tylko odczyt) | `wrist_screen.py`, `wrist_dn_inputs.py` → `wrist_screen_v1.json`, `wrist_dn_inputs_v1.json` | Dźwigacz (Ta levator) dostaje 12 % wejścia od neuronów zstępujących; największy DNge078 (140 synaps, 13 % wejścia z szczecinek głowy BM). VERIFIED (dane) |
| 30 | Naturalne czucie → pule stępu, pojedynczo i w parach, sieć z receptorami nogi i płytkami włosków | `explore_wrist.py` → `explore_wrist_v1.json` | 0 Hz we wszystkich kombinacjach. VERIFIED (model) |
| 31 | Droga BM → DNge078 → dźwigacz; droga wzrokowa LPLC4 → DNp07 → dźwigacz | `explore_wrist_dn.py` → `explore_wrist_dn_v1.json` | BM 40 mV → DNge078 119 Hz → dźwigacz 20 Hz (oba Glu identycznie); wzrok: DNp07 83 Hz, dźwigacz 0 Hz. VERIFIED (model) |
| 32 | Trening (ziarno 21401) | `reflex5.py`, `one_reflex5.sh` → `wrist_train/it0_*.json` | Nadgarstek ruszył w 12/13 prób, stał w 15/15 (oba Glu); sukces ścisły 4/13 (Glu +1), 7/13 (Glu −1) |
| 33 | Cel PRZED testem | `LOOP_TARGET_wrist_r1.md`, `analyze_wrist.py`; hasze w `PRE_TEST_HASHES.txt` (07:31:30) | K5-A: ≥ 80 % prób W z ruchem nadgarstka i ≥ 95 % prób C ze spoczynkiem, dla obu Glu |
| 34 | **Test nadgarstka** (ziarno 21701, 22 sieci × 6 póz, raz) | `one_reflex5.sh` → `wrist_test/wt_*.json` | 22/22 plików, bez Traceback |
| 35 | Analiza K5-A (hasz skryptu zgodny z zapisanym przed testem) | `analyze_wrist.py wrist_test wt` → `wrist_test/analysis_wrist.json` | tabela niżej |
| 36 | Analiza K5-B (H-R, hasz zgodny) | `analyze_reflex.py wrist_test wt` → `wrist_test/analysis_reflex_wt.json` | tabela niżej |
| 37 | Kontrola: czy obie wersje Glu dają identyczne wyniki nadgarstka | skrypt w linii na `wt_N_g1.json` i `wt_N_g-1.json` | Macierze różnią się (sha256 różne, 3219 neuronów), ale ruch nadgarstka: 25/25 prób ten sam kierunek i wielkość przy ±0,02; wartości dq identyczne w 21/25. Sugeruje, że droga BM → DNge078 → dźwigacz nie zależy od glutaminianu (INFERRED: nie sprawdzono, czy któryś z neuronów na tej drodze jest glutaminergiczny) |

### Wyniki testu nadgarstka (N, 25 ważnych par prób)

| Glu | Ruch nadgarstka w W (≥0,02 rad) | Spoczynek nadgarstka w C | Sukces ścisły W | Sukces ścisły C | K5-A |
|---|---|---|---|---|---|
| +1 | **19/25 = 76 %** (próg: ≥ 80 %, czyli 20) | 30/30 = 100 % (próg 95 %) | 15/25 | 20/30 | **NIE** (o jedną próbę) |
| −1 | **19/25 = 76 %** | 30/30 | 15/25 | 24/30 | **NIE** (o jedną próbę) |

Tasowania swobodne (F1–F5): nadgarstek ruszył 0 razy we wszystkich 10 przebiegach (oba Glu). Tasowania zachowujące warstwy: L4 i L5 przy Glu −1 ruszyły nadgarstkiem w 18 i 17 z 25 prób; przy Glu +1 prawie nigdy.

### Porównania rodzin (K5-B, analyze_reflex.py; sukces ścisły OBA)

| Glu | H-R(F) | H-R(L) |
|---|---|---|
| +1 | **POTWIERDZONA** (N : F1–F5 = 8:0 każde, p_Holm 0,039) | **POTWIERDZONA** (N : L1–L5 = 8:0 każde, p_Holm 0,039) |
| −1 | **POTWIERDZONA** (11:0 każde, p_Holm 0,005) | nie (N : L4 = 2:5, p_Holm 0,45) |

Uwaga do K5-B: wartości p są małe, bo para prób jest mała (n = 8–11 par rozstrzygających); przy progu p < 0,05 po Holmie wynik jest rozstrzygający, ale mało liczny.

### Werdykt kroku 5 (zgodnie z regułami zapisanymi przed testem)
- **K5-A (nadgarstek sterowany siecią przez naturalny dotyk): FAILED** o jedną próbę w obu wariantach znaku. Nadgarstek rusza się w 76 % prób cofnięcia (próg 80 %) i stoi w 100 % prób chwytu. Nie zmieniam progu po wyniku.
- **K5-B:** H-R(F) potwierdzona dla obu Glu; H-R(L) potwierdzona tylko dla Glu +1.
- Wniosek dla nadgarstka: droga przez szczecinki głowy i DNge078 jest w danych i w modelu realna (VERIFIED), ale w tej sieci uruchamia nadgarstek w większości, nie we wszystkich, próbach. To jest najbliższa wartość, jaką da się uczciwie podać.

Ograniczenia: symulacja; dotyk dłoni „przy głowie” to przypisanie modelu (ANALOGIA); odruch zwiększa nacisk na przedmiot (palm_max mediana 2,2 N, do 39 N), co nie jest bezpiecznym zachowaniem; sukces ścisły wymaga także braku ruchu barku i łokcia, co dla tego odruchu jest warunkiem trudnym.

| 38 | Glutaminian na drodze nadgarstka (tylko odczyt konsensusowego przekaźnika z MaleCNS) | skrypt w linii na `connectome-weights` i `body-neurotransmitters` | BM (69 neuronów): 100 % acetylcholina; DNge078 (2 neurony): 100 % acetylcholina; droga BM → DNge078 = 713 synaps (38 neuronów BM); DNge078 → mięśnie Ta levator = 164 synaps (wszystkie MN Ta levator, bez względu na stronę; w kroku 5 liczone z puli `fl` L: 140). VERIFIED (dane konsensusowe; nie sprawdzono predykcji pewności). Wniosek: identyczny wynik nadgarstka przy Glu ±1 wynika z przekaźnika, nie z błędu |
| 39 | Podział pracy z drugą sesją (fac970) | wiadomość między sesjami; zatwierdzenie Adama | Dawka i siła: druga sesja (explore_dose, test z kontrolą tasowań). Nadgarstek: ta sesja. Rejestr ziaren i hasze dopisuje sesja prowadząca dany test |

## Krok 5b — nadgarstek, próg oddania dłoni 3 N (16 XI 2026)

| # | Co | Plik / hasz | Wynik |
|---|---|---|---|
| 40 | Przegląd porażek testu r1 (tylko odczyt, zużyte ziarna) | skrypt w linii na `wrist_test/wt_N_g*.json` | 6 z 10 porażek cofnięcia przy obu Glu: nacisk dłoni w chwili oddania >1 N, ale spadał do 0,05–0,67 N w 0,5 s; nadgarstek nie ruszał. HIPOTEZA (wynik po teście) |
| 41 | Jedyna zmiana: F_ON 1 N → 3 N | `reflex5_f3.py` (reflex.py i reflex5.py bez zmian) | — |
| 42 | Trening kontrolny (ziarno 21411, 3 pozy) | `wrist_f3_train/f3tr3_N_g*.json` | 13/13 ważnych prób ruszyło nadgarstkiem (oba Glu); sukces ścisły 7/13 (oba Glu). Kontrola, nie dowód |
| 43 | Cel PRZED testem | `LOOP_TARGET_wrist_r2.md`; hasze w `PRE_TEST_HASHES.txt` (analyze_wrist.py cfb45de2…, analyze_reflex.py 34bb3236… — zgodne z przed testem) | — |
| 44 | **Test r2** (ziarno 21801, 6 póz, raz, `STEP5B_FINAL_TEST=1`), 22 sieci | `one_f3.sh` → `wrist_f3_test/w3t_*.json` | 22/22 plików, bez Traceback |
| 45 | Analizy pre-rejestrowane | `analyze_wrist.py … w3t` → `analysis_wrist_r2.json`; `analyze_reflex.py … w3t` → `analysis_reflex_r2.json` | tabela niżej |

### Wyniki testu r2 (N, 28 ważnych par)

| Glu | Ruch nadgarstka w W | Spoczynek nadgarstka w C | Sukces ścisły W / C | K5-A |
|---|---|---|---|---|
| +1 | **28/28 = 100 %** (próg 80 %) | **30/30 = 100 %** (próg 95 %) | 15/28, 19/30 | **TAK** |
| −1 | **28/28 = 100 %** | **30/30 = 100 %** | 15/28, 24/30 | **TAK** |

Porównania (K5-B, ścisły sukces OBA):
- H-R(F): **POTWIERDZONA** przy obu Glu (N : F1–F5 = 11:0 przy +1; 13:0 przy −1; p_Holm ≤ 0,005).
- H-R(L): **POTWIERDZONA** przy Glu +1 (11:0 każde). Przy Glu −1 **nie**: N : L5 = 4:11 (p_Holm 0,12); reszta L1–L4 13:0.

### Werdykt
- **K5-A (nadgarstek sterowany siecią przez naturalny dotyk, oba znaki glutaminianu): potwierdzony w teście r2**, zgodnie z regułami z LOOP_TARGET_wrist_r2.md. Nadgarstek rusza się w 100 % prób cofnięcia i stoi w 100 % prób chwytu.
- Zastrzeżenia, które muszą iść razem z tym wynikiem:
  1. Zmiana (3 N) wynikła z porażek testu r1. Test r2 jest na nowych ziarnach i kryteria były zapisane przed nim, ale cel sam powstał po r1. Wynik traktuję jako potwierdzenie hipotezy, nie jako pierwotne odkrycie.
  2. Nacisk dłoni w chwili cofania ma medianę ok. 9 N (maks. 40 N). Odruch „cofnij nadgarstek” działa przez mocne dociśnięcie dłoni, nie przy delikatnym dotyku. To nie jest bezpieczne zachowanie dla sprzętu.
  3. Bark i łokieć: w 1 z 28 prób przy Glu +1 przesunęły się o więcej niż 0,01 rad (maks. 0,038 rad). To nie wpływa na K5-A, ale wpływa na ścisły sukces.
  4. Droga czucia dłoni → głowa (BM) → DNge078 → dźwigacz stępu jest acetylcholinowa, więc znak glutaminianu nie zmienia wyniku; dlatego wyniki K5-A są takie same przy obu Glu.
  5. Symulacja; przypisanie „dłoń przy kamerze = szczecinki głowy” to wybór modelu.

## Punkt 3 — połączenie mózg–odnóża (16 XI 2026, tylko dane i model, bez robota)

| # | Co | Plik | Wynik |
|---|---|---|---|
| 46 | Przeszukanie zstępujących neuronów łączących się z pulami nogi T1 L (fl, L) i dostających wejście z czucia (tylko odczyt) | `brain_leg_search.py` → `brain_leg_search_v1.json` | 228 zstępujących neuronów łączy się z pulami; 201 z nich ma ≥5 synaps bezpośrednio z czucia. Największe: DNg15 (314 synaps na pule, 32 % wejścia z czucia, z tego ponad 5000 synaps z BM), DNge078 (365 synaps, 21 % z czucia), DNa02 (221 synaps, czucie głównie wzrokowe). VERIFIED (dane) |
| 47 | Cel: dwa szlaki z głowy do nogi, rozdzielone przez usunięcie jednego z nich z sieci | `explore_dng15.py` → `explore_dng15_v1.json` (pierwsza wersja była błędna — stymulowała wszystkie drogi naraz, wyniki zlewały się; poprawiona przez usuwanie szlaków z sieci) | Bodziec: BM 40 mV, 1 s, szum 0. Bez DNg15: dźwigacz 20 Hz, łokieć 0. Bez DNge078: łokieć ext 21–32 Hz (Glu +1) / 21 Hz (Glu −1), dźwigacz 0. VERIFIED (model, eksploracja) |

**Wniosek:** w modelu głowa-dotyk uruchamia dwa oddzielne ruchy nogi: DNge078 → nadgarstek (dźwigacz), DNg15 → łokieć (prostownik). Oba przez receptory, bez sztucznego pobudzania neuronów. Robotowy test tego (czy dotyk głowy rusza jednocześnie łokciem i nadgarstkiem, z kontrolami tasowań) wymaga nowego celu zapisanego przed testem — jeszcze go nie ma.

## Sprawa 2 — test „dawka dotyku → siła zacisku” (16 XI 2026; sesja „badania nadgarstka i konektomu”, numeracja D1–D5, żeby nie kolidować z krokami 29–47 drugiej sesji)

Podział z drugą sesją (zatwierdzony przez Adama, przekazany przez nią): ta sesja — dawka i siła; tamta — nadgarstek.

| # | Co | Komenda / plik | Wynik |
|---|---|---|---|
| D1 | Eksploracja bez robota: krzywa dawka → moment szczęki (9 poziomów 0–40 mV na szczecinki T2 L); dane + 9 tasowań eksploracyjnych (F 21 100 001–003, L i G 21 100 006–008) | `explore_dose.py` → `explore_dose_g±1_v1.json` | Dane τ(40 mV) 0,903 (Glu +1), 0,615 N·m (Glu −1), krzywe stopniowe. Tasowania: maks. 0,898 (G8, Glu +1) i 0,375 (G7, Glu −1). Stopniowość nie odróżnia danych od L/G — odrzucona jako kryterium przed testem |
| D2 | Cel PRZED testem + ziarna | `LOOP_TARGET_dose_r1.md`, `dose_test.py`, `analyze_dose.py`; ziarna 21 910/920/930 001–020 w `SEED_REGISTRY.md`; hasze w `PRE_TEST_HASHES.txt` (07:51:14). Pierwotnie planowane 21 81x/82x — kolizja z rezerwacją nadgarstka 5b drugiej sesji, przeniesione przed jakimkolwiek użyciem | kryteria: warunek P (ρ ≥ 0,9, τ40 ≥ 0,10); H-S (τ40 danych > każdego z 20 tasowań), H-Rec (wzajemność rec40 > każdego); H-D = obie; werdykt wymaga H-D(F) i H-D(L) dla obu Glu |
| D3 | Przegląd kodu przed testem (`/code-review low` na `dose_test.py`, `analyze_dose.py`) | — | 0 uwag |
| D4 | **Test** (2 × [dane + 3 rodziny × 20 tasowań], raz) | `one_dose.sh`, `dose_jobs.txt` → `dose/dose_g*_*.json` | 26/26 plików, bez Traceback; krzywa danych identyczna co do cyfry z eksploracją (deterministyczna). Obciążenie komputera do 110 — wpływa tylko na czas |
| D5 | Analiza (hasze `analyze_dose.py` 557dd468…, `dose_test.py` bc98e901…, celu 737b32db… = sprzed testu) | `analyze_dose.py dose dose/analysis_dose.json` | tabela niżej |

### Wynik (τ40 w N·m; rec40 = (zaciskacz − rozwieracz)/(suma) przy pełnym dotyku)

| Glu | Dane τ40 / rec40 | F: τ40 maks / rec40 ≥ danych | L: τ40 maks / rec40 ≥ danych | G: τ40 ≥ danych / rec40 ≥ danych | H-S F, L, G | H-Rec F, L, G |
|---|---|---|---|---|---|---|
| +1 | 0,903 / 0,569 (zaciskacz 249 Hz, rozwieracz 68 Hz) | 0,710 / 15 z 20 | 0,754 / 19 z 20 | 6 z 20 (maks. 0,990) / 20 z 20 | **tak, tak**, nie | nie, nie, nie |
| −1 | 0,615 / 1,0 (123 Hz / 0 Hz) | 0,257 / 2 z 20 (remis 1,0) | 0,275 / 16 z 20 (remis 1,0) | 1 z 20 (0,650) / 18 z 20 | **tak, tak**, nie | nie, nie, nie |

Warunek P spełniony (ρ 0,966 i 0,983). **Werdykt wg reguł zapisanych przed testem: FAILED** — „schemat połączeń ma znaczenie
dla dozowania siły” niepotwierdzone (H-Rec niespełniona w żadnej rodzinie; przy Glu +1 sieć z danych ma wzajemność
NIŻSZĄ niż mediana tasowań: współskurcz rozwieracza 68 Hz).
Co wolno powiedzieć: przy pełnym dotyku sieć z danych zaciska mocniej niż każde z 40 tasowań swobodnych i warstwowych,
dla obu znaków Glu (H-S(F), H-S(L): VERIFIED, model). Nie wiadomo, czy to „dobry schemat”, czy po prostu większa
ogólna aktywność sieci z danych (znana z H-cisza); kontrola wzajemności, która miała to rozstrzygnąć, nie wyszła.
Gdy zachować podział na nogi (G), przewaga znika (6 i 1 z 20 tasowań dorównuje lub przewyższa).

## Krok 6 — dotyk głowy → łokieć i nadgarstek (dwa szlaki z danych), 16 XI

| # | Co i dlaczego | Komenda / plik | Wynik |
|---|---|---|---|
| 48 | Znak przekaźnika na obu szlakach (czy Glu ±1 ma znaczenie) | `consensus_nt` / `predicted_nt` dla BM, DNge078, DNg15 | wszystkie acetylocholina (konsensus); w przewidywaniu BM 57 ACh, 7 serotonina, 5 niejasne. Znak Glu nie zmienia szlaków — VERIFIED (dane) |
| 49 | Sieć z oboma szlakami i analiza | `brainleg.py` (3221 neuronów: „pre” + 69 BM + 2 DNge078 + 2 DNg15), `analyze_brainleg.py` | — |
| 50 | Trening (ziarno 21421, 3 pozy; N, F1 21 100 001, L6 21 100 006; oba Glu) | `brainleg_train/tr_*.json` | 9 ważnych par na Glu (6 W nieważnych: poza nieosiągalna). N Glu −1: łokieć 7, nadgarstek 7, oba 7, C stoi 9/9. N Glu +1: łokieć 8, nadgarstek 0 (mediana 0,012 rad), C stoi 9/9. F1 i L6: ruszają ramieniem bez dotyku (C stoi 0/15) — VERIFIED (trening, nie dowód) |
| 51 | Zmiana miary porównania PRZED testem: odpowiedź wybiórcza (oba stawy w W **i** C stoi), bo tasowania ruszają się same | `analyze_brainleg.py` (funkcja `specific`); na treningu Glu −1: N 7 vs F1 0, L6 0 | — |
| 52 | Cel, ziarna, hasze PRZED testem | `LOOP_TARGET_brainleg_r1.md`; SEED_REGISTRY: 21 831 000–149, 21 840 001–005, 21 850 001–005 (dopisane na końcu); `PRE_TEST_HASHES.txt` 11:41:15 — hasze reflex/reflex5/nets/nets2 identyczne jak w krokach 4–5 (moduły bez zmian) | — |
| 53 | Wiadomość do drugiej sesji: SEED_REGISTRY.md był nadpisany ze starszej kopii (zginęły 2 wiersze „ZUŻYTE”, przywrócone); prośba o dopisywanie tylko na końcu | SendMessage → sesja „FlyMind badania nadgarstka i konektomu” | dostarczona (odczytu nie potwierdzono) |
| 54 | **Test** (ziarno 21831, 6 póz, raz, `STEP6_FINAL_TEST=1`), 22 sieci, 11:41–11:51 | `one_bl.sh` → `brainleg_test/te_*.json` | 22/22 plików, kod 0, bez Traceback |
| 55 | Analiza pre-rejestrowana | `analyze_brainleg.py brainleg_test te analysis_brainleg_r1.json` | tabela niżej |
| 56 | Dodatkowo (NIE pre-rejestrowane): oba stawy w W bez warunku C | odczyt `te_*.json` | Glu −1: N 20, tasowania F 0/0/0/0/0, L 7/0/0/0/0. Glu +1: N 0, F 0/0/0/1/0, L 4/0/0/0/0 |

**Wynik kroku 6 (28 ważnych par na Glu; 2 z 30 W nieważne — poza nieosiągalna):**

| | łokieć (≥80 %) | nadgarstek (≥80 %) | oba (≥70 %) | C stoi (≥95 %) | H(F) | H(L) |
|---|---|---|---|---|---|---|
| Glu −1 | 20/28 = 71 % **FAILED** | 20/28 = 71 % **FAILED** | 20/28 = 71 % **PASS** | 28/28 **PASS** | **POTWIERDZONA** (20:0 ×5, p_Holm < 0,001) | **POTWIERDZONA** (20:0 ×5) |
| Glu +1 | 22/28 = 79 % **FAILED** (o 1 próbę) | 0/28 **FAILED** | 0/28 FAILED | 28/28 PASS | nie (0:0) | nie (0:0) |

Gdzie N przy Glu −1 nie przeszło progu: śliskie tworzywo 6/6 prób (ruch był, ale za mały: łokieć 0,006–0,007, nadgarstek
0,0095–0,014 rad) i ciężki walec 2/6 (0,005 / 0,0075). We wszystkich 28 parach kierunek ruchu był właściwy (łokieć prostuje,
nadgarstek unosi). Tasowania ruszają się bez dotyku (C stoi 0–12/30), sieć z danych stoi w 30/30.
Wniosek: cel „dotyk głowy steruje łokciem i nadgarstkiem” — **FAILED** wg kryteriów (71 % < 80 %), tylko BL_C i BL_D
spełnione przy Glu −1; przy Glu +1 nadgarstek nie działa (zgodnie z przewidywaniem). Dowód schematu: przy Glu −1 odpowiedź
wybiórcza jest wyłącznie w sieci z danych (H(F), H(L) VERIFIED, model) — ale miara wybiórcza powstała po obejrzeniu
treningu (zapisane w celu przed testem). Ziarna 21 831 xxx, 21 840 xxx, 21 850 xxx zużyte.

## Krok 6 r2 — diagnoza porażki r1 i test z sondą dłoni, 16 XI

| # | Co i dlaczego | Komenda / plik | Wynik |
|---|---|---|---|
| 57 | Przebieg nacisku dłoni i częstości pul w czasie sterowania (trening 21421, N, oba Glu) | `explore_slick.py` → `explore_step6/slick_g±1.json` | kontakt znika po 1–3 taktach na twardym/śliskim/ciężkim walcu, na lekkim trwa 50/50; ruch kończy się razem z kontaktem. Glu +1: łokieć 33–66 Hz (Glu −1: 10–24 Hz), kontakt 2–9 taktów, nadgarstek nie zdąży — VERIFIED (model, eksploracja) |
| 58 | Kontrola: ramię zamrożone (sieć liczy, ruch 0) i tasowania F1/L6 | `explore_step6/frz_*`, `F1_*`, `L6_*` | zamrożone: kontakt 50/50 taktów przy każdym materiale → kontakt urywa ruch ramienia. Tasowania urywają kontakt nawet ruchem 0,0007 rad → zerwanie kontaktu nie odróżnia sieci — VERIFIED |
| 59 | Sonda dłoni: przedmiot dociskany do dłoni siłą ciężar + 3 N przez całe sterowanie (bodziec o stałym czasie) | `brainleg_probe.py`; `explore_step6/pr_*` | N: łokieć 0,05 (Glu −1) / 0,11 (Glu +1) rad, nadgarstek ~0,07 rad w 9/9 próbach, każdy materiał. F1: tylko łokieć; L6: prawie nic — VERIFIED (eksploracja) |
| 60 | Pełny trening z sondą (W i C; N, F1, L6; oba Glu) | `brainleg_probe_train/tr_*.json` | N: łokieć/nadgarstek/oba/C stoi 9/9 przy obu Glu; F1, L6: nadgarstek 0, C stoi 0 — VERIFIED (trening, nie dowód) |
| 61 | Cel r2, ziarna, hasze PRZED testem | `LOOP_TARGET_brainleg_r2.md`; SEED_REGISTRY: 21 861 000–149, 21 870 001–005, 21 880 001–005; `PRE_TEST_HASHES.txt` 12:34:09 — brainleg.py i analyze_brainleg.py identyczne jak w r1 | — |
| 62 | **Test r2** (ziarno 21861, 6 póz, raz, `STEP6B_FINAL_TEST=1`), 22 sieci, 12:34–12:44 | `one_pr.sh` → `brainleg_probe_test/te_*.json` | 22/22 plików, bez Traceback |
| 63 | Analiza pre-rejestrowana (ten sam kod co r1) | `analyze_brainleg.py brainleg_probe_test te analysis_brainleg_r2.json` | tabela niżej |

**Wynik kroku 6 r2 (26 ważnych par na Glu; 4 z 30 W nieważne — poza nieosiągalna):**

| | łokieć | nadgarstek | oba | C stoi | H(F) | H(L) |
|---|---|---|---|---|---|---|
| Glu −1 | 26/26 PASS (mediana 0,054 rad) | 26/26 PASS (0,073) | 26/26 PASS | 30/30 PASS | POTWIERDZONA (26:0 ×5) | POTWIERDZONA (26:0 ×5) |
| Glu +1 | 26/26 PASS (0,109) | 26/26 PASS (0,071) | 26/26 PASS | 30/30 PASS | POTWIERDZONA (26:0 ×5) | POTWIERDZONA (26:0 ×5) |

Tasowania: 2 z 20 (L3 Glu −1, L2 Glu +1) też ruszają oboma stawami po dotyku, ale ruszają się też bez dotyku (C stoi 0/30);
4 inne ruszają tylko łokciem; żadne tasowanie nie łączy ruchu po dotyku ze spokojem bez dotyku. Strażnik/siła bez uwag
(guard ≤ 0,38 tylko w 2 tasowaniach, fmax 0). Wniosek: przy dotyku o stałym czasie (0,5 s) sieć z danych porusza łokciem
i nadgarstkiem w 100 % prób przy obu znakach Glu — VERIFIED (model). Zastrzeżenie: r2 powstało po porażce r1 (r1 zostaje
FAILED); bodziec z sondą jest identyczny dla każdego materiału (czujnik nasyca się przy 1 N). Ziarna 21 861 / 870 / 880 zużyte.

## Krok 6 r3 — rodzina B i wycięcie szlaku, 16 XI

| # | Co i dlaczego | Komenda / plik | Wynik |
|---|---|---|---|
| 64 | Trening rodziny B z sondą (BM i DN jako osobne grupy; 21 100 006/007) | `brainleg_probe_b.py` → `brainleg_probeB_train/` | B6, B7: łokieć i nadgarstek 9/9 (oba Glu); C stoi: B6 Glu −1 9/9, pozostałe 0–2/9 — VERIFIED (trening) |
| 65 | Dlaczego B nie odróżnia: połączenia DN→pule po tasowaniu B | `explore_dn_targets.py` | N: DNge078→nadgarstek +28/−1, DNg15→łokieć −17; B6/B7: prawie identyczne (4 DN, brak krawędzi do zamiany); L6: szlaki rozbite. B nie jest kontrolą szlaków; testu B nie robię (zapisane w `LOOP_TARGET_brainleg_r3.md`) — VERIFIED (dane modelu) |
| 66 | Trening wycięcia szlaku (zerowanie wyjść 2 neuronów) | `brainleg_lesion.py` → `brainleg_lesion_train/` | bez DNg15: łokieć 0/9, nadgarstek 9/9; bez DNge078: łokieć 9/9, nadgarstek 0/9; C stoi 15/15; oba Glu — VERIFIED (trening) |
| 67 | Cel r3, analiza, ziarna, hasze PRZED testem | `LOOP_TARGET_brainleg_r3.md`, `analyze_lesion.py` (sprawdzona na treningu), SEED_REGISTRY 21 891 000–149, `PRE_TEST_HASHES.txt` 12:53:50 | — |
| 68 | **Test r3** (ziarno 21891, 6 póz, raz, `STEP6C_FINAL_TEST=1`), 6 przebiegów, 12:53–12:56 | `brainleg_lesion_test/te_*.json`; `analyze_lesion.py` → `analysis_lesion_r3.json` | 6/6 plików, bez Traceback |

**Wynik kroku 6 r3 (27 ważnych par na Glu):** N nienaruszone: łokieć 27, nadgarstek 27, C stoi 27 (LZ_3 PASS).
Bez DNg15: łokieć **0**/27, nadgarstek 27/27, C stoi 27/27 (LZ_1 PASS, p_Holm 3·10⁻⁸). Bez DNge078: łokieć 27/27,
nadgarstek **0**/27, C stoi 27/27 (LZ_2 PASS, p_Holm 3·10⁻⁸). Identycznie dla Glu +1 i Glu −1. Podwójna dysocjacja —
VERIFIED (model): w tym modelu łokciem steruje szlak BM→DNg15, nadgarstkiem BM→DNge078. Ziarna 21 891 xxx zużyte.

## Krok 6 r4 — szum neuronów, 16 XI

| # | Co i dlaczego | Komenda / plik | Wynik |
|---|---|---|---|
| 69 | Spis (tylko odczyt): które stawy steruje sieć w zadaniu całego ramienia (krok 3) | `launch3.sh`, `joint_net.ArmCfg` | sieć: stawy 1–3 w podnoszeniu (`--joints 1,2,3`), obrót nadgarstka 4 w trzymaniu (`--roll`), szczęka; klasyczne: staw 0 (podstawa), dojazd/zejście/odkładanie (IK), harmonogram. Staw 0 z sieci tylko w pokazie 1 (wzrok, osobne zadanie) — VERIFIED (kod) |
| 70 | Szum w modelu: `ALIFParams.noise` (σ mV, standard projektu 2 mV) | `alif.py` l. 31, 74; `brainleg_noise.py` (nowy, podmienia `BrainNet.reset` w pamięci) | — |
| 71 | Trening z szumem σ 2 i 6 mV (21421; ziarna szumu 21 601/602 xxx) | `brainleg_noise_train/` | N 9/9 oba stawy, C stoi 15/15; bez DNg15 łokieć 0; bez DNge078 nadgarstek 0; oba Glu, oba σ; ruch bez dotyku ≤ 0,006 rad — VERIFIED (trening) |
| 72 | Cel r4, ziarna, hasze PRZED testem | `LOOP_TARGET_brainleg_r4.md`; SEED_REGISTRY 21 631 xxx, 21 641/642 xxx; `PRE_TEST_HASHES.txt` 13:37:12 | — |
| 73 | **Test r4** (ziarno 21631, 6 póz, raz, `STEP6D_FINAL_TEST=1`), 12 przebiegów, 13:37–13:42 | `brainleg_noise_test/`; `analyze_lesion.py` → `analysis_noise_r4_s2.json`, `…_s6.json` | 12/12 plików, bez Traceback |

**Wynik r4 (26 par na Glu i σ):** σ 2 mV i σ 6 mV, Glu +1 i −1 — N: łokieć 26, nadgarstek 26, C stoi 26 (LZ_3 PASS);
bez DNg15: łokieć 0, nadgarstek 26 (LZ_1 PASS); bez DNge078: łokieć 26, nadgarstek 0 (LZ_2 PASS); p_Holm 6·10⁻⁸.
Wynik r2/r3 przetrwał szum neuronów — VERIFIED (model). Ziarna 21 631 / 641 / 642 xxx zużyte.
| 74 | Integracja (eksploracja, sceny treningowe 21101, limit 10 s): zadanie całego ramienia z kroku 3 z siecią kroku 6 (3221 neuronów) | `run3_ext.py` → `integr_train/ext_lm10_N_g±1.json`; porównanie z `train/it1_lm10_N_g±1.json` | odłożone: Glu +1 29/45 (krok 3: 29), Glu −1 30/45 (krok 3: 30); **0 prób o innym wyniku**; siła na stół 0 N, bezpiecznik 0. Dołożone drogi z głowy nie psują podnoszenia — VERIFIED (trening, nie test) |

## Krok 4 r2: „dwa odruchy”, test 3× większy (16 XI 2026; sesja dawki, numeracja R1–R4)

| # | Co | Plik / komenda | Wynik |
|---|---|---|---|
| R1 | Cel, ziarna i hasze PRZED testem; zgoda Adama 16 XI | `LOOP_TARGET_reflex_r2.md`, `analyze_reflex2.py`; SEED_REGISTRY: 21 951–953 xxx, 21 960/970/980 001–005 (dopisane na końcu); `PRE_TEST_HASHES.txt` 15:36:17 | reflex.py 65fc342f, nets.py 058d6c97, analyze_reflex.py 34bb3236: te same co w r1 |
| R2 | Przegląd kodu (/code-review low) | analyze_reflex2.py, one_reflex_r2.sh | 0 uwag |
| R3 | **Test** (raz): 32 sieci × 3 ziarna scen × 6 póz | `one_reflex_r2.sh`, `reflex_r2_jobs.txt` (xargs -P 5 -L 1) → `reflex_r2/x*_g*.json` | 96/96 plików, 0 Traceback, w każdym pliku hasze kodu sprzed testu, ziarna tasowań zgodne z rejestrem |
| R4 | Analiza (raz; hasz analyze_reflex2.py ea566752… = sprzed testu) | `analyze_reflex2.py reflex_r2 reflex_r2/analysis_reflex2.json` | tabela niżej |

### Wynik: pary z OBOMA odruchami udanymi, na 77 ważnych par (13 z 90 odpadło przez nieosiągalny podjazd, tak samo dla każdej sieci)

| Glu | N (dane) | F1–F5 | L1–L5 | G1–G5 |
|---|---|---|---|---|
| +1 | **49** (W 70 / C 53) | 0, 0, 1, 0, 0 | 34, 15, 3, 8, 26 | 43, 31, 34, 9, 14 |
| −1 | **22** (W 22 / C 62) | 0, 0, 0, 0, 0 | 0, 0, 0, 0, 1 | 0, 29, 12, 1, 2 |

| Hipoteza (McNemar + Holm) | Glu +1 | Glu −1 |
|---|---|---|
| H-R(F) | **POTWIERDZONA** (48–49 : 0) | **POTWIERDZONA** (22 : 0 ×5) |
| H-R(L) | **POTWIERDZONA** (najsłabiej L1 26 : 11, p_Holm 0,020) | **POTWIERDZONA** (21–22 : 0) |
| H-R(G) | nie: 4/5 (G1 20 : 14, p 0,39) | nie: 3/5 (G2 2 : 9 i G3 15 : 5, p 0,083) |

Werdykt wg `LOOP_TARGET_reflex_r2.md`: „schemat połączeń ma znaczenie w zadaniu dla robota” **POTWIERDZONE dla obu znaków Glu** (H-R(F) i H-R(L)).
- Przy Glu −1 oczekiwałem porażki (zapisane przed testem). Wynik jest lepszy od oczekiwań: sieć z danych robi oba odruchy rzadko (22/77), ale żadne tasowanie F ani L prawie nigdy (0–1).
- Wynik r1 (24 pary) pozostaje niespełniony. r2 to nowy test zaprojektowany po r1, z nowymi ziarnami.
- Ponieważ H-R(G) nie przeszło, wystarcza w dużej mierze zachować, która grupa neuronów (noga, warstwa) łączy się z którą; konkretny dobór neuronów nie jest potrzebny.
- Nie wykluczone: część przewagi może wynikać z większej ogólnej aktywności sieci z danych (por. test dawki). Ten test tego nie rozdziela.
- Stabilność między ziarnami scen (opisowo): N Glu +1 OBA 15/25, 15/25, 19/27; Glu −1 5/25, 8/25, 9/27.
