# Code/protocol audit (Agent B) - test_cx_working_memory_vs_kalman.py

Line numbers (exp:) refer to the baseline copy `archive/test_cx_working_memory_vs_kalman.py`. Nothing modified; only `mj_forward` probes and Brain construction were run (no stepping).

## A. Causal path and classification

| Stage | Where | Class |
|---|---|---|
| Camera frame (MuJoCo render) | exp:480-481 | engineered (simulator) |
| FlyRetinaFilter: R-channel drop, 32x24 blur/subsample, temporal high-pass tau 0.1 s -> L1/L2 | retina:21-38 | biologically-inspired model input (constants hand-set) |
| Efference-copy shift of retinal "slow" state by dpsi (from joint encoder) | vision:52-54, exp:475,482 | engineered + biologically-inspired |
| Blob candidates (thresholds, aspect, bipolarity) | vision:60-79 | hand-tuned detector (LC10-like by analogy only) |
| Ray x table-plane intersection at z=BALL_R, azimuth minus aim_az | exp:485-498 | engineered geometry; uses exact camera pose, known ball radius/table height, exact forward kinematics |
| Software blanking | exp:501-502 | experimental manipulation |
| EPG cue current (Gaussian, cue_amp 12, sigma 0.4) | brain:136-138 | model input (not connectome) |
| CX weights: profile-averaged synapse counts, J0_CX, G_INH, G_DD, b_a[cx]=0 | brain:32-34,77-116 | connectome-derived counts passed through hand-tuned constants; ring structure is synthetic interpolation |
| PEN rotation u_for(-w_base); table from calibrate_ring | exp:346, brain:190-214,255-258 | hand-tuned calibration (lookup of measured bump velocity); w_base = joint velocity (proprioception) |
| PFL3 goal=0 (goal_amp 6, 45 deg phase) | brain:143-145 | model input (Westeinde-style), not in data subset |
| PFL3 -> DNa02 crossed | brain:111-113 | connectome counts for DNa02; DNa01 is a model copy (dna01_frac=1) |
| DN rate L-R, filters tau 0.10/0.40 | exp:359-365 | model readout, hand-set taus |
| Linear decode (off, slope) vs (off_mem, slope_mem); x2.5 gain; clip 0.6 | exp:367-388 | hand-tuned calibration + classical P control (omega ~ 2.5 x decoded angle) |
| apply_base_velocity (windup 0.02, ctrl -= w dt) | exp:98-109 | classical servo layer |
| MuJoCo, 10 x 1 ms | exp:525-526 | simulator |

Sign chain verified: +omega lowers qpos[0]; `mj_forward` shows qpos0-0.1 raises aim azimuth 5.4->10.4 deg, so +omega = left; w_base (exp:477) and dpsi (exp:475) are consistent with agent.py:98,102.

## B. Findings

**1. [CRITICAL] Primary endpoint cannot discriminate working memory from "stay still"; a do-nothing controller is competitive.**
Scene is nearly identical across seeds (y0 in [0.12,0.16], vy in [-0.12,-0.09] m/s, exp:419-421); initial aim azimuth is 5.43 deg (probe), ball starts at ~17.7 deg and sweeps monotonically right at ~13 deg/s. Analytic e_reappear of a controller that never commands motion (aim fixed at 5.43 deg), seeds 0-39: t_occ 0.5/1.0/1.5/2.0 -> mean |e| = 1.6/7.8/14.5/21.1 deg. Perfect zero-order-hold at t=0.5 s gives mean -6.7/-13.6/-20.3/-26.9 deg. Preflight seed 100 (t_occ 1.0): LastObs -14.8, BIO-Static -14.0, Kalman -6.0, null -6.5: Kalman equals "do nothing"; ZOH-type controllers are worse. e_reappear measures how far the ball moved during occlusion minus how far the arm moved; Static/Shuffle/LastObs are indistinguishable by design (all hold the last world bearing).
Fix: add Null (omega=0) and Oracle references; randomize target direction/speed/start side; start occlusion after convergence (>=1.5 s); report error relative to null and ZOH.

