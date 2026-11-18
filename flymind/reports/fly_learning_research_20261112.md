# FlyMind — uczenie, uogólnianie i sieć muchy wobec modeli VLA

Raport badawczy, 2026-11-12. Autor: Claude (Fable 5.2), na prośbę właściciela projektu.
Buduje na `flymind/reports/bio_advantage_research_20261110.md` i `flymind/reports/fly_vs_vla_research_20261111.md`
(oba nietknięte). Status pliku: nowy, niezacommitowany, **jedyny plik utworzony w tej sesji**. Niczego nie symulowałem,
nie trenowałem, nie zmieniałem i nie commitowałem. Nie napisałem żadnego kodu w repozytorium.

**Etykiety dowodów:** **VERIFIED** (sprawdzone; podane źródło lub plik), **PARTIALLY VERIFIED**, **REPORTED** (przepisane
ze źródła, którego sam nie otworzyłem, albo z wyszukiwarki), **INFERRED** (mój wniosek z faktów), **HYPOTHESIS**,
**NOT VERIFIED**, **NOT IMPLEMENTED**. Przy literaturze podaję, co faktycznie przeczytałem: *streszczenie* (pełne
streszczenie pobrane dziś z Europe PMC albo z arXiv), *wycinek* (tylko podsumowanie z wyszukiwarki), *raport 10/11 XI*
(źródło czytane wtedy, dziś nieotwierane). **Pełnego tekstu żadnej nowej publikacji dziś nie czytałem.**

Trzy rzeczy trzymam osobno: **[LIT]** fakty z literatury, **[FM]** fakty o FlyMind, **[PROP]** moje propozycje i opinie.

---

## 0. Streszczenie dla Adama (prostym językiem)

**Pięć pytań, pięć krótkich odpowiedzi.**

1. **Czy sieć muchy może dorównać VLA?** W tym, co stanowi siłę VLA (język, nowe przedmioty, wiele zadań) — nie.
   Dorównać, a nawet wygrać, może tylko w wąskim sensie: **szybka reakcja na ruchomy bodziec, przy znikomym koszcie
   obliczeń i bez żadnych danych uczących**. Nikt tego dotąd nie zmierzył „głowa w głowę”. Dowód wymagałby prawdziwego
   małego VLA na tym samym zadaniu w tej samej symulacji. Uwaga: w tym samym wąskim sensie z VLA wygrywa też prosty
   program — więc „mucha dorównuje VLA” da się uczciwie powiedzieć, ale „dzięki połączeniom muchy” już nie, dopóki sieć
   z danych nie wygra z przetasowanymi.

2. **Jak można nauczyć sieć muchy czegoś nowego?** Jest sześć dróg, od „najbardziej musza” do „najbardziej inżynierska”:
   (a) zmieniać tylko to, co sieć widzi i jak czytamy jej wyjście; (b) uczenie takie, jakie ma prawdziwa mucha — „ten
   sygnał jest dobry/zły” w ciele grzybkowatym (obwód jest w naszych danych, niemodelowany); (c) uczenie nagrodą na
   poziomie pojedynczych połączeń; (d) strojenie kilkudziesięciu parametrów (progi, stałe czasowe) przy nietkniętych
   połączeniach; (e) uczenie gradientowe „e-prop”, zaprojektowane dokładnie dla takich neuronów jak nasze; (f) pełne
   trenowanie wag jak w zwykłej sieci. Im dalej na tej liście, tym więcej sieć umie i tym mniej zostaje w niej muchy.
   Drogi (b)–(f) wymagają Twojej zgody, bo to jest „uczenie”.

3. **Czy da się zbudować „tłumacza” na język muchy?** Tak, ale wąskiego. Mucha „rozumie” bodźce, nie polecenia:
   mały ruchomy obiekt (skręć do niego), szybko rosnący obiekt (uciekaj w tę stronę), dotyk (zaciśnij/cofnij), a po
   nauczeniu — „ten sygnał jest dobry/zły”. Tłumacz zamieniałby polecenie („weź czerwony klocek”) na bodziec pokazany
   musze („to jest ten mały obiekt, za którym masz podążać”), a z powrotem czytał neurony zstępujące i ruchowe.
   Słownik miałby kilka słów, nie tysiące. **Ważne:** w takim układzie rozumienie polecenia wykonuje tłumacz, a mucha
   tylko steruje ruchem. Tłumacz, który pobudzałby wprost wybrane neurony „rozkazowe”, byłby prostszy, ale **łamie
   Twoją zasadę z 3 XI**.

4. **Jak trenuje się modele, żeby robiły coś, czego ich nie uczono?** Nie ma magii: (i) bardzo szerokie i różnorodne
   dane, (ii) polecenie słowne jako „pokrętło”, dzięki któremu nowe zadanie jest nową kombinacją znanych kawałków,
   (iii) losowe zmienianie świata w symulacji, (iv) uczenie się uczenia, (v) warstwa planująca, która składa gotowe
   umiejętności, (vi) wbudowana z góry struktura. Sieć muchy jest skrajnym przypadkiem (vi): **wszystko, co robi,
   robi bez treningu** — ale tylko w zakresie tego, do czego ewolucja ją zbudowała.

5. **Jak dostraja się modele zbudowane ze skanów mózgu?** Sprawdzony przepis: połączenia zostają z danych, a uczy się
   tylko to, czego skan nie pokazuje (własności neuronów i siłę synaps), najlepiej wspólnie dla całego typu komórek.
   Dostraja się albo do zadania, albo do nagrań aktywności prawdziwych neuronów. Dwa ostrzeżenia z literatury: sam
   konektom często nie wystarcza, żeby wyznaczyć działanie sieci; a po treningu przewaga prawdziwych połączeń nad
   przetasowanymi potrafi zniknąć, gdy kontrole są uczciwe.

**Co kiedy (moja ocena, nie pomiar):**

| Horyzont | Co jest realne |
|---|---|
| **Do 1 XII 2026** | Tylko rzeczy bez uczenia: dwie analizy samych danych (P1, P2 w pkt 10), ewentualnie wcześniej zaproponowane E1/E2 — nadal niezatwierdzone. Z tego raportu na plakat/demo nadaje się „słownik muchy” (co mucha rozumie) jako uczciwy opis. Nic z uczeniem nie zdąży przejść kontroli jakości. |
| **Explory 2027** | Moduł uczenia „dobry/zły” z ciała grzybkowatego; tłumacz v1 (polecenie → bodziec); dostrajanie na poziomie typów komórek z pełnymi kontrolami; prawdziwe porównanie z małym VLA w symulacji. |
| **Długoterminowo** | Prawdziwy układ wzrokowy muchy zamiast wykrywacza koloru; cały układ nerwowy; uczenie ze wzmocnieniem na konektomie dla ramienia; dopasowanie do nagrań aktywności; sprzęt. |

**Sprzeczności z zasadą z 3 XI („mucha ma sterować, przez własne zmysły, bez sztucznego pobudzania wybranych
neuronów”) — mówię wprost:** (1) tłumacz przez neurony rozkazowe — sprzeczny; (2) każde uczenie wag zmienia sieć tak, że
przestaje być „połączeniami z danych” — wymaga Twojej zgody; (3) w układzie „tłumacz + mucha” o tym, *co* robić,
decyduje tłumacz — mucha decyduje tylko *jak* się ruszyć. Szczegóły w pkt 9.

**Decyzje dla Ciebie są w pkt 13.** Niczego nie uruchamiam.

---

## 1. Zakres, metoda, czego nie zrobiłem

**Zrobione (tylko odczyt):** przeczytałem oba wcześniejsze raporty; 24 wyszukiwania w sieci; pobrałem dziś pełne
streszczenia 45 publikacji bezpośrednio z Europe PMC (po DOI lub tytule) i z arXiv (po numerze), żeby każdy cytat miał
sprawdzony tytuł, autorów i identyfikator. Sprawdziłem, że oba wcześniejsze raporty nie zostały zmienione (pkt 12).

**Nie zrobione:** żadnej symulacji, treningu, kodu, nowych ziaren, commitu, zmiany istniejących plików, kontaktu
z robotem. Nie użyłem pod-agentów — wszystkie źródła sprawdzałem sam. Nie zapytałem dziś plików MaleCNS; liczby o danych
pochodzą z raportów 10–11 XI.

**Przegląd Nori („Bio-ML: kiedy się opłaca”, 12 XI).** Strona internetowa wymagała logowania, więc pkt 0–11 powstały
**bez** tego przeglądu. Adam dostarczył potem plik; przeczytałem go w całości i dopisałem pkt 12A (porównanie).
Punktów 0–11 po lekturze nie zmieniałem, żeby było widać, co ustaliłem niezależnie — wyjątkiem są trzy zdania, które
mówiły, że przeglądu nie czytałem.

