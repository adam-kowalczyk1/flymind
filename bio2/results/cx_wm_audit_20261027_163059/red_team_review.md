# Red-team review (read-only; quick pure-Python checks over raw/pilot_*.jsonl and raw/openloop_memory_probe.json)

Notation: e_on = e_onset_deg, dBall/dAim = ball/aim azimuth change over the occlusion (from *_reappear_deg - *_onset_deg), n = 30 seeds.
Identity used throughout (holds exactly in the records): e_reappear = e_on + dBall - dAim.

## 1. Strongest reason the main conclusion may be wrong
"PROTOCOL INVALID" over-reads a result the protocol *did* resolve. The endpoint has clear dynamic range: Kalman-PD 5.86 deg vs freeze 12.85 (context contrast -8.72, CI -9.30..-8.13), so it discriminates prediction from non-prediction. The pre-specified rules gave determinate answers: R2 fails (NI-2 upper 9.14 vs 5) and stats_plan §7 says that outcome is "negative or inconclusive", not "invalid". The NI-2 failure is not explained by the BIO onset deficit: regressing D(Hybrid-Kalman) on Hybrid e_on gives D = 7.87 at e_on = 0 (slope -0.18). Declaring the *protocol* invalid after a pre-specified negative risks shielding the hypothesis. The defensible weaker claim is: the closed-loop endpoint cannot support a *static*-memory test (NI-1, R5), but NI-2 is a genuine negative for this readout.

