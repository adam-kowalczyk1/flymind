# FlyMind — jak mózg działa jako jeden organizm i czy AI może tak samo

Raport badawczy, 2026-11-12. Autor: Claude (Fable 5.2), na prośbę właściciela projektu.
Buduje na czterech wcześniejszych raportach w `flymind/reports/` (10, 11 i dwa z 12 XI) — wszystkie nietknięte, sumy
kontrolne w pkt 10. Status pliku: nowy, niezacommitowany, **jedyny plik utworzony w tej sesji w repozytorium**.
Niczego nie symulowałem, nie trenowałem, nie pobierałem danych ani modeli, nie użyłem żadnych ziaren losowych, nie
zmieniłem żadnego istniejącego pliku, nie commitowałem. W repozytorium wykonałem tylko odczyt (`grep`, `shasum`, `git
rev-parse`). HEAD: `664b611`.

**Etykiety dowodów:** **VERIFIED** (sprawdzone dziś; podane źródło lub plik), **PARTIALLY VERIFIED**, **REPORTED**
(przepisane ze źródła, którego treści dziś nie otworzyłem — np. potwierdzony tylko tytuł — albo z wyszukiwarki),
**INFERRED** (mój wniosek z faktów), **HYPOTHESIS**, **NOT VERIFIED**, **NOT IMPLEMENTED**.
Przy literaturze „VERIFIED” znaczy tylko tyle: **praca istnieje i jej streszczenie mówi to, co piszę**. Nie znaczy, że
sama teza pracy jest prawdą — wiele z nich to przeglądy, modele i artykuły-opinie, co zaznaczam.
**Pełnego tekstu żadnej publikacji dziś nie czytałem — wyłącznie streszczenia** (Europe PMC, arXiv, Crossref).

Trzy rzeczy trzymam osobno: **[LIT]** literatura, **[FM]** fakty o FlyMind, **[PROP]** moje propozycje i opinie.

---

## 0. Streszczenie dla Adama (prostym językiem)

1. **Co robi z mózgu całość?** Nie ma w nim „centrali”, która skleja osobne moduły. Jedność bierze się z sześciu rzeczy,
   które działają naraz: (a) mózg ma **jedno zadanie — utrzymać przy życiu jedno ciało**, i wszystko jest temu
   podporządkowane; (b) **stan wewnętrzny** (głód, pragnienie, strach, pobudzenie) jest rozsyłany chemicznie po całym
   mózgu i zmienia sposób, w jaki *te same* obwody przetwarzają *te same* bodźce; (c) sygnały o własnym ruchu i stanie
   są **prawie wszędzie**, także w „czysto wzrokowych” częściach; (d) **pamięć i przewidywanie to ta sama maszyneria**,
   a emocja decyduje, co zostanie zapamiętane; (e) jedno ciało może w danej chwili zrobić jedną rzecz, więc wszystko
   schodzi się w **jednym wąskim gardle wyboru działania**; (f) nie ma osobnych części „od emocji” i „od myślenia”
   — te same sieci robią jedno i drugie. Podział na „percepcję, pamięć, emocje, motywację” pochodzi
   z psychologii — część neurobiologów twierdzi wprost, że mózg nie jest tak pokrojony.
2. **Czy AI może to odtworzyć?** Po kawałku — tak, i to już zrobiono. W całości — nie zrobiono tego nigdzie, co bym
   znalazł. Zasada, która (moim zdaniem, na podstawie literatury) jest potrzebna, to nie „więcej modułów”, tylko:
   **własne zmienne wewnętrzne, od których zależy „przeżycie” systemu, rozsyłane do wszystkich części i będące jedynym
   źródłem nagrody**, plus jeden model świata służący naraz pamięci i przewidywaniu, plus zamknięta pętla z ciałem.
3. **Jakie próby istnieją?** Są trzy rodziny: agenci z modelem świata (Dreamer — uczy się, „wyobrażając sobie”
   przyszłość; działa też na prawdziwych robotach), agenci „homeostatyczni” (nagrodą jest utrzymanie własnych
   zmiennych w normie; w małych symulacjach zachowanie rzeczywiście zaczyna zależeć od „głodu”) i architektury
   poznawcze (Spaun, Darwin VII, wspólna „przestrzeń robocza”). Każda łączy dwa–trzy składniki. **Żadna znaleziona
   praca nie łączy wszystkich czterech w jednym uczącym się systemie na poziomie choćby owada.**
4. **Co z tego dla FlyMind?** Uczciwie: FlyMind jest dziś **łukiem odruchowym bez stanu wewnętrznego** — tą częścią
   muchy, która *reaguje*, a nie tą, która *chce*. Sprawdziłem w kodzie: neuroprzekaźniki modulujące (dopamina,
   serotonina, oktopamina) nie mają w modelu żadnego działania. Biologia muchy podpowiada jeden konkretny, mały krok:
   **stan wewnętrzny, który nie steruje mięśniami, tylko zmienia czułość zmysłów** — dokładnie tak działa u muchy tor
   LC10a, którego już używamy. To jest propozycja na papierze, **nie na 1 grudnia** i wymaga Twojej decyzji, bo dotyka
   zasady z 3 XI.
5. **Gdzie są granice?** Biologia ma rzeczy, których w schemacie połączeń w ogóle nie widać (chemia „bez kabli”,
   komórki glejowe), ciało, które naprawdę może zginąć, uczenie się przez całe życie bez zapominania i znikomy koszt
   energii. Czy maszyna może mieć przeżycia — **nauka tego nie wie**; dwie główne teorie świadomości przegrały
   w 2025 r. część własnych testów. Nie wybieram strony.

**Jedna decyzja dla Ciebie:** czy chcesz, żebym przygotował (tylko na papierze) wstępną rejestrację kroku U1 z pkt 6 —
policzenia w danych MaleCNS, gdzie w używanych przez nas obwodach siedzą neurony modulujące. Nic poza tym nie
proponuję przed 1 XII.

---

## 1. Zakres, metoda, czego nie zrobiłem

- Źródła wybrałem sam, z prac, które znam, plus dwa wyszukiwania w sieci. **To nie jest przegląd systematyczny** —
  wybór jest mój i może być stronniczy (więcej w pkt 8).
- Każdą pracę z DOI sprawdziłem dziś w Europe PMC (tytuł, autorzy, rok, streszczenie); prace z arXiv — przez API arXiv;
  pięć prac nieobecnych w Europe PMC — w Crossref (dla trzech z nich jest tylko tytuł, bez streszczenia).
- Dwóch stron nie udało się otworzyć (logowanie / blokada przeglądarki): Man i Damasio 2019 na nature.com oraz LeCun
  2022 na openreview.net. Obie prace oznaczam odpowiednio niżej i **niczego z ich treści nie twierdzę jako
  sprawdzonego**.
