# Red Team runda 2: SHUF_WITHIN_SIDE v2 (warstwa × strona) i szkic protokołu V5 v3

Data: 2026-10-29. Przedmiot: `flymind/side_shuffle.py` (v2), `test_side_shuffle.py`, `v5v3_control_check.py` + `results/v5v3_prep/v5v3_control_check_v2_20261029T165755.json`,
`validation/v5v3_protocol_DRAFT.md`, `v5v3.py`, `test_v5v3_analysis.py`. Zmieniony jest tylko ten plik; bez `bio2`, bez pętli zamkniętej, `python -I -B`, ≤ 2 procesy.
Ziarna: tasowania v2 1441–1443 (+ 1451 dla dawki LC×LC), ALIF 1101–1110 (10 ziaren × 2 strony), symulacje statystyczne 1201. Skrypty/wyniki: `/private/tmp/claude-501/-Users-admin-so101-fly-project/31945ef1-39f8-4198-827d-6c45c0d388b2/scratchpad/redteam3v2/` (b1–b6, `*.out`, `*.json`, `*.npy`).
Testy autora uruchomione bez zmian: `test_side_shuffle.py` → OK (27 asercji), `test_v5v3_analysis.py` → OK (15).

## Odpowiedzi (skrót)

| # | Pytanie | Odpowiedź |
|---|---|---|
| 1 | Czy `properties()` może przejść przy złamanym deklarowanym niezmienniku? | **Reguła zamiany — tak (luka niskiego ryzyka); żaden z 16 deklarowanych niezmienników z osobna — nie znalazłem.** Sieć z przestawionymi wagami między postsynaptycznymi neuronami tej samej grupy (zachowane: stopnie, siły, multizbiory wag per neuron, skład grup per neuron: liczba i sumy dodatnie/ujemne, blok grupa×grupa) + jedna legalna zamiana ⇒ wszystkie 17 `KEYS` True, `nontrivial` True (b1.py, przypadek P2). Brakuje niezmiennika: **multizbiór wag per neuron i per grupa partnerów** — prawdziwe wyjścia `shuffle_within_side` go spełniają (b6.py: True, 3/3 instancje), więc dodanie go jest tanie |
| 2 | Czy v2 izoluje „wzorzec połączeń w bloku (w tym wzajemność LC10a)” przy stałych: lateralizacji, architekturze warstw, wejściach DNa02, składzie grup per neuron? | **Tak co do konstrukcji, z trzema zastrzeżeniami (niżej): (a) w praktyce izoluje wyłącznie blok LC10a×LC10a — jedyny blok, którego przetasowanie zmienia odpowiedź pętli otwartej; (b) zmienia wiele wskaźników wzorca naraz (wzajemność, trójkąty, klasteryzacja, asortatywność, ρ bloku), więc nie wskazuje który; (c) zachowuje, jako stałe, także 57–58% masy \|w\| (top 1% krawędzi: 97–99%)** |
| 3 | Czy deklarowany ograniczony wniosek w szkicu jest poprawny, a protokół bez błędów? | **Nie — wniosek jest nieaktualny (opisuje v1) i za szeroki; w protokole są 3 wady do poprawy przed zatwierdzeniem (rodzina Holma z D1/D2, uśrednianie efektów o przeciwnych znakach, asymetryczne wykluczanie SimError).** SESOI 1°, test permutacyjny ze zmianą znaku i n = 50 są poprawne (weryfikacja symulacją), ale moc dla spodziewanego efektu jest niska |
| 4 | Czy kontrola jest gotowa do zatwierdzenia przez użytkownika? | **Kontrola (kod): TAK, bez blokerów kodu.** **Protokół: jeszcze NIE** — 3 blokery dokumentu/analizy (B1–B3 w §5), wszystkie naprawialne bez ponownego uruchamiania eksperymentów |

## 1. `properties()` — próby obalenia (b1.py)

Stan faktyczny: v2 sprawdza 17 warunków (`KEYS`): stopnie, siły (podpisane), multizbiory wag we/wy per neuron, skład grup per neuron (liczba, suma dodatnich, suma ujemnych, dla pre i post, po wszystkich etykietach z `np.unique`), blok grupa×grupa, Dale, autapsy, krawędzie modelowe, `nontrivial`. Luki zamknięte względem rundy 1 (przypadki A, B, C wykryte).

