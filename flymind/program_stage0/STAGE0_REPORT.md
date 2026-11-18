# Etap 0 — raport: infrastruktura wielu kroków czasowych (2026-11-06)

Autor: ta sama sesja Claude, która napisała raporty rund 2 i 3. Raport nie jest niezależną recenzją.
Etap N nie został uruchomiony. Nie było porównania DATA vs SWS, eksperymentów LC×LC ani strojenia parametrów. Nic nie zostało zacommitowane.

**Wynik w skrócie:**
- 8 z 9 kryteriów ma test z dowodem.
- Kryterium 4 jest **niespełnione przy dt = 0,1 ms**: maksymalny błąd f–I wynosi 2,5% przy limicie 2%. Przy dt = 0,05 ms jest spełnione (1,3%).
- Kryteria 1 i 8 są częściowe, bo w tym etapie nie uruchamiałem pętli zamkniętej i sieci DATA przy dt ≠ 1.
- Przy dt = 1 nowy kod daje wyniki bit w bit równe staremu, łącznie z zapisanym przebiegiem DATA.

Zaliczenie Etapu 0 dotyczy wyłącznie **poprawności implementacji** i **poprawności numerycznej czasu dyskretnego**. Nie mówi niczego o **biologicznej wiarygodności** modelu: parametry Shiu, znaki przekaźników, J0, adaptacja i szum zostały bez zmian i bez oceny.

---

## 1. Stan projektu przed zmianami (VERIFIED)
- Repozytorium: `/Users/admin/so101_fly_project`, gałąź `flymind/fly-first-control`.
- Niezapisane zmiany przed pracą:
  - `M flymind/REPRODUCE.md` (+4) i `M flymind/VALIDATION_PLAN.md` (+170/−3);
  - 127 wpisów nieśledzonych.
  - Po pracy wszystkie są **identyczne**: ten sam `git diff --stat`, a różnica w `git status` to tylko 5 nowych wpisów (pkt 4).
- Sha256 przed zmianami są zgodne z `results/v5v41/config.json`:
  - `alif.py` 13e36619f211…;
  - `v5v41.py` 1e2ff5405e27…;
  - `decoder.py` 0efbc34f38e1….
- `integrity_v5v41.py --compare`:
  - przed: `Stage 1 28/28; manifests 18/18, 18/18; protected files 377 tree dfcabd78f1484c96 | changed 0 | INTEGRITY OK`;
  - po: to samo, `INTEGRITY OK`.
- Ustalenia raportów rund 2 i 3 sprawdziłem w kodzie (pkt 3 i T3). Potwierdzone:
  - przy dt = 1 refrakcja trwa 3 kroki, a opóźnienie 2 kroki;
  - przy dt = 0,2 stary kod blokuje 12 kroków (2,4 ms), a wzór `r_max` podaje 416,7 Hz zamiast zmierzonych 384,6 Hz;
  - przy dt = 0,25 opóźnienie wynosi 1,75 ms, a przy dt = 0,5 wynosi 2,0 ms.
- Jedno stwierdzenie rundy 3 skorygowałem: stary kod przy **dt = 0,05** daje poprawnie 44 kroki refrakcji. Błąd zmiennoprzecinkowy dotyczy dt = 0,2, nie całej drabinki.

## 2. Dziewięć kryteriów Etapu 0
Źródło: raport rundy 3, sekcja „Minimalne kryteria zaliczenia Etapu 0”. Wszystkie dziewięć dało się odtworzyć jednoznacznie, więc żadne nie jest oznaczone jako nierozstrzygnięte. Protokół `STAGE0_PROTOCOL.md` zapisałem przed uruchomieniem testów (sha 0ebf8767…). Mtime < start testów sprawdza T9.