- Nie uruchomiłem niczego z E1–E3, P1–P7, S1–S7. Zasada z 3 XI obowiązuje.

---

## 2. Pytanie 1 — co sprawia, że mózg jest całością, a nie zbiorem części?

### 2.1 Sześć mechanizmów jedności [LIT]

| # | Mechanizm | Dowód (co mówi streszczenie) | Rodzaj pracy | Status |
|---|---|---|---|---|
| J1 | **Jedno ciało, jeden cel.** Mózg nie czeka na błąd, tylko z wyprzedzeniem przewiduje potrzeby ciała i ustala priorytety między narządami i zachowaniami („allostaza”). Uczucia to przeżycia stanów ciała i część mechanizmu regulacji życia | Sterling 2012 (10.1016/j.physbeh.2011.06.004); Damasio i Carvalho 2013 (10.1038/nrn3403) | model teoretyczny; przegląd | VERIFIED (streszczenia). Sama teza: szeroko przyjęta rama, nie twierdzenie dowiedzione |
| J1a | Odczucia z wnętrza ciała mogą być w dużej mierze *przewidywaniami* mózgu o stanie ciała, korygowanymi sygnałem z narządów; emocje jako wnioskowanie o przyczynach tych sygnałów | Barrett i Simmons 2015 (10.1038/nrn3950); Seth 2013 (10.1016/j.tics.2013.09.007) | artykuł-opinia; teoria | VERIFIED, że tak piszą. Teza: **HYPOTHESIS** |
| J2 | **Stan wewnętrzny rozsyłany chemicznie.** Neuromodulatory przestrajają właściwości neuronów i siłę synaps; schemat połączeń daje „minimalną strukturę”, a dopiero środowisko chemiczne wyznacza, jaki obwód faktycznie działa | Marder 2012 (10.1016/j.neuron.2012.09.010); Bargmann i Marder 2013 (10.1038/nmeth.2451) | przeglądy | VERIFIED |
| J2a | U spragnionej myszy sygnał zapowiadający wodę rozlewa się po całym mózgu; po napojeniu — nie. Pobudzenie neuronów pragnienia w podwzgórzu przywraca stan „spragniony” w całym mózgu (ok. 24 000 neuronów, 34 obszary). Wniosek autorów: stan motywacyjny ustawia warunki początkowe, od których zależy, jak cały mózg zamieni bodziec na działanie | Allen i in., *Science* 2019 (10.1126/science.aav3932) | eksperyment | VERIFIED |
| J2b | Stany wewnętrzne (strach, głód, pobudzenie…) mają wspólne cechy: trwałość, stopniowalność, wpływ na wiele zachowań naraz; powstają z małych grup komórek, szerokich zmian aktywności i neuromodulacji. Autorzy: **nadal nie wiadomo, jak dokładnie układ nerwowy je wytwarza** | Flavell i in., *Neuron* 2022 (10.1016/j.neuron.2022.04.030) | przegląd | VERIFIED |
| J3 | **Ruch i zachowanie są wszędzie.** Neurony w niemal wszystkich badanych obszarach reagują na rozpoczęcie ruchu; aktywność kory wzrokowej jest „zlaniem” obrazu i wielowymiarowego stanu zachowania; aktywność całej kory zdominowana przez ruchy, także niezwiązane z zadaniem; 621 733 neurony w 279 obszarach — sygnał zbliżającego się ruchu „niemal wszędzie”, nagrody — „szeroko” | Steinmetz 2019 (10.1038/s41586-019-1787-x); Stringer 2019 (10.1126/science.aav7893); Musall 2019 (10.1038/s41593-019-0502-4); IBL 2025 (10.1038/s41586-025-09235-0) | eksperymenty (mysz) | VERIFIED |
| J4 | **Nie ma osobnych części „emocjonalnych” i „poznawczych”.** Zachowania poznawczo-emocjonalne opierają się na zmiennych koalicjach sieci; kluczowe są silnie połączone węzły. W ludzkim mózgu węzły te tworzą gęsto powiązany „klub” (12 obszarów, m.in. hipokamp, wzgórze, skorupa) | Pessoa 2008 (10.1038/nrn2317); van den Heuvel i Sporns 2011 (10.1523/JNEUROSCI.3539-11.2011) | artykuł-stanowisko; pomiar (21 osób, obrazowanie dyfuzyjne) | VERIFIED. Teza Pessoi: stanowisko, nie konsensus |
| J4a | Dwa układy modulujące (cholinergiczny i noradrenergiczny) mogą regulować, na ile sieć całego mózgu jest w danej chwili zintegrowana, a na ile podzielona | Shine 2019 (10.1016/j.tics.2019.04.002) | artykuł-opinia | VERIFIED, że tak pisze. Teza: **HYPOTHESIS** |
| J5 | **Pamięć i przewidywanie to jedna maszyneria.** Wyobrażanie przyszłości korzysta w dużej mierze z tych samych struktur co wspominanie; hipokamp jako „mapa przewidująca”; neurony dopaminowe sygnalizują błąd przewidywania nagrody; dwa uzupełniające się układy uczenia (szybki hipokamp, wolna kora, odtwarzanie wspomnień) | Schacter 2007 (10.1038/nrn2213); Stachenfeld 2017 (10.1038/nn.4650); Schultz 1997 (10.1126/science.275.5306.1593); McClelland 1995 (10.1037/0033-295X.102.3.419); Kumaran 2016 (10.1016/j.tics.2016.05.004) | przegląd; model; przegląd+teoria; teoria | VERIFIED |
| J5a | **Emocja decyduje, co zostaje w pamięci.** Ciało migdałowate, przez hormony stresu i noradrenalinę, wzmacnia utrwalanie wspomnień wielu rodzajów w innych częściach mózgu | McGaugh 2004 (10.1146/annurev.neuro.27.070203.144157) | przegląd | VERIFIED |
| J6 | **Jedno wąskie gardło wyboru.** Jądra podstawy jako centralny „przełącznik” rozstrzygający, który z konkurujących układów dostaje dostęp do mięśni; u stawonogów podobną rolę ma kompleks centralny (autorzy mówią o głębokiej homologii) | Redgrave 1999 (10.1016/S0306-4522(98)00319-4); Strausfeld i Hirth 2013 (10.1126/science.1231828) | propozycja teoretyczna; analiza porównawcza | VERIFIED, że tak piszą. Homologia: **REPORTED/sporna**, nie oceniałem |

Do tego zastrzeżenie o samym pytaniu: Cisek 2019 (10.3758/s13414-019-01760-1, VERIFIED streszczenie) dowodzi, że
kategorie takie jak „percepcja”, „poznanie”, „działanie” odziedziczyliśmy po psychologii i że lepiej opisywać mózg jako
stopniowo rozbudowywaną w ewolucji **pętlę sterowania kontaktem ze światem**. To stanowisko, nie konsensus — ale znaczy,
że pytanie „jak skleić moduły” może być źle postawione: w biologii one nigdy nie były osobne.

