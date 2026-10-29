# FlyMind — plan walidacji

Stan na 2026-10-28. Progi liczbowe oznaczone „propozycja” to decyzje projektu, nie standardy naukowe.
Zakres: tylko `flymind/`; bez importu `bio2`, bez zmian w plikach Stage 1, bez sprzętu.

## Zasada

Każde twierdzenie FlyMind ma przypisany poziom dowodu i kontrolę, która mogłaby je obalić. Od 2026-10-28 (sesja 2)
pętla jest zamknięta w MuJoCo: obraz → enkoder (model) → LC10a → sieć z danych → DNa02 → dekoder → warstwa
bezpieczeństwa → SO-101 (V4–V5 niżej). Sprzęt fizyczny — poza zakresem bez osobnej zgody.

## Poziomy walidacji

| Poziom | Pytanie | Stan | Kryterium |
|---|---|---|---|
| V0 Poprawność kodu | Czy moduły robią to, co deklarują? | Testy zielone (2026-10-28, sesja 2, uruchomione): connectome 20, snn_interface 20, alif 14, sensory 26, decoder 23, safety 21, latency 15, epg_ring 32, encoder 19, visual_path 9; symulator T1–T9 zielone | Wszystkie testy zielone przed każdym etapem; każda poprawka z testem regresji (jak T9) |
| V1 Wierność danym | Co w sieci pochodzi z connectomu, a co z modelu? | `channel_provenance`, raporty `build`; wejście DNa01 w 92–96 % z krawędzi modelowych; 2 MN prostownika bez NT w danych | Każda krawędź: dane albo `ModelEdge` z uzasadnieniem; udział modelu raportowany dla każdej populacji dekodera; „sterowanie z connectomu” tylko dla kanałów z udziałem modelu < 10 % (propozycja) |
| V2 Reżim dynamiki | Czy sieć działa w sensownym zakresie? | Zmierzone (krok 5): pierścień CX na surowych wagach — wygasanie przy J0 ≤ 0,1, trwała aktywność 0,14–0,2, nasycenie od 0,3 | J0 i transformację wybiera się wg kryteriów dynamiki PRZED testami zachowania: punkt stały ciszy, brak eksplozji, nasycony < 10 % neuronów (propozycja). Bez strojenia J0 pod wynik zachowania |
| V3 Obliczenia obwodu | Czy obwód koduje to, co twierdzimy? | V3.1 struktura EPG — wykonane (niżej); kodowanie PFL3→DNa02: RMS odczytu ≈ 0,055 na nowych ziarnach (krok 7); chwyt tylko z danych nie zamyka szczęki | Patrz „V3” |
| V4 Wejście sensoryczne | Czy enkoder przekazuje kierunek bodźca? | Wykonane (eksploracja v1 → v2): mediana błędu 2,7° na azymutach testowych; kontrole zgodne (niżej) | Błąd azymutu na `spot_clip` z prawdą; brak bodźca → 0; kontrole sieci |
| V5 Pętla zamknięta | Czy ramię orientuje się na cel dzięki sieci? | v1: 38/40; v2 (szersze zadanie): 28/50 — lateralizacja konieczna, topologia z danych +16 pp (czułość na słaby bodziec); regulator P 50/50 | Patrz „V5” |
| V6 Bezpieczeństwo i czas | Czy wynik nie jest artefaktem ograniczeń lub opóźnień? | Liczniki interwencji per źródło; B1–B3 zmierzone (niżej) | Interwencje raportowane osobno; zachowanie nie może zależeć od stałego przycinania (< 5 % taktów z flagą — propozycja); B4 (opóźnienia) po V4 |

## V3 — obliczenia obwodu

### V3.1 Struktura cykliczna EPG — WYKONANE (2026-10-28)

Moduł `epg_ring.py`, testy `test_epg_ring.py` (29 asercji, zielone). Skrypty analizy: jednorazowe, w scratchpadzie
sesji (nie w repozytorium).

**Pytanie.** Czy przypisanie kątów EPG do pierścienia CX wynika z danych, czy jest założeniem?

**Jak było w bio2 (odczyt tekstu, bez importu).** Glomerulus z sufiksu `instance` → ręcznie wpisana stała `RING`
(`bio2/extract_bio2.py:26`) → kąt = klin · 2π/16 (`bio2/brain.py:71`) → „idealna geometria”: wszystkie EPG równo
według rangi (`bio2/brain.py:85–91`).

**Dane.** Adnotacje MaleCNS v1.0: 46 EPG (typ dokładnie `EPG`; `EPGt`, 4 neurony L9/R9, wykluczony jawnie),
2–4 EPG na glomerulus (L1–L8, R1–R8). Litera sufiksu = `somaSide` w 46/46 — z tego pliku nie da się odróżnić strony
glomerulusa PB od strony somy. Wagi minconf 0,5: EPG→EPG 842 krawędzie, 11 486 synaps, 0 autapsów.
Brak danych o położeniu w EB i o regionie synapsy (EB vs PB).

**Metoda.** Macierz glomerulusów A[pre, post]; agregacja główna `pairs` (synapsy / liczba par neuronów — wybrana
przed obliczeniem), pomocnicza `sum`; przekątna (wewnątrz glomerulusa) wyłączona z celu. Dokładny cykl Hamiltona
o maksymalnej wadze w S = A + Aᵀ (Held–Karp). Postać kanoniczna względem obrotu i odbicia.

**Wyniki.**