**Uwaga o moich wcześniejszych twierdzeniach.** Liczby FlyMind poniżej mają etykietę „VERIFIED (11 XI)”: przeliczyłem
je wtedy z surowych plików; **dziś ich nie przeliczałem**.

---

## 2. Punkt wyjścia — fakty o FlyMind [FM]

| Fakt | Status |
|---|---|
| V5 (obrót bazy): sieć 38/40, sterownik P 40/40, sieć przetasowana 3/40, zamienione strony 0/40, bez obrazu 0/40, obraz opóźniony o 50 ms 17/40 | VERIFIED (11 XI) |
| Chwyt, miękki kontakt: sieć 90/135, klasyczny 93, odruch 80; sieć jest 4. z 11 (sieć + 10 przetasowań) | VERIFIED (11 XI) |
| Demo v3: sieć wydaje 8,8 % poleceń szczęki i 16,0 % poleceń bazy | VERIFIED (11 XI) |
| Brak wykazanej przewagi nad sterownikiem klasycznym ani nad VLA | VERIFIED (11 XI) |
| Wejście i wyjście sieci to pojedyncze liczby (ten sam prąd do wszystkich neuronów jednej strony; wyjście = różnica dwóch średnich) — dlatego test przetasowania nie mógł wykazać roli połączeń | VERIFIED (10 XI, w kodzie) |
| Model nie ma żadnej plastyczności: wagi są stałe, nic się nie uczy | PARTIALLY VERIFIED: raport 11 XI (§4) + dzisiejsze wyszukiwanie słów kluczowych (`stdp`, `plasticity`, `eligib`, `learning_rate`, `optimizer`, `.backward(`) w plikach `flymind/**/*.py` — zero trafień; kodu nie czytałem linia po linii |
| Sieć używa najwyżej 1 931 z 165 122 neuronów (1,2 %); cały układ wzrokowy (54 % neuronów) zastępuje wykrywacz koloru | VERIFIED (11 XI) |
| W danych MaleCNS jest obwód uczenia: 4 064 komórki Kenyona, 97 neuronów wyjściowych, 340 neuronów dopaminowych; nieużywany | VERIFIED (11 XI) |
| D0: w połączeniach są mapy „miejsce bodźca → kierunek ruchu” (4 z 5 par potwierdzających) | VERIFIED (11 XI) |
| D0 zakończone; E1 i E2 niezatwierdzone; rola muchy nierozstrzygnięta; zasada z 3 XI obowiązuje | stan decyzji wg polecenia |

---

## 3. Pytanie 1 — czy sieć z konektomu muchy może w jakimkolwiek sensie dorównać VLA?

### 3.1 Co wiadomo [LIT]

**Sieci z konektomu jako sterowniki — stan na listopad 2026.** Wszystkie poniższe prace *uczą* wagi; żadna nie porównuje
się z VLA.

| Praca | Co pokazano | Co przeczytałem |
|---|---|---|
| FlyGM — Jin, Zhu, Zhang, Sui, arXiv 2602.17997 | Cały konektom mózgu jako sieć grafowa sterująca symulowanym *ciałem muchy*, uczona przez uczenie ze wzmocnieniem; „lepsza efektywność próbek niż sieci grafowe i niegrafowe” | *streszczenie*; liczby w raporcie 10 XI |
| FLYNN — Wang, Chen, arXiv 2607.00025 | Sieć rekurencyjna o architekturze z konektomu, uczona nawigacji wzrokowej w MuJoCo: wynik „porównywalny” z ręcznie projektowanymi sieciami tej samej wielkości; lepsza odporność na dane spoza rozkładu i na utratę czujników, „działała nawet przy całkowitej utracie wzroku” | *streszczenie* |
| FlyCNS — Zhang, Lin, Lu, arXiv 2609.28816 | Konektom mózg–rdzeń jako *słaby* wzorzec podziału komunikacji w sterowaniu czworonogiem Go1 (symulacja); przy 21–22 % komunikacji strata ≤ 6,1 % | *streszczenie* |
| Guan i in., arXiv 2609.27001 | Sterownik „inspirowany muchą” (3 609 stanów) dla symulowanego humanoida G1: 61/63 warunków wobec 62/63 dla sterownika uprzywilejowanego. **Ale:** podmiana wejść wzrokowych i stanów „wyższych” nie zmieniała akcji, a wyjście zstępujące było zerowe — ruch niosła pętla ciało → stan ruchowy | *streszczenie* |
| Dhiman, arXiv 2604.04033 | Pozorne przewagi topologii konektomu „w dużej mierze znikają” przy uczciwej inicjalizacji i przetasowaniu zachowującym stopnie | *streszczenie* |
| Shiu i in., *Nature* 2024, doi 10.1038/s41586-024-07763-9 | Model całego mózgu **bez żadnego uczenia** trafnie przewiduje obwody karmienia i czyszczenia czułków | *streszczenie* |
| Eon Systems (marzec 2026) | Mózg Shiu + ciało NeuroMechFly; brak recenzowanej publikacji; część zachowań to gotowe procedury ciała | *wycinek* + raport 10 XI |

**Słabości VLA, na których mucha mogłaby „dorównać”** (z raportów 10–11 XI, dziś nieotwierane): na zadaniach
z ruchomymi obiektami typowe VLA mają 1–13 % sukcesu (DynamicVLA, arXiv 2601.22153); czas jednej decyzji 40–300 ms na
GPU; na ramieniu SO-101 średnio 32–56 % sukcesu po 100 pokazach na zadanie (arXiv 2606.08881). REPORTED.

**Nie znalazłem** żadnej pracy, w której sieć z konektomu i VLA rozwiązują to samo zadanie. NOT FOUND — to opis mojego
szukania, nie świata.

### 3.2 Odpowiedź [PROP / INFERRED]

„Dorównać” ma cztery możliwe znaczenia. Tylko dwa są osiągalne:

| Sens „dorównania” | Możliwe? | Dlaczego |
|---|---|---|
| Zakres zadań, język, nowe przedmioty | **Nie** | Nic w obwodach muchy tego nie dostarcza; żadna praca tego nie twierdzi |
| Jakość w jednym wąskim, szybkim zadaniu (śledzenie, unik) | **Tak, prawdopodobnie** — HYPOTHESIS | VLA są tu słabe z powodu opóźnień; mucha ma do tego wrodzone obwody. Nigdy nie zmierzone |
| Koszt: czas decyzji, energia, brak danych uczących | **Tak** — INFERRED | FlyMind: 1,65 ms na krok na jednym rdzeniu (VERIFIED 11 XI) wobec dziesiątek–setek ms na GPU. Prosty program ma to samo |
| Odporność na utratę czujnika | **Niepewne** | FLYNN to twierdzi (streszczenie, po uczeniu); u nas jest odwrotnie: bez obrazu 0/40, z opóźnieniem 17/40 |

### 3.3 Jak to udowodnić [PROP]

Dowód „dorównuje w sensie X” wymaga jednego stołu dla wszystkich:

1. **To samo zadanie, ta sama symulacja, te same sceny**, próby parowane. Zadanie szybkie i wąskie (ruchomy cel albo unik).
2. **Prawdziwy mały VLA** (np. SmolVLA) dostrojony na pokazach z tej symulacji — nie „zastępnik wolnej polityki”.
3. **Pięć ramion:** sieć z danych; ≥ 20 sieci przetasowanych; sterownik klasyczny; VLA; brak sterowania.
4. **Z góry zapisane progi równoważności** (np. różnica sukcesu ≤ 10 punktów procentowych) i miary: sukces, czas reakcji,
   czas obliczeń na tej samej maszynie.
5. **Dwa osobne zdania do udowodnienia**, których nie wolno sklejać: „mucha ≥ VLA w zadaniu X” (ramiona 1 i 4) oraz
   „to zasługa połączeń” (ramię 1 wobec 2). Drugie jest trudniejsze i ważniejsze naukowo.

### 3.4 Znaczenie dla FlyMind

- Uczciwe zdanie możliwe w przyszłości: „w szybkim zadaniu X sieć z połączeń muchy, bez żadnego uczenia, osiąga wynik
  nie gorszy niż model VLA uczony na N pokazach, przy tysiąckrotnie mniejszym koszcie obliczeń”. Dziś: NOT IMPLEMENTED.
- Praca Guan i in. to dla nas ostrzeżenie: sterownik „z muchy” może działać, choć jego „mózgowa” część nic nie wnosi.
  Nasze 8,8 % i 16 % poleceń to ten sam rodzaj pytania — trzeba mierzyć, *która* część faktycznie steruje.
- **Horyzont:** do 1 XII — nie (wymaga treningu VLA i nowej sceny). Explory 2027 — tak. Opinia.

