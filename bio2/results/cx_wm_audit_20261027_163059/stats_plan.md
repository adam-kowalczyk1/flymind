# Statistical-design review: CX working memory vs Kalman (pilot)

Scope: read-only review of `bio2/test_cx_working_memory_vs_kalman.py`. No simulation was run. I did not open the `preflight/` single-trial outputs, so nothing below depends on comparative outcomes. The only numbers used are from scene geometry and closed-form statistics.

## 1. Is the primary endpoint fully specified in code?

**No. It is only partly specified.**

- **Measurement (L529-533):** `e_reappear_deg = degrees(ball_az - aim_az)` is recorded at the first loop step with `t_sim >= t_reappear`. It is computed before that step's control action. The mask and the recording both test against the same `t_reappear`, so there is no leakage. `|e|` is not taken anywhere; the stored value is signed.
- **Comparator pairs:** Static vs LastObs and Hybrid vs Kalman appear only in the docstring (L11-12). No code encodes the pairing.
- **Subtraction direction:** `diffs = |e_BIO| - |e_base|` is documented in the `compute_non_inferiority_stats` docstring only (L721-725). Nothing builds `diffs`.
- **Sidedness and margin:** one-sided alpha 0.05 and a 3.0 deg margin are CFG defaults (L50-51). The margin applies to the mean of the paired |e| differences.
- **No runner:** grep finds no caller of `compute_non_inferiority_stats` or `estimate_required_sample_size`, apart from the `--estimate-sample-size` branch. `seeds_tune` and `seeds_test` (L54-55) are never read. The CLI runs one trial only.
- **Missing record:** the arm's error at occlusion onset (`e_onset`, t = 0.5 s) is not stored. It is needed for the null comparator (section 7).

**`compute_non_inferiority_stats` (L715-749).** The core is correct.
- `t = (m - delta)/se` with `p = t.cdf(t, n-1)` gives the correct lower-tail p-value for H0: mu >= delta.
- `ci_upper = m + t_{1-alpha} se` is the one-sided 95% upper bound, which equals a two-sided 90% interval.
- `ci_upper < delta` is equivalent to `p < alpha`.

Defects:
1. No guard for `n < 2`. `std(ddof=1)` returns NaN.
2. No NaN or `None` handling. Failed trials with `e = None` make `np.mean` raise or return NaN. The caller must pair and drop rows, and no code does so.
3. `se <= 1e-12` forces `t = 0` and `p = 0.5` (L734). That is wrong. It should be 0 or 1 depending on whether m is below or above delta.
4. The Hodges-Lehmann estimate uses Walsh averages with `j >= i`, which is correct. It has no confidence interval, and it estimates a pseudo-median. The test is on the mean, so the two answer different questions.
5. A t interval on a difference of folded, heavy-tailed |e| values is fragile at n = 30. A bootstrap interval is needed alongside it.

## 2. Is the 3 deg margin justified, and is noninferiority the right frame?

- **The margin has no derivation in the repo.** The only rationale is the "jaw geometry" comment (L51). One plausible anchor: ball radius 0.025 m at range 0.44 m (`BALL_X`) subtends atan(0.025/0.44) = 3.3 deg. That would make 3 deg roughly the ball's angular half-width. This needs the open-jaw aperture (`q_open = 0.93`) and a capture-success argument.
- **Ball motion dwarfs the margin.** The ball track is x = 0.44, with y0 in 0.12-0.16 and vy in -0.09 to -0.12 m/s. That gives roughly 11-16 deg/s of azimuth rate. A 3 deg margin is about 0.2-0.25 s of ball motion. Over a 1.0 s occlusion the target moves about 10-15 deg, close to the 20 deg CONTROL_FAILURE line.
- **Noninferiority is the wrong frame for a pilot.** A pilot should estimate the spread of the paired differences and check feasibility, not test. The N = 30 seeds were named "tune", so they are exploratory.
- **LastObs-PD is close to a zero-command null.** If the arm is on target at occlusion onset, `target_rel = theta_last - mouth_az` is about 0, so the command is near zero. "BIO-Static is noninferior to LastObs-PD" would therefore mean "no worse than doing nothing". That is weak evidence for working memory.
- **Better mechanism evidence is superiority.** Contrast BIO-Static and BIO-Hybrid with BIO-NoSelf and BIO-Shuffle (ablations), and with the zero-command null.
- **Noninferiority against Kalman-PD is the meaningful engineering claim.** Keep it for the held-out confirmation, only if the pilot decision rules pass.

## 3. Missing, degenerate and CONTROL_FAILURE trials