| | `pairs` | `sum` |
|---|---|---|
| Dokładny cykl (kanonicznie) | L1–R1–L8–R2–L7–R3–L6–R4–L5–R5–L4–R6–L3–R7–L2–R8 | ten sam |
| Udział wagi poza przekątną na cyklu | 82,2 % | 81,7 % |
| Waga cyklu | 725,5 | 5683 |
| Margines nad najlepszą alternatywą lokalną (2-opt / zamiana) | 8,8 % | 9,0 % |
| Wzajemni 2 najsilniejsi partnerzy = sąsiedzi w cyklu | 16/16, bez remisów | 16/16 |

- Cykl jest tym samym cyklem co `RING` w bio2 (inny punkt startu zapisu). 5683 to dokładne optimum przy `sum`;
  odtworzone innym kodem niż wcześniejszy skrypt ad hoc (ten sam autor i dane — nie jest to niezależna replikacja).
- Permutacja etykiet glomerulusów między neuronami (zachowuje graf i liczebności; ziarno 1001):
  wzajemni partnerzy — dane 16, null mediana 12, max 15, n = 10 000, p = 0,0001;
  udział wagi na dokładnym cyklu — dane 0,822, null mediana 0,317, max 0,394, n = 200, p = 0,005.
  Obie wartości p to granica rozdzielczości (żadna permutacja nie dorównała danym).
- Bootstrap neuronów w obrębie glomerulusów (n = 500, ziarno 1002): ten sam cykl w 100 % prób.
- Kierunek (krawędzie skierowane wzdłuż cyklu): cyrkulacja −0,019; null z losowym odwracaniem par
  (n = 10 000, ziarno 1003) 95 % [−0,049; +0,048], p dwustronne = 0,46 — brak informacji o orientacji.

**Wrażliwość skupienia C = |Σ rᵢ e^{iθᵢ}| / Σ rᵢ na geometrię** (aktywność równa w obrębie glomerulusa):

| Wzorzec | A (jeden kąt na glomerulus) | B (równo w klinie wg bodyId) | R (ranga, reguła bio2) |
|---|---|---|---|
| jeden glomerulus | 1,000 | 0,995 | 0,998 |
| równomierny | 0,031 | 0,030 | 0,000 |
| von Mises κ = 0,5 | 0,213 | 0,212 | 0,242 |
| von Mises κ = 2 | 0,682 | 0,679 | 0,701 |
| von Mises κ = 8 | 0,926 | 0,921 | 0,931 |

C jest niezdefiniowane przy Σ r = 0 (zwracane `None`, nie 0); nie zależy od skali r, obrotu ani odbicia.

**Wnioski.**
- Z danych: kolejność cykliczna 16 glomerulusów z dokładnością do obrotu i odbicia; stabilna; wyraźnie powyżej
  permutacji etykiet; kierunek krawędzi nie wyznacza orientacji.
- Założenia: sufiks = glomerulus PB; równe odstępy glomerulusów; kąty wewnątrz glomerulusa (B, R); punkt zero
  i kierunek obiegu.
- Nie do ustalenia z dostępnych plików: położenie w EB; czy cykl odzwierciedla EB, czy sąsiedztwo w PB i połączenia
  między półkulami.
- Konsekwencja dla pomiaru wzgórza: podawać wariant geometrii i odejmować C dla aktywności równomiernej
  (A/B ≈ 0,03); faza wektora populacji ma sens tylko po kalibracji znanym bodźcem i zawsze z możliwym odbiciem.
- FlyMind NIE odtworzył biologicznej geometrii CX — ustalił strukturę połączeń EPG.

### V3.2 Lokalizacja wzgórza w ALIF — WYKONANE (2026-10-28); wynik negatywny TYLKO bez wzmocnienia Delta7 (zawężone po Red Team, niżej v3)

Skrypt `v32_bump.py` (protokół w nagłówku, ustalony przed uruchomieniem), metryka `epg_ring.bump_metrics`
(testy: 32 asercje, zielone). Sieć tylko z danych: EPG 46, PEN_a 20, PEN_b 22, Delta7 42 (130 neuronów,
7606 krawędzi, 123 798 synaps); EPGt i PEG wykluczone. ALIF: szum 2 mV, b_a = 0,5 wszędzie. Bodziec 12 mV do EPG
jednego glomerulusa przez 300 ms, każdy z 16 glomerulusów × ziarna 1001–1005 (80 prób na J0); permutacje kątów
ziarno 1101. Czas: 9,9 s.

| J0 | V2 dopuszczalne | EPG aktywne w bodźcu (mediana) | dC w bodźcu (A, mediana) | Po bodźcu (650–1000 ms) |
|---|---|---|---|---|
| 0,05 | tak | 6,5 % (= tylko pobudzony glomerulus) | 0,969 | cisza we wszystkich 80 próbach (C niezdefiniowane) |
| 0,1 | tak | 6,5 % | 0,969 | cisza we wszystkich 80 |
| 0,14 | nie (eksplozja w części prób) | 6,5 %; w ≥ 25 % prób cały pierścień | 0,969 (q25 = 0,035) | 56/80 cisza; reszta dC ≈ 0,02, błąd fazy ≈ 77° |
| 0,2 | nie | 100 % (≈ 190 Hz) | 0,021 | dC ≈ 0,013, błąd fazy ≈ 73° |
| 0,3 | nie (nasycenie 24 %) | 100 % (≈ 220 Hz) | 0,003 | dC ≈ 0,000, błąd fazy ≈ 90° |

Warianty geometrii B i R dają ten sam obraz (R: C_uniform = 0, więc dC = C).

