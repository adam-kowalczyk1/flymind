# Red Team: V4 + V5 — „sieć z danych LC10a→DNa02 niesie znak i stronę potrzebne do orientacji w pętli zamkniętej; tasowanie okablowania to niszczy; nie jest lepszym regulatorem niż klasyczny P”

Recenzent: niezależny, adwersarialny. Data: 2026-10-28. Wszystkie liczby pochodzą z uruchomień wymienionych w sekcji 5; czego nie uruchomiłem, jest zaznaczone. Nie modyfikowałem niczego poza tym plikiem (skrypty w katalogu scratch `/private/tmp/claude-501/-Users-admin-so101-fly-project/31945ef1-39f8-4198-827d-6c45c0d388b2/scratchpad/redteam2/`). Nie importowałem bio2. Ziarna prób: tylko 1001–1020 (patrz 5.0 — jedno odstępstwo dotyczące ziaren RNG tasowania/szumu obrazu).

## 0. Wniosek w jednym akapicie

Liczby V5 są **policzone poprawnie i odtwarzalne** (analiza z JSON odtwarza `analysis_confirm.json` co do bajtu; moja kopia pętli odtwarza trajektorie dev1 dla ziaren 1001–1003 bit w bit). **Nie znalazłem wycieku prawdy** o celu do sterownika. Natomiast sformułowanie wniosku jest za mocne w trzech miejscach: (1) „tasowanie niszczy zachowanie” jest prawdą tylko dla tej klasy tasowania, którą wybrano — tasowanie zachowujące siłę wyjściową **i wejściową** neuronów (pary krawędzi o równej wadze) daje 20/20 sukcesów, a tasowania permutacyjne (kto zasila DNa02 / które LC10a zasila pośrednie) dają 3–4/20; (2) dane nie są *konieczne* — prosty przekaźnik ipsilateralny LC10a→DNa02 bez pośrednich, bez hamowania i bez danych daje 20/20 i mniejszy błąd (0,67° vs 1,85°); (3) sieć działa w wąskim oknie: poza ρ ≈ 0,26–0,28 m lub przy kuli r ≤ 1,5 cm **nie robi nic** (0/8, 0/12), podczas gdy regulator P na tym samym enkoderze działa wszędzie (8/8, 12/12); zakres zadania (ρ ≤ 0,24 m) leży tuż przy krawędzi okna. Dodatkowo H3 i H4 są z konstrukcji nieinformatywne co do sieci (potwierdzam eksperymentalnie), a „opóźnienie 100 ms: 0/20” to artefakt reguły świeżości klatki, nie test tolerancji na opóźnienia.

## 1. Tabela twierdzeń

