# Krok 6 — dotyk „głowy” porusza łokciem i nadgarstkiem ramienia (16 XI 2026)

Symulacja MuJoCo, ramię SO-101, sieć z danych MaleCNS (3221 neuronów: sieć nogi „pre” + 69 neuronów szczecinek głowy BM +
2 DNge078 + 2 DNg15). Czujnik dłoni robota → neurony BM (naturalny receptor). Klasyczny kod: dojazd, sonda, bezpiecznik.
O ruchu łokcia i nadgarstka decyduje sieć. Bez prawdziwego robota.

## Trzy testy, każdy raz, z celem zapisanym wcześniej

| Test | Pytanie | Wynik |
|---|---|---|
| r1 (ziarno 21831) | Dotyk dłoni (naturalny, sama ręka dociska) → łokieć i nadgarstek ≥ 80 % prób | **FAILED**: Glu −1 71 %, Glu +1 nadgarstek 0 %. Tylko sieć z danych łączy ruch po dotyku ze spokojem bez dotyku (20:0 vs każde z 10 tasowań) |
| r2 (ziarno 21861) | To samo, ale dotyk trwa stałe 0,5 s (sonda jak palec) | **PASS** oba Glu: 26/26 łokieć i nadgarstek, 30/30 spokój bez dotyku; 26:0 vs każde z 10 tasowań |
| r3 (ziarno 21891) | Wycięcie jednego szlaku | **PASS** oba Glu: bez DNg15 łokieć 0/27, nadgarstek 27/27; bez DNge078 łokieć 27/27, nadgarstek 0/27 |
| r4 (ziarno 21631) | r2 + r3 z szumem neuronów 2 mV (standard) i 6 mV (stres) | **PASS** oba Glu i oba poziomy: 26/26 i ten sam podział po wycięciu |

## Dlaczego r1 nie wyszedł (diagnoza na ziarnach treningowych)
Sieć odsuwa dłoń od dotyku; gdy kontakt znika (10–30 ms na twardym/śliskim/ciężkim walcu), ruch się kończy. Przy zamrożonym
ramieniu kontakt trwa całe 0,5 s — więc to ruch sieci kończy bodziec. Przy Glu +1 łokieć prostuje się 2× szybciej
i nadgarstek nie zdąży. r1 mierzył więc długość bodźca, a nie odpowiedź sieci.

## Integracja i spis stawów
- Ta sama sieć (z drogami z głowy) w zadaniu całego ramienia z kroku 3: 29/45 i 30/45 odłożonych — dokładnie jak bez dróg
  z głowy, próba w próbę (sceny treningowe; eksploracja, nie test).
- Kto steruje czym: sieć — bark, łokieć, nadgarstek przy podnoszeniu, obrót nadgarstka przy trzymaniu, szczęka, odruch
  łokcia i nadgarstka na dotyk; podstawa (staw 0) — z sieci tylko w pokazie 1 (wzrok); klasyczne — dojazd, zejście,
  odkładanie (IK), kolejność faz, bezpiecznik.

## Co wolno powiedzieć
- W tym modelu dotyk przy „głowie” porusza dwoma stawami przez dwa osobne szlaki z danych muchy: BM→DNg15→łokieć
  (prostowanie) i BM→DNge078→nadgarstek (unoszenie). Wycięcie szlaku wyłącza dokładnie jego staw (VERIFIED, model).
- Sieci z przetasowanymi połączeniami nie dają tego wzoru (ruszają się bez dotyku albo tylko łokciem).

## Czego NIE wolno powiedzieć
- Że mucha tak robi — szlaki wybrałem z danych sam; to model, nie pomiar na musze.
- Że ramię odsuwa się od dowolnego dotyku w świecie — r1 (naturalny dotyk) nie przeszedł; r2/r3 używają sondy.
- Że to działa na prawdziwym robocie.
- r2 i r3 powstały po porażce r1 — r1 zostaje FAILED.

## Ograniczenie kontroli
Tasowanie „B” (grupy BM i DN zachowane) zostawia szlaki prawie nietknięte (tylko 4 DN), więc nie było kontrolą szlaków —
zamiast niego zrobiłem wycięcie (r3). W r1–r3 sieć była bez szumu (wyniki 0 / 100 %); r4 pokazał, że z szumem 2 i 6 mV wynik jest ten sam.

Pliki: `audit_log_step3_20261115.md` (kroki 48–74), `LOOP_TARGET_brainleg_r4.md`, `analysis_noise_r4_s2/s6.json`, `brainleg_noise_test/`, `LOOP_TARGET_brainleg_r1/r2/r3.md`, `analysis_brainleg_r1/r2.json`,
`analysis_lesion_r3.json`, `brainleg_test/`, `brainleg_probe_test/`, `brainleg_lesion_test/`, `explore_step6/`.
