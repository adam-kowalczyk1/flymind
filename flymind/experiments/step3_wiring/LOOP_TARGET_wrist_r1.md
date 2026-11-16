# Krok 5 — nadgarstek sterowany siecią przez naturalny dotyk (cel zapisany PRZED testem, 16 XI 2026)

## Skąd droga (tylko dane, `wrist_screen.py`, `wrist_dn_inputs.py`, `explore_wrist*.py`)
Pule stępu nogi T1 L (dźwigacz / obniżacz = nadgarstek w naszym przypisaniu) nie odpowiadają na żadne czucie nogi (dotyk,
czujniki kąta, płytki włosków — pojedynczo i w parach: 0 Hz). W całym MaleCNS dźwigacz stępu dostaje 12 % wejścia od
neuronów zstępujących; największy to DNge078 (140 synaps), którego 13 % wejścia pochodzi od szczecinek mechanosensorycznych
głowy (BM, 69 neuronów). Bez robota: BM 40 mV → DNge078 119 Hz → dźwigacz stępu 20 Hz, pozostałe pule 0 Hz, identycznie
dla Glu ±1. (Droga wzrokowa LPLC4 → DNp07 → dźwigacz: DNp07 83 Hz, ale pula 0 Hz — w modelu za słaba.)

## Układ (`reflex5.py`; nic nie strojone)
Sieć „pre” + 69 BM + 2 DNge078 = 3219 neuronów. Czujnik dłoni robota (obok kamery) → BM (40 mV/N, maks. 40);
pady → szczecinki nogi T2 (bez zmian). Wyjścia jak w kroku 4; staw 3 = pule stępu (znak i k z kroku 2).
To przypisanie „dłoń przy kamerze = głowa” jest wyborem modelu [ANALOGIA].
- Próba W5: dłoń naciska walec 60 mm (≥ 1 N), potem 0,5 s sterowania siecią. Miara główna: ruch nadgarstka w kierunku
  unoszenia ≥ 0,02 rad. Sukces ścisły: do tego bark i łokieć ≤ 0,01 rad, szczęka nie zaciska, siła ramię↔blat ≤ 5 N.
- Próba C5: jak próba C kroku 4 (zaciśnij i trzymaj 2 s) + nadgarstek ≤ 0,01 rad.
- Odruch jest „w stronę dotyku” (w muszce: czyszczenie głowy), więc ZWIĘKSZA nacisk dłoni na przedmiot (w treningu mediana
  6,3 N, do 34 N w 0,5 s). To pokaz sterowania stawem, nie bezpieczne zachowanie; `palm_max` będzie raportowane.

## Trening (ziarno 21401, 3 pozy; nic nie zmieniano po obejrzeniu)
N: nadgarstek ruszył w 12/13 prób W i stał w 15/15 prób C (oba Glu). Sukces ścisły OBA: 4/13 (Glu +1), 7/13 (Glu −1).
Tasowania swobodne (2): nadgarstek 0/13. Zachowujące warstwy (2): nadgarstek ruszył w 11/13 w trzech z czterech przebiegów.

## Test
`--seed 21701` (W: 21 701 000–049, C: 21 701 100–149), 6 póz, **raz**. Sieci: N; F1–F5 (21 710 001–005); L1–L5
(21 720 001–005); oba znaki Glu.

## Kryteria
- **K5-A (sprawa 1, nadgarstek):** w sieci z danych nadgarstek rusza się (≥ 0,02 rad w kierunku unoszenia) w ≥ 80 % ważnych
  prób W5 ORAZ stoi (≤ 0,01 rad) w ≥ 95 % ważnych prób C5 — dla OBU znaków Glu. Spełnione → „nadgarstek jest sterowany
  siecią muszki przez naturalny dotyk (w symulacji)”.
- **K5-B (sprawa 2):** H-R5(F), H-R5(L): N lepsza na wyniku ścisłym OBA od każdego z 5 tasowań rodziny (McNemar + Holm).
  Oczekiwanie zapisane uczciwie: H-R5(F) możliwe, H-R5(L) raczej nie (tasowania warstwowe też ruszają nadgarstkiem).
- Opisowo: `palm_max`, ruch stawów, powody porażek.
