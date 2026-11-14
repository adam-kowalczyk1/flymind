# Plakat FlyMind — treść do szablonu Canva 980 × 680 mm (poziomo)

Przygotowano 14 XI 2026. Termin oddania: 16 XI. Wstawianie do Canvy: Nori.
Wszystkie liczby na plakacie mają etykietę **VERIFIED** (przeliczone 14 XI z plików wyników — tabela źródeł na końcu),
z jednym wyjątkiem oznaczonym **[R]** (REPORTED: liczba z wcześniejszego raportu, bez zachowanego pliku wyniku).
Limity znaków liczone ze spacjami. Teksty poniżej mieszczą się w limitach (liczba w nawiasie przy każdej sekcji).

## Jak to ułożyć

Trzy kolumny po ok. 300 mm, margines 20 mm, odstęp między kolumnami 20 mm. Pas tytułu na całą szerokość (wys. ok. 95 mm),
pas stopki na całą szerokość (wys. ok. 40 mm).

| Kolumna lewa | Kolumna środkowa | Kolumna prawa |
|---|---|---|
| S1 Pytanie | S4 Wynik 1 + G1 + Z1 | S6 Wynik 3 + G3 + Z2 |
| S2 Jak to zrobiłem + G4 (schemat może wejść pod tytuł na szerokość 2 kolumn) | S5 Wynik 2 + G2 | S7 Odpowiedź |
| S3 Kontrole | | S8 Ograniczenia · S9 Co dalej |

Wielkości pisma (czytelność z ok. 1,5 m): tytuł 120–130 pt · nagłówki sekcji 54–60 pt · tekst 30–32 pt (nie mniej niż 28) ·
podpisy grafik 24 pt · stopka 20–22 pt. Krój bezszeryfowy, ciemny tekst na jasnym tle. Kolory wykresów: niebieski = sieć
z danych, pomarańczowy = sieci przetasowane, czarny = klasyczny sterownik, szary = odruch / brak wzroku — warto użyć tych
samych kolorów w akcentach plakatu.

Pola do uzupełnienia przez autora (nie znam ich i nie zgaduję): **[IMIĘ I NAZWISKO]**, **[SZKOŁA, KLASA]**, **[OPIEKUN]**,
logo/elementy wymagane przez szablon konkursu.

---

## S0. Tytuł (limit 80; jest 70)

**Czy biologiczny konektom muszki może sterować ramieniem robota SO-101?**

Podtytuł (limit 110; jest 96):
FlyMind — sieć neuronów zbudowana z mapy połączeń muszki owocowej steruje ramieniem robota w symulacji

Autor (limit 120): [IMIĘ I NAZWISKO] · [SZKOŁA, KLASA] · opiekun: [OPIEKUN] · Explory 2026

---

## S1. Pytanie (limit 420; jest 369)

Naukowcy opublikowali mapę wszystkich połączeń w układzie nerwowym samca muszki owocowej (konektom MaleCNS).
Sprawdzam, czy sieć zbudowana z prawdziwych połączeń wybranych obwodów muszki potrafi sterować ramieniem robota —
i czy liczy się w tym dokładny schemat połączeń. Dlatego każdy wynik porównuję z siecią o przetasowanych połączeniach
i z klasycznym sterownikiem.

---

## S2. Jak to zrobiłem (limit 560; jest 504)

1. Z mapy MaleCNS wybieram obwód: neurony czuciowe, pośrednie i ruchowe wraz z liczbą synaps między nimi.
2. Każdy neuron to prosty model wysyłający impulsy. Połączeń nie uczę ani nie stroję — pochodzą z danych.
3. Zmysły robota (kamera, dotyk chwytaka) pobudzają neurony czuciowe; impulsy neuronów ruchowych zamieniam na ruch stawu.
4. Dojazd ramienia do przedmiotu, kolejność etapów i zabezpieczenia robi zwykły, klasyczny program.

Wszystko działa w symulatorze fizyki MuJoCo z modelem ramienia SO-101.