Proposed treatment, applied to the primary analysis:
- **Denominator:** all randomized seeds, with the recorded |e| for every trial where `e_reappear_deg` is defined.
- **CONTROL_FAILURE:** keep in. Dropping |e| >= 20 deg conditions on the outcome and favors the worst controllers. It is a bounded, informative outcome.
- **DEGENERATE_CALIBRATION:** keep in (e is recorded). For BIO-Shuffle it is a manipulation-check outcome. Report its count, and the primary contrast without it as a sensitivity analysis. For any other BIO arm, a degenerate calibration is an anomaly, so flag it. Sensitivity analysis excludes those seeds from all BIO arms.
- **TECHNICAL_FAILURE:** missing, dropped pairwise, never imputed. Sensitivity analyses: (a) worst-case, imputing the maximum observed |e| for the failed arm; (b) complete cases only. Report counts per arm.
- **Status priority:** an exception after `reappear_recorded` (L549-551) overrides the status but keeps `e`. Rule: analyze by `e` availability, and report status separately.
- **Stop rule:** if technical failures exceed 10% in any arm, stop and fix the code before interpreting anything.

## 4. Pairing by seed

Seed controls three things at once: `default_rng(seed)` for (y0, vy) at L418; `Brain(seed)` (the noise RNG at snn.py:38 plus calibration) at L298; and the shuffle permutation `default_rng(seed)` at L248.

- **Among the BIO arms:** this is common-random-numbers pairing. Noise and calibration are shared, so paired differences have lower variance. Calibration failures are shared too, so degenerate seeds are correlated across arms.
- **Against LastObs and Kalman:** only the scene is shared, because those arms have no network. The scene range is narrow (y0 0.04 m, vy 0.03 m/s), so the pairing gains little.
- **Correlated draws:** the scene `default_rng(seed)` and the shuffle `default_rng(seed)` start identical streams. This is a minor non-independence, but it breaks the "independent control" claim.
- **What a "seed" generalizes over:** one fixed connectome, with noise and a narrow scene family. It is not a population of animals. Say so in any conclusion.
- **Analysis consequence:** analyze paired differences with the seed as the unit. Do not treat the arms as independent samples.

## 5. Multiplicity

- **Pilot:** one occlusion time and two NI comparator pairs, so no confirmatory alpha is spent. Report unadjusted estimates and the adjusted p-values only descriptively.
- **Held-out:** the code uses alpha = 0.0125 (L788). That is Bonferroni over the 4 occlusion times, mislabelled "Holm". It ignores the comparator dimension. The family is up to 4 times × 2 comparators = 8 tests.
- **Remedy:** designate one primary (t_occ = 1.0 s, one pair) and a fixed-sequence or Holm gate for the secondaries. Holm over 8 has a first step at 0.05/8 = 0.00625.

## 6. Power

The formula `(z_a + z_b)² s²/δ²` (L755-763) uses the normal approximation and assumes a true difference of zero. It undersizes the sample by about 2 pairs. The table below uses an exact noncentral-t calculation, power 80%, delta = 3 deg, true difference 0:

| s_delta | N, alpha 0.05 (normal) | N, alpha 0.05 (exact t) | N, alpha 0.0125 (normal) | N, alpha 0.0125 (exact t) |
|---|---|---|---|---|
| 2 deg | 3 | 5 | 5 | 7 |
| 4 deg | 11 | 13 | 17 | 20 |
| 8 deg | 44 | 46 | 68 | 71 |

- **Held-out size:** N = 40 covers s_delta up to about 7 deg at alpha 0.05, but not s_delta = 8 deg, and it fails under Holm for s_delta >= 6 deg.
- **True difference above zero:** a nonzero true difference raises N sharply.
- **Precision of the SD at n = 30:** with chi-square limits, the 95% interval for the SD is (0.80 s, 1.34 s). The one-sided 95% upper bound is 1.28 s. Plan on the upper bound, not on the point estimate. This assumes normal differences; heavy tails make the SD less stable.
- **Conclusion:** n = 30 estimates s_delta only to about ±30%. That is adequate for sizing the held-out set, not for any claim of noninferiority.

## 7. Prespecified pilot analysis plan (written before outcomes were inspected)

This section is exploratory: no confirmatory claim, and it is frozen before any pilot data are opened.

**Design.** Seeds 100-129, t_occ = 1.0 s, 6 conditions, 1 trial per seed-condition (180 trials). Seeds 0-39 stay sealed. The controller gains (kp, kd, g_turn, Kalman q_w and r_v) stay fixed at their present values. No tuning on pilot results.

**Added measures (code changes, not yet made).** Record `e_onset_deg` at t = 0.5 s. Add one **Freeze-Null** arm: command 0 for the whole occlusion window, normal control otherwise. It cannot be derived from `LastObs-PD`, because that arm still moves toward its remembered position.

**Estimands.** For each condition c, the mean, median, SD and IQR of |e_c|, plus the signed mean (bias) and SD. For each paired difference, D_pair = |e_A| - |e_B| per seed.

**Comparisons (A vs B).**

| Role | A | B |
|---|---|---|
| NI pair 1 | BIO-Static | LastObs-PD |
| NI pair 2 | BIO-Hybrid | Kalman-PD |
| Mechanism (superiority) | BIO-Static | BIO-NoSelf |
| Mechanism (superiority) | BIO-Static | BIO-Shuffle |
| Mechanism (superiority) | BIO-Hybrid | BIO-Static |
| Null reference | every arm | Freeze-Null |
| Context | Kalman-PD | LastObs-PD |

