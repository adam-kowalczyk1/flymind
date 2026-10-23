# Biologiczny sterownik SO-101 z konektomu muchy — wyniki

Projekt na Explory: ramię SO-101 (5 stawów + chwytak, serwa STS3215) sterowane impulsową siecią
neuronową (ALIF, dt = 1 ms), w której **332 neurony i 53 766 synaps pochodzą z prawdziwego konektomu
samca muchy MaleCNS v1.0**. Robot śledzi toczącą się kulkę obwodem pościgu samca
(LC10a → AOTU019/AOTU025 → DNa02) i łapie ją odruchem nogi (czucie nacisku → interneurony →
motoneurony zginacza, prostownika i ltm), nie zgniatając jej.

Wszystkie liczby poniżej pochodzą z symulacji MuJoCo. Nic nie było sprawdzane na prawdziwym ramieniu.

![ablacja](ablation_results.png)

## Architektura

```
kamera (azymut kulki z osi bazy) ──► LC10a L/R (135+140) ──► AOTU019 (GABA, krzyżowo) ─┐
                                                        └─► AOTU025 (ACh, ta sama str.) ┴► DNa02 L/R ──► ω bazy
czujniki dotyku szczęk/dłoni ──► 20 aferentów proprioceptywnych nogi T1-L ──► 20 interneuronów ──► MN
          (campaniform sensilla)        │                                    (10 GABA, 8 ACh, 2 Glu)
                                        └──► moduł odruchu (16 neuronów MODELOWYCH):
                                             RR_assist (zatrzask „łap”) ──► zginacz + ltm (wszystkie MN)
                                             RR_hold  (koincydencja obu szczęk, zatrzask „trzymam”)
                                             RR_resist (GABA) ──► wyłącza szybkie/pośrednie MN, słabo wolne; hamuje DNa02
MN: Ti flexor ×5 (szybki/2×pośredni/2×wolny wg rozmiaru), ltm ×4, Ti extensor ×2 (FETi/SETi) ──► mięsień ──► PWM serwa chwytaka
```

Wagi: `W = sign(nt) · J0 · ln(1 + N_syn)` (ACh +, GABA −, Glu −), membrana z modelu Shiu i in. 2024
(V_rest = −52, V_th = −45 mV, τ_m = 20 ms, τ_syn = 5 ms, refrakcja 2,2 ms, opóźnienie 2 ms),
adaptacja τ_a = 300 ms, 0,5 mV na spike.

## Dane: MaleCNS v1.0

Publiczny bucket Janelii, bez tokenu, licencja CC-BY 4.0: 211 577 ciał, 151,9 mln połączeń,
311,8 mln synaps (`sim/extract_connectome.py`). Co wyciąłem:

| obwód | neurony | z danych |
|---|---|---|
| pościg | LC10a 135 L / 140 R, AOTU019 1+1 (GABA, 0,83), AOTU025 1+1 (ACh, 0,93), DNa02 1+1 (ACh, 0,95) | LC10a_R→AOTU019_R 7595 syn., AOTU019_R→DNa02_L 297, AOTU025_L→DNa02_L 205 |
| noga T1-L | 20 aferentów (2 opisane jako CS + 18 „leg” bez podtypu), 20 interneuronów o najsilniejszej ścieżce czucie→IN→MN, 11 MN | IN_GABA→Ti extensor 1290 syn., IN_GABA→Ti flexor 405 |

Push-pull z pracy Collie i in. (Wilson lab) potwierdza się u samca: GABAergiczny AOTU019 hamuje DNa02 po
przeciwnej stronie, a cholinergiczny AOTU025 pobudza DNa02 po tej samej. Pełny raport z
literaturą i tabelą liczb: [reports/Konektom muchy dla SO101.md](reports/Konektom%20muchy%20dla%20SO101.md).

## Etap 1 — scena MuJoCo (`sim/stage1_verify.py`)

Oficjalny model SO-101 (onshape-to-robot, kinematyka i serwa producenta). Zmiany: kolizje szczęk
jako pudełka, bo otoczka wypukła meshu wypełniała paszczę; czujniki touch na wewnętrznych padach
i dłoni; chwytak w trybie PWM (3,35 N·m · u); równia i miękka kulka 5 cm / 50 g.

- 10 s, 1000 cykli × 10 kroków po 1 ms. Cykl trwa średnio 0,14 ms (p99 0,19 ms), czyli ~50× szybciej niż czas rzeczywisty.
- Kontakty kulki: równia, stół, obie szczęki, dłoń. Brak kolizji ramię–stół. Wszystkie 6 sprawdzeń OK.
- Obserwacja: chwyt stałym PWM bez regulacji daje 7,6 N (0,5 N·m), a pełny PWM 72 N i wyciska kulkę ze szczęk.

## Etap 2 — sieć bez fizyki (`sim/stage2_test.py`, raster: `results/stage2_raster.png`)

348 neuronów (332 MaleCNS + 16 modelowych). Wszystkie 8 sprawdzeń OK:

