# Niezależna weryfikacja stanu projektu FlyMind / SO-101 (lokalny kod i dane, tylko odczyt)

Data: 2026-11-03 (HEAD `54155d4`, gałąź `flymind/fly-first-control`). Metoda: czytanie kodu i plików wyników oraz proste, tylko-odczytowe przeliczenia w Pythonie (`.venv/bin/python -I`, skrypty w scratchpadzie, nic nie zapisane w projekcie). NIE uruchamiałem symulacji, testów, generowania ziaren ani git-ów zmieniających stan. Źródła = ścieżki lokalne (brak URL-i); odniesienia do literatury przytaczam WYŁĄCZNIE tak, jak podają je pliki projektu — nie sprawdzałem ich w internecie.

Legenda werdyktów: POTWIERDZONE / CZĘŚCIOWO POTWIERDZONE / NIEZWERYFIKOWANE / SPRZECZNE.

---

## 1. Model konektomu: zbiór danych, lokalizacja, ekstrakcja, liczba neuronów, model neuronu, wagi, znaki

### Takeaway
Dane to MaleCNS v1.0 (Janelia, samiec), a nie FlyWire; leżą lokalnie w `data/malecns/` (3 pliki feather, 1,0 GB). Sieć sterująca obrotem to 424 neurony (275 LC10a + 147 pośrednich + 2 DNa02), wszystkie krawędzie z danych, ALIF w kroku 1 ms, wagi LINIOWE `J0·N_syn` ze znakiem wg przekaźnika (J0 = 0,2 mV/synapsę) — a znak glutaminianu (−1) jest założeniem modelu, nie daną.

### Cited Findings
- **Zbiór = MaleCNS v1.0, nie FlyWire — POTWIERDZONE.** Pliki: `data/malecns/body-annotations-male-cns-v1.0-minconf-0.5.feather` (211 577 ciał — odczytałem długość tabeli = 211 577), `body-neurotransmitters-male-cns-v1.0.feather` (1 835 518 wierszy), `connectome-weights-male-cns-v1.0-minconf-0.5.feather` (1 051 241 946 B, 151 856 684 krawędzi wg `flymind/connectome.py:1-12`). Daty plików 23.10.2026. Raporty (`reports/Projekt mózgu muchy dla inwestorów.md` l. 38) poprawnie piszą „MaleCNS, nie FlyWire”.
- **Liczba neuronów 424 — POTWIERDZONE.** `flymind/results/v5/v5_confirm_20261028T220223.json`, klucz `network`: `sizes` = in_L 135, in_R 140, mid 147, DNa02_L 1, DNa02_R 1 (=424), `edges.edges` = 13 510, `synapses` = 113 969, `bodies` = 424, `build.model.edges` = 0 (brak krawędzi modelowych, „tylko dane”). Zgodne z `flymind/VALIDATION_PLAN.md:431-434`. Weryfikacja niezależna: w annotations jest 275 neuronów typu `LC10a` (arytmetyka 135+140 zgadza się).
- **Dobór 147 pośrednich = kryterium progowe, nie „obwód znany z literatury” — POTWIERDZONE (z zastrzeżeniem).** Kryterium: ≥ 5 synaps od LC10a i ≥ 5 do DNa02, z przekaźnikiem (`VALIDATION_PLAN.md:433`). Najliczniejsze typy: LLPC1 43, AOTU015 8, AOTU001 7 … (`v5_confirm…json`, `network.mid_types`). Pośrednie dają tylko 12 % wejścia DNa02 (6022/49 357; plik wyników potwierdza `dna02_input_from_mid` = 6022, `dna02_input_total` = 49 357). Sieć NIE zawiera reszty wejść DNa02 (88 %).
- **Neuron ALIF — POTWIERDZONE.** `flymind/alif.py:19-35`: V_rest = V_reset = −52 mV, V_th = −45 mV, τ_m = 20 ms, τ_syn = 5 ms, t_ref = 2,2 ms, opóźnienie 1,8 ms, adaptacja τ_a = 300 ms, b_a = 0,5 mV, dt = 1 ms. Plik sam zaznacza: membrana „jak Shiu i in. 2024”, adaptacja „wybór projektu bio2… brak danych dla tych neuronów”. Kwantyzacja refrakcji → r_max = 250 Hz (`alif.py` docstring, l. 7-8) — realne ograniczenie przy dużych częstościach.
- **Wagi: synapsy → mV — POTWIERDZONE, z istotną niespójnością między generacjami kodu.** `flymind/snn_interface.py:28-31,107`: `W = sign · J0 · f(N_syn)`, gdzie f domyślnie liniowa. Przebieg V5 używa `transform: linear`, `J0: 0.2` (`v5_confirm…json`, `network.build.params`). Natomiast starsze `RESULTS.md:27` i `bio2/snn.py:43-45` mają `W = sign · J0 · ln(1+N_syn)` (v1–v3); `bio2/snn.py:8` sam zaznacza, że Shiu i in. używają wagi liniowej (0,275 mV/synapsę). Raport nasze_wyniki.md podaje wzór z ln dla całego systemu — to jest poprawne tylko dla `sim/` i `bio2/`, NIE dla `flymind/` (który wyniki V5–V6 produkuje na wadze liniowej). Liczba synaps NIE jest siłą fizjologiczną (`snn_interface.py` docstring, `bio2/MALECNS_DATA_AUDIT.md` §1 pkt 1).
- **Rozmiary starszych sieci — POTWIERDZONE.** `sim/circuit_malecns.json`: 332 neurony, 6932 krawędzi; suma wag krawędzi przeliczona = 53 766 (zgadza się z `RESULTS.md:4`). `bio2/circuit_bio2.json`: 272 neurony, 9252 krawędzi (nie 220+72, jak sugeruje opis w nasze_wyniki.md — 220+72 = 292 ≠ 272; NIE rozstrzygnąłem, skąd ta różnica, możliwe że pierścień 16 neuronów liczony osobno: 272+16+… — NIEZWERYFIKOWANE).
- **Znak neuroprzekaźników — CZĘŚCIOWO POTWIERDZONE.** `snn_interface.py:22-24`: `DEFAULT_SIGN = {acetylcholine: +1, gaba: −1, glutamate: −1}`; komentarz: „Założenie modelu (nie dane): Glu hamuje w OUN owadów przez GluCl (Liu & Wilson 2013)”. Źródła przekaźnika w sieci 424: ground_truth 323, consensus_nt 101 (`v5_confirm…json`). Kod odmawia budowy przy neuronach bez przekaźnika lub z przekaźnikiem spoza `sign_map` (`snn_interface.py:55-58,76-79`) — dobra praktyka. Neuromodulatory (DA, 5HT, OA, HA) nie mają znaku, wymagają jawnej decyzji. Pozostaje problem merytoryczny: znak Glu (±1) jest nierozstrzygnięty fizjologicznie dla neuronów ruchowych nogi — projekt to sam przyznaje (memory `flymind-d1-audit-2026-11-03.md`; `PILOT_NOTES.md`: „Glu −1 at leg MNs = reasonable default… no physiology”). W torze LC10a→DNa02 (V5) problem Glu jest mniejszy, bo kluczowe typy to ACh (LC10a, AOTU025, DNa02) i GABA (AOTU019) — sprawdziłem: wszystkie 275 LC10a i 2 DNa02 mają `consensus_nt` = acetylocholina; 2 AOTU019 = GABA; 2 AOTU025 = ACh (ground_truth dla AOTU025 = NaN, więc znak z predykcji).
- **Model SNN jest „wycinkiem połączeń”, nie „mózgiem muchy” — POTWIERDZONE.** Docstring `flymind/demo/demo.py` i nagłówki raportów powtarzają to; sieć 424 z ok. 166 tys. neuronów mózgu. Enkoder (detektor koloru → L−R), dekoder (DNa02 L−R → ω), kalibracja i filtr τ = 0,1 s to inżynieria (`REPRODUCE.md` tabela warstw; `v5_confirm…json` `steer`: gain 2,5, w_max 1,0).

