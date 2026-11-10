# FlyMind — etap „czucie, śledzenie i manipulacja” (cel na 1 grudnia 2026)

Stan na 2026-11-10. Commit odniesienia: `a7344e3` (gałąź `flymind/fly-first-control`). **Wszystko jest symulacją MuJoCo;
nic nie było uruchamiane na fizycznym SO-101.** Nowe pliki tego etapu nie są jeszcze zacommitowane.

Statusy: VERIFIED (sprawdzone tu, w kodzie/danych/przebiegu) · PARTIALLY VERIFIED · REPORTED (podane przez źródło, nie
sprawdzone tu) · INFERRED · HYPOTHESIS · NOT VERIFIED · FAILED · NOT IMPLEMENTED.

## 0. Najkrótsze podsumowanie (do prezentacji)

- W scenie z pudełkiem i 45 różnymi przedmiotami **o zaciśnięciu szczęki, sile chwytu i jego utrzymaniu decyduje obwód
  czuciowo-ruchowy lewej środkowej nogi muchy z danych MaleCNS** (1507 neuronów): dotyk padów trafia do receptorów
  szczecinkowych, kąt i prędkość szczęki do receptorów FeCO, a aktywność motoneuronów goleni daje moment szczęki.
- Ramię (dojazd, podniesienie, przeniesienie) i puszczenie nad pudełkiem prowadzi **klasyczne rusztowanie** — sieć muchy
  nie ma w danych sygnału „podnieś”, „zanieś” ani „puść”. Położenie przedmiotu pochodzi z symulatora (wyrocznia), **nie
  z kamery**: wzrok sieci (LC10a → DNa02) istnieje w projekcie osobno, ale nie jest jeszcze włączony w tę pętlę.
- **Wynik (135 prób na wariant, te same przedmioty i położenia):** klasyczny kontroler 93 udane, sieć muchy z samym
  dotykiem 90, prosty odruch 80, sieć z dodaną propriocepcją 83, trzy sieci przetasowane 74 / 49 / 82, bez wyjścia
  sterownika 0. Sieć dorównuje kontrolerowi klasycznemu i jest nieco lepsza od odruchu; propriocepcja w obecnym
  kodowaniu nie pomaga; przewaga nad sieciami przetasowanymi może wynikać z samej siły drogi dotyk → mięsień (§9).
- W konfiguracji przeniesionej wprost z wcześniejszego eksperymentu (FJ1) sieć zawodzi: 6/135.
- Cele 120 Hz i 5 ms: policzone tylko jako **budżet obliczeń** (§12); pętla w symulacji działa co 10 ms, nie co 8,33 ms.

## 1. Inwentaryzacja: co już istniało, a czego brakowało

| Element z koncepcji | Stan przed etapem | Status |
|---|---|---|
| Wzrok → obrót bazy (LC10a → 147 pośredników → DNa02) | pętla zamknięta, 38/40 trafień; późniejsze testy: wynik to lateralizacja, nie dowód na konkretne połączenia; regulator P lepszy | VERIFIED (symulacja), poza tą pętlą |
| Koder obrazu | heurystyka koloru (zielona plama → 2 liczby L/R), bez siatkówki, lamina, T4/T5 | VERIFIED, to MODEL |
| Płat wzrokowy (T4/T5, LPLC2, LC4…) | są w adnotacjach MaleCNS; tylko projekt testu (d2) | NOT IMPLEMENTED |
| Wzrok → noga (LC9 → DNp09 → VNC → motoneurony) | pilot: zbliża chwytak do piłeczki w wąskim zakresie, wciska w stół | PARTIALLY VERIFIED (pilot) |
| Dotyk → szczęka (szczecinki T2 L → prostownik goleni) | FJ1: 12/12 chwytów piłeczki, ale trywialny odruch też 12/12 | VERIFIED, bez przewagi nad odruchem |
| Propriocepcja (FeCO) | tylko mapowanie typów w danych, bez kodu | NOT IMPLEMENTED → **dodane w tym etapie** |
| Obciążenie / poślizg (sensilla kampaniformalne) | 2 neurony na nerw nogi w MaleCNS, brak drogi do MN goleni | brak danych → NOT IMPLEMENTED |
| Sygnał „podnieś” | kandydat T2L→T2R wycofany po red teamie | FAILED / brak |
| Sygnał „puść”, „zanieś do pudełka” | brak w danych | NOT IMPLEMENTED |
| Scena z wieloma przedmiotami i pudełkiem | brak (Etap 1: jedna kostka A↔B) | **zbudowana** (`object_handling.py`) |
| Pomiar opóźnień pętli z siecią | częściowy (`latency.py`, `bench_loop.py`) | **zmierzony dla tej pętli** (§12) |

Największe braki: (1) wzrok nie steruje niczym w zadaniu z pudełkiem, (2) ramieniem nie steruje sieć, (3) nie ma
biologicznego kanału siły/poślizgu, (4) nie ma sygnałów podniesienia i puszczenia.

## 2. Architektura tego etapu i przepływ informacji