---

## 4. Pytanie 2 — jak można uczyć sieć muchy nowego zachowania?

### 4.1 Co wiadomo [LIT]

**Jak uczy się prawdziwa mucha.**
- Uczenie skojarzeniowe w ciele grzybkowatym: ok. 2 000 komórek Kenyona koduje bodziec rzadko, zbiegają się na 34
  neurony wyjściowe 21 typów, które zbiorczo kodują „dobre/złe” i kierują wyborem działania (Aso i in., *eLife* 2014,
  doi 10.7554/eLife.04580, *streszczenie*).
- Mechanizm: połączenie zapachu z aktywacją konkretnych neuronów dopaminowych **osłabia** synapsy komórka Kenyona →
  neuron wyjściowy, tylko dla tego zapachu i tylko przy właściwej kolejności w czasie; dopamina działa osobno w każdym
  przedziale (Hige i in., *Neuron* 2015, doi 10.1016/j.neuron.2015.11.003, *streszczenie*). To reguła lokalna,
  trójczynnikowa: bodziec × odpowiedź × dopamina.
- Uczenie ruchowe poza mózgiem: bezgłowe muchy uczą się trzymać nogę w pozycji unikającej szoku (Booker i Quinn 1981,
  doi 10.1073/pnas.78.6.3940, raport 11 XI); uczenie operanckie skrętu wymaga plastyczności w motoneuronach sterujących
  skrzydłami (Ehweiner, Duch, Brembs, *F1000Research* 2024, doi 10.12688/f1000research.146347.2, *streszczenie*).
  Reguła na poziomie synaps nie jest opisana — NOT FOUND.

**Modele uczenia w obwodach muchy.**
- Model ciała grzybkowatego z regułami minimalizującymi błąd przewidywania nagrody odtwarza szeroki zakres
  eksperymentów warunkowania (Bennett, Philippides, Nowotny, *Nat. Commun.* 2021, doi 10.1038/s41467-021-22592-4,
  *streszczenie*).
- Dwufazowe „uczenie się uczenia”: najpierw optymalizuje się połączenia, potem sieć uczy się nowych zadań **wyłącznie**
  przez plastyczność bramkowaną dopaminą (Jiang i Litwin-Kumar, *PLoS Comput. Biol.* 2021,
  doi 10.1371/journal.pcbi.1009205, *streszczenie*; opis dwóch faz — *wycinek*).
- Motywy sprzężenia zwrotnego z konektomu larwy zwiększają elastyczność i wyniki modelu w zadaniach uczenia (Eschbach
  i in., *Nat. Neurosci.* 2020, doi 10.1038/s41593-020-0607-9, *streszczenie*).

**Metody uczenia sieci impulsowych (niezależne od muchy).**
- Reguły trójczynnikowe i plastyczność zależna od czasu impulsów modulowana nagrodą (Frémaux i Gerstner, *Front. Neural
  Circuits* 2016, doi 10.3389/fncir.2015.00085; Izhikevich, *Cereb. Cortex* 2007, doi 10.1093/cercor/bhl152; oba
  *streszczenie*).
- **e-prop**: uczenie w trakcie działania dla rekurencyjnych sieci impulsowych, zbliża się do jakości wstecznej
  propagacji w czasie; nadaje się też do uczenia ze wzmocnieniem (Bellec i in., *Nat. Commun.* 2020,
  doi 10.1038/s41467-020-17236-y, *streszczenie*). Że obejmuje neurony adaptacyjne typu ALIF — *wycinek* (dokumentacja
  symulatora NEST).
- Gradienty zastępcze — standard uczenia sieci impulsowych (Neftci, Mostafa, Zenke, arXiv 1901.09948, *streszczenie*).
- Uczenie parametrów przy połączeniach z konektomu: Lappalainen i in., *Nature* 2024, doi 10.1038/s41586-024-07939-3
  (*streszczenie*); uczenie ze wzmocnieniem na konektomie: FlyGM (*streszczenie*).

### 4.2 Sześć dróg — zestawienie [PROP na podstawie LIT]

| # | Droga | Co się zmienia | Czego można nauczyć | Ile „muchy” zostaje | Zgodność z zasadą 3 XI |
|---|---|---|---|---|---|
| a | Interfejs: koder, dekoder, wzmocnienia | nic w sieci | dopasowanie do ramienia; żadnego nowego zachowania | 100 % | zgodne (to robimy dziś) |
| b | Uczenie „dobry/zły” w ciele grzybkowatym | synapsy komórka Kenyona → neuron wyjściowy, regułą z biologii | nowe skojarzenie bodziec → podejdź/unikaj, po jednej–kilku próbach | bardzo dużo: to własny mechanizm muchy | wymaga zgody (plastyczność); sygnał kary/nagrody musi wejść przez zmysł, nie wprost do neuronów dopaminowych |
| c | Nagroda na poziomie synaps w całej sieci (reguły trójczynnikowe) | dowolne wagi | proste przekształcenia; wolno i z szumem | średnio — reguła jest ogólna, nie musza | wymaga zgody |
| d | Strojenie garstki parametrów (progi, stałe czasowe, znak glutaminianu, skale) | parametry, nie połączenia | lepsze działanie tego, co już jest (np. odporność na opóźnienie) | dużo | „strojenie” — wymaga zgody; częściowo już robione (G_INH) |
| e | e-prop w obrębie istniejących połączeń | wagi istniejących synaps | nowe odwzorowania czuciowo-ruchowe na ramię | mało–średnio | wymaga zgody; wagi odchodzą od danych |
| f | Pełne uczenie gradientowe / ze wzmocnieniem | wszystkie wagi (połączenia jako maska) | w zasadzie dowolne zadanie, na jakie pozwala rozmiar sieci | mało; rola połączeń sporna (Dhiman) | sprzeczne z „bez treningu”; nieproponowane wcześniej |

**Czego żadna droga nie da:** rozumienia języka ani nowych przedmiotów. Nowa *umiejętność ruchowa* (np. odłożenie
klocka do pudełka) jest osiągalna tylko drogą e/f — i wtedy uczy się sieć, a nie mucha. INFERRED.

**Co jest specyficznie musze i jednocześnie realne:** droga (b). Uczy tylko jednej rzeczy — wartości bodźca — ale robi
to szybko, lokalnie i mechanizmem opisanym w literaturze; obwód jest w naszych danych. VLA tego nie mają (uczą się
wsadowo, na setkach trajektorii — raport 11 XI).

### 4.3 Czego by trzeba [PROP]

- Do (b): model ok. 4 000 komórek Kenyona + neuronów wyjściowych i dopaminowych; reguła osłabiania z Hige 2015; **zmysł
  kary/nagrody** (np. „za duża siła na padzie” jako bodziec awersyjny, podany przez neurony czuciowe, nie wprost);
  ścieżka od neuronów wyjściowych do neuronów zstępujących (w danych: 88 neuronów zstępujących osiąganych bezpośrednio —
  VERIFIED 11 XI). Ryzyko: siły i znaki połączeń dopaminowych nie wynikają z konektomu — trzeba je założyć.
- Do (d): definicja celu, kilkadziesiąt parametrów na typ komórki, pełny zestaw kontroli z pkt 7.3.
- Do (e)/(f): środowisko uczenia, budżet obliczeń, te same kontrole; odejście od zasady.

### 4.4 Znaczenie dla FlyMind i horyzont

- Dziś sieć nie uczy się niczego (PARTIALLY VERIFIED, pkt 2). Każda z dróg b–f to nowy element i osobna decyzja.
- **Do 1 XII:** nic poza (a). **Explory 2027:** (b) jako główny kandydat, (d) jako drugi. **Długoterminowo:** (e), (f).

---

## 5. Pytanie 3 — czy da się zbudować „tłumacza” na język muchy?

### 5.1 Co wiadomo [LIT]

**Wyjście: jak mucha „mówi”.** Mózg steruje ciałem przez ok. 1 100 neuronów zstępujących (Aymanns, Chen, Ramdya,
*eLife* 2022, doi 10.7554/eLife.81527, *streszczenie*). Pobudzenie większości z nich wywołuje stereotypowe zachowania,
często zależne od stanu wyjściowego zwierzęcia (Cande i in., *eLife* 2018, doi 10.7554/eLife.34275, *streszczenie*).
Neurony „rozkazowe” nie działają same: rekrutują sieci kolejnych neuronów zstępujących, a bez tej rekrutacji dają tylko
proste ruchy (Braun i in., *Nature* 2024, doi 10.1038/s41586-024-07523-9, *streszczenie*). W nagraniach najwięcej
neuronów zstępujących koduje chód, wiele — skręt, nieliczne i słabo — prędkość (Aymanns 2022). Mapa ścieżek zstępujących:
Namiki i in., *eLife* 2018, doi 10.7554/eLife.34272 (*streszczenie*).