| Twierdzenie | Dowód (z repo / mój) | Alternatywne wyjaśnienie | Test obalający | Wynik |
|---|---|---|---|---|
| T1. Sterownik nie dostaje prawdy o celu | `loop.py:71` `bearing()` wołane tylko w `e.append(...)` (ocena); do sterownika idą `obs.frame.image`, `obs.q`, `obs.t`; `Frame.proprio` nieużywany | Pośredni wyciek przez wspólne ziarno RNG (`loop.py:67` `default_rng(seed)` w `trial_spec` i `loop.py:107` `ALIF(..., seed)`) | Czytanie kodu + sprawdzenie strumienia bitów: pierwsze `random_raw` seed 1001 jest wspólne dla obu generatorów | **Potwierdzone: brak wycieku.** Wspólny strumień bitów geometrii i szumu ALIF to higiena (minor 11), nie kanał informacji dla sterownika |
| T2. SNN to coś więcej niż przekaźnik (gL, gR) | Docstring `visual_path.py`: push-pull LC10a→DNa02 | DNa02 L i P to dwa progowe, nasycające się wyjścia ipsilateralne | Siatka 9×9 (gL, gR) → DNa02 (`t1_grid.py`); usunięcie wszystkich krawędzi hamujących; przekaźnik z modelowych krawędzi | **Obalone co do „więcej niż przekaźnik”:** L−P ma zgodność znaku 42/42 z gL−gR (max g ≥ 0,6), liniowe R² = 0,88; bez krawędzi hamujących 18/20; przekaźnik ipsilateralny bez danych 20/20 (sekcja 3.2) |
| T3. Tasowanie niszczy zachowanie przez „zmianę okablowania” przy tych samych wagach/stopniach | `visual_path.py:71` podwójna zamiana krawędzi; H2: 35 vs 0 par, p = 2,9·10⁻¹¹ | Tasowanie obniża siłę wejściową DNa02 (462 → 107–193 mV) i miesza lateralizację, a nie „psuje topologię” per se | (a) tasowanie zachowujące wejście i wyjście (równe wagi); (b) osłabienie wejścia DNa02 ×0,25; (c) permutacje | **Częściowo obalone.** (a) 20/20; (b) 20/20; (c) 3–4/20. Wynik H2 jest prawdziwy dla wybranej klasy tasowania, nie dla „topologii z danych” w ogóle (3.2) |
| T4. Kalibracja nie jest cyrkularna, znak ustalony z góry | `v4_open_loop.py:155–158` odmowa przy slope ≤ 0; `fit_steer` odmawia |slope| < 2 Hz/rad | Kalibracja na `spot_clip` z prawdą az, nie na symulatorze | `loop.py:200–202` nie sprawdza znaku slope ani `refused`/`sign_ok` | **Częściowo:** brak cyrkularności względem symulatora (potwierdzone); ale pętla nie broni się przed ujemnym slope (minor 8) |
| T5. J0 = 0,2 z reguły, „nie strojone na pętli” | `v4_open_loop.py:13–15` (v1) vs `:33–35` (v2) | Reguła v2 zmieniona po obejrzeniu v1 (martwa strefa); próg „g = 0,5, 20 Hz” dobrany ręcznie | Wrażliwość pętli na J0 i s_min (dev 1001–1010, rekalibracja) | **Częściowo obalone:** J0 wybrane przez v1 (0,05) daje w pętli 2/10; 0,1 i 0,2 → 10/10; 0,3 → 1/10. Okno ≈ ×2 (sekcja 3.4) |
| T6. Sukces jest nietrywialny; no_vision i swap są informatywne | `analyze_v5.py` H3/H4 | Sukces wymaga tylko właściwego znaku; no_vision to „nic nie rób” (|az0| ≥ 10,7° > 5° ⇒ porażka z definicji) | Komparator 1-bitowy sign(gL−gR) bez SNN; ten sam z odwróconym znakiem | **Obalone co do informatywności:** komparator 20/20, z odwróconym znakiem 0/20 (mediana 53°). H3/H4 nie odróżniają SNN z danych od czegokolwiek ze znakiem |
| T7. Statystyka (sparowane McNemar, Bonferroni, Wilson, bootstrap) | `analyze_v5.py:10–14, 17–21, 32, 60` | Wilson −0,0; n efektywne | Przeliczenie, tabela Wilsona, wrażliwość na tolerancję | **Potwierdzone** (formuły poprawne); n efektywne = 40 prób dla 1 sieci/1 kalibracji/1 pozy (3.7) |
| T8. Warstwa bezpieczeństwa nie ukrywa zachowania | 0 flag w snn/delay 0; 3600 flag w delay 50 ms | Flagi = artefakt progu świeżości (age = 0,05 dokładnie), nie fizyka | Powtórzenie z tolerancją 1e-6 na `max_age` i `max_sensor_age` | **Potwierdzone co do przyczyny flag, obalone co do wpływu:** 90 z 295 klatek/próbę flagowanych przez równość w granicy; usunięcie flag nie zmienia sukcesu (6/20 → 6/20), zmienia czas do |e|<5° (mediana 1,26 → 0,31 s). Regulator P przy 50 ms: 20/20 ⇒ spadek SNN jest właściwością SNN (3.8) |
| T9. Odporność na oświetlenie/dystraktory/szum/ruch | brak w V5; V4 tylko na `spot_clip` | Odporność na światło to normalizacja Webera w enkoderze, nie sieć | Zmiany sceny 3D w pętli (3.6) | **Mieszane:** światło ×0,3/×2,5, szum σ 15/30, ruch 0,03 m/s — bez wpływu (10–11/12); dystraktor zielony przeciwległy ściąga cel (0/12) — tak samo P (6/12, 0/12); martwa strefa zasięgu (ρ, r) specyficzna dla SNN |

## 2. Numerowane problemy (severity, plik:linia, poprawka)

