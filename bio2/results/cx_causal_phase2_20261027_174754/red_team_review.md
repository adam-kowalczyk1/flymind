# Red-team review: phase-2 CX causal-memory protocol

Analyses: pure Python on `dev/*.jsonl`, no simulation. dev3 = seeds 210-229. `T:` = `bio2/test_cx_causal_memory.py`.

## 1. What would show causal steering, and does Q1 do it?

A convincing result needs (i) an intervention whose motor consequence is not fixed by the readout code, (ii) a dose-response, and (iii) persistence-dependence: the effect should vanish if the ring is reset right after the pulse.

Q1 as written does none of these.
- The motor law is `omega = K * th_hat` (T:258) and `th_hat` is the bump angle (T:238). Q1 verifies only that the pulse moves the bump and that the arm follows K·bump. `hypotheses_and_thresholds.md` §5 concedes this.
- The Scalar-Shift positive control gives S = 27.3, against 17.7 (dev1) and 24.4 (dev2) for the CX. A trivially causal scalar passes better than the network, so Q1 cannot tell a ring attractor from any read-out variable.
- The pulse overwrites the stored angle (`cue_amp` = 12 mV, 200 ms). Any cue-driven ring steers during those 200 ms. No Pulse-into-Shuffle20 or pulse-then-reset arm exists.
- CX-DN (PFL3→DNa02 pathway) is the only arm with non-identity transmission. It has no pulse or sham arm.
- Falsifier (a) is nearly unfalsifiable: if the manipulation check passes, S > 5° follows from the readout; if it fails, the verdict is "no manipulation".

## 2. Persistent but behaviourally useless: do dev data already show it?

Largely yes.
- Coherence is 0.75-0.83 with 0/40 gate failures (dev3), yet Q2 is unresolved: dev1 -2.9 [-11.3, +5.4], dev2 +0.9 [-8.4, +10.1], dev3 -3.06 [-7.0, +0.9].
- Little target content is retained. Within each Δ sign, the correction (e_end − e_post) is uncorrelated with the onset bearing e0: dev3 r = -0.10 (Δ = -20) and +0.11 (Δ = +20). The ideal slope is -0.9; observed -0.19 and +0.43.
- Estimate error at reappearance is 24.5° against 17.3° for a never-updated estimate.
- Caveat: e0 has SD only 4.9° (range -7 to +6.5) against about 14.5° estimate-error SD, so even a perfect memory would reach r ≈ 0.3. That is itself a design defect: the remembered quantity is almost constant.
- A sign-independent bias that `hypotheses_and_thresholds.md` §0.2 misses: CX-Bump signed e_end is about -10° in both Δ conditions. dev3 gives -9.7 (seed-level t = -3.8), dev1 -9.5, dev2 -15.8. Averaging ±Δ does not cancel it. Removing a constant -9.7° would cut dev3 |e| from 14.3 to 11.5. The design doc lists a "bump-offset trim", but the code has none. The Q2 sign is hostage to it.

## 3. Could a frozen command or simple integrator reproduce the effects?

Yes, and they do better.
- Frozen-command replay: replace each CX trial's correction by the leave-one-out mean of the other trials with the same Δ sign, then recompute |e_end|.

  Actual CX versus frozen replay versus a constant ignoring sign: dev1 14.4 / 9.5 / 19.1°; dev3 14.3 / 9.7 / 17.9°; dev2 18.2 / 15.8 / 20.6°.
  A command that knows only the sign of the self-motion beats the closed-loop CX. Trial-specific CX state is net noise (within-sign SD of the correction 9-21°, against e0 SD 4.9°).
- A cue-free integrator (θ̂0 = 0 minus ∫λw) would give |e_end| ≈ |e0| ≈ 4.7-5.7° by the closed-form algebra in `control_comparator_design.md` §4. That is about 9° better than the CX.
- Q4: NoSelf (|e| 31 in dev1) is worse than Freeze (17.3), because stale θ̂ keeps driving the arm. Q4's "benefit" is mostly harm avoided relative to a mis-specified comparator; any integrator reproduces it, even if the CX is no better than doing nothing. Use a gated NoSelf (ω = 0 after passive) or Freeze instead.