| # | Kryterium | Status | Dowód (wynik `results/stage0/stage0_tests_20261106T162203.json`) |
|---|---|---|---|
| 1 | Regresja bit w bit przy dt = 1 (DATA.npz + 1 próba pętli zamkniętej) | **PARTIAL** | **Otwarta pętla: VERIFIED.**<br>• T1a: stary `v5v41.simulate` = nowy `simulate_dt` w 7 typach harmonogramu × 2 strony (krok, szum 0, kontra 0,5, pre ipsi, pre kontra, rampa, losowe v0). DN wystrzelił w każdym (17–66 spike'ów).<br>• T1b: `ALIFdt` = `ALIF` (spike'i oraz v, g, a) w 4 wariantach parametrów.<br>• T1c: DATA, E1 i E3 przy 8 mV, strony L/R, powtórzenia 0–1: wszystkie 8 przebiegów identyczne z zapisanym `DATA.npz` (counts, adapt, angle, first_dn).<br>**Pętla zamknięta: nie uruchomiona** (MuJoCo). Nowy kod jej nie dotyka, a sha `loop.py`, `alif.py` i `decoder.py` są równe zapisanym (VERIFIED), więc wynik byłby identyczny z konstrukcji (INFERRED) |
| 2 | Te same czasy spike'ów przy różnych dt → te same Hz, okna, biny, Fano | **COMPLETED** | T2: ten sam raster 1500 ms przy dt 1 / 0,2 / 0,1 / 0,05 daje identyczne counts, ss, first_dn (7,0 ms) i Fano (1,0268). Spike'y między węzłami 1 ms (10 − dt, 10,0, 20 − dt) trafiają do binów [1, 2, 0]. VERIFIED |
| 3 | Efektywne t_ref i opóźnienie równe nominalnym na drabince | **COMPLETED** | T3: n_ref·dt = 2,2 ms i n_delay·dt = 1,8 ms przy 0,2 / 0,1 / 0,05 (assert do 1e-12). Tryb `exact` odmawia przy dt 1 / 0,5 / 0,25 / 0,3, a `legacy` odmawia przy dt ≠ 1. VERIFIED |
| 4 | f–I przy dt = 0,1 w granicach 2% od wzoru ciągłego, D 10–100 mV | **NIESPEŁNIONE przy dt = 0,1** | T4: symulacja = wzór dyskretny dokładnie (91 wartości D × 4 dt, 0 niezgodności). Błąd częstości względem wzoru ciągłego:<br>• dt 0,1: maks. **2,53%**; powyżej 2% od D ≈ 64 mV, czyli 5% siatki D (RECOMPUTED na siatce co 0,01 mV);<br>• dt 0,05: maks. 1,30%, spełnione;<br>• dt 0,2: maks. 4,8%.<br>Przyczyna: zaokrąglenie czasu do przekroczenia w górę o ≤ 1 krok, czyli do 0,1 ms przy ISI ≈ 3,7 ms. To skutek siatki czasu, nie błąd kodu. Kryterium nie zostało zmienione |
| 5 | Stacjonarna wariancja v w granicach 5% od analitycznej przy każdym dt | **COMPLETED** | T5 (400 neuronów, 4 s), względem σ²/(2τ_m) = 0,1 mV²: +2,2% / +0,1% / +0,2% / +0,2% przy dt 1 / 0,2 / 0,1 / 0,05. Ze wzorem dyskretnym zgodne do 0,4%. Kontrola: stara semantyka szumu (σ na krok) przy dt 0,1 daje **−90%**. VERIFIED |
| 6 | Odpowiedź na pojedynczy impuls zaczyna się w oczekiwanym kroku | **COMPLETED** | T6: spike pre zapisany w kroku 3 podnosi g i zmienia v neuronu post w kroku 3 + n_delay: kroki 5 / 12 / 21 / 39 (n_delay 2 / 9 / 18 / 36). Refrakcja: v = V_reset przez n_ref kroków, ISI = n_ref + 1. VERIFIED |
| 7 | Dekoder: τ EMA 50 ms przy każdym dt | **COMPLETED** (otwarta pętla) | T7: dopasowane τ = 50,000 ms, pole impulsu = 0,99995 spike'a (teoria 1 − e⁻¹⁰), r(50 ms)/r(0) = e⁻¹ (do 1e-9) przy każdym dt. Kontrola błędu, który harness usuwa: wywołanie `dec.step(…, 1.0)` przy fizycznym dt 0,1 daje τ = 5 ms i pole 0,1 spike'a. Kalibracja dekodera pętli zamkniętej (`v4_open_loop`) nie jest przeniesiona: **NOT STARTED** |
| 8 | Benchmark dt = 0,1, przerwanie, gdy > 3× prognozy | **PARTIAL** | T8: syntetyczna sieć 424 neuronów z gęstą W (koszt W·s nie zależy od wartości wag). 1 s symulacji trwa 0,046 s przy dt 1 i 0,42 s przy dt 0,1, czyli 0,92× prognozy „10×”. Sieć DATA przy dt ≠ 1 nie była uruchamiana; to pierwszy krok Etapu N (BLOCKED do Twojej decyzji) |
| 9 | `alif.py` nietknięty, nowy moduł hashowany, protokół przed testami | **COMPLETED** | T9: sha `alif.py`, `v5v41.py`, `decoder.py`, `snn_interface.py` i `connectome.py` = `results/v5v41/config.json`; sha `loop.py` = `integrity_baseline.json`. Nowe moduły: `alif_dt.py` de140b40…, `v5v41_dt.py` 4cc908e0…, `test_stage0_dt.py` a5825519…. Zastrzeżenie: kod testów zmieniłem po protokole (pkt 9), kryteria nie |

