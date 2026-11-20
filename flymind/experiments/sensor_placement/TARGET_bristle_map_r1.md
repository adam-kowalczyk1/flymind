# Cel: mapa „koniec nogi / nasada” dla 322 szczecinek T2 L (r1, 20 XI 2026) — spisany PRZED pobraniem i liczeniem

Reguła z literatury: Elabbady i in. 2026, Curr Biol, doi:10.1016/j.cub.2026.03.045. Aksony szczecinek z KOŃCA nogi
kończą się w środku ośrodka nogi w zwoju brzusznym, a z nasady przy brzegu (pierścienie). Miara w pracy: średnia
odległość synaps aksonu od środka ośrodka (FANC, samica, noga przednia).

## Jak liczę (WYPROWADZONE tą regułą, nie opublikowana mapa)
- Dane: szkielety SWC MaleCNS v1.0 (publiczne, CC-BY, gs://flyem-male-cns/v1.0/segmentation/skeletons-malecns/skeletons-swc/)
  dla 322 neuronów z `step3_wiring/touch_map.json` (femur + tibia_tarsus). Synaps nie mam (plik 13 GB), więc zamiast synaps
  biorę **zakończenia gałęzi** (liście szkieletu) — przybliżenie.
- Na neuron: c_i = średnia liści; środek C = mediana wszystkich c_i (środek populacji ≈ środek ośrodka); r_i = |c_i − C|.
  Małe r = koniec nogi.
- **Sprawdzian wiarygodności (próg zapisany teraz):** jeżeli typy SNta mają spójne położenie, to typ wyjaśnia dużą część
  zmienności r: η² (ANOVA r ~ typ, typy z ≥ 3 neuronami) **≥ 0,5** → mapa „użyteczna”; < 0,5 → mapa NIE jest używana,
  podział zostaje hipotezą. Dodatkowo test permutacyjny η² (1000 tasowań, ziarno 2011203), p < 0,01.
- Porównanie z obecną hipotezą `touch_map.json`: czy grupy „femur” i „tibia_tarsus” różnią się r (Mann-Whitney) i w którą stronę.
- Przypisanie do czujników (tylko gdy mapa użyteczna): ranga u_i ∈ [0, 1] (0 = najbliżej środka = koniec nogi).
  Położenie czujnika wzdłuż szczęki od czubka do dłoni (68 mm): czubek ~8 mm → p = 0,12; A0 ~31 mm → p = 0,46.
  Czujnik dostaje neurony z |u_i − p| ≤ 0,15. Bez dopasowywania pod wynik zachowania.