## 4. Does the pulse change only the intended variable? Is the sham adequate?

- In CX-Bump the motor path reads only bump angle and the coherence gate (T:238). PFL3 and DN filters are logged but do not drive the arm. EPG rate rises about 5 Hz in pulse and sham alike.
- The sham pins the ring at the last 10-ms bump sample (T:225-226) for 200 ms, with about 5° jitter, against ongoing PEN integration. It blocks self-motion integration and is not neutral.
- Sham minus Bump bump angle at 0.95 s: +4.5° (SD 7.4) in dev1, -2.5° (SD 10.2) in dev2. The sign flips. The e_end difference is -5.2 (SD 7.7) and +2.3 (SD 13.1), comparable to the Q1 effect.
- |ω| sits at w_max in 30-42% of CX-Bump memory steps and 60-72% in Pulse+30. S is compressed and Δ-dependent: 10.6 versus 24.7 (dev1), 20.2 versus 28.6 (dev2).

## 5. Scalar versus CX: matched information?

The raw streams match; real asymmetries remain.
- The Scalar takes the last cue sample (T:99-100). The CX integrates cue history through spiking dynamics (50-100 ms lag, 4-6° onset encoding error). Int-from-bump is designed but not implemented.
- Private CX calibrations exist: `calibrate_ring`/`calibrate_steer`, the dev-fitted λ_cx = 0.65 trim, and the coherence gate (the Scalar is ungated). The Scalar's λ_self = 1.105 is also dev-derived.
- The CX sees the cue during the visible phase but its output is unused there.
- `cue_rel` is noise-free exact geometry. "CX inferior to Scalar" mainly measures spiking noise (2.0 mV, a tuned constant).

## 6. Can the criteria reject the CX hypothesis?

- (a): effectively no (§1).
- (b) is testable but fragile.
  - The 3° threshold equals dev3's point estimate (-3.06). Support needs point ≤ -3 and upper bound < 0, which flips on sampling noise at true d ≈ -3.
  - Rejection needs a CI lower bound > -3; at N ≤ 100 the half-width is about 1.7°, so true d from -3 to -1 lands on "not demonstrated".
- (b) compares against a strawman. Freeze equals the realised passive (17.31° at seed level, SD 0.01), so Q2 is a one-sample test of CX |e| against a design constant. CX |e| stays near 14° whatever the passive size, so "useful" holds iff passive > about 17-20°. The verdict is set by the chosen 20° rotation and by bump drift.
- CX-Reset and CX-Shuffle20 equal Freeze by construction (SD 0.00; T:238 gate), so they add no independent evidence.
- The convergence rule fires at 3.81-3.99 °/s in 20/20 logged trials, so 4 °/s is a first-crossing time, not convergence. The arm still moves at 8.3°/s on average at onset. There is no between-arm bias, but "converged" is a mislabel.
- The g escape hatch voids (b) and (c) if g is outside [0.75, 1.25]. g is measured at passive speed (0.58 rad/s), but the memory phase integrates at other speeds under a nonlinear `u_for` map.

## 7. Claims that remain model-level

All fly-level claims:
- the bump as a target bearing (flies encode heading/goal);
- the tuned noise and `J0` constants (`brain.py:32`) that set drift. About 14° in 0.6 s is roughly 330 deg²/s, against Noorman's fly drift ≈ 0 and Vafidis's 24.5, so a negative Q2 may be an artefact of this parameterisation;
- a single connectome-derived network (seeds vary only noise, scene and calibration);
- the 200-ms cue-like pulse (Kim 2017: about 1 s optogenetic), DNa01 as a model copy, PFL3 goal = 0, the λ trims, K = 2.5 and the noise-free `cue_rel`.

