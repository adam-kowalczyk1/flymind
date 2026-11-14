# FlyMind — co dokładnie wykorzystujemy i jakie ścieżki rozwoju już istnieją (stan 2026-11-12)

Etykiety: VERIFIED = otworzyłem plik/dane i sprawdziłem dziś (2026-11-12); REPORTED = przepisane z dokumentu repo, nie sprawdzane dziś; INFERRED = mój wniosek; PROPOSED = pomysł. Ścieżki względem `/Users/admin/so101_fly_project/`. Nic nie uruchamiałem (tylko odczyt plików i jednorazowe zapytania do danych), niczego w repo nie zmieniłem.

## Q1. Jakie dane i jakie obwody (z liczbami)?

### Takeaway
FlyMind używa konektomu MaleCNS v1.0 (nie FlyWire), czyli trzech lokalnych plików (1,0 GB). Zbudowana sieć to 1931 neuronów (424 wzrok + 1507 noga) z 165 122 prześledzonych, czyli ok. 1,2%; zewnętrzne dane to tylko wagi (liczba synaps), typy komórek i przekaźniki.

### Cited Findings
- Dane: trzy pliki w `data/malecns/`: `connectome-weights-male-cns-v1.0-minconf-0.5.feather` (1 051 241 946 B; 151 856 684 krawędzi: body_pre, body_post, weight=liczba synaps), `body-annotations-male-cns-v1.0-minconf-0.5.feather` (14,5 MB), `body-neurotransmitters-male-cns-v1.0.feather` (43 MB; 1 835 518 wierszy). Daty plików 23 X 2026. VERIFIED — `ls -la data/malecns`, `flymind/connectome.py` linie 1–12.
- Próg pewności synaps minconf=0,5 jest zaszyty w nazwie pliku przez dostawcę; loader odmawia innego progu; „weight” to liczba synaps, nie siła fizjologiczna. VERIFIED — `flymind/connectome.py` (docstring, `load_edges`).
- W adnotacjach: 166 700 ciał z superclass, z czego status „Traced” = 165 122 (zgadza się z kontekstem „165 122”). VERIFIED — zapytanie pandas na `body-annotations…feather`, 2026-11-12.
- Liczby typów w danych (VERIFIED, to samo zapytanie): LC10a 275 neuronów (= 135 L + 140 P użyte w V5); DNa02 2; LC9 219; DNp09 2; DNp01 2; LPLC2 185; LC4 126; LPLC1 134; Kenyon cells (typy zaczynające się od KC) 4064; MBON 97.
- Sieć wzrokowa V5: wejście 135 (L) + 140 (P) LC10a → 147 neuronów pośrednich → 2 DNa02 (1 L + 1 P) = 424 neurony; `dna02_input_total` 49 357 synaps, z pośrednich 6 022 (ok. 12%); 0 bezpośrednich synaps LC10a→DNa02. VERIFIED — `flymind/results/v5/v5_confirm_20261028T220223.json` (klucz `network`), `flymind/FLYMIND_MASTER_CONTEXT.md` pkt 5.
- Obwód nogi: lewa środkowa noga T2 L, 1507 neuronów: receptory szczecinkowe 322; FeCO claw-EXT 9 / claw-FLEX 14, hook-EXT 8 / hook-FLEX 3; motoneurony goleni: prostownik 2, zginacze 11. Wzrok+noga razem = 1931 (424+1507) neuronów; DNa02 L ma 70 krawędzi z danych do interneuronów nogi. REPORTED (z dokumentów etapów) — `flymind/SENSORY_MANIPULATION_STAGE.md` §0, §2; `flymind/VISION_MANIPULATION_STAGE.md` §0, §2. Suma 424+1507=1931 sprawdzona arytmetycznie.
- Pilot ścieżki wzrok→noga: LC9 → DNp09 → przekaźniki VNC → obie środkowe nogi (`flymind/vision_leg.py`, commit `da2d43b`); pilot FJ2 (stawy 1–2), słabo sprawdzony. REPORTED — `FLYMIND_MASTER_CONTEXT.md` pkt 6, 7.
- D0 (analiza samych danych, PASS): mapy przestrzenne LPLC2→DNp04, LPLC1→DNp03/06/11 (R 0,67–0,81), LC4→DNp02/DNp11 antykorelowane; typy szczecinek → pule motoneuronów swoiste (S 0,12 wobec maks. 0,025 w 100 tasowaniach). REPORTED — `flymind/reports/fly_vs_vla_research_20261111.md` §2–§5; nie sprawdzałem plików wynikowych D0 dziś.