```
 pady szczęk (siła, N) ──[MODEL 40 mV/N]──► receptory szczecinkowe T2 L (322) ─┐
 kąt szczęki (rad) ──[MODEL liniowy]──► FeCO claw-EXT (9) / claw-FLEX (14) ────┤   obwód nogi z danych MaleCNS
 prędkość szczęki ──[MODEL liniowy]──► FeCO hook-EXT (8) / hook-FLEX (3) ──────┤   1507 neuronów ALIF, krok 1 ms,
                                                                               ▼   10 kroków na takt 10 ms
                              interneurony VNC ──► motoneurony goleni: prostownik (2), zginacze (11)
                                                                               │
                moment szczęki = 0,005 N·m/Hz · (prostownik − zginacze)  [ANALOGIA: prostowanie goleni ≙ zaciskanie]
                                                                               ▼
        warstwa bezpieczeństwa (klasyczna) ──► MuJoCo: szczęka ściska przedmiot ──► nowe siły i kąt ──► z powrotem na górę
```

Rusztowanie klasyczne (jawnie oznaczone źródłem `classical:…`): plan i ruch ramienia, otwarcie szczęki przed chwytem,
doprowadzenie do pierwszego dotyku (słaby moment „szukania” 0,3 N·m albo dosuw boczny z FJ1), otwarcie nad pudełkiem.
Bramki czytają **wyjście sieci**, nie surowy dotyk: podniesienie rusza dopiero, gdy sieć sama zaciska (moment ≥ 0,10 N·m
przez 0,1 s); gdy w transporcie sieć przestaje zaciskać na 50 ms, próba jest przerywana.

## 3. Obwody MaleCNS i uzasadnienie

| Twierdzenie | Podstawa | Status |
|---|---|---|
| Receptory szczecinkowe nogi T2 L (322) dochodzą przez interneurony do MN goleni; statycznie netto pobudzają prostownik | audyt D1 (dwa niezależne przeliczenia), `leg_circuit.py` | VERIFIED (dane, statycznie) |
| Hamowanie zginaczy zależy od znaku glutaminianu | brak fizjologii dla MN nogi; domyślnie Glu = hamujący | HYPOTHESIS (parametr `--glu`) |
| SNpp51 / SNpp50 = FeCO claw, SNpp39 / SNpp41 = FeCO hook | pole `synonyms` w adnotacjach MaleCNS | VERIFIED (adnotacja) |
| Który typ koduje zgięcie, a który wyprost | reguła z Lee i in. 2024 zastosowana do połączeń; etykiety tylko dla T3 R | INFERRED |
| Zamykanie szczęki ≙ prostowanie goleni | decyzja projektowa po pilocie FJ1; mucha nie ma chwytaka | ANALOGIA, nie biologia chwytu |
| FeCO club, płytki włoskowe, CS | club: 0 % wejścia do MN; płytki działają na biodro/krętarz; CS: brak drogi | pominięte celowo |
| Kodowanie siła → prąd receptora, kąt → prąd FeCO | stałe wybrane z góry, niestrojone | MODEL |

Publikacji źródłowych nie czytałem ponownie w tej sesji; odwołania (Lee 2024, Phelps 2021, Lesser 2024) pochodzą z
wcześniejszych raportów projektu i mają tu status REPORTED.

## 4. Co jest zaimplementowane, częściowe i niezrealizowane

| Funkcja z zadania | Stan |
|---|---|
| Różne przedmioty, pudełko, kolejka, pojawianie się po potwierdzonym podniesieniu | VERIFIED (testy + serie) |
| Ewaluator na stanie prawdziwym, 5 etapów sukcesu, spis końcowy | VERIFIED |
| Klasyczny punkt odniesienia (A) | VERIFIED |
| Sieć steruje zaciskaniem i trzymaniem (B) | VERIFIED |
| Propriocepcja FeCO w pętli (C) | VERIFIED jako działający kanał; wartość biologiczna kodowania: MODEL |
| Pełna integracja wzrok + dotyk + propriocepcja (D) | **NOT IMPLEMENTED** |
| Wykrywanie i śledzenie przedmiotu przez sieć w tym zadaniu | NOT IMPLEMENTED (percept = wyrocznia) |
| Reakcja na przesunięcie przedmiotu, poślizg | NOT IMPLEMENTED jako test; sieć przerywa transport po utracie dotyku |
| Rozróżnianie stanów chwytu (jedna strona / obie / niestabilny…) | NOT IMPLEMENTED (brak analizy aktywności) |
| Sterowanie ramieniem przez sieć | NOT IMPLEMENTED (pilot FJ2 poza tą pętlą) |
| Kontrolowane puszczanie przez sieć | NOT IMPLEMENTED |
| 120 Hz w pętli zamkniętej, ścieżka 5 ms | NOT IMPLEMENTED (tylko budżet obliczeń) |
| Test wytrzymałościowy długiej pracy | NOT IMPLEMENTED |

## 5. Parametry

Sieć: `FlyJawCfg` — J0 0,2 mV/synapsę, Glu −1, dotyk 40 mV/N (nasycenie 40 mV), filtr częstości 50 ms, 0,005 N·m/Hz,
10 kroków ALIF na takt. Propriocepcja (`FlyCfg`): środek zakresu 0,80 rad, nasycenie claw po 0,90 rad, hook przy
1,0 rad/s, maks. 40 mV. Bramki: 0,10 N·m, 10 taktów; utrata: 5 taktów. Rusztowanie: szukanie 0,30 N·m do 4 s.
Scena, przedmioty i kryteria: `object_handling.py` (`Scene`, `Crit`, `MATERIALS`, `SHAPES`); każdy plik wynikowy zapisuje
pełną konfigurację i rzeczywiste masy z modelu.

