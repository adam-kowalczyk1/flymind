# Red Team: V3.2 (v1 + v2) — "brak generowanego przez sieć, zlokalizowanego, trwałego wzgórza EPG w ALIF z samych wag connectomu"

Recenzent: niezależny, adwersarialny. Data: 2026-10-28. Wszystkie liczby poniżej pochodzą z uruchomień opisanych w sekcji "Polecenia"; czego nie uruchomiłem, jest wprost zaznaczone. Ziarna użyte: 1001–1005 (powtórzenie protokołu i testy), 1301 (tylko tasowanie kontrolne). Nie dotykałem bio2/, assets/, data/. bio2/brain.py czytany wyłącznie jako tekst.

## 0. Wniosek w jednym akapicie

Wynik negatywny jest **poprawnie policzony i odtwarzalny**, ale jego zakres jest węższy niż sugeruje nagłówek "V3.2 ... wynik negatywny". Dotyczy on wyłącznie **jednej linii w przestrzeni parametrów: hamowanie Delta7 o tej samej jednostkowej sile na synapsę co pobudzenie (G_INH = 1, G_DD = 1)**. Jedna dodatkowa, wcześniej nieskanowana oś (mnożnik Delta7→{EPG,PEN}, ten sam, który stosuje bio2: G_INH = 8, G_DD = 0,3), przy b_a = 0 i na surowych wagach z danych (bez uśredniania profilowego, bez żadnych krawędzi modelowych) daje trwały (stabilny przez co najmniej 2,2 s po zdjęciu bodźca), ciągły łuk aktywności EPG o rozpiętości 113–158° i dC ≈ 0,7–0,8, z fazą skorelowaną z bodźcem. To odwraca zdanie "dane nie wspierają wzgórza w ALIF" na "dane nie wspierają wzgórza przy G_INH = 1". Dodatkowo: połowa wyniku (b_a = 0,5) jest nieinformatywna co do okablowania, bo **idealny, syntetyczny pierścień z tymi samymi parametrami ALIF też nie trzyma wzgórza przy b_a ≥ 0,25** (kontrola pozytywna).

## 1. Tabela twierdzeń

