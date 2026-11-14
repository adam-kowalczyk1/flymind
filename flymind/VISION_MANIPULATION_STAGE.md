# FlyMind — etap „wzrok w pętli”: kamera, śledzenie, wzrok + dotyk w jednej sieci (2026-11-10)

Kontynuacja etapu czucia i manipulacji. **Wszystko jest symulacją MuJoCo; fizyczny SO-101 nie był używany.**
Baza: commit `664b611` (etap dotyku, zapisany na początku tej sesji; poprzednia baza `a7344e3`). Pliki tego etapu
**nie są jeszcze zacommitowane**. Poprzedni dokument: `flymind/SENSORY_MANIPULATION_STAGE.md` (bez zmian).

## 0. Najkrótsze podsumowanie

1. **Położenie przedmiotu nie pochodzi już z symulatora.** Robot ma kamerę na chwytaku; z jej klatek i własnych enkoderów
   wyznacza, gdzie leży przedmiot, jak jest obrócony, jak szeroki i jak wysoki. Stan symulatora służy tylko do oceny.
2. **Sieć muchy obraca ramię na przedmiot.** Obraz → LC10a → DNa02 (droga z danych MaleCNS) steruje obrotem bazy, tak jak
   w zweryfikowanej wcześniej pętli V5. Zamiana stron wejścia odwraca ramię od przedmiotu (1/20 zamiast 14–20/20).
3. **Wzrok i dotyk są w jednej sieci** (1931 neuronów: droga wzrokowa + obwód lewej środkowej nogi; w danych DNa02 L ma
   bezpośrednie synapsy na interneurony tej nogi). Sieć steruje dwiema rzeczami: obrotem bazy i szczęką.
4. **Wynik benchmarku z kamerą (135 prób na wariant):** klasyczny 98, sieć wzrok + dotyk 86, sieć sam dotyk (wzrok poza
   siecią) 85, sieć z wyłączonym wzrokiem podczas chwytu 86, sieć + FeCO 80, sam wzrok 0.
5. **Połączenie wzroku z dotykiem w sieci nie daje mierzalnej korzyści w chwytaniu** (86 wobec 85 i 86). Wzrok jest
   potrzebny, żeby trafić w przedmiot; na samą decyzję o zaciśnięciu nie wpływa.
6. **Kontroler klasyczny jest lepszy od sieci** (98 wobec 86; 18 prób wygrywa tylko klasyczny, 6 tylko sieć).
7. **Trzy audyty podważają część wcześniejszych wniosków** (§7–9): po usztywnieniu kontaktu klasyczny ma 101, sieć 84;
   sieci przetasowane z wyrównaną siłą dają 4–102 (sieć z danych 90 mieści się w tym rozrzucie); FeCO działa jak odruch
   oporowy i dlatego osłabia chwyt.
8. **120 Hz nie zostało uruchomione; 5 ms jest nieosiągalne dla tej sieci:** od dotyku do pierwszego impulsu neuronu
   ruchowego mija co najmniej 9 ms czasu modelu. Obliczenia kamera → komenda: mediana 5,8 ms, p99 7,6 ms, maks. 25 ms.

## 1. Co zrobiono w tej sesji (w kolejności)

| Krok | Wynik | Status |
|---|---|---|
| P0: kontrola i commit etapu dotyku | `664b611`, 78 plików, bez push; manifest 68/68 zgodny, 17 plików Etapu 1 bez zmian, 54 powtórzone próby identyczne co do bitu (`results/sensory_manipulation/COMMIT_CHECK_2026-11-10.txt`) | VERIFIED |
| P1: kamera zamiast wyroczni | `vision_manipulation.py`; percept w 100 % prób; test V2: podmiana wartości wyroczni na NaN nie zmienia przebiegu | VERIFIED (symulacja) |
| P1: sieć obraca bazę na przedmiot | DNa02 L−P → obrót bazy; testy śledzenia | VERIFIED (symulacja) |
| P2: jedna sieć wzrok + dotyk | podgraf indukowany z danych, 1931 neuronów; bez wejścia wzrokowego identyczna co do bitu z siecią nogi (test V3) | VERIFIED; korzyść z integracji: FAILED (brak) |
| P3: audyt FeCO | znak i skalowanie sprawdzone; 5 wariantów × 135 prób | VERIFIED (model); przypisanie flex/ext nadal INFERRED |
| P4: fizyka kontaktu | przyczyna wnikania ustalona; wariant sztywny × 2 ramiona | VERIFIED (symulacja) |
| G: tasowania z wyrównaną siłą | 10 instancji × 135 prób | VERIFIED (symulacja) |
| P5: przenoszenie sterowania na sieć | nowe: obrót bazy przy patrzeniu; dojazd, podniesienie, transport, puszczenie nadal klasyczne | PARTIALLY (jedna oś) |
| P6: 120 Hz i 5 ms | pomiary budżetu i opóźnienia samej sieci; pętla 120 Hz | NOT IMPLEMENTED; 5 ms FAILED |
| P7: benchmark z kamerą | 6 wariantów × 135 prób (v3) | VERIFIED (symulacja) |
| P7: ciągła manipulacja z siecią | jedna seria pokazowa (3 z 6 wprowadzonych w pudełku, potem strefa zablokowana) | NOT VERIFIED (brak serii statystycznej) |
| Zestaw trudny (15 przedmiotów) z kamerą | — | NOT IMPLEMENTED |

