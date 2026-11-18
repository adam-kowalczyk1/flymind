# Etap 2 — „dwa odruchy” kontra tasowania o tej samej aktywności (test 18 XI 2026, symulacja MuJoCo)

Cel zapisany przed testem: `experiments/step3_wiring/LOOP_TARGET_loud_r1.md`; hasze PRE = POST (`PRE/POST_TEST_HASHES_loud_r1.txt`,
także pliki kalibracji). Test raz: sceny 21874–21876, 6 póz, 66 przebiegów, 80 ważnych par na Glu. Analiza `analysis_loud_r1.json`.

## Pytanie
Krok 4 r2: sieć z danych częściej niż tasowania robi oba odruchy (dotyk dłoni → cofnij; dotyk palców → zaciśnij). Ale jest
2–4× aktywniejsza od tasowań. Tu każde tasowanie wzmocniono jedną liczbą g, aż jego aktywność = aktywność sieci z danych
(±2 %, bez robota; F5 Glu +1 −2,1 %). Potrzebne g: F 1,37–2,06, L 0,99–1,38.

## Wynik (pary z oboma odruchami, na 80)
| | Glu +1 | Glu −1 |
|---|---|---|
| Sieć z danych | **54** | **27** |
| 5 tasowań swobodnych (wyrównane) | 1, 10, 0, 4, 32 | 15, 45, 19, 8, 14 |
| 5 tasowań warstwowych (wyrównane) | 1, 0, 2, 40, 1 | 9, 0, 0, 28, 9 |
| H-M(F): dane lepsze od każdego z 5 (McNemar, Holm) | **POTWIERDZONA** (najsłabiej F5: 36:14, p_Holm 0,003) | **nie** (1/5) |
| H-M(L) | **POTWIERDZONA** (najsłabiej L4: 29:15, p_Holm 0,049) | **nie** (4/5; L4 24:25) |

**Glu +1: przewaga kroku 4 r2 nie wynika z samej aktywności — POTWIERDZONE [VERIFIED, model].**
**Glu −1: NIE potwierdzone** — przy tej samej aktywności tasowanie F2 robi oba odruchy częściej (45 vs 27; 35:17, p_Holm 0,07).

## Przewidywanie zapisane przed testem — chybione dla Glu +1
Przewidziałem „raczej niespełnione dla obu Glu” na podstawie treningu (13 par, 2 tasowania na rodzinę, gdzie L7 miało 10 vs
dane 8). Trening był za mały: na 80 parach jedno z dziesięciu tasowań (L4) zbliża się do danych, reszta nie.

## Co wolno powiedzieć
- Przy Glu +1 w zadaniu „dwa odruchy” schemat połączeń z danych muchy wygrywa z tasowaniami swobodnymi i warstwowymi także
  wtedy, gdy mają one tę samą aktywność. To silniejszy wynik niż krok 4 r2.
- Przy Glu −1 wynik zależy od głośności albo od przypadku — nie twierdzimy przewagi.

## Czego nie wolno
Że działa dla obu znaków Glu; że mucha tak robi; że działa na prawdziwym robocie. Wyrównanie jedną liczbą g to jedna
z możliwych definicji „tej samej głośności” (inna: wyrównanie na neuronach ruchowych — niezrobione).
