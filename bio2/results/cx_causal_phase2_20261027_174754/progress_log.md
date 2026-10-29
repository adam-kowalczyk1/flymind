# Phase 2 progress log — causal validation of CX memory (started 2026-10-27 17:47 CET)

Output dir: bio2/results/cx_causal_phase2_20261027_174754. Phase-1 dir (read-only): bio2/results/cx_wm_audit_20261027_163059.
Python: /Users/admin/so101_fly_project/.venv/bin/python (system python lacks mujoco).

## Cycle 0 — integrity baseline and reproduction of phase-1 findings
- git_integrity_initial.txt: main @ 8f591242, tracked tree clean; untracked: 3 experiment scripts + 2 result dirs;
  sha256 of code files + every phase-1 output file. archive/test_cx_working_memory_vs_kalman.py = current (edited in
  phase 1) script, sha256 30f85768…; its phase-1 baseline f145bff8… is in phase-1 archive/.
- Reproduction (exit 0): phase-1 scripts/analyze_pilot.py and scripts/supplementary_analysis.py re-run on the saved
  raw/pilot_*.jsonl into verify/: analysis.md, summary_by_condition.csv, paired_contrasts.csv, reconciliation.json and
  supplementary_analysis.txt are byte-identical to the phase-1 outputs.
- Claims directly supported by saved records: 240/240 trials; NI-2 D = +7.29 [5.07, 9.51]; Δball 11.6–15.5° one
  direction in all 30 scenes; BIO-Shuffle slope_mem = 0 & j_ctrl = 0 in 30/30; freeze effect tied to onset sign;
  open-loop bump coherence 0.80 for 2 s; self-motion gain g ≈ 1.32 (SD 0.79).
- Inferences / unverified: that the bump "is" a target memory (only persistence shown); that LC10-type pathways rather
  than CX mediate object pursuit in flies (literature, abstract-level); cross-machine determinism; the post hoc
  |dAim − e_onset| negative.

## Cycle 1 — feasibility probes (dev network/scene seeds 200–205 only)
- Commands (all exit 0): scripts/probe_perturb_openloop.py 200,…,204 → probes/perturb_openloop.json (+_summary.txt);
  scripts/probe_graded_shuffle.py 200,201,202 f∈{0,.05,.1,.2,.35,.5} → probes/graded_shuffle.json (+_summary.txt);
  scripts/probe_scene.py → probes/scene_probe.json/.log.
- Evidence:
  * A stationary ball is NEVER detected (0 % of frames, both sides): the retina/LC10-like detector is motion-based.
    A "stationary target throughout" Experiment A is impossible without changing production vision (forbidden).
    Smallest valid alternative: moving target while visible, ball stopped (qvel := 0) at occlusion onset
    (it becomes undetectable within ~70 ms; the endpoint is ground truth, so this is acceptable).
  * Mirrored sweeps (y0 < 0, vy > 0) track symmetrically (lag +3.9° vs −5.6° at 1.2 s): direction can be randomised.
  * EPG pulse (same current form as the visual cue) at bump±30° for 200 ms shifts the bump −24.8/+26.7° (SD ~4.7),
    persists 600 ms later (−25.1/+30.4, SD ~12), coherence unchanged (0.80), EPG +5 Hz transient in pulse AND sham.
    Sham (Δ = 0, identical energy) shifts −0.5° ±5. 100 ms pulses give ~±20°. → intervention is well defined.
  * Ring reset (rest inhibition 50–200 ms) silences the ring and it stays silent (coherence 0, 0 Hz at +600 ms).
  * Graded shuffle (no gain compensation): f = 0.2 keeps a cue-driven bump (coherence 0.85, 36 Hz) but abolishes
    persistence (0 Hz, coherence 0 at 1 s); f = 0.05 keeps persistence but triples drift; f ≥ 0.35 cue-only.
    → f = 0.2 chosen as a persistence-selective structural control (Exp E), defined with its own calibrations.
- Decision: implement a new experiment-only runner bio2/test_cx_causal_memory.py (shared non-neural visible-phase
  tracker; memory-only swap during occlusion; passive rotation; interventions). No production file touched.

## Cycle 2 — implementation and smoke tests
- New file bio2/test_cx_causal_memory.py; `--test-unit` PASS (tests/unit_tests_v1.txt, v2.txt).
- Smoke 1 (dev/smoke.jsonl, seed 200, passive +20): FOUND DESIGN DEFECTS — (a) memory acted for 0.1 s before the
  passive window so realised rotation differed between arms (15.6–19.7°); (b) reset applied after the passive window,
  not at onset; (c) endpoint-only reading of the pulse hid a real ~10–13° predicted-direction effect behind later drift.
