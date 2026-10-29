# Second pre-confirmation audit (independent, read-only) — Exp A2, protocol v4

Scope: v4 protocol, frozen manifest, runner (diff vs `archive/pre_repair_20261027_185611/`), analysis, both test files, `regression/*`, REPRODUCE.md, implementation_plan.md, superseded docs. No seed 0–39 or 300–399 was run, and nothing was modified. I ran `test_analyze_cx_causal_confirmation.py` (SELFTEST PASS), `--test-unit` (PASS), and pure-Python probes on synthetic data (seeds 1300+).

## 0. Hash check (item 5): all consistent

- sha256 recomputed for runner `cc279579…`, analysis `2c6bf13c…`, analysis tests `901072ce…`, runner-safety tests `06e04c4e…` and protocol `13e68691…`. All five match `frozen_manifest_v4.json`; `frozen_runner_sha256.txt` also matches.
- `sha256(json.dumps(CFG, sort_keys=True))` from the imported runner is `be477e86…`, equal to `cfg_sha256`. `json.loads(json.dumps(CFG))` equals the manifest `cfg`.
- The §6 arm list is identical, in order, to `required_arms`.
- `brain.py`, `scene2.py`, `vision.py`, `snn.py`, `retina.py` and `circuit_bio2.json` are unchanged since `repair_integrity_initial.txt`.

## 1. First-audit blockers

| Blocker | Status | Evidence |
|---|---|---|
| (1) No confirmatory analysis code | **Resolved** | `analyze_cx_causal_confirmation.py` implements V1–V10, E1–E4, F1/F2/F3/F1s, t-CI, BCa, Wilcoxon and Holm, with stage1/final/dev modes. 48 synthetic checks pass. The dev4 cross-check against `scripts/analyze_dev4.py` matches (`regression/dev4_crosscheck.txt`). Caveats are in findings 6 and 7. |
| (2) Protocol contradictions | **Resolved** | v4 §5 has a blinded SD-only stage 1 with 24 seeds. §6 has 16 arms including Scalar-Shift±30. E3 is the positive control. F1/F2/F3/F1s replace the old families. V5 is conditional on Δ (analysis :212-214). Q4 is descriptive (C10). The two old documents carry SUPERSEDED banners (lines 1-3). |
| (3) Runner resume and safety | **Resolved, with minor residue** | Manifest identity (runner:412, :437-441) covers dataset_id, protocol, runner hash, cfg hash, jump, moving, arms, Δ and no_log. A record-level check runs in `_load_records` (:469-471). Duplicates are refused (:473). A truncated tail is refused unless `--repair-truncated`, which keeps an original copy and a report. `makedirs` is called at :428. The lock is `O_EXCL` (:433). Calibration exceptions are persisted as TECHNICAL_FAILURE for CX arms (:576-586). 23/23 safety checks pass. Residue is in finding 10. |

## 2. Analysis versus protocol (item 2)

Everything in this list was checked line by line and agrees with v4.

- **Contrasts and seed aggregation.**
  - S_DN: mean over the three Δ of (e(DN−30) − e(DN+30))/2.
  - P2a: Δ=0 only.
  - P2b: ±20 only, vs SelfOnly.
  - P3: all three Δ.
  - g: ±20.
  - S_scalar: all three Δ, used for E3 with threshold 20.
- **Q1.**
  - SUPPORTED if lo > 5 and ≥ 80 % positive; NEGATIVE if hi < 5 or < 60 % positive.
  - The manipulation check uses ≥ +15, ≤ −15, |sham| ≤ 5 and |median Δcoh| ≤ 0.1.
- **Q2.**
  - Two separate Holm m=2 families, one for benefit and one for "no meaningful benefit".
  - α = 0.025; thresholds 0 and −3; both point estimates must be ≤ −3.
  - The gate disables only the P2b component, so P2a can still give NEGATIVE.
  - The BCa counterpart is the two-sided 97.5 % interval.
  - The two outcomes are mutually exclusive, so the order of the code branches does not matter.