| Twierdzenie | Dowód | Alternatywne wyjaśnienie | Test obalający | Wynik |
|---|---|---|---|---|
| T1. Brak trwałego wzgórza dla J0 ∈ {0,05…0,3}, b_a ∈ {0,5; 0} (G_INH = 1) | Powtórzenie `run(1)`, `run(2)`: tabele identyczne z JSON (True/True); w oknie 650–1000 ms max dC (dowolna faza) = 0,080 (A), 0,080 (B), 0,101 (R); 0 prób z dC > 0,2 | Prawda w tej slicie; metryka nie przeoczyła niczego | Skan G_INH ∈ {1,2,4,8,16}, G_DD ∈ {1;0,3}, J0 ∈ [0,03; 0,2] na tej samej sieci i metryce | **Obalone dla uogólnienia**: G_INH ≥ 8 + b_a = 0 → 6/48…39/48 prób spełnia kryterium autora (sekcja 3.2). Dla G_INH = 1 potwierdzone |
| T2. Przejście "tylko bodziec" → "cały pierścień", bez stanu pośredniego | Okno "on": 16/1040 wierszy ma 0 < active_outside < 0,9, prawie wszystkie to +1 EPG (0,023); w oknie późnym zero stanów częściowych (partial = 0 w każdej z 13 kondycji) | Słusznie dla G_INH = 1; przy G_INH ≥ 8 stany częściowe są regułą (nact EPG mediana 18–22 z 46) | Skan G_INH + skan amplitudy bodźca (6/12/24 mV) i drobnego J0 (0,100–0,125) przy G_INH = 1 | Dla G_INH = 1 **potwierdzone** (amp 6: zawsze cisza; 12 i 24: wyłącznie 0 lub 46 aktywnych, partial = 0 we wszystkich 27 kondycjach). Dla G_INH ≥ 8 **obalone** |
| T3. Znaki NT poprawne (ACh+, Glu−) | EPG/PEN: ground_truth ACh 88/88; Delta7: ground_truth NaN 42/42, consensus = celltype = predicted = glutamate (średnia pewność predykcji 0,64) | Znak Delta7 to założenie modelu (GluCl), dane tylko przewidują Glu | Test syntetyczny 3 neuronów (11 ACh → 22 Glu → 33) | Znaki poprawne i zgodne z literaturą; Delta7 NT jest *predykcją* o niższej pewności (0,64), nie pomiarem — do zapisania w ograniczeniach |
| T4. Kierunek krawędzi W[post, pre] poprawny | 2-neuronowy test syntetyczny: W[22,11] = 5, W[33,22] = −4; sterowanie 11 podnosi 22 z 18 do 22 spike'ów, aktywne 22 (Glu) zbija 33 z 16 do 15 | — | `build()` + `ALIF.step`: `g += W @ buf[slot]`, kolumna = pre | **Potwierdzone** (brak błędu kierunku i znaku). Kosmetyka: `spec.W` (property, snn_interface.py) zwraca `-0.0`; hash liczony z wersji bez −0.0 — brak wpływu numerycznego |
| T5. Kryterium V2 (dopuszczalność) nie zniekształca wniosku | Wniosek T1 nie zależy od dopuszczalności (0 prób z dC > 0,2 także dla wierszy niedopuszczalnych) | Kryterium `runaway` (v32_bump.py:95) = "średnia po całej sieci okno późne > okno bodźca" jest *z konstrukcji* spełnione przez każdy stan trwały, bo w oknie bodźca aktywne są 2–4 neurony z 130 | Policzyłem to samo kryterium dla stanów dodatnich | **Obalone co do sensu**: dla G_INH = 8/16, b_a = 0 kryterium orzeka "runaway" w 45/80 i 75/80 prób, `admissible = False` mimo `max_sat = 0`. Dopuszczalne J0 (0,05; 0,1) to w praktyce "podprogowe, nic nie zapala" — dowód z "dopuszczalnych" jest tautologiczny |
| T6. Jakikolwiek attraktor jest niemożliwy z samych parametrów ALIF? (pytanie 6) | Idealny pierścień 46 E + 42 I (Gauss σ = 40°, ten sam ALIF, szum 2 mV) | Gdyby klasa modeli nie trzymała wzgórza, wynik byłby o modelu, nie o danych | Skan A × B, 168 kondycji × 15 prób | **Klasa modeli trzyma wzgórze, ale tylko dla b_a ≲ 0,1**: b_a = 0: 107 z 630 prób to trwały łuk (wąski pas wzdłuż A ≈ 2–2,5·B), b_a = 0,1: 4, b_a = 0,25: 0, b_a = 0,5: 1 (przypadkowa). Połowa siatki autora (b_a = 0,5) nie mogłaby wykryć wzgórza nawet w idealnej sieci |
| T7. "80 prób na J0", zmienność ziarnowa | Zliczenia ignicji na glomerulus × 5 ziaren | Wynik jest niemal deterministyczny na poziomie glomerulusa (0/5 lub 5/5 ziaren); szum 2 mV nie ma znaczenia | Tabela ziaren per glomerulus | Efektywne n ≈ 16 (glomeruli), nie 80. Ponadto bodziec 12 mV działa na 2, 3 lub 4 EPG (L8, R8 mają 4): glomeruli z 4 EPG zapalają się pierwsze |
| T8. Wiersze wspólne v1/v2 "co do bitu" | Powtórzenie: C, dC, phase_err, rate, active, active_outside identyczne (480/480 wierszy dla J0 0,10 i dla 0,14); C_perm **nie** (max |Δ| 0,177 i 0,277) | `rng = _rng(1101)` (v32_bump.py:81) jest wspólny dla całej pętli, więc C_perm zależy od kolejności siatki | Porównanie wierszy | Twierdzenie autora jest dokładne (mówi o C/dC/fazie), ale C_perm nie jest odtwarzalne między wersjami; docstring "ziarno 1101" sugeruje inaczej |

## 2. Lista problemów

Gradacja: blocker = unieważnia sformułowanie wniosku; major = istotnie osłabia lub zawęża; minor = redakcyjne/higiena.

1. **[BLOCKER dla sformułowania, nie dla liczb] Wniosek bez kwalifikatora G_INH.** VALIDATION_PLAN.md:89 ("wynik negatywny"), :107–112 (Wniosek), :141–142 (Wniosek eksploracji). Brakująca oś: mnożnik hamowania Delta7 (bio2/brain.py:107–108: G_INH = 8, G_DD = 0,3). Moje powtórzenie z surowymi wagami z danych, `W[ring, Delta7] *= G_INH`, `W[Delta7, Delta7] *= G_DD`, bez krawędzi modelowych, bez uśredniania profilowego, z metryką i progami autora (dC > 0,2, faza < 45°, okno 650–1000 ms, bodziec 12 mV / 300 ms): patrz sekcja 3.2. Wzgórze istnieje. Poprawka: zmienić nagłówek na "wynik negatywny przy G_INH = 1" i usunąć/uściślić zdanie "Ani gęstsza siatka J0, ani brak adaptacji nie dają..." (prawdziwe, ale czytane jako ogólne). Dopisać wprost: "G_INH jest kluczową osią, wynik jest do niego wrażliwy". Pozycja "osobne wzmocnienie hamowania Delta7" na liście "następnych kandydatur" (:143) powinna być awansowana do "rozstrzygającej".