## 2. Architektura i rozdział informacji

```
kamera „eye” na chwytaku ── klatka 96×128 co takt (100 Hz czasu symulacji)
   │  [KLASYCZNE] maska własnego chwytaka (złote śruby pobudzały enkoder)
   ▼
enkoder koloru [MODEL, nie oko muchy] ── prąd ──► LC10a L/R ─► pośrednie ─► DNa02 L/R ─► dekoder ─► OBRÓT BAZY  (snn:DNa02)
                                                     [DATA: podgraf indukowany MaleCNS, 1931 neuronów]      │
dotyk padów ─► szczecinki nogi T2 L ─► interneurony ◄── DNa02 L (70 krawędzi z danych) ─────────────────────┘
kąt/prędkość szczęki ─► FeCO (wariant F)   └─► MN goleni ─► MOMENT SZCZĘKI  (snn:vis+legT2L)

kamera, 2 klatki 480×640 na przedmiot ─► [KLASYCZNE] geometria: sylwetka rzutowana na blat z własnej kinematyki,
   wysokość z paralaksy ruchu (obrót bazy o 0,25 rad) ─► prostokąt + wysokość ─► [KLASYCZNE] plan dojazdu,
   podniesienie, transport, puszczenie (to samo rusztowanie co wcześniej)

stan symulatora ─► tylko ewaluator i dziennik błędu percepcji (nie trafia do sterowania)
```

- **Co sieć dostaje:** prądy czuciowe (obraz po enkoderze, siła na padach, kąt i prędkość szczęki). Nie dostaje
  współrzędnych z MuJoCo, etykiety przedmiotu, informacji o udanym chwycie ani gotowej decyzji.
- **Co decyduje sieć:** w którą stronę i jak szybko obrócić bazę podczas patrzenia; czy i jak mocno zacisnąć szczękę.
- **Co robi kod klasyczny (jawnie):** segmentacja i geometria obrazu (odległość, kształt, orientacja, wysokość), poza
  patrzenia, „zajrzenie z boku” (drugi widok), dojazd, pierwsze domknięcie do dotyku, podniesienie, transport, puszczenie.
- **Uproszczenia modelowe:** enkoder to detektor koloru zielonego (przedmioty są zielone); LC10a dostają prąd z enkodera,
  a nie z płata wzrokowego; „obrót bazy ≙ skręt muchy” to analogia; szum 2 mV tylko w drodze wzrokowej (jak w V5), obwód
  nogi bez szumu (jak w etapie dotyku); oświetlenie rozproszone; obraz bez szumu, zniekształceń i rozmycia.

## 3. Co mówią dane MaleCNS o połączeniu wzroku z nogą [DATA]

- DNa02 L → obwód nogi T2 L bezpośrednio: **1190 synaps na 30 neuronów** (27 interneuronów: 1040 synaps; 3 neurony
  ruchowe: 150 synaps). DNa02 R → T2 L bezpośrednio: 0 (przy progu 5 synaps). Przez jeden pośrednik VNC połączeń jest
  ok. 10 razy więcej (L: 10 902 synapsy, R: 4 889) — **tych pośredników sieć jeszcze nie zawiera**.
- W sieci wspólnej: 91 krawędzi wzrok → noga (70 od DNa02 L), 27 krawędzi noga → wzrok.
- Liczba synaps to nie siła fizjologiczna. Funkcja tych połączeń (np. skręt przez zmianę kroku) jest INFERRED.
- Zmierzony wpływ wzroku na szczękę w modelu: przy dotyku 0,5 N moment 0,328 N·m bez obrazu i 0,300–0,311 N·m z obrazem
  (spadek 5–9 %); sam obraz bez dotyku nie zaciska szczęki (0 N·m).

## 4. Percepcja z kamery

Procedura dla każdego przedmiotu: (1) ramię w pozie patrzenia, baza sterowana wyjściem DNa02 aż średni obrót ustanie;
(2) klatka 480×640; (3) klasyczny obrót bazy o 0,25 rad i druga klatka; (4) z przesunięcia skraju sylwetki między
widokami wysokość, z niej prawdziwy obrys. Do planu trafia wysokość + 5 mm zapasu (ustalone przed benchmarkiem).

- Percept powstał w każdej próbie; mediana błędu położenia 0,1 mm, p95 ok. 6 mm, maks. 7–8 mm; szerokość p95 ok. 5 mm.
- **Wysokość kuli i klina jest zaniżana do 30 mm** (paralaksa widzi krawędź sylwetki, nie wierzchołek).
- Tak mały błąd to zasługa idealnego obrazu i dokładnej kinematyki symulatora. Na prawdziwej kamerze będzie gorzej;
  wybrana kamera OV9281 jest monochromatyczna, więc enkoder koloru trzeba będzie zastąpić.