## 6. Przedmioty i fizyka

9 kształtów × 5 profili materiału = 45 przedmiotów (zestaw podstawowy), po 3 losowe położenia; 15 przedmiotów trudnych
(tylko baza klasyczna). Wszystkie bryły są **sztywne**. Profil = gęstość + tarcie + sztywność kontaktu:

| Profil | Gęstość [kg/m³] | Tarcie | Przybliża |
|---|---|---|---|
| hard_grip | 1150 | 1,00 | twarda guma |
| hard_slick | 1410 | 0,20 | gładkie tworzywo (POM) |
| heavy | 7850 | 0,50 | stal |
| light | 120 | 0,60 | balsa / sztywna pianka |
| mid | 700 | 0,50 | drewno |

Kształty: sześciany 2 / 3 / 4,5 cm, walec stojący ⌀3×5 cm, kula ⌀3,5 cm, płytka 5×3,5×1 cm, belka 8×2×2 cm, bryła L, klin.
Masy od 1 g do 715 g. **Korekta katalogu (v1 → v2):** profil „light” miał miękki kontakt i przy masie kilku gramów pady
przenikały przez przedmiot (artefakt MuJoCo, nie cecha materiału); w v2 ma kontakt twardy, a każdy wynik podaje liczbę
prób z wnikaniem padu > 2 mm.

## 7. Rozdział informacji

- **Sieć dostaje:** siły z dwóch padów szczęk, kąt i prędkość szczęki. Nic więcej (test N1).
- **Rusztowanie dostaje:** enkodery, dotyk (do potwierdzenia puszczenia), wyjście sieci, percept-wyrocznię
  (prostokąt z góry + wysokość z pozycji w symulatorze — to nie jest percepcja kamery).
- **Tylko ewaluator:** pozycje i prędkości przedmiotów, kontakty, masa, tarcie.

## 8. Wyniki: konfiguracje A–D na 45 przedmiotach × 3 położenia (135 prób na ramię)

Każde ramię dostało **te same przedmioty w tych samych położeniach** (sprawdzane w `tables.py`). „W pudełku” = przedmiot
po 1,5 s od puszczenia leży stabilnie w obrysie pudełka, nie dotyka blatu ani chwytaka, i jest tam nadal w spisie końcowym.
Porażki nie są usuwane. Jedna próba = jeden przedmiot w świeżej scenie, do 2 podejść.

Odpowiedniki konfiguracji z zadania: **A** = klasyczny kontroler; **B** = istniejąca sieć (sam dotyk): `B_fly_push`
(dokładnie jak w FJ1) i `B_fly_search` (ta sama sieć, inne doprowadzenie do dotyku); **C** = sieć rozszerzona
o propriocepcję FeCO (`C_fly_feco_search`); **D** (wzrok + dotyk + propriocepcja) = **NOT IMPLEMENTED**.
Kontrole: `D_reflex_*` (odruch w jednej linijce kodu), `N_null` (moment zero), `S_shuffle1–3` (obwód przetasowany
z zachowaniem stopni i wag), `C_no_touch` (odcięty dotyk), `glu+1` (odwrotny znak glutaminianu).
Przyczyna „snn_released” w tabeli znaczy: sterownik szczęki (sieć albo odruch) przestał zaciskać.

| Ramię | Źródło komendy szczęki | Chwyt | Podniesienie | Transport | Odłożenie | **W pudełku** | Upuszczone | Mediana operacji [s sym.] | Udane/h czasu sym. | Przyczyny porażek prób |
|---|---|---|---|---|---|---|---|---|---|---|
| A klasyczny (baza) | classical:object_handling | 125 | 99 | 91 | 93 | **93/135** (68.9 %) | 6 | 7.47 | 221 | lost_grip 60, no_contact 12, weak_grip 9 |
| B_fly_push | snn:legT2L | 6 | 6 | 6 | 6 | **6/135** (4.4 %) | 0 | 9.485 | 9 | no_engage 203, snn_released 49, unreachable 7 |
| B_fly_search_glu+1 | snn:legT2L | 110 | 101 | 90 | 90 | **90/135** (66.7 %) | 11 | 7.93 | 201 | snn_released 86 |
| B_fly_search_glu-1 | snn:legT2L | 108 | 97 | 89 | 90 | **90/135** (66.7 %) | 7 | 7.91 | 198 | snn_released 87 |
| C_fly_feco_search | snn:legT2L+FeCO | 109 | 97 | 83 | 83 | **83/135** (61.5 %) | 14 | 8.06 | 185 | snn_released 94 |
| C_no_touch_search | snn:legT2L+FeCO | 129 | 0 | 0 | 0 | **0/135** (0.0 %) | 0 | None | 0 | no_engage 261, snn_released 9 |
| D_reflex_push | classical:reflex | 49 | 39 | 38 | 39 | **39/135** (28.9 %) | 0 | 8.83 | 63 | no_engage 161, snn_released 27, unreachable 8 |
| D_reflex_search | classical:reflex | 101 | 88 | 79 | 80 | **80/135** (59.3 %) | 8 | 7.98 | 170 | snn_released 108 |
| N_null_search | classical:null | 129 | 0 | 0 | 0 | **0/135** (0.0 %) | 0 | None | 0 | no_engage 270 |
| S_shuffle1_search | snn:legT2L_shuffled | 100 | 88 | 74 | 74 | **74/135** (54.8 %) | 14 | 8.04 | 158 | snn_released 111 |
| S_shuffle2_search | snn:legT2L_shuffled | 96 | 64 | 49 | 49 | **49/135** (36.3 %) | 15 | 7.76 | 99 | snn_released 160 |
| S_shuffle3_search | snn:legT2L_shuffled | 128 | 104 | 82 | 82 | **82/135** (60.7 %) | 22 | 8.19 | 182 | no_engage 12, snn_released 74 |