- Brak eksplozji: maksimum pojedynczego neuronu 260 Hz (okno 50 ms). Po bodźcu sieć wraca do linii bazowej (0,43 vs 0,48 Hz).
- Huśtawka DNa02 zgodna ze stroną celu: L−R = +37 Hz dla celu po lewej, −35 Hz dla celu po prawej.
- Odwrócenie odruchu: ten sam nacisk szczęk w stanie pasywnym lekko hamuje zginacz (−0,7 Hz, słabo), a w aktywnym pobudza (+82 Hz).
- Zasada wielkości:
  - rekrutacja przy rampie prądu: wolny 61 ms → pośredni 562 ms → szybki 1138 ms;
  - derekrutacja przy rosnącej sile: szybki gaśnie po 64 ms, pośredni po 132 ms, wolny po 1996 ms.

## Etap 3 — pętla zamknięta (`sim/stage3.py`)

Sukces liczę z sił kontaktu MuJoCo, nie z czujników sterownika: kulka uniesiona ≥ 3 cm, trzymana
obiema szczękami na końcu próby, a siła ściskania (średnia 20 ms) nigdy nie przekroczyła 5 N.
Stałe strojone na ziarnach 100–119, walidowane na 120–139, testowane jednorazowo na 0–9.

| zbiór | sukces | zgniecione | bez chwytu | chybione |
|---|---|---|---|---|
| **test (ziarna 0–9)** | **7/10 = 70%** | 0 | 3 | 0 |
| walidacja (120–139) | 13/20 = 65% | 0 | 7 | 0 |
| strojenie (100–119) | 14/20 = 70% | 0 | 6 | 0 |
| pełny obwód, 3 ziarna szumu × 10 (Etap 4) | 21/30 = 70% | 3 | 6 | 0 |

- Czas od kontaktu do pewnego chwytu (obie szczęki ≥ 0,3 N przez 50 ms) w próbach udanych: **2119 ± 241 ms**.
- Latencja neuronalna (kontakt → moment > 0,2 N·m): **40 ± 7 ms**. Szczęka rusza po 90 ± 17 ms.
- Resztę czasu zajmuje celowo powolne domykanie: armatura serwa 0,028 kg·m² z modelu producenta to ~7,8 kg masy efektywnej na końcu szczęki, więc szybkie domknięcie zgniata kulkę uderzeniem.
- Siła trzymania 1,3–1,7 N, średni szczyt 1,85 N.
- Śledzenie: błąd celowania tuż przed paszczą 2,2° (tolerancja paszczy ±5,3°). Bez sterowania bazą byłoby 5,7°.

## Etap 4 — ablacja neuronów (`sim/stage4_ablation.py`)

Z każdej z 20 populacji usuwam losowo ten sam odsetek neuronów, ale zostawiam ≥ 1 w każdej (20 neuronów to
minimum strukturalne: po 1 na populację). Dla każdej wielkości: 3 losowania × 10 prób. Warianty:

- bez kompensacji;
- z kompensacją homeostatyczną — ocalałe neurony przejmują synapsy usuniętych z populacji (wagi × n_pełne/n_zostało), a ocalałe MN przejmują ich włókna mięśniowe.

| neurony | sukces bez komp. | sukces z komp. | błąd celowania (bez / z) | reakcja [ms] (bez / z) | CPU [ms/cykl 10 ms] |
|---|---|---|---|---|---|
| 348 | 70 ± 0% | 70 ± 0% | 2,2° / 2,2° | 2177 / 2177 | 0,370 |
| 300 | 37 ± 12% | **73 ± 9%** | 2,4° / 2,4° | 3199 / 2340 | 0,348 |
| 150 | 0% | 17 ± 5% | 5,6° / 4,1° | — / 3569 | 0,244 |
| 60 | 0% | 0% | 6,5° / 13,8° | — | 0,183 |
| 30 | 0% | 0% | 4,8° / 3,0° | — | 0,176 |
| 20 | 0% | 0% | 6,2° / 6,0° | — | 0,173 |

Nokauty pojedynczych populacji w pełnym obwodzie (10 prób, pełny obwód = 70%):

| usunięte | sukces | co się dzieje |
|---|---|---|
| RR_resist (6) | 0% | 10/10 zgniecionych, szczyt 48 N — bez hamowania nie ma regulacji siły |
| RR_assist (6) | 0% | 9/10 bez chwytu — nie ma zatrzasku „łap” |
| wolne MN (4) | 10% | trzymanie zostaje bez delikatnych jednostek; 4 zgniecione |
| RR_hold (4) | 40% | 5 zgniecionych — bez stanu „trzymam” szybkie MN wracają |
| AOTU025 L+P | 50% | |
| IN_GABA nogi (10) | 50% | 2 zgniecione |
| AOTU019 L+P | 60% | |
| szybki MN zginacza (1) | 70% | bez zmian — do delikatnego chwytu niepotrzebny |

Kontrola mechanizmu (`--protected`): ablacja jak wyżej, ale moduł odruchu (16 neuronów) zostaje w całości.

| neurony | sukces bez komp. | sukces z komp. |
|---|---|---|
| ~160 | 13% | 33% |
| ~73 | 0% | 13% |
| ~43 | 0% (14 zgniecionych) | 0% (15 zgniecionych) |