- Fixes: passive_start = 0 (passive window from onset), reset_start = 0, int_start = 0.7 s; explicit readout rule
  (bump coherence < 0.2 → no estimate → ω = 0) for all CX arms.
- Smoke 2 (dev/smoke2.jsonl): true_rel bit-identical across all arms through the passive window (realised 17.30°);
  CX-Reset ≡ Freeze (−14.27°); Pulse+30 − Sham = −24.8° (predicted sign); Scalar −1.10°; CX-Bump −30.7° (drift after
  correct integration: bump −11.9° vs true −14.3° post-passive).
- Next: development set (dev/commands.txt): Exp A seeds 200–205 × 13 arms × passive ±20; Exp B moving, seeds 200–203.
- Exp A dev attempt 1 FAILED for all 3 processes (argparse read '--passive -20,20' as an option; logs kept as dev/log_expA_*_failed_argparse.txt; no records written). Rerun with --passive=-20,20. Exp B dev (16 records) completed.

## Cycle 3 — development set 1 (Exp A seeds 200–205 × 13 arms × Δ ±20; Exp B seeds 200–203; λ_self = 1)
- Commands: dev/commands.txt (exit 0 after the argparse rerun). Analysis: scripts/analyze_dev.py → dev/analysis_dev.txt.
- Evidence (156 + 16 records, 0 failures, onset state bit-identical across arms in every (seed, Δ)):
  * Q1 perturbation: bump shift +26.2/−24.8° (sham +0.2°), coherence unchanged; e_end(Pulse+30) − e_end(Sham) −14.8
    [−23.7, −5.8]; (−30) +20.6 [+14.9, +26.3]; symmetric effect 17.7 ± 8.9, predicted sign 12/12. Sham − Bump −5.2
    [−10.2, −0.3] (the pulse itself has a non-specific effect → sham is necessary).
  * Q2: CX-Bump − Freeze −2.9 [−11.3, +5.4] (not resolved). CX-Reset and CX-Shuffle20 ≡ Freeze exactly (silent ring →
    readout gate) — they are behaviourally identical controls by construction.
  * Q3: CX-Bump − Scalar +13.0 [+6.5, +19.5]; Scalar |e| 1.42°, memory error 0.58°.
  * Q4: CX-Bump − NoSelf −16.6 [−30.4, −2.8]; closed-loop integration gain (aim-referenced) CX 1.54 ± 0.67, NoSelf
    0.00 ± 0.88, Scalar 0.91 ± 0.003 (= 1/1.105 kinematic factor).
  * Exp B (n = 4): CV 8.7°, Scalar 22.5°, Freeze 26.1°, CX 23.0 ± 23.8°.
- Challenge: Workstream C claimed κ = 0.87; PI measured 1.105 (control_comparator_design.md, PI section) → corrected.
- Decision (tuning on DEV only): λ_self = 1.105 (kinematics, shared); λ_cx = 0.65 (= 1/1.54) as an explicit CX-arm
  calibration trim of the PEN input. Verify on new dev seeds 206–209 (dev2) before freezing.

## Cycle 4 — dev2 verification of tuned trims (seeds 206–209, 7 arms, Δ ±20; λ_self 1.105, λ_cx 0.65)
- Commands: dev/commands.txt (dev2 lines), exit 0; 56/56 OK; dev/analysis_dev2.txt.
- Evidence: Scalar g = 1.00 ± 0.004 (kinematic factor fixed); CX g = 1.18 ± 0.86 (mean improved from 1.54, variance
  unchanged → trim cannot fix the dominant error). Q1 symmetric pulse effect 24.4 ± 6.1°, 8/8 predicted sign; bump
  shift +28.8/−22.7 (sham −1.9). Q2 CX-Bump − Freeze +0.9 [−8.4, +10.1]. Q3 CX-Bump − Scalar +16.6 [+7.1, +26.1].
  Q4 CX − NoSelf −6.7 [−22.3, +8.9].
- Decision: FREEZE parameters as code defaults (λ_self = 1.105, λ_cx = 0.65; all other CFG unchanged);
  runner sha256 in frozen_runner_sha256.txt. No further tuning. Dev seeds used: 200–209 only.