- **Q3.** Margin 5 with the 95 % t-CI; the gate makes it INCONCLUSIVE.
- **Robustness.** A BCa disagreement gives "INCONCLUSIVE (fragile)". The BCa seed is 20261027 with 10,000 resamples. Wilcoxon is reported only and never changes a verdict.
- **Complete case.** `contrast_values` (:276-288) requires every needed (arm, Δ) trial to be valid.
- **E1.** It counts seeds with V7, V8 or at least one invalid trial among all 16 arms × 3 Δ, using `n_tf > 0.10·N`.
- **E4.** `min_valid = max(20, ceil(0.85·N_planned))`. NOT_CONVERGED seeds are excluded from values but stay in the planned N, as the protocol says.
- **TF seeds in contrasts.** Seeds that count as TF for E1 are still used in contrasts whose trials are all valid. This matches V10 and is tested.
- **Stage-1 blinding.**
  - Output contains only counts, E1–E3 as PASS/FAIL, SD, SD_UB80, n_required, N_final and the decision. I confirmed this by printing it on synthetic data.
  - n_required depends only on SD_UB and a fixed δ, so it carries no mean information.
  - SD_UB uses `chi2.ppf(0.20)`, which is the correct upper bound. The protocol's "χ²₀.₂₀" notation is ambiguous but does not matter for the code.

## 3. Silent dropping, imputation and dev verdicts (item 3)

- There is no imputation. V1 and V2 REFUSE on a missing or duplicate record, a foreign hash, an unknown arm or Δ, or a seed outside the plan. `load_jsonl` refuses a truncated line.
- Dev mode (`--mode dev`, seeds 200–299 only) returns "DEV — NOT CONFIRMATORY" with no verdicts.
- Final mode REFUSES any record whose seed is outside `range(300, 300+n_final)`. Dev data therefore cannot yield a verdict.
- Remaining quiet exclusions are in finding 4. They are listed in `excluded_seeds` and count toward E4.

## 4. Runner (item 4)

- **`run_trial` is untouched.** The diff shows only a comment change in CFG, and the cfg hash is unchanged.
- **Brain creation is equivalent.**
  - `calibrated_brain(s, 0.0)` is identical to the old default call.
  - Non-CX arms never read `brain0`; `uses_cx` is at :169.
  - Arm and seed order, and therefore the order of calibrations, are unchanged.
- **Regression evidence is adequate.**
  - 10 trials match dev4 and 2 trials match dev2, bit-identically.
  - A further 2 trials, Scalar and CX-DN-Pulse+30 at Δ=0, are checked in the safety test.
  - Not covered: Shuffle and Scalar-Shift arms, and trials with logs.
- **CLI λ overrides** mutate CFG before `cfg_sha256` is computed (:535-537, :559). The runner then refuses the resume, or the analysis REFUSES on a cfg mismatch (tested).
- **Seeds and passive order.** Seeds are intentionally not part of the identity, which is needed for continuation. The order of arms and Δ is part of it, which is strict but safe.

## Findings

### BLOCKER
None.

### MAJOR
1. **The freeze is not anchored and the dependencies are not pinned.**
   - Nothing is committed: runner, analysis, protocol and tests are all untracked. The only freeze evidence is `frozen_at` in the manifest.
   - `runner_sha256` covers only `test_cx_causal_memory.py`. The behaviour also depends on `brain.py`, `scene2.py`, `vision.py`, `test_cx_working_memory_vs_kalman.py` (untracked) and `circuit_bio2.json`. Their hashes sit in `repair_integrity_initial.txt` but not in the manifest.
   - The mujoco, numpy and python versions are written to the dataset manifest but are not compared on resume. A venv change between stage 1 and the continuation would go undetected.
   - Fix before launching, without changing any hashed file:
     - Commit and tag the frozen files, plus the dependency files.
     - Append the dependency hashes and package versions to `progress_log.md`.
     - Check at continuation time that they are unchanged.