## 8. Other confounds

- The ball is teleported to rest (T:213) and is undetectable thereafter (scene probe: 0%), so "reappearance" never occurs physically. Both memories assume a stationary world, favouring the exact integrator.
- The passive rotation uses the same actuator path (T:254, ±0.58 rad/s near w_max). Memories see exact measured qvel. The whole utility test comes from the imposed rotation: without it Freeze is already near |e0| ≈ 4.7°.
- Common random numbers: `copy.deepcopy(brain0)` (T:150) and `Brain.reset()` (no RNG reseed) give every arm and both Δ of a seed one noise stream. Good for pairing, but ±Δ are not independent replicates (NoSelf drift is identical across ±Δ), and seed-level g SD (0.48) understates trial-level SD (0.67-0.86).
- λ tuning: dev1 (6 seeds) set λ_self and λ_cx; dev2 (4 seeds) gave g = 1.18 [0.37, 2.00], failing the acceptance interval, yet the freeze was declared; dev3 passed (0.992) against an interval written after dev2. A mild forking path, acceptable only with no further tuning.

## 9. Decision

**STOP — DESIGN STILL CONFOUNDED.** Implementation is not blocked, and the question becomes testable after changes. As written, the run would certify three outcomes already visible in dev: (a) true by readout identity, (b) "not demonstrated", (c) inferior. It would not show that CX state improves behaviour: Q1 is analytic, Q2 depends on the passive size and an untrimmed offset, Q4 uses a comparator worse than doing nothing, and e0 has almost no range.

Mandatory before the confirmation run:
1. Run the Q1 pulse through a non-identity readout (Pulse and Sham in CX-DN). Add Pulse-into-Shuffle20 and pulse-then-reset arms for persistence-dependence.
2. Widen the e0 range (stop the ball so that the onset bearing is ±15-25°, as `control_comparator_design.md` §4 recommends). Pre-register the within-Δ slope of correction on e0 as the memory-content test.
3. Add a cue-free integrator (θ̂0 = 0) and a Δ-conditioned replay or yoked-state control. Make them the primary Q2 comparators alongside Freeze.
4. Replace NoSelf with a gated version (ω = 0 after passive), or report Q4 against Freeze.
5. Add a dose-response over passive size (10, 20, 40°). Decouple the 3° threshold from the dev estimate. Report the -10° signed bias.
6. Add a drift-calibrated run (noise scaled to fly-range D of 0-25 deg²/s). Label every negative "this parameterisation".
7. Rename the onset rule "first crossing of 4 °/s" and show insensitivity at 3 and 5 °/s.

## Round 2 (revised design)

Method: pure Python on `dev/expA2_dev4_*.jsonl` and a runner diff against v1. No simulation.

### 1. Round-1 mandatory changes

1. **Non-identity pulse readout:** part adopted. CX-DN-Sham/Pulse±30 are primary. The pulse-into-Shuffle20 and pulse-then-reset arms (persistence-dependence) are missing.
2. **Wider e0, within-Δ slope:** part adopted. The jump widens e0, but the slope test is specified in a confounded form (§2).
3. **Cue-free integrator, replay control:** adopted/substituted. SelfOnly is co-primary. The replay control is analysis-only and not in §11.
4. **Gated NoSelf:** missing. Q4 still uses ungated NoSelf.
5. **Dose-response, 3° threshold, −10° bias:** substituted. Δ ∈ {−20, 0, +20}; the 3° no longer coincides with the dev estimate (dev4 point +13); signed bias is not in the report list.
6. **Drift-calibrated run:** not adopted, kept as a limitation. Acceptable only with a written label rule.
7. **Rename onset rule:** adopted. The 3/5 °/s sensitivity run is no longer mandatory, since the rule now only times the jump.

Mandatory for a 24-seed stage 1: the non-identity pulse (done), SelfOnly (done), and a within-Δ memory-content test (not done correctly). The rest matter only for stronger claims and must be stated as limits.