**Wniosek (v1, zawężony 2026-10-28 po Red Team).** W sieci ALIF z samymi wagami z danych, BEZ wzmocnienia hamowania
Delta7 (G_INH = 1), przy b_a = 0,5 i na tej siatce J0, nie powstaje
zlokalizowane wzgórze generowane przez sieć:
- przy dopuszczalnych J0 aktywne są tylko bezpośrednio pobudzone EPG — C ≈ 1 opisuje bodziec, nie sieć
  (permutacja kątów daje C ≈ 0,47 tylko dlatego, że aktywne są 2–4 neurony), a po bodźcu aktywność gaśnie;
- przy większych J0 aktywność obejmuje cały pierścień, C jest bliskie C_uniform, faza przypadkowa.

**Ograniczenia.** Jedna siatka J0 (luka 0,10–0,14 niezbadana — zagęszczenie byłoby NOWĄ wersją protokołu, nie
dostrajaniem); b_a = 0,5 w CX (bio2: 0); jedna amplituda bodźca; liniowa transformacja synaps; bez PEG/EPGt.
bio2 uzyskuje wzgórze wagami uśrednionymi profilowo, wzmocnieniem Delta7 (G_INH = 8) i zerową adaptacją w CX —
to decyzje modelu, nie dane. Wynik nie przesądza, że okablowanie z danych nie wspiera wzgórza; pokazuje, że
nie wspiera go w tej parametryzacji.

#### V3.2 wersja 2 — EKSPLORACJA (2026-10-28), wynik negatywny dla G_INH = 1

`v32_bump.py --protocol 2` (protokół dopisany w nagłówku przed uruchomieniem). Siatka J0 0,10–0,14 co 0,01 ×
b_a ∈ {0,5; 0,0} (0,0 = brak adaptacji jak w bio2); reszta jak v1. Nowe miary ustalone przed uruchomieniem:
`epg_active_outside` (aktywne EPG poza pobudzonym glomerulusem) i „wzgórze trwałe” (okno 650–1000 ms:
C zdefiniowane ∧ dC > 0,2 ∧ |błąd fazy| < 45°). Czas 17,5 s. Kontrola: wiersze wspólne z v1 (J0 0,10 i 0,14 przy
b_a 0,5; 960 wierszy) mają C, dC i fazę identyczne co do bitu.

| b_a | J0 dopuszczalne (V2) | „Wzgórze trwałe” (odsetek prób, każde J0, każdy wariant) | Po bodźcu |
|---|---|---|---|
| 0,5 | 0,10; 0,11 | 0 | J0 ≤ 0,11: cisza 80/80; 0,12–0,14: aktywne 4–24/80 prób, dC ≤ 0,07, faza przypadkowa (74–151°) |
| 0,0 | 0,10 | 0 | 0,10: cisza 80/80; 0,11–0,13: aktywne 7–34/80, dC ≤ 0,02; 0,14: cały pierścień (≈ 200 Hz), dC ≈ 0 |

EPG aktywne poza pobudzonym glomerulusem w bodźcu: mediana 0 we wszystkich warunkach poza J0 0,14 przy b_a 0
(tam 100 %). Przejście jest więc od „tylko bodziec” do „cały pierścień”, bez stanu pośredniego na tej siatce.

**Słabość kryterium V2 (wykryta przy tej analizie).** „Średnia po bodźcu > średnia w bodźcu” liczy średnią po
całej sieci; przy bodźcu obejmującym 2–4 neurony nawet słaba trwała aktywność kilku neuronów spełnia warunek
„eksplozji”. Kryterium z definicji wyklucza więc stany trwałe, których V3.2 szuka. Wniosek o braku wzgórza od tego
nie zależy (odsetek „wzgórza trwałego” = 0 również w warunkach niedopuszczalnych), ale kolejne wersje powinny
definiować eksplozję inaczej (np. przez nasycenie albo wzrost w czasie) — jako nowa wersja protokołu.

**Wniosek eksploracji (zawężony).** Przy G_INH = 1 ani gęstsza siatka J0, ani brak adaptacji nie dają trwałego,
zlokalizowanego wzgórza EPG. Zdanie „dane + ALIF nie dają wzgórza” w ogólnej postaci jest FAŁSZYWE — patrz v3.

#### V3.2 — Red Team (sesja 2, `results/redteam/v32_v2_redteam.md`) i weryfikacja

- Odtworzenie: v1 i v2 przeliczone ponownie (`results/v32/rerun/`) — tabele i dopuszczalność identyczne z archiwum
  sesji 1 (skopiowanym do `results/v32/`); liczby podgrafu (130 n, 7606 krawędzi, 123 798 synaps) potwierdzone
  niezależnym zliczeniem z feathera; V3.1 odtworzone skryptem `v31_reproduce.py` (wynik `results/v31_reproduce_20261028.txt`)
  — te same liczby (82,2 %, null max 0,394, p 0,0001/0,005, bootstrap 100 %, p kierunku 0,46). Ten sam kod — nie
  niezależna replikacja.
