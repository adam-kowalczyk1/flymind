> **SUPERSEDED (2026-10-27):** where this file conflicts with `confirmatory_protocol_v4.md`, the v4 protocol is
> binding. This file is kept unchanged below as history. Its pre-repair copy is
> `archive/pre_repair_20261027_185611/`.

# Hypotheses and thresholds (prespecified before seeds 300–399)

Labels: **[P]** provisional, **[D]** derived from dev data, **[L]** literature context only (not a requirement, not a biological fact). Dev1 = seeds 200–205 (λ_self=1, λ_cx=1; 12 trials/arm). Dev2 = seeds 206–209 (λ_self=1.105, λ_cx=0.65; 8 trials/arm, 7 arms). Only 10 dev seeds exist, so every dev SD is imprecise. Numbers are recomputed at seed level from `dev/*.jsonl`.

## 0. Design and data problems found

1. **Freeze and Scalar are constants at seed level.** Freeze |e_end| = 17.31 (SD 0.01); Scalar 1.4–1.6. Averaging |e| over ±Δ removes e_onset exactly (mean of |e0+x|, |e0−x| = |x| when |x| > |e0|). Every paired contrast against them has SD equal to the CX-Bump seed-level SD (7.4 dev1, 9.1 dev2). All variance is CX variability.
2. **The dominant CX error is a seed-specific bump drift, not gain.** In CX-Bump-NoSelf the bump moves identically in both Δ conditions of a seed: −5, +23, +25, −4, +6, +8° (dev1); +18, −15, +11, −6° (dev2). RMS ≈ 14° in 0.6 s, against a 17.3° passive signal. It makes raw g direction-dependent (dev1 2.04 for Δ=−20 vs 1.05 for +20; dev2 1.62 vs 0.75). Averaging ±Δ within a seed cancels it.
3. **The CX estimate is no better than doing nothing:** |θ̂ − truth| at reappearance is 20.1° (dev1), ≈21.8° (dev2), vs 17.3° never-updated and 0.6° Scalar.
4. **CX-Reset and CX-Shuffle20 equal Freeze exactly** (SD 0.00; silent ring gives ω=0).
5. **Pulse effect depends on Δ:** S = 10.6 (Δ=−20) vs 24.7 (+20) in dev1; 20.2 vs 28.6 in dev2 (21–30 % of memory steps saturated). Sham differs from plain CX-Bump (−5.2, +2.3), so Sham is the comparator.
6. **Cue slope and seen-count are not logged**, so §1 is only partly assessable. Log n_seen_30, slope and t_on in confirmation.

## 1. Pre-occlusion stable tracking

Criterion (implemented): t ≥ 1.0 s, cue seen ≥ 27/30 steps, |slope| ≤ 4°/s, else NOT_CONVERGED at 2.2 s (a seed property).
Observed [D], 14 seeds (10 Exp A, 4 Exp B): all converged; t_on 1.28–1.49 s, so the slope/seen condition binds, not t ≥ 1.0. e_onset −7.0 to +6.4°. w_base at onset 0.09–0.19 rad/s. Onset state bit-identical across arms; realised passive 17.35 ± 0.05°.
Assessment: adequate. NOT_CONVERGED 0/14 (95 % upper bound 21 %).
**Rule [P]:** NOT_CONVERGED seeds are excluded everywhere and counted. If > 20 % of confirmation seeds fail, no inference is drawn.

## 2. Bump coherence and persistence

Dev [D]: time-mean coherence 0.78–0.80; per-trial minimum over the memory phase 0.72 (dev1), 0.69 (dev2); 0/20 trials below the 0.2 gate at the end.
Acceptance [P], per CX-Bump trial: memory-phase mean ≥ 0.60 and minimum ≥ 0.40; gate passed if ≥ 90 % of valid trials meet both.
If it fails: results are reported intention-to-treat (silent ring → ω=0 → Freeze-equivalent) and labelled "persistence check failed". That is a negative result about the model, not a technical failure.
Coherence is necessary, not sufficient. Also reported: no-self-motion drift RMS over 0.6 s (dev ≈ 14°). **Prediction [P]:** drift RMS ≥ 8.7° (0.5 × passive) implies Q2 unresolved. Dev meets this.

