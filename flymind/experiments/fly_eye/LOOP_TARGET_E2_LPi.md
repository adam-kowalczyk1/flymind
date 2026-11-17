# LOOP_TARGET — E2 „hamowanie LPi” (zapisane PRZED testem, 17 XI 2026; Adam: „Tak, uruchom E2”)

## Skąd
E1 (`results/fly_eye_20261117/e1/`, odczyt danych): do LPLC2 i LPLC4 **nie dochodzi** sygnał o ruchu własnego ciała
(wstępujące 0 % i 0,19 % wejścia; przez jednego pośrednika 0,13 % i 0,94 %; neurony zstępujące 0,04–0,05 %).
Kopia ruchu z ciała nie jest więc w danych drogą, którą mucha odróżnia własny obrót od zbliżania (VERIFIED liczby).
W danych jest za to hamowanie wewnątrz oka: LPi → LPLC2 = 4,6 % wejścia, głównie glutaminian (hamujący).
W literaturze (Klapoetke i in. 2017, REPORTED) LPLC2 odrzuca ruch całego pola właśnie przez LPi: ruch „do środka” hamuje.
Nasz odczyt W5–W8 brał tylko T4/T5 (32 % wejścia LPLC2) i **pomijał LPi**.

## Test
- Kod `e2_lpi.py` (sprawdzenie `test_e2.py` OK), mapa `results/v1_camera/bridge_b1/map_rot30.npz` (zawiera LPi i krawędzie LPi→LPLC2, 9 061 synaps).
- Odczyt jak W7/W8 (przypisanie kierunków z pomiaru w każdym modelu, `w7_run.align`), plus jedna warstwa z danych:
  aktywność LPi = średnia ważona synapsami prostowanej aktywności T4/T5 (mianownik = wszystkie synapsy T4/T5 tej komórki);
  ramię LPLC2 = max(0, pobudzenie T4/T5 − Σ synapsy LPi→LPLC2 × aktywność LPi). Ramię hamowane = **warstwa wyjściowa z nazwy typu**
  (LPi43 → 3, LPi3412 → 1 i 2 po połowie, LPi2c → 2; INFERRED z nazewnictwa „wejście-wyjście”). Znak: tylko krawędzie hamujące (wszystkie takie są).
  LPi → LPi pominięte. **Bez stałych do dopasowania.** Równolegle liczony wariant bez LPi na tych samych symulacjach.
- Sceny: **nowe `w0d`** (`w0d_render.py`, przedmiot `heavy`, tor −2 cm w lewo i w dół; obejrzane tylko klatki — w renderze kostka wychodzi
  jasnoszara, prawie biała) oraz sceny W8 (`w0c`, hard_slick i mid).
- Modele: flyvis 000–049 (3 procesy po ok. 17 modeli).
- Ocena `e2_analysis.py` = reguła W8 (`w8_analysis.cam_eval`): komórki LPLC2 z ≥ 50 % synaps w polu; model OK, gdy szczyt AND w zbliżaniu > spokój, bok, bok wstecz, obrót ramienia.

## Kryteria
- **E2 PASS:** na `w0d`, wariant z LPi, reguła AND: ≥ 80 % modeli OK (≥ 40/50).
- Opisowo: wariant bez LPi (ile daje samo LPi); sceny W8 z LPi i bez (W8 „przed i po”); reguła LIN; mediana zbliżanie / obrót ramienia.

## Co wolno wnioskować
PASS → „w symulacji hamowanie LPi z danych MaleCNS wystarcza, by LPLC2 z oka flyvis odróżniał zbliżanie od ruchu w bok i obrotu ramienia
na nowych scenach” (przewidywanie modelu; dyski B1/W5/W7 nadal nie przechodzą). FAILED → samo LPi w tej postaci nie tłumaczy porażki W8.

## Zasady
Jeden przebieg; najwyżej 3 procesy; bez ziaren. Po wyniku nic nie zmieniam (scen, reguł, progów, mapowania warstw).
Wyniki: `flymind/results/fly_eye_20261117/e2/` (`{lpi,nolpi}_{w0d,hard_slick,mid}_*.npz`, `e2_result.json`, sumy przed/po).
