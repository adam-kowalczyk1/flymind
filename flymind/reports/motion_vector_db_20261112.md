# FlyMind — ruchy robota w bazie wektorowej (tylko badanie)

Data: 12 XI 2026 · Autor: Claude (Opus 5.5) na prośbę Adama · Status: raport. Nic nie uruchomiono, niczego nie zainstalowano ani nie zacommitowano.

**Etykiety:** [LIT] literatura · [FM] FlyMind · [PROP] moja propozycja. Status: VERIFIED (otworzyłem źródło i tam to jest) · PARTIALLY VERIFIED · REPORTED · INFERRED (mój wniosek) · HYPOTHESIS · NOT VERIFIED · NOT IMPLEMENTED.

---

## 0. Streszczenie dla Adama (prostym językiem)

1. **W projekcie nie ma dziś bazy wektorowej ani biblioteki ruchów.** Są tylko: nagrywarka pokazów z pada do formatu LeRobot (`pad_so101/record.py`), 2 zapisane pozy (`pad_so101/poses.json`) i cudzy zbiór `so101_lego_drop_real_50` w cache Hugging Face (nie nasz). [FM, VERIFIED — sprawdziłem repo]
2. **Ruch najlepiej zapisywać jako krótki kawałek (np. 0,5–1 s wszystkich stawów), zamieniony na wektor stałej długości.** Pełny zapis zostaje obok jako „prawda”. Tak robią dzisiejsze metody: ACT przewiduje paczki ruchu, FAST kompresuje je transformatą kosinusową, STRAP wyszukuje krótkie podfragmenty, a nie całe nagrania. [LIT, VERIFIED + PROP]
3. **Szukamy po tym, co robot widział i czuł, a nie tylko po kształcie ruchu.** Klucz = obraz + czucie + stan; wartość = kawałek ruchu + wynik (udany/nieudany) + kto sterował (mucha, klasyka, człowiek). [PROP]
4. **Przy naszej skali (setki–tysiące kawałków) wystarczy zwykłe, dokładne przeszukanie.** Serwer bazy wektorowej jest niepotrzebny; indeksy przybliżone (HNSW) mają sens dopiero przy bardzo dużych zbiorach. [INFERRED]
5. **Najbardziej użyteczne wzorce z biologii:** ruch składany z kilku „cegiełek” (synergie mięśniowe), neuron-komenda uruchamia całą sieć, a nie jeden mięsień, kolejność ruchów przez hierarchię tłumienia (czyszczenie u muchy), to samo polecenie daje różny ruch zależnie od stanu, a mucha robi „wyszukiwanie podobnych” w węchu przez rzadkie rozszerzenie (LSH). [LIT, VERIFIED na poziomie abstraktów]
6. **Największe ryzyko:** biblioteka, która sama odtwarza ruchy, **omija muchę**. To łamie zasadę z 3 XI. Uczciwa wersja: baza tylko zapisuje i porównuje, a jeśli kiedyś ma wykonywać ruchy, to mucha musi wybierać i modulować, z kontrolą „baza bez muchy”. [FM + INFERRED]
7. **Mylące analogie:** mózg to nie baza danych z odtwarzaniem; konektom MaleCNS nie zawiera nagrań ruchów; LSH muchy dotyczy zapachów, nie ruchu. [INFERRED]

---

## 1. Stan repo (sprawdzone dziś) [FM, VERIFIED]

| Co | Gdzie | Uwagi |
|---|---|---|
| Baza wektorowa / embeddingi | — | brak; grep po `faiss|chromadb|qdrant|lancedb|hnswlib|pgvector|embedding|vector db` w repo i `~/FlyMind_Hub` — 0 trafień |
| Nagrywanie pokazów | `pad_so101/record.py` | format LeRobot (obraz + stawy + komenda serw); w docstringu: „Źródło komend: classical:pad — to pokazy człowieka, nie mucha”; wg pamięci projektu testowane tylko offline |
| Zapisane pozy | `pad_so101/poses.json` | klucz `real` z 2 pozami (`4`, `1`) — to nie biblioteka ruchów |
| Cudze dane | `~/.cache/huggingface/lerobot/hub/datasets--TaeJun123123--so101_lego_drop_real_50` | nie nasze; licencji i zawartości nie sprawdzałem |
| Trajektorie z symulacji | `flymind/results/pick_place/validation/` itd. | logi z przebiegów; nie są ułożone jako biblioteka ruchów |

