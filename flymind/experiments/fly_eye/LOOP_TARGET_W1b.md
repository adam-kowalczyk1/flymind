# LOOP_TARGET — W1b „czy czujniki kierunku T4/T5 działają na obrazie z kamery robota” (zapisane PRZED testem, 17 XI 2026)

Zgoda Adama: „dalej kroki i badaj” (17 XI), po propozycji W1b z raportu `reports/fly_eye_w0_w1_atlas_20261116.md` §5.

## Skąd ten test
W1 (16 XI) = FAILED: kryterium K2 („który podtyp wygrywa”) przeszło w 1/10 modeli. Analiza po fakcie pokazała, że **ten sam podtyp**
porównany przy ruchu w prawo i w lewo zachowuje się poprawnie (T4b 8/10, T4a 9/10, T5a 8/10, T5b 7/10 modeli; razem 32/40).
To była miara wybrana po obejrzeniu danych, więc wymaga potwierdzenia na **nowych scenach**. Kierunku góra/dół (podtypy c, d) nikt jeszcze nie oglądał.

## Sceny (`w0b_render.py`, wyrenderowane przed tym celem — sam obraz, bez sieci; obejrzałem tylko klatki)
8 scen: 2 przedmioty × 4 kierunki. Przedmioty: kostka jasna (`hard_slick`, jaśniejsza od blatu) i brązowa (`mid`, ciemniejsza) — w W1 była czarna.
Tor przesunięty o 2 cm w prawo i 2 cm w górę względem osi kamery (w W1 na osi). Ruch: w prawo/lewo kadru 10 cm, w górę/dół 8 cm, w 1 s.
Kamera, poza ramienia, światło, czas (50 + 50 + 25 klatek co 20 ms) i optyka oka (`w1_atlas.hex_movie`) jak w W1.

## Miara (`w1b.py`, sprawdzona `test_w1b.py`; próba dymna potoku na modelu 040 bez oglądania liczb)
Odpowiedź podtypu = Σ max(0, aktywność − stan w klatce przed ruchem) po kolumnach w polu kamery i klatkach od początku ruchu (jak W1).
DI = (R_pref − R_null)/(R_pref + R_null), sumy po obu przedmiotach. Strona preferowana zapisana z góry:
**a = w lewo kadru, b = w prawo, c = w górę, d = w dół** (kierunki T4 modelu 000 z `PREREG_BRIDGE.md`: 178°, −9°, 59°, −84°). Poprawnie = DI > 0.

## Kryteria — modele flyvis 000–009 (te same co W1, sceny nowe)
- **K2b (poziom: T4a, T4b, T5a, T5b):** ≥ 80 % par podtyp × model poprawnych (≥ 32/40) **i** każdy podtyp poprawny w ≥ 6/10 modeli.
- **K2c (pion: T4c, T4d, T5c, T5d):** te same progi. Osobna etykieta (nowe przewidywanie).
- **W1b PASS = K2b.**
- Opisowo: to samo na modelach 010–019 (nieużytych w W1); wynik osobno dla każdego przedmiotu; mediany DI.

## Przewidywanie
K2b: na granicy (w starych scenach było dokładnie 32/40; jasna kostka ma mały kontrast z blatem). K2c: nie wiem.

## Zasady
Jeden przebieg. Po wyniku nie zmieniam miary, progów ani scen. Bez nowych ziaren (świat: 23 504 001 jak W0; flyvis deterministyczny).
Wyniki: `flymind/results/fly_eye_20261117/w1b/` (`w0b/*.npz`, `run_000-009.npz`, `run_010-019.npz`, `w1b_result.json`, `w1b_result_010-019.json`).
PASS → wolno pisać „czujniki kierunku flyvis rozróżniają lewo/prawo na obrazie z kamery robota (model, nie pomiar)”. FAILED → nie wolno.