## 3. Ukryte założenia „1 krok = 1 ms”
VERIFIED = przeczytane w kodzie lub potwierdzone testem. INFERRED = tylko z grepa, plik nieprzeczytany w całości.

| Miejsce | Założenie | Skutek przy dt ≠ 1 | Stan |
|---|---|---|---|
| `alif.py` `ref -= dt` | refrakcja jako float | dt 0,2: 12 kroków (2,4 ms) zamiast 11 (VERIFIED, T3) | `ALIFdt`: licznik całkowity |
| `alif.py` `delay_steps = round(delay/dt)` | zaokrąglenie po cichu | dt 0,25: 1,75 ms; dt 0,5: 2,0 ms (VERIFIED) | `exact` odmawia |
| `alif.py` `r_max` | wzór z ceil − 1e-9 | dt 0,2: 416,7 Hz wg wzoru, a mierzone 384,6 Hz (VERIFIED) | `ALIFdt.r_max_hz` z n_ref |
| `alif.py` szum `noise·ξ` na krok | σ zdefiniowane przy 1 ms | wariancja v ∝ dt: −90% przy dt 0,1 (VERIFIED, T5) | σ·√(1/dt) |
| `v5v41.simulate` `BIN = 10` | 10 kroków = 10 ms | bin 1 ms przy dt 0,1, więc ×100 i [50:100] w analizach V6 tracą sens (VERIFIED) | `k_bin = 10/dt` |
| `v5v41.simulate` T, pre, step_ms, rampa | ms = kroki | przebieg 10× krótszy fizycznie (VERIFIED) | `to_steps(…, 'exact')` |
| `v5v41.simulate` okno ss `b*BIN` vs `pre+500` | indeks binu × 10 = ms | złe okno (VERIFIED) | porównanie w ms |
| `v5v41.simulate` `first_dn = t − pre` | kroki = ms | wynik w krokach (VERIFIED) | ms + `first_dn_step` |
| `v5v41.simulate` `dec.step(chunk, 1.0)` | dt dekodera = 1 | τ 5 ms, Hz ×0,1 przy dt 0,1 (VERIFIED, T7) | `dec.step(chunk, dt)` |
| `v5v41.run_network` | przyjmuje `alif={"dt": …}` bez kontroli | po cichu zły harness (VERIFIED) | **nie poprawione** (pkt 9, propozycja) |
| `loop.py` `net.run(I, 10)`, `dec.step(net_spk, 1.0)` | takt 10 ms = 10 kroków | przy dt 0,1 SNN liczy 1 ms na takt 10 ms (VERIFIED) | nie przeniesione (pętla zamknięta) |
| `cl_runner.configure` | przyjmuje `alif` z dt bez kontroli | jak wyżej, po cichu (VERIFIED) | **nie poprawione** (propozycja) |
| `v4_open_loop.OpenLoop.tick` `exp(-1/50)`, `×1000`, `ms=10`; `run(I, 800)` | dt = 1 | kalibracja dekodera pętli zamkniętej błędna (VERIFIED) | nie przeniesione |
| `v5v4.calibrate` | używa `v4_open_loop` | dziedziczy (INFERRED) | nie przeniesione |
| `v5v43.py` `W0, W1, SS = 300, 1000, 500`, `T = 1000`; `v6m.py`, `v6m2.py`, `v6m3.py` `run(I, T)` i okna 300–1000 | indeksy = ms | eksperymenty mechanizmu (Etap M) nie działają przy dt ≠ 1 (INFERRED, grep) | nie przeniesione: należą do Etapu M |
| `v6_analysis.py` `[50:100] × 100` | biny 10 ms | poprawne, jeśli harness zachowuje biny fizyczne (VERIFIED: `simulate_dt` je zachowuje) | bez zmian |
| strumień RNG | jedno losowanie na krok | przebiegi przy różnych dt nie są sparowane szumem (INFERRED z kodu) | udokumentowane |
| `decoder.py` | brak założenia: dt jawne | — (VERIFIED, T7) | bez zmian |

