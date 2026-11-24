# Zamrożona nowa podstawa i bark: 10 nowych ziaren (24 XI 2026, zapisane PRZED przebiegami)

Nic się nie zmienia wobec próby `base_shoulder.py` (`nowa`): mapa, znaki (podstawa +1, bark −1, łokieć +1, nadgarstek −1), wzmocnienie 0,005 rad/s/Hz, filtr 50 ms, limity, scena 45 s, Glu −1, szum 2 mV. Zmienia się tylko ziarno szumu sieci.
Zamrożenie: `results/seeds10_20261124/zamrozenie.json` (sumy 38 plików, identyfikatory pul, macierz sieci); skrypt `seeds10.py` odmawia pracy, gdy cokolwiek się różni. Tylko MuJoCo, bez strojenia i bez sprzętu.

Ziarna: **27 602 001 – 27 602 010** (nowe, zarejestrowane). Przed nimi sprawdzian: ziarno 27 601 001 ma odtworzyć próbę `nowa` co do bitu (nie liczy się do wyników).

**Główna miara:** ruch barku (staw 1, kąt z MuJoCo) podczas pierwszego nacisku A0: kąt w 22,00 s minus kąt w 20,00 s. Podaję wszystkie 10 wartości, medianę, zakres, liczbę ruchów w tym samym kierunku. |ruch| < 0,05° = „bez ruchu” (liczone osobno, nie jako kierunek).
Plus = +q1 = opuszczanie (tak jak w próbie 27 601 001: +12,3°). Nie ma progu zaliczenia: to opis powtarzalności, nie test hipotezy. Ziarno pilotażu nie wchodzi do 10 wartości.

Wtórne, tak samo liczone: podstawa, łokieć (i nadgarstek, bark) przy A0 (20–22 s) i pierwszym A1 (27–29 s; drugie A1 w 36 s nakłada się na zbliżenie, więc osobno tylko w pliku); każdy staw.
Spokój: 0–6 s — zmiana kąta i największe wychylenie każdego stawu (od początku sceny, po 1 s osiadania) oraz liczba impulsów 76 neuronów.
Zadziałania ograniczeń: flagi SafetyLayer na staw, strażnik stołu, kontakty. Zbliżenie 2 ma artefakt przycinania kuli (od ok. 15 mm), więc nie wchodzi do żadnej miary.
Wszystkie 10 przebiegów pokazuję niezależnie od wyniku; przebieg przerwany błędem zgłaszam, nie zastępuję innym ziarnem.