### Wnioski

1. **Do 300 neuronów liczy się łączne pobudzenie, nie liczba komórek.** Bez kompensacji skuteczność spada do 37%, z kompensacją wraca do 73%, czyli poziomu pełnego obwodu. Ocalałe neurony przejmujące synapsy wystarczą, jak przy skalowaniu synaptycznym u zwierząt.
2. **Poniżej ~150 neuronów kompensacja już nie ratuje** (17% przy 150, 0% od 60 w dół). Pomiar wskazuje trzy przyczyny:
   - zatrzaski (RR_assist, RR_hold) z 1 neuronem nie mogą się samopodtrzymać, bo nie ma autapsy;
   - z puli 5 zginaczy zostaje 1. Jeśli to szybki MN, nie ma już wolnych jednostek do delikatnego trzymania (stąd zgniecenia), zgodnie z nokautem wolnych MN;
   - z 275 LC10a zostaje 6–12 i śledzenie traci precyzję (błąd 4–14° wobec tolerancji 5,3°).
3. **Najważniejsze dla „nie zgnieść” są neurony hamujące i wolne MN**, nie szybkie — dokładnie jak w zasadzie wielkości Hennemana.
4. **Koszt CPU prawie nie zależy od liczby neuronów:** 348 → 20 skraca cykl tylko 2,1× (0,37 → 0,17 ms). Przy tej skali dominuje narzut Pythona na krok, nie mnożenie macierzy N×N. Nawet pełny obwód zużywa ~4% budżetu 10 ms, więc oszczędzanie neuronów nie jest tu potrzebne.

## Co jest z konektomu, a co nasze (ważne na konkurs)

- **Z danych:** tożsamość i liczba neuronów, wszystkie liczby synaps między nimi, neuroprzekaźniki (znak), rozmiar MN (synapsy wejściowe), który wyznacza klasę szybki/pośredni/wolny.
- **Z literatury:**
  - parametry membrany (Shiu 2024);
  - stosunki rezystancji i siły klas MN (Azevedo 2020);
  - pola LC10a −15°…165° (Ribeiro 2018);
  - wzmocnienie pościgu ~2–3 (°/s)/° (Collie 2025).
- **Nasze (model, strojone w symulacji):**
  - 16 neuronów modułu odruchu i ich połączenia;
  - prądy tła (zastępują niezmodelowane wejścia, np. DNa02 ma silniejsze wejście z AN03A008 niż z AOTU);
  - wzmocnienia wejścia LC10a 0,5 i DNa02 2,5;
  - przydział aferentów do czujników;
  - mięsień → moment (k_muscle);
  - tłumienie prędkością szczęki (odpowiednik aferentów prędkości FeCO);
  - auto-trym DNa02, który kompensuje asymetrię L/P konektomu, inaczej dającą stały przechył ~7°.
- **Odchylenie od standardu:** wagi ln(1+N) zamiast liniowych jak u Shiu (o to prosiło zadanie). Logarytm ściska jedną silną synapsę AOTU→DNa02 i trzeba ją było kompensować wzmocnieniem DNa02.
- **Uproszczenia fizyki:**
  - wszystkie kontakty kulki mają tarcie μ = 1,0. Próba z gumowymi padami i śliską dłonią pogorszyła chwyt, bo kulka była wyciskana z „V”;
  - „oko” siedzi na osi bazy (kamera nieruchoma), nie na chwytaku. Oko na chwytaku dawało oscylacje ±40°;
  - przed puszczeniem kulki robot 1 s patrzy na nią i obraca się w jej stronę.
- **Słabe strony:**
  - 30% prób kończy się bez chwytu: kulka klinuje się albo odjeżdża w trakcie powolnego domykania;
  - reakcja 2 s jest daleka od muchy;
  - odwrócenie odruchu zrobiłem jako bramkowanie stanem aktywny/pasywny, a efekt w stanie pasywnym jest słaby (−0,7 Hz).

## Jak uruchomić

```bash
uv venv -p 3.12 .venv && uv pip install -p .venv/bin/python mujoco numpy matplotlib scipy pandas pyarrow
cd sim
../.venv/bin/python stage1_verify.py          # Etap 1
../.venv/bin/python stage2_test.py            # Etap 2 → results/stage2_raster.png
../.venv/bin/python stage3.py 10              # Etap 3, ziarna 0–9
../.venv/bin/python stage4_ablation.py        # Etap 4 → ablation_results.png, results/ablation.json (~35 s, 8 rdzeni)
../.venv/bin/python stage4_ablation.py --protected
../.venv/bin/python trial_plot.py 4 ../results/stage3_trial4.png      # przebieg jednej próby
../.venv/bin/python render_trial.py 4 0.3,0.7,1.5,2.6 ../results/x.png # klatki z próby
```

Ekstrakcję z MaleCNS (`extract_connectome.py`) trzeba uruchomić tylko po zmianie wyboru neuronów.
Wymaga pobrania ~1,1 GB do `data/malecns/` (adresy są w nagłówku skryptu). Wynik jest w repo jako `sim/circuit_malecns.json`.