**Grafika G4** — podpis (limit 150; jest 121):
Droga sygnału. Kolor pomarańczowy: część zbudowana z danych o muszce. Szara ramka: kod klasyczny, który nie jest „muchą”.

---

## S3. Kontrole — po co przetasowane sieci? (limit 430; jest 355)

Sam udany ruch niczego nie dowodzi. Dlatego każdy test powtarzam z tymi samymi neuronami, ale z losowo przepiętymi
połączeniami (ta sama liczba i siła połączeń, inny schemat). Jeśli przetasowana sieć radzi sobie tak samo, to schemat
połączeń muszki nie był potrzebny. Drugi punkt odniesienia to klasyczny sterownik i najprostszy odruch
„dotyk → zaciśnij”.

---

## S4. Wynik 1 — obrót w stronę piłeczki (limit 520; jest 435)

Obwód wzrokowy muszki (424 neurony) obraca podstawę ramienia w stronę zielonej piłeczki: **38 trafień na 40 prób**.
Klasyczny regulator: 40 na 40 i dokładniej.

Sieć z przetasowanymi połączeniami: 3 na 40. Ale gdy tasowanie zachowuje siłę połączeń po każdej stronie, przetasowana
sieć też trafia (10 na 10 w próbie kontrolnej **[R]**). Wniosek: liczy się to, że lewe „oko” jest połączone z lewą
stroną wyjścia — a nie drobne szczegóły schematu.

**Grafika G1** — podpis (limit 170; jest 137):
Trafienia na 40 prób. „Strony zamienione” i „bez wzroku” to sprawdzenie, czy układ w ogóle reaguje na obraz — nie dowód
na rolę połączeń.

**Grafika Z1** — podpis (limit 150; jest 133):
Pokaz na żywo: ramię obraca się za piłeczką, a po prawej widać impulsy poszczególnych neuronów i sygnał neuronów
sterujących skrętem.

---

## S5. Wynik 2 — chwyt sterowany „dotykiem” (limit 520; jest 519)

Obwód czuciowo-ruchowy nogi muszki (1507 neuronów) dostaje sygnał z czujników dotyku chwytaka i ustala siłę zacisku.
Ramię przenosi przedmioty do pudełka: **90 na 135 prób**. Klasyczny sterownik: 93. Prosty odruch: 80.

Trzynaście sieci przetasowanych: od 4 do 102 — trzy z nich są lepsze niż sieć z danych. Przy sztywniejszym kontakcie
klasyczny sterownik wygrywa wyraźniej (101 do 84). Sieć muszki chwyta, ale jej schemat połączeń nie daje tu przewagi.
Sieć wydaje ok. 3 % wszystkich komend — resztą steruje kod klasyczny.

**Grafika G2** — podpis (limit 170; jest 128):
Przedmioty odłożone do pudełka na 135 prób (45 przedmiotów × 3 położenia). Każda pomarańczowa kropka to jedna sieć
przetasowana.

**Grafika Z3 (opcjonalna)** — podpis (limit 110; jest 76):
Seria ciągła: ramię z chwytem sterowanym siecią przenosi kolejne przedmioty.

---

## S6. Wynik 3 — całe ramię: wynik negatywny (limit 600; jest 560)

Najtrudniejsza próba: sieć dwóch nóg muszki (2593 neurony + 1507 w chwytaku) steruje barkiem, łokciem i nadgarstkiem
przy podnoszeniu. **Odłożone przedmioty: 0 na 135.** Klasyczny sterownik: 81–89. Sieci przetasowane: od 0 do 96.

Co się dzieje: w sieci z danych dotyk pobudza prawie wyłącznie mięśnie „łokcia” — sam łokieć unosi przedmiot w 107 próbach
na 135, ale za wolno i za nisko, żeby go przenieść. Mięśnie „barku” i „nadgarstka” w tym modelu milczą. Sieci przetasowane
pobudzają wszystko naraz, więc ruszają się mocniej — ale to już nie jest schemat muszki.

