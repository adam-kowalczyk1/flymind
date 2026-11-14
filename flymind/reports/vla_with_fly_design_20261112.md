# FlyMind — VLA z siecią muchy w środku: studium architektury (tylko na papierze)

Raport projektowy, 2026-11-12. Autor: Claude (Fable 5.2), na prośbę właściciela projektu.
Buduje na `fly_learning_research_20261112.md` (z pkt 12A) oraz raportach z 10 i 11 XI — wszystkie nietknięte.
Status pliku: nowy, niezacommitowany, **jedyny plik utworzony w tym zadaniu**. Żadnego kodu, symulacji, treningu,
pobierania modeli, nowych ziaren, commitu ani kontaktu z robotem.

**Etykiety:** **VERIFIED** (sprawdzone; podane źródło), **PARTIALLY VERIFIED**, **REPORTED** (przepisane, sam nie
sprawdzałem), **INFERRED** (mój wniosek), **HYPOTHESIS**, **NOT VERIFIED**, **NOT IMPLEMENTED**.
Co czytałem: *pełny tekst — fragmenty* (strona HTML artykułu, wyszukane fragmenty z liczbami), *streszczenie* (pobrane
dziś z arXiv lub Europe PMC), *raport z dnia…* (czytane wcześniej, dziś nieotwierane).
**[LIT]** literatura · **[FM]** fakty o FlyMind · **[PROP]** moje propozycje i opinie.

---

## 0. Streszczenie dla Adama (prostym językiem)

**Czy da się zbudować jeden model, w którym VLA ma w sobie muchę? Tak. Czy da się to zrobić „bez dzielenia zadań”?
Częściowo — i tu biologia mówi coś ważnego.**

1. **Prawdziwe zwierzęta też dzielą pracę, tylko nie na „zadania”, lecz na „szybkość”.** U muchy mózg nie steruje
   mięśniami. Wysyła ogólne polecenia przez wąskie gardło ok. 1 100–1 300 neuronów zstępujących do „rdzenia” w tułowiu,
   a dopiero ten rdzeń — razem z dotykiem i czuciem stawów, które wchodzą **od razu na dole** — robi ruch. U ośmiornicy
   odcięte ramię samo wykonuje poprawny wyprost. To jest jeden organizm, ale warstwowy. Proponuję zbudować model tak
   samo: **jedno ciało, jedna pętla, różne szybkości** — a nie „VLA robi jedno zadanie, mucha drugie”.

2. **Zalecana architektura („zwierzę z dobudowaną korą”):** sieć muchy z danych jest **jedyną drogą do silników**.
   Dotyk i stan stawów wchodzą prosto do niej, jak u zwierzęcia. Kamera wchodzi dwoma torami: szybkim „okiem muchy”
   (ruch, zbliżanie, mały obiekt — przestrzennie, neuron po neuronie) i wolnym torem „kory” (mały model
   wizyjno-językowy, który rozumie polecenie). Kora **nie wydaje poleceń silnikom**. Robi to, co u samca muchy robi
   pobudzenie w czasie zalotów: **podkręca czułość oka na to, co ważne** — czyli wskazuje, na który obiekt mucha ma
   patrzeć. Resztę robi mucha.

3. **Co można wyrzucić z tradycyjnego VLA:** „eksperta akcji” (w π0 to ok. 300 mln parametrów, w SmolVLA ok. 100 mln),
   wejście stanu robota do modelu językowego i otwartą pętlę „porcji 50 akcji”. **Czego nie da się wyrzucić:** modelu
   rozumiejącego obraz i język — mucha nie ma niczego, co by go zastąpiło.

4. **Jak udowodnić, że mucha naprawdę pracuje:** (a) zbudować tak, żeby nie było drogi obok niej; (b) dać sieciom
   przetasowanym i zwykłej małej sieci **dokładnie to samo uczenie**; (c) zastąpić muchę jej „liniową kopią” — jeśli
   wynik się nie zmieni, mucha jest tylko przewodem; (d) wyłączać konkretne typy neuronów i sprawdzać, czy psuje się
   dokładnie to, co powinno; (e) „odciąć głowę” — zatrzymać korę i sprawdzić, czy odruchy działają dalej.

5. **Uczciwie o korzyściach:** najbardziej prawdopodobny wynik to model **gorszy w skuteczności od zwykłego małego VLA
   i od sterownika klasycznego**, za to z szybką reakcją na dotyk i zaburzenia, czytelnym mechanizmem i dużo mniejszą
   częścią uczoną. Że szybka, „rdzeniowa” warstwa pod VLA pomaga — to już pokazano w 2026 r. (NeuroVLA, DS-VLA), ale
   zwykłymi uczonymi sieciami impulsowymi, nie konektomem. **Czy konektom daje coś ponad to — nie wiadomo, i to jest
   właśnie pytanie badawcze tego projektu.** Jeśli celem byłaby najlepsza skuteczność, odpowiedź brzmi: nie warto.

6. **Zasada z 3 XI:** zalecany wariant jest z nią zgodny w najważniejszym punkcie (mucha steruje wszystkimi stawami,
   przez zmysły), ale **wymaga uczenia części łączących** i daje korze prawo wskazywania celu. To rola C z raportu
   11 XI w nowej, ściślejszej postaci. Decyzja należy do Ciebie.

7. **Terminy:** do 1 XII — nic z tego nie powstanie; najwyżej schemat na plakat jako „kierunek”. Explory 2027 —
   wersja minimalna w symulacji z pełnym zestawem dowodów. Długoterminowo — prawdziwy układ wzrokowy muchy, uczenie
   „dobry/zły”, prawdziwe ramię.

Decyzje są w pkt 13. Niczego nie uruchamiam.

---

## 1. Zakres i metoda

**Zrobione (tylko odczyt):** 10 zapytań do wyszukiwarki arXiv; pobrane dziś streszczenia 14 prac o VLA i hybrydach
(arXiv) oraz 15 prac biologicznych (Europe PMC); przeczytane fragmenty pełnych tekstów π0 i SmolVLA z liczbami
parametrów i czasów. Korzystam też ze źródeł sprawdzonych w raportach 10–12 XI.