Pozostałe luki:
| Lp | Opis | Dowód | Waga |
|---|---|---|---|
| Q1a | Brak niezmiennika „multizbiór wag per neuron **i per grupa**” (`side_shuffle.py` `properties`, zestaw `KEYS`). Konstrukcja: post q ma od grupy A wagi {1,3}, od M {2,2}; post q' odwrotnie ({2,2}/{1,3}); W1 = zamiana wzorców wag między q i q'. Zachowane wszystkie 16 warunków pozostałych | `b1.py` P (edge set bez zmian, `nontrivial=False` — wychwycone tylko przez `nontrivial`), **P2 (to samo + jedna legalna zamiana): failing=[] , nontrivial=True** | MINOR/MAJOR: prawdziwe tasowanie nie może tego zrobić (b6.py), więc ryzyko dotyczy tylko błędu implementacyjnego; ale `properties()` jest jedyną siatką bezpieczeństwa i abort-kryterium protokołu |
| Q1b | `properties()` ufa przekazanym `groups`; zbyt gruba siatka grup (np. wszystkie „A”) osłabia wszystkie testy bloków/składu (przypadek R: `failing=['nontrivial']` tylko). `v5v3.py` nie asertuje liczności grup (test to robi: `test_side_shuffle.py`, `grep_["groups"]==…`, lecz test ≠ przebieg) | b1.py R | MINOR: dodać w `run()` `assert grep_["groups"] == {...}` i zapisać hash etykiet w manifeście |
| Q1c | `nontrivial` = „≥ 1 krawędź zmieniona”; sam nie gwarantuje wymieszania. W praktyce chroni `complete` (swaps == target) i `changed_frac` ≈ 0,67, ale `changed_frac` nie jest w abort-kryterium | kod | MINOR: wymagać `changed_frac > 0.5` w `run()` |
| Q1d | `swappable` w raporcie (`edges_in_swappable_keys` = 13 210) zawiera krawędzie, które nigdy się nie ruszą: 59 klas (175 krawędzi) o wspólnym pre lub post, w tym wszystkie 151 wejść DNa02 (jedna klasa na neuron) | b5.py | MINOR (kosmetyka raportu) |
| Q1e | Nie porównywane: `sh.sign`, `sh.nt` | kod | MINOR |

Nie znalazłem sposobu na: zmianę stopnia, siły, zbioru wag, bloku grupa×grupa lub składu grup per neuron bez wykrycia (przypadki F, G, I z rundy 1 nadal wykrywane — testy autora to potwierdzają; sam nie powtarzałem F/G/I na v2 poza uruchomieniem jego testów).

## 2. Co v2 izoluje, a co nadal różni DATA i SWS v2

### 2.1 Zachowane (zweryfikowane)
LI ≤ 2 skoki = 1,0000 (te same E_ipsi, E_kontra); wejścia DNa02 identyczne; spis warstw (LC→LC 6189, LC→mid 4750, mid→LC 310, mid→mid 2089, mid→DN 151, LC→DN 0) identyczny; wejście LC na każdy pośredni (korelacja = 1,0); multizbiory wag we/wy per neuron i per grupa (b6.py). Mieszanie: dla v2 akceptacja zamian ≈ 51% (131 921 prób / 67 550 zamian), `complete=True` (3/3); zachowane krawędzie bloku LC×LC 18,5–19,6% (przy gęstości bloku ≈ 16% = poziom przypadkowy); przy 0,5 zamian/krawędź wzajemne pary LC–LC 555 vs 545 przy 5 → 5 zamian/krawędź wystarcza.

### 2.2 Co się zmienia (statyczne, b2.py; DATA | SWS v2 1441–1443)
| Własność | DATA | SWS v2 |
|---|---|---|
| wzajemne pary LC–LC | 2450 | 532–559 |
| cykliczne trójkąty w bloku LC×LC | 25 295 | 8 320–8 415 (−67%) |
| klasteryzacja bloku LC×LC (nieskierowana) | 0,601 | 0,309–0,313 |
| asortatywność sił we→we po krawędziach LC→LC (korelacja) | 0,213 (out→in 0,223) | 0,013–0,035 (out→in 0,033–0,063) |
| ρ(W_LC×LC) | 21,01 | 19,59–19,69 (−7%) |
| wzajemne pary mid–mid | 599 | 249–266 |
| ρ(W_mid×mid) / max Re | 32,74 / 24,93 | 31,47–32,33 / 24,25–24,63 |
| masa ścieżek 3-skokowych LC→DNa02 (ipsi) | 3 487 776 | 3 365 807–3 384 923 (−2,9…−3,5%) |
| zachowane krawędzie: LC×LC / LC→mid / mid→LC / mid→mid | 100% | 18,8–19,6% / 47,6–48,3% / 11,9–16,5% / 37,5–38,6% |
| zachowana masa \|w\| (wszystkie krawędzie), top 10%, top 1% | 100% | 57–58%, 67–68%, 97–99% |
| klasy z unikalnym kluczem (waga, grupa, grupa) | — | 300 krawędzi, 16,3% masy (v1: 157 / 10,3%) |
| λ_max (Re) całej W | 26,07 | 26,27–26,35 (JSON autora) — widmo praktycznie niezmienione, w odróżnieniu od v1 (+34%) |