- Uwagi RT potwierdzone: (1) brak osi G_INH — przy mnożnikach z bio2 (Delta7 → EPG/PEN ×G_INH, Delta7 → Delta7 ×0,3)
  i b_a = 0 pojawia się trwały łuk EPG: zweryfikowane MOIM kodem (`scratchpad/verify/ginh.py`) — G_INH 16 / J0 0,2:
  39/48 prób, trwa do 2,5 s; G_INH 8 / J0 0,14: 15/48; G_INH 16 przy b_a 0,5: 2/48; G_INH 1: 0/48.
  (2) Kontrola pozytywna (idealny pierścień, te same ALIF) trzyma wzgórze tylko przy b_a = 0 w wąskim paśmie — więc
  v1 i połowa v2 (b_a 0,5) nie mogły wykryć wzgórza nawet w idealnej sieci; protokół nie miał kontroli pozytywnej.
  (3) Kryterium dopuszczalności v1/v2 wyklucza z definicji stany trwałe. (4) Efektywne n ≈ 16 glomerulusów, nie 80.
  (5) Drobne: „dC ≤ 0,07” w tabeli v2 nieścisłe (max 0,080 w A, 0,101 w R); C_perm różni się między v1 i v2 (wspólny
  strumień RNG 1101), C/dC/faza identyczne.

#### V3.2 wersja 3 — POTWIERDZENIE (2026-10-28, `v32_v3_confirm.py`, ziarna 2001–2005, tasowanie 2101–2105)

Protokół i hipotezy zapisane w nagłówku przed uruchomieniem (hash: `results/v32/v3_protocol_sha256.txt`). Sieć jak v1
+ ZMIANY MODELU: Delta7 → EPG/PEN ×16, Delta7 → Delta7 ×0,3, J0 0,2, b_a 0. Czas 15 s.

| Warunek | Trwałe wzgórze (650–1000 ∧ 2150–2500 ms) | 95 % CI Wilsona | glomerulusy ≥ 3/5 ziaren | różne zbiory aktywnych EPG |
|---|---|---|---|---|
| dane | 65/80 (0,81) | 0,71–0,88 | 13/16 | 12 |
| tasowanie krawędzi (stopnie, siła wyjściowa i znak zachowane) | 0/80 | 0–0,05 | 0 | 0 |
| dane, b_a 0,5 | 3/80 | 0,01–0,11 | 1 | 3 |

H1, H2 (Fisher p = 1,2·10⁻³⁰; przy n efektywnym 16 glomerulusów nadal 13/16 vs 0/16), H3 spełnione.
**Wniosek:** przy dwóch założeniach modelu (wzmocnienie hamowania Delta7 ×16, brak adaptacji) sieć z okablowaniem
z danych utrzymuje zlokalizowaną, zgodną z bodźcem aktywność EPG ≥ 2,2 s po bodźcu; ta sama sieć po tasowaniu — nie.
**Czego to NIE pokazuje:** ciągłego atraktora (stany skwantowane: 12 zbiorów aktywnych), integracji ruchu (PEN nie
testowane), że ×16 jest biologiczne (to parametr modelu), odporności na inne G_INH/J0 poza punktem eksploracji.

#### V4/V5 — Red Team (sesja 2, `results/redteam/v4_v5_redteam.md`) i weryfikacja

Bez przecieku prawdy do sterownika (tylko obraz, q, t; `bearing()` wyłącznie w ocenie; piłeczka nieruszana). Liczby
`analyze_v5` odtworzone przez RT. Uwagi istotne — zweryfikowane MOIM kodem (`scratchpad/verify/rt2.py`, ziarna 1001–1010):
1. **[major, potwierdzone]** Tasowanie z H2 nie zachowuje siły wejściowej (wejście DNa02 spada z ~462 do 107–193 mV/spike
   łącznie). Tasowanie zachowujące siłę wejścia i wyjścia każdego neuronu (zamiany tylko krawędzi o identycznej wadze;
   `visual_path.shuffle(equal_weight=True)`): **10/10 sukcesów** (RT: 20/20). Permutacja tego, które neurony zasilają
   DNa02 L/R (RT): 3–4/20. ⇒ Zachowanie wymaga LATERALIZACJI (która strona LC10a dociera do którego DNa02 i z jaką siłą),
   nie wykazano roli szczegółowej topologii.
2. **[major, RT]** Dane wystarczają, ale nie są konieczne: zabawkowy przekaźnik ipsilateralny LC10a → DNa02 (krawędzie
   modelowe, bez pośrednich i hamowania) 20/20 i dokładniej (0,67° vs 1,85°); komparator 1-bitowy sign(gL − gR) 20/20.
3. **[major]** H3/H4 nie różnicują sieci: |az0| ≥ 10° > tolerancja 5°, więc no_vision nie może wygrać z konstrukcji;
   zamiana stron oblewa dla każdego sterownika niosącego znak. Są to kontrole poprawności łańcucha, nie dowód roli SNN.
4. **[major, potwierdzone]** Martwa strefa SNN: cel dalej (ρ = 0,30 m) → snn **0/10**, P **10/10** (RT: ρ ≥ 0,28 m 0/8;
   piłeczka 1,5 cm 0/8 vs 8/8). Zakres zadania (ρ ≤ 0,24 m) kończy się 4–6 cm przed załamaniem — zakres wybrany na dev
   bez sprawdzenia granic.
5. **[major, RT]** J0: reguła v2 ustalona po v1; v1 (J0 0,05) w pętli 2/10; J0 0,1 i 0,2: 10/10; 0,3: 1/10 (cykl
   graniczny); s_min 3 i 10: 9/10 — okno pracy ~×2 w J0.
6. RT: odporność na oświetlenie ×0,3/×2,5, szum σ 15/30, czerwony dystraktor, ruch 3 cm/s: 10–11/12 — zasługa
   normalizacji enkodera, nie sieci; ZIELONY dystraktor po przeciwnej stronie: 0/12 (brak selekcji celu; P 6/12, 0/12).
