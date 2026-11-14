# Najlepiej scharakteryzowane obwody neuronalne (okablowanie + funkcja) — katalog z perspektywy robotyki (stan: 2026-11-03)

**Uwagi metodologiczne dla autora raportu (ważne dla uczciwości):**
- Przeszukano sieć ~28 zapytaniami. Wyszukiwarka zwracała streszczenia/abstrakty, nie pełne teksty. Każde twierdzenie z linkiem pochodzi z wyniku wyszukiwania w tej sesji.
- Pozycje oznaczone **[PAMIĘĆ]** pochodzą z wiedzy własnej autora notatek i NIE zostały zweryfikowane w tej sesji (brak linku = brak weryfikacji). Nie traktować ich jako POTWIERDZONE bez sprawdzenia; podaję je tylko jako wskazówki do weryfikacji.
- Etykiety pewności: POTWIERDZONE / CZĘŚCIOWO POTWIERDZONE / HIPOTEZA / BRAK DANYCH / SPRZECZNE WYNIKI. Oznaczają pewność co do tego, co wynika z odnalezionych źródeł, nie z mojej wiedzy ogólnej.
- Zastosowania robotyczne są HIPOTEZAMI, chyba że napisano „zademonstrowano”.
- Nie znaleziono i nie zweryfikowano: pierwotnych prac Bidaye 2014 (Science, moonwalker), Bidaye 2020 (Neuron), Namiki 2018, Cande 2018, Hulse 2021, Aso 2014 w części DANs/MBON-funkcja (jest tylko anatomia), Hige, Mamiya 2018, haltery, Wehner (ant PI), Srinivasan (konkretny paper), Hoinville/Sun 2020, Lappalainen 2024, Vaxenburg 2025, Dorkenwald/Schlegel 2024 (FlyWire). Są to luki.

---

## 1. Ruch i wykrywanie ruchu wzrokowego (Drosophila: T4/T5)

### Takeaway
Pełny konektom wejść do T4 (ON) i T5 (OFF) w płacie wzrokowym jest zrekonstruowany z EM; podtypy a–d kodują cztery kierunki kardynalne. Obwód jest w pełni „zmapowany”, ale sam konektom nie rozstrzyga mechanizmu obliczeniowego (Hassenstein–Reichardt vs Barlow–Levick) — to wynika z dodatkowych danych fizjologicznych.