**Grafika G3** — podpis (limit 190; jest 169):
Przedmioty odłożone na 135 prób. Warianty A i B to dwa możliwe znaki jednego przekaźnika (glutaminianu), którego działania
dane nie rozstrzygają. Sieć z danych: 0 w obu.

**Grafika Z2** — podpis (limit 150; jest 121):
Całe ramię sterowane siecią: po prawej impulsy wszystkich 4100 neuronów i to, które grupy „mięśni” sterują którym stawem.

---

## S7. Odpowiedź (limit 380; jest 331) — wyróżniona ramka

**Częściowo.** Sieć z konektomu muszki potrafi obrócić ramię w stronę celu i dobrać siłę chwytu. Całym ramieniem nie
steruje: przedmiotu nie przenosi. W żadnym z trzech zadań dokładny schemat połączeń muszki nie okazał się lepszy od
schematu przetasowanego ani od klasycznego sterownika. To jest wynik — i wiem, czego w modelu brakuje.

---

## S8. Ograniczenia — mówię o nich wprost (limit 620; jest 562)

- **Tylko symulacja.** Fizyczne ramię SO-101 nie było jeszcze sterowane siecią.
- **„Oko” nie jest okiem muszki.** Obraz z kamery zamienia na sygnał prosty wykrywacz zielonego koloru, który podaje
  ten sam prąd wszystkim neuronom wzrokowym po jednej stronie. To sztuczne pobudzanie, nie siatkówka owada.
- **To model wybranych obwodów, nie cyfrowy mózg muszki.** Neurony są uproszczone; brakuje m.in. sygnałów z mózgu
  do nóg.
- **Przypisanie mięśni nogi do stawów robota jest umowne** (analogia, nie biologia).
- **Mucha steruje małą częścią ruchu** — dojazd ramienia jest klasyczny.

---

## S9. Co dalej (limit 400; jest 376)

1. Zadanie, w którym schemat połączeń powinien mieć znaczenie (np. dozowanie siły, rozróżnianie stron), z kontrolą
   przetasowania od początku.
2. Dodanie z danych neuronów, które w muszce przekazują polecenia z mózgu do mięśni nóg.
3. Wejście wzrokowe oparte na prawdziwych neuronach oka muszki zamiast wykrywacza koloru.
4. Dopiero potem: ostrożny test na prawdziwym ramieniu.

---

## S10. Stopka (limit 420; jest 378)

Dane: konektom MaleCNS v1.0 (Janelia Research Campus). Symulator: MuJoCo. Ramię: SO-101.
Dużą część kodu napisały narzędzia AI (Claude Code) według moich poleceń; kierunek badań, hipotezy i decyzje są moje.
Każdą liczbę z plakatu można odtworzyć z plików wyników w repozytorium projektu. Żadne zwierzę nie brało udziału
w badaniach — korzystam wyłącznie z opublikowanych danych.

---

## Grafiki (wszystkie w tym katalogu)

| Plik | Co pokazuje | Piksele | Maks. szerokość w druku przy 300 dpi | Proponowana szerokość na plakacie |
|---|---|---|---|---|
| `G1_obrot_do_pileczki.png` | wykres: trafienia na 40 prób (V5) | 3480 × 2220 | 295 mm | 290 mm (szerokość kolumny) |
| `G2_chwyt_dotykiem.png` | wykres: przedmioty w pudełku na 135 prób | 3480 × 2220 | 295 mm | 290 mm |
| `G3_cale_ramie.png` | wykres: całe ramię, odłożone na 135 prób | 3480 × 2220 | 295 mm | 290 mm |
| `G4_schemat_metody.png` | schemat drogi sygnału | 4500 × 1560 | 381 mm | 290–380 mm |
| `Z1_pokaz_obrot_bazy.png` | zrzut pokazu V5 (kopia `demo/media/flymind_04_track.png`) | 2560 × 1440 | 217 mm | do 217 mm |
| `Z2_pokaz_cale_ramie.png` | zrzut pokazu ramienia (kopia `demo/media_arm_20261113/demo_arm_01_lift.png`) | 1600 × 900 | 135 mm | do 135 mm |
| `Z3_chwyt_seria.png` | 9 klatek serii chwytów (kopia `results/sensory_manipulation/media/demo_B_fly_v1_sheet.png`) | 960 × 720 | 81 mm | do 81 mm (opcjonalna) |

