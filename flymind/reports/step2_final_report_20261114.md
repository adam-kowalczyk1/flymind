# FlyMind — krok 2: ramię SO-101 sterowane siecią muchy — RAPORT KOŃCOWY (symulacja MuJoCo)

Data: 14 XI 2026. Wszystko w symulacji; fizycznego robota nie dotykano. Dwie sesje Claude pracowały równolegle:
sesja „FlyMind autonomiczny plan ramienia” (stawy c, d, e, całe ramię, interfejs, konflikt bodźców, ten raport) i druga sesja
(staw b: pętla, test, dt 0,1 ms). Oznaczenia dowodów: VERIFIED / PARTIALLY VERIFIED / REPORTED / INFERRED / HYPOTHESIS /
NOT VERIFIED / FAILED / NOT IMPLEMENTED.

Logi źródłowe (wszystkie liczby poniżej pochodzą z nich i z plików wyników):
- `results/step2_whole_arm_20261113/step2_log_2026-11-13.md` (części 1–5.3; „Część 4” = staw b, druga sesja),
- `results/step2_whole_arm_20261113/step2_log_2026-11-13_part5.md` (§5.4–5.20: stawy c, d, e, całe ramię, dt 0,1 ms),
- `results/step2_whole_arm_20261113/step6_interface_log_2026-11-13.md` (krok 6),
- `results/step2_whole_arm_20261113/step7_conflict_log_2026-11-13.md` (krok 7).

---

## 1. Najkrócej (prostym językiem)

1. **Żaden staw ani całe ramię nie osiągnęły celu** (b, c, d, e, całe ramię: FAILED; siła 0 N wszędzie). Bark (b): sieć
   unosi 27/135 przy Glu +1, 0 przy Glu −1, 0 odłożeń; jedyny staw, gdzie sieć z danych pokonała 4 z 5 tasowań.
   Najbliżej był łokieć (c) przy Glu +1: sieć muchy podnosiła przedmiot tak samo często jak klasyczny sterownik (107 vs 100 na 135) i częściej niż prosty odruch (p = 0,0008). Ale sieci z
   **przetasowanymi** połączeniami robiły to samo albo lepiej (105–115) — więc nie ma dowodu, że liczą się połączenia z danych.
2. **Całe ramię z sieci: 0 odłożonych przedmiotów na 135** (oba Glu). Sieć unosi łokciem do ~3 cm w 3 s, a do przeniesienia
   trzeba 5,5 cm. Klasyczny sterownik odkłada 81–89/135.
3. **Przyczyna jest w danych, nie w kodzie** (VERIFIED przesiewem receptorów): sygnał dotyku i propriocepcji z nogi T1 L / T2 L
   nie dociera do neuronów ruchowych „wymachu” (bark do góry) ani do mięśni stępu (nadgarstek). Te pule dostają 76–81 % wejścia
   od interneuronów, których receptory nie pobudzają — w muszce sterują nimi najpewniej ośrodki wyższe [INFERRED].
4. **Bezpieczeństwo:** siła ramię↔stół 0,0 N we wszystkich próbach testowych tej sesji (c, d, e, całe ramię: 4 × 17 serii × 135
   prób, wszystkie ramiona) — VERIFIED z analiz; bezpiecznik stołu w sieci z danych
   ani razu nie przejął sterowania w testach.
5. **Wzrok + dotyk (krok 7):** bodziec wzrokowy bardzo silnie pobudza neuron DNa02 (+135 Hz), ale **nie zmienia chwytu** (< 1 %,
   kierunek niespójny) — ani w sieci z danych, ani w 5 wersjach z przetasowanymi połączeniami. Wynik zerowy.
6. **Interfejs na żywo (krok 6):** działa, test zgodności VERIFIED; samego okna interaktywnego nikt nie oglądał (NOT VERIFIED).
7. **Krok czasu 0,1 ms zamiast 1 ms:** dla (c), (d), (e) bez zmian wniosków (d, e identyczne; c −3 podniesienia na 45,
   nieistotne). **Dla barku (b) różnica duża:** Glu +1 23/45 podniesień przy 0,1 ms vs 7/45 przy 1 ms (p = 3·10⁻⁵). Testy
   i całe ramię liczono przy 1 ms (tak zatwierdzono), więc dla barku wynik jest zaniżony; wniosek „poniżej K” zostaje.

