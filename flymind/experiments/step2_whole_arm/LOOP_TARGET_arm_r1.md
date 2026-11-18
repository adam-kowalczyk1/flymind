# Cel dla kroku 5 — całe ramię z sieci naraz — wersja r1 (spisana 2026-11-13 PRZED jakimkolwiek przebiegiem kroku 5; hash w logu)

Zasady i statystyka jak `LOOP_TARGET_b_r2.md`; kalibracja `CALIBRATION_k_SIGNS.md` (k, znaki, pule) bez zmian.
Kod: `joint_net.py --joints 1,2,3 --roll` (jedna sieć T1 L + T2 L steruje czterema stawami). Analiza:
`analyze_joint.py DIR GLU --outcome placed` (wynik główny) oraz `--outcome lift` (pomocniczy).

## 1. Zadanie
Benchmark etapu czucia jak w (b)–(e). Od zaciśnięcia szczęki:
- faza podniesienia: stawy 1, 2, 3 z sieci jednocześnie (każdy ze swoich pul i znaku), staw 0 trzyma pozę chwytu;
  koniec jak w (b): cs_fixed na wysokości transportu albo 3 s → „no_lift”;
- staw 4 z sieci od zaciśnięcia do zwolnienia (jak (e));
- transport i odkładanie: stawy 0–3 rusztowanie (IK z bieżącej pozy), szczęka LegJaw T2 L (jak wszędzie poza K0).
**Wynik główny: `placed`/135**; pomocniczy `lift`/135, siła ramię↔blat, przejęcia bezpiecznika, udział komend sieci.

## 2. Wersja sieci (reguła ustalona z góry)
„Najlepsza wersja” każdego stawu wg jego pętli. Ponieważ to JEDNA sieć, wejścia = suma wejść receptorowych z najlepszych wersji
b–e, reguła interneuronów `fl` (jeśli którakolwiek najlepsza wersja jej używa). Staw z wynikiem negatywnym wchodzi w swojej
najlepszej wersji, oznaczony w raporcie. Jeśli najlepsze wersje wymagają sprzecznych ustawień (np. inny plik kalibracji), wygrywa
wersja stawu z wyższym wynikiem treningowym względem K — opisane w logu przed uruchomieniem.

## 3. Ramiona
N (sieć), S1–S5 (tasowania `visual_path.shuffle(equal_weight=True)`), **R = wszystkie odruchy naraz: stawy 1–3 stale „w górę”
0,5 rad/s każdy w fazie podniesienia, staw 4 trzymany** (zdefiniowane TERAZ), K (rusztowanie klasyczne), K0.

## 4. Iteracja 0 (bez strojenia): 3 przedmioty `--seed 20951`: odciski trajektorii do podniesienia identyczne w N/S/R/K, siła K ≈ 0 N,
czas serii. Brak pętli strojenia (krok 5 składa gotowe wersje). Następnie test raz.

## 5. Cel (test, raz, każdy Glu osobno) — jak r2 §4 na `placed`: C1 niegorszość wobec K (−10 pp, bootstrap), C2 McNemar N > R,
C3 N > S1–S5 (Holm), C4 ≤ 5 N i bezpiecznik ≤ 10 % taktów aktywnych.

## 6. Ziarna (SEED_REGISTRY.md): iteracja 0 `--seed 20951`; test `--seed 20901` × 135 (3 pozy), tasowania 20 910 001–005.