Sukces według kształtów (w pudełku / próby):

| Ramię | cube_S | cube_M | cube_L | cyl | sphere | flat | long | L | wedge |
|---|---|---|---|---|---|---|---|---|---|
| A klasyczny (baza) | 15/15 | 15/15 | 6/15 | 9/15 | 15/15 | 9/15 | 15/15 | 8/15 | 1/15 |
| B_fly_push | 0/15 | 0/15 | 0/15 | 4/15 | 0/15 | 0/15 | 2/15 | 0/15 | 0/15 |
| B_fly_search_glu+1 | 15/15 | 15/15 | 4/15 | 8/15 | 15/15 | 6/15 | 15/15 | 4/15 | 8/15 |
| B_fly_search_glu-1 | 15/15 | 15/15 | 1/15 | 7/15 | 15/15 | 8/15 | 15/15 | 6/15 | 8/15 |
| C_fly_feco_search | 15/15 | 13/15 | 0/15 | 9/15 | 15/15 | 9/15 | 11/15 | 6/15 | 5/15 |
| C_no_touch_search | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 |
| D_reflex_push | 6/15 | 5/15 | 6/15 | 6/15 | 2/15 | 5/15 | 6/15 | 3/15 | 0/15 |
| D_reflex_search | 14/15 | 13/15 | 0/15 | 3/15 | 13/15 | 7/15 | 15/15 | 9/15 | 6/15 |
| N_null_search | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 |
| S_shuffle1_search | 13/15 | 11/15 | 0/15 | 6/15 | 10/15 | 7/15 | 11/15 | 7/15 | 9/15 |
| S_shuffle2_search | 14/15 | 6/15 | 0/15 | 6/15 | 6/15 | 3/15 | 9/15 | 5/15 | 0/15 |
| S_shuffle3_search | 15/15 | 11/15 | 6/15 | 9/15 | 12/15 | 6/15 | 12/15 | 8/15 | 3/15 |

Sukces według materiałów (w pudełku / próby):

| Ramię | hard_grip | hard_slick | heavy | light | mid |
|---|---|---|---|---|---|
| A klasyczny (baza) | 20/27 | 14/27 | 17/27 | 21/27 | 21/27 |
| B_fly_push | 3/27 | 0/27 | 3/27 | 0/27 | 0/27 |
| B_fly_search_glu+1 | 20/27 | 17/27 | 16/27 | 19/27 | 18/27 |
| B_fly_search_glu-1 | 18/27 | 17/27 | 17/27 | 19/27 | 19/27 |
| C_fly_feco_search | 15/27 | 17/27 | 12/27 | 19/27 | 20/27 |
| C_no_touch_search | 0/27 | 0/27 | 0/27 | 0/27 | 0/27 |
| D_reflex_push | 22/27 | 0/27 | 14/27 | 0/27 | 3/27 |
| D_reflex_search | 9/27 | 14/27 | 17/27 | 19/27 | 21/27 |
| N_null_search | 0/27 | 0/27 | 0/27 | 0/27 | 0/27 |
| S_shuffle1_search | 7/27 | 14/27 | 12/27 | 19/27 | 22/27 |
| S_shuffle2_search | 3/27 | 6/27 | 3/27 | 17/27 | 20/27 |
| S_shuffle3_search | 19/27 | 13/27 | 4/27 | 23/27 | 23/27 |

Ruch, bezpieczeństwo, fizyka:

| Ramię | max prędkość [rad/s] | max przysp. [rad/s²] | takty > 1,5 rad/s | interwencje warstwy bezp. | kontakty niepożądane | resety | serie przerwane | wnikanie padu > 2 mm (próby) | fałszywe przekonanie kontrolera |
|---|---|---|---|---|---|---|---|---|---|
| A klasyczny (baza) | 0.987 | 99.3 | 0 | {'range': 18} | 0 | 0 | 0 | 3 | 0 |
| B_fly_push | 0.909 | 83.6 | 0 | {'range': 2} | 0 | 0 | 0 | 0 | 0 |
| B_fly_search_glu+1 | 0.987 | 98.8 | 0 | {'jaw_end': 321, 'range': 18} | 5 | 0 | 0 | 23 | 0 |
| B_fly_search_glu-1 | 0.987 | 95.7 | 0 | {'jaw_end': 58, 'range': 22} | 1 | 0 | 0 | 16 | 0 |
| C_fly_feco_search | 0.987 | 96.0 | 0 | {'range': 20} | 0 | 0 | 0 | 16 | 0 |
| C_no_touch_search | 0.836 | 92.9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| D_reflex_push | 0.956 | 90.2 | 0 | {'range': 6} | 0 | 0 | 0 | 0 | 0 |
| D_reflex_search | 0.987 | 94.3 | 0 | {'jaw_end': 20, 'range': 17} | 1 | 0 | 0 | 11 | 0 |
| N_null_search | 0.836 | 86.1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S_shuffle1_search | 0.987 | 95.9 | 0 | {'jaw_end': 2, 'range': 13} | 0 | 0 | 0 | 17 | 0 |
| S_shuffle2_search | 0.918 | 96.2 | 0 | {'range': 8} | 0 | 0 | 0 | 0 | 0 |
| S_shuffle3_search | 0.932 | 97.2 | 0 | {'range': 16} | 4 | 0 | 0 | 4 | 0 |

