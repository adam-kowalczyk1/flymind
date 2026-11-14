# Stan danych konektomicznych (listopad 2026) — tabela faktów per organizm dla platformy FlyMind

Legenda etykiet: POTWIERDZONE (czytane w źródle pierwotnym/streszczeniu lub co najmniej 2 zgodne źródła), CZĘŚCIOWO POTWIERDZONE (jedno źródło wtórne albo liczba z jednego miejsca), HIPOTEZA, BRAK DANYCH, SPRZECZNE WYNIKI.
Uwaga metodologiczna: wiele stron wydawców (nature.com, bioRxiv) zwróciło w tej sesji błąd 303/429, więc większość liczb pochodzi ze streszczeń/wyszukiwarki i stron instytucji, nie z pełnych tekstów. Gdzie to istotne, zaznaczono to wprost. Nie czytano licencji danych ani dokumentacji neuPrint/CAVE/Codex bezpośrednio (patrz Luki).

## 1. Drosophila dorosła — mózg (FlyWire FAFB v783, hemibrain), kompletność, liczby, metoda

### Takeaway
FlyWire (samica, cały mózg, ssTEM FAFB) to obecnie referencyjny kompletny konektom mózgu muszki: 139 255 neuronów, ok. 50 mln synaps chemicznych (Dorkenwald 2024, Nature). Hemibrain (FIB-SEM, ok. połowa mózgu centralnego, ~25 tys. neuronów, ~20 mln połączeń) jest niekompletny (brak większości płatów wzrokowych, SEZ, neuronów zstępujących/wstępujących, VNC).