**Wejście: jak „mówi się” do zwierzęcia.** Wirtualna rzeczywistość dla swobodnie poruszających się zwierząt, w tym
much: zwierzęciem steruje się, pokazując mu bodźce w zamkniętej pętli (Stowers i in., *Nat. Methods* 2017,
doi 10.1038/nmeth.4399, *streszczenie*). To biologiczny odpowiednik „tłumacza przez zmysły”.

**Jak robią to roboty.** Wzorzec „model językowy wybiera, niższa warstwa wykonuje”: SayCan (arXiv 2204.01691), Code as
Policies (arXiv 2209.07753), Hi Robot (arXiv 2502.19417) — wszystkie *streszczenie*. Model językowy nie steruje
silnikami; wybiera spośród gotowych umiejętności lub parametryzuje gotowe sterowniki.

**Tłumacza „język → model z konektomu” nie znalazłem.** NOT FOUND.

### 5.2 Odpowiedź [PROP / INFERRED]

Tłumacz ma dwie połowy.

**Połowa wejściowa (zadanie → to, co dostaje sieć).** Trzy możliwe konstrukcje:

| Wariant | Jak działa | Zgodność z zasadą 3 XI | Ocena |
|---|---|---|---|
| T1 — przez zmysły („wirtualna rzeczywistość dla sieci”) | Moduł rozumiejący polecenie (klasyczny albo model wizyjno-językowy) wskazuje cel i **przedstawia go musze jako bodziec, który ona rozumie**: mały ruchomy obiekt, obiekt rosnący, dotyk | zgodne co do litery (wejście przez zmysły). Koder pozostaje INŻYNIERIĄ, jak dziś | realny; rozszerza obecny koder: zamiast „zielone” → „to, co wskazano w poleceniu” |
| T2 — przez neurony rozkazowe | Polecenie → pobudzenie wybranych neuronów zstępujących | **sprzeczne** — to sztuczne pobudzanie wybranych neuronów | prostszy i silniejszy; nie proponuję |
| T3 — przez uczenie | Musze nie mówi się, co robić, tylko się ją **uczy** nagrodą/karą, że dany sygnał jest dobry lub zły (pkt 4, droga b) | wymaga zgody na plastyczność | najbardziej „po muszemu”; wolniejszy; Explory 2027 |

**„Słownik muchy” — ile słów ma ten język?** Tyle, ile jest wrodzonych zachowań, które umiemy wywołać zmysłem i odczytać:

| „Słowo” | Bodziec | Obwód | Stan w FlyMind |
|---|---|---|---|
| „skręć do tego” | mały obiekt po jednej stronie | LC10a → … → DNa02 | działa: 38/40 (VERIFIED 11 XI) |
| „uciekaj w tę stronę” | szybko rosnący obiekt w danym miejscu | LC4/LPLC2/LPLC1 → DNp | mapa w danych (D0); NOT IMPLEMENTED |
| „zaciśnij / puść” | dotyk, zgięcie stawu | szczecinki, FeCO → motoneurony | działa: 90/135 (VERIFIED 11 XI) |
| „to dobre / to złe” | sygnał skojarzony z nagrodą/karą | ciało grzybkowate | obwód w danych; NOT IMPLEMENTED |
| „trzymaj kierunek” | punkt odniesienia | kompleks centralny | próbowane, słabe (raport 10 XI) |

Czyli kilka słów. Tłumacz przełoży „*który* obiekt” i „*do niego czy od niego*”. Nie przełoży „*jak*” ani „*po co*”
(„włóż klocek do pudełka”) — do tego potrzebne jest rusztowanie sekwencji, czyli kod klasyczny. INFERRED.

**Połowa wyjściowa (co sieć robi → ruch ramienia i opis słowny).** Dziś: różnica lewy–prawy DNa02 → obrót bazy; różnica
dwóch grup motoneuronów → szczęka. Rozszerzenie: odczyt z populacji neuronów zstępujących (w modelu widzimy wszystkie,
inaczej niż w zwierzęciu) plus prosty klasyfikator stanu („śledzi”, „unika”, „chwyta”, „nic”), co dałoby też czytelny
podpis w demo. Przełożenie ciała muchy (6 nóg, skrzydła) na ramię 5-osiowe pozostaje analogią inżynierską — żadna
literatura tego nie rozwiązuje; prace z pkt 3.1 albo zostawiają ciało muchy, albo uczą odwzorowanie. INFERRED.

### 5.3 Uczciwe zastrzeżenia

1. **W T1 inteligencję zadania dostarcza tłumacz.** Jeśli moduł językowy wskaże cel, a mucha tylko do niego skręci, to
   krytyk powie: „VLM + regulator P zrobi to samo”. Nasze dane to potwierdzają (P 40/40 wobec 38/40).
2. **Przy wejściu-jednej-liczbie połączenia nie mają znaczenia** (raport 10 XI, §3). Tłumacz zyska sens naukowy dopiero
   wtedy, gdy bodziec trafia do neuronów *przestrzennie* (każdy neuron dostaje to, co „widzi” w swoim miejscu) — wtedy
   pracuje mapa z D0.
3. **Granica zasady 3 XI jest nieostra.** Już dziś koder podaje prąd wprost do neuronów LC10a, pomijając siatkówkę
   i płat wzrokowy. T1 tej granicy nie przesuwa, ale jej też nie naprawia. Do Twojej oceny.

### 5.4 Znaczenie dla FlyMind i horyzont

- **Do 1 XII:** sam „słownik muchy” jako tabela na plakat/demo (to opis, nie eksperyment) oraz analiza P2 (pkt 10).
- **Explory 2027:** tłumacz T1 z prawdziwym modułem językowym + przestrzenny koder; T3 po module uczenia.
- **Długoterminowo:** prawdziwy płat wzrokowy (model typu Lappalainen) jako „oczy”, wtedy tłumacz pokazuje musze
  po prostu obraz.

---

## 6. Pytanie 4 — jak trenować modele, żeby robiły coś, czego ich nie uczono?

### 6.1 Co wiadomo [LIT]

| Mechanizm | Przykład i wynik | Co przeczytałem |
|---|---|---|
| Szerokie, różnorodne dane; wspólny trening na danych z sieci i z robotów | RT-2 (arXiv 2307.15818): 6 tys. prób; lepsze uogólnianie na nowe obiekty i polecenia spoza danych robota. π0.5 (arXiv 2504.16054): długie zadania w zupełnie nowych domach. Open X-Embodiment (arXiv 2310.08864): 22 roboty, dodatni transfer między nimi | *streszczenia*. Liczby RT-2 „62 % wobec 32 %” — tylko *wycinek*, NOT VERIFIED |
| Polecenie/cel jako warunek — nowe zadanie to nowa kombinacja znanych części | BC-Z (arXiv 2202.02005): 24 nieznane zadania, średnio 44 % sukcesu, bez pokazów dla nich. π0.7 (arXiv 2604.15483): warunkowanie różnorodnym kontekstem, uogólnianie między robotami | *streszczenia*; π0.7 także raport 11 XI (60–80 % na nieznanych) |
| Losowanie świata w symulacji | Tobin i in. (arXiv 1703.06907): detektor uczony tylko w symulacji działa w rzeczywistości z dokładnością 1,5 cm. OpenAI (arXiv 1910.07113): automatyczne losowanie → przeniesienie na prawdziwą dłoń, oznaki „uczenia się uczenia” | *streszczenia* |
| Uczenie się uczenia | MAML (arXiv 1703.03400): model trenowany tak, by kilka kroków na nowym zadaniu wystarczało | *streszczenie* |
| Hierarchia: planista składa gotowe umiejętności | SayCan, Code as Policies, Hi Robot | *streszczenia* |
| Uczenie z filmów bez etykiet akcji | LAPA (arXiv 2410.11758) | *streszczenie* |
| Wbudowana struktura zamiast uczenia | Zador, *Nat. Commun.* 2019, doi 10.1038/s41467-019-11786-6: większość zachowań zwierząt jest zapisana w genomie jako reguły połączeń. Shuvaev i in., *PNAS* 2024, doi 10.1073/pnas.2409160121: sieć „ściśnięta” o kilka rzędów wielkości zachowuje dużą część jakości *przed* treningiem, a dla złożonych zadań lepiej przenosi się na nowe | *streszczenia* |
| Konektom jako ograniczenie → trafne przewidywania poza treningiem | Lappalainen 2024: sieć uczona jednego zadania (wykrywanie ruchu) trafnie przewiduje aktywność neuronów, zgodnie z 26 badaniami — czyli rzeczy, których nie było w celu uczenia | *streszczenie* |