**1. [MAJOR] „Tasowanie niszczy zachowanie” zależy od klasy tasowania; kontrola nie jest uczciwa co do siły wejściowej.**
`visual_path.py:71–97` (`shuffle`): zamienia cele przy zachowaniu wag przypiętych do presynaptycznego neuronu; zachowuje stopnie wejścia/wyjścia i siłę wyjściową presynaptyczną, ale **nie zachowuje siły wejściowej** neuronów postsynaptycznych. Zmierzone (`net_struct.py`): suma wag wejściowych DNa02 L/P: oryginał 461,8 / 460,6; po tasowaniu (ziarna 1,2,3) 127,0/111,2; 107,0/193,4; 155,2/112,8. W oryginale DNa02 nie ma **żadnej** bezpośredniej krawędzi LC10a→DNa02 (0 krawędzi; 65 krawędzi od pośrednich do L, 86 do P); po tasowaniu pojawia się 222–266 mV bezpośredniego, losowo lateralizowanego wejścia LC10a. Wyniki na dev 1001–1020 (n = 20, slope 495,6 Hz/rad, J0 0,2):

| Warunek | Sukces | mediana końcowego \|e\| | uwaga |
|---|---|---|---|
| snn (dane) | 19/20 | 1,85° | max \|DNa02 L−P\| średnio 222 Hz |
| shuffle_orig (`loop.shuffle`, seed+100000) | 2/20 | 27,98° | max \|L−P\| 44 Hz; confirm: 12/40 prób kończy dalej od celu niż zaczęło |
| shuffle_eqw_exact (zamiana tylko krawędzi o tej samej wadze i znaku: zachowane wejście, wyjście, znak) | **20/20** | 1,35° | 31 % krawędzi wejściowych DNa02 L nie ruszone; 2-skokowy wpływ L-LC→DNa02 L: 74 794 → 65 056 |
| shuffle_eqw_tol25 (waga w ±25 %) | 18/20 | 2,21° (średnia 4,89°) | 2-skokowy L-LC→DNa02 L: 74 794 → 2 156 |
| DNa02: wejścia ×0,25 (nietknięte okablowanie) | **20/20** | 0,97° | wyklucza „samo osłabienie” jako przyczynę |
| DNa02 wyciszone (wejścia = 0) | 0/20 | 19,90° | = no_vision (brak ruchu) |
| permutacja źródeł pośrednie→DNa02 (zachowane wagi i siła wejściowa) | 3/20 | 14,30° | 50 % prób odwraca się od celu |
| permutacja wyjść LC10a (która LC10a zasila które pośrednie; siła wejściowa wszystkich neuronów zachowana) | 4/20 | 29,12° | 60 % odwraca się |
| obie permutacje | 3/20 | 27,14° | 50 % odwraca się |

Wniosek: H2 (35 vs 0 par) jest prawdziwy dla tego tasowania; przyczyną nie jest samo osłabienie (×0,25 → 20/20) ani „cisza” (shuffle nie milczy, tylko losuje znak: w konfirmacji 12/40 prób kończy dalej od celu niż zaczęło, 19/40 zbliża się o > 5°, 10/40 zmienia błąd o ≤ 5°; kategorie nie są rozłączne; średnie |ω| snn 0,198 vs shuffle 0,048), tylko utrata lateralizacji toru ipsilateralnego. To **wspiera** tezę, że poprawne okablowanie ipsi→ipsi jest potrzebne — ale nie „topologia z danych” jako taka: tasowanie zachowujące mocne krawędzie (wagi unikalne zostają na miejscu) pozostawia zachowanie nietknięte. Sformułowanie w protokole („przy tych samych wagach, stopniach”) jest nieścisłe: siła wejściowa się zmienia.
Poprawka: dodać do protokołu kontrole permutacyjne (kod w `exp_null2.py`: permutacja kolumn `W[dn, mid]` oraz `W[:, LC]`) i kontrolę zachowującą siłę wejściową; w treści wniosku zastąpić „tasowanie okablowania niszczy” przez „niszczy je tasowanie krawędzi (podwójna zamiana) i permutacja źródeł wejść do DNa02/pośrednich; nie niszczy go tasowanie zachowujące siłę wejściową i wyjściową o równych wagach”.