### Inferences
- „Ok. 1,2%” = 1931/165 122 = 1,17% (obliczenie własne, INFERRED z liczb powyżej).
- Wzrokowa i nożna część to dwa niewielkie, niezależnie wybrane podgrafy sklejone jednym punktem (DNa02 L → interneurony nogi); to dobór inżynierski, nie „jeden obwód muchy”.

### Gaps
- Kontekst podaje „340 DAN” — w danych mam 354 (typy PPL1/PAM/PPL2/PPM) lub 332 (tylko PPL1+PAM), zależnie od definicji; nie umiem potwierdzić 340. Kontekst „4064 Kenyon cells” i „97 MBON” potwierdzone.
- Kontekst podaje „płat wzrokowy ok. 54% neuronów”: superclass `ol_*` = 95 501 z 166 700 ciał (57%; 58% względem 165 122 prześledzonych; liczba ciał z superclass obejmuje też nieprześledzone). Wartość 54% niepotwierdzona; poprawne jest „ponad połowa” (INFERRED, dokładna definicja „neuron” do ustalenia).
- Nie sprawdziłem liczb synaps dla każdej pary typów (poza `network` V5); liczby obwodu nogi (322, 9/14/8/3, 2/11) pochodzą z dokumentu etapu, nie z ponownego zapytania.

## Q2. Model neuronu, symulator, biblioteki, testy, sprzęt

### Takeaway
Neurony to impulsowy ALIF (nieszczelny, z adaptacją) z parametrami ogólnymi, nie zmierzonymi dla tych komórek; krok 1 ms, takt sterowania 10 ms; fizyka w MuJoCo 3.17; Python z numpy/scipy/pandas/pyarrow. Sprzęt realnie poświadczony: MacBook M1 Max, jedno ramię SO-101 skalibrowane raz (nigdy niepodłączone do kodu FlyMind), FaceTime/iPhone Continuity; czujniki dotyku tylko w symulacji.