Wniosek 2.2: przetasowanie wymazuje całą nielosową strukturę bloku LC×LC (wzajemność, trójkąty, klasteryzację, asortatywność) i mid×mid (wzajemność). Zmienia się więc *wiele* własności motywowych naraz; v2 pozwala powiedzieć „wzorzec wewnątrzblokowy”, nie „wzajemność”.

### 2.3 Gdzie to widać dynamicznie (b3.py, ALIF, 300 ms, szum 2 mV, 10 ziaren × 2 strony = 20 wartości; SEM w nawiasach; ipsi DNa02, Hz)
| Sieć | g = 0,50 | 0,55 | 0,60 | 0,70 |
|---|---|---|---|---|
| DATA | 14,7 (4,0) | 61,8 (1,3) | 98,0 (2,2) | 163,2 (1,7) |
| SWS v2 1441 / 1442 / 1443 | 6,5 / 6,7 / 5,0 | 51,8 / 50,3 / 51,5 | 89,7 / 91,8 / 91,7 | 166,2 / 167,7 / 169,2 |
| tylko blok LC×LC tasowany (reszta = DATA), 0,03 zam./kr. (wzajemne LC–LC 1918) | 12,2 | 59,2 | 98,5 | 163,0 |
| … 0,1 (1157) | 6,0 | 56,7 | 96,7 | 165,2 |
| … 0,2 (734) | 8,7 | 54,7 | 96,7 | 170,0 |
| … 0,5 (555) | 1,7 | 51,2 | 90,7 | 172,8 |
| … 5 (545) | 7,3 | 52,2 | 91,5 | 170,2 |
| DATA + blok LC×LC z SWS 1441 | 6,5 | 53,5 | 97,0 | 168,8 |
| SWS 1441 + blok LC×LC z DATA | 12,0 | 59,2 | 95,8 | 159,5 |
| DATA + blok mid×mid z SWS 1441 | 14,3 | 60,7 | 97,8 | 162,8 |

Odczyty: (i) deficyt SWS v2 przy słabym napędzie (−9…−10,5 Hz przy g 0,50–0,55; −6…−8 przy 0,60) zlokalizowany w bloku LC×LC (replikuje dekompozycję autora na innych instancjach i ziarnach); blok mid×mid i permutacje LC→mid są niewidoczne. (ii) Zależność dawka–odpowiedź względem wzajemności LC–LC jest monotoniczna (1918→12,2/59,2; 1157→6,0/56,7; 734→8,7/54,7; ≈550→1,7–7,3/51–52 Hz przy g 0,50/0,55). (iii) **Znak efektu odwraca się przy wysokim napędzie:** g = 0,70, SWS ≥ DATA o +3…+6 Hz (autorskie JSON: 167–169 vs 162,6; moje: 166–169 vs 163,2), tzn. DATA jest *bardziej stroma-w-dół*, nie tylko „czulsza”. (iv) Przy pełnym napędzie brak różnicy (226,3 vs 224,4–225,4 Hz, kontra 0 wszędzie). Istotność: przy g 0,55 różnica 10 Hz to ≈ 6 łącznych SEM; przy 0,50 i 0,60 ≈ 2 SEM; to są SEM ze 20 skorelowanych (strona) wartości — traktować orientacyjnie.