**Granice (raporty 10–11 XI):** pod zmianą kamery lub pozycji startowej sukces VLA potrafi spaść z ponad 90 % do
kilku–kilkunastu procent (LIBERO-Plus); nieznane długie zadania nadal się nie udają (π0.7). REPORTED.

### 6.2 Odpowiedź [INFERRED]

„Robi coś, czego nie trenowano” prawie zawsze znaczy jedno z trzech: (1) **nowa kombinacja** znanych elementów,
(2) **nowy wygląd** tego samego zadania, (3) **szybkie douczenie** z kilku przykładów. Nie znam wyniku, w którym model
wykonuje coś naprawdę spoza tego, co pokrywały dane lub wbudowana struktura.

### 6.3 Co to znaczy dla sieci muchy [PROP]

- Sieć muchy to czysty przypadek „wbudowanej struktury”: **żadne z jej zachowań nie było trenowane**. W tym sensie
  FlyMind już jest przykładem „robi coś bez uczenia” — ale tylko w zakresie przewidzianym przez ewolucję (i przez nasz
  interfejs).
- Co da się uczciwie sprawdzić: **uogólnianie wewnątrz wrodzonej mapy** — ustawić interfejs na kilku położeniach bodźca,
  testować na położeniach, prędkościach i rozmiarach, których przy ustawianiu nie było; porównać sieć z danych,
  przetasowane i małą zwykłą sieć nauczoną na tych samych kilku punktach. Jeśli mapa jest w połączeniach, sieć z danych
  powinna uogólniać „za darmo”. To jest dodatkowy wariant E1, nie nowy eksperyment. HYPOTHESIS.
- Zachowanie *ani wrodzone, ani uczone* nie pojawi się samo. Można je uzyskać tylko przez złożenie wrodzonych kawałków
  przez tłumacza (pkt 5) albo przez uczenie (pkt 4).
- **Horyzont:** wariant uogólniania — razem z E1, jeśli E1 zostanie zatwierdzone; reszta Explory 2027.

---

## 7. Pytanie 5 — jak dostrajać modele zbudowane ze skanów mózgu?

### 7.1 Co wiadomo [LIT]

| Podejście | Praca | Wynik | Co przeczytałem |
|---|---|---|---|
| Połączenia stałe; uczone tylko nieznane własności neuronów i synaps, pod zadanie | Lappalainen i in., *Nature* 2024 | 64 typy komórek płata wzrokowego; przewidywania zgodne z 26 badaniami; strategia działa tym lepiej, im rzadsze połączenia | *streszczenie*; rozmiar (ok. 44 tys. neuronów) — *wycinek* |
| Połączenia stałe; dopasowanie do **nagrań aktywności** | Mi i in., ICLR 2022 (C. elegans) | ograniczenie konektomem poprawia przewidywanie aktywności neuronów nieużytych w dopasowaniu | *wycinek* |
| Połączenia jako dozwolone wagi; dopasowanie do reakcji na pobudzanie pojedynczych neuronów | Creamer, Leifer, Pillow, bioRxiv 2024, doi 10.1101/2024.09.22.614271 (C. elegans) | model oddaje oddziaływania między neuronami w 82 % tak dobrze, jak powtarzalne są same dane; **z przetasowanym konektomem znacznie gorzej**; dodanie połączeń spoza konektomu nie pomaga | *streszczenie* |
| Konektom jako wstępne założenie statystyczne dla modelu przyczynowego | Pospisil i in., *Nature* 2024, doi 10.1038/s41586-024-07982-0 | dynamiką mózgu muchy rządzi wiele małych, w dużej mierze niezależnych obwodów → model przyczynowy jest osiągalny | *streszczenie* |
| Teoria: kiedy konektom wystarcza | Beiran i Litwin-Kumar, bioRxiv 2024, doi 10.1101/2024.02.22.581667 | **sam konektom często nie wyznacza dynamiki** sieci wykonującej zadanie; nagrania z małego podzbioru neuronów usuwają tę niejednoznaczność | *streszczenie* |
| Dopasowanie do zachowania po wyłączaniu neuronów | Cowley i in., *Nature* 2024, doi 10.1038/s41586-024-07451-8 | „trening z nokautami” daje odwzorowanie jeden-do-jednego: jednostka modelu ↔ typ neuronu (sieć głęboka, nie konektom) | *streszczenie* |
| Uczenie ze wzmocnieniem na konektomie | FlyGM (arXiv 2602.17997) | działa dla ciała muchy; dwa etapy (wstępny + PPO) | *streszczenie*; dwa etapy — *wycinek* |
| Model podstawowy z nagrań, douczany do nowego osobnika | Wang i in., *Nature* 2025, doi 10.1038/s41586-025-08829-y (mysz) | uogólnia na nowe myszy przy minimalnym treningu i na nowe rodzaje bodźców; uczony na aktywności, nie na konektomie | *streszczenie* |
| Sterownik ciała uczony naśladowaniem, potem używany przez warstwę wyższą | Vaxenburg i in., *Nature* 2025, doi 10.1038/s41586-025-09029-4 | realistyczny chód i lot; sterownik wysokiego poziomu korzysta z gotowego niskiego (bez konektomu) | *streszczenie* |
| Model nicienia w zamkniętej pętli | Zhao i in., *Nat. Comput. Sci.* 2024, doi 10.1038/s43588-024-00738-w | mózg dopasowany do danych + ciało + środowisko | *streszczenie* |
| Bez żadnego dostrajania | Shiu i in., *Nature* 2024 | wystarcza do przewidzenia obwodów karmienia i czyszczenia | *streszczenie* |
| Ostrzeżenie o kontrolach | Dhiman, arXiv 2604.04033 | po treningu przewaga konektomu znika przy uczciwych kontrolach | *streszczenie* |

### 7.2 Odpowiedź — „drabina dostrajania” [PROP na podstawie LIT]

Od najmniej do najbardziej inwazyjnego; każdy szczebel zostawia mniej „danych” w modelu:

| Szczebel | Co się stroi | Liczba parametrów (rząd) | Wzór w literaturze | FlyMind |
|---|---|---|---|---|
| 0 | tylko koder/dekoder | kilka | — | robione |
| 1 | globalne skale (siła synaps, hamowanie, znak glutaminianu) | < 10 | Shiu (1 parametr) | częściowo robione (G_INH) |
| 2 | własności **na typ komórki** (próg, stała czasowa, adaptacja) | dziesiątki–setki | Lappalainen | NOT IMPLEMENTED |
| 3 | skala każdej *istniejącej* synapsy, znak stały, kara za odejście od liczby synaps | tysiące–miliony | Creamer; Mi | NOT IMPLEMENTED |
| 4 | nowe połączenia spoza danych | dowolnie | — (Creamer: nie pomaga) | nieproponowane |

**Do czego dostrajać** — trzy możliwe cele, od najbardziej do najmniej obronnego naukowo:
1. **Do biologii:** do opublikowanych pomiarów (np. kierunki reakcji neuronów, znane odruchy), a potem test na robocie
   bez dalszych zmian. Wtedy robot jest sprawdzianem, nie celem uczenia. To najlepiej pasuje do ducha zasady 3 XI.
2. **Do nagrań aktywności:** najsilniejsze według Beirana i Creamera, ale potrzebne są dane z nagrań much — nie mamy.
3. **Do zadania na ramieniu:** najprostsze i najskuteczniejsze, ale najdalsze od „mucha steruje”.

### 7.3 Kontrole, bez których wynik dostrajania jest bezwartościowy [PROP]

1. Sieci przetasowane dostają **dokładnie ten sam budżet dostrajania** (lekcja z Dhimana).
2. Zwykła mała sieć tej samej wielkości — też.
3. Raport „jak daleko odeszliśmy od danych” (ile zmieniły się parametry).
4. Zbiór testowy niewidziany przy dostrajaniu; ziarna i progi zapisane z góry.
5. Świadomość niejednoznaczności (Beiran): wiele zestawów parametrów da ten sam wynik w zadaniu — nie wolno ich
   interpretować jako „odkrytych własności muchy”.

### 7.4 Znaczenie dla FlyMind i horyzont

- Szczebel 2 z celem „biologia” to wiarygodny projekt na Explory 2027 i naturalna kontynuacja zaplanowanego testu
  wariantów neuronu (N1). Wymaga zgody — to „strojenie”.
- **Do 1 XII:** nic. **Explory 2027:** szczebel 2. **Długoterminowo:** szczebel 3 i dopasowanie do nagrań.

---

## 8. Zestawienie horyzontów