**2. [MAJOR] Dane nie są konieczne, SNN nie robi nic poza przekaźnikiem ipsilateralnym ze znakiem.**
`visual_path.py`/`loop.py`. Fakty: LC10a → DNa02 nie ma bezpośrednich krawędzi; cały tor to 147 pośrednich. Odpowiedź otwartopętlowa (`t1_grid.py`, 3 ziarna, okno 300–600 ms): DNa02_L = 0 Hz dla gL ≤ 0,4, 2 Hz dla 0,5, 53 dla 0,6, 138 dla 0,8, 198 dla 1,0 (gR = 0); kontralateralne hamowanie działa tylko gdy oba g > 0,5 (gL = 0,6: 53 → 13 Hz przy gR 0 → 1,0). L−P: zgodność znaku z gL−gR 42/42 (|gL−gR| > 0,05, max g ≥ 0,6), dopasowanie liniowe R² = 0,88 (nachylenie 243 Hz); dla max(g) ≤ 0,5 |L−P| ≤ 5,6 Hz (martwa strefa). Model zabawkowy (bez pośrednich, bez hamowania, krawędzie modelowe LC10a_L→DNa02_L i LC10a_R→DNa02_R po 6,4 mV; ta sama kalibracja procedurą V4 v2: slope 393 Hz/rad): **20/20**, mediana 0,67° (SNN z danych: 1,85°), 0 prób odwracających. Bez krawędzi hamujących w sieci z danych: 18/20.
Wniosek: „sieć przenosi znak i stronę” jest prawdą, ale trywialną — LC10a ma `somaSide`, więc dowolna mapa ipsi→ipsi to spełnia. V5 pokazuje, że dane są *wystarczające*, nie że są *konieczne*, i nie wyjaśnia niczego ponad lateralizację.
Poprawka: do wniosku dopisać „wystarczające, niekonieczne; przekaźnik ipsilateralny bez danych daje porównywalny lub lepszy wynik”; dodać `toy_ipsi_relay` jako warunek protokołu (bez hipotezy przewagi).

**3. [MAJOR] SNN ma wąski zakres roboczy (martwa strefa progowa); zakres zadania leży tuż przy krawędzi.**
`encoder.py:27–30` (`c_min`, `e0`), `visual_path.network(0.2)`: DNa02 milczy przy g < ~0,5 (6 mV prądu). Zmierzone w pętli (dev 1001–1008, kąt 20°, slope z V4; snn / klasyczny P):
ρ = 0,24: 8/8 / 8/8 (mediana początkowego max g = 0,66); 0,26: 5/8 / 8/8 (0,61); 0,28: **0/8** / 8/8 (0,57); 0,30: 0/8 / 8/8 (0,53); 0,32: 0/8 / 8/8 (0,49). Kula r = 2,0 cm: 6/8 / 8/8; r = 1,5 cm: **0/8** / 8/8 (mediana max g = 0,41). Robust (1001–1012): ρ = 0,35 i 0,50: snn 0/12 (|e| = 20,00° — brak ruchu), P 12/12; kula r = 1,0 cm: snn 0/12, P 12/12. W konfirmacji korelacja ρ z końcowym błędem snn = −0,76 (bliskie cele gorsze: cykl graniczny; dalekie lepsze), mimo to zakres zadania ρ ≤ 0,24 m kończy się 2–4 cm przed załamaniem.
Poprawka: zapisać zakres roboczy (ρ ≤ ~0,26 m dla kuli 5 cm, r ≥ ~2 cm) jako część wniosku; przetestować jawnie poza nim (protokół na ziarnach 2051+, jak w planie).

**4. [MAJOR] Reguła wyboru J0 zmieniona po obejrzeniu wyników; wynik pętli wrażliwy na J0 (okno ×2).**
`v4_open_loop.py:13–15` (v1: ≥ 20 Hz przy g = (1,0) → J0 = 0,05) vs `:33–35` (v2: ≥ 20 Hz przy g = 0,5 → J0 = 0,2). Zmiana nastąpiła po v1 (martwa strefa, offset +7°) — próg „g = 0,5, 20 Hz” jest wolnym parametrem. Zmierzone w pętli (dev 1001–1010, `exp_j0.py`, slope przekalibrowany procedurą V4 v2; w nawiasie slope stały 495,6):