### Inferences
- „Sieć z konektomu” w V5 to właściwie: wejściowy kontrast L−R → LC10a → bogato połączony podgraf → różnica DNa02 L−R, z dekoderem skalibrowanym ręcznie. Ilość „biologii” w decyzji jest niska, bo kluczowa jest lateralizacja (zob. §3).
- W materiałach zewnętrznych trzeba rozróżniać trzy generacje (sim/ 332 + 20 model, bio2/, flymind/ 424) i dwie reguły wag (ln vs liniowa) — dziś te opisy są mieszane.

### Gaps
- Nie przeliczyłem składu przekaźników całej sieci 424 (ile neuronów Glu); nie uruchamiałem `visual_path.select`.
- Nie zweryfikowałem w internecie, czy dla MaleCNS v1.0 istnieje publikacja (raport inwestorski l. 9 mówi o Cell, 3 IX 2026) ani dokładnych liczb neuronów (164 838–166 691 w raporcie VLA) — spoza zakresu lokalnego.

---

## 2. Obwód LC10a → DNa02: bezpośredni czy przez neurony pośrednie? (przeliczone z danych)

### Takeaway
Pośredni, nie bezpośredni: w danych MaleCNS jest 0 bezpośrednich synaps LC10a→DNa02. Droga prowadzi przez AOTU019 (GABA) i AOTU025 (ACh), a także przez ok. 147 innych neuronów pośrednich (m.in. LLPC1) — struktura „push-pull” potwierdza się liczbami.