## 3. Self-motion integration gain

g = −Δbump(post-passive − onset) / realised passive rotation (aim-referenced; ideal 1; Scalar with λ=1.105 gives 1.00). **Primary: seed-level mean over ±Δ**, which cancels drift.
Observed [D]: dev1 1.54 (seed SD 0.38, n=6, t-CI 1.14–1.94); dev2 1.18 (SD 0.51, n=4, CI 0.37–2.00). Trial-level SDs 0.67 and 0.86 are drift-inflated. The dev2 trim predicted 1.0 and gave 1.18; it is not shown to work.
Acceptance [P/D]: point estimate in **[0.75, 1.25]** and 95 % CI inside [0.6, 1.5]. A 0.25 gain error gives ≈ 4.3° memory error over the passive window, just under the Q3 margin.
[L] Context only: Green 2017 fits 0.75–1.40; Seelig 2015 0.47 ± 1.2 (ball rotation, per literature_matrix.md). Both are per-fly and wide; they do not set the interval.
**Before freezing:** re-check g on ≥ 20 fresh dev seeds (210–229); four seeds cannot support a pass. On confirmation seeds g is a diagnostic: outside the interval, verdicts (b) and (c) become INCONCLUSIVE (miscalibrated); (a) is unaffected. No retuning on confirmation seeds.

## 4. Primary endpoint and contrasts (Exp A)

Endpoint: |e_end| at reappearance. Seed value = mean over Δ=±20. Unit of inference = seed. d = |e|(A) − |e|(B); negative favours A. Signed e_end is secondary.
- **Q2 CX-Bump vs Freeze.** Minimum meaningful benefit 3° (≈ 17 % of 17.3°) [P]. CX-Reset and CX-Shuffle20 are asserted identical to Freeze (max |diff| < 0.01°) and reported as one "no-ring" row. They are not independent tests (m=1). If the assertion fails they become real contrasts (m=3).
- **Q3 CX-Bump vs Scalar, non-inferiority, margin 5°** [P]. Rationale: ≈ 30 % of the Freeze–Scalar gap (15.9°); onset encoding error (SD 4.2–4.9° [D]) puts even an ideal CX ≈ 3–4° above Scalar, so smaller margins are unreachable; it matches the 4.3° gain tolerance. NI holds if the 95 % CI upper bound of d < 5°. Superiority is secondary, expected negative, tested only after NI.
- **Q4 CX-Bump vs NoSelf.** Minimum benefit 5° [P]. NoSelf is deliberately crippled; this tests the pathway, not usefulness.

Dev1 / dev2 [D], d mean (SD): Q2 −2.9 (7.4) / +0.9 (9.1); Q3 +13.0 (7.4) / +16.6 (9.0); Q4 −16.6 (15.8) / −6.7 (15.1).

## 5. Perturbation (Q1)

Primary S = (e_end(Pulse−30) − e_end(Pulse+30))/2 per seed (signed, mean over ±Δ), predicted > 0. Dev [D]: dev1 17.7 (SD 3.9, 6/6 positive); dev2 24.4 (SD 3.5, 4/4). Scalar-Shift±30 positive control 27.3.
Each pulse vs Sham (signed, secondary): +30: −14.8 / −16.5; −30: +20.6 / +32.3.
Minimum meaningful S: 5° [P] (≈ 1/6 of the 30° shift).
**Output follows state** iff all hold [P/D]:
1. Manipulation check: median measured bump shift ≥ 15° in the predicted direction for both pulses; Sham |median| ≤ 5°; coherence change ≤ 0.1. (Dev: +26.2 / −24.8; sham +0.2; 0.79 → 0.79.)
2. S CI lower bound > 5° and ≥ 80 % of seeds have S > 0.
3. Per-trial slope of e_end on measured bump shift (pulse and sham trials, seed-clustered) ≤ −0.25, CI excluding 0 (dev effect/shift 0.56–0.83).
4. Positive control S_scalar ≥ 20°, else the pipeline is broken (experiment TECHNICAL_FAILURE).
Caveat: ω = K·decode(bump) by construction, so Q1 mostly verifies the implementation.

