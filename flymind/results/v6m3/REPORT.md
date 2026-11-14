# V6m3 — Intermediate-layer count-vs-timing dissection: report (2026-10-30)

**Status: exploratory, pre-registered. Verdict: PASS_WITH_LIMITATIONS** (RT-H Part A, RT-I Part B — both PASS_WITH_LIMITATIONS; all 20
required corrections applied, §6). MODEL-level computational ablations (ALIF; DATA downstream wiring; model populations named after
connectome cell types). No biological manipulation; no claim about Drosophila.

## 1. Design and execution
Protocol `program_v5v41/V6m3_PROTOCOL.md` (r1 sha fbeeb64a… hashed 17:29:21; analysis script 4f1d675a… hashed 17:30:19 after a dry run on
smoke data whose output was discarded unseen; r2 sha f00db4bf… 17:33:46). r2: the r1 run crashed in one REPLICATION job (an added
count-swap spike had no ISI ≥ 4 ms position); **18/22** jobs had completed (corrected from "17"; RT-H) and were kept unopened; r2 places
such spikes in any free 1-ms slot and counts them. Re-running two kept r1 jobs under r2 was bit-identical (RT-H). Fallback spikes: 5
(REP B1 8 421 017: 1, 018: 4). Smoke run used rep 1 of the MAIN seeds (DATA, B1 8 421 001); values not opened.
Seeding (deviations from protocol §1, disclosed): the count-swap SeedSequence([8 446 000, set, level, side, rep, source]) has no
neuron-block word and one generator serves DB then BD; the LCIRC stream SeedSequence([8 446 000, 9, rep]) depends on rep only (shared
across levels, sides, sources and MAIN/REP → LCIRC "replication" differs only in noise).
Levels 8/9 mV, unilateral L/R, 8 reps; MAIN = DATA + B1 8 421 001–010 (noise 8 445 001–008); REPLICATION = DATA + B1 8 421 011–020 (noise
8 445 201–208). Calibration (DATA source, seeds 8 445 101–104, before the jobs): REF intermediate ipsi rate 16.2 Hz → intermediate gain
0.725 (MT0G), bias −7.0 mV (MT0B); DNa02 gain 0.525 (T0G); all inside their grids; matching holds per level and side within a few %, but
only for the ipsilateral mean (composition not matched — §2).
Part A: LC10a clamped to DATA or B1 trains, intermediates and DNa02 free; intermediate dynamics REF / MT0 (t_ref 0; the hard reset is kept)
/ MT0G / MT0B; control LCIRC. Part B: LC10a + intermediates clamped (DNa02 only free); 2×2 count-swap of real intermediate trains: DD, BB
(identity), DB (DATA timing, B1 per-neuron counts; added spikes 2.8 % MAIN / 2.4 % REP of the count source's 300–1000 ms spikes), BD (B1
timing, DATA counts; 12.2 % added at random times — ≈ 14 % at 8 mV, 10 % at 9 mV). Not surrogate-free: BD contains ~12 % random-time
spikes. **Design defect (pre-registered construction):** counts were matched over 300–1000 ms but DNa02 is scored over 500–1000 ms; in the
scored window DB carries 2.0 % less and BD 1.7 % more DNa02-weighted drive than intended (≈ 18 % of the drive gap each; both inflate |C|).
Validation in every run: REF clamp == free run (DATA only; close to a tautology — engine/RNG alignment), DD/BB == REF DNa02 raster, swapped
counts exact, deleted spikes ⊂ timing source; RT-H's independent engine matched `run3` in 128/128 cells; Stage 1 28/28; 22 jobs, 0 errors.