7. RT: sukces zależy od tolerancji (6°: 40/40, 4°: 29/40); P vs SNN w liczbie sukcesów 2 vs 0 par, p = 0,25 (różnica
   w dokładności istotna, w sukcesie nie). Statystyki (Wilson, McNemar, Bonferroni, bootstrap) poprawne.
8. Porządkowe: `loop.py` po zamrożeniu zmieniony (max_age, opóźnienia dla P, strażnik znaku slope) — wersja zamrożona
   w `validation/v5_frozen_code/`, a bieżący kod odtwarza trajektorie potwierdzenia co do bitu (sprawdzone: snn
   i snn_shuffle, ziarna 2011–2012). Ziarno ALIF = ziarno próby (wspólne z losowaniem celu) — bez wpływu na wnioski.

**Wniosek V5 (obowiązujący):** pętla obraz → enkoder → sieć z danych LC10a → DNa02 → dekoder → SO-101 działa
w MuJoCo (38/40 na zamrożonym protokole). Sieć przenosi STRONĘ celu dzięki lateralizacji połączeń w danych;
nie wykazano, że jej topologia ponad lateralizację ma znaczenie dla zachowania; prosty przekaźnik i regulator P działają
równie dobrze lub lepiej, są odporniejsze na opóźnienie i odległość celu. Udział SNN = wierne przeniesienie znaku
(z danych) przez progową, adaptującą dynamikę, która dodaje martwą strefę i cykl graniczny.

**Kontrast z V3.2 v3 (eksploracja, ziarna 1001–1003, `scratchpad/verify/v3eq.py`):** wzgórze EPG NIE przeżywa
tasowania zachowującego siłę (0/48 vs 39/48 dla danych) — tam topologia ponad siłę ma znaczenie (przy G_INH 16, b_a 0).

#### V5 wersja 2 — POTWIERDZENIE (2026-10-29, `loop_v2.py`, ziarna 2051–2100, n = 50, jeden przebieg)

Protokół, hipotezy, przewidywania i interpretacja zamrożone przed przebiegiem: `validation/v5_v2_protocol.md`,
`v5_v2_manifest.json`, kod `validation/v5_v2_frozen_code/`. Zadanie szersze niż v1: az0 ~ U(−30°, 30°), ρ ~ U[0,16; 0,35].
Wynik: `results/v5/v5v2_20261029T065804.json`, analiza `analysis_v5v2_confirm.json`. Stage 1 przed/po: OK.

| Warunek | Sukces | 95 % CI | ρ 0,16–0,24 | 0,24–0,30 | 0,30–0,35 | mediana |e| |
|---|---|---|---|---|---|---|
| snn (dane) | 28/50 | 0,42–0,69 | 16/16 | 9/19 | 3/15 | 4,4° |
| snn_eqshuffle (siła zachowana) | 20/50 | 0,28–0,54 | 14/16 | 3/19 | 3/15 | 9,9° |
| snn_dnperm (bez lateralizacji) | 9/50 | 0,10–0,31 | 3/16 | 3/19 | 3/15 | 15,9° |
| toy_relay (model, bez danych) | 22/50 | 0,31–0,58 | 16/16 | 3/19 | 3/15 | 8,1° |
| classical_p | 50/50 | 0,93–1,0 | 16/16 | 19/19 | 15/15 | 0,3° |
| no_vision (przypadek: |az0| < 5°) | 9/50 | 0,10–0,31 | 3/16 | 3/19 | 3/15 | 15,5° |
| snn + zielony dystraktor | 6/50 | 0,06–0,24 | 0/16 | 3/19 | 3/15 | 6,5° |
| P + zielony dystraktor | 17/50 | 0,22–0,48 | 12/16 | 3/19 | 2/15 | 5,6° |

- **H1 (lateralizacja konieczna): SPEŁNIONA** — snn > dnperm, 19 vs 0 par rozbieżnych, p = 1,9·10⁻⁶; dnperm = poziom
  „bez wzroku” (9/50).
- **H2 (topologia ponad lateralizację): „topologia ma znaczenie” wg reguły zapisanej z góry** — snn > eqshuffle,
  8 vs 0 par, McNemar p = 0,0078 < 0,025; różnica +0,16 (95 % CI 0,06–0,26). **Moje przewidywanie („równoważne”) było
  błędne.** Przekaźnik modelowy też gorszy od sieci z danych: −0,12 (CI −0,22; −0,04).
- Gdzie leży różnica (analiza po fakcie, opis): 7 z 8 par rozbieżnych to cele na granicy czułości (ρ 0,24–0,27 m,
  |az0| ≥ 17°); eqshuffle i przekaźnik zatrzymują się 6–14° przed celem (szersza martwa strefa), sieć z danych dochodzi.
  ⇒ Topologia z danych zwiększa **czułość na słaby bodziec** (mniejsza/dalsza piłeczka), nie zmienia znaku.
  Mechanizm (np. zbieżność LC10a na pośrednich, rekurencja wśród LLPC1/AOTU) NIE został zbadany — hipoteza na dalsze prace.
- Opis: regulator P 50/50 — przewaga +0,44 (CI 0,30–0,58); martwa strefa (próg LC10a ~7 mV) ogranicza wszystkie
  warianty SNN w ρ ≥ 0,30 do poziomu przypadku. Dystraktor: SNN 6/50 (0/16 dla bliskich celów), P 17/50 — brak selekcji
  celu w obu, SNN gorszy (−0,22, CI −0,38; −0,06 dla P − SNN).