| J0 | s_min | slope [Hz/rad] | sukces (rekal.) | (slope stały) |
|---|---|---|---|---|
| 0,05 | 5 | 12,3 | 2/10 | (0/10) |
| 0,1 | 5 | 206,0 | 10/10 | (9/10) |
| 0,2 | 5 | 495,6 | 10/10 | — |
| 0,3 | 5 | 560,3 | 1/10 (przeregulowanie med. 5,5°) | (0/10) |
| 0,2 | 3 | 480,3 | 9/10 | (9/10) |
| 0,2 | 10 | 515,8 | 9/10 | (7/10) |
| 0,1 | 3 | 209,8 | 10/10 | (9/10) |
| 0,3 | 3 | 558,0 | 1/10 | (0/10) |

Wniosek: reguła v1 (J0 = 0,05) dałaby w pętli 2/10 — zmiana v1→v2 była *potrzebna* dla wyniku, więc „nie strojone na pętli” jest prawdą co do kolejności (V4 przed V5), ale reguła została dobrana po obejrzeniu wyników V4; s_min 3–10 nie ma znaczenia (9–10/10), J0 ≥ 0,3 psuje pętlę (lokalne wzmocnienie przy środku ≈ 14 Hz/° vs globalny slope 560 Hz/rad ≈ 9,8 Hz/° ⇒ cykl graniczny). Kalibracja liniowa na ±30° przy nasyconej krzywej (Ymean dla J0 0,2: −217, −219, −151, −31, 123, 213, 210 Hz) nie jest wiernym slope’em w okolicy zera.
Poprawka: raportować J0-sweep w pętli jako ograniczenie; zapisać regułę v2 jako *post hoc*; ewentualnie wymusić kalibrację lokalną (±10°).

**5. [MAJOR] H3 i H4 nie niosą informacji o sieci; „zadanie jest trywialne dla każdego regulatora ze znakiem”.**
`analyze_v5.py:60`, `loop.py:trial_spec` (|az0| ∈ [10,7°; 29,7°], tolerancja 5° ⇒ no_vision nie może zaliczyć). Zmierzone (dev 1001–1020, `exp_misc.py ref`): komparator 1-bitowy 0,5·sign(gL−gR) (martwa strefa 0,02) **20/20**, mediana 0,39°; ten sam z odwróconym znakiem 0/20 (53,4°); tanh(3(gL−gR)) 20/20 (0,26°); regulator P 20/20 (0,26°). Więc: H3 (swap: 0/40, „odwraca się 40/40”) i H4 (bez wzroku: 0/40) zostałyby spełnione przez jakikolwiek regulator ze znakiem; informatywny jest tylko H2 (a ten zależy od klasy tasowania — problem 1) oraz opisowe P vs SNN. Krytyczna uwaga co do surowości: kryterium 5° przez cały czas 2,5–3 s jest ostre dla SNN (mediana odchylenia standardowego e w oknie: SNN 1,48°, P 0,00°); dla tolerancji 6° snn = 40/40, 4° = 29/40, 3° = 23/40 (shuffle: 4/40 przy 6°, 7/40 przy 8°, 11/40 przy 10°) — H1 (≥ 0,8, dolne CI > 0,6) nie zależy od progu między 5 a 6°, ale „38/40” jest wartością zależną od progu.
Poprawka: dodać kontrole z niezerowym wnioskiem: ruch „na ślepo” ze stałą prędkością w losowym kierunku, komparator 1-bitowy z poprawnym znakiem (jako dolna granica „trywialnego sukcesu”), kryterium raportować jako krzywą sukcesu vs tolerancja.