### 2.4 Ograniczenia identyfikacji (po stronie kontroli)
- **Enkoder** (`encoder.py:74-75`) daje identyczny prąd wszystkim LC10a danej strony; dlatego zamiana „który LC10a → który pośredni” jest niewidoczna (wejście LC na pośredni jest zachowane co do wagi). Wniosek z V5 v3 = wniosek o tej sieci pod enkoderem jednorodnym na stronę.
- **Warstwa „mid”** to jedna grupa 147 neuronów (LLPC1 ×43, AOTU, LAL…): typ komórki nie jest zachowany w mid×mid (np. AOTU→LAL może stać się AOTU→AOTU). Dynamicznie niewidoczne (tabela), ale „struktura typów” jest zmieniona.
- Definicja warstw zależy od reguły selekcji `s_min = 5` i od jednej sieci (J0 0,2); nie testowano innych.
- 57–58% masy \|w\| i 97–99% najsilniejszych 1% krawędzi pozostaje na miejscu (m.in. 175 krawędzi w klasach nieruchomych i 300 z unikalnym kluczem), więc „topologia” testowana to *wzorzec niskowagowych krawędzi*. Wynik zerowy DATA ≈ SWS v2 nie mówi nic o roli silnych krawędzi.

## 3. Poprawny, ograniczony wniosek (propozycja zdania do protokołu)
„H1 testuje, czy wzorzec połączeń wewnątrz bloków warstwa×strona (operacyjnie: blok LC10a×LC10a — wzajemność 2450→~550, trójkąty 25,3k→8,4k, klasteryzacja 0,60→0,31, asortatywność 0,22→0,03) wpływa na zachowanie, gdy zachowane są: lateralizacja ścieżek ≤ 2 skoki (1,0000), architektura warstw, wejścia DNa02, stopnie, siły i multizbiory wag każdego neuronu oraz skład grup jego partnerów, przy enkoderze jednorodnym na stronę. Nie rozróżnia wzajemności, klasteryzacji i asortatywności, nie testuje roli silnych krawędzi (97–99% najsilniejszych 1% pozostaje na miejscu) ani tożsamości LC10a→pośredni (niewidocznej dla tego enkodera). Strona = somaSide, nie strona synaps.”

## 4. Protokół — analiza logiki (zadanie 3)

Zweryfikowane i poprawne: test permutacyjny ze zmianą znaku, zera zostają (b4.py: 1500 symulacji, n = 50, dodatnio skośne d, równe średnie → odrzuceń 5,7% i 5,0% przy nominalnych 5%; d normalne 5,1%); Holm (testy autora); decyzja `decide` (testy autora); znak d = DATA − kontrola spójny w `v5v3.py` i w nagłówku (UWAGA: sekcja „Wiedza posiadana” cytuje V5 v2 jako +1,61 w konwencji *kontrola − DATA*; w v3 oczekiwany znak to −1,6 — ryzyko pomyłki przy czytaniu); sparowane ziarna i wspólne sceny.
Moc (przybliżenie normalne σ_d = 2,6°, n = 50, SE = 0,368°; b-inline): efekt 1,0°: α = 0,05 → 0,776; α = 0,025 → 0,684; α = 0,0167 → 0,628; α = 0,0125 → 0,588; α = 0,01 → 0,557 (zgodne ze szkicem 0,56–0,78). Równoważność (CI90 w ±1°): wymaga |średnia| < 0,395° → P = 0,72 dla d = 0.

| Prawdziwe d | P(„pierwszy lepszy”, α_Holm = 0,0167) | P(„równoważne”) | P(nierozstrzygnięte) |
|---|---|---|---|
| 0 | 0,01 | 0,72 | ≈ 0,27 |
| −0,25° | 0,04 | 0,61 | ≈ 0,35 |
| −0,5° | 0,15 | 0,38 | ≈ 0,47 |
| −1,0° | 0,63 | 0,05 | ≈ 0,32 |
Jeśli efekt zbliża się do wielkości sugerowanej przez pętlę otwartą (kilka procent napędu, przeciwne znaki zależnie od g), najbardziej prawdopodobny wynik to „nierozstrzygnięte” lub „równoważne w granicach 1°”.

## 5. Problemy

