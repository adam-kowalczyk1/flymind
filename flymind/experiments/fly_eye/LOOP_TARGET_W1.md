# LOOP_TARGET — W1 „co widzi każde piętro oka” (zapisane PRZED uruchomieniem flyvis, 16 XI 2026)

Zgoda Adama: „Tak, zacznij W0–W1” (16 XI, po planie `reports/fly_eye_reverse_engineering_plan_20261116.md`).

## Pytanie
Czy gotowe oko flyvis (Lappalainen i in. 2024; 10 najlepszych modeli `flow/0000/000–009`, bez wybierania), zasilone
**klatkami z kamery nadgarstka robota** (MuJoCo), daje sensowne „piętra” widzenia: podział jaśniej/ciemniej
w L1/L2/Mi1/Tm3/Tm1/Tm2 oraz kierunek ruchu w T4/T5, który odwraca się, gdy ruch idzie w drugą stronę?
To jest atlas dla Adama i sprawdzenie, czy flyvis działa na **naszym** obrazie, a nie tylko na bodźcach z pracy.

## Wejście (W0, `w0_render.py`, wyrenderowane przed tym celem — tylko obraz, bez sieci)
5 scen po 125 klatek co 20 ms (50 bez ruchu, 50 ruchu, 25 bez ruchu): S1 spokój, S2 przedmiot w prawo 10 cm/s,
S2r to samo w lewo, S3 przedmiot unosi się do kamery, S4 obrót podstawy 0,3 rad. Ciemna kostka 4,5 cm na szachownicy blatu.
Optyka (`w1_atlas.py`): jasność „Rh1” → Gauss FWHM 5° → 721 kolumn flyvis (5,1°/kolumnę); kolumny poza polem kamery = stała szarość
(mediana 1. klatki). Ta sama reguła dla wszystkich kolumn. Żaden neuron poza fotoreceptorami nie dostaje bodźca.

## Kryteria (na model; liczone w `w1_analysis.py`, kolumny w polu kamery, klatki ruchu 50–124, odniesienie = klatka 49)
- **K1 jaśniej/ciemniej (scena S2):** korelacja Pearsona między kontrastem czasowym (jasność − średnia z poprzednich 200 ms)
  a zmianą aktywności ma oczekiwany znak: L1 −, L2 −, Mi1 +, Tm3 +, Tm1 −, Tm2 −. Model OK, gdy ≥ 5/6.
  **K1 PASS, gdy ≥ 8/10 modeli OK.**
- **K2 kierunek (S2 vs S2r):** suma wyprostowanych odpowiedzi podtypów. Zwycięzca T4 w S2 ∈ {a, b} (oś pozioma),
  a w S2r zwycięża jego para (a↔b). To samo dla T5. Model OK, gdy T4 i T5 spełniają oba warunki.
  **K2 PASS, gdy ≥ 8/10 modeli OK.**
- **W1 PASS = K1 i K2.**
- Opisowo (bez wpływu na werdykt): D1 = aktywność T4+T5 w S1 / w S2 (oczekiwane ≪ 1); D2 = czy przy zbliżaniu (S3)
  zwycięskie kierunki wskazują „na zewnątrz” (kierunki podtypów z modelu 000 wg `PREREG_BRIDGE.md`); D3 = zwycięzcy w S4.
- Atlas (obrazy, filmy GIF) z modelu 000.

## Zasady
- Jeden przebieg na modelach 000–009. Próba dymna potoku tylko na modelu 040 (poza zestawem), bez oceny kryteriów.
- Nie zmieniam progów ani optyki po wyniku. Wynik ujemny opisuję wprost.
- Najwyżej 3 procesy naraz. Bez ziaren (flyvis deterministyczny); świat W0 ma ziarno 23 504 001 (`SEED_REGISTRY.md`).

## Wyniki
`flymind/results/fly_eye_20261116/w0/` (klatki), `w1/` (`model_000–009.npz`, `w1_result.json`, `atlas_*.png`, `film_*.gif`),
`PRE_W1_HASHES.txt`.