## 6. Causal memory vs frozen-command behaviour

A frozen command is output unrelated to the state-plus-self-motion history. "Causal memory" requires all of: (i) Q1 passes; (ii) the state is updated by self-motion: seed-level g CI inside [0.6, 1.5] and Q4 benefit ≥ 5° with CI excluding 0; (iii) the estimate beats a never-updated one: mean |θ̂ − truth| at reappearance has CI upper bound < 17.3°. **Dev fails (iii)** (20.1 / 21.8°). 

## 7. Failures, degenerate calibration, missing data

- **NOT_CONVERGED:** §1.
- **TECHNICAL_FAILURE** (seed excluded from CX contrasts): exception or NaN; onset state not bit-identical across arms; realised passive outside 17.35 ± 0.5°; degenerate calibration (steer_calib slope_mem < 7 [≈ ½ of dev 14.3] or offset_mem outside ±10 [dev −2.8 to −3.5]; slope_mem ≈ 0 means a dead DN readout).
- **Intact ring silent** under a valid calibration (coherence < 0.2) is a result, not a failure: kept ITT (ω=0) and counted.
- Missing: a seed needs both Δ trials in both arms (complete case).
- Seeds are used in order from 300; target = first N valid seeds, cap 399. Minimum: ≥ 85 % of planned N valid and ≥ 20 absolute for Q1/Q4; otherwise "inconclusive", not negative. If TECHNICAL_FAILURE > 10 % of seeds, stop and do not interpret.

## 8. Statistics

Paired t 95 % CI on seed-level d; BCa bootstrap (10 000 resamples of seeds, RNG seed 20261027); Wilcoxon signed-rank sensitivity. Decisions use the t-CI; if BCa disagrees the verdict is "fragile" and the conservative reading stands. Holm within families: Q1 {S, +30 vs Sham, −30 vs Sham} m=3; Q2 m=1; Q3 m=1; Q4 m=1.

## 9. Sample size

Seed-level SDs [D], pooled dev1+dev2 (df=8), one-sided 95 % chi-square upper bound (UB) in brackets: Q2/Q3 8.1 (13.8); Q4 15.6 (26.6); Q1 S 3.7 (6.4; per-batch UBs 8.1 and 10.1). Noncentral-t power for paired tests:

| Contrast, planned δ | N, point SD (α .0125, 90 %) | N, UB SD | N at α .05, 80 % (point / UB) |
|---|---|---|---|
| Q1 S vs threshold 5, true 15 (δ 10) | 6 | 18 (SD 10.1) | 4 / 11 |
| Q4 vs NoSelf, δ 10 | 38 | 104 | 21 / 58 |
| Q2 vs Freeze, δ 5 | 40 | 111 | 23 / 61 |
| Q2 vs Freeze, δ 3 | 105 | 301 | 58 / 166 |
| Q3 NI margin 5, true d 0 | 23 | 61 | (one-sided .025, 80 %) |
| Q3 NI, true d 2 | 58 | 166 | |
| Q3 NI, true d 3 | 128 | 371 | |

- **Small-scale causal experiment (Q1, Q4): N = 18 for Q1, 38 for Q4** at point SD, so N = 40. Q4 at UB SD needs ≈ 104.
- **Q2/Q3:** N ≈ 40–111 for a 5° benefit. Q3 NI is feasible within 100 seeds only if true d ≤ 2° and SD ≤ 8; observed d is +13 to +17, so NI is expected to fail at any N. Q2 observed d ≈ 0 ± 8; a 3° effect is out of reach.
- **Plan:** Stage 1 = seeds 300–339 (N=40). Compute only the SD of d for Q2/Q3 (no means, no tests). N_final = min(100, max(40, N for 5° at α .0125/90 % with that SD)). Run to N_final, test once. No interim effect looks.