Porównania sparowane (próba po próbie; test dokładny McNemara na parach niezgodnych, dwustronny):

| Porównanie | tylko pierwsze udane | tylko drugie udane | oba | żadne | p |
|---|---|---|---|---|---|
| B_fly_search_glu-1 vs A klasyczny (baza) | 12 | 15 | 78 | 30 | 0.701 |
| B_fly_search_glu-1 vs D_reflex_search | 14 | 4 | 76 | 41 | 0.031 |
| B_fly_search_glu-1 vs S_shuffle1_search | 22 | 6 | 68 | 39 | 0.004 |
| B_fly_search_glu-1 vs S_shuffle2_search | 49 | 8 | 41 | 37 | 0.000 |
| B_fly_search_glu-1 vs S_shuffle3_search | 22 | 14 | 68 | 31 | 0.243 |
| C_fly_feco_search vs B_fly_search_glu-1 | 4 | 11 | 79 | 41 | 0.118 |
| B_fly_search_glu+1 vs B_fly_search_glu-1 | 5 | 5 | 85 | 40 | 1.000 |
| B_fly_push vs D_reflex_push | 0 | 33 | 6 | 96 | 0.000 |
| B_fly_search_glu-1 vs B_fly_push | 87 | 3 | 3 | 42 | 0.000 |

Uwaga: 3 położenia tego samego przedmiotu nie są niezależne, a sieć i fizyka są deterministyczne — p jest orientacyjne.

## 9. Co z tego wynika (i czego nie wolno twierdzić)

1. **Sieć z danych, mając sam dotyk, radzi sobie tak jak klasyczny kontroler** (B 90/135 wobec A 93/135; próby
   niezgodne 12 do 15). To nie jest przewaga — to brak wyraźnej straty przy oddaniu szczęki sieci. VERIFIED (symulacja).
2. **Sieć jest nieco lepsza od trywialnego odruchu przy tym samym rusztowaniu** (90 wobec 80; 14 prób wygrywa tylko
   sieć, 4 tylko odruch). Różnica bierze się głównie z materiału o dużym tarciu (odruch 9/27, sieć 18/27). To pierwszy
   test w projekcie, w którym obwód nie jest równoważny odruchowi (w FJ1 było 12/12 wobec 12/12). PARTIALLY VERIFIED:
   jedna instancja sieci, bez szumu, położenia tego samego przedmiotu nie są niezależne.
3. **Trzy przetasowane obwody wypadły gorzej (74, 49, 82), ale to nie dowodzi, że liczą się konkretne połączenia.**
   Przetasowane sieci dają mniejszy moment trzymania (mediany 0,43 / 0,16 / 0,26 N·m wobec 0,53 N·m). Różnicę może
   więc tłumaczyć sama „głośność” drogi dotyk → prostownik, a nie jakość decyzji. Trzy instancje to za mało. HYPOTHESIS.
4. **Propriocepcja w obecnym kodowaniu nie pomaga** (C 83/135 wobec B 90/135; 4 do 11). FeCO działa jak hamulec
   położenia: moment w transporcie spada z 0,53 do 0,40 N·m, a reakcja na dotyk wydłuża się z 10 do 70 ms. To uczciwy
   wynik ujemny dla wybranego kodowania (MODEL), nie werdykt o biologii.
5. **Znak glutaminianu nie zmienia skuteczności** (90 wobec 90), zmienia tylko siłę ścisku (0,53 → 0,90 N·m).
6. **Bez wyjścia sterownika nic nie zostaje przeniesione** (moment zero: 0/135; sieć z odciętym dotykiem: 0/135) — sukces
   nie pochodzi z rusztowania.
7. **Doprowadzenie do dotyku ma duże znaczenie.** Przy dosuwie bocznym z FJ1 lekkie i śliskie przedmioty uciekają spod
   padu, zanim powstanie siła, którą czujnik (i sieć) może odczuć: sieć 6/135, odruch 39/135 — tu **odruch jest lepszy
   od sieci**. Istniejąca konfiguracja z FJ1 przeniesiona bez zmian na różne przedmioty praktycznie nie działa.
8. **Uwaga o fizyce:** przy mocnym ścisku sieci pad wnika w przedmiot ponad 2 mm w części prób (kolumna w tabeli; maks.
   3–4 mm). Kontakt w MuJoCo jest miękki; te próby są fizycznie mniej wiarygodne.

Nie wolno twierdzić, że: mucha „chwyta przedmioty”, sieć steruje ramieniem, wzrok bierze udział, wynik przenosi się na
prawdziwy robot, albo że połączenia z konektomu są lepsze od losowych.

