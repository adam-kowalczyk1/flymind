# LOOP_TARGET — W5 „LPLC2 jako bramka AND czterech ramion” (zapisane PRZED testem, 17 XI 2026)

Polecenie Adama (17 XI): „Nie nie zamykaj, badaj dalej /alien-space-of-science”.

## Skąd hipoteza
- B1 i B1b (inna sesja): LPLC2 = **suma** (synapsy × pobudzenie T4/T5) nie odrzuca przesuwania. Przy przesuwaniu w jedną stronę
  cały obraz pobudza jeden podtyp T4/T5, a suma tego nie odróżnia od zbliżania.
- Biologia (REPORTED, bez czytania pełnych tekstów): LPLC2 odpowiada na ruch **na zewnątrz w kilku kierunkach naraz**
  („przeciwstawność ruchu promieniowego”, Klapoetke i in. 2017); model OppLoD (Zhao i in. 2023, arXiv 2302.10284) robi to ręcznie
  zaprojektowanymi filtrami, bez konektomu.
- Przegląd w Lacuna (17 XI): praca z flyvis o zbliżaniu (Garcia-Duran, …, Lappalainen, arXiv 2611.14498, 10 XI 2026) używa
  **wytrenowanego** odczytu i sama pisze, że brakuje w niej LPLC2. Nie znalazłem pracy, która liczy LPLC2 z flyvis przez **ramiona z konektomu**
  regułą bez parametrów. Ocena nowości: „częściowo zrobione” (zasada znana z biologii i robotyki), „otwarte” w połączeniu flyvis + MaleCNS.

## Pytanie
Czy LPLC2 policzony jako **średnia geometryczna czterech ramion** (ramię g = synapsy od T4g + T5g z MaleCNS, z ich położeniem w kolumnach)
rozróżnia zbliżanie od oddalania i przesuwania — i czy wynik zależy od prawdziwego przypisania podtypów do ramion?

## Odczyt (`w5_and.py`; bez żadnego dopasowanego parametru)
d_g(t) = Σ synapsy ramienia g × max(0, aktywność T4/T5 − stan przed ruchem) (dokładnie jak B1, wariant 0).
**AND** = (d_a · d_b · d_c · d_d)^(1/4); szczyt w fazie ruchu. **LIN** = Σ_g d_g (= B1 wariant 0; przed testem sprawdziłem na modelu 000,
że kod odtwarza liczby B1 co do bitu, różnica 0,00). Hamowanie LPi pomijam (w B1 zmieniało wynik o ~5 %).
Mapa: `results/v1_camera/bridge_b1/map_rot30.npz` (inna sesja; tylko odczyt; sumy w `bridge_b1/PRE_BRIDGE_HASHES.txt`).
Bodźce: identyczne jak B1 (`bridge_loom.movies`). Komórki i miary jak B1 (`bridge_analysis.py`): LPLC2 ze środkiem pola ≤ 4 kolumny od środka bodźca.

## Modele
flyvis `flow/0000/020–049` (30 modeli; dla LPLC2 nieużywane — B1 użył 000–009, B1b 010–019). Model 000 posłużył tylko do sprawdzenia kodu
i ślepej próby dymnej (liczb AND nie oglądałem).

## Kryteria
- **W5 PASS (ciemny dysk, reguła AND, obrót 30°)**, jak B1: mediana LI > 0 **i** zbliżanie wygrywa z oddalaniem i przesuwaniem w ≥ 80 % przypadków
  (30 modeli × 7 środków) **i** układ prawdziwy lepszy od każdej z 23 permutacji podtypów.
- **W5-jasny** (osobna etykieta): to samo dla jasnego dysku.
- **W5-kamera** (osobna etykieta): sceny z kamery robota (W0, 16 XI), komórki LPLC2 z ≥ 50 % synaps w polu kamery, reguła AND;
  model OK, gdy zbliżanie (S3) > spokój, bok, bok wstecz i obrót ramienia (S4). PASS, gdy ≥ 80 % modeli.
- Opisowo: reguła LIN na tych samych modelach (porównanie AND vs LIN); obrót mapy 210° (kontrola, modele 020–029, oczekuję spadku);
  średnie odpowiedzi; liczba modeli z dodatnią medianą LI.

## Przewidywanie
AND powinno odrzucić przesuwanie (pobudza 1–2 ramiona). Ryzyka: (1) oddalanie — ramiona dostają ruch do środka, ale przy złym
rozkładzie przestrzennym synaps mogą i tak „świecić”; (2) słabe T5 w flyvis dla ciemnego dysku (B1: ciemny gorszy niż jasny) —
spodziewam się, że ciemny dysk może nie przejść, a jasny tak.

## Zasady
Jeden przebieg. Najwyżej 3 procesy, wątki torch 3. Bez ziaren (wszystko deterministyczne). Po wyniku nie zmieniam reguły, progów ani bodźców.
PASS → osobny cel: droga LPLC2 → neurony zstępujące → sieć nogi (najpierw sprawdzenie w danych, czy dochodzi do przedniej nogi).
FAILED → raport; bez strojenia.
Wyniki: `flymind/results/fly_eye_20261117/w5/` (`discs_rot30_*.npz`, `discs_rot210_*.npz`, `cam_*.npz`, `w5_result.json`, sumy przed/po).