- Dobierane na osobnej puli położeń (ziarna 101 xxx), nie na benchmarku: poza patrzenia, oświetlenie, segmentacja po
  odcieniu, kierunek drugiego widoku, kryterium ustalenia obrotu, szum drogi wzrokowej.

## 5. Benchmark z kamerą i śledzenie — tabele (v3)

Wariant v1 przerwano (za wolno, dryf bazy od śrub własnego chwytaka). Wariant v2 jest kompletny, ale obciążony wadą
pozy patrzenia (staw przy granicy zakresu → brak drugiego podejścia po porażce); dał 95 / 83 / 0 / 82 / 82 / 73.
Oba zostają w katalogu jako zapis. **Do cytowania służy v3.** Te same przedmioty i położenia co w etapie dotyku.

| Ramię | Szczęka | Obrót bazy przy patrzeniu | Chwyt | Podniesienie | Transport | Odłożenie | **W pudełku** | 95 % CI | Mediana operacji [s sym.] | Przyczyny porażek |
|---|---|---|---|---|---|---|---|---|---|---|
| A_cam | classical:object_handling | classical:P_encoder | 127 | 106 | 94 | 98 | **98/135** | 65–79 % | 7.53 | lost_grip 53, no_contact 13, unreachable 1, weak_grip 7 |
| B_cam | snn:legT2L | classical:P_encoder | 104 | 95 | 85 | 85 | **85/135** | 55–71 % | 8.01 | snn_released 96, unreachable 1 |
| D_vis | snn:vis+legT2L | snn:DNa02 | 128 | 0 | 0 | 0 | **0/135** | 0–3 % | None | no_engage 270 |
| E_vis_touch | snn:vis+legT2L | snn:DNa02 | 107 | 96 | 86 | 86 | **86/135** | 55–71 % | 8.015 | snn_released 90, too_wide 1, unreachable 1 |
| E_blind_grasp | snn:vis+legT2L | snn:DNa02 | 104 | 95 | 86 | 86 | **86/135** | 55–71 % | 7.985 | snn_released 90, unreachable 1 |
| F_vis_touch_feco | snn:vis+legT2L+FeCO | snn:DNa02 | 106 | 95 | 80 | 80 | **80/135** | 51–67 % | 8.05 | snn_released 96, unreachable 1 |
| A wyrocznia (etap dotyku) | — | położenie z symulatora | | | | | **93/135** | 61–76 % | | |
| B wyrocznia (etap dotyku) | — | położenie z symulatora | | | | | **90/135** | 58–74 % | | |
| C wyrocznia (etap dotyku) | — | położenie z symulatora | | | | | **83/135** | 53–69 % | | |

Percepcja z kamery względem prawdy symulatora (błąd bezwzględny; liczony po fakcie):

| Ramię | Percepty | Ustalone | Czas ustawiania mediana / p95 [s] | Położenie med / p95 / max [mm] | Szerokość med / p95 / max [mm] | Wysokość med / p95 / max [mm] | Orientacja med / p95 [°] | Brak perceptu (próby) |
|---|---|---|---|---|---|---|---|---|
| A_cam | 168 | 168 | 0.7 / 1.2 | 0.1 / 5.8 / 7.4 | 0.2 / 5.5 / 8.7 | 0.7 / 30.0 / 30.0 | 0.0 / 0.5 | 0 |
| B_cam | 182 | 182 | 0.7 / 1.1 | 0.1 / 5.6 / 7.0 | 0.2 / 5.2 / 7.8 | 0.6 / 30.0 / 30.0 | 0.0 / 0.0 | 0 |
| D_vis | 270 | 270 | 0.5 / 1.1 | 0.1 / 3.6 / 7.6 | 0.2 / 4.1 / 9.2 | 0.7 / 29.3 / 30.0 | 0.0 / 0.5 | 0 |
| E_vis_touch | 179 | 179 | 0.5 / 1.1 | 0.1 / 5.8 / 7.3 | 0.2 / 4.7 / 8.2 | 0.6 / 30.0 / 30.0 | 0.0 / 0.5 | 0 |
| E_blind_grasp | 177 | 177 | 0.6 / 1.1 | 0.1 / 5.8 / 7.1 | 0.2 / 4.9 / 8.7 | 0.6 / 30.0 / 30.0 | 0.0 / 0.5 | 0 |
| F_vis_touch_feco | 177 | 177 | 0.5 / 1.1 | 0.1 / 5.2 / 7.4 | 0.2 / 4.8 / 10.7 | 0.6 / 29.9 / 30.0 | 0.0 / 0.5 | 0 |

Sukces według kształtów (w pudełku / próby):

