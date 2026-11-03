# FJ1: wyniki (2026-11-03)

**Przebieg:** `run_fj1.py --run`, 288 prób, 611 s. Sumy sha256 kodu, protokołu, MJCF i danych są identyczne przed i po.
Red team wyników dał werdykt **VALID WITH ISSUES**. Wszystkie werdykty przeliczył niezależnym skryptem z wynikiem MATCH;
integralność, ziarna i kolejność czasowa (przebieg po poprawkach protokołu) są w porządku.

| | Glu −1 | Glu +1 |
|---|---|---|
| A (obwód z danych) | 12/12 → **H1 POTWIERDZONA** | 12/12 → **H1 POTWIERDZONA** |
| C (10 tasowań), sukcesy na instancję | 0, 10, 0, 12, 12, 0, 0, 0, 12, 0 (średnia 4,6) → **H2 NIEROZSTRZYGNIĘTA** | 12 × 10 → **H2 ODRZUCONA** |
| D (trywialny odruch) | 12/12 → brak przewagi obwodu | jw. |
| N (moment 0 po dotyku) | 0/12 | jw. |

## Wniosek (język ustalony w protokole przed uruchomieniem)

W tym modelu symulacyjnym obwód dotykowy lewej środkowej nogi muchy z danych (MaleCNS) daje moment zamykający wystarczający,
by chwycić i unieść piłeczkę we wszystkich 12 nowych pozycjach. Warunki tego wyniku: zamrożone mapowanie wyjścia i klasyczne
rusztowanie ramienia. Działa to przy obu założeniach o glutaminianie.

Nie mamy jednak dowodu, że liczą się dokładnie te połączenia:
- przy Glu −1 przetasowane kontrole dały wynik skrajnie nierówny: 3 z 10 instancji też 12/12, 6 z 10 instancji 0/12, jedna 10/12;
- przy Glu +1 wszystkie przetasowane obwody też dały 12/12.

Kontrole:
- trywialny odruch (jedna linijka kodu) także dał 12/12, więc obwód nie daje przewagi nad prostym odruchem;
- kontrola zerowa dała 0/12, więc moment z jakiegoś sterownika jest konieczny, ale nie musi to być ten obwód.

Ograniczenia testu:
- Test jest progowy: wystarcza dowolny moment powyżej ok. 0,14 N·m.
- Mapowanie wyjścia wybrano po pilocie.
- 12 pozycji to pseudo-powtórzenia; realną próbą jest 10 instancji tasowania na każdy znak.

To replikacja dostrojonej konfiguracji, a nie niezależny dowód. To model w symulacji MuJoCo, a nie mucha ani prawdziwy robot.

## Czego NIE wolno twierdzić

- że liczą się konkretne połączenia ani że obwód z danych jest lepszy od losowego lub przetasowanego;
- że obwód jest lepszy od trywialnego odruchu;
- że mucha tak chwyta albo że wynik przenosi się na prawdziwy robot (mapowanie to analogia wybrana po pilocie);
- że mucha steruje ramieniem: badana była tylko szczęka, a sięganie jest klasyczne;
- że 12/12 to 12 niezależnych potwierdzeń;
- że znak glutaminianu jest rozstrzygnięty.

## Szczegóły z red teamu

- **Instancja C 9201002 (10/12):** porażki w dwóch pozycjach na najdalszym promieniu (0,23 m). Obwód milknie do 0 Hz,
  a szczęka zamyka się na chwilę i puszcza. Instancja leży na granicy progu momentu (w jednej z udanych pozycji tylko 14 Hz).
- **Pozostałe porażki C:** całe instancje milczą na każdej pozycji. Porażki przypadają na instancję, nie na pozycję.
- **Różnice fizyczne przy tym samym wyniku binarnym:**
  - D: ok. 8,2 N, kąt szczęki 0,485 rad;
  - A Glu −1: ok. 9,4 N, kąt szczęki 0,47 rad, czyli moment podobny do D;
  - A Glu +1: ok. 14,8 N, kąt szczęki 0,41 rad, czyli większy moment. To efekt mapowania, nie lepszy chwyt.
- **Drobna niezgodność czasu:** zapis o smoke w protokole (08:37) jest wcześniejszy niż plik smoke (08:38), bo smoke powtórzono
  po dodaniu ramienia N. Wcześniejszy wynik smoke był identyczny w ramionach A, C i D i nie jest zarchiwizowany.

## Co z tego wynika dla projektu

Szczęka jest zadaniem za łatwym, żeby odróżnić obwód muchy od czegokolwiek innego. Test, który może to rozróżnić, musi
wymagać zachowania, którego trywialny odruch nie da. Przykłady:
- puszczenie przy nieoczekiwanym kontakcie;
- dozowanie siły;
- sterowanie ramieniem (FJ2, `../fj2_fly_arm/DESIGN.md`).