### MINOR
2. **Stage-1 enforcement is procedural.**
   - Final mode trusts `stage1_decision.json`. It checks only dataset_id and analysis_version (analysis :558). It does not recompute n_final, check that `decision` was CONTINUE, or require n_final ≥ 40.
   - A hand-edited `n_final=24` would allow an unblinded verdict on the 24 stage-1 seeds.
   - `--frozen` can point at another manifest, and the analysis does not verify its own hash against the manifest. It only records the hash in the output.
   - The manifest `dataset_id` is not compared with the frozen `CX-A2-CONFIRM-v4`.
   - These are exploitable only by deliberate action. The cheap fix is for final mode to recompute stage 1 from seeds 300–323 and compare. Any analysis edit changes the hash and requires re-freezing, which is cheap now because no data exist.
3. **Stage-1 output differs slightly from the §5.1 list.**
   - It adds `invalid_trials`, `silent_bump_trials` and `n_records`. The silent-bump count is outcome-adjacent but is not an effect on e.
   - Stage 1 also emits "STOP — NOT_CONVERGED > 20 %" for an E2 failure. §5.6 stops only on E1 and E3. Specify what to do on E2.
4. **Non-finite values vanish quietly.**
   - A NaN `e_end` is not a V3–V5 failure. The seed stays "OK" and is not counted in E1; it is only listed in `excluded_seeds`. I reproduced this. It can only trigger E4, which is conservative.
   - `mem_err_end` is None for a silent bump, so those seeds drop out of the descriptive composite criterion (iii). That biases iii favourably, though it is descriptive.
5. **Small text and code mismatches.**
   - V4 uses Freeze whenever its status is OK, not "if valid" (:201).
   - A V7 seed stays in contrasts that do not use the NC trials.
   - The manipulation-check coherence change is pooled across the three DN arms, while the protocol does not say pooled.
6. **Descriptive items from §3 are not implemented**: the "no-ring" row, signed e_end, offset-removed |e| and coherence statistics. Computing them later is post hoc, though they have no decision role.
7. **The persistence check and the real log layout have never run on real data.**
   - The dev records contain no logs, and the safety test uses `--no-log`.
   - I verified by reading the runner that the tuple is (rel, true_rel, ω, θ̂, coh), so index 4 is coherence and index 0 is rel. The code's use of those indices is consistent.
   - The check silently becomes "not evaluable" (None) if any valid CX-Bump trial lacks a log.
8. **Interaction of E2 and E4.** With N=40, 7 of 40 NOT_CONVERGED seeds (17.5 %) is below E2's 20 % but still triggers E4 (33 < 34). The effective threshold is 15 %. This is consistent, but state it.
9. **Document hygiene.**
   - `REPRODUCE.md` still shows the v1 command (seeds 300–339, no `--jump`, no `--dataset-id`, Δ ±20) under "Confirmation run". The runner would now refuse it, and the analysis would REFUSE its output.
   - `implementation_plan.md` cites a non-existent `final_preconfirmation_audit.md`.
   - `progress_log.md` "FINAL DECISION" still says 14 arms.
10. **Runner residue.**
    - Seeds 200–299 can be written into the confirm file. The analysis then REFUSES the whole dataset, which is loud but wastes compute.
    - A second `--out` with the same dataset_id creates an independent dataset, and there is no cross-path registry.
    - A stale lock needs manual deletion, and deleting it during a live run allows two writers. Duplicates would be caught by the analysis.
    - The runner does not check itself against `frozen_manifest_v4.json` before starting, so a mismatch is found only at analysis time.

## Recommendation: **READY FOR CONFIRMATION**

No blocker was found. The code implements v4 faithfully, and the dev4 cross-check and bit-identical regression support this. Before launching, do the following.

- Close finding 1 by committing and tagging the frozen files and recording the dependency hashes and package versions.
- Check that the venv is unchanged at the continuation.
- Mark the REPRODUCE.md v1 command as dead (finding 9).
- State what to do if stage 1 fails E2 (finding 3).

Findings 2 and 4–7 are optional hardening. Any change to the analysis needs a new hash in the manifest, which is cheap now because no data exist.
