# Oko muchy: jak działa, które części konektomu możemy użyć (16 XI 2026)

Raport badawczy. Bez kodu projektu, bez symulacji, bez pobierania i instalowania czegokolwiek. Liczby z MaleCNS v1.0
pochodzą z zapytań tylko do odczytu (skrypty i tabela w `fly_eye_research_20261116_scripts/`).
Uzupełnia plan z 12 XI (`fly_eye_plan_20261112.md`), nie zastępuje go.

Etykiety: [LIT] z literatury/internetu · [FM] z naszych danych · [PROP] propozycja.
VERIFIED · REPORTED (podane przez źródło, nie sprawdzone u nas) · INFERRED · HYPOTHESIS · NOT VERIFIED.

---

## 0. Najkrócej, dla Adama

1. **Oko muchy to ok. 750–890 małych „oczek”** (ommatidiów) na stronę. Każde patrzy w inną stronę, co ok. 4,5°.
   Obraz jest więc bardzo grubo ziarnisty, mniej więcej 30 × 30 „pikseli” na oko. Za to oko jest szybkie: widzi
   około 100–200 zmian na sekundę, a my około 60. Mucha nie ogląda „zdjęć”. Głównie wyłapuje **ruch** i to, że **coś się zbliża**.
2. **Za okiem są warstwy przetwarzania**, każda z gotowymi połączeniami w danych:
   siatkówka → lamina (podział na „robi się jaśniej” i „robi się ciemniej”) → rdzeń (medulla) → **T4/T5, czujniki
   kierunku ruchu** (4 kierunki) → **detektory cech** (LC, LPLC: „coś się zbliża”, „mały przedmiot się rusza”) →
   neurony zstępujące → nogi i skrzydła.
3. **W naszych danych (MaleCNS) jest całe to oko**, oba płaty wzrokowe: 89 403 neurony płata, 9201 neuronów
   wysyłających obraz do mózgu, ok. 890 kolumn na stronę. Brakuje tylko części fotoreceptorów (ich ciała leżą poza próbką).
4. **Nowe odkrycie (dziś):** z oka do naszej sieci przedniej nogi lewej prowadzą gotowe drogi przez neurony zstępujące.
   Najciekawsza jest **droga lądowania**: detektor zbliżania LPLC4 → **DNp07** → **dźwigacz stopy przedniej nogi lewej**,
   czyli **ten sam staw, którym nadgarstek ramienia ruszał w krokach 5 i 6**. U muchy coś zbliżającego się wywołuje
   wyprostowanie przednich nóg do lądowania.
5. **Istnieje gotowy, sprawdzony model oka z konektomu** (flyvis, Nature 2024, otwarty kod). Liczy jednak tylko do T4/T5
   i używa innego konektomu (samicy) niż nasz MaleCNS (samca).
6. **Rekomendacja:** pierwsze zachowanie przez prawdziwe oko to **„coś się zbliża → nadgarstek się unosi”**
   (droga lądowania LPLC4 → DNp07). Pierwszy test bez ramienia: czy nasze T4/T5 rozróżniają kierunek ruchu (bramka G2 z planu 12 XI).

---

## 1. Jak widzi mucha [LIT]

### 1.1 Budowa oka