### Cited Findings
- Parametry ALIF: v_rest = v_reset = −52 mV, v_th = −45 mV, τ_m = 20 ms, τ_syn = 5 ms, t_ref = 2,2 ms, opóźnienie 1,8 ms, adaptacja τ_a = 300 ms, b_a = 0,5 mV, dt = 1 ms; parametry błony wg Shiu i in. 2024 jako „parametry modelu, nie pomiar tych neuronów”; adaptacja to wybór projektu. VERIFIED — `flymind/alif.py` linie 1–45.
- Waga = J0 × liczba synaps; V5 używa J0 = 0,2 mV/synapsę i szumu σ = 2 mV (tylko droga wzrokowa); obwód nogi bez szumu. REPORTED+VERIFIED w JSON (`J0` = 0.2 w `results/v5/v5_confirm_…json`) — `VISION_MANIPULATION_STAGE.md` §2.
- Reguły znaku: acetylocholina +1, GABA −1, glutaminian −1 (założenie modelu: GluCl hamuje, Liu & Wilson 2013); neuromodulatory (DA, 5HT, OA, HA) nie mają znaku i wymagają jawnej decyzji, więc nie działają. Źródło przekaźnika: ground_truth → consensus_nt → celltype_predicted_nt. VERIFIED — `flymind/snn_interface.py` linie 1–25. Znak Glu w nodze jest hipotezą (parametr `--glu`; test Glu +1 vs −1 daje oba 90/135 w benchmarku dotyku). REPORTED — `SENSORY_MANIPULATION_STAGE.md` §3; wynik 90/90 VERIFIED w `results/sensory_manipulation/B_fly_search_glu±1_v1.json`.
- Wejścia sensoryczne: kamera MuJoCo → enkoder koloru zielonej plamy (ten sam prąd do wszystkich LC10a jednej strony; heurystyka ENGINEERING); siła padów → szczecinki (40 mV/N, MODEL); kąt/prędkość szczęki → FeCO (liniowo). Wyjście: DNa02 L−P → obrót bazy; moment szczęki = 0,005 N·m/Hz × (prostownik − zginacze). REPORTED — `VISION_MANIPULATION_STAGE.md` §2, `SENSORY_MANIPULATION_STAGE.md` §2.
- Symulator: MuJoCo 3.17.0, timestep 0,001 s; `.venv`: numpy 2.5.4, scipy 1.18.1, pandas 3.1.0, pyarrow 26.0.0, matplotlib 3.11.2, pygame_ce 2.5.8; lerobot i torch nie ma w `.venv` (LeRobot w osobnym env miniforge). VERIFIED — `ls .venv/lib/python*/site-packages`, `flymind/so101.py:61`; `loop.py:54` (TICKS=300, DT=0.01 s).
- Czas obliczeń: od czujników do komendy mediana 1,2924 ms, p95 1,3327 ms (sieć nogi, 10 kroków ALIF ≈ 1,29 ms mediany) — to ten sam wynik, który kontekst podaje jako „1,29 ms”. VERIFIED — `flymind/results/sensory_manipulation/latency_v1_stdout.txt`; tabela w `SENSORY_MANIPULATION_STAGE.md` ok. l. 276–279. Dla pętli z kamerą: kamera→komenda mediana 5,8 ms, p99 7,6 ms (`VISION_MANIPULATION_STAGE.md` §0, `results/vision_manipulation/latency_v3.json`).
- Testy: 39 plików `test_*.py` w drzewie `flymind/` (find), z czego 31 w głównym katalogu; zwykle skrypty z „WSZYSTKIE TESTY OK”, nie pytest, więc „liczby testów” nie da się podać jedną liczbą (w trzech plikach jest 25 funkcji `def test_`). VERIFIED — `find`/`grep` dziś. Integralność (7 XI): „Stage 1 28/28; manifests 18/18, 18/18; protected files 377 … INTEGRITY OK”. REPORTED — `FLYMIND_MASTER_CONTEXT.md` pkt 11.
- Sprzęt: MacBook Pro M1 Max 32 GB; jedno ramię SO-101 follower (serwa ID 1–6) skalibrowane 1 X, „nigdy nie było podłączone do kodu FlyMind”, brak leadera; kamery: FaceTime HD i iPhone Continuity; OV9281 (ok. 50 USD) tylko zalecona; 4× FSR tylko zalecone; nieznane: przełożenia serw, zasilacz, kamera zewnętrzna. REPORTED — `FLYMIND_MASTER_CONTEXT.md` pkt 4 (stan 7 XI); nie sprawdzałem fizycznie. Pad Xbox → `pad_so101/` jest przetestowany tylko offline.
- Git: gałąź `flymind/fly-first-control`, 39 commitów, HEAD `664b611` (10 XI 2026); 147 wpisów w `git status` (głównie nieśledzone wyniki i skrypty; etap wzroku niezacommitowany). VERIFIED dziś — `git log`, `git status --short`. Brak zdalnego repo/off-machine (REPORTED, 7 XI).

### Inferences
- Wszystkie liczby 1,29 ms i 5,8 ms to czas obliczeń modelu na laptopie, nie opóźnienie na prawdziwym ramieniu ani biologiczne (INFERRED).
- „Mózg muchy” to nadużycie: dynamika jest ogólna, nie dopasowana do komórek (INFERRED z `alif.py`).

### Gaps
- Nie wykonałem testów (zakaz uruchamiania), więc „ile testów przechodzi” nie jest potwierdzone dziś; są tylko logi (`results/object_handling/tests_v2.log`: „WSZYSTKIE TESTY OK”).
- Stan sprzętu po 7 XI nieznany bez potwierdzenia Adama.