**Nie zrobione:** żadnego kodu, symulacji, treningu, pobierania modeli; nie pytałem dziś plików MaleCNS — liczby
o danych pochodzą z raportów 10–11 XI. Pełnych tekstów prac biologicznych nie czytałem.

**Schemat VLA od Adama** (obraz → sieć wizyjna; tekst i stan robota → model językowy; „tokeny akcji” → dyfuzyjny
ekspert akcji) zgadza się z opisem π0: model językowo-wizyjny PaliGemma (3 mld parametrów) plus osobny ekspert akcji
(ok. 300 mln), razem 3,3 mld; porcje po 50 akcji, sterowanie do 50 Hz; 73 ms na jedno wnioskowanie na karcie RTX 4090
(arXiv 2410.24164, *pełny tekst — fragmenty*, VERIFIED). Traktuję go jako typowy przykład, nie wzorzec obowiązkowy.

---

## 2. Czego uczy biologia — osiem zasad, które prowadzą projekt [LIT]

| # | Zasada | Dowód | Co przeczytałem |
|---|---|---|---|
| B1 | **Sterowanie jest warstwowe.** W ssakach i w maszynach powtarza się ten sam układ: wyższe piętra ustalają cele, niższe same domykają pętle ruchu | Merel, Botvinick, Wayne, *Nat. Commun.* 2019, doi 10.1038/s41467-019-13239-6 (przegląd) | *streszczenie* |
| B2 | **Wąskie gardło poleceń.** Mózg muchy steruje ciałem przez ok. 1 100 neuronów zstępujących; neurony „rozkazowe” rekrutują sieci kolejnych, a pełne zachowanie powstaje dopiero z tej rekrutacji | Aymanns 2022 (doi 10.7554/eLife.81527); Braun 2024 (doi 10.1038/s41586-024-07523-9) | *streszczenia* (12 XI) |
| B3 | **Peryferia umieją same.** Odcięte ramię ośmiornicy wykonuje wyprost o niemal normalnej kinematyce; bezgłowa mucha uczy się pozycji nogi | Sumbre i in., *Science* 2001, doi 10.1126/science.1060976; Booker i Quinn 1981 | *streszczenie*; raport 11 XI |
| B4 | **Zmysły wchodzą na różnych piętrach.** Czucie stawów i dotyk trafiają prosto do obwodów ruchowych; siła połączeń przedruchowych jest uporządkowana według wielkości motoneuronu (stopniowe włączanie siły) | Lesser i in., *Nature* 2024, doi 10.1038/s41586-024-07600-z | *streszczenie* |
| B5 | **Zmysły są bramkowane przez własny ruch.** Sygnał ruchu stawu jest tłumiony podczas chodu i czyszczenia przez neurony sterowane z góry; neurony wzrokowe dostają „kopię polecenia”, która wycisza spodziewany obraz własnego skrętu | Dallmann i in., *Nature* 2025, doi 10.1038/s41586-025-09554-2; Kim, Fitzgerald, Maimon, *Nat. Neurosci.* 2015, doi 10.1038/nn.4083; Kim i in., *Cell* 2017, doi 10.1016/j.cell.2016.12.005 | *streszczenia* |
| B6 | **Ciało melduje w górę.** Setki neuronów wstępujących niosą do mózgu stan zachowania: własny ruch do ośrodka łączącego zmysły, konkretne czynności do ośrodka wyboru działania | Chen i in., *Nat. Neurosci.* 2023, doi 10.1038/s41593-023-01281-z | *streszczenie* |
| B7 | **Stan wewnętrzny zmienia czułość zmysłów, a nie steruje mięśniami.** W zalotach rośnie wzmocnienie neuronów LC10a; model pokazuje, że ten jeden tor, po wzmocnieniu, niemal w całości wyznacza podążanie samca za samicą | Hindmarsh Sten i in., *Nature* 2021, doi 10.1038/s41586-021-03714-w | *streszczenie* |
| B8 | **Uczenie siedzi z boku i podpina się pod wyjście.** Ciało grzybkowate dostaje też bogate wejście wzrokowe, a jego neurony wyjściowe łączą się bezpośrednio z neuronami zstępującymi; kompleks centralny ma drogi wyboru zachowania zależnie od kontekstu | Li i in., *eLife* 2020, doi 10.7554/eLife.62576; Hulse i in., *eLife* 2021, doi 10.7554/eLife.66039 | *streszczenia* |

Dodatkowo: łączenie zmysłów u ssaków zachodzi na wielu piętrach naraz (Stein i Stanford, *Nat. Rev. Neurosci.* 2008,
doi 10.1038/nrn2331); móżdżek jako model własnego ciała pozwalający sterować bez czekania na czucie (Ito, *Nat. Rev.
Neurosci.* 2008, doi 10.1038/nrn2332); opóźnienia czuciowo-ruchowe ograniczają każde zwierzę (More i Donelan, *Proc. R.
Soc. B* 2018, doi 10.1098/rspb.2018.0613) — wszystkie *streszczenie*.

**Wniosek dla projektu (INFERRED):** „reagowanie jak mózg” to nie jeden wielki blok, do którego wpada wszystko naraz
(tak działa typowy VLA). To kilka pętli o różnej szybkości, wspólne ciało, zmysły wpięte tam, gdzie są potrzebne,
wąskie gardło między „głową” a „rdzeniem” i meldunek z dołu do góry.

---

## 3. Czy to możliwe i w jakich formach — co już zrobiono [LIT]

### 3.1 Hybrydy „VLA + szybka warstwa inspirowana biologią” (żadna nie używa konektomu)