### Cited Findings
- **LC10a → DNa02 bezpośrednio: 0 krawędzi, 0 synaps — POTWIERDZONE (przeliczone).** Odczyt tylko-do-odczytu `connectome-weights…feather` filtrem `body_pre ∈ LC10a (275)`, `body_post ∈ DNa02 (2)`: 0 wierszy. Zgodne z opisem „LC10a→AOTU019/025→DNa02” w `RESULTS.md` / nasze_wyniki.md i z architekturą 424 (potrzebne neurony pośrednie).
- **LC10a → AOTU019: 206 krawędzi, 14 210 synaps; LC10a → AOTU025: 156 krawędzi, 7031 synaps — przeliczone.** AOTU019 (2 neurony: _L, _R) → DNa02 (2 krawędzie): 586 synaps; AOTU025 (2 neurony) → DNa02 (2 krawędzie): 401 synaps. Cytowane w nasze_wyniki.md „AOTU019_P→DNa02_L 297; AOTU025_L→DNa02_L 205” są spójne rzędem wielkości z sumami 586 / 401 (nie rozbijałem na pary). Rozbicie „LC10a_P→AOTU019_P 7595” NIEZWERYFIKOWANE co do pary, ale suma 14 210 (L+R) jest zgodna.
- **Znaki — POTWIERDZONE.** AOTU019 = GABA (ground_truth, 2/2), AOTU025 = ACh (consensus_nt; ground_truth puste), LC10a i DNa02 = ACh (ground_truth 275/275 i 2/2). Zgadza się z opisem „push-pull”: hamowanie przez AOTU019, pobudzanie przez AOTU025.
- **Udział LC10a w wejściach DNa02:** DNa02 ma łącznie 49 357 synaps wejściowych (zgodne z `dna02_input_total`); największe typy wejściowe to AN03A008 1458, PS049 1020, PS059 998, AN04B003 764, PFL3 736 — czyli LC10a-pośrednie to niewielki ułamek; sieć modeluje ok. 12 % wejścia (6022). To ważne ograniczenie: „obwód skrętu” w modelu jest wąskim podzbiorem tego, co karmi DNa02.
- **Największe wyjścia LC10a (liczone przeze mnie):** LC10a (25 244, samo-połączenia), TuTuA_2 23 354, AOTU008 16 114, AOTU041 14 304, AOTU019 14 210, LC10d 13 852, LT52 12 858 … — AOTU019 jest silnym, ale nie jedynym celem. Wybór AOTU019/025 jako „obwodu” jest więc uproszczeniem (projekt rozszerzył go do 147 pośrednich).
- **Zgodność z literaturą:** projekt powołuje się na Collie i in. (pościg, push-pull LC10a–AOTU–DNa02, samica FlyWire) oraz Ribeiro 2018 (LC10a) jako źródła porównawcze (`RESULTS.md` „Z literatury”). NIEZWERYFIKOWANE przeze mnie w literaturze (brak sprawdzenia w sieci); mogę stwierdzić tylko, że liczby w danych samca są spójne z opisem struktury podanym przez projekt.

### Inferences
- Skoro bezpośrednio 0, a pośredni dostarczają 12 % wejścia DNa02, niezależne od LC10a wejścia (88 %) mogą dominować w żywej muchie; model odtwarza tor, nie pełną funkcję DNa02. Nie wolno mówić „LC10a steruje DNa02” bez dopisku „przez AOTU019/025 i ok. 147 neuronów, w modelu”.

### Gaps
- Nie rozbijałem na L/R-pary; nie sprawdzałem funkcjonalnie (to tylko anatomia, nie dowód zachowania — `bio2/MALECNS_DATA_AUDIT.md` §1 pkt 3 to sam przyznaje).

---

## 3. Testy MuJoCo: SNN vs przetasowana vs klasyczny P (liczby z surowych wyników)

### Takeaway
Liczby 38/40 vs 3/40 vs 0/40 vs 40/40 oraz mediany błędu 0,16° (P) vs 1,41° (SNN) odtwarzają się DOKŁADNIE z surowych danych. Interpretacja jest jednak słabsza niż w pitchu: sukces SNN wynika głównie z lateralizacji, regulator P jest dokładniejszy, a V5 v4 pokazuje efekt topologii o wielkości ≈ progu 0,5° i zmiennym znaku. Jedno zdanie w raporcie V5 v4 („P lepszy w 450/450 parach”) nie zgadza się z surowymi danymi (446/450).