---

## 2. Pytanie 1 — jak reprezentować ruch w przestrzeni wektorowej

### 2.1 Co mówi literatura [LIT]
| Podejście | Co to jest | Źródło | Status |
|---|---|---|---|
| Paczki akcji (action chunks) | Model przewiduje sekwencję akcji naraz; ACT: 6 trudnych zadań, 80–90% sukcesu, z 10 min pokazów | Zhao et al. 2023, arXiv 2304.13705 (abstrakt) | VERIFIED |
| Kompresja częstotliwościowa (FAST) | Paczka ruchu → transformata kosinusowa → tokeny; zwykłe dzielenie na przedziały „zawodzi całkowicie” przy szybkich, zręcznych danych; FAST+ uczony na 1 mln trajektorii | Pertsch et al. 2025, arXiv 2501.09747 (abstrakt) | VERIFIED |
| Kwantyzacja wektorowa (VQ-BeT) | Akcje ciągłe → hierarchiczny słownik kodów; lepsze niż k-means przy dużych wymiarach; 5× szybsze wnioskowanie niż Diffusion Policy | Lee et al. 2024, arXiv 2403.03181 (abstrakt) | VERIFIED |
| Prymitywy dynamiczne (DMP) | Ruch jako atraktor (układ dynamiczny) + kilka wag kształtu | Ijspeert et al. 2013, Neural Computation (tylko metadane Crossref) | PARTIALLY VERIFIED |

### 2.2 Propozycja dla FlyMind [PROP, NOT IMPLEMENTED]
Jeden wpis = **kawałek ruchu** (np. 15–30 klatek przy 30 Hz, 5 stawów + szczęka):
- **wektor ruchu**: pierwsze współczynniki transformaty kosinusowej na staw, znormalizowane (stała długość, odporne na szum) — wzorowane na FAST;
- **surowe dane**: pełna trajektoria (prawda, do odtwarzania i audytu);
- **wektor kontekstu**: cechy obrazu (np. z gotowego enkodera, jak DINOv2 w STRAP), czucie (FSR/kontakt), stan sieci muchy, jeśli to ona sterowała (np. aktywność DN w oknie);
- **metadane**: źródło (`fly` / `classical` / `human:pad` / `reflex` / `shuffled-control`), wynik (sukces/porażka), seed, commit, wersja sceny.

Dlaczego tak: wektor kształtu ruchu sam w sobie jest mało użyteczny; ważne jest, **w jakiej sytuacji** ruch zadziałał. Metadane źródła są obowiązkowe ze względu na zasadę z 3 XI. [INFERRED]

---

## 3. Pytanie 2 — indeksowanie i wyszukiwanie

| Element | Literatura | Wniosek dla nas | Status |
|---|---|---|---|
| Wyszukiwanie po kontekście, akcja z sąsiadów | VINN: oddzielenie uczenia reprezentacji od zachowania + regresja ważona lokalnie; lepiej niż wcześniejsze metody, m.in. otwieranie drzwi na prawdziwym robocie | arXiv 2112.01511 (abstrakt) — VERIFIED | Najprostszy wariant: kNN po kontekście |
| Wyszukiwanie podfragmentów | STRAP: wyszukiwanie na poziomie „pod-trajektorii” poprawia wykorzystanie danych i uogólnianie; dopasowanie przez wariant DTW | arXiv 2412.15182 (abstrakt) — VERIFIED | Indeksować kawałki, nie całe epizody |
| Wybór danych do uczenia | Behavior Retrieval: mało danych eksperta → wyciąga pasujące przejścia z dużego, nieopisanego zbioru, filtrując nietrafne | arXiv 2304.08742 (abstrakt) — VERIFIED | Baza jako filtr danych, nie jako sterownik |
| Indeks przybliżony | HNSW: graf wielowarstwowy, złożoność logarytmiczna | arXiv 1603.09320 (abstrakt) — VERIFIED | Potrzebny dopiero przy dużych zbiorach |
| Biblioteka | Faiss: narzędzia do szukania, klastrowania, kompresji wektorów | arXiv 2401.08281 (abstrakt) — VERIFIED | Wystarczy wariant dokładny (płaski) |

