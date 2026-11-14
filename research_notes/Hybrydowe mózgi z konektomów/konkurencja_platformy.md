# Konkurencja i platformy: konektom -> SNN -> modyfikacja/kompozycja obwodów -> robot (stan na 3 listopada 2026)

Metoda: wyszukiwania WebSearch + pobrania stron (WebFetch), 3 XI 2026. Etykiety: **POTWIERDZONE** = przeczytałem stronę pierwotną (repo, abstrakt, strona instytucji) lub >=2 niezależne źródła; **CZĘŚCIOWO POTWIERDZONE** = jedno źródło wtórne / agregator / opis bez daty / niespójne liczby; **HIPOTEZA** = moje wnioskowanie; **BRAK DANYCH** = nie znalazłem. Wcześniejsze notatki (`Projekt mózgu muchy dla inwestorów/konkurencja_stan_wiedzy.md`) zawierają szczegóły o Eon, Fly Brain Bridge, FlyDrones, hobbystycznych repo i firmach "biologicznych" — tu je tylko podsumowuję i linkuję, a rozszerzam o platformy, C. elegans, neuromorfikę, laboratoria i macierz możliwości. Narzędzie wyszukiwania jest US-only i słabe na YouTube/Hackaday/Discord, więc "nie znalazłem" != "nie istnieje". Repo HF `hwihwalab/malecns-connectome-robotics-2026` zwraca HTTP 401 (prywatne/ukryte) — zawartości nie udało się odczytać.

---

## 1. Platformy i narzędzia (infrastruktura) — czy ktoś już buduje "FlyMind"?

### Takeaway
Nikt nie oferuje pełnego pipeline'u "wyciągnij obwód z prawdziwego konektomu -> zbuduj SNN -> modyfikuj/łącz -> osadź w robocie". Istnieją osobne klocki: dane i przeglądarki (FlyWire Codex, neuPrint, MaleCNS), model LIF (Shiu), ciała symulowane (flygym, flybody), platforma neurorobotyczna ogólnego przeznaczenia (EBRAINS NRP), symulatory SNN (NEST, Arbor, Brian2, GeNN, Nengo). Najbliższe są: (a) Eon Systems (zamknięty, sim), (b) hobbystyczne repo 2026 (sim lub niesprawdzony sprzęt), (c) EBRAINS NRP (dojrzała platforma sim+fizyczne roboty, ale bez ekstrakcji z konektomu muchy).

### Cited Findings