### Cited Findings
- **V5 potwierdzenie (ziarna 2011–2050, n = 40) — POTWIERDZONE.** Przeliczyłem z `flymind/results/v5/v5_confirm_20261028T220223.json` (240 przebiegów; kryterium `|e|<5°` przez ostatnie 0,5 s, zgodnie z `loop.py:metrics`): snn 38/40, snn_shuffle 3/40, snn_swap 0/40, no_vision 0/40, classical_p 40/40, snn przy opóźnieniu 50 ms 17/40. Mediana końcowego |e|: snn 1,41°, P 0,16°, swap 59,57°, no_vision 19,98° (zgodne z `analysis_confirm.json`; mediana shuffle w moim przeliczeniu 16,94° vs 16,35° w raporcie — różnica wynika z definicji okna uśredniania, nieistotna). Wilson 95 %: snn 0,835–0,986 (zgodne z VALIDATION_PLAN.md:473).
- **Opóźnienie 50 ms (17/40) — warunek ZAKŁÓCONY** (wykryte po przebiegu): 3600 taktów z flagą `vision_stale`, bo `max_age`=0,05 s leży na granicy (`VALIDATION_PLAN.md:~478-482`). Jest to opisane w planie; raport VLA (`nasz_kod_przelacznik.md` l. 44, 89) cytuje 17/40 z zastrzeżeniem — OK. Wynik 7/20 vs 20/20 przy 100 ms to eksploracja, a przy 100 ms KAŻDA klatka jest „stale” (red team `v4_v5_redteam.md:75`) — czyli to w dużej mierze test polityki odrzucania klatek, nie wrażliwości sieci.
- **Co „przetasowana” oznacza — CZĘŚCIOWO WAŻNE.** `visual_path.shuffle` (`flymind/visual_path.py:71-93`) to podwójna zamiana krawędzi (zachowuje stopnie), ale NIE zachowuje lateralizacji ani, domyślnie, siły wejściowej; `equal_weight=True` dodano po red teamie. Dlatego 3/40 dowodzi, że rozbicie okablowania psuje działanie, nie że „właśnie topologia muchy” jest potrzebna. `VALIDATION_PLAN.md:205-206`: „nie wykazano, że jej topologia ponad lateralizację ma znaczenie”.
- **V5 v2 (ziarna 2051–2100, n = 50) — POTWIERDZONE.** `flymind/results/v5/analysis_v5v2_confirm.json`: snn 28/50, snn_eqshuffle 20/50, snn_dnperm 9/50, toy_relay 22/50, classical_p 50/50, no_vision 9/50. Test H2 (snn vs eqshuffle): 8 vs 0 par rozbieżnych, p = 0,0078, różnica 0,16, CI 0,06–0,26 — „na krawędzi czułości”. Zwraca uwagę rozkład po odległości: w pasie ρ 0,30–0,35 m wszystkie sieci (też snn) osiągają tylko 3/15 (poziom no_vision) — „martwa strefa”, P tam 15/15.
- **V5 v4 (ziarna 4001–4450, 2700 prób) — POTWIERDZONE co do liczb, jedno SPRZECZNE zdanie.** Z `results/v5v4/raw_v5v4_{A,B}.jsonl` (450 ziaren × 6 warunków, 0 błędów): średni błąd końcowy DATA 2,88° (mediana 1,95°), SWS 3,05°, STR_OWN 4,26°, STR_SHARED 5,66°, TOY 4,31°, P 0,20° (mediana 0,18°); sukces DATA 352/450, SWS 336/450, STR_OWN 282/450, STR_SHARED 227/450, TOY 282/450, P 450/450. Różnica DATA−SWS: S1 (150 prób) +0,512°, S2 (300 prób) −0,518° — identyczna z `V5v4_FINAL_REPORT.md:§7` (zmiana znaku z odległością, wielkość ≈ SESOI 0,5°). Raport sam pisze (§8): „nie jest to twierdzenie o mózgu muchy”.
  - **SPRZECZNE (drobne):** `V5v4_FINAL_REPORT.md:63` „regulator P lepszy w 450/450 parach”. Z `final_abs_err` w surowych plikach P jest lepszy w 446/450 (wyjątki: ziarna 4309, 4315, 4411, 4425, gdzie DATA ma mniejszy końcowy błąd). Zgodne jest „348 o > 1°” (przeliczone 348). Być może raport użył innej miary błędu; nie znalazłem tego obliczenia w `v5v4.py` ani `audit_independent.txt`. To drobna nieścisłość, ale w raporcie o „uczciwości” warto ją poprawić.
- **Hierarchia dowodowa — zgodna z VALIDATION_PLAN:** w zadaniu nakierowania kamery regulator P (klasyczny) wygrywa dokładnością i niezawodnością w każdym teście (40/40, 50/50, 450/450~446/450). Projekt to otwarcie przyznaje (VALIDATION_PLAN, raporty). To uczciwa część i nie jest błędem.
- **Wyłącznie symulacja — POTWIERDZONE.** Wszystkie wyniki z MuJoCo (`so101.py`, `loop.py`); kamera „eye” renderowana; „Błąd e z prawdy symulatora — TYLKO do oceny” (`loop.py:1-10`).
- **Statystyka niezależności:** red team V5 v4 dotyczył PROTOKOŁU (r1 NOT READY → r2 READY → r3 READY); „Niezależnego Red Teamu WYNIKÓW nie przeprowadzono” (`V5v4_FINAL_REPORT.md:§4`); reanaliza to druga implementacja analizy (`audit_v5v4_independent.py`) przez tę samą rodzinę modeli. „Red team” = osobna instancja modelu, nie ludzki recenzent (raport sam tak pisze).
- **Zużycie ziaren:** pule 2001–2100, 3001–3100, 4001–4450 zużyte (`NEXT_SESSION.md:6`); brak wolnej puli potwierdzającej.

