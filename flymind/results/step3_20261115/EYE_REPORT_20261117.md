# FlyMind, 17 XI 2026: test „widzenie jak oko złożone muchy”

Wszystko w symulacji.
- Cel i przewidywania zapisane przed testem: `experiments/step3_wiring/LOOP_TARGET_eye_r1.md`.
- Test uruchomiony raz; szczegóły w `audit_log_step3_20261115.md`, wiersze O1–O5.
- Nic nie zostało zacommitowane.

## Co zmieniłem
Sieć nie dostaje już informacji od detektora koloru. Dostaje obraz przepuszczony przez **model oka złożonego**:
- **296 oczek (omatidiów) co 5°.** Każde widzi tylko jasność, tak jak komórki R1–R6 muchy, które prawie nie widzą czerwieni.
- Obrazki: `fly_view/co_odbiera_mucha_oko.png` (czerwony: 7 aktywnych oczek; żółty: 0).

Uczciwie: to model **optyki** oka, a nie neuronów. Między oczkami a neuronami LC10a nadal działa prosty detektor kontrastu.

## Wynik według reguł zapisanych przed testem: SPEŁNIONE [VERIFIED, model]
| Liczba przedmiotów odłożonych do pudełka (na 45) | czerwony | zielony | niebieski | żółty |
|---|---|---|---|---|
| Sieć muchy, detektor koloru (odniesienie) | 29 | — | — | — |
| **Sieć muchy, oko złożone** | **30** | 4 | 3 | 2 |
| Sterownik klasyczny, oko złożone | 33 | 3 | 3 | 3 |

- Z widzeniem „jak mucha” sieć steruje **tak samo dobrze** jak z detektorem koloru (30 wobec 29) dla przedmiotów, które oko muchy widzi.
- Przedmioty, które dla oka muchy mają tę samą jasność co szary stół (zielony, niebieski, żółty), są **prawie niewidoczne** (2–4 na 45), jak przewidywał model.
- Prawdziwa mucha widzi te kolory dodatkowymi komórkami R7 i R8 oraz ruchem. Tego model jeszcze nie ma.

## Co dalej
Następny krok to „inżynieria wsteczna” prawdziwych neuronów oka przez flyvis, czyli wytrenowany model płata wzrokowego oparty na konektomie. Plan sesji „Oko muchy” leży w `reports/fly_eye_reverse_engineering_plan_20261116.md` i czeka na Twoje decyzje.
