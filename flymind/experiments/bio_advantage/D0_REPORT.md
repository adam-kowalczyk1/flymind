# D0 — report: spatial sensorimotor maps in the MaleCNS wiring (data only)

2026-11-11. Author: Claude (Fable 5.2). Stage approved by the owner in chat ("Tak, zacznij D0").
Data analysis only: **no simulation, no neuron dynamics, no robot, no training, no commit, no existing file changed.**

Evidence labels: VERIFIED (computed now from raw files; file and hash given), INFERRED, HYPOTHESIS, NOT VERIFIED.

## 0. Streszczenie dla Adama (po polsku)

**Wynik: wszystkie trzy z góry zapisane hipotezy przeszły. Kryterium zakończenia linii nie zostało spełnione.**

1. **Mapy „gdzie w polu widzenia → który neuron wyjściowy” są w danych, po obu stronach mózgu.** Cztery z pięciu par
   wybranych do testu potwierdzającego przeszły (próg: wynik lepszy niż 99 % losowych przetasowań, osobno w lewej i prawej
   półkuli). Jedna para nie przeszła (LPLC2 → DNp06, prawa strona) i tak to zapisuję.
2. **Droga LC10a → DNa02, której FlyMind już używa, też niesie informację o położeniu**, nie tylko „lewo/prawo”. Główny
   wskaźnik przeszedł słabo, pomocniczy (siła drogi do DNa02 po tej samej stronie) — wyraźnie. Dziś enkoder tę informację
   wyrzuca, bo daje wszystkim neuronom jednej strony ten sam prąd.
3. **Różne typy szczecinek dotykowych nogi trafiają do różnych grup mięśni** — dużo wyraźniej niż w 100 sieciach
   przetasowanych, na obu nogach. Typy, które po lewej stronie „ciągną” ku prostownikowi, robią to też po prawej.
4. **Niezależna kontrola:** osobny pomocnik przeliczył na ślepo własnym kodem cztery pary i cztery korelacje — zgodność do
   trzeciego miejsca po przecinku.

**Czego to NIE znaczy.** To są wzory w liczbie synaps, nie zachowanie. Nie wiemy, czy w symulacji dadzą poprawny ruch,
i nadal nic nie mówi to o przewadze nad sterownikiem klasycznym ani nad VLA. Wynik był też w dużej mierze spodziewany —
układ nerwowy nie jest połączony losowo. Wartość D0 jest praktyczna: wskazuje konkretne grupy neuronów, w których
przetasowanie *musi* coś zepsuć, czyli pierwszy uczciwy test roli połączeń.

**Jedna decyzja:** czy mam napisać rejestrację wstępną etapów S1 i S2 (sam dokument, bez uruchamiania czegokolwiek)?

## 1. Provenance

| Item | Value |
|---|---|
| Pre-registration | `flymind/experiments/bio_advantage/D0_PREREG.md`, SHA-256 `de06eacb59c0f576ce3a420f8871def7bab1c7979ac9985c80b47ef361d6de39`, recorded before the run in `PREREG_SHA256_before_run.txt`; the script checked it at start |
| Script | `flymind/experiments/bio_advantage/d0_analysis.py`, SHA-256 `9e1bb539740b2054690ded3a5b3e23eae220bb4015bfac88f26d7e6cd8c403c7` (synthetic self-check passed before the run) |
| Command | `.venv/bin/python -I -B flymind/experiments/bio_advantage/d0_analysis.py --prereg-sha256 de06eacb… --out flymind/results/bio_advantage/d0_v1` |
| Run | 2026-11-11 09:08:52 +0100, 374 s, exit code 0, single run (no earlier attempt, nothing overwritten) |
| Raw output | `flymind/results/bio_advantage/d0_v1/d0_results.json` → `45725a6df9d2316a64a247cd5dc8004cec16fecf6f7b23edebfaf56216770ca4`; `d0_stdout.txt` → `d5ea0bdf9942a0503f5867a739a6ea683af0b07c1c829a8a5737f63a030cc25c` |
| Data | the three MaleCNS files; hashes equal `results/vision_manipulation/FREEZE_v3.txt` (checked by the script) |
| Seeds | 19 100 001 (permutation tests), 19 100 090–091 (label permutation), 19 100 101–200 (edge-swap shuffles) — now consumed |
| Git | HEAD still `664b611`; new untracked entries only: `flymind/experiments/bio_advantage/`, `flymind/results/bio_advantage/`, `flymind/reports/` |