## 4. Zmienione pliki
Żaden istniejący plik nie został zmieniony (porównanie sha256 wszystkich `flymind/*.py` przed i po: tylko 3 nowe wpisy). Nowe pliki:
- `flymind/alif_dt.py`:
  - `to_steps` (ms → kroki, reguły `exact` / `ceil` / `round`);
  - `ALIFdt(ALIF)` z `__init__`, `reset`, `step`, `timing_report` i `r_max_hz`;
  - `isi_steps` (wzór dyskretny f–I) i `isi_continuous_ms`.
- `flymind/v5v41_dt.py`: `simulate_dt` (harness w ms) i `fano`.
- `flymind/test_stage0_dt.py`: testy T1a–T9.
- `flymind/program_stage0/STAGE0_PROTOCOL.md`, ten raport oraz `stage0_new_files.diff`.
- `flymind/results/stage0/stage0_tests_20261106T162034.json` (pierwszy przebieg, przed dodaniem zabezpieczenia `legacy`, **zastąpiony**, nieusunięty) i `stage0_tests_20261106T162203.json` (wiążący).

## 5. Uzasadnienie zmian
1. **Nowe moduły zamiast edycji.** `alif.py`, `v5v41.py` i `loop.py` są przypięte hashami w manifestach i konfiguracjach wyników (`integrity_v5v41`, `results/*/config.json`). Kryterium 9 wymaga, żeby `alif.py` był nietknięty. `ALIFdt` dziedziczy po `ALIF`, więc równania nie są przepisane, a jedynie podmieniona jest obsługa czasu.
2. **Całkowite liczniki.** Usuwają błąd zmiennoprzecinkowy (dt 0,2) i czynią n_ref i n_delay jawnymi i testowalnymi.
3. **`exact` vs `legacy`.**
   - `exact` odmawia, gdy czas nie jest wielokrotnością dt, więc nic nie jest zaokrąglane po cichu.
   - `legacy` (ceil dla refrakcji, round dla opóźnienia) istnieje wyłącznie po to, by odtworzyć stary model przy dt = 1. Przy innym dt odmawia.