## 2. Results (MAIN | REPLICATION; CI = wider of nested bootstrap and jackknife-t — the jackknife-t was binding throughout; the nested
bootstrap is 2–3× too narrow here because DD is identical across instances and reps are resampled per instance, RT-I)
**Part A (QA).** D_rel = B1/DATA − 1 of DNa02-weighted excitatory intermediate drive (500–1000 ms); D_inh = inhibitory drive (DATA / B1):
| Intermediate dynamics | D_rel MAIN | D_rel REP | count rel. | D_inh DATA / B1 (MAIN) | pairwise r DATA / B1 | DNa02 gap [Hz] |
|---|---|---|---|---|---|---|
| REF | **−10.7 % (−12.9; −8.4)** | −10.8 % | −8.1 % | −383 / −418 | 0.14 / 0.38 | −23.1 (−26.8; −19.4) |
| MT0 (t_ref 0, unmatched; rate +50 %) | +0.5 % (−2.1; +3.1) | +1.1 % | −0.8 % | −291 / −536 | 0.21 / 0.56 | −33.0 |
| MT0G (gain-matched) | +2.2 % (−0.3; +4.8) | +2.7 % | +2.6 % | −39 / −95 | 0.19 / 0.53 | −24.1 |
| MT0B (bias-matched) | +5.4 % (+2.5; +8.4) | +5.9 % | +5.0 % | −19 / −24 | 0.20 / 0.53 | −22.0 |
| LCIRC (REF) | −3.9 % (−5.9; −1.9) | −4.4 % | −3.5 % | −135 / −141 | 0.05 / 0.05 | −4.5 |
F_A = 1 − D_rel(c)/D_rel(REF): MT0G 1.21 (0.94; 1.48), MT0B 1.51 (1.15; 1.87) | REP 1.26, 1.55. **Pre-registered decision: H-IR SUPPORTED in
MAIN and REPLICATION.** Rate matching fixes only the ipsilateral mean: the DNa02-inhibiting intermediates are almost silenced under
MT0G/MT0B (D_inh −383 → −39 / −19) and the mean excitatory-intermediate rate falls ~15–20 %; RT-H's control "block kept + the same bias"
(same silencing) leaves the full deficit, so this does not drive F_A. Per side the MT0 D_rel differs in sign (e.g. MAIN 8 mV L −0.7 %,
R −3.3 %; 9 mV R +4.8 %) — "≈ 0" holds on aggregate.
RT-H (own seeds 8 499 0xx, 3 new B1, post hoc): block-length dose–response D_rel −12.0 / −10.9 / −9.4 / −6.7 / 0.0 % for 4 / 3 (REF) / 2 /
1 / 0 blocked steps; t_ref 1 keeps 61 % of the deficit (F_A 0.39); block kept with gain 0.725, bias −7, bias +3 or b_a 0 → F_A ≈ 0
(specific to the block); τ_syn 10 → F_A 0.23; intermediate gain that scales only synaptic input (noise unscaled) gives the same
calibration and F_A 1.10 vs 1.09 (noise scaling not a confound); **MT0 + LCIRC −6.1 %, MT0B + LCIRC −7.3 %** (the non-synchrony residual
survives t_ref 0).
**Part B (QB)** — DNa02 ipsi (Hz) DD / DB / BD / BB:
| DNa02 dynamics | DD | DB | BD | BB | count effect C | timing effect Tm | C share | interaction |
|---|---|---|---|---|---|---|---|---|
| REF (MAIN) | 104.5 | 95.8 | 97.1 | 81.4 | −12.2 (−13.8; −10.7) | −10.9 (−13.9; −8.0) | 0.53 (0.46; 0.59) | −7.1 (−8.9; −5.4) |
| REF (REP) | 104.2 | 95.1 | 96.5 | 80.3 | −12.7 (−14.6; −10.8) | −11.3 (−14.7; −7.8) | 0.53 (0.45; 0.61) | −7.0 |
| T0 (MAIN) | 194.4 | 167.9 | 191.2 | 176.7 | −20.5 (−23.3; −17.7) | +2.8 (−1.6; +7.1) | — | +11.9 (+10.5; +13.4) |
| T0G gain-matched (MAIN) | 105.4 | 90.3 | 101.7 | 94.2 | −11.3 (−12.8; −9.7) | +0.1 (−2.5; +2.6) | — | +7.5 (+6.2; +8.9) |
Log scale (MAIN REF): C −0.132, Tm −0.118, share 0.53 (0.47; 0.59). Per level × side the share is 0.47–0.56 (MAIN) / 0.47–0.60 (REP), gap −18 to
−31 Hz; 9 mV R lowest in both sets. Bonferroni ×40: C, Tm and the REF interaction survive; the share widens to (0.39; 0.67) MAIN, (0.34;
0.72) REP. Path decomposition (a different quantity from construction bias): counts-first DB − DD = −8.7 then BB − DB = −14.5 (count share
0.37); timing-first BD − DD = −7.4 then BB − BD = −15.8 (0.68).
**Construction sensitivity (RT-I, own seeds 8 499 1xx, post hoc):** count share 0.53 (pre-registered construction) → 0.46 (0.39; 0.54) with
counts matched separately in each window; 0.44 (0.38; 0.49) when added spikes follow the timing source's population activity; 0.36 (0.30;
0.42) when both trains are thinned to the per-neuron minimum count. About half of the REF interaction (−7.1) is due to random-time addition
(−3.7 Hz with activity-following addition). T0G: the pooled Tm ≈ 0 averages opposite-sign paths (BD − DD −3.7, BB − DB +3.8, both CIs ≠ 0) and
opposite-sign levels (8 mV −2.9 (−4.8; −1.1), 9 mV +3.0); across constructions T0G Tm ranges −1.7…+5.2 Hz; under T0, B1's timing becomes
beneficial (+3…+10 Hz).