### 2.2 To samo u muchy i innych zwierząt [LIT]

| Co pokazano | Źródło | Status |
|---|---|---|
| Ciało grzybkowate działa jak **centrala przełączająca**: dopamina kieruje ten sam zapach do różnych obwodów wyjściowych zależnie od stanu i doświadczenia muchy; neurony dopaminowe tworzą sieć niosącą naraz kontekst zewnętrzny i stan wewnętrzny | Cohn, Morantte, Ruta, *Cell* 2015 (10.1016/j.cell.2015.11.019) | VERIFIED |
| **Głód bramkuje pamięć**: neuropeptyd F i sześć neuronów dopaminowych to „przełącznik motywacyjny” — syta mucha ma wspomnienie, ale go nie okazuje | Krashes i in., *Cell* 2009 (10.1016/j.cell.2009.08.035) | VERIFIED |
| **Głód zmienia sam zmysł**: głodzenie wzmacnia sygnał już na pierwszej synapsie węchowej (neuropeptyd sNPF + insulina) | Root i in., *Cell* 2011 (10.1016/j.cell.2011.02.008) | VERIFIED |
| Głodna mucha uparcie śledzi zapach jedzenia mimo braku nagrody; wytrwałość kontrolują neurony wyjściowe ciała grzybkowatego i dopamina, a hamuje neuron oktopaminowy | Sayin i in., *Neuron* 2019 (10.1016/j.neuron.2019.07.028) | VERIFIED |
| 8–10 neuronów P1 wywołuje **trwały stan wewnętrzny** (minuty) sprzyjający agresji i zalotom | Hoopfer i in., *eLife* 2015 (10.7554/eLife.11346) | VERIFIED |
| „Napęd godowy” samca spada z kolejnymi kopulacjami; niesie go dopamina do neuronów P1, gdzie **łączy się z informacją zmysłową o samicy tuż przed wyjściem ruchowym** | Zhang, Rogulja, Crickmore, *Neuron* 2016 (10.1016/j.neuron.2016.05.020) | VERIFIED |
| Stan zalotów zwiększa czułość neuronów wzrokowych LC10a (tor, którego używa FlyMind) | Hindmarsh Sten 2021 (10.1038/s41586-021-03714-w) | czytane 12 XI (raport W3, zasada B7); dziś nieotwierane |
| Powtarzany cień wywołuje u muchy stopniowalny, utrzymujący się stan obronny, który przerywa jedzenie — autorzy mówią o „pierwotnych składnikach emocji”, **nie** o ludzkich emocjach | Gibson i in., *Curr. Biol.* 2015 (10.1016/j.cub.2015.03.058); rama: Anderson i Adolphs 2014 (10.1016/j.cell.2014.03.003) | VERIFIED. Czy to „emocje” — **sporne**, sami autorzy to zaznaczają |
| Aktywność **większości** neuronów mózgu muchy koreluje z biegiem; mikroobwody „znają szerszy kontekst”. Sygnały chodu tworzą mapy także w obszarach pamięci i zmysłów | Schaffer 2023 (10.1038/s41467-023-41261-2); Brezovec 2024 (10.1016/j.cub.2023.12.063) | VERIFIED |
| „Kompas” muchy łączy wzrok z własnym ruchem, **utrzymuje kierunek w ciemności** (pamięć krótkotrwała) i przeucza się w ciągu minut w zmienionym otoczeniu | Seelig i Jayaraman 2015 (10.1038/nature14446); Fisher i in. 2019 (10.1038/s41586-019-1772-4) | VERIFIED |
| Sieć mózgu muchy ma „klub bogatych”: 30 % neuronów jest silnie połączonych; część może pełnić rolę integratorów lub rozgłaszaczy | Lin i in., *Nature* 2024 (10.1038/s41586-024-07968-y; dane FlyWire, nie MaleCNS) | VERIFIED |
| U nicienia przepływ sygnału **różni się od przewidywań z anatomii**; część różnicy to sygnalizacja pozasynaptyczna, niewidoczna w schemacie połączeń. Osobna, gęsta sieć neuropeptydowa „bez kabli” | Randi i in., *Nature* 2023 (10.1038/s41586-023-06683-4); Ripoll-Sánchez i in., *Neuron* 2023 (10.1016/j.neuron.2023.09.043) | VERIFIED |
| U larwy danio komórki glejowe (nie neurony) zliczają nieudane próby ruchu i wyłączają zachowanie | Mu i in., *Cell* 2019 (10.1016/j.cell.2019.05.050) | VERIFIED |

### 2.3 Co jest sporne albo nieznane — mówię wprost

- **Świadomość.** Nie ma zgody. Przegląd Setha i Bayne'a (2022, 10.1038/s41583-022-00587-4) wymienia cztery rodziny
  teorii i stwierdza, że nie jest jasne, czy da się je doświadczalnie rozróżnić. Test „przeciwników” z 2025 r.
  (Cogitate, *Nature*, 10.1038/s41586-025-08888-1; 256 osób) **podważył kluczowe założenia obu badanych teorii** —
  globalnej przestrzeni roboczej i zintegrowanej informacji. VERIFIED (streszczenia). Nie wybieram strony.
- **Problem wiązania** (jak z osobnych cech powstaje jeden przedmiot i jedno przeżycie). Feldman 2013
  (10.1007/s11571-012-9219-8): to co najmniej cztery różne problemy, często mylone. Hipoteza, że wiąże synchronizacja
  impulsów (Engel i Singer 2001, 10.1016/S1364-6613(00)01568-0 — VERIFIED streszczenie), ma znaną krytykę (Shadlen
  i Movshon 1999, 10.1016/S0896-6273(00)80822-3 — **REPORTED**: potwierdzony tylko tytuł, streszczenia brak).
  Nierozstrzygnięte.
- **„Jedna teoria mózgu”** (zasada wolnej energii, Friston 2010, 10.1038/nrn2787): autor sam stawia w tytule znak
  zapytania; to propozycja ujednolicenia, nie udowodniony fakt. Przetwarzanie predykcyjne w korze: rama, którą
  — według Kellera i Mrsic-Flogela (2018, 10.1016/j.neuron.2018.10.003) — dopiero trzeba próbować obalić. VERIFIED,
  że tak piszą; tezy: HYPOTHESIS.
- **Czy owady mają przeżycia.** Barron i Klein (2016, 10.1073/pnas.1520084113) twierdzą, że tak, w najprostszym
  sensie. To propozycja; nie znam rozstrzygającego testu. **Na plakacie nie wolno z tego robić faktu.**