| | Do 1 XII 2026 | Explory 2027 | Długoterminowo |
|---|---|---|---|
| P1 — dorównanie VLA | nie; można jedynie zmierzyć czas decyzji małego VLA na tym Macu (E3, niezatwierdzone) | wspólny stół: sieć, przetasowane, klasyczny, prawdziwy mały VLA | prawdziwe ramię |
| P2 — uczenie | nic poza interfejsem | moduł „dobry/zły”; strojenie na typ komórki | e-prop, uczenie ze wzmocnieniem |
| P3 — tłumacz | „słownik muchy” jako opis; analiza danych P2 | T1 z modułem językowym i koderem przestrzennym; T3 | prawdziwy płat wzrokowy jako oczy |
| P4 — bez treningu | wariant uogólniania w E1 (jeśli zatwierdzone) | para przeciwnych przewidywań (mapa: połączenia ważne; uczenie: nieważne) | — |
| P5 — dostrajanie | nic | szczebel 2 do biologii, z kontrolami | szczebel 3, nagrania aktywności |

Wszystkie oceny czasu to opinia. Do 1 XII zostało 19 dni, plakat 16 XI, dwie otwarte usterki bezpieczeństwa (prędkość
stawu 1,89 rad/s, wnikanie padów) — nie proponuję niczego, co wymaga nowego mechanizmu w sieci.

---

## 9. Sprzeczności z zasadą z 3 XI — wprost

| Odpowiedź w tym raporcie | Gdzie koliduje | Kto decyduje |
|---|---|---|
| Tłumacz T2 (neurony rozkazowe) | „bez sztucznego pobudzania wybranych neuronów” — sprzeczne wprost | nie proponuję; Adam, jeśli zechce |
| Tłumacz T1 (przez zmysły) | litera zasady zachowana, ale o tym, *co* robić, decyduje tłumacz; mucha decyduje *jak* się ruszyć. To rola B/C z raportu 11 XI, nie rola A | Adam (rola muchy nadal nierozstrzygnięta) |
| Każde uczenie (drogi b–f, szczeble 2–3) | „bez strojenia i treningu bez zgody”; po uczeniu sieć nie jest już „połączeniami z danych” | Adam, osobno dla każdej drogi |
| Uczenie „dobry/zły” | sygnał kary musi wejść przez zmysł; podanie go wprost do neuronów dopaminowych byłoby sztucznym pobudzaniem | do ustalenia w rejestracji wstępnej |
| Porównanie z VLA | wymaga wytrenowania VLA — to trening *innego* modelu, nie muchy; zasady nie łamie, ale kosztuje czas | Adam |
| Obecny koder | już dziś podaje prąd wprost do neuronów LC10a, z pominięciem oka — stan zastany, nie nowa propozycja | do wiadomości |

---

## 10. Eksperymenty, które bym zaproponował — **żadnego nie zaczynam**

Wszystkie: nowe pliki, bez zmian w modułach wspólnych, rejestracja wstępna z sumą kontrolną przed uruchomieniem, nowe
ziarna spoza zużytych zakresów. Czasy to moje szacunki.

| # | Co | Co by pokazał | Koszt | Ryzyko | Jak wygląda wynik negatywny |
|---|---|---|---|---|---|
| P1 | **Analiza danych:** czy połączenia wejściowe do komórek Kenyona różnią się od losowych (to „L0” z 11 XI) | czy uczenie w ciele grzybkowatym jest przypadkiem, w którym połączenia *nie* powinny mieć znaczenia | ok. pół dnia, bez symulacji | niejednoznaczne typy w adnotacjach | połączenia wyraźnie nielosowe → para „przeciwnych przewidywań” upada, trzeba ją przemyśleć |
| P2 | **Analiza danych: „słownik muchy”** — dla każdej grupy czuciowej, którą umiemy pobudzić, lista ścieżek do neuronów zstępujących/ruchowych, które umiemy odczytać | ile „słów” realnie ma tłumacz | ok. 1 dzień, bez symulacji | ścieżki wielostopniowe trudno interpretować | 2–3 słowa → tłumacz jest trywialny i nie warto go budować |
| P3 | **Tłumacz T1 v0 w symulacji:** polecenie „lewy/prawy” lub „ten kolor” → bodziec → sieć obraca bazę | odsetek poprawnie wykonanych poleceń; ramiona: dane, przetasowane, klasyczny | 2–3 dni + kontrola | przy wejściu-jednej-liczbie przetasowane wypadną tak samo | przetasowane = dane (**spodziewane** bez kodera przestrzennego) → tłumacz działa, ale mucha nie jest potrzebna |
| P4 | **Moduł uczenia „dobry/zły”** (droga b): jedno skojarzenie „sygnał → unikaj” | po ilu próbach sieć zmienia zachowanie; kontrole: bez dopaminy, przetasowane wejście (przewidywanie: bez różnicy), tablica klasyczna | 1–2 tygodnie; **wymaga zgody na plastyczność** | założone siły i znaki; znów „tablica z dodatkowymi krokami” | brak zmiany zachowania w ustalonej liczbie prób, albo zmiana także bez dopaminy |
| P5 | **Strojenie na typ komórki** (szczebel 2), cel: odporność V5 na opóźnienie obrazu (dziś 17/40) | czy strojenie pomaga i czy pomaga bardziej sieci z danych niż przetasowanym | 2–4 tygodnie; **wymaga zgody na strojenie** | niejednoznaczność parametrów; dopasowanie do symulacji | przetasowane po tym samym strojeniu osiągają to samo → połączenia nie dają przewagi także po dostrojeniu |
| P6 | **Wspólny stół z prawdziwym małym VLA** w symulacji, zadanie szybkie | pierwsze uczciwe „mucha wobec VLA” | 2–3 tygodnie + trening VLA | trening VLA może się nie udać na tym sprzęcie; klasyczny wygra z obojgiem | VLA ≥ mucha także w zadaniu szybkim → nie ma sensu, w którym mucha dorównuje |
| — | E1, E2, E3 z raportu 11 XI | bez zmian | bez zmian | bez zmian | **nadal niezatwierdzone**; do E1 proponuję dodać wariant uogólniania z pkt 6.3 |

**Moja kolejność, gdybyś pytał (opinia):** P1 i P2 są tanie, bezpieczne i nie łamią żadnej zasady. P3 bez kodera
przestrzennego najpewniej da wynik „mucha niepotrzebna” — sensowny dopiero po E1. P4–P6 to Explory 2027.

---

## 11. Adwokat diabła i ograniczenia

1. **Tłumacz może okazać się przebraniem.** Jeśli całą treść polecenia rozumie moduł językowy, „mucha” jest tylko
   regulatorem. To najpoważniejszy zarzut wobec pkt 5.
2. **Uczenie „dobry/zły” to w praktyce tablica skojarzeń.** Robi to, co kilka linijek kodu; wartość jest naukowa
   (mechanizm z biologii w pętli z robotem), nie użytkowa.
3. **Każde uczenie rozmywa twierdzenie projektu.** Dziś mówimy „połączenia z danych, zero treningu”. Po dostrojeniu
   trzeba mówić „połączenia z danych, parametry dopasowane” — a literatura (Dhiman) pokazuje, że wtedy przewaga
   połączeń bywa złudzeniem.
4. **Wszystkie pozytywne przykłady z literatury dotyczą ciała muchy albo chodu**, nie chwytania ramieniem. Przeniesienie
   na SO-101 jest analogią.
5. **Czytałem streszczenia, nie pełne teksty.** Streszczenia podają wnioski autorów w najkorzystniejszej wersji.
   Żadnej liczby z tego raportu nie należy dawać na plakat bez otwarcia publikacji. Preprinty arXiv z 2026 r. (FLYNN,
   FlyCNS, Guan i in., Dhiman, FlyGM) są nierecenzowane.
6. **Przegląd Nori przeczytałem dopiero po napisaniu pkt 0–11** (porównanie w pkt 12A). Jego wniosków nie przyjąłem
   automatycznie; tam, gdzie się różnimy, zostawiłem obie wersje.
7. **Fakty FlyMind nie były dziś przeliczane**; brak plastyczności w kodzie przyjąłem z własnego raportu z 11 XI.
8. **„Nie znalazłem”** zawsze opisuje moje szukanie. Dotyczy to zwłaszcza: tłumacza język → konektom, porównania
   konektom–VLA, reguły synaptycznej uczenia operanckiego u muchy.
9. **Moja stronniczość.** Trzeci raport z rzędu proponuję kierunki, w których „połączenia powinny mieć znaczenie”.
   Dlatego przy P3, P4 i P5 z góry wpisałem, że wynik negatywny jest spodziewany lub równie prawdopodobny.
10. Szacunki czasu i prawdopodobieństw to opinie.

---

## 12. Źródła i co z nich przeczytałem