---

## 2. Co było testowane (wspólne dla wszystkich stawów)

- Sieć: podgraf MaleCNS — obwód nogi T2 L + T1 L + wszystkie neurony ruchowe „fl” strony L + interneurony przedruchowe T1 L
  (reguła „fl” = `--net it2` drugiej sesji; ta sama macierz W: sha Glu +1 `2dfbb84e…`, Glu −1 `a85285c6…`, 2593 neurony).
  Neurony ALIF, dt 1 ms. Glu ±1 = dwa warianty znaku glutaminianu (w danych nieznany).
- Wejścia **tylko przez receptory**: dotyk padów chwytaka → szczecinki T2 L (i T1 L, [MODEL]); kąt łokcia → FeCO T1 L ([MODEL],
  tylko c it2). Żadnego pobudzania neuronów ruchowych ani interneuronów z zewnątrz.
- Komenda stawu: cel += znak·k·dt·(częstość puli POS − puli NEG); k = 0,005 rad/s/Hz, τ 50 ms (`CALIBRATION_k_SIGNS.md`).
  Pule: [BIOLOGIA] = mięśnie nogi o tej samej funkcji w muszce; [ANALOGIA] = przypisanie umowne (e: obrót = krętarz, znak arbitralny).
- Ramiona porównawcze: **N** sieć z danych; **S1–S5** ta sama sieć z przetasowanymi połączeniami (te same stopnie i wagi);
  **R** trywialny odruch (stała prędkość 0,5 rad/s „w górę”; w (e) i całym ramieniu trzymanie nadgarstka); **K** klasyczny IK z tym
  samym rusztowaniem; **K0** pełny klasyczny kontroler. Szczęka: osobna sieć nogi T2 L (LegJaw) we wszystkich ramionach poza K0.
- Kryteria (spisane przed testami): C1 niegorszość wobec K (dolna granica 95 % bootstrapu ≥ −10 pp), C2 McNemar N > R (p < 0,05,
  CI > 0), C3 N > każde Sᵢ (McNemar + Holm), C4 siła ≤ 5 N i bezpiecznik ≤ 10 % taktów. Test: 135 prób (45 scen × 3 pozy),
  ziarna testowe użyte raz.

---

## 3. Wyniki testów końcowych — staw po stawie

### (b) shoulder_lift — bark [BIOLOGIA: wymach vs podpór biodra T1] — prowadziła druga sesja
Pełny raport drugiej sesji: `results/step2_whole_arm_20261113/REPORT_b_2026-11-14.md`. Liczby poniżej sprawdziłem w
`lift_b/test/analysis_g±1.json` i `lift_b/test_dt01/compare_g±1.json` — VERIFIED. Test `--seed 20201`, wersja it3
(`lift_b.py --net it2 --lift-max 30`, dt 1 ms), wynik główny `lift`.

| Glu | N lift [Wilson 95 %] | K | R | K0 | S1–S5 | N placed | K / R / K0 placed |
|---|---|---|---|---|---|---|---|
| −1 | **0/135** [0; 3 %] | 95 | 77 | 98 | 0, 97, 99, 93, 109 | 0 | 87 / 65 / 94 |
| +1 | **27/135** [14; 28 %] | 103 | 87 | 98 | 105, 0, 0, 0, 0 | 0 | 93 / 73 / 94 |

