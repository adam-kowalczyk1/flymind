# Red team r1 — F1 Stage 1 design (STAGE1_DESIGN.md d1). Model only, read-only review.

Probes used: FK via SO101Sim.fk (render=False), a physics-only servo probe through SafetyLayer (no vision, no loop.run_trial), and reads of the stored V5 confirm file results/v5/v5_confirm_20261028T220223.json. No seeds were used.

## Verdict: PASS_WITH_FIXES (the sensory/motor separation is sound; the primary outcome and several statistical rules need fixing before implementation)

## Code facts (check 1)
- CONFIRMED. Only shoulder_pan yaws the camera. A +4 deg step on joints 1-3 gives dyaw 0 and dpitch -4. Wrist_roll gives pure roll.
- CONFIRMED. Pan +4 deg moves the eye 1.53 cm. The eye is 0.2584 m from the axis. Bearing gain g_b = 1.77-1.78 at rho 0.28, so 4 deg of pan gives 7.1 deg of bearing.
- Servo tracking is excellent, so F2 should pass easily. At 1 Hz with A = 2.3 deg, max |command - q| is 0.16 deg against the 1.15 deg lead cap. At omega = 1 rad/s plus the sinusoid it is 1.03-1.08 deg, which is marginal only at saturation.
- REFUTED (the crossover reasoning). Loop gain is 2.5 x g_b = 4-6 1/s, not 2.5 1/s. g_b is 1.6-2.4 over the design's own ranges, and the design cites 1.78 itself. The linear crossover is therefore about 0.65-0.95 Hz, not 0.4 Hz. The extra lags (tau_rate 50 ms, tau 0.1 s, 10 ms frame, servo) leave little phase margin, so 1 Hz is not "above the band".
- Empirical evidence of a nonlinear limit cycle: in the V5 confirm data, delay-0 DATA trials at rho 0.16-0.18 show a sustained peak in omega at 2.80 Hz (8 of 8 trials). omega rms is about 0.34 and e peak-to-peak is 8-9 deg, even in successful trials. The two failures have |e| of 4.2-5.2 deg in the last 0.5 s, just across the 5 deg tolerance.

## Findings

1. **MAJOR — the "1 Hz is above the motor band" argument (§1.5) is wrong.** See the crossover and limit-cycle evidence above.
   - Entrainment or subharmonic coupling with a threshold loop is plausible.
   - Fix: delete the claim. Justify f from the measured closed-loop transfer, i.e. a F3 pre-run with a swept f on the `none` loop. Also add a decoder-only variant (omega frozen) to separate the sensory effect from the motor reaction.

2. **MINOR (verified OK) — the command-level separation pan_t <- qt[0] - theta_s works.**
   - Without the subtraction the pan drifts to 37.8 deg in 6 s, with 444 rate flags.
   - With the subtraction the residual is 1e-15 and there are no flags (A 2.3-8 deg, 0.5-2 Hz).
   - Clipping is symmetric. The lead clip pulls pan_t toward q - theta_s, so it creates no wind-up.
   - vision_stale holds prev[j], so pan_t absorbs -Delta theta_s, a bias of up to 2A. This did not occur in the V5 delay-0 runs (flags {}). It appears only under delay (3600 flags in the delay-5 runs).
   - Fix: assert zero vision_stale/cmd_timeout ticks in F2. Any such tick makes the trial invalid.

3. **MAJOR — the primary outcome (e - theta_s*g_b) is ill-defined and state-dependent.**
   - g_b varies with pan state, rho and az: at rho 0.28 it is 1.78 at pan 0, 1.54 at 20 deg and 1.40 at 30 deg. For rho 0.16-0.36 it spans 2.4-1.2.
   - The product theta_s*g_b is therefore not a fixed linear correction. The choice of g_b (pan_t state or q state) is a researcher degree of freedom.
   - It differs per condition: for `virtual` g_b is 1 and e already contains the virtual rotation, because fk uses the mutated m.cam_quat. For `mt` the ball is displaced and a different subtraction is needed.
   - The sinusoid has a 1 s period and the window is 0.5 s, so the window covers only half a cycle.
   - Fix (exact and condition-neutral): every trial ends with theta_s ramped to 0 over the last 0.75 s, for sin, jvel, virtual and mt (gated already does this). Score raw e on the stationary final 0.5 s. No g_b is needed. Also report the e_motor counterfactual, bearing(sim.fk with q0 = pan_t), as secondary.