| Ramię | cube_S | cube_M | cube_L | cyl | sphere | flat | long | L | wedge |
|---|---|---|---|---|---|---|---|---|---|
| A_cam | 15/15 | 15/15 | 6/15 | 10/15 | 15/15 | 9/15 | 15/15 | 12/15 | 1/15 |
| B_cam | 15/15 | 15/15 | 1/15 | 11/15 | 15/15 | 7/15 | 15/15 | 5/15 | 1/15 |
| D_vis | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 |
| E_vis_touch | 15/15 | 13/15 | 2/15 | 10/15 | 15/15 | 7/15 | 15/15 | 6/15 | 3/15 |
| E_blind_grasp | 15/15 | 15/15 | 1/15 | 11/15 | 15/15 | 7/15 | 15/15 | 5/15 | 2/15 |
| F_vis_touch_feco | 15/15 | 11/15 | 0/15 | 10/15 | 14/15 | 8/15 | 12/15 | 5/15 | 5/15 |

| Ramię | hard_grip | hard_slick | heavy | light | mid |
|---|---|---|---|---|---|
| A_cam | 21/27 | 15/27 | 18/27 | 21/27 | 23/27 |
| B_cam | 16/27 | 17/27 | 17/27 | 16/27 | 19/27 |
| D_vis | 0/27 | 0/27 | 0/27 | 0/27 | 0/27 |
| E_vis_touch | 17/27 | 17/27 | 15/27 | 18/27 | 19/27 |
| E_blind_grasp | 17/27 | 17/27 | 17/27 | 16/27 | 19/27 |
| F_vis_touch_feco | 16/27 | 17/27 | 9/27 | 18/27 | 20/27 |

Porównania sparowane (te same przedmioty i położenia; test dokładny McNemara, dwustronny):

| Porównanie | tylko pierwsze | tylko drugie | oba | żadne | p |
|---|---|---|---|---|---|
| E_vis_touch vs A_cam | 6 | 18 | 80 | 31 | 0.023 |
| E_vis_touch vs B_cam | 5 | 4 | 81 | 45 | 1.000 |
| E_vis_touch vs E_blind_grasp | 3 | 3 | 83 | 46 | 1.000 |
| E_vis_touch vs D_vis | 86 | 0 | 0 | 49 | 0.000 |
| F_vis_touch_feco vs E_vis_touch | 5 | 11 | 75 | 44 | 0.210 |
| A_cam vs A wyrocznia (etap dotyku) | 7 | 2 | 91 | 35 | 0.180 |
| B_cam vs B wyrocznia (etap dotyku) | 5 | 10 | 80 | 40 | 0.302 |
| E_vis_touch vs B wyrocznia (etap dotyku) | 8 | 12 | 78 | 37 | 0.503 |
| F_vis_touch_feco vs C wyrocznia (etap dotyku) | 6 | 9 | 74 | 46 | 0.607 |

Uwaga: 3 położenia tego samego przedmiotu nie są niezależne — p i przedziały są orientacyjne.

Ruch, bezpieczeństwo, fizyka, czas reakcji:

| Ramię | max prędkość [rad/s] | interwencje warstwy bezp. | kontakty niepożądane | wnikanie padu > 2 mm (próby) | dotyk → komenda zaciskania mediana / p95 [ms sym.] | moment w transporcie mediana [N·m] |
|---|---|---|---|---|---|---|
| A_cam | 1.890 | {'lead': 48, 'range': 149, 'rate': 355} | 0 | 0 | — | — |
| B_cam | 1.890 | {'jaw_end': 3, 'lead': 70, 'range': 125, 'rate': 488} | 0 | 21 | 10 / 180 | 0.52 |
| D_vis | 1.890 | {'lead': 236, 'rate': 1764} | 0 | 0 | — | — |
| E_vis_touch | 1.890 | {'jaw_end': 41, 'lead': 71, 'range': 176, 'rate': 532} | 1 | 21 | 10 / 192 | 0.52 |
| E_blind_grasp | 1.890 | {'jaw_end': 2, 'lead': 75, 'range': 177, 'rate': 549} | 1 | 21 | 10 / 192 | 0.54 |
| F_vis_touch_feco | 1.890 | {'lead': 74, 'range': 160, 'rate': 546} | 0 | 18 | 90 / 252 | 0.40 |

Czas obliczeń na takt (zegar komputera; osobny przebieg `latency_v3`, 16486 taktów, ramię F):

| Etap | mediana [ms] | p95 | p99 | max |
|---|---|---|---|---|
| camera_render | 3.633 | 3.9637 | 5.4558 | 20.4887 |
| retina_encoder | 0.3654 | 0.3934 | 0.4793 | 2.9755 |
| sensory_currents | 0.0257 | 0.028 | 0.0312 | 0.1329 |
| snn_10_steps | 1.6462 | 1.743 | 1.8408 | 7.8837 |
| decoding | 0.079 | 0.0905 | 0.0985 | 1.816 |
| safety_and_command | 0.0348 | 0.0402 | 0.0439 | 0.1709 |
| camera_to_command_total | 5.7901 | 6.2059 | 7.649 | 25.3235 |