| Praca | Co zrobiono | Wynik podany przez autorów | Co przeczytałem |
|---|---|---|---|
| **NeuroVLA** — Guo i in., arXiv 2601.14628 | planista wizyjno-językowy („kora”) + moduł „móżdżkowy” + **impulsowy sterownik „rdzeniowy” ze stanem**, z szybkim czuciem stawów i siły | powrót po kolizji 54,8 % wobec 0,0 % dla porównywanych VLA; „rdzeń” na układzie FPGA: 2,19 ms i 0,87 mJ na krok | *streszczenie* |
| **DS-VLA** — Lyu i in., arXiv 2609.32253 | neurony akcji z „dendrytami” i bramką hamującą | LIBERO: 91,6 % normalnie, 87,35 % przy zaburzaniu akcji; w tych samych warunkach OpenVLA-OFT 39,45 %, π0 28,55 %, GR00T 30,75 % | *streszczenie* |
| **CereVLA** — Zeng i in., arXiv 2609.27468 | „móżdżkowy” nadzorca poprawek nad zamrożonym SmolVLA | **na SO-101**: sukces z 57,5 % do 90,0 % | *streszczenie* |
| **SaiVLA-0** — Shi i in., arXiv 2603.08124 | „kora” zamrożona, „most” łączy ją z czuciem stawów, „móżdżek” szybko dekoduje; zapis cech kory do pamięci skraca trening (7,5 h → 4,5 h) | praca koncepcyjna ze wstępnymi wynikami | *streszczenie* |
| **GR00T N1** — NVIDIA, arXiv 2503.14734 | dwa systemy: wolny wizyjno-językowy i szybki ruchowy, uczone razem | — | *streszczenie*; liczby (10 Hz / 120 Hz) raport 10 XI |
| Spike-driven VLA (arXiv 2609.39514), SpikeVLA (2606.27807), SpikingVLA (2610.09710) | całe VLA przerobione na sieci impulsowe | „konkurencyjna” skuteczność przy niższej *szacowanej* energii | *streszczenia* |
| TactileReflex — Feng i in., arXiv 2605.23568 | trzy klasyczne kanały odruchu dotykowego przy ok. 12 Hz | pełny układ 5/5, niepełne najwyżej 1/5 | *streszczenie* |

### 3.2 Sieci z konektomu jako sterowniki (żadna nie ma języka)

FlyGM, FLYNN, FlyCNS, Guan i in., Dhiman, Shiu — omówione w raporcie 12 XI, pkt 3.1 (*streszczenia*). Dwa wnioski
ważne tutaj: (i) po uczeniu sterownik „z muchy” może działać, choć jego część „mózgowa” nic nie wnosi (Guan i in.:
zerowe wyjście zstępujące); (ii) przewaga połączeń nad przetasowanymi bywa złudzeniem kontroli (Dhiman).

### 3.3 Znane choroby VLA, które dotyczą też hybrydy

- **Skróty.** Model potrafi wykonać zadanie, ignorując dowód, który powinien decydować (obiekt przy kamerze nadgarstka
  wypiera cel z polecenia; chwytak zamknięty na pustym i tak unosi) — PerturBot, arXiv 2610.04616 (*streszczenie*).
- **Narzędzia diagnostyczne.** Wyłączanie uwagi dla poszczególnych zmysłów i śledzenie dróg sterowania w π0.5
  i OpenVLA — VLA-Trace, arXiv 2605.30117 (*streszczenie*). Uczenie z „nokautami”, które wymusza zgodność jednostek
  modelu z typami neuronów — Cowley i in. 2024 (raport 12 XI).

### 3.4 Odpowiedź [INFERRED]

- **Możliwe:** tak. Układ „kora + rdzeń ze stanem” istnieje i działa (NeuroVLA); sieci na okablowaniu konektomu da się
  uczyć (FlyGM, FLYNN, Lappalainen).
- **Nowe byłoby:** wstawienie w miejsce „rdzenia” sieci z **prawdziwych, nieuczonych połączeń** i udowodnienie, że
  one coś wnoszą. Takiej pracy nie znalazłem — NOT FOUND (opis mojego szukania).
- **Cztery formy:**

| Forma | Opis | Ocena |
|---|---|---|
| W1 — mucha jako dodatkowy zmysł | stan sieci muchy podawany jako dodatkowe wejście do zwykłego VLA | najłatwiejsze; najłatwiej też modelowi ją zignorować. Tylko jako kontrola |
| W2 — mucha jako rdzeń odruchowy pod VLA | VLA wydaje akcje, mucha dodaje szybkie poprawki | sprawdzony wzorzec (NeuroVLA, CereVLA), ale to nadal „dwa sterowniki” — czyli to, czego Adam nie chce |
| **W3 — „zwierzę z dobudowaną korą”** | **wszystkie polecenia do stawów wychodzą z sieci muchy; kora tylko kieruje jej uwagą** | **zalecane jako projekt badawczy** (pkt 4) |
| W4 — konektom jako cała sieć | całe VLA zbudowane na grafie konektomu i uczone od zera | język nie ma odpowiednika w musze; wszystko uczone; nie zalecam |

---

## 4. Zalecana architektura: W3 — „zwierzę z dobudowaną korą” [PROP]

### 4.1 Schemat

```
                    POLECENIE (tekst)
                          │
   KAMERA ───────────────►│   KORA  (wolna, 1–5 Hz)
   (obraz)   ┌───────────►│   mały zamrożony model wizyjno-językowy
             │            │   + mała uczona głowica
             │            └───────────┬──────────────────────────────┐
             │                        │ K1: MAPA WAŻNOŚCI            │ K2: WARTOŚĆ „dobre/złe”
             │                        │ (gdzie w obrazie jest cel)   │ (dopiero z modułem uczenia)
             │                        ▼                              ▼
             │   ┌──────────────────────────────┐      ┌──────────────────────────────┐
             └──►│ OKO MUCHY (szybkie, co klatkę)│      │ CIAŁO GRZYBKOWATE (z danych) │
                 │ ruch · zbliżanie · mały obiekt│      │ plastyczność — NOT IMPLEMENTED│
                 │ każdy neuron dostaje swój     │      └───────────────┬──────────────┘
                 │ wycinek pola widzenia  × K1   │                      │
                 └───────────────┬──────────────┘                      │
                                 ▼                                      ▼
        ┌───────────────────────────────────────────────────────────────────────────┐
        │  „MÓZG” MUCHY — połączenia z MaleCNS, zamrożone                           │
        │  neurony wzrokowe (LC10a, LC4, LPLC2, LPLC1…) → neurony ZSTĘPUJĄCE        │
        └───────────────────────────────┬───────────────────────────────▲───────────┘
                    wąskie gardło       │ zstępujące                    │ wstępujące
                                        ▼                               │ (meldunek)
        ┌───────────────────────────────────────────────────────────────┴───────────┐
        │  „RDZEŃ” MUCHY — połączenia z MaleCNS, zamrożone        krok 1 ms         │
        │  obwody przedruchowe → MOTONEURONY (zginacze / prostowniki)               │
        │        ▲ dotyk (szczecinki)          ▲ czucie stawów (FeCO)               │
        └────────┼─────────────────────────────┼───────────────────┬────────────────┘
                 │                             │                   ▼
        CZUJNIKI SIŁY na szczęce        POZYCJA / RUCH       MAPA „MIĘŚNIE → STAWY”
        (FSR, wg miejsca)               STAWÓW (serwa)       (stała + mała kalibracja)
                                                                    │  polecenia 100 Hz
                                                                    ▼
                                                        6 SERW SO-101 (regulator w serwie)

        Meldunek w górę: uśredniony stan neuronów zstępujących i wstępujących ──► KORA
        (zamiast „stanu robota” w zwykłym VLA)

        ZABEZPIECZENIA (klasyczne, poza modelem): limity prędkości, siły, zakresu.
```