2. **[MAJOR] b_a = 0,5 jest hostylne dla każdego trwałego stanu — połowa wyniku jest nieinformatywna.** v32_bump.py:84, alif.py (b_a = 0,5 mV/spike, τ_a = 300 ms): stacjonarna adaptacja ≈ b_a·r·τ_a = 0,5·0,04·300 = 6 mV przy 40 Hz, przy luce progowej v_th − v_rest = 7 mV. Kontrola pozytywna (idealny pierścień, tabela 3.3) potwierdza: przy b_a ≥ 0,25 praktycznie brak wzgórza nawet w idealnej sieci. Wynik v1 (całe, b_a = 0,5) oraz połowa v2 mówią więc o parametrze adaptacji, nie o okablowaniu. Poprawka: dopisać do ograniczeń; jako kontrolę pozytywną dołączyć do protokołu idealny pierścień (patrz 3.3) i uznać wynik za informatywny tylko tam, gdzie kontrola daje wzgórze.

3. **[MAJOR] Brak kontroli pozytywnej w protokole.** v32_bump.py (cały protokół). Negatywne twierdzenie bez dowodu, że potok wykryłby wzgórze, gdyby istniało. Moja kontrola pokazuje, że metryka je wykrywa (15/15 prób dla idealnego pierścienia b_a = 0, A = 120, B = 50, AEI = 100; C ≈ 0,81, faza zgodna), ale tego brakuje w repo. Poprawka: dodać `test_*`/`v32_positive_control.py` z idealnym pierścieniem w tym samym ALIF i wymagać, by przechodził kryterium przed wyciąganiem wniosków negatywnych.

4. **[MAJOR] Kryterium dopuszczalności wyklucza z definicji szukany stan, a "dopuszczalne" J0 są tautologiczne.** v32_bump.py:95 i :106; autor sam to zauważa (VALIDATION_PLAN.md:135–139), ale zdanie "wnioski tylko z dopuszczalnych" z docstringu (v32_bump.py:8) pozostaje i tabela v1 (:96–105) nadal wyróżnia "dopuszczalne". Moje stany dodatnie mają `admissible = False` (45/80 i 75/80 prób "runaway"; `max_sat = 0`). Dla dopuszczalnych J0 (0,05; 0,1) sieć jest cicha *i bez recepcji bodźca*, więc ich "wynik" to tylko "poniżej progu zapłonu". Dobra wiadomość: wniosek T1 nie zależy od dopuszczalności w slicie G_INH = 1 (0 prób z dC > 0,2 w oknie późnym we wszystkich 13 kondycjach, także niedopuszczalnych). Poprawka: zastąpić `runaway` kryterium nasycenia w oknie późnym (sat ≥ 0,9·r_max dla > X % neuronów) albo wzrostu w czasie, i raportować wyniki dla wszystkich J0 bez filtrowania.

5. **[MAJOR] Efektywna liczba niezależnych prób to ≈ 16, nie 80; bodziec nierówny między glomerulusami.** v32_bump.py:90–93, :89. Per glomerulus liczba ziaren (z 5) z aktywnością późną jest prawie zawsze 0 lub 5 (np. b_a = 0, J0 = 0,12: L4, L8, R3, R8 = 5/5, reszta 0/5), a ten sam strumień szumu (`ALIF(spec, P, seed)`) jest używany dla każdego glomerulusa i każdego J0 (common random numbers). Do tego bodziec 12 mV trafia w 2, 3 lub 4 EPG (L1/L2/R1/R2: 2; L8/R8: 4), więc całkowity prąd wejściowy różni się 2×. Wskaźniki typu "w ≥ 25 % prób cały pierścień" (VALIDATION_PLAN.md tabela v1) są właściwością podzbioru glomeruli, nie szumu. Poprawka: raportować per glomerulus; rozważyć stałą liczbę pobudzonych EPG (np. 2) lub stały sumaryczny prąd.

