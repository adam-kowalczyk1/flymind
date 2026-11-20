# T2 v2 — komórki zbliżania MaleCNS (LPLC2 + LPi + rekurencja) na oku flyvis: **FAILED** (20 XI 2026)

Kryteria (PREREG_T2.md, PASS gdy w ≥ 2 z 3 modeli): K1 AUC test ≥ 0,90; K2 prawdziwe − potasowane ≥ 0,10; K3 zbliżanie
w czasie ruchu kamery ≥ 0,5 × czyste zbliżanie. Wynik: **0 / 3 modeli** (K1 0/3, K2 0/3, K3 3/3).

| model | LPLC2 prawdziwe AUC test | potasowane | różnica (K2) | K3 (prawdziwe) | bez LPi | nieuczony | LC4 |
|---|---|---|---|---|---|---|---|
| 000 | 0,74 | 0,76 | −0,02 | 1,01 | 0,44 | 0,29 | 0,42 |
| 001 | 0,87 | 0,77 | +0,10 (0,097) | 0,82 | 0,55 | 0,35 | 0,54 |
| 002 | 0,30 | 0,75 | −0,45 | 1,11 | 0,19 | 0,15 | 0,22 |

AUC trening: prawdziwe 0,995 / 1,000 / 0,805; potasowane 1,000 ×3.

## Rozbicie po rodzajach bodźców (opis po wyniku, NIE test)
AUC jednej grupy zbliżań wobec wszystkich negatywów testu:

| | zbliżanie l/v 20 ms | l/v 80 ms | zbliżanie na fakturze | zbliżanie w ruchu kamery |
|---|---|---|---|---|
| prawdziwe 000 / 001 / 002 | 0,79 / 0,94 / 0,28 | 0,68 / 0,90 / 0,29 | 0,82 / 1,00 / 0,15 | 0,66 / 0,57 / 0,51 |
| potasowane 000 / 001 / 002 | 1,00 / 1,00 / 1,00 | 1,00 / 1,00 / 1,00 | 0,34 / 0,50 / 0,27 | 0,46 / 0,35 / 0,48 |

Potasowane okablowanie uczy się „dysku na szarym tle” (idealnie), ale zawodzi, gdy zbliżanie jest na fakturze.
Prawdziwe okablowanie (modele 000, 001) radzi sobie z fakturą lepiej. To hipoteza po fakcie, sprawdzana w T2c na nowych modelach.

## Wnioski
- Oko flyvis + prawdziwe synapsy MaleCNS do LPLC2/LPi + uczone tylko właściwości typów: **nie** daje dziś niezawodnego
  detektora zbliżania (najlepiej 0,87) i **nie** pokazało przewagi prawdziwego okablowania w kryterium z planu.
- LPi pomagają (bez LPi 0,19–0,55, z LPi 0,30–0,87); bez uczenia 0,15–0,35 — samo okablowanie nie wystarcza.
- Model 002 uczył się słabo (trening 0,81) — wrażliwość na start.