## Cycle 5 — statistics workstream reconciliation and dev3 gain re-check
- Workstream D (hypotheses_and_thresholds.md) verified by PI spot-check (verify/stats_agent_spotcheck.txt): Freeze is a
  seed-level constant (17.30–17.32° = realised passive, because the ±Δ average cancels e_onset when |e_onset| < 17.35);
  Q1 seed-level S 17.7 (SD 3.9) / 24.4 (SD 3.4); Q2 seed SD 7.4 / 9.1 — all match the agent's numbers.
- Accepted D's request: re-check the frozen λ_cx on ≥ 20 fresh dev seeds before freezing. Runner change: logging only
  (conv_rate_deg_s, conv_seen at onset); behaviour bit-identical (tests/frozen_default_repro2.txt); new sha256 in
  frozen_runner_sha256.txt.
- dev3 (seeds 210–229, CX-Bump, frozen params, 40/40 OK; dev/analysis_dev3.txt): seed-level g = 0.992, SD 0.476,
  95 % CI [0.770, 1.215] → PASSES the prespecified acceptance (point in [0.75, 1.25], CI inside [0.6, 1.5]).
  |e_end| 14.25 vs Freeze 17.31: d ≈ −3.06 [−7.02, +0.91] (unresolved); memory-estimate error at reappearance 24.5°
  (> never-updated 17.3 → criterion §6 (iii) would fail). Coherence 0.75–0.83.
  Note: the convergence rule always fires at conv_rate 3.81–3.99 °/s, i.e. at its boundary — "slow enough", not
  converged; the 4 °/s threshold remains provisional.
- Decision: parameters stay frozen. Next: independent red-team review of the protocol.

## Cycle 6 — red-team review of the protocol and design revision (v2)
- Red team (red_team_review.md) recommended STOP — DESIGN STILL CONFOUNDED. PI verified (verify/redteam_spotcheck.txt):
  e_onset SD only 4.4–4.7°; within each Δ sign the CX correction is uncorrelated with the remembered onset bearing
  (r −0.20…+0.11); an ideal cue-free self-motion integrator would score |e| ≈ 4.7–5.2° vs CX 14.3° → the v1 task mostly
  tests path integration of the experimenter's rotation, not target memory. Q1 with ω = K·bump is an identity check.
- Accepted and implemented (frozen v1 archived as archive/test_cx_causal_memory_frozen_v1.py):
  (1) target jump ±U(10, 20)° (seed-determined, shared by arms) at the convergence time, visible for 0.2 s, then
      occlusion + ball stop → widens the remembered bearing; (2) SelfOnly arm (cue-free integrator: assumes target
      straight ahead at loss of view, then −∫λw); (3) DN-readout pulse arms (CX-DN-Sham/Pulse±30) — the PFL3→DN path is
      not an identity readout; (4) Δ = 0 condition (pure target memory, no self-motion demand).
- Checks: unit tests PASS (incl. SelfOnly); no-jump regression bit-identical to dev2 (tests/regression_v2_nojump.txt);
  jump smoke seeds 230–232 (dev/jump_smoke.jsonl): e_onset −19.1/−5.8/−8.8°; Δ = 0: Scalar |e| 2.6/4.8/1.2,
  Freeze 19.2/5.8/8.8, SelfOnly ≈ Freeze, CX-Bump 20.1/47.6/31.0.
- Not adopted now (kept as limitations/recommendations): yoked/replay control (analysis-level frozen-mean command is
  reported instead), drift-calibrated CX arm (an engineering patch that changes the model), passive dose-response beyond
  {−20, 0, +20}.
- Next: dev4 (seeds 230–235, 12 arms, Δ ∈ {−20, 0, 20}, --jump).

## Cycle 7 — dev4 on the revised design (Exp A2; seeds 230–235 × 12 arms × Δ ∈ {−20, 0, 20}; 216/216 OK)
- Commands: dev/commands.txt (dev4 lines), exit 0. Analysis: scripts/analyze_dev4.py → dev/analysis_dev4.txt.
- Evidence:
  * Onset: NOT strictly bit-identical — 2/216 trials differ at onset by ≤ 1.2e-5° (verify/dev4_onset_identity.txt),
    probably renderer nondeterminism; earlier "bit-identical" statements hold only for the records checked.
  * Q1 (non-identity DN readout): S_DN +21.1 [+18.2, +24.1], 6/6; bump readout S +23.0 [+19.0, +27.1], 6/6;
    manipulation check bump shift +30.3/−26.5 (DN arms), +28.4/−27.7 (bump arms), sham ≤ 2.4°.
  * Q2: Δ = 0 CX-Bump − Freeze +13.2 [−4.6, +31.0] (CX worse); ±20 CX-Bump − SelfOnly +12.2 [+2.2, +22.1] (CX worse than
    a cue-free integrator); ±20 CX-Bump − Freeze +2.7 [−4.2, +9.7].
  * Q3: CX-Bump − Scalar +18.9 [+1.7, +36.1] (Δ 0), +17.6 [+9.9, +25.4] (±20). Scalar − SelfOnly −5.5 (target memory
    adds value for the scalar).
  * Memory content: correction-on-bearing slope CX −0.71 ± 0.27 (r −0.55) vs Scalar −0.90 ± 0.03 (r −0.99).
