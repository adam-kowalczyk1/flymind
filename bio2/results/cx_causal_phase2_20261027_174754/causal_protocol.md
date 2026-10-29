> **SUPERSEDED (2026-10-27):** where this file conflicts with `confirmatory_protocol_v4.md`, the v4 protocol is
> binding. This file is kept unchanged below as history. Its pre-repair copy is
> `archive/pre_repair_20261027_185611/`.

# Causal protocol: does the persistent CX state causally improve occluded-target control?

**Status: v3 (design revised after red-team round 1 → Exp A2; see the end of this file). Parameters frozen after dev seeds 200–235.**

- Runner sha256: `frozen_runner_sha256.txt`. The frozen defaults reproduce the dev2 records bit-identically
  (`tests/frozen_default_repro.txt`).
- Frozen values: K = 2.5, λ_self = 1.105, λ_cx = 0.65, coherence gate 0.2, shuffle fraction 0.2, pulse 200 ms at
  onset + 0.7 s, passive ±20° nominal over 0.6 s, t_occ = 2.0 s. Convergence rule as in §1.
- No confirmation seed (300–399) has been run.

- Implementation: `bio2/test_cx_causal_memory.py`. Nothing outside it is modified.
- Seeds: development = 200–299. Confirmation = 300–399. Held out and never used = 0–39. Phase-1 exploratory = 100–129,
  not reused.

## 0. Research question and what each answer means

> When sensory input disappears, does the persistent state of the intact CX network causally improve target-directed
> behaviour beyond a matched non-neural memory receiving exactly the same information?

The question splits into four sub-questions, each answered by its own contrast.

| Q | Contrast | What a "yes" establishes | What it cannot establish |
|---|---|---|---|
| Q1 Causal efficacy | CX-Pulse±30 vs CX-Sham | The motor output follows the network state. | That the state is useful. |
| Q2 Behavioural usefulness | CX-Bump vs Freeze, CX-Reset and CX-Shuffle20 | The persistent state improves aim over having no state. | That it beats an engineered memory. |
| Q3 Matched comparison | CX-Bump vs Scalar (same cue, same λ·w_base, same K) | The CX is non-inferior (or superior) to a lossless angle integrator. | Any fly-level claim. |
| Q4 Self-motion integration | CX-Bump vs CX-Bump-NoSelf | The PEN pathway is needed for the result. | — |

**Why superiority over Scalar is a secondary, expected-negative test.** The cue is a single, almost noise-free bearing,
and w_base is the measured joint velocity. Under those conditions the scalar integrator is close to the sufficient
statistic (`control_comparator_design.md`). A CX advantage could only come from regimes the scalar handles badly: cue
noise, distractors, or long gaps. Those regimes are not part of this experiment and are listed as a recommended
extension.

## 1. Shared trial structure (all arms of a seed are identical until the occlusion onset)

1. **Scene** (`scene_params(seed)`):
   - The ball rolls across the visual field at x = 0.44 m.
   - Direction is random: y0 = s·U(0.12, 0.16) m and vy = −s·U(0.07, 0.12) m/s, with s = ±1 at p = ½.
   - The occluder is parked. Occlusion is applied by software blanking.
2. **Visible phase (shared and non-neural):**
   - ω = K·cue_rel, with K = 2.5. If the cue is not detected, ω = 0.
   - The command goes through the phase-1 actuator layer (w_max 0.6 rad/s, windup 0.02 rad).
   - CX arms run their network on the same cue and λ·w_base, but the network does not affect motion.
3. **Onset, fixed by a convergence criterion that is identical for every arm:**
   - Conditions: t ≥ 1.0 s; the cue was seen in ≥ 27 of the last 30 steps; and |slope of cue| over those 30 steps
     ≤ 4 °/s.
   - If the criterion is not met by 2.2 s, the trial is NOT_CONVERGED. That status is a property of the seed and applies
     to all its arms.
4. **At onset (Exp A):** the ball is stopped (qvel := 0). The motion-based retina cannot see a stationary target, which
   is why the ball moves while visible (`probes/scene_probe.log`).