- **Człowiek:** większość dowodów „z całego mózgu” (J2a, J3) pochodzi z myszy. Przeniesienie na człowieka: INFERRED.

### 2.4 Odpowiedź [INFERRED]

Mózg jest całością nie dlatego, że coś skleja części, tylko dlatego, że: wszystkie części **służą jednemu ciału**
(J1), **kąpią się w tym samym stanie chemicznym** (J2), **wiedzą, co ciało właśnie robi** (J3), **uczą się z tych
samych sygnałów błędu i wartości** (J5) i **muszą zmieścić się w jednym wyjściu** (J6). Emocja i motywacja nie są
osobnymi blokami — są *sposobem pracy całości* w danej chwili. To wniosek z zestawienia powyższych prac; żadna z nich
nie mówi tego jednym zdaniem.

---

## 3. Pytanie 2 — czy da się to odtworzyć w AI i jaka zasada by to umożliwiła?

### 3.1 Jak wygląda typowe AI na tle J1–J6 [INFERRED, na podstawie raportów 10–12 XI]

| Mechanizm | Typowy duży model (językowy, VLA) |
|---|---|
| J1 ciało i własny cel | brak: cel podaje człowiek w poleceniu; nic nie „zależy” od wyniku dla samego systemu |
| J2 stan wewnętrzny rozsyłany do wszystkiego | brak trwałego stanu; między wywołaniami nic nie zostaje poza zapisanym tekstem |
| J3 wiedza o własnym ruchu wszędzie | częściowo (stan robota jako jedno z wejść — raport W3) |
| J5 pamięć = przewidywanie; uczenie przez całe życie | uczenie raz, potem wagi zamrożone; pamięć dokładana z zewnątrz |
| J6 jedno wyjście | tak (to akurat mają) |

### 3.2 Zasady, które literatura proponuje [LIT]

| Zasada | Źródło | Co mówi | Status |
|---|---|---|---|
| **Nagroda = utrzymanie własnych zmiennych w normie.** Dowód matematyczny, że szukanie nagrody jest równoważne dążeniu do stabilności fizjologicznej; wyjaśnia też działanie z wyprzedzeniem | Keramati i Gutkin, *eLife* 2014 (10.7554/eLife.04811) | teoria normatywna | VERIFIED |
| **Model świata + „wyobraźnia”.** Agent uczy się modelu otoczenia i poprawia zachowanie, wyobrażając sobie przyszłe scenariusze | Ha i Schmidhuber 2018 (arXiv 1803.10122); Hafner i in., *Nature* 2025 (10.1038/s41586-025-08744-2) | działające systemy | VERIFIED |
| **Przewidywanie w przestrzeni pojęć, nie pikseli, plus moduł „kosztu wewnętrznego”** (LeCun 2022) | openreview.net — **strony nie udało się otworzyć** | propozycja architektury | **NOT VERIFIED dziś**; opis z mojej pamięci, do sprawdzenia przed użyciem |
| Częściowa realizacja tej linii: model uczony na ponad 1 mln godzin wideo, po doszkoleniu na < 62 h nagrań robota planuje ruchy ramienia Franka bez uczenia na miejscu | V-JEPA 2 (arXiv 2506.09985) | działający system | VERIFIED (streszczenie, ucięte w połowie zdania o wdrożeniu) |
| **Wspólna, wąska „przestrzeń robocza”**, o którą wyspecjalizowane moduły muszą konkurować | Goyal i in. 2021 (arXiv 2103.01197); VanRullen i Kanai 2021 (10.1016/j.tins.2021.04.005) | metoda; plan badań | VERIFIED |
| **Neuromodulatory jako „pokrętła” uczenia**: dopamina — błąd przewidywania nagrody, serotonina — horyzont czasu, noradrenalina — losowość wyboru, acetylocholina — szybkość zapisu pamięci | Doya 2002 (10.1016/S0893-6080(02)00044-8); Krichmar 2008 (10.1177/1059712308095775) | teoria; propozycja dla robotów | VERIFIED, że tak proponują. Przypisania: **HYPOTHESIS** |
| **Aktywne wnioskowanie** (jedna rama dla percepcji, działania i uczenia) w robotyce | Lanillos i in. 2021 (arXiv 2112.01871) | przegląd | VERIFIED |
| **Wspólny wzorzec architektury umysłu** (pamięć robocza, proceduralna, deklaratywna, percepcja, motoryka) | Laird, Lebiere, Rosenbloom 2017 (10.1609/aimag.v38i4.2744); wersja dla agentów językowych: Sumers i in. 2023 (arXiv 2309.02427) | propozycja konsensusu | VERIFIED. Streszczenia **nie wymieniają** emocji ani motywacji |
| „Maszyny czujące”: homeostaza + miękkie, podatne na uszkodzenie ciało | Man i Damasio, *Nat. Mach. Intell.* 2019 (10.1038/s42256-019-0103-7) | artykuł-perspektywa | **REPORTED**: potwierdzony tylko tytuł (Crossref); strony nie otworzyłem |

### 3.3 Odpowiedź [INFERRED / PROP]

**Funkcjonalnie i w małej skali — tak; to nie jest sprzeczne z niczym, co wiemy.** Każdy z mechanizmów J1–J6 ma
działający odpowiednik w maszynie. Zasada, która z nich wynika, to nie lista modułów, tylko cztery warunki naraz:

1. system ma **własne zmienne wewnętrzne**, których utrzymanie w normie jest jego jedynym źródłem nagrody (J1);
2. te zmienne są **rozsyłane do wszystkich części** i zmieniają ich czułość i szybkość uczenia, a nie tylko trafiają
   na wejście jako kolejna liczba (J2);
3. **jeden model świata** służy i pamięci, i przewidywaniu, i jest stale douczany (J5);
4. wszystko dzieje się w **zamkniętej pętli z ciałem**, a kopia własnych poleceń trafia z powrotem do zmysłów (J3, J6).

Czego ta odpowiedź **nie** mówi: że taki system byłby „jak człowiek” albo że coś by przeżywał. O tym nauka nie
rozstrzyga (pkt 2.3). I nie znam pracy, która spełnia wszystkie cztery warunki naraz w skali większej niż zabawkowa
symulacja (pkt 4).

---

## 4. Pytanie 3 — istniejące próby i co pokazały [LIT]

