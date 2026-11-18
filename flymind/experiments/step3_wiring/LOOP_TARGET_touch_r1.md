# Etap 1 — czy sieć sama kończy ZWYKŁY dotyk dłoni? (cel zapisany PRZED testem, 18 XI 2026)

## Skąd ten test (jawnie: pomysł powstał po porażce)
Krok 6 r1 (ziarno 21831) **FAILED**: przy zwykłym dotyku łokieć i nadgarstek ruszały się za mało, bo — według diagnozy
na scenach treningowych — sieć odsuwała dłoń i dotyk znikał po 10–30 ms. r1 mierzył więc długość bodźca. Ten test
pyta o to, co odruch wycofania naprawdę ma robić: **czy sieć sama kończy dotyk**, a bez dotyku stoi. r1 zostaje FAILED.

## Próba (bez zmian względem kroku 6 r1)
`touch_natural.py` = `brainleg.py` (świat, sieć 3221 neuronów, F_ON 3 N, 0,5 s sterowania siecią, progi) + tylko ZAPIS
siły dłoni po każdym kroku świata i opcjonalne wycięcie wyjść DNg15 i DNge078 (jak `brainleg_lesion.py`). Bez sondy.

## Trening (sceny 21421, 3 pozy, 9 par na Glu; `results/step3_20261115/touch_natural_train/`) — NIE dowód
| | wycofanie W | C stoi | wybiórczo | t_off mediana |
|---|---|---|---|---|
| N, Glu +1 | 9/9 | 9/9 | 9/9 | 0,05 s |
| N, Glu −1 | 7/9 (2 porażki: lekki walec jedzie z dłonią, 0,1–0,2 N) | 9/9 | 7/9 | 0,16 s |
| N bez DNg15 i DNge078, oba Glu | 0/9 | 9/9 | 0/9 | — |
| F1 (21 100 001), L6 (21 100 006) | 5–9/9 | 0/9 | 0/9 | — |

## Przewidywanie
Glu +1: T1_A, T1_B, T1_C tak. Glu −1: T1_A na granicy progu (trening 78 %; lekki walec), T1_B i T1_C tak.

## Test — raz
`TOUCH1_FINAL_TEST=1 touch_natural.py --seed 21871 --poses 6`. Sieci, oba Glu (24 przebiegi, najwyżej 3 naraz):
N; N `--lesion both`; F1–F5 (`--net F`, tasowania 21 872 001–005); L1–L5 (`--net L`, 21 873 001–005).

## Miary (analyze_touch.py, osobno dla każdego Glu, na parach ważnych W + C)
- wycofanie = w próbie W siła dłoni na końcu (ostatnie 50 ms) < 0,05 N; C stoi = |dq2| i |dq3| ≤ 0,01 rad w próbie C;
  wybiórczo = wycofanie i C stoi.
- **T1_A**: sieć N wycofuje dłoń w ≥ 80 % par.
- **T1_B**: N z wyciętymi DNg15 i DNge078 wycofuje w ≤ 20 % par (to ruch z tych dwóch szlaków kończy dotyk).
- **T1_C**: N w próbie C stoi w ≥ 95 % par.
- **H(F), H(L)**: wybiórcze wycofanie N lepsze niż każde z 5 tasowań (McNemar dokładny, Holm w rodzinie 5, p < 0,05).
Cel „sieć z danych sama kończy zwykły dotyk dłoni przez te dwa szlaki” = T1_A, T1_B i T1_C dla danego Glu.
Wyniki osobno dla Glu +1 i −1; nie wybieram znaku po fakcie.

## Zastrzeżenia z góry
- H(F)/H(L) są słabą kontrolą: na treningu tasowania przegrywają, bo ruszają się także bez dotyku. Główny dowód
  mechanizmu to T1_B (wycięcie).
- Wycofanie w 0,5 s mierzy tylko koniec dotyku, nie jakość ruchu; przy lekkim walcu przedmiot może jechać z dłonią.
- Szlaki wybrałem z danych sam. Symulacja MuJoCo, bez prawdziwego robota. Kolejny „odruch” nie znaczy, że mucha tak robi.