### Cited Findings
- Takemura i in. 2017 (eLife) zrekonstruowali wejścia synaptyczne T4 (FIB-SEM), wskazując kandydackie substraty anatomiczne zarówno dla detektora Hassensteina–Reichardta, jak i Barlowa–Levicka oraz nowe szlaki hamujące; recenzent zauważył, że Mi1 i Tm3 same nie tłumaczą selektywności kierunkowej T4 (potrzebne komórki z sąsiednich kolumn) — [Takemura 2017](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5435463/); [recenzje](https://elifesciences.org/articles/24394/peer-reviews).
- Shinomiya i in. 2019 (eLife) zmapowali wejścia do T4 i T5 w jednym zbiorze EM całego płata wzrokowego; T5 to pierwszy etap szlaku OFF-edge; podtypy a–d kodują cztery kierunki; oba szlaki używają strategii „opóźnij i porównaj” równolegle — [Shinomiya 2019](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6338461/).
- Etykieta: **POTWIERDZONE** (anatomia: EM; funkcja kierunkowa: z dodatkowych prac fizjologicznych [PAMIĘĆ: Maisak 2013, Nature; Borst] — niezweryfikowane tutaj). Mechanizm obliczeniowy: **CZĘŚCIOWO POTWIERDZONE / część SPRZECZNE** (recenzent kwestionuje wystarczalność Mi1+Tm3).

### Inferences
- Dla robotyki: gotowy, jednoznaczny wzorzec detektora ruchu lokalnego (kompaktowy, pasuje do kamer zdarzeniowych) — HIPOTEZA zastosowania; modele HR są stare w robotyce (Franceschini; patrz sekcja 9), ale związek z konkretnym obwodem T4/T5 nie został tu zademonstrowany.

### Gaps
- Brak weryfikacji tablic LPTC (HS/VS), optomotor — tylko [PAMIĘĆ]. Nie znaleziono w tej sesji pracy o HS/VS.

---

## 2. Orientacja przestrzenna / kierunek głowy / sterowanie celowe (Drosophila: kompleks centralny)

### Takeaway
Kompas E-PG (pierścień-attraktor), neurony FC2 (kąt celu) i PFL3/PFL2 (porównanie kierunku z celem → sygnał sterujący) to najlepiej scharakteryzowany obwód „nawigacji” u owada: konektom + obrazowanie + zaburzenia funkcji + behawior. Dalszy odcinek do neuronów zstępujących (DNa02) ma dane elektrofizjologiczne u chodzącej muchy, ale rola DNa01 jest niejasna.

### Cited Findings
- Seelig & Jayaraman 2015: populacja neuronów kompleksu centralnego śledzi kierunek (bump aktywności) — utrzymuje się po zniknięciu bodźca wzrokowego i przesuwa się względem wskazówki podczas chodzenia w ciemności — [PMC7419142](https://pmc.ncbi.nlm.nih.gov/articles/PMC7419142) (cytowane w wyniku wyszukiwania; sam paper nie otwarty).
- Turner-Evans 2017 (eLife): osobna populacja koduje kierunek i prędkość kątową; jej łączność z neuronami kompasu wyjaśnia aktualizację reprezentacji w ciemności — [PMC5440168](https://pmc.ncbi.nlm.nih.gov/articles/PMC5440168). Turner-Evans 2020 (eLife): „ultrastruktura i funkcja biologicznego attraktora pierścieniowego” — sieć zawiera kluczowe składniki attraktora pierścieniowego — [PMC8356802](https://pmc.ncbi.nlm.nih.gov/articles/PMC8356802).
- Dwa uzupełniające się prace Nature 2024 (626:808–818 i 626:819–826): Pires i in. (Maimon) — FC2 niosą kąt celu; EPG i FC2 łączą się monosynaptycznie z PFL3; pojedyncze komórki PFL3 mają sprzężone dostrajanie do kierunku i celu; wyciszenie podzbiorów PFL3 obniża zdolność orientacji w dowolnym kierunku celu — [PubMed 38326612](https://pubmed.ncbi.nlm.nih.gov/38326612/). Westeinde i in. (Wilson) — PFL3R, PFL3L i PFL2 łączą układ kierunku głowy z układem lokomotorycznym; każda populacja ma przesuniętą kopię reprezentacji kierunku i porównuje ją ze wspólnym wektorem celu; PFL2 zwiększa prędkość skrętu, gdy mucha jest daleko od celu — DOI 10.1038/s41586-024-07039-2, [opis zbiorczy](https://phys.org/news/2024-02-fruit-flies-brain-wheel.html).
- Rayshubskiy i in. (Wilson; eLife, wersja 2025): u chodzących much DNa02 przewiduje skręt o wysokim wzmocnieniu, DNa01 o niskim; DNa02 jest aktywowany wcześniej i bardziej przejściowo; DNa02 leży dwie synapsy za neuronami kierunku głowy; oba rekrutowane w sterowaniu opartym na pamięci; model „huśtawki” (pobudzenie jednej kopii DN + hamowanie kontralateralnej). Recenzenci: rola DNa02 istotna, ale rola DNa01 „niejasna” według fizjologii, optogenetyki i konektomu; utrata funkcji miała minimalny efekt — [eLife 102230 (recenzje)](https://elifesciences.org/reviewed-preprints/102230v2/reviews), [artykuł](https://elifesciences.org/articles/102230).
- Etykiety: kompas EPG i attraktor — **POTWIERDZONE** (obrazowanie Ca, EM). PFL3 → sygnał sterujący — **POTWIERDZONE** (obrazowanie + wyciszanie podzbiorów + konektom; zaburzenie tylko częściowe). DNa02 → skręt — **CZĘŚCIOWO POTWIERDZONE** (elektrofizjologia + korelacje; recenzenci zgłaszali ograniczenia). DNa01 — **SPRZECZNE WYNIKI / niejasne** wg recenzentów.

### Inferences
- Pełny łańcuch kompas → cel → PFL3 → DN → ruch jest jedną z najlepszych podstaw do kontrolera robota „sterowanego okablowaniem” (HIPOTEZA; nie zademonstrowano na robocie w znalezionych źródłach). Uwaga projektowa: wyjście PFL3 → DNa01 nie jest tym, co pokazują źródła; źródła wskazują PFL3 → … → DNa02 (dwie synapsy od neuronów kierunku głowy), a DNa01 ma niejasną rolę.

### Gaps
- Nie zweryfikowano Hulse 2021 (konektom CX) — brak wyniku. Nie zweryfikowano dokładnego szlaku PFL3 → DNa (bezpośredni vs pośredni) z pierwotnych prac. Nie znaleziono Mussells Pires w pełnym tekście.

---

## 3. Wzrokowe projekcje LC: pościg (LC10a → AOTU → DN) i łukowanie/ucieczka (LPLC2, LC4 → Giant Fiber)

### Takeaway
LC10a (pościg za samicą u samca) jest dobrze scharakteryzowany funkcjonalnie, ale połączenie „LC10a → AOTU → DNa02” NIE zostało przeze mnie potwierdzone w recenzowanej pracy; jedyny znaleziony wynik (preprint) wskazuje AOTU019/AOTU025 jako główne ogniwo do neuronów zstępujących sterujących. Looming → Giant Fiber (LPLC2: rozmiar; LC4: prędkość) jest solidnie potwierdzony.

### Cited Findings
- Hindmarsh Sten i in. (Dickson), Nature 2021: wzmocnienie (gain) neuronów LC10a jest selektywnie zwiększane w zalotach, co poprawia czułość na poruszające się cele; model sieci sugeruje, że sygnał wzrokowy przez obwód LC10a wzmocniony przez pobudzenie P1 niemal w pełni określa śledzenie samicy przez samca — [Nature s41586-021-03714-w](https://www.nature.com/articles/s41586-021-03714-w) (streszczenie z wyszukiwania).
- Preprint bioRxiv Collie i in. (2025, niecertyfikowany przez recenzję): AOTU019 i AOTU025 stanowią główne ogniwo łączące LC10a z neuronami zstępującymi sterującymi u obu płci; optogenetyczna aktywacja aIPg napędza pościg wzrokowy u samic — [bioRxiv](https://www.biorxiv.org/node/5005202). Wyszukiwanie NIE potwierdziło DNa02 w tym kontekście.
- Inne: aDN u samców dostają wejście wzrokowe przez LC10, u samic głównie węchowe; aDN kontrolują pościg wzrokowy u samców (źródło wtórne w wynikach wyszukiwania; patrz [Ribeiro lab](https://www.med.lmu.de/imp/en/research-groups/ribeiro-lab-neurogenetics-and-behavior/neural-circuits-and-computations-processing-of-visual-information/)).
- LPLC2: wysoce selektywny detektor „looming” przez radialną opozycję ruchu; populacja gęsto pokrywa pole widzenia i synapsuje na neurony Giant Fiber (GF), które sterują neuronem ruchowym skoku (Klapoetke i in. 2017, Nature 551:237–241). Ache i in. 2019 (Curr Biol 29:1073–1081): LPLC2→GF koduje rozmiar, LC4→GF prędkość narastania; oba synapsują bezpośrednio na GF (rekonstrukcja EM); wyciszenie LPLC2 usuwa składową rozmiaru; model sumujący reprodukuje dynamikę GF — [wyniki wyszukiwania](https://pmc.ncbi.nlm.nih.gov/articles/PMC7444277), [Drexel](https://researchdiscovery.drexel.edu/esploro/outputs/journalArticle/Neural-Basis-for-Looming-Size-and/991019168481004721). Preprint 2024: gradient synaptyczny LPLC2→GF wyjaśnia więcej skoków w trybie krótkim na wysokich wzniesieniach; LC4 nie tworzy takiego gradientu — [preprint](https://storage.prod.researchhub.com/uploads/papers/2025/11/14/2024.09.04.610846v3.full.pdf) (preprint).
- Etykiety: LC10a zysk i rola w pościgu — **POTWIERDZONE** (Nature 2021: obrazowanie, manipulacje + model). LC10a→AOTU→DN (konkretnie DNa02) — **CZĘŚCIOWO POTWIERDZONE / BRAK DANYCH dla DNa02** (tylko preprint, który DNa02 nie wspomina w streszczeniu). LPLC2/LC4 → GF — **POTWIERDZONE** (EM + wyciszanie + fizjologia).

### Inferences
- LPLC2/LC4 + GF to jasny wzorzec „detektor zbliżania → szybka ucieczka” (HIPOTEZA dla robota; podobna rola w robotyce zademonstrowana dla LGMD, nie dla LPLC2).

### Gaps
- Nie zweryfikowano Ribeiro 2018 (Cell) ani Cowley 2024 (Nature) w tej sesji. Szlak LC10a→DNa02 bezpośredni vs przez AOTU: BRAK wystarczających danych w znalezionych źródłach.

---

## 4. Uczenie i pamięć (Drosophila: ciało grzybkowe)

### Takeaway
Architektura ciała grzybkowego (KC → MBON, modulowana przez DAN w 15 kompartmentach) jest zmapowana w konektomie; anatomiczna logika uczenia asocjacyjnego jest udokumentowana. Nie znaleziono tu źródeł o zastosowaniu w robotyce RL dla Drosophila (są modele MB dla mrówek — sekcja 8).

### Cited Findings
- Aso i in. 2014 (eLife): ciało grzybkowe dzieli się na 15 kompartmentów zdefiniowanych przez zestaw typów komórek wyjściowych i dopaminergicznych — [eLife 04577](https://elifesciences.org/articles/04577).
- Konektom dorosłego MB (eLife 2020, e62576; autorzy nie zweryfikowani z wyników): dendryty MBON i zakończenia DAN przecinają wiązkę aksonów KC, tworząc 15 podobszarów — [PMC7909955](https://pmc.ncbi.nlm.nih.gov/articles/PMC7909955). Konektom płata α (eLife 2017): tylko 6% synaps KC>MBON dostaje bezpośrednią synapsę od DAN — [PMC5550281](https://pmc.ncbi.nlm.nih.gov/articles/PMC5550281) (wyniki wyszukiwania).
- Konektom larwy: [Eichler i in.](https://pmc.ncbi.nlm.nih.gov/articles/PMC7145459) (sieć wejściowa do DAN).
- Etykieta: struktura — **POTWIERDZONE**; funkcja uczenia (DAN uczą, MBON czytają) — **POTWIERDZONE** [PAMIĘĆ: Aso 2014 (2 prace), Hige 2015] — nie zweryfikowano w tej sesji.

### Inferences
- MB jako moduł uczenia „znajomości / wartości” jest kandydatem do wbudowania w robota (HIPOTEZA dla Drosophila; zademonstrowano dla modeli MB mrówek — patrz sekcja 8).

### Gaps
- Brak źródeł nt. Li 2020 jako autorstwa, Hige, ani zastosowań RL/robotycznych dla MB Drosophila.

---

## 5. Chodzenie, tył, lokomocja i obwody ruchowe nerwu (Drosophila: DN → VNC → MN)

### Takeaway
MANC (męski konektom nerwu) daje wgląd w to, jak sygnały zstępujące docierają do neuronów ruchowych nóg; bezpośrednie połączenia DN→MN są rzadkie, kontrola idzie przez sieci pośrednie. „Moonwalker” (MDN) jest uznawany za neuron komendy chodzenia wstecz, ale dane wskazują na rozproszone sterowanie.

### Cited Findings
- Cheong i in. 2024 (eLife, MANC): bezpośrednie połączenia DN–MN są rzadkie; zidentyfikowano „wspólnoty” neuronów wewnętrznych związane z różnymi systemami ruchowymi, w tym proponowane obwody brzuszne chodzenia; dopasowano homologiczne seryjnie neurony ruchowe nóg, co scharakteryzowało mięśnie docelowe dodatkowych 50% MN nóg; recenzent: ok. 50% MN nóg ma znacząco ograniczone dane łączności — [eLife 96084](https://elifesciences.org/articles/96084), [recenzje](https://elifesciences.org/reviewed-preprints/96084v1/reviews). Etykieta: **POTWIERDZONE** (anatomia, z zastrzeżeniem kompletności MN nóg). Funkcja behawioralna wynikająca z samej anatomii: **HIPOTEZA**.
- MDN: Feng i in. 2020 (Nat Commun) argumentują, że MDN działa jako neuron typu komendy przez rozproszone wyjścia przełączające stan dynamiki sieci ruchowej; dziesiątki celów MDN w obwodach nóg, w tym LBL40 (siła zadnich nóg); zmiana fazy ruchu nóg przy chodzeniu wstecz — [PMC7710706](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7710706/). Pobudzenie węchowe wywołuje chodzenie wstecz przez MDN; osobna para MooSEZ również może je wywołać — [Northumbria](https://researchportal.northumbria.ac.uk/en/publications/olfactory-stimuli-and-moonwalker-sez-neurons-can-drive-backward-l/). Etykieta: **CZĘŚCIOWO POTWIERDZONE** (optogenetyka + obrazowanie + anatomia; „komenda” kontestowana na rzecz modelu rozproszonego).
- Dopaminergiczne neurony „DopaMeander” napędzają chodzenie do przodu z większym skręcaniem (wynik wtórny wyszukiwania; autorzy nie zweryfikowani) — [NSF](https://par.nsf.gov/biblio/10627518).
- Model całego mózgu (Shiu i in., Nature 634:210–219, 2024, DOI 10.1038/s41586-024-07763-9): model LIF całego mózgu na bazie łączności i identyfikacji neuroprzekaźnika; aktywacja neuronów smakowych przewiduje neurony wymagane do inicjacji jedzenia; przewidywania o neuronach regionu żywienia napędzających neurony ruchowe zwalidowano optogenetyką i behawiorem; aktywacja mechanosensorów przewiduje obwód pielęgnacji czułków — [bohrium](https://bohrium.dp.tech/paper/arxiv/19279630), [IDEAS](https://ideas.repec.org/a/nat/nature/v634y2024i8032d10.1038_s41586-024-07763-9.html). Etykieta: **POTWIERDZONE** dla wybranych wskazań (jedzenie, pielęgnacja czułków); ogólna ważność modelu dla dowolnych zachowań — **CZĘŚCIOWO POTWIERDZONE**.
- Eon Systems (marzec 2026): deklarowana symulacja zachowań (chodzenie, pielęgnacja, żywienie) całego mózgu FlyWire sprzężonego z NeuroMechFly v2, według doniesień medialnych; The Register: sieć jest „spłaszczona” modelem ML z uproszczoną dynamiką; nie znaleziono recenzowanej pracy — [The Register](https://www.theregister.com/2026/03/16/digital_fruit_fly_brain_model/). Etykieta: **HIPOTEZA / BRAK DANYCH recenzowanych** (twierdzenia firmy i prasy).

### Inferences
- MANC + modele całego mózgu dają ścieżkę DN → premotoryka → MN dla kontrolera nóg robota, ale bez walidacji wzmocnionej na robocie (HIPOTEZA).

### Gaps
- Nie zweryfikowano Namiki 2018, Cande 2018, Bidaye 2014/2020, Takemura 2024 (MANC annotation). Brak weryfikacji Vaxenburg 2025 i Lappalainen 2024.

---

## 6. Dotyk, propriocepcja (Drosophila, C. elegans)

### Takeaway
Dla C. elegans pierwszy obwód dotyku został zidentyfikowany z EM + ablacji (Chalfie 1985), ale późniejsze prace pokazują redundancję i złożoność. Dla nogi Drosophila propriocepcja FeCO ma nową charakterystykę w konektomie FANC.

### Cited Findings
- C. elegans: Chalfie i in. 1985 — połączenie rekonstrukcji EM i ablacji laserowej określiło dwie ścieżki dotyku przedniego (AVD i AVB) i jedną tylną (PVC); komórki dotykowe synapsują także na komórki prawdopodobnie niezwiązane z ruchem — [PubMed 3981252](https://pubmed.ncbi.nlm.nih.gov/3981252/). AVA/AVD/AVE ważne dla inicjacji cofania, ale niezbędne nie są (robaki ich pozbawione nadal cofają się, rzadziej) — [WormAtlas](https://wormatlas.org/neurons/Individual%20Neurons/AVAmainframe.htm). Klasyczny model AVA(wstecz)/AVB(przód) z wzajemnym hamowaniem; nowsze wyniki grupy Zhen sugerują subtelniejszy mechanizm (tylko streszczenie prasowe) — [Sinai Health](https://www.sinaihealth.ca/?p=67189). Etykieta: dotyk — **POTWIERDZONE**; model AVA/AVB — **SPRZECZNE WYNIKI / CZĘŚCIOWO** (uproszczony model vs nowsze dane).
- Drosophila noga: Lee i in. (Tuthill, Agrawal; Nat Commun 2025, wcześniej bioRxiv 2024): podtypy neuronów FeCO zasilają osobne szlaki; neurony kodujące położenie/ruch łączą się z lokalnymi obwodami motorycznymi VNC (rola proprioceptywna), a neurony wibracji są integrowane przez nogi i przekazywane do regionów słuchowych mózgu; głównie FANC i FlyWire; w MANC FeCO rekonstrukcje są niekompletne — [PMC12048489](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12048489/). Etykieta: **POTWIERDZONE** (anatomia; funkcja z wnioskowania anatomicznego + wcześniejsze fizjologie [PAMIĘĆ]).

### Inferences
- Dotyk nogi i obwód wycofywania/uniesienia to temat własny projektu (zob. pamięć projektu: dotyk w danych, znak Glu-zależny) — nie rozstrzygam tu, tylko zaznaczam, że same wzorce konektomu nie wystarczają do przypisania znaku funkcji bez neuroprzekaźnika i fizjologii.

### Gaps
- Mamiya 2023 (Cell) znaleziono tylko jako cytowanie; Tuthill & Wilson 2016 nie zweryfikowane.

---

## 7. Pielęgnacja, żywienie (zachowania „manipulacyjne” Drosophila)

### Takeaway
Pielęgnacja to najlepiej scharakteryzowany obwód sekwencyjny z hierarchią supresji; żywienie i pielęgnację czułków przewidział model Shiu 2024 i zwalidowano eksperymentalnie.

### Cited Findings
- Seeds i in. 2014 (eLife): programy czyszczenia tworzą hierarchię supresji: oczy > czułki > odwłok > skrzydła > grzbiet — [eLife 02951](https://elifesciences.org/articles/02951/peer-reviews). Etykieta: **POTWIERDZONE** (genetyczne targetowanie podzbiorów + behawior).
- Hampel i in. 2015 (eLife 08758): neurony mechanosensoryczne strunowe wzbudzają trzy klasy połączonych interneuronów (dwie w mózgu + równoległe neurony zstępujące); warstwy wystarczają do wywołania pielęgnacji czułków i różnią się czasem jej trwania — [PMC4599031](https://pmc.ncbi.nlm.nih.gov/articles/PMC4599031). Hampel 2017 — sekwencja pielęgnacji zależna od lokalizacji pyłu — [wyniki](https://elifesciences.org/articles/87602/figures) (somatotopia, Eichler/Hampel eLife 2024: każdy obwód tłumi wszystkie podrzędne). Etykieta: **POTWIERDZONE**.
- Shiu 2024 (j.w., sekcja 5): przewiduje obwody żywienia i pielęgnacji czułków.

### Inferences
- Hierarchia supresji = gotowy „arbiter” zachowań (HIPOTEZA zastosowania). Do rzeczywistej manipulacji obiektami (chwytanie) NIE znaleziono w tej sesji odpowiednika obwodu u Drosophila → **BRAK DANYCH** dla „fly leg reaching” do celu.

### Gaps
- Brak źródeł o „sięganiu” nogą muchy; brak weryfikacji obwodu proboscis poza Shiu 2024.

---

## 8. Nawigacja, całkowanie ścieżki, nawigacja wzrokowa (pszczoła, mrówka) — z zastosowaniami robotycznymi

### Takeaway
Całkowanie ścieżki jest modelowane anatomicznie dla kompleksu centralnego (pszczoła), a uczenie tras wzrokowych przez ciało grzybkowe działa na robotach terenowych; to najlepiej wykazane przeniesienie obwód→robot.

### Cited Findings
- Stone i in. 2017 (Curr Biol 27(20):3069–3085): anatomicznie ograniczony model całkowania ścieżki w mózgu pszczoły w kompleksie centralnym z zidentyfikowanymi typami neuronów; ogólny mechanizm porównywania kierunku bieżącego i pożądanego. Wyszukiwanie nie potwierdziło, czy praca zawierała eksperyment na robocie — [PMC5388780](https://pmc.ncbi.nlm.nih.gov/articles/PMC5388780) (tytuł/streszczenie z wyników). Etykieta: **HIPOTEZA obliczeniowa** (model, nie potwierdzenie in vivo całej kaskady); komponenty kompasu — **POTWIERDZONE** u Drosophila (sekcja 2).
- Mrówki: modele ciała grzybkowego jako detektora znajomości; Jesusanmi i in. 2024 (Front Physiol): sieć spajkowa MB, 400 scen na 27 m trasie, online na robocie; błąd średni 0,144 m na trasie 6,5 m, porównywalny ze standardowymi algorytmami wizyjnymi — [Front Physiol](https://www.frontiersin.org/articles/10.3389/fphys.2024.1379977/full). Science Robotics (Zhu i in.): kamera zdarzeniowa na robocie lądowym w terenie (trawa, las, pola), ocena znajomości w czasie rzeczywistym, większa odporność niż SeqSLAM — [whiterose](https://eprints.whiterose.ac.uk/222341/1/Sci_robotics_revision.pdf). Etykieta: robotyczne wykonanie — **ZADEMONSTROWANE**; biologiczna prawdziwość modelu MB jako „detektora znajomości” — **CZĘŚCIOWO POTWIERDZONE** [PAMIĘĆ: dane behawioralne Wehner/Collett/Graham — niezweryfikowane tutaj].
- Pszczoła, optic flow: reliance na przepływ optyczny wynika z ograniczonej rozdzielczości, małej mocy neuronalnej i braku stereo; roboty używają go do odometrii wizualnej, nawigacji po punktach orientacyjnych i lądowania — [arXiv 2507.11992](https://arxiv.org/html/2507.11992v3). Zufferey & Floreano (EPFL): ultralekkie samoloty z kamerami do unikania przeszkód i kontroli wysokości głównie na przepływie optycznym — [EPFL](https://infoscience.epfl.ch/record/265975/files/EPFL_TH9316.pdf?version=1) (wyniki szczegółowe nie zweryfikowane).

### Inferences
- Najlepiej udowodnione: nawigacja wzrokowa przez MB-familiarity i przepływ optyczny w dronach. Całkowanie ścieżki CX na fizycznym robocie — nie znaleziono wykazanej demonstracji w tej sesji (**BRAK DANYCH**).

### Gaps
- Brak weryfikacji konkretnych prac Wehnera, Srinivasana (odometria), Hoinville/Sun 2020; brak prac nt. CX w mrówce.

---

## 9. Unikanie kolizji / zagrożenie (szarańcza LGMD/DCMD) — zastosowania robotyczne

### Takeaway
Modele LGMD są najczęściej wdrażanym w robotach „obwodem” z owadów; przegląd 2025 opisuje je w robotach lądowych i latających, ale problemem pozostaje nieznany rozmiar/prędkość obiektu.

### Cited Findings
- Przegląd Qin, Peng, Yue, Fu (arXiv 2501.02982, 2025): modele LGMD jako wizja wbudowana na mikro-robotach i małych quadkopterach do wykrywania/unikania kolizji; Khepera i Colias w złożonych środowiskach — [arXiv](https://arxiv.org/abs/2501.02982v2). Fu, Hu, Yue 2018: sieć LGMD2 testowana na miniaturowym robocie w arenie z wieloma przeszkodami (bliski zasięg) — [arXiv 1801.06452](https://arxiv.org/pdf/1801.06452.pdf). Wu, Yue, Hu (Front Neurorobot 2024): przegląd i standardowy prototyp — [DOAJ](https://doaj.org/article/e21747b9d9a84ba9ab94f0fb5eec2584).
- Etykieta: robotyczne wykonanie — **ZADEMONSTROWANE** (z zastrzeżeniem: wyniki ilościowe nie sprawdzone). Biologiczne wiring+function LGMD: **POTWIERDZONE** [PAMIĘĆ: Rind, Gabbiani — niezweryfikowane tutaj].

### Inferences
- LGMD to „detektor lokalny”, nie pełny obwód ruchowy; do sterowania wymaga osobnej warstwy decyzyjnej (HIPOTEZA).

### Gaps
- Brak źródeł pierwotnych o biologii LGMD (Rind, Gabbiani, Fotowat) pobranych w tej sesji.

---

## 10. Ucieczka i polowanie u kręgowców (danio, mantis)

### Takeaway
Obwód Mauthnera (ucieczka C-start) jest klasycznym, dobrze scharakteryzowanym szlakiem; polowanie larw danio ma zidentyfikowane komponenty (AF7, pretectum, tectum), ale „komendy” pretectalne działają probabilistycznie. Mantis: stereopsja z neuronów dostrojonych do dysparycji, bez znalezionej realizacji robotycznej.

### Cited Findings
- Mauthner: Hale i in. 2016 (J Neurogenet 30(2):89–100) przegląd obwodu startle ryb z komórkami Mauthnera i neuronami włókien spiralnych — [PubMed 27302612](https://pubmed.ncbi.nlm.nih.gov/27302612); Medan & Preuss 2014 — modulacja plastyczności obwodu (temperatura, status społeczny, serotonina, dopamina) — [rekord](https://cosechador.siu.edu.ar/bdu/Record/todo:paper_09284257_v108_n2-3_p129_Medan); w danio tectum optyczne przetwarza bodźce looming — [PMC4742414](https://pmc.ncbi.nlm.nih.gov/articles/PMC4742414). Etykieta: **POTWIERDZONE** (elektrofizjologia, ablacje klasyczne; szczegóły w przeglądach).
- Polowanie danio: Antinucci i in. 2019 (eLife 48114): aktywacja optogenetyczna komórek pretectalnych wywołuje polowanie bez ofiary, stymulacja pojedynczej komórki wystarcza, ablacja laserowa redukuje polowanie na żywą zdobycz — „układ komend”; recenzent: ok. 18% prób, długie opóźnienia ~4 s — [eLife 48114](https://elifesciences.org/articles/48114), [recenzje](https://elifesciences.org/articles/48114/peer-reviews). AF7 w pretectum: ablacja istotnie redukuje chwytanie zdobyczy; Bianco: neurony tectum wysoce selektywne dla ofiary o nieliniowej selektywności mieszanej; przegląd 2023 wskazuje AF10 i AF7 jako najważniejsze obszary — [PMC9928868](https://pmc.ncbi.nlm.nih.gov/articles/PMC9928868). Etykieta: **CZĘŚCIOWO POTWIERDZONE** (optogenetyka, ablacja; ograniczona niezawodność).
- Mantis: Rosner i in. 2019 (Nat Commun 10): co najmniej cztery klasy neuronów dostrojonych do dysparycji binokularnej — pierwsze w bezkręgowcach z właściwościami do stereoskopii; neuron TAOpro prawdopodobnie napędza uderzenie, silna odpowiedź dla dysparycji odpowiadającej zasięgowi chwytania; model obliczeniowy (O'Keeffe 2022 PLOS CB): pojedynczy „czujnik dysparycji” — [PMC6599392](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6599392/), [PMC9159633](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9159633/). Etykieta: neurony — **POTWIERDZONE** (elektrofizjologia); „TAOpro napędza uderzenie” — **HIPOTEZA** (autorzy „sugerują”). Robotyka: **BRAK DANYCH** (nie znaleziono realizacji).

### Inferences
- Danio i mantis dostarczają wzorców „wykryj cel → wyzwól akcję”, ale bez konektomu na poziomie pojedynczych neuronów w znalezionych źródłach.

### Gaps
- Brak weryfikacji optomotor/optokinetycznych szlaków danio, konektomu danio (nowe prace 2025–26 nie szukane).

---

## 11. Kontekst: ssaki (CPG rdzenia, adaptacja móżdżku)

### Takeaway
Nie badano w tej sesji (tylko kontekst żądany jako krótki). **BRAK DANYCH** z weryfikowalnymi źródłami; pominąć lub uzupełnić osobnym badaniem.

---

## Podsumowanie rankingu pewności (tylko na podstawie znalezionych źródeł)
1. Najmocniej: T4/T5 (anatomia), kompas EPG/CX, PFL3 → sterowanie, LPLC2/LC4→GF, hierarchia pielęgnacji, Mauthner, dotyk C. elegans (1985).
2. Częściowo: LC10a→DN (preprint), DNa02/DNa01, MDN jako komenda, pretectalne neurony polowania, TAOpro.
3. Wykazane w robotach: LGMD (Khepera, Colias, quadkopter), model MB mrówki (robot lądowy, trasa 27 m), przepływ optyczny (Zufferey & Floreano).
4. Medialne, niezweryfikowane recenzją: Eon Systems embodied fly (marzec 2026) — wymaga recenzowanej pracy.
5. Luki do uzupełnienia przez kolejnego badacza: Hulse 2021; Namiki 2018; Cande 2018; Bidaye 2014/2020; Takemura 2024; FlyWire (Dorkenwald/Schlegel 2024); Lappalainen 2024; Vaxenburg 2025; haltery; szarańcza LGMD biologia; Wehner/Srinivasan; zebrafish connectome; ssaki.
