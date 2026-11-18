# Oko muchy — bramka G2 w modelu impulsowym (ALIF) i 6 decyzji dla Adama (16 XI 2026)

Autor: Claude (Opus 5.5), sesja poboczna. Wszystko w symulacji, bez robota, bez commita.
Etykiety: VERIFIED · PARTIALLY VERIFIED · REPORTED · INFERRED · HYPOTHESIS · NOT VERIFIED · FAILED · NOT IMPLEMENTED.

## 0. Najkrócej

- **Pytanie:** czy czujniki ruchu muchy (T4/T5) zbudowane z mapy połączeń MaleCNS rozróżniają kierunek ruchu, gdy wszystkie
  neurony mają **te same** ustawienia sieci impulsowej, której FlyMind używa do sterowania ramieniem (ALIF)?
- **Odpowiedź: nie. G2 = FAILED.** Kierunkowość wynosi ok. 0 (mediany od −0,005 do 0,008 przy progu 0,20).
- **Co działa:** podział na „robi się jaśniej” i „robi się ciemniej” wyszedł sam z połączeń: 7/7 typów (G1 PASS).
- **To ten sam wynik co rano w modelu stopniowanym (r1).** Zmiana rodzaju neuronu nic nie dała. Wniosek się wzmacnia:
  **mapa połączeń mówi, kto z kim jest połączony, ale nie mówi, jak szybko działa każdy neuron, a kierunek ruchu wymaga właśnie tego.**
- Zgodnie z zasadą: **STOP.** Niczego nie stroję. Plan kroku LPLC/DN nie powstaje, bo warunek („jeśli G2 przejdzie”) nie jest spełniony.

## 1. Co sprawdziłem i jak

| Element | Ustawienie | Źródło |
|---|---|---|
| Sieć | wycinek prawego oka z MaleCNS: 5120 neuronów (L1–L5, Mi, Tm, T4a–d, T5a–d, LPLC2, LC4, R1-R6), ten sam co w r1 | `experiments/v1_camera_input/optic_slice.py` (bez zmian) |
| Neuron | ALIF projektu, `ALIFParams()` **bez zmian, jednakowy dla wszystkich typów** | `flymind/alif.py`, `alif_sparse.py` (bez zmian) |
| Wagi | znak × 0,2 mV × liczba synaps (jak w sieci nogi); reguła stabilności nie musiała nic zmniejszać | `experiments/fly_eye/g2_alif.py` |
| Wejście | obraz → model fotoreceptora → prąd **tylko do L1/L2/L3 wszystkich kolumn**, jedną regułą. **Żaden T4/T5/LC nie dostał prądu z bodźca.** | jw. |
| Bodźce | krawędzie jaśniejsze i ciemniejsze, 6 kierunków, 3 prędkości (60/120/240 °/s) + błysk całego pola | `eye_gate.py` (bez zmian) |
| Kontrola | 40 sieci z przetasowanymi połączeniami w obrębie typów | `eye_gate.shuffle_typed` (bez zmian) |
| Kryteria | identyczne z porannym r1, zapisane przed uruchomieniem | `experiments/fly_eye/LOOP_TARGET_G2_ALIF.md`, hasze `results/fly_eye_20261116/PRE_RUN_HASHES.txt` (19:16) |
| Ziarna | dane 23 502 001–010, tasowania 23 503 001–040 — zużyte | `experiments/fly_eye/SEED_REGISTRY.md` |

Sprawdzenie kodu: `test_g2_alif.py` — wersja liczona „wiele przebiegów naraz” daje **identyczne impulsy** jak oryginalny
silnik ALIF (VERIFIED). Próba dymna: sieć stabilna, ok. 23 Hz w spoczynku.

## 2. Wynik

Przebieg: 16 XI 19:16–20:45, 41/41 plików, bez błędów. Analiza: niezmieniony `eye_gate_analysis.py` →
`results/fly_eye_20261116/gate_result.json`.

| Kryterium | Wynik | Werdykt |
|---|---|---|
| **G1** jaśniej/ciemniej (≥ 6/7 typów) | L1 −1, L2 −1, Mi1 +1, Tm3 +1, Tm1 −1, T4 +1, T5 −1 → **7/7** | **PASS** |
| **G2** kierunek (≥ 3/4 podtypów T4: mediana DSI ≥ 0,20 i > tasowania) | T4a 0,008 · T4b −0,001 · T4c −0,005 · T4d −0,004 (tasowania, 95. percentyl: 0,004–0,006) | **FAILED (0/4)** |
| T5 (opisowo) | T5a 0,001 · T5b 0,003 · T5c 0,000 · T5d −0,004 | brak kierunkowości |
| **G3** oś Mi9→Mi4 (≤ 30°) | 41°, 40°, 45°, 50° (przypadek ≈ 45°) | **FAILED** |
| **BRAMKA** | | **FAILED → STOP** |

DSI = 0 to brak preferencji kierunku, 1 to reakcja tylko na jeden kierunek. Prawdziwe T4 mają zwykle DSI ok. 0,3–0,8 (LIT, NOT VERIFIED u nas).
T4a 0,008 jest minimalnie powyżej tasowań (0,006), ale to jeden podtyp i wartość ~25× poniżej progu: bez znaczenia (INFERRED).

| Wariant (wszystkie na tym samym wycinku) | Mediany DSI T4 | Werdykt |
|---|---|---|
| r1 — stopniowany, jednakowe τ (rano) | 0,001–0,008 | FAILED |
| r2 — stopniowany, τ z literatury | 0,025–0,030 | FAILED |
| **ALIF, jednakowe parametry (ten raport)** | **−0,005–0,008** | **FAILED** |
| flyvis (gotowy model z Nature 2024) | liczy się w innej sesji | — |