| Próba | Co łączy | Co pokazała (ze streszczenia) | Czego brak | Status |
|---|---|---|---|---|
| **Darwin VII** — prawdziwe urządzenie sterowane symulowanym „mózgiem” (Krichmar i Edelman 2002, 10.1093/cercor/12.8.818) | percepcja + warunkowanie (bodźce apetytywne i awersyjne) + ciało | rozpoznawanie przedmiotów zależne od doświadczenia, warunkowanie I i II rzędu; każdy egzemplarz wykształcił inne wagi | pamięć epizodyczna, potrzeby własne | VERIFIED |
| **Spaun** — 2,5 mln neuronów impulsowych, oko + ramię (Eliasmith i in., *Science* 2012, 10.1126/science.1225266) | percepcja + pamięć robocza + wybór działania + ruch | jeden model, osiem różnych zadań, wejście tylko obrazem, odpowiedź rysowana ramieniem | streszczenie nie wspomina o motywacji ani emocjach | VERIFIED |
| **DQN** (Mnih i in., *Nature* 2015, 10.1038/nature14236) | percepcja + uczenie nagrodą | uczenie się wprost z obrazu; streszczenie samo wskazuje na podobieństwo do sygnałów dopaminowych | nagroda z zewnątrz; odtwarzanie wspomnień jest w pracy, ale nie w części streszczenia, którą widziałem (PARTIALLY VERIFIED) | VERIFIED |
| **Ciekawość** jako nagroda wewnętrzna (Pathak i in. 2017, arXiv 1705.05363) | percepcja + przewidywanie + motywacja wewnętrzna | błąd przewidywania skutków własnych działań wystarcza, by agent eksplorował gry bez żadnej nagrody z zewnątrz | ciało, potrzeby | VERIFIED |
| **Dreamer V3 / DayDreamer** (10.1038/s41586-025-08744-2; arXiv 2206.14176) | percepcja + model świata (pamięć = przewidywanie) + uczenie | jedna konfiguracja na ponad 150 zadań; prawdziwy czworonóg uczy się wstawać i chodzić od zera w ok. godzinę, bez symulatora, i w 10 minut dostosowuje się do popychania | nagrodę nadal definiuje człowiek; brak stanu wewnętrznego | VERIFIED |
| **Agent ogólny Gato** (arXiv 2205.06175) | percepcja + język + ruch w jednej sieci | te same wagi grają, opisują obrazy i układają klocki ramieniem | brak motywacji i uczenia po wdrożeniu | VERIFIED |
| **Agenci „generatywni”** (Park i in. 2023, arXiv 2304.03442) | pamięć + refleksja + planowanie na modelu językowym | 25 agentów w piaskownicy zachowuje się „wiarygodnie”, pamięta i planuje | brak ciała; „motywacja” jest opisem tekstowym | VERIFIED |
| **Uczenie homeostatyczne w głębokich sieciach** (Yoshida i in., *Neural Netw.* 2024, 10.1016/j.neunet.2024.106379) | percepcja (także obraz) + zmienne wewnętrzne ciała + uczenie; nagroda = poprawa stanu wewnętrznego | wyuczeni agenci **zmieniają zachowanie zależnie od stanu wewnętrznego**; najlepiej działa nagroda liczona z różnicy „napędu” | dwa małe środowiska testowe; brak pamięci epizodycznej | VERIFIED |
| To samo dla wielu agentów (Yoshida i Man 2025, arXiv 2506.12894) | jw. + odczytywanie stanu partnera | zachowanie pomocne pojawia się **tylko** wtedy, gdy cierpienie partnera wpływa na własny stan agenta | trzy proste środowiska; preprint | VERIFIED |
| „Hormon stresu” w agencie aktywnego wnioskowania (Khan i Lowe 2024, arXiv 2406.08471) | fizjologia + przewidywanie | błąd przewidywania zamieniany na „kortyzol” regulujący fizjologię agenta w symulacji | wstępna praca; streszczenie ucięte przed wynikiem | PARTIALLY VERIFIED |
| Ramy i stanowiska: sztuczna interocepcja (Lee i in. 2023, arXiv 2309.05999; Candia-Rivera 2026, arXiv 2604.24527); ucieleśnienie i „śmiertelność” jako warunek uogólniania i troski (Christov-Moore i in. 2025, arXiv 2510.07117) | — | to **propozycje i przeglądy**, nie wyniki | — | VERIFIED, że tak proponują |
| Roboty z modelem emocji (Kismet — Breazeal 2003, 10.1016/S1071-5819(03)00018-1; przegląd: Moerland i in. 2018, 10.1007/s10994-017-5666-0) | emocje w robotach i w uczeniu nagrodą | — | — | **REPORTED**: potwierdzone tylko tytuły |
| Zbieżności „AI ↔ mózg”: kora przedczołowa jako układ uczący się uczyć (Wang i in. 2018, 10.1038/s41593-018-0147-8); rozkładowy kod wartości w neuronach dopaminowych myszy przewidziany przez AI (Dabney i in. 2020, 10.1038/s41586-019-1924-6); model hipokampa odtwarzający komórki siatkowe i miejsca (Whittington i in. 2020, 10.1016/j.cell.2020.10.024) | — | te same zasady obliczeń pojawiają się w obu światach | to teorie/modele poszczególnych części, nie całość | VERIFIED |
| Sieci z konektomu muchy sterujące ciałem (FlyGM; pokaz Eon Systems z marca 2026) | połączenia z danych + ciało | — | w dzisiejszym wyszukiwaniu **nie znalazłem** wśród nich modelu ze stanem wewnętrznym ani neuromodulacją | FlyGM: raport 12 XI; Eon: **REPORTED** (prasa, bez recenzji) |
| Test odniesienia: agent z widzeniem i zmiennymi „sytość, nawodnienie, temperatura” (NeurIPS 2025) | — | — | — | **NOT VERIFIED** (tylko wycinek z wyszukiwarki, bez tytułu) |

**Wniosek (INFERRED; „szukane i nieznalezione”):** nie znalazłem systemu, który w jednym uczącym się układzie łączy
percepcję, pamięć epizodyczną, stan podobny do emocji i motywację wynikającą z własnych potrzeb. Najbliżej jest
uczenie homeostatyczne z obrazem (Yoshida 2024) — ale to małe symulacje. Program „ucieleśnionego testu Turinga” (Zador
i in. 2023, 10.1038/s41467-023-37180-x, VERIFIED) nazywa to wprost celem na przyszłość, nie osiągnięciem. Brak
znaleziska nie dowodzi, że takiej pracy nie ma — szukałem krótko.

---

## 5. Pytanie 4 — co z tego da się zastosować w robotyce i w FlyMind?

### 5.1 Gdzie jest FlyMind na tle J1–J6 [FM]