## 2. Most important confound
Fixed-direction target motion x unconverged, family-dependent occlusion onset.
- Occlusion starts at 0.5 s mid-acquisition. aim_onset: LastObs 11.21, Kalman 11.79, BIO-Static 8.62 vs ball 11.83. e_on: BIO +3.21 +/- 4.29 vs LastObs +0.62 +/- 1.21 (SD 3.5x larger).
- All 30 scenes sweep the same way (vy in [-0.120,-0.091]), so a positive e_on partially cancels the drift for any "hold" arm. The BIO-Freeze vs LastObs-Freeze difference (10.27 vs 12.85 = 2.58) equals the e_on difference (3.21-0.62 = 2.59) to rounding: it is a tracker-lag artefact, not memory.
- Mirroring the sweep direction (e_on + dBall -> e_on - dBall): BIO freeze 16.69 vs LastObs freeze 14.10; the sign of the "freeze beats memory" effect flips.
- Stratifying freeze-BIO (|e_Static| - |e_Freeze|) by e_on: e_on <= 0 (n=8): +0.02; 3-6 deg (n=9): +6.9; >6 deg (n=9): +8.7. The "memory-driven commands are worse than freezing" result (+4.80) lives entirely in seeds where the arm was behind at onset, and finishing that correction is what a *correct* static memory does.
- Added engineered confound: the BIO readout swaps (off, slope) -> (off_mem, slope_mem) on the binary `seen` flag (Agent B #5, exp:368-384), i.e. the controller is told when it is blind. The DN filters (tau 0.1/0.4 s) also carry visible-phase momentum into the occlusion, so part of BIO-Static's dAim = +4.79 may be filter ringing. Not separable with current logs (arm velocity at onset not recorded).

## 3. Could a non-biological controller reproduce the effect?
Yes, for every headline result. LastObs-PD *is* one: NI-1 D = +0.49. Analytic freeze (|e_on + dBall|) reproduces the freeze arms exactly. Both reflect |e| ~ |dBall| = 13.48 +/- 1.2 regardless of controller. For the open-loop probe, a leaky/perfect scalar integrator fed `w_base` through the same `u_for` lookup would give persistence plus self-motion update; no such comparator was run, so "bump persists and integrates self-rotation" (f) has no non-neural reference.
Also note (f)'s self-motion claim is misdescribed. From raw/openloop_memory_probe.json, slope of err on w: intact static -18.2 +/- 6.7 deg per rad/s at t=1 (NoSelf +59.8; perfect = 0). Err = (1-g)*57.3*w*t gives g ~ 1.32 (also 1.37 at 0.5 s, 1.34 at 2 s): the PEN lookup *over*-compensates by ~30%, not "70% partial"/under-compensation. That fits `u_for` being an engineered inverse of a measured curve, not an emergent integrator.

## 4. Does BIO-Shuffle isolate connectivity organization?
No. It is a dead network: EPG 0 Hz, coherence 0.00 at every t (probe), slope_mem = [0,0], visual slope ~1.6 vs 15.9 Hz/rad (preflight §4), j_ctrl = 0 in 30/30 trials, e_on SD 6.56 (largest) and cue-seen min 16/50. Its |e| 10.96 is just freeze (analytic freeze for e_on ~ +2.8). It breaks visual steering, readout calibration and the ring simultaneously, so no inference about *organization* is possible. Better: (a) graded-fraction shuffles (dose-response) with global gain re-trimmed to match intact firing rate and bump coherence; (b) phase-rotation of PEN/PFL3 offsets only; (c) a state-reset ablation (clamp ring to baseline at onset, visible phase untouched). BIO-NoSelf is not a no-memory control either: it keeps a persistent bump (coherence 0.8, corr(cue,bump) 0.87-0.96) and moves *more* during occlusion (dAim +6.62).

## 5. What would falsify the working-memory hypothesis; has it occurred?
Hypothesis must be split.
- H-persist (bearing-selective activity survives occlusion): falsified by coherence collapse or cue-bump decorrelation. NOT falsified: corr(cue, bump) at w=0 = 0.95/0.92/0.89/0.81 at 0.25/0.5/1/2 s, slope ~1.1.
- H-accurate-and-useful (bump supports action like a static hold): falsified if, on a ball-motion-free endpoint, it cannot match a trivial hold. Computed r = dAim - e_on (ideal static memory): BIO-Static mean|r| 6.79, SD 7.97 vs LastObs 1.10, SD 0.21; paired |r| difference +5.69 +/- 4.30 (SD). Closed-loop internal drift (bump_reappear - (bump_onset - dAim)): mean|.| 12.0, SD 14.8. Open-loop 1-s bias +11 deg and SD 13.7, with 8.9 SD already at 0.25 s (so mostly offset/readout noise, not diffusion; single 10-ms spike-window readout, Agent B #8). This is a post hoc but unconfounded-by-ball-motion negative on accuracy.
- H-self-motion-integration: g ~ 1.3 +/- 0.12 (above); Static vs NoSelf on |r|: -2.3 +/- 1.4 SE, not distinguishable.
The pre-registered tests (R4, R5) could *not* have been passed by an ideal memory (R5: perfect static memory gives |e| = 13.5 vs freeze 10.3 here), so their failure is not a falsification. No prespecified falsifier existed for the open-loop probe either.

## 6. Best experiment: persistent state vs externally maintained estimate
Causal perturbation of the ring during occlusion, with everything external held fixed: (i) inject a brief current pulse that shifts the bump by +/-30 deg at mid-occlusion and measure whether the motor command shifts (state-dependent) or is overridden (external estimate); (ii) clamp/reset the ring at onset while leaving w_base and `seen` intact; (iii) in Hybrid, feed the ring a deliberately wrong tv while the external Kalman state stays correct and test which one the command follows (partial regression of command on bump vs external estimate with independent injected noise on each). Pair with a stationary target, long pre-convergence, and a single readout with no `seen` switch.

## 7. Additional controls required before a competition demo
1. Oracle and Null references plus a matched non-neural memory module (scalar leaky integrator / EKF on the same noisy cue, same `w_base`, no `aim_az`).
2. Equalized visible phase: identical tracker for all families, swap only the memory module; or condition/ANCOVA on e_on. Occlusion after convergence (>= 1.5 s), arm velocity at onset logged.
3. Stationary-target and direction/speed-randomised conditions (perfect static memory -> ~0 error, freeze -> e_on).
4. Information parity: baselines currently get absolute heading (`aim_az`), BIO gets rate (Agent B #4).
5. A valid structural ablation (Q4) and a no-`seen`-switch readout.
6. Symmetric baseline tuning (none tuned; Kalman R unmatched).
7. Prespecified numeric falsifiers for open-loop accuracy/gain, with a non-neural integrator as comparator.

## 8. PROTOCOL INVALID vs PILOT INCONCLUSIVE
Neither is exact. Integrity gate passed (240/240, deterministic, no leakage), NI-2 is determinately negative under the plan, and invalidity is limited to NI-1/R5/R4 as tests of *static* memory. Recommended status: "STOP - PILOT NEGATIVE ON NI-2 (prespecified); NI-1/R4/R5 UNINFORMATIVE BY DESIGN; WM NOT TESTED". If one of the three given must be chosen, choose PILOT INCONCLUSIVE; INVALID overstates (Kalman vs freeze shows the task works) and relabels a prespecified negative.

## 9. Analysis errors and possible post-hoc rescue
- NI-1 "nominally noninferior" (t upper 2.97; my one-sided 95% bootstrap upper 2.91): right on the margin, on a folded heavy-tailed |e| with 10/30 CONTROL_FAILURE, and the conclusion is meaningless for the reason in §2/§3. Do not report as supportive.
- R3 "required N ~ 60+" (progress_log Cycle 4) is wrong: stats_plan §6 formula assumes a true difference of 0. For NI-2 mean D = 7.29 > margin 3, so no N reaches noninferiority. For NI-1 with s = 7.98 x 1.28 = 10.2, delta 3, D = 0.49, alpha 0.0125 a z-approximation gives ~155 pairs. No script computes R3.
- Memory-fidelity table (reruns_and_memory_fidelity.txt): the Hybrid row compares a *moving* ring with an ideal *static* memory (mean -8.57); inappropriate. mem_err includes cue-to-bump encoding error at onset (bump_onset - true: mean|.| 5.1, SD 5.8, my computation) and single-window readout noise, so "14 deg of memory error" overstates drift; the 14.07 vs 14.3 closed/open "agreement" is not independent validation.
- Memory-gain and freeze contrasts (A6, R5) are geometry-signed (§2); they should have been reported on |dAim - e_on| or adjusted for e_on.
- Promised but absent in analysis.md: BCa intervals (percentile only), Holm-adjusted p-values, seed-level scatter, the worst-case-imputation/degenerate-excluded sensitivity analyses, frac(D<3) in the table.
- CONTROL_FAILURE inclusion matches the plan (not an error); 10-15/30 BIO "failures" are drift-driven given the 13.5 deg floor.
- Amendments: §9 states A1 was "motivated by code inspection, not comparative outcomes", yet preflight_audit §5 cites the seed-100 freeze results (LastObs 14.8 vs 12.9, BIO-Static 14.0 vs 6.8) as grounds, and seed 100 is a pilot seed (records bit-identical, so the preview was reused data). A2 (dropping Shuffle from R4) is permissive but harmless. The open-loop probe was added after the construct-validity failure with no acceptance criteria, and its "qualitative WM criteria met" is then asserted. The "PROTOCOL INVALID" label is itself the most important post-hoc reframing.

---
# PI responses (evidence: analysis/redteam_verification.txt, analysis/supplementary_analysis.txt)

All quantitative red-team claims were re-computed by the PI and confirmed: Δball identical across arms; freeze-arm gap
2.58 = onset gap 2.59; open-loop self-motion gain g = 1.32 (SD 0.79 across seed×angle) — over-compensation;
freeze-vs-BIO-Static effect +0.02 when e_onset ≤ 0 (n = 8) vs +7.80 when e_onset > 3 (n = 18); NI-2 D at equal onset
+7.65 (red team +7.87 with a slightly different regressor).

1. *"PROTOCOL INVALID over-reads; NI-2 is a determinate negative."* ACCEPTED IN PART. NI-2 is a prespecified, clean
   negative (D = +7.29, BCa [+5.22, +9.42]; +7.65 adjusted for onset) and the final report states it as such, not as an
   artefact. The status remains PROTOCOL INVALID because the status question is readiness for a held-out benchmark of
   *this protocol*, whose stated purpose is a test of CX working memory: R4, R5 and NI-1 could not have been passed by an
   ideal static memory (red team §5), BIO-Shuffle is a dead network, and t_reacquire is censored by design. No outcome of
   this design could have been conclusive about working memory, which is the operational meaning of "invalid" here;
   "inconclusive" would wrongly suggest that more seeds could help. Dissent preserved: the red team prefers PILOT
   INCONCLUSIVE. To avoid shielding the hypothesis, the report states explicitly that the invalidity finding does NOT
   rescue BIO-Hybrid.
2. *Confound: fixed sweep direction × family-dependent onset error.* ACCEPTED. The "memory-driven commands are worse than
   freezing" statement in progress_log cycle 4 is withdrawn as a mechanism claim: it is produced by sign correlation between
   onset lag and sweep direction. Within-family freeze contrasts share the visible phase but not the geometry; they are
   reported as uninformative by design.
3. *Non-biological reproduction.* ACCEPTED. LastObs-PD reproduces BIO-Static on the primary endpoint; analytic freeze
   reproduces the freeze arms; no non-neural integrator comparator was run for the open-loop probe (limitation).
4. *Shuffle = dead network.* ACCEPTED (agrees with preflight_audit §4).
5. *Falsification split.* ACCEPTED. H-persist: not falsified (coherence 0.80 for 2 s, bump follows cue). H-accurate:
   negative on the POST HOC ball-motion-free endpoint |dAim − e_onset|: BIO-Static 6.79° vs LastObs 1.10°
   (+5.69 [+4.09, +7.30]), and BIO-Static is not better than its own freeze arm on this endpoint (6.79 vs 4.52 = |e_onset|).
   Labelled post hoc. H-self-motion: PEN path present but over-compensates (g ≈ 1.3) and Static vs NoSelf on |r| is
   −2.32 [−5.25, +0.60] — not distinguishable.
6. *Perturbation experiment.* ACCEPTED as the top recommendation.
7. *Controls list.* ACCEPTED; carried into the final report.
8. *Status.* See 1.
9. *Analysis errors.* ACCEPTED: (a) "required N ~60+" withdrawn — with mean D = 7.29 > margin no N achieves NI-2;
   (b) memory-fidelity Hybrid row withdrawn (compares a moving ring with a static ideal); the 14° figure includes ~5.1°
   encoding error at onset (supplementary_analysis.txt), so it overstates drift; closed/open agreement is not independent
   validation; (c) BCa and Holm now added (supplementary_analysis.txt); worst-case imputation is moot (0 technical
   failures, 0 missing); degenerate-excluded sensitivity = Shuffle excluded throughout; (d) disclosure in stats_plan §9
   corrected: the seed-100 freeze outcomes had been seen and are cited in preflight_audit §5; A1 cannot be called purely
   mechanism-motivated. The open-loop probe had no prespecified acceptance criteria and is reported as exploratory.
