# CX working memory vs Kalman/PD (SO-101, bio2): audit and pilot report

**Final status: `STOP — PROTOCOL INVALID`**

The red-team reviewer dissents and prefers `STOP — PILOT INCONCLUSIVE`; see §7. Both readings rule out a held-out
benchmark of the current protocol.

- **Pilot:** it ran, after the integrity gate passed. 240 seed–condition trials were attempted: 6 primary arms × seeds
  100–129 = 180, plus 2 diagnostic Freeze arms × 30 = 60. All 240 completed and were recorded, with 0 missing,
  0 duplicates and 0 technical failures. There were 3 extra diagnostic reruns, kept in a separate file.
- **Seeds and hardware:** held-out seeds 0–39 were not used, and the runner now refuses them. No hardware was used.
- **Files outside the permitted scope:** none changed (`git_integrity_final.txt`). The only modified project file is
  `bio2/test_cx_working_memory_vs_kalman.py`, which is permitted. Its diff is in `script_changes.diff` and its original
  copy is in `archive/`. Python may have refreshed git-ignored `bio2/__pycache__` bytecode.
- **Unverified claims:** the literature claims come from abstracts and summaries, but all 24 DOIs were verified against
  Crossref. Determinism was shown only on this machine. The open-loop probe had no prespecified acceptance criteria.

## 1. Does the experiment test biological CX working memory?

**No, not as designed.** Evidence:

1. **The endpoint is dominated by target motion.** The ball always sweeps in the same direction. It moves 11.6–15.5° in
   azimuth during the 101-step occlusion (Δball, identical across arms).
   - A perfect *static* memory therefore scores |e| ≈ 13.5°.
   - A controller that freezes scores |e_onset + Δball|. It wins whenever the arm lags the target at onset.
   - Freeze-vs-memory effect: +0.02° for seeds with e_onset ≤ 0 (n = 8), and +7.80° for seeds with e_onset > 3°
     (n = 18) (`analysis/redteam_verification.txt`).
   - So R5 (memory beats freeze) and NI-1 could not have been passed or failed informatively by any memory.
2. **The non-biological reference matches BIO-Static.** LastObs-PD, a zero-order hold using kinematics, gives
   NI-1 D = +0.49° [t-CI −2.49, +3.47]. The nominal one-sided upper bound of 2.97° is below the 3° margin, but by
   point 1 this carries no information about memory.