**Wniosek V5 (obowiązujący po v2):** w pętli orientacji (1) lateralizacja połączeń z danych jest konieczna (H1);
(2) przy zachowanej sile wejścia i wyjścia każdego neuronu topologia z danych daje umiarkowaną, istotną przewagę
(+16 pp), skupioną na granicy czułości — sieć z danych lepiej przenosi słaby bodziec niż sieć przetasowana i niż
przekaźnik modelowy; (3) jako sterownik SNN pozostaje wyraźnie gorsza od regulatora P na tym samym enkoderze
(zasięg, opóźnienia, dystraktor). Ograniczenia: jedna sieć (s_min 5, J0 0,2), jeden enkoder i dekoder, efekt na 8 parach,
tolerancja 5°; próg czułości zależy od J0 (RT: okno ~×2).

### V3.3 Kontrole kodowania skrętu — droga LC10a WYKONANA w V4/V5; droga PFL3 DO ZROBIENIA (nie używana w pętli)

Kalibracja i test na rozłącznych ziarnach i wartościach bodźca (wg zamrożonego protokołu) oraz kontrole:
tasowanie z zachowaniem stopni (ten sam rozkład wag, losowe połączenia), odwrócenie znaku Glu, ablacja PFL3,
ablacja krawędzi modelowych. Jeśli tasowana sieć koduje równie dobrze — nie twierdzić, że ważne jest okablowanie.

### V3.4 Chwyt — ANALIZA DANYCH WYKONANA (2026-10-28, `v34_grip_inputs.py`, wynik `results/v34_grip_inputs_20261028.txt`)

MN „chwytu” bio2 to MN nogi T1 L (Ti flexor 5, Ti extensor 2, ltm 4). Podgraf bio2 zawiera 8,0 % (zginacz), 13,6 %
(prostownik), 9,1 % (ltm) ich wejścia; > 75 % wejścia to interneurony VNC, czuciowe bezpośrednio < 2 %.
Znakowany wpływ czuciowy w 2 skokach: na zginacz MIESZANY i netto ujemny (dzwonkowate +16 943, strunowe +40 768,
ale czucie nogi −29 566, odwłok −63 023 syn²); na ltm netto hamujący (−9887). **Wniosek:** dane nie dają uzasadnionego
odruchu „dotyk → zamknięcie szczęki”; ponadto MN goleni nogi muchy → szczęka robota to analogia, nie homologia.
Chwytaka NIE sterujemy SNN. Jeśli zadanie wymaga chwytu: jawny regulator klasyczny (źródło „classical:”), z wpływem
raportowanym osobno. Ograniczenia: 2 skoki, znak z przekaźnika (Glu = hamowanie — założenie), 6–15 % synaps bez NT.

## V4 — droga wzrokowa (2026-10-28, sesja 2)

**Wybór populacji z danych** (`visual_path.py`). PFL3 to tylko ~1,5 % wejścia DNa02 (380/24 830 i 356/24 527 synaps),
a PFL3 nie ma pola recepcyjnego wzrokowego. Ekran 8 typów wzrokowych (znakowany wpływ 1–2 skoków na DNa02 L/R):
LC10a — push-pull: ipsilateralnie +1877/+2041, kontralateralnie −1734/−2044 (×10³ syn²), symetrycznie; LLPC1 —
ipsilateralne pobudzenie; LC17, LPLC2 — słabe. Wybrano LC10a (detektory małych obiektów, literatura: skręt ipsilateralny)
PO tym ekranie — wybór eksploracyjny. Sieć: LC10a 275 (L 135, R 140, strona = somaSide) + 147 pośrednich (≥ 5 synaps
od LC10a i ≥ 5 do DNa02; wszystkie z przekaźnikiem; m.in. LLPC1 43, AOTU015/001/002) + DNa02 L/R = 424 neurony,
13 510 krawędzi, tylko dane. Pośrednie dostarczają 12 % wejścia DNa02 (6022/49 357) — reszty nie modelujemy.

**Enkoder** (`encoder.py`, MODEL SENSORYCZNY): kontrast chromatyczny (G − (R+B)/2)/jasność średnia → azymut kolumny
z modelu kamery → czułość „oka” L/P σ(az/10°) → g ∈ [0,1) na stronę → 12 mV·g do LC10a tej strony. Brak klatki → g = 0.
Szczęka w kadrze (czerwona/ciemna) i stół (szary) dają c ≤ 0 — nie są celem.

**Część A** (dynamika, `v4_open_loop.py`, ziarna 1001–1003): wszystkie J0 0,05–0,5 dopuszczalne (cisza po bodźcu,
nasycenie ≤ 7 %). Napęd LC10a lewych → wyłącznie DNa02_L (J0 0,2: 227 Hz vs 0), prawych → wyłącznie DNa02_R —
zgodne z przewidywaniem (nieużyte do wyboru J0).

| Część B (spot_clip, test: az ±5/15/25°, ziarna 1004–1006) | v1 (J0 0,05) | v2 (J0 0,2, offset z pustego obrazu, blur 3) |
|---|---|---|
| slope kalibracji (znak ustalony z góry > 0) | +13,6 Hz/rad | +495,6 Hz/rad |
| mediana / RMS błędu kąta | 6,0° / 9,8° | 2,7° / 4,3° |
| brak bodźca, poza polem (50°), brak obrazu | +7,2° (artefakt offsetu) | 0,0° |
| oświetlenie ×0,5 / ×1,5 (mediana) | 6,0 / 7,3° | 2,7 / 3,5° |
| słaby kontrast / szum σ 10 / czerwony dystraktor | 11,7° / 14,9° (detekcja zniszczona) / brak odpowiedzi | 3,8° / 3,5° / brak odpowiedzi |
| zamiana stron LC10a (nachylenie względem intaktnej) | lustro | −1,12 |
| ablacja LC10a / tasowanie ×3 | płasko / płasko | 0,0 / −0,01…0,05 |