## Q3. Wyniki eksperymentów — przeliczone z plików

### Takeaway
Wszystkie liczby kontekstu, które sprawdziłem w plikach JSON/stdout, się zgadzają. Obwód z danych steruje obrotem bazy (38/40) i szczęką (90/135), ale klasyczny kod jest lepszy lub równy, a przetasowane sieci o tej samej sile osiągają 4–102, więc wynik nie dowodzi roli konkretnych połączeń.

### Cited Findings
- V5 (pętla wzrok → obrót bazy, ziarna potwierdzające, opóźnienie 0): sieć z danych 38/40; tasowanie 3/40; zamiana stron („mirrored/swap”) 0/40; bez wzroku 0/40; regulator P 40/40. VERIFIED — `flymind/results/v5/v5_confirm_20261028T220223.json` (80 przebiegów snn: opóźnienie 0 → 38/40, opóźnienie 5 → 17/40). W kontekście brak informacji o wariancie z opóźnieniem 5 (17/40).
- Dokładność: P dokładniejszy o 1,2°; „tasowanie z dopasowaną siłą 10/10 → wynik pokazuje lateralizację, nie topologię”; P lepszy od SNN w 446/450 parach. REPORTED — `FLYMIND_MASTER_CONTEXT.md` pkt 7 (V5, porównanie z P). To oznacza, że w kontekście „shuffle strength-matching NOT VERIFIED” — plik master mówi, że kontrola zachowująca siłę dała 10/10 (czyli mechanizm lateralizacji); nie otworzyłem pliku z tą kontrolą (`results/v5_mech_strength/`).
- Chwyt, miękki kontakt, 135 prób (te same przedmioty): klasyczny 93/135 (`object_handling/B_base_v2.json`); sieć dotyku (Glu −1 i +1) 90/135 każda (`sensory_manipulation/B_fly_search_glu-1_v1.json`, `…glu+1_v1.json`); prosty odruch 80/135 (`D_reflex_search_v1.json`); sieć + FeCO 83/135 (`C_fly_feco_search_v1.json`); sieci przetasowane (3 niedopasowane) 74/49/82; bez wyjścia sterownika 0/135 (`C_no_touch_search`, `N_null_search`). VERIFIED.
- Sztywny kontakt: klasyczny 101/135 (`results/contact_audit/stiff_A_v1.json`), sieć 84/135 (`stiff_B_v1.json`). VERIFIED.
- 10 tasowań z dopasowaną siłą (ziarna 17100011–17100020) w pudełku: 101, 82, 80, 102, 83, 79, 82, 79, 99, 4 z 135 — dokładnie zgadza się z kontekstem; sieć z danych 90. VERIFIED — `results/shuffle_matched/shuffle_*_v1_stdout.txt`. Uwaga: skalowania k od 1,49 do 9,05 (jedno tasowanie wymagało k = 9,05 i dało 4/135); plik `shuffle_1.71e+07_v1_stdout.txt` to nieudane uruchomienie (błąd parsowania ziarna) — jest w katalogu wyników.
- Wzrok + dotyk (kamera zamiast wyroczni, 135 prób): klasyczny 98 (`A_cam_v3`), sieć wzrok+dotyk 86 (`E_vis_touch_v3`), sieć sam dotyk 85 (`B_cam_v3`), sieć z wyłączonym wzrokiem w chwycie 86 (`E_blind_grasp_v3`), sieć + FeCO 80 (`F_vis_touch_feco_v3`), sam wzrok 0 (`D_vis_v3`, chwyt 128/135 ale 0 podniesień). VERIFIED. 18 prób wygrywa tylko klasyczny, 6 tylko sieć: REPORTED (`VISION_MANIPULATION_STAGE.md` §0).
- Śledzenie przedmiotu (20 scen × 8 warunków): `tracking_snn_swap_v3` zamiana stron 1/20 sukcesów (kontekst: 1/20), `tracking_snn_v3` i `tracking_classical_v3` — policzone z JSON: klasyczny gorszy tylko w „loss” (5/20); sieć słabsza w loss (4/20), rotate (14/20), occl_push (15/20). VERIFIED — `results/vision_manipulation/tracking_*_v3.json` (obliczenie dziś).
- Błąd percepcji (klasyczna geometria z kamery, nie sieć): pozycja mediana 0,09 mm, p95 5,8 mm (A_cam_v3_stdout). VERIFIED.
- Wcześniejsze: FJ1 chwyt 12/12 bez przewagi nad odruchem 12/12 (commit `ccc19d7`); FJ2 pilot — chwytak zbliża się do piłeczki 71→17 mm, brak sygnału „podnieś”; kandydat T2L→T2R wycofany po red teamie (commit `54155d4`). REPORTED. F1 aktywne patrzenie: linia zamknięta 2 XI. REPORTED.
- Czego dziś NIE potwierdziłem: V5 v2/v3/v4 (28/50, DATA−SWS −0,19°, 4001–4450), program V5 v4.1→V6m3, κ, Etap 0 — tylko z `FLYMIND_MASTER_CONTEXT.md` (REPORTED).

