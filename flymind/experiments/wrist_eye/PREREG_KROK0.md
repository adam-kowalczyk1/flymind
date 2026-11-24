# Krok 0 — samo oko na kamerze nadgarstka w MuJoCo (24 XI 2026, zapisane PRZED pierwszym przebiegiem oka na tych scenach)

Bez sieci, bez sprzętu, bez treningu. Pytania (Adam): (1) czy oko wykrywa zbliżenie kuli przy nieruchomym ramieniu?
(2) czy mały ruch ramienia (jak wcześniejsza reakcja przy Glu −1) zauważalnie zmienia ten sygnał?

## Obraz
Kamera „eye” na chwytaku (so101.py), scena bez przedmiotów, światło rozproszone jak vision_manipulation.Eye, bez cieni. Render 640×400 →
średnia bloków 4×4 → 160×100, szarość 0,299/0,587/0,114, uint8 (jak droga prawdziwej kamery). 100 klatek/s (takt sterowania 10 ms).
Kula: promień 2 cm, ciemna (0,1), tylko rysowana (bez kontaktu i fizyki). Tor w ŚWIECIE stały: punkt startowy 25 cm przed kamerą w pozie
startowej, wzdłuż jej osi; rusza w t = 1,367 s, 0,3 m/s, staje 6 cm od POCZĄTKOWEGO położenia kamery w t = 2,0 s (jak dłoń w avoid.py).
W sytuacjach bez ruchu kuli kula stoi w punkcie startowym (jest w kadrze).

## Ruch kamery
15 zapisanych trajektorii barku/łokcia/nadgarstka: `avoid_r1/test/N_g-1_palm_numb_*.npz` (Glu −1, sam wzrok, sieć z danych; 3 kierunki × 5 ziaren),
odtworzone w oryginalnym tempie (1 próbka = 10 ms, 3,5 s) i tej samej pozie startowej — kąty ustawiane wprost (kinematyka), jak w oryginale.
Obrót kamery w tych zapisach: najwyżej 0,09–0,93°. Nadgarstek w nich stoi.
Kontrola czułości: te same trajektorie z przemieszczeniem stawów ×5 i ×20.

## Cztery sytuacje
S nieruchomo · K sama kula · R sama kamera · KR oba ruchy. Przed każdą: nowe oko i 2,0 s tej samej nieruchomej klatki startowej (≥ 8 stałych
adaptacji 0,25 s), potem 3,5 s próby z identycznymi czasami klatek. Szum kamery: główny pomiar bez szumu; do progu „zauważalnie” 10 pól szumu
σ = 3 (jak `oko_mucha.SIGMA`; ziarna 27 400 001–010), to samo pole w czterech sytuacjach.

## Oko
Główne: `oko_mucha.FlyEye(out_full=OUT_FULL2, vshs=True, g0=G0)`, dokładnie jak `live_avoid.make_eye("mucha")`. Ustawienia i skróty plików w
`eye_settings.json` (zapisane przed przebiegiem). Dodatkowo tylko w tabeli: `FlyEye3()` (wersja 3, nie domyślna). Nic nie stroję.
Sygnał do neuronów: `eye.loom` L / P [mV], 0–40. Nieobcięty: out / OUT_FULL × 40. Uwaga: oko liczy kod, nie neurony z danych.

## Kryteria
**P1 (wykrywa):** szczyt max(L, P) w K w oknie 1,367–2,1 s ≥ 20 mV i ≥ 4 × szczyt w S — w ≥ 9/10 pól szumu. „Słabo”: 7–20 mV (7 mV = próg
pobudzenia neuronu w modelu stałym prądem). Poniżej 7 mV: nie wykrywa.
**P2 (mały ruch zmienia):** Δ = KR − K (to samo pole szumu / bez szumu), największe |Δ| strony w oknie 1,1–2,5 s. „Zauważalnie” dla trajektorii, gdy
|Δ| bez szumu ≥ 2 mV ORAZ ≥ 10 % szczytu K ORAZ > 95. percentyl największej różnicy między dwoma polami szumu tej samej sytuacji K.
TAK, gdy ≥ 12 z 15 trajektorii; CZĘŚCIOWO 4–11; NIE ≤ 3. Osobno fałszywy alarm: szczyt R ≥ 7 mV.
Wtórnie: to samo dla ×5 i ×20; całka sygnału [mV·s]; przebicie 40 mV (obcięcie mogłoby ukryć różnicę).

## Sprawdziany aparatury
Adaptacja identyczna we wszystkich sytuacjach; S bez szumu = 0 mV; kula w kadrze; to samo oko na scenie kalibracyjnej oko_mucha (24 100 900) ≈ 1.
Po wyniku STOP do przeglądu (bez poprawek i kolejnych prób).