## 2. D0-a — looming pathways (primary)

y = synapses from each visual neuron onto the target descending neuron; R = multiple correlation of rank(y) with
retinotopic position (plane fit); p from 10 000 permutations (smallest possible p = 0.0001). Position by method A (direct
hex-annotated inputs) for all three types. "Null 95 %" = 95th percentile of R under permutation. All VERIFIED.

| Pair | Set | Left: n used / population, synapses, R (null 95 %), p | Right: n, synapses, R (null 95 %), p | Gradient angle L / R | Rule |
|---|---|---|---|---|---|
| LPLC2 → DNp04 | confirmatory | 92/94, 1 957, **0.81** (0.25), 0.0001 | 91/91, 1 441, **0.73** (0.26), 0.0001 | −50° / −49° | **PASS** |
| LPLC2 → DNp06 | confirmatory | 92/94, 886, 0.42 (0.25), 0.0001 | 91/91, 833, 0.29 (0.26), **0.024** | 177° / −141° | **fail** |
| LPLC1 → DNp03 | confirmatory | 56/68, 1 988, **0.70** (0.33), 0.0001 | 66/66, 1 614, **0.73** (0.30), 0.0001 | −163° / −166° | **PASS** |
| LPLC1 → DNp06 | confirmatory | 56/68, 1 604, **0.67** (0.33), 0.0001 | 66/66, 1 169, **0.80** (0.30), 0.0001 | 156° / 173° | **PASS** |
| LPLC1 → DNp11 | confirmatory | 56/68, 542, **0.75** (0.33), 0.0001 | 66/66, 499, **0.69** (0.30), 0.0001 | 135° / 125° | **PASS** |
| LC4 → DNp02 | exploratory (seen 10 Nov) | 71/71, 2 279, 0.75, 0.0001 | 55/55, 1 930, 0.85, 0.0001 | −46° / −45° | — |
| LC4 → DNp11 | exploratory | 71/71, 2 022, 0.84, 0.0001 | 55/55, 1 644, 0.86, 0.0001 | 116° / 120° | — |
| LC4 → DNp04 | exploratory | 71/71, 6 811, 0.63, 0.0001 | 55/55, 4 786, 0.64, 0.0001 | −141° / −113° | — |
| LC4 → DNp01 (giant fiber) | exploratory | 71/71, 3 782, 0.18, 0.33 | 55/55, 2 580, 0.26, 0.15 | — | no gradient |
| LPLC2 → DNp01 (giant fiber) | report only, no prediction | 92/94, 2 642, 0.73, 0.0001 | 91/91, 2 220, 0.83, 0.0001 | 12° / 23° | gradient present |

**H-a (at least one confirmatory pair passes): PASS — 4 of 5.** The kill criterion is not met.

Sensitivity (registered): with y as a fraction of each neuron's total output, and with the inclusion threshold raised to
50 synapses, the four passing pairs stay at p = 0.0001 in both hemispheres. LPLC2 → DNp06 right side: 0.0011 (fraction),
0.040 (threshold 50) — it stays a fail under the registered primary rule.

**Opposite gradients (secondary; Spearman between per-neuron counts onto two targets, permutation p):**

| Type | Target pair | Left ρ (p) | Right ρ (p) | Reading |
|---|---|---|---|---|
| LC4 | DNp02 vs DNp11 | −0.65 (0.0001) | −0.73 (0.0001) | push–pull, both sides (exploratory; same as 10 Nov) |
| LPLC2 | DNp06 vs DNp01 | −0.39 (0.0002) | −0.43 (0.0001) | push–pull, both sides (meets the registered ρ < 0, p < 0.01 condition) |
| LPLC2 | DNp04 vs DNp06 | −0.18 (0.08) | +0.02 (0.86) | none |
| LPLC1 | DNp03 vs DNp06 | +0.52 (0.0001) | +0.71 (0.0001) | same direction, not push–pull |
| LPLC1 | DNp06 vs DNp11 | +0.49 (0.0001) | +0.18 (0.14) | not replicated |
| other LC4 and LPLC pairs | | \|ρ\| ≤ 0.25, p > 0.06 | | none |