5. **Passive rotation, from onset to onset + 0.6 s:**
   - The base is commanded to rotate by the experimenter at Δ/0.6 s, with Δ ∈ {−20°, +20°} nominal (≈17.3° realised).
   - Every arm's own output is ignored during this window, so the arm trajectory is bit-identical across arms.
   - Memories receive only λ·w_base, with λ = 1.105 (dev-derived kinematic scale, shared).
6. **Memory phase, onset + 0.6 s to onset + 2.0 s:** ω = K·θ̂ from the arm's memory. If there is no estimate, ω = 0.
7. **Reappearance at onset + 2.0 s:**
   - The endpoint is the ground-truth e_end = wrap(ball_az − aim_az).
   - The memory's own estimate error at that moment is recorded too.

## 2. Arms

| Arm | Memory during occlusion | Purpose |
|---|---|---|
| Freeze | none (ω = 0) | Null: no memory |
| Scalar | θ̂ = last cue − ∫λ·w_base dt | Matched non-neural memory (Q3) |
| CX-Bump | θ̂ = EPG population-vector angle if coherence ≥ 0.2, else no estimate. PEN current u_for(−λ·w_base). | Main CX arm |
| CX-Bump-NoSelf | Same, but with PEN u_for(0) | Q4 |
| CX-DN | θ̂ = DNa02/DNa01 L−R decoded with the memory calibration only | Secondary: PFL3/DN pathway |
| CX-Reset | CX-Bump, with the ring inhibited (`rest`) for 100 ms at onset | Same network, state removed (Q2) |
| CX-Shuffle20 | CX-Bump on a network with 20 % of CX weights permuted within projection and sign. No gain compensation; the network's own calibrations. | Structural control: cue-driven bump kept, persistence lost (`probes/graded_shuffle_summary.txt`) (Q2) |
| CX-Sham | CX-Bump plus a 200-ms EPG pulse at the current bump angle, from onset + 0.7 s | Sham for Q1 |
| CX-Pulse±30 | The same pulse centred at bump ± 30° | Q1 |
| Scalar-Shift±30 | θ̂ += ±30° at onset + 0.7 s | Positive control for the readout (a trivially causal state) |
| CV (Exp B only) | Alpha-beta constant-velocity estimate on cue + λ·w_base | Velocity extrapolation comparator |

## 3. Experiments

- **A — stationary-target memory with passive rotation.** All arms except CV; Δ = ±20°. This is the primary experiment
  and covers Q2, Q3 and Q4.
- **B — moving-target generalisation.** Ball not stopped; direction and speed random; Δ = 0. Arms: Freeze, Scalar, CV,
  CX-Bump. It is reported descriptively and separates:
  - "maintaining a direction-like state" (Exp A);
  - "tracking a moving target" (the visible-phase tracker, shared);
  - "velocity extrapolation helps" (CV vs Scalar).

  The comparison is adjusted for onset error by regressing on e_onset (ANCOVA).
- **C — causal perturbation.** CX-Sham, CX-Pulse+30 and CX-Pulse−30 inside Exp A trials.
  - Prediction: a +30° pulse moves the bump left, so the controller turns left, so e_end becomes more negative. The −30°
    pulse is the mirror image.
  - Before/after state is recorded: bump angle, coherence, EPG and PFL3 rates, and the DNa02 L−R readout.
- **D — matched non-neural memory.** The Scalar arm. Its information is exactly the CX arm's: the cue sequence and
  λ·w_base, with no `aim_az` and no ground truth. It shares the tracker, onset state, K, limits and metric.
- **E — structural control.** CX-Shuffle20, with its exact definition above. Recalibration is part of the control
  definition: the network's own `calibrate_ring` and `calibrate_steer`, and no gain matching. The graded probe showed
  that f = 0.05 keeps persistence and f ≥ 0.2 removes it. An idealised cosine-ring reference was not implemented; it is
  listed in `implementation_plan.md` as optional.