**Wcześniejsze raporty (sprawdzone dziś, `shasum -a 256`, `stat`):**
`bio_advantage_research_20261110.md` → `1b6e93ee463cc2f27284360b8d2fa5ed4c9599364dd38a48f06e9657995cb7d9` — zgodna
z wartością zapisaną 11 XI, czyli plik niezmieniony (VERIFIED).
`fly_vs_vla_research_20261111.md` → `a1ebc4f6b927d9e5576b64fe9ebaa9cd45bbffccb2652dc099bc3fff39a25bc7`; data
modyfikacji 11 XI 16:11:10, bez zmian od utworzenia. Nie mam wcześniej zapisanej sumy do porównania, więc
„niezmieniony” opieram na dacie pliku (PARTIALLY VERIFIED). HEAD repozytorium: `664b611…`, bez zmian.

**Pełne streszczenie pobrane dziś (Europe PMC, po DOI lub tytule):**
Bellec 2020 (10.1038/s41467-020-17236-y) · Lappalainen 2024 (10.1038/s41586-024-07939-3) · Jiang i Litwin-Kumar 2021
(10.1371/journal.pcbi.1009205) · Hige 2015 (10.1016/j.neuron.2015.11.003) · Pospisil 2024 (10.1038/s41586-024-07982-0) ·
Cowley 2024 (10.1038/s41586-024-07451-8) · Braun 2024 (10.1038/s41586-024-07523-9) · Vaxenburg 2025
(10.1038/s41586-025-09029-4) · Wang 2025 (10.1038/s41586-025-08829-y) · Zador 2019 (10.1038/s41467-019-11786-6) ·
Wang-Chen 2024 (10.1038/s41592-024-02497-y) · Beiran i Litwin-Kumar 2024 (10.1101/2024.02.22.581667) · Creamer 2024
(10.1101/2024.09.22.614271) · Frémaux i Gerstner 2016 (10.3389/fncir.2015.00085) · Cande 2018 (10.7554/eLife.34275) ·
Namiki 2018 (10.7554/eLife.34272) · Aso 2014 (10.7554/eLife.04580) · Eschbach 2020 (10.1038/s41593-020-0607-9) ·
Bennett 2021 (10.1038/s41467-021-22592-4) · Shuvaev 2024 (10.1073/pnas.2409160121) · Zhao 2024
(10.1038/s43588-024-00738-w) · Izhikevich 2007 (10.1093/cercor/bhl152) · Stowers 2017 (10.1038/nmeth.4399) ·
Ehweiner 2024 (10.12688/f1000research.146347.2) · Shiu 2024 (10.1038/s41586-024-07763-9) · Aymanns 2022
(10.7554/eLife.81527).

**Pełne streszczenie pobrane dziś (arXiv, po numerze):**
2602.17997 (FlyGM) · 2607.00025 (FLYNN) · 2609.28816 (FlyCNS) · 2609.27001 (Guan i in.) · 2604.04033 (Dhiman) ·
2504.16054 (π0.5) · 2604.15483 (π0.7) · 2307.15818 (RT-2) · 2202.02005 (BC-Z) · 2310.08864 (Open X-Embodiment) ·
1703.06907 (Tobin) · 1910.07113 (OpenAI) · 1703.03400 (MAML) · 2204.01691 (SayCan) · 2209.07753 (Code as Policies) ·
2502.19417 (Hi Robot) · 2410.11758 (LAPA) · 1901.09948 (Neftci) · 2506.01844 (SmolVLA).

**Tylko wycinek z wyszukiwarki (NOT VERIFIED do użytku na plakacie):** Mi i in., ICLR 2022 („Connectome-constrained
Latent Variable Model of Whole-Brain Neural Activity”); liczby RT-2 dla nieznanych obiektów; dane o π0.5 (ok. 400 h,
ok. 100 domów); dwuetapowy trening FlyGM; rozmiar modelu Lappalainena z repozytorium `TuragaLab/flyvis`; to, że e-prop
obejmuje neurony ALIF (dokumentacja NEST); stan Eon Systems; plakat grupy Brembsa.

**Z raportów 10–11 XI, dziś nieotwierane:** DynamicVLA (2601.22153), test na SO-101 (2606.08881), LIBERO-Plus
(2510.13626), Booker i Quinn 1981, Dombrovski 2023, wszystkie liczby FlyMind i MaleCNS.

**Przegląd Nori:** przeczytany z pliku dostarczonego przez Adama — patrz pkt 12A.

---

## 12A. Przegląd Nori „Kiedy uczenie maszynowe oparte na biologicznych mózgach się opłaca” — porównanie

**Źródło:** plik `/Users/admin/Downloads/research_bio_ml_20261112.md` (poza repozytorium), SHA-256
`56fea667da7ad34e3bdddf0d6c714c6e88b78e555ed580ecded55f1f37ffe74f`; w nagłówku autor „Grok Bot”, data 12 XI 2026.
Przeczytałem cały (144 linie). **Wszystko, co z niego pochodzi, ma tu etykietę REPORTED**, chyba że zaznaczam, że
sprawdziłem to sam. Przegląd używa własnych etykiet („VERIFIED” = jego autor otworzył źródło) — to nie są moje
weryfikacje.

**Co sprawdziłem sam z jego źródeł (dziś, Europe PMC, *streszczenie*):** Beiran i Litwin-Kumar, *Nat. Neurosci.* 2025
(10.1038/s41593-025-02080-4) · Bargmann i Marder 2013 (10.1038/nmeth.2451) · Schlegel i in. 2024
(10.1038/s41586-024-07686-5) · Paredes-Vallés i in. 2024 (10.1126/scirobotics.adi0591) · Stone i in. 2017
(10.1016/j.cub.2017.08.052) · Falanga i in. 2020 (10.1126/scirobotics.aaz9712). Tytuły, autorzy i treść streszczeń
zgadzają się z tym, co pisze przegląd — VERIFIED. **Nie udało mi się sprawdzić** (brak w Europe PMC): Dampfhoffer 2023,
Yin i in. 2021, Davies 2021, Lechner 2020 — zostają REPORTED. Pozostałych źródeł przeglądu nie otwierałem.

### Gdzie się zgadzamy

| Teza | Przegląd Nori | Moje raporty |
|---|---|---|
| Zysk z modeli z konektomu jest dziś naukowy, nie inżynierski | pkt 1 | raport 11 XI §6.3; tu pkt 3 |
| Sam konektom często nie wyznacza działania sieci (Beiran i Litwin-Kumar) | pkt 2 | tu pkt 7.1 i 7.3 |
| Nie ma dowodu, że sieć z konektomu steruje manipulatorem lepiej niż klasyczny sterownik; brak porównania „konektom kontra losowa sieć” w robotyce | pkt 1, koniec §1 | raport 10 XI §5.2; tu pkt 3.1 |
| Mała sieć nie konkuruje z VLA w języku i semantyce; możliwa nisza to szybki odruch, brak danych, mała moc, czytelny mechanizm — i **klasyczny sterownik też to ma** | pkt 6, §6 | raport 11 XI §4; tu pkt 3.2 |
| Reguły trójczynnikowe (dopamina, ciało grzybkowate) to naturalny kierunek „uczenia po muszemu”, ale kierunek, nie gotowy wynik | §4 | tu pkt 4.2, droga b |
| Zador 2019 to najlepszy argument teoretyczny, ale esej, nie eksperyment | §2 | tu pkt 6.1 |
| Nie wolno twierdzić: „lepszy niż P / klasyczny chwyt / VLA”, „oszczędza energię”, „mózg muchy steruje robotem” (8,8 % i 16,0 % poleceń) | §8 | raporty 10–11 XI; tu pkt 2 |
| Liczby RT-2, OpenVLA, π0 | §6 | zgodne z tabelą w raporcie 10 XI §5.1 |

### Gdzie się różnimy albo gdzie dodaję zastrzeżenie

1. **„Można bronić tezy, że zachowanie zależy od prawdziwego okablowania” (Nori, pkt 7).** Zgadzam się **tylko dla
   obrotu bazy (V5)**: 38/40 wobec 3/40 po przetasowaniu i 0/40 po zamianie stron (VERIFIED 11 XI). Nie zgadzam się na
   wersję ogólną: w chwycie, przy przetasowaniach z wyrównaną siłą, sieć z danych jest 4. z 11 (VERIFIED 11 XI),
   a wejście i wyjście sieci to pojedyncze liczby (raport 10 XI §3). Czy przetasowanie w V5 miało wyrównaną siłę tak jak
   w chwycie — dziś **NOT VERIFIED**. Jeśli nie miało, wynik 3/40 może znaczyć „przetasowanie zrywa drogę sygnału”,
   a nie „liczy się dokładny wzór połączeń”. Bezpieczne zdanie: „w zadaniu obrotu wynik zależy od połączeń z danych;
   w chwycie tego nie wykazano”.