Uwaga do zrzutów: Z2 i Z3 mają mniej pikseli — przy 300 dpi nie należy ich powiększać ponad podaną szerokość. Zrzutów nie
powiększałem sztucznie. Na Z1 i Z2 widać napisy z programu (drobne) — z 1,5 m nie będą czytelne i nie muszą być; liczy
się obraz ramienia i „deszcz” impulsów. Wykresy G1–G4 odtwarza `make_figures.py` (liczby czytane wprost z plików).

## Źródła liczb (ścieżki względem `flymind/`)

| Liczba na plakacie | Źródło | Poziom |
|---|---|---|
| 38/40, 3/40, 0/40, 0/40, 40/40 | `results/v5/analysis_confirm.json` (`conds.*.success`) | VERIFIED |
| 10/10 przy tasowaniu zachowującym siłę | `VALIDATION_PLAN.md` § „V4/V5 — Red Team”, pkt 1 (brak zachowanego pliku wyniku) | REPORTED **[R]** |
| 424 neurony obwodu wzrokowego | `results/audit_spike_to_servo_20261113/audit_log_2026-11-13.md` krok 12; widoczne też na Z1 (135 + 140 + 147 + 2) | VERIFIED (13 XI) |
| 90/135 sieć (chwyt) | `results/sensory_manipulation/B_fly_search_glu-1_v1.json` (to samo dla `glu+1`) | VERIFIED |
| 93/135 klasyczny | `results/object_handling/B_base_v2.json` | VERIFIED |
| 80/135 odruch | `results/sensory_manipulation/D_reflex_search_v1.json` | VERIFIED |
| 13 tasowań: 4–102 (74, 49, 82 oraz 101, 82, 80, 102, 83, 79, 82, 79, 99, 4) | `results/sensory_manipulation/S_shuffle{1,2,3}_search_v1.json`, `results/shuffle_matched/shuffle_171000{11..20}_v1.json` | VERIFIED |
| 101 do 84 przy sztywnym kontakcie | `results/contact_audit/stiff_A_v1.json`, `stiff_B_v1.json` | VERIFIED |
| ok. 3 % komend | `safety_stats` w `results/vision_manipulation/E_vis_touch_v3.json` (3,14 %), `F_vis_touch_feco_v3.json` (3,10 %); sam dotyk 2,51 % | VERIFIED |
| 1507 neuronów nogi; 2593 + 1507 = 4100 | `demo/test_demo_arm.py` T3 (uruchomiony 14 XI) | VERIFIED |
| 0/135 całe ramię (oba warianty); klasyczny 81 i 89; tasowania 96, 89, 0, 0, 33 oraz 75, 89, 0, 91, 71 | `results/step2_whole_arm_20261113/whole_arm_5/test/arm_test_*.json` (`truth.placed`) | VERIFIED |
| łokieć unosi w 107/135 | `results/step2_whole_arm_20261113/elbow_c/test/c_test_N_g1.json` (`truth.lift`) | VERIFIED |
| „mięśnie barku i nadgarstka milczą” (0 Hz przy dotyku) | `results/verification_step2_20261114/v07_data_paths.json`, część B | VERIFIED (model, nie twierdzenie o żywej muszce) |

Sformułowania, których na plakacie celowo NIE ma: „połączenia muszki są lepsze”, „dowód roli konektomu”, „w danych brakuje
drogi do mięśni barku” (droga anatomiczna istnieje — zob. errata kroku 2), „robot sterowany mózgiem muchy”.