| Co | Jak jest | Źródło |
|---|---|---|
| Liczba oczek (ommatidiów) | ok. 750 na oko według literatury. W MaleCNS jest 884–892 kolumn L1 na stronę | [FlyGym](https://github.com/NeLy-EPFL/flygym), [Kemppainen i in. 2022](https://www.nature.com/articles/s42003-022-03142-0.pdf); [FM] VERIFIED |
| Kąt między oczkami | ok. 4,5° | [Kemppainen i in. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC8894348) REPORTED |
| Fotoreceptory w oczku | 8: R1–R6 na obwodzie (jasność i ruch), R7 i R8 w środku, jeden nad drugim (kolor) | jw. REPORTED |
| **Superpozycja nerwowa** | R1–R6 z 6 sąsiednich oczek patrzą w ten sam punkt i łączą się w jednej kolumnie laminy. Więcej światła z jednego kierunku, ta sama rozdzielczość | jw. REPORTED |
| Kolor | R7: dwa barwniki UV (Rh3, Rh4); R8: niebieski (Rh5) albo zielony (Rh6). Oczka „blade” i „żółte” | [Schnaitmann i in.](https://pubmed.ncbi.nlm.nih.gov/33636123/) REPORTED |
| Polaryzacja | Pas oczek na górnej krawędzi oka (DRA) widzi polaryzację światła nieba, czyli kompas | [PMC4245076](https://pmc.ncbi.nlm.nih.gov/articles/PMC4245076) REPORTED (jedno źródło) |
| Szybkość | Zlewanie migotania powyżej 120 Hz, często podawane ok. 200 Hz (zależnie od metody) | [PMC4798572](https://pmc.ncbi.nlm.nih.gov/articles/PMC4798572), [PMC7515906](https://pmc.ncbi.nlm.nih.gov/articles/PMC7515906) REPORTED |
| Mikroruchy fotoreceptorów | Fotoreceptory same lekko się przesuwają (poniżej 100 ms). Dzięki temu mucha widzi drobniej niż wynika z rozstawu oczek i ma widzenie głębi | [Juusola i in. 2017, eLife](https://elifesciences.org/articles/26117) REPORTED |

### 1.2 Przetwarzanie: od światła do ruchu nogi

```
światło → R1–R6 (+ R7/R8 kolor)
        → LAMINA: L1 (ścieżka „jaśniej”, ON), L2 (ścieżka „ciemniej”, OFF), L3 (jasność i kolor)
        → MEDULLA: Mi1, Tm3 (ON) · Tm1, Tm2, Tm4, Tm9 (OFF) · Mi4, Mi9 (opóźnienie i hamowanie)
        → T4 (ruch jasnych krawędzi) i T5 (ruch ciemnych krawędzi), każdy w 4 odmianach kierunku: a, b, c, d
        → PŁYTKA (lobula plate) i LOBULA: detektory cech (LC, LPLC, LLPC; ok. 9200 neuronów, kilkadziesiąt typów)
        → kłębuszki w mózgu centralnym → NEURONY ZSTĘPUJĄCE (DN) → odcinek piersiowy (VNC) → mięśnie nóg i skrzydeł
```

- Rozdział na ON i OFF dzieje się już przy pierwszej synapsie (L1 i L2) [LIT, [Takemura i in. 2017](https://elifesciences.org/articles/24394v2), [VFB](https://jupyterhub.virtualflybrain.org/docs/anatomy-diagrams/on-and-off-motion-detection-circuit/)] REPORTED.
- **Jak T4/T5 rozpoznają kierunek:** wzmacniają ruch w „swoją” stronę (wejście z jednej strony pola) i tłumią ruch w
  przeciwną stronę (wejście z drugiej strony). Oba mechanizmy są w każdym z 8 podtypów [[Haag i in. 2016](https://elifesciences.org/articles/17421.pdf), [Haag, Mishra, Borst 2017](https://elifesciences.org/articles/29044)] REPORTED.
  Dla nas to znaczy: kierunek zależy od **różnych opóźnień** wejść. Konektom podaje, kto z kim jest połączony, ale nie podaje opóźnień. To główne ryzyko (bramka G2).
- Wczesne warstwy (fotoreceptory, lamina, duża część medulli) działają głównie **potencjałami stopniowanymi**, nie
  impulsami. Model flyvis jest dlatego modelem nieimpulsowym. NOT VERIFIED u nas, do sprawdzenia przed budową.
- **Detektory cech (neurony LC/LPLC)** [[Wu i in. 2016, eLife](https://elifesciences.org/articles/21022)] REPORTED:
  - LC4, LPLC2: „coś się zbliża”. LPLC2 koduje rozmiar, LC4 prędkość zbliżania; obie dochodzą do włókna olbrzymiego
    (ucieczka) [[Ache i in. 2019](https://researchdiscovery.drexel.edu/esploro/outputs/journalArticle/Neural-Basis-for-Looming-Size-and/991019168481004721)].
  - LPLC3, LPLC4: zbliżanie → **lądowanie** przez DNp07 i DNp10 [[PMC7444277](https://pmc.ncbi.nlm.nih.gov/articles/PMC7444277)].
  - LC10: mały ruchomy przedmiot (zaloty, sięganie); jako jedyny LC zachowuje mapę pola widzenia [Wu 2016].
- Odwrotny kierunek też istnieje. Neurony odśrodkowe (563 w MaleCNS) niosą sygnał z mózgu z powrotem do oka, a
  analiza z 2026 r. znajduje pętle zwrotne między okiem a mózgiem [[bioRxiv 2026](https://www.biorxiv.org/content/10.64898/2026.02.02.700492v1.full.pdf)] REPORTED.

---

## 2. Co z oka jest w naszych danych (MaleCNS v1.0) [FM, VERIFIED odczyt]

| Grupa | Liczba |
|---|---|
| Neurony płata wzrokowego (`ol_intrinsic`) | 89 403 |
| Neurony wysyłające obraz do mózgu (`visual_projection`) | 9 201 |
| Neurony odśrodkowe (mózg → oko) | 563 |
| Fotoreceptory (`ol_sensory`; tylko zakończenia aksonów) | 6 098: R1–R6 3 377; R7 (p, y, d, niejasne) 1 300; R8 1 329; strona P 3 746, L 2 345. Pełne oko miałoby ok. 5 300 R1–R6 na stronę, więc część brakuje |
| Lamina L1 / L2 / L3 / L4 / L5 (L + P) | 884+892 / 886+893 / 880+892 / 879+891 / 889+898 |
| Medulla Mi1 / Tm1 / Tm2 / Tm3 | 886+887 / 887+890 / 883+883 / 1017+1037 |
| T4a–d (L, każdy) | 835, 844, 895, 850 (P podobnie: 849, 846, 883, 859) |
| T5a–d (L, każdy) | 826, 863, 862, 812 (P: 838, 852, 858, 808) |
| Detektory: LPLC2 / LC4 / LPLC4 / LPLC1 / LC10a / LC11 / LC9 (L + P) | 94+91 / 71+55 / 48+49 / 68+66 / 135+140 / 68+75 / 104+115 |
| Neurony zstępujące z ≥ 500 synapsami z oka | 134 |

Z planu 12 XI: rdzeń ruchu (od R1–R6 do T4/T5) to 47 473 neurony i 1,16 mln połączeń; 23 720 neuronów ma przypisaną kolumnę heksagonalną.

---

## 3. Drogi z oka do naszej przedniej nogi i ramienia [FM, VERIFIED odczyt; znaki przekaźników nie sprawdzone]

Szukałem neuronów zstępujących (DN), które dostają ≥ 300 synaps z detektorów oka **i** wysyłają ≥ 50 synaps do naszej sieci
nogi „pre” (3148 neuronów, przednia noga lewa, ta sama co w krokach 3–6). Takich DN jest **144**. Najważniejsze:

| Droga | Wejście z oka (strona oka) | Co porusza (synapsy bezpośrednio do neuronów ruchowych) | Znane zachowanie [LIT] | Dla ramienia |
|---|---|---|---|---|
| **LPLC4 → DNp07** (oba DNp07) | LPLC4 1065–1199, LoVP18, LLPC3 | **przednia noga L: dźwigacz stopy 55 + 24**, promotor 15; noga środkowa: zginacz goleni | **lądowanie: zbliżanie → wyprostowanie przednich nóg** | **nadgarstek** (ten sam staw co w krokach 5–6); 1451 + 982 synaps do sieci „pre” |
| **LPLC4 + LLPC2 → DNb05 L** | LPLC4 L 2298, LLPC2 L 1189 (28 % całego wejścia) | przednia noga L: prostownik krętarza 66, sternotrochanter 31; mięśnie skrzydeł | brak danych w literaturze (nie znalazłem) | bark/łokieć; **2135 synaps do sieci „pre”**, 231 bezpośrednio do neuronów ruchowych |
| **LC4 + LPLC1 + LC9 → DNp11** | LC4 1644–2022 | noga środkowa: zginacz goleni, rotator; brzuch | ucieczka/unik (LC4) | mniej przydatne (głównie inna noga) |
| **LC4 + LPLC2 → DNp01 (włókno olbrzymie)** | LC4 2580–3782, LPLC2 2220–2642 | **TTMn** (mięsień skoku, odcinek T2) | **ucieczka: skok** | „stop / cofnij” (plan 12 XI); w przedniej nodze słabo (167 synaps do „pre”) |
| **LLPC1 → DNa02** | LLPC1 193–330, LT51 | rotatory wszystkich nóg, reduktor uda | skręt (ta sama DN co w pokazie V5) | obrót podstawy; wejście z oka jest słabe (2–4 %) |

Wnioski:
- **Do naszego ramienia najlepiej pasuje droga lądowania LPLC4 → DNp07.** Jest opisana w literaturze. Daje
  naturalne zachowanie („coś się zbliża → wyciągnij przednie nogi”) i trafia w staw, który już umiemy sterować
  przez DNge078 (krok 6). [INFERRED]
- **DNb05** to najsilniejsza droga z oka do sieci przedniej nogi, ale jej zachowania nie znalazłem w literaturze, więc to hipoteza do zbadania. [HYPOTHESIS]
- Włókno olbrzymie (ucieczka) prowadzi głównie do mięśnia skoku w odcinku T2, a nie do przedniej nogi. Do „stop” w ramieniu nadaje się gorzej, niż zakładał plan z 12 XI. [INFERRED, korekta planu]

---

## 4. Gotowe modele oka, które istnieją [LIT]

| Model | Co robi | Plusy | Minusy dla nas |
|---|---|---|---|
| **flyvis** (Lappalainen i in. 2024, Nature; [GitHub](https://github.com/TuragaLab/flyvis), [PyPI](https://pypi.org/project/flyvis) 1.2.0, MIT, PyTorch) | 64 typy komórek drogi ruchu na siatce 721 kolumn (promień 15). Parametry dopasowane uczeniem. Przewidywania zgodne z 26 badaniami | gotowy, sprawdzony; rozwiązuje problem „opóźnień”, bo T4/T5 są kierunkowe | konektom FIB-SEM (fib25/fib19), nie MaleCNS; model nieimpulsowy; kończy się na T4/T5, bez LPLC4/LC4 ([dokumentacja](https://turagalab.github.io/flyvis/examples/01_flyvision_connectome)) |
| **FlyGym / NeuroMechFly v2** (Wang-Chen i in. 2024, Nat Methods; [GitHub](https://github.com/NeLy-EPFL/flygym), [samouczek](https://nely-epfl.github.io/flygym-gymnasium/tutorials/advanced_vision.html)) | Oko jako siatka heksagonalna oczek w MuJoCo, połączone z flyvis; mucha podąża za inną muchą | **MuJoCo, tak jak u nas**; gotowe próbkowanie obrazu na oczka | ciało muchy, nie ramię; API 2.x od marca 2026 (zmiany) |
| Mapy orientacji z pełnego konektomu, sieć impulsowa ([NeurIPS 2025](https://proceedings.neurips.cc//paper_files/paper/2025/hash/f11922f49803b5327c904df814ac5964-Abstract-Conference.html)) | Model impulsowy płata wzrokowego z pełnego konektomu | pokazuje, że model impulsowy z konektomu daje sensowne odpowiedzi | FlyWire, nie MaleCNS; nie sprawdzałem kodu |
| Shiu i in. 2024 (cały mózg LIF, Brian2) | Podstawa wielu projektów; nasze parametry ALIF są z niego | — | wzroku nie modeluje szczegółowo |
| [fly-brain (prywatny projekt)](https://github.com/erojasoficial-byte/fly-brain) | Twierdzi: 138 tys. neuronów + ciało w MuJoCo + wzrok | — | **niesprawdzone, bez recenzji; nie opierać się** |

---

## 5. Propozycja [PROP — nic nie zrobione, czeka na decyzję]

**Cel 1:** „przedmiot zbliża się do ramienia → nadgarstek się unosi”, przez prawdziwe oko z danych:
kamera MuJoCo → oczka (siatka heks.) → R1–R6/L1–L3 → T4/T5 → LPLC4 → DNp07 → sieć nogi „pre” → nadgarstek.

| Etap | Co | Bramka |
|---|---|---|
| E0 | Mapa kolumn i dróg (dane, tylko odczyt) | — |
| E1 | Kamera MuJoCo → próbkowanie na ok. 890 kolumn heks. (wzorem FlyGym) | obraz da się odtworzyć |
| E2 | Rdzeń ruchu z MaleCNS na naszych neuronach ALIF | **G2: czy T4/T5 rozróżniają 4 kierunki?** Jeśli nie → STOP i decyzja |
| E2' (zapas) | Jeśli G2 nie wyjdzie: flyvis jako rdzeń ruchu do T4/T5, dalej MaleCNS | mieszanie dwóch konektomów, uczciwie opisane |
| E3 | T4/T5 → LPLC4 / LPLC2 | G3: czy rozróżniają zbliżanie od oddalania i przesuwania |
| E4 | LPLC4 → DNp07 → sieć „pre” → nadgarstek, w ramieniu w symulacji | test z tasowaniami i wycięciem DNp07 (jak krok 6) |

Szacunek: E0–E2 to kilka dni pracy, a największa niewiadoma to G2. Pełna pętla E4 do 1 XII jest możliwa tylko wtedy,
gdy G2 wyjdzie od razu albo zadziała zapas E2'. [INFERRED]

## 6. Decyzje dla Adama

1. Czy pierwszym zachowaniem przez oko ma być „lądowanie” (zbliżanie → nadgarstek), zamiast „stop” z planu 12 XI?
2. Czy wolno pobrać i zainstalować flyvis (MIT, PyTorch) jako zapas na wypadek, gdyby G2 nie wyszło? Oznacza to mieszanie konektomu samicy (flyvis) z naszym konektomem samca, opisane uczciwie.
3. Czy zaczynamy od E0–E2 (sama symulacja, bez ramienia)?

## Źródła
- Kemppainen i in. 2022, Commun Biol: https://www.nature.com/articles/s42003-022-03142-0.pdf · https://pmc.ncbi.nlm.nih.gov/articles/PMC8894348
- Juusola i in. 2017, eLife: https://elifesciences.org/articles/26117
- Lappalainen i in. 2024, Nature (flyvis): https://github.com/TuragaLab/flyvis · https://pypi.org/project/flyvis · https://turagalab.github.io/flyvis/examples/01_flyvision_connectome · https://www.janelia.org/news/researchers-combine-the-power-of-ai-and-the-connectome-to-predict-brain-cell-activity
- Nern i in. 2025, Nature (optic lobe samca): https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11042306/ · https://ideas.repec.org/a/nat/nature/v641y2025i8065d10.1038_s41586-025-08746-0.html
- Wu i in. 2016, eLife (neurony LC): https://elifesciences.org/articles/21022
- Ache i in. 2019 (włókno olbrzymie: rozmiar i prędkość): https://researchdiscovery.drexel.edu/esploro/outputs/journalArticle/Neural-Basis-for-Looming-Size-and/991019168481004721
- Lądowanie DNp07/DNp10: https://pmc.ncbi.nlm.nih.gov/articles/PMC7444277
- Takemura i in. 2017, eLife (ON): https://elifesciences.org/articles/24394v2 · VFB: https://jupyterhub.virtualflybrain.org/docs/anatomy-diagrams/on-and-off-motion-detection-circuit/
- Haag i in. 2016/2017, eLife (T4/T5): https://elifesciences.org/articles/17421.pdf · https://elifesciences.org/articles/29044
- Kolor: https://pubmed.ncbi.nlm.nih.gov/33636123/ · https://pmc.ncbi.nlm.nih.gov/articles/PMC4245076
- Szybkość: https://pmc.ncbi.nlm.nih.gov/articles/PMC4798572 · https://pmc.ncbi.nlm.nih.gov/articles/PMC7515906
- FlyGym: https://github.com/NeLy-EPFL/flygym · https://nely-epfl.github.io/flygym-gymnasium/tutorials/advanced_vision.html · https://pubmed.ncbi.nlm.nih.gov/39533006/
- NeurIPS 2025: https://proceedings.neurips.cc//paper_files/paper/2025/hash/f11922f49803b5327c904df814ac5964-Abstract-Conference.html
- bioRxiv 2026 (wzrok w całym mózgu): https://www.biorxiv.org/content/10.64898/2026.02.02.700492v1.full.pdf
- Prywatny projekt (niesprawdzony): https://github.com/erojasoficial-byte/fly-brain

---

## Dopisek 16 XI, 14:50 — bramka G2 wykonana (Etap 0)
Wynik: `flymind/results/v1_camera/gate/GATE_RESULT_20261116.md`. Rozdział ON/OFF wychodzi z samych połączeń (G1 7/7 PASS).
Czujniki kierunku T4/T5 przy jednakowych parametrach neuronów **nie** powstają (DSI ≈ 0,003, jak w tasowaniach; G2, G3 FAILED).
Zgodnie z planem: STOP przed podłączeniem oka do ramienia; decyzja Adama: stałe czasowe z literatury / flyvis / wstrzymać.

## Dopisek 16 XI, 21:25 — opcje 1 i 2 na zmianę (decyzja Adama)
- **Opcja 1, r2** (MaleCNS + stałe czasowe z literatury): T4 DSI 0,025–0,030 — ponad tasowania, ale daleko od 0,20 → G2/G3 FAILED.
  `flymind/results/v1_camera/gate_r2/GATE_RESULT_r2_20261116.md`.
- **Opcja 2** (gotowe oko flyvis, 50 modeli): **G2-fv i G3-fv PASS** (T4a/c/d: mediana DSI 0,40/0,58/0,47; kierunki 22–26° od literatury).
  `flymind/results/v1_camera/gate_flyvis/GATE_RESULT_flyvis_20261116.md`. To jest oko z konektomu samicy z dopasowanymi
  parametrami, nie nasz MaleCNS.
- Most do MaleCNS: obie sieci kolumn pasują po obrocie o 30°; „ramiona” LPLC2 w MaleCNS wskazują na zewnątrz, zgodnie
  z kierunkami czujników flyvis (VERIFIED). Test B1 (zbliżanie vs oddalanie/przesuwanie) zapisany przed uruchomieniem:
  `flymind/experiments/v1_camera_input/PREREG_BRIDGE.md`; wynik w `flymind/results/v1_camera/bridge_b1/`.

## Dopisek 17 XI — most do LPLC2: B1 i B1b FAILED, STOP
B1 (ciemny dysk, modele 000–009): FAILED (wygrane 59 %, 5./24). Jasny dysk w raporcie wyglądał dobrze (80 %, 1./24),
ale potwierdzenie B1b na nowych modelach 010–019: FAILED (63 %, LI 0,089). Odczyt liniowy z danych MaleCNS nie daje
wiarygodnego detektora zbliżania, więc połączenie oka z ramieniem (B2) nie jest uzasadnione. Szczegóły:
`flymind/results/v1_camera/bridge_b1/B1_RESULT_20261117.md`, `flymind/results/v1_camera/bridge_b1b/B1b_RESULT_20261117.md`.
