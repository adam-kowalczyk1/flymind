# Krok 2 — wzmocnienie k i znaki pul (ZAMROŻONE PRZED przebiegami (b)–(e))

Data: 2026-11-13. Spisane przed jakimkolwiek przebiegiem sieci sterującej stawem ramienia. Hash tego pliku jest zapisany
w `results/step2_whole_arm_20261113/step2_log_2026-11-13.md`. Każda późniejsza zmiana = nowy plik `…_r1.md` z uzasadnieniem,
a przebiegi z wersją starszą i nowszą raportuje się osobno. Strojenie po wynikach jest zabronione.

## 1. Postać komendy (decyzja Adama: przyrost celu pozycyjnego)

    r_X ← r_X + (dt/τ_r)·(częstość chwilowa puli X − r_X),   τ_r = 50 ms   (średnia częstość neuronów puli [Hz], jak fly_arm.py)
    cel_j ← cel_j + s_j · k · dt · (r_POS_j − r_NEG_j),        dt = 0,01 s (takt sterowania)

Potem bez zmian: nowy klasyczny strażnik stołu (bezpiecznik) → `safety.SafetyLayer` → `SO101Sim.act`.

## 2. Wzmocnienie k — metoda (bez użycia sieci ani zadania)

    k = v_ref / Δr_ref = 0,5 rad/s / 100 Hz = 0,005 rad/s na Hz        — ten sam k dla stawów 1–4

- **v_ref = 0,5 rad/s** = 1/3 limitu prędkości warstwy bezpieczeństwa (`safety.Limits.v_max = 1,5 rad/s`) — wybór projektu.
- **Δr_ref = 100 Hz** = ustalona częstość pojedynczego neuronu ALIF przy 40 mV (maksymalny prąd dotyku, `fly_jaw.FlyJawCfg.max_mV`),
  b_a 0,5, dt 1 ms — zmierzona w `neuron_report_v2.json` (tabela A1 logu: 100 Hz). Liczba pochodzi z modelu neuronu, nie z sieci
  ani z wyników zadania.
- Maksymalnie |Δr| ≤ 250 Hz (sufit przy dt 1 ms) → |prędkość| ≤ 1,25 rad/s < v_max. Przy dt 0,1 ms sufit 435 Hz → do 2,2 rad/s
  (warstwa bezpieczeństwa by przycinała) — jeśli Adam wybierze dt 0,1 ms, k NIE zmienia się; przycięcia są raportowane.
- Ten sam k dla sieci z danych, wszystkich tasowań i obu znaków Glu. Szczęka bez zmian: moment, k_jaw = 0,005 N·m/Hz (FJ1).

## 3. Znaki s_j — z kinematyki robota (VERIFIED statycznie, `so101.SO101Sim.fk`, bez sieci) i z roli pul

Kinematyka (+0,05 rad, pozy Q_POSE z loop.py i Q_SURVEY z vision_manipulation.py): +q stawów 1, 2, 3 opuszcza punkt chwytaka
(Δz −11,3 / −12,1 / −6,5 mm w Q_POSE); +q stawu 2 zmniejsza odległość bark–nadgarstek (105,3 → 99,7 mm) = zgięcie; +q stawu 3
zmniejsza odległość łokieć–chwytak w Q_SURVEY (201,9 → 196,5 mm) = zgięcie; staw 4 tylko obraca (Δpoz ≤ 0,4 mm).

| Staw | POS | NEG | s_j | Znaczenie |
|---|---|---|---|---|
| 1 shoulder_lift | T1 L wymach: Sternal anterior rotator MN (2) | T1 L podpór: Pleural remotor/abductor MN (2) + Sternal posterior rotator MN (4) | **−1** | wymach → chwytak w górę (−q), podpór → w dół (+q) |
| 2 elbow_flex | T1 L: Ti flexor MN (5) + Acc. ti flexor MN (10) | T1 L: Ti extensor MN (2) | **+1** | zgięcie goleni → zgięcie łokcia (+q) |
| 3 wrist_flex | T1 L: Ta levator MN (2) | T1 L: Ta depressor MN (5) | **−1** | „levator” → koniec chwytaka w górę (−q w Q_POSE) |
| 4 wrist_roll | T1 L: Tr flexor MN (8) | T1 L: Tr extensor (2) + Sternotrochanter (2) + Tergotr. (4) MN | **+1** | **znak arbitralny** (obrót nie ma „góry”); ustalony tu, nie zmieniany |
| 0 shoulder_pan | DNa02 L | DNa02 R | bez zmian (V5) | — |
| 5 gripper | T2 L Ti extensor (2) | T2 L Ti flexor (5) + Acc. ti flexor (6) | bez zmian (FJ1) | moment, + = zamykanie |

Wiersze 1 i 4 zależą od akceptacji zmienionej tabeli C (sekcja G logu). Jeśli Adam wybierze inny wariant, przed przebiegiem
powstaje `CALIBRATION_k_SIGNS_r1.md`.

## 4. Glu i pozostałe parametry (stałe)

Glu −1 i Glu +1 — dwa osobne warianty, oba raportowane. J0 0,2 mV/synapsę (jak obwód nogi i wzrok). Szum 0 w obwodach nóg,
σ 2 mV w drodze wzrokowej (jak VisJaw). Kodowanie dotyku 40 mV/N, max 40 mV (FJ1). Krok ALIF: dt 1 ms, chyba że Adam zdecyduje
inaczej po pomiarze kosztu (tick_cost_v1.json).