**6. [MINOR→MAJOR dla interpretacji] „Opóźnienie 100 ms: 0/20” to artefakt reguły świeżości, nie test opóźnień.**
`sensory.py:104` (`age > self.max_age`) i `safety.py:117` (`sensor_age > L.max_sensor_age`), obie 0,05 s. Przy 100 ms każda klatka jest „stale” (290 klatek/próbę, 5800 taktów z flagą na 20 prób) — sterownik nie dostaje żadnego obrazu (mediana błędu 19,90° = brak ruchu); wynik taki sam dla tolerancji 1e-6. Przy 50 ms: `age` wychodzi z zaokrągleń zmiennoprzecinkowych ≈ 0,05 ± ε, więc **90 z 295 klatek/próbę** jest odrzucanych jako stale (flagi 3600/40 prób, 1800/20) — to losowe odrzucanie ~30 % klatek, nie opóźnienie. Wpływ na sukces zerowy w mojej próbie (dev 1001–1020, `exp_misc.py delay`): snn 50 ms: 6/20 (tol 0) vs 6/20 (tol 1e-6, flagi 0); wyniki per ziarno identyczne (te same 6 sukcesów), ale mediana czasu do |e|<5° 1,26 s → 0,31 s. Regulator P przy 50 ms: 20/20 w obu wariantach (0,26°). Zatem pogorszenie SNN przy 50 ms jest cechą SNN (adaptacja b_a, filtry τ 50+100 ms, histereza progu), nie warstwy bezpieczeństwa i nie opóźnienia per se; stwierdzenie w VALIDATION_PLAN („zachowanie częściowo kształtuje warstwa bezpieczeństwa”) nie ma poparcia przy 50 ms (flagi nie zmieniają sukcesu), a „100 ms: 0/20” nie mówi nic o dynamice.
Uwaga o repo: `loop.py` ma teraz parametr `max_age` (`loop.py:96, 105, 111`) — to jest ten sam problem rozwiązany po fakcie.
Poprawka: porównywać `age > max_age + 1e-9` (albo liczyć wiek w całkowitych taktach); dla badania opóźnień ustawić `max_age` > opóźnienia; raportować flagi per źródło/typ.

**7. [MINOR] Manifest „zamrożony” nie zgadza się już z plikiem na dysku.**
`validation/v5_confirm_manifest.json:10` podaje `loop.py` sha256 `375894a4…`; obecny plik ma `67ce92f4…` (dodane `max_age`; patrz 6). Pozostałe pliki z manifestu (encoder, visual_path, analyze_v5, decoder, safety, sensory, so101) zgadzają się z prefiksami hashy z manifestu. Przebieg konfirmacyjny użył starej wersji (jej hash jest w `v5_confirm_*.json: code_sha256`).
Poprawka: zachować snapshot zamrożonego `loop.py` obok manifestu (jak `results/v4/protocol_snapshot_v4_open_loop.py`) i dopisać nowy hash jako wersję 2.

**8. [MINOR] Pętla nie sprawdza znaku/odmowy kalibracji.**
`loop.py:200–202`: sprawdza `version`, `J0`, `offset`; nie sprawdza `calib.sign_ok`, `calib.refused` ani `slope > 0`; `decoder.py` odrzuca tylko slope = 0 (`decoder.py:74`). Plik V4 v2 z ujemnym slope (`v4_open_loop.py:156–158` zapisałby `refused`) przeszedłby w pętli jako dodatnie sprzężenie zwrotne. Ujemny slope *zostałby* odrzucony w V4 (wniosek T4), ale ochrona jest tylko w jednym miejscu.
Poprawka: `assert v4["calib"]["slope_hz_per_rad"] > 0 and "refused" not in v4["calib"]` w `main`.

**9. [MINOR] Offset dekodera = 0 z definicji (pusty obraz), nie z punktu symetrii.**
`v4_open_loop.py:141–145`. Dla J0 = 0,2 siatka kalibracji daje −31 Hz przy az = 0 (≈ −3,6° przy slope 495,6) i d(0,8; 0,8) = −30 Hz w siatce otwartej pętli (asymetria danych L/P DNa02). W zamkniętej pętli zmierzony błąd surowy jest mały (średni końcowy e = +0,30° dla snn vs +0,21° dla P, konfirmacja), ale metryka `signed_final_e_mean` (`analyze_v5.py`: mnożenie przez znak az0) kasuje stały błąd boczny między próbami o przeciwnych znakach — nie używać jej do tezy „brak biasu”.

**10. [MINOR] Robustness „światło” i „szum” nie testują sieci.**
Zmiana jasności ×0,3 obniża średni piksel 175,8 → 52,8, a wektor g pozostaje 0,786 / 0,232 (normalizacja Webera w `encoder.py:58–62`); ×2,5 → 203,2 (nasycenie), g = 0,882 / 0,308. Szum σ 15/30 jest tłumiony przez blur 3×3 i próg `c_min`. To własności enkodera, nie sieci. Dystraktor zielony po stronie przeciwnej (r = 1,25 cm) przesuwa błąd do 5,6° (snn 0/12; P 6/12), r = 1,75 cm: 11,2° (0/12; P 0/12) — brak selekcji celu; dystraktor czerwony ignorowany (10/12 snn, 12/12 P).