### Inferences
- Zdanie z pitchu „Gdy przetasuję połączenia, tylko w 3 z 40” jest PRAWDZIWE jako liczba, ale mylące jako dowód swoistości: w V5 v2 przetasowanie z zachowaniem siły dało 20/50 (vs 28/50), a główną część efektu tłumaczy lateralizacja.
- Poprawne ujęcie: „w symulacji sieć z danych nakierowuje kamerę w 38/40; klasyczny P robi to lepiej; przewaga konkretnej topologii jest mała (≈ 0,5°) i zależna od odległości”.

### Gaps
- Nie uruchamiałem żadnej symulacji, więc zgodność wyników z kodem co do bajta (hasze) opieram na plikach integralności i manifeście, których samodzielnie nie przeliczałem (`v5v4_run_integrity.txt` istnieje; nie sprawdzałem sha256).
- Nie przeliczyłem V5 v3, V6, F1 z surowych danych.

---

## 4. Ograniczenia sterowania SO-101: które stawy steruje SNN, co skryptowe/klasyczne, warstwa bezpieczeństwa, brak sterownika

### Takeaway
W głównym (V5) zadaniu sieć steruje WYŁĄCZNIE obrotem podstawy (shoulder_pan). Pozostałe stawy są ustawione stałą pozą (Q_POSE), a nie sterowane siecią. Warstwa bezpieczeństwa istnieje, jest klasyczna i NIE pilnuje stołu; w repozytorium nie ma żadnego sterownika sprzętowego.

### Cited Findings
- **Tylko staw 0 w V5 — POTWIERDZONE.** `flymind/loop.py:1-10` („poza bazą ramię stoi w pozie Q_POSE”), `loop.py:49` (`Q_POSE = [0, −0,4, 1,0, 0, 1,571, 0,5]`), `integrate_pan`; ω z różnicy DNa02 L−R → kąt podstawy. Pitch (`reports/Projekt…inwestorów.md:81`) pisze „sieć … kieruje ramieniem SO-101 na piłeczkę” — to przesada: sieć obraca podstawę tak, by kamera celowała w piłeczkę; ramię nie sięga ani nie chwyta w tym wyniku. **Flaga błędu raportu.**
- **FlyArm (FJ2) — częściowo, tylko pilot.** `flymind/fly_arm.py`: sieć `vision_leg` 5643 neurony steruje stawami 1–2 (shoulder_lift, elbow_flex) i momentem szczęki; przypisanie „mięsień nogi → staw ramienia” to analogia ustalona przez autorów (docstring). Piloty bez ziaren potwierdzających (`PILOT_NOTES.md`).
- **Klasyczne/skryptowe elementy:** IK i FSM chwytu (`reach.py`, `grip.py`), enkoder obrazu (detektor koloru), dekodery, filtr τ, kalibracja `calibrate_p()` — `REPRODUCE.md` tabela warstw; FJ1: „sięganie jest klasyczne” (`fj1_fly_jaw/RESULTS.md`). `safety.py:SOURCES = ("snn:", "classical:", "script:")` — warstwa liczy interwencje per źródło, by ograniczenia nie udawały zachowania sieci.
- **Warstwa bezpieczeństwa — POTWIERDZONE, z luką.** `flymind/safety.py` (154 l.): margines zakresu 0,05 rad, `v_max` 1,5 rad/s, `max_lead`, watchdog 50 ms, `vision_stale`. `safety.py:13`: „Czego NIE ma: kolizji ze stołem i przestrzeni roboczej”. Stałe (v_max itd.) to wybory projektu, nie pomiary serw (`nasz_kod_przelacznik.md` l. 40, 160). W pilocie FJ2 chwytak wciskał się w stół (29–44 N).
- **Brak sterownika sprzętowego — POTWIERDZONE.** Przeszukałem `*.py` (poza `.venv`/site-packages) pod kątem `serial|scservo|feetech|lerobot`: jedyne trafienia — `bio2/audit_and_validate.py:234` (tekst `print` o serwie Feetech STS3215) i napis „serializ…” w `v5v2_topology.py`/kopiach zamrożonych (fałszywe trafienia: słowo w innym znaczeniu). Brak importów, portów, kodu I/O. `reports/Mózgi owadów kontra modele VLA.md` l. 59 i `nasz_kod_przelacznik.md` l. 21 mówią to samo. Memory `so101-hardware-inventory.md`: kalibracja follower z 1 X 2026 istnieje na Macu, ramię nie podłączone; czujniki dotyku, kamera 96×128 i piłeczka istnieją tylko w MuJoCo.
- **Wszystkie wyniki są symulacyjne — POTWIERDZONE** (`program_v5v41/FINAL_REPORT.md:10`, `V5v4_FINAL_REPORT.md:§3`, `VALIDATION_PLAN.md` „sprzęt: poza zakresem bez zgody”).
- **Zasada „mucha ma sterować” — CZĘŚCIOWO spełniona** (memory `fly-must-control.md`): decyzję o obrocie podejmuje SNN, ale reszta toru jest klasyczna; P jest wzorcem odniesienia i jedynym stabilnym wykonawcą.
- **Demo:** `flymind/demo/` (SNN vs P w oknie MuJoCo; pętla przepisana z `loop.run_trial`, test równości w `test_demo.py`) — istnieje, ale pokazuje tylko obrót podstawy, powstało przed FJ1/FJ2.

