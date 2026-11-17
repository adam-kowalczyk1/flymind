# LOOP_TARGET — bramka G2 w wersji ALIF (zapisane PRZED uruchomieniem na danych, 16 XI 2026 ok. 19:15)

## Pytanie
Czy neurony T4/T5 z rdzenia ruchu MaleCNS, w impulsowym modelu projektu (`flymind/alif.py` + `alif_sparse.py`,
`ALIFParams()` bez zmian, **jednakowe dla wszystkich typów**), rozróżniają kierunek ruchu?

## Dlaczego jeszcze raz (jawnie)
Dziś inna sesja wykonała G2 dwa razy na tych samych danych: r1 (model **stopniowany** M-G, jednakowe τ) — FAILED;
r2 (stopniowany, τ z literatury) — FAILED; trwa wariant flyvis. Żaden nie używał **modelu ALIF**, którym FlyMind steruje
ramieniem i który plan z 12 XI (§3 O3) wskazuje dla rdzenia. Ten przebieg odpowiada dosłownie na pytanie z planu.
To NIE jest strojenie: parametry neuronów są domyślne projektu; nie zmieniam ich po wyniku.
Oczekiwanie z góry (INFERRED, z r1 i literatury): raczej FAILED — jednakowa dynamika nie daje różnych opóźnień wejść T4/T5.

## Co jest takie samo jak r1 (pożyczone z `experiments/v1_camera_input/`, pliki niezmieniane)
Wycinek prawego oka 5120 neuronów (`optic_slice.build`), bodźce S0/S1 (krawędzie ON/OFF, kontrast 50 %, 6 kierunków,
60/120/240 °/s), fotoreceptor (log − adaptacja τ 1 s → 2× filtr 12 ms), znaki (`eye_gate.SIGN`, Glu −1), tasowanie C1
(`eye_gate.shuffle_typed`), 10 jednostek danych (połowy A/B), 40 tasowań po 4 jednostki, **analiza i progi bez zmian**
(`eye_gate_analysis.py`).

## Co jest inne (ustalone teraz, przed danymi) [MODEL]
- Neuron: SparseALIF, `ALIFParams()` (v_rest −52, próg −45, τ_m 20, τ_syn 5, ref 2,2, opóźnienie 1,8 ms, τ_a 300, b_a 0,5, dt 1 ms).
- Wagi: W = znak · J0 · liczba synaps, J0 = 0,2 mV/synapsę (jak `FlyJawCfg.J0`). Reguła stabilności `pick_j0`: połowić J0,
  aż w spoczynku średnia < 50 Hz i < 5 % neuronów ≥ 0,9 r_max (odpowiednik `pick_g` z r1).
- Każdy neuron: stały prąd 10 mV + szum biały σ = 3 mV (jednakowo; odpowiednik V_rest > 0 i szumu z r1).
- Wejście tylko do L1/L2/L3 wszystkich kolumn: −20 mV × sygnał fotoreceptora. **Żaden inny neuron nie dostaje prądu z bodźca.**
- Częstość: impulsy wygładzone τ 20 ms, uśrednione po jednostkach połowy, potem szczyt − spoczynek (S1) / średnia zmiana (S0).
- 1000 ms stałego obrazu przed bodźcem (adaptacja dochodzi do równowagi).
- Bez wariantu Glu +1.

## Kryteria (identyczne z r1, `PREREG_GATE.md`)
- **G1** polaryzacja ON/OFF: ≥ 6/7 typów z oczekiwanym znakiem.
- **G2** kierunek: ≥ 3/4 podtypów T4 z medianą DSI ≥ **0,20** i > 95. percentyla 40 tasowań. T5 opisowo.
- **G3** oś Mi9→Mi4: ≥ 3/4 podtypów T4 z medianą różnicy ≤ 30°.
- **BRAMKA** = G1 i G2 i G3.
- **Nie przejdzie → STOP**: nie zmieniam parametrów, nie powtarzam; pytanie do Adama.

## Ziarna (`SEED_REGISTRY.md`)
Dane 23 502 001–010; tasowania 23 503 001–040; dymne 23 501 xxx. Każde użyte raz.

## Wyniki
`flymind/results/fly_eye_20261116/` — `data_glu-1.npz`, `shuf_01–40.npz`, `gate_result.json`, `PRE_RUN_HASHES.txt`, raport.