## 10. Baza klasyczna: zestaw trudny i serie ciągłe (tylko konfiguracja A)

- **Zestaw trudny (15 przedmiotów × 3): 26/45.** Zawiodły: sześcian 5,5 cm (za szeroki — odmowa bez ruchu), płytka
  6 mm (pady przechodzą nad nią), belka 12 cm ze stali, sześcian z „wolframu” 521 g, kula i sześcian o tarciu 0,05.
  Udały się m.in. walec leżący, jajo, kapsuła, młotek, sześcian 1,2 cm (5/6).
- **Serie ciągłe z kolejką (10 serii po 9 przedmiotów):** wprowadzono 53 z 90 przedmiotów, 35 trafiło do pudełka;
  6 z 10 serii **zatrzymało się**, bo dwa porzucone przedmioty zablokowały strefę (nikt ich nie usuwa). Jedno
  „fałszywe przekonanie” kontrolera (uznał odłożenie, przedmiot nie spełnił kryterium). W ciasnym pudełku pojawiły się
  kontakty niepożądane: 31 dotknięć leżących przedmiotów padem i 5 uderzeń niesionym przedmiotem.
- Przepustowość bazy: mediana operacji 7,5 s czasu symulacji; w seriach ciągłych 35 udanych w 573 s = **220 na godzinę
  czasu symulacji** (z porażkami wliczonymi). Pliki `C_mixed_v2.INCOMPLETE.json` są oznaczone jako niekompletne celowo.

## 11. Czasy operacji

Mediany faz udanej operacji (czas symulacji): dojazd 1,6 s, chwyt 0,9 s (klasyczny) lub ok. 1,4 s (z „szukaniem”),
podniesienie 0,7 s, transport 1,8 s, puszczenie 0,24 s, powrót 2,2 s. Czas wykrycia przedmiotu: 0 s — percept jest
wyrocznią, więc tej wielkości **nie zmierzono**. Czas planowania (zegar komputera) to setne części sekundy i nie jest
wliczony w czas symulacji. Ramię nie przekroczyło 1,0 rad/s (limit warstwy 1,5); przyspieszenie zmierzone do ok. 100 rad/s²
(brak limitu przyspieszenia — monitorowane, nie ograniczane); zero resetów i zero błędów fizyki we wszystkich przebiegach.

## 12. Częstotliwość i opóźnienia — co zmierzono, a czego nie

Czas obliczeń na takt (zegar komputera, przebieg pojedynczy `latency_v1`, 15150 taktów):

| Etap | mediana [ms] | p95 | p99 | max |
|---|---|---|---|---|
| sensory_encoding | 0.014 | 0.0146 | 0.0171 | 0.0636 |
| snn_10_steps | 1.2525 | 1.2914 | 1.3298 | 1.9535 |
| decoding | 0.0089 | 0.0098 | 0.0154 | 0.047 |
| safety_and_command | 0.0168 | 0.0185 | 0.0247 | 0.1257 |
| sensor_to_command_total | 1.2924 | 1.3327 | 1.386 | 2.0197 |

proces: {'wall_s': 25.9, 'cpu_s': 41.3, 'cpu_load': 1.59, 'max_rss_MB': 1272.5, 'driver_build_s': 2.3, 'ticks': 15150, 'sim_tick_ms': 10.0, 'gpu': 'nieużywany'}; dotyk → komenda zaciskania sterownika (czas symulacji): {'median': 180.0, 'p95': 220.0, 'p99': 220.0, 'max': 220.0, 'n': 15}

| Wielkość z zadania | Wynik | Status |
|---|---|---|
| Częstotliwość kroku sieci | 1 krok = 1 ms czasu modelu; 10 kroków na takt | VERIFIED (konstrukcja) |
| Częstotliwość sterowania w pętli zamkniętej | 100 Hz czasu symulacji (takt 10 ms) | VERIFIED; **120 Hz NOT IMPLEMENTED** |
| Czy obliczenia zmieszczą się w 8,33 ms (120 Hz) | tak, z zapasem — patrz tabela (całość czucie → komenda) | VERIFIED tylko jako budżet obliczeń na tym komputerze |
| Częstotliwość przetwarzania obrazu | brak obrazu w pętli | NOT MEASURED |
| Czas przetwarzania sygnału czuciowego | wiersz „sensory_encoding” | VERIFIED |
| Bodziec → zmiana aktywności sieci → komenda (czas symulacji) | dotyk → komenda zaciskania sieci: B mediana 10 ms (jeden takt), p95 180 ms, maks. 510 ms (n = 177); C (z FeCO) mediana 70 ms, p95 220 ms, maks. 910 ms | VERIFIED, rozdzielczość 10 ms |
| Ścieżka ok. 5 ms | **nieosiągnięta**: czujnik jest czytany co 10 ms, a wyjście wygładza filtr 50 ms | FAILED w obecnej pętli |
| CPU / GPU / pamięć | ok. 1,6 rdzenia CPU (biblioteki liczbowe są wielowątkowe), GPU nieużywany, ok. 1,3 GB RAM (wczytany konektom) | VERIFIED |
| Stabilność długiej pracy | najdłuższy ciągły przebieg z siecią: 80 s symulacji, 8 przedmiotów (§16) | NOT VERIFIED (brak testu wielogodzinnego) |