| Fakt | Status |
|---|---|
| Neuroprzekaźniki modulujące nie mają w modelu działania: `DEFAULT_SIGN` obejmuje tylko acetylocholinę (+), GABA (−), glutaminian (−); komentarz w kodzie: „Neuromodulatory (DA, 5HT, OA, HA) nie mają tu znaku — neuron z takim przekaźnikiem wymaga jawnej decyzji” | VERIFIED dziś (`flymind/snn_interface.py`, wiersze 22–24; tylko odczyt) |
| Model nie ma plastyczności ani żadnej zmiennej trwającej dłużej niż adaptacja neuronu | PARTIALLY VERIFIED (raport 12 XI, pkt 2; dziś niesprawdzane ponownie) |
| Sieć używa najwyżej 1,2 % neuronów; obwód uczenia (ciało grzybkowate, 340 neuronów dopaminowych) jest w danych, nieużywany | VERIFIED 11 XI (raport 12 XI, pkt 2) |
| Pętla LC10a → skręt działa (38/40), ale przewagi nad sterownikiem klasycznym nie wykazano | VERIFIED 11 XI (jw.) |

**Wniosek (INFERRED):** z sześciu mechanizmów FlyMind ma dziś J6 (jedno wyjście) i kawałek J3 (zamknięta pętla
wzrok–ruch). Nie ma J1, J2 ani J5. Uczciwe zdanie na plakat: *„FlyMind odtwarza łuk odruchowy muchy — część, która
reaguje. Stanu wewnętrznego, uczenia i pamięci jeszcze nie ma.”*

### 5.2 Co da się zastosować w robotyce w ogóle [INFERRED z pkt 3–4]

- **Sprawdzone na prawdziwych robotach:** model świata z uczeniem na żywo (DayDreamer), planowanie w wyuczonej
  przestrzeni pojęć (V-JEPA 2). Wymagają uczenia i karty graficznej — to nie jest droga „mucha steruje”.
- **Sprawdzone tylko w symulacji:** nagroda homeostatyczna (Yoshida 2024).
- **Tanie i zgodne z biologią:** stan wewnętrzny, który *zmienia czułość zmysłów*, a nie steruje mięśniami — zasada B7
  z raportu W3 i dokładnie to, co pokazują Root 2011, Cohn 2015 i Zhang 2016.

### 5.3 Propozycje dla FlyMind [PROP] — **żadnej nie zaczynam; wszystkie NOT IMPLEMENTED**

| # | Co | Rodzaj | Zasada z 3 XI | Horyzont (opinia) |
|---|---|---|---|---|
| U1 | Policzyć w danych MaleCNS, które neurony o przekaźniku modulującym (dopamina, serotonina, oktopamina) leżą w obwodach, których już używamy (LC10a → DNa02; noga T2L), i z czym się łączą — czyli „którędy stan wewnętrzny *mógłby* wejść”. Najpierw wstępna rejestracja | tylko odczyt danych, bez symulacji | zgodne | 1–2 dni po zgodzie; wynik może być „nie ma ich tam” |
| U2 | Jedna powolna zmienna stanu wyliczana **wyłącznie z własnych zmysłów sieci** (np. nagromadzony sygnał szybko rosnącego obiektu → „czujność”), która skaluje czułość wejścia wzrokowego, a nie polecenia ruchu. Kontrola: ta sama zmienna podana przetasowanej sieci | zmiana modelu + symulacja | **sporne — decyzja Adama.** Skalowanie czułości wybranych neuronów „z ręki” jest bliskie sztucznej stymulacji; zgodne z zasadą byłoby dopiero wtedy, gdyby stan powstawał w neuronach z danych (np. P1, neurony dopaminowe) pobudzanych przez zmysły. To pokrywa się z kanałem K1 z raportu W3 | Explory 2027, nie 1 XII |
| U3 | „Potrzeby” prawdziwego ramienia jako zmysł wewnętrzny: temperatura i obciążenie serw | sprzęt | zgodne co do idei; **czy nasze serwa udostępniają te odczyty — NOT VERIFIED** | po teście na sprzęcie |
| U4 | Test jedności, który da się zmierzyć: *ten sam bodziec, inny stan wewnętrzny → inne zachowanie*, a po przetasowaniu połączeń efekt znika | protokół | zgodne | razem z U2 |
| U5 | Pamięć i przewidywanie: „kompas” muchy (kompleks centralny) | — | — | **nie proponuję teraz**: wg notatki z 27 X pierwszy protokół był nieważny, drugi nieuruchomiony (REPORTED z notatki, dziś niesprawdzane) |

**Na 1 grudnia nie proponuję niczego z tej listy poza ewentualnym U1 na papierze.** Wartość tego raportu na pokaz to
uczciwe zdanie z pkt 5.1 i gotowa odpowiedź na pytanie jury „czym to się różni od mózgu”.

---

## 6. Pytanie 5 — gdzie są granice?

| # | Co ma biologia | Dowód | Czy AI to odtworzy w najbliższych latach (moja opinia — **HYPOTHESIS**) |
|---|---|---|---|
| G1 | **Chemię poza połączeniami**: neuromodulatory i neuropeptydy działające „bez kabli”; schemat połączeń to „minimalna struktura”; u nicienia przepływ sygnału odbiega od przewidywań z anatomii | Marder 2012; Bargmann i Marder 2013; Randi 2023; Ripoll-Sánchez 2023 (VERIFIED) | Dla konektomu muchy **brak danych**, nie brak mocy obliczeniowej: mapa połączeń tego nie zawiera. To granica także dla FlyMind |
| G2 | **Komórki glejowe liczą** (zliczanie porażek u danio) | Mu 2019 (VERIFIED) | Nie ma ich w żadnym konektomie, którego używamy |
| G3 | **Ciało, które naprawdę może zginąć** — potrzeby nie są umową, tylko fizyką | Sterling 2012; Chiel i Beer 1997 (10.1016/S0166-2236(97)01149-1, VERIFIED): zachowanie wynika z gry układu nerwowego, ciała i otoczenia | Można zasymulować zmienne; czy „symulowana stawka” wystarcza — **sporne** (Christov-Moore 2025 twierdzi, że potrzebna prawdziwa podatność; to stanowisko) |
| G4 | **Uczenie przez całe życie bez zapominania** | Kirkpatrick i in. 2017 (10.1073/pnas.1611835114): pokazali częściowe rozwiązanie na prostych zadaniach; Hadsell i in. 2020 (10.1016/j.tics.2020.09.004): AI nadal opiera się głównie na stałych zbiorach danych (VERIFIED) | Postęp jest, problem otwarty |
| G5 | **Koszt energii**: sygnalizacja pochłania dużą część energii mózgu, co wymusza oszczędne kody (≤ 15 % neuronów aktywnych naraz) | Attwell i Laughlin 2001 (10.1097/00004647-200110000-00001, VERIFIED) | Liczb porównawczych „mózg vs GPU” dziś nie sprawdzałem — **NOT VERIFIED**, nie podaję |
| G6 | **Elastyczne wiązanie i składanie pojęć** | Greff i in. 2020 (arXiv 2012.05208, VERIFIED): autorzy uważają to za główną przyczynę słabszego uogólniania sieci | Otwarte; to teza autorów, nie pomiar |
| G7 | **Wyposażenie wrodzone z ewolucji i rozwoju** | Cisek 2019; Zador 2019 (raport 12 XI) | Konektom to jego zamrożony ślad — to akurat mocna strona FlyMind |
| G8 | **Przeżywanie** | Seth i Bayne 2022; Cogitate 2025; raport Butlina i in. 2023 (arXiv 2308.08708, VERIFIED): „żaden obecny system AI nie jest świadomy, ale nie widać oczywistych przeszkód technicznych” | **Nieznane.** Ocena Butlina zależy od przyjęcia teorii, które same są sporne. Nie wybieram strony |

