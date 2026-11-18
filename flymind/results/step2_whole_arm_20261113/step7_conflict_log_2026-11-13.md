# Krok 7 — test konfliktu bodźców (wzrok + dotyk) — osobny log

Plan spisany przed testem: `experiments/step2_whole_arm/CONFLICT_TARGET_r1.md` (sha256 `e1746e72…dfd1`). Program:
`conflict_test.py` (sha `deb436ef…39e8` w każdym pliku wyniku). Moduły wspólne bez zmian: `vision_manipulation.py` `5c1da2f2…`,
`sensory_manipulation.py` `260c2c25…`, `object_handling.py` `0bf03d36…` (z pól `code_sha256` plików wynikowych). Piloty bodźca:
`step2_log_2026-11-13_part5.md` §5.5 (pilot 1 FAILED — zielone przedmioty nasycały enkoder; pilot 2 przyjęty, kolory materiałów).

## 7.1 Co i po co
Pytanie: czy bodziec wzrokowy pokazany W TRAKCIE trzymania przedmiotu zmienia chwyt, gdy wzrok NIE jest ręcznie wyłączany?
Sieć wspólna: droga wzrokowa LC10a → DNa02 ∪ obwód nogi T2 L (MaleCNS, 1931 neuronów, W sha `b728a3f9…`). Szczęka = moment z MN
goleni tej sieci. Bodziec: zielona kula w lewej części kadru kamery chwytaka od podniesienia do odkładania; sham = ta sama kula,
szara. Pary = ta sama scena i to samo ziarno szumu w „on” i „sham”.

## 7.2 Uruchomienie
`launch_conflict.sh N 3` (scratchpad), `STEP2_FINAL_TEST=1`, `--seed 20971 --poses 3` → 4 serie × 135 prób
(`conflict_7/test/conf_N_g{−1,1}_{on,sham}.json`), ok. 2 h 20 min zegarowo każda (obciążenie maszyny 450–760).
Tasowania S1–S2 uruchomione i WSTRZYMANE (SIGSTOP) na prośbę drugiej sesji, S3–S5 jeszcze nie — patrz 7.4.

## 7.3 Wynik sieci z danych (N), test raz — analiza `conflict_7/test_analysis_N_only.json` (sha `6a4cd55f…08e2`)
Okno = pierwsze 100 taktów (1 s) od włączenia bodźca; 135 par w obu Glu.

| Miara (on − sham) | Glu −1 | Glu +1 |
|---|---|---|
| **Kontrola manipulacji: DNa02 L** [Hz] | **+137,7** [127,5; 147,5], Wilcoxon p < 10⁻⁶ | **+133,4** [124,3; 142,6], p < 10⁻⁶ |
| DNa02 R [Hz] | +62,0 [54,2; 69,8] | +72,7 [65,1; 80,1] |
| Wejście wzrokowe g L / g R | +0,42 / +0,33 | +0,41 / +0,36 |
| **Główna: moment szczęki** [N·m] (sham średnio 0,50 / 0,73) | **−0,0044** [−0,0121; +0,0013], p = 0,63 | **−0,0065** [−0,0196; +0,0032], p = 0,00096 |
| mediana różnicy; par − / + | 0,0000; 60 / 56 | +0,0013; 48 / 76 |
| `placed` on / sham (McNemar dwustronny) | 87 / 91 (p = 0,125) | 93 / 94 (p = 1,0) |
| utrata chwytu `snn_released` on / sham | 51 / 49 (p = 0,5) | 50 / 48 (p = 0,5) |

Rozstrzygnięcie wg planu (oba warunki: Wilcoxon p < 0,05 **i** przedział bootstrapu bez 0):
- Kontrola manipulacji: **spełniona** w obu Glu — bodziec dociera do sieci (DNa02 L rośnie ~135 Hz) — VERIFIED.
- „Wzrok zmienia chwyt”: **NIE** w obu Glu. Glu −1: brak jakiegokolwiek efektu. Glu +1: test rang istotny (większość par
  nieznacznie DODATNIA, mediana +0,0013 N·m ≈ +0,2 %), ale średnia UJEMNA przez kilka dużych spadków (do −0,59 N·m) i przedział
  średniej zawiera 0 → kierunek niespójny; zgodnie z regułą spisaną z góry wynik = brak efektu. Rozmiar w każdym razie < 1 %
  momentu chwytu. VERIFIED (liczby z plików), interpretacja INFERRED.
