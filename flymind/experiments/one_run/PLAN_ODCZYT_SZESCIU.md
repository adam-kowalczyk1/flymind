# Odczyt sześciu osi w próbie 45 s (24 XI 2026, zapisane PRZED przebiegiem)

Powtórka przebiegu `pelny` z `one_run.py` (plik BEZ zmian, suma jak w PRE_HASHES): to samo ziarno 27 601 001, te same bodźce, to samo sterowanie (bark, łokieć, nadgarstek dotychczasową mapą;
podstawa, obrót i szczęka klasycznie). Jedyna różnica: do słownika masek `net._grp`, z którego pętla liczy impulsy do logu, dochodzi 76 masek po jednym neuronie. Maski nie wchodzą do sieci, wejść ani komend.
Tylko MuJoCo. Nic z nowych odczytów nie idzie do stawów.

## Zgodność (bez tolerancji)
Wszystkie pola dawnego zapisu (`q_all, dq, qc, qt, r, loom, felt, ball, rot, flag, guard, ncon, real_touch, q0, t` oraz 5 pierwszych kolumn `cnt`) równe co do bitu. Jeśli nie — wynik mapy nieważny.
Sprawdzian odczytu: częstości obecnego barku, łokcia i nadgarstka odtworzone z pojedynczych neuronów = zapisane `r` (≤ 1e-9 Hz).

## Komendy (ta sama reguła co dziś)
r ← r + 0,2·(średnia grupy w takcie [Hz] − r), komenda = 0,005 rad/s/Hz · (r₊ − r₋); średnia po neuronach grupy; amplitudy bez skalowania.
1 podstawa promotor 4 / remotor 2 · 2 bark Tr flexor + Acc 11 / Tr extensor + Sternotroch. + Tergotr. 8 · 3 łokieć Ti flexor + Acc 15 / Ti extensor 2 · 4 nadgarstek Ta levator 2 / Ta depressor 5 ·
5 obrót przedni rotator 2 / tylny rotator 4. Znak „+” = pierwsza grupa (mięsień), nie kierunek serwa: dla podstawy i barku znak serwa nie jest wybrany.
6 chwytak: ltm 4, ltm1 2, ltm2 2 osobno (bez pary „−”); obok T2 L: zaciskanie = Ti extensor 2, zwalnianie = Ti flexor + Acc 11, moment 0,005·(r₊ − r₋) N·m jak w `reflex.TwoNet`.
Bez limitów i SafetyLayer (nie są wysyłane).

## Obrót a podstawa (kierunek anatomiczny: + przód, − tył)
(1) impulsy w kubełkach 100 ms: tylko podstawa / tylko rotatory / oba / nic; (2) takty: jeden > 0,57 °/s, drugi < 0,05 °/s; (3) takty: oba > 0,05 °/s i przeciwny znak; jak (3) z progiem 0,57;
(4) kubełki 0,5 s: suma komendy > 0,05° u obu i przeciwny znak, oraz u jednego > 0,05° przy 0 impulsów drugiego. Wszystko w całym przebiegu i w oknach bodźców. Jeden przebieg, jedno ziarno — pokaz, nie test.