2. **Odporność jako „mierzalny atut do 1 XII” (Nori, pkt 8 i §8.3).** Jestem ostrożniejszy. Jedyne nasze dane o odporności
   świadczą przeciw sieci: 17/40 przy opóźnieniu 50 ms, 0/40 bez obrazu. Przegląd sam zauważa, że dla regulatora P nie
   podano wyniku z opóźnieniem. W repozytorium jest plik z serii próbnej `results/v5/v5_dev4_p_delays_…json` (P
   z opóźnieniami) — **dziś go nie analizowałem, NOT VERIFIED**. Test odporności warto zrobić, ale trzeba z góry zapisać,
   że spodziewany wynik to „P jest odporniejszy”.
3. **Koszt obliczeń i opóźnienie (Nori, §8.1).** Zgoda co do kierunku; to nasze odłożone E3. Połowa już jest: 1,65 ms
   na krok sieci na jednym rdzeniu (VERIFIED 11 XI). Brakuje tylko pomiaru małego VLA na tym samym Macu. Wynik będzie
   „sieć dużo szybsza od VLA, P jeszcze szybszy” — to opis, nie przewaga.
4. **Energia jako liczba zdarzeń synaptycznych (Nori, §8.2).** Nowy pomysł, którego nie miałem. Tani, ale dwa
   zastrzeżenia: (i) to szacunek teoretyczny, nie pomiar — przegląd też tak pisze; (ii) regulator P ma koszt praktycznie
   zerowy, więc porównanie ma sens tylko wobec VLA i tylko z dopiskiem „na sprzęcie neuromorficznym, którego nie mamy”.
5. **Ablacje typów neuronów jako najmocniejszy atut naukowy (Nori, §8.4).** Zgadzam się i uważam to za najlepszą nową
   sugestię z przeglądu: nie wymaga uczenia, nie łamie zasady z 3 XI, pokazuje mechanizm, czego VLA nie daje. W repozytorium
   są już dwa pliki z ablacji V5 z 29 X (`results/v5_ablation/`), których **dziś nie analizowałem (NOT VERIFIED)**. Dodaję
   to jako P7 poniżej.
6. **Zakres.** Przegląd nie zajmuje się tłumaczem (pytanie 3) ani dostrajaniem modeli ze skanów (pytanie 5) poza tezą
   „parametry trzeba dopasować”. Za to szeroko omawia sprzęt neuromorficzny i kamery zdarzeniowe, których ja w tym
   raporcie nie omawiałem. Oba teksty się uzupełniają, nie dublują.

### Co przegląd wnosi nowego (REPORTED, o ile nie zaznaczono inaczej)

- **Poprawka do mojego cytatu:** praca Beirana i Litwin-Kumara jest już opublikowana w *Nature Neuroscience* 2025
  (10.1038/s41593-025-02080-4) — VERIFIED dziś. W pkt 7.1 cytuję wersję bioRxiv 2024; treść streszczenia jest zgodna.
- **Adaptacyjne rekurencyjne sieci impulsowe** (neurony z adaptacją, jak nasze ALIF) uczone gradientem zastępczym
  dorównują klasycznym sieciom rekurencyjnym w zadaniach czasowych (Yin, Corradi, Bohté 2021). Wzmacnia to ocenę, że
  drogi e/f z pkt 4.2 są technicznie wykonalne dla naszego typu neuronu. REPORTED.
- **Energia:** sieci impulsowe wygrywają energetycznie dopiero przy bardzo rzadkiej aktywności (0,15–1,38 impulsu na
  synapsę na wnioskowanie; Dampfhoffer 2023), a zwykłe sieci na chipie Loihi dają „skromny, jeśli jakikolwiek” zysk
  (Davies 2021). Symulacja na MacBooku nie daje żadnej przewagi energetycznej. REPORTED; zgodne z moją oceną z 10 XI
  (kandydat 10: sprzęt neuromorficzny poza zakresem).
- **Przykłady małych sieci w wąskich niszach:** dron sterowany siecią impulsową na Loihi, 200 Hz, 7–12 mW na sieć
  (Paredes-Vallés 2024 — streszczenie VERIFIED dziś; autorzy sami piszą, że takie systemy ograniczały się dotąd do
  prostych zadań); omijanie przeszkód z opóźnieniem 3,5 ms (Falanga 2020 — VERIFIED dziś; to kamera zdarzeniowa
  i klasyczny algorytm, nie sieć biologiczna); model integracji drogi w mózgu pszczoły zbudowany z anatomii (Stone
  2017 — VERIFIED dziś) jako najbliższy nam przykład „funkcja sterowania wprost z anatomii”.
- **Zmienność między osobnikami:** około jednej trzeciej typów komórek z wcześniejszego konektomu nie dało się pewnie
  odnaleźć w drugim mózgu (Schlegel 2024 — VERIFIED dziś). Wniosek przeglądu, że pojedyncze połączenie z jednego
  osobnika jest mniej pewne niż powtarzalne, wzmacnia nasze zastrzeżenie „jedno zwierzę” z raportów 10–11 XI.
- **Wzorzec historyczny:** opłacały się abstrakcyjne zasady z biologii (hierarchia wzrokowa → sieci splotowe; dopamina →
  uczenie błędem przewidywania), nie dosłowne kopie mózgu. REPORTED. To argument przeciw oczekiwaniu przewagi użytkowej
  od FlyMind i za ramą „platforma badawcza”.
- **Uwaga o `MASTER_CONTEXT.md`:** przegląd pisze, że plik błędnie nazywa MaleCNS zbiorem „Janelia FlyWire”. Sprawdziłem
  dziś `flymind/FLYMIND_MASTER_CONTEXT.md`: linia 18 mówi „MaleCNS v1.0, Janelia; to nie jest FlyWire”, a linia 142
  wymienia „Dane FlyWire” jako błąd. W tym pliku błędu więc nie ma (VERIFIED); możliwe, że Nori czytał inną wersję.
  Pliku nie zmieniałem.

### Czy przegląd zmienia moje odpowiedzi na pięć pytań?

Nie zmienia żadnej; trzy wzmacnia, jedną uzupełnia.
- **Pytanie 1:** wzmacnia („nisza tak, przewaga nie; zawsze porównywać z klasycznym”).
- **Pytanie 2:** wzmacnia (reguły trójczynnikowe jako kierunek; e-prop i gradient zastępczy jako sprawdzone narzędzia).
- **Pytanie 5:** wzmacnia („parametry dopasowane do danych albo zadania, a nie tylko wagi z konektomu”).
- **Do 1 XII:** uzupełnia moją listę o ablacje i o szacunek zdarzeń synaptycznych.

### Dodatkowa propozycja po lekturze przeglądu — **nie zaczynam**

| # | Co | Co by pokazał | Koszt | Ryzyko | Wynik negatywny |
|---|---|---|---|---|---|
| P7 | **Ablacje typów neuronów w V5.** Krok 1 (bez symulacji): przeczytać i podsumować istniejące pliki `results/v5_ablation/` z 29 X oraz serię P z opóźnieniami. Krok 2 (symulacja, osobna zgoda): brakujące ablacje według z góry zapisanej listy typów | które typy neuronów są konieczne do obrotu bazy — czytelny mechanizm na plakat i demo | krok 1: kilka godzin; krok 2: 1–2 dni | istniejące serie mogą być próbne i nie nadawać się do cytowania | usunięcie dowolnego typu daje podobny spadek → brak wyróżnionego mechanizmu, sieć działa jak jeden wzmacniacz |

Krok 1 z P7 oraz P1 i P2 to trzy rzeczy bez symulacji i bez uczenia, które mieszczą się przed 1 XII.

---

## 13. Decyzje dla Adama

1. **P7, krok 1** (po lekturze przeglądu Nori, pkt 12A): zgoda na przeczytanie i podsumowanie istniejących plików
   z ablacji V5 i serii P z opóźnieniami? Tylko odczyt, kilka godzin.
2. **P1 i P2** (dwie analizy samych danych, łącznie ok. 1,5 dnia, bez symulacji): zgoda na napisanie rejestracji
   wstępnej? Uruchomienie to osobna zgoda.
3. **Uczenie w modelu** (moduł „dobry/zły”, strojenie na typ komórki): zostawić jako plan na Explory 2027, czy odrzucić
   jako sprzeczne z zasadą?
4. **Tłumacz:** czy wariant T1 (przez zmysły, ale z modułem językowym decydującym o celu) mieści się w zasadzie z 3 XI?
   Od tego zależy rola muchy (A/B/C z raportu 11 XI).
5. **E1, E2, E3** pozostają niezatwierdzone — bez zmian.

STOPPED AT CHECKPOINT 1 — awaiting Adam's approval.