**2. [CRITICAL] BIO-Shuffle (and every degenerate-calibration trial) is a zero-command null control, not a "structure ablation".**
make_within_projection_shuffled_brain (exp:241-271) does preserve multisets, signs and the sparsity pattern in all 64 CX x CX blocks (checked numerically, seed 100; blocks are ~98-100% dense, so sparsity carries no ring structure). Shuffling is applied only to CX_GROUPS pairs (exp:60,257-258); PFL3->DNa02/01 (brain:111-113) are untouched, as are all non-CX projections. Per-postsynaptic-neuron input balance is destroyed, silencing EPG -> bump() returns angle(0)=0 (brain:176) -> X is the zero column in calibrate_steer lstsq (brain:246-249) -> minimum-norm slope_mem = [0,0] exactly, offset_mem = mean(Y). Then exp:372-378 returns 0.0 whenever not seen. Consequence: memory-phase omega is exactly 0, j_ctrl = 0 exactly, the aim holds. Combined with PI's finding that the shuffled visual slope is ~1.6 vs ~15.9 Hz/rad, tracking itself is broken. calibrate_ring on a silent ring yields a flat v(u) table passed to np.interp with non-increasing xp (brain:212,258): undefined, not checked.
Fix: report Shuffle as "ring-destroyed -> zero command"; add a ring-health gate (bump rate/coherence, monotonic v(u), vis slope within 50% of intact) that is logged per trial; for a real ablation shuffle only phase-dependence (rotate/permute weights per post-neuron preserving row sums) and re-trim.

