# Krok 0 — samo oko na kamerze nadgarstka (24 XI 2026, MuJoCo, bez sieci i sprzętu)
Plan: `experiments/wrist_eye/PREREG_KROK0.md`; ustawienia oka zapisane przed przebiegiem: `eye_settings.json` (FlyEye v2, commit aea7dd4, bez zmian lokalnych); skróty: `PRE_TEST_HASHES.txt`; liczby: `analysis.json`.

**P1 — wykrywa zbliżenie przy nieruchomym ramieniu: TAK** (10/10 pól szumu; szczyt 40 mV po obu stronach = maksimum; nieruchoma scena 0 mV, z szumem 0,001 mV).
Sygnał > 7 mV od 1,82 s (kula 11 cm od kamery, 0,18 s przed zatrzymaniem) do 2,11 s — 0,29 s z 0,63 s lotu kuli.

**P2 — mały zapisany ruch zmienia sygnał: CZĘŚCIOWO (8/15 trajektorii; próg „TAK” 12).** Obrót kamery 0,09–0,93° (mediana 0,46°).
Największa różnica KR − K: 1,5–8,4 mV (mediana 4,2); ponad podłogę szumu 1,2 mV w 15/15, ponad 2 mV w 12/15, ponad 10 % szczytu (4 mV) w 8/15.
Szczyt bez zmian (40 mV, obcięty, w 15/15). Sama kamera: 0,00 mV (fałszywych alarmów 0/15, także ×5 i ×20).
Po fakcie: różnica to przesunięcie narastania o 0–20 ms wcześniej (1–2 takty); największa przy ok. 1,90 s; rośnie z obrotem kamery (r = 0,97, 15 punktów).

**Kontrola czułości.** ×5 (0,5–4,6°): różnica 2,8–18 mV, 11/15 zauważalnych. ×20 (1,9–18,5°): 38–40 mV, 15/15; przeważnie sygnał ZNIKA lub pęka (9/15 nigdy nie przekracza 20 mV).
Przyczyny spadku przy ×20 nie rozdzielano (tłumienie ruchem obrazu, kula poza środkiem, zmiana odległości).

**Oko v3 (tylko tabela):** też 40 mV; mały ruch zmienia 3,6–11,0 mV (mediana 7,1); sama kamera ≤ 0,12 mV.

**Ograniczenia:** zapisany ruch powstał w odpowiedzi na wyliczony „wzrok” i zaczyna się 1,13–1,43 s; to oko daje pierwszy sygnał dopiero ok. 1,74 s, więc
z tym okiem sieć ruszyłaby później. Jedna kula, jedna prędkość (0,3 m/s), jeden tor przez środek kadru, szachownica; kąty ustawiane wprost; kamera 70° zamiast
prawdziwej; bez opóźnienia i rozmycia. Oko to nasz kod, nie neurony z danych. Prawdziwa kamera: oko v2 nie zdało (21 XI).