**Podsumowanie (INFERRED):** najtwardsza granica dla FlyMind to G1 — mapa połączeń nie zawiera chemii, a to właśnie
chemia robi z obwodów organizm (J2). Każde dodanie stanu wewnętrznego do FlyMind będzie więc **założeniem modelu,
nie danymi**, i tak musi być podpisane.

---

## 7. Sprzeczności z zasadą z 3 XI — wprost

- U2 (zmienna stanu skalująca czułość zmysłów) może być odczytane jako sztuczne oddziaływanie na wybrane neurony.
  Nie rozstrzygam — to decyzja Adama, ta sama co przy kanale K1 w raporcie W3.
- Wszystkie „działające” próby z pkt 4 (Dreamer, V-JEPA 2, uczenie homeostatyczne) opierają się na **uczeniu wag**.
  Przeniesienie ich do FlyMind oznaczałoby, że zachowanie wyznacza uczenie, a nie połączenia muchy.
- Odpowiedź na pytanie 2 („tak, funkcjonalnie”) dotyczy AI w ogóle, nie sieci z konektomu.

---

## 8. Adwokat diabła i ograniczenia

1. **Czytałem tylko streszczenia.** Streszczenie mówi, co autorzy *twierdzą*, nie jak mocne są dane. Liczby w tabelach
   pochodzą ze streszczeń.
2. **Wybór źródeł jest mój** (z pamięci + dwa wyszukiwania). Mogłem pominąć prace przeczące obrazowi „wszystko jest
   wszędzie” — np. Steinmetz 2019 pokazuje też, że sygnały *bodźca i wyboru* są ograniczone do wybranych obszarów.
   Mózg jest więc jednocześnie wyspecjalizowany i zintegrowany; „jedność” w pkt 2.4 to uproszczenie.
3. **Sześć mechanizmów J1–J6 to moja synteza**, nie ustalona teoria. Inny autor ułożyłby to inaczej.
4. **Dowody z całego mózgu są głównie z myszy i muchy**, nie z człowieka; u człowieka to przede wszystkim
   obrazowanie, czyli korelacje.
5. **„Emocje” u muchy** — autorzy mówią o „pierwotnych składnikach”, nie o emocjach. Przenoszenie słów „chce”,
   „boi się” na FlyMind byłoby nadużyciem.
6. **Możliwe, że stan wewnętrzny niczego FlyMind nie da**: w zadaniu z jednym bodźcem i jednym ruchem nie ma między
   czym wybierać, więc J2 nie ma jak się ujawnić. Wtedy U2 byłoby ozdobą.
7. **Trzy źródła bez treści** (Man i Damasio, Breazeal, Moerland — tylko tytuły), jedno w ogóle nieotwarte (LeCun),
   jedno bez streszczenia (Shadlen i Movshon), jedno znane tylko z wycinka (test NeurIPS 2025).
8. Prognozy w pkt 6 („najbliższe lata”) to opinia, nie wynik.

---

## 9. Źródła i co z nich przeczytałem

**Pełne streszczenie pobrane dziś z Europe PMC (po DOI):**
Marder 2012 (10.1016/j.neuron.2012.09.010) · Bargmann i Marder 2013 (10.1038/nmeth.2451) · Pessoa 2008
(10.1038/nrn2317) · Sterling 2012 (10.1016/j.physbeh.2011.06.004) · Barrett i Simmons 2015 (10.1038/nrn3950) · Seth
2013 (10.1016/j.tics.2013.09.007) · Friston 2010 (10.1038/nrn2787) · Schultz, Dayan, Montague 1997
(10.1126/science.275.5306.1593) · Schacter 2007 (10.1038/nrn2213) · Stachenfeld 2017 (10.1038/nn.4650) · Steinmetz
2019 (10.1038/s41586-019-1787-x) · Stringer 2019 (10.1126/science.aav7893) · IBL 2025 (10.1038/s41586-025-09235-0) ·
Musall 2019 (10.1038/s41593-019-0502-4) · Allen 2019 (10.1126/science.aav3932) · Dehaene i Changeux 2011
(10.1016/j.neuron.2011.03.018) · Cogitate 2025 (10.1038/s41586-025-08888-1) · Feldman 2013 (10.1007/s11571-012-9219-8) ·
Seth i Bayne 2022 (10.1038/s41583-022-00587-4) · Cisek 2019 (10.3758/s13414-019-01760-1) · Flavell 2022
(10.1016/j.neuron.2022.04.030) · Cohn 2015 (10.1016/j.cell.2015.11.019) · Ripoll-Sánchez 2023
(10.1016/j.neuron.2023.09.043) · Randi 2023 (10.1038/s41586-023-06683-4) · Krashes 2009 (10.1016/j.cell.2009.08.035) ·
Sayin 2019 (10.1016/j.neuron.2019.07.028) · Root 2011 (10.1016/j.cell.2011.02.008) · Anderson i Adolphs 2014
(10.1016/j.cell.2014.03.003) · Gibson 2015 (10.1016/j.cub.2015.03.058) · Schaffer 2023 (10.1038/s41467-023-41261-2) ·
Brezovec 2024 (10.1016/j.cub.2023.12.063) · Lin 2024 (10.1038/s41586-024-07968-y) · Seelig i Jayaraman 2015
(10.1038/nature14446) · Fisher 2019 (10.1038/s41586-019-1772-4) · Strausfeld i Hirth 2013 (10.1126/science.1231828) ·
Barron i Klein 2016 (10.1073/pnas.1520084113) · Mu 2019 (10.1016/j.cell.2019.05.050) · Chiel i Beer 1997
(10.1016/S0166-2236(97)01149-1) · Attwell i Laughlin 2001 (10.1097/00004647-200110000-00001) · McClelland 1995
(10.1037/0033-295X.102.3.419) · Kumaran 2016 (10.1016/j.tics.2016.05.004) · McGaugh 2004
(10.1146/annurev.neuro.27.070203.144157) · Keller i Mrsic-Flogel 2018 (10.1016/j.neuron.2018.10.003) · Damasio
i Carvalho 2013 (10.1038/nrn3403) · van den Heuvel i Sporns 2011 (10.1523/JNEUROSCI.3539-11.2011) · Shine 2019
(10.1016/j.tics.2019.04.002) · Engel i Singer 2001 (10.1016/S1364-6613(00)01568-0) · Hoopfer 2015
(10.7554/eLife.11346) · Zhang 2016 (10.1016/j.neuron.2016.05.020) · Keramati i Gutkin 2014 (10.7554/eLife.04811) ·
Hafner 2025 (10.1038/s41586-025-08744-2) · Mnih 2015 (10.1038/nature14236) · Wang 2018 (10.1038/s41593-018-0147-8) ·
Eliasmith 2012 (10.1126/science.1225266) · Doya 2002 (10.1016/S0893-6080(02)00044-8) · Kirkpatrick 2017
(10.1073/pnas.1611835114) · Zador 2023 (10.1038/s41467-023-37180-x) · Dabney 2020 (10.1038/s41586-019-1924-6) · Yoshida
2024 (10.1016/j.neunet.2024.106379) · VanRullen i Kanai 2021 (10.1016/j.tins.2021.04.005) · Krichmar i Edelman 2002
(10.1093/cercor/12.8.818) · Hadsell 2020 (10.1016/j.tics.2020.09.004) · Redgrave 1999 (10.1016/S0306-4522(98)00319-4) ·
Whittington 2020 (10.1016/j.cell.2020.10.024).
Uwaga: streszczenia dłuższe niż ok. 1 300–1 700 znaków widziałem ucięte (dotyczy m.in. Sterlinga, Cogitate, Gibsona,
Fishera, McGaugha, Mniha, Yoshidy, Krichmara i Edelmana).

