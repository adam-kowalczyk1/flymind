# Etap 1 — sieć sama kończy zwykły dotyk dłoni (test 18 XI 2026, symulacja MuJoCo)

Cel zapisany przed testem: `experiments/step3_wiring/LOOP_TARGET_touch_r1.md` (hasze PRE = POST, `PRE/POST_TEST_HASHES_touch_r1.txt`).
Test raz: sceny 21871, 6 póz, 24 przebiegi, 26 ważnych par na Glu. Analiza: `analysis_touch_r1.json`.

| | Glu +1 | Glu −1 |
|---|---|---|
| T1_A sieć z danych kończy dotyk (≥ 80 %) | **26/26 PASS** | **18/26 = 69 % FAILED** |
| T1_B bez DNg15 i DNge078 kończy dotyk (≤ 20 %) | 0/26 PASS | 0/26 PASS |
| T1_C bez dotyku stoi (≥ 95 %) | 26/26 PASS | 26/26 PASS |
| H(F), H(L) wybiórczo lepiej niż każde z 5+5 tasowań | PASS (tasowania 0–9/26) | PASS (tasowania 0/26) |
| mediana czasu do końca dotyku | 0,04 s | 0,04 s |

Glu −1, porażki: walec lekki 1/6 i średni 1/4 (twardy, śliski, ciężki 16/16) — przedmiot jedzie z dłonią (jak w treningu).
Przewidywanie z celu (Glu +1 tak, Glu −1 na granicy) potwierdzone; Glu −1 zostaje FAILED.

**Wolno powiedzieć (model):** przy Glu +1 sieć z danych sama kończy zwykły dotyk dłoni w 26/26 próbach, a bez dotyku stoi;
po wycięciu 4 neuronów (2 DNg15 + 2 DNge078) dotyk nie kończy się nigdy (0/26) — to te dwa szlaki odsuwają dłoń.
**Nie wolno:** że działa przy obu znakach Glu (Glu −1 69 %), że mucha tak robi, że działa na prawdziwym robocie.
Kontrola tasowaniami jest słaba (tasowania ruszają się też bez dotyku); mocną kontrolą jest wycięcie.