## 3. Interpretation (MODEL level, corrected)
- **QA:** the pre-registered rule is met in both sets, but the mechanism is more specific than "removing the block eliminates the deficit".
  The deficit has a synchrony-dependent part (≈ 60 %: LCIRC F_A 0.63 MAIN / 0.59 REP; RT-H 0.57 (0.43; 0.71)) and a non-synchrony residual
  (LCIRC −3.9…−4.7 %). Removing the intermediate refractory block abolishes the synchrony-dependent part and reverses its sign (synchrony
  becomes a gain), while the residual persists (MT0 + LCIRC −6.1 %); the net ≈ 0 under t_ref 0 is a cancellation. F_A is therefore NOT "the
  fraction caused by refractoriness" (it exceeds 1 because t_ref 0 adds a synchrony bonus). Supported: the intermediates' refractory
  block converts LC10a synchrony into fewer intermediate spikes (block-specific; graded with block length; one blocked step still keeps
  61 % of the deficit — the largest single change is from 1 to 0 blocked steps). Not shown: that "the" 3-step block is needed; that the
  DNa02 gap in Part A t_ref 0 conditions is carried by timing (B1 also recruits +55–84 % more inhibitory drive there — untested).
- **QB:** with the DNa02 block intact both routes are present in every construction (C and Tm CIs exclude 0, survive Bonferroni). Their
  split depends on construction: 0.53 with the pre-registered (biased) swap — "neither dominant" holds only for that estimator — and
  0.36–0.46 with bias-reduced swaps, two of which put timing "dominant" by the pre-registered rule. Removing the DNa02 block reduces the
  timing effect from ≈ −11 Hz to within about ±3 Hz (gain-matched; sign level- and construction-dependent) and makes B1 timing beneficial
  when unmatched (+3…+10 Hz), consistent with V6m2.
- **Model chain:** LC×LC wiring → LC10a synchrony → (a) intermediate refractory block truncates synchronous volleys → fewer intermediate
  spikes (count route; synchrony-dependent ≈ 60 % of the drive deficit) and (b) more synchronous intermediate output → DNa02 refractory
  block penalises synchronous input (timing route; ≈ 45–65 % of the DNa02 gap depending on construction). Both are refractoriness ×
  synchrony interactions; a small non-synchrony difference between the sources remains.
- **Cannot conclude:** anything about Drosophila; generality beyond J0 0.2 / b_a 0.5 / σ 2 / dt 1 ms / 8–9 mV; exact shares.

## 4. Limitations
One DATA receiving network; effective n = 8 noise reps (B1 instances ≈ identical); two levels; count-swap construction biases (random
addition, window mismatch — quantified above); rate matching level-averaged and ipsilateral-mean only (inhibitory intermediates
silenced); ~40 intervals (Bonferroni check above); red-team checks post hoc with small n.

## 5. Files
`program_v5v41/V6m3_PROTOCOL.md` (r2), `v6m3.py`, `test_v6m3.py`, `v6m3_analysis.py`, `v6m3_figures.py`; `results/v6m3/` (raw/22 npz,
calibration.json, analysis.json, analysis_stdout.txt, figures/V6m3_F1.png, config_*, stdout.txt, stdout_r1_crashed.txt, run_done,
protocol_sha256_before_run.txt, redteam/RT_H_partA.md, RT_I_partB.md + scripts).

## 6. Red team
RT-H (`redteam/RT_H_partA.md`, seeds 8 499 001–099, ~8.5 CPU-min) and RT-I (`redteam/RT_I_partB.md`, seeds 8 499 101–199, ~19 CPU-min), separate
model instances (limited independence). Corrections applied: 18/22 jobs; cancellation reading of QA and F_A not a share; D_inh and
composition; Part A timing claim withdrawn; noise-scaling resolved; dose–response/specificity; LCIRC and swap seeding; per-side
heterogeneity; rounding; added fractions; window-mismatch defect; construction-sensitive share; interaction artefact; T0/T0G wording;
"surrogate-free" deleted; CI validity; Bonferroni; per-level/side shares.