C1 nie (N − K −0,70 / −0,56), C2 nie (N − R −0,57 / −0,44), C3 nie (Glu +1: N > S2–S5 po Holmie, 27:0, ale N < S1 −0,58),
C4 tak (0,00 N; bezpiecznik w N 0 %; tasowania pchające w dół: do 75–95 % taktów przejęte). **FAILED.** Udział sieci 25–26 %.
**dt 0,1 ms (N, 45 scen):** Glu −1 0 vs 0; **Glu +1 23/45 vs 7/45 przy 1 ms, pary 16:0, p = 3·10⁻⁵** — w tej sieci krok
1 ms wyraźnie zaniża wynik (to sprawdzenie, nie kryterium; nawet 23/45 < K).
Historia pętli (VERIFIED, Część 4 logu): it1 N 0/45 (błąd definicji sieci, poprawiony); it2 N 0/45 (Glu +1 Δz 3,8 mm w 3 s);
it3 (limit 30 s) Glu +1 11/45 podniesień ≥ 2 cm, 0 odłożeń; Glu −1 0/45. Koniec pętli na limicie 3 h. Wszystkie iteracje FAILED.

### (c) elbow_flex — łokieć [BIOLOGIA: zginacz vs prostownik goleni] — test `--seed 20401`, wersja it1
| Glu | N lift [Wilson 95 %] | K | R | K0 | S1–S5 | N placed |
|---|---|---|---|---|---|---|
| −1 | **0/135** [0; 2,8 %] | 96 | 75 | 99 | 0, 0, 76, 35, 114 | 0 |
| +1 | **107/135** [71,7; 85,2 %] | 100 | 87 | 99 | 111, 115, 113, 105, 115 | 0 |

Glu +1: C1 **tak** (N − K +0,05 [−0,01; +0,12]); C2 **tak** (+0,15 [0,07; 0,23], p = 0,0008); C3 **nie** (vs S: −0,06…+0,01,
Holm: żadne); C4 tak. **FAILED na C3.** Glu −1: FAILED (C1–C3). Siła 0 N, bezpiecznik 0. Udział komend sieci 7–9 % taktów.
Historia: it1 (padsT2 + padsT1) Glu +1 34/45 = K, S1 36 → C3 nie; it2 (+ FeCO T1) bez zmian; koniec pętli po it2 (~1 h 10 min).
dt 0,1 ms (45 scen, poza 0): Glu +1 32 vs 35 przy 1 ms (0/3 rozbieżne, p = 0,25); Glu −1 0 vs 0.

### (d) wrist_flex — zgięcie nadgarstka [BIOLOGIA: dźwigacz vs obniżacz stępu] — test `--seed 20601`, wersja it1
| Glu | N lift | K | R | K0 | S1–S5 | N placed | K / R / K0 placed |
|---|---|---|---|---|---|---|---|
| −1 | **0/135** | 95 | 98 | 98 | 0 ×5 | 0 | 87 / 6 / 96 |
| +1 | **0/135** | 101 | 106 | 98 | 0 ×5 | 0 | 92 / 7 / 96 |

**FAILED (C1–C3), C4 tak.** Pule stępu nie dostają żadnego pobudzenia z receptorów → sieć i tasowania nie ruszają nadgarstkiem.
Pętla: 1 iteracja, koniec z braku hipotezy w dozwolonych zmianach. dt 0,1 ms: 0 vs 0 (oba Glu).

### (e) wrist_roll — obrót nadgarstka [ANALOGIA: krętarz; znak arbitralny] — test `--seed 20801`, wynik `placed`
| Glu | N placed [Wilson 95 %] | K | R (trzymanie) | K0 | S1–S5 | maks. obrót N / S [rad] |
|---|---|---|---|---|---|---|
| −1 | **83/135** [53,1; 69,3 %] | 85 | 83 | 98 | 83, 83, 82, 82, 83 | 0,000 / 0,06–0,20 |
| +1 | **91/135** [59,1; 74,7 %] | 92 | 91 | 98 | 87, 86, 86, 86, 86 | 0,008 / 0,30–1,14 |

C1 tak (trywialnie), C2 nie dotyczy, C3 nie (p 0,06–0,13), C4 tak → **FAILED (C3).** Sieć z danych praktycznie nie obraca
nadgarstka (identyczna z „trzymaniem” w każdej próbie). dt 0,1 ms: 28 vs 28 i 32 vs 32.