**Zasada naczelna: nie ma strzałki z kory do stawów.** Do serw prowadzi tylko jedna droga — przez motoneurony muchy.

### 4.2 Bloki — co jest z danych, co uczone, co inżynierskie

| Blok | Pochodzenie | Uczone? | Biologiczny wzór | Stan w FlyMind |
|---|---|---|---|---|
| **Kora:** sieć wizyjna + model językowy | gotowy, mały, zamrożony (klasa SmolVLA: 450 mln parametrów, z czego ok. 100 mln to ekspert akcji, którego tu nie używamy — *pełny tekst — fragmenty*, VERIFIED) | nie (zamrożona) | brak u muchy; „dobudowana kora” | NOT IMPLEMENTED |
| **Głowica K1** (mapa ważności) | nowa | **tak** — mała, uczona na maskach obiektów z symulacji | pobudzenie podnoszące czułość LC10a (B7) | NOT IMPLEMENTED |
| **Oko muchy** | inżynieria: z obrazu kamery liczone trzy mapy (ruch, rozszerzanie, mały obiekt) i podawane **przestrzennie** — każdy neuron dostaje to, co „widzi” w swoim miejscu | nie w wersji podstawowej; ustawienia z góry | zastępuje siatkówkę i płat wzrokowy (54 % neuronów, których nie modelujemy) | dziś: wykrywacz koloru, ten sam prąd dla całej strony |
| **„Mózg” i „rdzeń” muchy** | **połączenia i znaki z MaleCNS v1.0** | **nie** w wersji podstawowej; strojenie parametrów na typ komórki dopiero w etapie T3 za zgodą | B1, B2, B4 | częściowo: do 1 931 neuronów, neurony ALIF |
| **Wejście dotyku** | FSR → grupy neuronów szczecinek według **miejsca** na szczęce | skala: kilka liczb | D0-c: różne typy szczecinek sięgają różnych pul motoneuronów (VERIFIED 11 XI) | dziś: 2 liczby |
| **Wejście czucia stawów** | pozycja → neurony „claw”, ruch → „hook” (typy FeCO zmapowane 5 XI — REPORTED z notatek projektu) | skala: kilka liczb | B4, B5 | dziś częściowo, pogarsza chwyt (83 wobec 90) |
| **Mapa „mięśnie → stawy”** | inżynieria: pary zginacz/prostownik → jeden staw ramienia; przypisanie stałe, zapisane z góry | mała kalibracja liniowa (dziesiątki liczb) | analogia noga → ramię; **to najsłabszy punkt projektu** | dziś: 1 liczba dla szczęki, 1 dla bazy |
| **Meldunek w górę** | średnie aktywności neuronów zstępujących i wstępujących → kilkanaście liczb dla kory | rzut liniowy | B6 | NOT IMPLEMENTED |
| **K2 + ciało grzybkowate** | połączenia z danych + reguła osłabiania synaps (Hige 2015) | **plastyczność w trakcie działania** | B8 | NOT IMPLEMENTED; etap późniejszy |
| **Zabezpieczenia** | kod klasyczny | nie | — | jest; dwie usterki otwarte (1,89 rad/s, wnikanie padów) |

### 4.3 Jak wchodzi każdy zmysł

| Zmysł | Dokąd wchodzi | Jak często | Uwagi |
|---|---|---|---|
| **Obraz — tor szybki** | oko muchy → neurony wzrokowe „mózgu” | co klatkę kamery | częstość klatek kupowanej kamery: NOT VERIFIED (sprzęt niedostarczony) |
| **Obraz — tor wolny** | kora → K1 | 1–5 Hz (INFERRED z czasów π0 na karcie RTX 4090; **na Macu NOT VERIFIED**) | ta sama kamera albo druga, kolorowa |
| **Polecenie** | tylko kora | przy zmianie polecenia | mucha nigdy nie „widzi” tekstu |
| **Dotyk** | prosto do „rdzenia” (szczecinki) | co krok sterowania | częstość odczytu FSR: NOT VERIFIED |
| **Stan stawów** | prosto do „rdzenia” (FeCO); do kory tylko przez meldunek | co krok sterowania | w zwykłym VLA idzie do modelu językowego / eksperta akcji |

### 4.4 Jak sygnał płynie do stawów i z jaką szybkością

1. **Pętla najszybsza (rdzeń):** dotyk i czucie stawów → motoneurony → serwa. Krok sieci 1 ms, polecenie co 10 ms
   (tak działa obecna symulacja; obliczenia 1,65 ms na 10 kroków na jednym rdzeniu — VERIFIED 11 XI). Opóźnienie
   modelu dotyk → pierwszy impuls motoneuronu: 9–29 ms (VERIFIED 11 XI).
2. **Pętla średnia (mózg muchy):** oko → neurony zstępujące → rdzeń. Opóźnienie modelu 25–74 ms (VERIFIED 11 XI).
3. **Pętla wolna (kora):** obraz + polecenie → K1 → zmiana czułości oka. Setki milisekund.
4. **Pętla najwolniejsza (uczenie):** nagroda/kara → zmiana wartości bodźca. Sekundy–minuty. Późniejszy etap.

Kora może się spóźniać albo zamilknąć — mucha dalej trzyma chwyt i reaguje na dotyk. To cecha projektu, nie usterka.

### 4.5 Warianty i modyfikacje