**Propozycja [PROP]:** dwa etapy — (1) dokładne kNN po wektorze kontekstu (lub ruchu), (2) ponowne uszeregowanie kilku kandydatów przez DTW na surowych trajektoriach. Przy setkach–tysiącach kawałków dokładne przeszukanie jest natychmiastowe na laptopie [INFERRED; liczby wydajności NOT VERIFIED]. Przechowywanie: obok danych LeRobot (już istniejący format), indeks jako plik obok — bez serwera.

**Pułapka [INFERRED]:** jeśli w bazie są kawałki z serii testowych, a potem używamy jej przy testach, to jest przeciek danych. Bazę trzeba dzielić po seedach, tak samo jak dzielimy serie.

---

## 4. Pytanie 3 — powiązanie z percepcją i działaniem

Trzy sposoby, od najbezpieczniejszego dla zasady z 3 XI:

| Tryb | Co robi baza | Kto steruje | Zgodność z 3 XI | Status |
|---|---|---|---|---|
| A. **Pamięć i analiza** | Zapisuje każdy epizod (mucha, klasyka, kontrole), pozwala znaleźć „podobne porażki”, porównać sterowniki | mucha / klasyka jak dziś | pełna | [PROP] |
| B. **Filtr danych do uczenia** | Wybiera dane do treningu (jak Behavior Retrieval / STRAP) | wytrenowana polityka | zależy, co jest trenowane; dla muchy — wymaga zgody (P1–P7 niezatwierdzone) | [PROP] |
| C. **Wykonawca prymitywów** | Mucha wybiera/moduluje prymityw z biblioteki, biblioteka go wykonuje | **częściowo baza** | **ryzyko**: mucha staje się przełącznikiem 1 bit/strona; potrzebna kontrola „baza bez muchy” i „baza z przetasowaną muchą” | [PROP, HYPOTHESIS] |

Pętla percepcja→działanie w trybie C byłaby wzorowana na biologii (pkt 5): sytuacja → wybór komendy (mucha) → rekrutacja całego wzorca ruchu → czucie kończy ruch i zwalnia następny. **Ale** jeśli większość „inteligencji” siedzi w bibliotece, wynik nie mówi nic o musze. To trzeba mierzyć, nie zakładać. [INFERRED]

---

## 5. Pytanie 4 — co z biologii daje użyteczny wzorzec

