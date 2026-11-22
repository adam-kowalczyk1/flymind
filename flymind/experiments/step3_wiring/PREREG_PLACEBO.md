# Test „placebo” dla odruchów dotyku (plan spisany 22 XI 2026 PRZED liczeniem; symulacja, bez sprzętu)

## Pytanie
Przegląd literatury (21 XI) ostrzegł: gdy ustawienia dobiera się pod dane muchy i przenosi na tasowania (P1), przewaga bywa
fałszywa — nawet dwa różne tasowania „wygrywają” jedno z drugim (placebo). Nasze odruchy dotyku (15–18 XI) oceniano podobnie.
**Czy przewaga sieci z danych MaleCNS nad tasowaniami w teście „głośność” (LOUD r1, 18 XI) jest prawdziwa?**

## Wybrany test
„Dwa odruchy” z `reflex.py` + wyrównanie aktywności z `loud.py`, tylko **Glu +1** (tam dane wygrały: 54/80; przy Glu −1 nie wygrały —
nie badamy). Wynik pary scen = OBA (cofnięcie dłoni bez zaciskania ORAZ zaciśnięcie po dotyku palców) — bez zmian z LOUD r1.
Kod `reflex.py`, `loud.py`, `nets.py` nietknięty; nowa nakładka `placebo.py` tylko ustawia wzmocnienie g · M.

## Już wiadomo (widziane przed planem — opis, nie test)
LOUD r1 Glu +1, wyrównane: dane 54; F 1, 10, 0, 4, 32; L 1, 0, 2, 40, 1 (80 par). Same tasowania różnią się między sobą nawet o 31–39 par
(np. L4 40 vs L1 1), więc „wygrana” jednego tasowania nad drugim w tej metodzie zdarza się bez udziału danych — to powód testu.
Te dane NIE wchodzą do żadnego kryterium poniżej (nowe sceny, nowe tasowania).

## Dane (nowe ziarna, ze 27 xxx xxx — SEED_REGISTRY)
- Sceny testowe 27111, 27112, 27113 (po 6 póz; 5 materiałów × 6 = 30 par na ziarno, ok. 90 par razem); sieć z danych N.
- **10 nowych tasowań swobodnych F01–F10** (ziarna 27 121 001–010, `--net F`) i **10 nowych warstwowych L01–L10** (27 122 001–010, `--net L`).
- Każde tasowanie wyrównane DOKŁADNIE jak w LOUD r1 (`loud.py calib`: jedno g, aktywność = aktywność N ±2 %, bez robota).

## Część 1 — placebo przy metodzie P1 (jak LOUD r1; ustawienie = g z wyrównania aktywności)
Wszystkie 21 sieci (N, F01–F10, L01–L10) na tych samych scenach, M = 1.
- **C1 (powtórzenie)**: N lepsza na OBA od każdego z 10 tasowań rodziny F i od każdego z 10 rodziny L (McNemar dokładny,
  Holm w rodzinie 10, p_Holm < 0,05 i różnica > 0) — jak H-M w LOUD r1, ale 10 zamiast 5.
- **Placebo**: każde tasowanie po kolei gra rolę „danych” i jest porównane tym samym kryterium z 9 pozostałymi tasowaniami swojej rodziny
  (Holm w rodzinie 9). **FPR** = ułamek tasowań, które „wygrywają ze wszystkimi” (placebo wygrywa bez żadnych danych).
- **Rangowy test łączny**: p_rang = (1 + liczba tasowań z wynikiem ≥ N) / 21 (20 tasowań F+L).
- **Margines**: N_marg = wynik N − najlepsze z 20 tasowań; placebo_marg = najlepsze − drugie najlepsze tasowanie (w liczbie par OBA).
- **C2 (przewaga ponad placebo)**: FPR_F ≤ 0,1 i FPR_L ≤ 0,1 (najwyżej 1 z 10) ORAZ p_rang ≤ 0,05 (N ściśle powyżej wszystkich 20)
  ORAZ N_marg ≥ placebo_marg + 5 par (margines 5 ustalony z góry, ok. 5 % par).

## Część 2 — P2: ustawienia dobrane OSOBNO dla każdej sieci tym samym budżetem
Sieci: N, F01–F06, L01–L06 (13). Pokrętło: mnożnik M na wzmocnieniu sieci (po wyrównaniu aktywności), siatka
M ∈ {0,6; 0,8; 1,0; 1,25; 1,6} — 5 prób na sieć, **jednakowo dla wszystkich** (dane też strojone). Wybór: na scenach treningowych
**27131** (4 pozy, 20 par), M z największą liczbą par OBA; remis → M najbliższe 1 (w skali log), potem mniejsze. Zero zaglądania
w wynik na scenach testowych; wybór liczy `analyze_placebo.py select`. Potem test na scenach 27111–27113 przy wybranych M
(gdy M = 1, wynik z Części 1 — ten sam przebieg).
- **C3**: N (strojona) lepsza od każdego z 6 strojonych F i 6 strojonych L (McNemar, Holm w rodzinie 6, p_Holm < 0,05, różnica > 0)
  ORAZ wynik N ściśle wyższy niż najlepszy strojony tasowany.

## Werdykt (z góry)
- **PRAWDZIWA**: C1 i C2 i C3. Na plakacie wolno: „w symulacji, przy tej samej aktywności i osobnym strojeniu, sieć z danych
  wygrywa z tasowaniami” — z podaniem, że przy Glu −1 przewagi nie ma, i że to model, nie robot/mucha.
- **CZĘŚCIOWA**: C1 i C2, ale nie C3 — przewaga zależy od sposobu doboru ustawień; wolno tylko „przy tej samej aktywności”,
  bez słowa „przewaga połączeń muchy”.
- **ZAWYŻONA**: C1 lub C2 niespełnione — przewagi odruchów dotyku nie cytować jako dowodu roli połączeń z danych.
Opisowo (niewchodzące do werdyktu): wyniki W i C osobno; liczba istotnych par tasowanie-tasowanie (z 45 w rodzinie) vs N-tasowanie;
rozstęp wyników tasowań; zmiana wyniku po strojeniu; FPR strojonych tasowań.

## Zastrzeżenia z góry
- Jeden zestaw parametrów neuronu, jedna definicja „tej samej głośności” (jedno g), siatka P2 skromna (5 wartości jednego pokrętła; inne
  pokrętła nie stroją) — P2 jest więc słabszy niż CMA-ES. Wynik negatywny dla danych jest wynikiem; niczego nie zmieniam po wyniku.
- Odstępstwa od planu opiszę w `WYNIK_PLACEBO.md`. Ziarno 27 199 000 użyte na próbę dymną kodu (1 poza, jedna sieć).
- Uruchomienie: `run_placebo.sh` (Glu +1, 3 przebiegi naraz, OMP_NUM_THREADS=1, nice). Wyniki: `results/placebo_20261122/`.
