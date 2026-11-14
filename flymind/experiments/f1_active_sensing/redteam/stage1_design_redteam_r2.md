# Red team r2 — F1 Stage 1 design (STAGE1_DESIGN.md d2). Model only, read-only.

Probes: `.venv/bin/python -I -B`, FK/encoder only. Static renders (no closed loop) of the ball at rho 0.16/0.22/0.30/0.36 and az 0/±8/±16 through `TargetEncoder(ENC)`, plus `loop.calibrate_p` and a binary-threshold version of it. No seeds used. Read: loop.py, encoder.py, Stage 0 systems.py/confirm_params.json/PROTOCOL §8.

## Verdict: PASS_WITH_FIXES (one MAJOR new problem: TH_LP-ster as specified; two MAJOR statistical gaps)

## r1 findings
1. 1 Hz argument — PARTIAL. The false claim is deleted (§1.5), but R5 chooses between only two f values, from 10 smoke trials, and the decoder-only (omega frozen) variant is not added.
2. Command-level separation / stale — RESOLVED. A stale or timeout tick invalidates the trial, with a >1 % STOP. It is not stated how invalid trials enter the paired stats (drop the unit, or count it as a failure).
3. Primary outcome — RESOLVED. A cosine ramp (4.75–5.5 s) is used for every motion trajectory, and success is scored on raw e at 5.5–6.0 s. The ramp is smooth, has A_pan ≤ 3.3° and a peak rate of about 14°/s. Servo lag is about 0.16° and decays, so there is no meaningful bias. The final window tests acquire-and-hold under a static view for all arms.
4. Circularity S7/S5 — PARTIAL. Raw e is now used. S7 is still near-tautological: gated stops moving once |ω| > ω_on, so its raw |e| in 3–4.75 s lacks the ±4° oscillation by construction.
5. Amplitude confound — RESOLVED (A_pan = 4°/g_b per trial).
6. Success windows — RESOLVED (one gate [0.1, 0.9], S5/S6/S10 ungated). See N2 for TH.
7. R2 — PARTIAL. The explicit Clopper–Pearson rule, pan_t-based cumulative |Δpan| and DiD for S8/S9 are fixed. See N3/N4.
8. TH_LP-ster — PARTIAL. The tau/theta circularity is removed, but see N1.
9. 3 s→6 s baseline — PARTIAL. The slope-shift STOP (>10 %) and the F1 bit-for-bit test are added. The 3 s early-window secondary and the `none` 3 s vs 6 s smoke comparison are not.
10. mt/virtual — RESOLVED (qvel = 0, F5, cam_quat restored). For `mt`, "orbit around the camera" does not say whether it is the current or the fixed eye (parallax). Minor.
11. Pilot degrees of freedom — RESOLVED. R3 has a floor of 0.10 (vacuous in practice, since N trials give ω = 0, which is fine as a fixed value). R1 uses Spearman–Kärber. The overlap of the gated re-enable ramp with the 4.75 s ramp is unspecified (take the product).
12. Budget/registry — RESOLVED. The budget is corrected, and the seeds are in SEED_REGISTRY.md lines 22–32.

## New findings

**N1 MAJOR — TH_LP-ster is implementable but behaves as a deadband controller.**
- §4 uses z = [y > 5.93 mV], u = z_L − z_R ∈ {−1, 0, +1}. Stage 0's TH_LP was a continuous rectified difference (`thresh_D`: mean of max(0, yL−θ) − max(0, yR−θ)). The 5.93 mV value was matched to a different object, so "value from Stage 0" does not transfer.
- Probe of 12·g (mV): rho 0.30 az 8 gives [5.08, 2.57] → u = 0. rho 0.36 at every az tested gives u = 0. rho 0.22 az 8 gives [7.09, 4.18] → u = 1. rho 0.16 az 8 gives [9.31, 6.62] → u = 0 (both eyes above θ).
- Whenever both eyes are above or both below θ, u = 0. In W the `none` success of this controller will be ≈ 0, so the arm is UNMEASURABLE and S4 is untestable. In S the deadband is wider than ±8°, so success is also capped.
- `slope_TH` by `calibrate_p` is also unrepresentative. The synthetic 9-px spots saturate (12g ≈ 11–12 mV), and u is a step: u = [−1, −1, 0, 0, 0, 1, 1] over az −30..30 by 10, giving slope 2.05 against slope_P 1.49. `calibrate_p(shape)` has no threshold hook, so a new function is needed. This is implementable but not "the same procedure".
- Fix: use the Stage 0 form, u = max(0, y_L−θ) − max(0, y_R−θ), divided by a slope calibrated on it. Add a pilot gate: TH_LP-ster `none` success ∈ [0.1, 0.9] in W, otherwise S4 is "not tested" (as Stage 0 did for S6). Alternatively define S4 on the open-loop D, not on closed-loop success.

**N2 MAJOR — S5 HARMFUL rule is degenerate.** "Upper CI95 of harm ≥ margin AND estimate ≥ margin" reduces to "estimate ≥ margin", since the upper bound ≥ the estimate. There is no significance requirement, so HARMFUL can fire on noise, and G-b then makes the result negative. Fix: HARMFUL iff the lower CI95 bound of harm > 0 and est ≥ margin (or lower bound ≥ margin). Keep "nieszkodliwy" as upper bound < margin.

**N3 MAJOR — S10 is not computable as written.**
- The "f component of pan_t in 2–4.75 s" has no estimator. The window is 2.75 s, which is 1.4 cycles at 0.5 Hz and 2.75 at 1 Hz, so there is leakage. pan_t also has a DC/ramp component and the 2–3 Hz limit cycle.
- `none` has no phase, so the paired reference is undefined.
- The range (W, S, or both) is not stated. R5 selects f on range S, but S10 harm is possibly judged on W.
- Fix: use a lock-in at f with the same φ_u assigned to the paired `none` trial, after detrending (linear) over 1.5–4.75 s. State the range (S and W, DATA). R5 on 10 trials with a 0.2° tie band is mostly noise; use 20 and report the SD.

**N4 MAJOR — R2 for S2/S3 ignores instance variance.**
- B1/SWS units cycle over 10 instances (`pick`), so the DiD statistic carries between-instance variance that does not shrink with n. A flat SD/√n formula overstates power.
- The pilot has only 5+5 instances, so the instance variance is poorly estimated.
- The formula uses z_0.975 and z_0.8 (superiority, unadjusted) for equivalence tests, which need TOST (z_0.95 + z_0.9, on CI90) and the Holm-adjusted α. S1 and S7–S9 are not in the max.
- Fix: size n by simulating the hierarchical bootstrap on the pilot's per-unit differences (Holm α, TOST margin 0.10). Include S1. Report the cap-bound power before the confirm run.

**N5 MINOR — S6** counts only sin-only events and uses all N trials as the denominator, ignoring none-only events. Use a McNemar-type exact bound on discordant pairs. Define the S6 count of valid N trials.

**N6 MINOR — `jvel` matching "whole trial"** is ambiguous with the ramp. State whether matching is on the ramped sinusoid. The gated and re-enable ramp product is also unspecified.

**N7 MINOR — The ramp causes no bias, but dilutes the effect.** Motion is active 4.75 s of 6 s, with acquisition-and-hold required. G-f at 0.9 would not distinguish a limit-cycle scan from success after the ramp.

## Top findings
N1 (TH_LP-ster deadband, S4 UNMEASURABLE), N2 (S5 HARMFUL rule trivially true), N3 (S10 estimator undefined), N4 (R2 ignores instance variance and uses the wrong z for equivalence).
