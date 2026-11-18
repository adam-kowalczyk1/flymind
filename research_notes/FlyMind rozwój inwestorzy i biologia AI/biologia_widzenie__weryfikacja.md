# Weryfikacja: biologia_widzenie.md (2026-11-12)

Metoda: WebFetch na arXiv API, Crossref, Europe PMC, strony producentów oraz odczyt plikow repo. Domyslnie UNVERIFIABLE, gdy nie otworzylem zrodla sam. Nie edytowano oryginalu.

## Poprawki OBOWIAZKOWE dla autora raportu (na gorze)

1. **arXiv 2509.13827 (Colias/LPLC2): usunac "96.1% vs 93.7% LGMD2" jako porownanie.** Abstrakt (otwarty) mowi tylko: "comparable robustness, at success rate of 96.1% in collision detection" wobec modelu locust-inspired. Liczby 93.7% nie potwierdzilem, wiec jest UNVERIFIABLE. Zdanie "LGMD2 could not do" kierunku ucieczki tez nie jest w abstrakcie; zostawic jako REPORTED. Autorzy: Liu, Zhou, Fang, Fu, 17.09.2025. Abstrakt twierdzi tez "first embodiment of an LPLC2 model in embedded vision on a physical mobile robot" i 70 KB.
2. **Lukę w D0 trzeba dopisac.** Raport (sek. 4) przywoluje "LPLC2/LC4 -> DNp01" jako droge zbliżanie -> stop i "D0 PASS". D0 PASS dotyczy LPLC2->DNp04 i LPLC1->DNp03/06/11 (d0_stdout.txt, linie 54-59). Mapa przestrzenna **LC4->DNp01 NIE jest istotna** (L: R=0.18, p=0.33; P: R=0.26, p=0.15). LPLC2->DNp01 jest istotna (R=0.73 i 0.83, p=0.0001). Nie sugerowac, ze D0 potwierdza caly tor do DNp01.
3. **Sumy synaps 4862 i 6362 potwierdzone** (2642+2220 oraz 3782+2580), ale to liczby synaps z danych, nie dowod funkcji "stop". Dopisac, ze DNp01 = hipoteza o wlasciwosci, bez testu w petli.
4. **Zdanie o Loihi 2 (arXiv 2605.00146):** data zlozenia to 30.04.2026 (raport mowi "April 2026": OK). Abstrakt dodatkowo mowi, ze SNN odzyskuja 87-100% dokladnosci ANN przy destylacji, a bez niej traca 11-27%. Raport pisze tylko ogolnie "accuracy lags"; mozna dac te liczby (VERIFIED abstrakt).
5. **Speck "2.7 mW, 0.5% Jetson Nano, 0.02% Intel CPU" (arXiv 2408.16754):** abstrakt tego NIE zawiera (tylko "<8% energii metod konwencjonalnych"; to praca LENS, Science Robotics DOI 10.1126/scirobotics.ads3968). Zostawic jako REPORTED/UNVERIFIABLE, nie cytowac na plakacie.
6. **Opteran, seed GBP 2.1M (2020):** nie znalazlem w otwartych zrodlach (tech.eu podaje tylko USD 12M, 24.06.2022; artykul edge-ai-vision 2021-10 nie podaje ani funduszy, ani 10 kHz, ani <1 W, ani FlowNet2). Te liczby zostaja jako vendor claim REPORTED, zrodlo cytowane (artykul 2021-10) ich nie zawiera: **zmienic cytat na slajdy 2022 lub oznaczyc UNVERIFIABLE.**
7. **Etykiety:** sek. 1-3 sa w calosci REPORTED/UNVERIFIABLE (sam to piszesz), wiec zdanie otwierajace sek. 3 "Lappalainen verified at abstract level" jest OK (zweryfikowane: patrz tabela). Nie podnosic pozostalych do VERIFIED.
8. **Rynek event-cameras (USD 0.18B-8B):** nie nadaje sie do argumentow inwestorskich; zostawic tylko jako zakres i zastrzezenie (juz tak jest). Nie sprawdzono pierwotnych raportow (platne).
9. Nie dopisywac, ze siec muchy dorownuje klasycznemu: fly-eye plan to papier; plakat: "oko = heurystyka koloru, plan oka testowany tylko w symulacji".

