# Research audit (phase 2)

## 1. Starting evidence

The phase-1 results directory is `bio2/results/cx_wm_audit_20261027_163059`.

- **Phase-1 analyses reproduce exactly.** All analyses were regenerated from the saved records and came out
  byte-identical (`verify/`).
- **Phase-1 conclusion still stands.** The old protocol cannot show whether CX memory is useful.
  - The target always moves 11–16° in one direction during occlusion.
  - A freeze controller wins whenever the arm lags the target at onset.
  - BIO-Shuffle was a silent network.
  - The baselines had privileged `aim_az`.

### What the data directly support

| Claim | Source |
|---|---|
| NI-2 (BIO-Hybrid vs Kalman-PD) is a clean negative, +7.3° | phase-1 records |
| The intact bump persists 2 s in open loop | open-loop probe |
| Open-loop self-motion gain ≈ 1.32 (SD 0.79) | open-loop probe |
| Open-loop memory error ≈ 14° at 1 s | open-loop probe |
| Shuffled ring is silent | phase-1 records |
| A stationary ball is invisible to the vision front end | phase 2, `probes/scene_probe.log` |
| ±30° EPG pulses shift and hold the bump; sham does not | phase 2, `probes/perturb_openloop_summary.txt` |
| A 20 % graded shuffle removes persistence but spares the cue-driven bump | phase 2, `probes/graded_shuffle_summary.txt` |

### Inferences and claims that remain unverified

- The model's bump stands in for a *target* memory. In flies, EPG encodes heading relative to landmarks
  (`literature_matrix.md`).
- Every claim of fly relevance.
- Determinism across machines.
- Any model parameter value as a biological fact.

## 2. One coherent information path (task §4)

| Component | Role in phase 1 | Necessary engineering or confound? | Phase-2 treatment |
|---|---|---|---|
| Separate visual and memory DN calibrations, switched by `seen` | DN decoding | **Confound.** The controller is told when it is blind, and visible-phase steering differed between families. | The visible phase uses one **shared non-neural tracker** for every arm, ω = K·cue. The CX is consulted only during occlusion. The DN arm uses only the memory calibration, with no switch inside the readout. |
| Fixed PFL3 goal = 0 | Converts the bump into "turn toward 0" | Necessary engineering. It repurposes a goal comparison, which is a model-level choice. | Kept unchanged, and used only in the secondary CX-DN arm. |
| Engineered DNa01 copy of the DNa02 path | Slow steering channel | Engineered, not in the data. | Kept in CX-DN, which is reported as engineered. |
| ×2.5 external gain | P controller | Necessary engineering. | The same K = 2.5 for *all* arms, in both the visible and memory phases. |
| `aim_az` given to the LastObs and Kalman baselines | Absolute heading | **Confound (information asymmetry).** | Removed. All arms get only `cue_rel` and `w_base`. |
| `np.polyfit` target velocity in Hybrid | Extrapolation | A classical estimator inside a "bio" arm. | Dropped. Velocity extrapolation is tested separately with a CV filter in Exp B. |
| `u_for` lookup (PEN current vs velocity) | Self-motion gain | Engineered calibration of a biological pathway. | Kept as the network's own calibration. The measured gain is reported against a threshold. |

The smallest change that allows a causal comparison is the **shared visible-phase tracker with a memory-only swap**. It
makes the onset state identical across every arm of a seed. It was bit-identical in dev1–dev3. In dev4, 2 of 216 trials
differed by ≤ 1.2e-5° (`verify/dev4_onset_identity.txt`). Any
difference at reappearance is then caused only by the memory used during occlusion.

The cost of this change is that the PFL3/DN pathway is no longer tested in the main arm. That pathway is tested in the
secondary arm, CX-DN.

## 3. Constraints that shaped the design

- **The retina is motion-based, so a stationary target is never detected.** Exp A therefore uses a target that moves
  while visible and is **stopped at occlusion onset**. A perfect static memory then gets about 0 error, and a freeze
  keeps the onset error.
- **The onset lag is small** (≈3–7°). To give memory a demanding job, every Exp A trial includes a **passive base
  rotation** of ±20° nominal (≈17° realised) during the first 0.6 s of occlusion. This rotation is commanded by the
  experimenter and is identical across arms. It is the path-integration test: the memory must use `w_base` to know where
  the target now is.
- **Perturbation is a cue-like current into EPG** (an optogenetic-stimulation analogue). It acts on the same input
  channel the visual cue uses. The sham is the same pulse at zero offset.
- **The ring reset uses the model's own "rest" inhibition.** The ring then stays silent, which makes the reset arm
  behave like freeze by construction of the readout rule. That is intended: it is the "same network, state removed"
  control.