Czas zegarowy i czas symulacji to różne rzeczy: sieć liczy takt w ok. 1,3 ms zegara, ale w symulacji takt trwa 10 ms.
120 Hz nie zostało uruchomione; 5 ms nie zostało osiągnięte. Do obu potrzebna jest zmiana taktu pętli (plan, pkt 4).

## 13. Porównanie z VFA (Eka Robotics)

„VFA” to model **Vision-Force-Action** firmy Eka Robotics. Co udało się ustalić (wyszukiwanie 2026-11-10; czytałem tylko
streszczenia wyników wyszukiwarki, nie same artykuły, więc wszystko poniżej ma status REPORTED):

- firma podaje **do ok. 1500 pobrań na godzinę** przedmiotów spoza danych uczących, niezawodność ponad 95 %, przedmioty do
  1 kg, w **laboratoryjnych** zadaniach podawania i wybierania z pojemnika; punkt odniesienia: człowiek ok. 600/h;
- liczby pochodzą z komunikatu firmy przy rundzie finansowania (październik 2026) i **nie są potwierdzone przez stronę
  trzecią ani zmierzone w znormalizowanych warunkach** (tak zaznacza część mediów);
- nie znalazłem publikacji technicznej z definicją „pobrania”, opisem sprzętu, toru ruchu i kryterium sukcesu.

