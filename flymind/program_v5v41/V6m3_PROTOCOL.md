# V6m3 — Intermediate-layer count-vs-timing dissection (EXPLORATORY, pre-registered) — protocol r1, 2026-10-30
Written after V6m / V6m2 and their red teams, before any V6m3 simulation (the user approved this experiment, FINAL_REPORT §I).
MODEL-level computational ablations only (ALIF; DATA downstream wiring; model populations named after connectome cell types).
No biological manipulation, no claim about Drosophila. Outputs `results/v6m3/` (new, isolated). Times in this text are not used as
evidence; file modification times are authoritative.

## 0. Questions
QA: Does the model intermediates' refractory block cause the B1 intermediate spike-count deficit (V6m Exp 6, post hoc: −10.4 %
rate-weighted excitatory drive to DNa02, vanishing when intermediate t_ref → 0 without rate matching)?
QB: With the DNa02 refractory block intact, how much of the B1 − DATA DNa02 gap is carried by intermediate per-neuron spike COUNTS vs
intermediate spike TIMING, measured with real trains (no surrogate) in an exactly additive 2×2 design?

## 1. Common framework
Sources: free runs of DATA and B1 instances (LC×LC block shuffle) at LC10a current 8 and 9 mV (levels where V6m2 effects are not at a
floor), unilateral L and R, 8 noise reps. LC10a trains of the source are replayed into the DATA network (LC10a clamped; v4.3 framework).
MAIN set: B1 8 421 001–010, noise 8 445 001–008. REPLICATION set: B1 8 421 011–020, noise 8 445 201–208 (analysed identically, reported
separately). Calibration seeds 8 445 101–104 (DATA source only). Count-swap randomness: numpy SeedSequence([8 446 000, set, level, side,
rep, source, neuron-block]). Window: steady 500–1000 ms; manipulations in 300–1000 ms. Default parameters (J0 0.2, b_a 0.5, σ 2,
t_ref 2.2, dt 1 ms).

## 2. Part A — intermediates free (LC10a clamped, DNa02 free, DATA downstream network)
Intermediate dynamics (single changes, intermediates only): REF; MT0 = t_ref 0; MT0G = t_ref 0 + intermediate input gain g_m (scales
synaptic input and noise, alif `gain`) chosen on calibration seeds (DATA source, levels 8/9, both sides) from the grid 0.30…1.00 step
0.025 to match the mean ipsilateral intermediate rate of REF; MT0B = t_ref 0 + additive intermediate bias b_m from the grid −20…0 mV
step 0.5, same criterion. Reference control LCIRC-REF (LC10a circular shift, REF dynamics).
Outcomes (B1 vs DATA source): ipsilateral intermediate count (500–1000 ms), DNa02-ipsi rate-weighted excitatory drive D_exc = Σ_j
max(W[dn, j], 0)·n_j and inhibitory D_inh, relative deficit D_rel = D_exc(B1)/D_exc(DATA) − 1, intermediate pairwise correlation (5 ms),
DNa02 ipsi rate and gap.
**Primary QA:** F_A(c) = 1 − D_rel(c)/D_rel(REF) for c ∈ {MT0G, MT0B}. Decision: H-IR ("intermediate refractoriness causes most of the
count deficit") SUPPORTED if D_rel(REF) < 0 (CI excl. 0) AND F_A ≥ 0.5 with CI lower bound > 0.25 for BOTH MT0G and MT0B; PARTIAL if
for exactly one; NOT SUPPORTED if neither; the replication set must agree in outcome category for "replicated".

## 3. Part B — DNa02-only, 2×2 count-swap with real trains (LC10a and all intermediates clamped; only DNa02 free)
For each (level, side, rep, B1 instance k) the REF replays give intermediate trains X_D (DATA source) and X_B (B1 source, same noise
seed). Four inputs, per neuron within 300–1000 ms (0–300 ms from the timing source):
- DD = X_D; BB = X_B (identity cells);
- DB = timing from X_D, per-neuron counts of X_B: if fewer, delete a random subset of X_D's spikes; if more, add spikes at uniformly
  random times keeping ISI ≥ 4 ms (added spikes counted and reported); r2 (after the r1 run crashed in one REPLICATION job — no valid
  ISI ≥ 4 position for an added spike; 17/22 jobs had completed and were not opened): if no ISI ≥ 4 position exists, the spike goes to any
  free 1-ms slot (ISI ≥ 1); such fallback spikes are counted and reported. The fallback only triggers where r1 raised, so completed
  r1 jobs are identical under r2 and are kept;
- BD = timing from X_B, counts of X_D (same rule).
Cells Y(t, c) (t = timing source, c = count source): count effect C = ½[(Y_DB − Y_DD) + (Y_BB − Y_BD)], timing effect Tm = ½[(Y_BD − Y_DD) +
(Y_BB − Y_DB)], interaction = Y_BB − Y_BD − Y_DB + Y_DD. C + Tm = Y_BB − Y_DD (exact). Also on the log scale.
DNa02 dynamics: REF (primary); T0 (t_ref 0, unmatched) and T0G (t_ref 0 + DNa02 gain matched on Y_DD to REF; grid 0.30…1.00 step 0.025,
calibration seeds) — secondary.
**Primary QB:** C and Tm under REF with CIs, and shares C/(C + Tm), Tm/(C + Tm). Pre-specified reading: a route is "present" if its CI
excludes 0 in the direction of the gap (negative); "dominant" if its share's CI lower bound > 0.5. Secondary (consistency with V6m2):
Tm under T0/T0G should be ≥ 0 or near 0 (timing penalty removed); count effect should persist.

## 4. Statistics
Unit structure: one DATA receiving network; B1 instances (10 per set) nearly identical; 8 noise reps crossed with sources by common
seeds. CI95 = wider of (i) nested hierarchical bootstrap (B1 instances, reps within instance; DATA reps) and (ii) jackknife-t over reps
(t_7); RNG 8 419 080 (main), 8 419 081 (replication); 10 000 draws. Per-level results reported (no decisions per level). ~40 intervals; no
multiplicity adjustment (Bonferroni check reported).

## 5. Validation (stop if any fails)
V1 engine (reuse v6m2.step2 extended with per-neuron gain/bias) identical to alif.ALIF.step with defaults; ablations touch only the
intended population. V2 REF replay == V6m/V6m2 framework (LC-clamped REF reproduces free run for DATA on non-LC neurons). V3 DD / BB cells
reproduce the REF DNa02 raster exactly. V4 count-swap: per-neuron counts in 300–1000 ms equal the count source; deleted spikes are a subset
of the timing source; added spikes satisfy ISI ≥ 4 ms; fraction of added spikes reported. V5 calibration chosen before the main jobs and
saved. V6 Stage 1 28/28 before/after; protected tree unchanged.
