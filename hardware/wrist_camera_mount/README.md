# Uchwyt kamery OV9281 na nadgarstek SO-101

Stan na 16 XI 2026: zaprojektowane i sprawdzone tylko w komputerze. Nic jeszcze nie zostało wydrukowane ani przymierzone.

## Zalecana kamera (16 XI)

InnoMaker OV9281 USB (płytka U20CAM-9281M) z Amazon.pl, ASIN B0CLRN9QRC: 132,25 zł, dostawa 18 XI, sprzedawca InnoMaker. Ma płytkę **32×32 mm** (tak podają zdjęcia produktu), więc pasuje na oficjalny uchwyt bez nakładki. Instrukcja uchwytu SO-101 też poleca kamery InnoMaker. Ma obiektyw M12 148°, czyli rybie oko: obraz będzie mocno wygięty na brzegach. Oferta z Allegro (7340PRDW) idzie z Chin 11–15 dni i nie ma podanych wymiarów.

Rozstawu otworów InnoMakera nie sprawdziłem. Oficjalny uchwyt ma otwory co 27 mm; po dostawie trzeba to zmierzyć.

## Co drukować

| Plik | Co to jest |
|---|---|
| `uchwyt_oficjalny_SO101.stl` | Oficjalny uchwyt kamery SO-101 (wersja „hex-nut”), skopiowany z modelu ramienia w `assets/so101_meshes/`. Jest przewidziany na płytkę 32×32 mm. |
| `ov9281_adapter_38mm_pitch34.stl` | Nasza nakładka 38×38×3 mm na większą płytkę. Przykręca się ją między uchwyt a kamerę. |

**Najpierw zmierz płytkę kamery.** Allegro nie podaje wymiarów. Zmierz bok płytki oraz odległość między środkami otworów.
- Bok ok. 32 mm: wystarczy sam oficjalny uchwyt, nakładka nie jest potrzebna.
- Bok ok. 38 mm i otwory co 34 mm: drukuj obie części.
- Inny rozstaw otworów: `python make_adapter.py <rozstaw_w_mm>` zrobi nową nakładkę. Potrzebne biblioteki: `pip install trimesh manifold3d networkx shapely rtree`.

Druk: PLA albo PETG, warstwa 0,2 mm, bez podpór. Nakładkę kładzie się płasko, stożkowymi otworami do góry.

## Śruby

- Uchwyt do nadgarstka: 2× M3×8 i 2 nakrętki M3. Nakrętki wchodzą w gniazda w części „wrist roll”, a przy montażu trzeba zdjąć silnik chwytaka (nr 6). Tak jest w instrukcji TheRobotStudio.
- Nakładka do uchwytu: 4× M2×6 z łbem stożkowym. Łeb musi się schować, żeby płytka leżała płasko.
- Płytka kamery do nakładki: 4× M2×6, wkręcane bezpośrednio w plastik.

Płytkę kładzie się **obiektywem w dół**: obiektyw przechodzi przez okienko nakładki i uchwytu w stronę szczęk.

## Co zostało sprawdzone (w komputerze)

- Skrypt `make_adapter.py` sprawdza, czy nakładka przylega do uchwytu bez nachodzenia na niego, czy 4 śruby trafiają w otwory uchwytu i czy obiektyw ma wolną drogę przez oba okienka.
- Całość złożyłem z modelem chwytaka (część wrist roll, silnik, ruchoma szczęka) i nic z nim nie koliduje.
- Render z miejsca obiektywu przy kącie 100° pokazuje obie szczęki (`podglad_widok_z_kamery.png`). Oś kamery wypada 12,5° od czubka szczęk.

## Czego nie sprawdziłem

- Rzeczywistych wymiarów płytki. Założyłem 38 mm i rozstaw 34 mm, bo tak wygląda na zdjęciach.
- Rzeczywistej wysokości oprawki obiektywu. W modelu przyjąłem typową oprawkę M12.
- Czy oficjalny plik z GitHuba (`SO101_Wrist_Cam_Hex-Nut_Mount_32x32_UVC_Module`) jest identyczny z naszą kopią z modelu ramienia. Sprawdzałem tylko kopię lokalną.