### Inferences
- Realistyczne zdanie na plakat: „w symulacji sieć z wycinka konektomu obraca podstawę ramienia tak, by kamera śledziła piłeczkę”. Przeniesienie na sprzęt wymaga adaptera I/O, kamery, kalibracji i bezpieczeństwa stołu — wszystkiego jeszcze nie ma.
- Czas taktu: 424-neuronowa pętla ma p50 4,3 ms (zmierzone w symulacji, `nasz_kod_przelacznik.md` l. 81) — dla prawdziwego sprzętu opóźnienia kamery/serw są niezmierzone.

### Gaps
- Nie mam informacji, czy fizyczne ramię jest sprawne i dostępne (pamięć: tylko ślad kalibracji). Nie dotykałem sprzętu ani portów.

---

## 5. Audyty biologiczne, red-teamy i badania obwodu dotyku (D1, FJ1/FJ2, T2L→T2R)

### Takeaway
Najważniejszy aktualny stan: kandydat „dotyk T2L → wymach T2R jako sygnał uniesienia” został zakwestionowany przez własny red team (commit `54155d4`, nowszy niż notatka nasze_wyniki.md); twierdzenie o „odpornym naturalnym sygnale uniesienia” WYCOFANO. Audyt D1 daje werdykt REVISE; znak glutaminianu i brak obwodu nacisku/poślizgu to otwarte problemy.

### Cited Findings
- **Notatka `nasze_wyniki.md` jest NIEAKTUALNA co do kontroli tasowania — SPRZECZNE z obecnym stanem repo.** Notatka (HEAD `bf05cb1`) pisze, że kontrola tasowania „NIE została jeszcze policzona na poważnie” i że smoke sugeruje brak swoistości. Od tego czasu: commit `9920bfd` dodał kontrolę (`experiments/fj2_fly_arm/results/shuffle_six_legs.jsonl`, 22 wiersze) i `54155d4` red team.
- **Kontrola tasowania — przeliczona, POTWIERDZONE.** Miara M = wymach − podpór w T2R po dotyku T2L (z `shuffle_six_legs.jsonl`, `res.T2R[0] − res.T2R[1]`): Glu −1: dane +22,9 Hz; 10 tasowań od −12,0 do +16,2 (wszystkie poniżej danych). Glu +1: dane +78,1; tasowania od −87,6 do +30,6 (wszystkie poniżej). Zgadza się z `PILOT_NOTES.md` (tabela). 10/10 poniżej danych przy obu znakach — liczbowo prawda. Ale wartość dowodowa mała: n = 10 na znak, tasowanie niszczy także strukturę klas (receptor → IN → MN), więc „dane > tasowanie” częściowo znaczy „wybrany obwód > losowe okablowanie”.
- **Red team wyniku (`PILOT_NOTES.md:~186-210`, commit `54155d4`) — odnotowane przeze mnie:** werdykt SUPPORTED WITH CAVEATS (przy Glu −1 „bliżej słabe”); efekt przy Glu −1 robi głównie jeden typ (Tr flexor, semantyka „= unoszenie” niezweryfikowana); przy dobrze opisanych pulach M = +2,9 Hz i swoistość znika; znak M odwraca się przy słabszym bodźcu (+22,9/+14,5/−2,5 przy 40/20/10 mV); dotyk T3L daje ten sam efekt w T2R (nie jest to para lewa–prawa); T2R wybrano po obejrzeniu 6 nóg; mierzy się aktywność pul, nie ruch nogi. Cytowane zdanie: „pierwszy znaleziony sygnał uniesienia odporny na założenie o glutaminianie — wycofuję”. Nie weryfikowałem ręcznie liczb red teamu (skrypty w scratchpadzie `rt_sixlegs/`, niedostępne w projekcie).
- **Audyt D1–D3 (2026-11-03, REVISE) — źródło: memory `flymind-d1-audit-2026-11-03.md`; raportu pełnego (`RAPORT_D1_D2_D3_PL.md`) nie czytałem (leży w scratchpadzie / kopii zapasowej).** Zawartość wg memory: znak sygnału dotyku zależy od Glu=−1 (literatura tylko z płata czułkowego, Liu & Wilson 2013); w danych jest tylko 2 L + 2 R sensille kampaniformne na nerw nogi → brak obwodu nacisku/poślizgu; DNp09 ma wejście 15 940, z czego LC9 1977 (12,4 %), tylko 18–24 synaps wprost do motoneuronów nogi. NIEZWERYFIKOWANE przeze mnie (nie liczyłem; mogłem to zrobić, ale spoza głównych pytań).
- **FJ1 (szczęka z dotyku nogi) — wyniki w `fj1_fly_jaw/RESULTS.md`:** obwód 12/12 przy obu znakach Glu, ale trywialny odruch 12/12 i test progowy (≈ 0,14 N·m); H2 nierozstrzygnięta (Glu −1) / odrzucona (Glu +1: wszystkie tasowania 12/12). Zgodne z nasze_wyniki.md. Nie przeliczałem surowych plików FJ1.
- **FJ2 FlyArm — piloty bez ziaren potwierdzających.** Zbliżanie chwytaka do piłeczki przy Glu −1 (0,30 m: 71 → 17 mm), niespójne przy Glu +1, kamera widzi piłeczkę tylko 0,30–0,40 m; brak kontroli tasowania dla samego FlyArm.
- **Red-teamy w `flymind/results/redteam/` (przejrzałem werdykty):** `v32_v2_redteam.md` (BLOCKER dla sformułowania bez kwalifikatora G_INH, efektywne n ≈ 16 nie 80), `v4_v5_redteam.md` (m.in. warunek opóźnienia zakłócony; hasz loop.py zmieniony po zamrożeniu przez dodanie `--max-age`, zachowanie domyślne bez zmian), `v5v3_*` (PASS_WITH_LIMITATIONS), `v5v4_protocol_r1..r3` (NOT READY → READY → READY). To samokrytyka modelu o ograniczonej niezależności; nie ma recenzji ludzkiej.
- **Audyt danych `bio2/MALECNS_DATA_AUDIT.md`:** autorzy „Antigravity & Gemini 4 Argon (Google DeepMind)” (!), data 25 X 2026. Dokument trafnie wprost wymienia ograniczenia (liczba synaps ≠ siła; obecność synapsy ≠ pobudzanie; ścieżka dwuskokowa ≠ dowód behawioralny). Uwaga: ten audyt został napisany przez innego modelu/narzędzie niż Claude i jest drugorzędnym źródłem; jego nazwy typów (IN12B018 itd.) są zgodne z konwencją MANC, ale nie sprawdzałem ich w pliku (poza wyszukaniem LC10a/DNa/AOTU, które zgadza się z danymi).
- **Aktualizacja `nasze_wyniki.md` l. o „bf05cb1 … kandydat na sygnał uniesienia”:** wymaga dopisku o commicie `54155d4` (wycofanie twierdzenia) i `9920bfd` (kontrola tasowania wykonana). Wnioski końcowe notatki o „braku testu potwierdzającego” pozostają prawdziwe.

