# Konektom -> model, modyfikacje konektomów i łączenie obwodów (w tym między gatunkami) - stan na listopad 2026

Uwaga metodologiczna: opisy poniżej pochodzą z abstraktów / streszczeń wyszukiwarki; pełnych tekstów w większości NIE czytano. Etykiety: POTWIERDZONE / CZĘŚCIOWO POTWIERDZONE / HIPOTEZA / BRAK DANYCH / SPRZECZNE WYNIKI. Brak recenzji ≠ błąd, ale oznaczam preprinty.

## 1. Konektom -> model: metody i ile samo okablowanie przewiduje

### Takeaway
Konektom jest warunkiem koniecznym, ale nie wystarczającym: najlepsze modele (Shiu 2024, Lappalainen 2024) dodają przewidywane transmitery lub dopasowują nieznane parametry do danych funkcjonalnych, a teoria (Beiran & Litwin-Kumar) i klasyka (Bargmann & Marder, Prinz) pokazują, że samo okablowanie nie wyznacza dynamiki. Przewagi "biologicznej topologii" w uczeniu są kwestionowane przez kontrole null (Dhiman 2026, preprint), ale wyniki są mieszane (FlyGM raportuje przewagę nad rewired).

### Cited Findings
- Shiu i in., Nature 634:210-219 (2024), DOI 10.1038/s41586-024-07763-9: model LIF całego mózgu muszki z synaps + przewidywanych neuroprzekaźników; aktywacja neuronów smaku/mechanoreceptorów przewiduje neurony wymagane do inicjacji karmienia i obwód groomingu; predykcje testowano optogenetyką i behawioralnie (POTWIERDZONE dla ograniczonego zestawu obwodów karmienie/grooming, nie dla całego repertuaru zachowań) — [abstrakt/streszczenie](https://collaborate.princeton.edu/en/publications/a-drosophila-computational-brain-model-reveals-sensorimotor-proce/)
- Doniesienie blogowe o zamkniętej pętli chodzenia/unikania przeszkód w modelu Shiu NIE zostało zweryfikowane w abstrakcie (BRAK DANYCH) — [blog](https://lilting.ch/en/articles/drosophila-whole-brain-connectome-flywire)
- Lappalainen i in., Nature 634:1132-1140 (2024), DOI 10.1038/s41586-024-07939-3: sieć z zmierzonym okablowaniem 64 typów komórek ścieżek ruchu w płacie wzrokowym, nieznane parametry neuronów/synaps dostrojone deep learningiem do zadania detekcji ruchu; przewidywania zgodne z pomiarami z 26 prac; sparse connectivity pomaga (POTWIERDZONE; uwaga: parametry są dopasowane, nie wynikają z samego konektomu) — [streszczenie](https://is.mpg.de/publications/lappalainennature24)
- Beiran & Litwin-Kumar (bioRxiv 2024, opublikowane 2025): konektom często NIE wystarcza do ograniczenia dynamiki sieci wykonującej zadanie (degeneracja); rejestracja małego podzbioru neuronów usuwa degenerację; wymagana liczba zależy od wymiarowości dynamiki, nie rozmiaru sieci; zastosowano do larwy Drosophila (motor-premotor) i układu kierunku głowy dorosłej muszki (POTWIERDZONE jako wynik teoretyczno-symulacyjny, "teacher-student", nie na danych in vivo) — [streszczenie](https://www.aminer.org/pub/65deb1de13fb2c6cf65ea341/prediction-of-neural-activity-in-connectome-constrained-recurrent-networks); [kod](https://zenodo.org/records/16618353)
- Kakaria & de Bivort, Front. Behav. Neurosci. 2017, DOI 10.3389/fnbeh.2017.00008: dynamika ring-attractor wyłania się w spikującym modelu protocerebral bridge w szerokim zakresie parametrów; model NIE był zbudowany z pełnego konektomu EM, lecz z zasad obwodowych — [artykuł](https://pmc.ncbi.nlm.nih.gov/articles/PMC5306390). Późniejsza praca EM (Turner-Evans i in. 2020) potwierdza główne elementy ring attractora, ale ujawnia cechy strukturalne nieprzewidziane przez teorię (CZĘŚCIOWO POTWIERDZONE) — [PubMed 32916090](https://pubmed.ncbi.nlm.nih.gov/32916090/)
- BAAIWorm (Nature Computational Science 2024): wieloprzedziałowy, biofizyczny model mózgu C. elegans sprzężony z modelem ciała (3341 tetrahedronów, 96 mięśni) i środowiska; pętla zamknięta odtwarza zygzakowaty ruch chemotaksji. Ograniczenia: dalej tylko chemotaksja, rozszerzenie do pełnych 300 neuronów potrzebne (CZĘŚCIOWO POTWIERDZONE; z wtórnych źródeł) — [State of Brain Emulation 2025](https://arxiv.org/pdf/2510.15745); [repo/opis](https://hyper.ai/en/stories/2f3136b4d2b779f41646870c64df8321)
- FlyGM (Jin, Zhu, Zhang, Sui; arXiv 2602.17997, v1 20.02.2026, v3 14.06.2026): konektom dorosłej muszki (139 246 neuronów) jako skierowany graf przekazywania komunikatów / GNN-kontroler ciała MuJoCo; wg streszczenia lepszy niż graf zrandomizowany z zachowaniem stopni, Erdős-Rényi i MLP; chód, skręt, lot. To kontroler UCZONY RL (wagi trenowane), nie symulacja dynamiki biologicznej (preprint, nie recenzowany wg dostępnych danych) — [arXiv](https://arxiv.org/abs/2602.17997)
- Dhiman, arXiv 2604.04033 (5.04.2026), "Topological Sensitivity in Connectome-Constrained Neural Networks": przy słabych kontrolach (obie sieci inicjalizowane z checkpointu konektomu; null dopasowany tylko do globalnych zliczeń) konektom wygląda lepiej (loss, aktywność, runtime); przy wspólnej losowej inicjalizacji przewaga w early-loss znika, a null z zachowaniem stopni usuwa pozorną przewagę aktywności; "largely disappear". Ograniczenia: jedna sieć (flyvis), 5 próbek nulla, jeden autor, preprint v1 (CZĘŚCIOWO POTWIERDZONE; SPRZECZNE z FlyGM co do tego, czy topologia daje przewagę w uczeniu — różne zadania i architektury, więc nie jest to bezpośrednia replikacja) — [arXiv](https://arxiv.org/abs/2604.04033)
- Therianos, arXiv 2606.17745 (16.06.2026, v2 2.07.2026): zamrożony operator ratowy z pełnego konektomu larwy (rdzeń 2825 neuronów, bez dopasowania parametrów); zgrubna odpowiedź (gain, wymiarowość) mieści się w kilku % w stosunku do ensemble dopasowanego co do stopni i wag, natomiast routing wejść i mody ciała grzybkowatego zależą od dokładnego okablowania. Wniosek: "co zależy od dokładnego okablowania" zależy od wielkości mierzonej (preprint) — [arXiv](https://arxiv.org/abs/2606.17745)
- Schmidgall, Schuman, Parsa, arXiv 2209.14406 (2022): obwód motoryczny C. elegans jako architektura ANN; silny bias indukcyjny do zadań lokomocyjnych, ale może szkodzić w zadaniach niepowiązanych (np. klasyfikacja obrazów); nawet po odrzuceniu dokładnego okablowania statystyki architektoniczne bywają użytecznym priorem — [arXiv](https://arxiv.org/abs/2209.14406)
- Suárez i in., Nat. Commun. 2024, conn2res: konektomy jako rezerwuary; wcześniejsza praca (Nat. Mach. Intell. 2021) – realistyczne architektury działają najlepiej w reżimie krytycznym; zależność od topologii. Bezpośredniego porównania "biologia vs rewired null" nie potwierdzono w wynikach wyszukiwania (BRAK DANYCH w tej notatce) — [Nat. Commun.](https://www.nature.com/articles/s41467-024-44900-4.pdf); [NMI 2021](https://www.nature.com/articles/s42256-021-00376-1)
- Bargmann & Marder, Nature Methods 10:483-490 (2013), DOI 10.1038/nmeth.2451: perspektywa historyczna o informacji potrzebnej poza diagramem połączeń (bezpośrednie tezy z pełnego tekstu nie zostały tu zweryfikowane) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/23866325/)
- Prinz, Bucher, Marder, Nature Neurosci. 7:1345-1352 (2004), DOI 10.1038/nn1352: >20 mln wariantów 3-komórkowego modelu pylorycznego STG; wiele zupełnie różnych zestawów parametrów daje niemal tę samą aktywność (degeneracja) (POTWIERDZONE) — [rekord](https://researchwith.njit.edu/en/publications/similar-network-activity-from-disparate-circuit-parameters/)
- Neuromodulacja przekonfiguruje funkcjonalnie anatomicznie stały obwód STG (monoaminy, peptydy zmieniają synapsy i przewodnictwa; neurony przełączają się między rytmami) (POTWIERDZONE w STG; transfer do much niezbadany) — [przegląd Marder/Gruber](https://gruber.yale.edu/press/2013-gruber-neuroscience-prize-press-release); [Marder 2012 PMC3482119](https://pmc.ncbi.nlm.nih.gov/articles/PMC3482119)
- Currier (seminarium, Stanford): proste predykcje oparte na konektomie w układzie wzrokowym muszki mają zaskakująco ograniczoną moc, możliwe mechanizmy pozasynaptyczne; silne połączenia mają nadmierny wpływ względem prostego sumowania ważonego (abstrakt seminarium, nie recenzowana praca) — [Stanford events](https://events.stanford.edu/event/tim-currier-testing-the-power-and-limitations-of-connectome-based-functional-predictions-in-the-fruit-fly-visual-system)
- Litwin-Kumar & Turaga 2019 (Curr. Opin. Neurobiol.): nawet "kompletny" konektom zostawia wiele nieznanych parametrów; gap junctions trudne do identyfikacji — [przegląd](https://dalhousie-university2.demo.elsevierpure.com/en/publications/a-connectome-is-not-enough-what-is-still-needed-to-understand-the)
- Przegląd 2026 (arXiv 2604.23903): modele z ograniczeniem konektomem ustalają łączność i optymalizują resztę (wagi, dynamikę neuronów, wzmocnienia neuromodulacyjne); konektom sam często nie wystarcza — [arXiv](https://arxiv.org/pdf/2604.23903) (tylko z opisu wyszukiwarki)

### Inferences
- Dla FlyMind: "konektom decyduje" jest najmocniej uzasadnione w sensie "konektom + przewidywany znak + zewnętrznie dopasowane parametry"; stwierdzenie "samo okablowanie przewiduje zachowanie" nie ma poparcia (Beiran, Prinz, Currier, Therianos wskazują zależność od miary).
- Rozbieżność FlyGM vs Dhiman wynika prawdopodobnie z różnych zadań (kontrola RL vs predykcja wzrokowa) i różnej rygorystyczności nulli; nie wolno cytować żadnego z nich jako rozstrzygającego.
- Wniosek praktyczny: kontrola null z zachowaniem stopni (i wag) to minimum, by móc powiedzieć, że wynik zależy od specyficznego okablowania.

### Gaps
- Pospisil et al. (przewidywanie funkcji z konektomu) i Mi et al. - nie znaleziono w wyszukiwaniu, nie cytować bez weryfikacji.
- Zhao 2024 "NeuroAI fly" - nie sprawdzano.
- Pełny tekst FlyGM v3 (co zmieniono) i recenzja - nie sprawdzono.
- Eon Systems 2026 (osadzona wirtualna muszka, "95%" trafności) - tylko wtórne doniesienia, brak pierwotnej publikacji (BRAK DANYCH) — [wtórne](https://ispr.info/2026/04/21/researchers-upload-model-of-flys-brain-to-matrix-let-it-control-virtual-body/)

## 2. Modyfikacje: lezje, wyciszanie, zmiana połączeń/parametrów, kontrole null, pomiar w pętli zamkniętej

### Takeaway
"Wirtualna optogenetyka" (aktywacja/wyciszenie in silico) ma walidację in vivo w Shiu 2024; kontrole przez przepięcie z zachowaniem stopni są już stosowane (FlyGM, Dhiman, Therianos). Brak jednak (w tym przeszukaniu) pierwotnych prac z lezjami w zamkniętej pętli w ciele NeuroMechFly/flybody.

### Cited Findings
- Aktywacja in silico neuronów (smak, mechanoreceptory, region karmienia) przewidziała neurony wywołujące odpowiedź, zweryfikowano optogenetycznie/behawioralnie (POTWIERDZONE, ograniczony zakres) — [Shiu 2024](https://collaborate.princeton.edu/en/publications/a-drosophila-computational-brain-model-reveals-sensorimotor-proce/)
- Ciała do zamkniętej pętli: NeuroMechFly v2 (Nature Methods 2024; wzrok, węch, sprzężenie zwrotne wstępujące, adhezja nóg; używa sieci wzrokowej z ograniczeniem konektomu) — [PubMed 39533006](https://pubmed.ncbi.nlm.nih.gov/39533006/); flybody (Vaxenburg i in., Nature 643:1312-1320, 2025, DOI 10.1038/s41586-025-09029-4; 102 stopnie swobody, MuJoCo, kontroler = sieć wytrenowana RL na zachowaniach, NIE konektom) — [PMC12310536](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12310536/)
- Null z przepięciem: degree-preserving rewired w FlyGM, Dhiman; degree-and-weight-matched ensemble i cell-class-preserving null w Therianos — źródła w sekcji 1.
- Teoria modyfikacji: ten sam konektom + różne parametry biofizyczne -> różna dynamika (Beiran & Litwin-Kumar; Prinz 2004).
- Rodzina "modyfikacji" w C. elegans: Izquierdo & Beer, PLoS Comput. Biol. 9(2):e1002890 (2013), DOI 10.1371/journal.pcbi.1002890 - ścieżkę czuciowo-szyjną wycięto z konektomu, a nieznane parametry elektrofizjologiczne dobrano algorytmem ewolucyjnym; wiele przebiegów daje ENSEMBLE różnych mechanizmów realizujących ten sam klinotaktyczny wynik (POTWIERDZONE) — [PMC3567170](https://pmc.ncbi.nlm.nih.gov/articles/PMC3567170); kontynuacja 2015 (analiza przepływu informacji w tym ensemble) — [PLoS One](https://pmc.ncbi.nlm.nih.gov/articles/PMC4605772)

### Inferences
- Ewolucyjny dobór parametrów przy ustalonej topologii (Izquierdo & Beer) to najlepszy precedens na "warianty jednej architektury"; ensemble ujawnia, że wiele rozwiązań pasuje do tego samego zachowania – to argument za raportowaniem rozkładu wyników po wielu wariantach/ziarnach, nie jednego "najlepszego mutanta".
- Wynik mutanta (zmiana okablowania) ma sens tylko względem rozkładu nulli z tymi samymi stopniami i tym samym treningiem.

### Gaps
- Brak pierwotnych źródeł o lezjach/wyciszeniach w pętli zamkniętej na NeuroMechFly/flybody z modelem konektomu (BRAK DANYCH w tym wyszukiwaniu).
- Standardy statystyczne dla efektów behawioralnych in silico - nie znaleziono dedykowanego opracowania.

## 3. Warianty jednej architektury: neuroewolucja, projektowane obwody C. elegans

### Takeaway
Precedensy są mocne dla C. elegans (Izquierdo & Beer; NCP), ale to są obwody jednego gatunku; dla "projektowanych" obwodów (NCP) nie wolno twierdzić odtwarzania biologii.

### Cited Findings
- Lechner, Hasani, Amini, Henzinger, Rus, Grosu, Nat. Mach. Intell. 2:642-652 (2020), DOI 10.1038/s42256-020-00237-3: Neural Circuit Policies - rzadkie sieci rekurencyjne inspirowane układem nerwowym C. elegans na neuronach LTC; kontroler kierownicy samochodu 19 neuronów, 253 synapsy, deklarowana lepsza generalizacja/interpretowalność/odporność niż duże modele czarnoskrzynkowe (POTWIERDZONE jako wynik autorów, inspiracja nie replika) — [rekord ISTA](https://research-explorer.ista.ac.at/record/8679); [kod](https://github.com/mlech26l/ncps)
- Schmidgall i in. 2022 (sekcja 1): obwód motoryczny C. elegans jako prior architektoniczny.
- Izquierdo & Beer 2013 (sekcja 2).

### Inferences
- NCP = kategoria (4) w taksonomii poniżej; Izquierdo = (3)/(1) zależnie od stopnia dopasowania do danych.

### Gaps
- Nie przeszukano osobno neuroewolucji konektomu muszki ani prac Olivaresa.

## 4. Łączenie obwodów: moduły, SPA/Spaun, NRP, hybrydy międzygatunkowe

### Takeaway
Łączenie modułów w jednym modelu ma solidne precedensy inżynierskie (Spaun, Neurorobotics Platform z funkcjami transferu), ale NIE znaleziono ani jednej pracy budującej hybrydę z konektomów różnych gatunków - to HIPOTEZA/BRAK DANYCH.

### Cited Findings
- Spaun: Eliasmith i in., Science 338:1202 (2012), DOI 10.1126/science.1225266 - ~2,5 mln neuronów, moduły zgodne z strukturami mózgu (PFC, zwoje podstawy, wzgórze), 8 zadań w jednym modelu; wejście obraz 28x28, wyjście ruch fizycznie modelowanego ramienia; Neural Engineering Framework i Nengo (POTWIERDZONE) — [uwaterloo/PDF](https://compneuro.uwaterloo.ca/files/publications/eliasmith.2012.pdf); [PMC4124604](https://pmc.ncbi.nlm.nih.gov/articles/PMC4124604)
- Neurorobotics Platform (HBP/EBRAINS): łączy modele mózgu (SNN do sieci głębokich) z ciałami robotów; funkcje transferu robot->neuron (czujniki w spiki/prąd) i neuron->robot (częstość spajków w polecenia motoryczne) (POTWIERDZONE jako infrastruktura interfejsu) — [EBRAINS](https://www.ebrains.eu/tools/nrp); przykład: móżdżkowy SNN w iCub (VOR) — [PMC9160925](https://pmc.ncbi.nlm.nih.gov/articles/PMC9160925)
- Insektopodobne moduły w robotach: Arena i in. 2017 (spikujący model ciał grzybkowatych jako pamięć parametrów kontrolera motorycznego heksapodu) — [PMC5340754](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5340754/)
- Wyszukiwanie "chimeric/cross-species/hybrid connectome model" nie znalazło obliczeniowej hybrydy z modułami z konektomów różnych gatunków; najbliższe: (a) jeden gatunek jako ANN (Schmidgall), (b) przegląd postulujący konektomikę porównawczą jako dane potrzebne do takich prac, (c) generatywne modele konektomów (Schneidman) - [arXiv 2209.14406](https://arxiv.org/pdf/2209.14406). Chimery biologiczne (komórki innego gatunku) to inny sens, np. [CZI](https://chanzuckerberg.com/science/programs-resources/neurodegeneration-challenge/projects/design-and-functions-of-neural-circuits-in-chimeric-brains)
- Bio-hybrydy (żywe neurony + robot) - tylko terminologia: inna klasa niż hybryda obliczeniowa.

### Inferences
- Brak precedensu w literaturze oznacza, że "hybrydowy mózg muszka+inny gatunek" byłby nowością i nie ma metodologii walidacji; każde twierdzenie o biologicznej zasadności byłoby HIPOTEZĄ.
- Spaun i NRP pokazują, że moduły można łączyć uczciwie, gdy interfejs jest jawnie zaprojektowany (transfer functions) i nazwany inżynierskim.

### Gaps
- Brak źródeł o hybrydzie muszka-wzrok + inny motor; nie sprawdzono prac typu "Neuromorphic multi-species".

## 5. Problemy łączenia i uczciwy interfejs

### Takeaway
Główne problemy: niezgodność typów neuronów/stałych czasowych/kodowania, znak i transmiter (przewidywany, nie zmierzony), I/O, brak biologicznego odpowiednika łączy między modułami; uczciwie rozwiązuje się to jawnymi adapterami z etykietą "inżynieryjny interfejs".

### Cited Findings
- Konektom nie niesie wag, stałych czasowych ani modulacji; gap junctions trudne — [Litwin-Kumar & Turaga 2019](https://dalhousie-university2.demo.elsevierpure.com/en/publications/a-connectome-is-not-enough-what-is-still-needed-to-understand-the); C. elegans: brak identyfikacji innexyn, brak neuromodulacji w danych — [FAQ arXiv 1805.11081](https://arxiv.org/pdf/1805.11081)
- Shiu 2024 opiera się na PRZEWIDYWANYM transmiterze (nie zmierzonym) — [streszczenie](https://collaborate.princeton.edu/en/publications/a-drosophila-computational-brain-model-reveals-sensorimotor-proce/)
- Degeneracja: różne parametry -> ta sama aktywność; ale parametry nie są wymienne po zmianie kontekstu/neuromodulacji — Prinz 2004, Marder (sekcja 1)
- NRP: interfejsy są jawnymi funkcjami transferu (rate/prąd) - wzorzec dla adapterów — [EBRAINS](https://www.ebrains.eu/tools/nrp)
- Schmidgall 2022: transfer bez odtwarzania dokładnego okablowania może pomagać lub szkodzić zależnie od zadania — [arXiv](https://arxiv.org/abs/2209.14406)

### Inferences
- Adaptery (uczone wagi interfejsu, normalizacja rate-matching) są dopuszczalne, ale to wtedy część inżynierska; wynik mówi o hybrydzie jako układzie obliczeniowym, nie o biologii. Wymóg kontroli: ten sam adapter bez modułu biologicznego / z modułem przepiętym (null) / z modułem losowym.
- Zasada uczciwego nazewnictwa: oznaczać każde połączenie jako "biologiczne (z danych)" vs "inżynierskie".

### Gaps
- Brak znalezionej literatury o formalnej metodologii "kompatybilności modułów z różnych gatunków" (BRAK DANYCH).

## 6. Taksonomia (5 klas) z przykładami

### Takeaway
Pięć klas rozróżnia stopień wierności biologii; hybryda międzygatunkowa (5) nie ma w literaturze odpowiednika.

### Cited Findings
1. Reprodukcja obwodu biologicznego (konektom + dane fizjologiczne, walidacja na danych): Shiu 2024; Lappalainen 2024; BAAIWorm 2024 — źródła w sekcji 1. (Dla Shiu walidacja ograniczona do obwodów karmienia/groomingu.)
2. Model inspirowany biologią (zasady, nie okablowanie): Kakaria & de Bivort 2017 (ring attractor z zasad obwodowych) — [PMC5306390](https://pmc.ncbi.nlm.nih.gov/articles/PMC5306390); Arena i in. 2017 (ciała grzybkowate w robocie) — [PMC5340754](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5340754/); Spaun (zgodność anatomiczna, ale model projektowany) — [Eliasmith 2012](https://compneuro.uwaterloo.ca/files/publications/eliasmith.2012.pdf)
3. Zmodyfikowany model konektomu (zmiana wag/połączeń/parametrów względem danych): ensemble Izquierdo & Beer 2013 (parametry dopasowane ewolucyjnie); rewired nulle (Dhiman 2026, Therianos 2026, FlyGM 2026) — źródła w sekcji 1/2. Uwaga: to głównie kontrole, nie "mutanty" jako cel.
4. W pełni sztuczny obwód bio-inspirowany: Neural Circuit Policies (Lechner 2020); Schmidgall 2022 (konektom jako szkielet ANN, biofizyka odrzucona) — [ISTA](https://research-explorer.ista.ac.at/record/8679); [arXiv](https://arxiv.org/abs/2209.14406). Graniczny: FlyGM (konektom jako szkielet, wagi uczone RL) — [arXiv](https://arxiv.org/abs/2602.17997)
5. Hybryda z modułów różnych organizmów: BRAK DANYCH - nie znaleziono pracy obliczeniowej; najbliższe tylko analogie inżynierskie (NRP łączy model mózgu z ciałem robota; Spaun łączy moduły jednego projektu).

### Inferences
- Wynik hybrydy (5) trzeba raportować jako "architekturę inżynierską zbudowaną z komponentów pochodzących z konektomów", nie jako "mózg" żadnego organizmu.
- Wspólne ryzyko wszystkich klas 3-5: efekt "konektom lepszy niż losowy" znika przy kontrolach (Dhiman) lub zależy od miary (Therianos).

### Gaps
- Klasyfikacja jest moją syntezą; nie znaleziono ustalonej taksonomii w literaturze (HIPOTEZA organizacyjna).