### Całe ramię (krok 5) — stawy 1–3 w podnoszeniu + obrót, test `--seed 20901`, wynik główny `placed`
Konfiguracja (§5.18, przed testem): ta sama sieć, wejścia padsT2 + padsT1, limit fazy 3 s (sprzeczność 30 s (b) vs 3 s (c, d)
rozstrzygnięta regułą z góry — wygrywa staw z lepszym wynikiem treningowym względem K: (c) dla Glu +1, (d) dla Glu −1).

| Glu | wynik | **N** | K | R (wszystkie odruchy) | K0 | S1–S5 |
|---|---|---|---|---|---|---|
| −1 | placed | **0/135** [0; 2,8 %] | 81 | 53 | 96 | 96, 89, 0, 0, 33 |
| −1 | lift | 0/135 | 93 | 62 | 99 | 110, 107, 0, 102, 109 |
| +1 | placed | **0/135** [0; 2,8 %] | 89 | 55 | 96 | 75, 89, 0, 91, 71 |
| +1 | lift | 83/135 | 101 | 65 | 99 | 112, 104, 108, 105, 84 |

**FAILED (C1–C3), C4 tak** (siła 0 N; bezpiecznik N 0 taktów; tasowanie S3 Glu −1 18 %). Na `lift` Glu +1 N > R (p = 0,004).
Udział komend sieci: 19–22 % taktów (najwyższy w kroku 2). Unosi głównie łokieć (pule łokcia 2,5/18,5 Hz; barku 2,2/5,4 Hz;
stępu 0/0) — maks. 29,7 mm w 3 s, potrzeba 55 mm.

---

## 4. Krok 6 — interfejs na żywo
Plik `flymind/demo/demo_arm.py` (nowy; `demo.py` bez zmian): okno MuJoCo + raster wszystkich 4100 neuronów sterujących
(sieć ramienia 2593 + szczęka 1507), pule POS/NEG każdego stawu z częstościami, dekoder wyjścia, źródło komendy, faza.
- Uruchomienie: `.venv/bin/mjpython flymind/demo/demo_arm.py --seed 20951` (okno); `--media KATALOG` (nagranie); `--bench`.
- Test zgodności `flymind/demo/test_demo_arm.py`: WSZYSTKIE OK (wynik identyczny z eksperymentem, sha trajektorii
  `50b22ed1…`) — VERIFIED. Nagranie i zrzuty `flymind/demo/media_arm_20261113/` — obejrzany zrzut VERIFIED.
- Wydajność: 53 takty/s bez panelu (0,53× czasu rzeczywistego), 47 z panelem — REPORTED (zmierzone przy obciążonej maszynie).
- Okno interaktywne na ekranie: NOT VERIFIED (nikt go nie oglądał).

## 5. Krok 7 — konflikt bodźców (wzrok + dotyk na jednej sieci)
Sieć LC10a → DNa02 ∪ noga T2 L (1931 neuronów), wzrok zawsze włączony; zielona kula w kadrze vs szara (sham); 135 par na Glu.
| | Glu −1 | Glu +1 |
|---|---|---|
| DNa02 L (kontrola, on − sham) | +137,7 Hz [127,5; 147,5] | +133,4 Hz [124,3; 142,6] |
| moment szczęki (główna) | −0,0044 N·m [−0,012; +0,001], p = 0,63 | −0,0065 [−0,020; +0,003], p = 0,001 (mediana +0,0013) |
| odłożone on / sham | 87 / 91 (p = 0,13) | 93 / 94 (p = 1,0) |
Wynik: bodziec dociera, **chwyt bez zmian wg reguły z góry** (oba warunki naraz nie spełnione).
Tasowania S1–S5 krawędzi wzrok → noga (45 wspólnych scen, `conflict_7/test_analysis_full.json`): ten sam obraz — DNa02 +131–134 Hz,
moment szczęki zmienia się o −0,004…+0,002 N·m, odłożenia on/sham bez różnic. Efekt N na wspólnych scenach (|0,0003| i |0,0012|)
jest **mniejszy** niż największy efekt tasowań (0,0037 i 0,0024) → **brak swoistości dla połączeń z danych**. VERIFIED.
Prostym językiem: konflikt wzrok–dotyk nie przechodzi na chwyt w żadnej wersji sieci. Chwyt jest odporny na rozpraszający
bodziec, ale z tego samego powodu wzrok nie steruje w tej sieci szczęką. Szczegóły: `step7_conflict_log_2026-11-13.md`.