Źródła wtórne: [The Robot Report](https://www.therobotreport.com/eka-robotics-raises-150m-scale-vision-force-action-model-robots/),
[AI Magazine](https://aimagazine.com/news/what-is-eka-robotics-how-it-raised-us-150m-in-series-a),
[TechCrunch](https://techcrunch.com/?p=3179067), [analiza „lab vs factory”](https://blog.pebblous.ai/blog/eka-robotics-vfa-lab-vs-factory/en/).

**Porównywalność: brak.** Nie wiadomo, czy „pobranie” VFA obejmuje odłożenie w miejsce docelowe i powrót, jaki jest dystans
i jaki robot. U nas jednostką jest: chwyt w strefie → przeniesienie ok. 25 cm → zrzut do pudełka → powrót do pozycji
wyjściowej, zaliczone tylko wtedy, gdy przedmiot stabilnie leży w pudełku. FlyMind to symulacja ramienia hobbystycznego
bez kamery w pętli; VFA to rzeczywisty sprzęt przemysłowy z własnym chwytakiem z czujnikami siły. Liczby z §8 można
zestawić z 1500/h wyłącznie jako rząd wielkości, nie jako wynik pojedynku. **Nie twierdzimy, że FlyMind jest szybszy
lub lepszy od VFA w czymkolwiek zmierzonym.** Jedyna cecha wspólna warta pokazania: oba systemy zamykają pętlę przez
czucie siły w chwytaku — u nas robi to obwód z konektomu, a nie model uczony.

## 14. Najważniejsze ograniczenia

1. Sieć steruje **tylko szczęką**. Ramię, kolejność faz i puszczenie są klasyczne; to rusztowanie, nie wynik biologiczny.
2. **Wzrok nie jest w pętli.** Położenie i wymiary przedmiotu pochodzą z symulatora. Konfiguracja D nie istnieje.
3. Mapowanie „prostownik goleni → zaciskanie” jest analogią; mucha nie ma chwytaka. Znak glutaminianu jest założeniem.
4. Kodowanie czujników (40 mV/N, liniowe FeCO) to model; receptory szczecinkowe muchy reagują na ugięcie włoska, nie na
   siłę w niutonach. Na sprzęcie nie ma jeszcze żadnych czujników dotyku.
5. Brak kanału obciążenia i poślizgu (w danych nie ma drogi z sensilli kampaniformalnych do tych motoneuronów).
6. Szum sieci = 0, jedna instancja sieci z danych, 3 instancje tasowania — to mało do wniosków o znaczeniu połączeń.
7. Próby na tym samym przedmiocie w 3 położeniach to nie 3 niezależne dowody; realną próbą jest 45 przedmiotów.
8. Dwa przedmioty (cube_M/mid, sphere/mid) służyły do uruchamiania kodu.
9. Serie ciągłe (kolejka) zmierzono porządnie tylko dla bazy klasycznej (10 serii); z siecią są dwie serie pokazowe.
   Serie zatrzymują się, gdy porzucone przedmioty zablokują strefę.
10. Pętla działa co 10 ms czasu symulacji; pomiar czasu obliczeń nie obejmuje kamery ani prawdziwych serw.

## 15. Odtwarzalność

Wszystko uruchamiane z katalogu tymczasowego (MuJoCo dopisuje ostrzeżenia do bieżącego katalogu), Python z `.venv`:

```
bash flymind/results/object_handling/run_all.sh <nowy_sufiks>        # baza klasyczna: testy, B, C, D, film
bash flymind/results/sensory_manipulation/run_arms.sh <nowy_sufiks>  # 11 ramion szczęki + pomiar opóźnień
.venv/bin/python -I -B flymind/test_object_handling.py               # 14 testów sceny i ewaluatora
.venv/bin/python -I -B flymind/test_sensory_manipulation.py          # 5 testów: wejścia sieci, źródła komend, kontrole
.venv/bin/python -I -B flymind/results/sensory_manipulation/tables.py v1 v2   # tabele z tego dokumentu
```

Skrypty zapisują skróty kodu i danych przed przebiegiem (`FREEZE_*.txt`), odmawiają nadpisania istniejących wyników
i na końcu sprawdzają 17 historycznych plików Etapu 1. Ziarna: `results/sensory_manipulation/SEED_REGISTRY.md`.
Fizyka i sieć są deterministyczne (szum 0), więc powtórzenie daje te same liczby.

## 16. Demonstracja

Film z serii klasycznej (czas symulacji 1:1): `results/object_handling/media/C_perm1_series0_v2.mp4`; plansza 9 klatek:
`results/object_handling/media/C_perm1_series0_v2_sheet.png`.

**Serie ciągłe z siecią muchy** (8 przedmiotów w kolejce, sieć pracuje bez przerwy, `record_demo.py`, ziarno 4242):

| Ramię | W pudełku | Czas serii [s sym.] | Pliki w `results/sensory_manipulation/media/` |
|---|---|---|---|
| B: sam dotyk | 5/8 | 74,6 | `demo_B_fly_v1.mp4`, `_sheet.png`, `.json` |
| C: dotyk + FeCO | 3/8 | 80,1 | `demo_C_fly_feco_v1.mp4`, `_sheet.png`, `.json` |

To po jednej serii na ramię — pokaz działania, nie statystyka. W obu seriach wprowadzono wszystkie 8 przedmiotów i seria
nie stanęła. Udział sieci w komendach szczęki: ok. 1300–1500 taktów (chwyt, podniesienie, transport); reszta taktów
szczęki i wszystkie komendy ramienia są klasyczne (liczby źródeł komend są w plikach `.json`).

Uruchomienie pokazu: `.venv/bin/python -I -B flymind/results/sensory_manipulation/record_demo.py B_fly 4242 <nowy_tag>`
(z katalogu tymczasowego).

## 17. Plan do 1 grudnia (priorytety)

| Nr | Zadanie | Dlaczego | Ryzyko |
|---|---|---|---|
| 1 | Włączyć wzrok w pętlę: obrót bazy na przedmiot siecią LC10a → DNa02 z kamery chwytaka, azymut z sieci zamiast z wyroczni; test z przesuwanym przedmiotem | bez tego nie ma „widzenia i śledzenia” w demonstracji | średnie: koder widzi tylko zieloną plamę, kamera na chwytaku |
| 2 | Testy reakcji: wyrwanie / zsunięcie przedmiotu w transporcie, czas od zaniku dotyku do zmiany momentu; analiza, czy z aktywności sieci da się odróżnić stany chwytu | „czucie i reakcja” wymaga zakłóceń, nie samych udanych prób | niskie |
| 3 | Nagranie demonstracji z siecią + serie ciągłe z siecią | materiał na 1 grudnia | niskie |
| 4 | Pętla 120 Hz (takt 8,33 ms) i szybka ścieżka dotyk → szczęka co 1–2 ms | cele 120 Hz / 5 ms | średnie: zmienia krok fizyki, wymaga powtórzenia baz |
| 5 | Więcej instancji tasowania (≥ 10) i szum sieci | bez tego nie wolno mówić o znaczeniu połączeń | niskie, tylko czas obliczeń |
| 6 | Ramię sterowane siecią (FJ2) | cel „mucha steruje”, ale w danych brak sygnału podniesienia | wysokie: raczej nie zdąży na 1 grudnia |

Ocena realności: punkty 1–3 są wykonalne do 1 grudnia; 4–5 prawdopodobnie; 6 traktować jako badanie, nie obietnicę.

## 18. Pliki, skróty i commit

- Commit odniesienia i bieżący HEAD: `a7344e377709eb0c1cfa427f269c914672db3f0b`, gałąź `flymind/fly-first-control`.
  **Nowe pliki nie są zacommitowane; nic nie zostało wypchnięte** (repozytorium nie ma zdalnego).
- Zmienione pliki śledzone przez Git: żaden z tego etapu. (`REPRODUCE.md` i `VALIDATION_PLAN.md` mają wcześniejsze,
  niezwiązane zmiany — nietknięte.) Kod wspólny Etapu 1 (`so101.py`, `pick_place.py`, `reach.py`, `grip.py`, `safety.py`)
  i model biologiczny (`alif.py`, `fly_jaw.py`, `leg_circuit.py`, dane MaleCNS) bez zmian — skróty w `FREEZE_*.txt`.
- Nowe pliki: `flymind/object_handling.py`, `flymind/test_object_handling.py`, `flymind/sensory_manipulation.py`,
  `flymind/test_sensory_manipulation.py`, ten dokument, katalogi `flymind/results/object_handling/` i
  `flymind/results/sensory_manipulation/`.
- Skróty sha256 wszystkich nowych plików oraz kontrola 17 historycznych plików Etapu 1:
  `flymind/results/sensory_manipulation/MANIFEST_2026-11-10.txt`. Skróty wyników są też w `run_v2.log` (baza) i
  `run_v1.log` (ramiona); każdy JSON zapisuje skróty kodu, którym powstał.
- W `results/object_handling/` pliki z sufiksem `v1` to pierwszy przebieg z artefaktem profilu „light” i błędem raportu
  w seriach; zostają jako zapis historii, **do cytowania służy `v2`**.
