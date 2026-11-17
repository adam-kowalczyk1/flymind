# LOOP_TARGET — W8 „powtórzenie W7-kamera: nowe sceny, nowe modele” (zapisane PRZED testem, 17 XI 2026)

Kontynuacja polecenia Adama „badaj dalej” (17 XI).

## Skąd
W7 (modele 000–019, przypisanie ramion z kierunków zmierzonych w każdym modelu, reguła AND): główne kryterium (ciemny dysk) FAILED,
jasny dysk FAILED o włos (75 % wygranych przy progu 80 %), ale **osobna etykieta „kamera” PASS: 18/20 modeli**
(zbliżający się przedmiot > spokój, bok, bok wstecz, obrót ramienia). To była etykieta poboczna na tych samych 5 scenach,
na których ustalałem odczyt od 16 XI — wymaga powtórzenia na nowych danych.

## Test
- Sceny: `w0c_render.py` (wyrenderowane przed tym celem, obejrzane tylko klatki): te same 5 typów ruchu co W0, ale **dwa nowe przedmioty**
  (jasna kostka `hard_slick`, brązowa `mid`; w W0 czarna) i tor przesunięty o 2 cm w prawo i 2 cm w górę kadru. Bez fizyki.
- Modele: flyvis **020–049** (30 modeli; w W7 nieużyte; dla nich nigdy nie liczono przypisania z pomiaru).
- Odczyt: **identyczny jak W7** (`w7_run.py cam`, `map_rot30.npz`, AND, przypisanie z krawędzi).
- Ocena: `w8_analysis.py` — komórki LPLC2 z ≥ 50 % synaps w polu kamery; model OK, gdy szczyt AND w S3 (zbliżanie) > S1, S2, S2r, S4.

## Kryteria
- **W8 PASS:** dla **obu** przedmiotów ≥ 80 % modeli OK (≥ 24/30).
- Opisowo: reguła LIN; wariant bez przypisania (`w5_and.py cam`, tożsamość jak B1/W5) na tych samych scenach i modelach —
  pokazuje, ile daje samo przypisanie; ile razy zbliżanie wygrywa z każdą sceną osobno; mediana stosunku zbliżanie / obrót ramienia.

## Co wolno wnioskować
PASS → „w symulacji, na obrazie z kamery robota, LPLC2 policzony z oka flyvis przez ramiona MaleCNS (reguła AND, kierunki skalibrowane
w każdym modelu) odróżnia zbliżający się przedmiot od ruchu w bok i od obrotu własnego ramienia”. To nadal **przewidywanie modelu**;
dyski z testów B1/W5/W7 (ciemne) nadal nie przechodzą — trzeba to mówić razem.
FAILED → wynik W7-kamera był przypadkiem.

## Zasady
Jeden przebieg; najwyżej 3 procesy; bez ziaren. Po wyniku nie zmieniam scen, reguł ani progów.
Wyniki: `flymind/results/fly_eye_20261117/w8/` (`al_*.npz`, `id_*.npz`, `w8_result.json`, sumy przed/po).