6. **[MAJOR] Brak testu kierunkowego w zakresie zadeklarowanych pominięć.** Pominięcie ER/EPGt/PEG, agregacja przedziałów (EB+PB w jednym wagu) i liniowa transformacja synaps są wymienione w "Ograniczeniach", ale wynik jest formułowany bez ich wagi. Zbadane przeze mnie: transformacja log1p przy G_INH = 1, b_a ∈ {0; 0,5}, J0 ∈ [0,2; 3,0]: 0 prób stanu częściowego, tylko 0 → pełne zapalenie (J0 = 1,5: 10/32; 2,0: 24/32). Czyli *transformacja nie jest czynnikiem rozstrzygającym*; Delta7-gain jest. Niezbadane (brak uruchomienia): ER, PEG/EPGt, osobne stałe czasowe synaps, opóźnienia, rozdział przedziałów.

7. **[MINOR] Podsumowanie `summarize` raportuje warunkowe kwartyle.** v32_bump.py:124–131. `dC_q25_50_75`, `phase_err_deg_median`, `frac_phase_within_half_wedge` liczone tylko po `C.notna()`, np. dla J0 = 0,14 b_a = 0,5 okno późne to 24 z 80 prób (n_undefined = 56); `frac_phase_within_half_wedge` = 0,083 jest ułamkiem aktywnych, nie wszystkich. Kolumna `n_undefined` jest, ale łatwo to przeoczyć. Poprawka: dopisać do nazw kolumn "_defined" albo podać n_defined obok.

8. **[MINOR] Niedokładność w tekście: "dC ≤ 0,07".** VALIDATION_PLAN.md:129. Z kwartylów q75 = 0,066; faktyczne maksimum (wariant A) to 0,080 przy b_a = 0,5, J0 = 0,12; wariant R do 0,101. Dla b_a = 0 maksimum 0,018 ("dC ≤ 0,02" zgodnie z tabelą). Nie zmienia wniosku (próg 0,2), ale zdanie jest niedokładne.

9. **[MINOR] "0,14: cały pierścień (≈ 200 Hz)" dla b_a = 0.** VALIDATION_PLAN.md:130. Dotyczy 45 z 80 prób (35/80 cisza), "≈ 200 Hz" to mediana po wszystkich. Doprecyzować.

10. **[MINOR] Metryka: okno 650–1000 ms i 350 ms uśrednienia.** v32_bump.py:56, :97. Wzgórze dryfujące o ≥ 90° w oknie spada poniżej progu (syntetycznie: dryf 90° → dC 0,60, błąd fazy 47° → "brak"; 180° → dC 0,42, faza 91°). Nie zadziałało to na wynik autora (w żadnej kondycji nie ma dC > 0,2 w żadnej fazie), ale kryterium wymaga fazy < 45° względem bodźca, co dyskwalifikuje wzgórze, które po prostu przeskoczyło o 2–3 glomeruli. Poprawka: raportować osobno "zlokalizowany w dowolnej fazie" (u mnie: `loc_anyphase`). Brak okna 300–650 ms; sprawdziłem je (G_INH = 1, 8 kondycji): partial = 0, brak stanów przejściowych.

11. **[MINOR] `bump_metrics` trywialnie daje C = 1 dla jednego aktywnego neuronu** (sprawdzone: dC = 0,969). W "oknie bodziec" `frac_bump = 1` to stwierdzenie "bodziec jest zlokalizowany" i autor to objaśnia, ale kolumna `frac_bump` w oknie "on" jest myląca. Poprawka: nie raportować `frac_bump` dla okna bodźca.

12. **[MINOR] C_perm zależy od kolejności siatki.** v32_bump.py:81, :99. Jedna `rng` dla całej pętli; v1 vs v2 dla tego samego (J0, b_a) daje różne mediany C_perm (np. J0 = 0,10, b_a = 0,5, wariant A, okno "on": 0,4669 vs 0,4739). Poprawka: seed per (J0, b_a, glomerulus, seed).

13. **[MINOR] Autapsy/diagonala.** Wagi z danych nie zawierają autapsji (`self loops = 0` dla tych 130 neuronów), więc różnica względem bio2 (`np.fill_diagonal(W, 0)`) nie ma znaczenia tutaj. Zapisuję jako sprawdzone, nie jako problem.

## 3. Dowody i polecenia