Observations:
- Gradient directions agree between hemispheres within a few degrees for every strong pair (e.g. −50°/−49°, 116°/120°).
  That is an internal replication of the map itself, not only of its existence. VERIFIED (numbers).
- LPLC2 → giant fiber shows a strong gradient; LC4 → giant fiber shows none. I registered no prediction for the former.
  A gradient in synapse count does not by itself mean the neuron encodes direction. INFERRED.
- Which retinal direction the hex axes correspond to is still NOT VERIFIED, so I cannot yet say "front/back" or "up/down".

## 3. D0-b — the LC10a → DNa02 path that FlyMind already uses

Network exactly as in `visual_path.network(J0=1.0)`: 135 + 140 LC10a, 147 intermediates, 2 DNa02; 0 neurons with unknown
sign. Position by method B (two-hop), because only 3.7 % (left) and 38.6 % (right) of LC10a have enough direct
hex-annotated input; all 275 neurons received a position. All VERIFIED; signs are a model assumption (glutamate = −1).

| Quantity per LC10a neuron | Left: R (null 95 %), p | Right: R (null 95 %), p | Angle L / R |
|---|---|---|---|
| **Primary:** signed two-hop weight onto same-side DNa02 minus opposite-side DNa02 | 0.30 (0.21), 0.0017 | 0.26 (0.21), 0.0083 | −152° / 178° |
| Signed weight onto same-side DNa02 only | 0.69 (0.21), 0.0001 | 0.72 (0.21), 0.0001 | 157° / 153° |
| Unsigned weight onto same-side DNa02 only | 0.69, 0.0001 | 0.72, 0.0001 | 157° / 153° |
| Unsigned same-side minus opposite-side | 0.76, 0.0001 | 0.72, 0.0001 | 148° / 147° |

**H-b: PASS** (p < 0.01 in both hemispheres) — but narrowly for the registered primary quantity (R ≈ 0.3). The clear
signal is in the same-side path strength (R ≈ 0.7, same direction in both hemispheres, spread across neurons about as
large as the mean: coefficient of variation 0.91 and 0.98). 87–89 % of LC10a neurons have a net positive push toward
their own side.

Reading fixed in advance: the path may encode *how far* to turn, so a retinotopic encoder is worth testing.
Caveats: positions here are two-hop averages and therefore blurrier; no "fraction of output" sensitivity was registered
for D0-b, so part of the gradient could reflect neuron size varying across the eye (HYPOTHESIS, not tested); paths longer
than two hops were ignored.

## 4. D0-c — leg bristle types → motor pools

Circuits from `leg_circuit.select("T2", side)`; unsigned direct + two-hop path weights; S = mean pairwise Jensen–Shannon
divergence between bristle types' distributions over motor pools; null = the project's degree-preserving edge-swap shuffle,
100 instances per side (10 swaps per edge; about 8 s each, so the full 100 were run). All VERIFIED.

| Side | Circuit (sensory / interneurons / motor) | Bristles used, types, pools | S data | Shuffles: mean ± sd, max | Shuffles ≥ data | Label-permutation p |
|---|---|---|---|---|---|---|
| T2 left | 677 / 772 / 58, 127 041 edges | 284, 15, 23 | **0.123** | 0.015 ± 0.002, 0.022 | 0 of 100 | 0.0001 |
| T2 right | 725 / 751 / 58, 119 561 edges | 329, 15, 25 | **0.121** | 0.016 ± 0.002, 0.025 | 0 of 100 | 0.0001 |

**H-c (data above every shuffle on both sides): PASS.** The data value is about five times the largest shuffled value.

Secondary — the two pool groups used by `fly_jaw.py` (tibia extensor = "close", tibia flexors = "open"): the per-type
index (close − open)/(close + open) ranges from −0.79 to +0.63 on the left and −0.90 to +0.58 on the right. So some
bristle types reach mainly the "closing" pool and others mainly the "opening" pool. The current code gives all of them the
same current and so averages this away.