**Poziom dowodu:** G1 PASS i G2 FAILED to **VERIFIED (w modelu)**: jeden przebieg wg zapisanego celu, kod sprawdzony testem.
To mówi o **tym modelu** (jednakowe ALIF na wycinku 5120 neuronów), nie o prawdziwej musze. Prawdziwe T4/T5 są
kierunkowe (Maisak 2013, LIT).

**Dlaczego tak wyszło (INFERRED, zgodne z literaturą):** T4 porównuje sygnały z sąsiednich kolumn, które docierają
z różnym opóźnieniem (Mi1/Tm3 szybko, Mi4/Mi9 wolniej). Gdy wszystkie neurony mają te same stałe czasowe, opóźnień
nie ma i sygnały z obu kierunków wyglądają tak samo. Ani model stopniowany (r1), ani impulsowy (dziś) tego nie zmienia.
Stałe czasowe z literatury (r2) dały ślad kierunkowości (0,03), ale też za mało.

**Koszt obliczeń (pomiar przy okazji):** jedna sieć 5120 neuronów, 120 przebiegów naraz po ok. 12 s czasu modelu
zajęła 15 min na jednym rdzeniu. Pełny rdzeń ruchu (47 473 neurony) byłby ok. 9× większy. REPORTED (z czasów plików).

**Uwaga uczciwości:** to już czwarte podejście do tej bramki dziś (r1, r2, flyvis w toku, to). Każde było zapisane
przed uruchomieniem i różni się jedną rzeczą. Ten przebieg zamówiła sesja główna, bo plan z 12 XI wprost mówi o ALIF.
Nie jest to „próbowanie, aż wyjdzie”: wynik jest ujemny i zostaje.

---

## 3. Sześć decyzji z planu 12 XI (§7) — prostym językiem

Część z nich już się zdezaktualizowała, bo dziś zrobiono sporo pracy. Przy każdej piszę, co jest teraz, i jedną rekomendację.

1. **Od czego zacząć: „coś się zbliża” czy „śledzenie celu”?**
   Teraz: plan z 12 XI mówił „zbliżanie → włókno olbrzymie DNp01 → stop”. Raport z 16 XI poprawił to: DNp01 słabo
   dochodzi do przedniej nogi (służy do skoku). Lepsza droga to **LPLC4 → DNp07 → staw stopy przedniej nogi** (u muchy:
   wyprostowanie nóg przy lądowaniu). Ten sam staw steruje już nadgarstkiem ramienia (kroki 5–6). [`fly_eye_research_20261116.md`, REPORTED z tamtego raportu]
   **Rekomenduję:** tak, najpierw „coś się zbliża”, ale wyjście przez **DNp07 (lądowanie → nadgarstek)**, nie DNp01.

2. **Jak dopasować pole widzenia kamery (ok. 70°) do oka muchy (prawie cała sfera)?**
   (a) ścisnąć całe oko w 70° — zniekształca kąty; (b) użyć tylko przednich kolumn oka; (c) kilka kamer w symulacji.
   **Rekomenduję (b):** kąty zostają prawdziwe, a zbliżanie z przodu to dokładnie to, czego potrzebujemy. Opisane jako decyzja inżynierska.

3. **Czy wolno „dopasować” parametry neuronów oka (uczenie), skoro sama mapa połączeń nie wystarcza?**
   Teraz: odpowiedziałeś już częściowo („najpierw opcja 1 — stałe czasowe z literatury, potem opcja 2 — flyvis, i tak na zmianę”).
   Opcja 1 nie przeszła; flyvis (gotowy, dopasowany przez autorów model) właśnie liczy się w innej sesji.
   **Rekomenduję:** nie trenować naszych parametrów samodzielnie. Jeśli flyvis przejdzie — użyć go jako
   „siatkówki i czujników ruchu”, a od T4/T5 dalej (LPLC4, DNp07, noga) zostawić MaleCNS. Jawnie nazwać to hybrydą
   (inny konektom, samica, parametry dopasowane przez autorów pracy z Nature 2024).

4. **Zgoda na mapę kolumn (O0 — tylko analiza danych)?**
   Teraz: częściowo zrobione — wycinek prawego oka (5120 neuronów, kolumny heksagonalne) istnieje i jest używany w testach.
   **Rekomenduję:** tak, dokończyć (mapa dla obu oczu, potrzebna przy zbliżaniu z przodu).

5. **Zgoda na pomiar kosztu obliczeń?**
   Teraz: w praktyce zmierzony przy okazji tego testu (patrz §2). **Rekomenduję:** tak — przyjąć ten pomiar; osobny nie jest potrzebny.

6. **Co pokazać 1 grudnia?**
   **Rekomenduję:** V5 z uczciwym opisem („wejście wzrokowe to dziś heurystyka koloru, nie oko muchy”) + wynik bramek oka
   jako wynik naukowy: „sama mapa połączeń daje podział jaśniej/ciemniej, ale nie daje czujnika kierunku — potrzebna jest
   dynamika neuronów”. Jeśli zdąży flyvis — dodać jego wynik.

## 4. Co robię do czasu Twojej odpowiedzi
Nic więcej nie uruchamiam w sprawie oka. Bramka nie przeszła, więc zgodnie z zasadą: STOP, bez zmieniania parametrów
„aż wyjdzie”. Wynik flyvis policzy i opisze druga sesja. Plan kroku LPLC → DN przygotuję dopiero, gdy jakiś wariant
czujników ruchu przejdzie bramkę.