## 6. Procedura i błędy (uczciwie)
- Zderzenie dwóch sesji (18:15–18:35): podwójne uruchomienie (b) it1 i moje (b) it2 — oba przerwane przed zapisem wyników,
  logi przeniesione do `*_killed`; uzgodniony podział pracy, przypięta kopia `lift_b_pin.py`.
- Iteracja 0 całego ramienia: tasowanie S1 dostało ziarno testowe 20910001 — przerwane przed zapisem, powtórzone z 20952001.
- Analiza testu (e) zapisana, gdy gotowe było 13/17 serii — zachowana jako PARTIAL, nieużywana.
- Pilot 1 konfliktu: zielone przedmioty nasycały kamerę — odrzucony na podstawie obrazu, nie zachowania.
- Obciążenie maszyny 450–760: sprawdzone, że 1 wątek daje identyczne wyniki (VERIFIED); serie wstrzymywane na prośbę drugiej
  sesji (wpływa tylko na czas zegarowy).

## 7. Własne propozycje (osobno; nic z tego nie jest zrobione, każda wymaga Twojej zgody)

- **W1 — poszerzyć sieć o drogę „z góry” (zbieżne z P-b2 drugiej sesji).** Najważniejszy wniosek kroku 2: pule barku i stępu
  słuchają interneuronów, których receptory nogi nie pobudzają (76–81 % wejścia). Kolejny krok to dodanie z danych neuronów
  zstępujących i przekaźników między segmentami (T2 → T1), a nie dalsze dokładanie receptorów. Wymaga nowej kalibracji
  (pule), nowego pliku celu i nowej pętli. [HYPOTHESIS: z tymi neuronami bark i nadgarstek dostaną sygnał].
- **W2 — krok 0,1 ms jako standard dla sieci nóg (= P-b1).** Dla barku zmienia wynik 3×. Koszt ok. 10× czasu sieci; przy
  obecnym tempie pełny test 135 prób to ~37 h procesora na staw. Rozsądnie: najpierw tylko N i R na treningu.
- **W3 — zadanie, w którym struktura sieci ma znaczenie.** W (b), (c) i całym ramieniu tasowania z tymi samymi wagami często
  unoszą tak samo albo lepiej: zadanie „podnieś szybko” nagradza każdy silny napęd. Żeby pokazać, że liczą się połączenia
  z danych, potrzebne jest zadanie wymagające proporcji (np. dozowana siła, strona lewa/prawa jak w 38/40). Do zaprojektowania
  przed jakimkolwiek przebiegiem.
- **W4 — całe ramię z dłuższą fazą podniesienia** (30 s jak w b). Byłaby to zmiana po zobaczeniu wyniku, więc tylko jako nowy
  cel `LOOP_TARGET_arm_r2.md` z nowymi ziarnami testowymi. Spodziewam się [INFERRED] wyższego `lift`, ale bez dowodu znaczenia
  połączeń (patrz W3).
- **W5 — plakat i Explory:** pokazać uczciwie wynik negatywny z mechanizmem: sieć muchy steruje ramieniem bezpiecznie (0 N,
  0 przejęć bezpiecznika), łokieć działa jak klasyczny sterownik, ale tasowania też — a bark i nadgarstek „milczą”, bo
  w danych brakuje drogi od dotyku do tych mięśni. Materiał wideo: `flymind/demo/media_arm_20261113/`.
- **W6 — dwie drobne rzeczy dla Ciebie:** (a) obejrzeć okno interfejsu jedną komendą
  `.venv/bin/mjpython flymind/demo/demo_arm.py --seed 20951` (jedyny punkt NOT VERIFIED kroku 6); (b) decyzja o zapisaniu nowych
  plików w git (lokalny commit, bez push) — nic nie zostało zacommitowane.