Post hoc (not registered): over the 13 bristle types present on both sides, the left and right indices correlate at
Spearman ρ = 0.92 (p = 1e-5); the sign agrees for 11 of 13. Treat as exploratory.

Caveats: unsigned counts — "reaches" is not "excites"; the label-permutation result carries little weight because bristle
types were defined partly by connectivity (registered caveat); the data do not say where on the leg each type sits, so
any assignment of types to places on a gripper would be an engineering choice.

## 5. Independent recheck

A separate model instance, given only the definitions and the raw file paths (forbidden to open this folder), recomputed
with its own code:

| Case | This script | Independent |
|---|---|---|
| LPLC2 L → DNp04: n, synapses, R, angle | 92/94, 1 957, 0.8102, −50.0° | 92/94, 1 957, 0.810, −50.014° |
| LPLC1 R → DNp03 | 66/66, 1 614, 0.7334, −166.0° | 66/66, 1 614, 0.733, −165.969° |
| LPLC1 L → DNp11 | 56/68, 542, 0.7507, 135.4° | 56/68, 542, 0.751, 135.395° |
| LPLC2 R → DNp06 (the failing one) | 91/91, 833, 0.2884, p 0.024 | 91/91, 833, 0.288, p 0.029 |
| LC4 DNp02 vs DNp11, ρ L / R | −0.6534 / −0.7304 | −0.653 / −0.730 |
| LPLC2 DNp06 vs DNp01, ρ L / R | −0.3901 / −0.4328 | −0.390 / −0.433 |
| Calibration of the test on pure noise | 5 % level checked in self-test | 0.053 false-positive rate (16/300) |

Status: D0-a VERIFIED twice. **D0-b and D0-c were not independently recomputed** (they reuse project code for network
construction and shuffling) — PARTIALLY VERIFIED in that sense.

## 6. Deviations from the pre-registration

- None in definitions, thresholds, seeds or verdict rules.
- Clarification: in the "threshold 50" sensitivity run the 80 % coverage rule was also evaluated at 50 synapses.
- One addition, labelled post hoc in §4 (left–right agreement of the close/open index).

## 7. What this does and does not establish

**Does (VERIFIED):** in this animal's wiring, per-neuron synapse counts from three looming-related visual types onto
descending neurons vary systematically with retinotopic position, with the same direction in both hemispheres; the path
FlyMind uses for steering has position-dependent strength; bristle types reach different motor pools far more
specifically than degree-matched random wiring.

**Does not:** show that any of this produces correct behaviour in a simulation; show an advantage over a classical
controller or a VLA; identify retinal axes or bristle locations; say anything about synaptic strength, sign or dynamics;
generalise beyond one animal. A PASS was largely expected a priori — nervous systems are not randomly wired.

**Why it still matters for the project:** these are concrete populations where a weight-preserving shuffle must destroy
the pattern. The grasp and steering tasks so far could not show a role for wiring because the interface was one number in,
one number out (`bio_advantage_research_20261110.md` §3). D0 says there is something to lose if one keeps doing that.

## 8. Proposed next step (not started; needs approval)

Write — only write — the pre-registration for:
- **S1** (cheap): is the present grasp network equivalent to a classical reflex with the same transfer curve and delay?
- **S2** (main): a spatial-map reflex in simulation, data wiring vs ≥ 20 shuffles vs a classical map vs a slow-policy
  surrogate. My recommendation for the map: LC4 → DNp02 / DNp11, because it is the only pair with both a push–pull
  structure in the data and a published behavioural meaning (Dombrovski et al., Nature 2023). Honest weakness: for LC4 the
  data evidence is exploratory; the confirmatory evidence is for LPLC1 and LPLC2, whose targets have no push–pull pair with
  a known meaning (except LPLC2 → DNp06 vs giant fiber).
- **S2b** (optional, small): the existing V5 steering loop with a position-aware encoder in a new file (the protected
  `encoder.py` untouched), to see whether the wiring then sets the steering gain by itself.

Seeds, sample sizes, margins and kill criteria would be fixed in that document before anything runs.