### 2. Defect in A2-4

A2-4 regresses the correction on the post-passive bearing **pooled over Δ**. That variance is mostly the imposed ±17° rotation. Dev4, slope (r):
- SelfOnly pooled: −0.69 (−0.86). It has no target memory and passes "slope ≤ −0.5, r ≤ −0.5".
- CX-Bump pooled: −0.71 (−0.55). The "borderline pass" is uninformative.
- Demeaned within Δ (my calculation): Scalar −0.82 (−0.96); CX-DN −0.51 (−0.23); CX-Bump −0.31 (−0.16); SelfOnly and Freeze 0.00 (r ≈ +0.4).

The CX retains little of the jumped bearing. **A2-4 must be redefined as within-Δ.** No new data are needed.

### 3. New confounds from the jump

- **e0 range is still narrow and bimodal.** e_onset: −19.1, −5.8, −8.8, +4.7, −5.0, +5.9. SD 9.2 (v1: 4.7), mean −4.7. corr(e_onset, jump) = 0.81, so e0 is mostly the jump sign. It is not the ±15–25° round 1 asked for.
- **Ghost at the old position.** The cue is not logged in the 0.2 s window. Indirectly, Scalar's last-cue error at onset is 0.9–4.7° (a ghost would give about 10–16°). The cue is correct at the last visible frame. A transient ghost inside the window is not excluded; log cue presence there.
- **Transient confound for the CX.**
  - Seeds 230 and 232 are still slewing at onset (|w_base| ≈ 0.4 rad/s). They have the largest CX onset errors: CX-DN +24.2°, CX-Bump +14.7°, against Scalar ≤ 4.7°.
  - Q2/Q3 at Δ = 0 therefore measure "encode a target that jumped 200 ms ago, then hold it", including bump settling lag.
  - The harm is not just an offset. CX-Bump at Δ = 0 has a signed mean of −21.4°. After leave-one-out offset removal |e| = 14.3°, still worse than Freeze (8.0). Zero-input drift reaches 24° in 0.6 s.
  - This is model diffusion (round 1 #6).

### 4. Is the DN pulse a non-identity test? Can A2 reject?

- **Q1 is a genuine but low-risk transmission test.**
  - Bump shifts of +19.7° / −24.4° map to DN-decoded shifts of +18.2° / −17.8°. Sham is +0.5°. The gain is about 0.7–0.9, so it is not identity.
  - It fails if PFL3→DN does not carry the ring, but a degenerate readout is classed TECHNICAL_FAILURE (§7) and a failed manipulation check means "no manipulation", so rejection routes are nearly closed. Q1 will almost surely pass.
  - It shows that a cue-like EPG current redirects DN-driven steering, not that stored content is necessary.
- **Q2 can reject, and with 24 seeds probably will.** Δ = 0 d = +13.2 (SD 16.9) gives a CI of about [+6, +20]. It cannot support "useful": a 3–5° benefit needs about 60–300 seeds.
- **Escape hatches still in force.**
  - The §3 g-gate ([0.75, 1.25]) makes (b) and (c) INCONCLUSIVE. A2 does not override it, g was not re-measured on dev4, and the jump alters onset dynamics. The Δ = 0 contrast has no self-motion demand and must be exempt.
  - §1 and §9 are stale ("bit-identical", seeds 300–339).
  - A2-6 says 12 arms but the command lists 14. CX-Reset and CX-Shuffle20 were never run with `--jump`.

### 5. Onset non-identity

Max 1.2e-5° in 2/216 trials, against an e_onset SD of 9°. This is immaterial and A2-5 (tolerance 1e-3°) covers it. The cause (renderer nondeterminism) is untested and must be stated as such.

### 6. Decision

**READY FOR SMALL-SCALE CAUSAL EXPERIMENT**, conditional on these text-only §11 amendments before seed 300 (runner hash unchanged):
1. Redefine A2-4 as within-Δ.
2. Exempt Δ = 0 from the g-gate, and report g.
3. Make the command and the arm list agree.
4. Report signed e_end and offset-removed |e|; demote Q4 to a comparison against Freeze.
5. Pre-register the frozen-mean replay and the cue-window log as secondary.

Scope: Q1 (transmission) is confirmatory. Q2 can reject "useful" but not establish it.

Limitations to state:
- one connectome network;
- model diffusion and tuned noise, so any negative reads "this parameterisation";
- the pulse is a 200 ms cue-like current;
- e0 SD ≈ 9° and set by the jump sign;
- CX onset error mixes encoding lag with memory;
- no persistence-dependence arm;
- stationary world;
- exact noise-free `cue_rel`; no fly-level claim.

---
## PI responses (rounds 1 and 2)

**Round 1: "STOP — DESIGN STILL CONFOUNDED".** Accepted. The design was revised to Exp A2 (progress_log Cycle 6):

- target jump; Δ = 0;
- SelfOnly, the cue-free integrator;
- CX-DN pulse, a non-identity readout;
- the onset rule renamed.

The yoked/replay control, the drift-calibrated arm and the passive dose-response were not adopted. They are listed as
limitations or recommendations. Round 2 judged them not mandatory for a small-scale experiment.

**Round 2: "READY, conditional on 5 text amendments".** All five were applied in `hypotheses_and_thresholds.md`
§A2-8. The PI verified the strongest remaining objection numerically (`verify/redteam2_spotcheck.txt`): pooled across Δ,
SelfOnly passed the memory-content test; within Δ, CX-Bump fails it.

### Answers to the seven red-team questions (evidence in this file and in `dev/analysis_dev*.txt`)

1. **What would show that CX state causally affects steering?**
   - Primary test, through a non-identity readout: the S_DN lower CI bound > 5°, ≥ 80 % of seeds positive, and the
     manipulation check passed.
   - Dev4: +21.1 [+18.2, +24.1], 6/6.
2. **What would show the activity is present but behaviourally useless?**
   - Coherence passes (dev 0.75–0.83), but Q2 rejects "useful", or the within-Δ memory-content test fails.
   - Dev data already lean this way: Δ = 0 CX-Bump − Freeze is +13.2; CX-Bump − SelfOnly is +12.2 [+2.2, +22.1]; the
     within-Δ slope is −0.31, r −0.16.
3. **Could a frozen command or a simple integrator reproduce the effect?**
   - For usefulness, yes: Scalar beats the CX, and SelfOnly matches or beats it.
   - For Q1 through the bump readout, the effect is an identity by construction; Scalar-Shift ±30 reproduces it.
   - Only the DN-pulse test probes transmission through the modelled PFL3→DN pathway.
4. **Does the perturbation affect only the intended state?**
   - It enters through the EPG cue channel and raises EPG rate by ~5 Hz in both pulse and sham trials. Coherence is
     unchanged.
   - Sham − Bump was −5.2 in dev1 and +2.3 in dev2, so the sham is needed, and all Q1 contrasts use it.
5. **Does the baseline receive exactly the same information?**
   - Yes for inputs: the same cue stream (including dropouts), the same λ_self·w_base and the same timing. There is no
     `aim_az` and no ground truth.
   - The asymmetries are architectural and disclosed: the CX also integrates cue history, and it has a dev-tuned PEN trim
     λ_cx = 0.65.
6. **Can the criteria reject the CX hypothesis?**
   - Yes. Replayed on dev4, they would reject usefulness and non-inferiority and pass Q1.
   - Escape hatches are limited to prespecified validity failures (§7), which are labelled "inconclusive", not
     "negative".
7. **Which claims remain model-level?**
   - All of them. Specifically: the bump as a target memory; the λ_cx trim; the EPG-pulse analogue of optogenetic
     relocation; the PFL3 goal of 0 and the DNa01 copy; the graded shuffle as a structural control.
   - None generalises to flies (`literature_matrix.md`).