v2 zapisana po v1 i przed uruchomieniem, z kryteriami lepszości ustalonymi z góry — wszystkie spełnione. Poprawka
techniczna w v1 (przepełnienie uint8 przy ×1,5) — `results/v4/protocol_sha256_before_run.txt`.
**Wada metryki ruchu (wykryta po fakcie):** protokół szukał opóźnienia tylko ≥ 0 i podał 0 ms. Ponownie (sinus 20°):
przy 0,5 Hz odczyt WYPRZEDZA bodziec o ~140 ms (adaptacja b_a działa różniczkująco), przy 2 Hz opóźnia o ~40 ms.

## V5 — pętla zamknięta w MuJoCo (2026-10-28, sesja 2)

Kod `loop.py`; analiza `analyze_v5.py`; protokół i manifest `validation/v5_confirm_protocol.md`,
`v5_confirm_manifest.json` (zamrożone przed przebiegiem). Zadanie: baza (shoulder_pan) ma ustawić kamerę „eye”
na piłeczkę leżącą w namiarze |az0| 10–30° i odległości 0,16–0,24 m; sukces = |e| < 5° przez całe 2,5–3,0 s.
Błąd e z prawdy symulatora — tylko ocena; sterownik widzi wyłącznie obraz.

Eksploracja (ziarna 1001–1030): snn 10/10 i 19/20; tasowanie 2/10; zamiana 0/10; bez wzroku 0/10; P 10/10.
Opóźnienie klatek 50 ms: 8/20, 100 ms: 0/20 (warstwa bezpieczeństwa: 1800 i 5800 taktów z flagą).

**Potwierdzenie (ziarna 2011–2050, jeden przebieg, n = 40, próby sparowane):**

| Warunek | Sukces | 95 % CI | mediana |e| końc. | mediana t(|e|<5°) | przeregulowanie (med.) | takty z flagą bezp. |
|---|---|---|---|---|---|---|
| snn (dane) | 38/40 | 0,84–0,99 | 1,41° | 0,28 s | 3,2° | 0 |
| snn_shuffle | 3/40 | 0,03–0,20 | 16,4° | 1,48 s | 0 | 0 |
| snn_swap | 0/40 | 0–0,09 | 59,6° (odwraca się 40/40) | — | 0 | 0 |
| no_vision | 0/40 | 0–0,09 | 20,0° | — | 0 | 0 |
| classical_p (omija SNN) | 40/40 | 0,91–1,0 | 0,16° | 0,27 s | 1,5° | 0 |
| snn, opóźnienie 50 ms (opis) | 17/40 | 0,29–0,58 | 3,5° | 1,27 s | 5,7° | 3600 |

H1 (≥ 0,8, dolne CI > 0,6) spełniona; H2 snn > shuffle: 35 vs 0 par rozbieżnych, p = 2,9·10⁻¹¹; H3 snn > swap i H4
snn > no_vision: p = 3,6·10⁻¹²; H3b: swap odwraca się w 40/40. Opis: |e| końcowe P − snn = −1,22° (95 % CI −1,40; −1,04).
Dwie porażki snn: cykl graniczny ±5–6° przy najbliższych celach (ρ ≈ 0,16–0,17 m).

**Opóźnienie — warunek z przebiegu potwierdzającego był ZAKŁÓCONY (wykryte po przebiegu).** Bramka i warstwa
bezpieczeństwa odrzucają klatki starsze niż `max_age` = 0,05 s; klatka opóźniona o 50 ms leży na tej granicy, więc
30 % taktów (3600) dostało `vision_stale` (brak obrazu + zatrzymanie bazy). Wynik 17/40 mierzy więc opóźnienie RAZEM
z polityką odrzucania. Kod zamrożony zarchiwizowany (`validation/v5_frozen_code/`, hashe zgodne z manifestem); potem
dodano opcję `--max-age` (domyślnie 0,05 — zachowanie zamrożone bez zmian). Eksploracja bez zakłócenia
(`--max-age 0.2`, ziarna 1031–1050, zero flag bezpieczeństwa):

| opóźnienie klatek | snn | classical_p |
|---|---|---|
| 0 ms | 19/20 (|e| med 1,48°) | 20/20 (0,13°) |
| 50 ms | 9/20 (2,78°) | 20/20 (0,12°) |
| 100 ms | 7/20 (5,08°) | 20/20 (0,21°) |

Droga SNN jest wyraźnie bardziej wrażliwa na opóźnienie niż regulator P na tym samym enkoderze (eksploracja, n = 20).
Kandydat na przyczynę (scratchpad `v4/fine.py`, spot_clip, ziarna 1001–1002): w strefie ±8° odpowiedź jest stopniowana,
ale lokalne nachylenie L−P ≈ 2× nachylenia z kalibracji ±30° (kalibracja obejmuje nasycenie) → efektywne wzmocnienie
pętli przy celu ≈ 2× zamierzone; do tego asymetria sieci (DNa02_R silniej napędzany; zero L−P przy ≈ +2,5°). W pętli
zamkniętej średnie e w ostatniej sekundzie = +0,25° (sd 0,72) — asymetria nie przenosi się na duży błąd stały.

