# Cel testu „hamulec” r1 (19 XI 2026), spisany PRZED testem

## Pytanie
W teście „nie dać się dotknąć” r1 (FAILED A1) ramię ze wzrokiem unikało dotyku dłoni rzadziej (9/15) niż bez wzroku (14/15).
Diagnoza na ziarnach rozwojowych 21 950 001–010 (`diag_vision.py`, `analyze_diag.py`, katalog `results/step3_20261115/diag_vision/`)
dała hipotezę:
dotyk dłoni (szczecinki głowy BM) zapala pętlę wzajemnie się pobudzających neuronów DNge078 ↔ DNge022 (+ GNG117, GNG423),
która napędza cofnięcie przez nogę. Zbliżająca się ręka (oko → neurony zstępujące wzrokowe DNp06, DNp35, DNp71, DNpe045,
DNpe053, DNp104) mocniej pobudza dwa hamujące neurony zstępujące **DNg98 i DNg70** (po 2 komórki), które hamują DNge078 i gaszą pętlę.

Rozwój (15 prób na warunek, ziarna 001–005): wyciszenie wyjść DNg98+DNg70 → ze wzrokiem unika 15/15 (0,55 s dotyku,
bez wyciszenia 10/15, 1,23 s); bez dotyku 0/15 (ramię stoi); 3 losowe zestawy 4 podobnych DN: 11/15, 9/15, 10/15.

## Test (raz, nowe ziarna)
- Sieć z danych, Glu −1, szum σ 2, czujniki hw2p (A0 szczęka stała + P dłoń), ręka do dłoni, 3 kierunki, ziarna **21 954 001–005**.
- Warunki (zawsze ze wzrokiem):
  - **N full**: bez wyciszeń;
  - **S full** i **S numb**: wyciszone wyjścia 4 komórek DNg98 + DNg70 (`silence_S.json`); numb = bez dotyku;
  - **C1–C3 full**: wyciszone wyjścia 4 losowych DN (`silence_C*.json`), losowanych ziarnem 21 954 901 z tej samej puli
    (DN aktywne 60–160 Hz po dotyku w danych rozwojowych, z przewagą wyjść hamujących; pula w `control_pool.json`).
- Wyciszenie = zerowanie wyjść (jak wycięcie DNg15+DNge078 w avoid r1). Unika = czas dotyku < czas ramienia nieruchomego − 0,2 s
  (nieruchome hw2p: przód 1,63 s, lewo 1,80 s, prawo 1,63 s).

## Kryteria (liczy `analyze_diag.py KATALOG --brake`)
- **B1:** S full unika w ≥ 4/5 ziaren w każdym kierunku.
- **B2:** S numb NIE unika w ≥ 4/5 ziaren w każdym kierunku (wyciszenie samo nie rusza ramieniem).
- **B3:** średni czas dotyku S full ≤ N full − 0,3 s.
- **B4:** każdy z 3 losowych zestawów: średni czas dotyku ≥ S full + 0,3 s (losowe wyciszenie nie daje tego samego).
- **PASS** = B1 ∧ B2 ∧ B3 ∧ B4.

## Co wolno potem powiedzieć
- PASS: „wzrok osłabia cofnięcie przez dwa konkretne neurony zstępujące (DNg98, DNg70); ich wyciszenie przywraca unikanie” —
  przyczynowo w tym modelu (symulacja, 1 sieć z danych). Nie wolno: że tak jest u prawdziwej muchy (funkcji DNg98/DNg70 nie znam z literatury).
- FAILED: opis, które kryterium nie przeszło; hipoteza nie potwierdzona.
- Wyciszenie to narzędzie badawcze, a NIE zmiana sterowania ramienia (mucha ma decydować bez naszych poprawek).

## Ograniczenia znane przed testem
Pętla i hamulec znalezione na tych samych danych rozwojowych, które dały hipotezę; dlatego test na nowych ziarnach.
Zestawy kontrolne mają słabsze wyjścia hamujące niż DNg98/DNg70 (−140 do −1200 vs −980 do −2070, suma wag) — kontrola nie jest idealnie dopasowana.

## Zmiana przed testem (19 XI 11:23)
Pierwsza wersja celu (hash 11:20:23) miała ziarna 21 951 xxx, które w rejestrze są już zajęte przez test kroku 4 r2.
Uruchomienie zatrzymano w trakcie budowania sieci, zanim policzyła się jakakolwiek próba (0 plików wyników).
Ziarna zmienione na 21 954 001–005, losowanie kontroli na 21 954 901 (nowe zestawy C1–C3). Kryteria bez zmian.