## 10. Falsifiers (at N_final, under the §7 validity rules)

- **(a) "CX state causally drives steering" is rejected** if the manipulation check passes (§5.1) and any of: S CI upper bound < 5°; S CI lower bound ≤ 0; < 60 % of seeds with the predicted sign. If the check fails the result is "no manipulation", not rejection. Dev would pass.
- **(b) "Persistent CX activity is behaviourally useful" is rejected** if the Q2 CI lower bound of d > −3° (a 3° benefit is excluded) or the CI lies wholly above 0 (harm). Supported only if the upper bound < 0 and the point estimate ≤ −3°. Otherwise "not demonstrated". Dev1 CI [−10.7, +4.8] and dev2 [−13.5, +15.3] are not demonstrated, with point estimates leaning negative.
- **(c) "CX non-inferior to the matched scalar" is rejected** if the Q3 CI lower bound > +5°. Supported if the upper bound < +5°. Dev1 lower bound +5.2 (would reject), dev2 +2.4 (not yet).
- **The criteria can reject.** Replaying them on dev gives three different verdicts: (a) passes, (b) unresolved, (c) inferior. Verdicts apply to this model and task, not to flies.

---
## 11. PI addendum v2 (after red-team round 1 and dev4; written BEFORE any confirmation seed)

The design was revised after red-team round 1 and run on dev seeds 230–235 (`dev/analysis_dev4.txt`). It is
**Exp A2**: a target jump of ±U(10, 20)° visible for 0.2 s, then occlusion, ball stop, and Δ ∈ {−20, 0, +20}. The
revised runner's sha256 is in `frozen_runner_sha256.txt`. Earlier sections stay in force unless overridden here.

### A2-1. Primary Q1 (causal efficacy)

- **Statistic.** S_DN = (e(CX-DN-Pulse−30) − e(CX-DN-Pulse+30))/2. Each seed's value is the mean over the three Δ
  conditions.
- **Why this readout.** The DN readout (PFL3→DNa02/DNa01, with a single memory calibration) is not an identity mapping of
  the bump. S_bump, from the bump readout, is demoted to a manipulation-level check.
- **Criteria.** As in §5:
  - CI lower bound > 5°;
  - ≥ 80 % of seeds positive;
  - manipulation check: median bump shift ≥ 15° for both pulses and ≤ 5° for sham.
- **Dev4 result.** S_DN = +21.1 [+18.2, +24.1], 6/6 positive. Bump shifts were +30.3 / −26.5 / sham +2.4.

### A2-2. Primary Q2 (behavioural usefulness)

- **Contrast.** Δ = 0 trials only, which test pure target memory. The seed-level paired difference
  d = |e|(CX-Bump) − |e|(Freeze).
- **Co-primary reference.** CX-Bump vs SelfOnly, the cue-free integrator, on Δ = ±20.
- **Rules.**
  - "Useful" requires the upper CI bound < 0 and the point estimate ≤ −3° for **both** contrasts.
  - "Useless or harmful" is declared if the lower CI bound of either contrast is > −3°.
- **Dev4 result.** Δ = 0 vs Freeze: +13.2 [−4.6, +31.0]. ±20 vs SelfOnly: +12.2 [+2.2, +22.1].

### A2-3. Q3

Unchanged: non-inferiority to Scalar with a 5° margin. Dev4: +18.9 [+1.7, +36.1] at Δ = 0, and +17.6 [+9.9, +25.4] at
±20.

### A2-4. New memory-content criterion

- **Method.** Regress the memory-phase correction (e_end − e at the end of the passive window) on the bearing at the end
  of the passive window, pooling all Δ.