proces: {'wall_s': 123.8, 'cpu_s': 119.6, 'cpu_load': 0.97, 'max_rss_MB': 1804.5, 'ticks': 16486, 'sim_tick_ms': 10.0, 'gpu': 'tylko render kamery (OpenGL)'}

Śledzenie (20 scen na scenariusz; sukces = |az| < 5° przez ostatnie 0,5 s):

| Warunek | Scenariusz | Sukces | 95 % CI | Końcowy \|az\| mediana [°] | Ustalenie po zdarzeniu mediana [s] | Przesunięcie przedmiotu mediana [mm] | Uwagi |
|---|---|---|---|---|---|---|---|
| classical | none | 20/20 | 84–100 % | 0.00 | 0.00 | 0 | dryf obrotu bez bodźca: mediana 0.000, max 0.000 rad |
| classical | static | 20/20 | 84–100 % | 0.16 | 0.14 | 0 |  |
| classical | offset | 20/20 | 84–100 % | 0.11 | 0.45 | 0 |  |
| classical | push | 20/20 | 84–100 % | 0.12 | 0.65 | 113 |  |
| classical | occlude | 20/20 | 84–100 % | 0.09 | 0.00 | 0 | dryf w czasie zasłonięcia: mediana 0.001 rad |
| classical | occl_push | 20/20 | 84–100 % | 0.16 | 0.57 | 111 | dryf w czasie zasłonięcia: mediana 0.001 rad |
| classical | rotate | 20/20 | 84–100 % | 1.59 | 1.80 | 0 | obrót przedmiotu mediana 0°; błąd orientacji z kamery mediana 0.0° (n=16) |
| classical | loss | 5/20 | 11–47 % | 75.11 | 0.46 | 759 | utrata wykryta w 15/20, mediana 0.15 s; |ω| po utracie mediana 0.000 rad/s |
| snn_swap | static | 1/20 | 1–24 % | 41.67 | 0.00 | 0 |  |
| snn | none | 20/20 | 84–100 % | 0.00 | 0.00 | 0 | dryf obrotu bez bodźca: mediana 0.000, max 0.000 rad |
| snn | static | 18/20 | 70–97 % | 2.35 | 0.14 | 0 |  |
| snn | offset | 20/20 | 84–100 % | 1.87 | 0.75 | 0 |  |
| snn | push | 17/20 | 64–95 % | 2.25 | 1.11 | 113 |  |
| snn | occlude | 18/20 | 70–97 % | 1.78 | 0.00 | 0 | dryf w czasie zasłonięcia: mediana 0.016 rad |
| snn | occl_push | 15/20 | 53–89 % | 1.74 | 0.96 | 113 | dryf w czasie zasłonięcia: mediana 0.018 rad |
| snn | rotate | 14/20 | 48–85 % | 2.25 | 1.73 | 0 | obrót przedmiotu mediana 0°; błąd orientacji z kamery mediana 0.0° (n=16) |
| snn | loss | 4/20 | 8–42 % | 75.69 | 0.32 | 759 | utrata wykryta w 15/20, mediana 0.15 s; |ω| po utracie mediana 0.000 rad/s |

Audyt FeCO (percept-wyrocznia, te same 135 prób co B = 90 i C = 83):

| Wariant | W pudełku | Mediana momentu w transporcie [N·m] | vs B: tylko wariant / tylko B | vs C: tylko wariant / tylko C | cube_S | cube_M | sphere |
|---|---|---|---|---|---|---|---|
| claw_only (40 mV) | 85/135 | 0.41 | 4 / 9 | 6 / 4 | 14/15 | 14/15 | 14/15 |
| hook_only (40 mV) | 89/135 | 0.54 | 1 / 2 | 10 / 4 | 15/15 | 15/15 | 15/15 |
| scale_0.25 (10 mV) | 89/135 | 0.53 | 0 / 1 | 10 / 4 | 15/15 | 15/15 | 15/15 |
| scale_0.5 (20 mV) | 89/135 | 0.51 | 1 / 2 | 11 / 5 | 15/15 | 15/15 | 15/15 |
| swap (40 mV) | 41/135 | 0.65 | 1 / 50 | 4 / 46 | 0/15 | 12/15 | 13/15 |

Audyt kontaktu (kontakt sztywniejszy: stała czasowa 0,002 s; te same 135 prób):

| Ramię | W pudełku (sztywny) | W pudełku (dotychczas) | tylko sztywny / tylko dotychczasowy | wnikanie > 2 mm (próby) | wnikanie mediana / max [mm] | light | mid |
|---|---|---|---|---|---|---|---|
| A | 101/135 | 93/135 | 9 / 1 | 0 | 0.26 / 0.99 | 22/27 | 23/27 |
| B | 84/135 | 90/135 | 10 / 16 | 0 | 0.19 / 1.09 | 20/27 | 19/27 |

## 6. Wnioski z benchmarku i śledzenia