**EBRAINS Neurorobotics Platform (dawniej HBP)**
- EBRAINS opisuje NRP jako trzon usługi "Closed-Loop Neuroscience": modele neuronalne, w tym SNN na chipach neuromorficznych, łączone z ciałami fizycznymi lub symulowanymi; usługa otwarta i bezpłatna, dostępna online w przeglądarce albo lokalnie (Docker/źródła); kod na Bitbucket. Strona nie wymienia symulatorów, robotów ani wersji. — [EBRAINS NRP](https://www.ebrains.eu/tools/nrp) — POTWIERDZONE (opis), szczegóły techniczne BRAK DANYCH na tej stronie
- Pierwsza wersja opisana w pracy z HBP: "Connecting Artificial Brains to Robots in a Comprehensive Simulation Framework: The Neurorobotics Platform" (2017). Z mojej wiedzy platforma łączy Gazebo z NEST/Nengo; stronie EBRAINS tego nie ma, a przeszukanie nie potwierdziło — CZĘŚCIOWO POTWIERDZONE. — [PMC5263131](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5263131/)
- Status po HBP: projekt-rodzic EBRAINS 2.0 trwa od 2024-01 do 2026-12 (czyli kończy się za ~2 miesiące); nie znalazłem żadnej informacji o następcy ani przedłużeniu. — [EPTA database](https://eptanetwork.org/database/projects/1617-ebrains-2-0) — CZĘŚCIOWO POTWIERDZONE (jedna baza projektów); losy po 12/2026: BRAK DANYCH
- Przykład użycia: robot uczący się łączyć wzrok i dotyk na EBRAINS (2021, CORDIS); Politecnico di Milano planuje use case neurorobotyczny z SNN i uczeniem błędem przewidywania. — [CORDIS](https://cordis.europa.eu/article/id/430360-a-robot-on-ebrains-has-learned-to-combine-vision-and-touch), [PoliMi](https://www.deib.polimi.it/eng/european-projects/details/495)
- Brak jakichkolwiek wzmianek o konektomie Drosophila w NRP w znalezionych źródłach — BRAK DANYCH
- NEST: nadal aktywny (wersja 3.9 ogłoszona przez EBRAINS; ślad dokumentacji 3.10; NEST wszedł do benchmarku SPEC CPU 2026, maj 2026). Arbor wchodzi do toolboxa EBRAINS (symulacje wielokompartmentowe). — [EBRAINS: NEST w SPEC](https://ebrains.eu/news-and-events/2026/nest-in-the-new-spec-benchmark-suite), [D3.1 EBRAINS 2.0](https://ebrains.eu/sites/default/files/downloads/2026/04/D3.1_EBRAINS%202.0_approved.pdf) — CZĘŚCIOWO POTWIERDZONE (wersje z bluesky/pakietów). "Arbor 3.0" nie znaleziono.

**Dane i narzędzia do eksploracji konektomu**
- FlyWire Codex (Princeton): portal do wyszukiwania neuronów po metadanych, grafy połączeń, Neuroglancer, eksport do analizy offline; MaleCNS dostępny w Codex. — [Codex](https://codex.flywire.ai/), [About Codex](https://codex.flywire.ai/about_codex), [FlyWire annotations](https://github.com/flyconnectome/flywire_annotations) — POTWIERDZONE (istnienie i funkcje); brak funkcji symulacji
- neuPrint: baza grafowa (Cypher) dla konektomów Janelia; opis z preprintu 2020. — [PMC / bioRxiv 2020.01.16.909465](https://0-doi-org.brum.beds.ac.uk/10.1101/2020.01.16.909465) — CZĘŚCIOWO POTWIERDZONE (źródło z 2020)
- Virtual Fly Brain, Allen Institute (MICrONS itd.): wyszukiwanie nie zwróciło żadnych wyników o ich stanie na 2026 — BRAK DANYCH (z mojej wiedzy to portale danych/anatomii, nie symulatory; niezweryfikowane)
- Fork Codex z symulacją `sim/` (Ryans-sS/malecns-embodied-fly): dwa zbiory (FlyWire 783: ~139k neuronów; MaleCNS v1.0: ~166,7k neuronów, 124,2M synaps), LIF + metabolizm, ciało NeuroMechFly/MuJoCo (66 stawów nóg), testy skryptowe z grupami kontrolnymi (chemotaksja, uczenie asocjacyjne w komórkach Kenyona, chód); brak sprzętu; autor wprost oddziela dane od założeń modelu (dynamika błon, progi, reguła uczenia, generator chodu to model). Wymaga ~16 GB RAM, dane ~11 GB osobno. — [GitHub](https://github.com/Ryans-sS/malecns-embodied-fly) — POTWIERDZONE (z README), jakość merytoryczna nierecenzowana
- Shiu et al. `Drosophila_brain_model`: LIF w Brian2, aktywacja (Poisson) i wyciszanie neuronów, dane FlyWire v630/v783 (CSV/Parquet), licencja MIT, 399 gwiazdek/82 forki, notatniki z tutorialem; brak narzędzi robotycznych; data ostatniego commita niewidoczna. — [GitHub](https://github.com/philshiu/Drosophila_brain_model) — POTWIERDZONE
- Sandia: cały konektom FlyWire (~140k neuronów, ~50M synaps) uruchomiony na Intel Loihi 2 (12 chipów), arXiv 2508.16792 (VIII 2025); Sandia mówi o >100x szybszym działaniu niż symulacja numeryczna na klasycznym sprzęcie i o "pierwszej nietrywialnej, biologicznie realistycznej symulacji konektomu na sprzęcie neuromorficznym"; wątek robotyczny nie występuje. Liczba "milivaty/real-time" pochodzi z wtórnego opisu, nie z pracy. — [arXiv 2508.16792](https://arxiv.org/pdf/2508.16792), [Sandia](https://www.sandia.gov/news/publications/hpc-annual-reports/article/advancing-neuromorphic-computing-at-the-neural-exploration-and-research-lab/) — POTWIERDZONE (praca); "real-time/mW" CZĘŚCIOWO
- Nengo (Applied Brain Research, Waterloo): system do budowy dużych modeli funkcjonalnych mózgu; licencja własna (darmowa do badań/użytku osobistego, komercyjna płatna); ABR wg Preqin: seed w styczniu 2026 (Two Small Fish Ventures), obecny focus = edge AI (transkrypcja głosu, biosygnały). Stan backendów Loihi/NengoDL w 2026: BRAK DANYCH. — [Preqin](https://www.preqin.com/data/profile/asset/applied-brain-research-inc-/785003), [Wikipedia via wyszukiwanie](https://Www.wikipedia.org/wiki/Neural_Engineering_Object) — CZĘŚCIOWO POTWIERDZONE
- GeNN (Sussex, Nowotny): biblioteka C++/Python generująca kod SNN na GPU (2014; PyGeNN 2021); użyta w robocie Quanser Q-car na Jetson TX2 z modelem ciała grzybkowatego mrówki (400 scen, trasa 27 m; błąd średni 0,144 +/- 0,088 m na trasie 6,5 m). Model biologii mrówki (nie Drosophila, nie z konektomu neuron-po-neuronie). — [Knight/Nowotny/Graham (2024)](https://www.frontiersin.org/journals/neuroinformatics/articles/10.3389/fninf.2021.659005/pdf) — CZĘŚCIOWO POTWIERDZONE (link wskazany przez wyszukiwarkę dla pracy o GeNN; szczegółowe liczby z podsumowania wyszukiwarki)

**Ciała symulowane i modele fizyczne** (szczegóły w poprzednich notatkach)
- NeuroMechFly v2/flygym (EPFL, Nature Methods XI 2024; MuJoCo; zawiera sieć wzrokową ograniczoną konektomem): [EPFL](https://actu.epfl.ch/news/simulating-how-fruit-flies-see-smell-and-navigat-7). Laboratorium Ramdyi: praca o koordynacji czyszczenia ("grooming") z symulacjami ograniczonymi konektomem — wg strony laboratorium przyjęta do Nature Communications w 2026 (nie potwierdziłem, czy pętla zamknięta/całomózgowa); przegląd "neuromechanical digital twins" (Wang-Chen, Ramdya) jako arXiv 2026, w recenzji. — [EPFL Ramdya lab](https://www.epfl.ch/labs/ramdya-lab/?p=484) — CZĘŚCIOWO POTWIERDZONE
- flybody (Janelia/DeepMind, Nature VII 2025, sterownik z RL — nie konektom): [repo](https://github.com/TuragaLab/flybody) — wg poprzedniej notatki POTWIERDZONE.

**C. elegans — platformy i roboty**
- BAAIWorm (Lei Ma, Peking University + BAAI; Nature Computational Science, XII 2024; DOI s43588-024-00738-w): biofizycznie szczegółowa sieć + model ciała (96 komórek mięśniowych) + środowisko 3D, pętla zamknięta, 30 klatek/s, chemotaksja ze zygzakowatym ruchem; otwarte repo (także Gitee). Raport "State of Brain Emulation 2025" wskazuje jako otwarte wyzwania: pełne 302 neurony i zachowania poza chemotaksją. Brak sprzętu. — [PKU NBIC](https://nbic.pku.edu.cn/en/Achievements/d57de79476bf4b279d32e0c285da6405.htm), [Gitee](https://gitee.com/garrychengitee/BAAIWorm), [State of Brain Emulation](https://arxiv.org/pdf/2510.15745) — POTWIERDZONE (wiele źródeł; liczby z wyszukiwarki)
- OpenWorm: c302 (framework obwodu 302 neuronów z konektomu Cook 2019, poziom C1 sprzęgany z Sibernetic) i Sibernetic (SPH na GPU, C++/OpenCL); mirror GitHub pokazuje aktualizacje sibernetic 30 III 2026 i c302 31 III 2026. Dokumentacja "preview" oraz mirrory nieoficjalne. — [docs.openworm.org](https://docs.openworm.org/projects/), [c302 docs](https://docs.openworm.org/preview/integrate-design-documents/Projects/c302) — CZĘŚCIOWO POTWIERDZONE
- Robot C. elegans: Busbice 2014 (LEGO Mindstorms; w poprzedniej notatce); Valencia Urbina i in. 2023 (robot różnokołowy z konektomem C. elegans — wg strony Plüssa, bez szczegółów hardware/sim); strona Ramiro Plüss "Connectome-Driven Embodied Robotics" deklaruje plan rozszerzenia na Drosophila i hexapoda, bez wyników. — [Plüss](https://plussramiro.github.io/projects/connectome-driven-robotics) — CZĘŚCIOWO POTWIERDZONE (strona projektowa, bez danych)

**Hobbystyczne repo 2026 (sim; sprzęt niepotwierdzony)** — szczegóły w poprzedniej notatce; nowe z mojego przeszukania GitHub:
- connectocopter (symulowany quadcopter-rover FPV; README: 19/20 dotarć do celu, 4/20 po przepleceniu konektomu) — [repo](https://github.com/TheJustas228/connectocopter); flywire-connectome-vizdoom (agent SNN w ViZDoom vs heurystyka i DQN, R-STDP) — [repo](https://github.com/marvenarg/flywire-connectome-vizdoom); flywire-brain-drone (1 871 neuronów ucieczki; sterowanie "cruise" nadal programowe) — [repo](https://github.com/huang12chen/flywire-brain-drone); ekorusd/flywire-snn-brain (NPC w Roblox) — [repo](https://github.com/ekorusd/flywire-snn-brain); flywire-fly-lab (C++ reimplementacja flygym ze spajkowym konektomem) — [temat GitHub](https://github.com/topics/neuromechfly). Tylko opisy z wyszukiwarki, nie czytałem README tych ostatnich — CZĘŚCIOWO POTWIERDZONE
- Poprzednio opisane: Fly Brain Bridge (kwadruped Sesame + MaleCNS; sprzęt częściowo) i FlyDrones (adaptery Tello/Crazyflie "nie testowane w locie") — patrz poprzednia notatka; nie sprawdzałem ponownie, czy od tamtej pory pojawiły się testy sprzętowe — BRAK DANYCH o zmianie.

### Inferences
- HIPOTEZA: Jeśli "platforma" = otwarty, utrzymywany, wieloetapowy pipeline z modyfikacją i kompozycją obwodów, to w znalezionych źródłach nie ma jej odpowiednika. Najbliżej "produktowo": forka Codex z `sim/` (jedna osoba, sim), Eon (zamknięty), NRP (ogólna platforma, bez konektomu muchy).
- HIPOTEZA: EBRAINS NRP może być tym, co "FlyMind" mógłby po prostu wykorzystać zamiast budować od zera (Gazebo/robot fizyczny + SNN), ale wątpliwa przyszłość po 12/2026 i brak aktywnej społeczności wokół muchy.
- Większość "modyfikacji" w istniejących narzędziach to wyciszanie/aktywacja neuronów (Shiu) lub przeplatanie całego grafu (connectocopter); kompozycji obwodów z różnych źródeł (np. mysz + mucha) nie znalazłem.

### Gaps
- Strona NRP nie wymienia symulatorów/robotów; nie sprawdziłem repozytorium Bitbucket ani liczby aktywnych użytkowników po 2023.
- Virtual Fly Brain, Allen tools: brak wyników 2026.
- HF `hwihwalab/malecns-connectome-robotics-2026`: 401, zawartość nieznana (HF zwraca 401 także dla nieistniejących repo, więc nawet istnienie nie jest potwierdzone).
- Nie sprawdziłem, czy kod sprzęgania ciała Eon został wydany.

---

## 2. Firmy

### Takeaway
Tylko Eon Systems realnie dotyka emulacji konektomu; reszta to inne technologie (żywe neurony, algorytmy inspirowane owadami, ciekłe sieci, układy neuromorficzne) — kontekst rynkowy i potencjalni dostawcy sprzętu, nie konkurenci pipeline'u.

### Cited Findings
- **Eon Systems PBC**: seed 3,5 M USD (XII 2025; Protocol Labs; Larry Page family office wg jednego źródła); 7 III 2026 pokazali "emulację całego mózgu muchy" (139 255 neuronów, ~50 M synaps) sprzężoną z ciałem MuJoCo; cel: emulacja mózgu myszy (~70 M neuronów) w 2 lata — eksperci sceptyczni (dekada+); nie znalazłem nowej rundy ani wyników na myszy; The Register 16 III 2026 relacjonuje demo. — [Untapped Ventures](https://untappedventures.substack.com/p/untapped-ventures-invests-in-eon), [Seedtable](https://seedtable.com/companies/eon-systems/funding-rounds/seed-2025-12), [The Register](https://www.theregister.com/2026/03/16/digital_fruit_fly_brain_model/), [The Decoder](https://the-decoder.com/startup-claims-first-full-brain-emulation-of-a-fruit-fly-in-a-simulated-body/) — POTWIERDZONE (finansowanie z 2 źródeł); termin "2 lata" to deklaracja firmy
- **Cortical Labs** (Melbourne): CL1 (III 2025, 35 000 USD), chmura "Cortical Cloud", przedsięwzięcie DayOne w Singapurze; łączna kwota finansowania niespójna (10,7-12,5 M USD wg agregatorów; stare prasowe "15 M" od Horizon Ventures); grant AUD 245 tys.; Gobi Partners (III 2026). Nic o robotach w znalezionych źródłach. — [IT Brief](https://itbrief.com.au/story/cortical-labs-cl1-commercial-milestone-after-aud-245k-grant), [CB Insights](https://www.cbinsights.com/company/cortical-labs), [Wikipedia](https://en.wikipedia.org/wiki/Cortical_Labs) — CZĘŚCIOWO POTWIERDZONE (finanse sprzeczne)
- **FinalSpark** (Vevey): Neuroplatform dla organoidów (zdalny dostęp od V 2024); deklaracje energooszczędności to twierdzenia firmy; kwota rundy A nieznana. — [BusinessWire](https://www.businesswire.com/news/home/20240515046329/en/) (z poprzedniej notatki), [przegląd 2026](https://biocomputer.pages.dev/blog/state-of-biocomputing-2026) — CZĘŚCIOWO POTWIERDZONE
- **Opteran** (Sheffield): sztuczna inteligencja inspirowana wzrokiem/nawigacją pszczoły; £2,1 M seed (XI 2020), 12 M USD (VI 2022, Join Capital); sumy 12,3-24,7 M USD zależnie od źródła; w 2026 brak nowej rundy. — [The Engineer](https://theengineer.co.uk/articles/opteran-secures-21m-to-solve-autonomy-in-robotics), [UKTN](https://www.uktech.news/ai/sheffield-spinout-opteran-insect-ai-20220624) — CZĘŚCIOWO POTWIERDZONE (technologia: reverse-engineering mózgu owada, nie konektom neuron-po-neuronie wg mojej wiedzy)
- **Liquid AI** (MIT spin-out, dziedzictwo sieci typu NCP/liquid z C. elegans): Series A 250 M USD przy wycenie ok. 2,35 mld USD (XII 2024, AMD Ventures) — jedno źródło wspomina nieprawdopodobną "Series C" i ~2 mld (III 2025) — niespójne; modele LFM2 (np. LFM2-24B, II 2026); "Liquid Labs" od 1 IV 2026. Brak związku z konektomem muchy w znalezionych źródłach; pochodzenie od NCP z C. elegans to wiedza własna, niezweryfikowana tu. — [Dealroom](https://dealroom.co/companies/liquid-ai/), [StartupHub](https://www.startuphub.ai/startups/liquid-ai.md) — CZĘŚCIOWO POTWIERDZONE
- **Numenta / Thousand Brains Project (Monty)**: od I 2025 niezależna organizacja non-profit; Gates Foundation min. 2,69 M USD na 2 lata; Monty open source (sensorimotor, robotyka jako cel); to model neokorteksu, nie konektom. Brak ogłoszeń 2026 o wdrożeniach robotycznych. — [BusinessWire](https://www.businesswire.com/news/home/20250107503206/en/), [arXiv 2412.18354](https://arxiv.org/html/2412.18354v1) — POTWIERDZONE
- **Neuromorfika sprzętowa**: SpiNNcloud (EIC Accelerator 10 M EUR blended, VII 2025; system "THOR" w USA; SpiNNaker 2 "Braunfels" w Sandia) — [EBRAINS news](https://ebrains.eu/news-and-events/2025/brain-tech-in-action-german-spinncloud-computing-startup-secures-funding-of-10), [Silicon Saxony](https://silicon-saxony.de/en/spinncloud-us-research-initiative-thor-equipped-with-neuromorphic-supercomputer-milestone-for-brain-inspired-computing/); Innatera (seria A ok. 15-21 M; produkt Synfire 2026) — [Innatera](https://innatera.com/news/innatera-raises-eur15m-for-neuromorphic-edge-ai); BrainChip (25 M USD, nieustalona data; AKD1500 wysyłany VI 2026) — [Quantum Zeitgeist](https://quantumzeitgeist.com/?p=252322); SynSense: brak danych o 2026; Prophesee (czujniki zdarzeniowe; ok. 20 M EUR w VI 2026 wg wtórnych źródeł, łącznie ~113 M USD wg Caplight); iniVation: brak danych 2026. — [Abovea przegląd](https://abovea.tech/insights-strategies/neuromorphic-computing-startups/), [Caplight/Prophesee](https://www.caplight.com/company/prophesee) — CZĘŚCIOWO POTWIERDZONE
- **Carboncopies Foundation**: organizacja non-profit; aktualizacja "Roadmap" WBE (poprzednia: Sandberg-Bostrom 2008), projekty: ramy etyczne i "Brain Emulation Challenge"; nie jest firmą ani platformą narzędziową. — [Carboncopies](https://carboncopies.org/Research/Roadmap/About/) — POTWIERDZONE
- **Koniku**: brak wyników wyszukiwania — BRAK DANYCH. MindPortal: nie sprawdzałem — BRAK DANYCH. Firma sprzedająca "biologiczne kontrolery" robotów z konektomu: nie znalazłem — BRAK DANYCH.

### Inferences
- HIPOTEZA: kategoria "emulacja konektomu jako produkt" ma jednego widocznego gracza (Eon, ~3,5 M USD); skala rund w pokrewnych kategoriach 10-25 M USD.
- Neuromorfika (Loihi 2, SpiNNaker 2, Innatera, BrainChip) to naturalne cele wdrożeniowe SNN z konektomów (Sandia pokazało to na Loihi 2), ale nie dostawcy narzędzi do ekstrakcji obwodów.

### Gaps
- Rundy FinalSpark, Opteran 2026, Cortical Labs: niespójne; wymagają Crunchbase/komunikatów firm.
- Prophesee: brak pierwotnego komunikatu 2026.

---

## 3. Laboratoria akademickie

### Takeaway
Nauka robi niezależnie: (1) konektom -> ciało w symulacji (Ramdya, Turaga, Eon-współpracownicy), (2) obwody owadów -> roboty fizyczne, ale zwykle zabstrahowane (Sussex, Webb, Opteran), (3) SNN -> manipulatory (neuromorfika, bez konektomu muchy). Połączenia (konektom muchy -> SNN -> robot fizyczny) nie znalazłem w publikacjach recenzowanych.

### Cited Findings
- **Ramdya lab (EPFL)**: NeuroMechFly v2/flygym; 2026 w publikacjach: koordynacja czyszczenia z konektomem (Nature Communications), przegląd neuromechanicznych cyfrowych bliźniaków (arXiv, w recenzji), praca bioRxiv o manipulacji obiektami u Drosophila — [EPFL](https://www.epfl.ch/labs/ramdya-lab/?p=484) — CZĘŚCIOWO POTWIERDZONE
- **Turaga lab (Janelia) / DeepMind**: flybody (Nature VII 2025) — [repo](https://github.com/TuragaLab/flybody); inne kierunki konektom-ograniczone (Lappalainen i in. 2024, wzrok) — wg poprzedniej notatki.
- **Sussex / Brains on Board** (Philippides, Nowotny, Graham; partnerzy: Sheffield, Queen Mary): program EPSRC; cel: autonomiczny latający robot z nawigacją i uczeniem na wzór pszczoły; wyniki: nawigacja wzrokowa na pokładzie robota; GeNN do symulacji. Źródła z lat 2016-2021, status 2026 BRAK DANYCH. — [Sussex](https://www.sussex.ac.uk/research/centres/ai-research-group/showcase/brains_on_board), [Frontiers GeNN](https://www.frontiersin.org/journals/neuroinformatics/articles/10.3389/fninf.2021.659005/pdf) — POTWIERDZONE (istnienie), status CZĘŚCIOWO
- **Webb lab (Edinburgh)**: model zakotwiczony anatomicznie dla integracji ścieżki w mózgu pszczoły z konektomu/anatomii, testowany na symulowanej pszczole i robocie (Stone i in., Current Biology 2017); styczeń 2026: Lu i Webb, preprint o nawigacji "point-goal" inspirowanej owadami (zabstrahowane modele, nie konektom) — [arXiv 2601.16806](https://arxiv.org/html/2601.16806), [ScienceDaily 2017](https://sciencedaily.com/releases/2017/10/171005125022.htm) — POTWIERDZONE (praca 2017); brak pracy 2025-26 "konektom centralnego kompleksu -> robot" — BRAK DANYCH
- **Sterowanie manipulatorami przez SNN (bez konektomu)**: Traub-Legenstein-Otte (sym., rekurencyjne SNN, do 75 DoF) [arXiv 2104.04064](https://arxiv.org/pdf/2104.04064); sterowanie neuromorficzne ramieniem na DYNAP-SE2 [arXiv 2501.17172](https://arxiv.org/abs/2501.17172v1) (z poprzedniej notatki) — POTWIERDZONE
- **Sandia NERL** (Loihi 2/SpiNNaker 2, konektom muchy na sprzęcie neuromorficznym) — patrz sekcja 1.
- **Zespoły zlecone w zadaniu bez wyników**: Murthy/Seung (Princeton, FlyWire), Litwin-Kumar (Columbia), TU Delft MAVLab, INI Zurich, Manchester, Heidelberg (BrainScaleS), Shiu/Scott (Berkeley) — w tej rundzie nie przeszukiwałem ich dorobku robotycznego; z wiedzy własnej: Princeton/FlyWire = konektom i Codex; Shiu (autor modelu LIF, dziś współpracownik Eon wg poprzedniej notatki); reszta BRAK DANYCH.
- **State of Brain Emulation Report 2025** (Zanichelli, Schons, Freeman, Shiu, Arkhipov; arXiv 2510.15745): przegląd trzech filarów — neural dynamics, connectomics, emulation/embodiment; w pełnym tekście nie czytałem (plik >10 MB) — [arXiv abs](https://arxiv.org/abs/2510.15745) — POTWIERDZONE (istnienie, struktura), treść szczegółowa BRAK DANYCH

### Inferences
- HIPOTEZA: luka akademicka — brak grupy, która traktuje "przeniesienie obwodu muchy do taniego robota" jako programu badawczego z kontrolami (przeplatanie, ablacja) na sprzęcie.

### Gaps
- Pełne przeszukanie dorobku TU Delft MAVLab, INI, Heidelberg, Litwin-Kumar — niewykonane (limit narzędzi).

---

## 4. Tabela zbiorcza

| Nazwa | Zespół | Rok | Technologia | Dane biologiczne | Osiągnięcia | Ograniczenia | Status | Link | Etykieta |
|---|---|---|---|---|---|---|---|---|---|
| EBRAINS NRP | HBP/EBRAINS | 2017- | platforma sim + SNN + roboty (Gazebo/NEST wg mojej wiedzy) | ogólne; brak konektomu muchy | otwarta usługa online/lokalna; roboty z SNN | funkcje szczegółowe niejawne; EBRAINS 2.0 do 12/2026 | działa, przyszłość niepewna | [link](https://www.ebrains.eu/tools/nrp) | CZĘŚCIOWO |
| NEST / Arbor | NEST Initiative / Arbor | -2026 | symulatory SNN/wielokomp. | — | NEST 3.9+, SPEC 2026 | brak modułu konektomu->robot | aktywne | [link](https://ebrains.eu/news-and-events/2026/nest-in-the-new-spec-benchmark-suite) | CZĘŚCIOWO |
| Shiu LIF (Drosophila_brain_model) | Shiu i in. | 2024 | Brian2 LIF | FlyWire 630/783 | silencing/aktywacja; Nature 2024 | brak ciała | MIT, 399 gw. | [link](https://github.com/philshiu/Drosophila_brain_model) | POTWIERDZONE |
| FlyWire Codex / neuPrint | Princeton / Janelia | 2023- | portale i bazy | FlyWire, MaleCNS, hemibrain | eksport, wyszukiwanie | brak symulacji | aktywne | [link](https://codex.flywire.ai/) | POTWIERDZONE |
| NeuroMechFly v2 / flygym | Ramdya, EPFL | 2024 | MuJoCo | morfologia muchy; opcj. konektom wzrokowy | Nature Methods | tylko sim | aktywne | [link](https://actu.epfl.ch/news/simulating-how-fruit-flies-see-smell-and-navigat-7) | POTWIERDZONE |
| flybody | Janelia/DeepMind | 2025 | MuJoCo + RL | zachowanie z wideo, nie konektom | Nature 2025 | nie spajkowe, tylko sim | repo | [link](https://github.com/TuragaLab/flybody) | POTWIERDZONE |
| Eon "embodied fly" | Eon Systems | 2026 | Shiu LIF + NeuroMechFly | FlyWire | demo wielu zachowań | zamknięte, sim, ręczny interfejs DN | seed 3,5 M USD | [link](https://eon.systems/updates/embodied-brain-emulation) | POTWIERDZONE |
| malecns-embodied-fly | Ryans-sS (indywidualnie) | 2026 | Codex fork + LIF + flygym | FlyWire 783 + MaleCNS | testy z kontrolami | sim; model != dane | repo | [link](https://github.com/Ryans-sS/malecns-embodied-fly) | POTWIERDZONE |
| Fly Brain Bridge / FlyDrones | hobbyści | 2026 | LIF MaleCNS -> kwadruped / dron | MaleCNS | otwarty kod | sprzęt niepotwierdzony | repo | patrz poprz. notatka | CZĘŚCIOWO |
| connectocopter i in. | hobbyści | 2026 | LIF GPU + MuJoCo/ViZDoom | FlyWire | kontrola przeplotem (19/20 vs 4/20) | sim, bez recenzji | repo | [link](https://github.com/TheJustas228/connectocopter) | CZĘŚCIOWO |
| BAAIWorm | PKU + BAAI | 2024 | HH-like + SPH ciało | C. elegans | pętla zamknięta, chemotaksja | 1 zachowanie, sim | otwarte | [link](https://gitee.com/garrychengitee/BAAIWorm) | POTWIERDZONE |
| OpenWorm (c302, Sibernetic) | OpenWorm | 2011- | NeuroML + SPH | C. elegans (Cook 2019) | pełny 302-neuronowy framework | wydajność/walidacja | aktywne w 2026 (mirror) | [link](https://docs.openworm.org/projects/) | CZĘŚCIOWO |
| Sandia Loihi 2 fly | Sandia NERL | 2025 | Loihi 2 (12 chipów) | FlyWire | >100x szybciej niż konwenc. | brak ciała/robota | preprint | [link](https://arxiv.org/pdf/2508.16792) | POTWIERDZONE |
| GeNN / Brains on Board | Sussex + Sheffield + QMUL | 2014-2024 | GPU SNN, Jetson | mózg pszczoły/mrówki (anatomia) | robot jeżdżący po trasie | nie konektom, nie Drosophila | akademickie | [link](https://www.sussex.ac.uk/research/centres/ai-research-group/showcase/brains_on_board) | CZĘŚCIOWO |
| Webb lab | Edinburgh | 2017-2026 | modele anatomicznie ograniczone | pszczoła | robot + sym. | abstrakcja | akademickie | [link](https://sciencedaily.com/releases/2017/10/171005125022.htm) | POTWIERDZONE |
| Nengo / ABR | ABR Waterloo | 2012- | NEF, kompilacja na chipy | — | seed I 2026 | focus na edge AI | firma | [link](https://www.preqin.com/data/profile/asset/applied-brain-research-inc-/785003) | CZĘŚCIOWO |
| Thousand Brains / Monty | Numenta -> non-profit | 2025 | sensorimotor, neokorteks | — | open source; 2,69 M USD (Gates) | nie konektom | aktywny | [link](https://www.businesswire.com/news/home/20250107503206/en/) | POTWIERDZONE |
| Cortical Labs CL1 | Cortical Labs | 2022- | żywe neurony | ludzkie neurony in vitro | produkt 35 000 USD | niejasne finanse | rynek | [link](https://itbrief.com.au/story/cortical-labs-cl1-commercial-milestone-after-aud-245k-grant) | CZĘŚCIOWO |
| FinalSpark | FinalSpark | 2024 | organoidy | in vitro | zdalny dostęp | niejasne finanse | rynek | patrz sekcja 2 | CZĘŚCIOWO |
| Opteran | Opteran | 2019- | algorytmy inspir. pszczołą | anatomia owada (bez konektomu) | roboty/drony | zamknięte | firma | [link](https://theengineer.co.uk/articles/opteran-secures-21m-to-solve-autonomy-in-robotics) | CZĘŚCIOWO |
| Liquid AI | MIT spin-out | 2023- | liquid NN / LFM | inspir. C. elegans | 250 M USD | niezwiązane z konektomem muchy | firma | [link](https://dealroom.co/companies/liquid-ai/) | CZĘŚCIOWO |
| SpiNNcloud / Innatera / BrainChip / SynSense / Prophesee / iniVation | firmy sprzętowe | różne | chipy/czujniki neuromorficzne | — | dostawcy sprzętu | brak narzędzi konektomowych | rynek | [przegląd](https://abovea.tech/insights-strategies/neuromorphic-computing-startups/) | CZĘŚCIOWO |
| Carboncopies | non-profit | 2010- | roadmap WBE | — | Roadmap, wyzwanie | nie narzędzie | aktywna | [link](https://carboncopies.org/Research/Roadmap/About/) | POTWIERDZONE |
| hwihwalab HF repo | nieznany | 2026? | ? | MaleCNS? | ? | 401 | niedostępne | [link](https://huggingface.co/hwihwalab/malecns-connectome-robotics-2026) | BRAK DANYCH |

---

## 5. Macierz możliwości (a) ekstrakcja obwodu, (b) konwersja do SNN, (c) modyfikacja/ablacja, (d) kompozycja cross-circuit/cross-species, (e) ciało w sim fizycznym, (f) robot fizyczny

Legenda: T = tak (potwierdzone w źródle), C = częściowo/ręcznie/ad hoc, N = nie, ? = brak danych. Ocena wynika z przeczytanych README/abstraktów; to moja klasyfikacja (HIPOTEZA tam, gdzie oparta na opisie wtórnym).

| Projekt | a | b | c | d | e | f |
|---|---|---|---|---|---|---|
| EBRAINS NRP | N | C (SNN z innych źródeł) | C | ? | T | C (chipy/roboty wg opisu) |
| Shiu LIF repo | C (lista neuronów) | T | T (silencing/aktywacja) | N | N | N |
| FlyWire Codex / neuPrint | T (zapytania, podgrafy) | N | N | N | N | N |
| flygym / NeuroMechFly | N | C | C | N | T | N |
| flybody | N | N (RL, nie SNN) | C | N | T | N |
| Eon | C (zestaw ~DN) | T | ? | ? | T | N (wg znalezionych źródeł) |
| malecns-embodied-fly | C | T | C (arms kontrolne) | N | T | N |
| Fly Brain Bridge | C | T | C | N | N (fizyczny sprzęt, ale niepotwierdzony) | C (kwadruped, niepotwierdzony) |
| FlyDrones | C | T | ? | N | N | C (nie flight-tested) |
| connectocopter | C | T | T (przeplot) | N | T | N |
| BAAIWorm | N (cały C. elegans) | T | C | N | T | N |
| OpenWorm | N | T | C | N | T | N |
| Sandia Loihi 2 fly | N (cały) | T (na chipie) | ? | N | N | N |
| GeNN + Brains on Board | N | T | C | N | C | T (Quanser Q-car, Jetson) |
| Nengo | N | T | T | C | C | C (przez NRP/ chipy) |
| Cortical Labs / FinalSpark | n/d | n/d | n/d | n/d | n/d | C (nie znaleziono robota) |

Wniosek z macierzy: (a)+(b)+(c)+(d)+(e)+(f) w jednym narzędziu — żaden wiersz; kolumna (d) praktycznie pusta; (f) tylko w pracach spoza konektomu muchy (GeNN/Sussex) oraz w niepotwierdzonych hobbystycznych repo.

---

## 6. Analiza: najbliższe platformy i luka

### Takeaway
Luka istnieje, ale wąska i mało "ochronna": prawie każdy element jest otwarty, a kilku hobbystów pokazało pętle konektom-LIF-ciało w sim w 2026. Wyróżnik FlyMind może leżeć tylko w kombinacji: narzędzia ekstrakcji i modyfikacji obwodów (z kontrolami: ablacja/przeplot) + kompozycja obwodów różnych źródeł + zwalidowane wdrożenie na tanim, powtarzalnym robocie.

### Inferences (z etykietami)
- **Najbliższy pod względem funkcji end-to-end: Eon Systems** — POTWIERDZONE co do istnienia i sim; HIPOTEZA co do tego, że jego wewnętrzne narzędzia mogłyby objąć modyfikację/kompozycję (brak jawnych danych); zamknięty, ukierunkowany na emulację mózgu myszy, nie na robotykę.
- **Najbliższy pod względem otwartości: kombinacja Shiu repo + flygym + fork Codex (`malecns-embodied-fly`)** — POTWIERDZONE; to de facto "FlyMind lite" w sim, wykonywany przez jedną osobę. Konsekwencja: samo "konektom -> LIF -> ciało MuJoCo" nie jest wyróżnikiem.
- **Najbliższy pod względem infrastruktury robotycznej: EBRAINS NRP** — CZĘŚCIOWO POTWIERDZONE; dojrzała platforma neurorobotyczna, ale w 12/2026 kończy się finansowanie EBRAINS 2.0 (następca BRAK DANYCH), brak dowodów użycia konektomu Drosophila.
- **Najbliższy pod względem sprzętu fizycznego z biologią owadzią: Sussex/GeNN i Opteran** — POTWIERDZONE; ale modele zabstrahowane (ciało grzybkowate), nie konektom neuron-po-neuronie.
- **Luki, które znalazłem (HIPOTEZA, nie "dowód braku")**:
  1. brak narzędzia do kompozycji obwodów z różnych konektomów/gatunków (mucha + C. elegans + mysz);
  2. brak narzędzia z wbudowanymi kontrolami (przeplot zachowujący stopnie, ablacja, wymiana znaków synaps) jako standard — występuje tylko lokalnie, np. connectocopter;
  3. brak udokumentowanej, walidowanej pętli na robocie z enkoderami (manipulator);
  4. dane o znakach synaps (predykcja neuroprzekaźnika) pozostają słabością wspólną wszystkich projektów (potwierdzone w poprzedniej notatce i w README forka Codex: dynamika błon, progi i gait to założenia).
- **Ryzyka dla narracji "nikt tego nie robi"**: hobbyści wchodzą szybko (wiele repo w 2026), Eon ma finansowanie i zespół z autorem modelu Shiu, NRP dostarcza bazy; BAAIWorm pokazuje, że konkurent akademicki może wydać pełny otwarty stos (dla C. elegans).
- **Czego nie zbadano**: Bitbucket NRP, pełne README Fly Brain Bridge/FlyDrones po aktualizacji, YouTube/Hackaday/Discord, prace konferencyjne ICRA/IROS/CoRL 2026, zawartość HF repo hwihwalab.

### Gaps
- Wszystkie oceny "nikt nie ma X" wynikają z ograniczonego wyszukiwania (US-only, ok. 25 wywołań); wymagają potwierdzenia ręcznego przed jakąkolwiek publiczną tezą o "pierwszeństwie".