Wszystkie polecenia: `cd /private/tmp/claude-501/-Users-admin-so101-fly-project/31945ef1-39f8-4198-827d-6c45c0d388b2/scratchpad/redteam && /Users/admin/so101_fly_project/.venv/bin/python -I -B <skrypt>`, skrypty importują `sys.path.insert(0, '/Users/admin/so101_fly_project/flymind')`. Żaden skrypt nie zapisywał nic w repo.

### 3.1 Powtórzenie protokołu, sieć, znaki, kierunek

- `repro.py`: `v32_bump.run(1, None)` i `run(2, None)` w procesie. Wynik: tabela i dopuszczalność identyczne z JSON (True/True dla v1 i v2). Wiersze wspólne: C/dC/faza/rate/active/outside bitowo równe (480/480 dla J0 = 0,10 i 480/480 dla 0,14), C_perm różne (max |Δ| = 0,177 i 0,277).
- `inspect_net.py`: bloki W przy J0 = 1 (liczba synaps, znak wg NT): EPG→EPG 11 486; EPG→Delta7 19 896; Delta7→EPG −4 294; Delta7→PEN_a −1 178; Delta7→PEN_b −6 061; Delta7→Delta7 −26 539. Promień spektralny W(J0 = 1) = 706,4. Autapsje 0. Zwróć uwagę: hamowanie Delta7→EPG (4 294 synaps) jest ~5× słabsze niż EPG→Delta7 (19 896), a Delta7→Delta7 (−26 539) jest największym blokiem — przy G_DD = 1 Delta7 silnie tłumią się wzajemnie, co osłabia hamowanie globalne.
- `ntcheck.py`: EPG/PEN: ground_truth = ACh (46, 20, 22); Delta7: ground_truth NaN (42/42), consensus = glutamate (42/42), predicted_nt_confidence średnia 0,64.
- `edge_dir.py`: sieć syntetyczna 3 neuronów (11 ACh → 22 Glu → 33 ACh). W[22,11] = 5, W[33,22] = −4. Przy napędzie 11: 22 odpala 22× (kontrola bez napędu 11: 18×), 33 odpala 15× (z aktywnym 22) vs 16× (22 ciszej). Kierunek i znak poprawne.

### 3.2 Rozstrzygająca oś: wzmocnienie hamowania Delta7 (surowe wagi z danych)

Skrypt: `gscan.py` (3 ziarna 1001–1003 × 16 glomeruli = 48 prób na komórkę, metryka i progi autora, wariant A). Kolumna `bump` = liczba prób z dC > 0,2 ∧ błąd fazy < 45° w oknie 650–1000 ms.

| b_a | G_INH | G_DD | J0 | prób z aktywnością późną /48 | z tego wszystkie 46 EPG | częściowe | `bump` /48 | maks. dC |
|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1 | 0,14 | 27 | 27 | 0 | 0 | 0,002 |
| 0 | 1 | 1 | 0,20 | 45 | 45 | 0 | 0 | 0,008 |
| 0 | 8 | 0,3 | 0,12 | 12 | 0 | 12 | 6 | 0,738 |
| 0 | 8 | 0,3 | 0,14 | 27 | 0 | 27 | 15 | 0,755 |
| 0 | 8 | 0,3 | 0,20 | 45 | 0 | 45 | 32 | 0,746 |
| 0 | 16 | 0,3 | 0,14 | 27 | 0 | 27 | 21 | 0,809 |
| 0 | 16 | 0,3 | 0,20 | 45 | 0 | 45 | 39 | 0,821 |
| 0,5 | 8 | 0,3 | 0,14 | 13 | 9 | 4 | 0 | 0,482 |
| 0,5 | 8 | 0,3 | 0,20 | 40 | 13 | 27 | 15 | 0,639 |
| 0,5 | 16 | 0,3 | 0,14 | 10 | 1 | 9 | 4 | 0,814 |

(Pełny skan: 108 kondycji, G_INH ∈ {1,2,4,8,16}, J0 ∈ {0,03…0,2}, b_a ∈ {0; 0,5}; wynik w `gscan.pkl`. G_INH = 1, 2 → zawsze 0 `bump`; G_INH = 4 → `bump` 9–12/48 przy b_a = 0 (J0 = 0,14 i 0,2), ale stan szeroki (> 30 aktywnych EPG, `loc_anyphase` = 0, dC ≈ 0,36–0,47), więc kryterium "łuku" jest wrażliwe na G_INH.)