**Pobrane i przeczytane, w tekście niecytowane:** Sternson 2013 (10.1016/j.neuron.2013.02.018) · Oudeyer i Kaplan 2007
(10.3389/neuro.12.006.2007) · Hassabis i in. 2017 (10.1016/j.neuron.2017.06.011).

**Pełne streszczenie pobrane dziś z arXiv (po numerze; długie — ucięte ok. 1 300 znaków):**
2012.05208 (Greff) · 2103.01197 (Goyal) · 2308.08708 (Butlin) · 1705.05363 (Pathak) · 2301.04104 (DreamerV3) ·
2206.14176 (DayDreamer) · 2205.06175 (Gato) · 1803.10122 (Ha i Schmidhuber) · 2309.02427 (Sumers) · 2304.03442 (Park) ·
2112.01871 (Lanillos) · 2506.09985 (V-JEPA 2) · 2604.24527 (Candia-Rivera) · 2510.07117 (Christov-Moore) · 2309.05999
(Lee) · 2406.08471 (Khan i Lowe) · 2506.12894 (Yoshida i Man).

**Crossref (dziś):** ze streszczeniem — Krichmar 2008 (10.1177/1059712308095775), Laird i in. 2017
(10.1609/aimag.v38i4.2744). **Tylko tytuł, autorzy, rok** — Man i Damasio 2019 (10.1038/s42256-019-0103-7), Moerland
i in. 2018 (10.1007/s10994-017-5666-0), Breazeal 2003 (10.1016/S1071-5819(03)00018-1). Europe PMC, tylko tytuł (brak
streszczenia): Shadlen i Movshon 1999 (10.1016/S0896-6273(00)80822-3).

**Nie udało się otworzyć:** https://www.nature.com/articles/s42256-019-0103-7 (przekierowanie do logowania);
https://openreview.net/forum?id=BZ5a1r-kVsf (LeCun 2022 — strona weryfikacji przeglądarki; identyfikator podałem
z pamięci i **nie jest potwierdzony**).

**Tylko wycinek z wyszukiwarki (NOT VERIFIED):** test „przetrwania” z NeurIPS 2025; pokaz Eon Systems
(https://www.theregister.com/2026/03/16/digital_fruit_fly_brain_model/ — strony nie otwierałem).

**Z raportów 10–12 XI, dziś nieotwierane:** Hindmarsh Sten 2021, Zador 2019, FlyGM, wszystkie liczby FlyMind i MaleCNS.

**Szukane i nieznalezione:** jeden uczący się system łączący percepcję, pamięć epizodyczną, stan emocjonalny
i motywację z własnych potrzeb; model z konektomu muchy ze stanem wewnętrznym lub neuromodulacją.

---

## 10. Wcześniejsze raporty — sumy SHA-256 (dziś, `shasum -a 256`)

| Plik | SHA-256 | Uwaga |
|---|---|---|
| `bio_advantage_research_20261110.md` | `1b6e93ee463cc2f27284360b8d2fa5ed4c9599364dd38a48f06e9657995cb7d9` | zgodna z zapisaną 11 i 12 XI — niezmieniony (VERIFIED) |
| `fly_vs_vla_research_20261111.md` | `a1ebc4f6b927d9e5576b64fe9ebaa9cd45bbffccb2652dc099bc3fff39a25bc7` | zgodna z zapisaną 12 XI — niezmieniony (VERIFIED) |
| `fly_learning_research_20261112.md` | `54a81177a8c8e6ad75dfe7a870005606f6aa12d34b1fffeaade602478fef54db` | nie mam wcześniejszej sumy; w tej sesji pliku nie zapisywałem |
| `vla_with_fly_design_20261112.md` | `5331e7b560cb47f79699f07a54e86b404ee9cec31a3bddb2086cdf59dc12e982` | jw. |

---

## 11. Proponowane następne kroki — **żadnego nie zaczynam**

1. **U1** — wstępna rejestracja (na papierze) policzenia neuronów modulujących w używanych obwodach MaleCNS.
2. Dopisanie do plakatu uczciwego zdania z pkt 5.1 (decyzja Adama co do brzmienia).
3. **U2 + U4** — dopiero po decyzji, czy mieszczą się w zasadzie z 3 XI; horyzont Explory 2027.
4. Doczytanie pełnych tekstów dla trzech prac, na których najbardziej opieram odpowiedź (Allen 2019, Cohn 2015,
   Yoshida 2024), oraz potwierdzenie LeCuna 2022 i Mana i Damasio 2019 z innego źródła.

## 12. Decyzje dla Adama

1. Zgoda (lub nie) na krok 1 — sama rejestracja wstępna U1, bez uruchamiania.
2. Czy stan wewnętrzny zmieniający czułość zmysłów (U2) mieści się w zasadzie „mucha ma sterować” — to ta sama decyzja
   co kanał K1 z raportu W3; wystarczy rozstrzygnąć raz.
3. Czy zdanie z pkt 5.1 ma trafić na plakat.

E1–E3, P1–P7, S1–S7 pozostają niezatwierdzone i nietknięte.

**STOPPED AT CHECKPOINT 1 — awaiting Adam's approval.**
