# Rynek i argument inwestorski dla "sterowania robotem inspirowanego mózgiem / konektomem" (pitch licealisty, konkurs szkolny, jurorzy biznesowi, sponsorzy typu ORLEN) — stan na 3 listopada 2026

Uwaga metodologiczna: wiele źródeł poniżej to wtórne agregatory/prasa branżowa (oznaczone). Raporty rynkowe (MarketsandMarkets, Grand View itd.) to prognozy komercyjne, nie fakty. Dane z lat 2022–2024 oznaczone jako starsze.

## 1. Rynek obliczeń neuromorficznych, gracze i argument energetyczny

### Takeaway
Prognozy rynku neuromorficznego na 2030 rozjeżdżają się o ponad rząd wielkości (od ok. 0,3 mld USD do ok. 20 mld USD), więc w pitchu trzeba podać zakres i zaznaczyć, że to szacunki. Argument energetyczny jest realny na poziomie układów (IBM, Intel, Innatera), ale to deklaracje producentów na wybranych benchmarkach; realne przychody firm neuromorficznych są wciąż małe (BrainChip 2025: 1,89 mln USD).

### Cited Findings
- Prognozy rynku na 2030 różnią się o rząd wielkości: Report Prime ok. 314 mln USD (CAGR 70,3% 2022–2030, dane starsze), MarketsandMarkets 1,325 mld USD (z bazy 20,9 mln USD w 2023), Allied Market Research ok. 8,58 mld USD, IndustryARC 8,49 mld USD, Grand View Research 20,27 mld USD (CAGR 19,9% 2024–2030); zakresy i definicje raportów różnią się (chip vs szeroki rynek) — [MarketsandMarkets](https://www.marketsandmarkets.com/Market-Reports/neuromorphic-chip-market-227703024.html); [Allied Market Research](https://www.alliedmarketresearch.com/neuromorphic-computing-market); [Grand View Research](https://www.grandviewresearch.com/press-release/global-neuromorphic-computing-market); [Report Prime](https://www.reportprime.com/neuromorphic-computing-r11603); [IndustryARC](https://www.industryarc.com/report/17070/neuromorphic-computing-market) (liczby ze streszczenia wyszukiwarki; nie otwierałem pełnych raportów).
- Dane centrów danych (IEA, źródło pierwotne): zużycie energii elektrycznej przez centra danych w 2024 ok. 415 TWh (ok. 1,5% światowego zużycia; USA 45%, Chiny 25%, Europa 15%); prognoza bazowa ok. 945 TWh w 2030 (mniej więcej podwojenie) i ok. 1 200 TWh w 2035; zakres 700–1 700 TWh w 2035 zależnie od scenariusza; scenariusz wysokiej efektywności daje 2035 o 20% niżej; AI to "najważniejszy czynnik" wzrostu, ale centra danych to ok. 1/10 wzrostu globalnego popytu na prąd do 2030 — [IEA, Energy and AI, Executive summary](https://www.iea.org/reports/energy-and-ai/executive-summary).
- IEA dodaje stronę pozytywną: AI w przemyśle mogłaby zaoszczędzić energię rzędu rocznego zużycia Meksyku, a wykrywanie usterek AI skraca przerwy w sieci o 30–50%; szeroki użytek istniejących rozwiązań AI mógłby obniżyć emisje związane z energią o ok. 5% w 2035, z zastrzeżeniem efektu odbicia (rebound) — [IEA, Energy and AI](https://www.iea.org/reports/energy-and-ai/executive-summary).
- Intel Hala Point (kwiecień 2024, starsze): 1152 procesory Loihi 2, do 1,15 mld neuronów i 128 mld synaps, maks. 2 600 W; deklarowane >15 bilionów operacji 8-bit/s/W na sieciach głębokich; do 100x mniej energii i 50x szybciej na problemach optymalizacyjnych względem CPU/GPU (deklaracja Intela, nie ogólna dla inferencji); to prototyp badawczy, nie produkt komercyjny, wdrożony w Sandia National Laboratories — [SiliconANGLE](https://siliconangle.com/2024/04/17/intel-unveils-powerful-brain-inspired-neuromorphic-chip-system-energy-efficient-ai-workloads/); [VentureBeat](https://venturebeat.com/ai/intel-unveils-hala-point-its-second-generation-neuromorphic-computing-system).
- IBM NorthPole (2023, starsze): 25x większa efektywność energetyczna (kl./W) niż GPU 12 nm na ResNet-50; wobec Nvidia H100 (4 nm) ok. 5x (źródło wtórne); w późniejszych testach IBM na LLM 3 mld parametrów 72,7x lepsza efektywność niż najszybszy GPU pod względem opóźnienia; NorthPole nie ma dostępu do pamięci zewnętrznej — [TechRadar](https://www.techradar.com/pro/inspired-by-the-human-brain-how-ibms-latest-ai-chip-could-be-25-times-more-efficient-than-gpus-by-being-more-integrated-but-neither-nvidia-nor-amd-have-to-worry-just-yet); [IBM Research](https://research.ibm.com/blog/northpole-llm-inference-results).
- Innatera (Delft, spin-off TU Delft, 2018): Series A łącznie 21 mln USD (najpierw ok. 16 mln USD / ok. 15 mln EUR ogłoszone w marcu 2024 + ok. 5 mln USD rozszerzenia; inwestorzy m.in. Innavest, InvestNL, EIC Fund); deklaruje (własne twierdzenie) 500x mniej energii i 100x szybciej niż konwencjonalne podejścia do przetwarzania danych z czujników; cel: miliard urządzeń do 2030. Daty rozszerzenia są niespójne między źródłami (2024 vs 2025) — [Unite.ai](https://www.unite.ai/innatera-secures-21m-to-drive-neuromorphic-ai-to-1-billion-devices-by-2030); [DatacenterDynamics](https://datacenterdynamics.com/en/news/neuromorphic-processor-startup-innatera-raises-21m); [Innatera news](https://innatera.com/news).
- SynSense (Chiny/Szwajcaria): CB Insights podaje ok. 43,9 mln USD zebrane w 14 rundach, ostatnia runda sierpień 2024 (agregator, wartości przybliżone) — [CB Insights](https://www.cbinsights.com/company/synsense/financials).
- BrainChip (Akida, ASX; dane z agregatorów/prasy): przychód 2025 wzrósł o 374% do 1,89 mln USD (z 0,398 mln USD w 2024), strata netto ok. 20,5 mln USD; w listopadzie 2025 emisja ok. 37 mln AUD, w grudniu 2025 ogłoszone 25 mln USD finansowania; I półrocze 2026 przychód 1,22 mln USD, strata 12,0 mln USD (źródło: Motley Fool Australia) — [Business Wire (BrainChip)](https://www.businesswire.com/news/home/20251210514718/en/BrainChip-Announces-25-Million-USD-Funding-Ahead-of-CES-to-Power-Next-Gen-Edge-AI); [Motley Fool AU](https://www.fool.com.au/2026/08/26/brainchip-shares-half-year-results-show-revenue-up-loss-widens/).
- Przegląd literatury o sterowaniu robotami na SNN wskazuje efektywność energetyczną, szybkość i obliczenia jako główne motywacje, ale traktuje oszczędność energii jako obietnicę, a nie rozstrzygnięty wynik; brak kompleksowego przeglądu — [Frontiers in Neurorobotics 2018 (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6043678/).

### Inferences
- Uczciwy pitch: "rynek neuromorficzny to dziś dziesiątki–setki mln USD przychodów (BrainChip 1,9 mln USD), a prognozy 2030 wahają się 0,3–20 mld USD" — jurorzy biznesowi docenią podanie zakresu zamiast jednej liczby.
- Argument energetyczny należy formułować jako "układy neuromorficzne mogą" i wskazywać, że to benchmarki producentów; projekt licealisty (symulacja SNN na zwykłym komputerze/SO-101) sam nie dowodzi oszczędności energii.
- Powiązanie z IEA jest mocne medialnie (podwojenie do 945 TWh), ale IEA zaznacza, że centra danych to ok. 1/10 wzrostu popytu — nie przesadzać z "AI pożre świat".

### Gaps
- Nie sprawdziłem pełnych treści raportów rynkowych (tylko streszczenia z wyszukiwarki) — definicje rynku niepotwierdzone.
- Brak niezależnych (nie-producenckich) pomiarów oszczędności energii SNN na rzeczywistych robotach; nie znalazłem krytycznego przeglądu "hype vs rzeczywistość".
- Brak potwierdzonych danych o funding SynSense z pierwotnego źródła.

## 2. Boom embodied AI / modele fundamentowe dla robotów i tani sprzęt (SO-101, LeRobot)

### Takeaway
Kapitał w robotyce ogólnego przeznaczenia jest ogromny (Figure 39 mld USD wyceny, Physical Intelligence ok. 11 mld USD i rozmowy o ok. 20 mld), co daje kontekst "robotyka to gorący temat". Jednocześnie SO-101 (ok. 100–130 USD) pokazuje, że sprzęt do eksperymentów jest dostępny dla uczniów; mały, tani sterownik to nisza "edge", nie bezpośredni konkurent dużych modeli.

### Cited Findings
- Figure AI: Series C ogłoszona 16 września 2025, ponad 1 mld USD zadeklarowanego kapitału przy wycenie post-money 39 mld USD (poprzednio 2,6 mld USD w 2024); prowadził Parkway Venture Capital; inwestorzy m.in. Brookfield, NVIDIA, Intel Capital, Qualcomm Ventures — [The Robot Report](https://www.therobotreport.com/figure-ai-raises-1b-in-series-c-funding-toward-humanoid-robot-development/); [Intel Capital](https://www.intelcapital.com/?p=11952).
- Physical Intelligence: według trackerów Series C 21 maja 2026, 1,05 mld USD przy wycenie ok. 11 mld USD (źródła niespójne co do dokładnej kwoty/daty; ok. 11,5 mld w innych); w październiku 2026 doniesienia (Bloomberg przez wtórne portale) o wstępnych rozmowach o co najmniej 1 mld USD przy wycenie ok. 20 mld USD — nieogłoszone; spółka nie ma jeszcze przychodów wg tych doniesień; Skild AI ok. 14 mld USD w styczniu 2026 — [Dealroom](https://dealroom.co/news/127095-robot-ai-startup-physical-intelligence-seeks-1b-at-11b-valuation/); [Wikipedia: Physical Intelligence](https://en.wikipedia.org/wiki/Physical_Intelligence_Inc.); [Bloomberg Government (nagłówek)](https://news.bgov.com/artificial-intelligence/ai-robotics-lab-in-talks-to-nab-1-billion-at-11-billion-value).
- Hugging Face SO-101: otwartoźródłowe, drukowane 3D ramię; wg HF baza ok. 100 USD, z drukiem i silnikami ok. 130 USD; w praktyce 100–500 USD zależnie od dostawcy i ceł; kamera osobno; teleoperacja wymaga dwóch ramion; część ekosystemu LeRobot — [TechCrunch (kwiecień 2025)](https://techcrunch.com/2025/04/28/hugging-face-releases-a-3d-printed-robotic-arm-starting-at-100); [Gigazine](https://gigazine.net/gsc_news/en/20250501-hugging-face-robotic-arm).
- Konektom muchy: FlyWire, Nature (październik 2024, tom 634) — diagram połączeń 139 255 neuronów i ok. 54,5 mln synaps dorosłej samicy Drosophila; dane dostępne publicznie (Codex); konsorcjum >146 laboratoriów w 122 instytucjach; wcześniejszy hemibrain ok. 20 tys. neuronów i 14 mln synaps — [Princeton](https://www.princeton.edu/index.php/news/2024/10/02/mapping-entire-fly-brain-step-toward-understanding-diseases-human-brain); [PMC (Nature paper)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842).

### Inferences
- Dobre otwarcie: "pieniądze płyną do robotów, ale do dużych modeli; my badamy drugi biegun — malutki, interpretowalny sterownik z prawdziwego mózgu, na sprzęcie za ~130 USD".
- Nie porównywać się do Physical Intelligence/Figure (inna skala i cel); to kontekst, nie konkurencja. Wyceny rynkowe nie są dowodem na model biznesowy (PI bez przychodów).
- Wartość projektu to otwarty, powtarzalny demonstrator naukowo-edukacyjny, nie produkt.

### Gaps
- Nie znalazłem potwierdzenia z pierwotnych komunikatów PI dla rundy z maja 2026; liczby wymagają weryfikacji (TechCrunch/Bloomberg).
- Brak liczb o sprzedaży SO-101/LeRobot (liczba użytkowników, przychody HF).

## 3. Startupy inspirowane owadzim/biologicznym mózgiem (Opteran, Cortical Labs, FinalSpark)

### Takeaway
Najbliższym komercyjnym analogiem jest Opteran (Sheffield): "Natural Intelligence" z mózgu owada dla unikania kolizji i nawigacji, finansowanie rzędu kilkunastu–kilkudziesięciu mln USD — ale zbiór danych o jego rundach po 2022 jest niepewny. Cortical Labs i FinalSpark to biokomputery z żywych neuronów (inna technologia, nie SNN na krzemie).

### Cited Findings
- Opteran: spin-out University of Sheffield (osiem lat badań prof. Jamesa Marshalla i dr. Alexa Cope'a nad mózgami owadów); seed 2,1 mln GBP (listopad 2020; IQ Capital, Episode1, Join, Seraphim; wcześniej grant CCF); runda 12 mln USD w czerwcu 2022 prowadzona przez Join Capital (+ IQ Capital, Northern Gritstone, Seraphim, Episode 1, Schauenburg) — [The Engineer](https://www.theengineer.co.uk/content/news/opteran-secures-21m-to-solve-autonomy-in-robotics/); [Tech.eu](https://tech.eu/2022/06/24/opteran-weaves-in-12-million-to-develop-ai-driven-by-brain-biomimicry-inspired-by-insects); [Edge AI Vision](https://www.edge-ai-vision.com/2022/06/opteran-secures-12-million-to-create-a-new-standard-for-autonomous-machines/).
- Opteran, późniejsze dane: Dealroom wymienia lipiec 2025 ($2,9 mln, wycena $60 mln, nieujawnieni inwestorzy), PitchBook "Series A" z 14.11.2024, CB Insights łącznie ok. 24,7 mln USD (inne źródła ok. 15 mln) — niespójne, agregatory; piloty u klientów w USA, RPA i Europie (kolizje i nawigacja w cobotach, dronach, robotach górniczych) — [Dealroom](https://dealroom.co/companies/opteran/); [PitchBook](https://pitchbook.com/profiles/company/434910-61); [CB Insights](https://www.cbinsights.com/company/opteran/financials).
- Cortical Labs (Australia): komputer biologiczny CL1 ogłoszony w marcu 2025 za 35 000 USD (rack 30 szt. po 20 000 USD); finansowanie niespójne w źródłach (ok. 10–15 mln USD; Horizons Ventures); kwiecień 2026 granty/kamienie milowe (grant 245 tys. AUD) — [DatacenterDynamics](https://datacenterdynamics.com/en/news/australian-startup-cortical-labs-unveils-worlds-first-commercial-biological-computer); [TechRadar](https://www.techradar.com/pro/a-breakthrough-in-computing-cortical-labs-cl1-is-the-first-living-biocomputer-and-costs-almost-the-same-as-apples-best-failure); [IT Brief](https://itbrief.co.uk/story/cortical-labs-cl1-commercial-milestone-after-aud-245k-grant).
- FinalSpark (Szwajcaria): od 2023 pierwsze laboratorium biokomputingu oferujące zdalny dostęp do sprzętu; agregator podaje "25 mln USD seed, luty 2026", ale wpis jest niejednoznaczny (nie potwierdzone) — [Ross Dawson (przegląd)](https://rossdawson.com/?p=24561); [Caplight](https://www.caplight.com/company/biocomputing).

### Inferences
- Opteran jest najlepszym punktem odniesienia: pokazuje, że inwestorzy VC finansują "mózg owada → autonomia robotów" i że klienci (cobot, dron, górnictwo) istnieją na etapie pilotaży. Jednak to firma z zespołem i latami R&D; licealista nie powinien sugerować równorzędności produktowej.
- Dwa różne pitchy: (a) Opteran = software/IP do autonomii; (b) Cortical Labs/FinalSpark = sprzęt biologiczny/badawczy (cena 35 tys. USD pokazuje, że rynek B2B-naukowy płaci).

### Gaps
- Brak potwierdzonych (pierwotnych) kwot finansowania Opteran po 2022 i FinalSpark.
- Brak danych o przychodach Opteran/Cortical Labs.

## 4. Wiarygodne zastosowania "małego mózgu, efektywne sterowanie" (rolnictwo, inspekcje, protezy, edukacja)

### Takeaway
Najlepiej udokumentowane rynki: roboty inspekcyjne w ropie/gazie/chemii (ANYbotics; relewantne dla ORLEN), roboty rolnicze (Carbon Robotics; ale też upadłość Naïo jako ostrzeżenie) i edukacyjne zestawy neuro (Backyard Brains, mała skala). Protezy: nie znalazłem w tym przebiegu źródeł — luka.

### Cited Findings
- ANYbotics (Zurych, czworonogi ANYmal): Series B maj 2023, 50 mln USD (Walden Catalyst, NGP Capital, Bessemer, Aramco Ventures, Swisscom Ventures); ANYmal X (Ex-proof) przyciągnął zamówienia/rezerwacje >150 mln USD od firm ropy, gazu i chemii; wśród klientów m.in. PETRONAS, Shell, SLB, Siemens Energy, BASF; pojedyncze źródło (getcoai) mówi o rundzie ponad 127 mln EUR — niezweryfikowane — [Business Wire](https://www.businesswire.com/news/home/20230516005081/en/ANYbotics-Secures-50M-Series-B-Funding-to-Revolutionize-Industrial-Inspection-with-its-Four-Legged-Robotic-Workforce); [EU-Startups](https://www.eu-startups.com/2023/05/zurich-based-anybotics-secures-e46m-series-b-round-to-conquer-the-industrial-world-with-its-four-legged-workforce/); [Offshore Magazine](https://www.offshore-mag.com/business-briefs/equipment-engineering/article/14294000/anybotics-secures-50m-in-funding-to-develop-robotics).
- ORLEN i inspekcje: ORLEN testował drona do ochrony zakładu w Płocku (2019), uruchomił monitoring rurociągu Wrocław–Ostrów Wlkp. dronem hybrydowym (ok. 180 km misji w pilotażu, data niepodana), w 2022 ogłosił analizy business case dla inspekcji dronowych aktywów (rafineria, petrochemia, energetyka); nie znalazłem informacji o pilotażu robotów naziemnych w Płocku — [ORLEN press 2019](https://www.orlen.pl/en/about-the-company/media/press-releases/archive/2019/december/modern-technologies-improve-the-security-of-orlens-production-plant-in-plock); [Money.pl](https://www.money.pl/gielda/pkn-orlen-wykorzystuje-drona-do-monitorowania-zakladu-w-plocku-6458354826638977a.html); [Bankier](https://www.bankier.pl/wiadomosc/PKN-Orlen-chce-zwiekszyc-wykorzystanie-dronow-8268084.html); [dlapilota.pl](https://dlapilota.pl/wiadomosci/pap/pkn-orlen-uruchomil-monitoring-rurociagu-z-wykorzystaniem-hybrydowego-drona).
- Roboty rolnicze: szacunki rynku znacznie się różnią (ResearchAndMarkets 2026: 21,2 mld USD w 2025 → 25,9 mld USD w 2026; Naïo cytuje 98 mld EUR do 2033 wg Spherical Insights — rozbieżne definicje); Carbon Robotics: Series D 70 mln USD (październik 2024); Naïo (Series A 14 mln EUR w 2020) przeszło przez postępowanie upadłościowe i przejęcie — [FertilizerDaily](https://www.fertilizerdaily.com/20241025-carbon-robotics-secures-70-million-in-series-d-funding-to-enhance-agricultural-robotics/); [FreshPlaza](https://www.freshplaza.com/europe/article/9784595/naio-technologies-targets-sales-of-eur11-million-by-2030/); [FutureFarming](https://www.futurefarming.com/tech-in-focus/field-robots/naio-technologies-relaunched-under-new-ownership/).
- Edukacja neuro: Backyard Brains (Ann Arbor, założone 2009 na U. Michigan): SpikerBox, RoboRoach; 10 000. SpikerBox sprzedany do czerwca 2016; przychód ok. 500 tys. USD po pięciu latach (starsze, regionalne doniesienie); dotacja NIMH SBIR ok. 450 tys. USD; ok. 60 krajów — małe, ale realne przychody z zestawów szkolnych — [Backyard Brains blog](https://blog.backyardbrains.com/2017/05/the-3000000-spike-byb-sales-milestone/); [NIMH SBIR](https://www.nimh.nih.gov/funding/sbir/backyard-brains-innovative-products-to-help-kids-learn-about-neuroscience); [Concentrate Media](https://concentratemedia.com/?p=25088).

### Inferences
- Najsilniejsze dla ORLEN: "inspekcja w strefach zagrożenia wybuchem" (ANYbotics ma ponad 150 mln USD zamówień wstępnych w branży); mały, energooszczędny sterownik dla czujników/robotów na baterii to hipoteza kierunkowa, nieprzetestowana przez projekt.
- Najuczciwsza ścieżka komercyjna dla licealisty: zestaw edukacyjny/otwarty demonstrator (model Backyard Brains) — skala niewielka, ale realna.
- Przestroga dla jurorów: Naïo pokazuje, że robotyka rolnicza bywa trudnym biznesem.

### Gaps
- Protezy/neuroprotezy: nie przeszukano — brak źródeł.
- Brak potwierdzonych liczb o przychodach ANYbotics i o skali rynku inspekcji robotycznych (pierwotne raporty).
- Brak aktualnych (2025–2026) danych Backyard Brains.

## 5. Cele Zrównoważonego Rozwoju (SDG) — jak uczciwie sformułować

### Takeaway
Wiarygodnie mapują się SDG 9 (innowacje, badania — cel 9.5) i SDG 4 (edukacja, jeśli projekt ma realny komponent edukacyjny); SDG 7/13 tylko jako pośrednia, hipotetyczna korzyść (efektywność energetyczna sprzętu); SDG 3 tylko jako długoterminowa nauka o mózgu, nie jako zdrowotny efekt projektu.

### Cited Findings
- SDG 9 brzmi "Build resilient infrastructure, promote inclusive and sustainable industrialization and foster innovation"; cel 9.5: wzmacnianie badań naukowych i zdolności technologicznych, zwiększanie liczby pracowników B+R i wydatków na B+R — [UN SDG 9](https://sdgs.un.org/goals/goal9).
- IEA: centra danych 415 TWh (2024) → ok. 945 TWh (2030) — podstawa do argumentu SDG 7/13 o efektywności obliczeń — [IEA](https://www.iea.org/reports/energy-and-ai/executive-summary).
- Konkurs Explory (FZT) w 2026 przyznaje Nagrody Zrównoważonego Rozwoju po 5 000 zł w kategoriach "Człowiek i społeczeństwo", "Klimat i środowisko", "Gospodarka i bezpieczeństwo" — [Explory, informacja prasowa półfinał 2026](https://explory.pl/wp-content/uploads/Informacja_prasowa_polfinal_2026.pdf).
- FlyWire konektom jest opisywany przez uczelnie jako krok do zrozumienia chorób ludzkiego mózgu — [Princeton](https://www.princeton.edu/index.php/news/2024/10/02/mapping-entire-fly-brain-step-toward-understanding-diseases-human-brain).

### Inferences
- Proponowane sformułowanie: główny SDG 9.5 (badania i innowacje, otwarte narzędzie z danych publicznych), pomocniczo SDG 4 (jeśli powstanie materiał dydaktyczny) oraz "potencjalnie 7/13: kierunek badawczy, nie zmierzony efekt".
- Nie twierdzić "oszczędzamy energię" ani "leczymy" — projekt (symulacja/SNN na ramieniu) tego nie mierzy; wpływ na SDG 3 jest co najwyżej odległy.
- Związek z kategoriami Explory (np. "Gospodarka i bezpieczeństwo") można wykorzystać do dopasowania narracji.

### Gaps
- Nie weryfikowałem pełnych tekstów celów SDG 3, 4, 7, 13 (tylko SDG 9 z UN).

## 6. ORLEN: programy dla startupów i młodych

### Takeaway
ORLEN ma trzy relewantne kanały: Fundacja ORLEN im. Łukasiewicza (programy dla uczniów, m.in. "Inżynierowie Przyszłości" — 100 grantów po 2 000 zł), ORLEN Skylight Accelerator (non-equity, piloty w infrastrukturze ORLEN, ale dla firm/startupów) oraz ORLEN VC (ok. 100 mln EUR, dojrzałe startupy). Dla licealisty realny cel to Fundacja i konkursy, nie VC.

### Cited Findings
- "Inżynierowie Przyszłości" (edycja 2026/2027): dla uczniów szkół ponadpodstawowych; 100 grantów po 2 000 zł na materiały i sprzęt; nagrody w finale do 8 000 zł netto; nabór od 1 września do 9 października 2026 (zamknięty w dniu notatki, 3 listopada 2026); finał: Ogólnopolska Konferencja Naukowa w czerwcu 2027; nauki ścisłe, przyrodnicze, technologia, inżynieria — [Warto Wiedzieć](https://wartowiedziec.pl/polityka-spoleczna/81788-100-grantow-dla-mlodych-naukowcow-po-2-tys-zl-na-wlasne-badania) (źródło wtórne; regulamin: fundacjalukasiewicza.orlen.pl).
- Fundacja ORLEN, inne: stypendium "Mogę więcej" (3 500 zł nieletni / 4 500 zł pełnoletni; nabór do 4 października 2026; wyniki do 10 listopada 2026); "Od cząsteczki do galaktyki" (granty do 25 000 zł dla kół naukowych, nabór październik 2025); stypendia Bona Fide i Łukasiewicza dla studentów — [Warto Wiedzieć: Mogę więcej](https://wartowiedziec.pl/rozwoj-i-fundusze/81832-trwa-nabor-do-programu-moge-wiecej-na-stypendia-przeznaczono-1-mln-zl); [Regulamin Fundacji Łukasiewicza (PDF)](https://fundacjalukasiewicza.orlen.pl/media/2mgkv4qf/2025-11-05-regulamin-programu.pdf).
- ORLEN Skylight Accelerator: 14. runda (kwiecień 2025: nabór 7–28 kwietnia) obejmowała ponad 20 wyzwań (m.in. Industry 4.0, odnawialne źródła, inteligentna infrastruktura energetyczna), start-upy także na etapie PoC/MVP/prototypu; ORLEN pokrywa koszty przygotowania i realizacji pilotażu w warunkach operacyjnych Grupy; strona nie wspomina o udziałach (program non-equity wg wtórnych źródeł) — [ORLEN, 14. runda](https://www.orlen.pl/en/about-the-company/innovations/news/We-have-announced-the-14th-round-of-recruitment-for-the-ORLEN-Skylight-accelerator-program); [ORLEN press kwiecień 2025](https://orlen.pl/en/about-the-company/media/press-releases/2025/April-2025/14th-edition-of-orlen-skylight-accelerator-launched-).
- Skylight, skala: do marca 2026 ponad 1 000 zgłoszonych startupów i ponad 40 projektów pilotażowych (przykłady: fotowoltaika, dynamiczne taryfy); kolejne nabory w 2026 (18 maja–8 czerwca 2026; nabór do 27 września 2026 wg wtórnych wyników) — [xyz.pl](https://xyz.pl/dzieje-sie/orlen-szuka-startupow-w-centrum-biogaz-wodor-i-cyfryzacja-3749); [Enerad](https://enerad.pl/900-startupow-40-pilotazy-orlen-ponownie-zaprasza-innowatorow/) (daty 2026 pochodzą z podsumowania wyszukiwarki; wymagają sprawdzenia na orlen.pl).
- ORLEN VC: fundusz CVC uruchomiony w 2022 z ok. 100 mln EUR; inwestuje bezpośrednio w startupy i pośrednio przez fundusze (np. 10 mln EUR w Emerald Technology Ventures Industrial Fund; Energy Impact Partners); w 2025 m.in. ReVentas (Series A) i OXCCU (Series B); dojrzałe startupy deep-tech/cleantech, nie projekty szkolne — [ORLEN VC](https://vc.orlen.pl/en/about-us); [Gazeta Prawna](https://www.gazetaprawna.pl/biznes/artykuly/10669393,orlen-fundusz-venture-capital-spolki-technologiczne.html); [Inwestycje.pl](https://inwestycje.pl/startupy/orlen-venture-capital-zainwestowal-w-szkocki-startup-reventas/).
- ORLEN sponsoruje główną nagrodę konkursu Explory 2025 (15 000 zł) — [Explory, informacje prasowe](https://explory.pl/wp-content/uploads/Informacja_prasowa_polfinal_2026.pdf) (kwota 2026 niepotwierdzona).

### Inferences
- Języki dla ORLEN: "inspekcja i bezpieczeństwo infrastruktury, energooszczędna elektronika, edukacja STEM" — pasują do wyzwań Skylight (Industry 4.0, inteligentna infrastruktura) i do profilu Fundacji (młodzież STEM).
- Skylight i VC nie są kanałem dla projektu szkolnego bez firmy/zespołu; sensowne "następne kroki" w pitchu: pilotaż w warunkach laboratoryjnych, kontakt z kołem naukowym/uczelnią, aplikacja do Inżynierów Przyszłości w kolejnej edycji.
- Nie wynika z źródeł, że ORLEN inwestuje konkretnie w neuromorficzne sterowanie ani w roboty-owady; wprost tego nie twierdzić.

### Gaps
- Nie znalazłem oficjalnych 2026 wyzwań Skylight ani informacji, czy ORLEN publicznie wskazuje robotykę/AI jako priorytet w 2026 (brak dostępu do pełnej strony ORLEN).
- Nie zweryfikowałem regulaminu "Inżynierowie Przyszłości" (limit wieku, dopuszczalność zespołów/ symulacji).
- Brak "Moje miejsce na Ziemi" — nie sprawdzono.

## 7. Polskie wsparcie młodych innowatorów i konkursy

### Takeaway
Explory (FZT) jest najbardziej adekwatnym konkursem (droga do ISEF w USA, partnerstwo ORLEN, kategorie zrównoważonego rozwoju). Fundusz ZDOLNI (dawniej KFnrD) wspiera uzdolnioną młodzież; Diamentowy Grant dotyczy studentów/doktorantów, nie licealistów.

### Cited Findings
- Explory 2026 (XV edycja): 377 projektów STEAM zgłoszonych, ponad 130 w półfinale; finał Gdynia Explory Week 21–23 października 2026; nagrody zrównoważonego rozwoju po 5 000 zł; konkurs jest drogą na międzynarodowy ISEF (Phoenix, Arizona) — FZT ma krajowe prawa do wysyłania reprezentacji — [Explory, informacja prasowa półfinał 2026](https://explory.pl/wp-content/uploads/Informacja_prasowa_polfinal_2026.pdf); [Explory ISEF](https://isef.explory.pl).
- Krajowy Fundusz na rzecz Dzieci (założony 1981; stowarzyszenie wspierające uzdolnioną młodzież, w tym techniczną; wg jednego źródła nazwa zmieniona na Fundusz ZDOLNI — niepotwierdzone) — [Wikipedia: Polish Children's Fund](https://en.wikipedia.org/wiki/Polish_Children%27s_Fund); [ITwiz](https://itwiz.pl/krajowy-fundusz-na-rzecz-dzieci-zmienia-nazwe-na-fundusz-zdolni/).
- Diamentowy Grant (MNiSW): dla wybitnych studentów lub absolwentów, do 200 000 zł (w tym pensja min. 2 500 zł/mc); 5. edycja — ok. 16 mln zł dla 83 młodych badaczy — nie dla licealistów — [Study in Poland](https://study.gov.pl/news/83-young-researchers-diamond-grants).

### Inferences
- Na dziś (3 listopada 2026) finał Explory 2026 już się odbył (21–23 października); kolejne okazje: edycja Explory 2027, "Inżynierowie Przyszłości" 2027/28, olimpiady i konkursy szkolne.
- Diamentowy Grant należy wskazać tylko jako "przyszła ścieżka po rozpoczęciu studiów".

### Gaps
- Nie sprawdziłem regulaminu Explory 2026/2027 (wymagania, nagroda główna, wymóg wieku), ani aktualnej oferty Funduszu ZDOLNI, ani innych programów (np. Olimpiada Innowacji Technicznych, Fundacja na rzecz Nauki Polskiej).
- Nie sprawdziłem, czy tegoroczny konkurs szkolny ("startup-style") ma własne kryteria — to zależy od organizatora.

---

### Notatka końcowa dla autora raportu (flagi hype vs realizm)
- Hype: prognozy rynku 20 mld USD (Grand View), wyceny Figure/PI, "500x mniej energii" (Innatera), "25x" (IBM NorthPole, starsze GPU), "100x" (Intel, tylko optymalizacja).
- Realizm: przychody BrainChip 1,9 mln USD w 2025; Opteran dopiero piloty; PI bez przychodów; Naïo w upadłości; Backyard Brains przychody rzędu setek tys. USD.
- Projekt licealisty jest badawczo-edukacyjnym demonstratorem na bazie publicznego konektomu (FlyWire, 139 255 neuronów) i taniego sprzętu (SO-101 ~130 USD); nie ma jeszcze dowodu przewagi energetycznej ani produktu — to należy powiedzieć wprost, bo jurorzy zapytają "kto za to zapłaci".