Stabilność i charakter (`bumpdetail.py`, `bumpspec.py`, `contig.py`):
- Przebieg 2500 ms (bodziec 0–300 ms), b_a = 0, G_INH = 8, G_DD = 0,3, J0 = 0,14: w każdym z okien 300–650, 650–1000, 1000–1500, 1500–2000, 2000–2500 ms aktywnych jest 27/48 prób, `bump` 16, 15, 15, 15, 15; mediana aktywnych EPG 22. Dla G_INH = 16: 27/48 aktywnych, `bump` 21 w każdym oknie. Stan jest stacjonarny (brak zaniku, brak dryfu).
- Rozpiętość kątowa zbioru aktywnych EPG (G_INH = 16, G_DD = 0,3, J0 = 0,2, b_a = 0, ziarno 1001, 16 glomeruli): 113–158° (zbiór ciągły, największa luka = reszta pierścienia).
- Zależność od bodźca (nie jest to losowy stan): b_a = 0, G_INH = 16, G_DD = 0,3, J0 = 0,2 — 75/80 prób aktywnych, odsetek z błędem fazy < 45° = 0,87; null (tasowanie kątów bodźca, 2000 permutacji, ziarno 1301) mediana 0,27, p95 = 0,35. Kąt stanu ≈ kąt bodźca w sposób monotoniczny (np. L3 90°→132°, L4 135°→131°, L5 180°→169°, L6 −135°→−128°, R4 −158°→−170°, R5 158°→161°), ale **skwantowany**: 13 różnych zbiorów aktywnych na 75 prób, 7 klas kąta w pojemnikach 10° — wzgórze jest przypięte heterogenicznością okablowania, nie ciągłe. Dla G_INH = 8, J0 = 0,14: 0,56 vs null 0,28 (p95 = 0,36), 8 zbiorów, 6 klas.
- Admissibility (kryterium autora, identyczny kod): b_a = 0, G_INH = 8, J0 = 0,14: runaway 45/80, `max_sat` = 0 → niedopuszczalne; G_INH = 16, J0 = 0,14: 45/80; G_INH = 16, J0 = 0,2: 75/80.

Zastrzeżenia do tej sekcji (uczciwie): (a) to eksploracja *po* zobaczeniu wyników autora i zaglądaniu do bio2 — nie jest potwierdzeniem; użyte ziarna 1001–1005 to te same ziarna co w v1/v2; (b) przeskanowano 108 kondycji, ale efekt jest monotoniczny po G_INH i J0 i obecny w całych podsiatkach (b_a = 0, G_INH ≥ 8, J0 ≥ 0,12), więc nie jest pojedynczym szczęśliwym trafieniem; (c) łuk 113–158° jest szeroki (≈ 1/3–1/2 pierścienia) i skwantowany, więc to "wzgórze" w sensie trwałej zlokalizowanej aktywności o fazie zależnej od bodźca, nie dowód na ciągły attraktor pierścieniowy z dryfem swobodnym; (d) G_INH = 8 jest decyzją modelu (strojoną w bio2), nie daną; (e) przy b_a = 0,5 efekt jest znacznie słabszy i wygasa w ≤ 2 s (G_INH = 16, J0 = 0,14, 2500 ms: aktywnych prób w kolejnych oknach 11, 10, 4, 1, 0 z 48).

### 3.3 Idealny pierścień (pytanie 6)

`idealring.py`, `idealring2.py`, `idealring3.py`: 46 neuronów E w równych odstępach, jądro gaussowskie σ = 40° znormalizowane do sumy A (mV/spike), E→I (42 neurony) jednorodne, AEI/NE; I→E jednorodne −B/NI; ten sam `ALIFParams(noise = 2,0)` i `ALIF` z `alif.py`, bodziec 12 mV do 3 sąsiednich E przez 300 ms, okno 650–1000 ms, 5 ziaren (1001–1005) × 3 pozycje = 15 prób na kondycję; kryterium "wzgórze" = C > 0,5 ∧ błąd fazy < 45° ∧ ≤ 30 aktywnych E.
- `idealring.py` (A ≤ 50): 0 aktywności wszędzie — zakres A za niski (nieinformatywne, nie raportuję jako dowód).
- `idealring2.py`: szeroka siatka A ∈ {10…400}, B ∈ {0…1600}, AEI ∈ {20, 100}: tylko jedna komórka z `bump` (b_a = 0, AEI = 100, A = 120, B = 50: 15/15, nact = 21, C = 0,81); reszta to cisza lub pełne zapalenie.
- `idealring3.py` (drobna siatka wokół pasa, AEI = 100): `bump` sumarycznie b_a = 0: 107 z 630 prób (7 A × 6 B × 15 prób na b_a; pas wzdłuż A ≈ 2–2,5·B, np. A/B = 100/35: 14/15; 120/50: 15/15; 140/70: 15/15; 200/100: 15/15; 260/140: 15/15), b_a = 0,1: 4 (tylko A = 260, B = 140), b_a = 0,25: 0, b_a = 0,5: 1 (A = 140, B = 70, nact = 46 — fałszywy pozytyw, mediana C 0,36).
- Wnioski: klasa neuronów ALIF z tymi parametrami **może** trzymać wzgórze, ale **wąski pas stroju** (równowaga E/I) i tylko przy b_a ≲ 0,1. Jednowymiarowy skan J0 po G_INH = 1 z surowymi wagami to jedna linia, która mogła ten pas ominąć. Skan G_INH (3.2) pokazuje, że dodanie drugiej osi wystarcza, żeby go trafić.

