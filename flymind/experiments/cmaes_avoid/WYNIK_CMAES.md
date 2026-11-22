# WYNIK — CMA-ES „nie dać się dotknąć” (22 XI 2026, symulacja)

Plan spisany przed liczeniem: `PREREG_CMAES.md` (commit 977eb1a). Hash planu i programu: `results/PRE_RUN_HASH.txt`
(12:59). Zgoda Adama na start: 22 XI ok. 13:00. Uczenie: 13:07–13:58. Test (RAZ): 13:58. Kryteria liczy `analyze.py`
→ `results/analysis.json`.

## Werdykt: **FAILED** (C4 i C5 niespełnione)
Strojenie nauczyło sieć muchy cofać ramię niezawodnie (15/15), tylko po dotyku i tylko przez DNg15 + DNge078.
Ale **przemieszane sieci, strojone osobno tak samo długo, uczą się tak samo dobrze**, a nawet minimalnie lepiej.
Ten test nie pokazuje, że do tego zadania potrzebne są połączenia z danych.

Średni czas dotyku na 15 scenach testowych (ramię nieruchome: 1,69 s).

| Sieć (test, 15 scen) | czas dotyku [s] | unika | bez dotyku (numb) | bez DNg15+DNge078 |
|---|---|---|---|---|
| mucha z danych, bez strojenia | 1,14 | 15/15* | — | — |
| **mucha z danych, strojona** | **0,10** | **15/15** | 1,69 (0/15 unika) | 1,69 (0/15 unika) |
| przemieszana L-A, strojona | 0,09 | 15/15 | 1,69 (0/15) | nie mierzono |
| przemieszana L-B, strojona | 0,09 | 15/15 | 1,69 (0/15) | nie mierzono |
| bez muchy (drut), strojony | 0,08 | 15/15 | 1,69 (0/15) | — |

| Kryterium | wynik |
|---|---|
| C1 uczy się (≥ 13/15 i ≥ 0,3 s lepiej niż bez strojenia) | ✓ 15/15, 1,14 → 0,10 s |
| C2 bez dotyku nie unika (≤ 2/15) | ✓ 0/15 |
| C3 bez DNg15 + DNge078 nie unika (≤ 2/15) | ✓ 0/15 |
| C4 dane lepsze od każdego tasowania o ≥ 0,2 s | ✗ 0,10 vs 0,09 i 0,09 |
| C5 przewaga danych większa niż różnica między tasowaniami | ✗ brak przewagi |

\* Próg „unika” (czas dotyku < T₀ − 0,2 s) spełnia już sieć bez strojenia: łokieć i nadgarstek drgną po dotyku, ale
ramię nie odjeżdża (odstęp końcowy ≈ 0 cm). Po strojeniu ramię odjeżdża na ~23 cm.

## Co to znaczy (prosto)
1. **Strojenie działa.** Pokrętła wystarczą, żeby z „drgnięcia” zrobić pewne cofnięcie: 0,1 s dotyku to praktycznie
   minimum, bo bez wzroku ramię musi najpierw poczuć dotyk. Ruch dalej wymaga sieci: bez dotyku ani po wycięciu dwóch
   neuronów zstępujących ramię stoi.
2. **Ale zadanie jest za łatwe, żeby coś rozstrzygnąć.** Wszystkie cztery sieci uderzają w to samo dno (~0,1 s).
   Każdą sieć, która w ogóle przenosi „dotyk → ruch”, da się wzmocnić pokrętłami. To właśnie przestroga z przeglądu z 21 XI:
   bez osobno strojonych tasowań wyglądałoby to na sukces połączeń muchy. Nie był.
3. **Na plakat / Explory wolno:** „po dostrojeniu ~30 pokręteł (połączenia z danych bez zmian) mózg muchy w symulacji
   cofa ramię po dotyku dłoni w 15/15 prób; bez dotyku albo bez dwóch neuronów zstępujących — nigdy”.
   **Nie wolno:** „dzięki połączeniom z konektomu” ani „lepiej niż losowa sieć” — przemieszane, dostrojone tak samo, robią to samo.

## Szczegóły i odstępstwa
- Sieć z danych po strojeniu: ruch łokciem i nadgarstkiem (≈ −0,9 rad każdy), bark nieruszony. Tasowania odjeżdżają
  wszystkimi trzema stawami (~35 cm). Drut: głównie łokciem. Ruch przed dotykiem: 0 we wszystkich sieciach z neuronami
  (drut 0,04 rad).
- Na zbiorze uczącym przemieszane też były minimalnie lepsze (J −0,113 vs −0,100), więc to nie przypadek testu.
- Strojenie uderzało w granice pokręteł (x = ±3, czyli wzmocnienie ×20 albo ×0,05) we wszystkich sieciach.
- Odstępstwa: `analyze.py` napisany po zapisaniu hasha, ale przed testem (liczy tylko kryteria z planu, bez zmian).
  Plan nie przewidział wycięcia DN w tasowaniach. Nic poza tym nie zmieniono.
- Ograniczenia: kinematyka bez fizyki, ręka = kula, bez wzroku, mała sieć (bez głowy), jedno ziarno CMA na sieć.
  Ziarna 26 1xx xxx z tego planu są ZUŻYTE.

## Co dalej (propozycje, nic nie uruchomione)
- Trudniejsze zadanie, w którym połączenia mogą mieć znaczenie: np. dotyk z różnych miejsc → różny kierunek ucieczki
  albo jednocześnie „dociśnij przy szczęce / cofnij przy dłoni” (test „GDZIE” pokazał, że mucha te miejsca rozróżnia),
  oceniane na tych samych kontrolach.
- Mniej pokręteł (np. tylko wejścia i wyjścia, bez bloków połączeń): wtedy mniej swobody, żeby „naprawić” losową sieć.