### Inferences
- Linia dotyku/uniesienia to wciąż hipotezy eksploracyjne; nie nadają się na „wynik”. Jej wartość dla pitchu: pokazuje kulturę falsyfikacji (własny red team wycofał twierdzenie w ciągu kilku godzin).
- Sam fakt, że wyniki FlyArm zależą od znaku Glu (±1), a znak jest niewiadomą fizjologiczną, jest głównym wąskim gardłem przejścia od „toru wzrokowego” do „nogi/dotyku”.

### Gaps
- Nie czytałem pełnych raportów D1–D3 ani surowych plików FJ1; skrypty red teamu T2L→T2R poza repozytorium.
- Nie sprawdzałem literatury (Liu & Wilson 2013, Azevedo 2024, Lacin 2019) w sieci.

---

## 6. Weryfikacja wcześniejszych raportów i notatek (co jest błędne lub przesadzone)

### Takeaway
Raporty trafnie podają kluczowe liczby V5 (38/40, 3/40, 0/40, 40/40, 0,16° vs 1,41°) i trafnie podkreślają „tylko symulacja”, „MaleCNS nie FlyWire”, „P wygrywa”. Ale znalazłem kilka przesad lub nieaktualności, które należy poprawić przed użyciem w pitchu.

### Cited Findings
Lista uwag (raport / notatka → co sprawdziłem → werdykt):