### Inferences
- Poprawne zdanie dla jury: „sieć z danych daje wynik porównywalny z klasycznym kodem w symulacji, ale to samo daje wiele przetasowanych sieci o tej samej sile, więc nie wykazaliśmy, że liczą połączenia” (INFERRED z 101/82/80/102/83/79/82/79/99/4 vs 90).
- Zadanie chwytu sprowadza się do progu momentu (FJ1, REPORTED), co tłumaczy brak przewagi nad odruchem.

### Gaps
- Brak jakiegokolwiek testu na prawdziwym ramieniu.
- „Shuffle strength-matching NOT VERIFIED” z kontekstu dotyczy V5 (wzrok); dla chwytu (10 tasowań, k-skalowane) jest zweryfikowane — to dwie różne kontrole, nie mieszać.

## Q4. Czego świadomie nie używamy i dlaczego to ważne

### Takeaway
Poza siecią zostaje ponad połowa mózgu (płat wzrokowy), cały układ uczenia (grzybki) i neuromodulatory. Dlatego „widzenie” to heurystyka koloru, sieć niczego się nie uczy, a nie ma stanów wewnętrznych — to wprost granica twierdzeń na plakacie.

### Cited Findings
- Płat wzrokowy zastąpiony enkoderem koloru: encoder → ten sam prąd do wszystkich LC10a jednej strony; Adam 12 XI uznał to za sztuczne pobudzanie wybranych neuronów, więc V5 jest „wynikiem pętli”, nie „mucha widzi cel”. VERIFIED w dokumencie — `flymind/reports/fly_eye_plan_20261112.md` l. 12; `flymind/reports/bio_vision_20261112.md` §10.
- Układ uczenia: 4064 Kenyon cells, 97 MBON w danych, nieużywane; dziś „sieć nie uczy się niczego”. VERIFIED liczby (zapytanie), REPORTED stan — `fly_learning_research_20261112.md` pkt 2, l. 236.
- Neuromodulatory (DA, 5HT, OA, HA) bez znaku, więc bez wpływu: VERIFIED — `flymind/snn_interface.py` l. 22–24 (dodatkowo `brain_unity_vs_ai_20261112.md` l. 218).
- Nieużyte też: obciążenie/poślizg (sensilla kampaniformalne, brak drogi do MN goleni w danych), FeCO „club”, sygnały „podnieś/zanieś/puść” (brak w danych → klasyczne rusztowanie), kopia eferentna. REPORTED — `SENSORY_MANIPULATION_STAGE.md` §1, §3.
- Ramię: oprócz obrotu bazy (staw 0) i szczęki (staw 5) wszystkie stawy planuje klasyczne rusztowanie (dojazd, podniesienie, transport, puszczenie); położenie przedmiotu z kamery liczy klasyczna geometria, nie sieć. REPORTED — `VISION_MANIPULATION_STAGE.md` §2; `FLYMIND_MASTER_CONTEXT.md` pkt 6.