4. **MAJOR — circularity of S7 and "useful vs uncontrolled" (check 7).**
   - §5 subtracts theta_s from e, so sin is never penalised for its own oscillation. §13 then says sin is "by definition" disadvantaged for terminal error vs gated.
   - The S7 result depends only on which e is used (raw: penalised by construction; subtracted: not penalised at all). The "S5/S6 not harmful" verdict is likewise computed on the metric that hides the cost.
   - The "uncontrolled" thresholds (>1.5 A_pan; envelope growth) are arbitrary and untested against a baseline. The V5 limit cycle at rho 0.16 already has a pan amplitude of about 0.7 A_pan, and it is unclear whether the criterion means the f component or total oscillation.
   - Fix: use the ramp-out raw metric (#3) for success and final error. Make S5/S6 harm and the oscillation criterion use raw e during scanning. Define the oscillation criterion as the f-component vs the none baseline, and say that S7 compares time-to-first-detection and scanning duty cycle.

5. **MAJOR — amplitude confound with rho.**
   - A_pan is a single median value. Bearing amplitude is then A_pan x g_b, which is 4.6 deg at rho 0.22 and about 3.6 deg at 0.36.
   - Stage 0 found the benefit is steep in amplitude (2 deg gives about +0.04, 4 deg about +0.09).
   - So the weakest targets (large rho) get the smallest stimulus, which biases sin against `virtual` and `mt` (exactly 4 deg). It also biases the rho-tercile analysis.
   - Fix: A_pan = 4 deg / g_b(rho, az0, pan = 0) per trial, deterministic from FK. Record the achieved amplitude.

6. **MAJOR — inconsistent success windows and statistical rules.**
   - Measurability is [0.1, 0.8] in §6, [0.15, 0.6] in R1, and [0.1, 0.9] in Stage 0 PROTOCOL §8.
   - Range S is the V5 range, where DATA/none already succeeds in 0.95 of the delay-0 trials. That is above the reused UNMEASURABLE cut of 0.9, so S5 arms are UNMEASURABLE by the reused rule and EQUIVALENT is unattainable. The S5 test also has a ceiling effect and little power to detect harm.
   - The wording "strong target" is fine, but "kamera stacjonarna zwykle wykrywa" holds only at rho >= 0.2. V5 success at rho 0.16-0.18 is 0.375-0.5 (all delays pooled, 40 seeds).
   - Fix: define one gate. Tune S range separately, or accept that S5 is NI-only with exact binomial bounds.

7. **MAJOR — the sample-size rule R2 differs from Stage 0 and covers only one test.**
   - Stage 0 R2 sized n over the maximum of H1 and S1-S6 (Holm alpha), with a 1.2 inflation. §8 R2 gives only "power 0.8, SD, SESOI". The test, alpha and sidedness are not specified.
   - Closed-loop discordance may be about 0.3, giving a paired SE of 0.039 at n = 200. That is about 75% power for 0.10 and ~0.055 for the DiD tests. The n = 200-400 equivalence tests (±0.10) are then INCONCLUSIVE.
   - Mixing SESOI 0.10 with the Stage 0 numeric cutoffs (0.07 in the SUPPORTED estimate rule and in CI90 ⊂ (-0.07, 0.07)) is ambiguous. If SUPPORTED needs est >= 0.10, power at true Delta = 0.10 is at most 50%.
   - Equivalence at ±0.10 equals the effect being studied, so S4 "EQUIVALENT" tolerates a TH_LP-ster that gets half the benefit.
   - S7 is a compound outcome with no combining rule. S8's G-e rule is a difference of significance, not a test of the difference: use a DiD test.
   - `mt` appears in no hypothesis.
   - Fix: write explicit thresholds per test, and run R2 as a max over all tests including NI tests, with the cap-bound achieved power written before the confirm run. For S6 (N-range false turns, expected 0 events) use an exact upper bound (rule of three at n = 200 gives 1.5%), not a point-mass bootstrap. Holm-adjust the TOST CIs, or at least state that equivalence claims are not FWER-controlled.
   - Define "cumulative |Delta pan|" on pan_t, not q. With q, a sinusoid trivially gives 53 deg.

8. **MAJOR — TH_LP-ster is circular and under-specified.**
   - tau_LP is fit on Stage 0 confirm data to reproduce DATA's response in stat, sin, J_shuf, J_rms and J_vel, and theta is matched to DATA stat BSC. S4 EQUIVALENT is then close to built in. It tests only whether open-loop matching transfers to the loop.
   - The output is described as "+-1" but calibrate_p is a linear fit. The output of the Stage 0 TH is a continuous rectified difference.
   - A rectified signal near threshold has low closed-loop gain, so the comparison may be about gain shape, not about spikes.
   - Fix: define the output formula, state the circularity, and match the closed-loop omega-vs-D map or the stationary detection rate.

9. **MINOR — baseline change from 3 s to 6 s.**
   - The Stage 0 BSC window is 1-3 s, so the baseline success of 0.33 does not transfer. More noise-driven detection opportunities will raise the stationary baseline.
   - Add a 3 s early-window secondary measure, and a smoke comparison of `none` at 3 s vs 6 s in 1-F.
   - Decoder recalibration: slope is a fit over ±30 deg with 3 seeds and sets loop gain as 1/slope. A shift of 10% changes K by 10% near the limit-cycle regime. The design reports but does not control this.
   - Fix: the F1 equivalence test should compare to loop.run_trial using the V4 slope. The recalibrated slope should be checked in pre-registration and fixed.

10. **MINOR — `mt` and `virtual` implementation.**
    - `mt`: setting the qpos of a free-joint ball each tick leaves its qvel and angular velocity stale. Use zeroed velocities, or a mocap/position-only body. The ball must be displaced relative to the current camera pose, not the fixed Q_POSE eye. The metric must score against the unmoved ball.
    - `virtual`: mutating m.cam_quat also changes fk(), so e in `virtual` includes the rotation. The `none` path must restore cam_quat.
    - The `mt` vs `sin` difference is small for this encoder: it is background motion only, and the encoder uses only green contrast. Treat it as a sanity check, not a mechanism test.

11. **MINOR — pilot degrees of freedom.**
    - R3 is degenerate: with FA = 0 the 95th percentile of |omega| in N trials is 0, so omega_on = 0.05 by the floor. That equals the latency threshold, so gating turns off exactly at the first decision.
    - The gated ramp spec ("phase theta_s = 0") is vague.
    - R1 (the rho50 logistic) is fit on n = 60 binary outcomes and can be off by several cm against a half-width of 7 cm. The jvel generator for 6 s needs a new W0 and window specification. R2 has a dof in the formula (see #7).
    - Fix: state omega_on = 0.05 a priori, fully specify the ramp, and fix the logistic form.

12. **MINOR — budget and registry.**
    - Stage 0 found rendering GL-bound at about 240 frames/s regardless of workers (PROTOCOL §13). 41 trials x 600 frames = 24,600 frames per unit is about 100 s per unit regardless of workers.
    - That gives about 1.7 h for the pilot and 5.7 h (n = 200) to 11 h (n = 400) for the confirm. The §12 estimate assumes a 4x speedup. V5 measured 1.46 s per 300-tick trial single-process.
    - Seeds 9 111-9 119 xxx: grep over flymind/ and bio2/ finds only STAGE1_DESIGN.md. There is no collision with the F1 SEED_REGISTRY (9 101-9 109) or the program_v5v41 registry (8 4xx-8 7xx and listed RNG seeds). The Stage 1 pools are not yet in SEED_REGISTRY.md; append them before any run.
    - Pixel noise default_rng([u,1]) for T = 600: the first 300 frames equal the Stage 0 stream for the same u, which is harmless with fresh units.

## Can Stage 1 answer its question?
Yes, if #3, #4 and #5 are fixed. As written, the primary metric hides the cost of motion, and the amplitude rule couples stimulus strength to the weakness of the target. Then "useful vs uncontrolled" reduces to definitions rather than data.