### 3.4 Metryka (pytanie 1)

`an5.py` — syntetyczne wzorce na kątach wariantu A:
- von Mises κ = 0,2 / 0,3 / 0,5 / 1 / 2 / 4: dC = 0,068 / 0,116 / 0,210 / 0,414 / 0,666 / 0,829; detekcja (dC > 0,2 ∧ < 45°): nie / nie / tak / tak / tak / tak. Próg 0,2 odpowiada wzgórzu o κ ≈ 0,5 (szerokie, słabe) — wystarczająco czułe.
- Dryf wzgórza o D° w oknie 350 ms (κ = 2): 0° → dC 0,666 (tak); 45° → 0,652, błąd fazy 24° (tak); 90° → 0,602, błąd fazy 47° (nie, tylko z powodu fazy); 180° → 0,417, 91° (nie); 360° → 0,002 (nie).
- Jeden aktywny neuron: C = 1, dC = 0,969. Brak aktywności: `C = None`, `reason = "Σr = 0 ..."` — obsłużone poprawnie; w `summarize` niezdefiniowane liczone w `n` i jako "brak wzgórza" (`frac_bump = len(bump)/len(d)`, poprawnie), statystyki jakościowe tylko po zdefiniowanych (problem 7).
- Maksymalne dC w oknie późnym, wszystkie kondycje v1+v2, G_INH = 1: A 0,080; B 0,080; R 0,101; liczba prób dC > 0,2: 0. Okno 320–650 ms (G_INH = 1, 8 kondycji b_a × J0 ∈ {0,10; 0,11; 0,12; 0,14}): `partial` = 0 wszędzie, `bump` = 0.

### 3.5 Amplituda bodźca, drobny J0, log1p (G_INH = 1)

- `an4.py`: b_a = 0, ziarna 1001–1002, 16 glomeruli = 32 próby/komórkę; J0 ∈ {0,100…0,125}; amp 6 mV: 0 aktywności wszędzie; 12 mV: 0 → 10/32 aktywnych (wszystkie pełne, `partial` = 0); 24 mV: 18/32 aktywnych już przy J0 = 0,100, 28/32 przy 0,125, wszystkie pełne, `partial` = 0, `bump` = 0. Brak stanu pośredniego w żadnej z 27 kondycji.
- `logscan.py`: transformacja log1p, G_INH = 1, J0 ∈ {0,2…3,0}: `partial` = 0 we wszystkich 16 kondycjach (b_a = 0 i 0,5), przejście od ciszy do pełnego zapalenia (J0 = 1,5: 10/32 lub 4/32; J0 = 3: 32/32).

### 3.6 Kto zapala, kiedy (zapłon globalny)

`an2b.py`: w ścieżce zapłonu (np. b_a = 0,5, J0 = 0,12, R8, ziarno 1002) czasowy przebieg w pojemnikach 50 ms: wszystkie populacje startują równocześnie ok. 100–150 ms (EPG 5 → 190 Hz, Delta7 do 85 Hz), potem trwałe ~130–180 Hz. Delta7 działają (do 87 Hz), ale przy G_INH = 1 nie zdołają zdławić EPG/PEN — tak jak sugeruje spektrum bloków (hamowanie Delta7→EPG 4 294 synaps vs pobudzenie EPG→EPG 11 486 + PEN→EPG 24 069).

## 4. Odpowiedzi na pytania