4. **Semantyka czasu** (konwencja; krok k = przedział [k·dt, (k+1)·dt)):
   - Spike zapisany w indeksie k ma znacznik k·dt. Przekroczenie progu leży w (k·dt, (k+1)·dt], więc znacznik jest wcześniejszy o 0–dt. Przy dt = 1 i D = 20 mV: −0,42 ms; przy dt 0,05: −0,02 ms (T6). Biny nie są przesunięte, bo granice binów są wielokrotnościami dt.
   - **Refrakcja:** kroki k+1 … k+n_ref zablokowane. Liczona od przekroczenia trwa [t_ref, t_ref + dt), czyli 3–4 ms przy dt = 1 i 2,20–2,25 ms przy dt 0,05. Najkrótszy ISI wynosi (n_ref + 1)·dt.
   - **Opóźnienie:** spike z indeksu k zmienia g i v celu w indeksie k + n_delay, czyli dokładnie n_delay·dt według znaczników. Liczone od przekroczenia daje [(n_delay − 1)·dt, n_delay·dt): 1–2 ms przy dt = 1 i 1,75–1,8 ms przy dt 0,05.
5. **Szum skalowany √(1/dt).**
   - Bez tego mniejsze dt po cichu zmniejsza szum: −90% wariancji v przy dt 0,1, czyli dynamika zmienia się przypadkowo.
   - Przy dt = 1 wynik jest bit w bit taki sam jak wcześniej.
   - To jest **decyzja interpretacyjna**: σ = 2 przyjmuję jako intensywność zdefiniowaną przy 1 ms, a nie jako σ na krok. Uzasadnienie: zachowuje fizykę przy dt = 1. Starą semantykę można przywrócić przez `noise_ref_dt=None`.
6. **Harness w ms.** Wszystkie długości są w ms, a kroki są liczone jawnie. Kształty wyjść (biny 10 ms) nie zależą od dt, więc analizy V6 nie wymagają zmian.

## 6. Testy, komendy i wyniki
Komendy wiążące (uruchomione z katalogu repozytorium):

```
.venv/bin/python -I -B flymind/test_stage0_dt.py --out flymind/results/stage0
→ t9 PASS | t1a PASS | t1b PASS | t1c PASS (1,8 s) | t2 PASS | t3 PASS | t4 PASS | t5 PASS (5,4 s) | t6 PASS | t7 PASS | t8 PASS
  zapisano: flymind/results/stage0/stage0_tests_20261106T162203.json
.venv/bin/python -I -B flymind/test_alif.py     → OK: dynamika ALIF (14 asercji)
.venv/bin/python -I -B flymind/test_decoder.py  → OK: dekoder motoryczny (23 asercje)
.venv/bin/python -I -B flymind/test_v5v41.py    → test_v5v41: 8 tests OK
.venv/bin/python -I -B flymind/integrity_v5v41.py --compare flymind/results/v5v41/integrity_baseline.json --label stage0_after
→ Stage 1 28/28; manifests 18/18, 18/18; protected files 377 tree dfcabd78f1484c96 | changed 0 | INTEGRITY OK
```

Uwaga: **„t4 PASS” oznacza tylko, że symulacja = wzór dyskretny.** Kryterium 4 jest zapisane osobno w JSON (`criterion4_dt01_within_2pct: false`) i jest niespełnione.

Testy, których nie wykonałem:
- próba pętli zamkniętej w MuJoCo;
- `test_cl_runner.py` (MuJoCo);
- `test_alif_sparse.py` (nie dotyczy zmian);
- sieć DATA przy dt ≠ 1;
- SWS.

## 7. Stare vs nowe zachowanie przy dt = 1
Identyczne bit w bit:
- 14 przebiegów syntetycznych harnessu (T1a);
- 4 warianty sieci, czyli 2000 kroków ze stanem v, g, a (T1b);
- 8 przebiegów DATA względem zapisanego pliku (T1c; DN 34–92 Hz w oknie ustalonym).

Przy dt = 1 nowy kod zachowuje **także stare wady**: refrakcję 3,0 ms, opóźnienie 2,0 ms i sufit 250 Hz. To celowe: dt = 1 to ramię „stary model”.