1. **Kamera zastępuje wyrocznię bez straty dla kontrolera klasycznego** (98 wobec 93; próby niezgodne 7 do 2). VERIFIED (symulacja).
2. **Sieć z kamerą: 85–86 wobec 90 z wyrocznią** (próby niezgodne 5–8 do 10–12; różnica w granicach niepewności).
3. **Integracja wzroku z dotykiem w sieci nie poprawia chwytu:** E 86, ten sam obwód z wzrokiem poza siecią 85, z wzrokiem
   wyłączonym podczas chwytu 86 (pary niezgodne 5/4 i 3/3). FAILED jako korzyść; VERIFIED jako wynik.
4. **Sam wzrok nie chwyta** (0/135: sieć bez dotyku nigdy nie zaciska); **sam dotyk bez żadnego wzroku nie ma celu**
   (test V4: bez klatek brak perceptu i brak sukcesu).
5. **Klasyczny kontroler wygrywa z siecią** (98 wobec 86; 18 do 6).
6. **FeCO znów nie pomaga** (80 wobec 86; 5 do 11).
7. **Śledzenie:** sieć utrzymuje przedmiot w osi kamery w 14–20 z 20 scen: po pojawieniu się (18), przy odkręconej bazie
   (20), po pchnięciu o ok. 11 cm (17, powrót w medianie 1,1 s), po 0,6 s zasłonięcia (18), po pchnięciu w czasie
   zasłonięcia (15), po obróceniu przedmiotu (14). Regulator klasyczny: 20/20 wszędzie i dokładniej (0,1–0,2° wobec ok. 2°).
   Sieć ma stały uchył ok. 2° (asymetria lewej i prawej strony w danych) i drga, bo DNa02 to jeden neuron na stronę.
8. **Utrata przedmiotu:** po wyrzuceniu z kadru brak bodźca jest wykrywany w 0,15 s (15/20; w 5 scenach przedmiot został
   w kadrze); baza się wtedy zatrzymuje — sieć nie szuka przedmiotu. Bez przedmiotu baza nie dryfuje (0 rad w 3 s).
9. **Śledzenie przedmiotu poruszającego się płynnie** i śledzenie podczas dojazdu chwytaka: NOT IMPLEMENTED.

## 7. Audyt propriocepcji FeCO (P3)

- **Odwzorowanie:** typy SNpp51/50 (claw) i SNpp39/41 (hook) są w adnotacjach narządami chordotonalnymi, ale dopisek
  „FeCO claw/hook” ma tylko część neuronów (1/32, 12/62, 2/39, 3/22). Przypisanie zgięcie/wyprost nie wynika z danych: INFERRED.
- **Znak w danych:** kanał „szczęka domknięta” hamuje neurony zamykające i pobudza otwierające; kanał „szczęka rozwarta”
  odwrotnie; kanały ruchu przeciwdziałają ruchowi. To **odruch oporowy** (ujemne sprzężenie), czyli zachowanie zgodne
  z biologią stojącej nogi — nie pomyłka znaku.
- **Skutek:** przy domkniętej szczęce (małe przedmioty) moment od dotyku spada z 0,31 do 0,10 N·m.
- **Skalowanie (135 prób, percept-wyrocznia):** prąd 10 mV → 89, 20 mV → 89, 40 mV → 83 (sam dotyk: 90). Sam kanał
  położenia → 85, sam kanał ruchu → 89. Przewidywania 1 i 2 spełnione.
- **Odwrócone przypisanie flex/ext → 41/135.** Przewidywanie 3 („wynik nie gorszy”) okazało się błędne: sprzężenie
  dodatnie psuje chwyt. Wniosek: wynik silnie zależy od niepewnego przypisania; obecne jest spójne z odruchem oporowym.
- **Czego brakuje, żeby propriocepcja pomagała:** u owadów odruch oporowy jest w ruchu czynnym przełączany. Obwodu, który
  by to robił, w tej sieci nie ma. Nie stroiłem parametrów, żeby wymusić poprawę.

## 8. Audyt fizyki kontaktu (P4)

- Wnikanie > 2 mm występuje tylko w materiałach „light” (kilka gramów) i „mid” (drewno, miękki profil), nigdy
  w ciężkich. Przyczyna: sztywność kontaktu MuJoCo skaluje się z masą, a ścisk sieci jest silny (0,5–0,9 N·m).
- Wariant sztywny (stała czasowa kontaktu 0,002 s dla wszystkich materiałów): wnikanie maks. 1,1 mm, 0 prób > 2 mm.
- **Wyniki w wariancie sztywnym: klasyczny 101/135 (było 93), sieć sam dotyk 84/135 (było 90).** W materiałach, w których
  było wnikanie, wynik sieci się nie zmienił (light 19 → 20, mid 19 → 19), więc samo wnikanie nie zawyżało sukcesów.
  Sieć traci na twardych materiałach. **Wniosek „sieć dorównuje kontrolerowi klasycznemu” z etapu dotyku zależał od
  miękkości kontaktu i w wariancie sztywnym nie zachodzi (101 wobec 84).**