- **Pass condition.** Slope ≤ −0.5 with its 95 % CI excluding 0, and r ≤ −0.5.
- **Dev4 result.**
  - CX-Bump: −0.71 ± 0.27, r −0.55 (borderline pass).
  - Scalar: −0.90 ± 0.03, r −0.99.
  - SelfOnly: −0.69, r −0.86. SelfOnly corrects only the self-motion part.

### A2-5. Onset identity

- **Rule.** The onset state must agree across arms within 1e-3°.
- **Reason.** In dev4, 2 of 216 trials were not bit-identical at onset. The maximum difference was 1.2e-5°
  (`verify/dev4_onset_identity.txt`), probably from offscreen-render nondeterminism. Bit-identity is not guaranteed.

### A2-6. Small-scale confirmation sample (stage 1)

- **Size.** Seeds 300–323 (24 seeds) × 12 arms × 3 Δ.
- **Why 24 is enough.**
  - Q1 needs ≤ 18 seeds even at the upper-bound SD (§9; dev4 S_DN SD 2.8).
  - The dev-estimated CX harm at Δ = 0 (+13°, seed SD 17) needs ≈ 14 seeds to exclude 0 at 80 % power.
- **What 24 cannot do.** It cannot establish a 3–5° benefit; that would need about 100–300 seeds (§9). If the
  stage-1 point estimate favours CX, stage 2 is sized from the stage-1 SD (cap seed 399).

### A2-7. Renamed onset rule

The "convergence" criterion is renamed the **slow-tracking onset rule**. In every dev trial it fired at its 4 °/s
boundary, so it is a timing rule, not proof of convergence.

### A2-8. Amendments from red-team round 2 (text only; runner hash unchanged; still before any confirmation seed)

These amendments **supersede** A2-4, A2-6 and §4/Q4 where they conflict.

1. **A2-4 memory-content test is within-Δ.**
   - Demean the correction and the post-passive bearing within each Δ, then pool.
   - Pass condition: slope ≤ −0.5 with its 95 % CI excluding 0, and r ≤ −0.5.
   - Reason: in the pooled version, SelfOnly (which has no target memory) passed.
   - Dev4 within-Δ results (`verify/redteam2_spotcheck.txt`):
     - Scalar −0.82 ± 0.06, r −0.96 (pass);
     - CX-Bump −0.31 ± 0.50, r −0.16 (would fail);
     - CX-DN −0.51 ± 0.54, r −0.23;
     - SelfOnly 0.
2. **The Δ = 0 contrasts are exempt from the self-motion-gain gate** of §3. At Δ = 0 there is no self-motion demand
   beyond the shared visible phase.
3. **Stage-1 arm list = the 14 arms in the stage-1 command** (`causal_protocol.md` §6).
4. **Additional reporting for every arm:**
   - signed e_end, mean and SD;
   - offset-removed |e|, that is |e − seed-mean-of-arm-across-Δ|, so that a constant drift bias and random error can be
     told apart. This is descriptive only.
5. **Q4 is demoted.** It is now reported as CX-Bump-NoSelf vs Freeze and CX-Bump vs NoSelf, both descriptive. NoSelf is
   worse than Freeze, so CX-Bump beating NoSelf shows only that harm was avoided.

### A2-9. Known limits of stage 1 (stated before running)

- **e_onset is still narrow and confounded.** Its SD is 9.2° and it correlates +0.81 with the jump sign, so the
  remembered quantity is partly predictable from the scene seed.
- **A negative Q2 means "this parameterisation".** The CX's harm at Δ = 0 comes from bump drift and the onset transient
  under the frozen calibration (K, λ_cx, coherence gate). A negative Q2 therefore describes this parameterisation, not
  ring attractors in general.
- **Q1 is a low-risk transmission test.** It shows that the network's state reaches the motor command, not that the
  state is useful.
- **24 seeds can reject "useful" but cannot establish a 3–5° benefit.**
