# P1 — oko muchy na prawdziwej kamerze, nagranie oko_r1 (21 XI 2026): **FAILED**

Plan: `flymind/experiments/step3_wiring/PREREG_OKO_KAMERA.md` (a172fad, przed nagraniem). Nagranie Adama: 306 s, 23 969 klatek,
średnio 78 kl./s (odstępy 8–25 ms), 30 kroków planu. Plik wideo (1,2 GB) zostaje na pulpicie: `~/Desktop/oko_r1.mkv`.

| kryterium | wynik | |
|---|---|---|
| K1 ruch kamery / dłoń w poprzek / odsuwanie ≤ 0,25 × zbliżanie (≥ 80 %) | 2 z 12 | **FAILED** |
| K2 zbliżanie ≥ 0,5 (≥ 80 %) | 0 z 7 (szczyty 0,05–0,15; mediana 0,12) | **FAILED** |
| K3 strona lewa/prawa | niezgodna | **FAILED** |
| K4 zbliżanie w czasie obrotu ≥ 0,5 × zbliżanie | 1 z 2 | **FAILED** |
| K5 spokój ≤ 0,1 | 0,006 | PASS |

Szczyty: zbliżania 0,05–0,15; dłoń w poprzek 0,03–0,05; odsuwanie 0,01–0,03; obrót kamery 0,12–0,27; pochylanie 0,04–0,49;
światło 0,19–0,40. Czyli na prawdziwym obrazie oko **prawie nie widzi zbliżającej się dłoni**, a ruch kamery i zmiana światła
dają **większy** sygnał niż zbliżanie. Mózg dostałby przy zbliżaniu najwyżej ~6 mV z 40.

## Odstępstwo od planu (zegar)
Kopia klatek do skryptu szła ze stałą częstotliwością 120 kl./s (ffmpeg dublował klatki), a plik ma prawdziwe ~78 kl./s → liczby
się nie zgadzały (36 734 vs 23 969). Czas klatki liczę więc jako czas przyjścia pierwszej klatki + znacznik w pliku (oba trwały
306,0 i 306,1 s). Znacznik „zasłoń obiektyw” nie dał ciemności (kamera sama dobiera jasność, a jasna dłoń z bliska), ale na
klatkach (`oko_r1_klatki.png`) widać, że okna trafiają w to, co mówił głos (dłoń rośnie w oknach zbliżania, obraz skacze przy
obrocie). Wynik nie zależy od tej poprawki — oko nie reaguje na zbliżanie w żadnym miejscu nagrania (`oko_r1_przebieg.png`).

## Dlaczego (opis po wyniku, nie test)
Sygnał fotoreceptorów przy prawdziwym zbliżaniu jest podobny jak w scenie syntetycznej (0,88 vs 1,33), ale „ruch na zewnątrz
we wszystkich 4 ramionach” jest **16× słabszy** (0,004 vs 0,06). Kandydaci: (1) prawdziwa dłoń nie jest rosnącym kołem na
środku — wchodzi z dołu/boku, jej krawędzie szybko wychodzą poza kadr, więc wszystkie 4 ramiona naraz (warunek „AND”) prawie
nigdy się nie zapalają; (2) dłoń i ściana mają podobną jasność (niski kontrast), a kamera sama wyrównuje jasność;
(3) siatka 40×25 i szybka dłoń z bliska — krawędź przeskakuje kilka „ommatidiów” na klatkę.
Test syntetyczny (ciemne koło na fakturze) był za łatwy względem prawdziwego obrazu.