- „Swoistość dla połączeń z danych” — nie dotyczy przy braku efektu w N; tasowania nadal będą policzone jako kontrola (7.4).

Wniosek prostym językiem: w tej sieci sygnał wzrokowy dochodzi do neuronu zstępującego DNa02 (bardzo silnie), ale prawie nie
zmienia siły szczęki sterowanej obwodem nogi. Sieć wspólna przy tym bodźcu NIE przenosi konfliktu na chwyt — trzymanie jest
odporne na rozpraszający bodziec bez ręcznego wyłączania wzroku. To wynik zerowy, nie dowód „mądrego” bramkowania.

## 7.4 Tasowania S1–S5 — uruchomienie
S1–S2 (8 serii) wstrzymane SIGSTOP 23:4x–04:24 na prośbę drugiej sesji (tylko czas zegarowy), wznowione po końcu testu (b);
S3–S5 (12 serii) start 04:25, 1 wątek. Ziarna 20 980 001–005; `--poses 1` (45 scen, poza 0), jak w planie. Koniec 05:12.

## 7.5 Wynik z tasowaniami — `conflict_7/test_analysis_full.json` (sha `ce258d7e…`)
Porównanie na wspólnych 45 scenach (poza 0). Moment szczęki on − sham [N·m], średnia [bootstrap 95 %], Wilcoxon p:

| | Glu −1 | Glu +1 |
|---|---|---|
| N (45 scen) | −0,0003 [−0,0046; +0,0036], p = 0,96 | −0,0012 [−0,0089; +0,0044], p = 0,12 |
| S1 | −0,0037 [−0,0084; +0,0001], p = 0,14 | +0,0013 [−0,0016; +0,0037], p = 0,052 |
| S2 | −0,0026, p = 0,91 | +0,0016, p = 0,012 |
| S3 | −0,0025, p = 0,56 | +0,0024, p = 0,006 |
| S4 | −0,0017, p = 0,47 | +0,0012, p = 0,029 |
| S5 | −0,0036, p = 0,21 | +0,0016, p = 0,050 |
| DNa02 L (on − sham), N / S | +134 / +133–134 Hz | +132 / +131–132 Hz |
| placed on/sham N; S | 32/34; 32–33/34 | 34/34; 34/34 |

- Kontrola manipulacji: spełniona w N i w każdym S. „Wzrok zmienia chwyt”: NIE (N). „Swoistość dla danych”: NIE
  (|N| 0,0003 < max |S| 0,0037 przy Glu −1; 0,0012 < 0,0024 przy Glu +1). VERIFIED.
- Uwaga: przy Glu +1 w tasowaniach S2–S5 test rang daje p < 0,05 (małe, dodatnie przesunięcie ~+0,2 % momentu), ale przedziały
  średniej zawierają 0 — wg reguły brak efektu. Nie ma też poprawki na wiele porównań. [INFERRED] Przetasowanie krawędzi
  wzrok → noga nie zmienia obrazu: wzrok w tej sieci praktycznie nie dociera do momentu szczęki niezależnie od układu połączeń.

## 7.6 Wniosek kroku 7 (prostym językiem)
Jedna wspólna sieć (wzrok + noga muchy) dostaje silny sygnał wzrokowy (DNa02 +130 Hz), ale trzymanie przedmiotu się nie
zmienia — ani w sieci z danych, ani w 5 wersjach z przetasowanymi połączeniami wzrok → noga. Konflikt bodźców nie przechodzi
na chwyt. To wynik zerowy; nie pokazuje „bramkowania” ani roli połączeń z danych. Sieć wspólna jest bezpieczna wobec
rozpraszającego bodźca, ale z tego samego powodu wzrok nie może w niej sterować chwytem.