**3. [MAJOR] Status logic: DEGENERATE_CALIBRATION is sticky, trial data are still recorded, and filter semantics are undefined.**
Set at exp:466-469; CONTROL_FAILURE requires status=="SUCCESS" (exp:536) so it is never overwritten by SUCCESS/CONTROL_FAILURE, but it IS overwritten by TECHNICAL_FAILURE (exp:513, 550). The 556 guard preserves it when reappearance not reached. e_reappear/e_ring/j_ctrl/t_reacquire are returned regardless (exp:560-576), so with zero command the degenerate trial reports a plausible, "SUCCESS-like" |e| (null/ZOH-level, see #1) and j_ctrl=0 (best possible "energy"). A degenerate trial can look misleadingly good on j_ctrl and decent on e. check_calibration_slope (exp:80-92) only tests |slope|<1e-6 absolute (Hz/rad): tiny-but-nonzero slopes give huge gain (division at exp:387, then clip +-0.6 -> bang-bang), and a negative slope (positive feedback) passes. Averaging per-channel quotients (exp:387) lets the weaker channel dominate.
Fix: relative threshold (|slope_mem| >= 0.25|slope|) plus sign check; NaN metrics for non-SUCCESS statuses; keep such trials in the denominator (worst-case imputation).

**4. [MAJOR] Information access is not equivalent across controllers.**
No true ball state reaches any controller: ball_az/true_rel_az (exp:488-489) are used only at exp:530,532,542 (metrics). Retina keeps processing the true ball under blanking (cue masked only at exp:502), fine. But: LastObs/Kalman/Hybrid receive absolute heading aim_az (exact forward kinematics, exp:487,507-509) and compute theta_w = cue + aim_az (exp:202,229); BIO-Static/Shuffle receive only velocity w_base = -qvel[0] and must integrate through a noisy, calibrated SNN ring. Same exact, noise-free, zero-latency proprioception for all, but the baselines get position, BIO gets rate. Hybrid additionally receives tv from an exact-kinematics world-frame polyfit (exp:332-338).
Fix: give baselines the same integrated w_base (dead-reckoned heading) or give BIO the aim_az; document; add encoder noise/latency equally.

**5. [MAJOR] "Hybrid mirrors agent.py" is false; memory is mostly the external polyfit.**
exp:342 `(self.tv if seen else self.tv)` is a no-op ternary (frozen tv during occlusion). The SNN merely integrates a known derivative tv - w_base; velocity extrapolation is np.polyfit over 0.6 s of world bearings (exp:332-338), tv clipped +-1, frozen at the last value; the ring adds only an integrator with calibration error. Divergences from agent.py: W_MAX 0.6 (exp:47, comment says "agent.py: W_MAX" but agent.py:43 is 1.0); rest=False always (exp:352 vs agent.py:145 rest=not hunting); no ACQ_N acquisition, no +-25 deg attention gate (agent.py:114-130) so strongest candidate is accepted blindly (exp:498); no LOCK/hunting latch and no dn_f reset to offset (agent.py:159-168); no HS/looming/DNp01/touch inputs; tv needs >=5 samples (exp:336) vs none in agent.py:137; off/slope switch instantaneously at visibility transitions (exp:368-384), creating command steps at onset/offset.
Fix: relabel as "agent-like", or port the gating; log the fraction of omega variance attributable to tv.

**6. [MAJOR] t_reacquire is censored by design, biased, and ill-defined.**
exp:541-547: reports t_sim of the 10th consecutive in-band step, i.e. window end (onset + 0.09 s, +~0.01 float shift => floor ~0.10 s), not onset. If already in-band at reappearance the value is ~0.10, never 0. The 5 deg band (|true_rel|<=5) is at/below the steady ramp-following error of the P loop: omega_ball/kp = 0.22/2.5 ~ 5 deg (Kalman: 0.22/2.8 = 4.5 deg; its kd*(omega_w - w_base) vanishes in steady tracking) plus servo lag => PI's 6-9 deg observation; null in most trials. Remaining horizon = t_total - t_reappear, only 1.0 s at t_occ=2.0 (exp:452-453); None is not distinguished from "never".
Fix: report onset time and right-censored survival (censor at horizon), band relative to steady-state error (e.g. 10 deg) or use time-to-|e|<band at first crossing.

**7. [MAJOR] Float time accumulation shifts occlusion/recording by one step.**
d.time is accumulated by mj_step; python replication matches the observed t_sim_final=3.4999999999997256. At k=150 t=1.4999999999999456 < 1.5, so is_occluded stays true (exp:501) and exp:529 fires at k=151 (t=1.51); same for 2.0->2.01 and 2.5->2.51 (t_occ=0.5 is exact). Actual occlusion = 101 frames (1.01 s) for t_occ>=1.0 vs 50 for 0.5; unmasking and recording are consistent with each other, but t_occ labels are off by 10 ms, and reacquire (exp:545) is shifted by 10 ms.
Fix: use integer step indices (k >= k_mask, k < k_reappear) with k_reappear = round((t_mask+t_occ)/dt).

**8. [MAJOR] e_ring is contaminated and noisy.**
b_ang (exp:353) is read in the same step where the first cue is re-injected (cue_rel unmasked at exp:502, injected brain:136-138), and from a single 10-ms spike window (brain:171-176). It then no longer measures the memory ring just before reappearance. Sign: true_rel - bump (both +left, aim-relative). BIO-only, so not paired with baselines; for Static it equals ~ -(ball displacement), not "ring accuracy".
Fix: record bump from the last masked step (k-1) averaged over 5 steps.

**9. [MAJOR] Status thresholds interact with t_occ: survivor bias.**
CONTROL_FAILURE (|e|>=20 deg, exp:536) triggers for 55% of ZOH trials at t_occ=1.5 and 100% at 2.0 (see #1). Analysis that keeps only SUCCESS drops precisely the memory-less controllers, destroying pairing (the pairing set is per seed x controller).
Fix: never filter on status for the endpoint; use |e| capped/winsorized, include failures.

**10. [MAJOR] Never-acquired target is undetected.**
No check that a cue was seen before t_mask_start. LastObs returns 0.0 (exp:205-206), Kalman 0.0 (exp:231-232), but BIO runs on spontaneous ring activity with rest=False (exp:352; agent.py comment on spontaneous bump). Retina is a temporal high-pass (retina:33-38): a well-tracked ball stops moving in the image and fades, so dropouts occur in the "visible" phase exactly for good trackers; BIO treats dropouts as memory with slope_mem decode, LastObs as ZOH.
Fix: log `n_pre_detect` and `acquired_before_occ`; exclude/flag trials with <15 detections in [0,0.5).

**11. [MINOR] Baseline tuning and PD signs.**
Gains are hand-set and untuned on seeds_tune (exp:434-437,386); Kalman R (sigma ~4 deg) is not matched to measured vision noise, so a fair NI claim needs a tuned baseline. PD signs are correct: `kd*(omega_target - w_base)` (exp:234) and `-kd*w_base` (exp:208) are the error-derivative term (d err/dt = omega_w - w_base). In steady tracking the term vanishes (no velocity feedforward); Kalman's benefit is position extrapolation only.

**13. [MINOR] Initial conditions, pairing, runtime.**
Same seed -> same scene for all controllers (exp:418-421). CLI --t-total default 2.5 (exp:778) vs CFG 3.5 (exp:57): with defaults t_occ>=1.5 ends before reappearance -> TECHNICAL_FAILURE (exp:556). calib_brain is never passed (exp:439-445), so each BIO trial rebuilds and recalibrates Brain(seed) (~11.5 s vs ~2.3 s per baseline trial; ~80 min of identical recomputation for 40 seeds x 4 t_occ x 3 modes). Pairing survives because construction is deterministic. Fix: calibrate once per seed and `copy.deepcopy` (copies net.rng; net.reset does not reset rng, brain:124-126).

**14. [MINOR] RNG and reproducibility.**
Scene rng (exp:418), Brain net.rng (brain:104) and shuffle rng (exp:253) share one integer seed, hence identical bitstreams (y0/vy correlate with the first SNN noise vector); use SeedSequence.spawn. Brain noise is also consumed by calibration. MuJoCo is deterministic per machine/version, but the GL render path (scene2:70-79) and hard detector thresholds (vision:62-72) may diverge across GPUs. Record env (mujoco 3.17.0, numpy 2.5.4, M1 Max).

**15. [MINOR] Metrics and units.**
e_reappear_deg: signed, true bearing minus aim, +left, state at the recording step (comment "exactly t_reappear" is wrong, #7); ball always sweeps right so signed means are sign-biased. j_ctrl = sum omega_cmd^2 dt over masked steps, rad^2/s, commanded not measured; minimised by doing nothing (LastObs 0.0018 because aim already sat on the last bearing). Renderer leaks if Brain/ctl construction throws between exp:429 and 471.

**16. [MINOR] Stats.** exp:755-763 is a z-approximation; "Holm" alpha=0.0125 (exp:788) is Bonferroni; NI stats use alpha 0.05 regardless. A 3 deg margin is small relative to the regime differences in #1; pre-register it against the null reference.

**17. [MAJOR] Sibling scripts are inconsistent with the main script.**
- test_openloop_cx.py:151,157,183,189,223 and test_cx_asymmetry_ablation.py:150,160 re-seed `b.net.rng`; the main script never does. The openloop "determinism test" (172-200) is tautological.
- Siblings run uncalibrated Brain with u=0.0 (openloop:75,82; ablation:167); the main script runs at u_for(~0) trim and subtracts `offset` via calibrate_steer, so Exp 1 asymmetries are not Exp 2's operating point.
- test_cx_asymmetry_ablation.py:443-453 print pre-written verdicts ("BRAK WPLYWU", "GLOWNA PRZYCZYNA ASYMETRII") unconditionally, not computed from data.
- ablation:81-84 "symmetric" grid has k=-23..22; ablation:125-126 assumes one DNa02 neuron per side.
Fix: derive text from computed values; state operating point.