| # | Wzorzec biologiczny | Dowód | Przełożenie na bazę ruchów | Status |
|---|---|---|---|---|
| B1 | **Ruch z kilku cegiełek.** U żaby 3 zmienne w czasie synergie mięśniowe tworzą kopnięcia w różnych kierunkach; podobne synergie w różnych zachowaniach | d'Avella, Saltiel, Bizzi 2003, Nat Neurosci (abstrakt) | Mały słownik prymitywów + wagi zamiast tysięcy nagrań | [LIT] VERIFIED |
| B2 | **Mapa postaw w rdzeniu kręgowym, łączenie wektorowe wyjść** daje duży repertuar | Bizzi, Mussa-Ivaldi, Giszter 1991, Science (abstrakt) | Prymitywy jako atraktory (jak DMP), łączone liniowo | [LIT] VERIFIED |
| B3 | **Neuron-komenda rekrutuje sieć.** U muchy DN „komendowe” współaktywują większe populacje DN; bez tego tylko proste, stereotypowe ruchy; skupiska dla zachowań wzajemnie się hamują | Braun et al. 2024, Nature (abstrakt) | Klucz = komenda; wartość = skoordynowany wzorzec wielu stawów; konkurencyjne prymitywy hamują się | [LIT] VERIFIED |
| B4 | **Kolejność przez hierarchię tłumienia.** Programy czyszczenia aktywne równolegle, wybierane po kolei; zakończenie (spadek bodźca) zwalnia następny | Seeds et al. 2014, eLife (abstrakt) | Łączenie prymitywów w sekwencję bez planisty: priorytety + warunek zakończenia z czucia | [LIT] VERIFIED |
| B5 | **Zależność od stanu.** Ten sam aktywowany DN daje różne zachowanie zależnie od stanu przed aktywacją; wiele DN daje podobne zachowania | Cande et al. 2018, eLife (abstrakt) | Wyszukiwanie musi uwzględniać stan (pozycja, kontakt), nie tylko komendę | [LIT] VERIFIED |
| B6 | **Wyszukiwanie podobnych u muchy (LSH).** Obwód węchowy przypisuje podobnym zapachom podobne wzorce, stosując wariant haszowania wrażliwego na lokalność | Dasgupta, Stevens, Navlakha 2017, Science (abstrakt) | Indeks: rzadkie, losowe rozszerzenie + „zwycięzca bierze wszystko” jako tani skrót kontekstu | [LIT] VERIFIED |
| B7 | **Czas jako rzadki kod.** Neurony HVC u ptaka śpiewającego strzelają raz, w precyzyjnym momencie sekwencji; sekwencja odtwarzana też we śnie | Hahnloser, Kozhevnikov, Fee 2002, Nature (abstrakt) | Indeks pozycji wewnątrz prymitywu (faza), zamiast porównywać całe krzywe | [LIT] VERIFIED |

Liczby z prasy (np. „ok. 50 neuronów, top 5% z ok. 2000” dla B6) pochodzą z komunikatu Salk, nie z abstraktu — **NOT VERIFIED**, nie używam ich w projekcie.

---

## 6. Pytanie 5 — co z biologii byłoby błędem albo mylącą analogią

| # | Analogia | Dlaczego myląca | Status |
|---|---|---|---|
| M1 | „Mózg przechowuje ruchy jak baza danych i je odtwarza” | Biologia (B1–B5) pokazuje **generowanie** z prymitywów zależnie od stanu, nie kopię nagrania. Baza z odtwarzaniem to rozwiązanie inżynierskie, nie biologiczne | INFERRED |
| M2 | „Konektom MaleCNS zawiera bibliotekę ruchów muchy” | Konektom to mapa połączeń, nie zapis trajektorii; nie ma tam nagrań do wyciągnięcia | INFERRED |
| M3 | „Mucha szuka ruchów przez LSH” | Dowód LSH dotyczy **węchu** (B6). To inspiracja dla indeksu, nie dowód, że ruch jest tak przechowywany | INFERRED |
| M4 | „Wektor” u Bizziego = wektor embeddingu | U Bizziego to pola sił i łączenie wyjść motorycznych; zbieżność słowa, nie metody | INFERRED |
| M5 | „Sen ptaka = offline’owe dotrenowanie z bazy” | B7 pokazuje odtwarzanie sekwencji we śnie; związek z uczeniem to osobne, sporne pytanie | INFERRED; nauka sporna |
| M6 | „DN muchy sterują stawami ramienia” | DN sterują nogami/skrzydłami przez VNC; mapowanie na stawy SO-101 jest inżynierskie | [FM] INFERRED |
| M7 | „FlyMind ma pamięć ruchową / uczy się” | W kodzie nie ma plastyczności ani stanu, a neuromodulatory nie działają. Baza dodana z boku to pamięć **systemu**, nie muchy | [FM] VERIFIED (z kontekstu) |

**Co sporne lub nieznane:** czy synergie mięśniowe to prawdziwe „cegiełki” układu nerwowego, czy artefakt metody rozkładu — w literaturze trwa o to spór (NOT VERIFIED — nie otwierałem prac krytycznych). Jak dokładnie VNC muchy składa ruchy nóg z poleceń DN — wiadomo tylko częściowo (Braun 2024 sam mówi o mechanizmie rekrutacji, nie o pełnym kodzie ruchu).