Przy dt ≠ 1 stary kod i nowy różnią się w trzech miejscach:
- refrakcja przy dt 0,2: 12 vs 11 kroków;
- szum: wariancja −80 / −90 / −95% w starym kodzie przy dt 0,2 / 0,1 / 0,05 (INFERRED ze wzoru h·σ²/(2−h); zmierzone tylko dla 0,1);
- stary harness przy dt ≠ 1 jest niepoprawny w całości (pkt 3).

## 8. Tabela dla czterech dt
Pojedynczy neuron bez szumu, adaptacji i sieci, chyba że zaznaczono inaczej. Źródło: JSON T3–T8.

| | dt 1,0 (legacy) | 0,2 | 0,1 | 0,05 | ciągły |
|---|---|---|---|---|---|
| n_ref / t_ref efektywne | 3 / 3,0 ms | 11 / 2,2 | 22 / 2,2 | 44 / 2,2 | 2,2 |
| n_delay / opóźnienie | 2 / 2,0 ms | 9 / 1,8 | 18 / 1,8 | 36 / 1,8 | 1,8 |
| r_max (najkrótszy ISI) | 250 Hz (4 ms) | 416,7 (2,4) | 434,8 (2,3) | 444,4 (2,25) | 454,5 |
| σ na krok | 2,000 | 4,472 | 6,325 | 8,944 | — |
| wariancja v [mV²] (teoria 0,1) | 0,1022 | 0,1001 | 0,1002 | 0,1002 | 0,1000 |
| f–I D = 20 mV [Hz] | 83,33 | 92,59 | 92,59 | 92,17 | 92,46 |
| f–I D = 50 mV | 166,67 | 185,19 | 188,68 | 190,48 | 191,70 |
| f–I D = 100 mV | 200,00 | 263,16 | 270,27 | 273,97 | 273,87 |
| maks. \|błąd f–I\|, D 10–100 | 28,9% | 4,8% | **2,5%** | 1,3% | — |
| średni błąd f–I, D 10–100 | −17,9% | −1,6% | −0,8% | −0,4% | — |
| pierwszy spike, D = 20,37: znacznik − ciągły | −0,42 ms | −0,22 | −0,12 | −0,02 | — |
| kroki na 1500 ms / na bin 10 ms | 1500 / 10 | 7500 / 50 | 15000 / 100 | 30000 / 200 | — |
| τ dekodera (dopasowane) | 50,000 ms | 50,000 | 50,000 | 50,000 | 50 |
| czas: 1 s symulacji, sieć syntetyczna 424 neuronów | 0,046 s | — | 0,42 s | — | — |

Uwaga do f–I: przy D = 20 i D = 30 kolumny dt 0,2 i dt 0,1 mają te same wartości (92,59 i 131,58), bo ISI jest liczbą całkowitą kroków i oba dt trafiają tu na ten sam czas.

## 9. Ograniczenia, nierozwiązane problemy i ryzyka
1. **Kryterium 4 przy dt = 0,1 jest niespełnione** (2,5% > 2% dla D ≳ 64 mV). Możliwe drogi; to Twoja decyzja, ja niczego nie zmieniam:
   - (a) traktować dt = 0,05 jako punkt odniesienia zbieżności;
   - (b) zachować drabinkę i raportować to jako znane ograniczenie;
   - (c) zmienić kryterium. To byłaby zmiana po zobaczeniu wyniku, więc tylko jawnie.