## 4. Analysis

The endpoints, thresholds, falsifiers and sample size are in `hypotheses_and_thresholds.md`. The general approach:

- All comparisons are paired within (seed, Δ). The onset state is bit-identical across arms within a pair.
- The unit of inference is the seed: the two Δ conditions are averaged within each seed before computing the CI.
- Reported for each contrast: the mean of the paired differences, a t 95 % CI, and a BCa bootstrap CI (10 000
  resamples, RNG seed 20261027), with a Wilcoxon signed-rank test as sensitivity.
- Holm adjustment within each family, Q1–Q4.

## 5. Development results (EXPLORATORY; dev seeds only; not evidence for confirmation)

Sources: `dev/analysis_dev.txt` (dev1, seeds 200–205, λ = 1/1) and `dev/analysis_dev2.txt` (dev2, seeds 206–209,
frozen λ). Differences are in degrees, as mean [95 % t-CI] over (seed, Δ) pairs.

| Contrast | dev1 (n = 12) | dev2 (n = 8) |
|---|---|---|
| Q1: (e(−30) − e(+30))/2 | +17.7 (SD 8.9), 12/12 predicted sign | +24.4 (SD 6.1), 8/8 |
| Q2: CX-Bump − Freeze | −2.9 [−11.3, +5.4] | +0.9 [−8.4, +10.1] |
| Q3: CX-Bump − Scalar | +13.0 [+6.5, +19.5] | +16.6 [+7.1, +26.1] |
| Q4: CX-Bump − NoSelf | −16.6 [−30.4, −2.8] | −6.7 [−22.3, +8.9] |
| CX closed-loop self-motion gain | 1.54 ± 0.67 | 1.18 ± 0.86 |

**Expected confirmatory outcome, stated in advance:**

- Q1 positive: the state causally steers.
- Q2 null or negative: the state is not useful relative to freezing, because bump drift and gain variance at 1.4 s
  (memory error ≈ 20°) exceed the onset error a freeze leaves (≈ 17°).
- Q3 CX inferior to Scalar.

A confirmation run is still needed, because dev estimates from 10 seeds are imprecise and the trims were tuned on them.

## 6. v3 revision (Exp A2), adopted after red-team round 1

The changes respond to red-team round 1 (`red_team_review.md`) and are validated on dev4 (`dev/analysis_dev4.txt`).

1. **Target jump.**
   - When the slow-tracking onset rule fires, the ball is teleported in azimuth by ±U(10, 20)°. The value is drawn from
     `default_rng(77777 + seed)`, so it is shared by all arms.
   - The ball stays visible and moving for 0.2 s, then occlusion starts and the ball is stopped.
   - This widens the remembered bearing (dev4 e_onset −19.1 … +5.9°).
2. **Δ ∈ {−20, 0, +20}.** Δ = 0 tests pure target memory, with no self-motion demand.
3. **New arm SelfOnly.** A cue-free integrator: it assumes the target is straight ahead when sight is lost, then
   integrates −λ·w_base. It separates path integration from target memory.
4. **New arms CX-DN-Sham and CX-DN-Pulse±30.** The perturbation is read through the PFL3→DN pathway, which is not an
   identity readout. This is now the primary Q1 test.
5. Primary endpoints and rules: `hypotheses_and_thresholds.md` §11.

The v1 design (no jump; Δ ±20) is kept for reference. Its frozen runner is `archive/test_cx_causal_memory_frozen_v1.py`.

### Stage-1 confirmation command (prespecified, NOT run)

```bash
$PY test_cx_causal_memory.py --run --seeds 300-323 --arms Freeze,Scalar,SelfOnly,CX-Bump,CX-Bump-NoSelf,CX-DN,CX-Sham,CX-Pulse+30,CX-Pulse-30,CX-DN-Sham,CX-DN-Pulse+30,CX-DN-Pulse-30,CX-Reset,CX-Shuffle20 --passive=-20,0,20 --jump --out $O/confirm/expA2_stage1.jsonl
```