- Kroku fizyki nie zmieniałem. Benchmark z kamerą (§5) biegł na dotychczasowych materiałach; wnikanie > 2 mm wystąpiło
  w 18–21 próbach ramion z siecią i w 0 próbach klasycznego. Przejście na materiały sztywne = następny wariant.
- Kontakt jedno- i obustronny, poślizg i utrata chwytu jako osobne testy z reakcją sieci: NOT IMPLEMENTED.

## 9. Kontrola G: sieci przetasowane z wyrównaną siłą

Dziesięć nowych tasowań obwodu nogi (stopnie i wagi zachowane); wzmocnienie wyjścia każdej dobrane tak, żeby na bodziec
odniesienia (0,5 N na obu padach) dawała ten sam moment co sieć z danych (0,306 N·m). Te same 135 prób.

| Tasowanie | 011 | 012 | 013 | 014 | 015 | 016 | 017 | 018 | 019 | 020 |
|---|---|---|---|---|---|---|---|---|---|---|
| Skala wzmocnienia | 2,0 | 2,3 | 2,7 | 2,1 | 3,4 | 2,9 | 1,5 | 2,3 | 2,4 | 9,0 |
| W pudełku /135 | 101 | 82 | 80 | 102 | 83 | 79 | 82 | 79 | 99 | 4 |
| Moment w transporcie [N·m] | 0,74 | 0,61 | 0,67 | 0,49 | 0,75 | 0,82 | 0,63 | 0,55 | 0,47 | — |

- Sieć z danych: 90. Trzy przetasowane wypadły lepiej, sześć nieco gorzej, jedna się załamała.
- **Topologia z konektomu nie daje w tym zadaniu przewagi nad sieciami przetasowanymi.** Wynik z etapu dotyku
  (74/49/82 wobec 90) wynikał ze słabszego ścisku, tak jak podejrzewałem.
- Wyrównanie jest niedoskonałe: moment w zadaniu nadal się różni (0,47–0,82 wobec 0,53). Dla drogi wzrokowej
  takiej kontroli w zadaniu chwytania nie wykonano (jest wcześniejsza z V5 dla samego skrętu).

## 10. Częstotliwość i opóźnienia

| Wielkość | Wynik | Status |
|---|---|---|
| Kamera | klatka co takt = 100 Hz czasu symulacji; render 3,6 ms zegara (mediana) | VERIFIED |
| Przetwarzanie obrazu (enkoder) | 0,36 ms | VERIFIED |
| Sieć wspólna, 10 kroków po 1 ms | 1,65 ms (p99 1,84; maks. 7,9) | VERIFIED |
| Dekodowanie, bezpieczeństwo i komenda | 0,08 + 0,03 ms | VERIFIED |
| **Kamera → komenda, razem** | **mediana 5,8 ms; p95 6,2; p99 7,6; maks. 25,3 ms** | VERIFIED (ten komputer, jeden proces) |
| Budżet 120 Hz (8,33 ms) | mieści się do p99; pojedyncze takty go przekraczają | PARTIALLY |
| Pętla 120 Hz | nieuruchomiona — takt symulatora 10 ms jest we wspólnym kodzie | NOT IMPLEMENTED |
| Dotyk → komenda zaciskania w pętli | mediana 10 ms czasu symulacji, p95 ok. 190 ms; z FeCO mediana 90 ms | VERIFIED |
| Opóźnienie samej sieci (krok 1 ms) | dotyk → pierwszy impuls MN: 9 ms przy 1–2 N, 14 ms przy 0,5 N, 29 ms przy 0,25 N; obraz → DNa02: 25–74 ms | VERIFIED (model) |
| **Ścieżka ok. 5 ms** | **nieosiągalna bez zmiany parametrów neuronów** (których nie wolno stroić pod cel) | FAILED |
| Wykonanie komendy przez serwo | symulowane, niemierzone osobno | NOT MEASURED |

Wąskie gardło obliczeń: render kamery (62 %), potem sieć (28 %). Wąskie gardło reakcji: czas całkowania błon i filtr
częstości wyjścia 50 ms. Czas zegarowy i czas symulacji to różne rzeczy; sieć liczy 10 ms czasu modelu w 1,65 ms zegara.

## 11. Porównanie z VFA (Eka Robotics)

- Ponowne wyszukiwanie: „do 1500 pobrań na godzinę” w laboratoryjnym pobieraniu z pojemnika i podawaniu, ok. 2,5 raza
  szybciej niż człowiek (ok. 600/h), skuteczność > 95 %, przedmioty do 1 kg. Źródłem są firma i jej inwestorzy;
  w materiałach firmy pada też „1500 operacji na godzinę”. **Definicji operacji, zestawu przedmiotów i warunków
  pomiaru nie znalazłem.** Status: REPORTED (deklaracja), przeczytane jako streszczenia wyników wyszukiwania.