3. **BIO-Shuffle is a dead network, not a structure control.**
   - The ring is silent (EPG 0 Hz).
   - `slope_mem` = [0, 0] in 30/30 trials, and j_ctrl = 0 in 30/30.
   - Visual steering is about 10× mis-gained.
   - Its "error" (mean |e| 10.96°, lower than BIO-Static's 15.07°) is an artefact of freezing. It was correctly flagged
     DEGENERATE_CALIBRATION in all 30 records and was excluded from comparative tables.
4. **`t_reacquire` is censored by design.** The ±5° band is narrower than the steady visible tracking lag of 6–9°. It was
   defined in only 0–7 of 30 trials per arm.
5. **Most of the causal path is engineered** (`preflight_audit.md` §1):
   - camera-ray geometry for the cue;
   - a calibrated lookup `u_for` that turns joint velocity into PEN current;
   - a fixed PFL3 goal of 0;
   - DNa01 as a copy of the DNa02 path;
   - a linear decoder with separate visual and memory calibrations, switched by a `seen` flag;
   - a ×2.5 P gain;
   - in Hybrid, `np.polyfit` target velocity.

   The genuinely network-dependent part is the persistence of the bump.

## 2. What the pilot did establish (exploratory)

The plan was prespecified in `stats_plan.md` §7, and the amendments made before the pilot are in §9 with a disclosure
correction. D = |e_A| − |e_B| in degrees, with paired t-CIs and BCa CIs (`analysis/`).

| Contrast | mean D | 95 % CI (t / BCa) | Reading |
|---|---|---|---|
| NI-2 BIO-Hybrid − Kalman-PD | **+7.29** | [5.07, 9.51] / [5.22, 9.42] | **Prespecified clean negative.** Hybrid is inferior. It stays +7.65 after adjusting for onset error. No sample size can show noninferiority. |
| NI-1 BIO-Static − LastObs-PD | +0.49 | [−2.49, 3.47] / [−2.32, 3.24] | Uninformative by design (§1) |
| BIO-Static − BIO-NoSelf | −2.73 | [−6.31, 0.84] / [−6.20, 0.58] | Self-motion effect not resolved |
| BIO-Hybrid − BIO-Static | −1.91 | [−5.29, 1.46] | Velocity extrapolation effect not resolved |
| Kalman-PD − LastObs-PD | −8.72 | [−9.30, −8.13] | The endpoint *does* separate prediction from hold |

Per-arm mean |e|:

| Arm | mean \|e\| | SD | CONTROL_FAILURE |
|---|---|---|---|
| Kalman-PD | 5.86° | 1.07 | — |
| BIO-Static-Freeze | 10.27° | — | — |
| LastObs-Freeze | 12.85° | — | — |
| BIO-Hybrid | 13.15° | — | 5/30 |
| LastObs-PD | 14.58° | 1.31 | — |
| BIO-Static | 15.07° | 7.82 | 10/30 |
| BIO-NoSelf | 17.80° | — | 15/30 |

Prespecified decision rules:

- R1 (integrity) passed.
- R2 (NI-2 promising) failed.
- R3 (feasible N) failed.
- R4 and R5 failed. They were uninformative by design.

**Open-loop memory probe** (exploratory, no MuJoCo, seeds 100–109; `analysis_openloop_probe.txt`):

- **Persistence is shown.** The intact bump stays coherent (0.80) for 2 s after the cue is removed. The shuffled ring is
  silent.
- **Accuracy is poor.** Mean |error| from the cued bearing is 9° at 0.25 s, 14° at 1 s and 20° at 2 s, with a +7…+15°
  systematic drift.
- **Self-motion integration overshoots.** The PEN pathway over-compensates imposed rotation, with gain ≈ 1.32 (SD 0.79).
  Without self-motion input there is no compensation (gain ≈ 0).

**Post hoc** (not prespecified) ball-motion-free check: |Δaim − e_onset| measures how well the arm executes the
correction a perfect static memory would make.

| Arm | mean \|Δaim − e_onset\| | SD |
|---|---|---|
| LastObs-PD | 1.10° | 0.21 |
| BIO-Static | 6.79° | 4.30 |
| BIO-Static-Freeze | 4.52° | — |

BIO-Static is worse than LastObs-PD by +5.69° [+4.09, +7.30], and slightly worse than its own freeze arm. The CX memory
as read out does not yet act as an accurate memory.

## 3. Claims, by level of evidence

| Claim | Status |
|---|---|
| Implementation has no target-state leakage | Verified (PI + Agent B, code trace) |
| Pipeline deterministic (same machine) | Verified: 8 bit-identical reruns |
| Bump persists without input in this model | Verified (open-loop probe), model-level only |
| Bump integrates self-rotation | Partly: present but gain ≈ 1.3, engineered lookup |
| CX bump acts as an accurate target memory in closed loop | Not supported (post hoc negative) |
| BIO-Hybrid noninferior to Kalman-PD | Refuted in pilot (prespecified) |
| BIO-Static noninferior to LastObs-PD | Nominal only; uninformative |
| Fly EPG encodes egocentric bearing of a moving object | Unsupported in the literature (`literature_matrix.md` Q1/Q5); EPG encodes heading vs landmarks; object pursuit in flies is LC10/optic-lobe mediated |
| PEN shifts bump by angular velocity; ring-attractor persistence | Directly supported in flies (Green 2017; Seelig & Jayaraman 2015; Kim 2017) |
| PFL3 → DNa02 steering via goal comparison | Directly supported (Westeinde 2024; Mussells Pires 2024; Rayshubskiy 2025), but the goal here is repurposed |
| DNa01 pathway, Delta7 ×8, Gaussian cue, linear decode ×2.5 | Engineered / unvalidated |

## 4. Changes made (all within permitted scope)

All changes are in `bio2/test_cx_working_memory_vs_kalman.py` (`script_changes.diff`). Primary-arm values are
bit-identical before and after the edits.

- `--run-pilot`: a resumable, append-only JSONL runner that records infrastructure exceptions. It refuses seeds 0–39
  unless `--allow-heldout` is passed.
- `LastObs-Freeze-Diag` and `BIO-Static-Freeze-Diag` diagnostic arms.
- New recorded fields:
  - `e_onset_deg`;
  - onset and reappear azimuths;
  - bump angle and coherence;
  - `e_ring_lastocc_deg`, because `e_ring` at reappearance already includes 10 ms of returned cue;
  - `n_cue_seen_pre_onset`;
  - `t_reappear_actual` and `n_occluded_steps`;
  - steering calibration.
- `k = -1` guard.

Not changed: endpoint definitions, gains, the `t_reacquire` definition, production code, the connectome and the scenes.

## 5. Known defects left in place (out of scope or would change the hypothesis)

- The CLI default `--t-total` of 2.5 s cannot serve t_occ ≥ 1.5. The runner uses CFG's 3.5 s.
- `compute_non_inferiority_stats` returns p = 0.5 when SE ≈ 0 and has no n < 2 or NaN guard.
- The sample-size helper uses a normal approximation, and its "Holm" option is actually Bonferroni.
- Line 342 `(self.tv if seen else self.tv)` is a no-op.
- The claim that "Hybrid mirrors agent.py" is false (W_MAX 0.6 vs 1.0, and gating is missing).
- The scene RNG, SNN noise RNG and shuffle RNG are all seeded with the same integer.
- The sibling script `test_cx_asymmetry_ablation.py:443-453` prints pre-written verdicts (Agent B #17). It was not
  modified.
- The baselines get absolute `aim_az` while BIO integrates `w_base`, which is an information asymmetry.

## 6. Recommendations before any held-out benchmark

These come from the red-team review §6–7, accepted by the PI. A redesign is needed, not more seeds.

1. **Stationary-target and randomised direction/speed conditions.** A perfect static memory should then give about 0
   error and freezing should give |e_onset|. Start the occlusion only after the visible tracking has converged, and log
   the arm velocity at onset.
2. **Ring perturbation during occlusion.** Shift the bump by ±30° partway through and check that the motor command
   follows it. Also clamp or reset the ring at onset. This is the most direct test of a persistent neural state versus
   an externally maintained estimate.
3. **A matched non-neural memory module.** Use a scalar integrator or an EKF on the same cue and `w_base`, without
   `aim_az`.
4. **The same visible-phase tracker for every arm,** so that only the memory module differs.
5. **A valid structural control.** Options:
   - graded shuffles with gains re-trimmed so that firing rate and coherence match the intact network;
   - phase-rotation ablations;
   - Delta7 or PEN lesions;
   - an idealised cosine ring.
6. **One readout with no `seen`-switched calibration.**
7. **Prespecified numeric falsifiers for memory accuracy and self-motion gain.**

## 7. Red-team dissent (preserved)

The red team argues that "PROTOCOL INVALID" relabels a prespecified negative, because NI-2 is determinate and the
endpoint does separate Kalman from hold.

The PI accepts that NI-2 is a clean negative and states it above without qualification. The PI keeps INVALID because the
benchmark's stated purpose is a working-memory test, and no outcome of this design could have been conclusive about
working memory. More seeds would not change that.

Full critique and responses: `red_team_review.md`.

## 8. File index

| File | Contents |
|---|---|
| `progress_log.md` | Cycles 0–5, with corrections |
| `literature_matrix.md` | Literature matrix |
| `preflight_audit.md` | Preflight audit |
| `code_audit_agentB.md` | Independent code audit |
| `stats_plan.md` | Analysis plan and amendments |
| `pilot_gate.md` | Pilot gate decision |
| `REPRODUCE.md` | Environment and commands |
| `raw/` | 240 pilot records, reruns, probe data, commands, logs |
| `analysis/` | CSV, JSON, analysis.md, supplementary analyses |
| `red_team_review.md` | Red-team critique and PI responses |
| `git_integrity_initial.txt`, `git_integrity_final.txt` | Git integrity before and after |
| `archive/` | Baseline copies of the 3 untracked scripts |
| `scripts/` | Diagnostic and analysis scripts |