**11. [MINOR] Statystyka i higiena.**
(a) `analyze_v5.py:10–14` wzór Wilsona jest **poprawny**; −0,0 dla k = 0 wynika z kasowania zmiennoprzecinkowego (c−h ≈ 1e-17 → `round` → −0,0); poprawka: `max(0, …)`/`min(1, …)`. Sprawdzone: 38/40 → [0,835; 0,986]; 40/40 → [0,912; 1,0]; 0/40 → [−0,0; 0,088]. (b) McNemar dokładny jednostronny i Bonferroni 0,05/3 poprawne; snn vs P: 2 vs 0 rozbieżne pary, p = 0,25 (brak istotnej różnicy w liczbie sukcesów; różnica w błędzie: −1,223°, CI [−1,404; −1,044]). (c) Efektywne n: 40 prób, ale **jedna** sieć, **jedna** kalibracja, **jedna** poza Q_POSE, **jedna** scena — wnioskowanie dotyczy rozkładu początkowych (az0, ρ, szumu), nie rodziny sieci. (d) `loop.py:67` i `:107`: ten sam `seed` dla geometrii (`trial_spec`) i szumu ALIF — wspólny strumień bitów; bez wpływu na sterownik, ale proponuję `seed+10_000_000` dla szumu. (e) Zakazane zakresy ziaren sprawdzane (`FORBIDDEN`, `loop.py:47`), ale nie ma ochrony przed 2001–2100 użytymi dwukrotnie — dopisać do `FORBIDDEN`/rejestru zużytych ziaren.

## 3. Szczegóły eksperymentów

### 3.1 Wyciek (pytanie 1)
Przejrzane: `loop.py` (`run_trial`: do kontrolera trafiają `obs.frame.image` przez `SensoryGate`, `TargetEncoder.encode`, `SteerDecoder.step`, `SafetyLayer.step(cmd, obs.q, now, sensor_age)`); `encoder.py` (tylko `image`); `so101.py::observe` (obraz, q, qd, touch, t); `bearing()` używa `sim.d.qpos` piłki, wołane jedynie do `e`. `place_ball` używa `fk(Q_POSE)`. Brak wycieku. Piłeczka nie jest dotykana przez ramię (maks. przemieszczenie piłki w 20 próbach snn i 20 P: 1,0·10⁻⁴ m).

### 3.2 Czy SNN jest przekaźnikiem (pytanie 2)
Patrz problemy 1 i 2. Dodatkowa informacja: część A V4 (J0 0,2) pokazuje, że LC10a_L napędza „wyłącznie” DNa02_L (227 Hz vs 0,0) — push-pull z docstringu nie jest widoczny w stanie ustalonym, bo kontralateralne hamowanie obcina się do 0 Hz; ujawnia się dopiero przy obu g > 0,5.

### 3.3 Kalibracja i znak (pytanie 3)
Kalibracja na `spot_clip` (96×128, r = 9 px, az z obrazu) — niezależna od symulatora ⇒ brak cyrkularności z prawdą pętli. Odmowa przy ujemnym slope: `v4_open_loop.py:155–158`; odmowa przy |slope| < 2 Hz/rad: `decoder.py:46–58`. Brak sprawdzenia w pętli (problem 8). Znak „L−P > 0 ⇒ w lewo” i mapowanie `PAN_LEFT = −1` pochodzą z testów inżynierskich (`so101.py`), nie z danych.

### 3.4 J0 / s_min — patrz problem 4.

### 3.5 Trudność zadania — patrz problem 5.

### 3.6 Odporność w scenie 3D (dev 1001–1012, n = 12; snn / P)
base 11/12 (mediana 2,02°) / 12/12 (0,38°); światło ×0,3: 11/12 / 12/12; ×2,5: 11/12 / 12/12; ciepłe: 10/12 / 12/12; szum σ 15: 11/12 / 12/12; σ 30: 10/12 / 12/12; czerwona piłka po przeciwnej stronie: 10/12 / 12/12; zielona przeciwna r 1,25 cm: 0/12 / 6/12; r 1,75 cm: 0/12 / 0/12; piłka ruchoma 0,03 m/s (kinematycznie): 11/12 / 12/12; piłka częściowo poza polem (|az0| 38–46°, połowa pola ≈ 43°): 9/12 / 12/12; ρ = 0,35: 0/12 / 12/12; ρ = 0,50: 0/12 / 12/12; kula r = 1,0 cm: 0/12 / 12/12.

