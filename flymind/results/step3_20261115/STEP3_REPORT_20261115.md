# FlyMind — krok 3 i 4: odpowiedzi na dwie sprawy (15 XI 2026)

Wszystko w symulacji MuJoCo. Cele i sposób analizy każdego testu były zapisane przed jego uruchomieniem
(`PRE_TEST_HASHES.txt`); każdy test na nowych scenach i nowych tasowaniach, uruchomiony raz. Szczegóły i wszystkie liczby:
`audit_log_step3_20261115.md`. Kod: `flymind/experiments/step3_wiring/`.

## Sprawa 1 — „mucha nie steruje całym ramieniem”

**Odpowiedź: steruje podnoszeniem ramienia i odkłada przedmioty tak dobrze jak klasyczny sterownik. Nadgarstkiem nie.**

Co było nie tak: w kroku 2 wzięliśmy z mapy połączeń za mały wycinek (36–55 % wejścia „mięśni”). Po dołożeniu z danych
wszystkich neuronów, które łączą się z neuronami ruchowymi nogi (74–82 % wejścia), bark zaczął pracować. Niczego nie
stroiłem: te same wagi, progi, wzmocnienie i reguły co w kroku 2.

| Test (135 nowych scen) | Wariant znaku | Sieć z danych | Klasyczny | Prosty odruch |
|---|---|---|---|---|
| limit podnoszenia 3 s | +1 | **88** | 90 | 55 |
| limit podnoszenia 3 s | −1 | **0** (unosi 102, za wolno) | 85 | 53 |
| limit podnoszenia 10 s | +1 | **94** | 93 | 59 |
| limit podnoszenia 10 s | −1 | **86** | 86 | 58 |

Siła ramienia na stół 0 N i 0 zadziałań bezpiecznika we wszystkich próbach sieci z danych.
„Wariant znaku” to niewiadoma z danych: nie wiemy, czy glutaminian w tych neuronach pobudza, czy hamuje, więc liczymy oba.

Czego nadal nie ma: (1) nadgarstek — jego „mięśnie” nie dostają sygnału z żadnego receptora nogi; w muszce słuchają
m.in. poleceń z mózgu; (2) przy wariancie −1 pracuje sam łokieć i jest wolny (5,5 s zamiast 1,9 s); (3) prawdziwe ramię.

## Sprawa 2 — „nie mamy dowodu, że liczy się schemat połączeń”

**Odpowiedź: liczy się dla tego, KTÓRY ruch wywołuje KTÓRE czucie — to potwierdzone. Nie liczy się dla tego, ile
przedmiotów ramię odłoży w zadaniu, które nagradza po prostu silny napęd.**

1. **Bez robota, potwierdzone na 80 nowych tasowaniach, przy obu wariantach znaku.** W sieci z danych dotyk nogi środkowej
   pobudza mięśnie tej samej nogi 81 Hz, a nogi przedniej 3,5 Hz (wskaźnik wybiórczości 0,87 i 0,91 w skali do 1).
   Po losowym przepięciu połączeń — także takim, które zachowuje warstwy czucie → pośrednie → ruch — wybiórczość znika
   (najwyżej 0,12). Przetasowana sieć „nie wie, która noga została dotknięta”.
   Granica: jeśli tasowanie zachowuje też, które neurony należą do której nogi, wybiórczość w dużej części zostaje
   (wariant +1: dane nadal najlepsze, o włos; wariant −1: już nie). Czyli liczy się głównie „która noga z którą”.
2. **Na robocie — zadanie „dwa czucia, dwa odruchy”** (dotyk dłoni → cofnij ramię i nie zaciskaj; dotyk palców → zaciśnij
   i trzymaj; jedna sieć steruje szczęką i ramieniem). Liczba par scen z oboma odruchami udanymi, na 24:
   wariant +1: dane **15**, tasowania swobodne **0, 0, 0, 0, 0**, zachowujące warstwy 5, 9, 16, 3, 2;
   wariant −1: dane 5, pozostałe prawie same zera.
   Sieć z danych wygrywa ze wszystkimi tasowaniami swobodnymi (potwierdzone), z tasowaniami zachowującymi warstwy w 3 z 5
   — pełne kryterium, które zapisałem przed testem, **nie jest spełnione**.
3. **W zadaniu „unieś i odłóż”** sieci przetasowane wypadają tak samo (73–92 wobec 88) — bez zmian.
4. Dwie moje hipotezy upadły i tak to zapisuję: sieć z danych nie jest „cichsza” (jest aktywniejsza niż wszystkie 80
   tasowań) ani jednoznacznie „spokojniejsza w ruchu” (9 z 10, a miało być 10).

## Jak to powiedzieć jurorowi

„Gdy przepnę połączenia losowo, robot dalej potrafi podnieść przedmiot, bo do tego wystarczy silny sygnał. Ale przestaje
rozróżniać, co zostało dotknięte: prawdziwa sieć po dotyku dłoni cofa rękę, a po dotyku palców zaciska chwyt —
przetasowana myli te reakcje albo nie reaguje wcale. Schemat połączeń decyduje więc o tym, który ruch odpowiada na które
czucie, a nie o samej sile ruchu.”

## Uczciwe granice

- Symulacja; uproszczone neurony; jeden zestaw parametrów; przypisanie „dłoń = noga przednia, palce = noga środkowa”
  i „mięśnie nogi → stawy ramienia” to nasz wybór, nie biologia.
- Wynik na robocie zależy od wariantu znaku glutaminianu; wynik bez robota — nie.
- Próba cofania używa jednego kształtu (walec 60 mm), bo tylko na nim dłoń robota może usiąść.
- Najostrzejsza kontrola pokazuje, że dobór pojedynczych neuronów ma znaczenie najwyżej częściowe.

## Propozycje (nic z tego nie zrobiłem)

1. Plakat: zdanie „całe ramię: 0/135” jest już nieaktualne — do decyzji, czy poprawić przed oddaniem (termin 16 XI).
2. Nadgarstek: przeszukać w danych drogi z mózgu (neurony zstępujące) do mięśni stępu i sprawdzić, jakie naturalne czucie
   je uruchamia.
3. Powtórzyć test dwóch odruchów z większą liczbą scen i tasowań tylko dla rodziny „warstwy” (3 z 5 to za mało, by
   rozstrzygać).
4. Commit i kopia zapasowa nowych plików (`experiments/step3_wiring/`, `results/step3_20261115/`) — czeka na decyzję.
