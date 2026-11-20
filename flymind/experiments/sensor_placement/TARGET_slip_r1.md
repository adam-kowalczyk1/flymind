# Cel testu: czy czujniki czują POŚLIZG (r1, 20 XI 2026) — spisany PRZED uruchomieniem

Pytanie (c) z planu Adama: czy 2× FSR402 poczuje, że trzymany przedmiot się wyślizguje. Literatura: owady czują
obciążenie/poślizg jako SPADEK siły (campaniform sensilla, Harris i in. 2022); FSR jest za wolny na drgania, więc
liczy się tylko siła normalna na polu czynnym.

## Model (MuJoCo, tylko symulacja)
- Szczęki: „schody” z prawdziwych siatek producenta (wewnętrzne ściany co 1 mm wzdłuż szczęki: wysunięcie i szerokość
  z punktów powierzchni, jak w placement.py); dłoń = płyta na z = −35,8 mm. Szczęka ruchoma na zawiasie modelu, silnik
  gear 3,35 N·m (jak so101.py), ctrl ∈ {0,15; 0,4}.
- Czujniki = płaskie walce Ø12,7 mm (tylko pole czynne), grubość 0,45 mm, na ścianie. Siła czujnika = suma sił
  normalnych kontaktów z tym walcem. Folia poza polem czynnym nie jest modelowana.
- Układy: **T** = czubek szczęki stałej (środek −7,9/−2,3/−96,2 mm, wystaje za krawędź) + A0 (−11,6/−0,1/−73,4);
  **H** = obecny hw2p (A0 + dłoń 2,9/−0,9/−35,8); **R** = najlepsza para r1 (szczęka ruchoma 11,9/−1,3/−54,9 i 11,9/2,0/−71,9).
  Każdy układ w osobnym przebiegu (czujniki zmieniają geometrię kontaktu).
- Przedmiot: pręt (kapsuła) w poprzek szczęk, długość 200 mm, Ø ∈ {8, 15, 25} mm, masa 60 g, na głębokości
  d ∈ {2, 6, 10} mm od czubka (S3) oraz pudełko 20×20×20 mm, d ∈ {15, 30} mm (S2); środek przedmiotu przesunięty
  w poprzek o 0 lub 60 mm (moment obrotowy).
- Szczęki skierowane w dół (grawitacja wyciąga przedmiot z czubków). Po chwycie (1 s) siła ciągnąca w dół rośnie
  0 → 20 N przez 4 s.
- Poślizg = przesunięcie przedmiotu względem chwytaka > 0,5 mm albo obrót > 2°.

## Miary (na układ)
- **M1:** odsetek prób, w których podczas trzymania (koniec 1. sekundy) ≥ 1 czujnik ma > 0,2 N (próg FSR ~20 g).
- **M2:** odsetek prób z poślizgiem, w których siła któregoś czujnika zmieni się o ≥ 20 % względem trzymania
  ≥ 20 ms PRZED początkiem poślizgu (ostrzeżenie).
- **M3:** odsetek prób z poślizgiem, w których w ciągu 200 ms PO początku poślizgu siła któregoś czujnika spadnie o ≥ 50 %
  (wykrycie wypadania).

## Kryteria
- **Q1:** T ma M1 ≥ 0,8 i M1(T) ≥ M1(H) + 0,3.
- **Q2:** T ma M3 ≥ 0,8.
- **Q3 (opis, bez progu):** M2 dla T, H, R — czy jakikolwiek układ ostrzega przed poślizgiem.
Mózg muchy nie jest tu używany. Wynik (także „nie czuje”) idzie do raportu bez zmian kryteriów.