- Źródła: [The Robot Report](https://www.therobotreport.com/eka-robotics-raises-150m-scale-vision-force-action-model-robots/),
  [The Next Web](https://thenextweb.com/news/eka-robotics-150m-series-a-vision-force-robots),
  [Zeniteq](https://www.zeniteq.com/eka-claims-1-500-picks-an-hour-but-needs-factory-proof-hk518u),
  [The AI Insider](https://theaiinsider.tech/2026/10/20/eka-robotics-raises-150m-series-a-to-scale-vision-force-action-model-for-dexterous-robots/).
- Nasze liczby są symulacyjne: mediana pełnej operacji z kamerą ok. 8 s czasu symulacji (z patrzeniem), skuteczność
  sieci 64 %. To nie jest porównywalne z fizycznym VFA i nie twierdzimy, że jest. Wyróżnikiem ma być sieć z konektomu
  w pętli czuciowo-ruchowej — z zastrzeżeniem z §9, że jej topologia nie daje dziś mierzalnej przewagi.

## 12. Ograniczenia i rzeczy nieudane

- Wszystko jest symulacją; obraz jest idealny; przedmioty są zielone; enkoder to detektor koloru.
- Sieć steruje jedną osią ramienia (obrót bazy) tylko podczas patrzenia i szczęką podczas chwytu. Reszta jest klasyczna.
- Integracja wzrok + dotyk nie dała korzyści; FeCO szkodzi; topologia nie daje przewagi nad tasowaniami.
- Jedna instancja sieci na wariant i jedno ziarno szumu na próbę; 3 położenia tego samego przedmiotu nie są niezależne.
- W v3 odnotowano 51–245 taktów na ramię z prędkością stawu > 1,5 rad/s (maks. 1,89 rad/s, ta sama wartość we
  wszystkich ramionach; liczba rośnie z liczbą pomiarów kamerą, więc najpewniej przejście z drugiego widoku do dojazdu).
  Przyczyna NOT VERIFIED — w próbie kontrolnej nie wystąpiło. Warstwa bezpieczeństwa zgłaszała ograniczenia tempa
  i wyprzedzenia celu (setki taktów na ramię), bez zatrzaśnięcia błędu. Limitów nie zmieniałem. Do naprawy przed
  jakimkolwiek użyciem na sprzęcie. W ramieniu E jedno „fałszywe przekonanie” kontrolera (uznał odłożenie, kryterium nie).
- Seria ciągła z siecią: tylko pokaz (3 z 6 wprowadzonych; potem dwa porzucone przedmioty blokują strefę).
- Zestaw trudny z kamerą, przedmioty z internetu, pętla 120 Hz, testy poślizgu, pośredniki VNC między DNa02 a nogą,
  sterowanie dojazdem przez sieć: NOT IMPLEMENTED.
- Biologicznych publikacji nie czytałem ponownie w tej sesji; odwołania pochodzą z wcześniejszych raportów projektu.

## 13. Odtwarzalność

```
# z dowolnego katalogu; skrypty same przechodzą do katalogu tymczasowego
flymind/results/vision_manipulation/run_arms.sh <nowy sufiks>       # testy + 6 ramion × 135 prób + pomiar czasu
flymind/results/vision_manipulation/run_tracking.sh <nowy sufiks>   # śledzenie: snn, classical, snn_swap
flymind/results/feco_audit/run_all.sh <nowy sufiks>                 # FeCO (5 wariantów) + kontakt sztywny (A, B)
flymind/results/shuffle_matched/run_all.sh <nowy sufiks>            # 10 tasowań z wyrównaną siłą
.venv/bin/python -I -B flymind/results/vision_manipulation/tables.py v3
```

Ziarna: `results/vision_manipulation/SEED_REGISTRY.md`. Zamrożenia kodu i skróty wyników: `FREEZE_v3.txt`, `run_v3.log`
(kod po przebiegu IDENTYCZNY, 17 plików Etapu 1 OK). Manifest: `results/vision_manipulation/MANIFEST_2026-11-10.txt`.
Testy: `test_vision_manipulation.py` (6), `test_sensory_manipulation.py` (5), `test_object_handling.py` (14).
Filmy: `results/vision_manipulation/media/demo_E_vis_touch_v3.mp4` (v2 obok, z wadą pozy).

## 14. Co dalej (propozycja kolejności)

1. Benchmark na materiałach sztywnych jako nowy wariant odniesienia (bez wnikania) — dla kamery i dla sieci.
2. Dołączenie pośredników VNC między DNa02 a nogą (dane pokazują 10× więcej połączeń niż bezpośrednich) i ponowny test,
   czy wzrok zmienia chwyt.
3. Seria ciągła z siecią z usuwaniem porzuconych przedmiotów przez samego robota (kamera je widzi).
4. Enkoder niezależny od koloru (kontrast lub ruch) pod kamerę monochromatyczną.
5. Pętla 120 Hz (zmiana taktu we wspólnym kodzie + regresje).
