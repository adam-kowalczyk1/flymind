# Prompt do nowego czatu — kamera nadgarstka, opóźnienie i „oko” muchy (19 XI 2026)

Wklej wszystko poniżej linii do nowego czatu Claude Code w folderze `/Users/admin/so101_fly_project`.

---

Jestem Adam, właściciel projektu FlyMind (mucha z konektomu MaleCNS steruje ramieniem SO-101). Nie jestem programistą — pisz krótko, po polsku. Ty ustalasz kolejne kroki. Najpierw przeczytaj pamięć projektu (MEMORY.md), zwłaszcza `so101-hardware-inventory.md`.

## Co powiedziałem (moimi słowami, 19 XI wieczorem)
„Chcę się dowiedzieć, jakie możliwości ma ta kamerka. Czy może widzieć w kolorze? Ile ma — 120 fps? Bo ja tego nie widzę. Jest mega duże opóźnienie, mega wielki delay. Już mi się to nie podoba. Czy ona widzi w nocy? Zaskoczyło mnie to, co widzi mucha. Nie wiem, jak to działa. »Różnica od tła« to nie do końca — jak to jest algorytm, to trochę słabo. Zrób najpierw diagnostykę.”

## Co już wiadomo (sprawdzone 19 XI)
- Kamera: OV9281 przez USB (UVC 0c45:636d, chip Sonix), przez hub USB 2.0; Mac ma tylko USB-C. Obraz **czarno-biały**. Czujnik OV9281 nie ma filtra koloru, więc koloru nie będzie nigdy. Rozdzielczość 1280×800, migawka globalna (bez rozmycia ruchu).
- **Kamera działa tylko z komend wpisanych lub wklejonych przez Adama w Terminal.** Komendy, które Claude uruchamia przez `osascript` / `open -a Terminal`, dostają po cichu 0 klatek (uprawnienia macOS). Diagnostykę i testy trzeba więc dawać Adamowi do wklejenia.
- Zmierzone klatki na sekundę:
  - 1280×800 przy żądanych 30 kl./s → naprawdę ~10 kl./s (w pierwszych 2 s ~3);
  - 640×400 przy żądanych 120 kl./s → 0 klatek, wisi;
  - 120 kl./s jest w specyfikacji, ale na Macu jeszcze nie zostało osiągnięte. Możliwa przyczyna: obraz bez kompresji nie mieści się w USB 2.0 — **niesprawdzone**.
- Widzenie w nocy: OV9281 jest czuły na podczerwień (~850 nm). To, czy ten moduł ma filtr podczerwieni i diody IR, jest **NIEZNANE** — nie zgadywać, sprawdzić (zdjęcie modułu, test w ciemności z pilotem TV).
- Opóźnienie: liczba „opóźn = 5 ms” wypisywana przez `live_avoid.py` mierzy **tylko** spóźnienie pętli mózgu wobec zegara, **a nie** czas od ruchu ręki do reakcji na ekranie. Prawdziwego opóźnienia nikt nie zmierzył. Znane źródła:
  - ~100 ms między klatkami przy 10 kl./s;
  - bufor ffmpeg;
  - stan na stronie odświeżany co 100 ms i uśredniany z 10 taktów;
  - wygładzanie w oku.
- „Oko” muchy dzisiaj (`flymind/experiments/step3_wiring/live_avoid.py`, klasa `Eye`) to klasyczny kod:
  - piksele różne od tła (tło łapane po 1,5 s, potem uczone powoli) → wielkość plamy → kąt θ → szybkość zbliżania L = dθ/dt;
  - L pobudza komórki zbliżania muchy (LPLC2, LC4, LPLC1, LC6, LC16).

  Działa zgrubnie: nie odróżnia ręki od innych rzeczy, a coś nieruchomego w kadrze „widzi” na stałe.
- Mózg i dotyk działają:
  - prawdziwy nacisk czujnika „dłoni” (FSR, Arduino `/dev/cu.usbmodem11201`, opornik 10 kΩ) → MDN ~30 Hz, DNge078 ~80 Hz → ramię w symulacji cofa się mocno;
  - sam wzrok nigdy nie rusza ramienia;
  - nacisk wychodzi jednak słaby: 0,2–0,4 N przy odczytach 170–430 / 1023.