**Interval methods.**
- Paired t interval at 95% two-sided, plus the one-sided 95% upper bound for the NI pairs.
- Bootstrap interval for the mean of D_pair: 10,000 seed resamples, percentile and BCa, fixed RNG seed 20261027.
- Hodges-Lehmann estimate with a Walsh-average bootstrap interval, plus a Wilcoxon signed-rank test as a sensitivity analysis.
- Report all of these side by side. No p-value-based conclusion.
- Estimates are unadjusted. Report Holm-adjusted p-values descriptively for the NI pairs and the mechanism family.

**Counts and tables.** Status counts per condition (SUCCESS, CONTROL_FAILURE, DEGENERATE_CALIBRATION, TECHNICAL_FAILURE). Seed-level scatter of |e| per pair. The fraction of seeds with D_pair < 3 deg.

**Missing-data rules.** As in section 3: primary analysis on all seeds with defined e; technical failures missing; sensitivity with worst-case imputation and with degenerate seeds excluded.

**Decision rules.** Open the held-out benchmark (seeds 0-39) only if all of these hold:
1. Technical failures are at most 10% in every arm, and BIO-Static and BIO-Hybrid have no degenerate calibrations.
2. For NI pair 2 (Hybrid vs Kalman), the pilot one-sided 95% upper bound on the mean D_pair is below 3 deg plus 2 deg, using both the t and the bootstrap interval. That "promising" margin is wider than the claim margin on purpose.
3. The upper-bound s_delta from section 6 (1.28 × the observed SD) gives a required N of at most 40 at alpha 0.0125 (exact t). If not, enlarge the held-out set instead of testing at N = 40.
4. Mechanism check: the mean |e| of BIO-Static is below BIO-NoSelf and BIO-Shuffle by more than the pooled SD of the paired differences. If not, the working-memory claim has no pilot support.
5. Null check: Freeze-Null's mean |e| is larger than that of the best BIO arm, with a bootstrap interval of the difference excluding 0. If Freeze-Null is statistically indistinguishable from BIO, report that no working memory is demonstrated, whatever the NI result.

If condition 1 fails, fix the code and rerun the pilot with new seeds (not 0-39, and not reuse of the 100-129 values for selection). If conditions 2-5 fail, report the pilot as negative or inconclusive. Do not change the margin afterwards.

## 8. Code observations (for the fix list)

- L734: `se <= 1e-12` gives `p = 0.5` (wrong for zero variance).
- L715-749: no `n < 2` guard, no NaN or `None` handling.
- L755-763 and L788: normal approximation, and the Bonferroni value labelled Holm, ignoring comparators.
- L342: `(self.tv if seen else self.tv)` is a no-op (harmless; hybrid keeps its last velocity through occlusion).
- L549-551: an exception after recording leaves `e` defined but the status TECHNICAL_FAILURE.
- L569: `k` is undefined if `n_steps_total == 0`.
- L248 and L418: same-seed generators for the shuffle and the scene.

## 9. PI amendments (recorded before the pilot was launched)

Disclosure: before this section was written the PI had seen seed-100 preflight outputs for LastObs-PD, Kalman-PD,
BIO-Static, BIO-Shuffle, LastObs-Freeze-Diag and BIO-Static-Freeze-Diag (preflight/). No gains, margins or endpoint
definitions were changed after seeing them. The amendments below were motivated mainly by code inspection (mechanism); however the seed-100 freeze
outcomes had been seen and are cited in preflight_audit.md §5, so A1 is NOT outcome-blind
(correction added after red-team review):

A1. Freeze-Null is implemented as two diagnostic arms sharing the visible-phase controller of their parent:
    `LastObs-Freeze-Diag` (parent LastObs-PD) and `BIO-Static-Freeze-Diag` (parent BIO-Static; the SNN keeps running,
    only the motor command is zeroed during the occlusion window). Decision rule 5 is evaluated per parent:
    BIO-Static vs BIO-Static-Freeze-Diag is the primary "does CX memory add anything over freezing" contrast.
A2. BIO-Shuffle: its calibration is degenerate by construction (EPG silent, slope_mem = 0) and its visual steering is
    also broken (visual slope ~10x lower). Its |e| is therefore NOT a memory-specific comparator. Decision rule 4 is
    evaluated on BIO-Static vs BIO-NoSelf only; BIO-Shuffle is reported descriptively, with status counts, and excluded
    from every comparative endpoint table (sensitivity: shown separately).
A3. e_ring is only interpreted when bump coherence at reappearance >= 0.2 (a silent ring returns angle(0)=0).
A4. t_reacquire is retained as defined, but is expected to be mostly missing (5 deg band below the steady visible
    tracking lag); it is reported as a missingness rate and not used for any decision.
A5. Effective occlusion is 101 control steps (t = 0.51 ... 1.51 s) because d.time accumulates just under multiples of
    0.01; identical for all arms.
A6. Additional exploratory decomposition (all arms): e_reappear = e_onset + delta_ball - delta_aim, where delta_ball and
    delta_aim are the azimuth changes of target and gripper during occlusion; "memory gain" of an arm = |e_freeze| - |e_arm|
    on the same seed.