### BLOCKER (dokument/analiza; nie wymagają nowych eksperymentów)
**B1. Szkic opisuje kontrolę v1 i interpretuje H1/H3 zbyt szeroko.** Sekcja „SHUF_WITHIN_SIDE — definicja” (strona-tylko, 10 zamian/kraw., „niewymienialne 157”, „lateralizacja 0,86–0,90 × DATA”), „Wiedza posiadana” (221/0 vs 0–4 Hz, v1) i „Interpretacja” ("organizacja połączeń z danych daje wkład … ponad skład stron") są nieaktualne wobec v2 (LI = 1,0000; wejścia DNa02 identyczne; 5 zamian; 300 unikalnych krawędzi). H3 „SWS vs SHUF_STR — czy samo zachowanie stron zmniejsza błąd” jest błędnie nazwane: v2 zachowuje warstwy, wejścia DNa02 i LI, nie tylko strony. Naprawa: zdanie z §3, przemianować H3 na „zachowanie struktury blokowej (warstwa×strona, wejścia DNa02, LI)”, zaktualizować liczby; dopisać do ograniczeń: enkoder jednorodny, silne krawędzie nieruszone, strona somy.
**B2. Rodzina Holma {H1,H2,H3,D1,D2} obniża moc głównej hipotezy.** D1/D2 są opisowe, a w rodzinie; D2 (P_CTRL) i H2 prawdopodobnie mają bardzo małe p i zajmują pierwsze rangi, więc H1 testowane jest przy α ≈ 0,0125–0,0167 (moc dla 1°: 0,59–0,63 zamiast 0,78 przy α = 0,05). Naprawa: H1 jako jedyna hipoteza główna α = 0,05; H2, H3 jako drugorzędne (Holm na {H2,H3}); D1, D2 bez p-wartości lub w osobnej rodzinie.
**B3. Estymand = średnia z całego zakresu scen może znosić efekty przeciwnych znaków.** Pętla otwarta: DATA lepsza przy słabym napędzie (−9…−10 Hz przy g 0,50–0,55), SWS v2 lepsza przy g 0,70 (+3…+6 Hz). Ruch ρ ∈ [0,16; 0,35] m obejmuje oba reżimy (V5 v2: efekt w ρ 0,24–0,30). Decyzja „równoważne” dla średniej puli (CI90 w ±1°) mogłaby nastąpić przy rzeczywistych efektach ±1° o przeciwnych znakach. Naprawa: wyspecyfikować przed przebiegiem warstwy (np. terciele ρ lub początkowego g z DATA) jako drugorzędne z przewidywanymi znakami i uznać „równoważne” za dotyczące wyłącznie średniej puli; albo zaostrzyć zakres ρ do rejonu słabego bodźca (decyzja użytkownika).

### MAJOR
**M1. Wykluczanie SimError** (`v5v3.analyze`, protokół „Wykluczenia”; `v5v3.run` abort > 5% × 250 prób): do 12 błędów w jednym warunku (24% par) mieści się poniżej progu, a SimError jest prawdopodobnie skorelowany z trudnością sceny i warunkiem ⇒ obciążenie sparowanej różnicy. Naprawa: limit na liczbę *wykluczonych ziaren* (≤ 5% = 2) i/lub limit per warunek; analiza wrażliwości (błąd = ostatnia wartość / kara) obok głównej.
**M2. Moc dla spodziewanego efektu** (§4): przy d ≈ −0,5° P(rozstrzygnięcie) ≈ 0,53. SESOI 1° jest uzasadniony odniesieniem do V5 v2 (1,61° dla znacznie mocniejszej kontroli); dla v2 spodziewany efekt jest mniejszy. Protokół powinien jawnie podać oczekiwane prawdopodobieństwa wyników i że „równoważne” znaczy „nie większe niż ~1°”, nie „topologia nieistotna”.
**M3. `properties()` — Q1a** (brak multizbiorów wag per neuron i per grupa) oraz brak asercji grup w `run()` (Q1b) i progu `changed_frac` (Q1c).
**M4. Mechanizm niezidentyfikowany:** efekt tasowania LC×LC jest monotoniczny względem wzajemności, ale wzajemność, trójkąty, klasteryzacja i asortatywność zmieniają się razem (dawki w §2.3). Jeśli wniosek ma mówić „wzajemność”, wymagana jest kontrola zachowująca wzajemność (nie istnieje). Nie nazywać mechanizmu w interpretacji.

### MINOR
- m1. `v5v3.run`: `sys.exit` przy naruszeniu kontroli/SimError traci dotychczasowe wyniki (zapis tylko na końcu). Dopisywać próby przyrostowo.
- m2. Bootstrap percentylowy CI95: pokrycie 0 w symulacjach 93,7–94,2% (n = 50, d skośne) — lekko liberalne; BCa albo tolerancja przy granicznych wynikach.
- m3. Test permutacyjny i bootstrap odpowiadają na różne pytania (sharp null vs średnia); reguła `decide` łączy oba. Akceptowalne, ale podać jawnie.
- m4. `edges_in_swappable_keys` zawiera krawędzie nieruchome (Q1d).
- m5. Opcjonalnie (dodatkowe warunki w pętli zamkniętej, jeśli budżet prób pozwala): (i) tasowanie *tylko* bloku LC×LC (etykiety jednoznaczne dla nie-LC), (ii) SWS v2 z blokiem LC×LC z DATA. Pozwalają zlokalizować efekt pętli zamkniętej tak jak pętla otwarta.