- Pliki:
  - `live_avoid.py` (`--check` = sprawdzian bez sprzętu);
  - strona `hardware/sensors/test_czujnikow.html`, punkt 3 „Mucha na żywo”, serwowana przez live_avoid na http://127.0.0.1:8793;
  - `hardware/sensors/kamera_diag.sh` (pomiar trybów i prawdziwych kl./s; wynik w `~/Desktop/kamera_diag.txt`);
  - logi testów: `flymind/experiments/step3_wiring/results/live_avoid_reka_r2/r3.npz`, `~/Desktop/test_reki*.txt`;
  - commity 0c3c3b7, 7737f9b, 2a6ed6e na gałęzi `flymind/fly-first-control`.

## Wynik diagnostyki (19 XI 21:18, `~/Desktop/kamera_diag.txt`)
- 1280×800: zawsze tylko **10 kl./s** („Configuration of video device failed, falling back to default”); żądanie 60 kl./s → 0 klatek.
- **640×400: przy 120 → ~78 kl./s, przy 60 → 61, przy 30 → 32**; format bez znaczenia (nv12 / yuyv422 / domyślny).
- 320×200 przy 120 → ~74–79 kl./s.
- `live_avoid.py` ustawiony na 640×400 przy 120 + `-fflags nobuffer` (commit po 8e71139). Kąt obiektywu wg opisu ~148° (pewnie po przekątnej). Program zakłada `--fov 70`, więc kąt trzeba zmierzyć: linijka 20 cm przed kamerą.

## Co zrobić (po kolei)
1. **Diagnostyka kamery:**
   - przeczytaj `~/Desktop/kamera_diag.txt` (jeśli go nie ma, daj mi do wklejenia `bash /Users/admin/so101_fly_project/hardware/sensors/kamera_diag.sh`);
   - ustal, w jakim trybie da się dostać najwięcej prawdziwych klatek na sekundę na tym Macu;
   - jeśli AVFoundation nie daje więcej niż ~10–30 kl./s, sprawdź inne drogi (np. MJPG przez libuvc / OpenCV, inny kabel lub hub USB 3, niższa rozdzielczość).
2. **Zmierz prawdziwe opóźnienie** od zdarzenia do reakcji. Przykład: miganie ekranu przed kamerą ze znacznikiem czasu albo dioda z Arduino w kadrze. Potem usuń zbędne bufory: ffmpeg z `-fflags nobuffer`, strona bez uśredniania, częstsze odświeżanie.
3. **Lepsze oko**, bez łamania zasad:
   - „mucha ma sterować”: klasyczny kod wolno użyć tylko do wykrycia ręki / przeliczenia czujnika;
   - „to ma być ścisła integracja w mózgu”;
   - opcje do porównania:
     - (a) model oka muchy z danych (flyvis → T4/T5 → LPLC2 — 17 XI zamrożony, bo most nie wykrywał zbliżania; zobacz `fly-eye-research-2026-11-16`);
     - (b) klasyczny przepływ optyczny / rozszerzanie obrazu (bliżej tego, co liczy prawdziwe oko);
     - (c) wykrywanie dłoni (np. model rąk) jako czujnik.

   Najpierw zaproponuj i zapytaj, nie koduj wszystkiego naraz.
4. Odpowiadaj mi krótko, uczciwie (co działa, co nie, czego nie wiesz), bez obietnic, których nie sprawdziłeś.

## Zasady, które obowiązują zawsze
- **Nigdy nie pisz do prawdziwego ramienia** bez mojego „ruszamy”, przy mnie. Czytanie kamery i Arduino jest OK.
- Mucha (sieć z konektomu) decyduje. Żadnej klasycznej reguły „uciekaj”.
- Po każdym etapie: commit i zwykły push na `origin flymind/fly-first-control`. Bez force, nie na main, bez `*.npz`, `raw/`, `.DS_Store`.
- Mój e-mail jest prywatny.