**Wniosek pierwotny (przed Red Team):** „sieć z okablowaniem z danych przenosi znak i rozróżnia stronę celu; tasowanie
okablowania niszczy zachowanie”. **Po Red Team V4/V5 — ZAWĘŻONY (niżej): tasowanie testowało lateralizację siły
wejścia DNa02, nie szczegółową topologię.** **Nie wynika:** że SNN steruje lepiej
(regulator P na tym samym enkoderze jest dokładniejszy i gładszy — SNN oscyluje ±2°); że to model widzenia muchy
(enkoder kolorowy, skala z kalibracji); że pętla toleruje opóźnienia (50 ms: 17/40, przy masowych interwencjach
warstwy bezpieczeństwa — zachowanie wtedy częściowo kształtuje warstwa bezpieczeństwa).

## V6 — czas (zmierzone 2026-10-28, jedna maszyna: macOS arm64, 10 rdzeni)

- B1, cały takt mierzony bezpośrednio (3 × 3000 taktów): p50 ≈ 4,1 ms, p99 ≈ 8,2–8,5 ms, 1–7 taktów > 10 ms;
  render (observe) p50 ≈ 3,5 ms. Proponowany cel p99 < 7 ms i 0 przekroczeń — NIE spełniony.
- B2, krok ALIF z gęstą W (sieci syntetyczne): 0,02 ms (N = 272), 0,11 (1000), 3,2 (3000), 14,4 ms (10 000) —
  N = 10 000 wymaga macierzy rzadkiej.
- B3, test komponentu (skok prądu PFL3, nie obraz): pierwszy spike DNa02 12 ms; połowa zmiany L−P 30 ms;
  znak ω 80 ms (DNa02) vs 105 ms (+ DNa01).
- Pętla V5 (sesja 2, przebieg potwierdzający, 40 prób × 300 taktów warunku snn, bez innych procesów obliczeniowych):
  cały takt p50 4,3 ms, p99 6,2 ms, max 16,4 ms, 50/12 000 taktów > 10 ms (0,4 %). Etapy (dev1, przy równolegle
  pracującym agencie — zawyżone): render/observe p50 8,1 ms, enkoder 0,26 ms, SNN 424 n × 10 kroków 0,43 ms,
  dekoder 0,06 ms, bezpieczeństwo 0,02 ms, fizyka 0,14 ms. Czas obliczeń ≠ opóźnienie sensomotoryczne: w pętli
  klatka z taktu k wpływa na komendę w tym samym takcie; reakcja ω na bodziec ~40 ms przy 2 Hz (V4).
- Znaleziony błąd mujoco 3.17 (`Renderer.close()` zwalnia bufory w cudzym kontekście GL → ciche śmieci w obrazie);
  poprawka w `SO101Sim.close()`, test regresji T9.

## Procedura (oddzielona od Stage 1)

- Ziarna: rozwojowe 1001–1999; potwierdzające 2001–2100 (jednorazowo); nigdy 0–39 ani 300–399.
- Rozłączne zbiory bodźców: azymuty rozwojowe vs testowe.
- Protokół zamrażany przed potwierdzeniem w `flymind/validation/`: hipotezy, metryki, progi, plan analizy,
  manifest z hashami kodu i parametrów. Po odsłonięciu wyników bez strojenia; zmiana = nowa wersja protokołu.
- Statystyka: rozmiary efektów z CI (bootstrap po ziarnach); jawna korekta wielokrotnych porównań albo hierarchia
  hipotez; raportowane wszystkie próby, także cenzurowane.
- Izolacja: każdy przebieg sprawdza hashe Stage 1, `git status` i `bio2/__pycache__` przed i po; bez importu bio2;
  uruchamianie z `python -I -B`; symulacje w `flymind/` objęte upoważnieniem użytkownika z 2026-10-28 (sesja 2;
  `loop.py` sprawdza hashe Stage 1 przed i po każdym przebiegu); sprzęt — tylko za osobną zgodą.
- Przydział ziaren potwierdzających (zużyte): 2001–2005 (V3.2 v3) + tasowanie 2101–2105; 2011–2050 (V5) + tasowanie
  102 011–102 050; bootstrap analizy 2201. 2051–2100 (V5 v2) + tasowania 102 051–102 100 i 202 051–202 100. Wolne: 2006–2010 (za mało na nowy test — przed
  kolejnym potwierdzeniem trzeba ustalić nową pulę, np. 3001–3100).

## Kolejność

1. Mechanizm przewagi topologii (V5 v2): które pośrednie/ścieżki podnoszą czułość na słaby bodziec — ablacje grup
   pośrednich (LLPC1, AOTU) na ziarnach dev; nowe potwierdzenie wymaga nowej puli ziaren (2001–2100 wyczerpane).
2. Odporność pętli w scenie 3D (oświetlenie, dystraktory, ruchomy cel) — nowy protokół na ziarnach 2051+.
3. Opóźnienia: źródło cyklu granicznego SNN (próg ALIF → odpowiedź quasi-dwustanowa, filtry odczytu) — nowa wersja dekodera/dynamiki jako eksploracja, potem potwierdzenie na 2051+.
4. Chwyt: tylko jako jawny regulator klasyczny, jeśli zadanie go wymaga (V3.4: brak podstaw w danych).
5. Decyzje przy okazji: DNa01 tylko jako jawna ablacja; reakcja warstwy bezpieczeństwa na kontakt ze stołem;
   koszt renderu wobec czasu rzeczywistego.

## Poza zakresem

Walidacja na fizycznym SO-101 (po kalibracji kamery i serw); porównanie z danymi behawioralnymi muchy
(najpierw źródła literaturowe).