## 6. Komendy
```
cd /private/tmp/claude-501/-Users-admin-so101-fly-project/31945ef1-39f8-4198-827d-6c45c0d388b2/scratchpad/redteam3v2
PY=/Users/admin/so101_fly_project/.venv/bin/python
$PY -I -B b1.py   # przypadki przeciwne dla properties() (P, P2, R)
$PY -I -B b2.py   # tasowania v2 1441–1443 + dawki LC×LC 0,1/0,5/5 (ziarno 1451); metryki: wzajemność, trójkąty, klasteryzacja, asortatywność, ρ, kept
$PY -I -B b3.py   # ALIF: DATA, SWS v2 ×3, dawki LC×LC (0,03–5), dekompozycje; ziarna ALIF 1101–1110; g 0,50/0,55/0,60/0,70
$PY -I -B b4.py   # type-I testu permutacyjnego / pokrycie bootstrapu (ziarno 1201)
$PY -I -B b5.py   # masa/top-1% zachowane, klasy unikalne i nieruchome
$PY -I -B b6.py   # multizbiory wag per neuron i per grupa (prawdziwe tasowanie: zachowane)
$PY -I -B /Users/admin/so101_fly_project/flymind/test_side_shuffle.py ; $PY -I -B /Users/admin/so101_fly_project/flymind/test_v5v3_analysis.py
```
Ograniczenia: otwarta pętla ALIF z jednorodnym napędem; dawki LC×LC na jednej instancji tasowania (ziarno 1451); SEM z 20 skorelowanych wartości; moc/prawdopodobieństwa wyników z przybliżenia normalnego i σ_d = 2,6° z V5 v2 (nie z v3); nie oceniałem aktualizacji `v5v3.py`/protokołu do etykiet v2 (zgodnie z poleceniem).

## 7. Podsumowanie (10 linii)
1. Kod v2 jest poprawny i spełnia deklarowane niezmienniki: LI = 1,0000, wejścia DNa02 i spis warstw identyczne, mieszanie wystarcza przy 5 zamianach/krawędź (akceptacja 51%).
2. `properties()` ma jedną realną lukę: brak multizbiorów wag per neuron i per grupa; sieć z przestawionymi wagami przechodzi wszystkie 17 `KEYS` (b1 P2). Prawdziwe tasowanie je spełnia, więc naprawa jest tania.
3. v2 w praktyce izoluje wzorzec połączeń bloku LC10a×LC10a: tasowanie samego tego bloku odtwarza SWS, przywrócenie go odtwarza DATA, mid×mid i LC→mid są niewidoczne.
4. Wzorzec LC×LC to jednocześnie wzajemność (2450→~550), trójkąty (−67%), klasteryzacja (0,60→0,31), asortatywność (0,22→0,03), ρ bloku (−7%); v2 nie wskazuje który.
5. Efekt zmienia znak z napędem: DATA lepsza o ~9–10 Hz przy g 0,50–0,55, SWS v2 lepsza o 3–6 Hz przy g 0,70, brak różnicy przy pełnym napędzie.
6. Zachowane jest 57–58% masy \|w\| i 97–99% top 1% krawędzi; wynik DATA ≈ SWS v2 nic nie mówi o silnych krawędziach.
7. Szkic protokołu opisuje jeszcze v1, a H1/H3 sformułowano za szeroko; ograniczony wniosek zaproponowano w §3.
8. Wady protokołu: rodzina Holma z D1/D2 (moc 0,59–0,63 zamiast 0,78), uśrednianie efektów o przeciwnych znakach, wykluczanie SimError do 24% par; test permutacyjny, SESOI i n = 50 są poprawne (type-I 5,0–5,7%).
9. Przy spodziewanym d ≈ −0,5° prawdopodobieństwo „pierwszy lepszy” to 0,15, a „równoważne” 0,38 — protokół powinien to jawnie podać.
10. Gotowość: kontrola — tak; protokół do zatwierdzenia — jeszcze nie, dopóki B1–B3 (tekst, rodzina testów, warstwy ρ/g) nie zostaną poprawione; nowe eksperymenty niepotrzebne.