## Tabela

| # | Twierdzenie | Werdykt | Poprawna wartosc / sformulowanie | Zrodlo sprawdzone |
|---|---|---|---|---|
| 1 | Gehrig & Scaramuzza Nature 2024: 20 fps RGB + zdarzenia = opoznienie kamery 5000 fps przy przepustowosci 45 fps | CONFIRMED | Abstrakt (Europe PMC): "20 fps RGB", "latency of a 5,000-fps camera", "bandwidth of a 45-fps camera". Tytul pracy: "Low-latency automotive vision with event cameras" (dotyczy motoryzacji, nie robotow-ramion) | Europe PMC REST, DOI 10.1038/s41586-024-07409-w |
| 2 | Paredes-Valles et al., Sci. Robotics 9(90), maj 2024, doi:10.1126/scirobotics.adi0591 | CONFIRMED (metadane) | Vol 9, issue 90, 15.05.2024, Paredes-Valles, Hagenaars, Dupeyroux, Stroobants, Xu, de Croon | Crossref |
| 3 | Ta praca: 200 Hz, 0.94 W idle + 7-12 mW sieci, Loihi, DVS240, 16x16 ROI | UNVERIFIABLE | Szczegoly z wtornych streszczen; nie otwarto pelnego tekstu. Zachowac zastrzezenie "caly system" | brak (publisher zablokowany) |
| 4 | Lappalainen Nature 634, 1132-1140 (2024); 64 typy komorek; 26 badan | CONFIRMED | Nature 634(8036):1132-1140, pierwsza publikacja 11.09.2024; abstrakt: "64 cell types", "26 studies". Tytul: "Connectome-constrained networks predict neural activity across the fly visual system". To wynik neuronaukowy, nie robotyczny (zgodnie z raportem) | Europe PMC REST |
| 5 | "Works better when connectivity is sparse" (Lappalainen) | UNVERIFIABLE | Nie ma w otwartym fragmencie; zrodlo wtorne | brak |
| 6 | arXiv 2509.13827: LPLC2 na Colias, 70 KB, 96.1% | CONFIRMED w czesci, reszta WRONG/UNVERIFIABLE | 96.1% i 70 KB potwierdzone w abstrakcie; "vs 93.7% LGMD2" niepotwierdzone, abstrakt mowi "comparable robustness"; OV7670/Cortex-M4F/72x99/30 fps niepotwierdzone | arXiv API 2509.13827 |
| 7 | Loihi 2 vs GPU, arXiv 2605.00146 (Gamage et al.) | CONFIRMED | Zlozone 30.04.2026; Loihi 2 najnizsza energia na inferencje vs Jetson Orin Nano/Nano B01/Apple M2; Orin Nano wyzsza czestosc inferencji. Dodatkowo 87-100% vs 11-27% spadek dokladnosci | arXiv API |
| 8 | Speck 2.7 mW, 0.5% Jetson Nano, 0.02% CPU (2408.16754) | UNVERIFIABLE | Abstrakt tego nie podaje (LENS: "<8% energii") | arXiv API |
| 9 | GenX320: 320x320, 6.3 um, >140 dB, <150 us, <50 mW, 36 uW tryb | UNVERIFIABLE | PDF producenta nie dal sie odczytac (skompresowane strumienie, zla metadane); liczby jako vendor claim | prophesee.ai PDF (nie odczytany) |
| 10 | IMX636 1280x720, <100 us, moc 50-205 mW | UNVERIFIABLE | Nie otwarto; raport sam zaznacza konflikt zrodel | brak |
| 11 | Rynek event-camera: SNS 2.53B->6.19B, Fortune 8.04B, Mordor 0.27B, Spherical 0.18B | UNVERIFIABLE | Nie otwierano raportow; roznice 3x+ wynikaja z definicji. Nie uzywac w materialach inwestorskich | brak |
| 12 | Opteran: USD 12M, czerwiec 2022 | CONFIRMED | tech.eu 24.06.2022, runda $12M prowadzona przez Join Capital | tech.eu |
| 13 | Opteran: seed GBP 2.1M (2020); 10 kHz <1 W; 2x vs FlowNet2s | UNVERIFIABLE | Cytowany artykul edge-ai-vision 2021-10 tych liczb nie zawiera; zrodlem moga byc slajdy 2022 (nie otwarte) | edge-ai-vision.com 2021/10 |
| 14 | MaleCNS: LPLC2->DNp01 4862, LC4->DNp01 6362 synaps | CONFIRMED | d0_stdout.txt: LPLC2 2642+2220=4862; LC4 3782+2580=6362; plik bio_vision_20261112.md linie 52-53 spojny | /Users/admin/so101_fly_project/flymind/results/bio_advantage/d0_v1/d0_stdout.txt |
| 15 | Rdzen ruchu 47 473 neuronow | CONFIRMED | fly_eye_plan_20261112.md: podsiec A 47 473 neurony, 1 155 853 polaczen, 7 109 349 synaps (wartosc z raportu planu, nie przeliczona przeze mnie z danych) | /Users/admin/so101_fly_project/flymind/reports/fly_eye_plan_20261112.md linie 14, 30 |
| 16 | "D0 PASS for LPLC2->DNp04 spatial maps" | CONFIRMED, ale OVERCLAIM jesli odnosic do toru DNp01 | PASS: LPLC2->DNp04, LPLC1->DNp03/06/11. LC4->DNp01 mapa NIE istotna (p 0.33/0.15); LPLC2->DNp01 istotna | d0_stdout.txt linie 8-22, 53-59 |
| 17 | "~890 kolumn/oko" (z danych) | UNVERIFIABLE (przeze mnie) | Raport bio_vision pisze 892 P/884 L (liczba L1), a w planie oka "1767 L1 z kolumna"; liczby nie sa spojne miedzy plikami; nie sprawdzano w danych | bio_vision linia 78; fly_eye_plan linia 14 |
| 18 | LPLC2 selektywnosc wynika z zadania kolizji (Zhou eLife 2022) | UNVERIFIABLE | Strona eLife nie zaladowala sie; zachowac jako REPORTED | elifesciences.org (blad) |
| 19 | CurvACE PNAS 2013, 630 ommatidiow, 1.75 g | UNVERIFIABLE | Nie otwierano; raport sam zaznacza rozbieznosci | brak |
| 20 | "Brak opublikowanej sieci z konektomu sterujacej robotem" | OVERCLAIM jesli zdanie jest absolutne | Zrodlo to ograniczone wyszukiwanie; napisz "nie znalazlem w moim przegladzie (listopad 2026)" | rozumowanie + wlasne zastrzezenie raportu |

## Przeglad zasad uczciwosci
- Nie znaleziono: sugestii, ze siec muchy bije klasyczna/AI, ani sugestii sprzetowych wynikow. Raport trzyma sie "symulacja", "nie lepsze". OK.
- Ryzyko: sek. 1 dobrze zastrzega energie (FlyMind na M1 Max nie ma korzysci energetycznej). Zostawic.
- Ryzyko: sek. 4 "fair claim is 'the fly wiring does it too'" jest INFERRED/PROPOSED, nie wynik. Utrzymac etykiete.
- Sam raport przyznaje, ze wiekszosc to REPORTED; moja weryfikacja podniosla do CONFIRMED tylko pozycje 1, 2, 4, 7, 12, 14, 15 oraz czesc 6.