| Wariant | Zmiana | Po co | Koszt dla zasady 3 XI |
|---|---|---|---|
| **W3-min** | bez modelu językowego: K1 z prostego wykrywacza („ten kolor / ta strona”) | pierwszy krok; oddziela pytanie „czy mucha pracuje” od kłopotów z VLM | brak nowego |
| **W3** | jak na schemacie | wersja docelowa na Explory 2027 | uczenie głowicy K1 i kalibracji |
| W3 + K3 (tryb) | kora podaje dodatkowo kilka wolnych sygnałów „trybu” (podejdź / trzymaj / puść) wprost do wybranych neuronów zstępujących | sekwencje typu „podnieś i odłóż” | **sprzeczne** — to sztuczne pobudzanie wybranych neuronów |
| W3 + rusztowanie | sekwencję zadania prowadzi kod klasyczny, przełączając K1 | „podnieś i odłóż” bez K3 | zgodne co do litery; rusztowanie już istnieje |
| W3 + reszta | mały ekspert akcji dodaje poprawkę obok muchy, przez mierzoną bramkę | ratunek dla skuteczności | łamie „nie ma drogi obok”; to już W2 |
| W3 + prawdziwe oko | oko muchy zastąpione modelem płata wzrokowego z konektomu (typ Lappalainen 2024) | usuwa największą inżynierską protezę | wymaga uczenia parametrów oka |
| W3 + uczenie | etap T3 (parametry na typ komórki) lub ciało grzybkowate | lepsze dopasowanie do ramienia; uczenie z doświadczenia | osobna zgoda |

**Jak to można modyfikować dalej:** dołożyć drugą „nogę” (druga pula motoneuronów) dla dwóch ramion; wymienić korę na
nowszy model bez ruszania muchy (uczy się tylko K1 — ten sam pomysł co w SaiVLA-0); wymienić ciało (inne ramię)
zmieniając tylko mapę „mięśnie → stawy”.

---

## 5. Co z tradycyjnego VLA usunąć, zastąpić, zostawić [PROP]

| Blok VLA (typ π0) | Decyzja | Dlaczego |
|---|---|---|
| Sieć wizyjna | **zostaje** (zamrożona) | rozpoznawanie dowolnych obiektów; mucha tego nie ma |
| Osadzenia tekstu + model językowy | **zostaje**, ale mały i zamrożony | język nie ma odpowiednika w musze — tu odpowiedź brzmi „nie da się usunąć” |
| Stan robota jako wejście modelu językowego / eksperta akcji | **zastąpione** | czucie stawów wchodzi na dole, do rdzenia (B4); kora dostaje tylko meldunek (B6) |
| „Tokeny akcji” | **zastąpione** mapą ważności K1 | kora mówi „gdzie patrzeć”, nie „jak ruszyć” (B7) |
| Dyfuzyjny ekspert akcji (π0: ok. 300 mln; SmolVLA: ok. 100 mln parametrów — VERIFIED) | **usunięty** (W3) | jego rolę przejmują połączenia muchy + kilkadziesiąt liczb kalibracji |
| Porcje 50 akcji wykonywane „na ślepo” | **usunięte** | zastępuje je ciągła pętla zamknięta |
| Wielki zbiór danych robotów (π0: ponad 10 000 h; SmolVLA: ok. 30 tys. godzin GPU na wstępny trening — VERIFIED) | **nie używany bezpośrednio**; korzystamy z gotowej, wytrenowanej kory | HYPOTHESIS, że to wystarczy |

**Cena tych cięć (INFERRED):** ekspert akcji daje VLA precyzję, płynność i umiejętność wyboru między kilkoma dobrymi
ruchami. Sieć muchy z 2 tys. neuronów i mapą „noga → ramię” tego nie da. Zręczne zadania (składanie, wkładanie)
pozostaną poza zasięgiem W3.

**„Osobne zwierzę z AI typu VLA” — czy to ma sens?** Tak, jako opis W3: ciało i niższe piętra są zwierzęce (wrodzone
odruchy, mapy, później uczenie „dobry/zły”), a rozumienie świata jest dobudowane. To nie jest mucha, która nauczyła
się mówić — to mucha, której ktoś mądrzejszy pokazuje palcem, co jest ważne.

---

## 6. Jak to trenować [PROP]

### 6.1 Etapy

| Etap | Co się uczy | Co zamrożone | Dane | Gdzie liczyć | Zgoda |
|---|---|---|---|---|---|
| T0 | nic — interfejsy ustawione ręcznie, zapisane z góry | wszystko | — | Mac | mieści się w dzisiejszych zasadach |
| T1 | skale wejść (dotyk, stawy, oko) i kalibracja mapy „mięśnie → stawy”: dziesiątki–setki liczb | mucha, kora | przebiegi sterownika klasycznego w symulacji (darmowe, dowolnie dużo); ewentualnie pokazy z pada | Mac, CPU — HYPOTHESIS, niezmierzone | **tak** (to strojenie) |
| T2 | głowica K1 | mucha, kora | obrazy z symulacji z maskami obiektów (etykiety za darmo) + polecenia | cechy kory liczone raz i zapisane (jak w SaiVLA-0), potem Mac; samo przeliczenie cech: Mac lub kilka godzin GPU — NOT VERIFIED | **tak** |
| T3 | parametry muchy na typ komórki (próg, stałe czasowe) — „szczebel 2” z raportu 12 XI | połączenia, kora | jak T1 lub pomiary biologiczne | Mac lub GPU; uczenie przez sieć impulsową gradientem zastępczym (Neftci 2019) | **tak**, osobno |
| T4 | ciało grzybkowate — uczenie w trakcie działania | reszta | własne doświadczenie robota | Mac | **tak**, osobno |
| T5 | dostrajanie kory (całości) | połączenia muchy | pokazy na ramieniu (SmolVLA: ok. 50 na zadanie — raport 10 XI) | **GPU** | **tak**; nie zalecam przed dowodami z pkt 7 |

### 6.2 Zasady uczenia, żeby nie oszukać samego siebie

1. **Interfejsy mają być „głupie”:** liniowe, wspólne dla typu komórki, przestrzennie uporządkowane, nieujemne. Jeśli
   wejście może dowolnie zakodować gotowy ruch, a wyjście go odkodować, mucha stanie się przewodem (pkt 7).