### Cited Findings
- POTWIERDZONE: FlyWire — "Neuronal wiring diagram of an adult brain", Dorkenwald i in., Nature 634(8032):124–138, online 2 X 2024, DOI 10.1038/s41586-024-07558-y; 139 255 neuronów, ok. 5×10^7 synaps chemicznych, adnotacje klas, typów, nerwów, hemilinii i przewidywanych neuroprzekaźników; licencja CC BY; dane do pobrania, dostępu programowego i przeglądania — [Europe PMC record](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/s41586-024-07558-y&resultType=core&format=json); liczba neuronów 139 255 i 5×10^7 synaps także w [Princeton record](https://collaborate.princeton.edu/en/publications/neuronal-wiring-diagram-of-an-adult-brain/)
- SPRZECZNE WYNIKI (liczba synaps): strona Wikipedii podaje dla FlyWire jednocześnie ~130 tys./~50 mln oraz ~120 tys./~30 mln ([Wikipedia](https://en.wikipedia.org/wiki/Drosophila_connectome)); wynik wyszukiwarki cytuje „139 tys. neuronów i 54,5 mln synaps" ([sciencedaily 2026-06 / agregat](https://sciencedaily.com/releases/2026/06/260610003047.htm) — wzmianka wtórna). Źródło pierwotne (streszczenie) mówi ok. 50 mln — przyjmować 5×10^7 jako wartość kanoniczną; różnice wynikają z wersji (snapshot) i progu detekcji synaps.
- CZĘŚCIOWO POTWIERDZONE: późniejszy preprint z 2025 (DOI 10.1101/2025.07.11.664377) ma nowszy zestaw synaps o lepszym recall, ale nieco gorszej precyzji — [Wikipedia](https://en.wikipedia.org/wiki/Drosophila_connectome) (nie czytano preprintu). Dla modelowania: zawsze zapisywać wersję materializacji/synaps.
- POTWIERDZONE: obraz FAFB 2017, Zheng i in., Cell 2018, DOI 10.1016/j.cell.2018.06.019 (wg [Wikipedia](https://en.wikipedia.org/wiki/Drosophila_connectome)); metoda: ssTEM, 40 nm przekroje (to ostatnie z wiedzy ogólnej, nie z odczytanego źródła — traktować jako CZĘŚCIOWO).
- POTWIERDZONE: hemibrain — Scheffer i in., eLife 2020;9:e57443, DOI 10.7554/eLife.57443; ~25 tys. neuronów, ~20 mln połączeń (digest eLife); dostęp przez neuPrint; wyklucza większość płatów wzrokowych, wszystkie neurony wstępujące/zstępujące, SEZ i VNC — [eLife](https://elifesciences.org/articles/57443), [recenzje](https://elifesciences.org/articles/57443/peer-reviews)
- BRAK DANYCH w tej sesji: metoda FIB-SEM dla hemibrain nie wymieniona w czytanych fragmentach (powszechnie znana; nie zweryfikowano tu). Wersja "v1.2.1" nie potwierdzona.

### Inferences
- Do modelowania pełnego mózgu (np. LIF, jak Shiu 2024) FlyWire jest właściwym zbiorem; hemibrain nadaje się do porównań i do walidacji typów, nie jako baza pełnych obwodów sensomotorycznych.

### Gaps
- Nie odczytano pełnego tekstu Dorkenwald 2024 (przekierowanie nature.com); brak potwierdzenia dokładnej liczby wejść/wyjść po proofreadingu i metryk precyzji/recall synaps.

## 2. Adnotacje typów komórek, hemilinie (Schlegel 2024), porównanie FlyWire–hemibrain, zmienność międzyosobnicza

### Takeaway
Schlegel i in. 2024 opisują 8 453 typy komórek w FlyWire (3 643 wcześniej zaproponowane dla hemibrain, 4 581 nowych), z definicją typu opartą na podobieństwie między mózgami; ~1/3 typów hemibrain nie dało się wiarygodnie ponownie zidentyfikować. Dane wspierają szeroką stereotypowość z lokalną zmiennością.

### Cited Findings
- POTWIERDZONE: Schlegel i in., "Whole-brain annotation and multi-connectome cell typing of Drosophila", Nature 634:139–152, 2024, DOI 10.1038/s41586-024-07686-5; 8 453 typy (3 643 z hemibrain, 4 581 nowych); hierarchiczna adnotacja klas, typów i hemilinii; typ = grupa komórek bardziej podobnych do komórek w innym mózgu niż do jakiejkolwiek innej w tym samym mózgu; ~1/3 typów hemibrain nie do wiarygodnej reidentyfikacji; heurystyki wiarygodności połączeń między mózgami; w grzybkach (mushroom body) zachowany stosunek E/I przy zmiennej absolutnej ilości wejścia pobudzającego — [wyszukiwarka/agreg. abstrakt (Princeton)](https://collaborate.princeton.edu/en/publications/whole-brain-annotation-and-multi-connectome-cell-typing-of-drosop/), [X-MOL](https://x-mol.com/paper/1841710989195534336)
- SPRZECZNE WYNIKI (liczba typów): Wikipedia podaje dla "consensus atlas" 4 552 typy (3 094 potwierdza hemibrain, 1 458 nowych), preprint DOI 10.1101/2023.06.27.546055, 2023; wersja opublikowana 2024 ma 8 453. Różnica = wersja preprintu vs wersja opublikowana (nie zweryfikowano pełnych tekstów) — [Wikipedia](https://en.wikipedia.org/wiki/Drosophila_connectome). Uwaga: Wikipedia podaje też ~61% typów hemibrain występujących w FlyWire dla preprintu.
- CZĘŚCIOWO POTWIERDZONE: wzmianka prasowa „ponad 8 000 typów" dla FlyWire — [Princeton/Dorkenwald summary](https://collaborate.princeton.edu/en/publications/neuronal-wiring-diagram-of-an-adult-brain/).
- Przewidywania neuroprzekaźnika oraz hemilinie są częścią adnotacji FlyWire (abstrakt Dorkenwald 2024, link wyżej).

### Inferences
- Zmienność między osobnikami jest jakościowo „umiarkowana”: większość typów powtarza się, ale skrajne wartości liczb synaps i pojedyncze typy się różnią. Modele powinny używać połączeń typ→typ (z progiem wiarygodności), a nie pojedynczych krawędzi neuron→neuron.

### Gaps
- Nie odczytano pełnych liczb (np. ułamek połączeń odtwarzalny między półkulami / między FlyWire i hemibrain, rozkład korelacji wag); abstrakt wymienia tylko heurystyki. Różnice lewo–prawo nie potwierdzone liczbowo w tej sesji.

## 3. Samiec CNS (MaleCNS), MANC, FANC, BANC — mózg + ośrodkowy układ nerwowy

### Takeaway
Dostępne są już kompletne konektomy CNS dla samca (Janelia/Cambridge/Google, >166 tys. neuronów, FIB-SEM) i samicy (BANC, ~160 tys. neuronów, ssTEM). Liczby synaps są niepewne (zależą od źródła wtórnego); wersje czasopismowe (Cell wrzesień 2026, Nature czerwiec 2026) są cytowane przez media, nie odczytane przeze mnie z wydawców.

### Cited Findings
- POTWIERDZONE: Male CNS — preprint "Sexual dimorphism in the complete connectome of the Drosophila male central nervous system", Berg i in., bioRxiv DOI 10.1101/2025.10.09.680999, strona Janelia z 6 X 2025; >166 tys. neuronów (mózg + VNC); FIB-SEM; segmentacja Google Research; proofreading i typowanie Janelia + Cambridge (MRC LMB); dane i narzędzia „bezpłatne dla badaczy"; Rubin: pierwszy raz można porównać obie płcie zwierzęcia o złożonych zachowaniach społecznych — [Janelia news](https://www.janelia.org/news/researchers-reveal-connectome-of-the-male-fruit-fly-central-nervous-system)
- CZĘŚCIOWO POTWIERDZONE: wersja w Cell, online 3 IX 2026, DOI 10.1016/j.cell.2026.08.015, 166 700 neuronów — [Sci.News 9 IX 2026](https://www.sci.news/biology/complete-fruit-fly-connectome-15053.html) (agregat; DOI nie sprawdzony w wydawcy). Tytuł wg Sci.News: "...in the complete Drosophila male central nervous system connectome" vs preprint "...in the complete connectome of the Drosophila male central nervous system" — różnica sformułowania (SPRZECZNE w drobnym zakresie; sprawdzić na cell.com).
- CZĘŚCIOWO POTWIERDZONE: ~312 mln synaps dla MaleCNS (preprint) i ~214 mln dla BANC — jedyne źródło: [Wikipedia](https://en.wikipedia.org/wiki/Drosophila_connectome); strona Janelia mówi tylko „miliony połączeń". Nie zweryfikowano w preprintach (bioRxiv zwrócił 429).
- BRAK DANYCH: liczba typów komórek, numer wersji ("v1.0") i dokładny format udostępnienia MaleCNS. Strona Janelia nie podaje; neuPrint niewspomniany na stronie Janelia, Wikipedia mówi, że dane są przeszukiwalne w neuPrint — [Wikipedia](https://en.wikipedia.org/wiki/Drosophila_connectome). Zintegrowane z Virtual Fly Brain — [VFB](https://virtualflybrain.org/blog/2026/09/03/video-the-first-complete-map-of-a-male-flys-entire-central-nervous-system/).
- POTWIERDZONE: BANC — "Distributed control circuits across a brain-and-cord connectome", Bates i in., Nature, DOI 10.1038/s41586-026-10735-w, PMID 42259917; cytowanie podaje 8 VI 2026; ok. 40 mln połączeń synaptycznych wg strony instytutu (patrz niżej), ~160 tys. neuronów wg [FlyWire blog](https://blog.flywire.ai/?p=1823); preprint 10.1101/2025.07.31.667571 (lipiec 2025); dane jako SQLite na Harvard Dataverse, przeszukiwalne przez Codex — [LIMES Bonn](https://limes-institut-bonn.de/en/public-relations/news/articles/news/auf-der-suche-nach-neuen-perspektiven-kopie-1/), [FlyWire blog BANC](https://blog.flywire.ai/?p=1823)
- SPRZECZNE WYNIKI (BANC): „~40 mln synaps” (LIMES) vs „~214 mln synaps” (Wikipedia). Rozbieżność może wynikać z różnej definicji (połączenia neuron→neuron vs pojedyncze synapsy). Data: strona LIMES wskazuje także „08/12/2026” — niejasne (8 VIII albo 12 XII); data cytowania (8 VI 2026) uznana za bardziej wiarygodną.
- POTWIERDZONE: MANC (samiec, VNC) — Takemura i in. (eLife 2024) ~23 tys. neuronów, ~10 mln miejsc presynaptycznych, 74 mln PSD; adnotacje Marin i in. 2024 (typy, linie rozwojowe); analiza zstępujące→motoneurony, predykcja neuroprzekaźnika z progiem prawdopodobieństwa 0,7 („unknown” poniżej) — [Janelia MANC](https://www.janelia.org/manc-connectome), [eLife 96084](https://elifesciences.org/articles/96084)
- POTWIERDZONE (wtórne): FANC (samica, VNC) — Azevedo i in., Nature 631(8020):360–368, DOI 10.1038/s41586-024-07389-x; ~14 600 komórek (ciała), ok. 45 mln synaps wg [Sci.News/wyszukiwarka](https://www.zoo.cam.ac.uk/node/441) i [Wikipedia](https://en.wikipedia.org/wiki/Drosophila_connectome) (autorzy nie sprawdzeni w tej sesji).

### Inferences
- Do rozszerzania FlyMind na ciało/VNC (ścieżka zstępujące→motoneurony, np. DNa02, DNp09) MANC (neuPrint) jest dziś najlepiej opisany; BANC daje spójne połączenie mózg+VNC u samicy (zgodne z FlyWire), MaleCNS — u samca. Mieszanie mózgu FlyWire (samica) z MANC (samiec) wprowadza efekt płci i osobnika.

### Gaps
- Nie odczytano pełnego tekstu żadnej z tych prac; dokładne licencje danych MaleCNS/BANC i liczby synaps do potwierdzenia.

## 4. Larwa Drosophila, C. elegans, Platynereis, Ciona

### Takeaway
Dla małych organizmów dostępne są kompletne konektomy: larwa muszki (3 016 neuronów), C. elegans (302 neurony + gap junctions, 8 osobników rozwojowych), Platynereis (ponad 9 000 komórek) i Ciona (177 neuronów CNS). Tylko C. elegans i Ciona zawierają gap junctions w opublikowanych macierzach.

### Cited Findings
- POTWIERDZONE: larwa L1 — Winding i in., Science 379(6636):eadd9330, 10 III 2023, DOI 10.1126/science.add9330; 3 016 neuronów, 548 tys. synaps, architektura wysoce rekurencyjna — [Cambridge](https://cam.ac.uk/research/news/first-wiring-map-of-insect-brain-complete), [wyszukiwarka PDN](https://www.pdn.cam.ac.uk/news/first-map-showing-every-neuron-wiring-fruit-fly-larva-complete); 93 typy wg Wikipedii.
- POTWIERDZONE: C. elegans dorosły — Cook i in., Nature 571:63–71, 2019: hermafrodyta 460 węzłów (302 neurony, 132 mięśnie, 26 narządów nie-mięśniowych), samiec 579 (385 neuronów, 155 mięśni, 39); obejmuje połączenia chemiczne i gap junctions (krawędzie nieskierowane) — [Google Research](https://research.google/pubs/whole-animal-connectomes-of-both-caenorhabditis-elegans-sexes/), [OpenWorm Connectome Toolbox](https://openworm.org/ConnectomeToolbox/Cook_2019/)
- POTWIERDZONE: C. elegans rozwój — Witvliet i in., Nature 2021: 8 izogenicznych osobników (3 L1, 2 L2, 1 L3, 2 dorosłe), ssTEM; geometria mózgu zachowana, łączność chemiczna istotnie się zmienia, centralne obwody decyzyjne stabilne, ścieżki sensoryczne i motoryczne przebudowane; gap junctions tylko częściowo oznaczone i wyłączone z analiz — [OpenWorm Witvliet](https://openworm.org/ConnectomeToolbox/Witvliet_2021/)
- POTWIERDZONE (wtórne): Platynereis — "Whole-body connectome of a segmented annelid larva", eLife 2025 (wersja 27 VIII 2025), >9 000 zrekonstruowanych komórek neuronalnych i nie-neuronalnych; liczby typów 202 neuronalne / 92 nie-neuronalne wg prezentacji z 2024 — [eLife 97964](https://elifesciences.org/articles/97964), [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12387772/), [Jekely lab talk](https://jekelylab.codeberg.page/EvoDevo_Neuro_Evo_27June2024.html)
- POTWIERDZONE: Ciona — Ryan, Lu, Meinertzhagen, eLife, XII 2016: 177 neuronów CNS, 6 618 synaps (w tym 1 772 złącza nerwowo-mięśniowe) plus 1 206 gap junctions, 922 poliadyczne; ≥25 typów; asymetria lewo–prawo — [eLife 16962](https://elifesciences.org/articles/16962), [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5140270/)

### Inferences
- C. elegans i Ciona są jedynymi zbiorami w tej puli z fizycznie zmierzonymi gap junctions; to dobry „test ujemny” dla twierdzeń o roli sprzężeń elektrycznych, której nie można odtworzyć z EM muszki (patrz sekcja 5).

### Gaps
- Nie sprawdzono licencji/formatów ani aktualizacji C. elegans po 2021 (np. nowsze wersje WormWiring) oraz dokładnej liczby synaps Platynereis.

## 5. Neuroprzekaźniki, znak synapsy, receptory, gap junctions, neuromodulatory

### Takeaway
Przewidywania neuroprzekaźników z EM (Eckstein 2024) są dobre (87% synaps, 94% neuronów, 91% znanych typów), ale to klasyfikacja sześciu transmiterów, nie znaku funkcjonalnego; znak glutaminianu (GluCl vs pobudzający) wymaga założenia o receptorach docelowych, których nie ma w EM.

### Cited Findings
- POTWIERDZONE: Eckstein i in., Cell 187(10), 9 V 2024, "Neurotransmitter classification from electron microscopy images at synaptic sites in Drosophila melanogaster"; sześć transmiterów (ACh, Glu, GABA, DA, 5-HT, OA); dokładność ~87% (synapsy), 94% (neurony), 91% (znane typy); neurony tej samej hemilinii zwykle jedna szybka substancja (ACh/Glu/GABA); predykcje publiczne (projekt "synister") — [Princeton](https://collaborate.princeton.edu/en/publications/neurotransmitter-classification-from-electron-microscopy-images-a/), [PubMed](https://pubmed.ncbi.nlm.nih.gov/38729112/), [Funke lab](https://funkelab.github.io/projects/synister)
- CZĘŚCIOWO POTWIERDZONE: znak jest wnioskowany z identyfikatora transmitera, nie obserwowany; przypadek glutaminianu zależy od ekspresji GluCl na celu (przykład z preprintu 2026 o FC2, arXiv 2607.18969, niska pewność 0,79 etykiety FB5A) — [arXiv 2607.18969](https://arxiv.org/pdf/2607.18969) (źródło tylko ilustracyjne, nie recenzowane).
- POTWIERDZONE: model LIF Shiu i in., Nature 634:210–219, 3 X 2024, waga z liczby synaps, znak z transmitera; walidacja głównie na karmieniu i pielęgnacji czułków; predykcje częściowo potwierdzone optogenetycznie — [Princeton](https://collaborate.princeton.edu/en/publications/a-drosophila-computational-brain-model-reveals-sensorimotor-proce/), [Ideas/RePEc](https://ideas.repec.org/a/nat/nature/v634y2024i8032d10.1038_s41586-024-07763-9.html)
- BRAK DANYCH w tej sesji (nie wyszukano wprost): receptory i gap junctions w EM muszki — z kontekstu (Cook 2019, Ryan 2016, Witvliet 2021) wiadomo, że w C. elegans/Ciona gap junctions są zmapowane, natomiast w opisach FlyWire/hemibrain/MANC nie ma ich wśród adnotacji (abstrakt Dorkenwald: tylko „chemical synapses”). HIPOTEZA, że brak gap junctions w EM muszki to ograniczenie rozdzielczości/barwienia, nie sprawdzono w źródle.
- Neuromodulatory: Eckstein obejmuje DA, 5-HT, OA jako klasy; peptydergiczna/neuromodulacyjna transmisja pozasynaptyczna nie jest odwzorowana w konektomie — nie znaleziono w tej sesji źródła pierwotnego dla tej drugiej części (HIPOTEZA/BRAK DANYCH).

### Inferences
- Dla FlyMind (wnioski z projektu: znak dotyku zależny od Glu) wynika, że parametr „znak Glu” należy traktować jako zmienną kontrolowaną/skanowaną, nie stałą z danych.

### Gaps
- Nie ma tu żadnych niezależnych estymat dokładności znaku funkcjonalnego (wymaga danych elektrofizjologicznych lub ekspresji receptorów), ani statystyki GluCl vs GluR w typach FlyWire.

## 6. Kierunkowość i „siła” połączeń (liczba synaps jako proxy wagi)

### Takeaway
Liczba synaps jest sensownym, ale niedoskonałym proxy wagi; wskazówki z larwy i fragmentów mózgu dorosłego sugerują korelację, a rozmiar synapsy/powierzchnia kontaktu poprawia przewidywanie.

### Cited Findings
- CZĘŚCIOWO POTWIERDZONE: Barnes, Bonnéry, Cardona, PLoS ONE 2022 (larwa): suma powierzchni kontaktów synaptycznych śledzi siłę; liczba synaps jest rozsądnym zastępnikiem, ale ani liczba, ani ułamek wejść nie jest gwarantem siły (różnice molekularne/biofizyczne) — [wyszukiwarka PLoS/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8979427)
- CZĘŚCIOWO POTWIERDZONE: grupa Jeanne (Yale) — liniowa korelacja liczby synaps z wagą połączenia — [Yale news](https://medicine.yale.edu/news-article/catalyzing-impact-through-focused-research-funding-james-jeanne); preprint hemibrain+PN→LHN uEPSP — [bioRxiv 2021.08.19.456845](https://www.biorxiv.org/content/10.1101/2021.08.19.456845.full.pdf) (wnioski końcowe nie odczytane).
- CZĘŚCIOWO POTWIERDZONE: abstrakt COSYNE 2025 (obwód motoryczny larwy): model z względnymi wagami lepszy niż sama liczba synaps — [COSYNE 2025](https://world-wide.org/cosyne-25/relating-synaptic-connectivity-function-3cf9cb08)
- POTWIERDZONE: Lappalainen i in., Nature 634:1132–1140, DOI 10.1038/s41586-024-07939-3: sieć z 64 typów komórek zachowuje łączność z konektomu, a parametry nieznane dopasowane uczeniem; zgodność z pomiarami z 26 prac — [MPI IS](https://is.mpg.de/publications/lappalainennature24)

### Inferences
- Bezpośredni test dla dorosłej muszki, który „rozstrzyga” zasadność liczby synaps jako wagi, nie został tu znaleziony; w FlyMind liczby synaps warto skalować parametrem i testować wrażliwość, nie traktować jako absolutu.

### Gaps
- Lokalizacja na dendrycie, gęstość receptorów, wpływ rozmiaru synapsy w FlyWire — brak źródeł odczytanych bezpośrednio.

## 7. Dane funkcjonalne vs strukturalne vs modelowane; Pospisil 2024

### Takeaway
Pospisil 2024 nie dostarcza empirycznej „funkcjonalnej łączności” z obrazowania, tylko estymator „effectome” (model liniowy z perturbacjami optogenetycznymi, konektom jako prior). MICrONS jest przykładem zbioru z koregistracją funkcjonalną (Ca2+) i EM.

### Cited Findings
- POTWIERDZONE: Pospisil i in., "The fly connectome reveals a path to the effectome", Nature 634:201–209, 2024, DOI 10.1038/s41586-024-07982-0: estymator liniowego modelu dynamicznego z danych stochastycznej perturbacji optogenetycznej z konektomem jako priorem; walidacja symulacjami; dynamika całego mózgu = zbiór małych, niemal niezależnych obwodów — [PMC11446844](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11446844/), [RePEc](https://ideas.repec.org/a/nat/nature/v634y2024i8032d10.1038_s41586-024-07982-0.html)
- UWAGA/KOREKTA: w zadaniu przypisano Pospisil 2024 „fly functional connectivity”; źródło potwierdza, że to praca metodologiczna (effectome), a nie zbiór danych funkcjonalnych — korekta tej klasyfikacji.
- POTWIERDZONE: MICrONS — "Functional connectomics spanning multiple areas of mouse visual cortex", Nature 640:435–447, 10 IV 2025, DOI 10.1038/s41586-025-08790-w; ~75 tys. neuronów obrazowanych Ca2+ w V1 i trzech wyższych obszarach, koregistrowane z EM >200 tys. komórek i ~0,5 mld synaps (523 mln wg komentarza); objętość ok. 1 mm^3; towarzysząca praca "Functional connectomics reveals general wiring rule..." (podobne odpowiedzi → preferencyjne połączenia) — [Princeton record](https://collaborate.princeton.edu/en/publications/functional-connectomics-spanning-multiple-areas-of-mouse-visual-c/), [MICrONS explorer](https://www.microns-explorer.org/cortical-mm3)
- SPRZECZNE WYNIKI (drobne): DOI MICrONS — wyszukiwarka w jednym miejscu daje 10.1038/s41586-025-08840-3 (RePEc), w innym 10.1038/s41586-025-08790-w; wymaga sprawdzenia (obie są w numerze Nature vol. 640 — prawdopodobnie różne prace towarzyszące) — [IDEAS](https://ideas.repec.org/a/nat/nature/v640y2025i8058d10.1038_s41586-025-08840-3.html).
- Definicje (własne, bez zewn. cytatu — HIPOTEZA terminologiczna): konektom strukturalny = graf z EM; funkcjonalny = korelacje/przyczynowość z aktywności; modelowany = struktura + model dynamiki (np. Shiu, Lappalainen).

### Inferences
- Dla FlyMind: dane funkcjonalne dla muszki są szczątkowe względem konektomu; waliduje się je głównie zachowaniem/obwodami znanymi z literatury (np. grooming, karmienie, Shiu).

### Gaps
- Nie wyszukano zbiorów funkcjonalnych dla całego mózgu muszki ani zebrafish (poza wzmianką o koregistracji w projekcie Janelia/Google). Funkcjonalny atlas FDA tylko wspomniany w wynikach, nie sprawdzony.

## 8. Kręgowce: zebrafish, mysz, człowiek (H01), plan całego mózgu myszy

### Takeaway
Dla kręgowców dostępne są duże fragmenty (MICrONS 1 mm^3, H01 1 mm^3) i trwające projekty całego mózgu larwy zebrafish; pełny konektom mózgu myszy jest dopiero w fazie skalowania (rząd 50× większy niż obecne objętości).

### Cited Findings
- POTWIERDZONE: H01 — Shapson-Coe i in., Science 384:eadk4858, 10 V 2024: ~1 mm^3 ludzkiej kory skroniowej z chirurgii padaczki, ~57 tys. komórek, ~230 mm naczyń, ~150 mln synaps, 1,4 PB; glej:neurony ~2:1; rzadkie silne wejścia aksonalne do 50 synaps; dane na h01-release.storage.googleapis.com — [Harvard VCG](https://vcg.seas.harvard.edu/publications/20240510-a-connectomic-study-of-a-petascale-fragment-of-human-cerebral-cortex)
- CZĘŚCIOWO POTWIERDZONE: zebrafish Fish-X — preprint bioRxiv 10.1101/2025.06.12.659365: "Multiplexed neuromodulatory-type-annotated whole-brain EM-reconstruction of larval zebrafish", 6 dpf, ssEM; 176 810 komórek i 25,25 mln synaps; anotacje molekularne (neuromodulatory); użyte do badania wejść do neuronów noradrenergicznych locus coeruleus — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.06.12.659365.full.pdf) (z wyników wyszukiwarki; pełnego PDF nie odczytano — przekroczono limit rozmiaru).
- CZĘŚCIOWO POTWIERDZONE: projekt Janelia/Google/Harvard (6 dpf, ~140 tys. neuronów, powiązany z obrazowaniem light-sheet tego samego osobnika; snapshoty wersjonowane) — [Janelia](https://www.janelia.org/node/70289); wzmianka wtórna, że proofreading ma się zakończyć w 2026 — [KuCoin news (agregat, niska wiarygodność)](https://www.kucoin.com/news/insight/BTC/6a6c7ced9bd794000857259f). Nazwy "Fish-X"/"Fish Fire&Wire" jako projekty: Fish-X to tytuł/skrót z preprintu (nie potwierdzony jako nazwa programu), "Fish Fire&Wire" pochodzi ze strony Janelia (wyszukiwarka). SPRZECZNE WYNIKI: 176 810 komórek (Fish-X, wszystkie komórki) vs ~140 tys. neuronów (Janelia) — różne definicje (komórki vs neurony) lub osobniki.
- POTWIERDZONE: wcześniej: Hildebrand i in. 2017 (Nature) — pierwsza całomózgowa ssEM larwy zebrafish 5,5 dpf — [Hildebrand 2017](https://www.lee.hms.harvard.edu/hildebrand-et-al-2017).
- CZĘŚCIOWO POTWIERDZONE: cały mózg myszy — Collins, Huffman, Koene (Cell Reports Methods 2025): EM najbardziej niezawodna ścieżka w najbliższym czasie, rozszerzona mikroskopia ekspansyjna może być wykonalna później; wymagana przepustowość niedostępna — [PMC11955263](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11955263/); BRAIN CONNECTS: mózg myszy ~50× większy niż obecnie obrazowane 10 mm^3 — [NIH BRAIN CONNECTS](https://braininitiative.nih.gov/taxonomy/term/235); raport "State of Brain Emulation 2025": 5-letni projekt ma obrazować ~2–3% mózgu myszy (~10× MICrONS) — [arXiv 2510.15745](https://arxiv.org/pdf/2510.15745).

### Inferences
- Dla modelowania SNN: zebrafish larva (całomózgowy, z koregistrowaną aktywnością) to kandydat na następny konektom po muszce, ale status dostępności publicznej jest niepotwierdzony.

### Gaps
- Nie sprawdzono: stanu dostępności danych Fish-X/Janelia na koniec 2026; MICrONS v1300+ wersje; neuroprzekaźniki w MICrONS/H01; alternatywne projekty całomózgowe myszy poza BRAIN CONNECTS.

## 9. Inne owady (pszczoła, mrówki, szarańcza)

### Takeaway
Nie znalazłem żadnego opublikowanego synaptycznego konektomu pszczoły, mrówki ani szarańczy; jedyna znaleziona praca to rozprawa o kompleksie centralnym pszczoły potnej (rekonstrukcja z EM).

### Cited Findings
- CZĘŚCIOWO POTWIERDZONE: rozprawa doktorska Lund University, styczeń 2026, o kompleksie centralnym "sweat bee" (słowa kluczowe: connectomics, volume EM, segmentation) — [Lund University](https://lup.lub.lu.se/record/36d49300-14d1-4a52-a83d-4efea73dbc29) (nie czytano; brak informacji o liczbie neuronów/synaps).
- BRAK DANYCH: Apis mellifera, mrówki, Locusta — brak wyników wyszukiwania na konektomy; nie jest to dowód nieistnienia (pojedyncze zapowiedzi mogły umknąć wyszukiwaniu).

### Inferences
- Porównania międzygatunkowe (kompleks centralny, grzybki) opierają się na muszce; nie ma w pełni użytecznych konektomów innych owadów na koniec 2026 wg tej wyszukiwarki.

### Gaps
- Powyższe do zweryfikowania celowanym przeszukaniem bioRxiv.

## 10. Narzędzia, formaty, licencje

### Takeaway
Dostęp do FlyWire jest przez CAVE/Codex (licencja CC BY dla publikacji z Nature), hemibrain/MANC/MaleCNS przez neuPrint, BANC przez Codex i SQLite (Harvard Dataverse), H01 przez Google Cloud.

### Cited Findings
- POTWIERDZONE: FlyWire — licencja CC BY, dane do pobrania, dostępu programowego i przeglądania — [Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/s41586-024-07558-y&resultType=core&format=json)
- POTWIERDZONE: hemibrain — przeglądarka neuPrint — [eLife](https://elifesciences.org/articles/57443); MANC — przeszukiwalny w neuPrint [Wikipedia](https://en.wikipedia.org/wiki/Drosophila_connectome); BANC — SQLite na Harvard Dataverse oraz Codex — [FlyWire blog](https://blog.flywire.ai/?p=1823); H01 — [Harvard VCG](https://vcg.seas.harvard.edu/publications/20240510-a-connectomic-study-of-a-petascale-fragment-of-human-cerebral-cortex); wiele projektów C. elegans zagregowane w OpenWorm Connectome Toolbox — [OpenWorm](https://openworm.org/ConnectomeToolbox/Cook_2019/).
- BRAK DANYCH (nie sprawdzano bezpośrednio): navis, fafbseg, natverse, formaty Arrow/feather/CSV Codex, licencje MaleCNS/BANC/MANC — ostrzeżenie: nie zakładać CC BY bez sprawdzenia strony zbioru.

### Inferences
- Wersjonowanie (materializacje CAVE, snapshoty neuPrint) jest krytyczne dla powtarzalności eksperymentów FlyMind.

### Gaps
- Cała ta sekcja wymaga bezpośredniego czytania dokumentacji (codex.flywire.ai, neuprint.janelia.org, male-cns.janelia.org), której nie wykonano z powodu ograniczeń narzędzi/limitu wywołań.