- Decision: protocol v3 + thresholds §11 written (no confirmation seed run); runner re-hashed; red-team round 2 launched.

## Cycle 8 — red-team round 2, amendments, integrity, decision
- Red team round 2 (red_team_review.md, "Round 2"): READY conditional on 5 text amendments; PI verified the main one
  (within-Δ memory-content slope: CX −0.31 ± 0.50, r −0.16; Scalar −0.82, r −0.96; SelfOnly 0 —
  verify/redteam2_spotcheck.txt) and applied all five (hypotheses_and_thresholds.md §A2-8, §A2-9). Runner unchanged.
- git_integrity_final.txt: tracked tree clean; all pre-existing code files and every phase-1 output file byte-identical
  to the start of phase 2; the only new project file is bio2/test_cx_causal_memory.py (frozen sha256 5592500…).
- Seeds used in phase 2: 200–235 (development) only. No confirmation seed (300–399), no held-out seed (0–39), no
  hardware. Trial counts: smoke 13, dev1 156 (+ 3 failed processes with 0 trials), Exp B dev 16, dev2 56, dev3 40,
  jump smoke 12, dev4 216, regression/repro checks 6.

## FINAL DECISION: READY FOR SMALL-SCALE CAUSAL EXPERIMENT
(Exp A2, seeds 300–323, 14 arms × Δ ∈ {−20, 0, 20}, protocol v3 + thresholds §11 incl. §A2-8/9.) Dev data predict:
Q1 positive (state causally reaches steering, including via PFL3→DN), Q2 "useful" rejected or not demonstrated,
Q3 CX inferior to the matched scalar. This decision is about readiness of the controlled experiment, not a result.

## Repair cycle R1 — pre-confirmation blockers (2026-10-27 18:56–19:15)
- Start: repair_integrity_initial.txt (tracked tree clean; runner 55925009…; dev data hashes). Backups of every file to be
  changed: archive/pre_repair_20261027_185611/.
- A (protocol): confirmatory_protocol_v4.md written as the single binding protocol with change history C1–C15;
  causal_protocol.md and hypotheses_and_thresholds.md given a SUPERSEDED banner (content unchanged).
- C (runner): Dataset layer (manifest, provenance, identity check, lock, fsync, truncated-tail refusal/explicit repair,
  directory creation, calibration-failure records). Trial logic untouched.
  BUG found by the new safety test and fixed: after a calibration failure, non-CX arms were also marked TECHNICAL_FAILURE
  (first run kept as regression/runner_safety_tests_run1_FAIL.txt).
- B (analysis): bio2/analyze_cx_causal_confirmation.py v1.0.0 + bio2/test_analyze_cx_causal_confirmation.py.
  Self-test T3 initially FAILED twice; both times the analysis was right (|e| folding with noise > base error; then a
  precise −2° effect correctly gave NEGATIVE) and the test scenario was wrong; the final scenario asserts its precondition.
  BCa degenerate-data handling and NaN memory-error handling added.
- D (regression): unit tests PASS; analysis selftest 48/48 PASS; runner safety 23/23 PASS; behavioural regression
  12 + 2 trials bit-identical to dev4/dev2; dev4 cross-check of S_DN, P2a, P2b, S_bump identical to scripts/analyze_dev4.py;
  CLI refusals correct. frozen_manifest_v4.json written (runner cc279579…, analysis 2c6bf13c…, protocol 13e68691…).
- No seed 300–399 or 0–39 run; no hardware; no commit.
- INCIDENT (R2 start): an archive `cp` mistakenly overwrote archive/pre_repair_20261027_185611/test_cx_causal_memory.py
  with the R1 runner and added an R1 analysis copy there. Recovered: the v3 runner was reconstructed by reversing the
  recorded R1 edits; its sha256 equals the recorded 55925009…; restored. The stray analysis copy (identical to
  archive/repair_r1/) was removed. All pre_repair backups now match repair_integrity_initial.txt byte-for-byte.