### Inferences
- Zgodnie z regułą Adama z 3 XI „mucha ma decydować” — dziś decyduje tylko o 2 z ~6 rzeczy (obrót bazy, siła zacisku); to trzeba mówić wprost (INFERRED).

### Gaps
- Nie ustaliłem, ile procent wejścia do DNa02/DNp09 pochodzi spoza wybranych podsieci (poza „ok. 12% z pośrednich DNa02”).

## Q5. Zaproponowane dalsze kroki i status (stan 12 XI; wszystko poniżej: nic nie uruchomiono)

### Takeaway
Wszystkie propozycje z raportów 10–12 XI mają status „czeka na Adama” (każdy raport kończy się „STOPPED AT CHECKPOINT 1 — awaiting Adam's approval”). Jedyną przyjętą decyzją 12 XI jest: encoder koloru → LC10a uznany za sztuczne pobudzanie i „Yes, plan fly eye” (zatwierdzony plan na papierze, nie uruchomienie).

### Cited Findings
- **Decyzja podjęta 12 XI:** encoder koloru → LC10a = sztuczne pobudzanie; wynik V5 zostaje prawdziwy jako wynik pętli; plan oka muchy zatwierdzony na papierze. VERIFIED — `fly_eye_plan_20261112.md` l. 3, 12.
- **Plan oka (O0–O6)** — status: plan zatwierdzony, żaden krok niezatwierdzony do uruchomienia. O0 mapa kolumn (tylko dane), O1 optyka (pole widzenia opcje a/b/c), O2 fotoreceptor, O3 rdzeń ruchu (1,16 mln niezerowych wag, 47–48 tys. neuronów, szybkość nieznana), O4 LPLC2/LC4 (etap 1) i LC10a + 28 typów (etap 2), O5 DNp01 „stop/cofnij” / DNa02, O6 ramię + bezpieczeństwo; bramki G2 (kierunkowość T4/T5; **STOP** jeśli brak) i G3. Decyzje Adama: (1) kolejność LPLC2/LC4→DNp01 potem LC10a, (2) opcja pola widzenia O1, (3) czy wolno dopasowanie parametrów, jeśli G2 nie przejdzie, (4) zgoda na O0 jako pierwszy krok, (5) zgoda na pomiar kosztu `bench_loop.py`, (6) zakres dema 1 XII. — `fly_eye_plan_20261112.md` §3–§7, l. 78–110, 123–131.
- **E1** (refleks mapy przestrzennej w pętli: LC4→DNp02/DNp11 + LPLC2→DNp06/giant fiber; metryka nie-kołowa, ≥20 tasowań z własnym znakiem i wzmocnieniem, ~200 par scen) — czeka; **E2** (czy chwyt to tylko krzywa siła→moment; ok. 1 dzień) — czeka; **E3** (czas małego VLA na tym Macu, wymaga pobrania wag) — czeka. Decyzja: zgoda na napisanie rejestracji wstępnej E1+E2 (sam dokument); uruchomienie to osobna zgoda; E1 wymaga zgody najpóźniej ok. 17 XI na wynik po red teamie przed 1 XII. — `fly_vs_vla_research_20261111.md` §10, §12 (l. 363–410, 432–434).
- **P1–P7** (raport o uczeniu): P1+P2 dwie analizy samych danych (ok. 1,5 dnia) i P7 krok 1 (odczyt istniejących wyników ablacji V5 i serii z opóźnieniami) — czekają; decyzje: uczenie w modelu jako plan na 2027 czy odrzucić; czy „tłumacz T1” (zmysły + moduł językowy decydujący o celu) mieści się w zasadzie 3 XI. — `fly_learning_research_20261112.md` §13 (l. 620–632).
- **W3 / S1–S7** (VLA z muchą w środku: mucha steruje wszystkimi stawami, kora/VLM tylko wskazuje cel lub moduluje czułość oka): czeka; decyzje: czy W3 jako plan na Explory 2027; czy kanał K1 (kora zmienia czułość oka) mieści się w zasadzie; czy dopuszczalne uczenie interfejsów T1/T2; zgoda na papierowe S1–S3; czy schemat na plakat jako „kierunek”; wybór kamery mono/kolor. — `vla_with_fly_design_20261112.md` §13 (l. 448–459).
- **U1–U5** (mózg jako jeden organizm: stan wewnętrzny/allostaza; U2 = wolna zmienna skalująca czułość oka — sporne wobec zasady 3 XI): niezatwierdzone; decyzje: zgoda na samą rejestrację U1 (bez uruchamiania), rozstrzygnięcie U2 (ta sama kwestia co K1), czy zdanie z pkt 5.1 trafia na plakat. — `brain_unity_vs_ai_20261112.md` §12 (l. 379–388).
- **R1–R4** (rewolucja w AI robotów): R1 = zmiana głównego pytania na „czy połączenia mają znaczenie w pętli”; R2 = dodanie sygnału (kopia eferentna) do sieci; decyzje: zmiana pytania; analiza danych pod kopię eferentną LC10a→DNa02; tabela FlyMind/VLA/VFA na plakat. — `robot_ai_revolution_20261112.md` l. 145–160.
- **Wzrok biologiczny (bio_vision):** otwarta decyzja o encoderze została rozstrzygnięta 12 XI (patrz wyżej); pozostają: plan oka (tu), mały wariant „zbliżanie→stop” (LPLC2/LC4→giant fiber), jedno zdanie na plakat: „wejście wzrokowe to dziś heurystyka koloru, nie oko muchy”. — `bio_vision_20261112.md` l. 175–190.
- **Baza wektorów ruchu:** tryby A (analiza porażek i porównanie sterowników, rekomendacja startowa), B (filtr danych do uczenia), C; decyzje: wybór trybu, specyfikacja wpisu, spis logów, czy wolno użyć cudzego zbioru `so101_lego_drop_real_50` (licencja niesprawdzona). — `motion_vector_db_20261112.md` l. 120–135.
- **Raport z 10 XI (bio_advantage_research):** D0 PASS wykonane; S1/S2 niezatwierdzone (wchłonięte przez E1/E2); czeka decyzja na plan z pkt 10. REPORTED — `bio_advantage_research_20261110.md` l. 35–37, 447.
- **Starsze otwarte decyzje (7 XI, REPORTED):** pokaz 1 XII na prawdziwym ramieniu czy tylko symulacja; commit ok. 130 nieśledzonych plików (częściowo wykonany: `664b611`, etap wzroku jeszcze nie); kopia poza komputerem (Adam odmówił 2 XI); Etap N (neuron-variant 2×2) po pokazie. — `FLYMIND_MASTER_CONTEXT.md` pkt 9, 10.
- Terminy: plakat 16 XI 2026; rejestracja projektu ok. 17 XI (do potwierdzenia); festiwal 1 XII 2026. REPORTED — `FLYMIND_MASTER_CONTEXT.md` pkt 3.

### Inferences
- Realistyczne do 1 XII (INFERRED z własnych szacunków w raportach): analizy samych danych (O0, P1, P2, D-type), rejestracje wstępne (E1/E2), ewentualnie E2 (1 dzień) i E1 tylko przy zgodzie przed ok. 17 XI; uczenie, VLA z muchą, U1–U5, W3 → Explory 2027.
- Najważniejsza, najtańsza zmiana na plakat: uczciwa tabela „co jest z muchy, co klasyczne” i zdanie o heurystyce koloru (oba proponowane w kilku raportach).

### Gaps
- Nie ma pliku „rejestru decyzji” — status wywnioskowany ze stopki każdego raportu i z `fly_eye_plan_20261112.md`; MEMORY wymienia te same pozycje jako niezatwierdzone. Jeśli Adam zatwierdził coś ustnie po 12 XI rano, nie ma tego w repo.
- Nie czytałem w całości raportów `fly_learning` (632 linie), `vla_with_fly_design` (459), `brain_unity` (388) — tylko sekcje decyzji i wyszukiwane fragmenty; ich cytowane prace (np. arXiv 2601.22153, DOI Sterling 2012) to REPORTED w tych raportach, nie sprawdzane tu.