### 3.7 Statystyka — patrz problem 11.

### 3.8 Czas i bezpieczeństwo — patrz problem 6.

## 4. Czego NIE sprawdziłem
- Nie replikowałem pełnego protokołu konfirmacyjnego (ziarna 2001–2100 wykluczone).
- Nie uruchamiałem testów na innej pozie niż `Q_POSE`, innej wysokości kamery ani w innych warunkach tarcia piłki.
- Nie sprawdzałem, czy slope kalibracji zmienia się z wersją mujoco/renderera.
- Wpływ wspólnego strumienia bitów (problem 11d) na wyniki nie został zmierzony (tylko wykazane wspólne `random_raw`).
- Ruchomy cel testowany tylko kinematycznie, jedna prędkość (0,03 m/s ≈ 8,6°/s przy ρ = 0,2 m).

## 5. Polecenia i ziarna

### 5.0 Ziarna
Próby: 1001–1020 (tasowania, kontrole, opóźnienia, ref.), 1001–1010 (J0), 1001–1012 (odporność), 1001–1008 (zasięg). Odstępstwo: ziarna RNG tasowania/permutacji = próba + 100 000 (101 001–101 021; zgodnie z konwencją loop.py), ziarna szumu obrazu 15001 i 30001; żadne nie leży w 0–39, 300–399, 2001–2100, 102 011–102 050 ani 2201, ale leżą poza 1001–1999 zadanym w poleceniu. Brak commitów, brak zmian poza tym plikiem.

### 5.1 Komendy (wszystkie z katalogu scratch; `PY=/Users/admin/so101_fly_project/.venv/bin/python`)
- `$PY -I -B t0_repro.py` — odtworzenie dev1 (1001–1003): maks. |Δe| = 0,0 dla 3/3.
- `$PY -I -B net_struct.py` — struktura sieci i siła wejściowa po tasowaniu.
- `$PY -I -B t1_grid.py` → `grid.npy` — siatka odpowiedzi (gL, gR) → DNa02.
- `$PY -I -B exp_shuffle.py` → `out_shuffle.json`, `log_shuffle.txt` (tabela w problemie 1).
- `$PY -I -B exp_null2.py perm` / `exp_null2.py toy` → permutacje i przekaźnik zabawkowy.
- `$PY -I -B exp_j0.py` → `out_j0.json` (tabela w problemie 4).
- `$PY -I -B exp_robust.py snn` i `exp_robust.py classical` → odporność w scenie 3D (3.6).
- `$PY -I -B exp_scan.py` → zasięg (ρ, r) (problem 3).
- `$PY -I -B exp_misc.py delay` / `exp_misc.py ref` → opóźnienia i kontrole trywialności.
- `$PY -I -B t_stats.py`, `t_light.py` — przeliczenie analizy (odtwarza `analysis_confirm.json`: True), Wilson, jasność sceny.
Uruchamiane maks. 2 procesy równolegle; czasy ≈ 2,8 s/próbę.

## 6. Podsumowanie rekomendacji
1. Poprawić sformułowanie wniosku: dane są *wystarczające*, nie *konieczne*; zachowanie niszczą tasowania/permutacje, które zrywają lateralizację, nie zachowujące siłę wejściową/wyjściową.
2. Dodać do protokołu kontrole: przekaźnik ipsilateralny (model), komparator 1-bitowy, permutacje, tasowanie z zachowaniem siły wejściowej.
3. Zapisać zakres roboczy SNN (ρ ≤ ~0,26 m, r ≥ ~2 cm; J0 ∈ [0,1; 0,2]) i przeprowadzić nowy protokół poza nim.
4. Naprawić porównanie wieku klatki (`age > max_age + ε`), traktować „100 ms: 0/20” jako artefakt reguły świeżości.
5. Zachować snapshot zamrożonego `loop.py`; zaktualizować manifest.
6. Dodać asercję znaku kalibracji w `loop.py`.
