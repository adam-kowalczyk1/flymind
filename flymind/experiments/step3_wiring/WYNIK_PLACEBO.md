# WYNIK — test „placebo” dla odruchów dotyku (22–23 XI 2026, symulacja, Glu +1)

Plan przed liczeniem: `PREREG_PLACEBO.md` (commit 951f796, hasze w `results/placebo_20261122/PRE_RUN_HASH.txt`). Wszystko policzone
raz, kryteria bez zmian po wyniku. Dane: `results/placebo_20261122/` (`analysis_placebo.json`). 93 przebiegi testu + 65 treningowych.

## Werdykt: **CZĘŚCIOWA** (C1 ✓, C2 ✓, C3 ✗)
Przewaga sieci z danych przy tej samej aktywności **powtórzyła się na nowych scenach i nowych tasowaniach** i nie jest artefaktem
„placebo”. Ale **znika po strojeniu osobno**: strojone tasowania warstwowe dorównują danym.

## Część 1 — metoda P1 (jak LOUD r1), 79 ważnych par, 20 nowych tasowań
| sieć | dane N | F01–F10 (swobodne) | L01–L10 (warstwowe) |
|---|---|---|---|
| pary z oboma odruchami | **43** | 26, 4, 17, 3, 0, 6, 0, 0, 5, 26 (mediana 4,5) | 21, 2, 4, 11, 16, 1, 14, 3, 0, 13 (mediana 7,5) |

- **C1 ✓** dane lepsze od każdego z 10 F i każdego z 10 L (najsłabiej: F01 31:14, p_Holm 0,016; L01 32:10, p_Holm 0,0009).
- **C2 ✓** placebo: żadne z 20 tasowań nie wygrało ze swoimi rówieśnikami (FPR 0/10 w obu rodzinach); p_rang = 1/21 = 0,048
  (dokładnie próg — minimum możliwe przy 20 tasowaniach); margines danych 17 par (43 vs najlepsze 26) ≥ 0 + 5.
- Ale **placebo jest głośne**: 24 z 45 par tasowań F i 25 z 45 par L różni się istotnie (p < 0,05 bez korekty) — czyli samo porównanie
  „pary OBA, McNemar” widzi „przewagę” tasowania nad tasowaniem w ponad połowie par. Rozstęp wyników tasowań 26 (F) i 21 (L).
  Test par pojedynczych jest więc zbyt liberalny; stąd kryterium z 10 tasowaniami na rodzinę zamiast wygrania z jednym.
- Wynik danych niższy niż w LOUD r1 (54/80 → 43/79); wzorzec ten sam (dane na szczycie, bez wygranej na Glu −1, którego nie badano).
  Dwa najlepsze tasowania miały po 26 (remis → margines placebo 0).

## Część 2 — P2: strojenie osobno (mnożnik 0,6–1,6, wybór na scenach treningowych 27131)
Wybrane M: dane 0,8; F: 0,8 / 0,6 / 1,0 / 1,0 / 1,6 / 1,0; L: 0,6 / 0,8 ×5.

| | dane | F01–F06 | L01–L06 |
|---|---|---|---|
| bez strojenia (M = 1) | 43 | 26, 4, 17, 3, 0, 6 (mediana 5) | 21, 2, 4, 11, 16, 1 (mediana 7,5) |
| **po strojeniu** | **56** | 32, 27, 17, 3, 9, 6 (mediana 13) | 21, **45**, 29, 31, **41**, 6 (mediana 30) |

- Jedno pokrętło podniosło tasowania warstwowe z mediany 7,5 do 30 (L02: 2 → 45), dane tylko z 43 do 56.
- **C3 ✗**: dane lepsze od wszystkich strojonych F (p_Holm ≤ 0,0015), ale **nie od strojonych L**: L02 23:12 (p_Holm 0,098)
  i L05 33:18 (p_Holm 0,098) — różnica niewykazana; wynik danych (56) nadal najwyższy (L02 45, L05 41).

## Co to znaczy (prosto)
1. Przewaga odruchów dotyku **nie była pozorna** w sensie placebo — tasowania z tym samym sposobem porównania nie wygrywają między sobą ze wszystkimi.
2. Jest jednak **zależna od ustawienia głośności**: po prostym dostrojeniu jednego pokrętła tasowania warstwowe (zachowujące „bok” nogi
   i warstwy) niemal dorównują danym. Przy samej aktywności wyrównanej bez strojenia dane wygrywają wyraźnie; przy strojeniu osobno — tylko z tasowaniami swobodnymi.
3. Liczą się więc cechy ogólne (strona, warstwy), a nie wyłącznie szczegółowe połączenia muchy — spójne z CMA-ES z 22 XI.

## Na plakat
Wolno (forma ostrożna): „W symulacji, przy tej samej aktywności sieci, schemat połączeń z danych muchy częściej niż 20 przemieszanych sieci
wykonuje oba odruchy dotyku (43 vs mediana 5–8 z 79 prób), także przy teście z osobnym placebo”. Z dopiskiem: „po osobnym dostrojeniu jednego
pokrętła część przemieszanych sieci (zachowujących warstwy) dorównuje” oraz: tylko Glu +1, model, nie robot ani prawdziwa mucha.
Nie wolno: „połączenia muchy są potrzebne/lepsze”, „przewaga niezależna od strojenia”, przewaga przy Glu −1.

## Odstępstwa i zastrzeżenia
- Ważnych par 79 (plan: ok. 90) — rzeczywista liczba z niedostępnych póz. Kalibracja F06 trafiła w aktywność z błędem 2,1 % (próg 2 %), jak w LOUD r1 dopuszczone.
- P2 skromny: jedno pokrętło, 5 wartości, trening 20 par (wybór szumny); nie sprawdzono innych pokręteł ani innej definicji głośności.
- Margines p_rang jest na granicy 0,05 (1/21). Test na jednym rodzaju pary (OBA); W i C osobno nie analizowane.