---

## 7. Zasada z 3 XI i ryzyka [FM / INFERRED]
- Tryb A (pamięć i analiza) jej nie narusza i nic nie zmienia w sterowaniu.
- Tryb C narusza ją, jeśli biblioteka decyduje. Warunki minimalne: mucha wybiera i moduluje; kontrole „baza bez muchy”, „mucha przetasowana + baza”, „losowy wybór prymitywu”; raport, ile wyniku daje baza, a ile mucha.
- Pokazy z pada (`human:pad`) i klasyka mogą być w bazie **tylko z etykietą źródła** — nigdy jako „ruchy muchy”.
- E1–E3, P1–P7, S1–S7, U1–U5 nadal niezatwierdzone; nic z nich tu nie uruchamiam.

---

## 8. Proponowane następne kroki — **żadnego nie zaczynam**
1. Decyzja Adama: który tryb (A / B / C) jest celem. Rekomenduję **A** na start: zerowe ryzyko dla zasady z 3 XI, przydatne od razu (analiza porażek, porównanie sterowników).
2. Specyfikacja wpisu na papierze (pola z pkt 2.2) + reguła podziału po seedach — do akceptacji przed jakimkolwiek kodem.
3. Spis istniejących logów symulacji, które dałoby się przekształcić w wpisy (bez uruchamiania czegokolwiek).
4. Decyzja, czy wolno użyć cudzego zbioru `so101_lego_drop_real_50` (licencja niesprawdzona).
5. Tryb C tylko po osobnym projekcie kontroli (pkt 7) i Twojej zgodzie.

---

## 9. Źródła i co z nich przeczytałem

| Źródło | ID | Co przeczytałem |
|---|---|---|
| Zhao et al. 2023, ACT | arXiv 2304.13705 | abstrakt (arXiv API) |
| Pertsch et al. 2025, FAST | arXiv 2501.09747 | abstrakt |
| Lee et al. 2024, VQ-BeT | arXiv 2403.03181 | abstrakt |
| Ijspeert et al. 2013, DMP | doi:10.1162/NECO_a_00393 | tylko metadane (Crossref) |
| Pari et al. 2021, VINN | arXiv 2112.01511 | abstrakt |
| Memmel et al. 2024, STRAP | arXiv 2412.15182 | abstrakt (DINOv2 i S-DTW z wyników wyszukiwania / strony HTML — PARTIALLY VERIFIED) |
| Du et al. 2023, Behavior Retrieval | arXiv 2304.08742 | abstrakt |
| Malkov & Yashunin 2016, HNSW | arXiv 1603.09320 | abstrakt |
| Douze et al. 2024, Faiss | arXiv 2401.08281 | abstrakt |
| d'Avella, Saltiel, Bizzi 2003 | doi:10.1038/nn1010 | abstrakt (Europe PMC) |
| Bizzi, Mussa-Ivaldi, Giszter 1991 | doi:10.1126/science.1857964 | abstrakt (Europe PMC) |
| Braun et al. 2024 | doi:10.1038/s41586-024-07523-9 | abstrakt (Europe PMC) |
| Seeds et al. 2014 | doi:10.7554/eLife.02951 | abstrakt (Europe PMC) |
| Cande et al. 2018 | doi:10.7554/eLife.34275 | abstrakt (Europe PMC) |
| Dasgupta, Stevens, Navlakha 2017 | doi:10.1126/science.aam9868 | abstrakt (Europe PMC) |
| Hahnloser, Kozhevnikov, Fee 2002 | doi:10.1038/nature00974 | abstrakt (Europe PMC) |

Wcześniejsze raporty (10, 11, 12 XI, w tym `robot_ai_revolution_20261112.md`) nie zostały zmienione.

---

STOPPED AT CHECKPOINT 1 — awaiting Adam's approval.