2. **Pętla zamknięta i Etap M nie są przeniesione** (`loop.py`, `cl_runner.py`, `v4_open_loop.py`, `v5v4.calibrate`, `v5v43.py`, `v6m*.py`). Przy dt ≠ 1 dają po cichu złe wyniki.
3. **Proponowana minimalna zmiana, NIE wprowadzona:** dwie linie `if P.dt != 1.0: raise ValueError(...)` w `v5v41.run_network` i `cl_runner.configure`. Nie wprowadziłem jej, bo zmienia sha plików zapisanych w konfiguracjach wyników (`v5v41/config.json`, `v6m`, `v5v42`, `v5v41_e6`) i psuje ich weryfikację. Potrzebuję Twojej zgody.
4. **Brak runnera Etapu N.** Jest `simulate_dt`, nie ma odpowiednika `run_network` ani harmonogramów. To mała praca na start Etapu N.
5. **Szum przy różnych dt nie jest sparowany** (inny strumień RNG). Porównania między dt muszą opierać się na wielu ziarnach, nie na parach.
6. **Skalowanie szumu to wybór interpretacyjny** (pkt 5.5). Model Shiu nie ma prądu szumu (ma wejście Poissona), więc nie daje tu punktu odniesienia.
7. **Znaczniki czasu spike'ów są systematycznie wcześniejsze o 0–dt.** `first_dn` przy dt = 1 ma błąd do 1 ms. Biny i okna nie są tym dotknięte.
8. **T1c uruchomił sieć DATA przy dt = 1.** To odtworzenie zapisanego przebiegu (te same ziarna, 8 przebiegów, wynik bit w bit równy plikowi), a nie nowy eksperyment. Uznałem to za test regresyjny, który dopuściłeś. Jeśli rozumiałeś zakaz szerzej, zgłaszam to wprost.
9. **Zmiany kodu testów po zapisaniu protokołu:**
   - zwiększyłem wagi sieci syntetycznej, bo pierwszy przebieg T1a był pusty (DN milczał);
   - dodałem test odmowy trybu `legacy` przy dt ≠ 1.
   Kryteria nie zostały zmienione. Pierwszy plik JSON (162034) jest zachowany jako zastąpiony.
10. **SparseALIF** (obwód nogi) nie ma wersji dt. Nie jest potrzebny w Etapie N.
11. **Znalezisko poza zakresem, nie poprawione** (VERIFIED: kod i dane):
    - `v6_fano_posthoc.py:21` dla strony R bierze kolumnę 1 (LC kontralateralne, nie stymulowane), a nie kolumnę 0;
    - w `DATA.npz` E1 8 mV ta kolumna ma 0,0 Hz, więc Fano wychodzi NaN i `nanmean` po cichu pomija stronę R;
    - zapisane w V6 liczby Fano pochodzą więc tylko ze strony L, wbrew opisowi „obie strony”;
    - nie sprawdzałem, czy to zmienia wnioski V6.

## 10. Diff
Wszystkie zmiany to nowe pliki. Pełny diff: `flymind/program_stage0/stage0_new_files.diff` (652 linie, `diff -u /dev/null <plik>` dla `alif_dt.py`, `v5v41_dt.py`, `test_stage0_dt.py`, `STAGE0_PROTOCOL.md`). Plik raportu i JSON-y z wynikami nie są w diffie.

Rdzeń zmiany, czyli `ALIFdt.step` względem `ALIF.step` (pozostałe linie identyczne):
```diff
-        slot = self.t % p.delay_steps
+        slot = self.t % self.n_delay
-        I = I_ext + p.noise * self.rng.standard_normal(self.N) if p.noise else I_ext
+        I = I_ext + self.sigma_step * self.rng.standard_normal(self.N) if self.sigma_step else I_ext
-        self.ref -= dt
+        np.maximum(self.ref - 1, 0, out=self.ref)          # self.ref: int64, kroki
-        self.ref[spk] = p.t_ref
+        self.ref[spk] = self.n_ref
```
`simulate_dt` względem `v5v41.simulate`:
- kroki z `to_steps(ms, dt, 'exact')`;
- `k_bin = 10/dt`;
- okno ss porównywane w ms;
- `dec.step(chunk, dt)`;
- `first_dn` w ms;
- do zwracanego słownika dochodzą pola dt, k_bin, steps, T_ms i timing.

---
**Zatrzymuję się tutaj.** Etap N nie został uruchomiony. Decyzje dla Ciebie:
- jak potraktować kryterium 4;
- czy wprowadzić zabezpieczenia z pkt 9.3;
- czy zatwierdzić pierwszy krok Etapu N: N1, czyli benchmark i krzywa f–I sieci DATA przy dt ≠ 1.