2. **Najpierw T0, potem każdy etap osobno,** z pomiarem po każdym: ile zyskaliśmy i ile „muchy” zostało.
3. **Każda sieć kontrolna dostaje to samo uczenie** — te same dane, kroki, ziarna.
4. **Uczenie z wyłączaniem** (pomysł z Cowley 2024): w części przebiegów wyłączać losowy typ neuronów, żeby model nie
   mógł oprzeć wszystkiego na jednej drodze.

### 6.3 Mac czy GPU — uczciwie

- Sama sieć muchy: 1,65 ms na krok sterowania na jednym rdzeniu (VERIFIED 11 XI) — symulacje i etapy T0–T1 powinny
  zmieścić się na MacBooku. Uczenie gradientowe przez tę sieć nie było mierzone — NOT VERIFIED.
- Kora: czas pracy małego VLM na tym Macu — NOT VERIFIED (to byłby pomiar E3). SmolVLA jest według autorów
  projektowany do uczenia na jednej karcie i pracy nawet na procesorze (VERIFIED, *pełny tekst — fragmenty*), ale
  liczb dla Maca M1 Max nie mam.
- Wszystko, co rusza wagi kory (T5), oraz prawdziwe porównanie z VLA: potrzebny GPU.

---

## 7. Jak udowodnić, że mucha pracuje, a nie jest omijana ani przewodem [PROP]

Trzy sposoby, w jakie mucha może „nie pracować”: **(O) ominięcie** — sygnał idzie obok; **(P) przewód** — sygnał
przechodzi przez muchę, ale ona nic nie liczy; **(Z) zastępowalność** — liczy, ale dowolna sieć zrobiłaby to samo.

| # | Test | Wykrywa | Co liczymy | Wynik „mucha pracuje” | Wynik negatywny |
|---|---|---|---|---|---|
| D1 | **Brak drogi obok** — z konstrukcji; w wariantach z resztą: udział poleceń | O | % poleceń z muchy (dziś 8,8 % szczęki, 16,0 % bazy) | W3: 100 % z definicji | w W2 udział muchy spada z treningiem ku zeru |
| D2 | **Liniowa kopia** — zastąpić muchę jej liniowym przybliżeniem o tych samych wejściach i wyjściach | P | sukces, reakcja na zaburzenie | liniowa kopia wyraźnie gorsza | kopia = oryginał → mucha jest przewodem z opóźnieniem |
| D3 | **Przetasowania z tym samym uczeniem** (≥ 20, z wyrównaną siłą) | Z | miejsce sieci z danych w rankingu | pierwsze miejsce (p ≤ 1/21) | w środku stawki, jak w chwycie (4. z 11) |
| D4 | **Zwykła mała sieć** o tej samej liczbie uczonych parametrów i tym samym uczeniu | Z | sukces, liczba danych potrzebnych do progu | mucha potrzebuje mniej danych lub lepiej uogólnia | zwykła sieć równa lub lepsza |
| D5 | **Wyłączanie typów neuronów** według listy zapisanej z góry; **podwójna dysocjacja** | P, Z | który odruch ginie | wyłączenie toru zbliżania psuje unik, a nie podążanie — i odwrotnie | każde wyłączenie psuje wszystko po trochu → jeden wzmacniacz |
| D6 | **Zamiana stron / zamiana kanałów** (jak V5: 0/40; jak FeCO: 83 → 41) | P | sukces | załamanie | brak różnicy |
| D7 | **„Bez głowy”** — zamrozić wyjście kory w trakcie zaburzenia (poślizg, pchnięcie) | O | czy chwyt i korekta trwają; czas reakcji | odruch działa, czas reakcji krótszy niż okres kory | bez kory nic nie działa → cała robota jest w korze |
| D8 | **„Bez ciała”** — odciąć dotyk lub czucie stawów | O, P | spadek sukcesu przy zaburzeniach | wyraźny spadek | brak spadku → te zmysły są ozdobą (jak dziś wzrok w chwycie: 86 wobec 86) |
| D9 | **Kora ślepa na cel** — podać złą lub pustą mapę K1 | O | czy robot idzie do złego obiektu | tak: zachowanie idzie za K1 | robot i tak trafia → jest inna, nieopisana droga informacji |
| D10 | **Pojemność interfejsów** — czy z samych wejść interfejsu da się liniowo odczytać gotowe polecenie | P | trafność takiego odczytu | niska | wysoka → interfejs robi całą pracę |

**Dwa osobne twierdzenia — nie wolno ich sklejać:**
„mucha jest konieczna w tym modelu” (D1, D2, D5–D8) oraz „połączenia z danych są lepsze niż inne” (D3, D4).
Pierwsze uważam za osiągalne. Drugie — za niepewne: literatura (Dhiman) i nasze własne wyniki z chwytu sugerują, że po
uczeniu interfejsów przetasowane sieci mogą dogonić. Moja ocena szans na sukces D3 w W3 z przestrzennym okiem: ok.
50 % (opinia).

**Jak wygląda całkowita porażka:** D2 i D3 negatywne naraz. Wtedy uczciwe zdanie brzmi: „zbudowaliśmy działające
VLA z siecią impulsową w środku; to, że pochodzi ona z muchy, nie ma mierzalnego znaczenia”.

---

## 8. Zalety i wady — wprost [PROP / INFERRED]

| Wobec | Możliwe zalety W3 | Wady W3 | Werdykt |
|---|---|---|---|
| **Tradycyjnego VLA** | reakcja na dotyk i zaburzenia w milisekundach zamiast setek ms; część uczona tysiące razy mniejsza; brak eksperta akcji; czytelny mechanizm, który można wyłączać po kawałku; działa dalej, gdy kora się spóźnia. Że szybki „rdzeń” pomaga — potwierdzają NeuroVLA i DS-VLA (*streszczenia*) | niższa precyzja i zręczność; wąski repertuar ruchów; mapa „noga → ramię” to analogia; nadal potrzebna kora; skuteczność w zwykłych zadaniach prawie na pewno niższa | **dla skuteczności: nie warto.** Dla badania „co wnosi wrodzona struktura”: warto |
| **Sterownika klasycznego** | rozumienie poleceń i dowolnych obiektów (z kory, nie z muchy) | wolniejszy, mniej dokładny, trudniejszy do zapewnienia bezpieczeństwa; każdą funkcję muchy da się napisać ręcznie | **nie** — klasyczny + ta sama kora będzie lepszy i prostszy. To jest właściwa, najtrudniejsza kontrola |
| **Obecnego FlyMind** | wreszcie przestrzenne wejście (mapy z D0 mogą pracować); wiele stawów zamiast dwóch liczb; język; meldunek w górę; jasny zestaw dowodów | koniec czystego „zero uczenia”; dużo nowej inżynierii; ryzyko, że po uczeniu połączenia przestaną się liczyć | **tak, jako kierunek na 2027** — ale tylko z dowodami z pkt 7 |