1. **Błędy metryki:** nie wykryłem błędu, który ukrywałby wzgórze w obszarze zbadanym przez autora (max dC późne 0,08–0,10 w każdej fazie). Metryka jest wystarczająco czuła (κ ≈ 0,5) i obsługuje Σr = 0. Słabe punkty: wymóg fazy < 45° względem bodźca i uśrednienie 350 ms (dryf ≥ 90° wypada), brak okna 300–650 w protokole (sprawdziłem: nic nie ma), warunkowe statystyki w `summarize`.
2. **Znaki:** poprawne (ACh+, Glu−); Delta7 NT to predykcja (pewność 0,64), co należy odnotować.
3. **Kierunek krawędzi:** poprawny, test syntetyczny.
4. **Dopuszczalność:** nie zmienia wniosku w slicie G_INH = 1, ale z konstrukcji wyklucza szukany stan i czyni "dopuszczalne J0" tautologią.
5. **Brakująca biologia — co jest rozstrzygające:** zmierzone jako rozstrzygające: mnożnik hamowania Delta7 (G_INH, G_DD) i adaptacja b_a. Zmierzone jako nierozstrzygające: transformacja log1p, amplituda bodźca 6–24 mV, drobniejsze J0. Niezmierzone (nie uruchomiłem): ER, PEG/EPGt, agregacja przedziałów EB/PB, stałe czasowe synaps, opóźnienia, siła wzajemnego tłumienia Delta7 poza G_DD ∈ {0,3; 1}.
6. **Prostsze wyjaśnienie (parametry ALIF):** częściowo tak. Idealny pierścień trzyma wzgórze tylko przy b_a ≲ 0,1 i w wąskim pasie A/B, a jednowymiarowy skan J0 w G_INH = 1 jest ortogonalny do tego pasa. Negatywny wynik jest więc o *skali E/I i adaptacji w tej parametryzacji*, a nie o okablowaniu per se.
7. **Ziarna i powtarzalność:** powtarzalność C/dC/faza potwierdzona; C_perm nie; efektywne n ≈ 16 (zapłon deterministyczny na poziomie glomerulusa); szum 2 mV prawie nieistotny; wielokrotne porównania nie dotyczą twierdzenia negatywnego w oryginale, ale dotyczą mojego skanu (108 kondycji, patrz zastrzeżenia).
8. **Sformułowanie:** za mocne w nagłówku i sekcjach "Wniosek" (VALIDATION_PLAN.md:89, :107, :141); właściwa treść "Ograniczeń" (:113–118) jest uczciwa, ale nie przewiduje, że pominięta oś jest rozstrzygająca. Za słabe: stwierdzenie, że "niezbadane" są "inna amplituda", "log1p" — te dwie osie są już obojętne (3.5).

## 5. Werdykt

Wynik V3.2 v1+v2 jest **liczbowo poprawny i odtwarzalny** (błędów kierunku, znaku, metryki nie znalazłem), ale **twierdzenie ogólne ("dane + ALIF nie dają wzgórza") jest fałszywe w tej postaci**: przy G_INH = 8–16, G_DD = 0,3 i b_a = 0 na surowych wagach connectomu pojawia się trwały, ciągły łuk EPG o fazie skorelowanej z bodźcem (stabilny > 2 s). Prawdziwe pozostaje wąskie twierdzenie: "przy G_INH = 1 (równa siła na synapsę dla pobudzenia i hamowania) i liniowej lub log1p transformacji nie ma stanu pośredniego pomiędzy 'tylko bodziec' a 'cały pierścień', dla b_a ∈ {0; 0,5}". Ponadto b_a = 0,5 nie mogłoby wykryć wzgórza nawet w idealnej sieci, więc ta połowa jest nieinformatywna co do okablowania. Zalecenie: zmienić brzmienie na "negatywny przy G_INH = 1", uznać G_INH i b_a za osie rozstrzygające, dodać kontrolę pozytywną (idealny pierścień), przedefiniować `runaway`, a potwierdzenie pozytywnego wyniku (G_INH ≥ 8, b_a = 0) przeprowadzić jako osobny protokół potwierdzający na ziarnach 2001+ (dokładnie tak, jak autor sam zapisał).

## 6. Co NIE zostało sprawdzone

Nie uruchamiałem mujoco ani żadnego skryptu bio2; nie porównywałem numerycznie `alif.py` z `bio2/snn.py` (tylko czytanie tekstu `bio2/brain.py`); nie badałem ER/PEG/EPGt, innych stałych czasowych synaps, opóźnień, rozdziału przedziałów EB/PB; nie sprawdzałem wzgórz o różnych szerokościach jądra w idealnym pierścieniu poza σ = 40°; skan G_INH nie obejmuje rozdzielenia G_INH dla Delta7→EPG i Delta7→PEN osobno.