1. **„sieć impulsowa … kieruje ramieniem SO-101 na piłeczkę” (`reports/Projekt…inwestorów.md:81`, pitch) — CZĘŚCIOWO POTWIERDZONE / przesada.** Obraca tylko podstawę (staw 0) tak, by kamera celowała w piłeczkę; nie ma sięgania (zob. §4). Zalecenie: „obraca podstawę ramienia”.
2. **„W symulacji działa w 38 z 40 prób. Gdy przetasuję połączenia, tylko w 3 z 40” (l. 81) — POTWIERDZONE co do liczb, wprowadzające w błąd co do znaczenia.** Przetasowanie V5 nie zachowuje lateralizacji; mocniejsza kontrola (zachowująca siłę) dała 20/50 vs 28/50 (V5 v2). Pitch dopisuje, że „przewaga … jest mała i zależy od warunków” — to jest uczciwe.
3. **„Liczby z kontroli (38/40 wobec 3/40 i 0/40) są mocne” (l. 87) — CZĘŚCIOWO POTWIERDZONE.** Liczby tak; „mocne” co do swoistości połączeń — nie (§3).
4. **„Wzór wag W = sign(nt)·J0·ln(1+N_syn)” (nasze_wyniki.md §1) — CZĘŚCIOWO POTWIERDZONE.** Prawda dla `sim/`/`bio2/`; dla `flymind/` (424 neurony, V5–V7) waga jest liniowa, J0 = 0,2 (§1).
5. **„bio2: 220 neuronów mózgu + 72 VNC” — NIEZWERYFIKOWANE/SPRZECZNE liczbowo.** `bio2/circuit_bio2.json`: 272 neurony (nie 292). Być może liczby dotyczą innych podzbiorów (np. 16 pierścień + …); nie rozstrzygnąłem.
6. **„regulator P lepszy w 450/450 parach” (`V5v4_FINAL_REPORT.md:63`, powtórzone w nasze_wyniki.md §2B pkt 3) — SPRZECZNE z surowymi danymi (446/450).** Zob. §3.
7. **nasze_wyniki.md §2C „kontrola z przetasowanymi połączeniami NIE została jeszcze policzona” — NIEAKTUALNE.** Policzona (`9920bfd`) i poddana red teamowi (`54155d4`), efekt osłabiony (§5).
8. **„Zakres V5 v2: ziarna 2051–2100” (nasze_wyniki.md) vs `VALIDATION_PLAN.md:282` „v5v2_topology … ziarna 3001–3050” — SPRZECZNOŚĆ pozorna.** To dwa osobne eksperymenty: (a) `loop_v2.py`, 2051–2100, 28/50; (b) `v5v2_topology.py`, 3001–3050, osobny test topologii. Plik wyników `v5v2_20261029T065804.json` ma ziarna [2051, 2100] — potwierdzone. Opis w memory jest nieprecyzyjny co do tego, który wynik pochodzi z której puli.
9. **„Zbiór MaleCNS: 211 577 ciał, 151,9 mln połączeń” — POTWIERDZONE** (długość annotations = 211 577; 151 856 684 wg nagłówka loadera). „311,8 mln synaps” — NIEZWERYFIKOWANE przeze mnie (nie sumowałem 1 GB wag).
10. **Raport VLA (`Mózgi owadów…VLA.md`:19):** liczby 38/40, 3/40, 0/40, P 40/40, 0,16° vs 1,41° — POTWIERDZONE. `nasz_kod_przelacznik.md` l. 33-38 (loop.py, takt 10 ms, 10×1 ms SNN, `SafetyLayer`) — zgodne z moją lekturą `loop.py`/`safety.py`. Stwierdzenie, że „żaden plik repo nie importuje lerobot, feetech ani serial” — POTWIERDZONE. Stwierdzenie, że „SNN oscyluje ±2 stopnie” — NIEZWERYFIKOWANE (nie przeliczyłem trajektorii); wyniki V5 mówią o cyklu granicznym ±5–6° przy najbliższych celach (VALIDATION_PLAN, „dwie porażki snn”).
11. **Kontekst konkurencji/rynku (Fly Brain Bridge, FlyDrones, Eon, Opteran, ORLEN itd.) — poza moim zakresem, NIEZWERYFIKOWANE.** Raport inwestorski sam przyznaje (l. 93), że liczby projektu cytuje z raportów bez ponownego przeliczania.
12. **Samoocena „inżynieria ~28 %, biologia ~15 %, walidacja ~30 %, sprzęt ~3 %” (memory D1) — opinia autora, nie pomiar.**

### Inferences
- Z perspektywy czytelnika zewnętrznego najbardziej ryzykowne są sformułowania (1) i (2) oraz brak rozróżnienia „lateralizacja vs topologia”. Sama metodologia (zamrożone protokoły, rejestr ziaren, kontrole zerowe, raporty z porażkami) jest naprawdę obecna w plikach i to jest realna siła.
- Dla porównania z literaturą należy traktować projekt jako: „symulacyjny wycinek połączeń MaleCNS (424 neurony) z kalibrowanym dekoderem; wynik zgodny z oczekiwaną lateralizacją push-pull; brak dowodu swoistości topologii; brak sprzętu”.

### Gaps
- Nie weryfikowałem w internecie żadnych twierdzeń o literaturze ani konkurencji (Collie i in., Shiu i in. 2024, Liu & Wilson 2013, Azevedo i in., Eon/Fly Brain Bridge itd.); cytuję je tylko za plikami projektu.
- Nie czytałem pełnego `VALIDATION_PLAN.md`, `program_v5v41/FINAL_REPORT.md`, `RAPORT_F1_PL.md`; wnioski o V5v41–V7 i F1 pochodzą z notatek i memory, nie z własnych przeliczeń.
- Nie uruchamiałem testów jednostkowych (`test_*.py`) — zakaz; ich zielony stan NIEZWERYFIKOWANY.