**Twierdzenia, których W3 nie uzasadni:** lepszy niż VLA; lepszy niż klasyczny; oszczędza energię (na Macu — nie;
raport 12 XI pkt 12A); „mózg muchy rozumie polecenia”.

**Twierdzenie, które W3 mógłby uzasadnić, gdyby dowody wyszły:** „model, w którym wszystkie ruchy ramienia wytwarza
sieć z prawdziwych połączeń muchy, a dobudowany model językowy jedynie kieruje jej uwagą, wykonuje polecenia słowne;
po wyłączeniu wskazanych typów neuronów giną wskazane odruchy”.

---

## 9. Zasada z 3 XI, rola muchy, terminy

### 9.1 Zgodność z zasadą

| Element W3 | Zgodność | Komentarz |
|---|---|---|
| Wszystkie stawy sterowane z motoneuronów muchy | **zgodne — mocniej niż dziś** | dziś sieć wydaje 8,8 % i 16,0 % poleceń |
| Dotyk i stawy wchodzą przez neurony czuciowe | zgodne | |
| Oko muchy jako proteza siatkówki | stan jak dziś | nadal prąd podawany do neuronów wzrokowych, z pominięciem oka; INŻYNIERIA |
| K1 — kora zmienia czułość oka | **granica** | wejście przez zmysł, ale o tym, *co* jest ważne, decyduje kora. Biologiczny wzór istnieje (B7), tyle że tam pobudzenie jest własne, nie cudze |
| K3 — sygnały trybu do neuronów zstępujących | **sprzeczne** | nie zalecam |
| Uczenie interfejsów (T1, T2) | wymaga zgody | połączenia muchy zostają nietknięte |
| Uczenie parametrów muchy (T3), plastyczność (T4) | wymaga osobnej zgody | |

### 9.2 Rola muchy (A/B/C z raportu 11 XI)

W3 to **rola C w ścisłej postaci**: mucha wykonuje *każdy* ruch (duch roli A), a kora wybiera cel (element roli B).
W3-min bez modelu językowego jest najbliżej roli A. W2 to czysta rola B.

### 9.3 Terminy (opinia)

| Horyzont | Realne | Nierealne |
|---|---|---|
| **1 XII 2026** (19 dni; plakat 16 XI) | schemat z pkt 4.1 na plakacie jako „kierunek na 2027”, z dopiskiem NOT IMPLEMENTED; nic więcej | jakakolwiek działająca część W3 |
| **Explory 2027** | W3-min w symulacji → W3 z zamrożoną małą korą → zestaw dowodów D1–D10 → porównanie z klasycznym + ta sama kora i z małym VLA | prawdziwe ramię z gwarancją bezpieczeństwa; zręczne zadania |
| **Długoterminowo** | prawdziwy płat wzrokowy z konektomu; ciało grzybkowate; sprzęt; druga kończyna | — |

**Uwaga o kupowanym sprzęcie (REPORTED, niedostarczony):** kamera mono dobrze służy torowi szybkiemu (ruch, zbliżanie),
ale kora była uczona na obrazach kolorowych — jak sobie poradzi z obrazem mono: NOT VERIFIED. Jeśli wybór kamery
jest jeszcze otwarty, W3 przemawia za kolorową albo za dwiema (mono na nadgarstku dla muchy, kolorowa dla kory).
Cztery czujniki FSR pasują do wejścia dotyku „według miejsca”.

---

## 10. Proponowane następne kroki — **żadnego nie zaczynam**

| # | Krok | Co by pokazał | Koszt | Ryzyko | Wynik negatywny |
|---|---|---|---|---|---|
| S1 | **Spis wejść i wyjść w danych** (tylko odczyt MaleCNS): które pule motoneuronów, typy FeCO, szczecinek i neuronów wzrokowych są na tyle opisane, by zasilić schemat 4.1; ile neuronów miałby „mózg + rdzeń” | czy W3 da się w ogóle zbudować z naszych danych; rozmiar sieci | 1–2 dni, bez symulacji | braki w adnotacjach (np. czujniki obciążenia prawie nieopisane) | za mało opisanych pul → mapa „mięśnie → stawy” niemożliwa dla więcej niż 2–3 stawów |
| S2 | **Dokument: stała mapa „noga → ramię”** i specyfikacja oka muchy, zapisane przed jakimkolwiek kodem | czy analogia jest do obrony; lista założeń | 1 dzień, papier | arbitralność | brak sensownego przypisania → W3 traci sens anatomiczny |
| S3 | **Rejestracja wstępna dowodów D1–D10** (sam dokument) | progi i kontrole ustalone, zanim cokolwiek powstanie | 1 dzień, papier | — | — |
| S4 | **Liniowa kopia obecnej sieci** (D2 na tym, co już jest) — bliskie niezatwierdzonemu E2 | czy dzisiejszy FlyMind jest „przewodem” | 1–2 dni, symulacja | — | kopia = sieć → dziś mucha nic nie liczy; mocny argument za zmianą interfejsu |
| S5 | **W3-min w symulacji** (przestrzenne oko, dotyk według miejsca, kilka stawów, bez języka) — rozszerzenie E1 | pierwszy model, w którym wszystkie ruchy idą z muchy | 3–5 tygodni | nowa scena, usterki bezpieczeństwa wciąż otwarte | D3 negatywne → połączenia bez znaczenia także z przestrzennym wejściem |
| S6 | **Pomiar czasu pracy małej kory na tym Macu** (to E3) | czy tor wolny mieści się w 1–5 Hz | pół dnia + pobranie modelu | — | zbyt wolno → kora musi iść na GPU |
| S7 | **W3 z zamrożoną korą i K1** | polecenia słowne wykonywane ruchem z muchy | 4–8 tygodni po S5; częściowo GPU | kora na obrazach z symulacji może zawodzić | D9 negatywne albo klasyczny + ta sama kora wygrywa wyraźnie |

S1–S3 to praca na papierze i danych, bez symulacji i uczenia. S4–S7 wymagają osobnych zgód; E1, E2, E3 i P1–P7
pozostają niezatwierdzone.

---

## 11. Ograniczenia i adwokat diabła

1. **Najmocniejszy zarzut:** klasyczny sterownik + ta sama kora zrobi to samo prościej i lepiej. W3 nie ma na to
   odpowiedzi użytkowej, tylko naukową.
2. **Mapa „noga → ramię” jest wymyślona.** Mucha nie ma ramienia; każde przypisanie mięśni nogi do stawów SO-101 to
   decyzja inżyniera. Jeśli S1–S2 wypadną słabo, cały projekt traci podstawę.
3. **Oko muchy to proteza.** Najtrudniejszą część widzenia nadal robi kod klasyczny (i kora).
4. **Po uczeniu połączenia mogą przestać się liczyć** — tak było w literaturze (Dhiman) i w naszym chwycie.
5. **„Bez dzielenia zadań” nie jest w pełni spełnione.** Kora wybiera cel, mucha rusza. Twierdzę, że to podział jak
   w zwierzęciu, a nie jak między dwoma programami — ale to interpretacja.
6. **Prace z 2026 r. (NeuroVLA, DS-VLA, CereVLA, SaiVLA-0, sieci impulsowe VLA) to nierecenzowane preprinty**, czytane
   tylko w streszczeniach; liczby podają sami autorzy. Żadnej nie należy cytować na plakacie bez otwarcia pełnego tekstu.
7. **Prace biologiczne czytałem w streszczeniach.** Liczba neuronów zstępujących „ok. 1 100” pochodzi ze streszczenia
   Aymanns 2022; w MaleCNS naliczyłem 1 314 (10 XI, inna definicja).
8. **Nic nie zmierzyłem.** Wszystkie częstości dla kory, kamery i czujników oraz wykonalność uczenia na Macu są
   NOT VERIFIED lub HYPOTHESIS.
9. **Rozmiar docelowej sieci muchy nieznany** — zależy od S1.
10. **Moja stronniczość:** to czwarty raport, w którym szukam roli dla połączeń muchy. Dlatego pkt 7 definiuje porażkę
    z góry, a pkt 8 mówi „nie warto” tam, gdzie tak uważam.

---

## 12. Źródła i co z nich przeczytałem

**Pełny tekst — fragmenty (dziś, strona HTML arXiv):** π0, arXiv 2410.24164 (3 mld + 300 mln = 3,3 mld; 50 akcji; do
50 Hz; ponad 10 000 h; 73 ms / 86 ms na RTX 4090; stan robota jako wejście) · SmolVLA, arXiv 2506.01844 (450 mln,
z czego ok. 100 mln ekspert akcji; model językowy zamrożony; ok. 30 tys. godzin GPU; jedna karta; praca na CPU).

**Streszczenie (dziś, arXiv):** 2601.14628 NeuroVLA · 2609.32253 DS-VLA · 2609.27468 CereVLA · 2603.08124 SaiVLA-0 ·
2503.14734 GR00T N1 · 2609.39514 Spike-driven VLA · 2606.27807 SpikeVLA · 2610.09710 SpikingVLA · 2605.23568
TactileReflex · 2610.04616 PerturBot · 2605.30117 VLA-Trace · 2603.23481 VTAM · 2606.30113 SA-VLA.

**Streszczenie (dziś, Europe PMC):** Merel 2019 (10.1038/s41467-019-13239-6) · Chen 2023 (10.1038/s41593-023-01281-z) ·
Kim 2017 (10.1016/j.cell.2016.12.005) · Kim 2015 (10.1038/nn.4083) · Stein i Stanford 2008 (10.1038/nrn2331) · Ito 2008
(10.1038/nrn2332) · Li 2020 (10.7554/eLife.62576) · Hulse 2021 (10.7554/eLife.66039) · Sumbre 2001
(10.1126/science.1060976) · Dallmann 2025 (10.1038/s41586-025-09554-2) · Hindmarsh Sten 2021
(10.1038/s41586-021-03714-w) · More i Donelan 2018 (10.1098/rspb.2018.0613) · Lesser 2024 (10.1038/s41586-024-07600-z) ·
Chahine 2023 (10.1126/scirobotics.adc8892, niecytowane w tekście) · Dallmann 2021 (10.1016/j.cophys.2021.03.001,
niecytowane w tekście).

**Z raportów 10–12 XI, dziś nieotwierane:** FlyGM, FLYNN, FlyCNS, Guan i in., Dhiman, Shiu, Lappalainen, Cowley, Braun,
Aymanns, Hige, Neftci, Booker i Quinn; wszystkie liczby FlyMind i MaleCNS; liczby GR00T N1 (10 Hz / 120 Hz); 50 pokazów
na zadanie dla SmolVLA.

**Szukane i nieznalezione:** praca łącząca model językowy z siecią o połączeniach z konektomu; VLA z nieuczonym
konektomem jako warstwą ruchową.

---

## 13. Decyzje dla Adama

1. **Kierunek:** czy W3 („zwierzę z dobudowaną korą”: mucha steruje wszystkimi stawami, kora tylko wskazuje cel)
   przyjąć jako plan na Explory 2027?
2. **Zasada z 3 XI:** czy kanał K1 (kora zmienia czułość oka muchy) mieści się w zasadzie? Od tego zależy, czy W3 jest
   w ogóle dozwolone.
3. **Uczenie:** czy dopuszczasz uczenie *interfejsów* (T1, T2) przy nietkniętych połączeniach muchy?
4. **Kroki na papierze S1–S3** (spis wejść/wyjść w danych, mapa „noga → ramię”, rejestracja dowodów): zgoda?
5. **Plakat:** czy schemat z pkt 4.1 może się pojawić jako „kierunek”, z dopiskiem, że nie jest zbudowany?
6. **Kamera:** czy wybór mono/kolor jest jeszcze otwarty? (pkt 9.3)

STOPPED AT CHECKPOINT 1 — awaiting Adam's approval.
